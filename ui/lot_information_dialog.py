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
        self.setFixedSize(420, 430)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        self.lot_info = lot_info or load_lot_info()
        self._save_checkboxes: dict[str, QCheckBox] = {}

        self._build_ui()
        self._load_from_model()

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

            QLineEdit, QComboBox {
                height: 28px;
                padding: 4px 6px;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                background: white;
            }

            QLineEdit[readOnly="true"] {
                background: #ececec;
                color: #555;
            }

            QGroupBox {
                border: 1px solid #cfcfcf;
                border-radius: 6px;
                margin-top: 16px;
                padding-top: 10px;
                font-weight: 600;
                color: #333;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                top: 0px;
                padding: 0 6px;
                background: #f7f7f7;
            }


            QCheckBox {
                spacing: 6px;
            }

            QPushButton {
                min-width: 90px;
                height: 30px;
                border-radius: 4px;
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

            QPushButton#cancelBtn {
                background-color: #e6e6e6;
                border: 1px solid #bdbdbd;
            }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(14)

        # ========= Lot Details =========
        grp_form = QGroupBox("LOT DETAILS")
        form = QGridLayout(grp_form)
        form.setHorizontalSpacing(14)
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
            ("Machine ID", self.machine_id),
            ("Operator ID", self.operator_id),
            ("Order No", self.order_no),
            ("Scan No", self.scan_no),
            ("Lot ID", self.lot_id),
            ("Lot Size", self.lot_size),
            ("Package Type", self.package_type),
        ]

        for row, (label, widget) in enumerate(fields):
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            form.addWidget(lbl, row, 0)
            form.addWidget(widget, row, 1)

        main.addWidget(grp_form)

        # ========= Save Images =========
        grp_save = QGroupBox("SAVE IMAGES")
        save_layout = QHBoxLayout(grp_save)
        save_layout.setContentsMargins(12, 12, 12, 12)
        save_layout.setSpacing(20)


        for key, text in [("pass", "Pass"), ("fail", "Fail"), ("all", "All")]:
            cb = QCheckBox(text)
            self._save_checkboxes[key] = cb
            save_layout.addWidget(cb)

        save_layout.addStretch()
        main.addWidget(grp_save)

        # ========= Buttons =========
        btns = QHBoxLayout()
        btns.addStretch()

        btn_ok = QPushButton("OK")
        btn_ok.setObjectName("okBtn")

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("cancelBtn")

        btn_ok.clicked.connect(self._on_ok)
        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        main.addLayout(btns)

    # ------------------------------
    def _load_from_model(self):
        self.machine_id.setText(self.lot_info.machine_id)
        self.operator_id.setText(self.lot_info.operator_id)
        self.order_no.setText(self.lot_info.order_no)
        self.scan_no.setText(self.lot_info.scan_no)
        self.lot_id.setText(self.lot_info.lot_id)
        self.lot_size.setText(self.lot_info.lot_size)
        self.package_type.setCurrentText(self.lot_info.package_type)

        for key, cb in self._save_checkboxes.items():
            cb.setChecked(self.lot_info.save_images.get(key, False))

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

        save_lot_info(self.lot_info)

    # ------------------------------
    def _on_ok(self):
        self._apply_to_model()
        self.accept()
