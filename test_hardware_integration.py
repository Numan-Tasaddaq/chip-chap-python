"""
Test Hardware Integration - Production Controller with I/O and Cameras

Tests the complete hardware-triggered inspection workflow:
1. Initialize I/O system (PCI-7230 card)
2. Initialize camera system (MVS cameras Doc1-Doc7)
3 Configure station triggers (position sensors + camera triggers)
4. Start production loop
5. Monitor position sensors
6. Trigger cameras on position detection
7. Run inspection (mock for this test)
8. Send results to handler

Prerequisites:
- PCI-7230 I/O card installed and drivers loaded
- MVS cameras configured in Windows Registry (run setup_cameras.py)
- I/O configuration in registry (run one of test_io_*.py)
"""

import sys
import time
import numpy as np

from device.io_manager import IOManager, get_io_manager, init_io_system
from device.production_controller import ProductionController, configure_standard_7_station_system
from device.camera_registry import CameraRegistry
from config.station_trigger_config import StationTriggerConfigManager
from imaging.grab_service import GrabService


def mock_inspection_callback(doc_index: int, frame: np.ndarray) -> bool:
    """
    Mock inspection function for testing.
    
    Args:
        doc_index: Station Doc index (1-7)
        frame: Captured image
    
    Returns:
        True (always pass for testing)
    """
    station_name = CameraRegistry.get_station_name(doc_index)
    print(f"[INSPECTION] Doc{doc_index} ({station_name}): Frame {frame.shape} - PASS (mock)")
    return True  # Always pass for testing


def test_hardware_integration():
    """Test complete hardware integration."""
    print("=" * 70)
    print("Hardware Integration Test - Production Controller")
    print("=" * 70)
    print()
    
    # Step 1: Initialize I/O system
    print("[STEP 1] Initializing I/O system...")
    io_manager = get_io_manager()
    
    if not io_manager.setup():
        print("❌ Failed to initialize I/O system")
        print("   Please check:")
        print("   - PCI-7230 card is installed")
        print("   - Drivers are loaded")
        print("   - Registry is configured (run test_io_registry.py)")
        return False
    
    print("✅ I/O system initialized")
    print(f"   Status: {io_manager.get_status()}")
    print()
    
    # Step 2: Load station trigger configuration
    print("[STEP 2] Loading station trigger configuration...")
    station_configs = StationTriggerConfigManager.load_config()
    
    if not station_configs:
        print("❌ Failed to load station configurations")
        return False
    
    print(f"✅ Loaded {len(station_configs)} station configurations")
    for doc_idx, config in station_configs.items():
        print(f"   Doc{doc_idx} ({config.station_name}): "
              f"sensor_line={config.position_sensor_line}, "
              f"trigger_line={config.camera_trigger_line}, "
              f"enabled={config.enabled}")
    print()
    
    # Step 3: Check camera registry
    print("[STEP 3] Checking camera registry...")
    cameras = CameraRegistry.read_registry()
    
    if not cameras:
        print("⚠️  No cameras configured in registry")
        print("   Run: python setup_cameras.py")
        print("   Continuing with test anyway...")
    else:
        print(f"✅ Found {len(cameras)} cameras in registry:")
        for doc_idx, serial in cameras.items():
            station = CameraRegistry.get_station_name(doc_idx)
            print(f"   Doc{doc_idx} ({station}): {serial}")
    print()
    
    # Step 4: Create production controller
    print("[STEP 4] Creating production controller...")
    
    # Create a minimal GrabService (we won't use it much in production controller)
    # Production controller captures directly for better hardware trigger timing
    grab_service = None  # We handle cameras directly in production_controller
    
    controller = ProductionController(io_manager, grab_service)
    
    # Configure stations from loaded config
    for doc_idx, config in station_configs.items():
        if config.enabled:
            controller.configure_station(
                doc_index=config.doc_index,
                position_sensor_line=config.position_sensor_line,
                camera_trigger_line=config.camera_trigger_line,
                ejector_distance=config.ejector_distance,
                use_hardware_trigger=config.use_hardware_trigger
            )
    
    print("✅ Production controller configured")
    print()
    
    # Step 5: Set inspection callback
    print("[STEP 5] Setting inspection callback...")
    controller.set_inspection_callback(mock_inspection_callback)
    print("✅ Inspection callback set (using mock for testing)")
    print()
    
    # Step 6: Test menu
    print("=" * 70)
    print("HARDWARE INTEGRATION TEST MENU")
    print("=" * 70)
    print()
    print("Options:")
    print("  [1] Test position sensor reading (single station)")
    print("  [2] Test hardware trigger output (single pulse)")
    print("  [3] Test single-station capture (sensor → trigger → capture)")
    print("  [4] Start production loop (all stations, hardware-triggered)")
    print("  [5] View statistics")
    print("  [Q] Quit")
    print()
    
    while True:
        choice = input("Your choice: ").strip().upper()
        
        if choice == "1":
            # Test position sensor
            print("\n[TEST 1] Position Sensor Test")
            station_input = input("Enter station Doc index (1-7): ").strip()
            try:
                doc_idx = int(station_input)
                if doc_idx not in station_configs:
                    print(f"Invalid Doc index: {doc_idx}")
                    continue
                
                config = station_configs[doc_idx]
                print(f"Waiting for position sensor on line {config.position_sensor_line}...")
                print("(Timeout: 10 seconds)")
                
                triggered = io_manager.wait_for_position_sensor(
                    line_number=config.position_sensor_line,
                    timeout_ms=10000,
                    rising_edge=True
                )
                
                if triggered:
                    print(f"✅ Position sensor triggered on line {config.position_sensor_line}")
                else:
                    print("⏱️  Timeout - no sensor trigger detected")
                    
            except ValueError:
                print("Invalid input")
            print()
        
        elif choice == "2":
            # Test hardware trigger
            print("\n[TEST 2] Hardware Trigger Test")
            line_input = input("Enter camera trigger line (0-7): ").strip()
            try:
                trigger_line = int(line_input)
                print(f"Sending trigger pulse on line {trigger_line}...")
                
                success = io_manager.send_hardware_trigger(
                    camera_line=trigger_line,
                    pulse_duration_ms=10.0
                )
                
                if success:
                    print(f"✅ Trigger pulse sent on line {trigger_line}")
                else:
                    print(f"❌ Failed to send trigger pulse")
                    
            except ValueError:
                print("Invalid input")
            print()
        
        elif choice == "3":
            # Test single-station capture
            print("\n[TEST 3] Single-Station Capture Test")
            print("This will:")
            print("  1. Wait for position sensor")
            print("  2. Send hardware trigger to camera")
            print("  3. Capture image")
            print("  4. Run mock inspection")
            print()
            
            station_input = input("Enter station Doc index (1-7): ").strip()
            try:
                doc_idx = int(station_input)
                if doc_idx not in station_configs:
                    print(f"Invalid Doc index: {doc_idx}")
                    continue
                
                config = station_configs[doc_idx]
                print(f"\nTesting {config.station_name} (Doc{doc_idx})...")
                print(f"Waiting for position sensor (line {config.position_sensor_line})...")
                
                # This would be handled by production controller in real use
                # For now just show the concept
                print("⚠️  Full capture test requires cameras connected")
                print("   Use option [4] to start full production loop")
                
            except ValueError:
                print("Invalid input")
            print()
        
        elif choice == "4":
            # Start production loop
            print("\n[TEST 4] Production Loop")
            print("Starting hardware-triggered production for all enabled stations...")
            print("Press Ctrl+C to stop")
            print()
            
            if not controller.start_production():
                print("❌ Failed to start production")
                continue
            
            try:
                # Run until interrupted
                while True:
                    time.sleep(1)
                    stats = controller.get_statistics()
                    print(f"\r[STATS] Inspected: {stats['total_inspected']}, "
                          f"Passed: {stats['total_passed']}, "
                          f"Failed: {stats['total_failed']}", end='', flush=True)
            
            except KeyboardInterrupt:
                print("\n\nStopping production...")
                controller.stop_production()
                print("✅ Production stopped")
                
                stats = controller.get_statistics()
                print(f"\nFinal Statistics:")
                print(f"  Total Inspected: {stats['total_inspected']}")
                print(f"  Total Passed: {stats['total_passed']}")
                print(f"  Total Failed: {stats['total_failed']}")
            
            print()
        
        elif choice == "5":
            # View statistics
            print("\n[TEST 5] Statistics")
            stats = controller.get_statistics()
            print(f"  Total Inspected: {stats['total_inspected']}")
            print(f"  Total Passed: {stats['total_passed']}")
            print(f"  Total Failed: {stats['total_failed']}")
            
            reset = input("\nReset statistics? (Y/N): ").strip().upper()
            if reset == "Y":
                controller.reset_statistics()
                print("✅ Statistics reset")
            print()
        
        elif choice == "Q":
            print("\nExiting...")
            break
        
        else:
            print("Invalid choice")
            print()
    
    # Cleanup
    print("\nCleaning up...")
    if controller.is_running:
        controller.stop_production()
    io_manager.shutdown()
    print("✅ Cleanup complete")
    
    return True


if __name__ == "__main__":
    try:
        success = test_hardware_integration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
