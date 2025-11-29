# Example Ableton Projects

This directory contains example Ableton Live projects for demonstrating the analysis features.

## For Hackathon Judges

If you're reviewing this submission, you can:

1. **Try the web UI**: Visit the HuggingFace Space and click "Example Projects"
2. **Upload your own**: Use the "Upload Files" tab to test with your projects
3. **Connect via MCP**: Add the Space URL to your Claude Desktop config

## Adding Example Projects

To add example projects for demo purposes:

1. Place .als files in this directory
2. Include varied projects to showcase different features:
   - Different BPMs (120, 130, 140, etc.)
   - Different track counts (minimal to complex)
   - Different plugin usage
   - Different completion states

### Recommended Examples

For a complete demo, include:
- **Techno_138BPM.als** - Heavy plugin usage, many tracks
- **Ambient_75BPM.als** - Minimal, atmospheric
- **House_124BPM.als** - Moderate complexity
- **Experimental_95BPM.als** - Unusual tempo
- **Almost_Done.als** - Well-structured with arrangement markers

## File Size Considerations

For HuggingFace Spaces deployment:
- Keep individual files under 10MB if possible
- Total examples directory should be under 50MB
- The analyzer reads .als files directly (they're gzipped XML)

## Privacy Note

Only include projects you have rights to share publicly. Do not include:
- Projects with copyrighted samples
- Unreleased commercial work
- Projects with sensitive/personal content
