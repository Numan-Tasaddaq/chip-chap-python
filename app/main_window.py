
# app/main_window.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QToolBar, QComboBox, QPushButton, QSplitter,
    QTableWidget, QMessageBox,QSlider
)
import cv2
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
from imaging.grab_service import GrabService
from imaging.image_loader import ImageLoader
from config.inspection_parameters import InspectionParameters
from config.inspection_parameters_io import load_parameters
from imaging.pocket_teach_overlay import PocketTeachOverlay
from ui.image_rotation_dialog import ImageRotationDialog

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
        self.current_image=None
       

        self.inspection_parameters = load_parameters()

        self.grab_service=GrabService(self)
        self.image_loader = ImageLoader(self)

        self.binary_mode = False
        self.binary_threshold = 75  # default (PDF example)
        self.is_teach_mode = False
        self.teach_overlay = None
        
        # Zoom variables
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.zoom_step = 0.1

        self._build_menu_bar()
        self._build_main_toolbar()
        self._build_track_bar()

        self._build_center_layout()



        self._apply_run_state()

    # =================================================
    # MENU BAR
    # =================================================
    def _build_menu_bar(self):
        mb = self.menuBar()

        # ---------- Production ----------
        m_production = mb.addMenu("Production")

        act_open_lot = QAction("Open Lot", self)
        act_open_lot.triggered.connect(self._open_lot_dialog)
        m_production.addAction(act_open_lot)

        m_production.addAction(
            QAction("End Lot", self, triggered=lambda: self._stub("End Lot"))
        )
        m_production.addSeparator()
        # ✅ Online / Offline (checkable)
        self.act_online_offline = QAction("Online / Offline", self)
        self.act_online_offline.setCheckable(True)
        self.act_online_offline.setChecked(False)  # ONLINE by default
        self.act_online_offline.triggered.connect(self._toggle_online_offline_from_menu)
        m_production.addAction(self.act_online_offline)

        # ---------- Engineering ----------
        m_engineering = mb.addMenu("Engineering")
        act_binarise = QAction("Binarise Image", self)
        act_binarise.setCheckable(True)
        act_binarise.triggered.connect(self._toggle_binarise)
        m_engineering.addAction(act_binarise)

        act_zoom_in = QAction("Zoom In", self)
        act_zoom_in.triggered.connect(self._zoom_in)
        m_engineering.addAction(act_zoom_in)
        
        act_zoom_fit = QAction("Zoom Fit", self)
        act_zoom_fit.triggered.connect(self._zoom_fit)
        m_engineering.addAction(act_zoom_fit)
        
        act_zoom_out = QAction("Zoom Out", self)
        act_zoom_out.triggered.connect(self._zoom_out)
        m_engineering.addAction(act_zoom_out)
        m_engineering.addSeparator()
        act_load_image = QAction("Load Image From Disk", self)
        act_load_image.triggered.connect(self.image_loader.load_from_disk)
        m_engineering.addAction(act_load_image)

        m_engineering.addAction(QAction("Save Image To Disk", self, triggered=lambda: self._stub("Save Image To Disk")))
        m_engineering.addSeparator()
        self._add_disabled(m_engineering, "Camera Enable")
        self._add_disabled(m_engineering, "RunTime Display Enable")
        self._add_disabled(m_engineering, "Camera AOI Resize Mode")

        # ---------- Configuration ----------
        m_config = mb.addMenu("Configuration")
        m_config.addAction(QAction("Select Config File", self, triggered=lambda: self._stub("Select Config File")))
        m_config.addAction(QAction("Save Config As", self, triggered=lambda: self._stub("Save Config As")))
        act_para_mark = QAction("Para & Mark Config File", self)
        act_para_mark.triggered.connect(self._open_para_mark_config_dialog)
        m_config.addAction(act_para_mark)
        
        m_config.addSeparator()
        act_device_loc = QAction("Device Location", self)
        act_device_loc.triggered.connect(self._open_device_location_dialog)
        m_config.addAction(act_device_loc)

        act_pocket_loc = QAction("Pocket Location", self)
        act_pocket_loc.triggered.connect(self._open_pocket_location_dialog)
        m_config.addAction(act_pocket_loc)

        act_device_inspection = QAction("Device Inspection", self)
        act_device_inspection.triggered.connect(self._open_device_inspection_dialog)
        m_config.addAction(act_device_inspection)


        m_mark = m_config.addMenu("Mark Inspection")
        m_mark.addAction(QAction("Mark Symbol Set", self, triggered=lambda: self._stub("Mark Symbol Set")))
        m_mark.addAction(QAction("Mark Parameters", self, triggered=lambda: self._stub("Mark Parameters")))
        m_mark.addAction(QAction("Mark Symbol Images", self, triggered=lambda: self._stub("Mark Symbol Images")))

        m_config.addSeparator()
        self._add_disabled(m_config, "Enable / Disable Inspection")
        self._add_disabled(m_config, "Camera Configuration")

        m_color = m_config.addMenu("Color Inspection")
        act_body_color = QAction("Body Color", self)
        act_body_color.triggered.connect(self._open_body_color_dialog)
        m_color.addAction(act_body_color)
        
        act_terminal_color = QAction("Terminal Color", self)
        act_terminal_color.triggered.connect(self._open_terminal_color_dialog)
        m_color.addAction(act_terminal_color)
        act_mark_color = QAction("Mark Color", self)
        act_mark_color.triggered.connect(self._open_mark_color_dialog)
        m_color.addAction(act_mark_color)
        
        
        # ---------- Run ----------
        m_run = mb.addMenu("Run")
        m_cycle = m_run.addMenu("Inspect Cycle")
        m_cycle.addAction(QAction("Single Image", self, triggered=lambda: self._stub("Inspect Cycle → Single Image")))

        m_saved = m_run.addMenu("Inspect Saved Images")
        m_saved.addAction(
    QAction("AutoRun", self,
            triggered=lambda: AutoRunSettingDialog(self).exec())
)
        m_saved.addAction(
    QAction("AutoRun With Draw", self,
            triggered=lambda: AutoRunWithDrawSettingDialog(self).exec())
)
        m_saved.addAction(QAction("Step", self, triggered=lambda: self._stub("Step")))
        m_saved.addAction(QAction("Set Stored Image Folder", self, triggered=lambda: self._stub("Set Stored Image Folder")))

        # ---------- Diagnostic ----------
        m_diag = mb.addMenu("Diagnostic")
        m_diag.addAction(
    QAction("Inspection", self, triggered=lambda: InspectionDebugDialog(self).exec())
)

        act_range = QAction("Inspection Parameters Range", self)
        act_range.triggered.connect(self._open_inspection_parameters_range)
        m_diag.addAction(act_range)

        m_diag.addAction(QAction("Enable Step Mode", self, triggered=lambda: self._stub("Enable Step Mode")))
        m_diag.addAction(
    QAction("Alert Messages", self, triggered=lambda: AlertMessagesDialog(self).exec())
)
        m_diag.addAction(QAction("Encrypt / Decrypt Images", self, triggered=lambda: self._stub("Encrypt / Decrypt Images")))
        m_diag.addAction(
    QAction("Ignore Count", self, triggered=lambda: IgnoreFailCountDialog(self).exec())
)

        # ---------- View ----------
        m_view = mb.addMenu("View")
        m_view.addAction(QAction("Restore", self, triggered=lambda: self._stub("Restore")))
        m_view.addAction(QAction("Reset Counters", self, triggered=lambda: self._stub("Reset Counters")))
        m_view.addAction(QAction("Pass Bin Counters", self, triggered=lambda: self._stub("Pass Bin Counters")))
        m_view.addAction(QAction("Password Details", self, triggered=lambda: self._stub("Password Details")))

        # ---------- Help ----------
        m_help = mb.addMenu("Help")
        m_help.addAction(QAction("About", self, triggered=lambda: self._stub("About")))

    def _add_disabled(self, menu, text):
        a = QAction(text, self)
        a.setEnabled(False)
        menu.addAction(a)

    # =================================================
    # TOOLBARS
    # =================================================
    def _build_main_toolbar(self):
        tb = QToolBar("MainToolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(36, 36))
        self.addToolBar(Qt.TopToolBarArea, tb)

        def add(text):
            act = QAction(text, self)
            tb.addAction(act)
            return act

        self.act_grab = add("GRAB")
        self.act_grab.triggered.connect(self.grab_service.grab)
        self.act_live = add("LIVE")
        self.act_live.triggered.connect(self.grab_service.toggle_live)
        self.act_teach = add("TEACH")
        self.act_teach.triggered.connect(self._on_teach)
        self.act_test = add("TEST")
        self.act_next = add("NEXT")
        self.act_next.triggered.connect(self._on_next)

        add("ABORT")
        self.act_start = add("START")
        self.act_end = add("END")
        self.act_open = add("OPEN")
        self.act_para = add("PARA")
        add("RESET")

        self.act_start.triggered.connect(self._on_start)
        self.act_end.triggered.connect(self._on_end)
        self.act_open.triggered.connect(self._open_lot_dialog)
        self.act_para.triggered.connect(self._open_device_inspection_dialog)

    def _build_track_bar(self):
        tb = QToolBar("TrackBar")
        tb.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, tb)

        self.btn_track_f = QPushButton("Track1-F")
        self.btn_track_p = QPushButton("Track1-P")

        self.btn_track_f.clicked.connect(lambda: self._set_station(Station.FEED))
        self.btn_track_p.clicked.connect(lambda: self._set_station(Station.TOP))

        tb.addWidget(self.btn_track_f)
        tb.addWidget(self.btn_track_p)

        tb.addSeparator()

        self.track_combo = QComboBox()
        self.track_combo.addItems(["Track1", "Track2", "Track3"])
        self.track_combo.currentIndexChanged.connect(self._on_track_changed)
        tb.addWidget(self.track_combo)
    def _set_station(self, station: Station):
        self.state.station = station
        self._update_station_ui()
        self._apply_run_state()



    def _on_track_changed(self, index: int):
        # index 0 -> Track1, 1 -> Track2, etc.
        self.state.track = index + 1
        print(f"Active Track: Track{self.state.track}")

        # Reset station to FEED on track change
        self.state.station = Station.FEED

    # =================================================
    # CENTER LAYOUT
    # =================================================
    def _build_center_layout(self):
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        lyt = QVBoxLayout(left)
        lyt.addWidget(QLabel("Track1"))

        self.image_label = QLabel()
        self.image_label.setMinimumSize(800, 520)
        self.image_label.setStyleSheet("background:black; border:1px solid #555;")
        self.image_label.setAlignment(Qt.AlignCenter)
        lyt.addWidget(self.image_label, 1)
        # ---- Binary Threshold Slider + Value ----
        slider_row = QHBoxLayout()
        self.binary_text_label=QLabel("Threshold:")
        self.binary_text_label.setVisible(False)
        self.binary_slider = QSlider(Qt.Horizontal)
        self.binary_slider.setRange(0, 255)
        self.binary_slider.setValue(self.binary_threshold)
        self.binary_slider.setVisible(False)  # hidden by default
        self.binary_slider.valueChanged.connect(self._on_binary_threshold_changed)

        self.binary_value_label = QLabel(str(self.binary_threshold))
        self.binary_value_label.setFixedWidth(40)
        self.binary_value_label.setAlignment(Qt.AlignCenter)
        self.binary_value_label.setVisible(False)
        self.binary_slider.valueChanged.connect(self._on_binary_threshold_changed)
        self.binary_text_label = QLabel("Threshold:")
        self.binary_text_label.setVisible(False)
        slider_row.addWidget(self.binary_text_label)

        slider_row.addWidget(self.binary_slider, 1)
        slider_row.addWidget(self.binary_value_label)
        

        lyt.addLayout(slider_row)


        lyt.addWidget(self.binary_slider)


        logo = QLabel("LOGO")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("background:#111; color:white; font-size:18px;")
        logo.setFixedHeight(120)
        lyt.addWidget(logo)

        splitter.addWidget(left)

        right = QWidget()
        rlyt = QVBoxLayout(right)

        top_tbl = QTableWidget(10, 2)
        top_tbl.setHorizontalHeaderLabels(["??", "Track1"])
        rlyt.addWidget(top_tbl)

        bot_tbl = QTableWidget(15, 3)
        bot_tbl.setHorizontalHeaderLabels(["??", "Track1 Qty", "Track1 %"])
        rlyt.addWidget(bot_tbl)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        

        self.setCentralWidget(splitter)

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
            and self.state.track == 1
            and self.state.station == Station.FEED
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

    # =================================================
    # REAL DIALOGS
    # =================================================
    def _open_inspection_parameters_range(self):
        dlg = InspectionParametersRangeDialog(self)
        if dlg.exec():
            ip = self.inspection_parameters
            print("Inspection Parameters:")
            print("Body Length:", ip.body_length_min, ip.body_length_max)
            print("Body Width :", ip.body_width_min, ip.body_width_max)
            print("Terminal Width:", ip.terminal_width_min, ip.terminal_width_max)

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
        qimg = QImage(
            binary.data,
            w,
            h,
            w,
            QImage.Format_Grayscale8
        )

        pix = QPixmap.fromImage(qimg)
        self._display_pixmap(pix)
    def _show_normal_image(self):
        if self.current_image is None:
            return

        rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w

        qimg = QImage(
            rgb.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        )

        pix = QPixmap.fromImage(qimg)
        self._display_pixmap(pix)
    def _on_binary_threshold_changed(self, value: int):
        self.binary_threshold = value
        self.binary_value_label.setText(str(value))

        if self.binary_mode:
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

        # 🔀 Dispatch teach logic by station
        if self.state.station == Station.FEED:
            self._teach_feed_station()
        else:
            # TOP & BOTTOM → same logic
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

        QMessageBox.information(
            self,
            "Teach Device Position",
            "Adjust rectangle to teach device position for rotation.\n"
            "Press Enter or click NEXT to continue."
        )

        # STEP 5 → Device rotation ROI
        self.teach_phase = TeachPhase.ROTATION_ROI

        self.teach_overlay = PocketTeachOverlay(self.image_label, self)
        self.teach_overlay.setGeometry(self.image_label.rect())
        self.teach_overlay.show()
        self.teach_overlay.setFocus()

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

        # Save pocket location
        self.inspection_parameters.pocket_x = roi.x
        self.inspection_parameters.pocket_y = roi.y
        self.inspection_parameters.pocket_w = roi.w
        self.inspection_parameters.pocket_h = roi.h
        self.inspection_parameters.is_defined = True

        # 🔁 Switch overlay to GREEN (important)
        self.teach_overlay.set_confirmed(True)

        self.teach_phase = TeachPhase.POCKET_DONE

        QMessageBox.information(
            self,
            "Pocket Teach",
            "Pocket position learned.\n(Green Box Confirmed)\n\nClick NEXT to continue."
        )

    def _ask_image_rotation(self):
        """
        STEP 12
        Ask user if image is rotated
        """

        if self.teach_phase != TeachPhase.POCKET_DONE:
            return

        reply = QMessageBox.question(
            self,
            "Image Rotation",
            "Is the image rotated?",
            QMessageBox.Yes | QMessageBox.No
        )

        # ---- NO ROTATION ----
        if reply == QMessageBox.No:
            self.inspection_parameters.rotation_angle = 0.0

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
            self.inspection_parameters.rotation_angle = dlg.angle

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
        Confirm package location and complete teach
        """

        reply = QMessageBox.question(
            self,
            "Confirm Package",
            "Is the package location correct?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Save package ROI
            self.inspection_parameters.package_x = roi.x
            self.inspection_parameters.package_y = roi.y
            self.inspection_parameters.package_w = roi.w
            self.inspection_parameters.package_h = roi.h

            self.teach_phase = TeachPhase.DONE

            QMessageBox.information(
                self,
                "Teach Complete",
                "Teach process completed successfully.\nClick OK to finish."
            )

            self._exit_teach_mode()
        else:
            # Retry package teach
            self._start_package_roi()

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

    def _on_track_changed(self, index: int):
        self.state.track = index + 1
        print(f"Active Track: Track{self.state.track}")

        # iTrue behavior: reset to FEED
        self.state.station = Station.FEED
        self._update_station_ui()
        self._apply_run_state()
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

        self._show_image(rotated)
    def _show_image(self, image):
        self.current_image = image
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        self._display_pixmap(pix)


    # =================================================
    # STUB
    # =================================================
    def _stub(self, name: str):
        QMessageBox.information(self, name, f"{name}\n\n(Not implemented yet)")
