# Camera System Testing Guide - Step by Step

## Prerequisites on Camera System

Before starting, ensure:
- ✓ USB3 Vision cameras physically connected
- ✓ Teli USB3 Vision drivers installed (SDK already on system)
- ✓ Python 3.12 installed
- ✓ No other camera application running (close any camera viewers)

---

## Step 1: Transfer Files to Camera System

### Option A: Network Share (Easiest)
```powershell
# On camera system, create destination folder
New-Item -ItemType Directory -Force -Path "C:\ChipResistor"

# Copy from development machine (replace with your network path)
robocopy "\\DEV-PC\share\chip-chap-python" "C:\ChipResistor" /E /Z
```

### Option B: USB Drive
1. Copy entire `chip-chap-python` folder to USB drive
2. On camera system, copy to `C:\ChipResistor`

### Option C: Remote Desktop
1. Connect to camera system via RDP with drive mapping
2. Copy folder directly through RDP session

---

## Step 2: Install Python Dependencies

```powershell
# On camera system, open PowerShell as Administrator
cd C:\ChipResistor

# Install required packages
pip install numpy opencv-python PyQt5 pywin32
```

---

## Step 3: Verify SDK Files Present

```powershell
# Check SDK DLLs are copied
Get-ChildItem "C:\ChipResistor\sdk\teli\*.dll"
```

**Expected output:**
```
TeliCamApi64.dll
TeliCamUtl64.dll
GenApi_MD_VC120_v3_0.dll
GCBase_MD_VC120_v3_0.dll
```

---

## Step 4: Test Camera Detection

```powershell
cd C:\ChipResistor
python device/teli_camera.py
```

**Success Output Example:**
```
=== Teli Camera SDK Test ===

✓ Teli SDK loaded: C:\ChipResistor\sdk\teli\TeliCamApi64.dll
Camera count: 2

Found 2 camera(s):

  Index 0:
    Vendor: TOSHIBA TELI
    Model: BU030
    Serial: 17E11506
    User Name: 
    Version: 1.0
    Type: 1

  Index 1:
    Vendor: TOSHIBA TELI
    Model: BU040
    Serial: 17F10217
    User Name: 
    Version: 1.0
    Type: 1
```

**If you see this, SDK integration is working! ✓**

---

## Step 5: Verify Serial Numbers Match Registry

```powershell
# Check Track1 camera serial
reg query "HKLM\SOFTWARE\iTrue\hardware" /v Track1CameraSerialNum

# Check Track2 camera serial  
reg query "HKLM\SOFTWARE\iTrue\hardware" /v Track2CameraSerialNum
```

**Compare registry values with detected cameras in Step 4.**

Example:
- Registry Track1: `17E11506` → Should match one of the detected cameras
- Registry Track2: `17F10217` → Should match the other camera

---

## Step 6: Test Camera Open by Serial

Create test script `test_camera_open.py`:

```python
from device.teli_camera import TeliCamera

# Replace with your actual serial numbers from registry
TRACK1_SERIAL = "17E11506"  
TRACK2_SERIAL = "17F10217"

print("Testing camera opening by serial number...\n")

# Test Track1 camera
print(f"Opening Track1 camera: {TRACK1_SERIAL}")
try:
    teli1 = TeliCamera()
    teli1.open_by_serial(TRACK1_SERIAL)
    print("✓ Track1 camera opened successfully")
    teli1.close()
    print("✓ Track1 camera closed\n")
except Exception as e:
    print(f"✗ Track1 camera failed: {e}\n")

# Test Track2 camera
print(f"Opening Track2 camera: {TRACK2_SERIAL}")
try:
    teli2 = TeliCamera()
    teli2.open_by_serial(TRACK2_SERIAL)
    print("✓ Track2 camera opened successfully")
    teli2.close()
    print("✓ Track2 camera closed\n")
except Exception as e:
    print(f"✗ Track2 camera failed: {e}\n")

print("Camera open test complete!")
```

**Run the test:**
```powershell
python test_camera_open.py
```

**Expected output:**
```
Testing camera opening by serial number...

Opening Track1 camera: 17E11506
✓ Teli SDK loaded: C:\ChipResistor\sdk\teli\TeliCamApi64.dll
✓ Camera opened by serial: 17E11506
✓ Track1 camera closed

Opening Track2 camera: 17F10217
✓ Teli SDK loaded: C:\ChipResistor\sdk\teli\TeliCamApi64.dll
✓ Camera opened by serial: 17F10217
✓ Track2 camera closed

Camera open test complete!
```

---

## Step 7: Test Basic Acquisition

Create test script `test_camera_grab.py`:

```python
from device.teli_camera import TeliCamera
import time

TRACK1_SERIAL = "17E11506"  # Replace with your serial

print("Testing camera acquisition...\n")

try:
    teli = TeliCamera()
    teli.open_by_serial(TRACK1_SERIAL)
    
    print("Starting acquisition...")
    teli.start_grab()
    print("✓ Acquisition started")
    
    # Run for 3 seconds
    print("Acquiring for 3 seconds...")
    time.sleep(3)
    
    print("Stopping acquisition...")
    teli.stop_grab()
    print("✓ Acquisition stopped")
    
    teli.close()
    print("✓ Test complete!")
    
except Exception as e:
    print(f"✗ Test failed: {e}")
    import traceback
    traceback.print_exc()
```

**Run the test:**
```powershell
python test_camera_grab.py
```

**Expected output:**
```
Testing camera acquisition...

✓ Teli SDK loaded: C:\ChipResistor\sdk\teli\TeliCamApi64.dll
✓ Camera opened by serial: 17E11506
Starting acquisition...
✓ Acquisition started
Acquiring for 3 seconds...
Stopping acquisition...
✓ Acquisition stopped
✓ Camera closed
✓ Test complete!
```

---

## Step 8: Check Registry Integration

```powershell
# Verify camera registry can read serial numbers
python -c "from device.camera_registry import CameraRegistry; reg = CameraRegistry(); print(f'Track1: {reg.get_track1_serial()}'); print(f'Track2: {reg.get_track2_serial()}')"
```

**Expected output:**
```
Track1: 17E11506
Track2: 17F10217
```

---

## Step 9: Test Main Application - Camera Configuration

```powershell
# Launch the main application
python main.py
```

**Test Camera Configuration Dialog:**
1. Click **Camera Configuration** menu item
2. You should see current camera settings:
   - Shutter (Exposure Time)
   - Gain
   - Brightness (Black Level)
   - AOI (Width, Height, X, Y offsets)
   - Bytes Per Packet
3. Adjust some settings (e.g., change Shutter from 3 to 10)
4. Click **OK** 
5. Settings saved to `.cam` file (e.g., `Track1.cam` in config directory)

**Verify .cam File:**
```powershell
# Check that .cam file was created/updated
$config = "YourConfigName"  # Replace with actual config name
Get-Content "Inspection\$config\Track1.cam"
```

Should see INI format:
```ini
[CamSettingTrack1]
Aperture=10
Gain=4
Brightness=1
...
```

---

## Step 10: Test GRAB Button (Single Frame Capture)

**This is the critical test - GRAB now uses Teli SDK!**

```powershell
# Make sure application is running (python main.py)
```

**In the application:**
1. Ensure you're in **ONLINE** mode (not OFFLINE/SIMULATOR)
2. Select **Track 1** (or Track 2)
3. Click **GRAB** button

**Expected Console Output:**
```
[CAMERA] Opening camera: 17E11506
✓ Teli SDK loaded: C:\ChipResistor\sdk\teli\TeliCamApi64.dll
✓ Camera opened by serial: 17E11506
✓ Camera settings applied
✓ Camera closed
```

**Expected Result:**
- ✓ Camera image appears in main window
- ✓ Image grabbed using Teli SDK (not OpenCV)
- ✓ Settings from .cam file applied to hardware
- ✓ Camera automatically closed after capture

**If you see black image:**
- Exposure time might be too short
- Check lighting conditions
- Try increasing Shutter value in Camera Configuration

---

## Step 11: Test LIVE Button (Continuous Acquisition)

**LIVE now uses Teli SDK with continuous streaming!**

**In the application:**
1. Ensure you're in **ONLINE** mode
2. Select **Track 1** (or Track 2)
3. Click **LIVE** button

**Expected Console Output:**
```
[CAMERA] Opening camera for LIVE: 17E11506
✓ Teli SDK loaded: C:\ChipResistor\sdk\teli\TeliCamApi64.dll
✓ Camera opened by serial: 17E11506
✓ Camera settings applied
[CAMERA] Teli LIVE started
```

**Expected Result:**
- ✓ Live video feed appears (~30 FPS)
- ✓ Continuous frames from Teli camera
- ✓ Settings applied from .cam file
- ✓ Smooth video playback

**To Stop LIVE:**
- Click **LIVE** button again (toggles off)

**Expected Console Output:**
```
✓ Camera closed
```

---

## Step 12: Test Settings Application

**Verify camera settings are actually applied to hardware:**

1. **Change Exposure in Camera Configuration:**
   - Open Camera Configuration
   - Set Shutter (Exposure) to **50** microseconds
   - Click OK

2. **Capture with GRAB:**
   - Click GRAB button
   - Image should be brighter (longer exposure)

3. **Change Exposure Again:**
   - Open Camera Configuration
   - Set Shutter to **1** microsecond
   - Click OK

4. **Capture with GRAB:**
   - Click GRAB button
   - Image should be darker (shorter exposure)

**This proves settings are being written to hardware!**

---

## Step 13: Test Track Switching

**Verify both cameras work independently:**

1. **Select Track 1:**
   - Click GRAB
   - Note serial number in console (e.g., 17E11506)
   - Note image content

2. **Select Track 2:**
   - Click GRAB
   - Note serial number in console (e.g., 17F10217)
   - Note image content (should be different camera view)

**Each track should open its own camera by serial number!**

---

## Troubleshooting

### Problem: "Failed to get camera count (error: 1)"

**Possible causes:**
- No cameras physically connected
- USB cable loose
- Driver not installed
- Camera powered off

**Solutions:**
```powershell
# Check USB devices
Get-PnpDevice | Where-Object {$_.FriendlyName -like "*Teli*"}

# Should show cameras like:
# OK    Toshiba Teli BU030MG USB Device
```

---

### Problem: "DLL load failed: The specified module could not be found"

**Causes:**
- Missing GenICam DLLs
- Wrong DLL architecture (32-bit vs 64-bit)

**Solutions:**
```powershell
# Verify Python architecture
python -c "import sys; print(f'{sys.maxsize > 2**32 and \"64-bit\" or \"32-bit\"}')"

# Should output: 64-bit

# Check all DLLs present
Get-ChildItem "sdk\teli\*.dll" | Select Name
```

---

### Problem: "Failed to open camera with serial 'XXXXX' (error: -1)"

**Causes:**
- Camera already open in another application
- Wrong serial number
- Camera not connected

**Solutions:**
```powershell
# List all detected cameras first
python device/teli_camera.py

# Close any camera applications
taskkill /IM "TeliCamSDK.exe" /F
taskkill /IM "opencv_viewer.exe" /F

# Verify serial number in registry
reg query "HKLM\SOFTWARE\iTrue\hardware"
```

---

### Problem: Camera detected but can't open

**Try opening by index instead:**
```python
from device.teli_camera import TeliCamera

teli = TeliCamera()
cameras = teli.list_cameras()
print(f"Found {len(cameras)} cameras")

# Open first camera by index
teli.open(0)
print("Opened camera 0")
teli.close()
```

---

### Problem: GRAB shows OpenCV fallback message

**Symptoms:**
```
[CAMERA] GRAB: Using OpenCV fallback
```

**Causes:**
- Teli SDK failed to initialize
- Camera serial not in registry
- Camera not connected

**Solutions:**
```powershell
# 1. Verify SDK loaded
python -c "from device.teli_camera import TeliCamera; t = TeliCamera()"

# 2. Check registry has serials
reg query "HKLM\SOFTWARE\iTrue\hardware"

# 3. Verify cameras connected
python device/teli_camera.py
```

---

### Problem: Black image displayed

**Causes:**
- Exposure time too short
- Lens cap on
- No lighting
- Wrong AOI (outside sensor bounds)

**Solutions:**
1. Open Camera Configuration
2. Increase Shutter (Exposure) to 100+ microseconds
3. Check physical camera - remove lens cap
4. Verify AOI settings are valid (X+Width ≤ sensor width)

---

### Problem: LIVE video stutters or freezes

**Causes:**
- USB bandwidth insufficient
- Exposure time too long
- Packet size too large

**Solutions:**
1. Reduce image size (set AOI smaller)
2. Lower exposure time
3. Reduce Bytes Per Packet in Camera Configuration
4. Check USB3 connection (should be blue port, not USB2)

---

## Success Criteria

### Basic SDK Tests:
✓ **Step 4**: Cameras detected (count > 0)
✓ **Step 5**: Serial numbers match registry
✓ **Step 6**: Both cameras open successfully by serial
✓ **Step 7**: Acquisition starts/stops without errors
✓ **Step 8**: Registry integration works

### Application Integration Tests:
✓ **Step 9**: Camera Configuration saves .cam files
✓ **Step 10**: GRAB captures single frame using Teli SDK
✓ **Step 11**: LIVE shows continuous video using Teli SDK
✓ **Step 12**: Settings changes affect image brightness
✓ **Step 13**: Both Track1 and Track2 cameras work

**If all steps pass, camera system is fully operational!**

---

## What You Should See

### Successful GRAB:
```
[CoPerformance Tips

### Optimize Frame Rate:
- **Reduce AOI size** - Smaller images transfer faster
- **Lower exposure** - Faster capture cycles
- **Adjust packet size** - Match network/USB bandwidth
- **Use USB3 ports** - Blue ports, not USB2 black ports

### Memory Management:
- **Stop LIVE before GRAB** - Application does this automatically
- **Close camera between captures** - Prevents resource locks
- **One camera at a time** - Track switching works seamlessly

### Debug Mode:
- Watch console output for detailed camera operations
- Look for `✓` markers indicating success
- Error messages show exact failure points
- Serial numbers logged for verification

---

## Comparison: Old C++ vs New Python

| Operation | Old C++ Behavior | New Python Behavior | Status |
|-----------|------------------|---------------------|---------|
| GRAB Click | Opens by serial → Grab frame | Opens by serial → Grab frame | ✓ Identical |
| LIVE Click | Opens by serial → Stream | Opens by serial → Stream | ✓ Identical |
| Settings Apply | Writes to hardware | Writes to hardware | ✓ Identical |
| Track Switch | Changes camera | Changes camera | ✓ Identical |
| .cam Files | Saves settings | Saves settings | ✓ Compatible |
| Serial Lookup | Registry | Registry | ✓ Same |
| Error Handling | Shows dialog | Shows console + dialog | Enhanced |

**Result: Python system operates identically to C++ system!**

---

## Notes

- **Don't modify code on camera system** - Make changes on dev machine, then copy
- **Always close cameras properly** - Application handles this automatically
- **Test one camera at a time first** - Easier to isolate issues
- **Check Windows Event Log** - May show USB/driver errors
- **Reboot if drivers updated** - USB drivers may need restart
- **Monitor console output** - Shows all camera operations in real-time

**Questions? Issues? Check error messages carefully - they indicate the exact problem (error codes documented in TeliCamApi.h)**

---

## Final Checklist

Before deploying to production:

- [ ] Both cameras detected in Step 4
- [ ] Serial numbers match registry (Step 5)
- [ ] GRAB captures images (Step 10)
- [ ] LIVE shows video feed (Step 11)
- [ ] Settings affect image brightness (Step 12)
- [ ] Track switching works (Step 13)
- [ ] No OpenCV fallback messages
- [ ] Camera closes cleanly after operations
- [ ] .cam files save/load correctly
- [ ] Both Track1 and Track2 functional

**When all items checked, camera system is production-ready!** ✅
- No OpenCV fallback messages
```

### Successful LIVE:
```
[Console Output]
[CAMERA] Opening camera for LIVE: 17E11506
✓ Camera opened by serial: 17E11506
✓ Camera settings applied
[CAMERA] Teli LIVE started

[Main Window]
- Continuous video feed (~30 FPS)
- Smooth playback
- Stop LIVE closes camera cleanly
```

### Settings Applied:
```
[After changing Shutter to 50]
- Image brighter than before

[After changing Shutter to 1]
- Image darker than before

This proves settings written to hardware!
```

---

## Quick Reference Commands

```powershell
# Test camera detection
python device/teli_camera.py

# Check registry
reg query "HKLM\SOFTWARE\iTrue\hardware"

# List USB devices
Get-PnpDevice | Where-Object {$_.FriendlyName -like "*Teli*"}

# Kill camera applications
tasklist | findstr /i "camera teli"
```

---

## Notes

- **Don't modify code on camera system** - Make changes on dev machine, then copy
- **Always close cameras** - Use context managers or explicit `close()`
- **Test one camera at a time first** - Easier to isolate issues
- **Check Windows Event Log** - May show USB/driver errors
- **Reboot if drivers updated** - USB drivers may need restart

**Questions? Issues? Check error messages carefully - they indicate the exact problem (error codes documented in TeliCamApi.h)**
