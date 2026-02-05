
# app/main_window.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt, QSize, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QFont, QColor, QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QToolBar, QComboBox, QPushButton, QSplitter,
    QTableWidget, QTableWidgetItem, QMessageBox, QSlider, QSizePolicy, QMenu, QFrame, QToolButton, QDialog, QFileDialog
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
from ui.mark_symbol_set_dialog import MarkSymbolSetDialog
from ui.mark_parameters_dialog import MarkParametersDialog
from ui.mark_symbol_images_dialog import MarkSymbolImagesDialog
from ui.para_mark_config_dialog import ParaMarkConfigDialog
from ui.device_location_dialog import DeviceLocationDialog
from ui.pocket_location_dialog import PocketLocationDialog
from ui.device_inspection_dialog import DeviceInspectionDialog
from ui.inspection_debug_dialog import InspectionDebugDialog
from ui.alert_messages_dialog import AlertMessagesDialog
from ui.ignore_fail_count_dialog import IgnoreFailCountDialog
from ui.autorun_setting_dialog import AutoRunSettingDialog
from ui.encrypt_decrypt_dialog import EncryptDecryptDialog
from ui.autorun_withdraw_setting_dialog import AutoRunWithDrawSettingDialog
from ui.step_debug_dialog import StepDebugDialog
from ui.select_config_file_dialog import SelectConfigFileDialog
from ui.camera_configuration_dialog import CameraConfigurationDialog
from imaging.grab_service import GrabService
from device.camera_registry import CameraRegistry
from imaging.image_loader import ImageLoader
from inspection.alert_tracker import AlertTracker
from config.inspection_parameters import InspectionParameters
from config.inspection_parameters_io import load_parameters
from config.camera_parameters_io import load_camera_parameters, save_camera_parameters
from config.auto_run_setting_io import load_auto_run_setting
from imaging.pocket_teach_overlay import PocketTeachOverlay
from ui.image_rotation_dialog import ImageRotationDialog
from ui.enable_disable_inspection_dialog import EnableDisableInspectionDialog
from config.teach_store import load_teach_data
from config.teach_store import save_teach_data
from config.mark_inspection_io import load_mark_inspection_config
from imaging.mark_inspection import detect_marks
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
    MARK_ASK = 12
    MARK_ROI = 13
    MARK_BINARY = 14
    MARK_DETECT = 15
    SYMBOL_ROI = 16
    DONE = 8

class Station(str, Enum):
    FEED = "Feed"
    TOP = "Top"
    BOTTOM = "Bottom"
    PICKUP1 = "Pick-up 1"
    PICKUP2 = "Pick-up 2"
    BOTTOM_SEAL = "Bottom Sealing"
    TOP_SEAL = "Top Sealing"


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
        
        # Engineering menu flags - matching old C++ system
        self.camera_enable = False  # m_bCamEnable in old C++ (user toggle)
        self.camera_available = True  # m_bCamAvail in old C++ (camera connected)
        self.live_image_active = False  # m_bLiveImage in old C++ (live feed running)
        self.fail_track_active = False  # m_bFailTrack in old C++
        self.teaching_active = False  # m_bTeaching in old C++
        self.inspecting_active = False  # m_bInspecting in old C++
        self.calibrating_active = False  # m_bCalibrating in old C++
        self.device_calibrating = False  # m_bCalibratingDevice in old C++
        self.camera_setup_dialog_open = False  # m_bCamSetupDlgOpen in old C++
        self.runtime_display_enable = False  # m_RuntimeDisplayEnable in old C++
        self.inspection_enabled = True  # m_bEnableInsp in old C++ (default: enabled)
        self.cont_insp_active = False  # m_bContInsp in old C++ (Inspect Cycle)
        self.insp_saved_images_active = False  # m_bInspSavedImage in old C++
        self.insp_saved_images_draw_active = False  # m_bInspSavedImageDraw in old C++
        self.saved_images_step_active = False  # m_bSavedImagesStep in old C++
        self.saved_images_folder = Path("New folder")
        self.saved_images_list = []
        self.saved_images_index = 0
        
        # Configuration management
        self.current_config_name = "default"  # m_strConfigurationName in old C++
        
        # Camera settings per track (matching old C++ m_nAperture1, m_nGain, etc.)
        self.camera_settings = {
            1: {
                "shutter_1": 3,
                "shutter_2": 2,
                "gain": 4,
                "brightness": 1,
                "bytes_per_packet": 1072,
                "lc_intensity_1": 158,
                "lc_intensity_2": 255,
                "lc_intensity_3": 100,
                "lc_min_1": 0, "lc_max_1": 255,
                "lc_min_2": 0, "lc_max_2": 255,
                "lc_min_3": 0, "lc_max_3": 255,
                "red_gain": 1.0,
                "green_gain": 1.0,
                "blue_gain": 1.0,
            },
            2: {
                "shutter_1": 3,
                "shutter_2": 2,
                "gain": 4,
                "brightness": 1,
                "bytes_per_packet": 1072,
                "lc_intensity_1": 158,
                "lc_intensity_2": 255,
                "lc_intensity_3": 100,
                "lc_min_1": 0, "lc_max_1": 255,
                "lc_min_2": 0, "lc_max_2": 255,
                "lc_min_3": 0, "lc_max_3": 255,
                "red_gain": 1.0,
                "green_gain": 1.0,
                "blue_gain": 1.0,
            },
        }

        # Shared inspection flags (one set for all stations)
        self.inspection_parameters = load_parameters()
        self.shared_flags = self.inspection_parameters.flags

        self.grab_service=GrabService(self)
        self.image_loader = ImageLoader(self)
        self.inspect_cycle_timer = QTimer()
        self.inspect_cycle_timer.timeout.connect(self._on_inspect_cycle_tick)
        self.saved_images_timer = QTimer()
        self.saved_images_timer.timeout.connect(self._on_saved_images_tick)

        self.binary_mode = False
        self.binary_threshold = 75  # default (PDF example)
        self.is_teach_mode = False
        self.teach_overlay = None
        self.step_mode_enabled = False  # Step-by-step debug mode toggle
        self.alert_tracker = AlertTracker()  # Alert messages failure tracking
        
        # Debug flags - matches C++ m_lDebugFlag and m_bDebugSaveFailedImages
        from config.debug_flags_io import load_debug_flags
        self.debug_flag = load_debug_flags()  # Bitwise OR of all debug flags
        from config.debug_flags import DEBUG_SAVE_FAIL_IMAGE
        self.debug_save_failed_images = bool(self.debug_flag & DEBUG_SAVE_FAIL_IMAGE)
        # Sync step mode from debug flags
        from config.debug_flags import DEBUG_STEP_MODE
        self.step_mode_enabled = bool(self.debug_flag & DEBUG_STEP_MODE)
        
        self._teach_binary_prev_mode = None
        self._mark_teach_roi = None
        
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
            Station.PICKUP1: InspectionParameters(),
            Station.PICKUP2: InspectionParameters(),
            Station.BOTTOM_SEAL: InspectionParameters(),
            Station.TOP_SEAL: InspectionParameters(),
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
        
        # List to store disabled features that should be enabled only when ONLINE
        self.online_only_features = []
        # List to store features that should be enabled only when OFFLINE
        self.offline_only_features = []
        # Menu item references for enable/disable logic
        self.act_camera_enable = None
        self.act_camera_config = None
        
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
        act_end_lot.triggered.connect(self._end_lot)
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
        self.act_station_pickup1 = QAction("     Pick-up 1", self, checkable=True)
        self.act_station_pickup2 = QAction("     Pick-up 2", self, checkable=True)
        self.act_station_bottom_seal = QAction("     Bottom Sealing", self, checkable=True)
        self.act_station_top_seal = QAction("     Top Sealing", self, checkable=True)

        self.act_station_feed.triggered.connect(lambda: self._select_station(Station.FEED))
        self.act_station_top.triggered.connect(lambda: self._select_station(Station.TOP))
        self.act_station_bottom.triggered.connect(lambda: self._select_station(Station.BOTTOM))
        self.act_station_pickup1.triggered.connect(lambda: self._select_station(Station.PICKUP1))
        self.act_station_pickup2.triggered.connect(lambda: self._select_station(Station.PICKUP2))
        self.act_station_bottom_seal.triggered.connect(lambda: self._select_station(Station.BOTTOM_SEAL))
        self.act_station_top_seal.triggered.connect(lambda: self._select_station(Station.TOP_SEAL))

        for act in (
            self.act_station_feed,
            self.act_station_top,
            self.act_station_bottom,
            self.act_station_pickup1,
            self.act_station_pickup2,
            self.act_station_bottom_seal,
            self.act_station_top_seal
        ):
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
        self.act_binarise = QAction("Binarise Image", self)
        self.act_binarise.setCheckable(True)
        self.act_binarise.setShortcut("V")  # Match old C++ shortcut
        self.act_binarise.triggered.connect(self._toggle_binarise)
        m_engineering.addAction(self.act_binarise)

        m_engineering.addSeparator()
        
        # Zoom section with subtle header
        zoom_header = QAction("━━━━━━ ZOOM ━━━━━━", self)
        zoom_header.setEnabled(False)
        zoom_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        m_engineering.addAction(zoom_header)
        
        act_zoom_in = QAction("     Zoom In", self)
        act_zoom_in.setShortcut("I")  # Match old C++ shortcut
        act_zoom_in.triggered.connect(self._zoom_in)
        m_engineering.addAction(act_zoom_in)
        
        act_zoom_fit = QAction("     Zoom Fit", self)
        act_zoom_fit.setShortcut("N")  # Match old C++ shortcut
        act_zoom_fit.triggered.connect(self._zoom_fit)
        m_engineering.addAction(act_zoom_fit)
        
        act_zoom_out = QAction("     Zoom Out", self)
        act_zoom_out.setShortcut("O")  # Match old C++ shortcut
        act_zoom_out.triggered.connect(self._zoom_out)
        m_engineering.addAction(act_zoom_out)
        
        m_engineering.addSeparator()
        
        # File operations
        file_header = QAction("━━━━ FILE ━━━━", self)
        file_header.setEnabled(False)
        file_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        m_engineering.addAction(file_header)
        
        act_load_image = QAction("     Load Image From Disk", self)
        act_load_image.setEnabled(False)  # Only in OFFLINE mode
        act_load_image.triggered.connect(self.image_loader.load_from_disk)
        m_engineering.addAction(act_load_image)
        self.offline_only_features.append(act_load_image)

        act_save_image = QAction("     Save Image To Disk", self)
        act_save_image.setEnabled(False)  # Only in OFFLINE mode
        act_save_image.triggered.connect(self._save_current_image)
        m_engineering.addAction(act_save_image)
        self.offline_only_features.append(act_save_image)
        
        m_engineering.addSeparator()
        
        # Disabled features with special visual treatment
        disabled_header = QAction("━━━ OFFLINE ONLY ━━━", self)
        disabled_header.setEnabled(False)
        disabled_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        m_engineering.addAction(disabled_header)
        
        font = QFont("Segoe UI", 9)
        font.setItalic(True)
        
        act_camera_enable = QAction("     🔒 Camera Enable", self)
        act_camera_enable.setCheckable(True)  # Checkable like old C++
        act_camera_enable.setEnabled(False)
        act_camera_enable.setFont(font)
        act_camera_enable.triggered.connect(self._toggle_camera_enable)
        m_engineering.addAction(act_camera_enable)
        self.offline_only_features.append(act_camera_enable)
        self.act_camera_enable = act_camera_enable  # Store reference
        
        act_runtime_display = QAction("     🔒 RunTime Display Enable", self)
        act_runtime_display.setCheckable(True)  # Checkable like old C++
        act_runtime_display.setEnabled(True)  # Always enabled (unless SEM enabled)
        act_runtime_display.setFont(font)
        act_runtime_display.triggered.connect(self._toggle_runtime_display)
        m_engineering.addAction(act_runtime_display)
        self.act_runtime_display = act_runtime_display  # Store reference
        # Note: Runtime Display only depends on SEM enabled status, not ONLINE/OFFLINE
        
        act_camera_aoi = QAction("     🔒 Camera AOI Resize Mode", self)
        act_camera_aoi.setShortcut("Ctrl+R")  # Match old C++ shortcut
        act_camera_aoi.setEnabled(False)
        act_camera_aoi.setFont(font)
        act_camera_aoi.triggered.connect(self._camera_aoi_resize)
        m_engineering.addAction(act_camera_aoi)
        self.offline_only_features.append(act_camera_aoi)

        # ---------- Configuration ----------
        m_config = mb.addMenu(" Configuration ")
        m_config.setStyleSheet(m_production.styleSheet())
        
        # Config file operations
        config_header = QAction("━━━ CONFIG FILES ━━━", self)
        config_header.setEnabled(False)
        config_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        m_config.addAction(config_header)
        
        act_select_config = QAction("     Select Config File", self)
        act_select_config.triggered.connect(self._select_config_file)
        m_config.addAction(act_select_config)
        
        act_save_config = QAction("     Save Config As", self)
        act_save_config.triggered.connect(self._save_config_as)
        m_config.addAction(act_save_config)
        
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
        m_mark.addAction(QAction("Mark Symbol Set", self, triggered=self._open_mark_symbol_set_dialog))
        m_mark.addAction(QAction("Mark Parameters", self, triggered=self._open_mark_parameters_dialog))
        m_mark.addAction(QAction("Mark Symbol Images", self, triggered=self._open_mark_symbol_images_dialog))
        m_config.addMenu(m_mark)

        m_config.addSeparator()
        
        # Disabled configuration items
        system_header = QAction("⚙️ SYSTEM SETTINGS (DISABLED)", self)
        system_header.setEnabled(False)
        system_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_config.addAction(system_header)
        
        act_inspection_disable = QAction("     ⚠️ Enable / Disable Inspection", self)
        act_inspection_disable.setCheckable(True)
        act_inspection_disable.setChecked(True)  # Default: enabled
        act_inspection_disable.setEnabled(True)  # Always enabled (per old C++)
        act_inspection_disable.triggered.connect(self._toggle_inspection_enable)
        font = QFont("Segoe UI", 9)
        font.setItalic(True)
        act_inspection_disable.setFont(font)
        m_config.addAction(act_inspection_disable)
        # Note: Old C++ always keeps this ENABLED so user can toggle anytime
        
        act_camera_config = QAction("     ⚠️ Camera Configuration", self)
        act_camera_config.setEnabled(False)
        act_camera_config.setFont(font)
        act_camera_config.triggered.connect(self._open_camera_configuration_dialog)
        m_config.addAction(act_camera_config)
        self.act_camera_config = act_camera_config  # Store reference
        self.act_inspection_enable = act_inspection_disable  # Store reference

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
        act_inspect_cycle_single = QAction("Single Image", self)
        act_inspect_cycle_single.setCheckable(True)
        act_inspect_cycle_single.triggered.connect(self._toggle_inspect_cycle_single)
        m_cycle.addAction(act_inspect_cycle_single)
        m_run.addMenu(m_cycle)
        self.act_inspect_cycle_single = act_inspect_cycle_single

        # Inspect Saved Images submenu
        m_saved = QMenu("💾 Inspect Saved Images", self)
        m_saved.setStyleSheet(m_mark.styleSheet())
        
        # AutoRun actions with special styling
        autorun_header = QAction("Auto Run Options", self)
        autorun_header.setEnabled(False)
        autorun_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_saved.addAction(autorun_header)
        
        act_saved_autorun = QAction("     AutoRun", self)
        act_saved_autorun.setCheckable(True)
        act_saved_autorun.triggered.connect(self._toggle_inspect_saved_images_autorun)
        m_saved.addAction(act_saved_autorun)

        act_saved_autorun_draw = QAction("     AutoRun With Draw", self)
        act_saved_autorun_draw.setCheckable(True)
        act_saved_autorun_draw.triggered.connect(self._toggle_inspect_saved_images_autorun_draw)
        m_saved.addAction(act_saved_autorun_draw)
        
        m_saved.addSeparator()
        
        standard_header = QAction("Standard Operations", self)
        standard_header.setEnabled(False)
        standard_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_saved.addAction(standard_header)
        
        act_saved_step = QAction("     Step", self)
        act_saved_step.setCheckable(True)
        act_saved_step.triggered.connect(self._run_saved_images_step)
        m_saved.addAction(act_saved_step)

        act_saved_set_folder = QAction("     Set Stored Image Folder", self)
        act_saved_set_folder.triggered.connect(self._set_saved_images_folder)
        m_saved.addAction(act_saved_set_folder)
        m_run.addMenu(m_saved)
        self.act_saved_autorun = act_saved_autorun
        self.act_saved_autorun_draw = act_saved_autorun_draw
        self.act_saved_step = act_saved_step
        self.act_saved_set_folder = act_saved_set_folder

        # ---------- Diagnostic ----------
        m_diag = mb.addMenu(" Diagnostic ")
        m_diag.setStyleSheet(m_production.styleSheet())
        
        # Diagnostic tools with icon
        diag_header = QAction("🔧 DIAGNOSTIC TOOLS", self)
        diag_header.setEnabled(False)
        diag_header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        m_diag.addAction(diag_header)
        
        act_inspection_debug = QAction("     Inspection", self)
        act_inspection_debug.triggered.connect(self._open_inspection_debug_dialog)
        m_diag.addAction(act_inspection_debug)

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
        act_step_mode.setChecked(self.step_mode_enabled)
        act_step_mode.triggered.connect(self._toggle_step_mode)
        m_diag.addAction(act_step_mode)
        self.act_step_mode = act_step_mode
        m_diag.addAction(
            QAction("     Alert Messages", self, triggered=self._open_alert_messages_dialog)
        )
        m_diag.addAction(QAction("     Encrypt / Decrypt Images", self, triggered=self._open_encrypt_decrypt_dialog))
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
            self.act_station_pickup1.setChecked(self.state.station == Station.PICKUP1)
            self.act_station_pickup2.setChecked(self.state.station == Station.PICKUP2)
            self.act_station_bottom_seal.setChecked(self.state.station == Station.BOTTOM_SEAL)
            self.act_station_top_seal.setChecked(self.state.station == Station.TOP_SEAL)

    

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
        """
        Simple 5-station camera display layout (step 1)
        """
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Track label (for backward compatibility)
        self.track_label = QLabel()
        self.track_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #333333;
                padding: 4px 0px;
            }
        """)
        main_layout.addWidget(self.track_label)
        
        # 5 Station Camera Display - Horizontal Layout
        camera_row = QHBoxLayout()
        camera_row.setContentsMargins(0, 0, 0, 0)
        camera_row.setSpacing(4)
        
        # Station configuration: name and color indicator
        stations = [
            {"name": "Top Index", "label": "Station 1", "color": "#4A90E2"},  # Blue
            {"name": "Bottom Index", "label": "Station 2", "color": "#4A90E2"},  # Blue
            {"name": "Feed", "label": "Station 3", "color": "#4A90E2"},  # Blue
            {"name": "Pick Up 1", "label": "Station 4", "color": "#E74C3C"},  # Red
            {"name": "Pick Up 2", "label": "Station 5", "color": "#E74C3C"},  # Red
        ]
        
        self.camera_panels = {}
        
        for idx, station in enumerate(stations):
            doc_index = idx + 1
            # Camera panel container
            panel = QWidget()
            panel.setStyleSheet("""
                QWidget {
                    background: white;
                    border: 2px solid #CCCCCC;
                    border-radius: 4px;
                }
            """)
            panel_layout = QVBoxLayout(panel)
            panel_layout.setContentsMargins(0, 0, 0, 0)
            panel_layout.setSpacing(0)
            
            # Colored header bar
            header = QWidget()
            header.setFixedHeight(24)
            header.setStyleSheet(f"""
                QWidget {{
                    background: {station['color']};
                    border-radius: 2px 2px 0px 0px;
                }}
            """)
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(6, 0, 6, 0)
            header_layout.setSpacing(0)
            
            station_label = QLabel(station['label'])
            station_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            header_layout.addWidget(station_label)
            header_layout.addStretch()
            
            panel_layout.addWidget(header)
            
            # Camera image area
            image_area = QLabel()
            image_area.setAlignment(Qt.AlignCenter)
            image_area.setMinimumSize(180, 180)
            image_area.setStyleSheet("""
                QLabel {
                    background: #1a1a1a;
                    color: #666;
                    font-size: 10px;
                }
            """)
            image_area.setText("")  # Will be populated with camera image
            panel_layout.addWidget(image_area, 1)
            
            # Store reference
            self.camera_panels[doc_index] = {
                "panel": panel,
                "image": image_area,
                "header": header,
                "label": station_label
            }
            if doc_index == 1:
                self.image_label = image_area
            
            camera_row.addWidget(panel)
        
        # Add camera row to main layout
        camera_container = QWidget()
        camera_container.setLayout(camera_row)
        main_layout.addWidget(camera_container, 1)
        
        # Bottom section: left two cameras + right tables
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(8)
        
        # Left column: two additional cameras (stacked)
        left_cam_col = QVBoxLayout()
        left_cam_col.setContentsMargins(0, 0, 0, 0)
        left_cam_col.setSpacing(8)
        
        extra_cams = [
            {"name": "Track 6", "label": "Station 6", "color": "#4A90E2"},
            {"name": "Track 7", "label": "Station 7", "color": "#4A90E2"},
        ]
        
        for offset, station in enumerate(extra_cams, start=6):
            panel = QWidget()
            panel.setStyleSheet("""
                QWidget {
                    background: white;
                    border: 2px solid #CCCCCC;
                    border-radius: 4px;
                }
            """)
            panel_layout = QVBoxLayout(panel)
            panel_layout.setContentsMargins(0, 0, 0, 0)
            panel_layout.setSpacing(0)
            
            header = QWidget()
            header.setFixedHeight(22)
            header.setStyleSheet(f"""
                QWidget {{
                    background: {station['color']};
                    border-radius: 2px 2px 0px 0px;
                }}
            """)
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(6, 0, 6, 0)
            header_layout.setSpacing(0)
            
            station_label = QLabel(station['label'])
            station_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }
            """)
            header_layout.addWidget(station_label)
            header_layout.addStretch()
            
            panel_layout.addWidget(header)
            
            image_area = QLabel()
            image_area.setAlignment(Qt.AlignCenter)
            image_area.setMinimumSize(220, 150)
            image_area.setStyleSheet("""
                QLabel {
                    background: #1a1a1a;
                    color: #666;
                    font-size: 10px;
                }
            """)
            image_area.setText("")
            panel_layout.addWidget(image_area, 1)
            
            self.camera_panels[offset] = {
                "panel": panel,
                "image": image_area,
                "header": header,
                "label": station_label
            }
            
            left_cam_col.addWidget(panel)
        
        bottom_row.addLayout(left_cam_col, 1)
        
        # Right column: threshold + tables
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(8)
        
        # Binary Threshold Section (hidden by default)
        self.threshold_container = QWidget()
        self.threshold_container.setVisible(False)
        threshold_layout = QVBoxLayout(self.threshold_container)
        threshold_layout.setContentsMargins(8, 8, 8, 8)
        threshold_layout.setSpacing(6)
        
        threshold_header = QLabel("Binary Threshold Settings")
        threshold_header.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #555;
            }
        """)
        threshold_layout.addWidget(threshold_header)
        
        slider_row = QHBoxLayout()
        slider_row.setContentsMargins(0, 0, 0, 0)
        slider_row.setSpacing(8)
        
        self.binary_text_label = QLabel("Threshold:")
        self.binary_text_label.setStyleSheet("QLabel { font-size: 11px; min-width: 70px; }")
        
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
            QSlider::handle:horizontal {
                background: #4A90E2;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
        """)
        self.binary_slider.valueChanged.connect(self._on_binary_threshold_changed)
        
        self.binary_value_label = QLabel(str(self.binary_threshold))
        self.binary_value_label.setFixedWidth(50)
        self.binary_value_label.setAlignment(Qt.AlignCenter)
        self.binary_value_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                font-weight: bold;
                color: #4A90E2;
                background: #F0F4F8;
                border: 1px solid #D0D7E2;
                border-radius: 3px;
                padding: 2px;
            }
        """)
        
        slider_row.addWidget(self.binary_text_label)
        slider_row.addWidget(self.binary_slider)
        slider_row.addWidget(self.binary_value_label)
        threshold_layout.addLayout(slider_row)
        
        right_col.addWidget(self.threshold_container)
        
        # Tables
        tables_container = QWidget()
        tables_layout = QVBoxLayout(tables_container)
        tables_layout.setContentsMargins(0, 0, 0, 0)
        tables_layout.setSpacing(8)
        
        summary_rows = [
            "UNIT INSPECTED",
            "UNIT PASSED",
            "UNIT FAILED",
            "PASS YIELD %",
            "FINAL YIELD %",
            "ENABLE/DISABLE STN",
            "LAST 20K UNIT FAILED",
            "LAST 20K FAIL YIELD %",
            "CONFIG NAME",
            "LOT NO INFO",
        ]
        track_headers = [f"Track{i}" for i in range(1, 8)]
        self.top_tbl = QTableWidget(len(summary_rows), 1 + len(track_headers))
        self.top_tbl.setHorizontalHeaderLabels(["Summary"] + track_headers)
        self.top_tbl.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #DEE2E6;
                border-radius: 3px;
                gridline-color: #E9ECEF;
                font-size: 10px;
                alternate-background-color: #F8F9FA;
            }
            QHeaderView::section {
                background: #4A90E2;
                color: white;
                font-weight: bold;
                padding: 4px;
                border: none;
                font-size: 10px;
            }
        """)
        self.top_tbl.horizontalHeader().setStretchLastSection(True)
        self.top_tbl.verticalHeader().setVisible(False)
        self.top_tbl.setMaximumHeight(120)
        for row_idx, label in enumerate(summary_rows):
            item = QTableWidgetItem(label)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.top_tbl.setItem(row_idx, 0, item)
        tables_layout.addWidget(self.top_tbl)
        
        defects_rows = [
            "Pkg Location",
            "Body Length",
            "Body Width",
            "Terminal Length",
            "Terminal Width",
            "Term to Term",
            "Body Smear",
            "Body Stain",
            "Edge Chipoff",
            "Terminal Poggo",
            "Terminal Incomplete",
            "Oxidation",
            "Terminal Chipoff",
            "Body Color",
            "Mark",
            "Mark Color",
        ]
        defect_headers = ["Defects"]
        for i in range(1, 8):
            defect_headers.extend(["Qty", "%"])
        self.bot_tbl = QTableWidget(len(defects_rows), len(defect_headers))
        self.bot_tbl.setHorizontalHeaderLabels(defect_headers)
        self.bot_tbl.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #DEE2E6;
                border-radius: 3px;
                gridline-color: #E9ECEF;
                font-size: 10px;
                alternate-background-color: #F8F9FA;
            }
            QHeaderView::section {
                background: #5CB85C;
                color: white;
                font-weight: bold;
                padding: 4px;
                border: none;
                font-size: 10px;
            }
        """)
        self.bot_tbl.horizontalHeader().setStretchLastSection(True)
        self.bot_tbl.verticalHeader().setVisible(False)
        for row_idx, label in enumerate(defects_rows):
            item = QTableWidgetItem(label)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.bot_tbl.setItem(row_idx, 0, item)
        tables_layout.addWidget(self.bot_tbl)

        track_colors = [
            "#9EC7FF",  # Track1 light blue
            "#9AA3AD",  # Track2 gray-blue
            "#8E8742",  # Track3 olive
            "#9EC7FF",  # Track4 light blue
            "#9AA3AD",  # Track5 gray-blue
            "#8E8742",  # Track6 olive
            "#9EC7FF",  # Track7 light blue
        ]

        def apply_track_bands(table, start_col, columns_per_track):
            for track_idx, color in enumerate(track_colors):
                for col in range(columns_per_track):
                    col_idx = start_col + (track_idx * columns_per_track) + col
                    for row in range(table.rowCount()):
                        existing = table.item(row, col_idx)
                        if existing is None:
                            existing = QTableWidgetItem("")
                            existing.setFlags(existing.flags() & ~Qt.ItemIsEditable)
                            table.setItem(row, col_idx, existing)
                        existing.setBackground(QColor(color))

        apply_track_bands(self.top_tbl, 1, 1)
        apply_track_bands(self.bot_tbl, 1, 2)
        
        right_col.addWidget(tables_container, 1)
        
        bottom_row.addLayout(right_col, 2)
        main_layout.addLayout(bottom_row, 1)
        
        self.multi_track_tables = True
        self.setCentralWidget(main_widget)
    
    def _create_camera_displays(self, parent_layout):
        """
        Dynamically create camera display panels based on registry configuration.
        If multiple cameras are configured, creates a grid of camera views.
        If only one camera, creates single large view (backward compatible).
        """
        # Get camera configuration from registry
        camera_count = self.grab_service.get_camera_count()
        cameras = self.grab_service.get_configured_cameras()
        
        if camera_count == 0:
            # No cameras configured - create single placeholder view
            print("[UI] No cameras configured - creating placeholder view")
            self._create_single_camera_view(parent_layout, "No Camera Configured")
            
        elif camera_count == 1:
            # Single camera - use large view (backward compatible)
            doc_idx, (station, serial) = list(cameras.items())[0]
            print(f"[UI] Single camera mode: Doc{doc_idx} ({station})")
            self._create_single_camera_view(parent_layout, f"{station} (Doc{doc_idx})")
            
        else:
            # Multiple cameras - create grid layout
            print(f"[UI] Creating grid for {camera_count} cameras")
            self._create_camera_grid(parent_layout, cameras)
    
    def _create_single_camera_view(self, parent_layout, title):
        """Create single large camera view (legacy mode)"""
        self.image_label = QLabel()
        self.image_label.setMinimumSize(400, 300)
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
        self.image_label.mousePressEvent = self._on_image_clicked
        parent_layout.addWidget(self.image_label, 1)
        
        # Store in camera_panels for unified access
        self.camera_panels[1] = {"label": self.image_label, "title": title}
    
    def _create_camera_grid(self, parent_layout, cameras):
        """Create grid of camera panels based on camera count"""
        from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QFrame
        
        # Create container for camera grid
        camera_container = QWidget()
        grid_layout = QGridLayout(camera_container)
        grid_layout.setSpacing(8)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Calculate grid dimensions
        camera_count = len(cameras)
        if camera_count <= 2:
            cols = 2
        elif camera_count <= 4:
            cols = 2
        elif camera_count <= 6:
            cols = 3
        else:  # 7 cameras
            cols = 3
        
        rows = (camera_count + cols - 1) // cols
        
        # Create camera panel for each configured camera
        for idx, (doc_idx, (station, serial)) in enumerate(cameras.items()):
            row = idx // cols
            col = idx % cols
            
            # Create camera panel frame
            panel_frame = QFrame()
            panel_frame.setStyleSheet("""
                QFrame {
                    background: #2C3E50;
                    border: 2px solid #34495E;
                    border-radius: 4px;
                }
            """)
            panel_layout = QVBoxLayout(panel_frame)
            panel_layout.setContentsMargins(4, 4, 4, 4)
            panel_layout.setSpacing(2)
            
            # Camera title label
            title_label = QLabel(f"Doc{doc_idx}: {station}")
            title_label.setStyleSheet("""
                QLabel {
                    color: #ECF0F1;
                    font-size: 11px;
                    font-weight: bold;
                    background: transparent;
                    border: none;
                    padding: 2px;
                }
            """)
            title_label.setAlignment(Qt.AlignCenter)
            panel_layout.addWidget(title_label)
            
            # Camera image label
            image_label = QLabel()
            image_label.setMinimumSize(200, 150)
            image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            image_label.setStyleSheet("""
                QLabel {
                    background: #000000;
                    border: 1px solid #555555;
                    border-radius: 2px;
                }
            """)
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setScaledContents(False)
            panel_layout.addWidget(image_label, 1)
            
            # Status label
            status_label = QLabel(f"SN: {serial[-8:]}")  # Show last 8 chars of serial
            status_label.setStyleSheet("""
                QLabel {
                    color: #95A5A6;
                    font-size: 9px;
                    background: transparent;
                    border: none;
                    padding: 2px;
                }
            """)
            status_label.setAlignment(Qt.AlignCenter)
            panel_layout.addWidget(status_label)
            
            # Add panel to grid
            grid_layout.addWidget(panel_frame, row, col)
            
            # Store references
            self.camera_panels[doc_idx] = {
                "label": image_label,
                "title": title_label,
                "status": status_label,
                "frame": panel_frame
            }
            
            # Set first camera as primary for backward compatibility
            if idx == 0:
                self.image_label = image_label
        
        # Add grid to parent layout
        parent_layout.addWidget(camera_container, 1)

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
        """
        Update menu items based on system state matching old C++ logic.
        
        From old C++ ChipCapacitorDoc::OnUpdateEngrCamEnable:
            pCmdUI->Enable(!m_bLiveImage && !m_bFailTrack && 
                          m_bCamAvail && !m_bOnLine);
                          
        From old C++ ChipCapacitorDoc::OnUpdateConfigCamsetup:
            pCmdUI->Enable(!m_bCamSetupDlgOpen && m_bCamEnable && 
                          m_bCamAvail && !m_bFailTrack && 
                          !m_bOnLine && !m_bTeaching && 
                          !m_bInspecting && !m_bCalibrating && 
                          !m_bCalibratingDevice);
        """
        offline = self.state.run_state == RunState.OFFLINE
        online = self.state.run_state == RunState.ONLINE
        
        # Basic run buttons
        self.act_teach.setEnabled(offline)
        self.act_test.setEnabled(offline)
        self.act_start.setEnabled(not offline)
        self.act_end.setEnabled(offline)

        # Camera LIVE and GRAB allowed only ONLINE
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
        
        # ========== OLD C++ MENU ENABLE/DISABLE LOGIC ==========
        
        # Enable/Disable Camera menu (ID_ENGR_CAM_ENABLE)
        # Enabled when: !LiveImage && !FailTrack && CamAvail && !OnLine
        if self.act_camera_enable:
            camera_enable_allowed = (
                not self.live_image_active and
                not self.fail_track_active and
                self.camera_available and
                offline  # !m_bOnLine = offline
            )
            self.act_camera_enable.setEnabled(camera_enable_allowed)
            self.act_camera_enable.setChecked(self.camera_enable)
        
        # Camera Configuration menu (ID_CONFIG_CAMSETUP)
        # Enabled when: !DlgOpen && CamEnable && CamAvail && !FailTrack && 
        #              !OnLine && !Teaching && !Inspecting && !Calibrating && !DeviceCalib
        if self.act_camera_config:
            camera_config_allowed = (
                not self.camera_setup_dialog_open and
                self.camera_enable and
                self.camera_available and
                not self.fail_track_active and
                offline and  # !m_bOnLine
                not self.teaching_active and
                not self.inspecting_active and
                not self.calibrating_active and
                not self.device_calibrating
            )
            self.act_camera_config.setEnabled(camera_config_allowed)

            # Debug output
            if not camera_config_allowed:
                reasons = []
                if self.camera_setup_dialog_open:
                    reasons.append("Dialog already open")
                if not self.camera_enable:
                    reasons.append("Camera not ENABLED (check Engineering → Camera Enable)")
                if not self.camera_available:
                    reasons.append("Camera not available")
                if self.fail_track_active:
                    reasons.append("Fail track active")
                if not offline:
                    reasons.append("System not OFFLINE (switch to OFFLINE mode)")
                if self.teaching_active:
                    reasons.append("Teaching active")
                if self.inspecting_active:
                    reasons.append("Inspecting active")
                if self.calibrating_active:
                    reasons.append("Calibrating active")
                if self.device_calibrating:
                    reasons.append("Device calibrating")

                # Print to console for debugging
                print(f"\n🔴 Camera Configuration DISABLED - Reasons:")
                for reason in reasons:
                    print(f"   • {reason}")
                print(f"\n📊 Current Flags:")
                print(f"   offline={offline}, camera_enable={self.camera_enable}, camera_available={self.camera_available}")
                print()
        
        # Enable/Disable Inspection checkbox (ID_CONFIGURATION_ENABLEDISABLEINSPECTION)
        # Old C++: pCmdUI->SetCheck(m_bEnableInsp); pCmdUI->Enable(FALSE);
        # Always enabled, just reflects current state
        if self.act_inspection_enable:
            self.act_inspection_enable.setChecked(self.inspection_enabled)
            # Old C++ keeps this always enabled (user can toggle anytime)
            self.act_inspection_enable.setEnabled(True)

        # Inspect Cycle → Single Image (ID_RUN_INSPECTCYCLE_SINGLEIMAGE)
        if hasattr(self, "act_inspect_cycle_single"):
            inspect_cycle_allowed = (
                not self.live_image_active and
                not self.fail_track_active and
                offline and
                not self.teaching_active and
                not self.calibrating_active and
                not self.insp_saved_images_active and
                not self.insp_saved_images_draw_active
            )
            self.act_inspect_cycle_single.setEnabled(inspect_cycle_allowed)
            self.act_inspect_cycle_single.setChecked(self.cont_insp_active)

        # Inspect Saved Images actions
        if hasattr(self, "act_saved_autorun"):
            saved_images_allowed = (
                not self.live_image_active and
                not self.fail_track_active and
                not self.cont_insp_active and
                offline and
                not self.teaching_active and
                not self.inspecting_active and
                not self.calibrating_active and
                (not self.insp_saved_images_active or
                 not self.insp_saved_images_draw_active or
                 not self.saved_images_step_active)
            )
            self.act_saved_autorun.setEnabled(saved_images_allowed)
            self.act_saved_autorun.setChecked(self.insp_saved_images_active)

        if hasattr(self, "act_saved_autorun_draw"):
            saved_images_allowed = (
                not self.live_image_active and
                not self.fail_track_active and
                not self.cont_insp_active and
                offline and
                not self.teaching_active and
                not self.inspecting_active and
                not self.calibrating_active and
                (not self.insp_saved_images_active or
                 not self.insp_saved_images_draw_active or
                 not self.saved_images_step_active)
            )
            self.act_saved_autorun_draw.setEnabled(saved_images_allowed)
            self.act_saved_autorun_draw.setChecked(self.insp_saved_images_draw_active)

        if hasattr(self, "act_saved_step"):
            saved_step_allowed = (
                not self.live_image_active and
                not self.fail_track_active and
                not self.cont_insp_active and
                offline and
                not self.teaching_active and
                not self.inspecting_active and
                not self.calibrating_active and
                not self.insp_saved_images_active and
                not self.insp_saved_images_draw_active
            )
            self.act_saved_step.setEnabled(saved_step_allowed)
            self.act_saved_step.setChecked(self.saved_images_step_active)
            
            # Store debug info for tooltip
            if reasons:
                self.act_camera_config.setToolTip("Disabled because:\n• " + "\n• ".join(reasons))
        else:
            self.act_camera_config.setToolTip("")
        
        # Enable ONLINE-only features (only when ONLINE)
        for feature in self.online_only_features:
            feature.setEnabled(online)
        
        # Enable OFFLINE-only features (only when OFFLINE)
        for feature in self.offline_only_features:
            feature.setEnabled(offline)
        
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
    
    def _end_lot(self):
        """
        End Lot functionality (matching old C++ OnProductionCloselot).
        
        Operations performed:
        1. Mark lot as closed (m_bLotOpened = FALSE)
        2. Reset to production mode if online (OnProductionmode)
        3. Record end time (strEndLotTime)
        4. Write lot summary file (WriteLotSummaryToFile)
        5. Save online pass/fail images (SaveOnlinePassFailImages)
        6. Copy configuration files to lot directory
        7. Reset scan numbers (m_strScanNo, m_strReelMachScanNo, m_strReelOrderNo)
        8. Display results if pocket post-seal enabled
        9. Auto-open next lot if enabled (m_nDisplayOpenLot)
        """
        from config.lot_information_io import load_lot_info, save_lot_info
        from datetime import datetime
        from pathlib import Path
        import shutil
        
        try:
            # 1. Mark lot as closed
            lot_opened = False
            
            # 2. Reset to production mode if online
            if self.state.run_state.name == "ONLINE":
                # Would call OnProductionmode() equivalent
                pass
            
            # 3. Get current time and record end time
            now = datetime.now()
            end_lot_time = now.strftime("%d/%m/%Y  %H:%M:%S")
            
            # 4. Load lot info
            lot_info = load_lot_info()
            
            # 5. Write lot summary file (create lot summary directory if needed)
            lot_summary_root = Path("lot_summaries")
            lot_summary_root.mkdir(exist_ok=True)
            
            lot_start_time = now.strftime("%d%m%Y_%H%M%S")
            lot_summary_file = lot_summary_root / f"{lot_start_time}_{lot_info.lot_id}_summary.txt"
            
            summary_content = f"""
╔════════════════════════════════════════════════════════════════╗
║                        LOT SUMMARY REPORT                      ║
╚════════════════════════════════════════════════════════════════╝

Lot Information:
  Machine ID:        {lot_info.machine_id}
  Operator ID:       {lot_info.operator_id}
  Order No:          {lot_info.order_no}
  Lot ID:            {lot_info.lot_id}
  Lot Size:          {lot_info.lot_size}
  Package Type:      {lot_info.package_type}

Timing:
  Start Time:        (recorded at open lot)
  End Time:          {end_lot_time}

Save Images:
  Pass Images:       {lot_info.save_images.get('pass', False)}
  Fail Images:       {lot_info.save_images.get('fail', False)}
  All Images:        {lot_info.save_images.get('all', False)}

Status: Lot Closed

═══════════════════════════════════════════════════════════════════
"""
            
            with lot_summary_file.open("w") as f:
                f.write(summary_content)
            
            # 6. Save online pass/fail images (if image directories exist)
            # This would copy images from camera/inspection folders
            if lot_info.save_images.get('pass') or lot_info.save_images.get('fail'):
                images_dir = lot_summary_root / f"{lot_start_time}_{lot_info.lot_id}_images"
                images_dir.mkdir(exist_ok=True)
                # Image copying would happen here if folders are available
            
            # 7. Copy configuration files to lot directory
            config_files = [
                "inspection_parameters.json",
                "pocket_params.json",
                "device_location_setting.json"
            ]
            
            lot_dir = lot_summary_root / f"{lot_start_time}_{lot_info.lot_id}"
            lot_dir.mkdir(exist_ok=True)
            
            for config_file in config_files:
                config_path = Path(config_file)
                if config_path.exists():
                    try:
                        shutil.copy(config_path, lot_dir / config_file)
                    except Exception as e:
                        print(f"Warning: Could not copy {config_file}: {e}")
            
            # 8. Reset scan numbers and lot information
            lot_info.scan_no = "noid"
            lot_info.lot_id = ""
            lot_info.lot_size = ""
            
            # 9. Save reset state to JSON
            save_lot_info(lot_info)
            
            # 10. Show confirmation with lot summary file location
            result_msg = f"""Lot closed successfully!

Summary Report: {lot_summary_file}
Lot Directory: {lot_dir}

All lot counters reset and ready for next lot."""
            
            QMessageBox.information(self, "Lot Closed", result_msg)
            
            # 11. Auto-open next lot if enabled (m_nDisplayOpenLot equivalent)
            # This would be a configuration option
            # For now, user can manually open next lot
            
        except Exception as e:
            QMessageBox.critical(self, "Error Closing Lot", f"Error during lot closure:\n{str(e)}")
        
    def _open_body_color_dialog(self):
        dlg = BodyColorDialog(self)
        dlg.exec()
        
    def _open_terminal_color_dialog(self):
        dlg = TerminalColorDialog(self)
        dlg.exec()
        
    def _open_mark_color_dialog(self):
        dlg = MarkColorDialog(self)
        dlg.exec()

    def _open_mark_symbol_set_dialog(self):
        """Open Mark Symbol Set Setting dialog"""
        dlg = MarkSymbolSetDialog(self)
        if dlg.exec():
            # Configuration is already saved by the dialog
            QMessageBox.information(
                self,
                "Mark Symbol Set",
                "Mark Symbol Set configuration saved successfully."
            )
    
    def _open_mark_parameters_dialog(self):
        """Open Mark Inspect Parameters dialog"""
        dlg = MarkParametersDialog(self)
        if dlg.exec():
            # Configuration is already saved by the dialog
            QMessageBox.information(
                self,
                "Mark Parameters",
                "Mark Parameters configuration saved successfully."
            )

    def _open_mark_symbol_images_dialog(self):
        """Open Mark Symbol Images dialog to teach symbol images"""
        if self.current_image is None:
            QMessageBox.warning(self, "Mark Symbol Images", "No image loaded.")
            return
        self.mark_symbol_dialog = MarkSymbolImagesDialog(self, self.current_image)
        self.mark_symbol_dialog.symbol_captured.connect(self._start_symbol_image_teaching)
        self.mark_symbol_dialog.exec()

    def _start_symbol_image_teaching(self, symbol: str, image: np.ndarray):
        """
        Start symbol image teaching workflow.
        User clicks a symbol -> gets asked about rotation -> draws ROI -> captures image
        """
        if image is None or image.size == 0:
            QMessageBox.warning(self, "Symbol Teaching", f"No image provided for symbol '{symbol}'.")
            return
        
        # Show message about ROI selection
        QMessageBox.information(
            self,
            f"Teach Symbol '{symbol}'",
            f"Focus the Red Box on the symbol '{symbol}' and press 'Next'."
        )
        
        # Start ROI selection for symbol
        self.current_teach_symbol = symbol
        self.teach_phase = TeachPhase.SYMBOL_ROI
        
        self.teach_overlay = PocketTeachOverlay(self.image_label, self)
        self.teach_overlay.setGeometry(self.image_label.rect())
        self.teach_overlay.show()
        self.teach_overlay.setFocus()

    def _confirm_symbol_image_roi(self, roi):
        """
        Capture symbol image at specified ROI and store it.
        """
        if not hasattr(self, 'current_teach_symbol'):
            return
        
        symbol = self.current_teach_symbol
        
        if self.teach_overlay:
            self.teach_overlay.hide()
            self.teach_overlay.deleteLater()
            self.teach_overlay = None
        
        # Extract symbol image from ROI
        x, y, w, h = self._map_label_roi_to_image(roi)
        
        if self.current_image is None or w <= 0 or h <= 0:
            QMessageBox.warning(self, "Symbol Teaching", "Invalid ROI for symbol image.")
            return
        
        gray = self.current_image
        if len(gray.shape) == 3:
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
        
        symbol_image = gray[y:y+h, x:x+w]
        
        if symbol_image.size == 0:
            QMessageBox.warning(self, "Symbol Teaching", f"Failed to extract symbol '{symbol}' image.")
            return
        
        # Get the dialog and add the symbol image
        # (Dialog should still be accessible as a property or we re-open it)
        # For now, we'll find it in the window's children or recreate temporarily
        self._last_symbol_images = getattr(self, '_last_symbol_images', {})
        self._last_symbol_images[symbol] = symbol_image
        
        # Also save to disk via MarkSymbolImagesDialog
        from pathlib import Path
        symbol_dir = Path("MarkSymbols")
        symbol_dir.mkdir(exist_ok=True)
        symbol_file = symbol_dir / f"{symbol}.png"
        cv2.imwrite(str(symbol_file), symbol_image)
        
        # Update the dialog button style
        if hasattr(self, 'mark_symbol_dialog') and self.mark_symbol_dialog:
            self.mark_symbol_dialog.add_symbol_image(symbol, symbol_image)
        
        # Show preview and confirmation
        preview = symbol_image.copy()
        if len(preview.shape) == 2:
            preview = cv2.cvtColor(preview, cv2.COLOR_GRAY2BGR)
        
        self._show_image(preview)
        
        reply = QMessageBox.information(
            self,
            f"Symbol '{symbol}' Captured",
            f"Symbol '{symbol}' image has been saved.\n\n"
            "Click OK to teach the next symbol or Cancel to close.",
            QMessageBox.Ok | QMessageBox.Cancel
        )
        
        self.teach_phase = TeachPhase.NONE
        
        # Reshow the dialog so user can teach next symbol
        if reply == QMessageBox.Ok:
            if hasattr(self, 'mark_symbol_dialog') and self.mark_symbol_dialog:
                self.mark_symbol_dialog.show()
                self.mark_symbol_dialog.setFocus()
        else:
            # User clicked Cancel, close the dialog
            if hasattr(self, 'mark_symbol_dialog') and self.mark_symbol_dialog:
                self.mark_symbol_dialog.close()

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

    def _get_active_image_label(self) -> QLabel | None:
        """Get the target QLabel for the current station camera panel."""
        station_enum = self.state.station
        station_name = station_enum.name if hasattr(station_enum, "name") else str(station_enum).upper()
        doc_index = CameraRegistry.get_doc_index(station_name)
        if doc_index and hasattr(self, "camera_panels"):
            panel = self.camera_panels.get(doc_index)
            if panel:
                return panel.get("image") or panel.get("label")
        return self.image_label

    def _display_pixmap(self, pixmap: QPixmap):
        """Display pixmap with current zoom level"""
        target_label = self._get_active_image_label()
        if target_label is None:
            return
        self.image_label = target_label
        scaled_pix = self._apply_zoom(pixmap)
        target_label.setPixmap(scaled_pix)

    def _display_pixmap_to_doc(self, doc_index: int, pixmap: QPixmap) -> None:
        """Display pixmap in a specific station panel by Doc index."""
        if not hasattr(self, "camera_panels"):
            return
        panel = self.camera_panels.get(doc_index)
        if not panel:
            return
        target_label = panel.get("image") or panel.get("label")
        if target_label is None:
            return
        scaled_pix = pixmap.scaled(
            target_label.size(),
            Qt.IgnoreAspectRatio,
            Qt.SmoothTransformation
        )
        target_label.setPixmap(scaled_pix)

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

    def _toggle_inspection_enable(self):
        """Toggle Inspection Enable - matches old C++ OnConfigurationEnabledisableinspection()."""
        # Toggle the flag
        self.inspection_enabled = not self.inspection_enabled
        
        # Update checkbox state
        if self.act_inspection_enable:
            self.act_inspection_enable.setChecked(self.inspection_enabled)
        
        # Show informational dialog
        dlg = EnableDisableInspectionDialog(self, self.inspection_enabled)
        dlg.exec()
        
        # In old C++, this also saves to PkgLocBlobMethodParm.bEnableInspection
        # For now, just store in memory. Add persistence later if needed.
        
        status = "ENABLED" if self.inspection_enabled else "DISABLED"
        print(f"📋 Inspection {status}")
        
        # Refresh menu states
        self._apply_run_state()
    
    def _toggle_camera_enable(self):
        """Toggle Camera Enable - matches old C++ OnEngrCamEnable()."""
        # In old C++: m_pTrackManager->m_bCamEnable = !m_pTrackManager->m_bCamEnable
        # This toggles the camera hardware on/off
        self.camera_enable = self.act_camera_enable.isChecked()
        
        if self.camera_enable:
            QMessageBox.information(
                self,
                "Camera Enable",
                "Camera hardware has been ENABLED.\n\n"
                "This allows the camera to capture images during inspection.\n\n"
                "Note: This is a placeholder. Full implementation requires\n"
                "camera hardware integration."
            )
        else:
            QMessageBox.information(
                self,
                "Camera Enable",
                "Camera hardware has been DISABLED.\n\n"
                "The camera will not capture images during inspection."
            )
        
        # Update menu states after toggling camera
        self._apply_run_state()
    
    def _open_camera_configuration_dialog(self):
        """Open Camera Configuration Dialog - matches old C++ OnConfigCamsetup()."""
        # This is only callable when:
        # - Dialog not already open
        # - Camera is ENABLED
        # - Camera is AVAILABLE
        # - System is OFFLINE
        # - Not teaching/inspecting/calibrating
        # - No fail track
        
        # Check conditions and give helpful feedback
        if self.state.run_state != RunState.OFFLINE:
            QMessageBox.warning(
                self,
                "Camera Configuration",
                "Camera Configuration is only available in OFFLINE mode.\n\n"
                "Please switch to OFFLINE mode first."
            )
            return
        
        if not self.camera_enable:
            QMessageBox.warning(
                self,
                "Camera Configuration",
                "Camera is not ENABLED.\n\n"
                "Please enable the camera first:\n"
                "1. Go to Engineering menu\n"
                "2. Click 'Camera Enable' checkbox"
            )
            return
        
        if not self.camera_available:
            QMessageBox.warning(
                self,
                "Camera Configuration",
                "Camera is not available.\n\n"
                "Please ensure camera is connected."
            )
            return
        
        if not self.camera_setup_dialog_open:
            self.camera_setup_dialog_open = True
            
            # Get current track number (1 or 2)
            track_num = self.state.track

            # Load camera parameters from legacy .cam file (if present)
            config_dir = self._get_config_dir()
            cam_params = load_camera_parameters(config_dir, self.current_config_name, track_num)
            if cam_params:
                current = self.camera_settings.get(track_num, {})
                current.update(cam_params)
                self.camera_settings[track_num] = current
            
            # Create dialog
            dlg = CameraConfigurationDialog(self, track_num)
            
            # Load current settings for this track
            if track_num in self.camera_settings:
                dlg.set_settings(self.camera_settings[track_num])
            
            # Show dialog
            if dlg.exec() == QDialog.Accepted:
                # Save settings to memory
                self.camera_settings[track_num] = dlg.get_settings()

                # Save to legacy .cam file (C++ compatible)
                cam_path = save_camera_parameters(
                    config_dir,
                    self.current_config_name,
                    track_num,
                    self.camera_settings[track_num],
                )
                
                # TODO: Apply settings to real camera hardware
                # Right now settings are only stored in memory!
                # 
                # To make settings work with real cameras, you need to:
                # 1. Install camera SDK (pypylon for Basler, or MvCameraControl for HIK)
                # 2. Create camera hardware layer (device/camera_hardware.py)
                # 3. Implement: self._apply_camera_settings_to_hardware(track_num, settings)
                # 4. Call it here after saving
                #
                # Example:
                # try:
                #     self._apply_camera_settings_to_hardware(track_num, self.camera_settings[track_num])
                #     QMessageBox.information(self, "Success", "Settings applied to camera!")
                # except Exception as e:
                #     QMessageBox.warning(self, "Hardware Error", f"Failed to apply to camera: {e}")
                
                QMessageBox.information(
                    self,
                    "Camera Configuration",
                    f"Camera settings for Track {track_num} have been saved.\n\n"
                    f"Saved to: {cam_path}\n\n"
                    f"⚠️ Note: Hardware integration is not yet implemented.\n"
                    f"Settings will not be applied to real cameras until\n"
                    f"camera hardware layer is implemented."
                )
            
            self.camera_setup_dialog_open = False
            # Refresh menu state
            self._apply_run_state()
        else:
            QMessageBox.warning(self, "Camera Configuration", "Camera setup dialog is already open.")
    
    def _toggle_runtime_display(self):
        """Toggle Runtime Display Enable - matches old C++ OnEngineeringRuntimedisplayenable()."""
        # In old C++: m_RuntimeDisplayEnable = !m_RuntimeDisplayEnable
        # This toggles whether inspection results are displayed in real-time
        is_enabled = self.act_runtime_display.isChecked()
        
        if is_enabled:
            QMessageBox.information(
                self,
                "Runtime Display Enable",
                "Runtime Display has been ENABLED.\n\n"
                "Inspection results and overlays will be displayed in real-time\n"
                "during production runs.\n\n"
                "This helps monitor inspection quality but may slow down\n"
                "high-speed inspection."
            )
        else:
            QMessageBox.information(
                self,
                "Runtime Display Enable",
                "Runtime Display has been DISABLED.\n\n"
                "Inspection results will not be displayed during production runs.\n"
                "This maximizes inspection speed."
            )

    # =================================================
    # RUN → INSPECT CYCLE / SAVED IMAGES
    # =================================================
    def _toggle_inspect_cycle_single(self):
        """Toggle continuous inspection on the current single image (offline)."""
        if self.state.run_state != RunState.OFFLINE:
            QMessageBox.warning(self, "Inspect Cycle", "Switch to OFFLINE mode first.")
            if hasattr(self, "act_inspect_cycle_single"):
                self.act_inspect_cycle_single.setChecked(self.cont_insp_active)
            return

        if self.current_image is None:
            QMessageBox.warning(self, "Inspect Cycle", "No image loaded. Please GRAB or load an image first.")
            if hasattr(self, "act_inspect_cycle_single"):
                self.act_inspect_cycle_single.setChecked(self.cont_insp_active)
            return

        if self.cont_insp_active:
            self._stop_inspect_cycle()
        else:
            self._start_inspect_cycle()

        self._apply_run_state()

    def _start_inspect_cycle(self):
        """Start continuous inspection loop."""
        self.cont_insp_active = True
        delay = load_auto_run_setting().delay_time
        delay = max(10, int(delay))
        self.inspect_cycle_timer.start(delay)
        self._on_inspect_cycle_tick()

    def _stop_inspect_cycle(self):
        """Stop continuous inspection loop."""
        self.cont_insp_active = False
        if self.inspect_cycle_timer.isActive():
            self.inspect_cycle_timer.stop()

    def _on_inspect_cycle_tick(self):
        """Periodic tick for continuous inspection."""
        if not self.cont_insp_active:
            return
        if self.current_image is None:
            self._stop_inspect_cycle()
            return
        try:
            self.inspecting_active = True
            self._on_test()
        except Exception as exc:
            print(f"[WARN] Inspect Cycle error: {exc}")
            self._stop_inspect_cycle()
        finally:
            self.inspecting_active = False

    def _toggle_inspect_saved_images_autorun(self):
        """Toggle AutoRun for inspecting saved images."""
        if self.insp_saved_images_active:
            self._stop_saved_images_run()
        else:
            dlg = AutoRunSettingDialog(self)
            if dlg.exec() != QDialog.Accepted:
                self._apply_run_state()
                return
            self._start_saved_images_run(with_draw=False)

    def _toggle_inspect_saved_images_autorun_draw(self):
        """Toggle AutoRun With Draw for inspecting saved images."""
        if self.insp_saved_images_draw_active:
            self._stop_saved_images_run()
        else:
            dlg = AutoRunWithDrawSettingDialog(self)
            if dlg.exec() != QDialog.Accepted:
                self._apply_run_state()
                return
            self._start_saved_images_run(with_draw=True)

    def _start_saved_images_run(self, with_draw: bool):
        """Start inspecting saved images in sequence."""
        if self.state.run_state != RunState.OFFLINE:
            QMessageBox.warning(self, "Inspect Saved Images", "Switch to OFFLINE mode first.")
            self._apply_run_state()
            return

        if not self._load_saved_images_list(reset=True):
            return

        self.insp_saved_images_active = not with_draw
        self.insp_saved_images_draw_active = with_draw
        self.saved_images_step_active = False

        delay = load_auto_run_setting().delay_time
        delay = max(10, int(delay))
        self.saved_images_timer.start(delay)
        self._on_saved_images_tick()
        self._apply_run_state()

    def _stop_saved_images_run(self):
        """Stop inspecting saved images."""
        self.insp_saved_images_active = False
        self.insp_saved_images_draw_active = False
        if self.saved_images_timer.isActive():
            self.saved_images_timer.stop()
        self._apply_run_state()

    def _on_saved_images_tick(self):
        """Periodic tick to inspect next saved image."""
        if not (self.insp_saved_images_active or self.insp_saved_images_draw_active):
            return

        if self.saved_images_index >= len(self.saved_images_list):
            self._stop_saved_images_run()
            return

        image_path = self.saved_images_list[self.saved_images_index]
        self.saved_images_index += 1
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"[WARN] Failed to load image: {image_path}")
            return

        self.current_image = img
        self._show_image(img)
        try:
            self.inspecting_active = True
            self._on_test()
        except Exception as exc:
            print(f"[WARN] Saved Images inspect error: {exc}")
            self._stop_saved_images_run()
        finally:
            self.inspecting_active = False

    def _run_saved_images_step(self):
        """Inspect one saved image per click (Step mode)."""
        if self.state.run_state != RunState.OFFLINE:
            QMessageBox.warning(self, "Inspect Saved Images", "Switch to OFFLINE mode first.")
            self._apply_run_state()
            return

        if not self._load_saved_images_list(reset=False):
            self._apply_run_state()
            return

        # Toggle step mode active; when active, each click processes next image
        if not self.saved_images_step_active:
            self.saved_images_step_active = True

        if self.saved_images_index >= len(self.saved_images_list):
            # End of list → stop step mode
            self.saved_images_step_active = False
            self.saved_images_index = 0
            self._apply_run_state()
            return

        image_path = self.saved_images_list[self.saved_images_index]
        self.saved_images_index += 1
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"[WARN] Failed to load image: {image_path}")
            self.saved_images_step_active = False
            self._apply_run_state()
            return

        self.current_image = img
        self._show_image(img)
        try:
            self.inspecting_active = True
            self._on_test()
        except Exception as exc:
            print(f"[WARN] Saved Images step error: {exc}")
        finally:
            self.inspecting_active = False
        # Keep step mode active until end of list; user clicks again for next image
        self._apply_run_state()

    def _set_saved_images_folder(self):
        """Select folder containing saved images for inspection."""
        folder = QFileDialog.getExistingDirectory(self, "Select Stored Image Folder", str(self.saved_images_folder))
        if folder:
            self.saved_images_folder = Path(folder)
            self.saved_images_list = []
            self.saved_images_index = 0
            QMessageBox.information(self, "Stored Image Folder", f"Stored image folder set to:\n{folder}")

    def _load_saved_images_list(self, reset: bool = True) -> bool:
        """Load image list from saved images folder."""
        if not self.saved_images_folder.exists():
            QMessageBox.warning(self, "Inspect Saved Images", "Stored image folder does not exist. Please set it first.")
            return False

        exts = {".bmp", ".png", ".jpg", ".jpeg"}
        files = [p for p in self.saved_images_folder.iterdir() if p.suffix.lower() in exts]
        files.sort()

        if not files:
            QMessageBox.warning(self, "Inspect Saved Images", "Stored image folder is empty.")
            return False

        if reset or not self.saved_images_list:
            self.saved_images_list = files
            self.saved_images_index = 0

        return True

    def _camera_aoi_resize(self):
        """Camera AOI Resize Mode - matches old C++ OnEngrCamAoi()."""
        # Check if in OFFLINE mode (required for AOI resize)
        if self.state.run_state == RunState.ONLINE:
            QMessageBox.warning(
                self,
                "Camera AOI Resize",
                "Camera AOI Resize is only available in OFFLINE mode.\n"
                "Please switch to OFFLINE mode first."
            )
            return

        # Get current camera model for current station
        camera_model = self._get_current_camera_model()
        
        # Check if camera model supports AOI resizing
        # USB3CT, USB4CT, USB5MT, USB3MT, USB4CU, USB4MK, USB4CK, 1394MB support direct AOI
        supported_models = ["USB3CT", "USB4CT", "USB5MT", "USB3MT", "USB4CU", "USB4MK", "USB4CK", "1394MB"]
        
        if camera_model in supported_models:
            # For supported cameras: Show AOI resize dialog
            QMessageBox.information(
                self,
                "Camera AOI Resize Mode",
                f"Camera AOI Resize Mode activated for {camera_model}.\n\n"
                "This feature allows you to adjust the camera's Area of Interest (AOI).\n\n"
                "In the old system, this would:\n"
                "1. Open an interactive AOI selection window\n"
                "2. Allow you to draw a RED box to define the new AOI\n"
                "3. Click NEXT button to apply the changes\n"
                "4. Save the new AOI settings to camera parameters\n\n"
                "Note: This is a placeholder implementation. Full AOI resize requires\n"
                "camera hardware integration."
            )
        else:
            # For other cameras: Show restart confirmation dialog
            reply = QMessageBox.question(
                self,
                "Camera AOI Resize",
                "Application will close. Click 'Yes' and reopen the application \n"
                "to automatically enable AOI Resizing feature.\n\n"
                "This will reset the camera AOI to maximum size.\n\n"
                "Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # In the old C++ code, this would:
                # 1. Reset m_rectAoi to m_rectAoiMax
                # 2. Save camera parameters
                # 3. Close the application
                QMessageBox.information(
                    self,
                    "Camera AOI Reset",
                    "Camera AOI has been reset to maximum size.\n\n"
                    "The application will now close. Please restart the application\n"
                    "to apply the changes."
                )
                # Close the application
                self.close()

    def _get_current_camera_model(self) -> str:
        """Get the camera model for the current station."""
        # Map station to camera model from camera_settings.json
        station_to_model = {
            "Feed": "USB4CT",      # Color camera
            "Top": "USB3CT",       # Mono camera
            "Bottom": "USB3CT",    # Mono camera
            "Pick-up 1": "USB3CT",
            "Pick-up 2": "USB3CT",
            "Bottom Sealing": "USB3CT",
            "Top Sealing": "USB3CT"
        }
        return station_to_model.get(self.state.station, "USB3CT")

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
            "Do you want to rotate image?",
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
        # Show red box to define rotation ROI (matches old teaching procedure)
        self._start_rotation_teach()


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

            # Ask about mark teaching first (matches old procedure)
            self._ask_mark_teach()
        else:
            # Retry package teach
            self._start_package_roi()

    def _ask_mark_teach(self):
        """
        Ask if user wants to teach marking (matches old procedure).
        """
        mark_config = load_mark_inspection_config()

        if not mark_config.symbol_set.enable_mark_inspect:
            self._ask_color_inspection_teach()
            return

        reply = QMessageBox.question(
            self,
            "Teach Marking",
            "Do you want to Teach Marking?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._start_mark_teach_roi()
        else:
            self._ask_color_inspection_teach()

    def _start_mark_teach_roi(self):
        """
        Teach mark position - adjust rectangle to teach mark area.
        """
        self.teach_phase = TeachPhase.MARK_ROI

        QMessageBox.information(
            self,
            "Teach Mark Position",
            "Adjust the red rectangle to teach the mark area.\n"
            "Press Enter to confirm."
        )

        self.teach_overlay = PocketTeachOverlay(self.image_label, self)
        self.teach_overlay.setGeometry(self.image_label.rect())
        self.teach_overlay.show()
        self.teach_overlay.setFocus()

    def _confirm_mark_teach_roi(self, roi):
        """
        Confirm mark area ROI and switch to binary preview.
        """
        params = self.current_params()

        x, y, w, h = self._map_label_roi_to_image(roi)
        params.mark_teach_x = x
        params.mark_teach_y = y
        params.mark_teach_w = w
        params.mark_teach_h = h
        params.mark_binary_threshold = self.binary_threshold

        self._mark_teach_roi = (x, y, w, h)

        save_teach_data(self.inspection_parameters_by_station)

        if self.teach_overlay:
            self.teach_overlay.hide()
            self.teach_overlay.deleteLater()
            self.teach_overlay = None

        self._start_mark_binary_preview()

    def _start_mark_binary_preview(self):
        """
        Enable binary mode for mark visibility adjustment.
        """
        self.teach_phase = TeachPhase.MARK_BINARY
        self._teach_binary_prev_mode = self.binary_mode

        params = self.current_params()
        if params.mark_binary_threshold:
            self.binary_threshold = params.mark_binary_threshold
            self.binary_slider.setValue(self.binary_threshold)

        if hasattr(self, "act_binarise") and self.act_binarise is not None:
            self.act_binarise.blockSignals(True)
            self.act_binarise.setChecked(True)
            self.act_binarise.blockSignals(False)

        self._toggle_binarise(True)

        QMessageBox.information(
            self,
            "Mark Binary",
            "Binary mode enabled. Adjust the threshold until the mark is clear.\n"
            "Click NEXT to continue."
        )

    def _detect_mark_symbols(self):
        """
        Detect marks after binary adjustment and show rectangles.
        """
        if self.current_image is None:
            QMessageBox.warning(self, "Teach Marking", "No image loaded.")
            return

        params = self.current_params()
        roi = self._mark_teach_roi

        if not roi or roi[2] <= 0 or roi[3] <= 0:
            QMessageBox.warning(self, "Teach Marking", "Invalid mark teach area.")
            return

        mark_config = load_mark_inspection_config()

        # --- Teach-time detection based on connected components ---
        x, y, w, h = roi
        gray = self.current_image
        if len(gray.shape) == 3:
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

        roi_img = gray[y:y + h, x:x + w]

        thresh_type = cv2.THRESH_BINARY
        if mark_config.mark_color == "Black":
            thresh_type = cv2.THRESH_BINARY_INV

        _, binary = cv2.threshold(roi_img, self.binary_threshold, 255, thresh_type)

        # Light open to split touching strokes
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)

        roi_area = w * h
        min_area = max(20, int(roi_area * 0.001))
        min_size = 5

        marks = []
        for label in range(1, num_labels):
            x_c, y_c, w_c, h_c, area = stats[label]
            if area < min_area:
                continue
            if w_c < min_size or h_c < min_size:
                continue

            marks.append({
                "x": x + x_c,
                "y": y + y_c,
                "width": w_c,
                "height": h_c,
                "area": area
            })

        if not marks:
            QMessageBox.warning(
                self,
                "Teach Marking",
                "No marks detected. Please adjust the threshold and try again."
            )
            return

        # Sort marks left-to-right and keep required count
        required = mark_config.symbol_set.total_symbol_set
        marks = sorted(marks, key=lambda m: m.get("x", 0))
        marks = marks[:required]

        if len(marks) < required:
            QMessageBox.warning(
                self,
                "Teach Marking",
                f"Detected {len(marks)} mark(s), but {required} are required.\n"
                "Adjust the threshold and try again."
            )
            return

        params.mark_symbol_rois = [
            {
                "x": m.get("x", 0),
                "y": m.get("y", 0),
                "w": m.get("width", 0),
                "h": m.get("height", 0)
            }
            for m in marks
        ]
        params.mark_binary_threshold = self.binary_threshold

        save_teach_data(self.inspection_parameters_by_station)

        # Restore normal display and draw rectangles
        self._restore_teach_binary_mode()

        preview = self.current_image.copy()
        for m in params.mark_symbol_rois:
            x = m.get("x", 0)
            y = m.get("y", 0)
            w = m.get("w", 0)
            h = m.get("h", 0)
            cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 0), 2)

        self._show_image(preview)

        self.teach_phase = TeachPhase.MARK_DETECT

        QMessageBox.information(
            self,
            "Teach Marking",
            "The rectangles have been placed on each mark.\n"
            "Click NEXT to continue."
        )

    def _restore_teach_binary_mode(self):
        """Restore binary mode state after mark teaching."""
        if self._teach_binary_prev_mode is None:
            return

        prev_mode = self._teach_binary_prev_mode
        self._teach_binary_prev_mode = None

        if hasattr(self, "act_binarise") and self.act_binarise is not None:
            self.act_binarise.blockSignals(True)
            self.act_binarise.setChecked(prev_mode)
            self.act_binarise.blockSignals(False)

        self._toggle_binarise(prev_mode)

    def _finish_mark_teach(self):
        """Finalize mark teaching and continue workflow."""
        QMessageBox.information(
            self,
            "Teach Complete",
            "Mark teaching completed.\nClick OK to continue."
        )

        # Continue with color teaching or finish
        self._ask_color_inspection_teach()

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

        # Restore binary mode if teach enabled it
        self._restore_teach_binary_mode()

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
            TeachPhase.PACKAGE_ROI,
            TeachPhase.MARK_ROI
        ):
            if self.teach_overlay:
                self.teach_overlay.confirm()

        elif self.teach_phase == TeachPhase.MARK_BINARY:
            self._detect_mark_symbols()

        elif self.teach_phase == TeachPhase.MARK_DETECT:
            self._finish_mark_teach()


    def _confirm_overlay(self, roi):

        # ---- FEED pocket confirm ----
        if self.teach_phase == TeachPhase.NONE:
            self._confirm_pocket_teach(roi)
            return

        # ---- P station device ROI confirm ----
        if self.teach_phase == TeachPhase.ROTATION_ROI:
            self.teach_overlay.set_confirmed(True)

            # Rotation dialog after ROI confirmation
            params = self.current_params()
            dlg = ImageRotationDialog(
                self,
                initial_angle=params.rotation_angle
            )

            if dlg.exec():
                params.rotation_angle = dlg.angle
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

        # ---- Mark teach ROI confirm ----
        if self.teach_phase == TeachPhase.MARK_ROI:
            self.teach_overlay.set_confirmed(True)
            self._confirm_mark_teach_roi(roi)
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

        # ---- Symbol Image teach ROI confirm ----
        if self.teach_phase == TeachPhase.SYMBOL_ROI:
            self.teach_overlay.set_confirmed(True)
            self._confirm_symbol_image_roi(roi)
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
        if not getattr(self, "multi_track_tables", False):
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
        from config.debug_flags import DEBUG_STEP_MODE
        from config.debug_flags_io import save_debug_flags
        
        if checked:
            self.debug_flag |= DEBUG_STEP_MODE
        else:
            self.debug_flag &= ~DEBUG_STEP_MODE
        save_debug_flags(self.debug_flag)
        
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
        debug_flags = self.debug_flag
        from config.debug_runtime import set_debug_flags
        set_debug_flags(debug_flags)
        from config.debug_flags import DEBUG_STEP_MODE
        step_mode_active = bool(debug_flags & DEBUG_STEP_MODE) or self.step_mode_enabled
        if station == Station.FEED:
            # FEED station test
            if step_mode_active:
                print(f"[TEST] Step Mode ENABLED - running step-by-step inspection")
                # Create explicit copy using numpy to prevent any reference sharing
                test_image = np.array(self.current_image, copy=True, order='C')
                print(f"[DEBUG] Test image copy - id={id(test_image)}")
                result = test_feed(
                    image=test_image,
                    params=params,
                    step_mode=True,
                    step_callback=self._handle_test_step,
                    debug_flags=debug_flags
                )
            else:
                # Create explicit copy using numpy to prevent any reference sharing
                test_image = np.array(self.current_image, copy=True, order='C')
                print(f"[DEBUG] Test image copy - id={id(test_image)}")
                result = test_feed(
                    image=test_image,
                    params=params,
                    debug_flags=debug_flags
                )
        else:
            # TOP/BOTTOM test with optional step mode
            if step_mode_active:
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
                    step_callback=self._handle_test_step,
                    debug_flags=debug_flags
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
                    params=params,
                    debug_flags=debug_flags
                )

        if result.result_image is not None:
            from config.debug_flags import DEBUG_DRAW
            if self.debug_flag & DEBUG_DRAW:
                self._show_image(result.result_image)
            else:
                self._show_image(self.current_image)

        # Debug: Verify current_image wasn't modified by test
        mean_after = cv2.mean(self.current_image)[0]
        print(f"[DEBUG] After test - current_image mean: {mean_after:.1f}")

        # Check alert threshold if test failed
        if result.status == TestStatus.FAIL:
            # Extract defect name from message if available
            # The test result message typically starts with the defect name
            defect_name = self._extract_defect_name_from_message(result.message)
            if defect_name:
                self.alert_tracker.record_result(defect_name, is_pass=False, parent_widget=self)
        
        # Display detailed reason in dialog box
        title = f"Test Result: {result.status}"
        QMessageBox.information(self, title, result.message)

        print(f"[TEST RESULT] {result.status} - {result.message}")

        # Save result image to track-specific folder (fail only if enabled)
        try:
            if self.debug_save_failed_images and result.status == TestStatus.FAIL:
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

    def _extract_defect_name_from_message(self, message: str) -> str | None:
        """Extract defect name from test result message"""
        # Common defect patterns in messages
        defect_keywords = [
            "Package Location", "Pocket Location", "Body Length", "Body Width",
            "Terminal Width", "Terminal Length", "Term-Term Length", "Terminal Pogo",
            "Terminal Offset", "Incomplete Termination", "Terminal Oxidation",
            "Terminal Chipoff", "Terminal Color", "Body Color", "Body Stain",
            "Body Smear", "Edge Chipoff", "Body Crack", "Mark"
        ]
        
        for keyword in defect_keywords:
            if keyword.lower() in message.lower():
                return keyword
        
        return None

    def _open_alert_messages_dialog(self):
        """Open Alert Messages dialog and reload configuration after editing"""
        dlg = AlertMessagesDialog(self)
        if dlg.exec():
            # Reload alert configuration after user edits
            self.alert_tracker.reload_config()
            print("[ALERT] Alert messages configuration reloaded")

    def _open_inspection_debug_dialog(self):
        """Open Debug Flag Setting dialog - matches C++ OnDebugFlag()"""
        dlg = InspectionDebugDialog(self.debug_flag, self)
        if dlg.exec():
            # Update debug flags - matches C++ m_lDebugFlag
            self.debug_flag = dlg.get_debug_flags()
            
            # Save to configuration file
            from config.debug_flags_io import save_debug_flags
            save_debug_flags(self.debug_flag)
            
            # Log the updated flags
            from config.debug_flags import (
                DEBUG_DRAW, DEBUG_PRINT, DEBUG_PRINT_EXT, DEBUG_EDGE, DEBUG_STEP_MODE,
                DEBUG_SAVE_FAIL_IMAGE, DEBUG_TIME, DEBUG_TIME_EXT, DEBUG_BLOB, DEBUG_HIST,
                DEBUG_PKGLOC, DEBUG_PVI
            )
            
            flags_enabled = []
            if self.debug_flag & DEBUG_DRAW:
                flags_enabled.append("Debug Draw")
            if self.debug_flag & DEBUG_PRINT:
                flags_enabled.append("Debug Print")
            if self.debug_flag & DEBUG_PRINT_EXT:
                flags_enabled.append("Debug Print Ext")
            if self.debug_flag & DEBUG_TIME:
                flags_enabled.append("Debug Timing")
            if self.debug_flag & DEBUG_TIME_EXT:
                flags_enabled.append("Debug Timing Ext")
            if self.debug_flag & DEBUG_STEP_MODE:
                flags_enabled.append("Debug Step Mode")
            if self.debug_flag & DEBUG_EDGE:
                flags_enabled.append("Debug Edge")
            if self.debug_flag & DEBUG_BLOB:
                flags_enabled.append("Debug Blob")
            if self.debug_flag & DEBUG_HIST:
                flags_enabled.append("Debug Histogram")
            if self.debug_flag & DEBUG_SAVE_FAIL_IMAGE:
                flags_enabled.append("Save Failed Images")
            if self.debug_flag & DEBUG_PKGLOC:
                flags_enabled.append("Package Location")
            if self.debug_flag & DEBUG_PVI:
                flags_enabled.append("Top Station")

            # Sync save failed images flag (matches C++ m_bDebugSaveFailedImages)
            self.debug_save_failed_images = bool(self.debug_flag & DEBUG_SAVE_FAIL_IMAGE)

            # Sync step mode flag and menu action
            from config.debug_flags import DEBUG_STEP_MODE
            self.step_mode_enabled = bool(self.debug_flag & DEBUG_STEP_MODE)
            if hasattr(self, "act_step_mode"):
                self.act_step_mode.setChecked(self.step_mode_enabled)
            
            if flags_enabled:
                print(f"[DEBUG] Enabled flags: {', '.join(flags_enabled)}")
            else:
                print("[DEBUG] All debug flags disabled")

    def _open_encrypt_decrypt_dialog(self):
        """Open Encrypt/Decrypt Images dialog"""
        dlg = EncryptDecryptDialog(self)
        dlg.exec()

    # =================================================
    # STUB
    # =================================================
    def _stub(self, name: str):
        QMessageBox.information(self, name, f"{name}\n\n(Not implemented yet)")

    # =================================================
    # Configuration File Management
    # =================================================
    def _get_inspection_dir(self) -> Path:
        inspection_dir = Path(".")
        if hasattr(self, "lot_info"):
            inspection_dir = Path(getattr(self.lot_info, "inspection_dir", "."))
        return inspection_dir

    def _get_config_dir(self, config_name: str | None = None) -> Path:
        name = config_name or self.current_config_name
        return self._get_inspection_dir() / name

    def _select_config_file(self):
        """Select and load a configuration file - matches old C++ OnConfigSelFile()."""
        inspection_dir = self._get_inspection_dir()
        
        dialog = SelectConfigFileDialog(
            current_config_name=self.current_config_name,
            inspection_dir=str(inspection_dir),
            parent=self
        )
        
        if dialog.exec():
            selected_config = dialog.selected_config
            if selected_config:
                self._load_config_file(selected_config)
    
    def _load_config_file(self, config_name: str):
        """Load configuration file - matches old C++ LoadConfigFile()."""
        import json
        from config import inspection_parameters_io
        
        # Set configuration name and directory
        self.current_config_name = config_name
        config_dir = self._get_config_dir(config_name)
        
        # Create config directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        
        files_loaded = []
        errors = []
        
        try:
            # Load inspection_parameters.json
            params_file = config_dir / "inspection_parameters.json"
            if params_file.exists():
                try:
                    # Load directly from the config file
                    with open(params_file, 'r') as f:
                        params_data = json.load(f)
                    self.inspection_parameters = InspectionParameters(**params_data)
                    files_loaded.append("inspection_parameters.json")
                except Exception as e:
                    errors.append(f"inspection_parameters.json: {str(e)}")
            
            # Load pocket_params.json
            pocket_file = config_dir / "pocket_params.json"
            if pocket_file.exists():
                try:
                    with open(pocket_file, 'r') as f:
                        pocket_data = json.load(f)
                    files_loaded.append("pocket_params.json")
                except Exception as e:
                    errors.append(f"pocket_params.json: {str(e)}")
            
            # Load device_location_setting.json
            device_loc_file = config_dir / "device_location_setting.json"
            if device_loc_file.exists():
                try:
                    with open(device_loc_file, 'r') as f:
                        device_loc_data = json.load(f)
                    files_loaded.append("device_location_setting.json")
                except Exception as e:
                    errors.append(f"device_location_setting.json: {str(e)}")
            
            # Load teach_data.json
            teach_file = config_dir / "teach_data.json"
            if teach_file.exists():
                try:
                    with open(teach_file, 'r') as f:
                        teach_data = json.load(f)
                    files_loaded.append("teach_data.json")
                except Exception as e:
                    errors.append(f"teach_data.json: {str(e)}")
            
            # Load alert_messages.json
            alert_file = config_dir / "alert_messages.json"
            if alert_file.exists():
                try:
                    with open(alert_file, 'r') as f:
                        alert_data = json.load(f)
                    files_loaded.append("alert_messages.json")
                except Exception as e:
                    errors.append(f"alert_messages.json: {str(e)}")
            
            # Load ignore_fail_count.json
            ignore_file = config_dir / "ignore_fail_count.json"
            if ignore_file.exists():
                try:
                    with open(ignore_file, 'r') as f:
                        ignore_data = json.load(f)
                    files_loaded.append("ignore_fail_count.json")
                except Exception as e:
                    errors.append(f"ignore_fail_count.json: {str(e)}")
            
            # Load device_inspection.json and copy to workspace root
            device_insp_file = config_dir / "device_inspection.json"
            if device_insp_file.exists():
                try:
                    import shutil
                    # Copy to workspace root so Device Inspection dialog reads it
                    workspace_device_insp = Path("device_inspection.json")
                    print(f"[DEBUG] Found device_inspection.json in config: {device_insp_file}")
                    print(f"[DEBUG] Copying to workspace root: {workspace_device_insp}")
                    
                    # Read and display sample values before copying
                    with open(device_insp_file, 'r') as f:
                        device_insp_data = json.load(f)
                    print(f"[DEBUG] device_inspection.json keys: {list(device_insp_data.keys())}")
                    # Show sample values from the config file
                    if "UnitParameters" in device_insp_data:
                        unit_params = device_insp_data["UnitParameters"]
                        print(f"[DEBUG] Config UnitParameters sample: {list(unit_params.keys())[:2] if isinstance(unit_params, dict) else 'N/A'}")
                    
                    shutil.copy2(device_insp_file, workspace_device_insp)
                    print(f"[DEBUG] Successfully copied device_inspection.json")
                    
                    # Verify file was copied and display new values
                    if workspace_device_insp.exists():
                        with open(workspace_device_insp, 'r') as f:
                            workspace_content = json.load(f)
                        print(f"[DEBUG] Workspace device_inspection.json now contains: {list(workspace_content.keys())}")
                        if "UnitParameters" in workspace_content:
                            unit_params = workspace_content["UnitParameters"]
                            print(f"[DEBUG] Workspace UnitParameters sample: {list(unit_params.keys())[:2] if isinstance(unit_params, dict) else 'N/A'}")
                    
                    files_loaded.append("device_inspection.json")
                except Exception as e:
                    print(f"[DEBUG] Failed to copy device_inspection.json: {e}")
                    errors.append(f"device_inspection.json: {str(e)}")
            else:
                print(f"[DEBUG] device_inspection.json NOT found in config directory: {config_dir}")

            # Load camera parameters from .cam file (legacy C++ format)
            for track_num in sorted(self.camera_settings.keys()):
                cam_params = load_camera_parameters(config_dir, config_name, track_num)
                if cam_params:
                    current = self.camera_settings.get(track_num, {})
                    current.update(cam_params)
                    self.camera_settings[track_num] = current
                    files_loaded.append(f"{config_name}.cam (Track{track_num})")
            
            # Show success message
            message = f"Configuration '{config_name}' loaded successfully!\n\n"
            
            if files_loaded:
                message += "Files loaded:\n" + "\n".join(f"  ✓ {f}" for f in files_loaded)
            else:
                message += "No configuration files found in directory.\n"
                message += "This is a new/empty configuration."
            
            if errors:
                message += "\n\nErrors encountered:\n" + "\n".join(f"  ✗ {e}" for e in errors)
            
            QMessageBox.information(
                self,
                "Configuration Loaded",
                message
            )
            
            # Update current config name
            self.current_config_name = config_name
            
            print(f"[CONFIG] Loaded configuration: {config_name}")
            print(f"[CONFIG] Config directory: {config_dir}")
            print(f"[CONFIG] Please close and reopen Device Inspection to see updated settings")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Failed",
                f"Failed to load configuration '{config_name}':\n{str(e)}"
            )
    
    def _save_config_as(self):
        """Save current configuration as new name - matches old C++ OnConfigurationSaveconfigas()."""
        from PySide6.QtWidgets import QInputDialog
        
        inspection_dir = self._get_inspection_dir()
        
        while True:
            # Show input dialog to get new config name
            new_config_name, ok = QInputDialog.getText(
                self,
                "Save Configuration As",
                "Enter new configuration file name:",
                text=""
            )
            
            if not ok or not new_config_name:
                break
            
            # Check if config already exists
            new_config_dir = inspection_dir / new_config_name
            if new_config_dir.exists():
                QMessageBox.warning(
                    self,
                    "File Exists",
                    "This filename already exists!\n"
                    "Please use another filename."
                )
                continue
            
            # Copy current configuration
            try:
                self._copy_config_file(new_config_name)
                break  # Success, exit loop
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    f"Failed to save configuration:\n{str(e)}"
                )
                break
    
    def _copy_config_file(self, new_config_name: str):
        """Copy current configuration to new name - matches old C++ CopyConfigFile()."""
        from dataclasses import asdict
        import shutil
        import json
        
        # Get directories
        inspection_dir = self._get_inspection_dir()
        
        # Destination: new config directory
        dst_config_dir = inspection_dir / new_config_name
        dst_config_dir.mkdir(parents=True, exist_ok=True)
        
        files_copied = []
        
        # Save CURRENT settings to the new config directory
        try:
            # Save current inspection_parameters
            params_file = dst_config_dir / "inspection_parameters.json"
            params_dict = asdict(self.inspection_parameters)
            with open(params_file, 'w') as f:
                json.dump(params_dict, f, indent=4)
            print(f"[DEBUG] Saved inspection_parameters with keys: {list(params_dict.keys())[:3]}...")
            print(f"[DEBUG] Sample value - body_crack_enable: {params_dict.get('body_crack_enable')}")
            files_copied.append("inspection_parameters.json")
        except Exception as e:
            print(f"[CONFIG] Failed to save inspection_parameters.json: {e}")

        # Save camera parameters to legacy .cam file in new config directory
        for track_num in sorted(self.camera_settings.keys()):
            try:
                cam_path = save_camera_parameters(
                    dst_config_dir,
                    new_config_name,
                    track_num,
                    self.camera_settings.get(track_num, {}),
                )
                files_copied.append(cam_path.name)
            except Exception as e:
                print(f"[CONFIG] Failed to save camera .cam for Track{track_num}: {e}")
        
        # Copy other config files from current workspace or source config
        config_files_to_copy = [
            "pocket_params.json",
            "device_location_setting.json",
            "teach_data.json",
            "alert_messages.json",
            "ignore_fail_count.json",
            "device_inspection.json"
        ]
        
        # First try to copy from current config directory
        src_config_dir = inspection_dir / self.current_config_name
        
        print(f"[DEBUG] _copy_config_file: Copying {len(config_files_to_copy)} file types")
        print(f"[DEBUG] Source config dir: {src_config_dir}")
        print(f"[DEBUG] Destination config dir: {dst_config_dir}")
        
        if src_config_dir.exists() and src_config_dir.is_dir():
            print(f"[DEBUG] Source config directory exists, copying files from it")
            for config_file in config_files_to_copy:
                src_file = src_config_dir / config_file
                if src_file.exists():
                    dst_file = dst_config_dir / config_file
                    try:
                        shutil.copy2(src_file, dst_file)
                        print(f"[DEBUG] Copied {config_file} from {src_file} to {dst_file}")
                        files_copied.append(config_file)
                    except Exception as e:
                        print(f"[CONFIG] Failed to copy {config_file}: {e}")
                else:
                    print(f"[DEBUG] {config_file} not found in {src_config_dir}")
        else:
            print(f"[DEBUG] Source config directory does NOT exist: {src_config_dir}")
            # Fall back to workspace root
            for config_file in config_files_to_copy:
                src_file = Path(config_file)
                if src_file.exists():
                    dst_file = dst_config_dir / config_file
                    try:
                        print(f"[DEBUG] Copying {config_file} from workspace root")
                        shutil.copy2(src_file, dst_file)
                        print(f"[DEBUG] Copied {config_file} from {src_file} to {dst_file}")
                        files_copied.append(config_file)
                    except Exception as e:
                        print(f"[CONFIG] Failed to copy {config_file}: {e}")
                else:
                    print(f"[DEBUG] {config_file} not found in workspace root")
            # If source doesn't exist, copy from current workspace root
            config_files = [
                "inspection_parameters.json",
                "pocket_params.json",
                "device_location_setting.json",
                "teach_data.json",
                "alert_messages.json",
                "ignore_fail_count.json"
            ]
            
            for config_file in config_files:
                src_file = Path(config_file)
                if src_file.exists():
                    dst_file = dst_config_dir / config_file
                    try:
                        shutil.copy2(src_file, dst_file)
                        files_copied.append(config_file)
                    except Exception as e:
                        print(f"[CONFIG] Failed to copy {config_file}: {e}")
        
        print(f"[CONFIG] Configuration saved as: {new_config_name}")
        print(f"[CONFIG] Files copied: {', '.join(files_copied) if files_copied else 'none'}")
        
        # Load the new configuration and show success message
        self._load_config_file(new_config_name)
        
        QMessageBox.information(
            self,
            "Save Complete",
            f"Configuration saved as: {new_config_name}\n\n"
            f"Files copied: {len(files_copied)}\n"
            "The new configuration has been loaded."
        )


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
