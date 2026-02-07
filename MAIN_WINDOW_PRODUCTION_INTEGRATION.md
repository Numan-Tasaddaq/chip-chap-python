# Main Window Production Controller Integration

## Overview

The main application window now supports automatic hardware-triggered production operation. When you switch to **ONLINE mode**, the system automatically starts the production controller, which monitors position sensors and triggers inspections when chips arrive at each station.

## How It Works

### Automatic Operation

1. **Start Application**: Launch the application normally
   ```bash
   python main.py
   ```

2. **Switch to ONLINE Mode**: Use the menu `Run → Online/Offline` (or press the toggle)
   - System automatically initializes production controller
   - Loads station configurations from `station_trigger_config.json`
   - Configures all 7 stations with their position sensors and trigger lines
   - Starts hardware-triggered operation

3. **Production Loop Runs Automatically**:
   - Each station monitors its position sensor
   - When a chip arrives (sensor triggers), the station:
     - Sends hardware trigger pulse to camera
     - Captures image from camera
     - Runs inspection algorithms
     - Displays result in corresponding Doc panel
     - Sends pass/fail to handler via I/O output
   - Process repeats continuously

4. **Switch to OFFLINE Mode**: Use the same toggle
   - System automatically stops production controller
   - Returns to manual mode (GRAB/LIVE buttons)

### Manual Operation (OFFLINE Mode)

When in OFFLINE mode:
- Production controller is stopped
- Manual GRAB and LIVE buttons work normally
- You can teach stations, adjust parameters, test images
- This is the mode for setup and configuration

## Integration Details

### Code Changes

#### 1. Imports Added
```python
from device.io_manager import IOManager, get_io_manager
from device.production_controller import ProductionController
from config.station_trigger_config import StationTriggerConfigManager
```

#### 2. Instance Variables Added to `__init__()`
```python
# Hardware integration - production controller
self.io_manager = None
self.production_controller = None
self.station_configs = None
```

#### 3. Production Controller Initialization Method
```python
def _init_production_controller(self):
    """Initialize production controller for hardware-triggered operation."""
    # Loads station configs
    # Initializes I/O manager
    # Creates production controller
    # Configures all enabled stations
    # Sets inspection callback
```

#### 4. State Change Logic in `_apply_run_state()`
```python
# When transitioning to ONLINE
if online:
    if self.production_controller is None:
        self._init_production_controller()
    
    if self.production_controller is not None:
        self.production_controller.start_production()

# When transitioning to OFFLINE
else:
    if self.production_controller is not None:
        self.production_controller.stop_production()
```

#### 5. Production Inspection Callback
```python
def _production_inspection_callback(self, doc_index: int, frame: np.ndarray) -> bool:
    """Called by production controller when a frame is captured."""
    # Maps doc_index to station
    # Gets station parameters
    # Runs inspection (test_feed or test_top_bottom)
    # Updates UI with result
    # Saves failed images if enabled
    # Tracks alerts
    # Returns PASS/FAIL
```

## Hardware Requirements

### Minimum Setup
- **PCI-7230 I/O Card**: For position sensors and camera triggers
- **Position Sensors**: One per station (7 total)
- **MVS Cameras**: Doc1-Doc7 configured in Windows Registry

### Configuration Files

#### 1. Station Configuration (`station_trigger_config.json`)
Automatically created with defaults on first run:
```json
[
  {
    "doc_index": 1,
    "station_name": "Top",
    "position_sensor_line": 0,
    "camera_trigger_line": 0,
    "ejector_distance": 10,
    "use_hardware_trigger": true,
    "trigger_pulse_ms": 5,
    "enabled": true
  },
  ...
]
```

#### 2. Windows Registry
Camera configuration (created by `setup_cameras.py`):
- `Doc1CamSN` through `Doc7CamSN`: Camera serial numbers
- `Doc1Color` through `Doc7Color`: Camera types (0=mono, 1=color)
- `Doc1Model` through `Doc7Model`: Camera models
- `TopVisionEjectorDistance`, `BottomVisionEjectorDistance`: Trigger distances

## Operation Modes Comparison

| Feature | OFFLINE Mode | ONLINE Mode |
|---------|-------------|-------------|
| Production Controller | Stopped | Running |
| Position Sensors | Ignored | Monitored |
| Hardware Triggers | Disabled | Enabled |
| GRAB/LIVE Buttons | Active | Available |
| Teaching | Allowed | Blocked |
| Parameter Editing | Allowed | Limited |
| Inspection | Manual | Automatic |
| Multi-threading | No | Yes (7 threads) |

## Graceful Hardware Handling

The integration gracefully handles missing or disconnected hardware:

### No Hardware Scenario
```
[PROD] 🔧 Initializing production controller...
[PROD] ⚠️ I/O manager setup failed - hardware may not be connected
[PROD] → Production controller will not be available
[PROD] → Manual GRAB/LIVE will still work
```

**Result**: Application continues to work normally in manual mode.

### Partial Hardware Scenario
- If only some cameras are configured, those stations work
- Unconfigured stations are skipped
- System continues operating with available hardware

### Full Hardware Scenario
```
[PROD] 🔧 Initializing production controller...
[PROD] ✅ Loaded 7 station configurations
[PROD] ✅ I/O manager initialized
[PROD]   ✓ Doc1 (Top): sensor=0, trigger=0
[PROD]   ✓ Doc2 (Bottom): sensor=1, trigger=1
[PROD]   ... (all 7 stations)
[PROD] ✅ Configured 7 stations
[PROD] ✅ Inspection callback registered
[PROD] 🎉 Production controller ready for hardware-triggered operation
[PROD] ✅ Production controller started (hardware-triggered mode)
```

**Result**: Full automatic multi-station production operation.

## Testing

### Test Without Hardware
```bash
python test_main_window_production.py
```

This verifies:
- ✅ MainWindow initializes correctly
- ✅ ONLINE/OFFLINE transitions work
- ✅ Production controller initialization is attempted
- ✅ Inspection callback can be executed
- ✅ System handles missing hardware gracefully

### Test With Hardware
1. Connect PCI-7230 I/O card
2. Configure cameras: `python setup_cameras.py`
3. Run application: `python main.py`
4. Switch to ONLINE mode
5. Monitor console for production controller messages
6. Trigger position sensors to test full workflow

## Inspection Results

### Console Output
```
[PROD] Doc1 (Top): ✅ All tests passed
[PROD] Doc2 (Bottom): ❌ Body Length NG
[PROD] Doc3 (Feed): ✅ All tests passed
...
```

### UI Updates
- Result images displayed in Doc panels (if DEBUG_DRAW flag is set)
- Pass/fail indicators updated
- Defect tables populated
- Alert counters incremented for failures

### Saved Images
Failed images saved to:
```
New folder/
  Doc1_Top_f/        # Doc1 Top station failures
  Doc2_Bottom_f/     # Doc2 Bottom station failures
  ...
```

Only saved if `DEBUG_SAVE_FAIL_IMAGE` flag is enabled.

## Troubleshooting

### Production Controller Doesn't Start

**Check**:
1. Is system in ONLINE mode?
   - Menu shows "ONLINE" state
   - Window title shows "[ONLINE]"

2. Is hardware connected?
   - Check PCI-7230 card installation
   - Verify Device Manager shows I/O card
   - Check registry settings

3. Is DLL available?
   - Ensure PCI7230.dll is in PATH
   - Or in project root
   - Check DLL architecture (32-bit vs 64-bit)

**Solution**:
```bash
# Check I/O system first
python test_io_setup.py
```

### Cameras Not Capturing

**Check**:
1. Are cameras configured in registry?
   ```bash
   python setup_cameras.py
   ```

2. Are cameras connected and powered?
   - Check USB/Ethernet cables
   - Verify MVS SDK recognizes cameras

3. Is camera trigger working?
   ```bash
   python test_hardware_integration.py
   # Select option 2 to test hardware trigger
   ```

### Inspection Always Fails

**Check**:
1. Is station taught correctly?
   - Switch to OFFLINE
   - Load a good sample image
   - Select station
   - Go through teaching process

2. Are parameters correct?
   - Check `teach_data.json`
   - Verify package ROI
   - Check inspection thresholds

3. Is lighting correct?
   - Check camera exposure/gain settings
   - Verify LED controller intensities

## See Also

- [HARDWARE_INTEGRATION_GUIDE.md](HARDWARE_INTEGRATION_GUIDE.md) - Complete hardware setup
- [MVS_CAMERA_IMPLEMENTATION.md](MVS_CAMERA_IMPLEMENTATION.md) - Camera system details
- [CAMERA_CONFIGURATION_GUIDE.md](CAMERA_CONFIGURATION_GUIDE.md) - Camera setup guide
- `test_hardware_integration.py` - Hardware testing tools
- `station_trigger_config.py` - Configuration management
- `production_controller.py` - Controller implementation

## Quick Reference

### Switch to Production Mode
1. Launch application
2. Configure cameras (if first time)
3. Verify hardware connections
4. Menu: Run → Online/Offline (uncheck)
5. Production starts automatically

### Return to Manual Mode
1. Menu: Run → Online/Offline (check)
2. Production stops automatically
3. GRAB/LIVE buttons active

### Check Status
- Console messages show production controller state
- Window title shows current mode
- Doc panels update with live results
