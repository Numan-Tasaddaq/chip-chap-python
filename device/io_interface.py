"""
IO Interface - Main IO module with DLL binding via ctypes
Equivalent to: ChipCap-Oldversion/ChipCap/Libdll/Fgio/IOInterface.h/cpp

This module:
1. Loads IO DLL dynamically (PCI7230.dll, ITrueParallelPort.dll, etc.)
2. Binds C++ function signatures to ctypes
3. Provides Python wrapper functions matching the old IO_MODULE interface
4. Handles initialization, port configuration, and read/write operations
"""

import ctypes
from ctypes import wintypes, CFUNCTYPE, POINTER
import os
from typing import Optional, Callable
from threading import Event, Thread
import time

from device.io_constants import (
    PORT_NAME_MAP, get_port_id_by_name, get_port_name_by_id,
    IO_MODE_IN, IO_MODE_OUT, RISING_EDGE, FALLING_EDGE,
    encode_output_signal, decode_output_signal
)


class IOModule:
    """
    Main IO module that loads and manages IO DLL.
    
    Equivalent to IO_MODULE struct in C++:
    - InitIODLL()
    - RegIOCard()
    - ConfigIOPort()
    - OutPortWrite() / OutPortRead()
    - InPortRead()
    - OutLineWrite() / OutLineRead()
    - InLineRead()
    - SetDIInterrupt()
    - WaitForActiveDIInterrupt()
    - ExitIODLL()
    """
    
    def __init__(self, dll_name: str):
        """
        Initialize IO module by loading DLL.
        
        Args:
            dll_name: DLL name without extension (e.g., "PCI7230", "ITrueParallelPort")
        
        Example:
            io = IOModule("PCI7230")
        """
        self.dll_name = dll_name
        self.dll = None
        self.is_loaded = False
        self.is_initialized = False
        
        # Function pointers (will be set by _load_dll)
        self.InitIODLL_func: Optional[Callable] = None
        self.RegIOCard_func: Optional[Callable] = None
        self.ConfigIOPort_func: Optional[Callable] = None
        self.OutPortWrite_func: Optional[Callable] = None
        self.OutPortRead_func: Optional[Callable] = None
        self.InPortRead_func: Optional[Callable] = None
        self.OutLineWrite_func: Optional[Callable] = None
        self.OutLineRead_func: Optional[Callable] = None
        self.InLineRead_func: Optional[Callable] = None
        self.SetDIInterrupt_func: Optional[Callable] = None
        self.WaitForActiveDIInterrupt_func: Optional[Callable] = None
        self.ExitIODLL_func: Optional[Callable] = None
        
        # Interrupt event
        self.di_interrupt_event: Optional[Event] = None
        self.interrupt_thread: Optional[Thread] = None
        self.interrupt_active = False
        
        # Load DLL and bind functions
        self._load_dll()
    
    def _load_dll(self) -> bool:
        """
        Load DLL dynamically and bind function pointers.
        Equivalent to LoadIODll() in C++.
        
        Returns:
            True if DLL loaded successfully, False otherwise
        """
        try:
            # Build DLL filename
            dll_filename = f"{self.dll_name}.dll"
            
            # Try to load DLL
            try:
                self.dll = ctypes.WinDLL(dll_filename)
            except OSError:
                # Try with full path if DLL not in PATH
                print(f"Warning: Could not load {dll_filename} from PATH")
                return False
            
            # Bind function pointers
            self._bind_functions()
            
            self.is_loaded = True
            print(f"IO DLL loaded successfully: {dll_filename}")
            return True
            
        except Exception as e:
            print(f"Error loading IO DLL: {e}")
            return False
    
    def _bind_functions(self) -> None:
        """Bind C++ function signatures from DLL to ctypes."""
        if not self.dll:
            return
        
        try:
            # Define function signatures matching C++ prototypes
            # All functions return: long (int)
            
            # InitIODLL(long lReserved)
            self.InitIODLL_func = self.dll.InitIODLL
            self.InitIODLL_func.argtypes = [wintypes.LONG]
            self.InitIODLL_func.restype = ctypes.c_long
            
            # RegIOCard(long lCardNo, long lReserved)
            self.RegIOCard_func = self.dll.RegIOCard
            self.RegIOCard_func.argtypes = [wintypes.LONG, wintypes.LONG]
            self.RegIOCard_func.restype = ctypes.c_long
            
            # ConfigIOPort(long lCardNo, long lPortID, long lIOMode, long lReserved)
            self.ConfigIOPort_func = self.dll.ConfigIOPort
            self.ConfigIOPort_func.argtypes = [wintypes.LONG, wintypes.LONG, wintypes.LONG, wintypes.LONG]
            self.ConfigIOPort_func.restype = ctypes.c_long
            
            # OutPortWrite(long lCardNo, long lPortID, long lData, long lReserved)
            self.OutPortWrite_func = self.dll.OutPortWrite
            self.OutPortWrite_func.argtypes = [wintypes.LONG, wintypes.LONG, wintypes.LONG, wintypes.LONG]
            self.OutPortWrite_func.restype = ctypes.c_long
            
            # OutPortRead(long lCardNo, long lPortID, long *plData, long lReserved)
            self.OutPortRead_func = self.dll.OutPortRead
            self.OutPortRead_func.argtypes = [wintypes.LONG, wintypes.LONG, POINTER(wintypes.LONG), wintypes.LONG]
            self.OutPortRead_func.restype = ctypes.c_long
            
            # InPortRead(long lCardNo, long lPortID, long *plData, long lReserved)
            self.InPortRead_func = self.dll.InPortRead
            self.InPortRead_func.argtypes = [wintypes.LONG, wintypes.LONG, POINTER(wintypes.LONG), wintypes.LONG]
            self.InPortRead_func.restype = ctypes.c_long
            
            # OutLineWrite(long lCardNo, long lPortID, long lline, short plState)
            self.OutLineWrite_func = self.dll.OutLineWrite
            self.OutLineWrite_func.argtypes = [wintypes.LONG, wintypes.LONG, wintypes.LONG, ctypes.c_short]
            self.OutLineWrite_func.restype = ctypes.c_long
            
            # OutLineRead(long lCardNo, long lPortID, long lline, short *plState)
            self.OutLineRead_func = self.dll.OutLineRead
            self.OutLineRead_func.argtypes = [wintypes.LONG, wintypes.LONG, wintypes.LONG, POINTER(ctypes.c_short)]
            self.OutLineRead_func.restype = ctypes.c_long
            
            # InLineRead(long lCardNo, long lPortID, long lline, short *plState)
            self.InLineRead_func = self.dll.InLineRead
            self.InLineRead_func.argtypes = [wintypes.LONG, wintypes.LONG, wintypes.LONG, POINTER(ctypes.c_short)]
            self.InLineRead_func.restype = ctypes.c_long
            
            # SetDIInterrupt(long lCardNo, long lPortID, long lData, long lReserved)
            self.SetDIInterrupt_func = self.dll.SetDIInterrupt
            self.SetDIInterrupt_func.argtypes = [wintypes.LONG, wintypes.LONG, wintypes.LONG, wintypes.LONG]
            self.SetDIInterrupt_func.restype = ctypes.c_long
            
            # WaitForActiveDIInterrupt(long lCardNo, long lPortID, long lData, long lReserved)
            self.WaitForActiveDIInterrupt_func = self.dll.WaitForActiveDIInterrupt
            self.WaitForActiveDIInterrupt_func.argtypes = [wintypes.LONG, wintypes.LONG, wintypes.LONG, wintypes.LONG]
            self.WaitForActiveDIInterrupt_func.restype = ctypes.c_long
            
            # ExitIODLL(long lReserved)
            self.ExitIODLL_func = self.dll.ExitIODLL
            self.ExitIODLL_func.argtypes = [wintypes.LONG]
            self.ExitIODLL_func.restype = ctypes.c_long
            
        except Exception as e:
            print(f"Error binding IO DLL functions: {e}")
            self.is_loaded = False
    
    # ========================================================================
    # Public API - Wrapper functions matching C++ IO_MODULE interface
    # ========================================================================
    
    def init_io_dll(self, param: int = 0) -> bool:
        """
        Initialize the IO DLL.
        Equivalent to: InitIODLL(0)
        
        Args:
            param: Initialization parameter (usually 0)
        
        Returns:
            True if successful
        """
        if not self.is_loaded or not self.InitIODLL_func:
            return False
        
        try:
            result = self.InitIODLL_func(param)
            self.is_initialized = (result == 0)
            return self.is_initialized
        except Exception as e:
            print(f"Error in InitIODLL: {e}")
            return False
    
    def reg_io_card(self, card_no: int, address: int = 0) -> bool:
        """
        Register an IO card.
        Equivalent to: RegIOCard(card_no, address)
        
        Args:
            card_no: Card number (0, 1, 2, etc.)
            address: Hardware address from registry
        
        Returns:
            True if successful
        """
        if not self.is_initialized or not self.RegIOCard_func:
            return False
        
        try:
            result = self.RegIOCard_func(card_no, address)
            return result == 0
        except Exception as e:
            print(f"Error in RegIOCard: {e}")
            return False
    
    def config_io_port(self, card_no: int, port_id: int, mode: int) -> bool:
        """
        Configure IO port for input or output.
        Equivalent to: ConfigIOPort(port_id, mode)
        
        Args:
            card_no: Card number
            port_id: Port ID (numeric, e.g., 0 for PORT_1A)
            mode: IO_MODE_IN (1) or IO_MODE_OUT (2)
        
        Returns:
            True if successful
        """
        if not self.is_initialized or not self.ConfigIOPort_func:
            return False
        
        try:
            result = self.ConfigIOPort_func(card_no, port_id, mode, 0)
            return result == 0
        except Exception as e:
            print(f"Error in ConfigIOPort: {e}")
            return False
    
    def out_port_write(self, card_no: int, port_id: int, value: int) -> bool:
        """
        Write 8-bit value to output port.
        Equivalent to: OutPortWrite(port_id, value)
        
        Args:
            card_no: Card number
            port_id: Port ID (numeric)
            value: 8-bit value to write (0-255)
        
        Returns:
            True if successful
        
        Example:
            io.out_port_write(0, PORT_1A, 0x87)  # Write 0x87 (busy + fail)
        """
        if not self.is_initialized or not self.OutPortWrite_func:
            return False
        
        try:
            # Ensure value is 0-255
            value = value & 0xFF
            result = self.OutPortWrite_func(card_no, port_id, value, 0)
            return result == 0
        except Exception as e:
            print(f"Error in OutPortWrite: {e}")
            return False
    
    def out_port_read(self, card_no: int, port_id: int) -> Optional[int]:
        """
        Read 8-bit value from output port (last written value).
        Equivalent to: OutPortRead(port_id, &value)
        
        Args:
            card_no: Card number
            port_id: Port ID (numeric)
        
        Returns:
            Read value (0-255) or None if failed
        """
        if not self.is_initialized or not self.OutPortRead_func:
            return None
        
        try:
            value = wintypes.LONG()
            result = self.OutPortRead_func(card_no, port_id, ctypes.byref(value), 0)
            return value.value if result == 0 else None
        except Exception as e:
            print(f"Error in OutPortRead: {e}")
            return None
    
    def in_port_read(self, card_no: int, port_id: int) -> Optional[int]:
        """
        Read 8-bit value from input port.
        Equivalent to: InPortRead(port_id, &value)
        
        Args:
            card_no: Card number
            port_id: Port ID (numeric)
        
        Returns:
            Read value (0-255) or None if failed
        
        Example:
            ack = io.in_port_read(0, PORT_1A)  # Read acknowledgement from hardware
        """
        if not self.is_initialized or not self.InPortRead_func:
            return None
        
        try:
            value = wintypes.LONG()
            result = self.InPortRead_func(card_no, port_id, ctypes.byref(value), 0)
            return value.value if result == 0 else None
        except Exception as e:
            print(f"Error in InPortRead: {e}")
            return None
    
    def out_line_write(self, card_no: int, port_id: int, line_num: int, state: int) -> bool:
        """
        Write single bit to output port.
        Equivalent to: OutLineWrite(port_id, line_num, state)
        
        Args:
            card_no: Card number
            port_id: Port ID (numeric)
            line_num: Bit position (0-7)
            state: 0 or 1
        
        Returns:
            True if successful
        """
        if not self.is_initialized or not self.OutLineWrite_func:
            return False
        
        try:
            result = self.OutLineWrite_func(card_no, port_id, line_num, state)
            return result == 0
        except Exception as e:
            print(f"Error in OutLineWrite: {e}")
            return False
    
    def out_line_read(self, card_no: int, port_id: int, line_num: int) -> Optional[int]:
        """
        Read single bit from output port.
        Equivalent to: OutLineRead(port_id, line_num, &state)
        
        Args:
            card_no: Card number
            port_id: Port ID (numeric)
            line_num: Bit position (0-7)
        
        Returns:
            Bit state (0 or 1) or None if failed
        """
        if not self.is_initialized or not self.OutLineRead_func:
            return None
        
        try:
            state = ctypes.c_short()
            result = self.OutLineRead_func(card_no, port_id, line_num, ctypes.byref(state))
            return state.value if result == 0 else None
        except Exception as e:
            print(f"Error in OutLineRead: {e}")
            return None
    
    def in_line_read(self, card_no: int, port_id: int, line_num: int) -> Optional[int]:
        """
        Read single bit from input port.
        Equivalent to: InLineRead(port_id, line_num, &state)
        
        Args:
            card_no: Card number
            port_id: Port ID (numeric)
            line_num: Bit position (0-7)
        
        Returns:
            Bit state (0 or 1) or None if failed
        """
        if not self.is_initialized or not self.InLineRead_func:
            return None
        
        try:
            state = ctypes.c_short()
            result = self.InLineRead_func(card_no, port_id, line_num, ctypes.byref(state))
            return state.value if result == 0 else None
        except Exception as e:
            print(f"Error in InLineRead: {e}")
            return None
    
    def set_di_interrupt(self, card_no: int, port_id: int, edge_type: int) -> bool:
        """
        Set up interrupt on digital input port.
        Equivalent to: SetDIInterrupt(port_id, edge_type, event)
        
        Args:
            card_no: Card number
            port_id: Port ID (numeric)
            edge_type: RISING_EDGE (0) or FALLING_EDGE (1)
        
        Returns:
            True if successful
        
        Example:
            io.set_di_interrupt(0, PORT_1A, RISING_EDGE)
        """
        if not self.is_initialized or not self.SetDIInterrupt_func:
            return False
        
        try:
            # Create event for interrupt signaling
            self.di_interrupt_event = Event()
            
            # Set interrupt
            result = self.SetDIInterrupt_func(card_no, port_id, edge_type, 0)
            return result == 0
        except Exception as e:
            print(f"Error in SetDIInterrupt: {e}")
            return False
    
    def wait_for_active_di_interrupt(self, card_no: int, port_id: int, timeout_ms: int = 5000) -> bool:
        """
        Wait for digital input interrupt to occur.
        Equivalent to: WaitForActiveDIInterrupt(timeout_ms)
        
        Args:
            card_no: Card number
            port_id: Port ID (numeric)
            timeout_ms: Timeout in milliseconds (default: 5000ms = 5 seconds)
        
        Returns:
            True if interrupt occurred, False if timeout
        
        Example:
            if io.wait_for_active_di_interrupt(0, PORT_1A, 5000):
                print("Handler acknowledged")
            else:
                print("Timeout waiting for handler")
        """
        if not self.is_initialized or not self.WaitForActiveDIInterrupt_func:
            return False
        
        try:
            timeout_sec = timeout_ms / 1000.0
            result = self.WaitForActiveDIInterrupt_func(card_no, port_id, timeout_ms, 0)
            return result == 0
        except Exception as e:
            print(f"Error in WaitForActiveDIInterrupt: {e}")
            return False
    
    def exit_io_dll(self) -> bool:
        """
        Clean up and exit IO DLL.
        Equivalent to: ExitIODLL()
        
        Returns:
            True if successful
        """
        if not self.is_initialized or not self.ExitIODLL_func:
            return False
        
        try:
            result = self.ExitIODLL_func(0)
            self.is_initialized = False
            return result == 0
        except Exception as e:
            print(f"Error in ExitIODLL: {e}")
            return False
    
    def close(self) -> None:
        """Clean up resources."""
        if self.is_initialized:
            self.exit_io_dll()
        if self.dll:
            try:
                ctypes.windll.kernel32.FreeLibrary(self.dll._handle)
            except:
                pass
    
    def __del__(self):
        """Destructor - clean up on object deletion."""
        self.close()


# ============================================================================
# Helper Functions for High-Level IO Operations
# ============================================================================

def send_result_signal(io: IOModule, card_no: int, port_id: int, 
                      busy: bool, result: int) -> bool:
    """
    Send result signal: encode busy bit + result and write to output port.
    
    Args:
        io: IOModule instance
        card_no: Card number
        port_id: Port ID (numeric)
        busy: True to set busy bit, False to clear
        result: Result code (0-7)
    
    Returns:
        True if successful
    
    Example:
        # Send FAIL signal with busy bit set
        send_result_signal(io, 0, PORT_1A, True, RESULT_FAIL_GENERAL)
        
        # Clear busy bit (acknowledge handler)
        send_result_signal(io, 0, PORT_1A, False, RESULT_FAIL_GENERAL)
    """
    byte_value = encode_output_signal(busy, result)
    return io.out_port_write(card_no, port_id, byte_value)


def read_result_signal(io: IOModule, card_no: int, port_id: int) -> Optional[tuple[bool, int]]:
    """
    Read result signal: read output port and decode busy bit + result.
    
    Args:
        io: IOModule instance
        card_no: Card number
        port_id: Port ID (numeric)
    
    Returns:
        Tuple of (busy: bool, result: int) or None if failed
    
    Example:
        busy, result = read_result_signal(io, 0, PORT_1A)
        print(f"Busy: {busy}, Result: {result}")
    """
    byte_value = io.out_port_read(card_no, port_id)
    if byte_value is not None:
        return decode_output_signal(byte_value)
    return None
