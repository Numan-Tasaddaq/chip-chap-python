"""
Enable/Disable Inspection Dialog

Simple dialog explaining the automatic inspection behavior.
This is an informational dialog only - the actual enable/disable
is controlled by a checkbox in the Configuration menu.

Matches old C++ behavior where:
- Menu item acts as a toggle checkbox
- When cameras connect (ONLINE), inspection auto-activates
- User can manually disable if needed
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class EnableDisableInspectionDialog(QDialog):
    """Informational dialog for Enable/Disable Inspection"""
    
    def __init__(self, parent=None, is_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Enable / Disable Inspection")
        self.setFixedSize(500, 200)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Status label
        status_layout = QHBoxLayout()
        status_label = QLabel("Inspection Status:")
        status_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        status_layout.addWidget(status_label)
        
        self.status_value = QLabel()
        self.status_value.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._update_status_display(is_enabled)
        status_layout.addWidget(self.status_value)
        status_layout.addStretch()
        
        main_layout.addLayout(status_layout)
        
        # Information text
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setFont(QFont("Segoe UI", 9))
        info_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        message = (
            "Cameras in connection (Online) or disconnect will be automatically "
            "activated. If want to do the manual inspection, disable the inspection.\n\n"
            "• When ONLINE: Inspection runs automatically\n"
            "• When OFFLINE: Manual control available\n"
            "• Toggle via Configuration → Enable/Disable Inspection checkbox"
        )
        info_text.setText(message)
        
        main_layout.addWidget(info_text)
        
        # OK button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        btn_ok = QPushButton("OK")
        btn_ok.setFixedWidth(100)
        btn_ok.clicked.connect(self.accept)
        btn_ok.setDefault(True)
        button_layout.addWidget(btn_ok)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def _update_status_display(self, is_enabled):
        """Update the status display based on enable state"""
        if is_enabled:
            self.status_value.setText("✓ ENABLED")
            self.status_value.setStyleSheet("color: #2e7d32; font-weight: bold;")
        else:
            self.status_value.setText("✗ DISABLED")
            self.status_value.setStyleSheet("color: #c62828; font-weight: bold;")
