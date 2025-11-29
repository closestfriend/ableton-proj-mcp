# Ableton Project Manager - Gradio Interface

Beautiful web interface for the Ableton MCP Server, featuring Swiss-inspired design with frosted glass aesthetics.

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements-gradio.txt
```

2. **Run the app:**
```bash
python app.py
```

3. **Open in browser:**
The app will launch at `http://localhost:7860`

## Features

- **Project Scanning**: Browse all .als files in a directory with safety limits
- **Deep Analysis**: Extract BPM, track counts, and plugin usage
- **Recent Projects**: Quickly find your most recently modified projects
- **BPM Visualization**: Interactive Plotly chart showing tempo distribution
- **Beautiful UI**: Custom Swiss-inspired design with:
  - Frosted glass effects (`backdrop-filter: blur`)
  - Muted color palette
  - Refined typography (Cormorant Garamond, Space Mono, Inter)
  - Subtle Swiss grid lines
  - Smooth hover animations

## Design Philosophy

The interface draws from Swiss design principles:
- **Grid-based layout** with subtle reference lines
- **Hierarchy through typography** rather than color
- **Whitespace as a design element**
- **Functional beauty** - every element serves a purpose

Color palette:
- Background: `#e8e8e8`, `#f5f5f5` (soft grays)
- Elements: `#5a5a6a`, `#4a4a5a` (muted blue-grays)
- Text: `#2a2a2a`, `#3a3a3a` (dark grays)
- Accents: `rgba(100, 100, 120, 0.08)` (subtle highlights)

## Usage Tips

- **Deep Analysis is slower** - it parses XML from each .als file
- **Without Deep Analysis** - shows file metadata only (fast)
- **BPM chart** - only appears when Deep Analysis is enabled
- **Safety limits** - max 100 files, 50MB file size, 3 folders deep

## Tech Stack

- **Gradio 6** - Web UI framework
- **Plotly** - Interactive data visualization
- **Custom CSS** - Frosted glass, Swiss typography
- **Backend** - Existing MCP server (`music_mcp.py`)

## For Hackathon Submission

This is the Gradio wrapper version for **Track 2: MCP in Action (Productivity Agents)**.

The standalone MCP server (`music_mcp.py`) is for **Track 1: Building MCP (Productivity)**.

Both submissions demonstrate different aspects of the same core technology.
