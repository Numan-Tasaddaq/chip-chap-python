from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QCheckBox,
    QHBoxLayout, QPushButton
)
from config.debug_flags import DebugFlags
from config.debug_flags_io import save_debug_flags, load_debug_flags


class InspectionDebugDialog(QDialog):
    def __init__(self, parent=None, flags: DebugFlags | None = None):
        super().__init__(parent)
        self.setWindowTitle("Debug Flag Setting")
        self.resize(420, 300)

        # Model
        self.flags = flags or load_debug_flags()

        # Store checkboxes in a dict for easy access
        self._checkboxes: dict[str, QCheckBox] = {}

        self._build_ui()
        self._load_from_model()

    # ------------------------------
    # Build UI
    # ------------------------------
    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background: #f7f7f7;
                font-size: 13px;
            }

            QLabel {
                color: #2b2b2b;
            }

            QGroupBox {
                border: 1px solid #cfcfcf;
                border-radius: 6px;
                margin-top: 14px;
                padding-top: 10px;
                font-weight: 600;
                color: #333;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 6px;
                background: #f7f7f7;
            }

            QCheckBox {
                spacing: 8px;
                padding: 2px;
            }

            QPushButton {
                height: 28px;
                min-width: 90px;
                border-radius: 4px;
                background: #e6e6e6;
                border: 1px solid #bdbdbd;
                font-weight: 600;
            }

            QPushButton#okBtn {
                background-color: #0078d7;
                color: white;
                border: none;
            }

            QPushButton#okBtn:hover {
                background-color: #006ac1;
            }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(14)

        # ================= Station Modules =================
        grp_station = QGroupBox("STATION MODULES")
        v1 = QVBoxLayout(grp_station)
        v1.setSpacing(8)

        for key, label in [
            ("package_location", "Package Location"),
            ("top_station", "Top Station"),
            ("bottom_station", "Bottom Station"),
        ]:
            cb = QCheckBox(label)
            self._checkboxes[key] = cb
            v1.addWidget(cb)

        main.addWidget(grp_station)

        # ================= Debugging Options =================
        grp_debug = QGroupBox("DEBUG OPTIONS")
        v2 = QVBoxLayout(grp_debug)
        v2.setSpacing(10)

        row1 = QHBoxLayout()
        row1.setSpacing(20)
        for key, label in [
            ("debug_draw", "Debug Draw"),
            ("debug_step_mode", "Step Mode"),
        ]:
            cb = QCheckBox(label)
            self._checkboxes[key] = cb
            row1.addWidget(cb)
        row1.addStretch()
        v2.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(20)
        for key, label in [
            ("debug_print", "Debug Print"),
            ("debug_edge", "Debug Edge"),
        ]:
            cb = QCheckBox(label)
            self._checkboxes[key] = cb
            row2.addWidget(cb)
        row2.addStretch()
        v2.addLayout(row2)

        cb = QCheckBox("Save Failed Images")
        self._checkboxes["save_failed_images"] = cb
        v2.addWidget(cb)

        main.addWidget(grp_debug)

        # ================= Buttons =================
        btns = QHBoxLayout()
        btns.addStretch()

        ok = QPushButton("OK")
        ok.setObjectName("okBtn")

        cancel = QPushButton("Cancel")

        ok.clicked.connect(self._on_ok)
        cancel.clicked.connect(self.reject)

        btns.addWidget(ok)
        btns.addWidget(cancel)
        main.addLayout(btns)

    # ------------------------------
    # Load model values into UI
    # ------------------------------
    def _load_from_model(self):
        for key, cb in self._checkboxes.items():
            cb.setChecked(getattr(self.flags, key, False))

    # ------------------------------
    # Apply UI values to model
    # ------------------------------
    def _apply_to_model(self):
        for key, cb in self._checkboxes.items():
            setattr(self.flags, key, cb.isChecked())
        save_debug_flags(self.flags)

    # ------------------------------
    # OK button handler
    # ------------------------------
    def _on_ok(self):
        self._apply_to_model()
        self.accept()
