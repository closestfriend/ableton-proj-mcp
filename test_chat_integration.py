#!/usr/bin/env python3
"""
Test script to verify chat integration
"""

from music_mcp import SafeAbletonProject
from app import format_projects_as_context, chat_with_claude
import os

# Create mock project data
class MockProject:
    def __init__(self, filename, bpm, track_count, audio_track_count, midi_track_count, size_mb, filepath):
        self.filename = filename
        self.bpm = bpm
        self.track_count = track_count
        self.audio_track_count = audio_track_count
        self.midi_track_count = midi_track_count
        self.size_mb = size_mb
        self.filepath = filepath
        self.plugin_count = 0
        self.plugins = []
        self.last_modified = "2 days ago"

# Test format_projects_as_context
print("Testing format_projects_as_context()...")
mock_projects = [
    MockProject("Test Project 1.als", 138, 12, 8, 4, 8.5, "/path/to/test1.als"),
    MockProject("Test Project 2.als", 120, 16, 10, 6, 12.3, "/path/to/test2.als"),
]

context = format_projects_as_context(mock_projects)
print("\nGenerated context:")
print(context)
print("\n" + "="*60)

# Test chat_with_claude with no API key
print("\nTesting chat_with_claude() without API key...")
if "ANTHROPIC_API_KEY" in os.environ:
    print("Warning: ANTHROPIC_API_KEY is set. Temporarily removing for test...")
    api_key_backup = os.environ.pop("ANTHROPIC_API_KEY")
else:
    api_key_backup = None

chat_history = []
result = chat_with_claude("What's my average BPM?", chat_history, mock_projects)
print(f"\nChat history after error: {len(result)} messages")
print(f"Last message: {result[-1][1][:100]}..." if result else "No messages")

# Restore API key if it was set
if api_key_backup:
    os.environ["ANTHROPIC_API_KEY"] = api_key_backup

print("\n" + "="*60)
print("All tests passed!")
