"""
Test script to verify camera power and live feed
"""
import sys
from device.mvs_camera import MVSCamera
import time

print("=" * 70)
print("Camera Live Feed Test")
print("=" * 70)

# Step 1: Enumerate cameras
print("\n[STEP 1] Enumerating cameras...")
cameras = MVSCamera.enumerate_cameras()

if not cameras:
    print("❌ No cameras found!")
    print("\nTroubleshooting:")
    print("  1. Camera power LED on?")
    print("  2. USB cable connected?")
    print("  3. Device Manager shows camera?")
    print("  4. MVS SDK DLL exists?")
    sys.exit(1)

print(f"✅ Found {len(cameras)} camera(s):")
for idx, (serial, model) in enumerate(cameras):
    print(f"  [{idx}] {model} (SN: {serial})")

# Step 2: Open first camera
print(f"\n[STEP 2] Opening camera...")
serial = cameras[0][0]
model = cameras[0][1]

camera = MVSCamera()
if not camera.open_camera(serial):
    print(f"❌ Failed to open camera {serial}")
    sys.exit(1)

print(f"✅ Camera opened: {model}")

# Step 3: Start grabbing
print(f"\n[STEP 3] Starting live grab...")
if not camera.start_grabbing():
    print("❌ Failed to start grabbing")
    camera.close_camera()
    sys.exit(1)

print("✅ Grabbing started")

# Step 4: Try to grab frames
print(f"\n[STEP 4] Grabbing frames for 5 seconds...")
try:
    for i in range(5):
        frame = camera.grab_frame(timeout_ms=2000)
        if frame is None:
            print(f"  Frame {i+1}: ❌ No frame")
        else:
            print(f"  Frame {i+1}: ✅ {frame.shape[0]}x{frame.shape[1]} pixels")
        time.sleep(1)
except KeyboardInterrupt:
    print("\n⏸️  Interrupted by user")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Cleanup
print(f"\n[STEP 5] Closing camera...")
camera.stop_grabbing()
camera.close_camera()
print("✅ Camera closed")

print("\n" + "=" * 70)
print("✅ Test Complete!")
print("=" * 70)
print("""
Results:
  ✅ Camera detected = Camera connected and MVS SDK working
  ✅ Camera opened = Camera accessible
  ✅ Frames grabbed = Camera is powered and transmitting
  
If you saw frames above, camera is working!
Next: Run setup_cameras.py to register it.
""")
