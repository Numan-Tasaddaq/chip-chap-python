import sys

from PySide6.QtWidgets import QApplication

from config.store import ensure_first_run_files
from license.manager import (
    is_license_present,
    load_license,
    verify_license,
)
from ui.license_dialog import LicenseDialog
from app.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    # Create app data files/directories on first run
    ensure_first_run_files()

    # Block app startup until license is valid
    license_ok = False

    if is_license_present():
        ld = load_license()
        license_ok = ld is not None and verify_license(ld)

    if not license_ok:
        dlg = LicenseDialog()
        if dlg.exec() == 0:  # user cancelled
            sys.exit(0)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
