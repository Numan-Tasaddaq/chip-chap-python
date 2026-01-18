from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton,
    QGroupBox, QRadioButton, QSlider
)

from config.device_location_setting_io import (
    load_device_location_setting,
    save_device_location_setting
)

class DeviceLocationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

       

        self.setWindowTitle("Package Location Parameters")

        self.setWindowFlags(
    Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint
)
        self.settings = load_device_location_setting()
        self.checkboxes = {}
        self.numerics = {}
        self.radios = {}
        self.sliders = {}

        self._build_ui()
        self._load_from_settings()

        # Resize to fit available screen (NO scrolling)
        screen = self.screen().availableGeometry()
        self.resize(int(screen.width() * 0.95), int(screen.height() * 0.9))

        # Let Qt fine-tune final size
        self.adjustSize()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(6)
        main.setContentsMargins(6, 6, 6, 6)

        content = QHBoxLayout()
        content.setSpacing(10)

        # =================================================
        # LEFT COLUMN
        # =================================================
        left = QVBoxLayout()
        left.setSpacing(6)

        # ---- Enable options ----
        grp_enable = QGroupBox()
        grp_enable.setContentsMargins(6, 8, 6, 6)
        g = QGridLayout(grp_enable)
        g.setHorizontalSpacing(6)
        g.setVerticalSpacing(4)

        self._add_checkbox("enable_pkg", "Enable Package Location", g, 0, 0, 1, 2)
        self._add_checkbox("teach_pos", "Enable Package Loc As Teach Pos", g, 1, 0, 1, 2)

        self._add_checkbox("enable_edge_scan", "Enable Package Loc Use Edge Scan", g, 2, 0)
        


        self._add_checkbox("enable_reverse_edge", "Enable Reverse Edge Scan", g, 3, 0)
        self._add_numeric("reverse_edge_angle", 180, g, 3, 1)

        self._add_checkbox("enable_4color", "Enable 4 color images", g, 4, 0)
        self._add_numeric("four_color_threshold", 80, g, 4, 1)

        self._add_checkbox("ignore_blue", "Enable Ignore Blue", g, 5, 0)
        self._add_numeric("ignore_blue_threshold", 90, g, 5, 1)


        left.addWidget(grp_enable)

        # ---- Flip Check ----
        grp_flip = QGroupBox("Enable Flip Check")
        grp_flip.setContentsMargins(6, 8, 6, 6)
        g2 = QGridLayout(grp_flip)
        g2.setHorizontalSpacing(6)
        g2.setVerticalSpacing(4)

        self._add_checkbox("flip_white_body", "White Body", g2, 0, 0)
        self._add_checkbox("flip_top", "Top", g2, 0, 1)
        self._add_checkbox("flip_bot", "Bot", g2, 1, 1)

        self._add_numeric("flip_white_tol", 16, g2, 0, 2)
        self._add_numeric("flip_bot_tol", 5, g2, 1, 2)


        left.addWidget(grp_flip)

        # ---- Recheck & Contrast ----
        grp_recheck = QGroupBox()
        grp_recheck.setContentsMargins(6, 8, 6, 6)
        g3 = QGridLayout(grp_recheck)
        g3.setHorizontalSpacing(6)
        g3.setVerticalSpacing(4)

        self._add_checkbox("pkg_loc_recheck", "Enable Pkg Loc Recheck", g3, 0, 0)
        self._add_numeric("pkg_loc_recheck_val", 50, g3, 0, 1)

                # ---- Recheck & Contrast ----
        grp_recheck = QGroupBox()
        grp_recheck.setContentsMargins(6, 8, 6, 6)
        g3 = QGridLayout(grp_recheck)
        g3.setHorizontalSpacing(6)
        g3.setVerticalSpacing(4)

        # Enable recheck
        self._add_checkbox("pkg_loc_recheck", "Enable Pkg Loc Recheck", g3, 0, 0)
        self._add_numeric("pkg_loc_recheck_val", 50, g3, 0, 1)

        # Contrast slider
        g3.addWidget(QLabel("Contrast:"), 1, 0)

        contrast_slider = QSlider(Qt.Horizontal)
        contrast_slider.setRange(0, 255)
        contrast_slider.setValue(0)
        self.sliders["contrast"] = contrast_slider
        g3.addWidget(contrast_slider, 1, 1)

        contrast_value_lbl = QLabel("0")
        contrast_value_lbl.setAlignment(Qt.AlignCenter)
        g3.addWidget(contrast_value_lbl, 1, 2)

        # Live update label
        contrast_slider.valueChanged.connect(
            lambda v: contrast_value_lbl.setText(str(v))
        )
        contrast_value_lbl.setText(str(contrast_slider.value()))

        # Contrast+
        g3.addWidget(QLabel("Contrast+:"), 2, 0)
        self._add_numeric("contrast_plus", 0, g3, 2, 1)





        left.addWidget(grp_recheck)

        # ---- Parameters ----
        grp_param = QGroupBox()
        grp_param.setContentsMargins(6, 8, 6, 6)
        g4 = QGridLayout(grp_param)
        g4.setHorizontalSpacing(6)
        g4.setVerticalSpacing(4)

        fields = [
    ("x_pkg_shift_tol", "X Package Shift Tol:", 50),
    ("y_pkg_shift_tol", "Y Package Shift Tol:", 50),
    ("x_sampling_size", "X Sampling Size:", 4),
    ("y_sampling_size", "Y Sampling Size:", 4),
    ("max_parallel_angle", "Max Parallel Angle Tol:", 10),
    ("terminal_height_diff", "Terminal Height Difference:", 10),
    ("edge_scan_part_size", "Edge Scan Part Size:", 4),
    ("dilate_size", "Dilate Size:", 0),
]

        for i, (key, label, default) in enumerate(fields):
            g4.addWidget(QLabel(label), i, 0)
            self._add_numeric(key, default, g4, i, 1)


        left.addWidget(grp_param)

        # ---- Index Gap Inspection ----
        grp_index = QGroupBox("Index Gap Inspection")
        grp_index.setContentsMargins(6, 8, 6, 6)
        g5 = QGridLayout(grp_index)
        g5.setHorizontalSpacing(6)
        g5.setVerticalSpacing(4)

        self._add_checkbox("index_gap_enable", "Enable", g5, 0, 0)
        g5.addWidget(QLabel("Contrast:"), 0, 1)
        self._add_numeric("index_gap_contrast", 50, g5, 0, 2)

        g5.addWidget(QLabel("Min. Y:"), 1, 1)
        self._add_numeric("index_gap_min_y", 10, g5, 1, 2)


        left.addWidget(grp_index)
        left.addStretch()

        # =================================================
        # RIGHT COLUMN
        # =================================================
        right = QVBoxLayout()
        right.setSpacing(6)

        # ---- Reflection / Red ----
        grp_reflect = QGroupBox()
        grp_reflect.setContentsMargins(6, 8, 6, 6)
        g6 = QGridLayout(grp_reflect)
        g6.setHorizontalSpacing(6)
        g6.setVerticalSpacing(4)

        self._add_checkbox("enable_reflection_mask", "Enable Reflection Mask", g6, 0, 0)
        self._add_checkbox("enable_red_pkg_location", "Enable Red Pkg Location", g6, 1, 0)


        right.addWidget(grp_reflect)

        # ---- Edge Scan Mask ----
        grp_edge = QGroupBox("Edge Scan Mask")
        grp_edge.setContentsMargins(6, 8, 6, 6)
        g7 = QGridLayout(grp_edge)
        g7.setHorizontalSpacing(6)
        g7.setVerticalSpacing(4)

        g7.addWidget(QLabel("Left and Right Y:"), 0, 0)
        self._add_numeric("edge_scan_mask_y", 20, g7, 0, 1)


        right.addWidget(grp_edge)

        # ---- Ignore Scan ----
        grp_ignore = QGroupBox("Ignore Scan")
        grp_ignore.setContentsMargins(6, 8, 6, 6)
        g8 = QGridLayout(grp_ignore)
        g8.setHorizontalSpacing(6)
        g8.setVerticalSpacing(4)

        self._add_checkbox("ignore_top", "Top", g8, 0, 0)
        self._add_checkbox("ignore_left", "Left", g8, 0, 1)
        self._add_checkbox("ignore_bottom", "Bottom", g8, 1, 0)
        self._add_checkbox("ignore_right", "Right", g8, 1, 1)


        right.addWidget(grp_ignore)

        # ---- Mark Inspection ----
        grp_mark = QGroupBox("Mark Inspection")
        grp_mark.setContentsMargins(6, 8, 6, 6)
        v1 = QVBoxLayout(grp_mark)
        v1.setSpacing(4)

        self._add_checkbox_v("mark_reverse", "Enable Reverse", v1)
        self._add_checkbox_v("mark_mix", "Enable Mix", v1)



        right.addWidget(grp_mark)

        # ---- Insp Image ----
        grp_img = QGroupBox("Insp Image")
        grp_img.setContentsMargins(6, 8, 6, 6)
        g9 = QGridLayout(grp_img)
        g9.setHorizontalSpacing(6)
        g9.setVerticalSpacing(4)

        radio_keys = ["merge", "red", "green", "blue", "rg", "rb", "gb"]

        for i, key in enumerate(radio_keys):
            self._add_radio(f"insp_img_{key}", key.upper(), g9, i // 2, i % 2)

        self.radios["insp_img_merge"].setChecked(True)


        right.addWidget(grp_img)

        # ---- Filter Red Mark ----
        grp_filter = QGroupBox("Filter Red Mark")
        grp_filter.setContentsMargins(6, 8, 6, 6)
        g10 = QGridLayout(grp_filter)
        g10.setHorizontalSpacing(6)
        g10.setVerticalSpacing(4)

        self._add_checkbox("filter_red_enable", "Enable", g10, 0, 0)
        g10.addWidget(QLabel("Red:"), 1, 0)
        self._add_numeric("filter_red_value", 100, g10, 1, 1)

        g10.addWidget(QLabel("Green:"), 2, 0)
        self._add_numeric("filter_green_value", 70, g10, 2, 1)


        right.addWidget(grp_filter)

        right.addWidget(QLabel("No. Of Line Mask:"))
        self._add_numeric_v("line_mask_count", 0, right)


        right.addStretch()

        content.addLayout(left, 1)
        content.addLayout(right, 1)
        main.addLayout(content)

        # =================================================
        # BUTTONS
        # =================================================
        btns = QHBoxLayout()
        btns.addStretch()

        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_apply = QPushButton("Apply")

        btn_ok.clicked.connect(self._on_ok)
        btn_apply.clicked.connect(self._on_apply)

        btn_cancel.clicked.connect(self.reject)


        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_apply)

        main.addLayout(btns)

    def _add_checkbox(self, key, text, layout, row, col, rowspan=1, colspan=1):
        cb = QCheckBox(text)
        self.checkboxes[key] = cb
        layout.addWidget(cb, row, col, rowspan, colspan)

    def _add_numeric(self, key, default, layout, row, col):
        le = QLineEdit(str(default))
        le.setAlignment(Qt.AlignCenter)
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

        # Sliders  ✅ IMPORTANT
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
            sl.setValue(self.settings.get(key, sl.value()))
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
        self.numerics[key] = le
        layout.addWidget(le)
    def _add_checkbox_v(self, key, text, layout):
        cb = QCheckBox(text)
        self.checkboxes[key] = cb
        layout.addWidget(cb)

    def _add_numeric_v(self, key, default, layout):
        le = QLineEdit(str(default))
        le.setAlignment(Qt.AlignCenter)
        self.numerics[key] = le
        layout.addWidget(le)

    def _add_radio_v(self, key, text, layout):
        rb = QRadioButton(text)
        self.radios[key] = rb
        layout.addWidget(rb)
