from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QTextEdit
)

from license.manager import load_license, verify_license, LicenseData, save_license
import json
from pathlib import Path


class LicenseDialog(QDialog):
    """
    Dialog to ask user to load a license file.
    Works without machine locking — only license_key + signature.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("License Required")
        self.setModal(True)
        self.setMinimumWidth(520)

        layout = QVBoxLayout()

        info = QLabel(
            "This software requires a license.\n"
            "Load your license file to continue."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Optional: show license key from existing license
        self.license_key_box = QTextEdit()
        self.license_key_box.setReadOnly(True)
        existing_license = load_license()
        if existing_license:
            self.license_key_box.setText(existing_license.license_key)
        self.license_key_box.setFixedHeight(60)
        layout.addWidget(QLabel("Current License Key (if any):"))
        layout.addWidget(self.license_key_box)

        # Buttons
        btn_row = QHBoxLayout()
        self.btn_load = QPushButton("Load License File…")
        self.btn_load.clicked.connect(self._load_license_file)
        self.btn_exit = QPushButton("Exit")
        self.btn_exit.clicked.connect(self.reject)

        btn_row.addWidget(self.btn_load)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_exit)

        layout.addLayout(btn_row)
        self.setLayout(layout)

    def _load_license_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select license file",
            "",
            "License (*.json);;All Files (*.*)"
        )
        if not path:
            return

        try:
            # Read and validate the selected file
            raw = json.loads(Path(path).read_text(encoding="utf-8"))

            # Validate schema
            if "license_key" not in raw or "signature" not in raw:
                raise ValueError("Invalid license file format (missing fields).")

            # Create LicenseData instance
            ld = LicenseData(
                license_key=raw["license_key"],
                signature=raw["signature"]
            )

            # Verify license
            if not verify_license(ld):
                QMessageBox.critical(self, "License Error", "License is not valid.")
                return

            # Save license into app folder
            save_license(ld)
            self.license_key_box.setText(ld.license_key)
            QMessageBox.information(self, "License OK", "License accepted. The software will open now.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "License Error", f"Failed to load license:\n{e}")
