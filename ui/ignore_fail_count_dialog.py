from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QLabel,
    QLineEdit, QHBoxLayout, QPushButton
)
from config.ignore_fail_count import IgnoreFailCount
from config.ignore_fail_count_io import save_ignore_fail_count, load_ignore_fail_count


class IgnoreFailCountDialog(QDialog):
    def __init__(self, parent=None, model: IgnoreFailCount | None = None):
        super().__init__(parent)
        self.setWindowTitle("Ignore Fail Count")
        self.resize(350, 200)

        # Model
        self.model = model or load_ignore_fail_count()

        # Store references to widgets
        self._checkboxes: dict[str, QCheckBox] = {}
        self._lineedits: dict[str, QLineEdit] = {}

        self._build_ui()
        self._load_from_model()

    # ------------------------------
    # Build UI
    # ------------------------------
    def _build_ui(self):
        main = QVBoxLayout(self)

        # Package Location checkbox
        cb = QCheckBox("Package Location")
        self._checkboxes["package_location"] = cb
        main.addWidget(cb)

        # Empty Filter Contrast row
        row = QHBoxLayout()
        row.addWidget(QLabel("Empty Filter Contrast"))
        edt = QLineEdit()
        edt.setFixedWidth(60)
        self._lineedits["empty_filter_contrast"] = edt
        row.addWidget(edt)
        main.addLayout(row)

        # Body Color checkbox
        cb = QCheckBox("Body Color")
        self._checkboxes["body_color"] = cb
        main.addWidget(cb)

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
        for key, cb in self._checkboxes.items():
            cb.setChecked(getattr(self.model, key, False))

        for key, edt in self._lineedits.items():
            edt.setText(str(getattr(self.model, key, 0)))

    # ------------------------------
    # Apply UI values to model
    # ------------------------------
    def _apply_to_model(self):
        for key, cb in self._checkboxes.items():
            setattr(self.model, key, cb.isChecked())

        for key, edt in self._lineedits.items():
            try:
                setattr(self.model, key, int(edt.text()))
            except ValueError:
                setattr(self.model, key, 0)

        save_ignore_fail_count(self.model)

    # ------------------------------
    # OK button handler
    # ------------------------------
    def _on_ok(self):
        self._apply_to_model()
        self.accept()
