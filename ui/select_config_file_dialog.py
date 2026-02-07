# ui/select_config_file_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt
from pathlib import Path
import shutil


class SelectConfigFileDialog(QDialog):
    """
    Dialog for selecting, loading, and deleting configuration files.
    Matches old C++ CSelectConfigFileDlg.
    """

    def __init__(self, current_config_name: str, inspection_dir: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Configuration File")
        self.setModal(True)
        self.resize(450, 200)

        self.current_config_name = current_config_name
        self.inspection_dir = Path(inspection_dir)
        self.selected_config = current_config_name
        self.loaded_file = current_config_name  # Remember originally loaded file
        self.loaded_file_deleted = False

        self._init_ui()
        self._load_config_files()

    def _init_ui(self):
        layout = QVBoxLayout()

        # Instruction label
        label = QLabel("Select the configuration file to load:")
        label.setStyleSheet("font-size: 10pt; margin-bottom: 10px;")
        layout.addWidget(label)

        # Combo box for file selection
        self.combo_file_select = QComboBox()
        self.combo_file_select.setStyleSheet("""
            QComboBox {
                padding: 6px;
                font-size: 10pt;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        self.combo_file_select.currentTextChanged.connect(self._on_selection_changed)
        layout.addWidget(self.combo_file_select)

        layout.addSpacing(20)

        # Buttons
        button_layout = QHBoxLayout()

        self.btn_load = QPushButton("Load This File")
        self.btn_load.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 20px;
                font-size: 10pt;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_load.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_load)

        self.btn_delete = QPushButton("Delete This File")
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px 20px;
                font-size: 10pt;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_delete.clicked.connect(self._delete_file)
        button_layout.addWidget(self.btn_delete)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px 20px;
                font-size: 10pt;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _load_config_files(self):
        """Load configuration directories from inspection_dir."""
        if not self.inspection_dir.exists():
            self.inspection_dir.mkdir(parents=True, exist_ok=True)

        # Find all subdirectories in inspection directory (each is a config)
        config_dirs = [d.name for d in self.inspection_dir.iterdir() if d.is_dir()]
        config_dirs.sort()

        self.combo_file_select.clear()
        self.combo_file_select.addItems(config_dirs)

        # Select current config if it exists
        if self.current_config_name in config_dirs:
            self.combo_file_select.setCurrentText(self.current_config_name)

        # Update button states
        self._on_selection_changed(self.combo_file_select.currentText())

    def _on_selection_changed(self, selected_file: str):
        """Update button states when selection changes."""
        # Disable Load and Delete if selected file is the currently loaded file
        is_loaded_file = (selected_file == self.loaded_file)
        self.btn_load.setEnabled(not is_loaded_file)
        self.btn_delete.setEnabled(not is_loaded_file)

    def _delete_file(self):
        """Delete the selected configuration file."""
        selected_file = self.combo_file_select.currentText()
        if not selected_file:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Configuration File",
            f"Delete the configuration file set '{selected_file}'?\n\n"
            "This will permanently delete the configuration directory and all its contents.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Delete the configuration directory
        config_dir = self.inspection_dir / selected_file
        if config_dir.exists():
            try:
                shutil.rmtree(config_dir)
                QMessageBox.information(
                    self,
                    "Delete Complete",
                    f"Configuration file '{selected_file}' has been deleted."
                )

                # Check if we deleted the loaded file
                if selected_file == self.loaded_file:
                    self.loaded_file_deleted = True

                # Reload the list
                self._load_config_files()

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Delete Failed",
                    f"Failed to delete configuration file:\n{str(e)}"
                )
        else:
            QMessageBox.warning(
                self,
                "File Not Found",
                f"Configuration file '{selected_file}' not found."
            )

    def reject(self):
        """Override reject to check if loaded file was deleted."""
        if self.loaded_file_deleted:
            QMessageBox.warning(
                self,
                "Configuration File Deleted",
                "The Configuration File that was previously loaded has been deleted.\n"
                "Please Load another Configuration File."
            )
            return
        super().reject()

    def accept(self):
        """Accept and save selected config name."""
        self.selected_config = self.combo_file_select.currentText()
        if not self.selected_config:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a configuration file."
            )
            return
        super().accept()
