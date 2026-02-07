"""
Inspection Debug Flag Dialog - Python port from C++ DebugFlagDlg.cpp
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
)
from config.debug_flags import (
    DEBUG_DRAW, DEBUG_PRINT, DEBUG_PRINT_EXT, DEBUG_EDGE,
    DEBUG_STEP_MODE, DEBUG_SAVE_FAIL_IMAGE, DEBUG_TIME, DEBUG_TIME_EXT,
    DEBUG_BLOB, DEBUG_HIST, DEBUG_PKGLOC, DEBUG_PVI, DebugFlagManager
)


class InspectionDebugDialog(QDialog):
    """Debug Flag Setting Dialog - matches C++ CDebugFlagDlg"""

    def __init__(self, debug_flag: int = 0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Debug Flag Setting")
        self.resize(720, 620)

        # Initialize debug flag manager
        self.debug_manager = DebugFlagManager(debug_flag)

        # Create UI
        self._create_ui()

        # Load current flags into checkboxes
        self._load_flags()

    def _create_ui(self):
        """Create the dialog UI"""
        layout = QVBoxLayout()

        # Station Modules Group
        station_group = QGroupBox("Station Modules")
        station_layout = QVBoxLayout()

        self.chk_pkg_loc = QCheckBox("Package Location")
        self.chk_top_station = QCheckBox("Top Station")
        self.chk_bottom_station = QCheckBox("Bottom Station")

        station_layout.addWidget(self.chk_pkg_loc)
        station_layout.addWidget(self.chk_top_station)
        station_layout.addWidget(self.chk_bottom_station)
        station_group.setLayout(station_layout)

        # Debugging Options Group
        debug_group = QGroupBox("Debugging Options")
        debug_layout = QVBoxLayout()

        self.chk_debug_draw = QCheckBox("Debug Draw")
        self.chk_debug_print = QCheckBox("Debug Print")
        self.chk_debug_print_ext = QCheckBox("Debug Print Ext")
        self.chk_debug_time = QCheckBox("Debug Timing")
        self.chk_debug_time_ext = QCheckBox("Debug Timing Ext")
        self.chk_debug_step = QCheckBox("Debug Step Mode")
        self.chk_debug_edge = QCheckBox("Debug Edge")
        self.chk_debug_blob = QCheckBox("Debug Blob")
        self.chk_debug_hist = QCheckBox("Debug Histogram")
        self.chk_save_failed = QCheckBox("Save Failed Images")

        debug_layout.addWidget(self.chk_debug_draw)
        debug_layout.addWidget(self.chk_debug_print)
        debug_layout.addWidget(self.chk_debug_print_ext)
        debug_layout.addWidget(self.chk_debug_time)
        debug_layout.addWidget(self.chk_debug_time_ext)
        debug_layout.addWidget(self.chk_debug_step)
        debug_layout.addWidget(self.chk_debug_edge)
        debug_layout.addWidget(self.chk_debug_blob)
        debug_layout.addWidget(self.chk_debug_hist)
        debug_layout.addWidget(self.chk_save_failed)
        debug_group.setLayout(debug_layout)

        # Description Table
        table_label = QGroupBox("Description")
        table_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Option", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Add descriptions
        descriptions = [
            ("Debug Draw", "Draw overlays on inspection images (lines, rectangles, etc.)"),
            ("Debug Print", "Print inspection data to console"),
            ("Debug Print Ext", "Print extra inspection data to console"),
            ("Debug Timing", "Print timing information"),
            ("Debug Timing Ext", "Print extended timing information"),
            ("Debug Step Mode", "Enable step-by-step inspection with confirmation dialogs"),
            ("Debug Edge", "Enable edge detection debugging information"),
            ("Debug Blob", "Enable blob detection debugging information"),
            ("Debug Histogram", "Enable histogram debugging information"),
            ("Save Failed Images", "Automatically save images when inspection fails"),
            ("Package Location", "Enable debugging for package location inspection"),
            ("Top Station", "Enable debugging for top station PVI inspection"),
            ("Bottom Station", "Enable debugging for bottom station inspection")
        ]

        self.table.setRowCount(len(descriptions))
        for i, (option, desc) in enumerate(descriptions):
            self.table.setItem(i, 0, QTableWidgetItem(option))
            self.table.setItem(i, 1, QTableWidgetItem(desc))

        table_layout.addWidget(self.table)
        table_label.setLayout(table_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)

        # Add all to main layout
        layout.addWidget(station_group)
        layout.addWidget(debug_group)
        layout.addWidget(table_label)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_flags(self):
        """Load current flags into checkboxes - matches C++ OnInitDialog()"""
        # Station Modules
        self.chk_pkg_loc.setChecked(self.debug_manager.has_flag(DEBUG_PKGLOC))
        self.chk_top_station.setChecked(self.debug_manager.has_flag(DEBUG_PVI))
        self.chk_bottom_station.setChecked(False)  # Not in C++ - disabled
        self.chk_bottom_station.setEnabled(False)  # Disable since not implemented

        # Debugging Options
        self.chk_debug_draw.setChecked(self.debug_manager.has_flag(DEBUG_DRAW))
        self.chk_debug_print.setChecked(self.debug_manager.has_flag(DEBUG_PRINT))
        self.chk_debug_print_ext.setChecked(self.debug_manager.has_flag(DEBUG_PRINT_EXT))
        self.chk_debug_time.setChecked(self.debug_manager.has_flag(DEBUG_TIME))
        self.chk_debug_time_ext.setChecked(self.debug_manager.has_flag(DEBUG_TIME_EXT))
        self.chk_debug_step.setChecked(self.debug_manager.has_flag(DEBUG_STEP_MODE))
        self.chk_debug_edge.setChecked(self.debug_manager.has_flag(DEBUG_EDGE))
        self.chk_debug_blob.setChecked(self.debug_manager.has_flag(DEBUG_BLOB))
        self.chk_debug_hist.setChecked(self.debug_manager.has_flag(DEBUG_HIST))
        self.chk_save_failed.setChecked(self.debug_manager.has_flag(DEBUG_SAVE_FAIL_IMAGE))

    def accept(self):
        """Save flags when OK is clicked - matches C++ OnOK()"""
        # Reset flags
        self.debug_manager.reset()

        # Station Modules
        if self.chk_pkg_loc.isChecked():
            self.debug_manager.set_flag(DEBUG_PKGLOC)

        if self.chk_top_station.isChecked():
            self.debug_manager.set_flag(DEBUG_PVI)

        # Bottom station not implemented in C++, so we skip it

        # Debugging Options
        if self.chk_debug_draw.isChecked():
            self.debug_manager.set_flag(DEBUG_DRAW)

        if self.chk_debug_print.isChecked():
            self.debug_manager.set_flag(DEBUG_PRINT)

        if self.chk_debug_print_ext.isChecked():
            self.debug_manager.set_flag(DEBUG_PRINT_EXT)

        if self.chk_debug_time.isChecked():
            self.debug_manager.set_flag(DEBUG_TIME)

        if self.chk_debug_time_ext.isChecked():
            self.debug_manager.set_flag(DEBUG_TIME_EXT)

        if self.chk_debug_step.isChecked():
            self.debug_manager.set_flag(DEBUG_STEP_MODE)

        if self.chk_debug_edge.isChecked():
            self.debug_manager.set_flag(DEBUG_EDGE)

        if self.chk_debug_blob.isChecked():
            self.debug_manager.set_flag(DEBUG_BLOB)

        if self.chk_debug_hist.isChecked():
            self.debug_manager.set_flag(DEBUG_HIST)

        if self.chk_save_failed.isChecked():
            self.debug_manager.set_flag(DEBUG_SAVE_FAIL_IMAGE)

        super().accept()

    def get_debug_flags(self) -> int:
        """Get the resulting debug flags"""
        return self.debug_manager.get_flags()
