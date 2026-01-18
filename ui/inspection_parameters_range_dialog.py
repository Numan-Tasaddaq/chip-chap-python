# ui/inspection_parameters_range_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QLabel, QGridLayout, QLineEdit,
    QPushButton, QCheckBox
)
from PySide6.QtCore import Qt
from config.inspection_parameters_io import save_parameters

class InspectionParametersRangeDialog(QDialog):
    """
    UI-only recreation of:
    Inspection Parameters Range - Track1

    - Default tab: Parameter & Measurement
    - Inspection Item Selection tab fully implemented
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Inspection Parameters Range - Track1")
        self.resize(950, 700)
        self.setWindowFlags(
        self.windowFlags()
        | Qt.Window
        | Qt.WindowMinMaxButtonsHint
    )
        self._numeric_fields: dict[str, QLineEdit] = {}
        self._inspection_checkboxes: dict[str, QCheckBox] = {}


        self._build_ui()

    # -------------------------------------------------
    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tabs (order matches real software)
        self.tab_param = self._parameter_measurement_tab()
        self.tabs.addTab(self.tab_param, "Parameter & Measurement")
        self.tabs.addTab(self._pkg_loc_cam_tab(), "Pkg Loc & Cam Setup")
        self.tabs.addTab(self._tqs_tab(), "TQS Range")
        self.tabs.addTab(self._body_inspection_range_tab(), "Body Inspection Range")
        self.tabs.addTab(self._terminal_inspection_range_tab(), "Terminal Inspection Range")
        self.tabs.addTab(self._inspection_item_selection_tab(), "Inspection Item Selection")
        

        # Default tab
        self.tabs.setCurrentWidget(self.tab_param)
        # LOAD STORED VALUES INTO UI
        self._load_from_model()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_apply = QPushButton("Apply")

        btn_ok.clicked.connect(self._on_ok)
        btn_apply.clicked.connect(self._on_apply)
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_apply)

        main_layout.addLayout(btn_row)
        

    # =================================================
    # TAB: Parameter & Measurement
    # =================================================
    def _parameter_measurement_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # ---------------- Unit Parameter ----------------
        grp_unit = QGroupBox("Unit Parameter")
        g = QGridLayout(grp_unit)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(8)

        g.addWidget(QLabel(""), 0, 0)
        g.addWidget(QLabel("Min"), 0, 1, Qt.AlignCenter)
        g.addWidget(QLabel("Max"), 0, 2, Qt.AlignCenter)
        g.addWidget(QLabel(""), 0, 3)
        g.addWidget(QLabel("Min"), 0, 4, Qt.AlignCenter)
        g.addWidget(QLabel("Max"), 0, 5, Qt.AlignCenter)

        g.addWidget(QLabel("Body Length:"), 1, 0)
        self.body_length_min = QLineEdit("120")
        self.body_length_max = QLineEdit("200")
        self._numeric_fields["body_length_min"] = self.body_length_min
        self._numeric_fields["body_length_max"] = self.body_length_max

        g.addWidget(self.body_length_min, 1, 1)
        g.addWidget(self.body_length_max, 1, 2)

        g.addWidget(QLabel("Body Width:"), 2, 0)
        self.body_width_min = QLineEdit("50")
        self.body_width_max = QLineEdit("100")
        self._numeric_fields["body_width_min"] = self.body_width_min
        self._numeric_fields["body_width_max"] = self.body_width_max

        g.addWidget(self.body_width_min, 2, 1)
        g.addWidget(self.body_width_max, 2, 2)

        pkg_loc_min = QLineEdit("40")
        pkg_loc_max = QLineEdit("120")

        g.addWidget(QLabel("Pkg Loc:"), 3, 0)
        g.addWidget(pkg_loc_min, 3, 1)
        g.addWidget(pkg_loc_max, 3, 2)

        self._numeric_fields["pkg_loc_min"] = pkg_loc_min
        self._numeric_fields["pkg_loc_max"] = pkg_loc_max


        terminal_length_min = QLineEdit("20")
        terminal_length_max = QLineEdit("70")

        g.addWidget(QLabel("Terminal Length:"), 1, 3)
        g.addWidget(terminal_length_min, 1, 4)
        g.addWidget(terminal_length_max, 1, 5)

        self._numeric_fields["terminal_length_min"] = terminal_length_min
        self._numeric_fields["terminal_length_max"] = terminal_length_max

        g.addWidget(QLabel("Terminal Width:"), 2, 3)
        self.terminal_width_min = QLineEdit("50")
        self.terminal_width_max = QLineEdit("100")
        self._numeric_fields["terminal_width_min"] = self.terminal_width_min
        self._numeric_fields["terminal_width_max"] = self.terminal_width_max

        g.addWidget(self.terminal_width_min, 2, 4)
        g.addWidget(self.terminal_width_max, 2, 5)

        term_term_length_min = QLineEdit("20")
        term_term_length_max = QLineEdit("180")

        g.addWidget(QLabel("Term-Term Length:"), 3, 3)
        g.addWidget(term_term_length_min, 3, 4)
        g.addWidget(term_term_length_max, 3, 5)

        self._numeric_fields["term_term_length_min"] = term_term_length_min
        self._numeric_fields["term_term_length_max"] = term_term_length_max

        tt_diff_min = QLineEdit("1")
        tt_diff_max = QLineEdit("20")

        g.addWidget(QLabel("Term-Term Length Max-Min:"), 4, 3)
        g.addWidget(tt_diff_min, 4, 4)
        g.addWidget(tt_diff_max, 4, 5)

        self._numeric_fields["term_term_length_diff_min"] = tt_diff_min
        self._numeric_fields["term_term_length_diff_max"] = tt_diff_max


        g.setColumnStretch(0, 2)
        g.setColumnStretch(3, 2)

        layout.addWidget(grp_unit)

        # ---------------- Dimension Measurement ----------------
        grp_dim = QGroupBox("Dimension Measurement")
        g2 = QGridLayout(grp_dim)

        g2.addWidget(QLabel(""), 0, 0)
        g2.addWidget(QLabel("Min"), 0, 1, Qt.AlignCenter)
        g2.addWidget(QLabel("Max"), 0, 2, Qt.AlignCenter)
        g2.addWidget(QLabel(""), 0, 3)
        g2.addWidget(QLabel("Min"), 0, 4, Qt.AlignCenter)
        g2.addWidget(QLabel("Max"), 0, 5, Qt.AlignCenter)

        bc_min = QLineEdit("5")
        bc_max = QLineEdit("100")

        g2.addWidget(QLabel("Body Contrast:"), 1, 0)
        g2.addWidget(bc_min, 1, 1)
        g2.addWidget(bc_max, 1, 2)

        self._numeric_fields["body_contrast_min"] = bc_min
        self._numeric_fields["body_contrast_max"] = bc_max

        tc_min = QLineEdit("6")
        tc_max = QLineEdit("20")

        g2.addWidget(QLabel("Terminal Contrast:"), 2, 0)
        g2.addWidget(tc_min, 2, 1)
        g2.addWidget(tc_max, 2, 2)

        self._numeric_fields["terminal_contrast_min"] = tc_min
        self._numeric_fields["terminal_contrast_max"] = tc_max

        ep_min = QLineEdit("6")
        ep_max = QLineEdit("20")

        g2.addWidget(QLabel("No. Of Pixels Used for Detecting Edge:"), 3, 0)
        g2.addWidget(ep_min, 3, 1)
        g2.addWidget(ep_max, 3, 2)

        self._numeric_fields["edge_pixel_count_min"] = ep_min
        self._numeric_fields["edge_pixel_count_max"] = ep_max

        mc_min = QLineEdit("6")
        mc_max = QLineEdit("20")

        g2.addWidget(QLabel("No. Of Measurement:"), 4, 0)
        g2.addWidget(mc_min, 4, 1)
        g2.addWidget(mc_max, 4, 2)

        self._numeric_fields["measurement_count_min"] = mc_min
        self._numeric_fields["measurement_count_max"] = mc_max


        tso_min = QLineEdit("6")
        tso_max = QLineEdit("20")

        g2.addWidget(QLabel("Terminal Search Offset:"), 1, 3)
        g2.addWidget(tso_min, 1, 4)
        g2.addWidget(tso_max, 1, 5)

        self._numeric_fields["terminal_search_offset_min"] = tso_min
        self._numeric_fields["terminal_search_offset_max"] = tso_max
        top_offset_min = QLineEdit("5")
        top_offset_max = QLineEdit("20")

        g2.addWidget(QLabel("Top Offset:"), 2, 3)
        g2.addWidget(top_offset_min, 2, 4)
        g2.addWidget(top_offset_max, 2, 5)

        self._numeric_fields["top_offset_min"] = top_offset_min
        self._numeric_fields["top_offset_max"] = top_offset_max

        bottom_offset_min = QLineEdit("5")
        bottom_offset_max = QLineEdit("20")

        g2.addWidget(QLabel("Bottom Offset:"), 3, 3)
        g2.addWidget(bottom_offset_min, 3, 4)
        g2.addWidget(bottom_offset_max, 3, 5)

        self._numeric_fields["bottom_offset_min"] = bottom_offset_min
        self._numeric_fields["bottom_offset_max"] = bottom_offset_max


        layout.addWidget(grp_dim)

        # ---------------- Image Quality Check ----------------
        grp_img = QGroupBox("Image Quality Check")
        g3 = QGridLayout(grp_img)
        g3.setHorizontalSpacing(16)
        g3.setVerticalSpacing(8)

# Header row
        g3.addWidget(QLabel(""), 0, 0)
        g3.addWidget(QLabel("Min"), 0, 1, Qt.AlignCenter)
        g3.addWidget(QLabel("Max"), 0, 2, Qt.AlignCenter)
        g3.addWidget(QLabel(""), 0, 3)
        g3.addWidget(QLabel("Min"), 0, 4, Qt.AlignCenter)
        g3.addWidget(QLabel("Max"), 0, 5, Qt.AlignCenter)

# Body Intensity row
        bi_min = QLineEdit("0")
        bi_max = QLineEdit("255")

        g3.addWidget(QLabel("Body Intensity:"), 1, 0)
        g3.addWidget(bi_min, 1, 1)
        g3.addWidget(bi_max, 1, 2)

        self._numeric_fields["body_intensity_min"] = bi_min
        self._numeric_fields["body_intensity_max"] = bi_max


# Terminal Intensity row
        ti_min = QLineEdit("0")
        ti_max = QLineEdit("255")

        g3.addWidget(QLabel("Terminal Intensity:"), 1, 3)
        g3.addWidget(ti_min, 1, 4)
        g3.addWidget(ti_max, 1, 5)

        self._numeric_fields["terminal_intensity_min"] = ti_min
        self._numeric_fields["terminal_intensity_max"] = ti_max


        layout.addWidget(grp_img)
        layout.addStretch()
        return tab

    # =================================================
    # TAB: Body Inspection Range
    # =================================================
    def _body_inspection_range_tab(self):
        tab = QWidget()
        grid = QGridLayout(tab)

        grid.addWidget(
    self._minmax_group(
        "Body Smear",
        key_prefix="body_smear"
    ),
    0, 0
)

        grid.addWidget(
            self._minmax_group(
                "Body Stain",
                key_prefix="body_stain"
            ),
            0, 1
        )

        grid.addWidget(
            self._minmax_group(
                "Body Edge Chipoff (Black)",
                key_prefix="body_edge_chipoff_black",
                short=True
            ),
            1, 0
        )

        grid.addWidget(
            self._minmax_group(
                "Body Edge Chipoff (White)",
                key_prefix="body_edge_chipoff_white",
                short=True
            ),
            1, 1
        )


        grid.setRowStretch(2, 1)
        return tab

    # =================================================
    # TAB: Terminal Inspection Range
    # =================================================
    def _terminal_inspection_range_tab(self):
        tab = QWidget()
        grid = QGridLayout(tab)

        grid.addWidget(
    self._minmax_group(
        "Terminal Pogo",
        key_prefix="terminal_pogo"
    ),
    0, 0
)

        grid.addWidget(
            self._minmax_group(
                "Incomplete Termination",
                key_prefix="incomplete_termination"
            ),
            0, 1
        )

        grid.addWidget(
            self._minmax_group(
                "Terminal Chipoff (Inner)",
                key_prefix="terminal_chipoff_inner",
                short=True
            ),
            1, 0
        )

        grid.addWidget(
            self._minmax_group(
                "Terminal Chipoff (Outer)",
                key_prefix="terminal_chipoff_outer",
                short=True
            ),
            1, 1
        )


        grid.setRowStretch(2, 1)
        return tab

    
    # =================================================
# TAB: Pkg Loc & Cam Setup (REFINED UI)
# =================================================
    def _pkg_loc_cam_tab(self):
        tab = QWidget()
        root = QGridLayout(tab)
        root.setHorizontalSpacing(20)
        root.setVerticalSpacing(16)

        # ---------------- Package Location Parameter ----------------
        grp_pkg = QGroupBox("Package Location Parameter")
        g1 = QGridLayout(grp_pkg)
        g1.setHorizontalSpacing(12)
        g1.setVerticalSpacing(6)

        g1.addWidget(QLabel(""), 0, 0)
        g1.addWidget(QLabel("Min"), 0, 1, Qt.AlignCenter)
        g1.addWidget(QLabel("Max"), 0, 2, Qt.AlignCenter)

        self._row(g1, 1, "Contrast:", 0, 50,
          key_prefix="pkg_loc_contrast")

        self._row(g1, 2, "X Package Shift Tol:", 20, 100,
                key_prefix="pkg_loc_x_shift_tol")

        self._row(g1, 3, "Y Package Shift Tol:", 20, 100,
                key_prefix="pkg_loc_y_shift_tol")

        self._row(g1, 4, "X Sampling Size:", 1, 4,
                key_prefix="pkg_loc_x_sampling")

        self._row(g1, 5, "Y Sampling Size:", 1, 4,
                key_prefix="pkg_loc_y_sampling")

        self._row(g1, 6, "Max Parallel Angle Tol:", 5, 25,
                key_prefix="pkg_loc_parallel_angle_tol")

        self._row(g1, 7, "Terminal Height Difference:", 5, 20,
                key_prefix="pkg_loc_terminal_height_diff")


        # ---------------- Pocket Location Parameter ----------------
        grp_pocket = QGroupBox("Pocket Location Parameter")
        g2 = QGridLayout(grp_pocket)
        g2.setHorizontalSpacing(12)
        g2.setVerticalSpacing(6)

        g2.addWidget(QLabel(""), 0, 0)
        g2.addWidget(QLabel("Min"), 0, 1, Qt.AlignCenter)
        g2.addWidget(QLabel("Max"), 0, 2, Qt.AlignCenter)

        self._row(g2, 1, "Pocket Length:", 50, 200,
          key_prefix="pocket_loc_length")

        self._row(g2, 2, "Pocket Width:", 30, 150,
                key_prefix="pocket_loc_width")

        self._row(g2, 3, "Outer Stain Contrast:", 5, 20,
                key_prefix="pocket_loc_outer_stain_contrast")

        self._row(g2, 4, "Outer Stain Min Area:", 10, 100,
                key_prefix="pocket_loc_outer_stain_min_area")

        self._row(g2, 5, "Outer Stain Min Sqr Size:", 1, 50,
                key_prefix="pocket_loc_outer_stain_min_sqr")

        self._row(g2, 6, "Outer Stain Insp Width:", 5, 30,
                key_prefix="pocket_loc_outer_stain_insp_width")

        self._row(g2, 7, "Outer Stain Insp Offset:", 2, 20,
                key_prefix="pocket_loc_outer_stain_insp_offset")


        # ---------------- Camera Setup ----------------
        grp_cam = QGroupBox("Camera Setup")
        g3 = QGridLayout(grp_cam)
        g3.setHorizontalSpacing(12)
        g3.setVerticalSpacing(6)

        g3.addWidget(QLabel(""), 0, 0)
        g3.addWidget(QLabel("Min"), 0, 1, Qt.AlignCenter)
        g3.addWidget(QLabel("Max"), 0, 2, Qt.AlignCenter)

        self._row(g3, 1, "Shutter:", 2, 1000,
          key_prefix="camera_shutter")

        self._row(g3, 2, "Gain:", 2, 800,
                key_prefix="camera_gain")

        self._row(g3, 3, "Brightness:", 0, 1,
                key_prefix="camera_brightness")


        # ---------------- Layout placement ----------------
        root.addWidget(grp_pkg, 0, 0)
        root.addWidget(grp_pocket, 0, 1)
        root.addWidget(grp_cam, 1, 0)

        # Stretch to match original empty space
        root.setColumnStretch(0, 1)
        root.setColumnStretch(1, 1)
        root.setRowStretch(2, 1)

        return tab
    # =================================================
    # TAB: TQS Range (EXACT GROUP MATCH)
    # =================================================
    def _tqs_tab(self):
        tab = QWidget()
        root = QGridLayout(tab)
        root.setHorizontalSpacing(24)
        root.setVerticalSpacing(12)

        # ================= LEFT COLUMN =================
        left_col = QVBoxLayout()

        # ---- Pick Up ----
        grp_pick = QGroupBox("Pick Up")
        g1 = QGridLayout(grp_pick)
        g1.setHorizontalSpacing(10)
        g1.setVerticalSpacing(6)

        g1.addWidget(QLabel(""), 0, 0)
        g1.addWidget(QLabel("Min"), 0, 1, Qt.AlignCenter)
        g1.addWidget(QLabel("Max"), 0, 2, Qt.AlignCenter)

        self._row(
        g1, 1, "Pocket Gap:", 1, 50,
        key_prefix="tqs_pickup_pocket_gap_1"
    )
        self._row(
            g1, 2, "Pocket Gap:", 1, 50,
            key_prefix="tqs_pickup_pocket_gap_2"
    )


        left_col.addWidget(grp_pick)

        # ---- Sealing Stain Inspection ----
        grp_stain = QGroupBox("Sealing Stain Inspection")
        g2 = QGridLayout(grp_stain)
        g2.setHorizontalSpacing(10)
        g2.setVerticalSpacing(6)

        g2.addWidget(QLabel(""), 0, 0)
        g2.addWidget(QLabel("Min"), 0, 1, Qt.AlignCenter)
        g2.addWidget(QLabel("Max"), 0, 2, Qt.AlignCenter)

        self._row(
        g2, 1, "Contrast:", 1, 200,
        key_prefix="tqs_sealing_stain_contrast"
    )
        self._row(
            g2, 2, "Min Area:", 10, 2000,
            key_prefix="tqs_sealing_stain_min_area"
        )
        self._row(
            g2, 3, "Min Sqr Size:", 2, 10,
            key_prefix="tqs_sealing_stain_min_sqr"
        )


        left_col.addWidget(grp_stain)

        # ---- Inspection Width ----
        grp_width = QGroupBox("Inspection Width")
        g3 = QGridLayout(grp_width)
        g3.setHorizontalSpacing(10)
        g3.setVerticalSpacing(6)

        g3.addWidget(QLabel("Left:"), 0, 0)
        left_min = QLineEdit("50")
        left_max = QLineEdit("100")

        g3.addWidget(left_min, 0, 1)
        g3.addWidget(left_max, 0, 2)

        self._numeric_fields["tqs_insp_width_left_min"] = left_min
        self._numeric_fields["tqs_insp_width_left_max"] = left_max


        g3.addWidget(QLabel("Top:"), 1, 0)
        top_min = QLineEdit("50")
        top_max = QLineEdit("100")

        g3.addWidget(top_min, 1, 1)
        g3.addWidget(top_max, 1, 2)

        self._numeric_fields["tqs_insp_width_top_min"] = top_min
        self._numeric_fields["tqs_insp_width_top_max"] = top_max


        g3.addWidget(QLabel("Right:"), 2, 0)
        right_min = QLineEdit("50")
        right_max = QLineEdit("100")

        g3.addWidget(right_min, 2, 1)
        g3.addWidget(right_max, 2, 2)

        self._numeric_fields["tqs_insp_width_right_min"] = right_min
        self._numeric_fields["tqs_insp_width_right_max"] = right_max


        g3.addWidget(QLabel("Bottom:"), 3, 0)
        bottom_min = QLineEdit("50")
        bottom_max = QLineEdit("100")

        g3.addWidget(bottom_min, 3, 1)
        g3.addWidget(bottom_max, 3, 2)

        self._numeric_fields["tqs_insp_width_bottom_min"] = bottom_min
        self._numeric_fields["tqs_insp_width_bottom_max"] = bottom_max


        left_col.addWidget(grp_width)
        left_col.addStretch()

        # ================= RIGHT COLUMN =================
        right_col = QVBoxLayout()

        # ---- Sealing Shift Inspection ----
        grp_shift = QGroupBox("Sealing Shift Inspection")
        g4 = QGridLayout(grp_shift)
        g4.setHorizontalSpacing(10)
        g4.setVerticalSpacing(6)

        g4.addWidget(QLabel(""), 0, 0)
        g4.addWidget(QLabel("Min"), 0, 1, Qt.AlignCenter)
        g4.addWidget(QLabel("Max"), 0, 2, Qt.AlignCenter)

        self._row(
    g4, 1, "Contrast Left:", 1, 200,
    key_prefix="tqs_sealing_shift_contrast_left"
)
        self._row(
            g4, 2, "Contrast Right:", 1, 200,
            key_prefix="tqs_sealing_shift_contrast_right"
        )
        self._row(
            g4, 3, "Tolerance Left:", 1, 30,
            key_prefix="tqs_sealing_shift_tol_left"
        )
        self._row(
            g4, 4, "Tolerance Right:", 1, 30,
            key_prefix="tqs_sealing_shift_tol_right"
        )


        right_col.addWidget(grp_shift)

        # ---- Hole Side Shift ----
        grp_hole = QGroupBox("Hole Side Shift")
        g5 = QGridLayout(grp_hole)
        g5.setHorizontalSpacing(10)
        g5.setVerticalSpacing(6)

        g5.addWidget(QLabel(""), 0, 0)
        g5.addWidget(QLabel("Min"), 0, 1, Qt.AlignCenter)
        g5.addWidget(QLabel("Max"), 0, 2, Qt.AlignCenter)

        self._row(
    g5, 1, "Contrast:", 50, 200,
    key_prefix="tqs_hole_shift_contrast"
)
        self._row(
            g5, 2, "Min Width:", 50, 150,
            key_prefix="tqs_hole_shift_min_width"
        )


        right_col.addWidget(grp_hole)
        right_col.addStretch()

        # ================= PLACE COLUMNS =================
        root.addLayout(left_col, 0, 0)
        root.addLayout(right_col, 0, 1)

        root.setColumnStretch(0, 1)
        root.setColumnStretch(1, 1)

        return tab

    # =================================================
    # TAB: Inspection Item Selection (EXACT MATCH)
    # =================================================
    def _inspection_item_selection_tab(self) -> QWidget:
        tab = QWidget()
        root = QVBoxLayout(tab)
        root.setSpacing(10)

        # ---------------- Package & Pocket Location ----------------
        grp_pkg = QGroupBox("Package & Pocket Location Parameters")
        h = QHBoxLayout(grp_pkg)
        self.chk_package_location = QCheckBox("Package Location Inspection")
        self.chk_pocket_location = QCheckBox("Pocket Location Inspection")
        self.chk_pocket_post_seal = QCheckBox("Pocket Post Seal")

        h.addWidget(self.chk_package_location)
        h.addWidget(self.chk_pocket_location)
        h.addWidget(self.chk_pocket_post_seal)

        self._inspection_checkboxes.update({
            "enable_package_location": self.chk_package_location,
            "enable_pocket_location": self.chk_pocket_location,
            "enable_pocket_post_seal": self.chk_pocket_post_seal,
        })

        h.addStretch()
        root.addWidget(grp_pkg)

       # ---------------- Dimension Measurement ----------------
        grp_dim = QGroupBox("Dimension Measurement")
        g_dim = QGridLayout(grp_dim)
        g_dim.setHorizontalSpacing(30)

        self.chk_body_length = QCheckBox("Body Length")
        self.chk_terminal_width = QCheckBox("Terminal Width")
        self.chk_term_term_length = QCheckBox("Term-Term Length")
        self.chk_body_width = QCheckBox("Body Width")
        self.chk_terminal_length = QCheckBox("Terminal Length")
        self.chk_adjust_pkgloc = QCheckBox("Adjust PkgLoc By Body Height")

        self._inspection_checkboxes.update({
    "check_body_length": self.chk_body_length,
    "check_terminal_width": self.chk_terminal_width,
    "check_term_term_length": self.chk_term_term_length,
    "check_body_width": self.chk_body_width,
    "check_terminal_length": self.chk_terminal_length,
    "adjust_pkgloc_by_body_height": self.chk_adjust_pkgloc,
})


        root.addWidget(grp_dim)


        # ---------------- Main Grid ----------------
        mid = QGridLayout()
        mid.setHorizontalSpacing(16)
        mid.setVerticalSpacing(12)

        # ===== COLUMN 1 =====
        mid.addWidget(self._check_group("Terminal Inspection", [
    ("Terminal Pogo", "check_terminal_pogo"),
    ("Incomplete Termination 1", "check_incomplete_termination_1"),
    ("Incomplete Termination 2", "check_incomplete_termination_2"),
    ("Terminal Length Difference", "check_terminal_length_diff"),
    ("Terminal to Body Gap", "check_terminal_to_body_gap"),
    ("Terminal Color", "check_terminal_color"),
    ("Terminal Oxidation", "check_terminal_oxidation"),
]), 0, 0)


        mid.addWidget(self._check_group("Body Crack", [
    ("Body Crack", "check_body_crack"),
    ("Low And High Contrast Reject", "check_low_high_contrast"),
    ("Black Defect", "check_black_defect"),
    ("White Defect", "check_white_defect"),
]), 1, 0)


        mid.addWidget(self._check_group("Body Inspection", [
    ("Body Stain 1", "check_body_stain_1"),
    ("Body Stain 2", "check_body_stain_2"),
    ("Body Color", "check_body_color"),
    ("Body to Term Body Width", "check_body_to_term_width"),
    ("Body Width Difference", "check_body_width_diff"),
]), 2, 0)


        # ===== COLUMN 2 =====
        mid.addWidget(self._check_group("Terminal Chipoff", [
    ("Inner Term Chipoff", "check_inner_term_chipoff"),
    ("Outer Term Chipoff", "check_outer_term_chipoff"),
]), 0, 1)


        mid.addWidget(self._check_group("Inspection Width", [
    ("Left", "check_insp_width_left"),
    ("Right", "check_insp_width_right"),
    ("Top", "check_insp_width_top"),
    ("Bottom", "check_insp_width_bottom"),
]), 1, 1)


        mid.addWidget(self._check_group("Body Smear", [
    ("Body Smear 1", "check_body_smear_1"),
    ("Body Smear 2", "check_body_smear_2"),
    ("Body Smear 3", "check_body_smear_3"),
    ("Reverse Chip Check", "check_reverse_chip"),
    ("White", "check_smear_white"),
]), 2, 1)


        # ===== COLUMN 3 =====
        mid.addWidget(self._check_group("Body Edge Inspection", [
    ("Body Edge Black Defect", "check_body_edge_black"),
    ("Body Edge White Defect", "check_body_edge_white"),
]), 0, 2)


        # ===== COLUMN 4 =====
        mid.addWidget(self._check_group("TQS Inspection", [
    ("Enable Sealing Stain", "enable_sealing_stain"),
    ("Enable Sealing Stain2", "enable_sealing_stain2"),
    ("Enable Sealing Shift", "enable_sealing_shift"),
    ("Black To White Scar", "enable_black_to_white_scar"),
    ("Hole Reference", "enable_hole_reference"),
    ("White To Black Scan", "enable_white_to_black_scan"),
    ("Enable Emboss Tape Pick Up", "enable_emboss_tape_pickup"),
]), 0, 3, 2, 1)


        # ---- Auto Fill Parameters ----
        grp_auto = QGroupBox("Auto Fill Parameters")
        g_auto = QGridLayout(grp_auto)
        g_auto.setHorizontalSpacing(10)

        g_auto.addWidget(QLabel(""), 0, 0)
        g_auto.addWidget(QLabel("Min"), 0, 1)
        g_auto.addWidget(QLabel("Max"), 0, 2)

        auto_items = [
            "Body Length",
            "Terminal Width",
            "Terminal Length",
            "Term to Term Length"
        ]
        for i, txt in enumerate(auto_items, start=1):
            chk = QCheckBox(txt)
            g_auto.addWidget(chk, i, 0)

            field_map = {
                "Body Length": "auto_body_length",
                "Terminal Width": "auto_terminal_width",
                "Terminal Length": "auto_terminal_length",
                "Term to Term Length": "auto_term_term_length",
            }

            self._inspection_checkboxes[field_map[txt]] = chk

            g_auto.addWidget(QLineEdit("20"), i, 1)
            g_auto.addWidget(QLineEdit("20"), i, 2)

        mid.addWidget(grp_auto, 2, 3)

        root.addLayout(mid)
        root.addStretch()

        return tab
    
        



    # =================================================
    # HELPERS
    # =================================================
    def _minmax_group(self, title, key_prefix=None, short=False):
        grp = QGroupBox(title)
        g = QGridLayout(grp)

        g.addWidget(QLabel(""), 0, 0)
        g.addWidget(QLabel("Min"), 0, 1)
        g.addWidget(QLabel("Max"), 0, 2)

        rows = ["contrast", "min_area", "min_sqr_size"]
        if not short:
            rows += ["top", "bottom", "left", "right"]

        for r, field in enumerate(rows, start=1):
            label = field.replace("_", " ").title() + ":"
            g.addWidget(QLabel(label), r, 0)

            min_edit = QLineEdit("1")
            max_edit = QLineEdit("20")

            g.addWidget(min_edit, r, 1)
            g.addWidget(max_edit, r, 2)

            # ✅ Only register fields if key_prefix is provided
            if key_prefix is not None:
                self._numeric_fields[f"{key_prefix}_{field}_min"] = min_edit
                self._numeric_fields[f"{key_prefix}_{field}_max"] = max_edit

        return grp



        


    def _row(
    self,
    grid,
    row,
    label,
    vmin,
    vmax,
    key_prefix=None,
    col=0
):
        """
        If key_prefix is provided → values are saved
        If key_prefix is None → UI-only row
        """
        grid.addWidget(QLabel(label), row, col)

        min_edit = QLineEdit(str(vmin))
        max_edit = QLineEdit(str(vmax))

        grid.addWidget(min_edit, row, col + 1)
        grid.addWidget(max_edit, row, col + 2)

        if key_prefix is not None:
            self._numeric_fields[f"{key_prefix}_min"] = min_edit
            self._numeric_fields[f"{key_prefix}_max"] = max_edit


    def _check_group(self, title: str, items: list[tuple[str, str]]) -> QGroupBox:
        """
        items = [(checkbox_label, dataclass_field_name)]
        """
        grp = QGroupBox(title)
        layout = QVBoxLayout(grp)

        for label, field_name in items:
            chk = QCheckBox(label)
            layout.addWidget(chk)

            # REGISTER CHECKBOX
            self._inspection_checkboxes[field_name] = chk

        return grp
   

    

    def _apply_to_model(self):
        ip = self.parent().inspection_parameters

        # ---- numeric fields ----
        for key, widget in self._numeric_fields.items():
            try:
                ip.ranges[key] = int(widget.text())
            except ValueError:
                ip.ranges[key] = 0

        # ---- checkbox fields ----
        for key, checkbox in self._inspection_checkboxes.items():
            ip.flags[key] = checkbox.isChecked()

        ip.is_defined = True
        save_parameters(ip)



    def _on_apply(self):
        self._apply_to_model()

    def _on_ok(self):
        self._apply_to_model()
        self.accept()
    def _load_from_model(self):
        ip = self.parent().inspection_parameters

        for key, widget in self._numeric_fields.items():
            widget.setText(str(ip.ranges.get(key, 0)))

        for key, checkbox in self._inspection_checkboxes.items():
            checkbox.setChecked(ip.flags.get(key, False))



