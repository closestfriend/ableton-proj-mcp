#!/usr/bin/env python3
"""
Music Project Manager MCP
Safely scans and analyzes Ableton projects
Enhanced Edition ✨ — Now with MAXIMUM metadata extraction!
"""

from mcp.server import Server
import mcp.server.stdio
import mcp.types as types
import os
import gzip
import tempfile
import datetime
import hashlib
from pathlib import Path
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

# Known CPU-heavy plugins (for analysis)
HEAVY_PLUGINS = {
    'Serum', 'Vital', 'Omnisphere', 'Kontakt', 'Massive', 
    'Diva', 'Repro', 'Pigments', 'Spire', 'Sylenth1',
    'Zebra', 'Phase Plant', 'Avenger', 'Falcon'
}


class SafeAbletonProject:
    """Lightweight project analyzer with safety checks — ENHANCED EDITION ✨"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.folder = os.path.basename(os.path.dirname(filepath))
        self.last_modified = datetime.datetime.fromtimestamp(
            os.path.getmtime(filepath)
        ).strftime("%Y-%m-%d")
        self.size_mb = round(os.path.getsize(filepath) / (1024 * 1024), 2)
        
        # Basic analysis results
        self.bpm = None
        self.track_count = 0
        self.audio_tracks = 0
        self.midi_tracks = 0
        self.audio_track_count = 0  # Alias for compatibility
        self.midi_track_count = 0   # Alias for compatibility
        self.plugins = []  # List of (type, name) tuples
        self.plugin_count = 0
        self.error = None
        
        # ✨ ENHANCED FEATURES ✨
        self.track_names = []           # Names of all tracks
        self.track_details = []         # Full track info dicts
        self.master_chain = []          # Devices on master track
        self.return_tracks = []         # Return/send track info
        self.frozen_track_count = 0     # Number of frozen tracks
        
        # Arrangement & structure
        self.arrangement_length_bars = 0
        self.scene_count = 0
        self.marker_count = 0
        self.markers = []               # Marker names like "DROP", "OUTRO"
        self.automation_lane_count = 0
        self.total_clips = 0
        
        # Hashes for duplicate detection
        self.content_hash = ""
        self.midi_pattern_hash = ""
        
        # CPU & complexity
        self.heavy_plugin_count = 0
        self.builtin_devices = []       # Ableton stock devices
        
        # Completion analysis
        self.has_arrangement = False
        self.has_master_chain = False
        self.likely_finished = False
        
        # Sample tracking
        self.sample_paths = []
        self.missing_samples = []
        self.sample_count = 0
        self.missing_sample_count = 0
        
    def analyze(self):
        """Safely analyze the project file — FULL DEEP DIVE ✨"""
        if self.size_mb > MAX_FILE_SIZE_MB:
            self.error = f"File too large ({self.size_mb}MB)"
            return False
            
        try:
            return self._parse_als_file()
        except Exception as e:
            self.error = str(e)
            return False
    
    def _parse_als_file(self):
        """Parse .als file (gzipped XML) — Enhanced Edition"""
        if not ET:
            self.error = "XML parser not available"
            return False
            
        try:
            # Decompress directly to memory (faster, no temp file needed)
            with gzip.open(self.filepath, 'rb') as f:
                xml_content = f.read()
            
            root = ET.fromstring(xml_content)
            
            # === BASIC INFO ===
            self._extract_bpm(root)
            self._count_tracks(root)
            self._extract_plugins(root)
            
            # === ENHANCED FEATURES ✨ ===
            self._extract_track_details(root)
            self._extract_master_chain(root)
            self._extract_arrangement_info(root)
            self._extract_markers(root)
            self._count_automation(root)
            self._extract_samples(root)
            self._generate_hashes(root)
            self._count_heavy_plugins()
            self._extract_builtin_devices(root)
            self._assess_completion()
            
            return True
            
        except Exception as e:
            self.error = str(e)
            return False

    def _extract_bpm(self, root):
        """Extract project BPM"""
        tempo = root.find(".//Tempo/Manual")
        if tempo is not None:
            value = tempo.get("Value")
            if value:
                self.bpm = round(float(value), 1)

    def _count_tracks(self, root):
        """Count tracks by type"""
        audio_tracks = root.findall(".//AudioTrack")
        midi_tracks = root.findall(".//MidiTrack")
        self.audio_tracks = len(audio_tracks)
        self.midi_tracks = len(midi_tracks)
        self.audio_track_count = self.audio_tracks
        self.midi_track_count = self.midi_tracks
        self.track_count = self.audio_tracks + self.midi_tracks

    def _extract_plugins(self, root):
        """Extract plugin names from the XML"""
        plugin_devices = root.findall(".//PluginDevice")
        plugins_found = []

        for device in plugin_devices:
            # Try VST3 plugin name
            vst3_name = device.find(".//PluginDesc/Vst3PluginInfo/Name")
            if vst3_name is not None:
                name = vst3_name.get("Value")
                if name:
                    plugins_found.append(("VST3", name))
                    continue

            # Try AU plugin name
            au_name = device.find(".//PluginDesc/AuPluginInfo/Name")
            if au_name is not None:
                name = au_name.get("Value")
                if name:
                    plugins_found.append(("AU", name))
                    continue

            # Try VST2 plugin name
            vst2_name = device.find(".//PluginDesc/VstPluginInfo/PlugName")
            if vst2_name is not None:
                name = vst2_name.get("Value")
                if name:
                    plugins_found.append(("VST2", name))

        self.plugins = plugins_found
        self.plugin_count = len(plugins_found)

    def _extract_track_details(self, root):
        """Extract detailed info for all tracks ✨"""
        track_details = []
        track_names = []
        frozen_count = 0
        
        # Process MIDI tracks
        for track in root.findall(".//MidiTrack"):
            info = self._parse_track(track, "MIDI")
            track_details.append(info)
            track_names.append(info['name'])
            if info['is_frozen']:
                frozen_count += 1
        
        # Process Audio tracks
        for track in root.findall(".//AudioTrack"):
            info = self._parse_track(track, "Audio")
            track_details.append(info)
            track_names.append(info['name'])
            if info['is_frozen']:
                frozen_count += 1
        
        self.track_details = track_details
        self.track_names = track_names
        self.frozen_track_count = frozen_count
    
    def _parse_track(self, track_elem, track_type):
        """Parse a single track element"""
        # Get track name
        name = "Untitled"
        name_elem = track_elem.find(".//EffectiveName")
        if name_elem is not None:
            name = name_elem.get("Value", "Untitled")
        
        # Alternative name location
        if name == "Untitled":
            user_name = track_elem.find(".//UserName")
            if user_name is not None:
                name = user_name.get("Value", "Untitled")
        
        # Get devices on this track
        devices = []
        device_chain = track_elem.find(".//DeviceChain")
        if device_chain is not None:
            devices = self._get_devices_from_chain(device_chain)
        
        # Check if frozen
        is_frozen = False
        freeze_elem = track_elem.find(".//Freeze")
        if freeze_elem is not None:
            is_frozen = freeze_elem.get("Value", "false").lower() == "true"
        
        # Get color
        color = None
        color_elem = track_elem.find(".//Color")
        if color_elem is not None:
            color = color_elem.get("Value")
        
        # Get volume (for mixing analysis)
        volume = None
        vol_elem = track_elem.find(".//Volume/Manual")
        if vol_elem is not None:
            volume = vol_elem.get("Value")
        
        return {
            'name': name,
            'type': track_type,
            'devices': devices,
            'is_frozen': is_frozen,
            'color': color,
            'volume': volume
        }
    
    def _get_devices_from_chain(self, chain_elem):
        """Extract device names from a device chain"""
        devices = []
        
        # Look for various device types
        for device in chain_elem.findall(".//Devices/*"):
            device_name = self._identify_device(device)
            if device_name:
                devices.append(device_name)
        
        return devices
    
    def _identify_device(self, device_elem):
        """Identify a device by its XML tag or plugin info"""
        tag = device_elem.tag
        
        # Built-in Ableton devices have recognizable tags
        builtin_devices = {
            'Eq8': 'EQ Eight',
            'Compressor2': 'Compressor',
            'GlueCompressor': 'Glue Compressor',
            'Limiter': 'Limiter',
            'Saturator': 'Saturator',
            'AutoFilter': 'Auto Filter',
            'Reverb': 'Reverb',
            'Delay': 'Delay',
            'PingPongDelay': 'Ping Pong Delay',
            'FilterDelay': 'Filter Delay',
            'Chorus2': 'Chorus',
            'Flanger': 'Flanger',
            'Phaser': 'Phaser',
            'Redux2': 'Redux',
            'Vinyl': 'Vinyl Distortion',
            'Amp': 'Amp',
            'Cabinet': 'Cabinet',
            'Overdrive': 'Overdrive',
            'Pedal': 'Pedal',
            'Utility': 'Utility',
            'Tuner': 'Tuner',
            'Spectrum': 'Spectrum',
            'MultibandDynamics': 'Multiband Dynamics',
            'Gate': 'Gate',
            'StereoGain': 'Utility',
            'CrossDelay': 'Echo',
            'FrequencyShifter': 'Frequency Shifter',
            'Erosion': 'Erosion',
            'BeatRepeat': 'Beat Repeat',
            'Looper': 'Looper',
            'DrumBuss': 'Drum Buss',
            'Echo': 'Echo',
            'Corpus': 'Corpus',
            'Resonators': 'Resonators',
            'Vocoder': 'Vocoder',
            # Instruments
            'OriginalSimpler': 'Simpler',
            'MultiSampler': 'Sampler',
            'InstrumentVector': 'Wavetable',
            'InstrumentImpulse': 'Impulse',
            'Drift': 'Drift',
            'DrumGroupDevice': 'Drum Rack',
            'InstrumentGroupDevice': 'Instrument Rack',
            'AudioEffectGroupDevice': 'Audio Effect Rack',
            'MidiEffectGroupDevice': 'MIDI Effect Rack',
            'Operator': 'Operator',
            'Collision': 'Collision',
            'StringStudio': 'Tension',
            'LoungeLizard': 'Electric',
            'Analog': 'Analog',
        }
        
        if tag in builtin_devices:
            return builtin_devices[tag]
        
        # Check if it's a plugin device
        if tag == 'PluginDevice':
            # VST3
            vst3_name = device_elem.find(".//PluginDesc/Vst3PluginInfo/Name")
            if vst3_name is not None:
                return vst3_name.get("Value")
            
            # AU
            au_name = device_elem.find(".//PluginDesc/AuPluginInfo/Name")
            if au_name is not None:
                return au_name.get("Value")
            
            # VST2
            vst2_name = device_elem.find(".//PluginDesc/VstPluginInfo/PlugName")
            if vst2_name is not None:
                return vst2_name.get("Value")
        
        # Return tag if we can't identify it better
        return tag if tag not in ['On', 'LomId', 'IsExpanded', 'ModulationSourceCount'] else None

    def _extract_master_chain(self, root):
        """Extract master track device chain ✨"""
        master_devices = []
        master_track = root.find(".//MasterTrack")
        
        if master_track is not None:
            device_chain = master_track.find(".//DeviceChain")
            if device_chain is not None:
                for device in device_chain.findall(".//Devices/*"):
                    device_name = self._identify_device(device)
                    if device_name:
                        master_devices.append(device_name)
        
        self.master_chain = master_devices
        self.has_master_chain = len(master_devices) > 0

    def _extract_arrangement_info(self, root):
        """Extract arrangement view information ✨"""
        # Get arrangement length
        # Look for the furthest end point
        end_times = []
        
        # Check arrangement clips
        for clip in root.findall(".//ArrangerAutomation//Events/*"):
            end = clip.find(".//CurrentEnd")
            if end is not None:
                val = end.get("Value")
                if val:
                    end_times.append(float(val))
        
        # Also check MainSequencer
        for clip in root.findall(".//MainSequencer//Events/*"):
            end = clip.find(".//CurrentEnd") 
            if end is not None:
                val = end.get("Value")
                if val:
                    end_times.append(float(val))
        
        # Get length in bars (assuming 4 beats per bar)
        if end_times:
            max_beats = max(end_times)
            self.arrangement_length_bars = round(max_beats / 4, 1)
        
        self.has_arrangement = self.arrangement_length_bars > 0
        
        # Count scenes (session view)
        self.scene_count = len(root.findall(".//Scene"))
        
        # Count clips
        self.total_clips = len(root.findall(".//ClipSlot//AudioClip")) + \
                          len(root.findall(".//ClipSlot//MidiClip")) + \
                          len(root.findall(".//MainSequencer//AudioClip")) + \
                          len(root.findall(".//MainSequencer//MidiClip"))

    def _extract_markers(self, root):
        """Extract arrangement markers/locators ✨"""
        markers = []
        
        for locator in root.findall(".//Locator"):
            name_elem = locator.find(".//Name")
            if name_elem is not None:
                name = name_elem.get("Value", "")
                if name:
                    markers.append(name)
        
        self.markers = markers
        self.marker_count = len(markers)

    def _count_automation(self, root):
        """Count automation envelopes ✨"""
        self.automation_lane_count = len(root.findall(".//AutomationEnvelope"))

    def _extract_samples(self, root):
        """Extract sample file references and check for missing ✨"""
        sample_paths = []
        missing_samples = []
        
        # Find all file references
        for file_ref in root.findall(".//SampleRef//FileRef"):
            # Get the path
            path_elem = file_ref.find(".//Path")
            if path_elem is not None:
                path = path_elem.get("Value", "")
                if path:
                    sample_paths.append(path)
                    
                    # Check if file exists (for local paths)
                    if not path.startswith(("http://", "https://")):
                        # Try to resolve the path
                        if not Path(path).exists():
                            # Also check relative to project
                            project_dir = Path(self.filepath).parent
                            relative_path = project_dir / Path(path).name
                            if not relative_path.exists():
                                missing_samples.append(path)
        
        # Also check HasRelativePath entries
        for file_ref in root.findall(".//FileRef"):
            rel_path = file_ref.find(".//RelativePath")
            if rel_path is not None:
                # Has relative path components
                path_parts = []
                for part in rel_path.findall(".//RelativePathElement"):
                    dir_name = part.get("Dir", "")
                    if dir_name:
                        path_parts.append(dir_name)
                if path_parts:
                    sample_paths.append("/".join(path_parts))
        
        self.sample_paths = list(set(sample_paths))  # Dedupe
        self.missing_samples = list(set(missing_samples))
        self.sample_count = len(self.sample_paths)
        self.missing_sample_count = len(self.missing_samples)

    def _generate_hashes(self, root):
        """Generate content hashes for duplicate detection ✨"""
        # Content hash: based on track structure
        content_str = f"bpm:{self.bpm}|tracks:{self.track_count}|"
        content_str += "|".join(self.track_names[:10])  # First 10 track names
        content_str += "|" + "|".join(self.master_chain[:5])  # First 5 master devices
        self.content_hash = hashlib.md5(content_str.encode()).hexdigest()[:12]
        
        # MIDI pattern hash: based on MIDI note events
        midi_events = root.findall(".//MidiNoteEvent")
        midi_str = f"events:{len(midi_events)}|"
        # Sample some note data for the hash
        for event in midi_events[:50]:  # First 50 events
            pitch = event.get("NoteId", "")
            midi_str += pitch
        self.midi_pattern_hash = hashlib.md5(midi_str.encode()).hexdigest()[:12]

    def _count_heavy_plugins(self):
        """Count CPU-intensive plugins ✨"""
        count = 0
        for plugin_type, plugin_name in self.plugins:
            for heavy in HEAVY_PLUGINS:
                if heavy.lower() in plugin_name.lower():
                    count += 1
                    break
        self.heavy_plugin_count = count

    def _extract_builtin_devices(self, root):
        """List all Ableton built-in devices used ✨"""
        builtin_tags = [
            'Eq8', 'Compressor2', 'GlueCompressor', 'Limiter', 'Saturator',
            'AutoFilter', 'Reverb', 'Delay', 'PingPongDelay', 'FilterDelay',
            'Chorus2', 'Flanger', 'Phaser', 'Redux2', 'Vinyl', 'Amp', 'Cabinet',
            'Overdrive', 'Pedal', 'Utility', 'MultibandDynamics', 'Gate',
            'Echo', 'DrumBuss', 'Corpus', 'Resonators', 'Vocoder',
            'OriginalSimpler', 'MultiSampler', 'InstrumentVector', 'Drift',
            'Operator', 'Analog', 'Collision', 'StringStudio', 'LoungeLizard'
        ]
        
        found = set()
        for tag in builtin_tags:
            if root.find(f".//{tag}") is not None:
                found.add(tag)
        
        self.builtin_devices = list(found)

    def _assess_completion(self):
        """Assess whether project is likely finished ✨"""
        indicators = 0
        
        # Has arrangement markers?
        if self.marker_count >= 3:
            indicators += 1
        
        # Has master chain with multiple devices?
        if len(self.master_chain) >= 2:
            indicators += 1
        
        # Arrangement is long enough? (> 64 bars = ~2 min at 120bpm)
        if self.arrangement_length_bars > 64:
            indicators += 1
        
        # Has multiple scenes?
        if self.scene_count >= 5:
            indicators += 1
        
        # Has decent track count?
        if self.track_count >= 8:
            indicators += 1
        
        # 3+ indicators suggests likely finished
        self.likely_finished = indicators >= 3
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            # Basic info
            'filename': self.filename,
            'filepath': self.filepath,
            'folder': self.folder,
            'last_modified': self.last_modified,
            'size_mb': self.size_mb,
            
            # Core analysis
            'bpm': self.bpm,
            'track_count': self.track_count,
            'audio_tracks': self.audio_tracks,
            'midi_tracks': self.midi_tracks,
            'plugin_count': self.plugin_count,
            
            # Enhanced features
            'track_names': self.track_names,
            'track_details': self.track_details,
            'master_chain': self.master_chain,
            'frozen_track_count': self.frozen_track_count,
            
            # Arrangement
            'arrangement_length_bars': self.arrangement_length_bars,
            'scene_count': self.scene_count,
            'markers': self.markers,
            'marker_count': self.marker_count,
            'automation_lane_count': self.automation_lane_count,
            'total_clips': self.total_clips,
            
            # Hashes
            'content_hash': self.content_hash,
            'midi_pattern_hash': self.midi_pattern_hash,
            
            # Complexity
            'heavy_plugin_count': self.heavy_plugin_count,
            'builtin_devices': self.builtin_devices,
            
            # Completion
            'has_arrangement': self.has_arrangement,
            'has_master_chain': self.has_master_chain,
            'likely_finished': self.likely_finished,
            
            # Samples
            'sample_count': self.sample_count,
            'missing_sample_count': self.missing_sample_count,
            'missing_samples': self.missing_samples[:10],  # First 10 only
        }


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


# =============================================================================
# MCP SERVER TOOLS (for Claude Desktop integration)
# =============================================================================

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
            description="Deep analysis of specific projects. Returns BPM, track details, plugins, master chain, markers, arrangement length, completion status, and more.",
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
                    result_lines.append(f"   🎵 BPM: {proj.bpm}")
                result_lines.append(f"   🎚️  Tracks: {proj.track_count} ({proj.audio_tracks} audio, {proj.midi_tracks} MIDI)")
                
                # Track names
                if proj.track_names:
                    result_lines.append(f"   📝 Track names: {', '.join(proj.track_names[:8])}")
                    if len(proj.track_names) > 8:
                        result_lines.append(f"      ... and {len(proj.track_names) - 8} more")
                
                # Master chain
                if proj.master_chain:
                    result_lines.append(f"   🔊 Master chain: {' → '.join(proj.master_chain)}")
                
                # Plugins
                if proj.plugin_count > 0:
                    result_lines.append(f"   🔌 Plugins: {proj.plugin_count} third-party")
                    unique_plugins = {}
                    for plugin_type, plugin_name in proj.plugins:
                        if plugin_name not in unique_plugins:
                            unique_plugins[plugin_name] = plugin_type
                    for plugin_name, plugin_type in list(unique_plugins.items())[:10]:
                        result_lines.append(f"      • {plugin_name} ({plugin_type})")
                    if len(unique_plugins) > 10:
                        result_lines.append(f"      ... and {len(unique_plugins) - 10} more")
                
                # Arrangement info
                if proj.arrangement_length_bars > 0:
                    result_lines.append(f"   📐 Arrangement: {proj.arrangement_length_bars} bars")
                if proj.markers:
                    result_lines.append(f"   🏷️  Markers: {', '.join(proj.markers)}")
                if proj.scene_count > 0:
                    result_lines.append(f"   🎬 Scenes: {proj.scene_count}")
                
                # Complexity
                if proj.frozen_track_count > 0:
                    result_lines.append(f"   ❄️  Frozen tracks: {proj.frozen_track_count}")
                if proj.heavy_plugin_count > 0:
                    result_lines.append(f"   🔥 Heavy plugins: {proj.heavy_plugin_count}")
                
                # Missing samples
                if proj.missing_sample_count > 0:
                    result_lines.append(f"   ⚠️  Missing samples: {proj.missing_sample_count}")
                    for sample in proj.missing_samples[:5]:
                        result_lines.append(f"      • {sample}")
                
                # Completion
                status = "✅ Likely finished" if proj.likely_finished else "🚧 Work in progress"
                result_lines.append(f"   {status}")
                
                # Hashes for duplicate detection
                result_lines.append(f"   🔑 Content hash: {proj.content_hash}")
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
