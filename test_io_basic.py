# test_io_basic.py
from device.io_interface import IOModule

def test_dll_loading():
    print("="*70)
    print("TEST 1: DLL Loading and Initialization")
    print("="*70)
    
    try:
        io = IOModule()
        print("✅ DLL loaded successfully")
        
        # Test initialization
        if io.init_io_dll():
            print("✅ InitIODLL() successful")
        else:
            print("❌ InitIODLL() failed")
            return False
        
        # Test card registration
        if io.reg_io_card():
            print("✅ RegIOCard() successful")
        else:
            print("❌ RegIOCard() failed")
            return False
        
        print("\n✅ TEST 1 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_dll_loading()
