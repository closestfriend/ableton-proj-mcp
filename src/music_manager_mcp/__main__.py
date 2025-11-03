#!/usr/bin/env python3
"""
Enhanced Music Project Manager MCP
Now with FULL detective capabilities! ✨
Hunter can see EVERYTHING inside .als files!
"""

from mcp.server import Server
import mcp.server.stdio
import mcp.types as types
import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Import our enhanced analyzer
try:
    from .enhanced_analyzer import (
        EnhancedAbletonAnalyzer,
        ProjectStructure, 
        compare_projects,
        calculate_similarity
    )
    ENHANCED_MODE = True
except ImportError:
    ENHANCED_MODE = False
    print("Enhanced analyzer not available, falling back to basic mode")

server = Server("music-manager")

# SAFETY LIMITS
MAX_FILES_TO_SCAN = 100
MAX_FILE_SIZE_MB = 50
SCAN_DEPTH = 3

@server.list_tools()
async def list_tools():
    """List all available music management tools"""
    tools = [
        types.Tool(
            name="scan_projects",
            description="""Scan a directory for Ableton Live .als project files and return basic metadata.

Returns: JSON with project names, sizes, modification dates, and folder locations.

Use cases:
- Initial discovery: "What projects do I have in this folder?"
- Quick overview without deep analysis
- Getting file paths for use with analyze_projects

Safety limits:
- Scans max 100 files (configurable)
- Skips files over 50MB
- Only goes 3 folders deep
- Excludes heavy folders (Backup, Samples, Library)

Use this FIRST to discover projects, then use analyze_projects for detailed info.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Absolute path to directory containing Ableton projects (e.g., '/Users/username/Music/Ableton')"
                    }
                },
                "required": ["directory"]
            }
        ),
        types.Tool(
            name="analyze_projects",
            description="""Deep analysis of specific Ableton Live projects. Extracts comprehensive metadata from .als files.

Returns: JSON with BPM, track details, plugins, master chain, arrangement structure, completion indicators, and more.

What it analyzes:
- Basic: BPM, track counts (audio/MIDI/frozen)
- Structure: Arrangement length, scenes, markers, automation lanes
- Plugins: All third-party plugins, CPU-heavy plugin count
- Master chain: All devices on master track
- Tracks: First 10 tracks with names, types, devices, frozen status
- Completion: Heuristic for whether project is likely finished
- Content hashes: For duplicate detection

Performance: Each project requires XML parsing (gzip decompression + parse). Use scan_projects first to get paths.

Best practice: Analyze 5-10 projects at a time, not all at once.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of absolute paths to .als files (get these from scan_projects results)"
                    }
                },
                "required": ["project_paths"]
            }
        ),
        types.Tool(
            name="find_recent",
            description="""Find the most recently modified Ableton projects in a directory, sorted by modification time.

Returns: JSON with the N most recent projects, including paths, names, folders, modification dates, and sizes.

Use cases:
- "What have I been working on lately?"
- Quick access to active projects
- Finding projects modified in the last week/month

Comparison with scan_projects:
- scan_projects: Returns ALL projects (up to limit), unsorted
- find_recent: Returns ONLY the N most recent, sorted by time

This is faster than scan + sort if you only need recent projects.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Absolute path to directory containing Ableton projects"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent projects to return (default: 10, recommended max: 20)",
                        "default": 10
                    }
                },
                "required": ["directory"]
            }
        )
    ]
    
    # Add enhanced tools if available
    if ENHANCED_MODE:
        tools.extend([
            types.Tool(
                name="find_duplicates",
                description="""Find duplicate Ableton projects based on content similarity, not just filename.

Analyzes: Track structure, device chains, MIDI patterns, BPM, track counts, master chains.

Returns: JSON with pairs of similar projects, similarity scores, and comparison details.

Similarity factors:
- Content hash (track names + device chains): 40%
- Track count match: 15%
- BPM match: 10%
- Master chain match: 20%
- MIDI pattern hash: 15%

Use cases:
- "Do I have multiple versions of the same project?"
- Cleaning up before backup
- Finding alternate versions (e.g., "Project v1", "Project v2", "Project FINAL")

Performance: Analyzes ALL projects in directory (up to 100), then compares pairs. Can be slow for large collections.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory to scan for duplicate projects"
                        },
                        "threshold": {
                            "type": "number",
                            "description": "Similarity threshold percentage (0-100). Default 80 = very similar. Lower = more matches. Higher = only near-exact duplicates.",
                            "default": 80
                        }
                    },
                    "required": ["directory"]
                }
            ),
            types.Tool(
                name="find_missing_plugins",
                description="""Scan projects and list all third-party plugins used. Useful for checking plugin availability.

Returns: JSON with all unique plugins found across projects, and which projects use each plugin.

Use cases:
- "What plugins do I need to open these projects?"
- Checking before moving projects to a new computer
- Finding projects that use a specific plugin

Note: Does NOT actually verify if plugins are installed (no access to system VST folders). It lists what's in the projects.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory containing projects to scan for plugin usage"
                        }
                    },
                    "required": ["directory"]
                }
            ),
            types.Tool(
                name="analyze_master_chains",
                description="""Extract and compare master track device chains across multiple projects.

Returns: JSON grouped by unique master chains, showing which projects use each chain.

Use cases:
- "Do I reuse the same mastering chain across projects?"
- Finding projects with similar mastering setups
- Identifying your mastering patterns/templates

Example: Groups projects using "EQ8 → Glue Compressor → Limiter" together.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of .als file paths to analyze (get from scan_projects)"
                        }
                    },
                    "required": ["project_paths"]
                }
            ),
            types.Tool(
                name="find_finished_projects",
                description="""Classify projects as 'likely finished' vs 'sketches' using heuristics.

Classification criteria (needs 3+ to be 'finished'):
- Has 3+ arrangement markers (like DROP, VERSE, OUTRO)
- Has 2+ devices on master track (mastering chain)
- Arrangement is 64+ bars long
- Has 5+ scenes in session view

Returns: JSON with two lists: finished projects and sketches, with completion indicators.

Use cases:
- "Which projects are ready to export/release?"
- Separating ideas from complete tracks
- Finding abandoned projects vs works-in-progress

Note: This is a heuristic, not perfect. Your workflow may differ.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory to scan and classify projects"
                        }
                    },
                    "required": ["directory"]
                }
            )
        ])
    
    return tools

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    
    if name == "scan_projects":
        return await scan_projects(arguments.get("directory"))
        
    elif name == "analyze_projects":
        return await analyze_projects(arguments.get("project_paths"))
        
    elif name == "find_recent":
        return await find_recent(
            arguments.get("directory"),
            arguments.get("limit", 10)
        )
        
    # Enhanced tools
    elif name == "find_duplicates" and ENHANCED_MODE:
        return await find_duplicates(
            arguments.get("directory"),
            arguments.get("threshold", 80)
        )
        
    elif name == "find_missing_plugins" and ENHANCED_MODE:
        return await find_missing_plugins(arguments.get("directory"))
        
    elif name == "analyze_master_chains" and ENHANCED_MODE:
        return await analyze_master_chains(arguments.get("project_paths"))
        
    elif name == "find_finished_projects" and ENHANCED_MODE:
        return await find_finished_projects(arguments.get("directory"))
    
    return [types.TextContent(
        type="text",
        text=f"Unknown tool or tool not available: {name}"
    )]

async def scan_projects(directory: str):
    """Basic scan - quick overview"""
    projects = []
    scanned = 0

    try:
        for root, _, files in os.walk(directory):
            # Check depth
            depth = root[len(directory):].count(os.sep)
            if depth > SCAN_DEPTH:
                continue

            for file in files:
                if file.endswith('.als'):
                    if scanned >= MAX_FILES_TO_SCAN:
                        break

                    filepath = os.path.join(root, file)
                    size_mb = os.path.getsize(filepath) / (1024 * 1024)

                    if size_mb <= MAX_FILE_SIZE_MB:
                        projects.append({
                            'path': filepath,
                            'name': file,
                            'folder': os.path.basename(os.path.dirname(filepath)),
                            'size_mb': round(size_mb, 2),
                            'modified': datetime.datetime.fromtimestamp(
                                os.path.getmtime(filepath)
                            ).strftime("%Y-%m-%d %H:%M")
                        })
                        scanned += 1

        result = {
            "success": True,
            "directory": directory,
            "summary": f"Found {len(projects)} Ableton projects",
            "hit_limit": scanned >= MAX_FILES_TO_SCAN,
            "projects": projects,
            "limits": {
                "max_files": MAX_FILES_TO_SCAN,
                "max_size_mb": MAX_FILE_SIZE_MB,
                "scan_depth": SCAN_DEPTH
            }
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except FileNotFoundError:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "directory_not_found",
                "directory": directory,
                "message": f"Directory does not exist: {directory}"
            }, indent=2)
        )]
    except PermissionError:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "permission_denied",
                "directory": directory,
                "message": f"Permission denied accessing: {directory}"
            }, indent=2)
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "scan_failed",
                "directory": directory,
                "message": str(e)
            }, indent=2)
        )]

async def analyze_projects(project_paths: List[str]):
    """Deep analysis with our enhanced analyzer! ✨"""

    if not ENHANCED_MODE:
        # Fallback to basic analysis
        return await basic_analyze_projects(project_paths)

    results = []
    errors = []

    for path in project_paths:
        if not os.path.exists(path):
            errors.append({
                "path": path,
                "error": "file_not_found",
                "message": f"Project file not found: {path}"
            })
            continue

        try:
            analyzer = EnhancedAbletonAnalyzer(path)
            analysis = analyzer.analyze()

            # Convert dataclass to dict for JSON serialization
            project_data = {
                'path': path,
                'name': os.path.basename(path),
                'folder': os.path.basename(os.path.dirname(path)),
                'file_info': {
                    'size_mb': round(os.path.getsize(path) / (1024 * 1024), 2),
                    'modified': datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M')
                },
                'basic_info': {
                    'bpm': analysis.bpm,
                    'track_count': analysis.track_count,
                    'audio_tracks': analysis.audio_tracks,
                    'midi_tracks': analysis.midi_tracks,
                    'frozen_tracks': analysis.frozen_track_count
                },
                'structure': {
                    'arrangement_length_bars': analysis.arrangement_length_bars,
                    'scene_count': analysis.scene_count,
                    'markers': analysis.markers,
                    'automation_lanes': analysis.automation_lane_count,
                    'total_clips': analysis.total_clips
                },
                'master_chain': analysis.master_chain,
                'plugins': {
                    'third_party': analysis.third_party_plugins,
                    'heavy_count': analysis.heavy_plugin_count,
                    'missing': analysis.missing_plugins
                },
                'completion': {
                    'likely_finished': analysis.likely_finished,
                    'has_arrangement': analysis.has_arrangement_view,
                    'has_master_chain': analysis.has_master_chain
                },
                'tracks': [
                    {
                        'name': track.name,
                        'type': track.track_type,
                        'devices': track.devices[:5],  # First 5 devices
                        'frozen': track.is_frozen,
                        'volume': track.volume,
                        'color': track.color
                    }
                    for track in analysis.tracks[:10]  # First 10 tracks
                ],
                'content_hashes': {
                    'structure': analysis.content_hash,
                    'midi_patterns': analysis.midi_pattern_hash
                }
            }

            results.append(project_data)

        except PermissionError:
            errors.append({
                "path": path,
                "error": "permission_denied",
                "message": f"Permission denied reading: {path}"
            })
        except Exception as e:
            errors.append({
                "path": path,
                "error": "analysis_failed",
                "message": str(e)
            })

    response = {
        "success": len(results) > 0,
        "summary": f"Analyzed {len(results)} of {len(project_paths)} projects",
        "analyzed_count": len(results),
        "error_count": len(errors),
        "results": results,
        "errors": errors if errors else None
    }

    return [types.TextContent(
        type="text",
        text=json.dumps(response, indent=2)
    )]

async def basic_analyze_projects(project_paths: List[str]):
    """Basic analysis fallback when enhanced mode not available"""
    result_lines = ["Analyzing projects (basic mode)...\n", "=" * 60]
    
    for path in project_paths:
        if not os.path.exists(path):
            result_lines.append(f"\n❌ Not found: {path}")
            continue
            
        result_lines.append(f"\n📊 {os.path.basename(path)}")
        result_lines.append(f"   Size: {round(os.path.getsize(path) / (1024 * 1024), 2)}MB")
        result_lines.append(f"   Last modified: {datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d')}")
    
    return [types.TextContent(
        type="text",
        text="\n".join(result_lines)
    )]

async def find_recent(directory: str, limit: int = 10):
    """Find recently modified projects"""

    try:
        projects = []

        for root, _, files in os.walk(directory):
            depth = root[len(directory):].count(os.sep)
            if depth > SCAN_DEPTH:
                continue

            for file in files:
                if file.endswith('.als'):
                    filepath = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(filepath)
                        size_mb = os.path.getsize(filepath) / (1024 * 1024)

                        projects.append({
                            'path': filepath,
                            'name': file,
                            'folder': os.path.basename(os.path.dirname(filepath)),
                            'modified_time': mtime,
                            'modified': datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M'),
                            'size_mb': round(size_mb, 2)
                        })
                    except (OSError, IOError):
                        # Skip files we can't read
                        continue

        # Sort by modification time
        projects.sort(key=lambda p: p['modified_time'], reverse=True)

        # Take top N
        recent = projects[:limit]

        result = {
            "success": True,
            "directory": directory,
            "summary": f"Found {len(recent)} most recent projects (of {len(projects)} total)",
            "limit": limit,
            "total_found": len(projects),
            "projects": [
                {
                    'path': p['path'],
                    'name': p['name'],
                    'folder': p['folder'],
                    'modified': p['modified'],
                    'size_mb': p['size_mb']
                }
                for p in recent
            ]
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except FileNotFoundError:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "directory_not_found",
                "directory": directory,
                "message": f"Directory does not exist: {directory}"
            }, indent=2)
        )]
    except PermissionError:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "permission_denied",
                "directory": directory,
                "message": f"Permission denied accessing: {directory}"
            }, indent=2)
        )]
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": "search_failed",
                "directory": directory,
                "message": str(e)
            }, indent=2)
        )]

# Enhanced functions (only available when enhanced analyzer is imported)
async def find_duplicates(directory: str, threshold: float = 80):
    """Find duplicate projects based on actual content!"""
    if not ENHANCED_MODE:
        return [types.TextContent(
            type="text",
            text="Enhanced analyzer not available. Cannot detect duplicates."
        )]
    
    # First, scan all projects
    projects = []
    for root, _, files in os.walk(directory):
        depth = root[len(directory):].count(os.sep)
        if depth > SCAN_DEPTH:
            continue
        for file in files:
            if file.endswith('.als'):
                projects.append(os.path.join(root, file))
    
    # Analyze all projects
    analyzed = {}
    for path in projects[:MAX_FILES_TO_SCAN]:  # Safety limit
        try:
            analyzer = EnhancedAbletonAnalyzer(path)
            analyzed[path] = analyzer.analyze()
        except:
            continue
    
    # Compare all pairs
    duplicates = []
    paths = list(analyzed.keys())
    
    for i, path1 in enumerate(paths):
        for path2 in paths[i+1:]:
            comparison = compare_projects(analyzed[path1], analyzed[path2])
            
            if comparison['similarity_score'] >= threshold:
                duplicates.append({
                    'project1': os.path.basename(path1),
                    'project2': os.path.basename(path2),
                    'similarity': comparison['similarity_score'],
                    'same_structure': comparison['same_structure_hash'],
                    'same_midi': comparison['same_midi_patterns']
                })
    
    result_lines = [
        f"🔍 Duplicate Detection Results (threshold: {threshold}%)\n",
        f"Scanned: {len(analyzed)} projects\n",
        f"Duplicates found: {len(duplicates)}\n",
        "=" * 60
    ]
    
    for dup in duplicates:
        result_lines.append(
            f"\n📄 {dup['project1']}\n"
            f"📄 {dup['project2']}\n"
            f"   Similarity: {dup['similarity']}%\n"
            f"   Same structure: {'✅' if dup['same_structure'] else '❌'}\n"
            f"   Same MIDI: {'✅' if dup['same_midi'] else '❌'}"
        )
    
    return [types.TextContent(
        type="text",
        text="\n".join(result_lines)
    )]

async def find_missing_plugins(directory: str):
    """Find projects using plugins that might not be installed"""
    if not ENHANCED_MODE:
        return [types.TextContent(
            type="text",
            text="Enhanced analyzer not available. Cannot detect plugins."
        )]
    
    projects = []
    for root, _, files in os.walk(directory):
        depth = root[len(directory):].count(os.sep)
        if depth > SCAN_DEPTH:
            continue
        for file in files:
            if file.endswith('.als'):
                projects.append(os.path.join(root, file))
    
    plugin_usage = {}  # plugin_name -> list of projects using it
    all_plugins = set()
    
    for path in projects[:MAX_FILES_TO_SCAN]:
        try:
            analyzer = EnhancedAbletonAnalyzer(path)
            analysis = analyzer.analyze()
            
            for plugin in analysis.third_party_plugins:
                all_plugins.add(plugin)
                if plugin not in plugin_usage:
                    plugin_usage[plugin] = []
                plugin_usage[plugin].append(os.path.basename(path))
                
        except:
            continue
    
    result_lines = [
        f"🔌 Plugin Analysis\n",
        f"Total unique plugins: {len(all_plugins)}\n",
        "=" * 60,
        "\n📋 All Third-Party Plugins Found:"
    ]
    
    for plugin in sorted(all_plugins)[:20]:  # Show first 20
        count = len(plugin_usage[plugin])
        result_lines.append(f"   • {plugin} (used in {count} project{'s' if count > 1 else ''})")
    
    return [types.TextContent(
        type="text",
        text="\n".join(result_lines)
    )]

async def analyze_master_chains(project_paths: List[str]):
    """Compare master chains across projects"""
    if not ENHANCED_MODE:
        return [types.TextContent(
            type="text",
            text="Enhanced analyzer not available. Cannot analyze master chains."
        )]
    
    chains = {}
    
    for path in project_paths:
        try:
            analyzer = EnhancedAbletonAnalyzer(path)
            analysis = analyzer.analyze()
            
            chain_str = ' → '.join(analysis.master_chain) if analysis.master_chain else "No master chain"
            
            if chain_str not in chains:
                chains[chain_str] = []
            chains[chain_str].append(os.path.basename(path))
            
        except:
            continue
    
    result_lines = [
        f"🎛️ Master Chain Analysis\n",
        f"Unique chains: {len(chains)}\n",
        "=" * 60
    ]
    
    for chain, projects in chains.items():
        result_lines.append(f"\n📊 Chain: {chain}")
        result_lines.append(f"   Used in {len(projects)} project{'s' if len(projects) > 1 else ''}:")
        for proj in projects[:5]:  # Show first 5
            result_lines.append(f"     • {proj}")
    
    return [types.TextContent(
        type="text",
        text="\n".join(result_lines)
    )]

async def find_finished_projects(directory: str):
    """Detect which projects are likely finished"""
    if not ENHANCED_MODE:
        return [types.TextContent(
            type="text",
            text="Enhanced analyzer not available. Cannot assess completion."
        )]
    
    projects = []
    for root, _, files in os.walk(directory):
        depth = root[len(directory):].count(os.sep)
        if depth > SCAN_DEPTH:
            continue
        for file in files:
            if file.endswith('.als'):
                projects.append(os.path.join(root, file))
    
    finished = []
    sketches = []
    
    for path in projects[:MAX_FILES_TO_SCAN]:
        try:
            analyzer = EnhancedAbletonAnalyzer(path)
            analysis = analyzer.analyze()
            
            project_info = {
                'name': os.path.basename(path),
                'bars': analysis.arrangement_length_bars,
                'markers': len(analysis.markers),
                'has_master': analysis.has_master_chain,
                'track_count': analysis.track_count
            }
            
            if analysis.likely_finished:
                finished.append(project_info)
            else:
                sketches.append(project_info)
                
        except:
            continue
    
    result_lines = [
        f"✅ Project Completion Analysis\n",
        f"Total scanned: {len(finished) + len(sketches)}\n",
        f"Likely finished: {len(finished)}\n",
        f"Likely sketches: {len(sketches)}\n",
        "=" * 60
    ]
    
    if finished:
        result_lines.append("\n🏁 Likely Finished Projects:")
        for proj in finished[:10]:
            result_lines.append(
                f"   • {proj['name']}\n"
                f"     {proj['bars']} bars, {proj['markers']} markers, {proj['track_count']} tracks"
            )
    
    if sketches:
        result_lines.append("\n🎨 Likely Sketches/Ideas:")
        for proj in sketches[:10]:
            result_lines.append(
                f"   • {proj['name']}\n"
                f"     {proj['bars']} bars, {proj['markers']} markers, {proj['track_count']} tracks"
            )
    
    return [types.TextContent(
        type="text",
        text="\n".join(result_lines)
    )]

def main():
    """Run the MCP server"""
    import asyncio
    async def run_server():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, 
                write_stream, 
                server.create_initialization_options()
            )
    asyncio.run(run_server())

if __name__ == "__main__":
    main()
