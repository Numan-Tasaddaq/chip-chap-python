# config/debug_flags_io.py
import json
from pathlib import Path
from dataclasses import asdict
from .debug_flags import DebugFlags

DEBUG_FILE = Path("debug_flags.json")

def save_debug_flags(flags: DebugFlags):
    with DEBUG_FILE.open("w") as f:
        json.dump(asdict(flags), f, indent=4)

def load_debug_flags() -> DebugFlags:
    if not DEBUG_FILE.exists():
        return DebugFlags()
    with DEBUG_FILE.open("r") as f:
        data = json.load(f)
    return DebugFlags(**data)
