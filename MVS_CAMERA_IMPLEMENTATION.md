# HIKVision MVS Camera Implementation

## Overview
Replaced Toshiba Teli SDK with **HIKVision MVS (Machine Vision SDK)** for industrial camera control across **7 inspection stations** with **Doc-index-based routing** (Doc1-Doc7).

## Station Mapping
```
Doc1 → TOP (Top inspectection)
Doc2 → BOTTOM (Bottom inspection)
Doc3 → FEED (Feed station)
Doc4 → PICKUP1 (Pick-up 1)
Doc5 → PICKUP2 (Pick-up 2)
Doc6 → BOTTOM_SEAL (Bottom sealing station)
Doc7 → TOP_SEAL (Top sealing station)
```

## Installation Location
```
C:\Program Files (x86)\Common Files\MVS\
├── Drivers/          # Camera drivers
├── Licenses/         # License files
├── Runtime/          # SDK DLL files
│   ├── Win32_i86/    # 32-bit DLLs
│   └── Win64_x64/    # 64-bit DLLs (we use this)
└── Service/          # Background services
```

## Key DLL
- **MvCameraControl.dll** (Win64_x64 version)
- Path: `C:\Program Files (x86)\Common Files\MVS\Runtime\Win64_x64\MvCameraControl.dll`

## Implementation Files

### 1. device/camera_registry.py (Updated)
Windows Registry handler for camera configuration with full metadata support:
- **Registry path**: `HKEY_CURRENT_USER\Software\iTrue\hardware`
- **Registry entries per camera**:
  - `Doc[1-7]CamSN` - Camera serial number
  - `Doc[1-7]Color` - Camera type (0=mono, 1=color)
  - `Doc[1-7]Model` - Camera model (USB3CT, USB4CT, etc.)
  - `Doc[1-7]CamFile` - Optional camera profile/calibration file path
- **Key methods**:
  - `read_registry()` - Read all Doc1-Doc7 camera configurations
  - `write_registry(doc_index, serial, model, is_color, cam_file)` - Write full config
  - `get_station_name(doc_index)` - Get station name for Doc index
  - `get_doc_index(station_name)` - Get Doc index for station name
  - `print_registry()` - Display all configured cameras with details

### 2. setup_cameras.py (New)
Interactive script for camera enumeration and registry configuration:
- **Step 1**: Enumerate all connected MVS cameras
- **Step 2**: Show current registry configuration
- **Step 3**: Configure cameras (auto or manual):
  - **Auto-configure**: Assigns cameras to Doc1, Doc2, etc. in order
  - **Manual configure**: Choose Doc index for each camera
  - Automatically detects camera type (mono vs color) from model name
- **Step 4**: Verify final configuration in registry
- **Usage**: `python setup_cameras.py`

### 3. device/mvs_camera.py (Updated)
Complete HIKVision MVS SDK wrapper with:
- **MVSCamera class**: Main camera interface
- **Device enumeration**: `enumerate_cameras()` - Find all connected cameras
- **Camera operations**:
  - `open_camera(serial_number)` - Open camera by serial number
  - `close_camera()` - Close camera and release resources
  - `start_grabbing()` - Start image acquisition
  - `stop_grabbing()` - Stop image acquisition
  - `grab_frame(timeout_ms)` - Capture single frame
- **Parameter control**:
  - `set_exposure(exposure_us)` / `get_exposure()` - Exposure time in microseconds
  - `set_gain(gain_db)` / `get_gain()` - Gain in dB
  - `set_trigger_mode(enabled)` - Enable/disable trigger mode
  - `software_trigger()` - Execute software trigger

### 4. imaging/grab_service.py (Updated)
Doc-index-based camera routing with MVS SDK integration:
- **Routing logic**: Each station's camera feed routes to its Doc panel via doc_index
- **GRAB operations**: Returns (frame, doc_index) tuple for per-panel display routing
- **LIVE operations**: Stores doc_index and passes through frame display pipeline
- **Source resolution**: 
  - `_resolve_camera_source()` returns (source, backend, doc_index) tuple
  - Maps station → Doc index → camera config (registry or camera_settings.json)
  - MVS SDK preferred, OpenCV fallback for Doc1 only if unconfigured
- **Display routing**:
  - `_display_frame(frame, doc_index)` routes pixmap to correct Doc panel
  - `_display_pixmap_to_doc(doc_index, pixmap)` displays in specific station panel
- **Fallback logic**:
  - Doc1 (TOP): Laptop camera fallback if no registry serial
  - Doc2-7: MVS serial required, no fallback

### 5. app/main_window.py (Updated)
Multi-station camera display with Doc-indexed panels:
- **Camera panels**: Dict[int, {image: QLabel, header, panel, label}] keyed by Doc1-7
- **Layout**: 
  - Top row: 5 stations (Doc1-5) with colored headers
  - Bottom row left: 2 stations (Doc6-7) stacked
  - Bottom row right: Data tables (Summary, Defects)
- **Display methods**:
  - `_get_active_image_label()` - Get image label for current station via registry
  - `_display_pixmap_to_doc(doc_index, pixmap)` - Route pixmap to specific Doc panel
  - `_display_pixmap(pixmap)` - Legacy fallback to active panel
- **Panel colors**: Fixed per-station to identify cameras visually

## Supported Pixel Formats
```python
MVSPixelType.PixelType_Gvsp_Mono8          # 8-bit monochrome
MVSPixelType.PixelType_Gvsp_RGB8_Packed    # RGB 8-bit
MVSPixelType.PixelType_Gvsp_BGR8_Packed    # BGR 8-bit
MVSPixelType.PixelType_Gvsp_BayerGR8       # Bayer patterns
MVSPixelType.PixelType_Gvsp_Mono10         # 10-bit mono
MVSPixelType.PixelType_Gvsp_Mono12         # 12-bit mono
```

## MVS Error Codes
```python
MV_OK.SUCCESS = 0x00000000                 # Success
MVSErrorCode.MV_E_HANDLE = 0x80000000      # Invalid handle
MVSErrorCode.MV_E_PARAMETER = 0x80000004   # Invalid parameter
MVSErrorCode.MV_E_NODATA = 0x80000006      # No data (timeout)
MVSErrorCode.MV_E_RESOURCE = 0x80000005    # Resource allocation error
```

## Camera Operations Workflow

### GRAB (Single Frame with Doc-Index Routing)
```
1. User clicks GRAB button in station panel
2. Get current station (e.g., FEED)
3. Convert station to Doc index (FEED → Doc3)
4. Get serial number from registry for Doc3 (e.g., "CAM123456")
5. Open camera by serial number (MVS SDK)
6. Load camera settings from .cam file (if exists)
7. Apply settings (exposure, gain, trigger mode)
8. Start grabbing
9. Grab single frame (1000ms timeout)
10. Return (frame, doc_index=3) tuple
11. Stop grabbing
12. Close camera
13. Route frame to Doc3 panel via _display_pixmap_to_doc(3, pixmap)
```

### LIVE (Continuous Multi-Station Display)
```
1. User enables LIVE mode
2. Get current station and convert to Doc index
3. Get serial number from registry for that Doc
4. Open camera, apply settings, start grabbing
5. Store live_doc_index for routing
6. QTimer triggers every 30ms (~30 FPS):
   - Grab frame (100ms timeout)
   - Return (frame, live_doc_index)
   - Route to correct panel via _display_pixmap_to_doc()
7. Crucially: Each station displays ITS OWN camera feed
   - Switching active station doesn't change other displays
   - Frame routing is based on doc_index, not active selection
8. On stop: Stop grabbing → Close camera
```

### Fallback Behavior
```
Doc1 (TOP):
  ├─ If registry has serial → Use MVS SDK
  └─ If registry empty → Fall back to OpenCV (laptop camera index 0)

Doc2-Doc7:
  ├─ If registry has serial → Use MVS SDK
  └─ If registry empty → Only try camera_settings.json, no laptop fallback
```

## Data Structures

### MV_CC_DEVICE_INFO
```c
struct MV_CC_DEVICE_INFO {
    unsigned int nMajorVer;
    unsigned int nMinorVer;
    unsigned int nMacAddrHigh;
    unsigned int nMacAddrLow;
    unsigned int nTLayerType;
    unsigned char chSerialNumber[16];
    unsigned char chModelName[32];
    unsigned char chDeviceVersion[32];
    unsigned char chManufacturerName[32];
    unsigned char chUserDefinedName[32];
    // ... more fields
};
```

### MV_FRAME_OUT_INFO_EX
```c
struct MV_FRAME_OUT_INFO_EX {
    unsigned int nWidth;
    unsigned int nHeight;
    unsigned int enPixelType;
    unsigned int nFrameNum;
    unsigned int nDevTimeStampHigh;
    unsigned int nDevTimeStampLow;
    unsigned int nHostTimeStamp;
    unsigned int nFrameLen;
    unsigned int nLostPacket;
};
```

## API Function Signatures
```python
# Device enumeration
MV_CC_EnumDevices(nTLayerType, pstDevList) -> int

# Device handle
MV_CC_CreateHandle(handle, pstDevInfo) -> int
MV_CC_DestroyHandle(handle) -> int

# Device operations
MV_CC_OpenDevice(handle, nAccessMode, nSwitchoverKey) -> int
MV_CC_CloseDevice(handle) -> int

# Image acquisition
MV_CC_StartGrabbing(handle) -> int
MV_CC_StopGrabbing(handle) -> int
MV_CC_GetOneFrameTimeout(handle, pData, nDataSize, pFrameInfo, nMsec) -> int

# Parameters
MV_CC_SetFloatValue(handle, strKey, fValue) -> int
MV_CC_GetFloatValue(handle, strKey, pfValue) -> int
MV_CC_SetEnumValue(handle, strKey, nValue) -> int
MV_CC_GetEnumValue(handle, strKey, pnValue) -> int
```

## Camera Settings Format
Settings loaded from `.cam` files should contain:
```json
{
  "exposure": 10000.0,     // Exposure time in microseconds
  "gain": 5.0,             // Gain in dB
  "trigger_mode": false    // true = hardware trigger, false = free run
}
```

## Testing

### 1. Camera Setup (Required Before Testing)
```bash
cd "e:\Office Work\chip-chap-python"

# Step 1: Connect all 7 MVS cameras to system
# Step 2: Run setup script
python setup_cameras.py

# Step 3: Choose auto-configure option [1]
# Output:
# [AUTO-CONFIGURE] Assigning cameras to Doc1, Doc2, etc...
#   ✅ Doc1 (TOP) → CAM001234 (USB3CT - Mono)
#   ✅ Doc2 (BOTTOM) → CAM001235 (USB4CT - Color)
#   ...etc
```

### 2. Verify Registry Configuration
```bash
python device\camera_registry.py
```

Expected output:
```
[REGISTRY] Configured cameras:
  Doc1 → TOP         | SN=CAM001234    | USB3CT     | Mono
  Doc2 → BOTTOM      | SN=CAM001235    | USB4CT     | Color
  Doc3 → FEED        | SN=CAM001236    | USB3CT     | Mono
  Doc4 → PICKUP1     | SN=CAM001237    | USB4CT     | Color
  Doc5 → PICKUP2     | SN=CAM001238    | USB3CT     | Mono
  Doc6 → BOTTOM_SEAL | SN=CAM001239    | USB4CT     | Color
  Doc7 → TOP_SEAL    | SN=CAM001240    | USB3CT     | Mono
```

### 3. Test Individual Camera (Doc Index)
```bash
python
```

```python
from device.mvs_camera import MVSCamera
from device.camera_registry import CameraRegistry

# Get Doc3 (FEED) camera serial
cameras = CameraRegistry.read_registry()
serial = cameras.get(3)  # Doc3
print(f"Doc3 serial: {serial}")

# Open and grab
mvs = MVSCamera()
if mvs.open_camera(serial):
    mvs.start_grabbing()
    frame = mvs.grab_frame(timeout_ms=1000)
    if frame is not None:
        print(f"Doc3 frame captured: {frame.shape}")
    mvs.stop_grabbing()
    mvs.close_camera()
```

### 4. Test Multi-Station Display
```bash
# Start main application
python main.py

# In GUI:
# 1. Mode: ONLINE
# 2. Click GRAB for each station (FEED, TOP, BOTTOM, PICKUP1, etc)
# 3. Verify each frame appears in correct station panel (Doc panel)
# 4. Enable LIVE and verify continuous feeds in all panels simultaneously
```

### 5. Old Enumerate Cameras Test
```bash
python device\mvs_camera.py
```

Expected output (when cameras are connected):
```
Enumerating MVS cameras...

Found 7 camera(s):
  - MV-CA016-10UC (SN: CAM001234)
  - MV-CA013-10GC (SN: CAM001235)
  - MV-CA016-10UC (SN: CAM001236)
  ...
```

## Setup Workflow (From Old System to New)

### Step 1: Connect Cameras
Connect all 7 MVS cameras to the system (USB or GigE based on camera type)

### Step 2: Run Camera Setup
```bash
python setup_cameras.py
```
- Auto-detects connected cameras by serial number
- Writes to Windows Registry: `HKEY_CURRENT_USER\Software\iTrue\hardware`
- Stores: Doc[1-7]CamSN, Doc[1-7]Color, Doc[1-7]Model, Doc[1-7]CamFile

### Step 3: Start Application
```bash
python main.py
```

### Step 4: Test in GUI
- Mode → ONLINE
- Click GRAB in different stations
- Verify feeds appear in correct Doc panels
- Enable LIVE for continuous multi-station display

### Key Differences from Old System
1. **Multi-Doc routing**: Each Doc panel displays its own camera feed independently
2. **Registry persistence**: Camera configuration survives application restart
3. **Automatic fallback**: Doc1 uses laptop camera if not in registry (for testing)
4. **Color detection**: Automatically detects mono (USB3CT) vs color (USB4CT) cameras

## Architecture Notes

### Doc-Index System
The application routes camera feeds using **Doc indices** (1-7) stored in the registry:

```
User selects FEED station
    ↓
Convert FEED → Doc3 via CameraRegistry.get_doc_index()
    ↓
Read Doc3 serial from registry: "CAM001236"
    ↓
Open MVS camera by serial "CAM001236"
    ↓
Grab frame (returns (frame, doc_index=3))
    ↓
Route to panel via _display_pixmap_to_doc(doc_index=3, pixmap)
    ↓
Frame appears in Doc3 panel (FEED station)
```

### Why Doc-Index Routing?
1. **Multi-station display**: Each station shows its own camera independently
2. **Persistent mapping**: Registry stores station-to-camera mapping permanently
3. **Fallback handling**: Can gracefully handle missing cameras without UI crashes
4. **Future expansion**: Easy to add more Doc indices if needed

## Compatibility Notes

1. **Serial Number Format**: MVS cameras use HIK serial numbers
   - Example: "CAM001234" or "FA0987654321"
   - Set via setup_cameras.py, stored in registry
   - Not hardcoded in code (more flexible)

2. **Camera Settings**: 
   - MVS uses different parameter names than Teli
   - Exposure: microseconds (same as Teli)
   - Gain: dB (same as Teli)
   - Trigger: `TriggerMode` enum (0=Off, 1=On)
   - `.cam` files should match MVS GenICam parameter names

3. **Frame Format**:
   - Returns numpy arrays like Teli
   - Mono8 → (height, width)
   - RGB8/BGR8 → (height, width, 3)
   - Bayer → (height, width) - raw Bayer pattern

4. **Error Handling**:
   - MVS returns error codes (0x80000000 range for errors)
   - Doc1 gracefully falls back to OpenCV if serial not in registry
   - Doc2-7 require valid registry entry or DVR fails

5. **Laptop Camera Fallback** (Doc1 Only):
   - If Doc1 serial not in registry, uses OpenCV index 0
   - Allows testing without real cameras
   - Doc2-7: No fallback, requires MVS camera

## Troubleshooting

### Setup Issues

#### No Cameras Found by setup_cameras.py
**Error**: `⚠️  WARNING: No MVS cameras detected!`
**Solution**:
1. Check cameras are connected (USB/GigE cable)
2. Power on cameras
3. Verify in Device Manager: Right-click → Imaging devices
4. Reinstall MVS driver from `C:\Program Files (x86)\Common Files\MVS\Drivers`

#### setup_cameras.py Crashes
**Error**: `AttributeError: 'NoneType' object has no attribute 'xxx'`
**Solution**: Update setup_cameras.py error handling. Ensure MVSCamera.enumerate_cameras() succeeds.

### Runtime Issues

#### Camera Feed Not Appearing in Panel
**Symptoms**: GRAB/LIVE works but frame doesn't show in expected station panel
**Possible causes**:
1. Doc index mapping incorrect
2. camera_panels dictionary not initialized
3. QLabel not properly sized
**Debug**: Check console logs for `[CAMERA] Doc[X]:` messages

#### Wrong Camera Showing in Wrong Panel
**Symptoms**: Doc3 feeds shows Doc1 panel
**Possible causes**:
1. Registry serials mixed up (Doc index points to wrong serial)
2. setup_cameras.py assigned wrong Doc index
**Solution**: Re-run setup_cameras.py with manual configuration option [2]

#### All Panels Show Same Feed
**Symptoms**: All 7 stations displaying same camera
**Possible causes**:
1. All registry entries point to same serial number
2. Doc-index routing not working (check grab_service.py)
3. Main window camera_panels keyed incorrectly
**Debug**: Print camera_panels dictionary structure

### DLL and Driver Issues

#### DLL Not Found
**Error**: `OSError: [WinError 126] The specified module could not be found`
**Solution**: Check MVS installation at `C:\Program Files (x86)\Common Files\MVS\Runtime\Win64_x64\`

#### Camera Won't Open
**Error**: `Create handle failed: 0x80000004` or `Open device failed: 0x80000004`
**Possible causes**:
1. Serial number doesn't match connected camera (check setup_cameras.py)
2. Camera already in use by another process
3. Insufficient permissions
**Solution**:
- Verify registry entry: `reg query "HKEY_CURRENT_USER\Software\iTrue\hardware"`
- Close HIKVision MVS viewer if running
- Run as administrator

#### Frame Timeout
**Error**: `Get frame failed: 0x80000006` (MV_E_NODATA)
**Possible causes**:
1. Exposure time too long
2. Camera not triggered (when in trigger mode)
3. Camera stopped grabbing
4. Timeout too short for current settings
**Solution**:
- Increase timeout: `grab_frame(timeout_ms=5000)`
- Disable trigger mode for free-run: `set_trigger_mode(False)`
- Check exposure settings in camera_settings.json

### Registry Issues

#### Registry Entry Not Written
**Symptoms**: setup_cameras.py says OK, but registry has no entries
**Debug**:
```powershell
reg query "HKEY_CURRENT_USER\Software\iTrue\hardware"
# Should show Doc1CamSN, Doc1Color, Doc1Model, etc.
```
**Solution**: Run as administrator

#### Can't Find Camera in Registry but It's Connected
**Solution**: Run setup_cameras.py again with the connected camera

#### Doc1 Using Laptop Camera Instead of MVS
**This is intentional**: Doc1 falls back to OpenCV if registry empty (for testing)
**To force MVS for Doc1**: Manually set Doc1CamSN in registry

## Key Files Reference

**Main Implementation**:
- `device/mvs_camera.py` - MVS SDK wrapper
- `device/camera_registry.py` - Windows registry handler for Doc1-Doc7 mapping
- `imaging/grab_service.py` - Doc-index routing for GRAB/LIVE operations
- `app/main_window.py` - Multi-station UI with Doc-indexed camera panels
- `setup_cameras.py` - Automated camera configuration tool

**Configuration Files**:
- `camera_settings.json` - Optional CV indices/DirectShow names (fallback only)
- Windows Registry: `HKEY_CURRENT_USER\Software\iTrue\hardware` - Primary configuration

**Testing**:
- `device/camera_registry.py` - Test registry reading
- `device/mvs_camera.py` - Test camera enumeration
- `setup_cameras.py` - Interactive camera setup

## Summary

✅ **Replaced**: Teli SDK → HIKVision MVS SDK  
✅ **Multi-station**: 7 independent Doc panels with routing (Doc1-Doc7)  
✅ **Registry**: Windows Registry stores camera serials + model + color type  
✅ **Setup**: Automated setup_cameras.py for camera discovery and configuration  
✅ **Routing**: Doc-index system ensures each station displays own camera feed  
✅ **Fallback**: Doc1 gracefully uses laptop camera if MVS not configured  
✅ **Display**: Main window shows all 7 stations simultaneously (when cameras configured)  
✅ **Production-ready**: Full error handling and logging throughout pipeline
