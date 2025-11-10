# Ableton Project MCP Server

[![GitHub stars](https://img.shields.io/github/stars/closestfriend/ableton-proj-mcp?style=social)](https://github.com/closestfriend/ableton-proj-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io)

Model Context Protocol (MCP) server for analyzing Ableton Live project files. Provides Claude with the ability to extract and analyze project metadata, including BPM, track structure, plugin usage, device chains, and sample integrity.

## What is this?

This tool allows Claude (the AI assistant) to read and analyze your Ableton Live project files. It works by:
1. Installing a "server" (background helper) on your computer
2. Connecting it to the Claude Desktop app
3. Enabling Claude to answer questions like "Which of my projects use the most plugins?" or "Find my unfinished tracks"

**Important:** Your project files stay on your computer. This tool reads them locally and gives Claude the information - nothing is uploaded to the cloud.

**What are .als files?** These are Ableton Live Set files (the main project files you open in Ableton). This tool reads these files to extract information without opening Ableton.

**Recommended:** Pair this with the [filesystem MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) for the best experience in Claude Desktop. The filesystem server lets Claude browse your directories and locate project files, which it can then analyze using this tool. This combination enables natural conversations like "find my recent projects and analyze the ones with the most plugins."

## What Problems Does This Solve?

**Missing Sample Recovery:**
Extracts complete file paths from project XML. Paired with the filesystem MCP, Claude can search your drives and locate samples even if they've been renamed or moved. Structured JSON output includes every missing file path, making batch recovery or relinking straightforward.

**Plugin Inventory:**
Extracts complete plugin lists (VST3/VST2/AU) with instance counts from project files without opening Ableton. Useful for system migrations, checking project portability, or locating projects that use specific plugins.

**BPM and Technical Metadata:**
Query projects by BPM, track count, arrangement length, or automation lane count without opening Ableton. Structured JSON output suitable for scripting or spreadsheet analysis.

**Duplicate Detection by Content:**
Compares project content (track structure, device chains, MIDI patterns) rather than filenames. Identifies duplicate projects regardless of naming scheme.

**Master Chain Analysis:**
Extracts and compares mastering device chains across projects. Groups projects by shared master processing.

**Natural Language + Structured Data:**
Conversational queries return structured JSON. Example: "find my 140 BPM projects with Serum that have missing samples" returns JSON with file paths. Export to CSV, pipe into scripts, or use filesystem MCP for file operations. Combines natural language interface with machine-readable output.

## Installation

### Prerequisites

**System Requirements:**
- macOS (tested on macOS 10.15+)
- Claude Desktop app installed
- Python 3.10 or higher (usually pre-installed on modern macOS)

**To check your Python version:**
1. Open Terminal (Applications → Utilities → Terminal)
2. Type: `python3 --version`
3. You should see "Python 3.10" or higher

If you don't have Python 3.10+, download it from [python.org](https://www.python.org/downloads/)

**Install uv package manager:**

This tool requires `uv` - a modern Python package manager that handles all the technical dependencies automatically (you won't need to manage Python versions or packages yourself).

Install `uv` by pasting this command into your Terminal:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Note for macOS users:** Terminal can be found in Applications → Utilities → Terminal

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

**To find your installation path:**
1. Open Terminal
2. Navigate to where you downloaded/cloned this repository
3. Type `pwd` and press Enter
4. Copy the path that appears (e.g., `/Users/yourname/Downloads/ableton-proj-mcp`)
5. Use this path in the configuration above

**Example:** If `pwd` shows `/Users/jane/Projects/ableton-proj-mcp`, your config should be:
```json
"args": [
  "tool",
  "run",
  "--from",
  "/Users/jane/Projects/ableton-proj-mcp",
  "music-manager-mcp"
]
```

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
