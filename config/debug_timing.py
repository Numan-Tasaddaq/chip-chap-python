"""
Debug timing module for performance measurement.
Provides timing utilities gated by DEBUG_TIME and DEBUG_TIME_EXT flags.
"""

import time
from config.debug_flags import DEBUG_TIME, DEBUG_TIME_EXT
from config.debug_runtime import get_debug_flags


class DebugTimer:
    """Context manager for measuring elapsed time with debug output."""
    
    def __init__(self, label, is_ext=False):
        """
        Initialize timer.
        
        Args:
            label: Description of operation being timed
            is_ext: If True, only logs when DEBUG_TIME_EXT is set. If False, uses DEBUG_TIME
        """
        self.label = label
        self.is_ext = is_ext
        self.start_time = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and conditionally log."""
        if self.start_time is None:
            return
        
        elapsed_ms = (time.time() - self.start_time) * 1000
        
        # Get current debug flags
        debug_flags = get_debug_flags()
        
        # Determine which flag controls this timer
        if self.is_ext:
            should_log = bool(debug_flags & DEBUG_TIME_EXT)
        else:
            should_log = bool(debug_flags & DEBUG_TIME)
        
        # Log if appropriate flag is set
        if should_log:
            print(f"[TIMING] {self.label}: {elapsed_ms:.2f}ms")


def log_timing(label, elapsed_ms, is_ext=False):
    """
    Log timing measurement if appropriate debug flag is set.
    
    Args:
        label: Description of what was timed
        elapsed_ms: Elapsed time in milliseconds
        is_ext: If True, uses DEBUG_TIME_EXT; otherwise uses DEBUG_TIME
    """
    debug_flags = get_debug_flags()
    
    if is_ext:
        should_log = bool(debug_flags & DEBUG_TIME_EXT)
    else:
        should_log = bool(debug_flags & DEBUG_TIME)
    
    if should_log:
        print(f"[TIMING] {label}: {elapsed_ms:.2f}ms")


def should_measure_time(is_ext=False):
    """
    Check if timing measurements should be taken.
    
    Args:
        is_ext: If True, checks DEBUG_TIME_EXT; otherwise checks DEBUG_TIME
    
    Returns:
        True if appropriate debug flag is set
    """
    debug_flags = get_debug_flags()
    
    if is_ext:
        return bool(debug_flags & DEBUG_TIME_EXT)
    else:
        return bool(debug_flags & DEBUG_TIME)
