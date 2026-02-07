"""
Station Trigger Configuration

Stores per-station hardware trigger settings matching old system registry:
- Position sensor line assignments
- Camera trigger line assignments  
- Ejector distances (TopVisionEjectorDistance, BottomVisionEjectorDistance)
- Trigger modes (hardware vs software)

Configuration stored in: station_trigger_config.json
"""

import json
import os
from typing import Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class StationTriggerConfig:
    """Hardware trigger configuration for one station"""
    doc_index: int                      # 1-7
    station_name: str                   # TOP, BOTTOM, FEED, etc.
    position_sensor_line: int           # I/O input line (0-7)
    camera_trigger_line: int            # I/O output line (0-7)
    ejector_distance: int               # Distance from sensor to ejector
    use_hardware_trigger: bool = True   # True=hardware, False=software
    trigger_pulse_ms: float = 10.0      # Pulse duration in ms
    enabled: bool = True                # Enable/disable this station


class StationTriggerConfigManager:
    """Manages station trigger configuration"""
    
    DEFAULT_CONFIG_FILE = "station_trigger_config.json"
    
    @classmethod
    def load_config(cls, config_file: str = None) -> Dict[int, StationTriggerConfig]:
        """
        Load station trigger configuration from JSON file.
        
        Args:
            config_file: Path to config file (default: station_trigger_config.json)
        
        Returns:
            Dictionary of {doc_index: StationTriggerConfig}
        """
        config_file = config_file or cls.DEFAULT_CONFIG_FILE
        
        if not os.path.exists(config_file):
            print(f"[CONFIG] Config file not found: {config_file}")
            print("[CONFIG] Creating default configuration...")
            default_config = cls.create_default_config()
            cls.save_config(default_config, config_file)
            return default_config
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            configs = {}
            for station_data in data.get('stations', []):
                doc_index = station_data['doc_index']
                config = StationTriggerConfig(**station_data)
                configs[doc_index] = config
            
            print(f"[CONFIG] Loaded {len(configs)} station configurations from {config_file}")
            return configs
            
        except Exception as e:
            print(f"[CONFIG] Error loading config: {e}")
            return {}
    
    @classmethod
    def save_config(cls, configs: Dict[int, StationTriggerConfig], 
                   config_file: str = None) -> bool:
        """
        Save station trigger configuration to JSON file.
        
        Args:
            configs: Dictionary of {doc_index: StationTriggerConfig}
            config_file: Path to config file
        
        Returns:
            True if saved successfully
        """
        config_file = config_file or cls.DEFAULT_CONFIG_FILE
        
        try:
            data = {
                "version": "1.0",
                "description": "Station trigger configuration for hardware-triggered inspection",
                "stations": [asdict(config) for config in configs.values()]
            }
            
            with open(config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"[CONFIG] Saved {len(configs)} station configurations to {config_file}")
            return True
            
        except Exception as e:
            print(f"[CONFIG] Error saving config: {e}")
            return False
    
    @classmethod
    def create_default_config(cls) -> Dict[int, StationTriggerConfig]:
        """
        Create default 7-station configuration matching old system.
        
        Based on hardware documentation images:
        - Doc1 (TOP): sensor_line=0, trigger_line=0, ejector_distance=10
        - Doc2 (BOTTOM): sensor_line=1, trigger_line=1, ejector_distance=4
        - Doc3-7: Sequential assignments
        
        Returns:
            Dictionary of default configurations
        """
        default_stations = [
            StationTriggerConfig(
                doc_index=1,
                station_name="TOP",
                position_sensor_line=0,
                camera_trigger_line=0,
                ejector_distance=10,  # TopVisionEjectorDistance from registry
                use_hardware_trigger=True,
                trigger_pulse_ms=10.0,
                enabled=True
            ),
            StationTriggerConfig(
                doc_index=2,
                station_name="BOTTOM",
                position_sensor_line=1,
                camera_trigger_line=1,
                ejector_distance=4,  # BottomVisionEjectorDistance from registry
                use_hardware_trigger=True,
                trigger_pulse_ms=10.0,
                enabled=True
            ),
            StationTriggerConfig(
                doc_index=3,
                station_name="FEED",
                position_sensor_line=2,
                camera_trigger_line=2,
                ejector_distance=0,
                use_hardware_trigger=True,
                trigger_pulse_ms=10.0,
                enabled=True
            ),
            StationTriggerConfig(
                doc_index=4,
                station_name="PICKUP1",
                position_sensor_line=3,
                camera_trigger_line=3,
                ejector_distance=0,
                use_hardware_trigger=True,
                trigger_pulse_ms=10.0,
                enabled=True
            ),
            StationTriggerConfig(
                doc_index=5,
                station_name="PICKUP2",
                position_sensor_line=4,
                camera_trigger_line=4,
                ejector_distance=0,
                use_hardware_trigger=True,
                trigger_pulse_ms=10.0,
                enabled=True
            ),
            StationTriggerConfig(
                doc_index=6,
                station_name="BOTTOM_SEAL",
                position_sensor_line=5,
                camera_trigger_line=5,
                ejector_distance=0,
                use_hardware_trigger=True,
                trigger_pulse_ms=10.0,
                enabled=True
            ),
            StationTriggerConfig(
                doc_index=7,
                station_name="TOP_SEAL",
                position_sensor_line=6,
                camera_trigger_line=6,
                ejector_distance=0,
                use_hardware_trigger=True,
                trigger_pulse_ms=10.0,
                enabled=True
            ),
        ]
        
        return {config.doc_index: config for config in default_stations}
    
    @classmethod
    def update_ejector_distances_from_registry(cls, configs: Dict[int, StationTriggerConfig]) -> None:
        """
        Update ejector distances from Windows Registry (if configured).
        
        Registry keys:
        - HKEY_CURRENT_USER\Software\iTrue\hardware\TopVisionEjectorDistance
        - HKEY_CURRENT_USER\Software\iTrue\hardware\BottomVisionEjectorDistance
        
        Args:
            configs: Station configurations to update
        """
        try:
            import winreg
            
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\iTrue\hardware") as key:
                # Update TOP station (Doc1)
                try:
                    top_distance, _ = winreg.QueryValueEx(key, "TopVisionEjectorDistance")
                    if 1 in configs:
                        configs[1].ejector_distance = int(top_distance)
                        print(f"[CONFIG] Updated TOP ejector distance: {top_distance}")
                except FileNotFoundError:
                    pass
                
                # Update BOTTOM station (Doc2)
                try:
                    bottom_distance, _ = winreg.QueryValueEx(key, "BottomVisionEjectorDistance")
                    if 2 in configs:
                        configs[2].ejector_distance = int(bottom_distance)
                        print(f"[CONFIG] Updated BOTTOM ejector distance: {bottom_distance}")
                except FileNotFoundError:
                    pass
                    
        except Exception as e:
            print(f"[CONFIG] Could not read ejector distances from registry: {e}")


if __name__ == "__main__":
    # Test: Create and save default configuration
    print("Station Trigger Configuration Manager")
    print("=" * 60)
    
    # Create default config
    configs = StationTriggerConfigManager.create_default_config()
    
    print(f"\nCreated {len(configs)} default station configurations:")
    for doc_idx, config in configs.items():
        print(f"  Doc{doc_idx} ({config.station_name}): "
              f"sensor={config.position_sensor_line}, "
              f"trigger={config.camera_trigger_line}, "
              f"ejector_dist={config.ejector_distance}")
    
    # Try to update from registry
    print("\nTrying to read ejector distances from registry...")
    StationTriggerConfigManager.update_ejector_distances_from_registry(configs)
    
    # Save to file
    print("\nSaving to station_trigger_config.json...")
    StationTriggerConfigManager.save_config(configs)
    
    # Test reload
    print("\nReloading from file...")
    loaded_configs = StationTriggerConfigManager.load_config()
    print(f"Loaded {len(loaded_configs)} configurations")
