# ui/simulator_prompt.py
from PySide6.QtWidgets import QMessageBox


def ask_disable_image_checks(parent=None) -> bool:
    """
    Returns True if user chooses to disable checks.
    """
    msg = QMessageBox(parent)
    msg.setWindowTitle("Simulator Mode Detected")
    msg.setIcon(QMessageBox.Question)
    msg.setText(
        "This software is running in simulator mode (no hardware).\n\n"
        "Pass/Fail image checks may cause unnecessary popups.\n\n"
        "Do you want to disable these checks?"
    )
    disable_btn = msg.addButton("Disable", QMessageBox.AcceptRole)
    keep_btn = msg.addButton("Keep Enabled", QMessageBox.RejectRole)

    msg.exec()
    return msg.clickedButton() == disable_btn
