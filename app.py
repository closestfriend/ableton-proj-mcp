#!/usr/bin/env python3
"""
Ableton Project Manager - MCP Server & Gradio Interface
Track 1: Building MCP - Productivity Category

A Model Context Protocol server that enables LLMs to analyze Ableton Live projects.
Extracts BPM, track counts, plugin inventories, and project metadata from .als files.
"""

import gradio as gr
import html as _html
import os
import sys
from pathlib import Path
import music_mcp
from music_mcp import SafeAbletonProject, safe_scan_directory, MAX_FILES_TO_SCAN, MAX_FILE_SIZE_MB, SCAN_DEPTH
from datetime import datetime
from typing import Optional
from gradio.utils import get_upload_folder

# =============================================================================
# HOSTED-SPACE SAFETY
# The MCP tools below are reachable by anonymous callers and used to take raw
# server-side paths. Anything a caller names must now resolve inside one of these
# roots; everything else gets the same generic answer, so "missing", "exists but
# not allowed" and "wrong type" can't be told apart.
# =============================================================================

EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples")
DENIED_MSG = "Path not found or not allowed. On this Space, only uploaded files and the bundled examples can be analyzed."

# Sample paths inside an uploaded .als describe the uploader's machine, not this server.
music_mcp.VERIFY_SAMPLES_ON_DISK = False


def _resolve_allowed(path, want_dir):
    """Return the real path if it is an allowed .als file (or examples folder), else None.

    Directory scans are limited to the bundled examples: the upload cache holds other
    visitors' files, so it must never be listable. Single files may also come from the
    upload cache (the only way to reach a file you uploaded yourself).
    """
    if not isinstance(path, str) or not path or "\x00" in path:
        return None
    real = os.path.realpath(path)  # resolves "..", "~"-less relative paths and symlinks first
    roots = [EXAMPLES_DIR] if want_dir else [EXAMPLES_DIR, get_upload_folder()]
    if not any(_is_within(real, os.path.realpath(root)) for root in roots):
        return None
    if want_dir:
        return real if os.path.isdir(real) else None
    return real if os.path.isfile(real) and real.lower().endswith(".als") else None


def _is_within(path, root):
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:  # e.g. different drives
        return False


def _generic_error(exc):
    """Log the real exception server-side; hand callers a fixed message."""
    print(f"tool error: {exc!r}", file=sys.stderr)
    return "Analysis failed"

# =============================================================================
# MCP TOOL FUNCTIONS (exposed to LLMs via gr.api())
# These functions return structured JSON data for machine consumption
# =============================================================================

def mcp_scan_projects(directory: str) -> dict:
    """Scan a directory for Ableton Live project files (.als).
    
    Discovers all Ableton projects in the specified directory and subdirectories,
    returning basic metadata without deep analysis. Use this for initial discovery
    before calling mcp_analyze_projects on specific files.
    
    Args:
        directory: Full path to the folder containing .als project files.
                   Example: "/Users/musician/Music/Ableton/Projects"
    
    Returns:
        Dictionary containing:
        - projects: List of project objects with name, path, folder, size_mb, last_modified
        - count: Total number of projects found
        - hit_limit: Boolean indicating if scan limit was reached
        - scanned_directory: The directory that was scanned
    """
    if not directory:
        return {"error": "No directory provided", "projects": [], "count": 0}
    
    expanded_path = _resolve_allowed(directory, want_dir=True)
    if expanded_path is None:
        return {"error": DENIED_MSG, "projects": [], "count": 0}
    
    try:
        projects, hit_limit = safe_scan_directory(expanded_path)
        
        return {
            "projects": [
                {
                    "name": p.filename,
                    "path": p.filepath,
                    "folder": p.folder,
                    "size_mb": p.size_mb,
                    "last_modified": p.last_modified
                }
                for p in projects
            ],
            "count": len(projects),
            "hit_limit": hit_limit,
            "scanned_directory": directory,
            "limits": {
                "max_files": MAX_FILES_TO_SCAN,
                "max_file_size_mb": MAX_FILE_SIZE_MB,
                "max_depth": SCAN_DEPTH
            }
        }
    except Exception as e:
        return {"error": _generic_error(e), "projects": [], "count": 0}


def mcp_analyze_projects(project_paths: list[str]) -> dict:
    """Perform deep analysis on specific Ableton Live project files.
    
    Parses the internal XML structure of .als files to extract comprehensive
    metadata including BPM, track details, plugins, master chain, markers,
    arrangement structure, and completion assessment.
    
    Args:
        project_paths: List of full paths to .als files to analyze.
                       Get these paths from mcp_scan_projects results.
                       Maximum 20 projects per call for performance.
    
    Returns:
        Dictionary containing:
        - projects: List of analyzed project objects with full metadata
        - analyzed_count: Number of successfully analyzed projects
        - errors: List of any errors encountered
        
        Each project includes: bpm, track_count, track_names, master_chain,
        markers, arrangement_length_bars, scene_count, plugins, heavy_plugin_count,
        frozen_track_count, missing_samples, likely_finished, content_hash
    """
    if not project_paths:
        return {"error": "No project paths provided", "projects": [], "analyzed_count": 0}
    
    if len(project_paths) > 20:
        return {
            "error": "Maximum 20 projects per analysis call. Please reduce the list.",
            "projects": [],
            "analyzed_count": 0
        }
    
    results = []
    errors = []
    
    for path in project_paths:
        safe_path = _resolve_allowed(path, want_dir=False)
        if safe_path is None:
            errors.append({"path": path, "error": DENIED_MSG})
            continue
        
        try:
            proj = SafeAbletonProject(safe_path)
            success = proj.analyze()
            
            plugin_summary = {}
            if proj.plugin_count > 0:
                for plugin_type, plugin_name in proj.plugins:
                    key = f"{plugin_name} ({plugin_type})"
                    plugin_summary[key] = plugin_summary.get(key, 0) + 1
            
            result = {
                "name": proj.filename,
                "path": proj.filepath,
                "folder": proj.folder,
                "size_mb": proj.size_mb,
                "last_modified": proj.last_modified,
                "analysis_success": success,
                "bpm": proj.bpm,
                "track_count": proj.track_count,
                "audio_tracks": proj.audio_tracks,
                "midi_tracks": proj.midi_tracks,
                "track_names": proj.track_names,
                "frozen_track_count": proj.frozen_track_count,
                "master_chain": proj.master_chain,
                "has_master_chain": proj.has_master_chain,
                "arrangement_length_bars": proj.arrangement_length_bars,
                "scene_count": proj.scene_count,
                "markers": proj.markers,
                "marker_count": proj.marker_count,
                "total_clips": proj.total_clips,
                "plugin_count": proj.plugin_count,
                "plugins": plugin_summary,
                "heavy_plugin_count": proj.heavy_plugin_count,
                "builtin_devices": proj.builtin_devices,
                "sample_count": proj.sample_count,
                "missing_sample_count": proj.missing_sample_count,
                "missing_samples": proj.missing_samples[:10],
                "likely_finished": proj.likely_finished,
                "content_hash": proj.content_hash,
                "midi_pattern_hash": proj.midi_pattern_hash,
            }
            
            if not success and proj.error:
                result["analysis_error"] = proj.error
            
            results.append(result)
            
        except Exception as e:
            errors.append({"path": path, "error": _generic_error(e)})
    
    return {
        "projects": results,
        "analyzed_count": len(results),
        "errors": errors if errors else None
    }


def mcp_find_recent_projects(directory: str, limit: int = 10) -> dict:
    """Find the most recently modified Ableton projects in a directory.
    
    Scans for projects and returns them sorted by modification time,
    with full analysis performed on each. Useful for finding works-in-progress.
    
    Args:
        directory: Full path to the folder to scan.
        limit: Maximum number of recent projects to return (default: 10, max: 20).
    
    Returns:
        Dictionary containing:
        - projects: List of recent projects with full analysis, sorted newest first
        - count: Number of projects returned
        - wip_count: Number of work-in-progress projects
        - finished_count: Number of likely finished projects
    """
    if not directory:
        return {"error": "No directory provided", "projects": [], "count": 0}
    
    expanded_path = _resolve_allowed(directory, want_dir=True)
    if expanded_path is None:
        return {"error": DENIED_MSG, "projects": [], "count": 0}
    
    limit = min(max(1, limit), 20)
    
    try:
        projects, _ = safe_scan_directory(expanded_path)
        
        if not projects:
            return {"projects": [], "count": 0, "scanned_directory": directory}
        
        projects.sort(key=lambda p: os.path.getmtime(p.filepath), reverse=True)
        recent = projects[:limit]
        
        results = []
        wip_count = 0
        finished_count = 0
        
        for proj in recent:
            proj.analyze()
            
            plugin_summary = {}
            if proj.plugin_count > 0:
                for plugin_type, plugin_name in proj.plugins:
                    key = f"{plugin_name} ({plugin_type})"
                    plugin_summary[key] = plugin_summary.get(key, 0) + 1
            
            if proj.likely_finished:
                finished_count += 1
            else:
                wip_count += 1
            
            results.append({
                "name": proj.filename,
                "path": proj.filepath,
                "folder": proj.folder,
                "size_mb": proj.size_mb,
                "last_modified": proj.last_modified,
                "bpm": proj.bpm,
                "track_count": proj.track_count,
                "audio_tracks": proj.audio_tracks,
                "midi_tracks": proj.midi_tracks,
                "track_names": proj.track_names,
                "master_chain": proj.master_chain,
                "markers": proj.markers,
                "arrangement_length_bars": proj.arrangement_length_bars,
                "scene_count": proj.scene_count,
                "plugin_count": proj.plugin_count,
                "plugins": plugin_summary,
                "heavy_plugin_count": proj.heavy_plugin_count,
                "frozen_track_count": proj.frozen_track_count,
                "missing_sample_count": proj.missing_sample_count,
                "likely_finished": proj.likely_finished,
                "content_hash": proj.content_hash,
            })
        
        return {
            "projects": results,
            "count": len(results),
            "wip_count": wip_count,
            "finished_count": finished_count,
            "scanned_directory": directory
        }
        
    except Exception as e:
        return {"error": _generic_error(e), "projects": [], "count": 0}


def mcp_analyze_uploaded_file(file_path: str) -> dict:
    """Analyze a single uploaded Ableton Live project file.
    
    Performs comprehensive analysis on an uploaded .als file, extracting
    all available metadata including track details, plugins, master chain,
    markers, and completion assessment.
    
    Args:
        file_path: Path to the uploaded .als file (provided by Gradio upload).
    
    Returns:
        Dictionary containing full project analysis:
        - Basic: name, bpm, track_count, size
        - Tracks: track_names, frozen_track_count
        - Structure: arrangement_length_bars, scene_count, markers
        - Audio: master_chain, plugins, heavy_plugin_count
        - Status: likely_finished, missing_samples, content_hash
    """
    if not file_path:
        return {"error": "No file provided"}
    
    safe_path = _resolve_allowed(file_path, want_dir=False)
    if safe_path is None:
        return {"error": DENIED_MSG}
    
    try:
        proj = SafeAbletonProject(safe_path)
        success = proj.analyze()
        
        plugin_summary = {}
        if proj.plugin_count > 0:
            for plugin_type, plugin_name in proj.plugins:
                key = f"{plugin_name} ({plugin_type})"
                plugin_summary[key] = plugin_summary.get(key, 0) + 1
        
        result = {
            "name": proj.filename,
            "size_mb": proj.size_mb,
            "last_modified": proj.last_modified,
            "analysis_success": success,
            "bpm": proj.bpm,
            "track_count": proj.track_count,
            "audio_tracks": proj.audio_tracks,
            "midi_tracks": proj.midi_tracks,
            "track_names": proj.track_names,
            "frozen_track_count": proj.frozen_track_count,
            "master_chain": proj.master_chain,
            "has_master_chain": proj.has_master_chain,
            "arrangement_length_bars": proj.arrangement_length_bars,
            "has_arrangement": proj.has_arrangement,
            "scene_count": proj.scene_count,
            "markers": proj.markers,
            "marker_count": proj.marker_count,
            "total_clips": proj.total_clips,
            "plugin_count": proj.plugin_count,
            "plugins": plugin_summary,
            "unique_plugins": list(set(name for _, name in proj.plugins)) if proj.plugins else [],
            "heavy_plugin_count": proj.heavy_plugin_count,
            "builtin_devices": proj.builtin_devices,
            "sample_count": proj.sample_count,
            "missing_sample_count": proj.missing_sample_count,
            "missing_samples": proj.missing_samples[:10],
            "likely_finished": proj.likely_finished,
            "content_hash": proj.content_hash,
            "midi_pattern_hash": proj.midi_pattern_hash,
        }
        
        if not success and proj.error:
            result["analysis_error"] = proj.error
        
        return result
        
    except Exception as e:
        return {"error": _generic_error(e)}


# =============================================================================
# UI HELPER FUNCTIONS (for the Gradio web interface)
# =============================================================================

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&family=Space+Mono:wght@400;700&family=Cormorant+Garamond:wght@300;400&display=swap');

/* === BASE CONTAINER === */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: linear-gradient(180deg, #f8f8f9 0%, #eeeef0 100%) !important;
    min-height: 100vh;
}

/* === HEADER STYLES === */
.header {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.5rem;
    font-weight: 300;
    letter-spacing: -0.02em;
    color: #2a2a2a;
    margin-bottom: 0.5rem;
}

.subtitle {
    font-size: 0.875rem;
    color: #888;
    font-weight: 300;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 2rem;
    border-bottom: 1px solid rgba(0,0,0,0.08);
    padding-bottom: 1rem;
}

/* === INPUT SECTIONS === */
.input-section {
    background: rgba(255, 255, 255, 0.7) !important;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(200, 200, 210, 0.5) !important;
    border-radius: 12px !important;
    padding: 2rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.03) !important;
}

/* === PROJECT CARDS GRID === */
.projects-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.project-card {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(200, 200, 210, 0.4);
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.3s ease;
    position: relative;
}

.project-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, rgba(90, 90, 110, 0.2) 0%, rgba(90, 90, 110, 0) 100%);
    border-radius: 12px 12px 0 0;
}

.project-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.06);
    border-color: rgba(90, 90, 110, 0.25);
}

.project-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.35rem;
    font-weight: 400;
    color: #2a2a2a;
    margin-bottom: 0.75rem;
    letter-spacing: -0.01em;
}

/* === MCP INFO BOX === */
.mcp-info {
    background: rgba(90, 90, 110, 0.04);
    border: 1px solid rgba(90, 90, 110, 0.1);
    border-radius: 8px;
    padding: 1.5rem;
    margin-top: 2rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    color: #3a3a4a;
}

.mcp-info code {
    background: rgba(0, 0, 0, 0.05);
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
}

/* Force readable text color inside MCP info regardless of theme */
.mcp-info, .mcp-info *, .mcp-info ul, .mcp-info li {
    color: #2f2f3a !important;
}

/* === EXPANDABLE TRACK LISTS === */
.track-expand-btn {
    cursor: pointer;
    color: #6a6a8a;
    font-size: 0.65rem;
    padding: 0.15rem 0;
    transition: color 0.2s;
}

.track-expand-btn:hover {
    color: #4a4a6a;
}

.track-hidden {
    display: none;
}

.track-visible {
    display: block;
}

/* === TAB STYLING === */
.tabs button {
    color: #4a4a5a !important;
}

.tabs button.selected {
    color: #2a2a3a !important;
    font-weight: 500 !important;
}

/* === FILE UPLOAD STYLING === */
.upload-box {
    border: 2px dashed rgba(90, 90, 110, 0.25) !important;
    border-radius: 12px !important;
    background: rgba(250, 250, 252, 0.5) !important;
    transition: all 0.3s ease !important;
    min-height: 180px !important;
}

.upload-box:hover {
    border-color: rgba(90, 90, 110, 0.4) !important;
    background: rgba(250, 250, 252, 0.8) !important;
}

/* Keep file upload area usable after files are added */
.upload-box .file-preview {
    min-height: 120px !important;
}

.upload-box [data-testid="file-upload-area"] {
    min-height: 160px !important;
}

/* === BUTTON TEXT FIX === */
/* Force primary button text to be white for readability */
button.primary,
.primary button,
button[variant="primary"] {
    color: white !important;
}
"""

# Custom theme to replace Gradio's orange defaults
CUSTOM_THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.slate,
    secondary_hue=gr.themes.colors.gray,
    neutral_hue=gr.themes.colors.gray,
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("Space Mono"), "monospace"],
).set(
    # Buttons
    button_primary_background_fill="linear-gradient(135deg, #5a5a6a 0%, #4a4a5a 100%)",
    button_primary_background_fill_hover="linear-gradient(135deg, #6a6a7a 0%, #5a5a6a 100%)",
    button_primary_text_color="white",
    button_secondary_background_fill="rgba(90, 90, 110, 0.08)",
    button_secondary_background_fill_hover="rgba(90, 90, 110, 0.15)",
    button_secondary_text_color="#4a4a5a",
    
    # Inputs
    input_background_fill="rgba(255, 255, 255, 0.8)",
    input_border_color="rgba(200, 200, 210, 0.5)",
    input_border_color_focus="rgba(90, 90, 110, 0.4)",
    
    # Blocks
    block_background_fill="rgba(255, 255, 255, 0.6)",
    block_border_color="rgba(200, 200, 210, 0.4)",
    block_label_background_fill="rgba(250, 250, 252, 0.8)",
    block_title_text_color="#3a3a4a",
    
    # Checkboxes
    checkbox_background_color="rgba(255, 255, 255, 0.9)",
    checkbox_background_color_selected="#5a5a6a",
    checkbox_border_color="rgba(200, 200, 210, 0.6)",
)


def generate_project_card_html(project, analyzed=False):
    """Generate HTML for a single project card"""
    
    # Plugin section
    plugin_html = ""
    if analyzed and project.plugin_count > 0:
        plugin_counts = {}
        for _, plugin_name in project.plugins:
            plugin_counts[plugin_name] = plugin_counts.get(plugin_name, 0) + 1
        
        plugin_tags = []
        for plugin, count in list(plugin_counts.items())[:5]:
            display = _html.escape(f"{plugin} × {count}" if count > 1 else plugin)
            plugin_tags.append(f'<span style="padding: 0.25rem 0.75rem; background: rgba(100, 100, 120, 0.08); border-radius: 6px; font-size: 0.7rem; color: #5a5a6a; margin-right: 0.5rem; margin-bottom: 0.5rem; display: inline-block;">{display}</span>')

        plugin_html = f"""
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(0, 0, 0, 0.06);">
            <div style="font-size: 0.65rem; color: #999; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; font-weight: 500;">Plugins ({project.plugin_count})</div>
            <div style="display: flex; flex-wrap: wrap;">
                {''.join(plugin_tags)}
            </div>
        </div>
        """
    
    # Master chain section
    master_html = ""
    if analyzed and hasattr(project, 'master_chain') and project.master_chain:
        master_devices = ' → '.join(project.master_chain[:6])
        if len(project.master_chain) > 6:
            master_devices += f' (+{len(project.master_chain) - 6})'
        master_devices = _html.escape(master_devices)
        master_html = f"""
        <div style="margin-top: 0.75rem;">
            <div style="font-size: 0.65rem; color: #999; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.25rem; font-weight: 500;">Master Chain</div>
            <div style="font-size: 0.75rem; color: #5a5a6a;">{master_devices}</div>
        </div>
        """
    
    # Markers section
    markers_html = ""
    if analyzed and hasattr(project, 'markers') and project.markers:
        marker_tags = [f'<span style="padding: 0.15rem 0.5rem; background: rgba(80, 120, 100, 0.12); border-radius: 4px; font-size: 0.65rem; color: #4a6a5a; margin-right: 0.4rem; display: inline-block;">{_html.escape(m)}</span>' for m in project.markers[:6]]
        markers_html = f"""
        <div style="margin-top: 0.75rem;">
            <div style="font-size: 0.65rem; color: #999; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.25rem; font-weight: 500;">Markers</div>
            <div>{''.join(marker_tags)}</div>
        </div>
        """
    
    # Track names section — split by type with expandable lists
    tracks_html = ""
    if analyzed and hasattr(project, 'track_details') and project.track_details:
        import random
        card_id = f"card_{random.randint(10000, 99999)}"
        
        midi_tracks = [t['name'] for t in project.track_details if t.get('type') == 'MIDI']
        audio_tracks = [t['name'] for t in project.track_details if t.get('type') == 'Audio']
        
        def build_track_list(tracks, track_type, card_id):
            if not tracks:
                return '<div style="font-size: 0.7rem; color: #bbb;">—</div>'
            
            visible = tracks[:6]
            hidden = tracks[6:]
            list_id = f"{card_id}_{track_type}"
            
            html = ''.join([f'<div style="font-size: 0.7rem; color: #6a6a7a; padding: 0.15rem 0; border-bottom: 1px solid rgba(0,0,0,0.04);">{_html.escape(name)}</div>' for name in visible])
            
            if hidden:
                hidden_html = ''.join([f'<div style="font-size: 0.7rem; color: #6a6a7a; padding: 0.15rem 0; border-bottom: 1px solid rgba(0,0,0,0.04);">{_html.escape(name)}</div>' for name in hidden])
                html += f'''
                <div id="{list_id}_hidden" style="display: none;">{hidden_html}</div>
                <div id="{list_id}_btn" class="track-expand-btn" onclick="
                    var hidden = document.getElementById('{list_id}_hidden');
                    var btn = document.getElementById('{list_id}_btn');
                    if (hidden.style.display === 'none') {{
                        hidden.style.display = 'block';
                        btn.textContent = '▲ collapse';
                    }} else {{
                        hidden.style.display = 'none';
                        btn.textContent = '+{len(hidden)} more';
                    }}
                ">+{len(hidden)} more</div>
                '''
            return html
        
        midi_html = build_track_list(midi_tracks, 'midi', card_id)
        audio_html = build_track_list(audio_tracks, 'audio', card_id)
        
        tracks_html = f"""
        <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(0,0,0,0.06);">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                    <div style="font-size: 0.65rem; color: #888; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; font-weight: 500;">🎹 MIDI ({len(midi_tracks)})</div>
                    {midi_html}
                </div>
                <div>
                    <div style="font-size: 0.65rem; color: #888; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; font-weight: 500;">🎚️ Audio ({len(audio_tracks)})</div>
                    {audio_html}
                </div>
            </div>
        </div>
        """
    
    # Missing samples section
    missing_html = ""
    if analyzed and hasattr(project, 'missing_samples') and project.missing_samples:
        import os
        import random
        missing_id = f"missing_{random.randint(10000, 99999)}"
        
        sample_names = [os.path.basename(p) for p in project.missing_samples]
        visible = sample_names[:5]
        hidden = sample_names[5:]
        
        missing_list = ''.join([f'<div style="font-size: 0.7rem; color: #8a2a2a; padding: 0.15rem 0; border-bottom: 1px solid rgba(200,60,60,0.04); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{_html.escape(project.missing_samples[i])}">{_html.escape(name)}</div>' for i, name in enumerate(visible)])
        
        if hidden:
            hidden_html = ''.join([f'<div style="font-size: 0.7rem; color: #8a2a2a; padding: 0.15rem 0; border-bottom: 1px solid rgba(200,60,60,0.04); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{_html.escape(project.missing_samples[i+5])}">{_html.escape(name)}</div>' for i, name in enumerate(hidden)])
            missing_list += f'''
            <div id="{missing_id}_hidden" style="display: none;">{hidden_html}</div>
            <div id="{missing_id}_btn" class="track-expand-btn" style="color: #a22; font-weight: 500;" onclick="
                var hidden = document.getElementById('{missing_id}_hidden');
                var btn = document.getElementById('{missing_id}_btn');
                if (hidden.style.display === 'none') {{
                    hidden.style.display = 'block';
                    btn.textContent = '▲ collapse';
                }} else {{
                    hidden.style.display = 'none';
                    btn.textContent = '+{len(hidden)} more';
                }}
            ">+{len(hidden)} more</div>
            '''
        
        missing_html = f"""
        <div style="margin-top: 0.75rem; padding: 0.75rem; background: rgba(200, 60, 60, 0.04); border-radius: 8px; border: 1px solid rgba(200, 60, 60, 0.1);">
            <div style="font-size: 0.65rem; color: #8a2a2a; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; font-weight: 600; display: flex; align-items: center;">
                <span style="margin-right: 0.4rem;">⚠️</span> Missing Samples ({len(project.missing_samples)})
            </div>
            {missing_list}
        </div>
        """
    
    # Status badges
    badges_html = ""
    if analyzed:
        badges = []
        if hasattr(project, 'likely_finished') and project.likely_finished:
            badges.append('<span style="padding: 0.2rem 0.5rem; background: rgba(80, 160, 80, 0.15); color: #3a7a3a; border-radius: 4px; font-size: 0.6rem; font-weight: 500;">✓ FINISHED</span>')
        else:
            badges.append('<span style="padding: 0.2rem 0.5rem; background: rgba(180, 140, 60, 0.15); color: #8a6a2a; border-radius: 4px; font-size: 0.6rem; font-weight: 500;">WIP</span>')
        
        if hasattr(project, 'frozen_track_count') and project.frozen_track_count > 0:
            badges.append(f'<span style="padding: 0.2rem 0.5rem; background: rgba(100, 160, 200, 0.15); color: #3a6a8a; border-radius: 4px; font-size: 0.6rem;">❄️ {project.frozen_track_count} frozen</span>')
        
        if hasattr(project, 'heavy_plugin_count') and project.heavy_plugin_count > 0:
            badges.append(f'<span style="padding: 0.2rem 0.5rem; background: rgba(200, 100, 80, 0.15); color: #8a3a2a; border-radius: 4px; font-size: 0.6rem;">⚓️ {project.heavy_plugin_count} heavy</span>')
        
        if hasattr(project, 'missing_sample_count') and project.missing_sample_count > 0:
            badges.append(f'<span style="padding: 0.2rem 0.5rem; background: rgba(200, 60, 60, 0.15); color: #8a2a2a; border-radius: 4px; font-size: 0.6rem;">⚠️ {project.missing_sample_count} missing</span>')
        
        if badges:
            badges_html = f'<div style="display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.75rem;">{" ".join(badges)}</div>'
    
    bpm_value = f"{project.bpm} BPM" if analyzed and project.bpm else "—"
    tracks_value = f"{project.track_count} Total" if analyzed else "—"
    arrangement_value = f"{project.arrangement_length_bars} bars" if analyzed and hasattr(project, 'arrangement_length_bars') and project.arrangement_length_bars > 0 else "—"
    scenes_value = f"{project.scene_count}" if analyzed and hasattr(project, 'scene_count') and project.scene_count > 0 else "—"
    
    return f"""
    <div class="project-card">
        <h3 class="project-title">{_html.escape(project.filename.replace('.als', ''))}</h3>
        {badges_html}
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; margin: 1rem 0;">
            <div>
                <span style="font-size: 0.65rem; color: #999; text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.25rem;">Tempo</span>
                <span style="font-family: 'Space Mono', monospace; font-size: 0.875rem; color: #4a4a5a;">{bpm_value}</span>
            </div>
            <div>
                <span style="font-size: 0.65rem; color: #999; text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.25rem;">Tracks</span>
                <span style="font-family: 'Space Mono', monospace; font-size: 0.875rem; color: #4a4a5a;">{tracks_value}</span>
            </div>
            <div>
                <span style="font-size: 0.65rem; color: #999; text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.25rem;">Arrangement</span>
                <span style="font-family: 'Space Mono', monospace; font-size: 0.875rem; color: #4a4a5a;">{arrangement_value}</span>
            </div>
            <div>
                <span style="font-size: 0.65rem; color: #999; text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.25rem;">Scenes</span>
                <span style="font-family: 'Space Mono', monospace; font-size: 0.875rem; color: #4a4a5a;">{scenes_value}</span>
            </div>
            <div>
                <span style="font-size: 0.65rem; color: #999; text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.25rem;">Modified</span>
                <span style="font-family: 'Space Mono', monospace; font-size: 0.875rem; color: #4a4a5a;">{project.last_modified}</span>
            </div>
            <div>
                <span style="font-size: 0.65rem; color: #999; text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.25rem;">Size</span>
                <span style="font-family: 'Space Mono', monospace; font-size: 0.875rem; color: #4a4a5a;">{project.size_mb} MB</span>
            </div>
        </div>
        {tracks_html}
        {missing_html}
        {master_html}
        {markers_html}
        {plugin_html}
    </div>
    """


def ui_scan_and_display(directory, analyze_all=False):
    """UI handler: Scan directory and return HTML grid"""
    if not directory or not os.path.exists(os.path.expanduser(directory)):
        return "<p style='color: #999; text-align: center; padding: 2rem;'>Please enter a valid directory path</p>"

    try:
        projects, hit_limit = safe_scan_directory(os.path.expanduser(directory))

        if not projects:
            return "<p style='color: #999; text-align: center; padding: 2rem;'>No Ableton projects found in this directory</p>"

        if analyze_all and len(projects) <= 20:
            for proj in projects:
                proj.analyze()

        cards = [generate_project_card_html(proj, analyze_all) for proj in projects]
        html = f'<div class="projects-grid">{"".join(cards)}</div>'
        
        if hit_limit:
            html = f'<p style="color: #888; text-align: center; margin-bottom: 1rem;">⚠️ Showing first {len(projects)} projects (limit reached)</p>' + html

        return html

    except Exception as e:
        return f"<p style='color: #ff6b6b; padding: 2rem;'>{_generic_error(e)}</p>"


def ui_find_recent(directory, limit=10):
    """UI handler: Find recent projects"""
    if not directory or not os.path.exists(os.path.expanduser(directory)):
        return "<p style='color: #999; text-align: center; padding: 2rem;'>Please enter a valid directory path</p>"

    try:
        projects, _ = safe_scan_directory(os.path.expanduser(directory))

        if not projects:
            return "<p style='color: #999; text-align: center; padding: 2rem;'>No projects found</p>"

        projects.sort(key=lambda p: os.path.getmtime(p.filepath), reverse=True)
        recent = projects[:limit]

        for proj in recent:
            proj.analyze()

        cards = [generate_project_card_html(proj, True) for proj in recent]
        return f'<div class="projects-grid">{"".join(cards)}</div>'

    except Exception as e:
        return f"<p style='color: #ff6b6b; padding: 2rem;'>{_generic_error(e)}</p>"


def ui_handle_uploads(files, analyze_all=False):
    """UI handler: Process uploaded files"""
    if not files or len(files) == 0:
        return "<p style='color: #999; text-align: center; padding: 2rem;'>Please upload some .als files</p>"

    try:
        projects = []
        file_list = files if isinstance(files, list) else [files]

        for file_path in file_list:
            if not file_path:
                continue
            try:
                proj = SafeAbletonProject(file_path)
                if analyze_all:
                    proj.analyze()
                projects.append(proj)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue

        if not projects:
            return "<p style='color: #999; text-align: center; padding: 2rem;'>No valid Ableton projects found</p>"

        cards = [generate_project_card_html(proj, analyze_all) for proj in projects]
        html = f'<div class="projects-grid">{"".join(cards)}</div>'

        return html

    except Exception as e:
        return f"<p style='color: #ff6b6b; padding: 2rem;'>{_generic_error(e)}</p>"


def ui_load_examples(analyze_all=False):
    """UI handler: Load example projects"""
    examples_dir = os.path.join(os.path.dirname(__file__), "examples")

    if not os.path.exists(examples_dir):
        return """
        <p style='text-align: center; padding: 2rem; color: #999;'>No examples found. Upload .als files to test.</p>
        """

    try:
        projects, _ = safe_scan_directory(examples_dir)

        if not projects:
            return "<p style='color: #999; text-align: center; padding: 2rem;'>No example projects found</p>"

        if analyze_all:
            for proj in projects:
                proj.analyze()

        cards = [generate_project_card_html(proj, analyze_all) for proj in projects]
        html = f'<div class="projects-grid">{"".join(cards)}</div>'

        return html

    except Exception as e:
        return f"<p style='color: #ff6b6b; padding: 2rem;'>{_generic_error(e)}</p>"


# =============================================================================
# BUILD THE GRADIO APP
# =============================================================================

with gr.Blocks(title="Ableton Project Manager · MCP Server") as demo:
    # Header
    gr.HTML('<h1 class="header">Ableton Project Manager</h1>')
    gr.HTML('<p class="subtitle">MCP Server · Project Analysis & Discovery</p>')

    # Tabbed interface
    with gr.Tabs():
        # Tab 1: Upload Files (primary for HF Spaces)
        with gr.Tab("「Upload Files」"):
            with gr.Group(elem_classes="input-section"):
                gr.Markdown("""
                ### Analyze Your Ableton Projects
                Upload `.als` files to extract BPM, track counts, and plugin inventories.
                """)

                upload_files = gr.File(
                    file_count="multiple",
                    file_types=[".als"],
                    label="Drop .als files here",
                    height=180,
                    elem_classes="upload-box"
                )

                upload_analyze_checkbox = gr.Checkbox(
                    label="Deep Analysis (includes BPM/plugins)",
                    value=True
                )

                upload_btn = gr.Button("Analyze Uploaded Files", variant="primary", size="lg")

        # Tab 2: Example Projects
        with gr.Tab("「Examples」"):
            with gr.Group(elem_classes="input-section"):
                gr.Markdown("""
                ### Try Pre-Loaded Examples
                See how the analysis works with sample projects.
                """)

                examples_analyze_checkbox = gr.Checkbox(
                    label="Deep Analysis",
                    value=True
                )

                examples_btn = gr.Button("Load Examples", variant="primary", size="lg")

    # Output section
    projects_output = gr.HTML()

    # MCP Integration Info
    gr.HTML("""
    <div class="mcp-info">
        <strong style="color: #3a3a4a; font-size: 0.95rem;">MCP Integration</strong>
        <p style="color: #5a5a6a; margin: 0.75rem 0 1rem 0; line-height: 1.6;">
            Exposes .als file metadata via <strong style="color: #4a4a5a;">Model Context Protocol</strong>. Connects to Claude Desktop, Cursor, or other MCP clients. Useful if you have hundreds of project files and have lost track of what's in them.
        </p>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 1rem;">
            <div>
                <strong style="color: #4a4a5a; font-size: 0.8rem;">Available Tools</strong>
                <ul style="margin: 0.5rem 0; padding-left: 1.25rem; color: #5a5a6a; font-size: 0.8rem; line-height: 1.6;">
                    <li><code style="color: #4a4a5a;">mcp_scan_projects</code> — Discover .als files</li>
                    <li><code style="color: #4a4a5a;">mcp_analyze_projects</code> — Deep metadata extraction</li>
                    <li><code style="color: #4a4a5a;">mcp_find_recent_projects</code> — Sort by modification date</li>
                    <li><code style="color: #4a4a5a;">mcp_analyze_uploaded_file</code> — Single file analysis</li>
                </ul>
            </div>
            <div>
                <strong style="color: #4a4a5a; font-size: 0.8rem;">What AI Can Extract</strong>
                <ul style="margin: 0.5rem 0; padding-left: 1.25rem; color: #5a5a6a; font-size: 0.8rem; line-height: 1.6;">
                    <li>BPM, track counts, arrangement length</li>
                    <li>Full plugin inventory + CPU-heavy warnings</li>
                    <li>Master chain device analysis</li>
                    <li>Missing samples detection</li>
                    <li>"Likely finished" completion assessment</li>
                </ul>
            </div>
        </div>
        
        <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid rgba(90, 90, 110, 0.1); font-size: 0.75rem; color: #6a6a7a;">
            <strong style="color: #5a5a6a;">Endpoint:</strong> <code style="color: #4a4a5a;">/gradio_api/mcp/sse</code> · 
            Built with Gradio's native MCP support · 
            <a href="https://modelcontextprotocol.io" target="_blank" style="color: #5a6a8a;">Learn about MCP →</a>
        </div>
    </div>
    """)

    # Footer
    gr.HTML("""
        <div style="text-align: center; margin-top: 3rem; padding-top: 2rem; border-top: 1px solid rgba(0,0,0,0.08);">
            <p style="font-size: 0.75rem; color: #888; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.5rem;">
                Built for MCP's 1st Birthday Hackathon · Gradio
            </p>
            <p style="font-size: 0.7rem; color: #999;">
                by <a href="https://hnsk.site" target="_blank" style="color: #6a6a8a; text-decoration: none;">closestfriend™</a> · 
                <a href="https://github.com/closestfriend" target="_blank" style="color: #6a6a8a; text-decoration: none;">GitHub</a>
            </p>
        </div>
    """)

    # Event handlers
    upload_btn.click(ui_handle_uploads, [upload_files, upload_analyze_checkbox], [projects_output])
    examples_btn.click(ui_load_examples, [examples_analyze_checkbox], [projects_output])

    # Register MCP-only API functions
    gr.api(mcp_scan_projects)
    gr.api(mcp_analyze_projects)
    gr.api(mcp_find_recent_projects)
    gr.api(mcp_analyze_uploaded_file)


if __name__ == "__main__":
    demo.launch(mcp_server=True, theme=CUSTOM_THEME, css=CUSTOM_CSS)
