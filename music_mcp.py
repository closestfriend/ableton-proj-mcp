#!/usr/bin/env python3
"""
Music Project Manager MCP
Safely scans and analyzes Ableton projects
"""

from mcp.server import Server
import mcp.server.stdio
import mcp.types as types
import os
import gzip
import tempfile
import datetime
try:
    import xml.etree.ElementTree as ET
except ImportError:
    ET = None

server = Server("music-manager")

# SAFETY LIMITS - Prevent scanning massive directories
MAX_FILES_TO_SCAN = 100  # Stop after this many .als files
MAX_FILE_SIZE_MB = 50    # Skip files larger than this
SCAN_DEPTH = 3           # Only go 3 folders deep
TIMEOUT_SECONDS = 30     # Max time for any operation

class SafeAbletonProject:
    """Lightweight project analyzer with safety checks"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.folder = os.path.basename(os.path.dirname(filepath))
        self.last_modified = datetime.datetime.fromtimestamp(
            os.path.getmtime(filepath)
        ).strftime("%Y-%m-%d")
        self.size_mb = round(os.path.getsize(filepath) / (1024 * 1024), 2)
        
        # Analysis results
        self.bpm = None
        self.track_count = 0
        self.audio_tracks = 0
        self.midi_tracks = 0
        self.error = None
        
    def analyze(self):
        """Safely analyze the project file"""
        # Skip if file is too large
        if self.size_mb > MAX_FILE_SIZE_MB:
            self.error = f"File too large ({self.size_mb}MB)"
            return False
            
        try:
            return self._parse_als_file()
        except Exception as e:
            self.error = str(e)
            return False
    
    def _parse_als_file(self):
        """Parse .als file (gzipped XML)"""
        if not ET:
            self.error = "XML parser not available"
            return False
            
        temp_file = None
        try:
            # Decompress the .als file
            with tempfile.NamedTemporaryFile(delete=False, mode='w+b') as temp:
                temp_file = temp.name
                with gzip.open(self.filepath, 'rb') as f:
                    temp.write(f.read())
            
            # Parse XML
            tree = ET.parse(temp_file)
            root = tree.getroot()
            
            # Extract BPM
            tempo = root.find(".//Tempo/Manual")
            if tempo is not None:
                value = tempo.get("Value")
                if value:
                    self.bpm = round(float(value), 1)
            
            # Count tracks
            audio_tracks = root.findall(".//AudioTrack")
            midi_tracks = root.findall(".//MidiTrack")
            self.audio_tracks = len(audio_tracks)
            self.midi_tracks = len(midi_tracks)
            self.track_count = self.audio_tracks + self.midi_tracks
            
            return True
            
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass

def safe_scan_directory(root_path, max_files=MAX_FILES_TO_SCAN, max_depth=SCAN_DEPTH):
    """Safely scan for .als files with limits"""
    if not os.path.exists(root_path):
        raise ValueError(f"Path does not exist: {root_path}")
    
    if not os.path.isdir(root_path):
        raise ValueError(f"Path is not a directory: {root_path}")
    
    projects = []
    file_count = 0
    
    for root, dirs, files in os.walk(root_path):
        # Check depth
        depth = root[len(root_path):].count(os.sep)
        if depth >= max_depth:
            dirs[:] = []  # Don't recurse deeper
            continue
        
        # Skip common large folders
        dirs[:] = [d for d in dirs if d not in [
            'Backup', 'Samples', 'Presets', 'Library', 
            'Cache', 'Recordings', 'Rendered'
        ]]
        
        for filename in files:
            if filename.endswith('.als'):
                if file_count >= max_files:
                    return projects, True  # Hit limit
                
                filepath = os.path.join(root, filename)
                try:
                    projects.append(SafeAbletonProject(filepath))
                    file_count += 1
                except Exception as e:
                    # Skip files we can't read
                    continue
    
    return projects, False  # Didn't hit limit

@server.list_tools()
async def list_tools():
    """Tell Claude what tools are available"""
    return [
        types.Tool(
            name="scan_projects",
            description=f"Scan a directory for Ableton projects. Safety limits: {MAX_FILES_TO_SCAN} files max, {SCAN_DEPTH} folders deep, skips files over {MAX_FILE_SIZE_MB}MB. Returns basic info without deep analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Full path to scan for .als files"
                    }
                },
                "required": ["directory"]
            }
        ),
        types.Tool(
            name="analyze_projects",
            description="Analyze specific projects to get BPM, track count, etc. Pass project paths from scan_projects results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of .als file paths to analyze"
                    }
                },
                "required": ["project_paths"]
            }
        ),
        types.Tool(
            name="find_recent",
            description="Find the most recently modified projects in a directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to scan"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent projects to return (default 10)",
                        "default": 10
                    }
                },
                "required": ["directory"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls from Claude"""
    
    if name == "scan_projects":
        directory = arguments["directory"]
        
        try:
            projects, hit_limit = safe_scan_directory(directory)
            
            result_lines = [f"Found {len(projects)} Ableton projects in: {directory}\n"]
            
            if hit_limit:
                result_lines.append(f"⚠️  Hit safety limit of {MAX_FILES_TO_SCAN} files. Showing first {len(projects)}.\n")
            
            result_lines.append("=" * 60)
            
            for proj in projects:
                result_lines.append(
                    f"\n📁 {proj.folder}/{proj.filename}\n"
                    f"   Last modified: {proj.last_modified}\n"
                    f"   Size: {proj.size_mb}MB"
                )
            
            return [types.TextContent(
                type="text",
                text="\n".join(result_lines)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error scanning directory: {str(e)}"
            )]
    
    elif name == "analyze_projects":
        paths = arguments["project_paths"]
        
        if len(paths) > 20:
            return [types.TextContent(
                type="text",
                text="⚠️  Please analyze 20 or fewer projects at a time for safety."
            )]
        
        result_lines = ["Analyzing projects...\n", "=" * 60]
        
        for path in paths:
            if not os.path.exists(path):
                result_lines.append(f"\n❌ Not found: {path}")
                continue
            
            proj = SafeAbletonProject(path)
            success = proj.analyze()
            
            result_lines.append(f"\n📊 {proj.filename}")
            result_lines.append(f"   Folder: {proj.folder}")
            result_lines.append(f"   Last modified: {proj.last_modified}")
            result_lines.append(f"   Size: {proj.size_mb}MB")
            
            if success:
                if proj.bpm:
                    result_lines.append(f"   BPM: {proj.bpm}")
                result_lines.append(f"   Tracks: {proj.track_count} ({proj.audio_tracks} audio, {proj.midi_tracks} MIDI)")
            else:
                result_lines.append(f"   ⚠️  Analysis failed: {proj.error}")
        
        return [types.TextContent(
            type="text",
            text="\n".join(result_lines)
        )]
    
    elif name == "find_recent":
        directory = arguments["directory"]
        limit = arguments.get("limit", 10)
        
        try:
            projects, hit_limit = safe_scan_directory(directory)
            
            # Sort by modification time
            projects.sort(key=lambda p: os.path.getmtime(p.filepath), reverse=True)
            
            # Take top N
            recent = projects[:limit]
            
            result_lines = [f"🕒 {len(recent)} Most Recent Projects:\n", "=" * 60]
            
            for i, proj in enumerate(recent, 1):
                result_lines.append(
                    f"\n{i}. {proj.filename}\n"
                    f"   📁 {proj.folder}\n"
                    f"   📅 {proj.last_modified}\n"
                    f"   💾 {proj.size_mb}MB"
                )
            
            return [types.TextContent(
                type="text",
                text="\n".join(result_lines)
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, 
            write_stream, 
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
