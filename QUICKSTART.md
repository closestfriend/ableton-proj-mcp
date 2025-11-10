# Quick Start Guide

## 3-Minute Setup

### Step 1: Download and Install

1. **Download this repository** to your computer
   - Click the green "Code" button → Download ZIP
   - Or use git clone if you're familiar with git

2. **Install uv** (Python package manager)
   - Open Terminal (Applications → Utilities → Terminal)
   - Paste this command and press Enter:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Step 2: Configure Claude Desktop

1. **Open Terminal** (Applications → Utilities → Terminal)

2. **Open the Claude Desktop configuration file:**
   ```bash
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   If the file doesn't exist, create it first:
   ```bash
   mkdir -p ~/Library/Application\ Support/Claude
   touch ~/Library/Application\ Support/Claude/claude_desktop_config.json
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

3. **Configure the server:**

   **If the file is empty or new**, paste this entire configuration:
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

   **If you already have MCP servers configured**, your file will look like this:
   ```json
   {
     "mcpServers": {
       "some-other-server": {
         ...
       }
     }
   }
   ```

   Just add the `music-manager` entry inside the `mcpServers` section (add a comma after the previous server):
   ```json
   {
     "mcpServers": {
       "some-other-server": {
         ...
       },
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

4. **Find your installation path:**
   - Open Terminal
   - Navigate to the folder where you downloaded this tool (use `cd` command)
   - Type `pwd` and press Enter
   - Copy the path that appears
   - Replace `/absolute/path/to/ableton-proj-mcp` in the config with this path

5. **Save the file** and close it

### Step 3: Restart Claude Desktop

Quit Claude Desktop completely (Cmd+Q) and reopen it.

### Step 4: Test It

Ask Claude:

> "What are my 5 most recent Ableton projects in ~/Music/Ableton?"

(Replace `~/Music/Ableton` with wherever you keep your Ableton projects)

---

## First Time Using?

### Good Directories to Scan

✅ **Safe**: Specific project folders
- `~/Music/Ableton/Current`
- `~/Documents/Music/2025 Projects`

⚠️ **Careful**: Very large folders
- Your entire `Music` folder (might hit the 100 file limit)
- External drives with thousands of projects

❌ **Don't Scan**:
- Root directory (`/`)
- Your entire user folder
- Backup drives with duplicates

### Common Paths

Where are your Ableton projects? Common locations:
- `~/Music/Ableton/Projects`
- `~/Documents/Ableton Projects`
- `/Volumes/External/Music Production`

**Tip:** `~` is shorthand for `/Users/yourname`

Not sure? Ask Claude to help you find them!

---

## Example Conversation

**You**: "Scan ~/Music/Ableton for Ableton projects"

**Claude**: [calls scan_projects, shows 47 projects]

**You**: "Show me the 10 most recent"

**Claude**: [calls find_recent, shows top 10 with dates]

**You**: "Analyze the top 3 and tell me which has the most tracks"

**Claude**: [calls analyze_projects, compares, gives recommendation]

---

## Troubleshooting

### "Tool not found" or "Server not connected"
- Make sure you **completely quit** Claude Desktop (Cmd+Q) after editing the config
- Check that the path in the config matches where you downloaded this tool
- Verify the path by running `pwd` in the tool's directory
- Try closing and reopening Terminal, then retry the `uv` installation

### "command not found: uv"
- The uv installation didn't work or isn't in your PATH
- Close and reopen Terminal
- Try running the installation command again
- Or install with: `pip3 install uv`

### "No projects found"
- Double-check the path you're scanning (use full path like `/Users/yourname/Music/Ableton`)
- Make sure it contains .als files
- Try listing files: `ls ~/Music/Ableton` in Terminal to verify
- Try a more specific subfolder

### "Permission denied"
- The scanner can't access that folder
- Make sure you have read permission for the directory
- Don't scan system folders or protected directories

### Need Help?
Ask Claude! It can help debug, adjust settings, or find your projects.
