# Music Project Manager MCP

A Model Context Protocol (MCP) server for safely scanning and analyzing Ableton Live projects.

## Features

- 🔍 **Safe Scanning**: Built-in limits prevent scanning massive directories
- 📊 **Project Analysis**: Extract BPM, track counts, and metadata
- 🕒 **Recent Projects**: Find what you've been working on lately
- ⚡ **Fast**: Only analyzes what you ask for

## Safety Features

- **File Limit**: Stops after 100 .als files (configurable)
- **Size Limit**: Skips files over 50MB (configurable)
- **Depth Limit**: Only scans 3 folders deep (configurable)
- **Smart Skipping**: Ignores common heavy folders (Backup, Samples, Library, etc.)

## Installation

1. **Install MCP Python SDK**:
   ```bash
   pip install mcp
   ```

2. **Add to Claude Desktop Config**:
   
   Open `~/Library/Application Support/Claude/claude_desktop_config.json` and add:
   
   ```json
   {
     "mcpServers": {
       "music-manager": {
         "command": "python3",
         "args": ["/absolute/path/to/ableton-proj-mcp/music_mcp.py"]
       }
     }
   }
   ```

   Replace `/absolute/path/to/` with your actual path to where you cloned this repo.

3. **Restart Claude Desktop**

## Usage

Once installed, you can ask Claude things like:

- "Scan my Ableton projects in ~/Music/Ableton"
- "What are my 5 most recent projects?"
- "Analyze these specific projects and show me their BPM and track counts"

### Example Commands

```
You: Show me my recent music projects in ~/Music/Ableton
Claude: [calls find_recent tool]

You: Analyze the top 3 and tell me which one I should finish
Claude: [calls analyze_projects with those paths]
```

## Tools Available

### `scan_projects`
Scans a directory for all .als files and returns basic info (name, date, size).

**Input**: `directory` (string) - Path to scan

**Safety**: Stops at 100 files, skips large files, limited depth

### `analyze_projects`
Deep analysis of specific projects to extract BPM, track counts, etc.

**Input**: `project_paths` (array of strings) - Paths from scan results

**Safety**: Max 20 projects per call

### `find_recent`
Quick way to find recently modified projects.

**Input**: 
- `directory` (string) - Path to scan
- `limit` (integer, optional) - Number to return (default: 10)

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
- Only works with files accessible to Claude Desktop
- Temp files are always cleaned up, even on error

## Next Steps

Future enhancements could include:
- Completion score estimation
- Plugin/sample inventory
- Project comparison
- Direct Ableton integration
- Export to JSON for other tools

---

## Contributing

Issues and pull requests welcome! This is my first MCP server, so feedback is appreciated.

## License

MIT License - see LICENSE file for details
