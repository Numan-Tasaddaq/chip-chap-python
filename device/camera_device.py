import cv2


class CameraDevice:
    """
    Hardware abstraction for camera.
    Laptop camera is used as temporary hardware.
    """

    def __init__(self, index=0):
        self.index = index

    def grab_once(self):
        cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)

        if not cap.isOpened():
            cap.release()
            return None

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None

        return frame
