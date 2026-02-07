"""
IO Constants - Port IDs and modes matching the old system
File: FrameGrabIO/FGIOHead/IOCode.h
"""

# ============================================================================
# Port ID Constants
# ============================================================================
# Maps to C++ values in IOCode.h (IMPORTANT: 1-based, not 0-based)
# Each port represents 8 bits only

PORT_1A = 1
PORT_1B = 2
PORT_1C = 3
PORT_2A = 4
PORT_2B = 5
PORT_2C = 6
PORT_3A = 7
PORT_3B = 8
PORT_3C = 9
PORT_4A = 10
PORT_4B = 11
PORT_4C = 12

# String to numeric ID mapping
PORT_NAME_MAP = {
    "PORT_1A": PORT_1A,
    "PORT_1B": PORT_1B,
    "PORT_1C": PORT_1C,
    "PORT_2A": PORT_2A,
    "PORT_2B": PORT_2B,
    "PORT_2C": PORT_2C,
    "PORT_3A": PORT_3A,
    "PORT_3B": PORT_3B,
    "PORT_3C": PORT_3C,
    "PORT_4A": PORT_4A,
    "PORT_4B": PORT_4B,
    "PORT_4C": PORT_4C,
}

# Reverse mapping: numeric to string
NUMERIC_PORT_MAP = {v: k for k, v in PORT_NAME_MAP.items()}

# ============================================================================
# IO Mode Constants
# ============================================================================

IO_MODE_IN = 1    # Input mode
IO_MODE_OUT = 2   # Output mode

# ============================================================================
# Interrupt Edge Type Constants
# ============================================================================

RISING_EDGE = 0
FALLING_EDGE = 1

# ============================================================================
# Result/Status Code Constants
# ============================================================================

RESULT_PASS = 0          # PASS (000)
RESULT_FAIL_TYPE_1 = 1   # FAIL_TYPE_1 (001)
RESULT_FAIL_TYPE_2 = 2   # FAIL_TYPE_2 (010)
RESULT_FAIL_TYPE_3 = 3   # FAIL_TYPE_3 (011)
RESULT_FAIL_TYPE_4 = 4   # FAIL_TYPE_4 (100)
RESULT_FAIL_TYPE_5 = 5   # FAIL_TYPE_5 (101)
RESULT_FAIL_TYPE_6 = 6   # FAIL_TYPE_6 (110)
RESULT_FAIL_GENERAL = 7  # FAIL_GENERAL (111)

RESULT_MAP = {
    "PASS": RESULT_PASS,
    "FAIL": RESULT_FAIL_GENERAL,
    "FAIL_TYPE_1": RESULT_FAIL_TYPE_1,
    "FAIL_TYPE_2": RESULT_FAIL_TYPE_2,
    "FAIL_TYPE_3": RESULT_FAIL_TYPE_3,
    "FAIL_TYPE_4": RESULT_FAIL_TYPE_4,
    "FAIL_TYPE_5": RESULT_FAIL_TYPE_5,
    "FAIL_TYPE_6": RESULT_FAIL_TYPE_6,
}

# ============================================================================
# Output Signal Bit Layout - CONFIGURABLE PER TRACK
# ============================================================================
# IMPORTANT: Old system does NOT use fixed bit positions!
# 
# Instead:
# - m_nBusyBits[track] = bit position for busy signal (0-7, per track)
# - m_nResultBits[track] = bit position for result signal (0-7, per track)
# 
# Read from registry: HKEY_LOCAL_MACHINE\SOFTWARE\iTrue\ChipResistor\IO
# - Track1_Busy = 7 (example)
# - Track1_Result = 0 (example)
# - Track2_Busy = 6 (example)
# - Track2_Result = 1 (example)
# 
# Signal encoding uses OutLineWrite() to set individual bit positions

# DEFAULT BIT POSITIONS (when not configured in registry)
# These are typical defaults, but MUST be read from registry for production
DEFAULT_BUSY_BIT = 7     # Bit 7 is typical for busy
DEFAULT_RESULT_BIT = 0   # Bit 0 is typical for result


def encode_output_signal(result_code: int, busy_bit_pos: int = DEFAULT_BUSY_BIT, 
                        result_bit_pos: int = DEFAULT_RESULT_BIT) -> int:
    """
    Encode result code and busy signal into output byte using configurable bit positions.
    
    Matches old C++ system:
    - Sets busy bit (typically bit 7)
    - Sets result bits (3-bit code, typically bits 0-2)
    
    Args:
        result_code: Result code (0-7): 0=PASS, 1-7=various FAIL types
        busy_bit_pos: Bit position for busy signal (0-7, from registry)
        result_bit_pos: Starting bit position for result code (0-7, from registry)
    
    Returns:
        Complete output byte value (0-255)
    
    Example (old system typical config):
        encode_output_signal(0, busy_bit_pos=7, result_bit_pos=0)
        # Result: 0b10000000 (bit 7=1 for busy, bits 0-2=000 for PASS)
        
        encode_output_signal(1, busy_bit_pos=7, result_bit_pos=0)
        # Result: 0b10000001 (bit 7=1 for busy, bits 0-2=001 for FAIL)
    """
    byte_value = 0
    
    # Set busy bit (always 1 when sending signal)
    byte_value |= (1 << busy_bit_pos)
    
    # Set result code (3 bits: 0-7)
    byte_value |= (result_code & 0x07) << result_bit_pos
    
    return byte_value


def decode_output_signal(byte_value: int, busy_bit_pos: int = DEFAULT_BUSY_BIT,
                        result_bit_pos: int = DEFAULT_RESULT_BIT) -> tuple[bool, int]:
    """
    Decode output byte using configurable bit positions.
    
    Args:
        byte_value: Output byte value (0-255)
        busy_bit_pos: Bit position for busy signal (0-7)
        result_bit_pos: Bit position for result signal (0-7)
    
    Returns:
        Tuple of (busy: bool, result: int)
    
    Example:
        busy, result = decode_output_signal(0x81, busy_bit_pos=7, result_bit_pos=0)
        # Returns: (True, 1)
    """
    busy = bool((byte_value >> busy_bit_pos) & 1)
    result = bool((byte_value >> result_bit_pos) & 1)
    return busy, result


def get_port_id_by_name(port_name: str) -> int | None:
    """
    Convert port name string to numeric port ID.
    
    Args:
        port_name: Port name string (e.g., "PORT_1A")
    
    Returns:
        Numeric port ID (0-11) or None if not found
    
    Equivalent to C++ GetIOPortID() function
    """
    return PORT_NAME_MAP.get(port_name)


def get_port_name_by_id(port_id: int) -> str | None:
    """
    Convert numeric port ID to port name string.
    
    Args:
        port_id: Numeric port ID (0-11)
    
    Returns:
        Port name string (e.g., "PORT_1A") or None if not found
    """
    return NUMERIC_PORT_MAP.get(port_id)
