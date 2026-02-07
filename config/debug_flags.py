"""
Debug Flag Constants - Python port from C++ ImgDef.h and AppDef.h

Range 0x00000000 to 0x000FFFFF for ImgTool Debug Flags
Range 0x00100000 to 0xFFF000000 for Application Debug Flags
"""

# ImgTool Debug Flags (0x00000000 - 0x000FFFFF)
DEBUG_OFF = 0x00000000  # No Debugging
DEBUG_DISP_IMAGE = 0x00000001  # Display Image
DEBUG_DRAW = 0x00000002  # Draw Data using line and rect
DEBUG_PRINT = 0x00000004  # Print Data
DEBUG_PRINT_EXT = 0x00000008  # Print Extra Data
DEBUG_EDGE = 0x00000010  # Debug Edge Detection
DEBUG_BLOB = 0x00000020  # Debug Blob Detection
DEBUG_HIST = 0x00000040  # Debug Histogram
DEBUG_TIME = 0x00000080  # Debug Timing
DEBUG_TIME_EXT = 0x00000100  # Debug Timing Extension
DEBUG_STEP_MODE = 0x00000200  # Step by Step Mode
DEBUG_CHECKBLOB = 0x00000400
DEBUG_CHECKAREA = 0x00000800
DEBUG_STOP_ON_GOOD = 0x00001000
DEBUG_STOP_ON_BAD = 0x00002000
DEBUG_SAVE_FAIL_IMAGE = 0x00004000  # Save Failed Images
DEBUG_SAVE_PASS_IMAGE = 0x00008000

# Application Debug Flags (0x00100000 - 0xFFF000000)
DEBUG_PKGLOC = 0x00100000  # Debug Package Location
DEBUG_PVI = 0x04000000  # Debug Top Side PVI Inspect (Top Station)


class DebugFlagManager:
    """Manages debug flags using bitwise operations - matches C++ CDebugFlagDlg"""
    
    def __init__(self, flags: int = 0):
        self.flags = flags
    
    def set_flag(self, flag: int) -> None:
        """Set a debug flag"""
        self.flags |= flag
    
    def clear_flag(self, flag: int) -> None:
        """Clear a debug flag"""
        self.flags &= ~flag
    
    def has_flag(self, flag: int) -> bool:
        """Check if a debug flag is set"""
        return (self.flags & flag) != 0
    
    def reset(self) -> None:
        """Reset all flags"""
        self.flags = DEBUG_OFF
    
    def get_flags(self) -> int:
        """Get the current flags value"""
        return self.flags
    
    def set_flags(self, flags: int) -> None:
        """Set the flags value"""
        self.flags = flags
