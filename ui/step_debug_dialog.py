# ui/step_debug_dialog.py
"""
Step-by-step debugging dialog for inspection tests.
Displays measurement results and waits for user input to proceed to next step.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox
)


class StepDebugDialog(QDialog):
    """
    Modal dialog for step-by-step inspection debugging.
    Shows test results and waits for user to click NEXT.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Step Debug - Inspection Test")
        self.setGeometry(100, 100, 800, 500)
        self.next_clicked = False
        self.edit_params_clicked = False

        self._build_ui()

    def _build_ui(self):
        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("Step-by-Step Inspection Debug")
        title_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        title.setFont(title_font)
        layout.addWidget(title)

        # Info text
        info = QLabel(
            "Below is the measurement result for this step.\n"
            "Review the information and click NEXT to proceed or EDIT PARAMS to adjust."
        )
        info_font = QFont("Segoe UI", 10)
        info.setFont(info_font)
        info.setStyleSheet("color: #555; padding: 8px;")
        layout.addWidget(info)

        # Text area for debug info
        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)
        self.debug_text.setFont(QFont("Courier New", 10))
        self.debug_text.setStyleSheet("""
            QTextEdit {
                background: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                color: #333;
            }
        """)
        layout.addWidget(self.debug_text, 1)

        # Result label (PASS/FAIL with color coding)
        self.result_label = QLabel("PASS")
        self.result_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet("""
            padding: 8px;
            border-radius: 4px;
        """)
        layout.addWidget(self.result_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.btn_next = QPushButton("NEXT")
        self.btn_next.setFixedSize(120, 40)
        self.btn_next.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.btn_next.clicked.connect(self._on_next)
        button_layout.addWidget(self.btn_next)

        self.btn_edit = QPushButton("EDIT PARAMS")
        self.btn_edit.setFixedSize(140, 40)
        self.btn_edit.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #f57c00;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e65100;
            }
            QPushButton:pressed {
                background-color: #d84315;
            }
        """)
        self.btn_edit.clicked.connect(self._on_edit_params)
        button_layout.addWidget(self.btn_edit)

        button_layout.addStretch()

        self.btn_abort = QPushButton("ABORT")
        self.btn_abort.setFixedSize(120, 40)
        self.btn_abort.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_abort.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c62828;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.btn_abort.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_abort)

        layout.addLayout(button_layout)

    def set_result(self, step_name: str, status: str, measured: str, 
                   expected: str, debug_info: str = ""):
        """
        Set the result information to display.

        Args:
            step_name: Name of the inspection step (e.g., "Body Length")
            status: "PASS" or "FAIL"
            measured: Measured value with unit (e.g., "122 pixels")
            expected: Expected range (e.g., "101 - 166 pixels")
            debug_info: Additional debug information
        """
        # Build debug text
        text = f"Step: {step_name}\n"
        text += f"Status: {status}\n"
        text += f"\nMeasured: {measured}\n"
        text += f"Expected: {expected}\n"

        if debug_info:
            text += f"\nDebug Info:\n{debug_info}\n"

        self.debug_text.setText(text)

        # Update result label color and text
        if status == "PASS":
            self.result_label.setText("✓ PASS")
            self.result_label.setStyleSheet("""
                background: #4caf50;
                color: white;
                padding: 8px;
                border-radius: 4px;
            """)
        else:
            self.result_label.setText("✗ FAIL")
            self.result_label.setStyleSheet("""
                background: #f44336;
                color: white;
                padding: 8px;
                border-radius: 4px;
            """)

    def _on_next(self):
        """User clicked NEXT."""
        self.next_clicked = True
        self.accept()

    def _on_edit_params(self):
        """User clicked EDIT PARAMS."""
        self.edit_params_clicked = True
        self.accept()
