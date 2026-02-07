# test_io_port_config.py - Test 2: Port Configuration
from device.io_interface import IOModule
from device.io_constants import PORT_1A, PORT_1B, PORT_2A, PORT_2B

def test_port_config():
    print("="*70)
    print("TEST 2: Port Configuration")
    print("="*70)
    
    try:
        io = IOModule(dll_name="PCI7230")
        
        # Initialize IO
        result = io.init_io_dll()
        print(f"DLL Initialization: {'✅ OK' if result == 0 else '❌ FAILED'}")
        
        if result != 0:
            print(f"⚠️  DLL init returned {result}, may not have hardware")
        
        # Test port ID constants
        print(f"\nPort ID Constants:")
        print(f"  PORT_1A = {PORT_1A}")
        print(f"  PORT_1B = {PORT_1B}")
        print(f"  PORT_2A = {PORT_2A}")
        print(f"  PORT_2B = {PORT_2B}")
        
        # Verify port IDs are in valid range (1-12)
        assert 1 <= PORT_1A <= 12, f"PORT_1A out of range: {PORT_1A}"
        assert 1 <= PORT_1B <= 12, f"PORT_1B out of range: {PORT_1B}"
        assert 1 <= PORT_2A <= 12, f"PORT_2A out of range: {PORT_2A}"
        assert 1 <= PORT_2B <= 12, f"PORT_2B out of range: {PORT_2B}"
        
        print("\n✅ TEST 2 PASSED - Port configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_port_config()
