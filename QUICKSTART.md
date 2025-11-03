# Quick Start Guide

## 3-Minute Setup

### Step 1: Install MCP
```bash
pip install mcp
```

### Step 2: Add to Claude Config

1. Open your Claude Desktop config:
   ```bash
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Copy the contents from `example_config.json` in this folder

3. If you already have other MCPs, add the `music-manager` entry to your existing `mcpServers` object

4. Save and close the file

### Step 3: Restart Claude Desktop

Quit Claude Desktop completely and reopen it.

### Step 4: Test It

Come back to this chat and ask me:

> "What are my 5 most recent Ableton projects in /Users/hnsk/WERK?"

(Replace `/Users/hnsk/WERK` with wherever you keep your Ableton projects)

---

## First Time Using?

### Good Directories to Scan

✅ **Safe**: Specific project folders
- `/Users/hnsk/WERK/Current`
- `/Users/hnsk/Music/2025 Projects`

⚠️ **Careful**: Very large folders
- Your entire `Music` folder (might hit the 100 file limit)
- External drives with thousands of projects

❌ **Don't Scan**:
- Root directory (`/`)
- Your entire user folder
- Backup drives with duplicates

### Common Paths

Where are your Ableton projects? Common locations:
- `/Users/hnsk/WERK`
- `/Users/hnsk/Music/Ableton/Projects`
- `/Users/hnsk/Documents/Ableton Projects`
- `/Volumes/External/Music Production`

Not sure? Ask me to list directories and we'll find them!

---

## Example Conversation

**You**: "Scan /Users/hnsk/WERK for Ableton projects"

**Claude**: [calls scan_projects, shows 47 projects]

**You**: "Show me the 10 most recent"

**Claude**: [calls find_recent, shows top 10 with dates]

**You**: "Analyze the top 3 and tell me which has the most tracks"

**Claude**: [calls analyze_projects, compares, gives recommendation]

---

## Troubleshooting

### "Tool not found" or "Server not connected"
- Make sure you restarted Claude Desktop AFTER editing the config
- Check that the path in the config matches this file's location
- Try `python3 --version` in terminal to confirm Python 3 is installed

### "No projects found"
- Double-check the path you're scanning
- Make sure it contains .als files
- Try a more specific subfolder

### Need Help?
Just ask me! I can help debug, adjust settings, or find your projects.
