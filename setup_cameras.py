"""
Camera Setup Script - Configure MVS cameras in Windows Registry

Run this script after connecting your MVS cameras to set up the serial numbers
in the Windows Registry so the application can find them.
"""

from device.mvs_camera import MVSCamera
from device.camera_registry import CameraRegistry


def main():
    print("=" * 70)
    print("MVS Camera Setup - Configure Camera Serial Numbers")
    print("=" * 70)
    
    # Step 1: Enumerate connected cameras
    print("\n[STEP 1] Enumerating connected MVS cameras...")
    cameras = MVSCamera.enumerate_cameras()
    
    if not cameras:
        print("\n⚠️  WARNING: No MVS cameras detected!")
        print("\nPlease check:")
        print("  1. Camera is connected (USB/GigE cable)")
        print("  2. Camera is powered on")
        print("  3. MVS driver is installed correctly")
        print("  4. Camera appears in Windows Device Manager")
        return
    
    print(f"\n✅ Found {len(cameras)} camera(s):\n")
    for idx, (serial, model) in enumerate(cameras, 1):
        print(f"  [{idx}] {model}")
        print(f"      Serial Number: {serial}")
    
    # Step 2: Show current registry configuration
    print("\n" + "=" * 70)
    print("[STEP 2] Current camera configuration in Windows Registry:")
    print("=" * 70 + "\n")
    CameraRegistry.print_registry()
    
    # Step 3: Configure cameras
    print("\n" + "=" * 70)
    print("[STEP 3] Camera Configuration")
    print("=" * 70)
    print("\nDoc/Station Mapping:")
    print("  Doc1 → TOP (Track 1)")
    print("  Doc2 → BOTTOM (Track 2)")
    print("  Doc3 → FEED")
    print("  Doc4 → PICKUP1")
    print("  Doc5 → PICKUP2")
    print("  Doc6 → BOTTOM_SEAL")
    print("  Doc7 → TOP_SEAL")
    
    print("\n" + "-" * 70)
    print("Options:")
    print("  [1] Auto-configure (assign cameras to Doc1, Doc2, ... in order)")
    print("  [2] Manual configuration (choose Doc index for each camera)")
    print("  [3] Skip configuration (just view current setup)")
    print("  [Q] Quit")
    
    choice = input("\nYour choice: ").strip().upper()
    
    if choice == "1":
        # Auto-configure
        print("\n[AUTO-CONFIGURE] Assigning cameras to Doc1, Doc2, etc...")
        for idx, (serial, model) in enumerate(cameras, 1):
            if idx > 7:
                print(f"  ⚠️  Skipping camera {idx} (only Doc1-Doc7 supported)")
                break
            
            # Determine if color camera (USB4CT = color, USB3CT = mono)
            is_color = "USB4CT" in model or "Color" in model.upper()
            
            success = CameraRegistry.write_registry(
                idx, serial, model=model, is_color=is_color
            )
            if success:
                station = CameraRegistry.get_station_name(idx)
                camera_type = "Color" if is_color else "Mono"
                print(f"  ✅ Doc{idx} ({station}) → {serial} ({model} - {camera_type})")
        
        print("\n✅ Auto-configuration complete!")
        
    elif choice == "2":
        # Manual configuration
        print("\n[MANUAL CONFIGURATION]")
        for idx, (serial, model) in enumerate(cameras, 1):
            print(f"\nCamera {idx}: {model} (SN: {serial})")
            while True:
                doc_idx = input(f"  Assign to Doc index (1-7, or S to skip): ").strip().upper()
                
                if doc_idx == "S":
                    print("  ⏭️  Skipped")
                    break
                
                try:
                    doc_num = int(doc_idx)
                    if 1 <= doc_num <= 7:
                        station = CameraRegistry.get_station_name(doc_num)
                        confirm = input(f"  Assign to Doc{doc_num} ({station})? (Y/N): ").strip().upper()
                        if confirm == "Y":
                            # Determine if color camera
                            is_color = "USB4CT" in model or "Color" in model.upper()
                            
                            success = CameraRegistry.write_registry(
                                doc_num, serial, model=model, is_color=is_color
                            )
                            if success:
                                camera_type = "Color" if is_color else "Mono"
                                print(f"  ✅ Assigned to Doc{doc_num} ({station}) - {camera_type}")
                            break
                    else:
                        print("  ❌ Invalid. Enter 1-7")
                except ValueError:
                    print("  ❌ Invalid input")
        
        print("\n✅ Manual configuration complete!")
        
    elif choice == "3":
        print("\n⏭️  Configuration skipped")
        
    else:
        print("\n👋 Exiting...")
        return
    
    # Step 4: Verify final configuration
    print("\n" + "=" * 70)
    print("[STEP 4] Final Camera Configuration:")
    print("=" * 70 + "\n")
    CameraRegistry.print_registry()
    
    print("\n" + "=" * 70)
    print("✅ Setup Complete!")
    print("=" * 70)
    print("\nYou can now:")
    print("  • Run the main application")
    print("  • Click GRAB button to capture single frame")
    print("  • Click LIVE button for continuous preview")
    print("\nNote: Make sure you're in ONLINE mode and correct Track is selected")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
