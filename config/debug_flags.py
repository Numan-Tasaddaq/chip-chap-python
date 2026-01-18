# config/debug_flags.py
from dataclasses import dataclass, field

@dataclass
class DebugFlags:
    # Station Modules
    package_location: bool = False
    top_station: bool = False
    bottom_station: bool = False

    # Debugging Options
    debug_draw: bool = False
    debug_step_mode: bool = False
    debug_print: bool = False
    debug_edge: bool = False
    save_failed_images: bool = False
