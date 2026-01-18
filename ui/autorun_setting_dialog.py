from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton
)
from PySide6.QtCore import Qt
from config.auto_run_setting import AutoRunSetting
from config.auto_run_setting_io import save_auto_run_setting, load_auto_run_setting


class AutoRunSettingDialog(QDialog):
    def __init__(self, parent=None, model: AutoRunSetting | None = None):
        super().__init__(parent)

        self.setWindowTitle("AutoRun Setting")
        self.setFixedSize(300, 150)

        self.model = model or load_auto_run_setting()

        self._build_ui()
        self._load_from_model()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(15)

        # ---- Delay Time Row ----
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(QLabel("AutoRun Delay Time :"))

        self.delay_edit = QLineEdit()
        self.delay_edit.setFixedWidth(60)
        self.delay_edit.setAlignment(Qt.AlignCenter)
        row.addWidget(self.delay_edit)
        row.addStretch()
        main.addLayout(row)

        # ---- Buttons ----
        btns = QHBoxLayout()
        btns.addStretch()
        ok = QPushButton("OK")
        cancel = QPushButton("Cancel")
        ok.setFixedWidth(80)
        cancel.setFixedWidth(80)
        ok.clicked.connect(self._on_ok)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        btns.addStretch()
        main.addLayout(btns)

    def _load_from_model(self):
        self.delay_edit.setText(str(self.model.delay_time))

    def _apply_to_model(self):
        try:
            self.model.delay_time = int(self.delay_edit.text())
        except ValueError:
            self.model.delay_time = 100
        save_auto_run_setting(self.model)

    def _on_ok(self):
        self._apply_to_model()
        self.accept()
