# imaging/grab_service.py
import cv2
import json
from pathlib import Path
import numpy as np

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap

from device.camera_registry import CameraRegistry
from device.teli_camera import TeliCamera
from config.camera_parameters_io import load_camera_parameters


class GrabService:
    """
    Handles GRAB and LIVE camera operations using Teli SDK.

    - GRAB  : single frame capture
    - LIVE  : continuous capture using QTimer
    """

    def __init__(self, main_window):
        self.main_window = main_window
        self.teli_camera = None  # Teli SDK camera instance
        self.cap = None  # OpenCV fallback
        self.live_timer = QTimer()
        self.live_timer.timeout.connect(self._grab_live_frame)
        self.live_running = False
        self.using_teli_sdk = False  # Track which backend is active

        # Load camera registry (serial number mapping)
        self.registry_cameras = CameraRegistry.read_registry()

        # Initialize Teli SDK
        try:
            self.teli_camera = TeliCamera()
            print("[CAMERA] Teli SDK initialized")
        except Exception as e:
            print(f"[CAMERA] Teli SDK not available: {e}")
            self.teli_camera = None

        # Optional JSON configuration for cameras (OpenCV fallback)
        self.camera_settings = self._load_camera_settings()
        self.camera_map = self._build_camera_map()

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

        # Try Teli SDK first
        if self.teli_camera is not None:
            try:
                frame = self._grab_teli_frame()
                if frame is not None:
                    self.main_window.current_image = frame
                    self._display_frame(frame)
                    return
            except Exception as e:
                print(f"[CAMERA] GRAB: Teli SDK failed: {e}")

        # Fallback to OpenCV
        print("[CAMERA] GRAB: Using OpenCV fallback")
        source, backend = self._resolve_camera_source()
        cap = self._open_capture(source, backend)

        if not cap.isOpened():
            print("[CAMERA] GRAB: Failed to open camera. Falling back to laptop camera (index 0).")
            cap.release()
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                print("[CAMERA] GRAB: Laptop camera also failed.")
                cap.release()
                return
            else:
                print("[CAMERA] GRAB: Laptop camera opened successfully.")

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return

        self.main_window.current_image = frame
        self._display_frame(frame)

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

        # Try Teli SDK first
        if self.teli_camera is not None:
            try:
                if self._start_teli_live():
                    self.using_teli_sdk = True
                    self.live_running = True
                    self.live_timer.start(30)  # ~30 FPS
                    return
            except Exception as e:
                print(f"[CAMERA] LIVE: Teli SDK failed: {e}")
                self.using_teli_sdk = False

        # Fallback to OpenCV
        print("[CAMERA] LIVE: Using OpenCV fallback")
        self.using_teli_sdk = False
        source, backend = self._resolve_camera_source()
        self.cap = self._open_capture(source, backend)

        if not self.cap.isOpened():
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

        self.live_running = True
        self.live_timer.start(30)  # ~30 FPS

    def stop_live(self):
        if not self.live_running:
            return

        self.live_timer.stop()
        self.live_running = False

        # Stop Teli SDK acquisition
        if self.using_teli_sdk and self.teli_camera is not None:
            try:
                self.teli_camera.stop_grab()
                self.teli_camera.close()
            except Exception as e:
                print(f"[CAMERA] Stop Teli SDK error: {e}")
            self.using_teli_sdk = False

        # Stop OpenCV
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def _grab_live_frame(self):
        # Teli SDK path
        if self.using_teli_sdk and self.teli_camera is not None:
            try:
                frame = self.teli_camera.grab_image(timeout_ms=100)
                if frame is not None:
                    # Convert mono to BGR for display
                    if len(frame.shape) == 2:
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    self.main_window.current_image = frame
                    self._display_frame(frame)
            except Exception as e:
                print(f"[CAMERA] Teli grab error: {e}")
            return

        # OpenCV path
        if not self.cap:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        self.main_window.current_image = frame
        self._display_frame(frame)

    # =================================================
    # Display helper
    # =================================================
    def _display_frame(self, frame):
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

    def _resolve_camera_source(self):
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
                        return f"video={dshow_name}", cv2.CAP_DSHOW

                    if isinstance(cv_index, int) and cv_index >= 0:
                        print(f"[CAMERA] Doc{doc_index}: Using CV index {cv_index}")
                        return cv_index, None

        # Check global preferred settings
        preferred = self.camera_settings.get("preferred", {})
        dshow_name = preferred.get("dshow_name", "").strip()
        idx = preferred.get("index")

        if dshow_name:
            print(f"[CAMERA] Using preferred DirectShow device: '{dshow_name}'")
            return f"video={dshow_name}", cv2.CAP_DSHOW

        if isinstance(idx, int) and idx >= 0:
            print(f"[CAMERA] Using preferred index from settings: {idx}")
            return idx, None

        # Check camera_map by (track, station)
        key = (track, station_str)
        if key in self.camera_map:
            selector = self.camera_map[key]
            if isinstance(selector, dict):
                name = selector.get("dshow_name")
                if name:
                    print(f"[CAMERA] Map DShow: '{name}' for {key}")
                    return f"video={name}", cv2.CAP_DSHOW
                idx2 = selector.get("index")
                if isinstance(idx2, int):
                    print(f"[CAMERA] Map index: {idx2} for {key}")
                    return idx2, None
            elif isinstance(selector, str):
                print(f"[CAMERA] Map string selector: {selector}")
                backend = cv2.CAP_DSHOW if selector.startswith("video=") else None
                return selector, backend
            elif isinstance(selector, int):
                print(f"[CAMERA] Map index: {selector} for {key}")
                return selector, None

        # fallback to laptop camera
        print("[CAMERA] No specific camera found. Using laptop camera (index 0).")
        return 0, cv2.CAP_DSHOW

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
    # Teli SDK helpers
    # =================================================
    def _get_camera_serial_for_track(self) -> str:
        """Get camera serial number for current track from registry"""
        track = self.main_window.state.track
        
        if track == 1:
            return CameraRegistry.get_track1_serial()
        elif track == 2:
            return CameraRegistry.get_track2_serial()
        else:
            print(f"[CAMERA] Unknown track: {track}")
            return None
    
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
    
    def _grab_teli_frame(self) -> np.ndarray:
        """Grab single frame using Teli SDK"""
        serial = self._get_camera_serial_for_track()
        if not serial:
            raise RuntimeError("No serial number for current track")
        
        print(f"[CAMERA] Opening camera: {serial}")
        
        # Open camera by serial
        self.teli_camera.open_by_serial(serial)
        
        # Load and apply settings
        settings = self._load_camera_settings_for_track()
        if settings:
            self.teli_camera.apply_settings(settings)
        
        # Start acquisition
        self.teli_camera.start_grab()
        
        # Grab frame
        frame = self.teli_camera.grab_image(timeout_ms=1000)
        
        # Stop and close
        self.teli_camera.stop_grab()
        self.teli_camera.close()
        
        if frame is None:
            raise RuntimeError("Failed to capture frame (timeout)")
        
        # Convert mono to BGR for display
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        
        return frame
    
    def _start_teli_live(self) -> bool:
        """Start continuous acquisition using Teli SDK"""
        serial = self._get_camera_serial_for_track()
        if not serial:
            print("[CAMERA] No serial number for current track")
            return False
        
        print(f"[CAMERA] Opening camera for LIVE: {serial}")
        
        # Open camera by serial
        self.teli_camera.open_by_serial(serial)
        
        # Load and apply settings
        settings = self._load_camera_settings_for_track()
        if settings:
            self.teli_camera.apply_settings(settings)
        
        # Start acquisition
        self.teli_camera.start_grab()
        
        print("[CAMERA] Teli LIVE started")
        return True
