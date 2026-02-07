from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton,
    QListWidget, QGroupBox, QMessageBox
)
from pathlib import Path
import json


class ParaMarkConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Para & Mark Config File")
        self.resize(780, 460)

        # Match legacy dialog behavior
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )

        # Data storage
        self.para_configs = {}  # {scan_no: config_name}
        self.mark_configs = {}  # {scan_no: config_name}
        
        # Load existing data
        self._load_configs()

        self._build_ui()
        self._load_data_to_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog {
                background: #f7f7f7;
                font-size: 13px;
            }

            QLabel {
                color: #2b2b2b;
            }

            QLineEdit {
                height: 28px;
                padding: 4px 6px;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                background: white;
            }

            QListWidget {
                border: 1px solid #bdbdbd;
                border-radius: 4px;
                background: white;
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

            QPushButton {
                height: 28px;
                min-width: 70px;
                border-radius: 4px;
                background: #e6e6e6;
                border: 1px solid #bdbdbd;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #dcdcdc;
            }
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(12)

        # ================= Panels =================
        panels = QHBoxLayout()
        panels.setSpacing(14)

        # ---------- PARA FILE ----------
        grp_para = QGroupBox("PARA FILE")
        para_layout = QGridLayout(grp_para)
        para_layout.setHorizontalSpacing(10)
        para_layout.setVerticalSpacing(8)

        para_layout.addWidget(QLabel("Scan No"), 0, 0)
        self.para_scan_no = QLineEdit()
        para_layout.addWidget(self.para_scan_no, 0, 1)

        self.btn_para_add = QPushButton("Add")
        self.btn_para_add.clicked.connect(lambda: self._add_config("para"))
        para_layout.addWidget(self.btn_para_add, 0, 2, 2, 1)

        para_layout.addWidget(QLabel("Config Name"), 1, 0)
        self.para_config_name = QLineEdit()
        para_layout.addWidget(self.para_config_name, 1, 1)

        self.para_list = QListWidget()
        para_layout.addWidget(self.para_list, 2, 0, 1, 2)

        self.btn_para_remove = QPushButton("Remove")
        self.btn_para_remove.clicked.connect(lambda: self._remove_config("para"))
        para_layout.addWidget(self.btn_para_remove, 2, 2, Qt.AlignTop)

        panels.addWidget(grp_para)

        # ---------- MARK FILE ----------
        grp_mark = QGroupBox("MARK FILE")
        mark_layout = QGridLayout(grp_mark)
        mark_layout.setHorizontalSpacing(10)
        mark_layout.setVerticalSpacing(8)

        mark_layout.addWidget(QLabel("Scan No"), 0, 0)
        self.mark_scan_no = QLineEdit()
        mark_layout.addWidget(self.mark_scan_no, 0, 1)

        self.btn_mark_add = QPushButton("Add")
        self.btn_mark_add.clicked.connect(lambda: self._add_config("mark"))
        mark_layout.addWidget(self.btn_mark_add, 0, 2, 2, 1)

        mark_layout.addWidget(QLabel("Mark Symbol"), 1, 0)
        self.mark_symbol = QLineEdit()
        mark_layout.addWidget(self.mark_symbol, 1, 1)

        self.mark_list = QListWidget()
        mark_layout.addWidget(self.mark_list, 2, 0, 1, 2)

        self.btn_mark_remove = QPushButton("Remove")
        self.btn_mark_remove.clicked.connect(lambda: self._remove_config("mark"))
        mark_layout.addWidget(self.btn_mark_remove, 2, 2, Qt.AlignTop)

        panels.addWidget(grp_mark)

        main.addLayout(panels)

        # ================= Bottom Button =================
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(90)
        btn_close.clicked.connect(self.accept)

        btn_row.addWidget(btn_close)
        main.addLayout(btn_row)

    def _add_config(self, config_type):
        """Add a configuration entry."""
        if config_type == "para":
            scan_no = self.para_scan_no.text().strip()
            config_name = self.para_config_name.text().strip()
            configs = self.para_configs
            list_widget = self.para_list
            scan_input = self.para_scan_no
            config_input = self.para_config_name
        else:  # mark
            scan_no = self.mark_scan_no.text().strip()
            config_name = self.mark_symbol.text().strip()
            configs = self.mark_configs
            list_widget = self.mark_list
            scan_input = self.mark_scan_no
            config_input = self.mark_symbol
        
        # Validate inputs
        if not scan_no:
            QMessageBox.warning(self, "Input Error", "Please enter Scan No")
            return
        
        if not config_name:
            QMessageBox.warning(self, "Input Error", "Please enter Config Name")
            return
        
        # Check for duplicate
        if scan_no in configs:
            QMessageBox.warning(self, "Duplicate Error", 
                              f"Scan No '{scan_no}' already exists")
            return
        
        # Add to data storage
        configs[scan_no] = config_name
        
        # Add to list widget
        item_text = f"{scan_no} = {config_name}"
        list_widget.addItem(item_text)
        
        # Clear inputs
        scan_input.clear()
        config_input.clear()
        scan_input.setFocus()
        
        # Save to file
        self._save_configs()
        
        QMessageBox.information(self, "Success", 
                              f"{config_type.upper()} configuration added")
    
    def _remove_config(self, config_type):
        """Remove selected configuration."""
        if config_type == "para":
            list_widget = self.para_list
            configs = self.para_configs
        else:
            list_widget = self.mark_list
            configs = self.mark_configs
        
        current_item = list_widget.currentItem()
        if not current_item:
            QMessageBox.information(self, "Info", "Please select an item to remove")
            return
        
        # Parse item text "scan_no = config_name"
        item_text = current_item.text()
        parts = item_text.split(" = ")
        if len(parts) != 2:
            return
        
        scan_no = parts[0].strip()
        
        # Confirm removal
        reply = QMessageBox.question(self, "Confirm", 
                                    f"Remove '{scan_no}'?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        
        # Remove from data
        if scan_no in configs:
            del configs[scan_no]
        
        # Remove from list widget
        list_widget.takeItem(list_widget.row(current_item))
        
        # Save to file
        self._save_configs()
        
        QMessageBox.information(self, "Success", f"'{scan_no}' removed")
    
    def _load_configs(self):
        """Load configurations from JSON file."""
        config_file = Path("para_mark_config.json")
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.para_configs = data.get("para_configs", {})
                    self.mark_configs = data.get("mark_configs", {})
                print("[PARAMARK] Loaded Para & Mark configurations")
            except Exception as e:
                print(f"[PARAMARK] Failed to load configurations: {e}")
    
    def _save_configs(self):
        """Save configurations to JSON file."""
        config_file = Path("para_mark_config.json")
        
        try:
            data = {
                "para_configs": self.para_configs,
                "mark_configs": self.mark_configs
            }
            with open(config_file, 'w') as f:
                json.dump(data, f, indent=4)
            print("[PARAMARK] Saved Para & Mark configurations")
        except Exception as e:
            print(f"[PARAMARK] Failed to save configurations: {e}")
    
    def _load_data_to_ui(self):
        """Load saved data into the UI lists."""
        for scan_no, config_name in self.para_configs.items():
            self.para_list.addItem(f"{scan_no} = {config_name}")
        
        for scan_no, config_name in self.mark_configs.items():
            self.mark_list.addItem(f"{scan_no} = {config_name}")
