# imaging/grab_service.py
import cv2
import json
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap

from device.camera_registry import CameraRegistry


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

        # Load camera registry (Doc1-Doc7 serial number mapping)
        self.registry_cameras = CameraRegistry.read_registry()

        # Optional JSON configuration for cameras.
        # Place a file named "camera_settings.json" at the workspace root with content like:
        # {
        #   "cameras": [
        #     {"doc_index": 1, "station": "TOP", "dshow_name": "USB3.0 Camera SN123", "index": 1},
        #     {"doc_index": 2, "station": "BOTTOM", "dshow_name": "USB3.0 Camera SN456", "index": 2},
        #     ...
        #   ],
        #   "preferred": {
        #     "index": 0  # fallback to laptop camera
        #   }
        # }
        self.camera_settings = self._load_camera_settings()

        # Map of (track, station) → camera selector
        # Now based on registry Doc indices with fallback to USB indices
        self.camera_map = self._build_camera_map()




    def _build_camera_map(self):
        """
        Build camera map from registry and settings.
        Maps (track, station) to camera selector.

        Returns:
            dict: {(track, station): camera_selector}
            - camera_selector can be int (CV index), str (DirectShow name), or dict
        """
        camera_map = {}

        # Get camera settings from JSON
        camera_list = self.camera_settings.get("cameras", [])

        # Build map from JSON camera list
        for cam_config in camera_list:
            doc_index = cam_config.get("doc_index")
            station = cam_config.get("station")

            if not (doc_index and station):
                continue

            # For now, map to all tracks (later: could add track-specific mapping)
            track = self.main_window.state.track
            key = (track, station)

            # Prefer DirectShow name, fallback to index
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
        Resolve preferred camera based on:
        1) Windows Registry (Doc1-Doc7 serial number mapping)
        2) camera_settings.json (DirectShow name or index)
        3) camera_map for current (track, station)
        4) fallback to laptop camera index 0

        Returns: (source, backend)
        - source: int index or str name or dict
        - backend: cv2 backend flag (e.g., cv2.CAP_DSHOW) or None
        """
        track = self.main_window.state.track
        station_enum = self.main_window.state.station

        # Get station string name - use .name for enum name (TOP, BOTTOM, FEED, etc.)
        # Don't use .value which gives display strings like "Top", "Bottom"
        station_str = station_enum.name if hasattr(station_enum, 'name') else str(station_enum).upper()

        # Get Doc index for this station from registry
        doc_index = CameraRegistry.get_doc_index(station_str)

        if doc_index:
            print(f"[CAMERA] Station '{station_str}' mapped to Doc{doc_index}")

            # 1) Check JSON settings for this Doc index
            camera_list = self.camera_settings.get("cameras", [])
            for cam_config in camera_list:
                if cam_config.get("doc_index") == doc_index:
                    dshow_name = cam_config.get("dshow_name", "").strip()
                    cv_index = cam_config.get("index")

                    if dshow_name:  # Only use if non-empty
                        print(f"[CAMERA] Doc{doc_index}: Using DirectShow '{dshow_name}'")
                        return f"video={dshow_name}", cv2.CAP_DSHOW

                    if isinstance(cv_index, int) and cv_index >= 0:
                        print(f"[CAMERA] Doc{doc_index}: Using CV index {cv_index}")
                        return cv_index, None

            # 2) Fallback: use Doc index as CV index if registry has SN
            if doc_index in self.registry_cameras:
                serial = self.registry_cameras[doc_index]
                print(f"[CAMERA] Doc{doc_index}: Using registry SN '{serial}' as CV index {doc_index}")
                return doc_index, None

        # 3) Check global preferred settings
        preferred = self.camera_settings.get("preferred", {})
        dshow_name = preferred.get("dshow_name", "").strip()
        idx = preferred.get("index")

        if dshow_name:  # Only use if non-empty
            print(f"[CAMERA] Using preferred DirectShow device: '{dshow_name}'")
            return f"video={dshow_name}", cv2.CAP_DSHOW

        if isinstance(idx, int) and idx >= 0:
            print(f"[CAMERA] Using preferred index from settings: {idx}")
            return idx, None

        # 4) Check camera_map by (track, station)
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
                # Accept direct show name as "video=..."
                print(f"[CAMERA] Map string selector: {selector}")
                backend = cv2.CAP_DSHOW if selector.startswith("video=") else None
                return selector, backend
            elif isinstance(selector, int):
                print(f"[CAMERA] Map index: {selector} for {key}")
                return selector, None

        # 5) fallback to laptop camera
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
