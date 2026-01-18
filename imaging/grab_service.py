# imaging/grab_service.py
import cv2

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

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
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

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
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
