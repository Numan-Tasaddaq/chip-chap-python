"""
Mark Symbol Set Setting Dialog
Matches old C++ MarkSymbolSetDlg functionality
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QSpinBox, QCheckBox, QPushButton,
    QGroupBox, QMessageBox
)
from config.mark_inspection_io import load_mark_inspection_config, save_mark_inspection_config


class MarkSymbolSetDialog(QDialog):
    """
    Symbol/Mark Set Setting Dialog
    
    Allows configuration of:
    - Enable Mark Inspection checkbox
    - Total Mark Set (1-3)
    - Total Symbol Set (1-5)
    - Inspect Color checkbox
    
    Matches old C++ CMarkSymbolSetDlg
    """
    
    def __init__(self, parent=None, enable_mark_inspect_control=True):
        super().__init__(parent)
        
        self.setWindowTitle("Symbol/Mark Set Setting")
        self.setFixedSize(280, 160)
        
        # Match legacy dialog window behavior
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )
        
        # Store whether the Enable Mark Inspection control should be enabled
        # (corresponds to m_bEnableMarkInspect2 in old C++)
        self._enable_control = enable_mark_inspect_control
        
        # Build UI
        self._build_ui()
        
        # Load current configuration
        self._load_config()
        
        # Apply initial enable/disable state
        self._on_enable_changed()
    
    def _build_ui(self):
        """Build the dialog UI matching old application layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Enable Mark Inspection checkbox
        self.enable_checkbox = QCheckBox("Enable Mark Inspection")
        main_layout.addWidget(self.enable_checkbox)
        
        # Connect enable checkbox to handler
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        
        # Grid for Mark Set and Symbol Set inputs
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        grid_layout.setContentsMargins(0, 5, 0, 5)
        
        # Total Mark Set (Range: 1-3 as per old C++ DDV_MinMaxInt)
        mark_set_label = QLabel("Total Mark Set")
        self.mark_set_spin = QSpinBox()
        self.mark_set_spin.setRange(1, 3)
        self.mark_set_spin.setValue(1)
        self.mark_set_spin.setFixedWidth(120)
        grid_layout.addWidget(mark_set_label, 0, 0)
        grid_layout.addWidget(self.mark_set_spin, 0, 1)
        
        # Total Symbol Set (Range: 1-5 as per old C++ DDV_MinMaxInt)
        symbol_set_label = QLabel("Total Symbol Set")
        self.symbol_set_spin = QSpinBox()
        self.symbol_set_spin.setRange(1, 5)
        self.symbol_set_spin.setValue(1)
        self.symbol_set_spin.setFixedWidth(120)
        grid_layout.addWidget(symbol_set_label, 1, 0)
        grid_layout.addWidget(self.symbol_set_spin, 1, 1)
        
        main_layout.addLayout(grid_layout)
        
        # Inspect Color checkbox
        self.color_checkbox = QCheckBox("Inspect Color")
        main_layout.addWidget(self.color_checkbox)
        
        # Add stretch to push buttons to bottom
        main_layout.addStretch()
        
        # OK and Cancel buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.setFixedWidth(80)
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedWidth(80)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
    
    def _load_config(self):
        """Load configuration from mark_inspection.json"""
        try:
            config = load_mark_inspection_config()
            
            # Load Enable Mark Inspection
            self.enable_checkbox.setChecked(
                config.symbol_set.enable_mark_inspect
            )
            
            # Load Total Mark Set (number of mark sets configured)
            # In the old system, this was 1-3
            self.mark_set_spin.setValue(config.symbol_set.total_mark_set)
            
            # Load Total Symbol Set (number of symbol sets)
            # In the old system, this was 1-5
            self.symbol_set_spin.setValue(config.symbol_set.total_symbol_set)
            
            # Load Inspect Color
            self.color_checkbox.setChecked(
                config.symbol_set.inspect_color
            )
            
            # Set enable state of the Enable checkbox based on control parameter
            # (corresponds to m_bEnableMarkInspect2 in old C++)
            if not self._enable_control:
                self.enable_checkbox.setEnabled(False)
            
        except Exception as e:
            print(f"[WARN] Failed to load mark symbol set config: {e}")
            # Set defaults
            self.enable_checkbox.setChecked(False)
            self.mark_set_spin.setValue(1)
            self.symbol_set_spin.setValue(1)
            self.color_checkbox.setChecked(False)
    
    def _save_config(self):
        """Save configuration to mark_inspection.json"""
        try:
            # Load current config
            config = load_mark_inspection_config()
            
            # Update Enable Mark Inspection
            config.symbol_set.enable_mark_inspect = self.enable_checkbox.isChecked()
            
            # Update Total Mark Set and Total Symbol Set
            config.symbol_set.total_mark_set = self.mark_set_spin.value()
            config.symbol_set.total_symbol_set = self.symbol_set_spin.value()
            
            # Update Inspect Color
            config.symbol_set.inspect_color = self.color_checkbox.isChecked()
            
            # Save to file
            save_mark_inspection_config(config)
            
            print(f"[INFO] Mark symbol set configuration saved:")
            print(f"  - Enable Mark Inspection: {config.symbol_set.enable_mark_inspect}")
            print(f"  - Total Mark Set: {config.symbol_set.total_mark_set}")
            print(f"  - Total Symbol Set: {config.symbol_set.total_symbol_set}")
            print(f"  - Inspect Color: {config.symbol_set.inspect_color}")
            
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save mark symbol set configuration:\n{e}"
            )
            return False
    
    def _on_enable_changed(self):
        """
        Handle Enable Mark Inspection checkbox state change
        Matches old C++ OnEnableMarkInsp() handler
        
        When enabled: Enable Total Mark Set and Total Symbol Set spinboxes
        When disabled: Disable Total Mark Set and Total Symbol Set spinboxes
        """
        enabled = self.enable_checkbox.isChecked()
        
        # Enable/disable the spinboxes based on checkbox state
        self.mark_set_spin.setEnabled(enabled)
        self.symbol_set_spin.setEnabled(enabled)
        
        # Optionally enable/disable Inspect Color as well
        # (Old C++ didn't do this, but it makes sense logically)
        # self.color_checkbox.setEnabled(enabled)
    
    def accept(self):
        """Handle OK button click"""
        # Validate inputs
        if self.enable_checkbox.isChecked():
            mark_set = self.mark_set_spin.value()
            symbol_set = self.symbol_set_spin.value()
            
            if mark_set < 1 or mark_set > 3:
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Total Mark Set must be between 1 and 3."
                )
                return
            
            if symbol_set < 1 or symbol_set > 5:
                QMessageBox.warning(
                    self,
                    "Invalid Input",
                    "Total Symbol Set must be between 1 and 5."
                )
                return
        
        # Save configuration
        if self._save_config():
            super().accept()
    
    def get_values(self):
        """
        Get current dialog values
        
        Returns:
            dict: {
                'enable_mark_inspect': bool,
                'mark_set': int,
                'symbol_set': int,
                'inspect_color': bool
            }
        """
        return {
            'enable_mark_inspect': self.enable_checkbox.isChecked(),
            'mark_set': self.mark_set_spin.value(),
            'symbol_set': self.symbol_set_spin.value(),
            'inspect_color': self.color_checkbox.isChecked()
        }
    
    def set_values(self, enable_mark_inspect, mark_set, symbol_set, inspect_color):
        """
        Set dialog values programmatically
        
        Args:
            enable_mark_inspect: bool
            mark_set: int (1-3)
            symbol_set: int (1-5)
            inspect_color: bool
        """
        self.enable_checkbox.setChecked(enable_mark_inspect)
        self.mark_set_spin.setValue(max(1, min(3, mark_set)))
        self.symbol_set_spin.setValue(max(1, min(5, symbol_set)))
        self.color_checkbox.setChecked(inspect_color)
        
        # Trigger enable/disable logic
        self._on_enable_changed()


if __name__ == "__main__":
    """Test the dialog"""
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dialog = MarkSymbolSetDialog()
    if dialog.exec() == QDialog.Accepted:
        values = dialog.get_values()
        print("\nDialog accepted with values:")
        print(f"  Enable Mark Inspection: {values['enable_mark_inspect']}")
        print(f"  Total Mark Set: {values['mark_set']}")
        print(f"  Total Symbol Set: {values['symbol_set']}")
        print(f"  Inspect Color: {values['inspect_color']}")
    else:
        print("\nDialog cancelled")
    
    sys.exit(0)
