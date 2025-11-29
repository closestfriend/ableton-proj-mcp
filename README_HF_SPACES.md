---
title: Ableton Project Manager
emoji: 🎹
colorFrom: gray
colorTo: purple
sdk: gradio
sdk_version: "5.6.0"
app_file: app_hackathon.py
pinned: false
license: mit
tags:
  - building-mcp-track-productivity
  - mcp-server
  - gradio
  - music
  - ableton
  - audio
short_description: MCP server for analyzing Ableton Live projects
---

# Ableton Project Manager

**An MCP server that enables LLMs to analyze Ableton Live project files.**

🎯 **Track:** Building MCP → Productivity  
🔗 **Social Post:** [Coming soon]  
🎬 **Demo Video:** [Coming soon]

---

## What It Does

This tool parses Ableton Live `.als` files (gzipped XML) and extracts:

- **BPM / Tempo**
- **Track counts** (Audio, MIDI, Frozen)
- **Plugin inventory** (VST3, VST2, AU with instance counts)
- **Project metadata** (size, modification date, folder structure)

LLMs can use these tools to answer questions like:
- "Which of my projects use Serum?"
- "Find my 140 BPM tracks"
- "What are my most recent works-in-progress?"

---

## MCP Tools

Connect to this server at: `https://[space-url]/gradio_api/mcp/sse`

| Tool | Description |
|------|-------------|
| `mcp_scan_projects` | Discover all .als files in a directory |
| `mcp_analyze_projects` | Deep analysis of specific project files |
| `mcp_find_recent_projects` | Find recently modified projects |
| `mcp_analyze_uploaded_file` | Analyze a single uploaded file |

### Example MCP Client Config

```json
{
  "mcpServers": {
    "ableton-manager": {
      "url": "https://YOUR-SPACE.hf.space/gradio_api/mcp/sse"
    }
  }
}
```

---

## Try It

1. **Upload** your `.als` files using the web interface
2. **Enable Deep Analysis** to extract BPM and plugins
3. **View** the project cards and BPM distribution chart

---

## Technical Details

- **File Format:** Ableton .als files are gzip-compressed XML
- **Parsing:** Uses Python's `gzip` + `xml.etree.ElementTree`
- **Safety Limits:** Max 100 files, 50MB per file, 3 subdirectory depth
- **Plugins Detected:** VST3, VST2, Audio Units

---

## Built With

- [Gradio](https://gradio.app) - UI framework with MCP support
- [Plotly](https://plotly.com/python/) - BPM distribution charts
- [MCP](https://modelcontextprotocol.io) - Model Context Protocol

---

## Author

Built by [@closestfriend](https://huggingface.co/closestfriend) for MCP's 1st Birthday Hackathon 🎂

