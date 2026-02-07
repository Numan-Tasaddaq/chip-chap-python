# Hardware-Triggered Multi-Station Inspection System

## Overview

Complete hardware integration system connecting:
- **PCI-7230 I/O Card** - Position sensors and trigger outputs
- **MVS Cameras** (Doc1-Doc7) - Image capture with hardware triggering
- **Production Controller** - Multi-threaded position-based inspection workflow
- **Inspection Algorithms** - Real-time defect detection

## System Architecture

```
Position Sensor → I/O Card → Production Controller → Camera Trigger → MVS Camera
     (Input)         ↓              ↓                  (Output)          ↓
                  Software      Inspection          Hardware Trig    Image Capture
                               Algorithms               Pulse            ↓
                     ↓              ↓                     ↓          Frame Buffer
                Result Out ← Pass/Fail ← Frame Processing ← Inspection
                  (Output)
```

## Hardware Configuration

### Station Mapping (Doc1-Doc7)

| Doc Index | Station Name | Position Sensor Line | Camera Trigger Line | Ejector Distance |
|-----------|--------------|----------------------|---------------------|------------------|
| **Doc1**  | TOP          | I/O In Line 0        | I/O Out Line 0      | 10               |
| **Doc2**  | BOTTOM       | I/O In Line 1        | I/O Out Line 1      | 4                |
| **Doc3**  | FEED         | I/O In Line 2        | I/O Out Line 2      | 0                |
| **Doc4**  | PICKUP1      | I/O In Line 3        | I/O Out Line 3      | 0                |
| **Doc5**  | PICKUP2      | I/O In Line 4        | I/O Out Line 4      | 0                |
| **Doc6**  | BOTTOM_SEAL  | I/O In Line 5        | I/O Out Line 5      | 0                |
| **Doc7**  | TOP_SEAL     | I/O In Line 6        | I/O Out Line 6      | 0                |

### I/O Card Connections

**PCI-7230 Card:**
- **37-pin connector** → Machine I/O board
- **Input Port (PA):** Position sensors (8 lines, 0-7)
- **Output Port (PB):** Camera triggers + results (8 lines, 0-7)
- **RS232:** Communication with controller (optional)

**Cable Routing:**
- VGA cable → Monitor
- USB cables → Cameras (or IEEE 1394 for old controllers)
- Trigger cables → Camera hardware trigger inputs
- 37-pin parallel → Machine I/O board

## Software Components

### 1. IOManager (device/io_manager.py)
**Purpose:** High-level I/O operations with PCI-7230 card

**Key Methods:**
```python
# Position sensor reading
read_position_sensor(line_number: int) -> bool
wait_for_position_sensor(line_number, timeout_ms) -> bool

# Hardware trigger output
send_hardware_trigger(camera_line, pulse_duration_ms) -> bool

# Production workflow
send_result(result: int, wait_timeout_ms) -> bool
```

### 2. ProductionController (device/production_controller.py)
**Purpose:** Multi-threaded hardware-triggered inspection workflow

**Architecture:**
- One thread per station (Doc1-Doc7)
- Each thread waits for position sensor independently
- Position trigger → Hardware trigger → Camera capture → Inspection → Result

**Key Methods:**
```python
# Configure stations
configure_station(doc_index, position_sensor_line, 
                 camera_trigger_line, ejector_distance)

# Set inspection callback
set_inspection_callback(callback_function)

# Start/stop production
start_production() -> bool
stop_production()
```

**Production Loop (per station thread):**
```
while running:
    1. Wait for position sensor trigger (rising edge)
    2. Send hardware trigger pulse to camera
    3. Camera captures frame (hardware triggered)
    4. Open MVS camera by serial from registry
    5. Grab frame (timeout 2000ms)
    6. Run inspection callback on frame
    7. Send pass/fail result to handler via I/O
    8. Wait for handler acknowledgement
    9. Clear busy bit
    10. Repeat for next part
```

### 3. StationTriggerConfig (config/station_trigger_config.py)
**Purpose:** Per-station trigger configuration storage

**Configuration File:** `station_trigger_config.json`

**Structure:**
```json
{
  "stations": [
    {
      "doc_index": 1,
      "station_name": "TOP",
      "position_sensor_line": 0,
      "camera_trigger_line": 0,
      "ejector_distance": 10,
      "use_hardware_trigger": true,
      "trigger_pulse_ms": 10.0,
      "enabled": true
    },
    ...
  ]
}
```

**Registry Integration:**
- Reads `TopVisionEjectorDistance` and `BottomVisionEjectorDistance` from Windows Registry
- Auto-updates config from registry values

## Setup Workflow

### Step 1: Hardware Setup
1. Install PCI-7230 I/O card in PC
2. Connect 37-pin cable: PC → Machine I/O board
3. Connect position sensors to input lines
4. Connect camera trigger lines to camera/controller
5. Connect MVS cameras via USB/GigE

### Step 2: Configure I/O System
```bash
# Run I/O registry test to configure card
python test_io_registry.py
```

This sets up:
- I/O DLL name (PCI7230 or ITrueParallelPort)
- Input card/port configuration
- Output card/port configuration

### Step 3: Configure Cameras
```bash
# Enumerate cameras and write to registry
python setup_cameras.py
```

Select option `[1]` for auto-configure or `[2]` for manual.

### Step 4: Configure Station Triggers
```bash
# Create/edit station_trigger_config.json
python config/station_trigger_config.py
```

Or manually edit `station_trigger_config.json` to adjust:
- Position sensor line assignments
- Camera trigger line assignments
- Ejector distances
- Enable/disable specific stations

### Step 5: Test Hardware Integration
```bash
python test_hardware_integration.py
```

**Test Menu Options:**
1. Test position sensor reading (single station)
2. Test hardware trigger output (single pulse)
3. Test single-station capture (sensor → trigger → capture)
4. Start production loop (all stations, hardware-triggered)
5. View statistics

## Production Integration

### In Main Application (main.py)

```python
from device.io_manager import IOManager, get_io_manager
from device.production_controller import ProductionController
from config.station_trigger_config import StationTriggerConfigManager

# Initialize I/O system
io_manager = get_io_manager()
if not io_manager.setup():
    print("Failed to initialize I/O system")
    return

# Load station configurations
station_configs = StationTriggerConfigManager.load_config()

# Create production controller
controller = ProductionController(io_manager, grab_service)

# Configure all stations
for doc_idx, config in station_configs.items():
    if config.enabled:
        controller.configure_station(
            doc_index=config.doc_index,
            position_sensor_line=config.position_sensor_line,
            camera_trigger_line=config.camera_trigger_line,
            ejector_distance=config.ejector_distance,
            use_hardware_trigger=config.use_hardware_trigger
        )

# Set inspection callback
def inspection_callback(doc_index, frame):
    # Run your inspection algorithms here
    result = run_inspection(doc_index, frame)
    return result == PASS

controller.set_inspection_callback(inspection_callback)

# Start production when user clicks "Start" or goes ONLINE
controller.start_production()

# Stop production when user clicks "Stop" or goes OFFLINE
controller.stop_production()
```

### Inspection Callback Signature

```python
def inspection_callback(doc_index: int, frame: np.ndarray) -> bool:
    """
    Args:
        doc_index: Station Doc index (1-7)
        frame: Captured image (numpy array)
    
    Returns:
        True if passed, False if failed
    """
    # Your inspection logic
    station_name = CameraRegistry.get_station_name(doc_index)
    
    # Run defect detection
    defects = detect_defects(frame, doc_index)
    
    # Determine pass/fail
    passed = len(defects) == 0
    
    # Update UI with results
    update_inspection_results(doc_index, passed, defects)
    
    return passed
```

## Hardware Trigger Modes

### Mode 1: Hardware Trigger (Recommended)
**Setup:**
1. Camera set to hardware trigger mode (`TriggerMode=1`)
2. Position sensor triggers I/O output line
3. I/O output line connected to camera trigger input
4. Camera captures on rising edge of trigger pulse

**Advantages:**
- Precise timing (hardware-level synchronization)
- No software delays
- Consistent frame captures

**Configuration:**
```python
config.use_hardware_trigger = True
config.trigger_pulse_ms = 10.0  # 10ms pulse duration
```

### Mode 2: Software Trigger
**Setup:**
1. Camera set to trigger mode (`TriggerMode=1`)
2. Position sensor triggers software
3. Software sends `camera.software_trigger()` command
4. Camera captures on software trigger

**Advantages:**
- No external trigger wiring needed
- Simpler hardware setup

**Configuration:**
```python
config.use_hardware_trigger = False
```

## Troubleshooting

### Position Sensor Not Triggering
**Symptoms:** `wait_for_position_sensor()` times out

**Solutions:**
1. Check sensor wiring to I/O card input port
2. Verify sensor line number in config matches physical connection
3. Test sensor with voltmeter (should be 0V/5V or 0V/24V)
4. Check I/O card input port configuration (PA mode should be INPUT)
5. Run `test_io_read_write.py` to manually test input lines

### Camera Not Capturing on Trigger
**Symptoms:** Frame capture times out after trigger

**Solutions:**
1. Verify camera is in hardware trigger mode: `camera.set_trigger_mode(True)`
2. Check trigger cable connection: I/O output → Camera trigger input
3. Verify trigger line number matches hardware wiring
4. Test trigger output with oscilloscope (should see 10ms pulse)
5. Check camera trigger polarity (rising vs falling edge)
6. Increase frame timeout: `camera.grab_frame(timeout_ms=5000)`

### Multiple Stations Interfering
**Symptoms:** Wrong camera captures or missed captures

**Solutions:**
1. Verify each station thread is monitoring correct sensor line
2. Check for sensor line conflicts (one sensor per line)
3. Ensure each camera has unique trigger line
4. Verify registry has correct camera serials per Doc index
5. Check for I/O port conflicts (input vs output)

### I/O Card Not Found
**Symptoms:** `IOManager.setup()` fails with DLL error

**Solutions:**
1. Verify PCI-7230 card installed in PC
2. Check Device Manager for card presence
3. Install/reinstall PCI-7230 drivers
4. Verify registry has correct DLL name (`PCI7230` or `ITrueParallelPort`)
5. Try hardware simulator mode for testing without card

## Performance Optimization

### Trigger Timing
- **20 Trigger pulse:** 10ms (configurable per station)
- **Camera exposure:** Set appropriately for lighting (e.g., 5000 μs)
- **Frame capture timeout:** 2000ms (allows for slow frames)
- **Result acknowledgement timeout:** 5000ms

### Thread Safety
- Each station runs in separate thread (7 threads total)
- No shared camera resources (each thread opens/closes its own)
- I/O operations are thread-safe via ctypes/DLL

### Throughput
- **Per-station cycle time:** ~100-500ms (sensor wait + trigger + capture + inspect)
- **Max throughput:** Limited by mechanical feed rate, not software
- **Concurrent stations:** All 7 stations run simultaneously without interference

## Summary

✅ **Hardware I/O Integration:** PCI-7230 card with position sensors and trigger outputs  
✅ **Multi-Station Support:** 7 independent stations (Doc1-Doc7) with concurrent inspection  
✅ **Hardware Triggering:** Precise camera synchronization via I/O trigger pulses  
✅ **Production Loop:** Multi-threaded workflow with position-based triggering  
✅ **Configuration:** JSON-based per-station trigger settings with registry integration  
✅ **Testing:** Complete test suite for I/O, cameras, and full workflow validation  
✅ **Production Ready:** Matches old system architecture with improved multi-threading
