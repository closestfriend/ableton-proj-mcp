# Music Project Manager MCP

[![GitHub stars](https://img.shields.io/github/stars/closestfriend/ableton-proj-mcp?style=social)](https://github.com/closestfriend/ableton-proj-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0-green.svg)](https://modelcontextprotocol.io)

A Model Context Protocol (MCP) server that gives Claude deep insight into your Ableton Live projects. More than just a file scanner - it's an intelligent music project analyst that helps you make creative decisions.

## Features

- 🔍 **Safe Scanning**: Built-in limits prevent scanning massive directories
- 📊 **Deep Analysis**: Extract BPM, track counts, plugin usage, and metadata
- 🎛️ **Plugin Detection**: Discover which VST/AU plugins are used in each project
- 🕒 **Smart Discovery**: Find recent projects or search by musical characteristics
- 🧠 **AI-Powered Insights**: Claude can interpret data to answer creative questions
- ⚡ **Fast**: Only analyzes what you ask for

## Safety Features

- **File Limit**: Stops after 100 .als files (configurable)
- **Size Limit**: Skips files over 50MB (configurable)
- **Depth Limit**: Only scans 3 folders deep (configurable)
- **Smart Skipping**: Ignores common heavy folders (Backup, Samples, Library, etc.)

## Installation

1. **Ensure you have `uv` installed**:
   ```bash
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Add to Claude Desktop Config**:

   Open `~/Library/Application Support/Claude/claude_desktop_config.json` and add:

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

   Replace `/absolute/path/to/ableton-proj-mcp` with your actual path to where you cloned this repo.

3. **Restart Claude Desktop**

## Usage

This isn't just a file scanner - Claude can answer **creative and analytical questions** about your music projects:

### Creative Decision-Making
- "Which of my unfinished projects has the most potential?"
- "Find projects similar to [project name] based on BPM and plugin usage"
- "Analyze my last 10 projects and suggest which one to finish based on complexity"
- "What's my typical project structure? (average tracks, common BPMs)"

### Plugin Intelligence
- "Which projects use Serum?"
- "Show me all projects that use [specific plugin]"
- "What are my most-used plugins across all projects?"
- "Find projects with more than 5 different plugins"
- "Which projects only use stock Ableton devices?"

### Workflow Analysis
- "Find my most complex project from the last month"
- "Show me small projects (< 5MB) I haven't touched in a while"
- "Group my projects by BPM ranges (120-130, 130-140, etc.)"
- "Find all projects with more than 10 MIDI tracks"

### Basic Queries
- "Scan my Ableton projects in ~/Music/Ableton"
- "What are my 5 most recent projects?"
- "Show me projects modified this week"

### How It Works

```
You: Find all my projects that use Serum and have a BPM around 140

Claude: Let me scan your projects and analyze them...
[calls find_recent or scan_projects]
[calls analyze_projects on the results]
[filters and interprets the data]

Claude: I found 8 projects using Serum. Here are the 3 with BPM closest to 140:
1. "Dark Techno Idea" - 138 BPM, 7 Serum instances
2. "Bass Experiment" - 142 BPM, 3 Serum instances
3. "Club Track Draft" - 140 BPM, 5 Serum instances

Based on the track counts and plugin usage, "Dark Techno Idea" looks
most developed and might be worth finishing first.
```

## Tools Available

### `scan_projects`
Scans a directory for all .als files and returns basic info (name, date, size).

**Input**: `directory` (string) - Path to scan

**Output**: List of projects with filename, folder, last modified date, and size

**Safety**: Stops at 100 files, skips large files, limited depth

### `analyze_projects`
Deep analysis of specific projects to extract detailed musical information.

**Input**: `project_paths` (array of strings) - Paths from scan results

**Output**: For each project:
- BPM (tempo)
- Track counts (total, audio, MIDI)
- Plugin inventory (VST3/AU/VST2)
- Plugin instance counts
- File metadata

**Safety**: Max 20 projects per call

### `find_recent`
Quick way to find recently modified projects.

**Input**:
- `directory` (string) - Path to scan
- `limit` (integer, optional) - Number to return (default: 10)

**Output**: List of most recently modified projects, sorted by date

## Configuration

Edit the constants at the top of `music_mcp.py`:

```python
MAX_FILES_TO_SCAN = 100  # Increase if you need more
MAX_FILE_SIZE_MB = 50    # Raise if you have larger projects
SCAN_DEPTH = 3           # Go deeper into folders
```

## Troubleshooting

**"Found 0 projects"**: Check the path is correct and contains .als files

**"Hit safety limit"**: Increase `MAX_FILES_TO_SCAN` or scan a more specific folder

**"File too large"**: Increase `MAX_FILE_SIZE_MB` or skip that project

**"Analysis failed"**: File might be corrupted or from a very old/new Ableton version

## Technical Notes

- Ableton .als files are gzipped XML
- Analysis requires temporary file extraction
- Plugin detection works with VST3, AU (Audio Units), and VST2 formats
- Extracts data from the LiveSet XML structure
- Only works with files accessible to Claude Desktop
- Temp files are always cleaned up, even on error

## What Can Be Analyzed

**Currently Supported:**
- ✅ BPM/Tempo
- ✅ Track counts (Audio, MIDI, Total)
- ✅ Plugin names and types (VST3/AU/VST2)
- ✅ Plugin instance counts
- ✅ File metadata (size, modification date)

**Potential Future Enhancements:**
- Missing plugin detection (compare against installed plugins)
- Effects chain order and routing
- Completion score estimation
- Sample file inventory
- Project comparison tools
- Export to JSON for external tools
- Clip and automation analysis

---

## Contributing

Issues and pull requests welcome! This is my first MCP server, so feedback is appreciated.

## License

MIT License - see LICENSE file for details
