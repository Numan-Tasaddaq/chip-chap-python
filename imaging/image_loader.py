# imaging/image_loader.py
import cv2
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap


class ImageLoader:
    def __init__(self, main_window):
        self.main_window = main_window

    def load_from_disk(self):
        # Only allowed in OFFLINE
        if self.main_window.state.run_state.name != "OFFLINE":
            QMessageBox.warning(
                self.main_window,
                "Not Allowed",
                "Load Image is only allowed in OFFLINE mode."
            )
            return

        # Stop LIVE if running
        if self.main_window.grab_service.live_running:
            self.main_window.grab_service.stop_live()

        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Load Image From Disk",
            "",
            "Image Files (*.bmp *.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        img = cv2.imread(file_path)
        if img is None:
            QMessageBox.critical(
                self.main_window,
                "Error",
                "Failed to load image."
            )
            return

        self.main_window.current_image = img
        self._display_image(img)

    def _display_image(self, frame):
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
