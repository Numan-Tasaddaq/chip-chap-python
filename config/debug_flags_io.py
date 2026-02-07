"""
Debug Flags Configuration I/O - integer flag storage
"""

import json
from pathlib import Path

DEBUG_FLAGS_FILE = Path("debug_flags.json")

def load_debug_flags() -> int:
    """
    Load debug flags from JSON file.
    Returns integer flag value (bitwise OR of all enabled flags).
    Matches C++ behavior of loading flags into long m_lDebugFlag.
    """
    if not DEBUG_FLAGS_FILE.exists():
        return 0
    
    try:
        with open(DEBUG_FLAGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Return the integer flag value
        return data.get('debug_flag', 0)
    
    except (json.JSONDecodeError, IOError):
        return 0


def save_debug_flags(debug_flag: int) -> None:
    """
    Save debug flags to JSON file.
    Saves integer flag value (bitwise OR of all enabled flags).
    Matches C++ behavior of saving long m_lDebugFlag.
    """
    data = {
        'debug_flag': debug_flag
    }
    
    try:
        with open(DEBUG_FLAGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    except IOError as e:
        print(f"Error saving debug flags: {e}")

