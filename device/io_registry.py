"""
IO Registry - Read IO configuration from Windows Registry
Equivalent to: ChipCap-Oldversion/ChipCap/Application/ChipCapacitor/ChipCapacitor.cpp
Registry Path: HKEY_LOCAL_MACHINE\SOFTWARE\iTrue\ChipResistor\Hardware
"""

import winreg
from dataclasses import dataclass
from typing import Optional


@dataclass
class IOCardConfig:
    """Configuration for a single IO card"""
    card_index: int
    name: str                    # DLL name (e.g., "PCI7230")
    address: int                 # Hardware address or COM port
    in_card_no: int              # Input card number
    in_port_id: str              # Input port ID string (e.g., "PORT_1A")
    out_card_no: int             # Output card number
    out_port_id: str             # Output port ID string (e.g., "PORT_1A")


@dataclass
class TrackIOConfig:
    """
    Configuration for IO signals on a single track.
    
    Equivalent to: ChipCapacitor.cpp m_nBusyBits[track], m_nResultBits[track]
    Read from registry: Software\\iTrue\\ChipResistor\\IO
    """
    track_number: int            # Track 1, 2, 3, etc.
    busy_bit: int                # Bit position for busy signal (0-7)
    result_bit: int              # Bit position for result signal (0-7)
    mark_result_bit: int = -1    # Optional: result bit for marking


@dataclass
class IOConfig:
    """Complete IO configuration including cards and tracks"""
    card_count: int
    cards: list[IOCardConfig]
    track_configs: dict[int, TrackIOConfig]


class IORegistry:
    """
    Read IO configuration from Windows Registry.
    
    Expected Registry Structure:
        IOCardCount (DWORD)
        IOCard0_Name (STRING) 
        IOCard0_Addr (DWORD)
        IOCard0_InCardNo (DWORD)
        IOCard0_InPortID (STRING)
        IOCard0_OutCardNo (DWORD)
        IOCard0_OutPortID (STRING)
    """
    
    REGISTRY_PATH = r"SOFTWARE\iTrue\ChipResistor\Hardware"
    
    @staticmethod
    def read_config() -> Optional[IOConfig]:
        """
        Read IO configuration from Windows Registry.
        Reads both Hardware config and Track IO config.
        
        Returns:
            IOConfig object with all settings, or None if registry not found
        """
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, IORegistry.REGISTRY_PATH) as key:
                # Read card count
                try:
                    card_count, _ = winreg.QueryValueEx(key, "IOCardCount")
                except FileNotFoundError:
                    card_count = 0
                
                cards = []
                
                # Read each card's configuration
                for i in range(card_count):
                    card_config = IORegistry._read_card_config(key, i)
                    if card_config:
                        cards.append(card_config)
                
                # Also read track-specific IO configuration
                track_configs = IORegistry._read_track_configs()
                
                return IOConfig(card_count=card_count, cards=cards, track_configs=track_configs)
                
        except FileNotFoundError:
            # Registry path not found
            return None
        except Exception as e:
            print(f"Error reading IO registry: {e}")
            return None
    
    @staticmethod
    def _read_card_config(key, card_index: int) -> Optional[IOCardConfig]:
        """
        Read configuration for a single IO card from registry.
        
        Args:
            key: Registry key handle
            card_index: Card index (0, 1, 2, etc.)
        
        Returns:
            IOCardConfig object or None if read fails
        """
        try:
            # Read card name (e.g., "PCI7230")
            name, _ = winreg.QueryValueEx(key, f"IOCard{card_index}_Name")
            
            # Read card address
            try:
                address, _ = winreg.QueryValueEx(key, f"IOCard{card_index}_Addr")
            except FileNotFoundError:
                address = 0
            
            # Read input card settings
            try:
                in_card_no, _ = winreg.QueryValueEx(key, f"IOCard{card_index}_InCardNo")
            except FileNotFoundError:
                in_card_no = -1
            
            try:
                in_port_id, _ = winreg.QueryValueEx(key, f"IOCard{card_index}_InPortID")
            except FileNotFoundError:
                in_port_id = "PORT_1A"
            
            # Read output card settings
            try:
                out_card_no, _ = winreg.QueryValueEx(key, f"IOCard{card_index}_OutCardNo")
            except FileNotFoundError:
                out_card_no = -1
            
            try:
                out_port_id, _ = winreg.QueryValueEx(key, f"IOCard{card_index}_OutPortID")
            except FileNotFoundError:
                out_port_id = "PORT_1A"
            
            return IOCardConfig(
                card_index=card_index,
                name=name,
                address=address,
                in_card_no=in_card_no,
                in_port_id=in_port_id,
                out_card_no=out_card_no,
                out_port_id=out_port_id
            )
            
        except Exception as e:
            print(f"Error reading IO card {card_index} config: {e}")
    
    @staticmethod
    def _read_track_configs() -> dict[int, TrackIOConfig]:
        """
        Read track-specific IO configuration from registry.

        Registry Path: HKEY_LOCAL_MACHINE\SOFTWARE\iTrue\ChipResistor\IO

        Keys:
            Track1_Busy, Track1_Result, Track1_Mark_Result
            Track2_Busy, Track2_Result, Track2_Mark_Result
            ... and so on for each track

        Equivalent to: ChipCapacitor.cpp lines 437-443
        
        Returns:
            Dictionary of {track_number: TrackIOConfig}
        """
        try:
            io_registry_path = r"SOFTWARE\iTrue\ChipResistor\IO"

            track_configs = {}

            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, io_registry_path) as key:
                    # Read up to 8 tracks
                    for track_num in range(1, 9):
                        try:
                            # Read busy bit position
                            busy_key = f"Track{track_num}_Busy"
                            busy_bit, _ = winreg.QueryValueEx(key, busy_key)
                
                            # Read result bit position
                            result_key = f"Track{track_num}_Result"
                            result_bit, _ = winreg.QueryValueEx(key, result_key)
                
                            # Try to read mark result bit (optional)
                            mark_key = f"Track{track_num}_Mark_Result"
                            try:
                                mark_result_bit, _ = winreg.QueryValueEx(key, mark_key)
                            except FileNotFoundError:
                                mark_result_bit = -1
                
                            track_configs[track_num] = TrackIOConfig(
                                track_number=track_num,
                                busy_bit=busy_bit,
                                result_bit=result_bit,
                                mark_result_bit=mark_result_bit
                            )
                    
                        except FileNotFoundError:
                            # Track not configured
                            pass
                        except Exception as e:
                            print(f"Error reading Track{track_num} IO config: {e}")

            except FileNotFoundError:
                # IO registry path not found - return empty
                pass

            return track_configs

        except Exception as e:
            print(f"Error reading track configs: {e}")
            return {}
    
    @staticmethod
    def write_config(config: IOConfig) -> bool:
        """
        Write IO configuration to Windows Registry.
        
        Args:
            config: IOConfig object to write
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, IORegistry.REGISTRY_PATH, 0, 
                               winreg.KEY_WRITE) as key:
                
                # Write card count
                winreg.SetValueEx(key, "IOCardCount", 0, winreg.REG_DWORD, config.card_count)
                
                # Write each card's configuration
                for card in config.cards:
                    winreg.SetValueEx(key, f"IOCard{card.card_index}_Name", 0, 
                                    winreg.REG_SZ, card.name)
                    winreg.SetValueEx(key, f"IOCard{card.card_index}_Addr", 0, 
                                    winreg.REG_DWORD, card.address)
                    winreg.SetValueEx(key, f"IOCard{card.card_index}_InCardNo", 0, 
                                    winreg.REG_DWORD, card.in_card_no)
                    winreg.SetValueEx(key, f"IOCard{card.card_index}_InPortID", 0, 
                                    winreg.REG_SZ, card.in_port_id)
                    winreg.SetValueEx(key, f"IOCard{card.card_index}_OutCardNo", 0, 
                                    winreg.REG_DWORD, card.out_card_no)
                    winreg.SetValueEx(key, f"IOCard{card.card_index}_OutPortID", 0, 
                                    winreg.REG_SZ, card.out_port_id)
                
                return True
                
        except Exception as e:
            print(f"Error writing IO registry: {e}")
            return False
    
    @staticmethod
    def create_default_config() -> IOConfig:
        """
        Create default IO configuration (1 card, PCI-7230, 1 track).
        
        Returns:
            Default IOConfig object
        """
        return IOConfig(
            card_count=1,
            cards=[
                IOCardConfig(
                    card_index=0,
                    name="PCI7230",
                    address=0,
                    in_card_no=0,
                    in_port_id="PORT_1A",
                    out_card_no=0,
                    out_port_id="PORT_1A"
                )
            ],
            track_configs={
                1: TrackIOConfig(
                    track_number=1,
                    busy_bit=7,        # Default: bit 7 for busy
                    result_bit=0       # Default: bit 0 for result
                )
            }
        )
