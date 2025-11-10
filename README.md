# Ableton Project MCP Server

[![GitHub stars](https://img.shields.io/github/stars/closestfriend/ableton-proj-mcp?style=social)](https://github.com/closestfriend/ableton-proj-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io)

Model Context Protocol (MCP) server for analyzing Ableton Live project files. Provides Claude with the ability to extract and analyze project metadata, including BPM, track structure, plugin usage, device chains, and sample integrity.

## Features

- **Project Scanning**: Recursively scan directories for .als files with configurable safety limits
- **Deep Analysis**: Extract BPM, track counts, arrangement structure, automation, and markers
- **Device Detection**: Identify and categorize stock Ableton devices vs third-party VST/AU plugins
- **Plugin Analysis**: Detect VST3, VST2, and AU plugins with instance counts
- **Sample Integrity**: Check for missing audio file references
- **Duplicate Detection**: Compare projects by content similarity
- **Master Chain Analysis**: Extract and compare mastering device chains
- **Project Classification**: Heuristic-based identification of finished vs sketch projects

## Installation

### Prerequisites

Install `uv` package manager:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Configuration

Add to Claude Desktop configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "music-manager": {
      "command": "uv",
      "args": [
        "tool",
        "run",
        "--from",
        "/absolute/path/to/ableton-proj-mcp",
        "music-manager-mcp"
      ]
    }
  }
}
```

Replace `/absolute/path/to/ableton-proj-mcp` with the repository path.

Restart Claude Desktop to load the server.

## Available Tools

### Core Tools

#### `scan_projects`
Scan directory for .als files and return basic metadata.

**Input:**
- `directory` (string): Path to scan

**Output:**
- Project name, folder, size, modification date
- Safety limits applied automatically

**Safety Limits:**
- Max 100 files (configurable via `MAX_FILES_TO_SCAN`)
- Skip files > 50MB (configurable via `MAX_FILE_SIZE_MB`)
- Max depth: 3 subdirectories (configurable via `SCAN_DEPTH`)

#### `analyze_projects`
Deep analysis of project files. Parses gzipped XML to extract comprehensive metadata.

**Input:**
- `project_paths` (array): List of absolute .als file paths

**Output:**
```json
{
  "basic_info": {
    "bpm": 140.0,
    "track_count": 15,
    "audio_tracks": 6,
    "midi_tracks": 9,
    "frozen_tracks": 2
  },
  "structure": {
    "arrangement_length_bars": 128,
    "scene_count": 8,
    "markers": ["INTRO", "DROP", "OUTRO"],
    "automation_lanes": 24,
    "total_clips": 45
  },
  "devices": {
    "stock_ableton": ["Eq8", "Compressor2", "Reverb"],
    "third_party_vsts": ["Serum 2", "OTT", "ShaperBox 3"],
    "heavy_cpu_count": 3
  },
  "master_chain": ["Eq8", "GlueCompressor", "Limiter"],
  "completion": {
    "likely_finished": true,
    "has_arrangement": true,
    "has_master_chain": true
  }
}
```

**Supported Devices:**
- Stock: All Ableton Live instruments, effects, and utility devices
- VST3: Full name extraction from plugin metadata
- VST2: Legacy plugin format support
- AU: Audio Units (macOS)

#### `find_recent`
Find recently modified projects, sorted by modification time.

**Input:**
- `directory` (string): Path to scan
- `limit` (integer, optional): Number of results (default: 10)

**Output:** List of most recent projects with metadata

### Enhanced Analysis Tools

#### `find_duplicates`
Content-based duplicate detection using structural hashing.

**Similarity Factors:**
- Track structure hash: 40%
- Track count match: 15%
- BPM match: 10%
- Master chain match: 20%
- MIDI pattern hash: 15%

**Input:**
- `directory` (string): Path to scan
- `threshold` (number, optional): Similarity percentage (default: 80)

#### `find_missing_plugins`
Enumerate all third-party plugins used across projects.

**Output:**
- List of unique plugins found
- Projects using each plugin
- Note: Does not verify system installation

#### `find_missing_samples`
Scan projects for broken audio file references.

**Input:**
- `directory` (string): Path to scan

**Output:**
```json
{
  "projects_with_issues": [
    {
      "name": "project.als",
      "missing_count": 5,
      "total_samples": 20,
      "missing_samples": ["/path/to/missing.wav"]
    }
  ],
  "total_missing_samples": 142
}
```

#### `analyze_master_chains`
Extract and compare mastering device chains across projects.

**Input:**
- `project_paths` (array): List of .als file paths

**Output:** Groups projects by unique master chain configurations

#### `find_finished_projects`
Classify projects as finished or sketches using heuristics.

**Completion Indicators (requires 3+ for "finished"):**
- Has 3+ arrangement markers
- Has 2+ devices on master track
- Arrangement length > 64 bars
- Has 5+ session view scenes

## Technical Details

### File Format
Ableton .als files are gzip-compressed XML documents. The server:
1. Decompresses files using gzip
2. Parses XML with ElementTree
3. Extracts data from LiveSet structure
4. Returns structured JSON

### Device Detection
Stock devices are identified by XML tag names. Third-party plugins are parsed from `PluginDevice` elements:
- VST3: `Vst3PluginInfo/Name`
- VST2: `VstPluginInfo/PlugName`
- AU: `AuPluginInfo/Name`

### Performance
- Scans: ~100ms per project (metadata only)
- Deep analysis: ~200-500ms per project (full XML parse)
- Batch operations use safety limits to prevent timeouts

## Configuration

Edit constants in `src/music_manager_mcp/__main__.py`:

```python
MAX_FILES_TO_SCAN = 100  # Maximum files per scan
MAX_FILE_SIZE_MB = 50    # Skip files larger than this
SCAN_DEPTH = 3           # Maximum subdirectory depth
```

## Supported Data

**Extracted:**
- BPM, track counts (audio/MIDI/frozen)
- Arrangement length, scenes, markers
- All devices (stock and third-party)
- Master chain device order
- Automation lane count
- Clip count
- Sample file references
- Content hashes for duplicate detection

**Not Currently Extracted:**
- MIDI note data
- Audio clip waveforms
- Plugin parameter values
- Routing/send configurations
- Clip envelopes

## Troubleshooting

**No projects found:** Verify directory path and .als file presence

**Analysis timeout:** Reduce batch size or increase `MAX_FILES_TO_SCAN`

**Missing plugin names:** Ensure project is from Ableton Live 11+

**Large file skipped:** Increase `MAX_FILE_SIZE_MB` or analyze individually

## Contributing

Pull requests welcome. Please ensure:
- Code follows existing style
- New features include tests
- Documentation is updated

## License

MIT License - see LICENSE file for details
