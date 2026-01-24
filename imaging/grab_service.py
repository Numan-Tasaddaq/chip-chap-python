# imaging/grab_service.py
import cv2
import json
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap



class GrabService:
    """
    Handles GRAB and LIVE camera operations.

    - GRAB  : single frame capture
    - LIVE  : continuous capture using QTimer
    """

    def __init__(self, main_window):
        self.main_window = main_window
        self.cap = None
        self.live_timer = QTimer()
        self.live_timer.timeout.connect(self._grab_live_frame)
        self.live_running = False
        # Map of (track, station) → camera selector
        # Selector can be:
        #  - int: OpenCV index (e.g., 0, 1, 2)
        #  - str: DirectShow name ("video=My USB3 Camera")
        #  - dict: {"dshow_name": "...", "index": 0} for more explicit config
        self.camera_map = {
            # Example: Track1 + TOP → external camera at index 1
            (1, "TOP"): 1
        }

        # Optional JSON configuration for cameras.
        # Place a file named "camera_settings.json" at the workspace root with content like:
        # {
        #   "preferred": {
        #       "dshow_name": "USB3.0 Camera Model X1234",  # or user-defined name
        #       "index": 1                                    # fallback index
        #   }
        # }
        self.camera_settings = self._load_camera_settings()


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

        source, backend = self._resolve_camera_source()
        cap = self._open_capture(source, backend)

        if not cap.isOpened():
            print("[CAMERA] GRAB: Failed to open camera. Falling back to laptop camera (index 0).")
            cap.release()
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                print("[CAMERA] GRAB: Laptop camera also failed.")
            return

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return

        self._display_frame(frame)
        self.main_window.current_image = frame

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

        source, backend = self._resolve_camera_source()
        self.cap = self._open_capture(source, backend)

        if not self.cap.isOpened():
            print("[CAMERA] LIVE: Failed to open preferred camera. Trying laptop camera (index 0).")
            self.cap.release()
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                print("[CAMERA] LIVE: Laptop camera also failed.")
            self.cap = None
            return

        self.live_running = True
        self.live_timer.start(30)  # ~30 FPS

    def stop_live(self):
        if not self.live_running:
            return

        self.live_timer.stop()
        self.live_running = False

        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def _grab_live_frame(self):
        if not self.cap:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        self._display_frame(frame)
        self.main_window.current_image = frame

    # =================================================
    # Display helper
    # =================================================
    def _display_frame(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w

        qimg = QImage(
            rgb.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        )

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
        Resolve preferred camera based on:
        1) camera_settings.json (DirectShow name or index)
        2) camera_map for current (track, station)
        3) fallback to laptop camera index 0

        Returns: (source, backend)
        - source: int index or str name
        - backend: cv2 backend flag (e.g., cv2.CAP_DSHOW) or None
        """
        track = self.main_window.state.track
        station = self.main_window.state.station.value

        # 1) JSON settings take priority
        preferred = self.camera_settings.get("preferred", {})
        dshow_name = preferred.get("dshow_name")
        idx = preferred.get("index")

        if dshow_name:
            print(f"[CAMERA] Preferred DirectShow device: '{dshow_name}'")
            return f"video={dshow_name}", cv2.CAP_DSHOW

        if isinstance(idx, int):
            print(f"[CAMERA] Preferred index from settings: {idx}")
            return idx, None

        # 2) camera_map based on track/station
        key = (track, station)
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
                # Accept direct show name as "video=..."
                print(f"[CAMERA] Map string selector: {selector}")
                backend = cv2.CAP_DSHOW if selector.startswith("video=") else None
                return selector, backend
            elif isinstance(selector, int):
                print(f"[CAMERA] Map index: {selector} for {key}")
                return selector, None

        # 3) fallback to laptop camera
        print("[CAMERA] No specific camera found. Using laptop camera (index 0).")
        return 0, cv2.CAP_DSHOW

    def _open_capture(self, source, backend=None):
        """
        Open cv2.VideoCapture with optional backend.
        - If source is a string, backend is likely cv2.CAP_DSHOW for DirectShow.
        - If backend is None, OpenCV chooses default.
        Also logs basic info for debugging.
        """
        try:
            if backend is not None:
                cap = cv2.VideoCapture(source, backend)
            else:
                cap = cv2.VideoCapture(source)
        except Exception as e:
            print(f"[CAMERA] OpenCapture error for source '{source}': {e}")
            return cv2.VideoCapture(0, cv2.CAP_DSHOW)

        # Print basic info for debugging
        if cap.isOpened():
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"[CAMERA] Opened source={source} backend={backend} size={int(width)}x{int(height)} fps={fps:.1f}")
        else:
            print(f"[CAMERA] Failed to open source={source} backend={backend}")

        return cap
