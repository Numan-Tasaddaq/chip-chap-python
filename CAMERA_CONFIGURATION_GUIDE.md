# Camera Configuration Guide

## Overview

This guide explains how to properly configure your cameras for GRAB and LIVE operations.

## The Problem

When you run your application, you may see errors like:
```
[ERROR] Camera index out of range
[CAMERA] Failed to open source=3 backend=None
[CAMERA] LIVE: Failed to open preferred camera. Trying laptop camera (index 0).
```

This means the camera indices in your `camera_settings.json` don't match the actual cameras connected to your system.

## Solution: Discovery and Configuration

### Step 1: Run Camera Discovery

```bash
python camera_discovery.py
```

This script will:
1. **Scan** your system for all available cameras (indices 0-9)
2. **Test** each camera for GRAB (single frame) and LIVE (continuous) operations
3. **Report** which cameras work and which don't
4. **Generate** a proper `camera_settings.json` configuration

### Step 2: Review the Output

The script will show:

```
================================================================================
SCANNING FOR AVAILABLE CAMERAS
================================================================================

Testing camera index 0... ✓ FOUND - Resolution: 1920x1080 | FPS: 30.0 | Type: Color
Testing camera index 1... ❌ NOT AVAILABLE
Testing camera index 2... ❌ NOT AVAILABLE
Testing camera index 3... ⚠ Cannot read frames
...

✓ Found 1 camera(s)
```

**What each status means:**

- ✓ **FOUND** - Camera is available and working
- ❌ **NOT AVAILABLE** - No camera at this index
- ⚠ **Cannot read frames** - Camera exists but is not responding

### Step 3: Test Results

The script will then test GRAB and LIVE operations:

```
================================================================================
TESTING GRAB AND LIVE OPERATIONS
================================================================================

Camera Index 0 (Color):
  Testing GRAB on index 0... ✓ GRAB OK (attempt 1)
  Testing LIVE on index 0... ✓ LIVE OK (120 frames in 2.0s = 60.0 FPS)
```

**What this means:**

- ✓ **GRAB OK** - Can capture single frames (needed for snapshot capture)
- ✓ **LIVE OK** - Can capture continuous stream (needed for live preview)
- ❌ **FAILED** - Camera doesn't support this operation

### Step 4: Accept Generated Configuration

The script will prompt you to generate `camera_settings.json`:

```
Generate camera_settings.json from discovered cameras? (y/n): y
✓ Configuration saved to: C:\...\camera_settings.json
  Configured 1 cameras
```

This creates a properly configured file with the correct indices.

## Understanding camera_settings.json

Here's an example of a properly configured file:

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
      "index": 0
    },
    {
      "doc_index": 2,
      "station": "BOTTOM",
      "description": "Bottom inspection",
      "model": "USB3CT",
      "type": 0,
      "dshow_name": "",
      "index": 2
    }
  ],
  "preferred": {
    "index": 0
  }
}
```

### Key Fields Explained

| Field | Meaning | Example |
|-------|---------|---------|
| `doc_index` | Internal document ID (1-7) | `1` |
| `station` | Station name for your application | `"TOP"`, `"BOTTOM"`, `"FEED"` |
| `description` | Human-readable description | `"Top inspection"` |
| `model` | Camera model | `"USB3CT"`, `"USB4CT"` |
| `type` | Camera type: 0=Mono, 1=Color | `0` or `1` |
| `dshow_name` | (Optional) DirectShow device name | `"USB3.0 Camera SN123"` |
| **`index`** | **OpenCV camera index - THIS IS THE CRITICAL VALUE** | **`0`, `2`, `3`** |
| `preferred` | Fallback camera index | `0` (your laptop camera) |

## The Critical Value: `index`

The **`index`** field must match an available camera index on your system.

### Finding the Correct Index

Run `camera_discovery.py` to see:

```
Camera Index 0: Color camera ✓
  Resolution: 1920x1080
  FPS: 30
  GRAB: ✓  |  LIVE: ✓

Camera Index 1: ❌ NOT AVAILABLE

Camera Index 2: Mono camera ✓
  Resolution: 640x480
  FPS: 15
  GRAB: ✓  |  LIVE: ✓
```

If you have cameras at indices **0** and **2**, use those values:

```json
{
  "cameras": [
    {
      "doc_index": 1,
      "station": "TOP",
      "index": 0        ← Use this index
    },
    {
      "doc_index": 2,
      "station": "BOTTOM",
      "index": 2        ← Use this index
    }
  ]
}
```

## How GRAB and LIVE Work

### GRAB Operation (Single Frame Capture)

The application uses GRAB when:
- Taking a snapshot for inspection
- Capturing a single frame for testing
- Recording a reference image

```python
cap = cv2.VideoCapture(camera_index)
ret, frame = cap.read()  # Grab one frame
cap.release()
```

**Requirements:**
- Camera must be opened successfully
- Camera must return at least one valid frame
- Camera is closed immediately after (low resource usage)

### LIVE Operation (Continuous Stream)

The application uses LIVE when:
- Showing real-time preview in the UI
- Monitoring the feed continuously
- Recording a video stream

```python
cap = cv2.VideoCapture(camera_index)
while live_is_running:
    ret, frame = cap.read()  # Grab frame continuously
    # Process frame...
# When done:
cap.release()
```

**Requirements:**
- Camera must stay open continuously
- Camera must deliver frames reliably
- No conflicts with other applications using the camera
- Sufficient system resources

## Troubleshooting

### Issue: "Camera index out of range"

**Cause:** The index in `camera_settings.json` doesn't exist on your system.

**Solution:**
1. Run `camera_discovery.py` to find available indices
2. Update the `index` fields in `camera_settings.json` with correct values
3. Verify the indices match your hardware setup

### Issue: GRAB fails but LIVE works (or vice versa)

**Cause:** Driver issue or resource conflict.

**Solutions:**
1. Make sure no other application is using the camera
2. Try restarting your application
3. Update camera drivers
4. If the camera is shared with another program, close that program first

### Issue: Camera detected but returns "Cannot read frames"

**Cause:** Camera is recognized by the system but not responding.

**Solutions:**
1. Restart your computer
2. Reconnect the USB cable
3. Update the camera driver
4. Try the camera in another USB port
5. Check if the camera works in another application (e.g., Windows Camera app)

### Issue: No cameras found

**Cause:** USB cameras not recognized by the system.

**Solutions:**
1. Check all USB connections
2. Install camera drivers
3. Check Device Manager to see if cameras appear
4. Try different USB ports
5. For USB3 cameras, try USB 2.0 compatible ports as fallback

## Advanced: DirectShow Device Names (Windows)

For more reliable camera identification on Windows, you can use DirectShow device names:

```json
{
  "doc_index": 1,
  "station": "TOP",
  "dshow_name": "USB3.0 Camera #0",
  "index": 0
}
```

To find DirectShow names, run:
```bash
python -c "import cv2; cap = cv2.VideoCapture(0, cv2.CAP_DSHOW); print('Available')"
```

Or use the Windows Device Manager to see camera names.

## Best Practices

1. **Run Discovery First** - Always run `camera_discovery.py` after connecting new cameras
2. **Document Your Setup** - Add comments to `camera_settings.json` noting which physical camera is which
3. **Test After Configuration** - Verify GRAB and LIVE work for each station
4. **Use Fallback Index** - Keep the `preferred.index` pointing to your laptop camera as fallback
5. **Monitor Logs** - Check application logs for camera-related errors

## Quick Start Checklist

- [ ] Connect all USB cameras to your system
- [ ] Run `python camera_discovery.py`
- [ ] Review the output to identify working cameras
- [ ] Accept the generated `camera_settings.json`
- [ ] Verify the `index` values are correct for your stations
- [ ] Test your application - GRAB and LIVE should work for each station
- [ ] If issues persist, check the troubleshooting section above

## Example Complete Configuration

For a 2-camera setup (TOP and BOTTOM stations):

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
      "index": 0
    },
    {
      "doc_index": 2,
      "station": "BOTTOM",
      "description": "Bottom inspection",
      "model": "USB3CT",
      "type": 0,
      "dshow_name": "",
      "index": 2
    }
  ],
  "preferred": {
    "index": 0
  }
}
```

## Support

If you still have issues after following this guide:

1. Review the [camera_discovery.py](camera_discovery.py) output
2. Check your system's Device Manager for USB camera status
3. Verify camera drivers are installed and up-to-date
4. Test cameras with Windows Camera app or another OpenCV-based tool
5. Ensure no other application is using the cameras
