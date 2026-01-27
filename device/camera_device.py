"""
Camera device abstraction with support for multiple stations (Doc1-Doc7).

Camera types:
  0 = Mono (BU030 → USB3CT)
  1 = Color (BU040 → USB4CT)

Each station (Top, Bottom, Feed, Pick-up 1/2, Bottom Sealing, Top Sealing)
has a dedicated camera with fixed Doc index and optional DirectShow mapping.
"""

import cv2
from typing import Optional, Tuple


class CameraDevice:
    """
    Hardware abstraction for camera.
    Supports USB3 cameras mapped to Doc1-Doc7 stations.
    """

    # Camera type constants
    TYPE_MONO = 0
    TYPE_COLOR = 1

    # Camera model constants
    MODEL_USB3CT = "USB3CT"  # BU030: Mono camera
    MODEL_USB4CT = "USB4CT"  # BU040: Color camera

    def __init__(
        self,
        doc_index: int = 1,
        station: str = "TOP",
        camera_type: int = TYPE_MONO,
        model: str = "USB3CT",
        cv_index: int = 0,
        dshow_name: Optional[str] = None
    ):
        """
        Initialize camera device.

        Args:
            doc_index: Doc index (1-7) for station mapping
            station: Station name (TOP, BOTTOM, FEED, etc.)
            camera_type: 0 = Mono, 1 = Color
            model: Camera model (USB3CT, USB4CT)
            cv_index: OpenCV index (fallback)
            dshow_name: DirectShow device name (Windows)
        """
        self.doc_index = doc_index
        self.station = station
        self.camera_type = camera_type
        self.model = model
        self.cv_index = cv_index
        self.dshow_name = dshow_name

    def grab_once(self, backend: Optional[int] = None) -> Optional:
        """
        Capture a single frame from the camera.

        Args:
            backend: OpenCV backend (e.g., cv2.CAP_DSHOW)

        Returns:
            numpy.ndarray: Frame in BGR format, or None if failed
        """
        # Prefer DirectShow if available
        source = self.cv_index
        if self.dshow_name:
            source = f"video={self.dshow_name}"
            backend = cv2.CAP_DSHOW

        cap = cv2.VideoCapture(source, backend) if backend else cv2.VideoCapture(source)

        if not cap.isOpened():
            cap.release()
            return None

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None

        return frame

    def get_info(self) -> dict:
        """
        Get camera information.

        Returns:
            dict: Camera metadata
        """
        return {
            "doc_index": self.doc_index,
            "station": self.station,
            "type": self.camera_type,
            "type_name": "Color" if self.camera_type == self.TYPE_COLOR else "Mono",
            "model": self.model,
            "cv_index": self.cv_index,
            "dshow_name": self.dshow_name,
        }
