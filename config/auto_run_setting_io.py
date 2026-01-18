
# config/auto_run_setting_io.py
import json
from pathlib import Path
from dataclasses import asdict
from .auto_run_setting import AutoRunSetting

AUTO_RUN_FILE = Path("auto_run_setting.json")

def save_auto_run_setting(setting: AutoRunSetting):
    with AUTO_RUN_FILE.open("w") as f:
        json.dump(asdict(setting), f, indent=4)

def load_auto_run_setting() -> AutoRunSetting:
    if not AUTO_RUN_FILE.exists():
        return AutoRunSetting()
    with AUTO_RUN_FILE.open("r") as f:
        data = json.load(f)
    return AutoRunSetting(**data)
