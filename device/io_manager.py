"""
IO Manager - High-level IO operations and production loop integration
Orchestrates initialization, configuration, and production workflow
"""

from typing import Optional, Callable
import time

from device.io_interface import IOModule
from device.io_registry import IORegistry, IOConfig, IOCardConfig
from device.io_constants import (
    get_port_id_by_name, get_port_name_by_id,
    IO_MODE_IN, IO_MODE_OUT, RISING_EDGE,
    encode_output_signal, decode_output_signal,
    RESULT_PASS, RESULT_FAIL_GENERAL
)


class IOManager:
    """
    High-level IO manager for production workflow.
    
    Responsibilities:
    1. Read IO configuration from registry
    2. Load and initialize IO DLL
    3. Configure input/output ports
    4. Manage production cycle signals (busy, result, acknowledgement)
    5. Provide interface to application for IO operations
    
    Equivalent to the initialization and production sections of ChipCapacitor.cpp
    """
    
    def __init__(self):
        """Initialize IO manager (no hardware access until setup() called)."""
        self.io_module: Optional[IOModule] = None
        self.io_config: Optional[IOConfig] = None
        
        self.in_card_no: int = -1
        self.in_port_id: int = -1
        self.in_port_name: str = ""
        
        self.out_card_no: int = -1
        self.out_port_id: int = -1
        self.out_port_name: str = ""
        
        self.is_initialized = False
    
    def setup(self) -> bool:
        """
        Complete IO initialization sequence.
        Equivalent to: ReadIOConfig() + InitIOCard() + ConfigIOPorts()
        
        Steps:
        1. Read IO configuration from registry
        2. Load IO DLL
        3. Initialize DLL
        4. Register input/output cards
        5. Configure input/output ports
        6. Set up interrupt (optional)
        
        Returns:
            True if all steps successful, False if any step fails
        """
        try:
            # Step 1: Read registry configuration
            if not self._read_registry_config():
                print("Error: Failed to read IO registry configuration")
                return False
            
            # Step 2: Load IO DLL
            if not self._load_io_dll():
                print("Error: Failed to load IO DLL")
                return False
            
            # Step 3: Initialize DLL
            if not self._initialize_dll():
                print("Error: Failed to initialize IO DLL")
                return False
            
            # Step 4: Register cards and configure ports
            if not self._setup_cards_and_ports():
                print("Error: Failed to set up IO cards and ports")
                return False
            
            self.is_initialized = True
            print("IO system initialized successfully")
            return True
            
        except Exception as e:
            print(f"Error during IO setup: {e}")
            return False
    
    def _read_registry_config(self) -> bool:
        """
        Step 1: Read IO configuration from Windows Registry.
        Equivalent to ChipCapacitor.cpp lines 1360-1455
        """
        try:
            self.io_config = IORegistry.read_config()
            
            if not self.io_config or self.io_config.card_count == 0:
                print("No IO cards configured in registry")
                # Use default configuration
                self.io_config = IORegistry.create_default_config()
            
            # Extract first card configuration
            if self.io_config.cards:
                card = self.io_config.cards[0]
                self.in_card_no = card.in_card_no
                self.in_port_name = card.in_port_id
                self.in_port_id = get_port_id_by_name(card.in_port_id)
                
                self.out_card_no = card.out_card_no
                self.out_port_name = card.out_port_id
                self.out_port_id = get_port_id_by_name(card.out_port_id)
                
                print(f"IO Config read from registry:")
                print(f"  DLL: {card.name}")
                print(f"  Input: Card {self.in_card_no}, Port {self.in_port_name}")
                print(f"  Output: Card {self.out_card_no}, Port {self.out_port_name}")
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error reading registry config: {e}")
            return False
    
    def _load_io_dll(self) -> bool:
        """
        Step 2: Load IO DLL dynamically.
        Equivalent to ChipCapacitor.cpp InitIOCard() + IOInterface::LoadIODll()
        """
        try:
            if not self.io_config or not self.io_config.cards:
                return False
            
            dll_name = self.io_config.cards[0].name
            
            # Load DLL via ctypes
            self.io_module = IOModule(dll_name)
            
            if not self.io_module.is_loaded:
                print(f"Failed to load IO DLL: {dll_name}.dll")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error loading IO DLL: {e}")
            return False
    
    def _initialize_dll(self) -> bool:
        """
        Step 3: Initialize IO DLL.
        Equivalent to IOInterface::InitIODLL()
        """
        try:
            if not self.io_module:
                return False
            
            return self.io_module.init_io_dll(0)
            
        except Exception as e:
            print(f"Error initializing IO DLL: {e}")
            return False
    
    def _setup_cards_and_ports(self) -> bool:
        """
        Step 4-5: Register IO cards and configure ports.
        Equivalent to ChipCapacitor.cpp InitIOCard() lines 2280-2425
        """
        try:
            if not self.io_module or not self.io_config:
                return False
            
            card = self.io_config.cards[0]
            
            # Register input card
            if self.in_card_no >= 0:
                if not self.io_module.reg_io_card(self.in_card_no, card.address):
                    print(f"Failed to register input card {self.in_card_no}")
                    return False
                
                # Configure input port
                if self.in_port_id >= 0:
                    if not self.io_module.config_io_port(self.in_card_no, self.in_port_id, IO_MODE_IN):
                        print(f"Failed to configure input port {self.in_port_name}")
                        return False
                    
                    print(f"Input port configured: {self.in_port_name} (ID: {self.in_port_id})")
            
            # Register output card
            if self.out_card_no >= 0:
                if not self.io_module.reg_io_card(self.out_card_no, card.address):
                    print(f"Failed to register output card {self.out_card_no}")
                    return False
                
                # Configure output port
                if self.out_port_id >= 0:
                    if not self.io_module.config_io_port(self.out_card_no, self.out_port_id, IO_MODE_OUT):
                        print(f"Failed to configure output port {self.out_port_name}")
                        return False
                    
                    print(f"Output port configured: {self.out_port_name} (ID: {self.out_port_id})")
            
            return True
            
        except Exception as e:
            print(f"Error setting up cards and ports: {e}")
            return False
    
    # ========================================================================
    # Production Workflow API
    # ========================================================================
    
    def read_position_sensor(self, line_number: int) -> bool:
        """
        Read specific position sensor line from input port.
        Used to detect chip position at inspection stations.
        
        Args:
            line_number: Bit position (0-7) of the sensor line
        
        Returns:
            True if sensor is active (high), False otherwise
        
        Example:
            # Read sensor line 2 for TOP station
            if io.read_position_sensor(2):
                print("Chip detected at TOP station")
        """
        if not self.is_initialized or not self.io_module:
            return False
        
        return self.io_module.in_line_read(self.in_card_no, self.in_port_id, line_number) == 1
    
    def send_hardware_trigger(self, camera_line: int, pulse_duration_ms: float = 10) -> bool:
        """
        Send hardware trigger pulse to camera via output line.
        
        Args:
            camera_line: Output line number (0-7) for camera trigger
            pulse_duration_ms: Duration of trigger pulse in milliseconds
        
        Returns:
            True if successful
        
        Example:
            # Trigger camera 1 (Doc1/TOP)
            io.send_hardware_trigger(camera_line=0, pulse_duration_ms=10)
        """
        if not self.is_initialized or not self.io_module:
            return False
        
        try:
            # Set trigger line HIGH
            if not self.io_module.out_line_write(self.out_card_no, self.out_port_id, camera_line, 1):
                return False
            
            # Hold pulse
            time.sleep(pulse_duration_ms / 1000.0)
            
            # Set trigger line LOW
            if not self.io_module.out_line_write(self.out_card_no, self.out_port_id, camera_line, 0):
                return False
            
            return True
        except Exception as e:
            print(f"Error sending hardware trigger: {e}")
            return False
    
    def wait_for_position_sensor(self, line_number: int, timeout_ms: int = 5000, 
                                 rising_edge: bool = True) -> bool:
        """
        Wait for position sensor to trigger (blocking).
        
        Args:
            line_number: Sensor line to monitor
            timeout_ms: Timeout in milliseconds
            rising_edge: True to wait for rising edge, False for falling edge
        
        Returns:
            True if sensor triggered within timeout
        
        Example:
            # Wait for chip to arrive at TOP station
            if io.wait_for_position_sensor(line_number=2, timeout_ms=5000):
                # Trigger camera and capture
                io.send_hardware_trigger(camera_line=0)
        """
        if not self.is_initialized or not self.io_module:
            return False
        
        edge_type = RISING_EDGE if rising_edge else FALLING_EDGE
        return self.io_module.wait_for_active_di_interrupt(
            self.in_card_no, self.in_port_id, timeout_ms, line_number, edge_type
        )
    
    def send_result(self, result: int, wait_timeout_ms: int = 5000) -> bool:
        """
        Send inspection result to hardware.
        
        This is Step 5 of the production workflow:
        1. Set busy bit
        2. Write result to output port
        3. Wait for handler acknowledgement
        4. Clear busy bit when acknowledged
        
        Args:
            result: Result code (RESULT_PASS, RESULT_FAIL_GENERAL, etc.)
            wait_timeout_ms: Timeout to wait for handler acknowledgement
        
        Returns:
            True if successful
        
        Production workflow example:
            # After inspection completes
            if inspection_result == PASS:
                io.send_result(RESULT_PASS)
            else:
                io.send_result(RESULT_FAIL_GENERAL)
        """
        if not self.is_initialized or not self.io_module:
            return False
        
        try:
            # Step 5A: Set busy bit + send result
            byte_value = encode_output_signal(busy=True, result=result)
            
            if not self.io_module.out_port_write(self.out_card_no, self.out_port_id, byte_value):
                print(f"Failed to write result signal: {byte_value}")
                return False
            
            print(f"Sent result signal: {byte_value} (busy=True, result={result})")
            
            # Step 5B: Wait for handler acknowledgement (blocking)
            print("Waiting for handler acknowledgement...")
            if not self.io_module.wait_for_active_di_interrupt(self.in_card_no, self.in_port_id, wait_timeout_ms):
                print("Timeout: Handler did not acknowledge")
                return False
            
            print("Handler acknowledged, clearing busy bit...")
            
            # Step 5C: Clear busy bit
            time.sleep(0.1)  # Small delay for handler to settle
            byte_value = encode_output_signal(busy=False, result=result)
            
            if not self.io_module.out_port_write(self.out_card_no, self.out_port_id, byte_value):
                print("Failed to clear busy bit")
                return False
            
            print("Busy bit cleared, ready for next part")
            return True
            
        except Exception as e:
            print(f"Error in send_result: {e}")
            return False
    
    def read_result_acknowledgement(self, timeout_ms: int = 5000) -> bool:
        """
        Wait for handler to acknowledge result (non-blocking alternative).
        
        Args:
            timeout_ms: Timeout in milliseconds
        
        Returns:
            True if acknowledgement received
        """
        if not self.is_initialized or not self.io_module:
            return False
        
        return self.io_module.wait_for_active_di_interrupt(
            self.in_card_no, self.in_port_id, timeout_ms
        )
    
    def clear_busy_bit(self) -> bool:
        """
        Clear busy bit to indicate ready for next part.
        
        Returns:
            True if successful
        """
        if not self.is_initialized or not self.io_module:
            return False
        
        try:
            byte_value = encode_output_signal(busy=False, result=RESULT_PASS)
            return self.io_module.out_port_write(self.out_card_no, self.out_port_id, byte_value)
        except Exception as e:
            print(f"Error clearing busy bit: {e}")
            return False
    
    def read_output_port(self) -> Optional[int]:
        """
        Read current output port value.
        
        Returns:
            Port value (0-255) or None if failed
        """
        if not self.is_initialized or not self.io_module:
            return None
        
        return self.io_module.out_port_read(self.out_card_no, self.out_port_id)
    
    def read_input_port(self) -> Optional[int]:
        """
        Read current input port value.
        
        Returns:
            Port value (0-255) or None if failed
        """
        if not self.is_initialized or not self.io_module:
            return None
        
        return self.io_module.in_port_read(self.in_card_no, self.in_port_id)
    
    def get_status(self) -> dict:
        """
        Get IO system status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "initialized": self.is_initialized,
            "dll_loaded": self.io_module.is_loaded if self.io_module else False,
            "in_card": self.in_card_no,
            "in_port": self.in_port_name,
            "out_card": self.out_card_no,
            "out_port": self.out_port_name,
        }
    
    def shutdown(self) -> None:
        """Clean up IO system."""
        if self.io_module:
            self.io_module.close()
        self.is_initialized = False
        print("IO system shut down")


# Global IO manager instance
_io_manager: Optional[IOManager] = None


def get_io_manager() -> IOManager:
    """Get or create global IO manager instance."""
    global _io_manager
    if _io_manager is None:
        _io_manager = IOManager()
    return _io_manager


def init_io_system() -> bool:
    """Initialize global IO system."""
    return get_io_manager().setup()


def shutdown_io_system() -> None:
    """Shutdown global IO system."""
    global _io_manager
    if _io_manager:
        _io_manager.shutdown()
        _io_manager = None
