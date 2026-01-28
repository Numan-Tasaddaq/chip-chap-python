"""
Windows Registry handler for camera configuration.

Maps camera serial numbers (stored in Windows Registry) to Doc1-Doc7 indices.
This follows the old application's camera management pattern.

Registry location:
HKEY_CURRENT_USER\Software\iTrue\hardware
  - Doc1CamSN, Doc2CamSN, ..., Doc7CamSN

Stations:
  Doc1 → Top inspection
  Doc2 → Bottom inspection
  Doc3 → Feed
  Doc4 → Pick-up 1
  Doc5 → Pick-up 2
  Doc6 → Bottom sealing
  Doc7 → Top sealing
"""

import winreg
from typing import Optional, Dict, Tuple


class CameraRegistry:
    """
    Manages camera serial number mapping from Windows Registry.
    Doc indices are fixed (1-7), not auto-discovered.
    """

    REGISTRY_PATH = r"Software\iTrue\hardware"
    DOC_KEYS = [f"Doc{i}CamSN" for i in range(1, 8)]  # Doc1CamSN through Doc7CamSN

    # Station mapping: Doc index → (station_name, physical_location)
    DOC_TO_STATION = {
        1: ("TOP", "Top inspection"),
        2: ("BOTTOM", "Bottom inspection"),
        3: ("FEED", "Feed"),
        4: ("PICKUP1", "Pick-up 1"),
        5: ("PICKUP2", "Pick-up 2"),
        6: ("BOTTOM_SEAL", "Bottom sealing"),
        7: ("TOP_SEAL", "Top sealing"),
    }

    # Camera models: part number → (model_name, type)
    # BU030 = USB3CT (Mono), BU040 = USB4CT (Color)
    CAMERA_MODELS = {
        "USB3CT": (0, "USB3CT"),  # (type: 0=Mono, model_name)
        "USB4CT": (1, "USB4CT"),  # (type: 1=Color, model_name)
    }

    @classmethod
    def ensure_registry_exists(cls) -> bool:
        """
        Ensure the registry path exists. Creates it if needed.

        Returns:
            bool: True if registry exists or was created successfully
        """
        try:
            with winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                cls.REGISTRY_PATH
            ) as hkey:
                print(f"[REGISTRY] Registry path ready: {cls.REGISTRY_PATH}")
                return True
        except Exception as e:
            print(f"[REGISTRY] Error creating registry path: {e}")
            return False

    @classmethod
    def read_registry(cls) -> Dict[int, str]:
        """
        Read camera serial numbers from Windows Registry.

        Returns:
            dict: {doc_index (1-7): serial_number}
            e.g., {1: "CAM123456", 2: "CAM789012", ...}
        """
        cameras = {}
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REGISTRY_PATH
            ) as hkey:
                for i, key_name in enumerate(cls.DOC_KEYS, 1):
                    try:
                        value, _ = winreg.QueryValueEx(hkey, key_name)
                        if value:  # Only store non-empty serial numbers
                            cameras[i] = value
                    except FileNotFoundError:
                        # Key doesn't exist, skip
                        pass
        except FileNotFoundError:
            # Registry path doesn't exist - create it for future use
            cls.ensure_registry_exists()
            return {}
        except Exception as e:
            print(f"[REGISTRY] Error reading registry: {e}")
            return {}

        return cameras

    @classmethod
    def write_registry(cls, doc_index: int, serial_number: str) -> bool:
        """
        Write camera serial number to Windows Registry.

        Args:
            doc_index: Doc index (1-7)
            serial_number: Camera serial number (e.g., "CAM123456")

        Returns:
            bool: True if successful, False otherwise
        """
        if not (1 <= doc_index <= 7):
            print(f"[REGISTRY] Invalid doc_index: {doc_index}. Must be 1-7.")
            return False

        key_name = f"Doc{doc_index}CamSN"

        try:
            with winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                cls.REGISTRY_PATH
            ) as hkey:
                winreg.SetValueEx(hkey, key_name, 0, winreg.REG_SZ, serial_number)
                print(f"[REGISTRY] Set {key_name} = {serial_number}")
                return True
        except Exception as e:
            print(f"[REGISTRY] Error writing registry: {e}")
            return False

    @classmethod
    def get_station_name(cls, doc_index: int) -> Optional[str]:
        """
        Get station name for a Doc index.

        Args:
            doc_index: Doc index (1-7)

        Returns:
            str: Station name (e.g., "TOP", "BOTTOM", "FEED") or None
        """
        station_info = cls.DOC_TO_STATION.get(doc_index)
        return station_info[0] if station_info else None

    @classmethod
    def get_doc_index(cls, station_name: str) -> Optional[int]:
        """
        Get Doc index for a station name.

        Args:
            station_name: Station name (e.g., "TOP", "BOTTOM", "FEED")

        Returns:
            int: Doc index (1-7) or None
        """
        for doc_idx, (stn_name, _) in cls.DOC_TO_STATION.items():
            if stn_name == station_name:
                return doc_idx
        return None

    @classmethod
    def print_registry(cls) -> None:
        """Print current registry configuration for debugging."""
        cameras = cls.read_registry()
        if not cameras:
            print("[REGISTRY] No cameras configured in Windows Registry.")
            return

        print("[REGISTRY] Configured cameras:")
        for doc_idx, serial in cameras.items():
            station_name, location = cls.DOC_TO_STATION.get(doc_idx, ("UNKNOWN", "Unknown"))
            print(f"  Doc{doc_idx} → {station_name:12s} ({location:20s}) SN={serial}")


if __name__ == "__main__":
    # Test: Print current registry
    CameraRegistry.print_registry()
