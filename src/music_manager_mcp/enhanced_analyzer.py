#!/usr/bin/env python3
"""
Enhanced Ableton Project Analyzer
Deep XML inspection for comprehensive project analysis.
"""

import gzip
import xml.etree.ElementTree as ET
from pathlib import Path
import hashlib
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class TrackInfo:
    """Information about a single track"""
    name: str
    track_type: str  # 'Audio', 'Midi', 'Return', 'Master'
    devices: List[str]
    volume: float
    is_frozen: bool
    color: Optional[int]
    
@dataclass
class PluginInfo:
    """Information about a plugin/device"""
    name: str
    device_type: str  # 'BuiltIn', 'VST', 'AU', 'VST3'
    preset_name: Optional[str]
    is_active: bool

@dataclass  
class ProjectStructure:
    """Complete project analysis results"""
    # Basic info (we already have this)
    filepath: str
    bpm: float
    track_count: int
    audio_tracks: int
    midi_tracks: int
    
    # Enhanced analysis features
    # Track details
    tracks: List[TrackInfo]
    master_chain: List[str]
    return_tracks: List[TrackInfo]
    
    # Plugin analysis
    all_plugins: List[PluginInfo]
    missing_plugins: List[str]  # Plugins that might not be installed
    builtin_devices: List[str]
    third_party_plugins: List[str]
    
    # Arrangement analysis  
    arrangement_length_bars: float
    scene_count: int
    marker_count: int
    markers: List[str]  # Marker names like "DROP", "OUTRO"
    
    # Automation & complexity
    automation_lane_count: int
    total_clips: int
    unique_clips: int
    
    # Duplicate detection helpers
    content_hash: str  # Hash of core structure for duplicate detection
    midi_pattern_hash: str  # Hash of MIDI data
    
    # CPU impact analysis
    heavy_plugin_count: int  # Serum, Omnisphere, etc.
    frozen_track_count: int
    
    # Project "done-ness" indicators
    has_arrangement_view: bool
    has_master_chain: bool
    likely_finished: bool
    
    # Sample/file references
    sample_paths: List[str]
    missing_samples: List[str]

class EnhancedAbletonAnalyzer:
    """The detective that knows all your production secrets! (◕‿◕)♡"""
    
    # Known CPU-heavy plugins
    HEAVY_PLUGINS = {
        'Serum', 'SerumWavetable', 'Vital', 'Omnisphere', 
        'Kontakt', 'Massive', 'Diva', 'Repro', 'Pigments'
    }
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.xml_root = None
        
    def analyze(self) -> ProjectStructure:
        """Perform complete analysis of the .als file"""
        try:
            # Step 1: Decompress and parse XML
            self._load_xml()
            
            # Step 2: Extract all project data
            structure = ProjectStructure(
                filepath=str(self.filepath),
                bpm=self._get_bpm(),
                track_count=self._count_tracks()['total'],
                audio_tracks=self._count_tracks()['audio'],
                midi_tracks=self._count_tracks()['midi'],
                tracks=self._get_all_tracks(),
                master_chain=self._get_master_chain(),
                return_tracks=self._get_return_tracks(),
                all_plugins=self._get_all_plugins(),
                missing_plugins=self._detect_missing_plugins(),
                builtin_devices=self._get_builtin_devices(),
                third_party_plugins=self._get_third_party_plugins(),
                arrangement_length_bars=self._get_arrangement_length(),
                scene_count=self._count_scenes(),
                marker_count=self._count_markers(),
                markers=self._get_marker_names(),
                automation_lane_count=self._count_automation_lanes(),
                total_clips=self._count_clips()['total'],
                unique_clips=self._count_clips()['unique'],
                content_hash=self._generate_content_hash(),
                midi_pattern_hash=self._generate_midi_hash(),
                heavy_plugin_count=self._count_heavy_plugins(),
                frozen_track_count=self._count_frozen_tracks(),
                has_arrangement_view=self._check_arrangement_view(),
                has_master_chain=len(self._get_master_chain()) > 0,
                likely_finished=self._assess_completion(),
                sample_paths=self._get_sample_paths(),
                missing_samples=self._detect_missing_samples()
            )
            
            return structure
            
        except Exception as e:
            logger.error(f"Analysis failed for {self.filepath}: {e}")
            raise
    
    def _load_xml(self):
        """Decompress .als and parse XML"""
        with gzip.open(self.filepath, 'rb') as f:
            xml_content = f.read()
            self.xml_root = ET.fromstring(xml_content)
    
    def _get_bpm(self) -> float:
        """Extract project BPM"""
        tempo = self.xml_root.find('.//Tempo/Manual')
        if tempo is not None and 'Value' in tempo.attrib:
            return float(tempo.attrib['Value'])
        return 120.0  # Default
    
    def _count_tracks(self) -> Dict[str, int]:
        """Count tracks by type"""
        audio_tracks = len(self.xml_root.findall('.//AudioTrack'))
        midi_tracks = len(self.xml_root.findall('.//MidiTrack'))
        return {
            'audio': audio_tracks,
            'midi': midi_tracks,
            'total': audio_tracks + midi_tracks
        }
    
    def _get_all_tracks(self) -> List[TrackInfo]:
        """Get detailed info for every track"""
        tracks = []
        
        # Process MIDI tracks
        for track in self.xml_root.findall('.//MidiTrack'):
            name_elem = track.find('.//EffectiveName')
            name = name_elem.attrib.get('Value', 'Untitled') if name_elem is not None else 'Untitled'
            
            devices = self._get_track_devices(track)
            volume = self._get_track_volume(track)
            is_frozen = self._is_track_frozen(track)
            color = self._get_track_color(track)
            
            tracks.append(TrackInfo(
                name=name,
                track_type='Midi',
                devices=devices,
                volume=volume,
                is_frozen=is_frozen,
                color=color
            ))
        
        # Process Audio tracks  
        for track in self.xml_root.findall('.//AudioTrack'):
            name_elem = track.find('.//EffectiveName')
            name = name_elem.attrib.get('Value', 'Untitled') if name_elem is not None else 'Untitled'
            
            devices = self._get_track_devices(track)
            volume = self._get_track_volume(track)
            is_frozen = self._is_track_frozen(track)
            color = self._get_track_color(track)
            
            tracks.append(TrackInfo(
                name=name,
                track_type='Audio',
                devices=devices,
                volume=volume,
                is_frozen=is_frozen,
                color=color
            ))
            
        return tracks
    
    def _get_master_chain(self) -> List[str]:
        """Extract master track device chain"""
        devices = []
        master = self.xml_root.find('.//MasterTrack')
        if master:
            # Find all devices on master
            for device in master.findall('.//Device'):
                name = self._extract_device_name(device)
                if name:
                    devices.append(name)
        return devices
    
    def _extract_device_name(self, device_elem) -> Optional[str]:
        """Extract device name from various device types"""
        # Comprehensive list of stock Ableton Live devices
        STOCK_DEVICES = [
            'Eq8', 'EqEight', 'ChannelEq', 'Compressor2', 'Limiter', 'Saturator',
            'GlueCompressor', 'MultibandDynamics', 'Gate', 'Reverb', 'Delay',
            'AutoFilter', 'AutoPan', 'Chorus', 'Flanger', 'Phaser', 'Erosion',
            'Redux', 'Vinyl', 'BeatRepeat', 'Looper', 'PitchLoop59', 'Resonator',
            'FrequencyShifter', 'RingMod', 'Vocoder', 'Amp', 'Cabinet', 'Pedal',
            'DrumBuss', 'Utility', 'SpectrumAnalyzer', 'Tuner',
            'OriginalSimpler', 'OriginalSampler', 'Operator', 'Analog', 'Collision',
            'Electric', 'Tension', 'LoungeLizard', 'StringStudio', 'InstrumentVector',
            'DrumGroupDevice', 'InstrumentGroupDevice', 'AudioEffectGroupDevice',
            'MidiEffectGroupDevice'
        ]

        # Try built-in Ableton device
        for child in device_elem:
            if child.tag in STOCK_DEVICES:
                return child.tag

        # Try plugin device - check VST3/VST/AU info structures
        plugin_desc = device_elem.find('.//PluginDesc')
        if plugin_desc is not None:
            # Check VST3
            vst3_info = plugin_desc.find('.//Vst3PluginInfo')
            if vst3_info is not None:
                name_elem = vst3_info.find('Name')  # Direct child
                if name_elem is not None and name_elem.attrib.get('Value'):
                    return name_elem.attrib['Value']

            # Check VST2
            vst_info = plugin_desc.find('.//VstPluginInfo')
            if vst_info is not None:
                name_elem = vst_info.find('PlugName')  # Direct child
                if name_elem is not None and name_elem.attrib.get('Value'):
                    return name_elem.attrib['Value']

            # Check AU
            au_info = plugin_desc.find('.//AuPluginInfo')
            if au_info is not None:
                name_elem = au_info.find('Name')  # Direct child
                if name_elem is not None and name_elem.attrib.get('Value'):
                    return name_elem.attrib['Value']

        return None
    
    def _get_track_devices(self, track_elem) -> List[str]:
        """Get all devices on a track"""
        devices = []
        for device in track_elem.findall('.//Device'):
            name = self._extract_device_name(device)
            if name:
                devices.append(name)
        return devices
    
    def _get_track_volume(self, track_elem) -> float:
        """Get track volume/mixer level"""
        volume = track_elem.find('.//Volume/Manual')
        if volume is not None and 'Value' in volume.attrib:
            return float(volume.attrib['Value'])
        return 0.7  # Default ~0dB
    
    def _is_track_frozen(self, track_elem) -> bool:
        """Check if track is frozen"""
        frozen = track_elem.find('.//Freeze')
        if frozen is not None and 'Value' in frozen.attrib:
            return frozen.attrib['Value'] == 'true'
        return False
    
    def _get_track_color(self, track_elem) -> Optional[int]:
        """Get track color index"""
        color = track_elem.find('.//Color')
        if color is not None and 'Value' in color.attrib:
            return int(color.attrib['Value'])
        return None
    
    def _count_heavy_plugins(self) -> int:
        """Count CPU-intensive plugins"""
        count = 0
        all_plugins = self._get_all_plugins()
        for plugin in all_plugins:
            if any(heavy in plugin.name for heavy in self.HEAVY_PLUGINS):
                count += 1
        return count
    
    def _get_all_plugins(self) -> List[PluginInfo]:
        """Get all plugins used in project"""
        plugins = []
        for device in self.xml_root.findall('.//PluginDevice'):
            plugin_desc = device.find('.//PluginDesc')
            if plugin_desc is not None:
                # Plugin name is stored inside VST3/VST/AU PluginInfo elements
                name = None
                device_type = 'Unknown'

                # Check for VST3 plugins
                vst3_info = plugin_desc.find('.//Vst3PluginInfo')
                if vst3_info is not None:
                    name_elem = vst3_info.find('Name')  # Direct child, not descendant
                    if name_elem is not None and name_elem.attrib.get('Value'):
                        name = name_elem.attrib.get('Value')
                    device_type = 'VST3'

                # Check for VST2 plugins
                if name is None:
                    vst_info = plugin_desc.find('.//VstPluginInfo')
                    if vst_info is not None:
                        name_elem = vst_info.find('PlugName')  # Direct child
                        if name_elem is not None and name_elem.attrib.get('Value'):
                            name = name_elem.attrib.get('Value')
                        device_type = 'VST'

                # Check for AU (Audio Units) plugins
                if name is None:
                    au_info = plugin_desc.find('.//AuPluginInfo')
                    if au_info is not None:
                        name_elem = au_info.find('Name')  # Direct child
                        if name_elem is not None and name_elem.attrib.get('Value'):
                            name = name_elem.attrib.get('Value')
                        device_type = 'AU'

                # If we found a plugin name, add it
                if name is not None:
                    # Check if active
                    is_active = True
                    on_elem = device.find('.//On/Manual')
                    if on_elem is not None and 'Value' in on_elem.attrib:
                        is_active = on_elem.attrib['Value'] == 'true'

                    plugins.append(PluginInfo(
                        name=name,
                        device_type=device_type,
                        preset_name=None,  # Could extract this too
                        is_active=is_active
                    ))
        return plugins
    
    def _generate_content_hash(self) -> str:
        """Generate hash of project structure for duplicate detection"""
        # Hash: track count + names + device chains
        content_str = f"{self._count_tracks()}"
        for track in self._get_all_tracks():
            content_str += f"{track.name}{track.devices}"
        return hashlib.md5(content_str.encode()).hexdigest()[:8]
    
    def _generate_midi_hash(self) -> str:
        """Generate hash of MIDI patterns"""
        # This would need to extract actual MIDI note data
        # For now, simplified version
        midi_data = str(len(self.xml_root.findall('.//MidiNoteEvent')))
        return hashlib.md5(midi_data.encode()).hexdigest()[:8]
    
    def _assess_completion(self) -> bool:
        """Guess if project is actually finished"""
        indicators = 0
        
        # Has markers?
        if self._count_markers() > 2:
            indicators += 1
            
        # Has master chain?
        if len(self._get_master_chain()) > 1:
            indicators += 1
            
        # Long enough arrangement?
        if self._get_arrangement_length() > 64:
            indicators += 1
            
        # Multiple scenes?
        if self._count_scenes() > 4:
            indicators += 1
            
        return indicators >= 3
    
    # ... Additional helper methods would go here ...
    # (keeping it concise for now but we'd implement all of them!)
    
    def _get_return_tracks(self) -> List[TrackInfo]:
        """Get return/send tracks"""
        # Simplified for now
        return []
    
    def _detect_missing_plugins(self) -> List[str]:
        """Detect potentially missing plugins"""
        # Would check against system VST folders
        return []
    
    def _get_builtin_devices(self) -> List[str]:
        """List all Ableton built-in devices used"""
        # Comprehensive list of stock Ableton Live devices
        builtin = [
            # Audio Effects
            'Eq8', 'EqEight', 'ChannelEq', 'Compressor2', 'Limiter', 'Saturator',
            'GlueCompressor', 'MultibandDynamics', 'Gate', 'Reverb', 'Delay',
            'AutoFilter', 'AutoPan', 'Chorus', 'Flanger', 'Phaser', 'Erosion',
            'Redux', 'Vinyl', 'BeatRepeat', 'Looper', 'PitchLoop59', 'Resonator',
            'FrequencyShifter', 'RingMod', 'Vocoder', 'Amp', 'Cabinet', 'Pedal',
            'DrumBuss', 'Utility', 'SpectrumAnalyzer', 'Tuner',

            # Instruments
            'OriginalSimpler', 'OriginalSampler', 'Operator', 'Analog', 'Collision',
            'Electric', 'Tension', 'LoungeLizard', 'StringStudio', 'InstrumentVector',

            # Container devices
            'DrumGroupDevice', 'InstrumentGroupDevice', 'AudioEffectGroupDevice',
            'MidiEffectGroupDevice'
        ]

        found = []
        for device_name in builtin:
            count = len(self.xml_root.findall(f'.//{device_name}'))
            if count > 0:
                # Add each instance (so if there are 3 EQ8s, add 3 times)
                found.extend([device_name] * count)
        return found
    
    def _get_third_party_plugins(self) -> List[str]:
        """List all third-party plugins"""
        return [p.name for p in self._get_all_plugins()]
    
    def _get_arrangement_length(self) -> float:
        """Get arrangement length in bars"""
        end = self.xml_root.find('.//End')
        if end is not None and 'Value' in end.attrib:
            return float(end.attrib['Value']) / 4  # Convert beats to bars
        return 0
    
    def _count_scenes(self) -> int:
        """Count session view scenes"""
        return len(self.xml_root.findall('.//Scene'))
    
    def _count_markers(self) -> int:
        """Count arrangement markers/locators"""
        return len(self.xml_root.findall('.//Locator'))
    
    def _get_marker_names(self) -> List[str]:
        """Get marker/locator names"""
        markers = []
        for locator in self.xml_root.findall('.//Locator'):
            name = locator.find('.//Name')
            if name is not None and 'Value' in name.attrib:
                markers.append(name.attrib['Value'])
        return markers
    
    def _count_automation_lanes(self) -> int:
        """Count automation envelopes"""
        return len(self.xml_root.findall('.//AutomationEnvelope'))
    
    def _count_clips(self) -> Dict[str, int]:
        """Count total and unique clips"""
        clips = self.xml_root.findall('.//ClipSlot')
        return {
            'total': len(clips),
            'unique': len(set(c.attrib.get('Id', '') for c in clips))
        }
    
    def _count_frozen_tracks(self) -> int:
        """Count frozen tracks"""
        return len([t for t in self._get_all_tracks() if t.is_frozen])
    
    def _check_arrangement_view(self) -> bool:
        """Check if project uses arrangement view"""
        return self._get_arrangement_length() > 0
    
    def _get_sample_paths(self) -> List[str]:
        """Extract all sample file references"""
        samples = []
        for file_ref in self.xml_root.findall('.//FileRef'):
            path = file_ref.find('.//Path')
            if path is not None and 'Value' in path.attrib:
                samples.append(path.attrib['Value'])
        return samples
    
    def _detect_missing_samples(self) -> List[str]:
        """Find referenced samples that don't exist"""
        missing = []
        for sample_path in self._get_sample_paths():
            if not Path(sample_path).exists():
                missing.append(sample_path)
        return missing


def compare_projects(proj1: ProjectStructure, proj2: ProjectStructure) -> Dict:
    """
    Compare two projects to detect if they're duplicates
    Returns similarity metrics.
    """
    return {
        'same_structure_hash': proj1.content_hash == proj2.content_hash,
        'same_midi_patterns': proj1.midi_pattern_hash == proj2.midi_pattern_hash,
        'track_count_match': proj1.track_count == proj2.track_count,
        'bpm_match': proj1.bpm == proj2.bpm,
        'master_chain_match': proj1.master_chain == proj2.master_chain,
        'likely_duplicate': (
            proj1.content_hash == proj2.content_hash and 
            proj1.track_count == proj2.track_count
        ),
        'similarity_score': calculate_similarity(proj1, proj2)
    }

def calculate_similarity(p1: ProjectStructure, p2: ProjectStructure) -> float:
    """Calculate 0-100% similarity score"""
    score = 0.0
    factors = 0
    
    # Check various factors
    if p1.content_hash == p2.content_hash:
        score += 40
    if p1.track_count == p2.track_count:
        score += 15
    if p1.bpm == p2.bpm:
        score += 10
    if p1.master_chain == p2.master_chain:
        score += 20
    if p1.midi_pattern_hash == p2.midi_pattern_hash:
        score += 15
        
    return min(score, 100.0)


# Example usage
if __name__ == "__main__":
    # Test with your projects!
    analyzer = EnhancedAbletonAnalyzer(
        "/Users/hnsk/Projects/Audio-Production/test-ableton-batch/lobby_crazy Project/lobby_crazy.als"
    )
    
    result = analyzer.analyze()
    print(f"Project: {result.filepath}")
    print(f"BPM: {result.bpm}")
    print(f"Master Chain: {result.master_chain}")
    print(f"Heavy Plugins: {result.heavy_plugin_count}")
    print(f"Likely Finished? {result.likely_finished}")
    print(f"Content Hash: {result.content_hash}")
