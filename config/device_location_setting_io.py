import json
from pathlib import Path

DEVICE_LOCATION_FILE = Path("device_location_setting.json")

def load_device_location_setting() -> dict:
    if not DEVICE_LOCATION_FILE.exists():
        return {}
    with DEVICE_LOCATION_FILE.open("r") as f:
        return json.load(f)

def save_device_location_setting(data: dict):
    with DEVICE_LOCATION_FILE.open("w") as f:
        json.dump(data, f, indent=4)
