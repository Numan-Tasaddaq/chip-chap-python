from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import Qt, QRect

from imaging.roi import Rect

HANDLE_SIZE = 8


class PocketTeachOverlay(QLabel):
    """
    Generic ROI overlay used for:
    - Pocket Teach
    - Rotation ROI
    - Package Teach

    Behavior is controlled by MainWindow.teach_phase
    """

    def __init__(self, image_label, main_window):
        super().__init__(image_label)
        self.main_window = main_window

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background: transparent;")

        # ROI state
        self.roi = Rect(200, 150, 200, 120)
        self.dragging = False
        self.resizing = False
        self.active_handle = None

        # Visual state
        self.confirmed = False

    # =================================================
    # DRAW
    # =================================================
    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)

        color = QColor("green") if self.confirmed else QColor("red")
        pen = QPen(color, 2)
        p.setPen(pen)

        r = QRect(self.roi.x, self.roi.y, self.roi.w, self.roi.h)
        p.drawRect(r)

        # Handles only visible when NOT confirmed
        if not self.confirmed:
            for hx, hy in self._handles():
                p.fillRect(hx, hy, HANDLE_SIZE, HANDLE_SIZE, color)

    def _handles(self):
        r = self.roi
        return [
            (r.x - 4, r.y - 4),               # TL
            (r.right() - 4, r.y - 4),         # TR
            (r.x - 4, r.bottom() - 4),        # BL
            (r.right() - 4, r.bottom() - 4),  # BR
        ]

    # =================================================
    # MOUSE
    # =================================================
    def mousePressEvent(self, e):
        if self.confirmed:
            return

        x, y = int(e.position().x()), int(e.position().y())

        for i, (hx, hy) in enumerate(self._handles()):
            if QRect(hx, hy, HANDLE_SIZE, HANDLE_SIZE).contains(x, y):
                self.resizing = True
                self.active_handle = i
                return

        r = QRect(self.roi.x, self.roi.y, self.roi.w, self.roi.h)
        if r.contains(x, y):
            self.dragging = True
            self.last_pos = e.position()

    def mouseMoveEvent(self, e):
        if self.confirmed:
            return

        x, y = int(e.position().x()), int(e.position().y())

        if self.dragging:
            dx = x - self.last_pos.x()
            dy = y - self.last_pos.y()
            self.roi.x += dx
            self.roi.y += dy
            self.last_pos = e.position()
            self.update()

        elif self.resizing:
            self._resize_roi(x, y)
            self.update()

    def mouseReleaseEvent(self, e):
        self.dragging = False
        self.resizing = False

    # =================================================
    # RESIZE
    # =================================================
    def _resize_roi(self, x, y):
        r = self.roi

        if self.active_handle == 0:      # TL
            r.w += r.x - x
            r.h += r.y - y
            r.x, r.y = x, y

        elif self.active_handle == 1:    # TR
            r.w = x - r.x
            r.h += r.y - y
            r.y = y

        elif self.active_handle == 2:    # BL
            r.w += r.x - x
            r.x = x
            r.h = y - r.y

        elif self.active_handle == 3:    # BR
            r.w = x - r.x
            r.h = y - r.y

    # =================================================
    # KEY / CONFIRM
    # =================================================
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.confirm()

    def confirm(self):
        """
        Called by:
        - Enter key
        - Toolbar NEXT button
        Delegates decision to MainWindow based on teach_phase
        """
        self.main_window._confirm_overlay(self.roi)

    # =================================================
    # STATE
    # =================================================
    def set_confirmed(self, confirmed: bool):
        self.confirmed = confirmed
        self.update()
