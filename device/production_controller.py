"""
Production Controller - Hardware-triggered multi-station inspection workflow

Integrates:
1. Position sensors (via I/O card) - Detect chip at each station
2. Camera hardware triggers (via I/O card or controller) - Trigger camera capture
3. MVS cameras (Doc1-Doc7) - Capture images
4. Inspection algorithms - Process images and detect defects  
5. Result output (via I/O card) - Send pass/fail to handler/ejector

Production Flow:
    Position sensor active → Hardware trigger → Camera capture → 
    Inspection → Pass/Fail result → Handler acknowledge → Next part
"""

from typing import Optional, Callable, Dict
from dataclasses import dataclass
import time
import threading
import queue

from device.io_manager import IOManager
from device.camera_registry import CameraRegistry
from device.mvs_camera import MVSCamera
from imaging.grab_service import GrabService
from device.io_constants import RESULT_PASS, RESULT_FAIL_GENERAL


@dataclass
class StationConfig:
    """Configuration for one inspection station"""
    doc_index: int                    # Doc1-Doc7
    station_name: str                 # TOP, BOTTOM, FEED, etc.
    position_sensor_line: int         # I/O line for position sensor (0-7)
    camera_trigger_line: int          # I/O line for camera trigger (0-7) 
    ejector_distance: int             # Distance from sensor to ejector (for timing)
    use_hardware_trigger: bool = True # True = hardware trigger, False = software
    trigger_pulse_ms: float = 10.0    # Trigger pulse duration in milliseconds


class ProductionController:
    """
    Hardware-triggered production workflow controller.
    
    Manages concurrent inspection across multiple stations with position-based triggering.
    """
    
    def __init__(self, io_manager: IOManager, grab_service: GrabService):
        """
        Initialize production controller.
        
        Args:
            io_manager: Initialized IO manager for hardware I/O
            grab_service: Grab service for camera operations
        """
        self.io_manager = io_manager
        self.grab_service = grab_service
        
        # Station configurations (Doc1-Doc7)
        self.station_configs: Dict[int, StationConfig] = {}
        
        # Production control
        self.is_running = False
        self.station_threads: Dict[int, threading.Thread] = {}
        self.stop_event = threading.Event()
        
        # Inspection callback (provided by application)
        self.inspection_callback: Optional[Callable] = None
        
        # Statistics
        self.stats = {
            "total_inspected": 0,
            "total_passed": 0,
            "total_failed": 0
        }
    
    def configure_station(self, doc_index: int, position_sensor_line: int,
                         camera_trigger_line: int, ejector_distance: int = 0,
                         use_hardware_trigger: bool = True) -> None:
        """
        Configure one inspection station.
        
        Args:
            doc_index: Doc1-Doc7 index
            position_sensor_line: I/O input line for position sensor
            camera_trigger_line: I/O output line for camera trigger
            ejector_distance: Distance from sensor to ejector (timing calculation)
            use_hardware_trigger: True for hardware trigger, False for software
        
        Example:
            # Configure TOP station (Doc1)
            controller.configure_station(
                doc_index=1,
                position_sensor_line=2,  # Input line 2
                camera_trigger_line=0,    # Output line 0
                ejector_distance=10,
                use_hardware_trigger=True
            )
        """
        station_name = CameraRegistry.get_station_name(doc_index) or f"Unknown_Doc{doc_index}"
        
        config = StationConfig(
            doc_index=doc_index,
            station_name=station_name,
            position_sensor_line=position_sensor_line,
            camera_trigger_line=camera_trigger_line,
            ejector_distance=ejector_distance,
            use_hardware_trigger=use_hardware_trigger
        )
        
        self.station_configs[doc_index] = config
        print(f"[PRODUCTION] Configured {station_name} (Doc{doc_index}): "
              f"sensor_line={position_sensor_line}, trigger_line={camera_trigger_line}")
    
    def set_inspection_callback(self, callback: Callable) -> None:
        """
        Set inspection processing callback.
        
        Callback signature: (doc_index: int, frame: np.ndarray) -> bool
        Returns: True if passed, False if failed
        
        Example:
            def my_inspection(doc_index, frame):
                # Run inspection algorithms
                result = run_inspection(frame)
                return result == PASS
            
            controller.set_inspection_callback(my_inspection)
        """
        self.inspection_callback = callback
    
    def start_production(self) -> bool:
        """
        Start production loop for all configured stations.
        Each station runs in its own thread waiting for position triggers.
        
        Returns:
            True if started successfully
        """
        if self.is_running:
            print("[PRODUCTION] Already running")
            return False
        
        if not self.station_configs:
            print("[PRODUCTION] No stations configured")
            return False
        
        if not self.io_manager.is_initialized:
            print("[PRODUCTION] I/O system not initialized")
            return False
        
        print(f"[PRODUCTION] Starting production for {len(self.station_configs)} stations...")
        
        self.is_running = True
        self.stop_event.clear()
        
        # Start thread for each configured station
        for doc_index, config in self.station_configs.items():
            thread = threading.Thread(
                target=self._station_loop,
                args=(config,),
                name=f"Station-Doc{doc_index}",
                daemon=True
            )
            thread.start()
            self.station_threads[doc_index] = thread
            print(f"[PRODUCTION] Started thread for {config.station_name}")
        
        print("[PRODUCTION] Production started")
        return True
    
    def stop_production(self) -> None:
        """Stop production loop for all stations."""
        if not self.is_running:
            return
        
        print("[PRODUCTION] Stopping production...")
        self.is_running = False
        self.stop_event.set()
        
        # Wait for all threads to finish
        for doc_index, thread in self.station_threads.items():
            thread.join(timeout=2.0)
            print(f"[PRODUCTION] Stopped Doc{doc_index} thread")
        
        self.station_threads.clear()
        print("[PRODUCTION] Production stopped")
    
    def _station_loop(self, config: StationConfig) -> None:
        """
        Production loop for one station (runs in separate thread).
        
        Loop:
            1. Wait for position sensor trigger
            2. Send hardware trigger to camera (or software trigger)
            3. Capture image from camera
            4. Run inspection callback
            5. Send pass/fail result to handler
            6. Wait for handler ACK
            7. Repeat
        
        Args:
            config: Station configuration
        """
        print(f"[{config.station_name}] Production loop started")
        
        while self.is_running and not self.stop_event.is_set():
            try:
                # Step 1: Wait for position sensor (with timeout for responsiveness)
                sensor_triggered = self.io_manager.wait_for_position_sensor(
                    line_number=config.position_sensor_line,
                    timeout_ms=500,  # Short timeout for stop responsiveness
                    rising_edge=True
                )
                
                if not sensor_triggered:
                    continue  # Timeout, check stop flag and retry
                
                print(f"[{config.station_name}] Position sensor triggered")
                
                # Step 2: Trigger camera
                if config.use_hardware_trigger:
                    # Hardware trigger via I/O line
                    self.io_manager.send_hardware_trigger(
                        camera_line=config.camera_trigger_line,
                        pulse_duration_ms=config.trigger_pulse_ms
                    )
                    print(f"[{config.station_name}] Hardware trigger sent")
                
                # Step 3: Capture image
                # Note: For hardware triggered cameras, grab_frame waits for triggered frame
                # For software trigger, we can call camera.software_trigger() here
                frame, doc_index_returned = self._capture_frame(config)
                
                if frame is None:
                    print(f"[{config.station_name}] Failed to capture frame")
                    continue
                
                print(f"[{config.station_name}] Frame captured: {frame.shape}")
                
                # Step 4: Run inspection
                result = self._run_inspection(config.doc_index, frame)
                
                self.stats["total_inspected"] += 1
                if result:
                    self.stats["total_passed"] += 1
                else:
                    self.stats["total_failed"] += 1
                
                print(f"[{config.station_name}] Inspection result: {'PASS' if result else 'FAIL'}")
                
                # Step 5: Send result to handler
                result_code = RESULT_PASS if result else RESULT_FAIL_GENERAL
                self.io_manager.send_result(result_code, wait_timeout_ms=5000)
                
                print(f"[{config.station_name}] Result sent to handler")
                
            except Exception as e:
                print(f"[{config.station_name}] Error in production loop: {e}")
                time.sleep(0.1)  # Prevent tight loop on persistent errors
        
        print(f"[{config.station_name}] Production loop stopped")
    
    def _capture_frame(self, config: StationConfig):
        """
        Capture frame from camera for this station.
        
        Args:
            config: Station configuration
        
        Returns:
            Tuple of (frame, doc_index) or (None, None) if failed
        """
        try:
            # Get camera serial from registry
            cameras = CameraRegistry.read_registry()
            serial = cameras.get(config.doc_index)
            
            if not serial:
                print(f"[{config.station_name}] No camera serial in registry")
                return None, None
            
            # Open camera
            camera = MVSCamera()
            if not camera.open_camera(serial):
                print(f"[{config.station_name}] Failed to open camera {serial}")
                return None, None
            
            # Start grabbing
            if not camera.start_grabbing():
                print(f"[{config.station_name}] Failed to start grabbing")
                camera.close_camera()
                return None, None
            
            # For software trigger mode, send trigger now
            if not config.use_hardware_trigger:
                camera.software_trigger()
            
            # Wait for frame (hardware or software triggered)
            frame = camera.grab_frame(timeout_ms=2000)
            
            # Cleanup
            camera.stop_grabbing()
            camera.close_camera()
            
            return frame, config.doc_index
            
        except Exception as e:
            print(f"[{config.station_name}] Error capturing frame: {e}")
            return None, None
    
    def _run_inspection(self, doc_index: int, frame) -> bool:
        """
        Run inspection on captured frame.
        
        Args:
            doc_index: Station Doc index
            frame: Captured image
        
        Returns:
            True if passed, False if failed
        """
        if self.inspection_callback:
            try:
                return self.inspection_callback(doc_index, frame)
            except Exception as e:
                print(f"[Doc{doc_index}] Inspection callback error: {e}")
                return False
        else:
            # No callback - default to PASS
            print(f"[Doc{doc_index}] No inspection callback, defaulting to PASS")
            return True
    
    def get_statistics(self) -> dict:
        """Get production statistics."""
        return self.stats.copy()
    
    def reset_statistics(self) -> None:
        """Reset production statistics."""
        self.stats = {
            "total_inspected": 0,
            "total_passed": 0,
            "total_failed": 0
        }


# Example usage configuration for old system stations
def configure_standard_7_station_system(controller: ProductionController) -> None:
    """
    Configure controller for standard 7-station system matching old hardware.
    
    Station mapping (from hardware images):
    - Station 1-3: Rotating turret (TOP, BOTTOM, FEED)
    - Station 4-7: Linear stages (PICKUP1, PICKUP2, BOTTOM_SEAL, TOP_SEAL)
    
    Args:
        controller: ProductionController instance
    """
    # Doc1: TOP inspection (Station 1)
    controller.configure_station(
        doc_index=1,
        position_sensor_line=0,   # I/O input line 0
        camera_trigger_line=0,     # I/O output line 0
        ejector_distance=10,       # From registry: TopVisionEjectorDistance
        use_hardware_trigger=True
    )
    
    # Doc2: BOTTOM inspection (Station 2) 
    controller.configure_station(
        doc_index=2,
        position_sensor_line=1,   # I/O input line 1
        camera_trigger_line=1,     # I/O output line 1
        ejector_distance=4,        # From registry: BottomVisionEjectorDistance
        use_hardware_trigger=True
    )
    
    # Doc3: FEED station (Station 3)
    controller.configure_station(
        doc_index=3,
        position_sensor_line=2,
        camera_trigger_line=2,
        ejector_distance=0,
        use_hardware_trigger=True
    )
    
    # Doc4: PICKUP 1 (Station 4)
    controller.configure_station(
        doc_index=4,
        position_sensor_line=3,
        camera_trigger_line=3,
        ejector_distance=0,
        use_hardware_trigger=True
    )
    
    # Doc5: PICKUP 2 (Station 5)
    controller.configure_station(
        doc_index=5,
        position_sensor_line=4,
        camera_trigger_line=4,
        ejector_distance=0,
        use_hardware_trigger=True
    )
    
    # Doc6: BOTTOM SEAL (Station 6)
    controller.configure_station(
        doc_index=6,
        position_sensor_line=5,
        camera_trigger_line=5,
        ejector_distance=0,
        use_hardware_trigger=True
    )
    
    # Doc7: TOP SEAL (Station 7)
    controller.configure_station(
        doc_index=7,
        position_sensor_line=6,
        camera_trigger_line=6,
        ejector_distance=0,
        use_hardware_trigger=True
    )
    
    print("[PRODUCTION] Configured standard 7-station system")


if __name__ == "__main__":
    # Test/Example
    print("Production Controller Module")
    print("=" * 60)
    print("This module integrates I/O hardware with camera system")
    print("for hardware-triggered multi-station inspection.")
    print()
    print("Usage:")
    print("  1. Initialize IO manager: io = IOManager(); io.setup()")
    print("  2. Initialize grab service: grab = GrabService(main_window)")
    print("  3. Create controller: ctrl = ProductionController(io, grab)")
    print("  4. Configure stations: configure_standard_7_station_system(ctrl)")
    print("  5. Set inspection callback: ctrl.set_inspection_callback(my_func)")
    print("  6. Start production: ctrl.start_production()")
