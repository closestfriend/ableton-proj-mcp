#!/usr/bin/env python3
"""
Quick test to verify the Gradio app dependencies and setup
Run this before launching the full app
"""

import sys

def check_dependencies():
    """Check if all required packages are installed"""
    missing = []
    
    try:
        import gradio
        print(f"✓ Gradio {gradio.__version__} installed")
    except ImportError:
        missing.append("gradio")
        print("✗ Gradio not found")
    
    try:
        import plotly
        print(f"✓ Plotly {plotly.__version__} installed")
    except ImportError:
        missing.append("plotly")
        print("✗ Plotly not found")
    
    # Check MCP backend
    try:
        from music_mcp import SafeAbletonProject, safe_scan_directory
        print("✓ MCP backend (music_mcp.py) accessible")
    except ImportError as e:
        print(f"✗ MCP backend import failed: {e}")
        missing.append("music_mcp")
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        print("  pip install -r requirements-gradio.txt")
        return False
    else:
        print("\n✅ All dependencies installed! Ready to run:")
        print("  python app.py")
        return True

if __name__ == "__main__":
    success = check_dependencies()
    sys.exit(0 if success else 1)
