from PySide6.QtWidgets import (
    QDialog, QGridLayout, QCheckBox, QLineEdit,
    QLabel, QPushButton, QHBoxLayout, QVBoxLayout
)
from config.alert_messages import AlertMessages
from config.alert_messages_io import save_alert_messages, load_alert_messages


class AlertMessagesDialog(QDialog):
    def __init__(self, parent=None, alerts: AlertMessages | None = None):
        super().__init__(parent)
        self.setWindowTitle("Alert Message")
        self.resize(600, 450)

        # Model
        self.alerts = alerts or load_alert_messages()

        # Keep references to widgets
        self._checkboxes: dict[str, QCheckBox] = {}
        self._lineedits: dict[str, QLineEdit] = {}

        self._build_ui()
        self._load_from_model()

    # ------------------------------
    # Build UI
    # ------------------------------
    def _build_ui(self):
        main = QVBoxLayout(self)
        grid = QGridLayout()

        row = 0
        col = 0
        for i, name in enumerate(self.alerts.alerts.keys()):
            chk = QCheckBox(name)
            edt = QLineEdit()
            edt.setFixedWidth(50)

            self._checkboxes[name] = chk
            self._lineedits[name] = edt

            grid.addWidget(chk, row, col)
            grid.addWidget(edt, row, col + 1)
            grid.addWidget(QLabel("%"), row, col + 2)

            row += 1
            if row > 12:
                row = 0
                col += 3

        main.addLayout(grid)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        ok = QPushButton("OK")
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
        for name, data in self.alerts.alerts.items():
            self._checkboxes[name].setChecked(data.get("enabled", False))
            self._lineedits[name].setText(str(data.get("threshold", 20)))

    # ------------------------------
    # Apply UI values to model
    # ------------------------------
    def _apply_to_model(self):
        for name in self.alerts.alerts.keys():
            self.alerts.alerts[name]["enabled"] = self._checkboxes[name].isChecked()
            try:
                self.alerts.alerts[name]["threshold"] = int(self._lineedits[name].text())
            except ValueError:
                self.alerts.alerts[name]["threshold"] = 20  # fallback default
        save_alert_messages(self.alerts)

    # ------------------------------
    # OK button handler
    # ------------------------------
    def _on_ok(self):
        self._apply_to_model()
        self.accept()
