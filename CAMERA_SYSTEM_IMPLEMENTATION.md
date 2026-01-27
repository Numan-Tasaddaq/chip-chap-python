## Camera System Implementation - 7 Stations (Doc1-Doc7)

### Overview
Implemented multi-station camera management following the old application pattern with 7 USB3 cameras mapped to fixed Doc indices (1-7), each representing a specific inspection station.

### Architecture

#### 1. **Windows Registry Integration** (`device/camera_registry.py`)
Maps camera serial numbers to Doc indices via Windows Registry:

```
HKEY_CURRENT_USER\Software\iTrue\hardware
├── Doc1CamSN → "CAM123456"
├── Doc2CamSN → "CAM789012"
├── ...
└── Doc7CamSN → "CAM567890"
```

**Station Mapping (Doc1-Doc7):**
- Doc1 → TOP (Top inspection) - Mono (USB3CT)
- Doc2 → BOTTOM (Bottom inspection) - Mono (USB3CT)
- Doc3 → FEED (Feed) - Color (USB4CT)
- Doc4 → PICKUP1 (Pick-up 1) - Mono (USB3CT)
- Doc5 → PICKUP2 (Pick-up 2) - Mono (USB3CT)
- Doc6 → BOTTOM_SEAL (Bottom sealing) - Color (USB4CT)
- Doc7 → TOP_SEAL (Top sealing) - Mono (USB3CT)

#### 2. **Grab Service** (`imaging/grab_service.py`)
Enhanced camera source resolution with priority order:

1. **Windows Registry** - Doc index to serial number mapping
2. **camera_settings.json** - DirectShow device names or CV indices
3. **camera_map** - (track, station) lookup table
4. **Preferred settings** - Global fallback index
5. **Laptop camera** - Final fallback (index 0)

**Key Methods:**
- `grab()` - Single frame capture (stops LIVE first)
- `toggle_live()` - Start/stop continuous capture (~30 FPS)
- `_resolve_camera_source()` - Multi-priority camera resolution
- `_build_camera_map()` - Populate camera lookup table

#### 3. **Camera Device** (`device/camera_device.py`)
Hardware abstraction layer:

```python
device = CameraDevice(
    doc_index=1,
    station="TOP",
    camera_type=CameraDevice.TYPE_MONO,  # 0=Mono, 1=Color
    model="USB3CT",                       # USB3CT or USB4CT
    cv_index=1,                           # OpenCV fallback
    dshow_name="USB3.0 Camera SN123"      # DirectShow name
)
frame = device.grab_once()
```

#### 4. **Main Window** (`app/main_window.py`)
Updated to support all 7 stations:

**Station Enum:**
```python
class Station(str, Enum):
    FEED = "Feed"
    TOP = "Top"
    BOTTOM = "Bottom"
    PICKUP1 = "Pick-up 1"
    PICKUP2 = "Pick-up 2"
    BOTTOM_SEAL = "Bottom Sealing"
    TOP_SEAL = "Top Sealing"
```

**Station Menu Actions:**
```
🎯 SELECT STATION
  └─ Feed
  └─ Top
  └─ Bottom
  └─ Pick-up 1
  └─ Pick-up 2
  └─ Bottom Sealing
  └─ Top Sealing
```

**Inspection Parameters:**
Each station has its own InspectionParameters instance for teaching and defect detection.

#### 5. **Configuration File** (`camera_settings.json`)
JSON configuration with all 7 cameras:

```json
{
  "cameras": [
    {
      "doc_index": 1,
      "station": "TOP",
      "description": "Top inspection",
      "model": "USB3CT",
      "type": 0,
      "dshow_name": "",
      "index": 1
    },
    ...
  ],
  "preferred": {
    "index": 0
  }
}
```

### Camera Resolution Priority

When GRAB or LIVE is triggered:

1. **Station lookup** - Get Doc index from current station (TOP, BOTTOM, FEED, etc.)
2. **Registry check** - Look for DocXCamSN in Windows Registry
3. **Settings lookup** - Check camera_settings.json for DirectShow name or CV index
4. **camera_map lookup** - Check (track, station) tuple in memory
5. **Preferred settings** - Use global preferred index
6. **Fallback** - Use laptop camera (index 0)

Each level provides logging for debugging.

### Camera Types

**Type 0 - Mono (USB3CT)**
- BU030 model
- Stations: TOP, BOTTOM, PICKUP1, PICKUP2, TOP_SEAL
- Typical use: Electrical defect inspection

**Type 1 - Color (USB4CT)**
- BU040 model
- Stations: FEED, BOTTOM_SEAL
- Typical use: Color/cosmetic defect inspection

### Logging Output

The system logs camera resolution steps:

```
[CAMERA] Station 'TOP' mapped to Doc1
[CAMERA] Doc1: Using registry SN 'CAM123456' as CV index 1
[CAMERA] Opened source=1 backend=None size=1920x1080 fps=30.0
```

### Configuration Steps

#### Step 1: Set Windows Registry (Windows only)

```python
from device.camera_registry import CameraRegistry

# Set camera serial numbers in registry
CameraRegistry.write_registry(1, "CAM123456")  # Doc1 (TOP)
CameraRegistry.write_registry(2, "CAM789012")  # Doc2 (BOTTOM)
CameraRegistry.write_registry(3, "CAM567890")  # Doc3 (FEED)
...

# View current registry
CameraRegistry.print_registry()
```

Or via Windows Registry Editor:
```
HKEY_CURRENT_USER\Software\iTrue\hardware
  Doc1CamSN = "CAM123456"
  Doc2CamSN = "CAM789012"
  Doc3CamSN = "CAM567890"
  ...
```

#### Step 2: Configure camera_settings.json

Update `dshow_name` fields for each camera if known:

```json
{
  "cameras": [
    {
      "doc_index": 1,
      "station": "TOP",
      "dshow_name": "USB3.0 Camera BU030 SN123456",
      "index": 1
    },
    ...
  ]
}
```

To find DirectShow names on Windows:
```powershell
$ffmpeg = "ffmpeg -list_devices true -f dshow -i dummy"
Invoke-Expression $ffmpeg 2>&1 | Select-String "dshow"
```

#### Step 3: Test Camera Resolution

```python
from imaging.grab_service import GrabService

# Initialize in MainWindow context
service = GrabService(main_window)

# Manually test camera resolution
source, backend = service._resolve_camera_source()
print(f"Source: {source}, Backend: {backend}")

# Test GRAB
service.grab()

# Test LIVE
service.start_live()
# ... (observe frames in UI)
service.stop_live()
```

### Testing Checklist

- [ ] Registry values set for Doc1-Doc7 with serial numbers
- [ ] camera_settings.json contains all 7 cameras with correct doc_index/station mapping
- [ ] Station menu shows all 7 stations
- [ ] GRAB works for each station (logs show correct Doc index)
- [ ] LIVE works for each station
- [ ] Fallback to laptop camera if registry/settings are incomplete
- [ ] Switching stations updates camera source correctly
- [ ] Frame resolution and FPS logged correctly
- [ ] No camera conflicts when switching between stations

### Backwards Compatibility

The system maintains backwards compatibility:
- Existing 3-station systems (FEED, TOP, BOTTOM) continue to work
- New stations (PICKUP, SEALING) are available when configured
- Fallback to laptop camera (index 0) if cameras are not configured
- Simulator mode disables camera access entirely

### Implementation Summary

| File | Changes |
|------|---------|
| `device/camera_registry.py` | NEW - Windows Registry handler for Doc1-Doc7 mapping |
| `device/camera_device.py` | Updated - Support for camera types and DirectShow names |
| `imaging/grab_service.py` | Updated - Registry-based camera resolution with 5-level priority |
| `app/main_window.py` | Updated - 7-station enum and menu items |
| `camera_settings.json` | Updated - All 7 cameras with type/model configuration |

### Future Enhancements

1. **Track-specific camera mapping** - Different cameras for Track1-F vs Track1-P
2. **Camera auto-discovery** - Enumerate USB devices and match to registry SNs
3. **Live preview panel** - Show all 7 camera feeds simultaneously
4. **Health monitoring** - Check camera connectivity and frame rate
5. **Recording capability** - Log camera frames to disk for debugging
