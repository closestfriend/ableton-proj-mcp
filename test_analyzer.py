#!/usr/bin/env python3
"""
Test the enhanced Ableton analyzer locally! ✨
Run this to see all the detective features in action!
"""

from enhanced_analyzer import EnhancedAbletonAnalyzer, compare_projects
import json
from pathlib import Path

def test_single_project(filepath):
    """Test analysis on a single project"""
    print(f"\n{'='*60}")
    print(f"🔍 ANALYZING: {Path(filepath).name}")
    print('='*60)
    
    analyzer = EnhancedAbletonAnalyzer(filepath)
    result = analyzer.analyze()
    
    print(f"\n📊 BASIC INFO:")
    print(f"  BPM: {result.bpm}")
    print(f"  Tracks: {result.track_count} total ({result.audio_tracks} audio, {result.midi_tracks} MIDI)")
    print(f"  Arrangement: {result.arrangement_length_bars} bars")
    
    print(f"\n🎛️ MASTER CHAIN:")
    if result.master_chain:
        for i, device in enumerate(result.master_chain, 1):
            print(f"  {i}. {device}")
    else:
        print("  No master chain devices")
    
    print(f"\n🔌 PLUGINS:")
    print(f"  Third-party: {len(result.third_party_plugins)} plugins")
    print(f"  Heavy plugins: {result.heavy_plugin_count}")
    if result.third_party_plugins[:5]:  # Show first 5
        print(f"  Examples: {', '.join(result.third_party_plugins[:5])}")
    
    print(f"\n🎵 TRACK DETAILS (first 5):")
    for track in result.tracks[:5]:
        frozen_indicator = " ❄️" if track.is_frozen else ""
        print(f"  • {track.name} ({track.track_type}){frozen_indicator}")
        if track.devices:
            print(f"    Devices: {' → '.join(track.devices[:3])}")
    
    print(f"\n📍 MARKERS:")
    if result.markers:
        print(f"  {', '.join(result.markers)}")
    else:
        print("  No markers")
    
    print(f"\n✅ COMPLETION ASSESSMENT:")
    print(f"  Likely finished? {'YES! 🎉' if result.likely_finished else 'Not yet...'}")
    print(f"  Has arrangement: {result.has_arrangement_view}")
    print(f"  Has master chain: {result.has_master_chain}")
    print(f"  Automation lanes: {result.automation_lane_count}")
    
    print(f"\n🔑 CONTENT HASH: {result.content_hash}")
    print(f"🎹 MIDI HASH: {result.midi_pattern_hash}")
    
    return result

def test_duplicate_detection(proj1_path, proj2_path):
    """Compare two projects for duplicates"""
    print(f"\n{'='*60}")
    print("🔍 DUPLICATE DETECTION")
    print('='*60)
    
    analyzer1 = EnhancedAbletonAnalyzer(proj1_path)
    analyzer2 = EnhancedAbletonAnalyzer(proj2_path)
    
    result1 = analyzer1.analyze()
    result2 = analyzer2.analyze()
    
    comparison = compare_projects(result1, result2)
    
    print(f"\nComparing:")
    print(f"  1. {Path(proj1_path).name}")
    print(f"  2. {Path(proj2_path).name}")
    
    print(f"\n📊 SIMILARITY SCORE: {comparison['similarity_score']}%")
    print(f"\nMATCHES:")
    print(f"  Structure hash: {'✅' if comparison['same_structure_hash'] else '❌'}")
    print(f"  MIDI patterns: {'✅' if comparison['same_midi_patterns'] else '❌'}")
    print(f"  Track count: {'✅' if comparison['track_count_match'] else '❌'}")
    print(f"  BPM: {'✅' if comparison['bpm_match'] else '❌'}")
    print(f"  Master chain: {'✅' if comparison['master_chain_match'] else '❌'}")
    
    if comparison['likely_duplicate']:
        print("\n⚠️ LIKELY DUPLICATE DETECTED!")
    else:
        print("\n✅ These appear to be different projects")

if __name__ == "__main__":
    # Test with your projects!
    test_dir = "/Users/hnsk/Projects/Audio-Production/test-ableton-batch"
    
    projects = [
        f"{test_dir}/worth_saving_claim_it Project/worth_saving_claim_it.als",
        f"{test_dir}/lil_flash_djagainagain Project/lil_flash_djagainagain.als",
        f"{test_dir}/lobby_crazy Project/lobby_crazy.als"
    ]
    
    # Test single project analysis
    for project_path in projects:
        if Path(project_path).exists():
            test_single_project(project_path)
    
    # Test duplicate detection (comparing first two)
    if len(projects) >= 2 and all(Path(p).exists() for p in projects[:2]):
        test_duplicate_detection(projects[0], projects[1])
    
    print("\n" + "="*60)
    print("✨ Analysis complete! ✨")
    print("="*60)
