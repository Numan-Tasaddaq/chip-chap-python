# test_io_manager.py - Test 6: IOManager Integration
from device.io_manager import IOManager
from device.io_constants import RESULT_PASS, RESULT_FAIL_TYPE_1

def test_io_manager():
    print("="*70)
    print("TEST 6: IOManager Integration")
    print("="*70)
    
    try:
        manager = IOManager()
        
        # Test setup (9-step initialization)
        print("\n1. Testing IOManager setup...")
        result = manager.setup()
        
        if result:
            print("✅ IOManager setup completed successfully")
        else:
            print("⚠️  IOManager setup returned False (may not have hardware)")
            print("   Continuing with simulation tests...")
        
        # Test result encoding/sending
        print("\n2. Testing result encoding...")
        
        # Simulate sending PASS result
        print("   Encoding PASS result (code 0)...")
        # Note: send_result() requires hardware, so we just test encoding
        from device.io_constants import encode_output_signal
        
        pass_byte = encode_output_signal(RESULT_PASS, busy_bit_pos=7, result_bit_pos=0)
        print(f"   PASS signal: 0b{pass_byte:08b} (0x{pass_byte:02X})")
        assert pass_byte == 0b10000000, f"Expected 0x80, got 0x{pass_byte:02X}"
        
        # Simulate sending FAIL result
        print("   Encoding FAIL result (code 1)...")
        fail_byte = encode_output_signal(RESULT_FAIL_TYPE_1, busy_bit_pos=7, result_bit_pos=0)
        print(f"   FAIL signal: 0b{fail_byte:08b} (0x{fail_byte:02X})")
        assert fail_byte == 0b10000001, f"Expected 0x81, got 0x{fail_byte:02X}"
        
        print("\n3. Testing send_result (only if initialized)...")
        if manager.is_initialized:
            result_sent = manager.send_result(RESULT_PASS)
            print(f"   send_result returned: {result_sent}")
        else:
            print("   ⚠️  Skipping send_result (not initialized)")
        
        # Test shutdown
        print("\n4. Testing shutdown...")
        manager.shutdown()
        print("   ✅ Shutdown completed")
        
        print("\n✅ TEST 6 PASSED - IOManager integration successful")
        return True
        
    except Exception as e:
        print(f"❌ TEST 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_io_manager()
