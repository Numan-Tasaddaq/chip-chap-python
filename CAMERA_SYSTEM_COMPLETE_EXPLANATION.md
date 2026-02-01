# Camera System Complete Explanation - Simple Terms

## Overview
The old C++ application uses **industrial USB3 Vision cameras** (like Teli cameras) to capture images of chip components for quality inspection. Think of it like this: cameras take pictures → software processes pictures → pass/fail decision.

---

## 🎥 PART 1: HOW CAMERAS ARE CONNECTED (Hardware)

### Physical Connection
```
Camera (USB3 Vision) 
    ↓ (USB 3.0 cable)
Computer USB Port
    ↓
Windows recognizes camera device
```

### What Happens at Startup:

1. **Windows detects USB cameras** automatically (like detecting a USB drive)
2. **Each camera has a unique Serial Number** (like "12345678" burned into camera hardware)
3. **Cameras appear as USB devices** that can be enumerated (listed)

### Multiple Camera Support
- The application supports **up to 8 cameras** (Track 1 through Track 8)
- Each camera is called a "Track" or "Station"
- Each Track inspects components independently

---

## 🔧 PART 2: HOW CAMERA SYSTEM WORKS IN C++ CODE

### Step-by-Step Camera Initialization:

#### **STEP 1: Application Starts (InitInstance)**
**File**: `ChipCapacitor.cpp` → `InitInstance()` function

```
Application starts
    ↓
Read registry: How many tracks/stations? (1-8)
    ↓
For each track:
    - Create TrackManager object
    - Load camera settings from registry
```

**What's loaded from registry**:
- `Doc1 CamFile`: Camera serial number (e.g., "12345678")
- `Doc1 FB`: Frame grabber DLL name (e.g., "iTrue_USB3CT.dll")
- `Doc1 Lens`: Lens magnification (e.g., "1.0")

**Registry Path**: `HKEY_CURRENT_USER\Software\iTrue\hardware`

---

#### **STEP 2: Initialize Each Camera (InitFrameGrabber)**
**File**: `TrackManager.cpp` → `InitFrameGrabber()` function

```cpp
// Simplified version of what happens:

1. Load Camera DLL
   - Load "iTrue_USB3CT.dll" (or USB4CT for 4K cameras)
   - This DLL talks to the camera hardware
   
2. Get Function Pointers
   - AllocAppModule: Initialize application module
   - AllocSysModule: Initialize system module
   - AllocCamModule: Open camera by serial number
   - ImageGrab: Function to capture image
   - SetAperture, SetGain, SetBrightness: Camera settings
   
3. Match Camera by Serial Number
   - DLL enumerates ALL connected cameras
   - Finds camera matching serial number from registry
   - Opens that specific camera
   
4. Apply Default Settings
   - Set trigger mode (software trigger = manual grab)
   - Set grab timeout (how long to wait for image)
```

**Key Structure**: `FG_MODULE`
This structure holds:
- DLL handle (loaded DLL)
- Function pointers (like ImageGrab, SetAperture)
- Camera module pointer (connected camera)
- System module pointer

Think of it like a **remote control** - it has buttons (function pointers) to control the camera.

---

#### **STEP 3: Load Camera Parameters (LoadCameraParm)**
**File**: `TrackManager.cpp` → `LoadCameraParm()` function

**From `.cam` configuration file** (NOT registry!):
```
Configuration.cam file contains:
- rectAoi: Area of Interest (which part of sensor to use)
- Aperture: Camera aperture setting
- Gain: Camera gain/sensitivity
- Brightness: Brightness adjustment
- BytesPerPkt: USB packet size (for speed)
- WhiteBalance: Color balance values
- RedGain, GreenGain, BlueGain: Individual color gains
- LCIntensity1, 2, 3: Light controller intensities
```

**Where stored**: `D:\iTrueVision\Configuration\{ProductName}.cam`

**Important**: Parameters are stored in `.cam` files, NOT in registry! Registry only stores serial number and DLL name.

---

#### **STEP 4: Apply Settings to Camera**
**When**: When Camera Setup dialog closes

```cpp
1. User changes settings in Camera Setup dialog
2. On dialog close:
   - Call SetAperture() → writes to camera
   - Call SetGain() → writes to camera
   - Call SetBrightness() → writes to camera
   - Call SetCameraAoi() → sets capture area
3. Save settings to .cam file for next time
```

**Camera DLL Functions Used**:
- `lpSetAperture(pCamModule, nAperture)` - Set aperture
- `lpSetCameraGain(pCamModule, nGain)` - Set gain
- `lpSetBrightness(pCamModule, nBrightness)` - Set brightness
- `lpSetCameraAoi(pCamModule, rectAoi)` - Set capture region
- `lpSetBytesPerPkt(pCamModule, nBytesPerPkt)` - Set USB speed

---

## 📸 PART 3: HOW IMAGE CAPTURE WORKS

### Simple Image Grab Flow:

```
User clicks "Live Image" or inspection starts
    ↓
Call ImageGrab function
    ↓
Camera DLL: lpImageGrab(pCamModule, pImageBuffer)
    ↓
Camera captures frame → sends via USB3
    ↓
Image data fills buffer (CImgBuf object)
    ↓
Display image on screen
```

### Actual Code Flow:
**File**: `Hardware.cpp` → `Grab()` function

```cpp
int Grab(CVisionDoc *pDoc, BOOL bDisplay) 
{
    // Get camera device
    FG_MODULE *pFG = &pInspDoc->m_pTrackManager->m_FGResource;
    
    // Call DLL to grab image
    nError = pFG->lpImageGrab(pFG->pCamModule, &pInspDoc->m_ImgBufSrc);
    
    // If image flipping needed (some cameras are upside down)
    if (bFlipX || bFlipY)
        ImgFlipXYCopy(...);
    
    // Display on screen
    if (bDisplay)
        pInspDoc->m_VisSysInfo.ScrnID->RedrawWindow();
        
    return 0;
}
```

### Trigger Modes:

1. **Software Trigger** (TRIG_SOFT):
   - Application calls `ImageGrab()` when ready
   - Camera immediately captures frame
   - Used for offline/manual inspection

2. **Hardware Trigger** (External):
   - Camera waits for electrical signal
   - PLC/machine sends trigger pulse
   - Camera captures when pulse received
   - Used for online/production mode

---

## 💡 PART 4: LIGHT CONTROLLER SYSTEM

### How Lighting Works:

```
Light Controller Hardware (Serial RS-232)
    ↓ (COM port, e.g., COM3)
Computer
    ↓
Software controls light intensity via serial commands
```

### Light Controller Setup:
**File**: `LightControlDlg.cpp`

- Uses **CSerial** class for RS-232 communication
- Sends commands to control light head
- Settings: 
  - Card Number
  - Port ID  
  - Bank Number
  - Light segments (up to 64 levels, 0-63)

### When Lights Are Used:
```
Before image capture:
    1. Set light intensity (LCIntensity1, 2, 3)
    2. Turn on specific light segments
    
During capture:
    Camera shutter opens
    Lights illuminate component
    Image captured
    
After capture:
    Can turn off lights to save bulb life
```

**Light intensities stored in `.cam` file** along with camera settings.

---

## 🔄 PART 5: COMPLETE WORKFLOW FROM STARTUP TO IMAGE CAPTURE

### Startup Sequence:

```
1. APPLICATION STARTS
   └─ ChipCapacitor.cpp → InitInstance()
      └─ Read registry: Total tracks (1-8)
      └─ For each track:
         └─ Create TrackManager

2. INITIALIZE TRACK/CAMERA
   └─ TrackManager::Initialize()
      └─ Read from registry:
         - Doc1 CamFile = "12345678" (serial number)
         - Doc1 FB = "iTrue_USB3CT.dll"
         - Doc1 Lens = "1.0"
      
      └─ InitFrameGrabber()
         └─ RegFGCard() → Load DLL "iTrue_USB3CT.dll"
         └─ RegFGAppModule() → Initialize app module
         └─ RegFGSysModule() → Initialize system
         └─ RegFGCamModule() → Open camera by serial "12345678"
            └─ DLL enumerates cameras on USB
            └─ Finds camera with matching serial
            └─ Opens camera, stores handle
         └─ SetTrigMode(TRIG_SOFT)
         └─ SetGrabTimeout(10000 ms)

3. LOAD CAMERA PARAMETERS
   └─ LoadCameraParm()
      └─ Read from ".cam" file:
         - Aperture = 20
         - Gain = 20
         - Brightness = 200
         - AOI = (168, 120, 488, 360)
         - LCIntensity1 = 100
         - etc.

4. INITIALIZE LIGHT CONTROLLER
   └─ Open COM port (RS-232)
   └─ Configure light head settings
   └─ Set initial light intensity

5. CREATE DOCUMENT/VIEW
   └─ Create inspection document
   └─ Initialize image buffers
   └─ Display main window

6. READY FOR INSPECTION!
```

### Live Image Sequence:

```
User clicks "Live Image" button
    ↓
Start thread: TrackLiveImage()
    ↓
LOOP:
    ├─ Turn on lights (if configured)
    ├─ Call lpImageGrab(pCamModule, pImageBuffer)
    │  └─ Camera DLL sends USB command to camera
    │  └─ Camera captures frame
    │  └─ Image data transferred via USB3 to buffer
    ├─ Display image on screen (RedrawWindow)
    ├─ Sleep(50 ms)
    └─ Check if stop button pressed
```

### Inspection Sequence:

```
Component arrives at inspection station
    ↓
PLC sends trigger signal (or software trigger)
    ↓
1. Set lights to inspection intensity
2. Call lpImageGrab() to capture image
3. Turn off lights
4. Process image (find defects)
5. Send result to PLC (Pass/Fail)
6. Save image if failed
7. Update statistics
```

---

## 🗄️ PART 6: DATA STORAGE SUMMARY

### Registry (HKEY_CURRENT_USER\Software\iTrue\hardware):
```
Doc1 CamFile = "12345678"           ← Camera serial number
Doc1 FB = "iTrue_USB3CT.dll"        ← Frame grabber DLL
Doc1 Lens = "1.0"                   ← Lens magnification
Color = 1                           ← Color/Mono flag
FlipX = 0                           ← Flip image horizontally
FlipY = 0                           ← Flip image vertically
AOIEnable = 1                       ← Enable area of interest
```

### .cam Configuration File (e.g., "Product123.cam"):
```
[CamSetting]
rectAoi = 168,120,488,360           ← Capture area
Aperture = 20                       ← Camera aperture
Gain = 20                           ← Camera gain
Brightness = 200                    ← Brightness
BytesPerPkt = 1072                  ← USB packet size
WhiteBalance = 2183066279           ← Color balance
LCIntensity1 = 100                  ← Light channel 1
LCIntensity2 = 100                  ← Light channel 2
LCIntensity3 = 100                  ← Light channel 3
RedGain = 1.0                       ← RGB gains
GreenGain = 1.0
BlueGain = 1.0
```

---

## 🔌 PART 7: FRAME GRABBER DLL ARCHITECTURE

### What is a Frame Grabber DLL?

Think of it as a **translator** between your application and the camera:

```
Your Application (C++)
    ↓ (calls AllocCamModule, ImageGrab)
Frame Grabber DLL (iTrue_USB3CT.dll)
    ↓ (calls Teli Camera SDK functions)
Teli Camera SDK
    ↓ (USB3 Vision protocol)
Camera Hardware
```

### USB3CT DLL Functions (IEEE1394V1.6.cpp):

**AllocCamModule** - Opens camera:
```cpp
1. Enumerate all USB3 Vision cameras
   - Call Cam_GetNumberOfCameras() → count
   - For each camera:
     - Call Cam_GetInformation() → get serial number
     - Compare serial with requested serial
     - If match → Open camera
2. Return camera handle
```

**ImageGrab** - Captures image:
```cpp
1. Allocate image buffer if needed
2. Set grab timeout
3. Send grab command to camera
4. Wait for image data
5. Copy data to application buffer
6. Return success/error
```

**SetAperture, SetGain, etc.** - Camera settings:
```cpp
1. Get camera feature handle
2. Send USB3 Vision command to camera
3. Camera updates its internal registers
4. Return success/error
```

### USB3 Vision Protocol:
- **Industry standard** for machine vision cameras
- Uses **USB 3.0** for high-speed data transfer
- Cameras are **GenICam compliant** (generic interface)
- Commands are **XML-based** feature access

---

## 🎯 PART 8: KEY DIFFERENCES vs PYTHON IMPLEMENTATION

### What OLD C++ Code Does:
1. ✅ Loads binary DLLs (iTrue_USB3CT.dll)
2. ✅ Uses Windows Registry for hardware config
3. ✅ Uses .cam INI files for parameters
4. ✅ Direct USB3 Vision camera access via Teli SDK
5. ✅ Serial port (RS-232) for light controller
6. ✅ Hardware trigger from PLC
7. ✅ Multi-threaded inspection (8 cameras)

### What PYTHON Code Should Do:
1. ✅ Use Python USB3 Vision library (e.g., Vimba, pypylon, or harvesters)
2. ✅ Use JSON/config files instead of registry
3. ✅ Use JSON for camera parameters
4. ✅ Access cameras via USB3 Vision SDK (Python wrapper)
5. ✅ Use PySerial for light controller
6. ✅ Implement trigger handling via GPIO or network
7. ✅ Use threading/multiprocessing for multiple cameras

---

## 📝 PART 9: SUMMARY IN SIMPLEST TERMS

### The Big Picture:

**Think of it like a digital camera system**:

1. **Camera Connection**: 
   - Cameras plug into USB ports (like USB drives)
   - Each camera has a unique serial number
   - Computer recognizes cameras automatically

2. **Camera Setup**:
   - Application reads "which camera to use" from registry
   - Loads a DLL that knows how to talk to that camera
   - DLL finds camera by serial number and opens it
   - Settings like brightness, zoom area stored in .cam file

3. **Taking Pictures**:
   - Application calls `ImageGrab()` function
   - DLL tells camera "take a picture now!"
   - Camera captures image → sends via USB
   - Image appears in memory buffer
   - Display on screen or process for inspection

4. **Lighting**:
   - Separate light controller connected via serial port
   - Application sends commands to turn lights on/off
   - Light intensities saved with camera settings

5. **Inspection**:
   - Capture image → Process for defects → Pass/Fail
   - If online mode: Wait for trigger from machine
   - If offline mode: User clicks button to inspect

### Key Files:
- **ChipCapacitor.cpp**: Main application startup
- **TrackManager.cpp**: Camera/track management
- **FGInterface.cpp**: Frame grabber DLL interface
- **Hardware.cpp**: Image capture functions
- **IEEE1394V1.6.cpp** (in DLL): Actual camera control

### Key Concepts:
- **Track/Station**: One camera inspection station
- **Frame Grabber**: DLL that talks to camera
- **Serial Number**: Unique ID to identify specific camera
- **AOI (Area of Interest)**: Which part of sensor to use
- **Trigger**: Signal to capture image (software or hardware)
- **.cam file**: Configuration file with all camera settings

---

## 🔍 TECHNICAL DETAILS FOR PYTHON IMPLEMENTATION

### Recommended Libraries:

1. **Camera Control**:
   - **Vimba SDK** (Allied Vision cameras) - has Python wrapper
   - **pypylon** (Basler cameras) - Python native
   - **harvesters** (GenICam/GenTL) - Universal USB3 Vision
   - **aravis** (Linux, cross-platform)

2. **Serial Communication**:
   - **pyserial** - Standard Python serial port library

3. **Image Processing**:
   - **OpenCV** (cv2) - Already using
   - **NumPy** - Array operations

### Architecture Recommendation:

```python
# Camera manager class
class CameraDevice:
    def __init__(self, serial_number):
        self.serial_number = serial_number
        self.camera = None  # Camera object from SDK
        self.settings = {}
        
    def open(self):
        # Find camera by serial number
        # Open camera
        # Apply settings
        
    def capture(self):
        # Grab image
        # Return numpy array
        
    def set_aperture(self, value):
        # Set camera feature
        
    def close(self):
        # Close camera

# Usage
camera = CameraDevice("12345678")
camera.open()
camera.set_aperture(20)
image = camera.capture()  # Returns numpy array
```

### Config File Structure (JSON):

```json
{
  "cameras": [
    {
      "track_id": 1,
      "serial_number": "12345678",
      "lens": "1.0",
      "settings": {
        "aperture": 20,
        "gain": 20,
        "brightness": 200,
        "aoi": {"x": 168, "y": 120, "width": 320, "height": 240},
        "flip_x": false,
        "flip_y": false
      },
      "lights": {
        "com_port": "COM3",
        "intensity1": 100,
        "intensity2": 100,
        "intensity3": 100
      }
    }
  ]
}
```

---

## ✅ CONCLUSION

The camera system in the old C++ code is a **well-designed industrial vision system**:

- Uses **industry-standard USB3 Vision cameras**
- **Modular DLL architecture** for different camera types
- **Persistent storage** (registry + .cam files)
- **Multi-camera support** (up to 8 stations)
- **Hardware and software triggers**
- **Integrated lighting control**

For Python implementation, you'll need to:
1. Choose a USB3 Vision SDK with Python bindings
2. Replace registry with JSON config files
3. Implement camera discovery by serial number
4. Create camera wrapper classes
5. Add light controller (PySerial)
6. Maintain multi-threading for multiple cameras

The core concepts remain the same - just different technology stack!
