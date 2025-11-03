#!/usr/bin/env python3
"""
Quick switcher between basic and enhanced MCP versions
Run this to update your Claude config! ✨
"""

import json
from pathlib import Path

def update_claude_config(use_enhanced=True):
    """Update the Claude config to use enhanced version"""
    
    config_path = Path.home() / ".config" / "claude-desktop" / "claude_desktop_config.json"
    
    if not config_path.exists():
        print(f"❌ Config not found at {config_path}")
        return
    
    # Read current config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Find our MCP entry
    mcp_name = "music-manager"
    mcp_found = False
    
    if "mcpServers" in config:
        if mcp_name in config["mcpServers"]:
            # Update the command to use enhanced version
            if use_enhanced:
                config["mcpServers"][mcp_name]["command"] = "python3"
                config["mcpServers"][mcp_name]["args"] = [
                    "/Users/hnsk/Projects/ableton-proj-mcp/music_mcp_enhanced.py"
                ]
                print(f"✅ Updated to use ENHANCED version with detective features!")
            else:
                config["mcpServers"][mcp_name]["command"] = "python3"
                config["mcpServers"][mcp_name]["args"] = [
                    "/Users/hnsk/Projects/ableton-proj-mcp/music_mcp.py"
                ]
                print(f"✅ Updated to use BASIC version")
            
            mcp_found = True
    
    if not mcp_found:
        print(f"❌ MCP '{mcp_name}' not found in config")
        print("Add it first with:")
        print(f"""
  "mcpServers": {{
    "music-manager": {{
      "command": "python3",
      "args": ["/Users/hnsk/Projects/ableton-proj-mcp/music_mcp_enhanced.py"]
    }}
  }}
        """)
        return
    
    # Write updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n📝 Config updated at: {config_path}")
    print("\n⚠️ IMPORTANT: Restart Claude Desktop for changes to take effect!")
    
    # Show new features
    if use_enhanced:
        print("\n🎉 NEW DETECTIVE FEATURES AVAILABLE:")
        print("  • find_duplicates - Find duplicate projects by content")
        print("  • find_missing_plugins - Find projects with missing VSTs")
        print("  • analyze_master_chains - Compare master chains")
        print("  • find_finished_projects - Detect completed vs sketch projects")
        print("  • Deep track analysis with device chains")
        print("  • Content hashing for true duplicate detection")

if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("🎹 ABLETON MCP VERSION SWITCHER 🎹")
    print("="*60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "basic":
        print("\nSwitching to BASIC version...")
        update_claude_config(use_enhanced=False)
    else:
        print("\nSwitching to ENHANCED version with detective features...")
        update_claude_config(use_enhanced=True)
    
    print("\n💡 TIP: Run './test_analyzer.py' to test locally first!")
