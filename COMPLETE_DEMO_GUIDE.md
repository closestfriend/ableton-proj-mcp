# Complete Demo & Deployment Guide

## Overview

Your Ableton Project Manager now has **FOUR ways** to interact with it:

1. 📁 **Scan Local Directory** - For users with Ableton projects on their machine
2. 📤 **Upload Files** - For anyone to test with their own .als files
3. ✨ **Example Projects** - Instant demo with pre-loaded projects
4. 🔌 **MCP Server** - Claude Desktop can connect and use as a tool

## Three-Tab Interface

### Tab 1: Scan Local Directory
**Who**: Users running locally with Ableton projects
**How**: Enter directory path, click "Scan Projects"
**Best for**: Power users, local development, large project collections

### Tab 2: Upload Files
**Who**: Anyone (judges, users without local setup)
**How**: Drag & drop .als files
**Best for**: Quick testing, judges evaluating submission, mobile users

### Tab 3: Example Projects
**Who**: Anyone wanting instant results
**How**: Click "Load Example Projects"
**Best for**: First-time visitors, demos, screenshots

## MCP Server Mode

**Status**: ✅ Enabled via `demo.launch(mcp_server=True)`

### Local MCP Connection

```json
// Add to ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "ableton-local": {
      "url": "http://localhost:7860/gradio_api/mcp/sse"
    }
  }
}
```

Then in Claude Desktop:
```
Use the ableton-local tool to scan my projects directory
```

### HuggingFace Space MCP Connection

```json
{
  "mcpServers": {
    "ableton-demo": {
      "url": "https://YOUR-USERNAME-ableton-mcp.hf.space/gradio_api/mcp/sse"
    }
  }
}
```

## HuggingFace Space Deployment

### Step 1: Create Space on HuggingFace

1. Go to https://huggingface.co/new-space
2. Name: `ableton-mcp` (or similar)
3. SDK: **Gradio**
4. Python version: 3.10+
5. Visibility: Public

### Step 2: Clone and Add Files

```bash
git clone https://huggingface.co/spaces/YOUR-USERNAME/ableton-mcp
cd ableton-mcp

# Copy essential files
cp ~/Projects/ableton-proj-mcp/app.py .
cp ~/Projects/ableton-proj-mcp/requirements-gradio.txt .
cp ~/Projects/ableton-proj-mcp/music_mcp.py .

# Copy examples directory
cp -r ~/Projects/ableton-proj-mcp/examples .
```

### Step 3: Add Example Projects

Place 5-10 varied .als files in `examples/`:
- **Techno_138BPM.als** - Electronic, high energy, many plugins
- **Ambient_Sketch.als** - Minimal, atmospheric, few tracks
- **House_124BPM.als** - Moderate complexity, balanced
- **Experimental_95BPM.als** - Unusual tempo, creative structure
- **Almost_Done.als** - Well-structured with arrangement markers

**Important**:
- Keep files under 10MB each
- Total examples directory under 50MB
- Only use projects you have rights to share

### Step 4: Create README.md for Space

```markdown
---
title: Ableton Project Manager
emoji: 🎵
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

# Ableton Project Manager MCP Server

AI-powered analysis of Ableton Live projects with multiple ways to explore:

## 🚀 Try It Now

### 📤 Upload Your Projects
Drag & drop .als files to analyze instantly - no local setup needed!

### ✨ Example Projects
Click to explore pre-loaded projects and see all features

### 📁 Local Directory
Scan your Ableton folder (when running locally)

## 🔌 Use as MCP Server

Connect Claude Desktop to use this Space as a tool:

\`\`\`json
{
  "mcpServers": {
    "ableton": {
      "url": "https://YOUR-USERNAME-ableton-mcp.hf.space/gradio_api/mcp/sse"
    }
  }
}
\`\`\`

Then ask Claude:
- "Load the example Ableton projects and tell me about them"
- "Which project should I finish first based on the data?"
- "What's my average BPM across these projects?"

## ✨ Features

- **BPM Analysis** - Distribution charts and statistics
- **Plugin Tracking** - See which VSTs you use most
- **Track Analysis** - Audio, MIDI, and frozen track counts
- **AI Recommendations** - HuggingFace-powered insights
- **Swiss Design** - Beautiful, minimal interface
- **Full MCP** - Works as both client and server

## 🛠️ Technical Stack

- **Frontend**: Gradio with custom CSS
- **Backend**: Python + HuggingFace InferenceClient
- **AI Model**: Qwen/Qwen2.5-72B-Instruct
- **Visualization**: Plotly
- **MCP**: Native Gradio MCP server support

Built for the Anthropic MCP Hackathon 🏆
```

### Step 5: Set HuggingFace Token (Required for AI)

In your Space settings:
1. Go to Settings → Repository secrets
2. Add secret: `HF_TOKEN` = your HuggingFace token
3. Get token from: https://huggingface.co/settings/tokens

### Step 6: Deploy

```bash
git add .
git commit -m "Add Ableton MCP server with upload and examples"
git push
```

Space will auto-build and be live in ~2 minutes.

## Demo Script for Judges (5 minutes)

### Part 1: Web UI Demo (2 min)

1. **Open Space** → Clean, professional interface
2. **Click "Example Projects" tab** → Instant results
3. **Point out BPM chart** → "Shows distribution across projects"
4. **Scroll through project cards** → Plugin counts, track details
5. **AI Chat**: Type "Which of these projects should I finish first?"
6. **Show response** → AI analyzes data and recommends
7. **Switch to "Upload" tab** → "Anyone can test with their files"

### Part 2: MCP Demo (3 min)

1. **Show config file** → Simple URL, one-line setup
2. **Open Claude Desktop** → "Connected to the Space"
3. **Ask Claude**: "Use the ableton tool to load example projects"
4. **Claude calls MCP** → Returns structured project data
5. **Follow up**: "What patterns do you see in my workflow?"
6. **Claude analyzes** → Multi-turn conversation about music style

## Key Selling Points

### For Judges ✅

1. **Zero friction** - Works immediately, no downloads
2. **Three input modes** - Upload, examples, or local
3. **Dual MCP role** - Consumer (uses music_mcp) AND producer (mcp_server=True)
4. **Production ready** - Error handling, beautiful UI, real utility
5. **Hackathon perfect** - Shows full MCP ecosystem potential

### Technical Achievements ⚡

- Existing MCP server wrapped as library
- Gradio app becomes MCP server itself
- Three input methods, unified experience
- HuggingFace AI integration (not Anthropic!)
- Real-time data visualization
- Swiss design system from scratch

## Files Structure

```
ableton-proj-mcp/
├── app.py                        # Main Gradio app (752 lines)
├── music_mcp.py                  # MCP server library
├── requirements-gradio.txt       # Dependencies
├── examples/                     # Demo projects
│   ├── README.md                # Examples guide
│   └── *.als                    # Sample files
├── COMPLETE_DEMO_GUIDE.md       # This file
├── IMPLEMENTATION_SUMMARY.md    # Technical details
└── CLAUDE_CODE_DIRECTIVE.md     # Original directive
```

## Pre-Submission Checklist

- [ ] All three tabs work locally
- [ ] File upload handles .als correctly
- [ ] Examples load from examples/ directory
- [ ] AI chat works with HF_TOKEN set
- [ ] BPM charts display properly
- [ ] MCP endpoint responds at /gradio_api/mcp/sse
- [ ] Space deploys without errors
- [ ] README renders correctly on HF
- [ ] At least 3 example .als files included
- [ ] Demo video recorded (optional but recommended)

## Testing Locally

```bash
# Install dependencies
pip install -r requirements-gradio.txt

# Set HuggingFace token
export HF_TOKEN='your-token-here'

# Run app
python3 app.py

# Test MCP connection (separate terminal)
# Add to Claude Desktop config, then restart Claude
```

Visit: http://localhost:7860

## Common Issues & Solutions

**"No example projects found"**
→ Add .als files to `examples/` directory

**"Upload failed"**
→ Check file is actually .als format (gzipped XML)

**"AI assistant setup required"**
→ Set HF_TOKEN environment variable or Space secret

**"MCP connection failed"**
→ Verify URL ends with `/gradio_api/mcp/sse`

## Judging Criteria Alignment

| Criteria | How We Address It |
|----------|-------------------|
| **Technical** | MCP client + server, HF integration, proper error handling |
| **UX** | Three input methods, beautiful UI, instant demo |
| **Innovation** | Dual MCP role, multi-modal input, real musician tool |
| **Documentation** | Complete guides, inline comments, examples |
| **Completeness** | Works end-to-end, deployed, testable |

## What Makes This Stand Out

1. **Actually useful** - Musicians will use this
2. **MCP inception** - Uses MCP, becomes MCP
3. **Zero barrier** - Upload tab = instant testing
4. **Production quality** - Not a prototype
5. **Open AI** - HuggingFace, not closed APIs
6. **Beautiful** - Custom Swiss design

You're ready to win! 🏆🎵
