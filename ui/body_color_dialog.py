from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QFrame
)


class BodyColorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("字符颜色目录 Track1")
        self.resize(520, 360)

        # Match legacy dialog window behavior
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )

        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(12)

        # ================= Top Row =================
        top = QHBoxLayout()
        top.addWidget(QLabel("Total Color:"))
        self.total_color = QLineEdit("0")
        self.total_color.setFixedWidth(60)
        self.total_color.setReadOnly(True)
        top.addWidget(self.total_color)
        top.addStretch()
        main.addLayout(top)

        # ================= Button Row =================
        btn_row = QHBoxLayout()

        buttons = [
            "Select", "Red", "Green", "Blue",
            "Range", "Bin", "Color", "Sample"
        ]

        for txt in buttons:
            btn = QPushButton(txt)
            btn.setFixedHeight(26)
            btn_row.addWidget(btn)

        btn_row.addStretch()
        main.addLayout(btn_row)

        # ================= Main Empty Area =================
        area = QFrame()
        area.setFrameShape(QFrame.Panel)
        area.setFrameShadow(QFrame.Sunken)
        area.setMinimumHeight(180)
        main.addWidget(area)

        # ================= Bottom Row =================
        bottom = QHBoxLayout()

        btn_delete = QPushButton("Delete")
        btn_delete.setEnabled(False)
        bottom.addWidget(btn_delete)

        bottom.addStretch()

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        bottom.addWidget(btn_close)

        main.addLayout(bottom)
