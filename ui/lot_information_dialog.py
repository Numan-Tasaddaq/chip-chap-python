from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox,
    QGroupBox, QCheckBox, QPushButton
)
from config.lot_information import LotInformation
from config.lot_information_io import save_lot_info, load_lot_info


class LotInformationDialog(QDialog):
    def __init__(
        self,
        parent=None,
        lot_info: LotInformation | None = None,
        machine_id: str = "",
        operator_id: str = "",
        order_no: str = "",
        current_config_file: str = "",
        sem_enabled: bool = False,
        inspection_dir: str = "inspection"
    ):
        """
        Initialize Lot Information Dialog (matching old C++ behavior).
        
        Args:
            lot_info: LotInformation object to load/save from
            machine_id: Pre-populated from app state (read-only)
            operator_id: Pre-populated from app state (if not SEM)
            order_no: Pre-populated from app state (read-only)
            current_config_file: Current config file name for package type pre-selection
            sem_enabled: If True, operator_id field is read-only
            inspection_dir: Path to scan for package type directories
        """
        super().__init__(parent)

        self.setWindowTitle("Lot Information")
        self.setFixedSize(420, 430)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        # Store parameters for UI building
        self._machine_id_param = machine_id
        self._operator_id_param = operator_id
        self._order_no_param = order_no
        self._current_config_file = current_config_file
        self._sem_enabled = sem_enabled
        self._inspection_dir = inspection_dir

        # Load or create lot information
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
        # If SEM enabled or no operator_id passed, operator_id is editable
        # Otherwise it's pre-populated and read-only
        if self._sem_enabled and self._operator_id_param:
            self.operator_id.setReadOnly(True)

        self.order_no = QLineEdit()
        self.order_no.setReadOnly(True)

        self.scan_no = QLineEdit()
        self.lot_id = QLineEdit()
        self.lot_size = QLineEdit()

        self.package_type = QComboBox()
        self._fill_package_type_combo()

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
    def _fill_package_type_combo(self):
        """Fill package type combo box from inspection directory (matching C++ FillComboBoxList)."""
        self.package_type.clear()

        # Try to scan inspection directory for subdirectories
        insp_path = Path(self._inspection_dir)
        if insp_path.exists() and insp_path.is_dir():
            try:
                dirs = sorted([d.name for d in insp_path.iterdir() 
                              if d.is_dir() and d.name not in (".", "..")])
                if dirs:
                    for dir_name in dirs:
                        self.package_type.addItem(dir_name)
                else:
                    # If no directories found, use default
                    self.package_type.addItem("Default")
            except Exception:
                # If error reading directory, use default
                self.package_type.addItem("Default")
        else:
            # If inspection directory doesn't exist, use default
            self.package_type.addItem("Default")

    # ------------------------------

    def _load_from_model(self):
        """
        Load dialog values - prioritizes parameters passed from app state,
        then falls back to lot_info from JSON file (matching C++ behavior).
        """
        # Machine ID: From parameter (app state) - always read-only
        if self._machine_id_param:
            self.machine_id.setText(self._machine_id_param)
        else:
            self.machine_id.setText(self.lot_info.machine_id)

        # Operator ID: From parameter (app state) if provided
        if self._operator_id_param:
            self.operator_id.setText(self._operator_id_param)
        else:
            self.operator_id.setText(self.lot_info.operator_id)

        # Order No: From parameter (app state) - always read-only
        if self._order_no_param:
            self.order_no.setText(self._order_no_param)
        else:
            self.order_no.setText(self.lot_info.order_no)

        # Other fields: Load from JSON persistence
        self.scan_no.setText(self.lot_info.scan_no)
        self.lot_id.setText(self.lot_info.lot_id)
        self.lot_size.setText(self.lot_info.lot_size)

        # Package Type: Pre-select current config file if provided
        if self._current_config_file:
            idx = self.package_type.findText(self._current_config_file)
            if idx >= 0:
                self.package_type.setCurrentIndex(idx)
            else:
                self.package_type.setCurrentText(self.lot_info.package_type)
        else:
            self.package_type.setCurrentText(self.lot_info.package_type)

        # Save Images: Load from JSON
        for key, cb in self._save_checkboxes.items():
            cb.setChecked(self.lot_info.save_images.get(key, False))

    def _apply_to_model(self):
        """
        Save dialog values to lot_info.
        Note: Machine ID and Order No are read-only in the UI,
        so we only update the editable fields.
        """
        # Note: Machine ID and Order No are read-only and come from app state
        # Only update if they weren't provided from app state
        if not self._machine_id_param:
            self.lot_info.machine_id = self.machine_id.text()
        if not self._order_no_param:
            self.lot_info.order_no = self.order_no.text()

        # Operator ID: Update if not pre-populated or if user edited it
        self.lot_info.operator_id = self.operator_id.text()

        # User-editable fields: Always save
        self.lot_info.scan_no = self.scan_no.text()
        self.lot_info.lot_id = self.lot_id.text()
        self.lot_info.lot_size = self.lot_size.text()
        self.lot_info.package_type = self.package_type.currentText()

        # Save image preferences
        for key, cb in self._save_checkboxes.items():
            self.lot_info.save_images[key] = cb.isChecked()

        # Persist to JSON file
        save_lot_info(self.lot_info)

    # ------------------------------
    def _on_ok(self):
        self._apply_to_model()
        self.accept()
