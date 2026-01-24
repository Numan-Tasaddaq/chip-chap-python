from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton,
    QGroupBox, QRadioButton, QSlider, QFrame
)
from PySide6.QtWidgets import QScrollArea, QWidget
from PySide6.QtGui import QFont

from config.device_location_setting_io import (
    load_device_location_setting,
    save_device_location_setting
)

class DeviceLocationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Package Location Parameters")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        # Set a minimum width for better spacing but maintain current height
        self.setMinimumWidth(850)
        
        self.settings = load_device_location_setting()
        self.checkboxes = {}
        self.numerics = {}
        self.radios = {}
        self.sliders = {}
        
        # Apply professional styling
        self._setup_styles()
        self._build_ui()
        self._load_from_settings()

    def _setup_styles(self):
        """Setup professional color palette and fonts"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #374151;
            }
            QLabel {
                color: #374151;
            }
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 3px;
                padding: 4px;
                background-color: white;
                min-height: 24px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
                outline: none;
            }
            QCheckBox {
                spacing: 6px;
                color: #374151;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton {
                spacing: 6px;
                color: #374151;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QPushButton#cancelButton {
                background-color: #6b7280;
            }
            QPushButton#cancelButton:hover {
                background-color: #4b5563;
            }
            QSlider::groove:horizontal {
                border: 1px solid #d1d5db;
                height: 4px;
                background: #e5e7eb;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #3b82f6;
                border: 1px solid #d1d5db;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a8a8a8;
            }
        """)

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(8)

        # ================================
        # SCROLL AREA
        # ================================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(10)
        scroll_layout.setContentsMargins(8, 8, 8, 8)

        scroll.setWidget(scroll_content)

        content = QHBoxLayout()
        content.setSpacing(15)

        # =================================================
        # LEFT COLUMN
        # =================================================
        left = QVBoxLayout()
        left.setSpacing(8)

        # ---- Enable options ----
        grp_enable = QGroupBox("Package Location Settings")
        grp_enable.setContentsMargins(10, 15, 10, 10)
        g = QGridLayout(grp_enable)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(6)

        self._add_checkbox("enable_pkg", "Enable Package Location", g, 0, 0, 1, 2)
        self._add_checkbox("teach_pos", "Use as Teach Position", g, 1, 0, 1, 2)

        # Add a separator line
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFrameShadow(QFrame.Sunken)
        sep1.setStyleSheet("background-color: #e5e7eb;")
        g.addWidget(sep1, 2, 0, 1, 3)

        self._add_checkbox("enable_edge_scan", "Enable Edge Scan", g, 3, 0)
        self._add_checkbox("enable_reverse_edge", "Enable Reverse Edge Scan", g, 4, 0)
        self._add_numeric("reverse_edge_angle", 180, g, 4, 1)
        self._add_checkbox("enable_4color", "Enable 4-Color Images", g, 5, 0)
        self._add_numeric("four_color_threshold", 80, g, 5, 1)
        self._add_checkbox("ignore_blue", "Enable Ignore Blue", g, 6, 0)
        self._add_numeric("ignore_blue_threshold", 90, g, 6, 1)

        left.addWidget(grp_enable)

        # ---- Flip Check ----
        grp_flip = QGroupBox("Flip Detection")
        grp_flip.setContentsMargins(10, 15, 10, 10)
        g2 = QGridLayout(grp_flip)
        g2.setHorizontalSpacing(10)
        g2.setVerticalSpacing(6)

        self._add_checkbox("flip_white_body", "White Body", g2, 0, 0)
        self._add_checkbox("flip_top", "Top", g2, 0, 1)
        self._add_checkbox("flip_bot", "Bottom", g2, 1, 1)
        self._add_numeric("flip_white_tol", 16, g2, 0, 2)
        self._add_numeric("flip_bot_tol", 5, g2, 1, 2)

        left.addWidget(grp_flip)

        # ---- Recheck & Contrast ----
        grp_recheck = QGroupBox("Recheck & Image Processing")
        grp_recheck.setContentsMargins(10, 15, 10, 10)
        g3 = QGridLayout(grp_recheck)
        g3.setHorizontalSpacing(10)
        g3.setVerticalSpacing(6)

        self._add_checkbox("pkg_loc_recheck", "Enable Package Location Recheck", g3, 0, 0)
        self._add_numeric("pkg_loc_recheck_val", 50, g3, 0, 1)

        # Add separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        sep2.setStyleSheet("background-color: #e5e7eb; margin: 5px 0;")
        g3.addWidget(sep2, 1, 0, 1, 3)

        # Contrast slider
        contrast_label = QLabel("Contrast Adjustment:")
        contrast_label.setStyleSheet("font-weight: bold;")
        g3.addWidget(contrast_label, 2, 0)

        contrast_slider = QSlider(Qt.Horizontal)
        contrast_slider.setRange(0, 255)
        contrast_slider.setValue(0)
        self.sliders["contrast"] = contrast_slider
        g3.addWidget(contrast_slider, 2, 1)

        contrast_value_lbl = QLabel("0")
        contrast_value_lbl.setAlignment(Qt.AlignCenter)
        contrast_value_lbl.setStyleSheet("""
            background-color: #f3f4f6;
            border: 1px solid #d1d5db;
            border-radius: 3px;
            padding: 2px 8px;
            min-width: 40px;
        """)
        g3.addWidget(contrast_value_lbl, 2, 2)

        contrast_slider.valueChanged.connect(
            lambda v: contrast_value_lbl.setText(str(v))
        )
        contrast_value_lbl.setText(str(contrast_slider.value()))

        # Contrast+
        g3.addWidget(QLabel("Additional Contrast:"), 3, 0)
        self._add_numeric("contrast_plus", 0, g3, 3, 1)

        left.addWidget(grp_recheck)

        # ---- Parameters ----
        grp_param = QGroupBox("Location Parameters")
        grp_param.setContentsMargins(10, 15, 10, 10)
        g4 = QGridLayout(grp_param)
        g4.setHorizontalSpacing(10)
        g4.setVerticalSpacing(6)

        fields = [
            ("x_pkg_shift_tol", "X Package Shift Tolerance:", 50),
            ("y_pkg_shift_tol", "Y Package Shift Tolerance:", 50),
            ("x_sampling_size", "X Sampling Size:", 4),
            ("y_sampling_size", "Y Sampling Size:", 4),
            ("max_parallel_angle", "Max Parallel Angle Tolerance:", 10),
            ("terminal_height_diff", "Terminal Height Difference:", 10),
            ("edge_scan_part_size", "Edge Scan Part Size:", 4),
            ("dilate_size", "Dilate Size:", 0),
        ]

        for i, (key, label, default) in enumerate(fields):
            label_widget = QLabel(label)
            g4.addWidget(label_widget, i, 0)
            self._add_numeric(key, default, g4, i, 1)

        left.addWidget(grp_param)

        # ---- Index Gap Inspection ----
        grp_index = QGroupBox("Index Gap Inspection")
        grp_index.setContentsMargins(10, 15, 10, 10)
        g5 = QGridLayout(grp_index)
        g5.setHorizontalSpacing(10)
        g5.setVerticalSpacing(6)

        self._add_checkbox("index_gap_enable", "Enable Inspection", g5, 0, 0, 1, 2)
        g5.addWidget(QLabel("Contrast Threshold:"), 1, 0)
        self._add_numeric("index_gap_contrast", 50, g5, 1, 1)
        g5.addWidget(QLabel("Minimum Y Value:"), 2, 0)
        self._add_numeric("index_gap_min_y", 10, g5, 2, 1)

        left.addWidget(grp_index)
        left.addStretch()

        # =================================================
        # RIGHT COLUMN
        # =================================================
        right = QVBoxLayout()
        right.setSpacing(8)

        # ---- Reflection / Red ----
        grp_reflect = QGroupBox("Reflection & Color Processing")
        grp_reflect.setContentsMargins(10, 15, 10, 10)
        g6 = QGridLayout(grp_reflect)
        g6.setHorizontalSpacing(10)
        g6.setVerticalSpacing(6)

        self._add_checkbox("enable_reflection_mask", "Enable Reflection Mask", g6, 0, 0, 1, 2)
        self._add_checkbox("enable_red_pkg_location", "Enable Red Package Location", g6, 1, 0, 1, 2)

        right.addWidget(grp_reflect)

        # ---- Edge Scan Mask ----
        grp_edge = QGroupBox("Edge Scan Mask")
        grp_edge.setContentsMargins(10, 15, 10, 10)
        g7 = QGridLayout(grp_edge)
        g7.setHorizontalSpacing(10)
        g7.setVerticalSpacing(6)

        g7.addWidget(QLabel("Left/Right Y Mask:"), 0, 0)
        self._add_numeric("edge_scan_mask_y", 20, g7, 0, 1)

        right.addWidget(grp_edge)

        # ---- Ignore Scan ----
        grp_ignore = QGroupBox("Ignore Scan Regions")
        grp_ignore.setContentsMargins(10, 15, 10, 10)
        g8 = QGridLayout(grp_ignore)
        g8.setHorizontalSpacing(10)
        g8.setVerticalSpacing(6)

        self._add_checkbox("ignore_top", "Top", g8, 0, 0)
        self._add_checkbox("ignore_left", "Left", g8, 0, 1)
        self._add_checkbox("ignore_bottom", "Bottom", g8, 1, 0)
        self._add_checkbox("ignore_right", "Right", g8, 1, 1)

        right.addWidget(grp_ignore)

        # ---- Mark Inspection ----
        grp_mark = QGroupBox("Mark Inspection Options")
        grp_mark.setContentsMargins(10, 15, 10, 10)
        v1 = QVBoxLayout(grp_mark)
        v1.setSpacing(6)

        self._add_checkbox_v("mark_reverse", "Enable Reverse Mark", v1)
        self._add_checkbox_v("mark_mix", "Enable Mixed Mark", v1)

        right.addWidget(grp_mark)

        # ---- Inspection Image ----
        grp_img = QGroupBox("Inspection Image Mode")
        grp_img.setContentsMargins(10, 15, 10, 10)
        g9 = QGridLayout(grp_img)
        g9.setHorizontalSpacing(10)
        g9.setVerticalSpacing(6)

        radio_keys = ["merge", "red", "green", "blue", "rg", "rb", "gb"]

        for i, key in enumerate(radio_keys):
            self._add_radio(f"insp_img_{key}", key.upper(), g9, i // 2, i % 2)

        self.radios["insp_img_merge"].setChecked(True)

        right.addWidget(grp_img)

        # ---- Filter Red Mark ----
        grp_filter = QGroupBox("Red Mark Filter")
        grp_filter.setContentsMargins(10, 15, 10, 10)
        g10 = QGridLayout(grp_filter)
        g10.setHorizontalSpacing(10)
        g10.setVerticalSpacing(6)

        self._add_checkbox("filter_red_enable", "Enable Filter", g10, 0, 0, 1, 2)
        g10.addWidget(QLabel("Red Threshold:"), 1, 0)
        self._add_numeric("filter_red_value", 100, g10, 1, 1)
        g10.addWidget(QLabel("Green Threshold:"), 2, 0)
        self._add_numeric("filter_green_value", 70, g10, 2, 1)

        right.addWidget(grp_filter)

        # ---- Line Mask ----
        line_mask_label = QLabel("Number of Line Masks:")
        line_mask_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        right.addWidget(line_mask_label)
        self._add_numeric_v("line_mask_count", 0, right)

        right.addStretch()

        content.addLayout(left, 1)
        content.addLayout(right, 1)

        scroll_layout.addLayout(content)
        scroll_layout.addStretch()

        main.addWidget(scroll)

        # =================================================
        # BUTTONS (with improved layout)
        # =================================================
        # Add a separator line above buttons
        button_sep = QFrame()
        button_sep.setFrameShape(QFrame.HLine)
        button_sep.setFrameShadow(QFrame.Sunken)
        button_sep.setStyleSheet("background-color: #d1d5db; margin: 10px 0;")
        main.addWidget(button_sep)

        btns = QHBoxLayout()
        btns.addStretch()

        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_apply = QPushButton("Apply")

        # Set object names for specific styling
        btn_cancel.setObjectName("cancelButton")

        btn_ok.clicked.connect(self._on_ok)
        btn_apply.clicked.connect(self._on_apply)
        btn_cancel.clicked.connect(self.reject)

        # Set consistent button sizes
        for btn in [btn_ok, btn_cancel, btn_apply]:
            btn.setFixedWidth(90)

        btns.addWidget(btn_ok)
        btns.addSpacing(10)
        btns.addWidget(btn_cancel)
        btns.addSpacing(10)
        btns.addWidget(btn_apply)

        main.addLayout(btns)

    def _add_checkbox(self, key, text, layout, row, col, rowspan=1, colspan=1):
        cb = QCheckBox(text)
        self.checkboxes[key] = cb
        layout.addWidget(cb, row, col, rowspan, colspan)

    def _add_numeric(self, key, default, layout, row, col):
        le = QLineEdit(str(default))
        le.setAlignment(Qt.AlignCenter)
        le.setMaximumWidth(80)
        self.numerics[key] = le
        layout.addWidget(le, row, col)

    def _add_radio(self, key, text, layout, row, col):
        rb = QRadioButton(text)
        self.radios[key] = rb
        layout.addWidget(rb, row, col)

    def _apply_settings(self):
        # Checkboxes
        for key, cb in self.checkboxes.items():
            self.settings[key] = cb.isChecked()

        # Numeric fields
        for key, le in self.numerics.items():
            try:
                self.settings[key] = int(le.text())
            except ValueError:
                self.settings[key] = 0

        # Radios
        for key, rb in self.radios.items():
            self.settings[key] = rb.isChecked()

        # Sliders
        for key, sl in self.sliders.items():
            self.settings[key] = int(sl.value())

        save_device_location_setting(self.settings)

    def _load_from_settings(self):
        for key, cb in self.checkboxes.items():
            cb.setChecked(self.settings.get(key, False))

        for key, le in self.numerics.items():
            le.setText(str(self.settings.get(key, le.text())))

        for key, rb in self.radios.items():
            rb.setChecked(self.settings.get(key, False))

        for key, sl in self.sliders.items():
            val = int(self.settings.get(key, sl.value()))
            sl.setValue(val)

    def _on_ok(self):
        self._apply_settings()
        self.accept()

    def _on_apply(self):
        self._apply_settings()

    def _add_checkbox_v(self, key, text, layout):
        cb = QCheckBox(text)
        self.checkboxes[key] = cb
        layout.addWidget(cb)

    def _add_numeric_v(self, key, default, layout):
        le = QLineEdit(str(default))
        le.setAlignment(Qt.AlignCenter)
        le.setMaximumWidth(80)
        self.numerics[key] = le
        layout.addWidget(le)

    def _add_radio_v(self, key, text, layout):
        rb = QRadioButton(text)
        self.radios[key] = rb
        layout.addWidget(rb)