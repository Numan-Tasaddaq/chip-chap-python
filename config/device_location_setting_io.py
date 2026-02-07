import json
from pathlib import Path
from dataclasses import asdict

from config.device_location_setting import DeviceLocationSetting

DEVICE_LOCATION_FILE = Path("device_location_setting.json")

def _normalize_keys(data: dict) -> dict:
    """Normalize legacy/mismatched keys to current ones."""
    normalized = dict(data)

    # Legacy key alias: mark_mix vs enable_mix
    if "mark_mix" in normalized and "enable_mix" not in normalized:
        normalized["enable_mix"] = normalized["mark_mix"]

    return normalized

def load_device_location_setting() -> dict:
    """Load device location settings with defaults and normalization."""
    defaults = asdict(DeviceLocationSetting())

    if not DEVICE_LOCATION_FILE.exists():
        return defaults

    with DEVICE_LOCATION_FILE.open("r") as f:
        data = json.load(f)

    data = _normalize_keys(data)

    # Merge over defaults to ensure all parameters exist
    merged = defaults
    merged.update(data)
    return merged

def save_device_location_setting(data: dict):
    """Save device location settings to JSON."""
    with DEVICE_LOCATION_FILE.open("w") as f:
        json.dump(data, f, indent=4)
