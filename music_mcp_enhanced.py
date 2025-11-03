#!/usr/bin/env python3
"""
Enhanced Music Project Manager MCP
Now with FULL detective capabilities! ✨
Hunter can see EVERYTHING inside .als files!
"""

from mcp.server import Server
import mcp.server.stdio
import mcp.types as types
import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Import our enhanced analyzer
from enhanced_analyzer import (
    EnhancedAbletonAnalyzer,
    ProjectStructure, 
    compare_projects,
    calculate_similarity
)

server = Server("music-manager")

# SAFETY LIMITS
MAX_FILES_TO_SCAN = 100
MAX_FILE_SIZE_MB = 50
SCAN_DEPTH = 3

@server.list_tools()
async def list_tools():
    """List all available music management tools"""
    return [
        types.Tool(
            name="scan_projects",
            description="Scan a directory for Ableton projects",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to scan"}
                },
                "required": ["directory"]
            }
        ),
        types.Tool(
            name="analyze_projects",
            description="Deep analysis of Ableton projects (plugins, structure, completion)",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of .als file paths"
                    }
                },
                "required": ["project_paths"]
            }
        ),
        types.Tool(
            name="find_duplicates",
            description="Find duplicate projects based on content, not just filename",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to scan"},
                    "threshold": {
                        "type": "number",
                        "description": "Similarity threshold (0-100)",
                        "default": 80
                    }
                },
                "required": ["directory"]
            }
        ),
        types.Tool(
            name="find_missing_plugins",
            description="Find projects using plugins you don't have installed",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to scan"}
                },
                "required": ["directory"]
            }
        ),
        types.Tool(
            name="analyze_master_chains",
            description="Extract and compare master chains across projects",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of .als file paths"
                    }
                },
                "required": ["project_paths"]
            }
        ),
        types.Tool(
            name="find_finished_projects",
            description="Detect which projects are likely finished vs sketches",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to scan"}
                },
                "required": ["directory"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    
    if name == "scan_projects":
        return await scan_projects(arguments.get("directory"))
        
    elif name == "analyze_projects":
        return await analyze_projects(arguments.get("project_paths"))
        
    elif name == "find_duplicates":
        return await find_duplicates(
            arguments.get("directory"),
            arguments.get("threshold", 80)
        )
        
    elif name == "find_missing_plugins":
        return await find_missing_plugins(arguments.get("directory"))
        
    elif name == "analyze_master_chains":
        return await analyze_master_chains(arguments.get("project_paths"))
        
    elif name == "find_finished_projects":
        return await find_finished_projects(arguments.get("directory"))
        
    return {"error": f"Unknown tool: {name}"}

async def scan_projects(directory: str):
    """Basic scan - quick overview"""
    projects = []
    scanned = 0
    
    for root, _, files in os.walk(directory):
        # Check depth
        depth = root[len(directory):].count(os.sep)
        if depth > SCAN_DEPTH:
            continue
            
        for file in files:
            if file.endswith('.als'):
                if scanned >= MAX_FILES_TO_SCAN:
                    break
                    
                filepath = os.path.join(root, file)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                
                if size_mb <= MAX_FILE_SIZE_MB:
                    projects.append({
                        'path': filepath,
                        'name': file,
                        'size_mb': round(size_mb, 2),
                        'modified': datetime.datetime.fromtimestamp(
                            os.path.getmtime(filepath)
                        ).strftime("%Y-%m-%d %H:%M")
                    })
                    scanned += 1
    
    return {
        'found': len(projects),
        'projects': projects,
        'truncated': scanned >= MAX_FILES_TO_SCAN
    }

async def analyze_projects(project_paths: List[str]):
    """Deep analysis with our enhanced analyzer! ✨"""
    results = []
    
    for path in project_paths:
        try:
            analyzer = EnhancedAbletonAnalyzer(path)
            analysis = analyzer.analyze()
            
            # Convert to dict for JSON serialization
            result = {
                'project': os.path.basename(path),
                'path': path,
                'bpm': analysis.bpm,
                'tracks': {
                    'total': analysis.track_count,
                    'audio': analysis.audio_tracks,
                    'midi': analysis.midi_tracks,
                    'frozen': analysis.frozen_track_count
                },
                'master_chain': analysis.master_chain,
                'plugins': {
                    'third_party': analysis.third_party_plugins,
                    'heavy_count': analysis.heavy_plugin_count,
                    'missing': analysis.missing_plugins
                },
                'structure': {
                    'bars': analysis.arrangement_length_bars,
                    'scenes': analysis.scene_count,
                    'markers': analysis.markers,
                    'automation_lanes': analysis.automation_lane_count
                },
                'completion': {
                    'likely_finished': analysis.likely_finished,
                    'has_arrangement': analysis.has_arrangement_view,
                    'has_master_chain': analysis.has_master_chain
                },
                'hashes': {
                    'structure': analysis.content_hash,
                    'midi': analysis.midi_pattern_hash
                }
            }
            
            # Add track details
            track_details = []
            for track in analysis.tracks[:10]:  # Limit to first 10 for readability
                track_details.append({
                    'name': track.name,
                    'type': track.track_type,
                    'devices': track.devices[:5],  # First 5 devices
                    'frozen': track.is_frozen
                })
            result['track_details'] = track_details
            
            results.append(result)
            
        except Exception as e:
            results.append({
                'project': os.path.basename(path),
                'error': str(e)
            })
    
    return {'analyzed': len(results), 'results': results}

async def find_duplicates(directory: str, threshold: float = 80):
    """Find duplicate projects based on actual content!"""
    # First, scan all projects
    projects_data = await scan_projects(directory)
    project_paths = [p['path'] for p in projects_data['projects']]
    
    # Analyze all projects
    analyzed = {}
    for path in project_paths:
        try:
            analyzer = EnhancedAbletonAnalyzer(path)
            analyzed[path] = analyzer.analyze()
        except:
            continue
    
    # Compare all pairs
    duplicates = []
    paths = list(analyzed.keys())
    
    for i, path1 in enumerate(paths):
        for path2 in paths[i+1:]:
            comparison = compare_projects(analyzed[path1], analyzed[path2])
            
            if comparison['similarity_score'] >= threshold:
                duplicates.append({
                    'project1': os.path.basename(path1),
                    'project2': os.path.basename(path2),
                    'similarity': comparison['similarity_score'],
                    'same_structure': comparison['same_structure_hash'],
                    'same_midi': comparison['same_midi_patterns'],
                    'details': comparison
                })
    
    return {
        'scanned': len(analyzed),
        'duplicates_found': len(duplicates),
        'threshold': threshold,
        'duplicates': duplicates
    }

async def find_missing_plugins(directory: str):
    """Find projects using plugins that might not be installed"""
    projects_data = await scan_projects(directory)
    project_paths = [p['path'] for p in projects_data['projects']]
    
    plugin_usage = {}  # plugin_name -> list of projects using it
    all_plugins = set()
    
    for path in project_paths:
        try:
            analyzer = EnhancedAbletonAnalyzer(path)
            analysis = analyzer.analyze()
            
            for plugin in analysis.third_party_plugins:
                all_plugins.add(plugin)
                if plugin not in plugin_usage:
                    plugin_usage[plugin] = []
                plugin_usage[plugin].append(os.path.basename(path))
                
        except:
            continue
    
    # Check which plugins might be missing (simplified check)
    # In reality, we'd check VST folders, but for now we'll flag suspicious ones
    potentially_missing = []
    
    for plugin in all_plugins:
        # If a plugin name contains certain keywords, it might be missing
        suspicious = ['crack', 'demo', 'trial', '(1)', 'copy']
        if any(s in plugin.lower() for s in suspicious):
            potentially_missing.append({
                'plugin': plugin,
                'used_in': plugin_usage[plugin][:5],  # First 5 projects
                'total_projects': len(plugin_usage[plugin])
            })
    
    return {
        'total_plugins': len(all_plugins),
        'potentially_missing': len(potentially_missing),
        'plugins': potentially_missing,
        'all_third_party': list(all_plugins)[:20]  # First 20
    }

async def analyze_master_chains(project_paths: List[str]):
    """Compare master chains across projects"""
    chains = {}
    
    for path in project_paths:
        try:
            analyzer = EnhancedAbletonAnalyzer(path)
            analysis = analyzer.analyze()
            
            chain_str = ' → '.join(analysis.master_chain) if analysis.master_chain else "No master chain"
            
            if chain_str not in chains:
                chains[chain_str] = []
            chains[chain_str].append(os.path.basename(path))
            
        except:
            continue
    
    # Group by similarity
    return {
        'unique_chains': len(chains),
        'chains': [
            {
                'chain': chain,
                'projects': projects,
                'count': len(projects)
            }
            for chain, projects in chains.items()
        ]
    }

async def find_finished_projects(directory: str):
    """Detect which projects are likely finished"""
    projects_data = await scan_projects(directory)
    project_paths = [p['path'] for p in projects_data['projects']]
    
    finished = []
    sketches = []
    
    for path in project_paths:
        try:
            analyzer = EnhancedAbletonAnalyzer(path)
            analysis = analyzer.analyze()
            
            project_info = {
                'name': os.path.basename(path),
                'path': path,
                'bars': analysis.arrangement_length_bars,
                'markers': analysis.markers,
                'has_master': analysis.has_master_chain,
                'track_count': analysis.track_count
            }
            
            if analysis.likely_finished:
                finished.append(project_info)
            else:
                sketches.append(project_info)
                
        except:
            continue
    
    return {
        'total_scanned': len(project_paths),
        'likely_finished': len(finished),
        'likely_sketches': len(sketches),
        'finished_projects': finished[:10],  # Top 10
        'sketch_projects': sketches[:10]     # Top 10
    }

async def main():
    """Run the enhanced MCP server"""
    await server.run(
        mcp.server.stdio.create_stdio_streams()
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
