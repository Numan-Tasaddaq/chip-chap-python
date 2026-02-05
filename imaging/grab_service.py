# imaging/grab_service.py
import cv2
import json
from pathlib import Path
import numpy as np
from typing import Dict, Tuple, Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap

from device.camera_registry import CameraRegistry
from device.mvs_camera import MVSCamera
from config.camera_parameters_io import load_camera_parameters


class GrabService:
    """
    Handles GRAB and LIVE camera operations using HIKVision MVS SDK.

    - GRAB  : single frame capture
    - LIVE  : continuous capture using QTimer
    """

    def __init__(self, main_window):
        self.main_window = main_window
        self.mvs_camera = None  # MVS SDK camera instance
        self.cap = None  # OpenCV fallback
        self.live_timer = QTimer()
        self.live_timer.timeout.connect(self._grab_live_frame)
        self.live_running = False
        self.using_mvs_sdk = False  # Track which backend is active
        self.live_doc_index = None

        # Load camera registry (serial number mapping)
        self.registry_cameras = CameraRegistry.read_registry()
        
        # Log detected cameras from registry
        self._log_registry_cameras()

        # Initialize MVS SDK
        try:
            self.mvs_camera = MVSCamera()
            print("[CAMERA] MVS SDK initialized")
        except Exception as e:
            print(f"[CAMERA] MVS SDK not available: {e}")
            self.mvs_camera = None

        # Optional JSON configuration for cameras (OpenCV fallback)
        self.camera_settings = self._load_camera_settings()
        self.camera_map = self._build_camera_map()
    
    def _log_registry_cameras(self):
        """Log detected cameras from registry"""
        if not self.registry_cameras:
            print("[CAMERA] No cameras configured in Windows Registry")
            print("[CAMERA] Please run setup_cameras.py to configure camera serial numbers")
            return
        
        print(f"[CAMERA] Detected {len(self.registry_cameras)} camera(s) from registry:")
        for doc_idx, serial in self.registry_cameras.items():
            station = CameraRegistry.get_station_name(doc_idx)
            print(f"[CAMERA]   Doc{doc_idx} ({station}): {serial}")
    
    def get_camera_count(self) -> int:
        """
        Get number of cameras configured in registry.
        This should be used by UI to create dynamic camera display panels.
        
        Returns:
            int: Number of cameras configured (0-7)
        """
        return len(self.registry_cameras)
    
    def get_configured_cameras(self) -> Dict[int, Tuple[str, str]]:
        """
        Get all configured cameras with their station names.
        
        Returns:
            dict: {doc_index: (station_name, serial_number)}
            Example: {1: ("TOP", "FA1234567890"), 2: ("BOTTOM", "FA0987654321")}
        """
        result = {}
        for doc_idx, serial in self.registry_cameras.items():
            station = CameraRegistry.get_station_name(doc_idx)
            result[doc_idx] = (station, serial)
        return result

    def _build_camera_map(self):
        """
        Build camera map from registry and settings.
        Maps (track, station) to camera selector.

        Returns:
            dict: {(track, station): camera_selector}
        """
        camera_map = {}
        camera_list = self.camera_settings.get("cameras", [])

        for cam_config in camera_list:
            doc_index = cam_config.get("doc_index")
            station = cam_config.get("station")

            if not (doc_index and station):
                continue

            track = self.main_window.state.track
            key = (track, station)

            dshow_name = cam_config.get("dshow_name")
            cv_index = cam_config.get("index")

            if dshow_name:
                camera_map[key] = f"video={dshow_name}"
            elif isinstance(cv_index, int):
                camera_map[key] = cv_index

        return camera_map

    # =================================================
    # GRAB (single frame)
    # =================================================
    def grab(self):
        # Disabled in simulator mode
        if self.main_window.is_simulator_mode:
            return

        # Only allowed in ONLINE
        if self.main_window.state.run_state.name != "ONLINE":
            return

        # If LIVE is running, stop it first (old ChipCap behavior)
        if self.live_running:
            self.stop_live()

        # Try MVS SDK first
        if self.mvs_camera is not None:
            try:
                frame, doc_index = self._grab_mvs_frame()
                if frame is not None:
                    self.main_window.current_image = frame
                    self._display_frame(frame, doc_index)
                    return
            except Exception as e:
                print(f"[CAMERA] GRAB: MVS SDK failed: {e}")

        # Fallback to OpenCV
        print("[CAMERA] GRAB: Using OpenCV fallback")
        allow_laptop_fallback = self._allow_laptop_fallback()
        source, backend, doc_index = self._resolve_camera_source(allow_laptop_fallback)
        if source is None:
            print("[CAMERA] GRAB: No camera configured for this station")
            return
        cap = self._open_capture(source, backend)

        if not cap.isOpened():
            if allow_laptop_fallback:
                print("[CAMERA] GRAB: Failed to open camera. Falling back to laptop camera (index 0).")
                cap.release()
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    print("[CAMERA] GRAB: Laptop camera also failed.")
                    cap.release()
                    return
                else:
                    print("[CAMERA] GRAB: Laptop camera opened successfully.")
            else:
                print("[CAMERA] GRAB: Failed to open camera for this station.")
                cap.release()
                return

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return

        self.main_window.current_image = frame
        self._display_frame(frame, doc_index)

    # =================================================
    # LIVE (continuous)
    # =================================================
    def toggle_live(self):
        if self.live_running:
            self.stop_live()
        else:
            self.start_live()

    def start_live(self):
        # Disabled in simulator mode
        if self.main_window.is_simulator_mode:
            return

        # Only allowed in ONLINE
        if self.main_window.state.run_state.name != "ONLINE":
            return

        if self.live_running:
            return

        # Try MVS SDK first
        if self.mvs_camera is not None:
            try:
                if self._start_mvs_live():
                    self.using_mvs_sdk = True
                    self.live_doc_index = self._get_doc_index_for_current_station()
                    self.live_running = True
                    self.live_timer.start(30)  # ~30 FPS
                    return
            except Exception as e:
                print(f"[CAMERA] LIVE: MVS SDK failed: {e}")
                self.using_mvs_sdk = False

        # Fallback to OpenCV
        print("[CAMERA] LIVE: Using OpenCV fallback")
        self.using_mvs_sdk = False
        allow_laptop_fallback = self._allow_laptop_fallback()
        source, backend, doc_index = self._resolve_camera_source(allow_laptop_fallback)
        if source is None:
            print("[CAMERA] LIVE: No camera configured for this station")
            return
        self.cap = self._open_capture(source, backend)
        self.live_doc_index = doc_index

        if not self.cap.isOpened():
            if allow_laptop_fallback:
                print("[CAMERA] LIVE: Failed to open preferred camera. Trying laptop camera (index 0).")
                self.cap.release()
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    print("[CAMERA] LIVE: Laptop camera also failed.")
                    if self.cap:
                        self.cap.release()
                    self.cap = None
                    return
                else:
                    print("[CAMERA] LIVE: Laptop camera opened successfully.")
            else:
                print("[CAMERA] LIVE: Failed to open camera for this station.")
                if self.cap:
                    self.cap.release()
                self.cap = None
                return

        self.live_running = True
        self.live_timer.start(30)  # ~30 FPS

    def stop_live(self):
        if not self.live_running:
            return

        self.live_timer.stop()
        self.live_running = False

        # Stop MVS SDK acquisition
        if self.using_mvs_sdk and self.mvs_camera is not None:
            try:
                self.mvs_camera.stop_grabbing()
                self.mvs_camera.close_camera()
            except Exception as e:
                print(f"[CAMERA] Stop MVS SDK error: {e}")
            self.using_mvs_sdk = False

        # Stop OpenCV
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def _grab_live_frame(self):
        # MVS SDK path
        if self.using_mvs_sdk and self.mvs_camera is not None:
            try:
                frame = self.mvs_camera.grab_frame(timeout_ms=100)
                if frame is not None:
                    # Convert mono to BGR for display
                    if len(frame.shape) == 2:
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    self.main_window.current_image = frame
                    self._display_frame(frame, self.live_doc_index)
            except Exception as e:
                print(f"[CAMERA] MVS grab error: {e}")
            return

        # OpenCV path
        if not self.cap:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        self.main_window.current_image = frame
        self._display_frame(frame, self.live_doc_index)

    # =================================================
    # Display helper
    # =================================================
    def _display_frame(self, frame, doc_index=None):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w

        # Copy RGB data to prevent memory sharing
        rgb_copy = rgb.copy()
        qimg = QImage(
            rgb_copy.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        ).copy()

        pix = QPixmap.fromImage(qimg)
        if doc_index:
            self.main_window._display_pixmap_to_doc(doc_index, pix)
        else:
            self.main_window._display_pixmap(pix)
        self.main_window.current_image = frame

    # =================================================
    # Camera selection helpers
    # =================================================
    def _load_camera_settings(self):
        """Load optional camera settings from camera_settings.json."""
        settings_path = Path("camera_settings.json")
        if not settings_path.exists():
            return {}
        try:
            with settings_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            print("[CAMERA] Loaded camera_settings.json")
            return data
        except Exception as e:
            print(f"[CAMERA] Failed to load camera_settings.json: {e}")
            return {}

    def _resolve_camera_source(self, allow_laptop_fallback: bool):
        """
        Resolve preferred camera (OpenCV fallback only).
        Returns: (source, backend)
        """
        track = self.main_window.state.track
        station_enum = self.main_window.state.station
        station_str = station_enum.name if hasattr(station_enum, 'name') else str(station_enum).upper()

        doc_index = CameraRegistry.get_doc_index(station_str)

        if doc_index:
            print(f"[CAMERA] Station '{station_str}' mapped to Doc{doc_index}")
            camera_list = self.camera_settings.get("cameras", [])
            for cam_config in camera_list:
                if cam_config.get("doc_index") == doc_index:
                    dshow_name = cam_config.get("dshow_name", "").strip()
                    cv_index = cam_config.get("index")

                    if dshow_name:
                        print(f"[CAMERA] Doc{doc_index}: Using DirectShow '{dshow_name}'")
                        return f"video={dshow_name}", cv2.CAP_DSHOW, doc_index

                    if isinstance(cv_index, int) and cv_index >= 0:
                        print(f"[CAMERA] Doc{doc_index}: Using CV index {cv_index}")
                        return cv_index, None, doc_index

        # Check global preferred settings
        preferred = self.camera_settings.get("preferred", {})
        dshow_name = preferred.get("dshow_name", "").strip()
        idx = preferred.get("index")

        if dshow_name:
            print(f"[CAMERA] Using preferred DirectShow device: '{dshow_name}'")
            return f"video={dshow_name}", cv2.CAP_DSHOW, doc_index

        if isinstance(idx, int) and idx >= 0:
            print(f"[CAMERA] Using preferred index from settings: {idx}")
            return idx, None, doc_index

        # Check camera_map by (track, station)
        key = (track, station_str)
        if key in self.camera_map:
            selector = self.camera_map[key]
            if isinstance(selector, dict):
                name = selector.get("dshow_name")
                if name:
                    print(f"[CAMERA] Map DShow: '{name}' for {key}")
                    return f"video={name}", cv2.CAP_DSHOW, doc_index
                idx2 = selector.get("index")
                if isinstance(idx2, int):
                    print(f"[CAMERA] Map index: {idx2} for {key}")
                    return idx2, None, doc_index
            elif isinstance(selector, str):
                print(f"[CAMERA] Map string selector: {selector}")
                backend = cv2.CAP_DSHOW if selector.startswith("video=") else None
                return selector, backend, doc_index
            elif isinstance(selector, int):
                print(f"[CAMERA] Map index: {selector} for {key}")
                return selector, None, doc_index

        if allow_laptop_fallback:
            print("[CAMERA] No specific camera found. Using laptop camera (index 0).")
            return 0, cv2.CAP_DSHOW, 1

        print("[CAMERA] No specific camera found for this station.")
        return None, None, None

    def _open_capture(self, source, backend=None):
        """Open cv2.VideoCapture with optional backend."""
        try:
            if backend is not None:
                cap = cv2.VideoCapture(source, backend)
            else:
                cap = cv2.VideoCapture(source)
        except Exception as e:
            print(f"[CAMERA] OpenCapture error for source '{source}': {e}")
            return cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if cap.isOpened():
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"[CAMERA] Opened source={source} backend={backend} size={int(width)}x{int(height)} fps={fps:.1f}")
        else:
            print(f"[CAMERA] Failed to open source={source} backend={backend}")

        return cap

    # =================================================
    # MVS SDK helpers
    # =================================================
    def _get_doc_index_for_current_station(self) -> Optional[int]:
        station_enum = self.main_window.state.station
        station_name = station_enum.name if hasattr(station_enum, "name") else str(station_enum).upper()
        return CameraRegistry.get_doc_index(station_name)

    def _get_camera_serial_for_station(self) -> Optional[str]:
        """Get camera serial number for current station from registry"""
        doc_index = self._get_doc_index_for_current_station()
        if not doc_index:
            return None
        return self.registry_cameras.get(doc_index)

    def _allow_laptop_fallback(self) -> bool:
        """Only allow laptop camera fallback for Station 1 (Doc1) when not configured."""
        doc_index = self._get_doc_index_for_current_station()
        return doc_index == 1 and doc_index not in self.registry_cameras
    
    def _load_camera_settings_for_track(self) -> dict:
        """Load camera settings from .cam file for current track"""
        try:
            config_name = self.main_window.state.config_name
            track = self.main_window.state.track
            
            # Get inspection directory
            inspection_dir = Path(self.main_window.state.inspection_dir)
            config_dir = inspection_dir / config_name
            
            if not config_dir.exists():
                print(f"[CAMERA] Config dir not found: {config_dir}")
                return {}
            
            settings = load_camera_parameters(str(config_dir), config_name, track)
            return settings
        except Exception as e:
            print(f"[CAMERA] Failed to load camera settings: {e}")
            return {}
    
    def _grab_mvs_frame(self) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """Grab single frame using MVS SDK"""
        doc_index = self._get_doc_index_for_current_station()
        serial = self._get_camera_serial_for_station()
        if not serial:
            return None, doc_index
        
        print(f"[CAMERA] Opening camera: {serial}")
        
        # Open camera by serial
        if not self.mvs_camera.open_camera(serial):
            raise RuntimeError(f"Failed to open camera {serial}")
        
        # Load and apply settings
        settings = self._load_camera_settings_for_track()
        if settings:
            self._apply_mvs_settings(settings)
        
        # Start acquisition
        if not self.mvs_camera.start_grabbing():
            self.mvs_camera.close_camera()
            raise RuntimeError("Failed to start grabbing")
        
        # Grab frame
        frame = self.mvs_camera.grab_frame(timeout_ms=1000)
        
        # Stop and close
        self.mvs_camera.stop_grabbing()
        self.mvs_camera.close_camera()
        
        if frame is None:
            raise RuntimeError("Failed to capture frame (timeout)")
        
        # Convert mono to BGR for display
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        
        return frame, doc_index
    
    def _start_mvs_live(self) -> bool:
        """Start continuous acquisition using MVS SDK"""
        serial = self._get_camera_serial_for_station()
        if not serial:
            print("[CAMERA] No serial number for current station")
            return False
        
        print(f"[CAMERA] Opening camera for LIVE: {serial}")
        
        # Open camera by serial
        if not self.mvs_camera.open_camera(serial):
            print(f"[CAMERA] Failed to open camera {serial}")
            return False
        
        # Load and apply settings
        settings = self._load_camera_settings_for_track()
        if settings:
            self._apply_mvs_settings(settings)
        
        # Start acquisition
        if not self.mvs_camera.start_grabbing():
            print("[CAMERA] Failed to start grabbing")
            self.mvs_camera.close_camera()
            return False
        
        print("[CAMERA] MVS LIVE started")
        return True
    
    def _apply_mvs_settings(self, settings: dict):
        """Apply camera settings to MVS camera"""
        try:
            # Apply exposure if present
            if 'exposure' in settings:
                self.mvs_camera.set_exposure(float(settings['exposure']))
            
            # Apply gain if present
            if 'gain' in settings:
                self.mvs_camera.set_gain(float(settings['gain']))
            
            # Apply trigger mode if present
            if 'trigger_mode' in settings:
                self.mvs_camera.set_trigger_mode(bool(settings['trigger_mode']))
                
            print(f"[CAMERA] Applied settings: {settings}")
        except Exception as e:
            print(f"[CAMERA] Failed to apply settings: {e}")
