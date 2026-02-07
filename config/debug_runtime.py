"""
Runtime Debug Flag State - shared by inspection functions.
"""

from config.debug_flags import (
    DEBUG_PRINT, DEBUG_PRINT_EXT, DEBUG_EDGE, DEBUG_BLOB,
    DEBUG_HIST, DEBUG_TIME, DEBUG_TIME_EXT
)

_current_debug_flags: int = 0


def set_debug_flags(flags: int) -> None:
    """Set current debug flags for runtime checks."""
    global _current_debug_flags
    _current_debug_flags = flags


def get_debug_flags() -> int:
    """Get current debug flags."""
    return _current_debug_flags


def is_debug_enabled() -> bool:
    """Return True if any debug print flag is enabled."""
    return bool(_current_debug_flags & (
        DEBUG_PRINT | DEBUG_PRINT_EXT | DEBUG_EDGE |
        DEBUG_BLOB | DEBUG_HIST | DEBUG_TIME | DEBUG_TIME_EXT
    ))


def resolve_debug(debug: bool) -> bool:
    """Resolve debug parameter against runtime flags.

    If debug is True, it becomes controlled by runtime flags.
    If debug is False, it remains False.
    """
    if debug is True:
        return is_debug_enabled()
    return bool(debug)
