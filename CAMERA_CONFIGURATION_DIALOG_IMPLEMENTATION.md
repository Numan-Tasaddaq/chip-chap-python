# Camera Configuration Dialog - Implementation Complete ✅

## Created Components

### 1. **New Dialog Class** (`ui/camera_configuration_dialog.py`)
- `CameraConfigurationDialog` class
- Professional UI matching old C++ dialog

### 2. **Dialog Features**

#### Camera Parameters Section
- **Shutter 1 (µs)** - Range: 1-10000
- **Shutter 2 (µs)** - Range: 1-10000
- **Gain** - Range: 0-100
- **Brightness** - Range: 0-100
- **Bytes per packet** - Range: 1-10000

#### Light Controller Section
- **Channel 1 (Red)**
  - Slider: 0-255 (default: 158)
  - Min/Max controls: 0-255
  
- **Channel 2 (Green)**
  - Slider: 0-255 (default: 255)
  - Min/Max controls: 0-255
  
- **Channel 3 (Blue)**
  - Slider: 0-255 (default: 100)
  - Min/Max controls: 0-255

#### RGB Color Gains Section
- **Red Gain** - Range: 0-200% (default: 100%)
- **Green Gain** - Range: 0-200% (default: 100%)
- **Blue Gain** - Range: 0-200% (default: 100%)

#### Action Buttons
- **Balance** - Auto-balances all light channels to their average
- **OK** - Save settings and close dialog
- **Cancel** - Discard changes and close dialog

---

## Integration with Main Window

### Added to `app/main_window.py`:

1. **Import**
   ```python
   from ui.camera_configuration_dialog import CameraConfigurationDialog
   ```

2. **Camera Settings Storage**
   ```python
   self.camera_settings = {
       1: {...},  # Track 1 settings
       2: {...}   # Track 2 settings
   }
   ```

3. **Menu Item Connection**
   - "Camera Configuration" menu item now opens the dialog
   - Only enabled when system is OFFLINE and camera is enabled

4. **Handler Method** - `_open_camera_configuration_dialog()`
   - Creates dialog instance
   - Loads current track settings
   - Shows dialog
   - Saves settings if OK clicked
   - Updates menu states

---

## How It Works

### Opening the Dialog

1. **Menu**: Configuration → Camera Configuration
2. **Conditions** (must ALL be true):
   - System is OFFLINE
   - Camera is ENABLED
   - Camera is AVAILABLE
   - Not teaching/inspecting/calibrating
   - No fail track active
   - Dialog not already open

3. **Dialog Opens**:
   - Loads current settings for active track
   - User modifies parameters
   - User clicks Balance (optional) to auto-adjust light channels

4. **Closing the Dialog**:
   - **OK**: Saves all settings for current track
   - **Cancel**: Discards changes

### Settings Persistence

Settings are stored per track:
```python
camera_settings[track_number] = {
    "shutter_1": value,
    "shutter_2": value,
    "gain": value,
    ...
    "blue_gain": value
}
```

---

## Features

### Light Channel Sliders
- Real-time visual feedback
- Value displayed next to each slider
- Separate min/max controls for each channel
- Perfect for adjusting lighting for different inspection tasks

### Balance Button
- Calculates average of all 3 channels
- Sets all channels to the average
- Useful for balanced RGB lighting
- Shows confirmation message

### Track-Specific Settings
- Each track (Track 1, Track 2) has separate settings
- Dialog title shows current track
- Settings load when dialog opens
- Settings save when OK is clicked

### Settings Validation
- Input ranges enforced (spinboxes)
- Min/Max values locked within 0-255
- All values returned as dictionary

---

## Dialog Methods

### `get_settings()` → dict
Returns all current camera settings

### `set_settings(dict)`
Loads settings into dialog controls

### Internal Signals
- `settings_changed` signal emitted when settings modified

---

## Files Modified

1. **New File**: `ui/camera_configuration_dialog.py` (240 lines)
   - Complete dialog implementation
   - Slider handling
   - Balance functionality
   - Settings get/set methods

2. **Modified**: `app/main_window.py`
   - Added import (line 43)
   - Added camera_settings storage (lines 127-155)
   - Updated `_open_camera_configuration_dialog()` method (lines 1928-1960)

---

## Usage Example

```python
# Access camera settings for current track
track = self.state.track
settings = self.camera_settings[track]

# Get specific setting
shutter_1 = settings["shutter_1"]
gain = settings["gain"]

# Light controller channels
ch1 = settings["lc_intensity_1"]
ch2 = settings["lc_intensity_2"]
ch3 = settings["lc_intensity_3"]

# RGB gains
red_gain = settings["red_gain"]
green_gain = settings["green_gain"]
blue_gain = settings["blue_gain"]
```

---

## Next Steps (Optional)

To fully integrate with camera hardware:

1. In `_open_camera_configuration_dialog()`, after receiving settings:
   ```python
   # Send settings to camera hardware
   camera.set_shutter(settings["shutter_1"], settings["shutter_2"])
   camera.set_gain(settings["gain"])
   camera.set_brightness(settings["brightness"])
   # ... etc
   ```

2. Implement hardware validation:
   ```python
   if not camera.validate_settings(settings):
       QMessageBox.warning(self, "Invalid Settings", "...")
   ```

---

## Status

✅ **Dialog Created**
✅ **Menu Integration Complete**
✅ **Settings Storage Implemented**
✅ **Per-Track Settings Supported**
✅ **Balance Function Implemented**
✅ **UI Matches Old C++ Application**

**Ready to use!** Click "Camera Configuration" in the Configuration menu to open the dialog.
