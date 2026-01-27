
# app/main_window.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt, QSize, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QFont, QColor, QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QToolBar, QComboBox, QPushButton, QSplitter,
    QTableWidget, QMessageBox, QSlider, QSizePolicy, QMenu, QFrame, QToolButton, QDialog
)
import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap

# ✅ IMPORT REAL DIALOGS
from ui.inspection_parameters_range_dialog import InspectionParametersRangeDialog
from ui.lot_information_dialog import LotInformationDialog
from ui.body_color_dialog import BodyColorDialog
from ui.terminal_color_dialog import TerminalColorDialog
from ui.mark_color_dialog import MarkColorDialog
from ui.para_mark_config_dialog import ParaMarkConfigDialog
from ui.device_location_dialog import DeviceLocationDialog
from ui.pocket_location_dialog import PocketLocationDialog
from ui.device_inspection_dialog import DeviceInspectionDialog
from ui.inspection_debug_dialog import InspectionDebugDialog
from ui.alert_messages_dialog import AlertMessagesDialog
from ui.ignore_fail_count_dialog import IgnoreFailCountDialog
from ui.autorun_setting_dialog import AutoRunSettingDialog
from ui.autorun_withdraw_setting_dialog import AutoRunWithDrawSettingDialog
from ui.step_debug_dialog import StepDebugDialog
from imaging.grab_service import GrabService
from imaging.image_loader import ImageLoader
from config.inspection_parameters import InspectionParameters
from config.inspection_parameters_io import load_parameters
from imaging.pocket_teach_overlay import PocketTeachOverlay
from ui.image_rotation_dialog import ImageRotationDialog
from config.teach_store import load_teach_data
from config.teach_store import save_teach_data
from tests.test_top_bottom import test_top_bottom, test_feed
from tests.test_runner import TestResult, TestStatus
from pathlib import Path
from datetime import datetime

# ================= ENUMS & STATE =================
class TeachPhase(Enum):
    NONE = 0
    POCKET_DONE = 1
    ROTATION_ASK = 2
    ROTATION_ROI = 3
    ROTATION_DONE = 4
    PACKAGE_ASK = 5
    PACKAGE_ROI = 6
    PACKAGE_CONFIRM = 7
    COLOR_ASK = 9
    COLOR_BODY_ROI = 10
    COLOR_TERMINAL_ROI = 11
    DONE = 8

class Station(str, Enum):
    FEED = "Feed"
    TOP = "Top"
    BOTTOM = "Bottom"


class RunState(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


@dataclass
class AppState:
    station: Station = Station.FEED
    run_state: RunState = RunState.ONLINE
    track: int = 1


# ================= MAIN WINDOW =================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("iTrue - ChipCap Simulator [ONLINE]")
        self.resize(1500, 850)

        self.state = AppState()
        self.teach_phase = TeachPhase.NONE
        self.is_simulator_mode=False
        self.current_image=None  # Original loaded image (never modified)
        self.displayed_image=None  # Currently displayed image (may be modified with overlays)
       

        # Shared inspection flags (one set for all stations)
        self.inspection_parameters = load_parameters()
        self.shared_flags = self.inspection_parameters.flags

        self.grab_service=GrabService(self)
        self.image_loader = ImageLoader(self)

        self.binary_mode = False
        self.binary_threshold = 75  # default (PDF example)
        self.is_teach_mode = False
        self.teach_overlay = None
        self.step_mode_enabled = False  # Step-by-step debug mode toggle
        
        # Zoom variables
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.zoom_step = 0.1

        self._build_menu_bar()
        self._build_main_toolbar()
        self._build_track_bar()
        self._on_track_changed(self.track_combo.currentIndex())

        self._build_center_layout()


        self._update_active_track_ui()

        self._apply_run_state()
        self.inspection_parameters_by_station = {
            Station.FEED: InspectionParameters(),
            Station.TOP: InspectionParameters(),
            Station.BOTTOM: InspectionParameters(),
        }
        loaded = load_teach_data()
        for station_name, params in loaded.items():
            self.inspection_parameters_by_station[Station(station_name)] = params

        # Ensure all stations point to the shared flags
        for params in self.inspection_parameters_by_station.values():
            params.flags = self.shared_flags

        # Also keep the global inspection_parameters in sync with shared flags
        self.inspection_parameters.flags = self.shared_flags

        # Sync station menu to show Feed as default
        self._sync_station_actions()
          # =================================================
    # MENU BAR
    # =================================================
       # =================================================
    # MENU BAR
    # =================================================
    def _build_menu_bar(self):
        mb = self.menuBar()
        
        # Professional gradient styling with subtle shadow
        mb.setStyleSheet("""
            QMenuBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #34495e, stop:0.3 #2c3e50, stop:1 #1a252f);
                color: #ffffff;
                font-weight: 500;
                font-size: 11pt;
                padding: 3px 0px;
                border-bottom: 2px solid #3498db;
            }
            QMenuBar::item {
                padding: 8px 20px;
                background: transparent;
                border-radius: 0px;
                margin: 0px;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }
            QMenuBar::item:first {
                border-left: 1px solid rgba(255, 255, 255, 0.1);
            }
            QMenuBar::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(52, 152, 219, 0.3), stop:1 rgba(41, 128, 185, 0.3));
                color: #ffffff;
                font-weight: 600;
            }
            QMenuBar::item:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(52, 152, 219, 0.5), stop:1 rgba(41, 128, 185, 0.5));
            }
        """)

        # ---------- Production ----------
        m_production = mb.addMenu(" Production ")
        m_production.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 6px 0px;
                margin-top: 4px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
            QMenu::item {
                padding: 8px 30px 8px 25px;
                margin: 1px 8px;
                border-radius: 3px;
                color: #2c3e50;
                font-size: 10pt;
                min-width: 180px;
            }
            QMenu::item:selected {
                background-color: #3498db;
                color: white;
                font-weight: 500;
            }
            QMenu::item:disabled {
                color: #95a5a6;
                background-color: transparent;
            }
            QMenu::separator {
                height: 1px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, stop:0.2 #3498db, stop:0.8 #3498db, stop:1 transparent);
                margin: 6px 15px;
            }
            QMenu::indicator {
                width: 13px;
                height: 13px;
            }
            QMenu::indicator:checked {
                background-color: #3498db;
                border: 2px solid #2980b9;
                border-radius: 3px;
            }
        """)

        act_open_lot = QAction("Open Lot", self)
        act_open_lot.triggered.connect(self._open_lot_dialog)
        m_production.addAction(act_open_lot)

        act_end_lot = QAction("End Lot", self)
        act_end_lot.triggered.connect(lambda: self._stub("End Lot"))
        m_production.addAction(act_end_lot)

        # ---------- Station Selector ----------
        m_station = mb.addMenu(" Station ")
        m_station.setStyleSheet(m_production.styleSheet())

        station_header = QAction("🎯 SELECT STATION", self)
        station_header.setEnabled(False)
        station_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_station.addAction(station_header)

        station_group = QActionGroup(self)
        station_group.setExclusive(True)

        self.act_station_feed = QAction("     Feed", self, checkable=True)
        self.act_station_top = QAction("     Top", self, checkable=True)
        self.act_station_bottom = QAction("     Bottom", self, checkable=True)

        self.act_station_feed.triggered.connect(lambda: self._select_station(Station.FEED))
        self.act_station_top.triggered.connect(lambda: self._select_station(Station.TOP))
        self.act_station_bottom.triggered.connect(lambda: self._select_station(Station.BOTTOM))

        for act in (self.act_station_feed, self.act_station_top, self.act_station_bottom):
            station_group.addAction(act)
            m_station.addAction(act)

        self._sync_station_actions()

        m_production.addSeparator()
        
        # ✅ Online / Offline (checkable) - Special styling
        self.act_online_offline = QAction("🟢 Online / Offline", self)
        self.act_online_offline.setCheckable(True)
        self.act_online_offline.setChecked(False)  # ONLINE by default
        self.act_online_offline.triggered.connect(self._toggle_online_offline_from_menu)
        m_production.addAction(self.act_online_offline)

        # ---------- Engineering ----------
        m_engineering = mb.addMenu(" Engineering ")
        m_engineering.setStyleSheet(m_production.styleSheet())
        
        # Binarise with check indicator
        act_binarise = QAction("Binarise Image", self)
        act_binarise.setCheckable(True)
        act_binarise.triggered.connect(self._toggle_binarise)
        m_engineering.addAction(act_binarise)

        m_engineering.addSeparator()
        
        # Zoom section with subtle header
        zoom_header = QAction("━━━━━━ ZOOM ━━━━━━", self)
        zoom_header.setEnabled(False)
        zoom_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        m_engineering.addAction(zoom_header)
        
        act_zoom_in = QAction("     Zoom In", self)
        act_zoom_in.triggered.connect(self._zoom_in)
        m_engineering.addAction(act_zoom_in)
        
        act_zoom_fit = QAction("     Zoom Fit", self)
        act_zoom_fit.triggered.connect(self._zoom_fit)
        m_engineering.addAction(act_zoom_fit)
        
        act_zoom_out = QAction("     Zoom Out", self)
        act_zoom_out.triggered.connect(self._zoom_out)
        m_engineering.addAction(act_zoom_out)
        
        m_engineering.addSeparator()
        
        # File operations
        file_header = QAction("━━━━ FILE ━━━━", self)
        file_header.setEnabled(False)
        file_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        m_engineering.addAction(file_header)
        
        act_load_image = QAction("     Load Image From Disk", self)
        act_load_image.triggered.connect(self.image_loader.load_from_disk)
        m_engineering.addAction(act_load_image)

        act_save_image = QAction("     Save Image To Disk", self)
        act_save_image.triggered.connect(self._save_current_image)
        m_engineering.addAction(act_save_image)
        
        m_engineering.addSeparator()
        
        # Disabled features with special visual treatment
        disabled_header = QAction("━━━ DISABLED FEATURES ━━━", self)
        disabled_header.setEnabled(False)
        disabled_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        m_engineering.addAction(disabled_header)
        
        self._add_disabled_styled(m_engineering, "     🔒 Camera Enable", QColor("#95a5a6"))
        self._add_disabled_styled(m_engineering, "     🔒 RunTime Display Enable", QColor("#95a5a6"))
        self._add_disabled_styled(m_engineering, "     🔒 Camera AOI Resize Mode", QColor("#95a5a6"))

        # ---------- Configuration ----------
        m_config = mb.addMenu(" Configuration ")
        m_config.setStyleSheet(m_production.styleSheet())
        
        # Config file operations
        config_header = QAction("━━━ CONFIG FILES ━━━", self)
        config_header.setEnabled(False)
        config_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        m_config.addAction(config_header)
        
        m_config.addAction(QAction("     Select Config File", self, triggered=lambda: self._stub("Select Config File")))
        m_config.addAction(QAction("     Save Config As", self, triggered=lambda: self._stub("Save Config As")))
        
        act_para_mark = QAction("     Para & Mark Config File", self)
        act_para_mark.triggered.connect(self._open_para_mark_config_dialog)
        m_config.addAction(act_para_mark)
        
        m_config.addSeparator()
        
        # Location settings with beautiful header
        location_header = QAction("📍 LOCATION SETTINGS", self)
        location_header.setEnabled(False)
        location_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_config.addAction(location_header)
        
        act_device_loc = QAction("     Device Location", self)
        act_device_loc.triggered.connect(self._open_device_location_dialog)
        m_config.addAction(act_device_loc)

        act_pocket_loc = QAction("     Pocket Location", self)
        act_pocket_loc.triggered.connect(self._open_pocket_location_dialog)
        m_config.addAction(act_pocket_loc)

        act_device_inspection = QAction("     Device Inspection", self)
        act_device_inspection.triggered.connect(self._open_device_inspection_dialog)
        m_config.addAction(act_device_inspection)

        # Mark Inspection submenu with special icon
        m_mark = QMenu("🔤 Mark Inspection", self)
        m_mark.setStyleSheet("""
            QMenu {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px 0px;
                box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
            }
            QMenu::item {
                padding: 7px 30px 7px 25px;
                margin: 1px 8px;
                border-radius: 3px;
                color: #495057;
                font-size: 10pt;
            }
            QMenu::item:selected {
                background-color: #e9ecef;
                color: #212529;
            }
        """)
        m_mark.addAction(QAction("Mark Symbol Set", self, triggered=lambda: self._stub("Mark Symbol Set")))
        m_mark.addAction(QAction("Mark Parameters", self, triggered=lambda: self._stub("Mark Parameters")))
        m_mark.addAction(QAction("Mark Symbol Images", self, triggered=lambda: self._stub("Mark Symbol Images")))
        m_config.addMenu(m_mark)

        m_config.addSeparator()
        
        # Disabled configuration items
        system_header = QAction("⚙️ SYSTEM SETTINGS (DISABLED)", self)
        system_header.setEnabled(False)
        system_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_config.addAction(system_header)
        
        self._add_disabled_styled(m_config, "     ⚠️ Enable / Disable Inspection", QColor("#95a5a6"))
        self._add_disabled_styled(m_config, "     ⚠️ Camera Configuration", QColor("#95a5a6"))

        # Color Inspection submenu with color palette icon
        m_color = QMenu("🎨 Color Inspection", self)
        m_color.setStyleSheet("""
            QMenu {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 6px 0px;
                box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08);
            }
            QMenu::item {
                padding: 8px 30px 8px 25px;
                margin: 1px 8px;
                border-radius: 3px;
                color: #495057;
                font-size: 10pt;
            }
            QMenu::item:selected {
                background-color: #e9ecef;
                color: #212529;
            }
        """)
        act_body_color = QAction("Body Color", self)
        act_body_color.triggered.connect(self._open_body_color_dialog)
        m_color.addAction(act_body_color)
        
        act_terminal_color = QAction("Terminal Color", self)
        act_terminal_color.triggered.connect(self._open_terminal_color_dialog)
        m_color.addAction(act_terminal_color)
        
        act_mark_color = QAction("Mark Color", self)
        act_mark_color.triggered.connect(self._open_mark_color_dialog)
        m_color.addAction(act_mark_color)
        m_config.addMenu(m_color)
        
        # ---------- Run ----------
        m_run = mb.addMenu(" Run ")
        m_run.setStyleSheet(m_production.styleSheet())
        
        # Inspect Cycle submenu
        m_cycle = QMenu("🔄 Inspect Cycle", self)
        m_cycle.setStyleSheet(m_mark.styleSheet())
        m_cycle.addAction(QAction("Single Image", self, triggered=lambda: self._stub("Inspect Cycle → Single Image")))
        m_run.addMenu(m_cycle)

        # Inspect Saved Images submenu
        m_saved = QMenu("💾 Inspect Saved Images", self)
        m_saved.setStyleSheet(m_mark.styleSheet())
        
        # AutoRun actions with special styling
        autorun_header = QAction("Auto Run Options", self)
        autorun_header.setEnabled(False)
        autorun_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_saved.addAction(autorun_header)
        
        m_saved.addAction(
            QAction("     AutoRun", self,
                    triggered=lambda: AutoRunSettingDialog(self).exec())
        )
        m_saved.addAction(
            QAction("     AutoRun With Draw", self,
                    triggered=lambda: AutoRunWithDrawSettingDialog(self).exec())
        )
        
        m_saved.addSeparator()
        
        standard_header = QAction("Standard Operations", self)
        standard_header.setEnabled(False)
        standard_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_saved.addAction(standard_header)
        
        m_saved.addAction(QAction("     Step", self, triggered=lambda: self._stub("Step")))
        m_saved.addAction(QAction("     Set Stored Image Folder", self, triggered=lambda: self._stub("Set Stored Image Folder")))
        m_run.addMenu(m_saved)

        # ---------- Diagnostic ----------
        m_diag = mb.addMenu(" Diagnostic ")
        m_diag.setStyleSheet(m_production.styleSheet())
        
        # Diagnostic tools with icon
        diag_header = QAction("🔧 DIAGNOSTIC TOOLS", self)
        diag_header.setEnabled(False)
        diag_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_diag.addAction(diag_header)
        
        m_diag.addAction(
            QAction("     Inspection", self, triggered=lambda: InspectionDebugDialog(self).exec())
        )

        act_range = QAction("     Inspection Parameters Range", self)
        act_range.triggered.connect(self._open_inspection_parameters_range)
        m_diag.addAction(act_range)

        m_diag.addSeparator()
        
        # Advanced diagnostic
        advanced_header = QAction("⚡ ADVANCED DIAGNOSTICS", self)
        advanced_header.setEnabled(False)
        advanced_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_diag.addAction(advanced_header)
        
        act_step_mode = QAction("Enable Step Mode", self, checkable=True)
        act_step_mode.setChecked(False)
        act_step_mode.triggered.connect(self._toggle_step_mode)
        m_diag.addAction(act_step_mode)
        m_diag.addAction(
            QAction("     Alert Messages", self, triggered=lambda: AlertMessagesDialog(self).exec())
        )
        m_diag.addAction(QAction("     Encrypt / Decrypt Images", self, triggered=lambda: self._stub("Encrypt / Decrypt Images")))
        m_diag.addAction(
            QAction("     Ignore Count", self, triggered=lambda: IgnoreFailCountDialog(self).exec())
        )

        # ---------- View ----------
        m_view = mb.addMenu(" View ")
        m_view.setStyleSheet(m_production.styleSheet())
        
        # View operations with eye icon
        view_header = QAction("👁 VIEW OPTIONS", self)
        view_header.setEnabled(False)
        view_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_view.addAction(view_header)
        
        m_view.addAction(QAction("     Restore", self, triggered=lambda: self._stub("Restore")))
        m_view.addAction(QAction("     Reset Counters", self, triggered=lambda: self._stub("Reset Counters")))
        m_view.addAction(QAction("     Pass Bin Counters", self, triggered=lambda: self._stub("Pass Bin Counters")))
        m_view.addAction(QAction("     Password Details", self, triggered=lambda: self._stub("Password Details")))

        # ---------- Help ----------
        m_help = mb.addMenu(" Help ")
        m_help.setStyleSheet(m_production.styleSheet())
        
        # Help with question mark icon
        help_header = QAction("❓ HELP & SUPPORT", self)
        help_header.setEnabled(False)
        help_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_help.addAction(help_header)
        
        m_help.addAction(QAction("     About", self, triggered=lambda: self._stub("About")))

    def _add_disabled(self, menu, text):
        a = QAction(text, self)
        a.setEnabled(False)
        menu.addAction(a)
        
    def _add_disabled_styled(self, menu, text, color=None):
        """Add disabled action with beautiful styling"""
        a = QAction(text, self)
        a.setEnabled(False)
        # Use a slightly smaller, italic font for disabled items
        font = QFont("Segoe UI", 9)
        font.setItalic(True)
        a.setFont(font)
        menu.addAction(a)
    # =================================================
    # TOOLBARS
    # =================================================
        # =================================================
    # TOOLBARS
    # =================================================
    def _build_main_toolbar(self):
        tb = QToolBar("MainToolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(36, 36))
        
        # Professional toolbar styling
        tb.setStyleSheet("""
            QToolBar {
                background-color: #f5f7fa;
                border-bottom: 2px solid #d1d9e6;
                spacing: 8px;
                padding: 8px 12px;
            }
            QToolBar::separator {
                width: 1px;
                background: #c8d0e0;
                margin: 0 12px;
            }
        """)
        
        self.addToolBar(Qt.TopToolBarArea, tb)

        def add_professional_button(text, bg_color="#4a6fa5", hover_color="#385d8a"):
            """Create a professional looking button with clear disabled state"""
            btn = QToolButton()
            btn.setText(text)
            btn.setFixedSize(90, 38)
            btn.setStyleSheet(f"""
                /* ENABLED STATE */
                QToolButton {{
                    background-color: {bg_color};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-weight: 600;
                    font-size: 11pt;
                    padding: 8px;
                    letter-spacing: 0.5px;
                }}
                QToolButton:hover {{
                    background-color: {hover_color};
                }}
                QToolButton:pressed {{
                    background-color: #2a4365;
                    padding-top: 9px;
                    padding-bottom: 7px;
                }}
                
                /* DISABLED STATE - Very clear visual difference */
                QToolButton:disabled {{
                    background-color: #e0e0e0;
                    color: #9e9e9e;
                    border: 2px dashed #bdbdbd;
                    font-weight: normal;
                    opacity: 0.7;
                }}
                
                /* Checkable button states */
                QToolButton:checked {{
                    background-color: #2a4365;
                    border: 2px solid #1a2d4a;
                }}
                QToolButton:checked:disabled {{
                    background-color: #b0bec5;
                    color: #757575;
                    border: 2px dashed #90a4ae;
                }}
            """)
            return btn

        # Button colors for visual grouping
        colors = {
            "GRAB": ("#2e7d32", "#1b5e20"),      # Green
            "LIVE": ("#d32f2f", "#b71c1c"),      # Red
            "TEACH": ("#ed6c02", "#c55700"),     # Orange
            "TEST": ("#7b1fa2", "#5d1481"),      # Purple
            "NEXT": ("#1976d2", "#0d47a1"),      # Blue
            "ABORT": ("#d32f2f", "#b71c1c"),     # Red
            "START": ("#2e7d32", "#1b5e20"),     # Green
            "END": ("#d32f2f", "#b71c1c"),       # Red
            "OPEN": ("#0288d1", "#01579b"),      # Light Blue
            "PARA": ("#7b1fa2", "#5d1481"),      # Purple
            "RESET": ("#757575", "#424242")      # Gray
        }

        # Create and add buttons
        self.act_grab = add_professional_button("GRAB", *colors["GRAB"])
        self.act_grab.clicked.connect(self.grab_service.grab)
        tb.addWidget(self.act_grab)

        self.act_live = add_professional_button("LIVE", *colors["LIVE"])
        self.act_live.setCheckable(True)
        self.act_live.clicked.connect(self.grab_service.toggle_live)
        tb.addWidget(self.act_live)

        self.act_teach = add_professional_button("TEACH", *colors["TEACH"])
        self.act_teach.clicked.connect(self._on_teach)
        tb.addWidget(self.act_teach)

        self.act_test = add_professional_button("TEST", *colors["TEST"])
        self.act_test.clicked.connect(self._on_test)
        tb.addWidget(self.act_test)

        self.act_next = add_professional_button("NEXT", *colors["NEXT"])
        self.act_next.clicked.connect(self._on_next)
        tb.addWidget(self.act_next)

        tb.addSeparator()

        self.act_abort = add_professional_button("ABORT", *colors["ABORT"])
        tb.addWidget(self.act_abort)

        self.act_start = add_professional_button("START", *colors["START"])
        self.act_start.clicked.connect(self._on_start)
        tb.addWidget(self.act_start)

        self.act_end = add_professional_button("END", *colors["END"])
        self.act_end.clicked.connect(self._on_end)
        tb.addWidget(self.act_end)

        self.act_open = add_professional_button("OPEN", *colors["OPEN"])
        self.act_open.clicked.connect(self._open_lot_dialog)
        tb.addWidget(self.act_open)

        self.act_para = add_professional_button("PARA", *colors["PARA"])
        self.act_para.clicked.connect(self._open_device_inspection_dialog)
        tb.addWidget(self.act_para)

        tb.addSeparator()

        self.act_reset = add_professional_button("RESET", *colors["RESET"])
        tb.addWidget(self.act_reset)

        # Add flexible spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

    def _build_track_bar(self):
        tb = QToolBar("TrackBar")
        tb.setMovable(False)
        
        # Clean trackbar styling
        tb.setStyleSheet("""
            QToolBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                padding: 6px 12px;
                spacing: 10px;
            }
            QToolBar::separator {
                width: 1px;
                background: #e0e0e0;
                margin: 0 15px;
            }
        """)
        
        self.addToolBar(Qt.TopToolBarArea, tb)

        # Track selection section
        track_label = QLabel("Track Control")
        track_label.setStyleSheet("""
            QLabel {
                color: #37474f;
                font-weight: 600;
                font-size: 11pt;
                padding-right: 10px;
            }
        """)
        tb.addWidget(track_label)

        # Station buttons with clear enabled/disabled states
        self.btn_track_f = QPushButton("Track1-F")
        self.btn_track_f.setFixedSize(110, 36)
        self.btn_track_f.setStyleSheet("""
            /* ENABLED STATE */
            QPushButton {
                background-color: #e3f2fd;
                color: #1565c0;
                border: 2px solid #1565c0;
                border-radius: 5px;
                font-weight: 600;
                font-size: 10pt;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #bbdefb;
            }
            QPushButton:pressed {
                background-color: #90caf9;
            }
            QPushButton:checked {
                background-color: #1565c0;
                color: white;
                border: 2px solid #0d47a1;
            }
            
            /* DISABLED STATE - Very clear visual difference */
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #bdbdbd;
                border: 2px dashed #e0e0e0;
                font-weight: normal;
            }
            QPushButton:checked:disabled {
                background-color: #cfd8dc;
                color: #78909c;
                border: 2px dashed #b0bec5;
            }
        """)
        self.btn_track_f.setCheckable(True)
        self.btn_track_f.clicked.connect(lambda: self._open_track_folder('f'))


        self.btn_track_p = QPushButton("Track1-P")
        self.btn_track_p.setFixedSize(110, 36)
        self.btn_track_p.setStyleSheet("""
            /* ENABLED STATE */
            QPushButton {
                background-color: #f3e5f5;
                color: #7b1fa2;
                border: 2px solid #7b1fa2;
                border-radius: 5px;
                font-weight: 600;
                font-size: 10pt;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #e1bee7;
            }
            QPushButton:pressed {
                background-color: #ce93d8;
            }
            QPushButton:checked {
                background-color: #7b1fa2;
                color: white;
                border: 2px solid #5d1481;
            }
            
            /* DISABLED STATE - Very clear visual difference */
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #bdbdbd;
                border: 2px dashed #e0e0e0;
                font-weight: normal;
            }
            QPushButton:checked:disabled {
                background-color: #cfd8dc;
                color: #78909c;
                border: 2px dashed #b0bec5;
            }
        """)
        self.btn_track_p.setCheckable(True)
        self.btn_track_p.clicked.connect(lambda: self._open_track_folder('p'))


        tb.addWidget(self.btn_track_f)
        tb.addWidget(self.btn_track_p)

        tb.addSeparator()

        # Track selector with clear disabled state
        selector_label = QLabel("Select Track:")
        selector_label.setStyleSheet("""
            QLabel {
                color: #546e7a;
                font-weight: 500;
                font-size: 10pt;
                padding-right: 8px;
            }
            QLabel:disabled {
                color: #bdbdbd;
            }
        """)
        tb.addWidget(selector_label)

        self.track_combo = QComboBox()
        self.track_combo.setFixedSize(120, 34)
        self.track_combo.setStyleSheet("""
            /* ENABLED STATE */
            QComboBox {
                background-color: white;
                border: 2px solid #607d8b;
                border-radius: 4px;
                padding: 6px 10px;
                font-weight: 500;
                font-size: 10pt;
                color: #37474f;
                min-width: 80px;
            }
            QComboBox:hover {
                border-color: #455a64;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
                border: none;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #607d8b;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #e3f2fd;
                selection-color: #1565c0;
            }
            
            /* DISABLED STATE - Very clear visual difference */
            QComboBox:disabled {
                background-color: #f5f5f5;
                color: #bdbdbd;
                border: 2px dashed #e0e0e0;
            }
            QComboBox:disabled::down-arrow {
                opacity: 0.5;
            }
        """)
        self.track_combo.addItems(["Track1", "Track2", "Track3"])
        self.track_combo.currentIndexChanged.connect(self._on_track_changed)
        tb.addWidget(self.track_combo)

        # Add flexible spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        # Current selection indicator with disabled state
        selection_frame = QFrame()
        selection_frame.setStyleSheet("""
            /* ENABLED STATE */
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QFrame:disabled {
                background-color: #fafafa;
                border: 1px dashed #e0e0e0;
            }
        """)
        selection_layout = QHBoxLayout(selection_frame)
        selection_layout.setContentsMargins(8, 4, 8, 4)
        selection_layout.setSpacing(6)
        
        current_label = QLabel("Active:")
        current_label.setStyleSheet("""
            QLabel {
                color: #546e7a;
                font-weight: 500;
            }
            QLabel:disabled {
                color: #bdbdbd;
            }
        """)
        selection_layout.addWidget(current_label)
        
        self.current_track_label = QLabel()

        self.current_track_label.setStyleSheet("""
            QLabel {
                color: #d32f2f;
                font-weight: 600;
            }
            QLabel:disabled {
                color: #ef9a9a;
                font-weight: normal;
            }
        """)
        selection_layout.addWidget(self.current_track_label)
        
        tb.addWidget(selection_frame)

    def _set_station(self, station: Station):
        self.state.station = station
        self._update_active_track_ui()
        self._update_station_ui()
        self._apply_run_state()
        self._sync_station_actions()

    def _select_station(self, station: Station):
        # Map station choice to a default track (Top→1, Bottom→2, Feed→keep current)
        if station == Station.TOP:
            desired_track = 1
        elif station == Station.BOTTOM:
            desired_track = 2
        else:
            desired_track = max(1, self.state.track)

        # Sync track combo without firing signals
        if hasattr(self, "track_combo"):
            self.track_combo.blockSignals(True)
            self.track_combo.setCurrentIndex(desired_track - 1)
            self.track_combo.blockSignals(False)

        # Apply track-related UI updates
        self._on_track_changed(desired_track - 1)

        # Apply station change
        self._set_station(station)

    def _sync_station_actions(self):
        if hasattr(self, "act_station_feed"):
            self.act_station_feed.setChecked(self.state.station == Station.FEED)
            self.act_station_top.setChecked(self.state.station == Station.TOP)
            self.act_station_bottom.setChecked(self.state.station == Station.BOTTOM)

    

    def _on_track_changed(self, index: int):
        self.state.track = index + 1

        # 🔁 Update button labels to match track
        track_no = self.state.track
        self.btn_track_f.setText(f"Track{track_no}-F")
        self.btn_track_p.setText(f"Track{track_no}-P")

        # ❌ Do NOT change station here
        # Station will be resolved later from inspection parameters

        self._update_active_track_ui()
        self._apply_run_state()


       # =================================================
    # CENTER LAYOUT
    # =================================================
    def _build_center_layout(self):
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background: #E0E0E0;
            }
            QSplitter::handle:hover {
                background: #B0B0B0;
            }
        """)

        # LEFT PANEL (60%) ========================================
        left = QWidget()
        lyt = QVBoxLayout(left)
        lyt.setContentsMargins(16, 16, 16, 16)
        lyt.setSpacing(12)

        # Track label with styling
        self.track_label = QLabel()
        self.track_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333333;
                padding: 4px 0px;
            }
        """)
        lyt.addWidget(self.track_label)


        # Image display area with responsive sizing
        self.image_label = QLabel()
        self.image_label.setMinimumSize(400, 300)  # Reduced minimum for smaller screens
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet("""
            QLabel {
                background: #000000;
                border: 2px solid #CCCCCC;
                border-radius: 4px;
                min-height: 300px;
            }
        """)
        self.image_label.setAlignment(Qt.AlignCenter)
        # Show threshold slider when image area is clicked
        self.image_label.mousePressEvent = self._on_image_clicked
        lyt.addWidget(self.image_label, 1)  # Takes available space

        # Binary Threshold Section
        threshold_container = QWidget()
        threshold_container.setVisible(False)  # Hidden by default
        self.threshold_container = threshold_container  # Store reference for toggling
        
        threshold_layout = QVBoxLayout(threshold_container)
        threshold_layout.setContentsMargins(0, 8, 0, 0)
        
        # Threshold label
        threshold_header = QLabel("Binary Threshold Settings")
        threshold_header.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #555555;
                padding-bottom: 4px;
            }
        """)
        threshold_layout.addWidget(threshold_header)
        
        # Slider row with improved layout
        slider_row = QHBoxLayout()
        slider_row.setContentsMargins(0, 0, 0, 0)
        slider_row.setSpacing(8)
        
        self.binary_text_label = QLabel("Threshold:")
        self.binary_text_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #666666;
                min-width: 70px;
            }
        """)
        
        self.binary_slider = QSlider(Qt.Horizontal)
        self.binary_slider.setRange(0, 255)
        self.binary_slider.setValue(self.binary_threshold)
        self.binary_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.binary_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #E0E0E0;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #4A90E2;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: #E0E0E0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4A90E2;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #3A7BC8;
                width: 20px;
            }
        """)
        self.binary_slider.valueChanged.connect(self._on_binary_threshold_changed)
        
        self.binary_value_label = QLabel(str(self.binary_threshold))
        self.binary_value_label.setFixedWidth(50)
        self.binary_value_label.setAlignment(Qt.AlignCenter)
        self.binary_value_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #4A90E2;
                background: #F0F4F8;
                border: 1px solid #D0D7E2;
                border-radius: 3px;
                padding: 3px;
            }
        """)
        
        slider_row.addWidget(self.binary_text_label)
        slider_row.addWidget(self.binary_slider)
        slider_row.addWidget(self.binary_value_label)
        
        threshold_layout.addLayout(slider_row)
        lyt.addWidget(threshold_container)

        # Logo section with improved styling
        logo_container = QWidget()
        logo_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        logo_container.setStyleSheet("""
            QWidget {
                background: #2C3E50;
                border-radius: 6px;
                min-height: 80px;
            }
        """)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(16, 16, 16, 16)
        
        logo = QLabel("LOGO")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("""
            QLabel {
                color: #ECF0F1;
                font-size: 18px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)
        logo.setFixedHeight(60)
        logo_layout.addWidget(logo)
        
        lyt.addWidget(logo_container)

        splitter.addWidget(left)

        # RIGHT PANEL (40%) ========================================
        right = QWidget()
        right.setStyleSheet("""
            QWidget {
                background: #F8F9FA;
            }
        """)
        rlyt = QVBoxLayout(right)
        rlyt.setContentsMargins(12, 12, 12, 12)
        rlyt.setSpacing(12)

        # Top table with styling and responsive sizing
        self.top_tbl = QTableWidget(10, 2)
        self.top_tbl.setHorizontalHeaderLabels(["Parameter", "Track 1"])
        self.top_tbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.top_tbl.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #DEE2E6;
                border-radius: 4px;
                gridline-color: #E9ECEF;
                font-size: 11px;
                alternate-background-color: #F8F9FA;
            }
            QHeaderView::section {
                background: #4A90E2;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #E9ECEF;
            }
            QTableWidget::item:selected {
                background: #E3F2FD;
            }
        """)
        self.top_tbl.horizontalHeader().setStretchLastSection(True)
        self.top_tbl.verticalHeader().setVisible(False)
        self.top_tbl.setAlternatingRowColors(True)
        rlyt.addWidget(self.top_tbl, 1)  # Takes half of available space

        # Bottom table with styling and responsive sizing
        self.bot_tbl = QTableWidget(15, 3)
        self.bot_tbl.setHorizontalHeaderLabels(["Parameter", "Track 1 Qty", "Track 1 %"])
        self.bot_tbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.bot_tbl.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #DEE2E6;
                border-radius: 4px;
                gridline-color: #E9ECEF;
                font-size: 11px;
                alternate-background-color: #F8F9FA;
            }
            QHeaderView::section {
                background: #5CB85C;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #E9ECEF;
            }
            QTableWidget::item:selected {
                background: #E3F2FD;
            }
        """)
        self.bot_tbl.horizontalHeader().setStretchLastSection(True)
        self.bot_tbl.verticalHeader().setVisible(False)
        self.bot_tbl.setAlternatingRowColors(True)
        rlyt.addWidget(self.bot_tbl, 1)  # Takes half of available space

        splitter.addWidget(right)
        
        # Set initial sizes for 60/40 split
        splitter.setSizes([600, 400])  # Will be adjusted based on window size
        
        # Ensure proper proportions when resizing
        def update_splitter_sizes():
            total_width = splitter.width()
            left_width = int(total_width * 0.6)
            right_width = total_width - left_width
            splitter.setSizes([left_width, right_width])
        
        # Connect resize event
        splitter.splitterMoved.connect(lambda: update_splitter_sizes())
        
        # Set initial stretch factors for 60/40 ratio
        splitter.setStretchFactor(0, 6)  # Left gets 60% weight
        splitter.setStretchFactor(1, 4)  # Right gets 40% weight

        self.setCentralWidget(splitter)
        
        # Schedule initial layout update after window is shown
        QTimer.singleShot(100, update_splitter_sizes)

    # =================================================
    # RUN STATE
    # =================================================
    def _on_start(self):
    # START = go OFFLINE + Simulator ON
        self.grab_service.stop_live()
        self.state.run_state = RunState.OFFLINE
        self.is_simulator_mode = True
        self._apply_run_state()


    def _on_end(self):
    # END = go ONLINE + Hardware mode
        self._exit_teach_mode()
        self.grab_service.start_live()
        self.state.run_state = RunState.ONLINE
        self.is_simulator_mode = False
        self._apply_run_state()


    def _apply_run_state(self):
        offline = self.state.run_state == RunState.OFFLINE
        self.act_teach.setEnabled(offline)
        self.act_test.setEnabled(offline)
        self.act_start.setEnabled(not offline)
        self.act_end.setEnabled(offline)
        self.act_grab.setEnabled(
        self.state.run_state == RunState.ONLINE and not self.is_simulator_mode
    )
        online = self.state.run_state == RunState.ONLINE

        camera_allowed = (
    online
    and not self.is_simulator_mode
    and self._is_camera_supported()
)


        self.act_grab.setEnabled(camera_allowed)
        self.act_live.setEnabled(camera_allowed)

        # Stop LIVE automatically if camera not allowed
        if not camera_allowed:
            self.grab_service.stop_live()


        # If switching OFFLINE → stop LIVE immediately
        if not online:
            self.grab_service.stop_live()
        if hasattr(self, "act_online_offline"):
            self.act_online_offline.blockSignals(True)
            self.act_online_offline.setChecked(offline)
            self.act_online_offline.blockSignals(False)
        self.setWindowTitle(f"iTrue - ChipCap Simulator [{self.state.run_state.value}]")
    def _is_camera_supported(self) -> bool:
        """
        Defines whether camera/LIVE/GRAB is allowed
        based on current UI state.
        """
        # Simulator rule: camera allowed for all tracks & stations
        return True

    # =================================================
    # REAL DIALOGS
    # =================================================
    def _open_inspection_parameters_range(self):
        dlg = InspectionParametersRangeDialog(self)
        if dlg.exec():
           pass

    def _open_lot_dialog(self):
        dlg = LotInformationDialog(self)
        dlg.exec()
        
    def _open_body_color_dialog(self):
        dlg = BodyColorDialog(self)
        dlg.exec()
        
    def _open_terminal_color_dialog(self):
        dlg = TerminalColorDialog(self)
        dlg.exec()
        
    def _open_mark_color_dialog(self):
        dlg = MarkColorDialog(self)
        dlg.exec()
    def _toggle_online_offline_from_menu(self, checked: bool):
        """
        Menu toggle:
        Checked   -> OFFLINE
        Unchecked -> ONLINE
        """
        if checked:
            self.state.run_state = RunState.OFFLINE
        else:
            self.state.run_state = RunState.ONLINE

        self._apply_run_state()
    def _open_para_mark_config_dialog(self):
        dlg = ParaMarkConfigDialog(self)
        dlg.exec()
    def _open_device_location_dialog(self):
        dlg = DeviceLocationDialog(self)
        dlg.exec()
    def _open_pocket_location_dialog(self):
        dlg = PocketLocationDialog(self)
        dlg.exec()
    def _open_device_inspection_dialog(self):
        dlg = DeviceInspectionDialog(self)
        dlg.exec()
    def _toggle_binarise(self, checked: bool):
        self.binary_mode = checked
        self.binary_slider.setEnabled(checked)
        self.binary_slider.setVisible(checked)
        self.binary_text_label.setVisible(checked)
        self.binary_value_label.setVisible(checked)
        # Ensure the threshold container visibility matches mode
        if hasattr(self, "threshold_container"):
            self.threshold_container.setVisible(checked)


        if self.current_image is None:
            return

        if checked:
            self._apply_binary()
        else:
            self._show_normal_image()

    def _apply_zoom(self, pixmap: QPixmap):
        """Apply zoom level to pixmap"""
        if self.zoom_level == 1.0:
            # No zoom, fit to label
            scaled_pix = pixmap.scaled(
                self.image_label.size(),
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            # Apply zoom
            new_w = int(pixmap.width() * self.zoom_level)
            new_h = int(pixmap.height() * self.zoom_level)
            scaled_pix = pixmap.scaledToWidth(new_w, Qt.SmoothTransformation)
        
        return scaled_pix

    def _display_pixmap(self, pixmap: QPixmap):
        """Display pixmap with current zoom level"""
        scaled_pix = self._apply_zoom(pixmap)
        self.image_label.setPixmap(scaled_pix)

    def _zoom_in(self):
        if self.current_image is None:
            return
        
        self.zoom_level = min(self.zoom_level + self.zoom_step, self.max_zoom)
        self._refresh_display()

    def _zoom_out(self):
        if self.current_image is None:
            return
        
        self.zoom_level = max(self.zoom_level - self.zoom_step, self.min_zoom)
        self._refresh_display()

    def _zoom_fit(self):
        if self.current_image is None:
            return
        
        self.zoom_level = 1.0
        self._refresh_display()

    def _refresh_display(self):
        """Refresh the current display with new zoom level"""
        if self.current_image is None:
            return
        
        if self.binary_mode:
            self._apply_binary()
        else:
            self._show_normal_image()

    def _apply_binary(self):
        if self.current_image is None:
            return

        gray = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2GRAY)

        _, binary = cv2.threshold(
            gray,
            self.binary_threshold,
            255,
            cv2.THRESH_BINARY
        )

        h, w = binary.shape
        # Copy binary data to prevent memory sharing
        binary_copy = binary.copy()
        qimg = QImage(
            binary_copy.data,
            w,
            h,
            w,
            QImage.Format_Grayscale8
        ).copy()

        pix = QPixmap.fromImage(qimg)
        self._display_pixmap(pix)
    def _show_normal_image(self):
        if self.current_image is None:
            return

        rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w

        # Copy RGB data to prevent memory sharing
        rgb_copy = rgb.copy()
        qimg = QImage(
            rgb_copy.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        ).copy()

        pix = QPixmap.fromImage(qimg)
        self._display_pixmap(pix)
    def _on_binary_threshold_changed(self, value: int):
        self.binary_threshold = value
        self.binary_value_label.setText(str(value))

        if self.binary_mode:
            self._apply_binary()

    def _on_image_clicked(self, event):
        """On image click, show binary slider if binary mode is active."""
        if self.current_image is None:
            return

        # Only show threshold UI if binary mode is already enabled from menu
        if self.binary_mode:
            if hasattr(self, "threshold_container"):
                self.threshold_container.setVisible(True)

            self.binary_slider.setEnabled(True)
            self.binary_slider.setVisible(True)
            self.binary_text_label.setVisible(True)
            self.binary_value_label.setVisible(True)

            # Apply binary preview with current threshold
            self._apply_binary()

  





    def _on_teach(self):
        # 🚫 Block re-entry
        if self.is_teach_mode:
            return

        # ❌ No image → cannot teach
        if self.current_image is None:
            QMessageBox.warning(self, "Teach", "No image loaded.")
            return

        # ❌ Teach only allowed in OFFLINE
        if self.state.run_state != RunState.OFFLINE:
            QMessageBox.warning(
                self,
                "Teach",
                "Please switch to OFFLINE mode before teaching."
            )
            return

        params = self.current_params()
        flags = self.shared_flags

        # Drive teach path from explicit station selection
        if self.state.station == Station.FEED:
            if not flags.get("enable_package_location", False):
                QMessageBox.warning(
                    self,
                    "Teach",
                    "Package Location Inspection must be enabled before Feed Teach."
                )
                return
            if not flags.get("enable_pocket_location", False):
                QMessageBox.warning(
                    self,
                    "Teach",
                    "Pocket Location Inspection must be enabled before Feed Teach."
                )
                return
            self._teach_feed_station()
            return

        # TOP/BOTTOM path (package teach)
        if not flags.get("enable_package_location", False):
            QMessageBox.warning(
                self,
                "Teach",
                "Package Location Inspection must be enabled before Teach."
            )
            return

        self._teach_top_bottom_station()


   


    def _teach_feed_station(self):
        reply = QMessageBox.question(
            self,
            "Teach Feed Station",
            "Do you want to teach Pocket Position?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._start_pocket_teach()

            
    def _teach_top_bottom_station(self):
        self.is_teach_mode = True

        # PDF: Start by asking if image is rotated
        self.teach_phase = TeachPhase.ROTATION_ASK
        self._ask_image_rotation()



    def _start_pocket_teach(self):
        self.is_teach_mode = True
        self.teach_phase = TeachPhase.NONE  # <-- IMPORTANT

        QMessageBox.information(
            self,
            "Pocket Teach",
            "Adjust the Red Box to pocket position.\nPress Enter to confirm."
        )

        self.teach_overlay = PocketTeachOverlay(self.image_label, self)
        self.teach_overlay.setGeometry(self.image_label.rect())
        self.teach_overlay.show()
        self.teach_overlay.setFocus()


    def _confirm_pocket_teach(self, roi):
        """
        STEP 11
        Green box = pocket position learned
        """

        # Save pocket location to station-specific parameters
        params = self.current_params()
        params.pocket_x = roi.x
        params.pocket_y = roi.y
        params.pocket_w = roi.w
        params.pocket_h = roi.h
        params.is_defined = True

        # Save teach data to file
        save_teach_data(self.inspection_parameters_by_station)

        # 🔁 Switch overlay to GREEN (important)
        self.teach_overlay.set_confirmed(True)

        self.teach_phase = TeachPhase.POCKET_DONE

        QMessageBox.information(
            self,
            "Pocket Teach",
            "Pocket position learned.\n(Green Box Confirmed)\n\nClick NEXT to continue."
        )
        
        # Remove overlay after confirmation
        if self.teach_overlay:
            self.teach_overlay.hide()
            self.teach_overlay.deleteLater()
            self.teach_overlay = None

    def _ask_image_rotation(self):
        """
        STEP 12
        Ask user if image is rotated
        """

        if self.teach_phase not in (
            TeachPhase.POCKET_DONE,
            TeachPhase.ROTATION_ASK
        ):
            return


        reply = QMessageBox.question(
            self,
            "Image Rotation",
            "Is the image rotated?",
            QMessageBox.Yes | QMessageBox.No
        )

        # ---- NO ROTATION ----
        if reply == QMessageBox.No:
            params = self.current_params()
            params.rotation_angle = 0.0


            QMessageBox.information(
                self,
                "Rotation",
                "No rotation applied.\nClick OK to continue."
            )

            self._start_package_teach()
            return

        # ---- YES ROTATION ----
        dlg = ImageRotationDialog(
            self,
            initial_angle=self.inspection_parameters.rotation_angle
        )

        if dlg.exec():
            params = self.current_params()
            params.rotation_angle = dlg.angle


            QMessageBox.information(
                self,
                "Rotation",
                "Image rotation completed.\nClick OK to continue."
            )

            self._start_package_teach()


    def _start_rotation_teach(self):
        """
        STEP 13
        Red box appears to cover entire device for rotation detection
        """

        self.teach_phase = TeachPhase.ROTATION_ROI

        QMessageBox.information(
            self,
            "Rotation Teach",
            "Adjust the red box to fully cover the device.\nPress Enter to confirm."
        )

        # TODO: Replace with RotationTeachOverlay later
        self.teach_overlay = PocketTeachOverlay(self.image_label, self)
        self.teach_overlay.setGeometry(self.image_label.rect())
        self.teach_overlay.show()
        self.teach_overlay.setFocus()
    def _confirm_rotation_teach(self, angle_deg: float = 0.0):
        """
        STEP 14
        Rotate image until device is upright
        """

        self.inspection_parameters.rotation_angle = angle_deg
        self.teach_phase = TeachPhase.ROTATION_DONE

        QMessageBox.information(
            self,
            "Rotation",
            "Image rotation completed.\nThen Done."
        )

        self._exit_teach_mode()

        # Continue to package teach
        self._start_package_teach()
    def _start_package_teach(self):
        """
        STEP 15
        Inform user that package teach will start
        """

        self.teach_phase = TeachPhase.PACKAGE_ASK

        QMessageBox.information(
            self,
            "Package Teach",
            "This is to Teach the Package Position.\nClick OK to continue."
        )

        # STEP 16
        self._start_package_roi()
    def _start_package_roi(self):
        """
        STEP 16
        Red box to define package position
        """

        self.teach_phase = TeachPhase.PACKAGE_ROI

        QMessageBox.information(
            self,
            "Package Teach",
            "Adjust the red rectangle to set the package position.\nPress Enter to confirm."
        )

        # Reuse overlay for now
        self.teach_overlay = PocketTeachOverlay(self.image_label, self)
        self.teach_overlay.setGeometry(self.image_label.rect())
        self.teach_overlay.show()
        self.teach_overlay.setFocus()
    def _confirm_package_teach(self, roi):
        """
        STEP 17 & 18
        Confirm package location, then ask about color inspection teach
        """

        reply = QMessageBox.question(
            self,
            "Confirm Package",
            "Is the package location correct?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Save package ROI
            params = self.current_params()

            x, y, w, h = self._map_label_roi_to_image(roi)

            params.package_x = x
            params.package_y = y
            params.package_w = w
            params.package_h = h
            params.is_defined = True

            save_teach_data(self.inspection_parameters_by_station)

            # Ask about color inspection teach (same pattern as old code)
            self._ask_color_inspection_teach()
        else:
            # Retry package teach
            self._start_package_roi()

    def _ask_color_inspection_teach(self):
        """
        Ask if user wants to teach color inspection (body and/or terminal color).
        Same pattern as old C++ code: after package location confirmation.
        """
        params = self.current_params()
        flags = params.flags

        # Check if color inspection is enabled
        check_body_color = flags.get("check_body_color", False)
        check_terminal_color = flags.get("check_terminal_color", False)

        if not (check_body_color or check_terminal_color):
            # No color inspection enabled, skip to done
            self.teach_phase = TeachPhase.DONE
            QMessageBox.information(
                self,
                "Teach Complete",
                "Teach process completed successfully.\nClick OK to finish."
            )
            self._exit_teach_mode()
            return

        # If color inspection enabled, ask to teach colors
        reply = QMessageBox.question(
            self,
            "Color Inspection Teach",
            "Do you want to teach Color Inspection?\n\n(Body Color and/or Terminal Color)",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Start body color teach if enabled
            if check_body_color:
                self.teach_phase = TeachPhase.COLOR_BODY_ROI
                self._start_body_color_teach()
            else:
                # Skip to terminal color
                if check_terminal_color:
                    self.teach_phase = TeachPhase.COLOR_TERMINAL_ROI
                    self._start_terminal_color_teach()
                else:
                    self.teach_phase = TeachPhase.DONE
                    QMessageBox.information(
                        self,
                        "Teach Complete",
                        "Teach process completed successfully.\nClick OK to finish."
                    )
                    self._exit_teach_mode()
        else:
            # Skip color teaching
            self.teach_phase = TeachPhase.DONE
            QMessageBox.information(
                self,
                "Teach Complete",
                "Teach process completed successfully.\nClick OK to finish."
            )
            self._exit_teach_mode()

    def _start_body_color_teach(self):
        """
        Show overlay for body color ROI selection and capture intensity
        """
        QMessageBox.information(
            self,
            "Body Color Teach",
            "Adjust the Red Box to set the body color area.\nPress Enter to confirm."
        )

        # Create and show overlay for color ROI selection
        self.teach_overlay = PocketTeachOverlay(self.image_label, self)
        self.teach_overlay.setGeometry(self.image_label.rect())
        self.teach_overlay.show()
        self.teach_overlay.setFocus()

    def _confirm_body_color_teach(self, roi):
        """
        Confirm body color ROI and capture mean intensity
        """
        params = self.current_params()

        # Map ROI to image coordinates
        x, y, w, h = self._map_label_roi_to_image(roi)

        # Capture mean intensity from ROI
        if self.current_image is None:
            QMessageBox.warning(self, "Error", "No image loaded")
            return

        import cv2
        img = self.current_image
        if img.size == 0:
            QMessageBox.warning(self, "Error", "Invalid image")
            return

        # Clamp ROI to image bounds
        x2 = min(img.shape[1], x + w)
        y2 = min(img.shape[0], y + h)
        x = max(0, x)
        y = max(0, y)

        if x2 <= x or y2 <= y:
            QMessageBox.warning(self, "Error", "Invalid ROI")
            return

        roi_img = img[y:y2, x:x2]
        if roi_img.size == 0:
            QMessageBox.warning(self, "Error", "ROI is empty")
            return

        # Convert to grayscale and get mean intensity
        if len(roi_img.shape) == 3:
            roi_gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        else:
            roi_gray = roi_img

        mean_intensity = int(roi_gray.mean())

        # Save body color intensity with tolerance (±20)
        tolerance = 20
        params.body_intensity_min = max(0, mean_intensity - tolerance)
        params.body_intensity_max = min(255, mean_intensity + tolerance)

        save_teach_data(self.inspection_parameters_by_station)

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Body Color Captured",
            f"Body Color Intensity: {mean_intensity}\n(Range: {params.body_intensity_min}-{params.body_intensity_max})\n\nSave this value?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Remove overlay and proceed to terminal color
            if self.teach_overlay:
                self.teach_overlay.hide()
                self.teach_overlay.deleteLater()
                self.teach_overlay = None

            if params.flags.get("check_terminal_color", False):
                self.teach_phase = TeachPhase.COLOR_TERMINAL_ROI
                self._start_terminal_color_teach()
            else:
                self.teach_phase = TeachPhase.DONE
                QMessageBox.information(
                    self,
                    "Teach Complete",
                    "Teach process completed successfully.\nClick OK to finish."
                )
                self._exit_teach_mode()
        else:
            # Retry body color teach
            self._start_body_color_teach()

    def _start_terminal_color_teach(self):
        """
        Show overlay for terminal color ROI selection and capture intensity
        """
        QMessageBox.information(
            self,
            "Terminal Color Teach",
            "Adjust the Red Box to set the terminal color area.\nPress Enter to confirm."
        )

        # Create and show overlay for color ROI selection
        self.teach_overlay = PocketTeachOverlay(self.image_label, self)
        self.teach_overlay.setGeometry(self.image_label.rect())
        self.teach_overlay.show()
        self.teach_overlay.setFocus()

    def _confirm_terminal_color_teach(self, roi):
        """
        Confirm terminal color ROI and capture mean intensity
        """
        params = self.current_params()

        # Map ROI to image coordinates
        x, y, w, h = self._map_label_roi_to_image(roi)

        # Capture mean intensity from ROI
        if self.current_image is None:
            QMessageBox.warning(self, "Error", "No image loaded")
            return

        import cv2
        img = self.current_image
        if img.size == 0:
            QMessageBox.warning(self, "Error", "Invalid image")
            return

        # Clamp ROI to image bounds
        x2 = min(img.shape[1], x + w)
        y2 = min(img.shape[0], y + h)
        x = max(0, x)
        y = max(0, y)

        if x2 <= x or y2 <= y:
            QMessageBox.warning(self, "Error", "Invalid ROI")
            return

        roi_img = img[y:y2, x:x2]
        if roi_img.size == 0:
            QMessageBox.warning(self, "Error", "ROI is empty")
            return

        # Convert to grayscale and get mean intensity
        if len(roi_img.shape) == 3:
            roi_gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        else:
            roi_gray = roi_img

        mean_intensity = int(roi_gray.mean())

        # Save terminal color intensity with tolerance (±20)
        tolerance = 20
        params.terminal_intensity_min = max(0, mean_intensity - tolerance)
        params.terminal_intensity_max = min(255, mean_intensity + tolerance)

        save_teach_data(self.inspection_parameters_by_station)

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Terminal Color Captured",
            f"Terminal Color Intensity: {mean_intensity}\n(Range: {params.terminal_intensity_min}-{params.terminal_intensity_max})\n\nSave this value?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Remove overlay and complete teach
            if self.teach_overlay:
                self.teach_overlay.hide()
                self.teach_overlay.deleteLater()
                self.teach_overlay = None

            self.teach_phase = TeachPhase.DONE
            QMessageBox.information(
                self,
                "Teach Complete",
                "Teach process completed successfully.\nClick OK to finish."
            )
            self._exit_teach_mode()
        else:
            # Retry terminal color teach
            self._start_terminal_color_teach()
    def _exit_teach_mode(self):
        if not self.is_teach_mode:
            return

        self.is_teach_mode = False

        if self.teach_overlay:
            self.teach_overlay.hide()
            self.teach_overlay.deleteLater()
            self.teach_overlay = None
    def _on_grab_safe(self):
        self._exit_teach_mode()
        self.grab_service.grab()

    def _on_live_safe(self):
        self._exit_teach_mode()
        self.grab_service.toggle_live()

    def _update_station_ui(self):
        # Reset styles
        self.btn_track_f.setStyleSheet("")
        self.btn_track_p.setStyleSheet("")

        if self.state.station == Station.FEED:
            self.btn_track_f.setStyleSheet(
                "background:#2ecc71; color:black; font-weight:bold;"
            )
        else:
            # TOP & BOTTOM both come under P
            self.btn_track_p.setStyleSheet(
                "background:#3498db; color:white; font-weight:bold;"
            )
    def _on_next(self):
        if not self.is_teach_mode:
            return

        # After green pocket box
        if self.teach_phase == TeachPhase.POCKET_DONE:
            self._ask_image_rotation()

        # Confirm ROI via NEXT (optional, same as Enter)
        elif self.teach_phase in (
            TeachPhase.ROTATION_ROI,
            TeachPhase.PACKAGE_ROI
        ):
            if self.teach_overlay:
                self.teach_overlay.confirm()


    def _confirm_overlay(self, roi):

        # ---- FEED pocket confirm ----
        if self.teach_phase == TeachPhase.NONE:
            self._confirm_pocket_teach(roi)
            return

        # ---- P station device ROI confirm ----
        if self.teach_phase == TeachPhase.ROTATION_ROI:
            self.teach_overlay.set_confirmed(True)

            reply = QMessageBox.question(
                self,
                "Image Rotation",
                "Is the image rotated?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.No:
                self.inspection_parameters.rotation_angle = 0.0
                self._start_package_teach()
                return

            # YES → rotation dialog
            dlg = ImageRotationDialog(
                self,
                initial_angle=self.inspection_parameters.rotation_angle
            )

            if dlg.exec():
                self.inspection_parameters.rotation_angle = dlg.angle
                QMessageBox.information(
                    self,
                    "Rotation",
                    "Image rotation completed.\nClick OK to continue."
                )
                self._start_package_teach()
            return

        # ---- Package ROI confirm ----
        if self.teach_phase == TeachPhase.PACKAGE_ROI:
            self.teach_overlay.set_confirmed(True)
            self._confirm_package_teach(roi)
            return

        # ---- Body Color teach ROI confirm ----
        if self.teach_phase == TeachPhase.COLOR_BODY_ROI:
            self.teach_overlay.set_confirmed(True)
            self._confirm_body_color_teach(roi)
            return

        # ---- Terminal Color teach ROI confirm ----
        if self.teach_phase == TeachPhase.COLOR_TERMINAL_ROI:
            self.teach_overlay.set_confirmed(True)
            self._confirm_terminal_color_teach(roi)
            return

    def _apply_rotation_preview(self, angle_deg: float):
        """
        Rotate image LIVE during rotation dialog
        """
        if self.current_image is None:
            return

        h, w = self.current_image.shape[:2]
        center = (w // 2, h // 2)

        M = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
        rotated = cv2.warpAffine(self.current_image, M, (w, h))

        # Preview only - don't save this as current_image
        self._show_image(rotated)
    def _show_image(self, image):
        """Display an image (possibly with overlays) without overwriting the original."""
        self.displayed_image = image
        
        # Debug: Verify current_image is not being modified
        if self.current_image is not None:
            mean_val = cv2.mean(self.current_image)[0]
            print(f"[DEBUG] current_image mean: {mean_val:.1f}, displayed_image mean: {cv2.mean(image)[0]:.1f}")
        
        # IMPORTANT: Create a copy of the RGB data to prevent memory sharing with QImage
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        # Make a copy to ensure QImage doesn't share memory with our numpy array
        rgb_copy = rgb.copy()
        qimg = QImage(rgb_copy.data, w, h, ch * w, QImage.Format_RGB888).copy()
        pix = QPixmap.fromImage(qimg)
        self._display_pixmap(pix)


    def _update_active_track_ui(self):
        # Update "Active:" label in Track Control bar
        if hasattr(self, "current_track_label"):
            self.current_track_label.setText(f"Track{self.state.track}")

        # Update main image panel title
        if hasattr(self, "track_label"):
            self.track_label.setText(f"Track {self.state.track}")
        
        # Update table headers to reflect active track
        if hasattr(self, "top_tbl"):
            self.top_tbl.setHorizontalHeaderLabels(["Parameter", f"Track {self.state.track}"])
        
        if hasattr(self, "bot_tbl"):
            self.bot_tbl.setHorizontalHeaderLabels(["Parameter", f"Track {self.state.track} Qty", f"Track {self.state.track} %"])
    def current_params(self) -> InspectionParameters:
        if self.state.station not in self.inspection_parameters_by_station:
            raise RuntimeError(
                f"Invalid station state: {self.state.station}"
            )
        params = self.inspection_parameters_by_station[self.state.station]
        # Always use shared flags for inspection item selection
        params.flags = self.shared_flags
        return params

    

  

    def _map_label_roi_to_image(self, roi):
        """
        Convert ROI from QLabel (view) coordinates
        to actual image pixel coordinates
        """
        if self.current_image is None:
            return roi

        img_h, img_w = self.current_image.shape[:2]

        label_w = self.image_label.width()
        label_h = self.image_label.height()

        # Scale factors
        sx = img_w / label_w
        sy = img_h / label_h

        return (
            int(roi.x * sx),
            int(roi.y * sy),
            int(roi.w * sx),
            int(roi.h * sy),
        )
    def on_inspection_parameters_changed(self):
        # Station is now explicitly selected via the Station menu
        # No need to auto-detect from flags anymore
        # Just update the UI without changing the station
        self._update_station_ui()
        self._update_active_track_ui()
    def _resolve_top_bottom_station(self) -> Station:
        # Old iTrue behavior:
        # Track1 → TOP
        # Track2 → BOTTOM
        # (Extendable if needed)

        if self.state.track == 1:
            return Station.TOP
        else:
            return Station.BOTTOM
    def _toggle_step_mode(self, checked: bool):
        """Toggle step mode on/off."""
        self.step_mode_enabled = checked
        status = "ENABLED" if checked else "DISABLED"
        print(f"[STEP MODE] {status}")

    def _on_test(self):
        if self.current_image is None:
            QMessageBox.warning(self, "Test", "No image loaded.")
            return

        if self.state.run_state != RunState.OFFLINE:
            QMessageBox.warning(self, "Test", "Switch to OFFLINE mode.")
            return

        # Use the explicitly selected station
        station = self.state.station

        # TOP and BOTTOM stations use the same teach data
        test_station = station
        if station == Station.BOTTOM:
            test_station = Station.TOP

        # Get station-specific parameters with shared flags
        params = self.inspection_parameters_by_station[test_station]

        # Debug: Log image state before test
        mean_before = cv2.mean(self.current_image)[0]
        # Also check the ROI region that will be tested
        x, y, w, h = params.package_x, params.package_y, params.package_w, params.package_h
        roi_crop = self.current_image[y:y+h, x:x+w]
        roi_mean = cv2.mean(roi_crop)[0]
        print(f"[DEBUG] Before test - current_image mean: {mean_before:.1f}, ROI mean: {roi_mean:.1f}")

        print(f"\n[TEST] Station: {station}")
        if station == Station.BOTTOM:
            print(f"[TEST] Using TOP station teach data for BOTTOM station")
        print(f"[TEST] Shared Inspection Flags: {self.shared_flags}")
        print(f"[TEST] Station Teach Data: package=({params.package_x}, {params.package_y}, {params.package_w}, {params.package_h})")

        # Run test based on station
        if station == Station.FEED:
            # FEED station test
            if self.step_mode_enabled:
                print(f"[TEST] Step Mode ENABLED - running step-by-step inspection")
                # Create explicit copy using numpy to prevent any reference sharing
                test_image = np.array(self.current_image, copy=True, order='C')
                print(f"[DEBUG] Test image copy - id={id(test_image)}")
                result = test_feed(
                    image=test_image,
                    params=params,
                    step_mode=True,
                    step_callback=self._handle_test_step
                )
            else:
                # Create explicit copy using numpy to prevent any reference sharing
                test_image = np.array(self.current_image, copy=True, order='C')
                print(f"[DEBUG] Test image copy - id={id(test_image)}")
                result = test_feed(
                    image=test_image,
                    params=params
                )
        else:
            # TOP/BOTTOM test with optional step mode
            if self.step_mode_enabled:
                print(f"[TEST] Step Mode ENABLED - running step-by-step inspection")
                # Create explicit copy using numpy to prevent any reference sharing
                # FORCE new memory allocation by using array constructor
                test_image = np.array(self.current_image, copy=True, order='C')
                # Verify the copy is independent
                test_mean = cv2.mean(test_image)[0]
                test_roi = test_image[y:y+h, x:x+w]
                test_roi_mean = cv2.mean(test_roi)[0]
                print(f"[DEBUG] Test image copy - mean: {test_mean:.1f}, ROI mean: {test_roi_mean:.1f}, id={id(test_image)}")
                result = test_top_bottom(
                    image=test_image,
                    params=params,
                    step_mode=True,
                    step_callback=self._handle_test_step
                )
            else:
                # Create explicit copy using numpy to prevent any reference sharing
                # FORCE new memory allocation by using array constructor
                test_image = np.array(self.current_image, copy=True, order='C')
                # Verify the copy is independent
                test_mean = cv2.mean(test_image)[0]
                test_roi = test_image[y:y+h, x:x+w]
                test_roi_mean = cv2.mean(test_roi)[0]
                print(f"[DEBUG] Test image copy - mean: {test_mean:.1f}, ROI mean: {test_roi_mean:.1f}, id={id(test_image)}")
                result = test_top_bottom(
                    image=test_image,
                    params=params
                )

        if result.result_image is not None:
            self._show_image(result.result_image)

        # Debug: Verify current_image wasn't modified by test
        mean_after = cv2.mean(self.current_image)[0]
        print(f"[DEBUG] After test - current_image mean: {mean_after:.1f}")

        # Display detailed reason in dialog box
        title = f"Test Result: {result.status}"
        QMessageBox.information(self, title, result.message)

        print(f"[TEST RESULT] {result.status} - {result.message}")

        # Save result image to track-specific folder (pass/fail)
        try:
            self._save_result_image(result)
        except Exception as e:
            print(f"[WARN] Failed to save result image: {e}")

    def _save_result_image(self, result: TestResult):
        """Save the current/result image to 'New folder/Track{N}p' or 'Track{N}f'."""
        # Decide pass/fail suffix
        suffix = 'p' if result.status == TestStatus.PASS else 'f'

        # Base folder 'New folder' at workspace root
        base_dir = Path("New folder")
        base_dir.mkdir(parents=True, exist_ok=True)

        # Track-specific folder
        track_dir = base_dir / f"Track{self.state.track}{suffix}"
        track_dir.mkdir(parents=True, exist_ok=True)

        # Choose image: prefer overlay/result_image, else raw current image
        img = result.result_image if hasattr(result, 'result_image') and result.result_image is not None else self.current_image
        if img is None:
            print("[WARN] No image to save")
            return

        # Build filename with timestamp
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out_path = track_dir / f"{ts}.png"

        # Save using OpenCV
        ok = cv2.imwrite(str(out_path), img)
        if ok:
            print(f"[INFO] Saved image: {out_path}")
        else:
            print(f"[WARN] cv2.imwrite failed: {out_path}")

    def _open_track_folder(self, kind: str):
        """Open the Track folder for current track. kind: 'p' or 'f'."""
        base_dir = Path("New folder")
        track_dir = base_dir / f"Track{self.state.track}{kind}"
        try:
            track_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(track_dir)))

    def _handle_test_step(self, step_data: dict) -> bool:
        """
        Handle a single step in step-by-step test mode.
        
        Args:
            step_data: Dict with keys:
                - step_name: Name of the inspection (e.g., "Body Length")
                - status: "PASS" or "FAIL"
                - measured: Measured value
                - expected: Expected range
                - debug_info: Extra debug information
        
        Returns:
            True to continue to next step, False to abort
        """
        dlg = StepDebugDialog(self)
        dlg.set_result(
            step_name=step_data.get("step_name", "Unknown"),
            status=step_data.get("status", "?"),
            measured=step_data.get("measured", ""),
            expected=step_data.get("expected", ""),
            debug_info=step_data.get("debug_info", "")
        )

        result = dlg.exec()

        if dlg.edit_params_clicked:
            # Open Device Inspection dialog for parameter editing
            print("[STEP] User requested parameter edit")
            self._open_device_inspection_dialog()
            return False  # Abort current test, user will adjust and re-test

        if result == QDialog.Accepted and dlg.next_clicked:
            print("[STEP] Proceeding to next step")
            return True

        print("[STEP] Test aborted by user")
        return False


    # =================================================
    # STUB
    # =================================================
    def _stub(self, name: str):
        QMessageBox.information(self, name, f"{name}\n\n(Not implemented yet)")

    def _save_current_image(self):
        """Save the currently loaded image to 'New folder/ManualSaved'."""
        if self.current_image is None:
            QMessageBox.warning(self, "Save Image", "No image loaded.")
            return

        base_dir = Path("New folder")
        target_dir = base_dir / "ManualSaved"
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "Save Image", f"Failed to create folder: {e}")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out_path = target_dir / f"manual_{ts}.png"

        ok = cv2.imwrite(str(out_path), self.current_image)
        if ok:
            QMessageBox.information(self, "Save Image", f"Saved to:\n{out_path}")
        else:
            QMessageBox.warning(self, "Save Image", "Failed to save image.")
