"""
IO System Usage Examples
Demonstrates how to use the IO module in your application
"""

from device.io_manager import init_io_system, get_io_manager, shutdown_io_system
from device.io_constants import (
    RESULT_PASS, RESULT_FAIL_GENERAL, RESULT_FAIL_TYPE_1,
    PORT_1A
)


def example_1_basic_initialization():
    """Example 1: Basic IO system initialization"""
    
    print("\n=== Example 1: Basic IO Initialization ===\n")
    
    # Initialize IO system (reads registry, loads DLL, configures ports)
    if not init_io_system():
        print("Failed to initialize IO system")
        return
    
    # Get IO manager instance
    io = get_io_manager()
    
    # Check status
    status = io.get_status()
    print(f"IO Status: {status}")
    
    # Cleanup
    shutdown_io_system()


def example_2_send_result():
    """Example 2: Send inspection result to hardware"""
    
    print("\n=== Example 2: Send Result with Handler Handshake ===\n")
    
    if not init_io_system():
        print("Failed to initialize IO system")
        return
    
    io = get_io_manager()
    
    # Simulate inspection completing with PASS result
    inspection_result = RESULT_PASS
    
    # Send result to hardware (blocking - waits for handler acknowledgement)
    print(f"Sending inspection result: {inspection_result}")
    
    success = io.send_result(inspection_result, wait_timeout_ms=5000)
    
    if success:
        print("Result sent and handler acknowledged successfully")
    else:
        print("Failed to send result or handler did not acknowledge in time")
    
    shutdown_io_system()


def example_3_manual_control():
    """Example 3: Manual port read/write control"""
    
    print("\n=== Example 3: Manual Port Control ===\n")
    
    if not init_io_system():
        print("Failed to initialize IO system")
        return
    
    io = get_io_manager()
    
    # Manually write to output port
    print("Writing 0xFF to output port...")
    io.io_module.out_port_write(io.out_card_no, io.out_port_id, 0xFF)
    
    # Read back the value
    import time
    time.sleep(0.1)
    value = io.read_output_port()
    print(f"Read back from output port: 0x{value:02X}")
    
    # Read input port
    input_value = io.read_input_port()
    print(f"Read from input port: 0x{input_value:02X}")
    
    shutdown_io_system()


def example_4_integration_with_inspection():
    """Example 4: Integration with inspection loop (production-like)"""
    
    print("\n=== Example 4: Production Loop Integration ===\n")
    
    if not init_io_system():
        print("Failed to initialize IO system")
        return
    
    io = get_io_manager()
    
    # Simulate production loop
    for part_number in range(1, 4):
        print(f"\n--- Part {part_number} ---")
        
        # Step 1: Capture image and analyze (simulated)
        print("1. Capturing image...")
        import time
        time.sleep(0.5)
        
        # Step 2: Run inspection algorithm (simulated)
        print("2. Running inspection...")
        time.sleep(1.0)
        
        # Step 3: Determine result
        if part_number == 1:
            result = RESULT_PASS
            print(f"3. Result: PASS")
        elif part_number == 2:
            result = RESULT_FAIL_TYPE_1
            print(f"3. Result: FAIL_TYPE_1")
        else:
            result = RESULT_FAIL_GENERAL
            print(f"3. Result: FAIL_GENERAL")
        
        # Step 4-5: Send result and wait for handler
        print("4-5. Sending result to hardware and waiting for handler...")
        if io.send_result(result, wait_timeout_ms=5000):
            print("6. Handler acknowledged, ready for next part")
        else:
            print("ERROR: Handler did not acknowledge in time!")
            break
    
    print("\nProduction loop complete")
    shutdown_io_system()


def example_5_diagnostic():
    """Example 5: IO diagnostic - monitor signals in real-time"""
    
    print("\n=== Example 5: Real-time IO Diagnostic ===\n")
    
    if not init_io_system():
        print("Failed to initialize IO system")
        return
    
    io = get_io_manager()
    
    print("Monitoring IO signals for 10 seconds...")
    print("(Equivalent to IODiagDlg in old system)")
    print()
    
    import time
    start_time = time.time()
    
    while time.time() - start_time < 10:
        # Read both input and output ports
        out_val = io.read_output_port()
        in_val = io.read_input_port()
        
        if out_val is not None and in_val is not None:
            # Display as binary
            print(f"Output: 0x{out_val:02X} (0b{out_val:08b})  |  " + 
                  f"Input: 0x{in_val:02X} (0b{in_val:08b})", end="\r")
        
        time.sleep(0.5)
    
    print()
    shutdown_io_system()


if __name__ == "__main__":
    # Run examples
    example_1_basic_initialization()
    # example_2_send_result()
    # example_3_manual_control()
    # example_4_integration_with_inspection()
    # example_5_diagnostic()
    
    print("\n=== All examples completed ===\n")
