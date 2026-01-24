# ui/inspection_parameters_range_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QLabel, QGridLayout, QLineEdit,
    QPushButton, QCheckBox, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from config.inspection_parameters_io import save_parameters, load_parameters
from config.teach_store import save_teach_data
from PySide6.QtWidgets import QScrollArea
from PySide6.QtGui import QFont

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
        self.resize(1100, 520)
        self.setMinimumHeight(520)
        self.setMaximumHeight(520)

        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        self._numeric_fields: dict[str, QLineEdit] = {}
        self._inspection_checkboxes: dict[str, QCheckBox] = {}

        # Set professional color palette
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 4px;
                background-color: white;
                min-height: 22px;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
                background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                color: #7f8c8d;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #3498db;
                color: #2c3e50;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c5a7d;
            }
            QPushButton#cancelButton {
                background-color: #95a5a6;
            }
            QPushButton#cancelButton:hover {
                background-color: #7f8c8d;
            }
            QCheckBox {
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self._build_ui()

    # -------------------------------------------------
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create a frame for the content to add subtle shadow effect
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        content_layout.addWidget(self.tabs)

        # Tabs (order matches real software)
        self.tab_param = self._parameter_measurement_tab()
        self.tabs.addTab(self._make_scrollable(self.tab_param), "Parameter & Measurement")
        self.tabs.addTab(self._make_scrollable(self._pkg_loc_cam_tab()), "Pkg Loc & Cam Setup")
        self.tabs.addTab(self._make_scrollable(self._tqs_tab()), "TQS Range")
        self.tabs.addTab(self._make_scrollable(self._body_inspection_range_tab()), "Body Inspection Range")
        self.tabs.addTab(self._make_scrollable(self._terminal_inspection_range_tab()), "Terminal Inspection Range")
        self.tabs.addTab(self._make_scrollable(self._inspection_item_selection_tab()), "Inspection Item Selection")

        # Default tab
        self.tabs.setCurrentWidget(self.tab_param)
        # LOAD STORED VALUES INTO UI
        self._load_from_model()

        # Add frame to main layout
        main_layout.addWidget(content_frame)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0; margin: 5px 0;")
        main_layout.addWidget(separator)

        # Buttons with improved layout
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("cancelButton")
        btn_apply = QPushButton("Apply")

        # Set fixed button sizes for consistency
        btn_ok.setFixedSize(90, 32)
        btn_cancel.setFixedSize(90, 32)
        btn_apply.setFixedSize(90, 32)

        btn_ok.clicked.connect(self._on_ok)
        btn_apply.clicked.connect(self._on_apply)
        btn_cancel.clicked.connect(self.reject)

        # Add spacing between buttons
        btn_row.addWidget(btn_apply)
        btn_row.addSpacing(10)
        btn_row.addWidget(btn_ok)
        btn_row.addSpacing(10)
        btn_row.addWidget(btn_cancel)

        main_layout.addLayout(btn_row)

    # =================================================
    # TAB: Parameter & Measurement
    # =================================================
    def _parameter_measurement_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(15, 15, 15, 15)

        # ---------------- Unit Parameter ----------------
        grp_unit = QGroupBox("Unit Parameter")
        grp_unit.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g = QGridLayout(grp_unit)
        g.setHorizontalSpacing(20)
        g.setVerticalSpacing(10)
        g.setContentsMargins(12, 20, 12, 12)

        # Header row with improved styling
        header_font = QFont()
        header_font.setBold(True)
        
        for col, text in enumerate(["", "Min", "Max", "", "Min", "Max"]):
            label = QLabel(text)
            if text in ["Min", "Max"]:
                label.setFont(header_font)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
            g.addWidget(label, 0, col)

        # Body Length
        self.body_length_min = self._create_line_edit("120")
        self.body_length_max = self._create_line_edit("200")
        self._numeric_fields["body_length_min"] = self.body_length_min
        self._numeric_fields["body_length_max"] = self.body_length_max

        g.addWidget(self._create_label("Body Length:"), 1, 0)
        g.addWidget(self.body_length_min, 1, 1)
        g.addWidget(self.body_length_max, 1, 2)

        # Body Width
        self.body_width_min = self._create_line_edit("50")
        self.body_width_max = self._create_line_edit("100")
        self._numeric_fields["body_width_min"] = self.body_width_min
        self._numeric_fields["body_width_max"] = self.body_width_max

        g.addWidget(self._create_label("Body Width:"), 2, 0)
        g.addWidget(self.body_width_min, 2, 1)
        g.addWidget(self.body_width_max, 2, 2)

        # Pkg Loc
        pkg_loc_min = self._create_line_edit("40")
        pkg_loc_max = self._create_line_edit("120")
        g.addWidget(self._create_label("Pkg Loc:"), 3, 0)
        g.addWidget(pkg_loc_min, 3, 1)
        g.addWidget(pkg_loc_max, 3, 2)
        self._numeric_fields["pkg_loc_min"] = pkg_loc_min
        self._numeric_fields["pkg_loc_max"] = pkg_loc_max

        # Terminal Length
        terminal_length_min = self._create_line_edit("20")
        terminal_length_max = self._create_line_edit("70")
        g.addWidget(self._create_label("Terminal Length:"), 1, 3)
        g.addWidget(terminal_length_min, 1, 4)
        g.addWidget(terminal_length_max, 1, 5)
        self._numeric_fields["terminal_length_min"] = terminal_length_min
        self._numeric_fields["terminal_length_max"] = terminal_length_max

        # Terminal Width
        self.terminal_width_min = self._create_line_edit("50")
        self.terminal_width_max = self._create_line_edit("100")
        self._numeric_fields["terminal_width_min"] = self.terminal_width_min
        self._numeric_fields["terminal_width_max"] = self.terminal_width_max
        g.addWidget(self._create_label("Terminal Width:"), 2, 3)
        g.addWidget(self.terminal_width_min, 2, 4)
        g.addWidget(self.terminal_width_max, 2, 5)

        # Term-Term Length
        term_term_length_min = self._create_line_edit("20")
        term_term_length_max = self._create_line_edit("180")
        g.addWidget(self._create_label("Term-Term Length:"), 3, 3)
        g.addWidget(term_term_length_min, 3, 4)
        g.addWidget(term_term_length_max, 3, 5)
        self._numeric_fields["term_term_length_min"] = term_term_length_min
        self._numeric_fields["term_term_length_max"] = term_term_length_max

        # Term-Term Length Max-Min
        tt_diff_min = self._create_line_edit("1")
        tt_diff_max = self._create_line_edit("20")
        g.addWidget(self._create_label("Term-Term Length Max-Min:"), 4, 3)
        g.addWidget(tt_diff_min, 4, 4)
        g.addWidget(tt_diff_max, 4, 5)
        self._numeric_fields["term_term_length_diff_min"] = tt_diff_min
        self._numeric_fields["term_term_length_diff_max"] = tt_diff_max

        g.setColumnStretch(0, 2)
        g.setColumnStretch(3, 2)
        layout.addWidget(grp_unit)

        # ---------------- Dimension Measurement ----------------
        grp_dim = QGroupBox("Dimension Measurement")
        grp_dim.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g2 = QGridLayout(grp_dim)
        g2.setHorizontalSpacing(20)
        g2.setVerticalSpacing(10)
        g2.setContentsMargins(12, 20, 12, 12)

        # Header
        for col, text in enumerate(["", "Min", "Max", "", "Min", "Max"]):
            label = QLabel(text)
            if text in ["Min", "Max"]:
                label.setFont(header_font)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
            g2.addWidget(label, 0, col)

        # Body Contrast
        bc_min = self._create_line_edit("5")
        bc_max = self._create_line_edit("100")
        g2.addWidget(self._create_label("Body Contrast:"), 1, 0)
        g2.addWidget(bc_min, 1, 1)
        g2.addWidget(bc_max, 1, 2)
        self._numeric_fields["body_contrast_min"] = bc_min
        self._numeric_fields["body_contrast_max"] = bc_max

        # Terminal Contrast
        tc_min = self._create_line_edit("6")
        tc_max = self._create_line_edit("20")
        g2.addWidget(self._create_label("Terminal Contrast:"), 2, 0)
        g2.addWidget(tc_min, 2, 1)
        g2.addWidget(tc_max, 2, 2)
        self._numeric_fields["terminal_contrast_min"] = tc_min
        self._numeric_fields["terminal_contrast_max"] = tc_max

        # Edge Pixels
        ep_min = self._create_line_edit("6")
        ep_max = self._create_line_edit("20")
        g2.addWidget(self._create_label("No. Of Pixels Used for Detecting Edge:"), 3, 0)
        g2.addWidget(ep_min, 3, 1)
        g2.addWidget(ep_max, 3, 2)
        self._numeric_fields["edge_pixel_count_min"] = ep_min
        self._numeric_fields["edge_pixel_count_max"] = ep_max

        # Measurement Count
        mc_min = self._create_line_edit("6")
        mc_max = self._create_line_edit("20")
        g2.addWidget(self._create_label("No. Of Measurement:"), 4, 0)
        g2.addWidget(mc_min, 4, 1)
        g2.addWidget(mc_max, 4, 2)
        self._numeric_fields["measurement_count_min"] = mc_min
        self._numeric_fields["measurement_count_max"] = mc_max

        # Terminal Search Offset
        tso_min = self._create_line_edit("6")
        tso_max = self._create_line_edit("20")
        g2.addWidget(self._create_label("Terminal Search Offset:"), 1, 3)
        g2.addWidget(tso_min, 1, 4)
        g2.addWidget(tso_max, 1, 5)
        self._numeric_fields["terminal_search_offset_min"] = tso_min
        self._numeric_fields["terminal_search_offset_max"] = tso_max

        # Top Offset
        top_offset_min = self._create_line_edit("5")
        top_offset_max = self._create_line_edit("20")
        g2.addWidget(self._create_label("Top Offset:"), 2, 3)
        g2.addWidget(top_offset_min, 2, 4)
        g2.addWidget(top_offset_max, 2, 5)
        self._numeric_fields["top_offset_min"] = top_offset_min
        self._numeric_fields["top_offset_max"] = top_offset_max

        # Bottom Offset
        bottom_offset_min = self._create_line_edit("5")
        bottom_offset_max = self._create_line_edit("20")
        g2.addWidget(self._create_label("Bottom Offset:"), 3, 3)
        g2.addWidget(bottom_offset_min, 3, 4)
        g2.addWidget(bottom_offset_max, 3, 5)
        self._numeric_fields["bottom_offset_min"] = bottom_offset_min
        self._numeric_fields["bottom_offset_max"] = bottom_offset_max

        layout.addWidget(grp_dim)

        # ---------------- Image Quality Check ----------------
        grp_img = QGroupBox("Image Quality Check")
        grp_img.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g3 = QGridLayout(grp_img)
        g3.setHorizontalSpacing(20)
        g3.setVerticalSpacing(10)
        g3.setContentsMargins(12, 20, 12, 12)

        # Header
        for col, text in enumerate(["", "Min", "Max", "", "Min", "Max"]):
            label = QLabel(text)
            if text in ["Min", "Max"]:
                label.setFont(header_font)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
            g3.addWidget(label, 0, col)

        # Body Intensity
        bi_min = self._create_line_edit("0")
        bi_max = self._create_line_edit("255")
        g3.addWidget(self._create_label("Body Intensity:"), 1, 0)
        g3.addWidget(bi_min, 1, 1)
        g3.addWidget(bi_max, 1, 2)
        self._numeric_fields["body_intensity_min"] = bi_min
        self._numeric_fields["body_intensity_max"] = bi_max

        # Terminal Intensity
        ti_min = self._create_line_edit("0")
        ti_max = self._create_line_edit("255")
        g3.addWidget(self._create_label("Terminal Intensity:"), 1, 3)
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
        tab.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(15)
        
        grid.addWidget(
            self._styled_minmax_group(
                "Body Smear",
                key_prefix="body_smear"
            ),
            0, 0
        )

        grid.addWidget(
            self._styled_minmax_group(
                "Body Stain",
                key_prefix="body_stain"
            ),
            0, 1
        )

        grid.addWidget(
            self._styled_minmax_group(
                "Body Edge Chipoff (Black)",
                key_prefix="body_edge_chipoff_black",
                short=True
            ),
            1, 0
        )

        grid.addWidget(
            self._styled_minmax_group(
                "Body Edge Chipoff (White)",
                key_prefix="body_edge_chipoff_white",
                short=True
            ),
            1, 1
        )

        layout.addLayout(grid)
        layout.addStretch()
        return tab

    # =================================================
    # TAB: Terminal Inspection Range
    # =================================================
    def _terminal_inspection_range_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(15)
        
        grid.addWidget(
            self._styled_minmax_group(
                "Terminal Pogo",
                key_prefix="terminal_pogo"
            ),
            0, 0
        )

        grid.addWidget(
            self._styled_minmax_group(
                "Incomplete Termination",
                key_prefix="incomplete_termination"
            ),
            0, 1
        )

        grid.addWidget(
            self._styled_minmax_group(
                "Terminal Chipoff (Inner)",
                key_prefix="terminal_chipoff_inner",
                short=True
            ),
            1, 0
        )

        grid.addWidget(
            self._styled_minmax_group(
                "Terminal Chipoff (Outer)",
                key_prefix="terminal_chipoff_outer",
                short=True
            ),
            1, 1
        )

        layout.addLayout(grid)
        layout.addStretch()
        return tab

    # =================================================
    # TAB: Pkg Loc & Cam Setup (REFINED UI)
    # =================================================
    def _pkg_loc_cam_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QVBoxLayout(tab)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(20)

        # Main container with grid
        container = QWidget()
        grid = QGridLayout(container)
        grid.setHorizontalSpacing(30)
        grid.setVerticalSpacing(20)

        # ---------------- Package Location Parameter ----------------
        grp_pkg = self._styled_section("Package Location Parameter", [
            ("Contrast:", 0, 50, "pkg_loc_contrast"),
            ("X Package Shift Tol:", 20, 100, "pkg_loc_x_shift_tol"),
            ("Y Package Shift Tol:", 20, 100, "pkg_loc_y_shift_tol"),
            ("X Sampling Size:", 1, 4, "pkg_loc_x_sampling"),
            ("Y Sampling Size:", 1, 4, "pkg_loc_y_sampling"),
            ("Max Parallel Angle Tol:", 5, 25, "pkg_loc_parallel_angle_tol"),
            ("Terminal Height Difference:", 5, 20, "pkg_loc_terminal_height_diff"),
        ])
        grid.addWidget(grp_pkg, 0, 0)

        # ---------------- Pocket Location Parameter ----------------
        grp_pocket = self._styled_section("Pocket Location Parameter", [
            ("Pocket Length:", 50, 200, "pocket_loc_length"),
            ("Pocket Width:", 30, 150, "pocket_loc_width"),
            ("Outer Stain Contrast:", 5, 20, "pocket_loc_outer_stain_contrast"),
            ("Outer Stain Min Area:", 10, 100, "pocket_loc_outer_stain_min_area"),
            ("Outer Stain Min Sqr Size:", 1, 50, "pocket_loc_outer_stain_min_sqr"),
            ("Outer Stain Insp Width:", 5, 30, "pocket_loc_outer_stain_insp_width"),
            ("Outer Stain Insp Offset:", 2, 20, "pocket_loc_outer_stain_insp_offset"),
        ])
        grid.addWidget(grp_pocket, 0, 1)

        # ---------------- Camera Setup ----------------
        grp_cam = self._styled_section("Camera Setup", [
            ("Shutter:", 2, 1000, "camera_shutter"),
            ("Gain:", 2, 800, "camera_gain"),
            ("Brightness:", 0, 1, "camera_brightness"),
        ])
        grid.addWidget(grp_cam, 1, 0)

        root.addWidget(container)
        root.addStretch()
        return tab

    # =================================================
    # TAB: TQS Range (EXACT GROUP MATCH)
    # =================================================
    def _tqs_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QVBoxLayout(tab)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(0)

        # Main container
        container = QWidget()
        main_layout = QHBoxLayout(container)
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ================= LEFT COLUMN =================
        left_col = QVBoxLayout()
        left_col.setSpacing(15)

        # ---- Pick Up ----
        grp_pick = self._styled_section("Pick Up", [
            ("Pocket Gap:", 1, 50, "tqs_pickup_pocket_gap_1"),
            ("Pocket Gap:", 1, 50, "tqs_pickup_pocket_gap_2"),
        ])
        left_col.addWidget(grp_pick)

        # ---- Sealing Stain Inspection ----
        grp_stain = self._styled_section("Sealing Stain Inspection", [
            ("Contrast:", 1, 200, "tqs_sealing_stain_contrast"),
            ("Min Area:", 10, 2000, "tqs_sealing_stain_min_area"),
            ("Min Sqr Size:", 2, 10, "tqs_sealing_stain_min_sqr"),
        ])
        left_col.addWidget(grp_stain)

        # ---- Inspection Width ----
        grp_width = QGroupBox("Inspection Width")
        grp_width.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
            }
        """)
        g3 = QGridLayout(grp_width)
        g3.setHorizontalSpacing(15)
        g3.setVerticalSpacing(8)
        g3.setContentsMargins(12, 20, 12, 12)

        header_font = QFont()
        header_font.setBold(True)
        
        for col, text in enumerate(["", "Min", "Max"]):
            label = QLabel(text)
            if text in ["Min", "Max"]:
                label.setFont(header_font)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
            g3.addWidget(label, 0, col)

        # Left
        left_min = self._create_line_edit("50")
        left_max = self._create_line_edit("100")
        g3.addWidget(self._create_label("Left:"), 1, 0)
        g3.addWidget(left_min, 1, 1)
        g3.addWidget(left_max, 1, 2)
        self._numeric_fields["tqs_insp_width_left_min"] = left_min
        self._numeric_fields["tqs_insp_width_left_max"] = left_max

        # Top
        top_min = self._create_line_edit("50")
        top_max = self._create_line_edit("100")
        g3.addWidget(self._create_label("Top:"), 2, 0)
        g3.addWidget(top_min, 2, 1)
        g3.addWidget(top_max, 2, 2)
        self._numeric_fields["tqs_insp_width_top_min"] = top_min
        self._numeric_fields["tqs_insp_width_top_max"] = top_max

        # Right
        right_min = self._create_line_edit("50")
        right_max = self._create_line_edit("100")
        g3.addWidget(self._create_label("Right:"), 3, 0)
        g3.addWidget(right_min, 3, 1)
        g3.addWidget(right_max, 3, 2)
        self._numeric_fields["tqs_insp_width_right_min"] = right_min
        self._numeric_fields["tqs_insp_width_right_max"] = right_max

        # Bottom
        bottom_min = self._create_line_edit("50")
        bottom_max = self._create_line_edit("100")
        g3.addWidget(self._create_label("Bottom:"), 4, 0)
        g3.addWidget(bottom_min, 4, 1)
        g3.addWidget(bottom_max, 4, 2)
        self._numeric_fields["tqs_insp_width_bottom_min"] = bottom_min
        self._numeric_fields["tqs_insp_width_bottom_max"] = bottom_max

        left_col.addWidget(grp_width)
        left_col.addStretch()

        # ================= RIGHT COLUMN =================
        right_col = QVBoxLayout()
        right_col.setSpacing(15)

        # ---- Sealing Shift Inspection ----
        grp_shift = self._styled_section("Sealing Shift Inspection", [
            ("Contrast Left:", 1, 200, "tqs_sealing_shift_contrast_left"),
            ("Contrast Right:", 1, 200, "tqs_sealing_shift_contrast_right"),
            ("Tolerance Left:", 1, 30, "tqs_sealing_shift_tol_left"),
            ("Tolerance Right:", 1, 30, "tqs_sealing_shift_tol_right"),
        ])
        right_col.addWidget(grp_shift)

        # ---- Hole Side Shift ----
        grp_hole = self._styled_section("Hole Side Shift", [
            ("Contrast:", 50, 200, "tqs_hole_shift_contrast"),
            ("Min Width:", 50, 150, "tqs_hole_shift_min_width"),
        ])
        right_col.addWidget(grp_hole)
        right_col.addStretch()

        # Add columns to main layout
        main_layout.addLayout(left_col)
        main_layout.addLayout(right_col)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 1)

        root.addWidget(container)
        root.addStretch()
        return tab

    # =================================================
    # TAB: Inspection Item Selection (EXACT MATCH)
    # =================================================
    def _inspection_item_selection_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QVBoxLayout(tab)
        root.setSpacing(15)
        root.setContentsMargins(15, 15, 15, 15)

        # ---------------- Package & Pocket Location ----------------
        grp_pkg = QGroupBox("Package & Pocket Location Parameters")
        grp_pkg.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        h = QHBoxLayout(grp_pkg)
        h.setContentsMargins(12, 20, 12, 12)
        h.setSpacing(20)
        
        self.chk_package_location = self._create_checkbox("Package Location Inspection")
        self.chk_pocket_location = self._create_checkbox("Pocket Location Inspection")
        self.chk_pocket_post_seal = self._create_checkbox("Pocket Post Seal")

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
        grp_dim.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_dim = QGridLayout(grp_dim)
        g_dim.setContentsMargins(12, 20, 12, 12)
        g_dim.setHorizontalSpacing(30)
        g_dim.setVerticalSpacing(10)

        self.chk_body_length = self._create_checkbox("Body Length")
        self.chk_terminal_width = self._create_checkbox("Terminal Width")
        self.chk_term_term_length = self._create_checkbox("Term-Term Length")
        self.chk_body_width = self._create_checkbox("Body Width")
        self.chk_terminal_length = self._create_checkbox("Terminal Length")
        self.chk_adjust_pkgloc = self._create_checkbox("Adjust PkgLoc By Body Height")

        self._inspection_checkboxes.update({
            "check_body_length": self.chk_body_length,
            "check_terminal_width": self.chk_terminal_width,
            "check_term_term_length": self.chk_term_term_length,
            "check_body_width": self.chk_body_width,
            "check_terminal_length": self.chk_terminal_length,
            "adjust_pkgloc_by_body_height": self.chk_adjust_pkgloc,
        })

        g_dim.addWidget(self.chk_body_length, 0, 0)
        g_dim.addWidget(self.chk_body_width, 0, 1)
        g_dim.addWidget(self.chk_terminal_length, 1, 0)
        g_dim.addWidget(self.chk_terminal_width, 1, 1)
        g_dim.addWidget(self.chk_term_term_length, 2, 0)
        g_dim.addWidget(self.chk_adjust_pkgloc, 2, 1)

        root.addWidget(grp_dim)

        # ---------------- Main Grid ----------------
        scroll_content = QWidget()
        mid = QGridLayout(scroll_content)
        mid.setHorizontalSpacing(20)
        mid.setVerticalSpacing(15)

        # ===== COLUMN 1 =====
        mid.addWidget(self._styled_check_group("Terminal Inspection", [
            ("Terminal Pogo", "check_terminal_pogo"),
            ("Incomplete Termination 1", "check_incomplete_termination_1"),
            ("Incomplete Termination 2", "check_incomplete_termination_2"),
            ("Terminal Length Difference", "check_terminal_length_diff"),
            ("Terminal to Body Gap", "check_terminal_to_body_gap"),
            ("Terminal Color", "check_terminal_color"),
            ("Terminal Oxidation", "check_terminal_oxidation"),
        ]), 0, 0)

        mid.addWidget(self._styled_check_group("Body Crack", [
            ("Body Crack", "check_body_crack"),
            ("Low And High Contrast Reject", "check_low_high_contrast"),
            ("Black Defect", "check_black_defect"),
            ("White Defect", "check_white_defect"),
        ]), 1, 0)

        mid.addWidget(self._styled_check_group("Body Inspection", [
            ("Body Stain 1", "check_body_stain_1"),
            ("Body Stain 2", "check_body_stain_2"),
            ("Body Color", "check_body_color"),
            ("Body to Term Body Width", "check_body_to_term_width"),
            ("Body Width Difference", "check_body_width_diff"),
        ]), 2, 0)

        # ===== COLUMN 2 =====
        mid.addWidget(self._styled_check_group("Terminal Chipoff", [
            ("Inner Term Chipoff", "check_inner_term_chipoff"),
            ("Outer Term Chipoff", "check_outer_term_chipoff"),
        ]), 0, 1)

        mid.addWidget(self._styled_check_group("Inspection Width", [
            ("Left", "check_insp_width_left"),
            ("Right", "check_insp_width_right"),
            ("Top", "check_insp_width_top"),
            ("Bottom", "check_insp_width_bottom"),
        ]), 1, 1)

        mid.addWidget(self._styled_check_group("Body Smear", [
            ("Body Smear 1", "check_body_smear_1"),
            ("Body Smear 2", "check_body_smear_2"),
            ("Body Smear 3", "check_body_smear_3"),
            ("Reverse Chip Check", "check_reverse_chip"),
            ("White", "check_smear_white"),
        ]), 2, 1)

        # ===== COLUMN 3 =====
        mid.addWidget(self._styled_check_group("Body Edge Inspection", [
            ("Body Edge Black Defect", "check_body_edge_black"),
            ("Body Edge White Defect", "check_body_edge_white"),
        ]), 0, 2)

        # ===== COLUMN 4 =====
        mid.addWidget(self._styled_check_group("TQS Inspection", [
            ("Enable Sealing Stain", "enable_sealing_stain"),
            ("Enable Sealing Stain2", "enable_sealing_stain2"),
            ("Enable Sealing Shift", "enable_sealing_shift"),
            ("Black To White Scar", "enable_black_to_white_scar"),
            ("Hole Reference", "enable_hole_reference"),
            ("White To Black Scan", "enable_white_to_black_scan"),
            ("Enable Emboss Tape Pick Up", "enable_emboss_tape_pickup"),
        ], rows=2), 0, 3, 2, 1)

        # ---- Auto Fill Parameters ----
        grp_auto = QGroupBox("Auto Fill Parameters")
        grp_auto.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_auto = QGridLayout(grp_auto)
        g_auto.setContentsMargins(12, 20, 12, 12)
        g_auto.setHorizontalSpacing(15)
        g_auto.setVerticalSpacing(8)

        header_font = QFont()
        header_font.setBold(True)
        
        for col, text in enumerate(["", "Min", "Max"]):
            label = QLabel(text)
            if text in ["Min", "Max"]:
                label.setFont(header_font)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
            g_auto.addWidget(label, 0, col)

        auto_items = [
            "Body Length",
            "Terminal Width",
            "Terminal Length",
            "Term to Term Length"
        ]
        for i, txt in enumerate(auto_items, start=1):
            chk = self._create_checkbox(txt)
            g_auto.addWidget(chk, i, 0)

            field_map = {
                "Body Length": "auto_body_length",
                "Terminal Width": "auto_terminal_width",
                "Terminal Length": "auto_terminal_length",
                "Term to Term Length": "auto_term_term_length",
            }

            self._inspection_checkboxes[field_map[txt]] = chk

            min_edit = self._create_line_edit("20")
            max_edit = self._create_line_edit("20")
            g_auto.addWidget(min_edit, i, 1)
            g_auto.addWidget(max_edit, i, 2)

        mid.addWidget(grp_auto, 2, 3)

        # Add scroll area for the main content
        scroll = QScrollArea()
        scroll.setWidget(scroll_content)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(scroll)

        return tab

    # =================================================
    # HELPER METHODS FOR STYLING
    # =================================================
    def _styled_minmax_group(self, title, key_prefix=None, short=False):
        grp = QGroupBox(title)
        grp.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g = QGridLayout(grp)
        g.setHorizontalSpacing(15)
        g.setVerticalSpacing(8)
        g.setContentsMargins(12, 20, 12, 12)

        header_font = QFont()
        header_font.setBold(True)
        
        for col, text in enumerate(["", "Min", "Max"]):
            label = QLabel(text)
            if text in ["Min", "Max"]:
                label.setFont(header_font)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
            g.addWidget(label, 0, col)

        rows = ["contrast", "min_area", "min_sqr_size"]
        if not short:
            rows += ["top", "bottom", "left", "right"]

        for r, field in enumerate(rows, start=1):
            label = field.replace("_", " ").title() + ":"
            g.addWidget(self._create_label(label), r, 0)

            min_edit = self._create_line_edit("1")
            max_edit = self._create_line_edit("20")

            g.addWidget(min_edit, r, 1)
            g.addWidget(max_edit, r, 2)

            if key_prefix is not None:
                self._numeric_fields[f"{key_prefix}_{field}_min"] = min_edit
                self._numeric_fields[f"{key_prefix}_{field}_max"] = max_edit

        return grp

    def _styled_section(self, title, rows):
        """Create a styled section with multiple rows"""
        grp = QGroupBox(title)
        grp.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g = QGridLayout(grp)
        g.setHorizontalSpacing(15)
        g.setVerticalSpacing(8)
        g.setContentsMargins(12, 20, 12, 12)

        header_font = QFont()
        header_font.setBold(True)
        
        for col, text in enumerate(["", "Min", "Max"]):
            label = QLabel(text)
            if text in ["Min", "Max"]:
                label.setFont(header_font)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
            g.addWidget(label, 0, col)

        for i, (label, vmin, vmax, key_prefix) in enumerate(rows, start=1):
            g.addWidget(self._create_label(label), i, 0)
            
            min_edit = self._create_line_edit(str(vmin))
            max_edit = self._create_line_edit(str(vmax))
            
            g.addWidget(min_edit, i, 1)
            g.addWidget(max_edit, i, 2)
            
            self._numeric_fields[f"{key_prefix}_min"] = min_edit
            self._numeric_fields[f"{key_prefix}_max"] = max_edit

        return grp

    def _styled_check_group(self, title: str, items: list[tuple[str, str]], rows=1) -> QGroupBox:
        grp = QGroupBox(title)
        grp.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        layout = QVBoxLayout(grp)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(6)

        for label, field_name in items:
            chk = self._create_checkbox(label)
            layout.addWidget(chk)
            self._inspection_checkboxes[field_name] = chk

        if rows > 1:
            layout.addStretch()
        
        return grp

    def _create_line_edit(self, text=""):
        """Create a styled line edit"""
        edit = QLineEdit(text)
        edit.setAlignment(Qt.AlignCenter)
        edit.setFixedHeight(24)
        edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdcdc;
                border-radius: 3px;
                padding: 2px 6px;
                background-color: white;
                selection-background-color: #3498db;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        return edit

    def _create_label(self, text):
        """Create a styled label"""
        label = QLabel(text)
        label.setStyleSheet("color: #333333;")
        return label

    def _create_checkbox(self, text):
        """Create a styled checkbox"""
        checkbox = QCheckBox(text)
        checkbox.setStyleSheet("""
            QCheckBox {
                color: #333333;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 1px solid #2980b9;
                image: url();
            }
            QCheckBox::indicator:hover {
                border: 1px solid #3498db;
            }
        """)
        return checkbox

    def _make_scrollable(self, widget: QWidget) -> QWidget:
        scroll = QScrollArea(self)
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        return scroll

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
        grid.addWidget(self._create_label(label), row, col)

        min_edit = self._create_line_edit(str(vmin))
        max_edit = self._create_line_edit(str(vmax))

        grid.addWidget(min_edit, row, col + 1)
        grid.addWidget(max_edit, row, col + 2)

        if key_prefix is not None:
            self._numeric_fields[f"{key_prefix}_min"] = min_edit
            self._numeric_fields[f"{key_prefix}_max"] = max_edit

    def _check_group(self, title: str, items: list[tuple[str, str]]) -> QGroupBox:
        grp = QGroupBox(title)
        layout = QVBoxLayout(grp)

        for label, field_name in items:
            chk = self._create_checkbox(label)
            layout.addWidget(chk)
            self._inspection_checkboxes[field_name] = chk

        return grp

    # =================================================
    # BUSINESS LOGIC METHODS (UNCHANGED)
    # =================================================
    def _apply_to_model(self):
        # Use the current station's parameters instead of the global one
        ip = self.parent().current_params()

        # ---- numeric fields (station-specific) ----
        for key, widget in self._numeric_fields.items():
            try:
                ip.ranges[key] = int(widget.text())
            except ValueError:
                ip.ranges[key] = 0

        # ---- checkbox fields (shared across stations) ----
        shared_flags = self.parent().shared_flags
        for key, checkbox in self._inspection_checkboxes.items():
            shared_flags[key] = checkbox.isChecked()

        ip.is_defined = True

        # Save shared flags to inspection_parameters.json, preserve other fields
        shared_model = load_parameters()
        shared_model.flags = shared_flags
        save_parameters(shared_model)

        # Save station-specific ranges/teach data
        save_teach_data(self.parent().inspection_parameters_by_station)

    def _on_apply(self):
        self._apply_to_model()
        self.parent().on_inspection_parameters_changed()

    def _on_ok(self):
        self._apply_to_model()
        self.parent().on_inspection_parameters_changed()
        self.accept()


    def _load_from_model(self):
        # Use the current station's parameters instead of the global one
        ip = self.parent().current_params()

        # Numeric fields remain station-specific
        for key, widget in self._numeric_fields.items():
            widget.setText(str(ip.ranges.get(key, 0)))

        # Inspection item selection is shared across stations
        shared_flags = self.parent().shared_flags
        for key, checkbox in self._inspection_checkboxes.items():
            checkbox.setChecked(shared_flags.get(key, False))