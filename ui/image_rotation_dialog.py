# ui/image_rotation_dialog.py
from PySide6.QtWidgets import QDialog, QPushButton, QLabel, QGridLayout
from PySide6.QtCore import Qt

class ImageRotationDialog(QDialog):
    def __init__(self, parent, initial_angle=0.0):
        super().__init__(parent)

        self.setWindowTitle("Image Rotation")
        self.angle = initial_angle

        self.label = QLabel(f"Angle: {self.angle:.2f}°")
        self.label.setAlignment(Qt.AlignCenter)

        btn_p1 = QPushButton("+1")
        btn_m1 = QPushButton("-1")
        btn_p01 = QPushButton("+0.1")
        btn_m01 = QPushButton("-0.1")
        btn_done = QPushButton("Done")

        btn_p1.clicked.connect(lambda: self._change_angle(1.0))
        btn_m1.clicked.connect(lambda: self._change_angle(-1.0))
        btn_p01.clicked.connect(lambda: self._change_angle(0.1))
        btn_m01.clicked.connect(lambda: self._change_angle(-0.1))
        btn_done.clicked.connect(self.accept)

        layout = QGridLayout(self)
        layout.addWidget(btn_p1, 0, 0)
        layout.addWidget(btn_m1, 0, 1)
        layout.addWidget(btn_p01, 1, 0)
        layout.addWidget(btn_m01, 1, 1)
        layout.addWidget(self.label, 2, 0, 1, 2)
        layout.addWidget(btn_done, 3, 0, 1, 2)

    def _change_angle(self, delta):
        self.angle += delta
        self.label.setText(f"Angle: {self.angle:.2f}°")
        self.parent()._apply_rotation_preview(self.angle)
