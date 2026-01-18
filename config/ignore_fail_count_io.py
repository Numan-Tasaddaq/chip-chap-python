# config/ignore_fail_count_io.py
import json
from pathlib import Path
from dataclasses import asdict
from .ignore_fail_count import IgnoreFailCount

IGNORE_FAIL_FILE = Path("ignore_fail_count.json")

def save_ignore_fail_count(data: IgnoreFailCount):
    with IGNORE_FAIL_FILE.open("w") as f:
        json.dump(asdict(data), f, indent=4)

def load_ignore_fail_count() -> IgnoreFailCount:
    if not IGNORE_FAIL_FILE.exists():
        return IgnoreFailCount()
    with IGNORE_FAIL_FILE.open("r") as f:
        data = json.load(f)
    return IgnoreFailCount(**data)
