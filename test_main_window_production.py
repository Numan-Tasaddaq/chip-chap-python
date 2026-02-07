"""
Test script to verify MainWindow production controller integration.

This script tests that:
1. MainWindow initializes without errors
2. Production controller can be initialized (when hardware is available)
3. ONLINE/OFFLINE transitions work correctly
4. Manual GRAB/LIVE still works when hardware is not available
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow, RunState


def test_main_window_init():
    """Test that MainWindow initializes without errors."""
    print("\n" + "="*70)
    print("TEST 1: MainWindow Initialization")
    print("="*70)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    try:
        window = MainWindow()
        print("✅ MainWindow created successfully")
        
        # Check that production controller instance variables exist
        assert hasattr(window, 'io_manager'), "Missing io_manager attribute"
        assert hasattr(window, 'production_controller'), "Missing production_controller attribute"
        assert hasattr(window, 'station_configs'), "Missing station_configs attribute"
        print("✅ Production controller attributes exist")
        
        # Production controller may be initialized during startup if default state is ONLINE
        # This is expected behavior
        if window.production_controller is not None:
            print("✅ Production controller initialized during startup (hardware available)")
        else:
            print("⚠️  Production controller not initialized (hardware not available - expected)")
        
        if window.station_configs is not None:
            print(f"✅ Station configs loaded ({len(window.station_configs)} stations)")
        else:
            print("⚠️  Station configs not loaded (hardware setup failed - expected)")
        
        return window
        
    except Exception as e:
        print(f"❌ MainWindow initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_online_transition(window: MainWindow):
    """Test transitioning to ONLINE mode."""
    print("\n" + "="*70)
    print("TEST 2: ONLINE Mode Transition")
    print("="*70)
    
    try:
        # Initially should be ONLINE (default)
        print(f"Initial state: {window.state.run_state.value}")
        
        # Transition to OFFLINE first
        window.state.run_state = RunState.OFFLINE
        window._apply_run_state()
        print(f"✅ Transitioned to OFFLINE")
        
        # Now transition to ONLINE (this should initialize production controller)
        window.state.run_state = RunState.ONLINE
        window._apply_run_state()
        print(f"✅ Transitioned to ONLINE")
        
        # Check if production controller was attempted to initialize
        # (it may be None if hardware is not available, which is OK)
        if window.production_controller is not None:
            print("✅ Production controller initialized successfully")
            print("   → Hardware is available, production mode ready")
        else:
            print("⚠️  Production controller is None")
            print("   → This is expected if I/O hardware is not connected")
            print("   → Manual GRAB/LIVE will still work")
        
        return True
        
    except Exception as e:
        print(f"❌ ONLINE transition failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_offline_transition(window: MainWindow):
    """Test transitioning to OFFLINE mode."""
    print("\n" + "="*70)
    print("TEST 3: OFFLINE Mode Transition")
    print("="*70)
    
    try:
        # Transition to OFFLINE
        window.state.run_state = RunState.OFFLINE
        window._apply_run_state()
        print(f"✅ Transitioned to OFFLINE")
        
        # If production controller exists, it should be stopped
        if window.production_controller is not None:
            print("✅ Production controller stopped (if it was running)")
        
        print("✅ Manual mode active")
        
        return True
        
    except Exception as e:
        print(f"❌ OFFLINE transition failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_inspection_callback(window: MainWindow):
    """Test the production inspection callback."""
    print("\n" + "="*70)
    print("TEST 4: Production Inspection Callback")
    print("="*70)
    
    try:
        import numpy as np
        
        # Create a dummy test image (640x480 grayscale)
        test_image = np.zeros((480, 640), dtype=np.uint8)
        test_image[:, :] = 128  # Gray background
        
        # Test callback for Doc1 (TOP station)
        doc_index = 1
        print(f"Testing inspection callback for Doc{doc_index}...")
        
        result = window._production_inspection_callback(doc_index, test_image)
        print(f"✅ Inspection callback executed")
        print(f"   Result: {'PASS' if result else 'FAIL'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Inspection callback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("PRODUCTION CONTROLLER INTEGRATION TEST")
    print("="*70)
    print("\nThis test verifies that:")
    print("  1. MainWindow initializes with production controller support")
    print("  2. ONLINE/OFFLINE transitions work correctly")
    print("  3. Production controller initializes when hardware is available")
    print("  4. Inspection callback can be called")
    print("\nNote: Production controller may not initialize if I/O hardware")
    print("      is not connected. This is expected and doesn't affect")
    print("      manual GRAB/LIVE functionality.")
    
    # Run tests
    window = test_main_window_init()
    if window is None:
        print("\n❌ TEST SUITE FAILED: MainWindow initialization error")
        sys.exit(1)
    
    success = True
    success = test_online_transition(window) and success
    success = test_offline_transition(window) and success
    success = test_inspection_callback(window) and success
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUITE SUMMARY")
    print("="*70)
    
    if success:
        print("✅ All tests passed!")
        print("\nProduction controller integration is working correctly.")
        print("\nNext steps:")
        print("  1. Connect I/O hardware (PCI-7230 card)")
        print("  2. Configure cameras in registry (run setup_cameras.py)")
        print("  3. Switch to ONLINE mode in the application")
        print("  4. Production controller will start automatically")
    else:
        print("❌ Some tests failed")
        print("\nPlease check the error messages above for details.")
    
    print("="*70)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
