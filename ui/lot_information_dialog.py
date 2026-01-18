from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox,
    QGroupBox, QCheckBox, QPushButton
)
from config.lot_information import LotInformation
from config.lot_information_io import save_lot_info, load_lot_info


class LotInformationDialog(QDialog):
    def __init__(self, parent=None, lot_info: LotInformation | None = None):
        super().__init__(parent)

        self.setWindowTitle("Lot Information")
        self.setFixedSize(380, 360)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        # Load existing model or create new
        self.lot_info = lot_info or load_lot_info()

        # Store checkbox references
        self._save_checkboxes: dict[str, QCheckBox] = {}

        self._build_ui()
        self._load_from_model()  # populate UI with saved values

    # ------------------------------
    # Build the UI
    # ------------------------------
    def _build_ui(self):
        main = QVBoxLayout(self)

        # ================= Form =================
        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.machine_id = QLineEdit()
        self.machine_id.setReadOnly(True)
        self.operator_id = QLineEdit()
        self.order_no = QLineEdit()
        self.order_no.setReadOnly(True)
        self.scan_no = QLineEdit()
        self.lot_id = QLineEdit()
        self.lot_size = QLineEdit()

        self.package_type = QComboBox()
        self.package_type.addItem("Default")

        fields = [
            ("Machine ID :", self.machine_id),
            ("Operator ID :", self.operator_id),
            ("Order No :", self.order_no),
            ("Scan No :", self.scan_no),
            ("Lot ID :", self.lot_id),
            ("Lot Size :", self.lot_size),
            ("Package Type :", self.package_type),
        ]

        for row, (label, widget) in enumerate(fields):
            form.addWidget(QLabel(label), row, 0)
            form.addWidget(widget, row, 1)

        main.addLayout(form)

        # ================= Save Images =================
        grp_save = QGroupBox("Save Images")
        grp_save.setObjectName("Save Images")  # needed for findChild
        h = QHBoxLayout(grp_save)

        for key in ["pass", "fail", "all"]:
            cb = QCheckBox(key.capitalize())
            self._save_checkboxes[key] = cb
            h.addWidget(cb)
        h.addStretch()

        main.addWidget(grp_save)

        # ================= Buttons =================
        btns = QHBoxLayout()
        btns.addStretch()

        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")

        btn_ok.clicked.connect(self._on_ok)
        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        main.addLayout(btns)

    # ------------------------------
    # Load values from model to UI
    # ------------------------------
    def _load_from_model(self):
        self.machine_id.setText(self.lot_info.machine_id)
        self.operator_id.setText(self.lot_info.operator_id)
        self.order_no.setText(self.lot_info.order_no)
        self.scan_no.setText(self.lot_info.scan_no)
        self.lot_id.setText(self.lot_info.lot_id)
        self.lot_size.setText(self.lot_info.lot_size)
        self.package_type.setCurrentText(self.lot_info.package_type)

        # Save images checkboxes
        for key, cb in self._save_checkboxes.items():
            cb.setChecked(self.lot_info.save_images.get(key, False))

    # ------------------------------
    # Apply UI values to model
    # ------------------------------
    def _apply_to_model(self):
        self.lot_info.machine_id = self.machine_id.text()
        self.lot_info.operator_id = self.operator_id.text()
        self.lot_info.order_no = self.order_no.text()
        self.lot_info.scan_no = self.scan_no.text()
        self.lot_info.lot_id = self.lot_id.text()
        self.lot_info.lot_size = self.lot_size.text()
        self.lot_info.package_type = self.package_type.currentText()

        for key, cb in self._save_checkboxes.items():
            self.lot_info.save_images[key] = cb.isChecked()

        # Save to JSON
        save_lot_info(self.lot_info)

    # ------------------------------
    # OK button handler
    # ------------------------------
    def _on_ok(self):
        self._apply_to_model()
        self.accept()
