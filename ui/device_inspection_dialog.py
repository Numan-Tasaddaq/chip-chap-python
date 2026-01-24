from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton,
    QGroupBox, QTabWidget, QWidget, QRadioButton, QSlider, QSizePolicy, QComboBox, QButtonGroup,
    QFrame, QSpacerItem
)
from PySide6.QtWidgets import QScrollArea
from PySide6.QtGui import QFont

TAB_UNIT = "UnitParameters"
TAB_MULTI = "MultiTerminal"
TAB_DIM = "DimensionMeasurement"
TAB_BODYS = "BodySmearTab"
TAB_BODYST = "BodyStainTab"
TAB_TERMP = "TerminalPlatingTab"
TAB_TERMBS = "TerminalBlackSpotTab"
TAB_BODYCR = "BodyCrackTab"
TAB_TERMCOR = "TerminalCornerTab"
TAB_BODYEDGE = "BodyEdgeTab"
TAB_COLOR = "ColorInspectionTab"

class DeviceInspectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Device Inspection - Track1")
        self.resize(1100, 520)
        self.setMinimumHeight(500)
        self.setMaximumHeight(560)

        # Enable maximize
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        # Apply professional styling
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
                padding: 4px 6px;
                background-color: white;
                min-height: 24px;
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
            QRadioButton {
                spacing: 6px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: #e6e6e6;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #3498db;
                border: 1px solid #777;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: #e6e6e6;
                border: 1px solid #777;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #ccc;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #f0f0f0;
                border: 1px solid #3498db;
            }
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 4px;
                background-color: white;
                min-height: 24px;
            }
            QComboBox:hover {
                border: 1px solid #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #555555;
                margin-right: 5px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self._build_ui()
        self.load_tab(self.unit_tab, TAB_UNIT, "device_inspection.json")
        self.load_tab(self.multi_tab, TAB_MULTI, "device_inspection.json")
        self.load_tab(self.dimensionmeasurement_tab, TAB_DIM, "device_inspection.json")
        self.load_tab(self.body_smear_tab, TAB_BODYS, "device_inspection.json")
        self.load_tab(self.body_stain_tab, TAB_BODYST, "device_inspection.json")
        self.load_tab(self.terminal_platting_defect_tab, TAB_TERMP, "device_inspection.json")
        self.load_tab(self.terminal_black_spot_tab, TAB_TERMBS, "device_inspection.json")
        self.load_tab(self.body_crack_tab, TAB_BODYCR, "device_inspection.json")
        self.load_tab(self.terminal_corner_defect_tab, TAB_TERMCOR, "device_inspection.json")
        self.load_tab(self.body_edge_effect_tab, TAB_BODYEDGE, "device_inspection.json")
        self.load_tab(self.color_inspection_tab, TAB_COLOR, "device_inspection.json")

    # =================================================
    # UI
    # =================================================
    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(10)
        main.setContentsMargins(10, 10, 10, 10)

        # Create a frame for the content
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

        # ---------- Tabs ----------
        self.unit_tab = self._unit_parameters_tab()
        self.tabs.addTab(self._make_scrollable(self.unit_tab), "Unit Parameters")

        self.multi_tab = self._multi_terminal_tab()
        self.tabs.addTab(self._make_scrollable(self.multi_tab), "Multi Terminal")

        self.dimensionmeasurement_tab = self._dimension_measurement_parameters_tab()
        self.tabs.addTab(self._make_scrollable(self.dimensionmeasurement_tab), "Dimension Measurement")

        # Body Smear
        self.body_smear_tab = self._body_smear_tab()
        self.tabs.addTab(self._make_scrollable(self.body_smear_tab), "Body Missing Solder")

        # Body Stain
        self.body_stain_tab = self._body_stain_tab()
        self.tabs.addTab(self._make_scrollable(self.body_stain_tab), "Body Stain")

        # Terminal Plating Defect
        self.terminal_platting_defect_tab = self._terminal_platting_defect_tab()
        self.tabs.addTab(self._make_scrollable(self.terminal_platting_defect_tab), "Terminal Plating Defect")

        # Terminal Black Spot
        self.terminal_black_spot_tab = self._terminal_black_spot_tab()
        self.tabs.addTab(self._make_scrollable(self.terminal_black_spot_tab), "Terminal Black Spot")
        # Body Crack
        self.body_crack_tab = self._body_crack_tab()
        self.tabs.addTab(self._make_scrollable(self.body_crack_tab), "Body Crack")

        # Terminal Corner Defect
        self.terminal_corner_defect_tab = self._terminal_corner_deffect_tab()
        self.tabs.addTab(self._make_scrollable(self.terminal_corner_defect_tab), "Terminal Corner Defect")
        # Body Edge Defect
        self.body_edge_effect_tab = self._body_edge_effect_tab()
        self.tabs.addTab(self._make_scrollable(self.body_edge_effect_tab), "Body Edge Defect")

        # Color Inspection
        self.color_inspection_tab = self._color_inspection_tab()
        self.tabs.addTab(self._make_scrollable(self.color_inspection_tab), "Color Inspection")

        self.tabs.setCurrentIndex(0)

        # Add frame to main layout
        main.addWidget(content_frame)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #e0e0e0; margin: 5px 0;")
        main.addWidget(separator)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()

        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("cancelButton")
        btn_apply = QPushButton("Apply")

        # Set fixed button sizes for consistency
        btn_ok.setFixedSize(90, 32)
        btn_cancel.setFixedSize(90, 32)
        btn_apply.setFixedSize(90, 32)

        # Connect Apply
        btn_apply.clicked.connect(lambda: (
            self.save_tab(self.unit_tab, TAB_UNIT, "device_inspection.json"),
            self.save_tab(self.multi_tab, TAB_MULTI, "device_inspection.json"),
            self.save_tab(self.dimensionmeasurement_tab, TAB_DIM, "device_inspection.json"),
            self.save_tab(self.body_smear_tab, TAB_BODYS, "device_inspection.json"),
            self.save_tab(self.body_stain_tab, "BodyStainTab", "device_inspection.json"),
            self.save_tab(self.terminal_platting_defect_tab, "TerminalPlatingTab", "device_inspection.json"),
            self.save_tab(self.terminal_black_spot_tab, "TerminalBlackSpotTab", "device_inspection.json"),
            self.save_tab(self.body_crack_tab, "BodyCrackTab", "device_inspection.json"),
            self.save_tab(self.terminal_corner_defect_tab, "TerminalCornerTab", "device_inspection.json"),
            self.save_tab(self.body_edge_effect_tab, "BodyEdgeTab", "device_inspection.json"),
            self.save_tab(self.color_inspection_tab, "ColorInspectionTab", "device_inspection.json")
        ))

        # Connect OK
        btn_ok.clicked.connect(lambda: (
            self.save_tab(self.unit_tab, TAB_UNIT, "device_inspection.json"),
            self.save_tab(self.multi_tab, TAB_MULTI, "device_inspection.json"),
            self.save_tab(self.dimensionmeasurement_tab, TAB_DIM, "device_inspection.json"),
            self.save_tab(self.body_smear_tab, TAB_BODYS, "device_inspection.json"),
            self.save_tab(self.body_stain_tab, "BodyStainTab", "device_inspection.json"),
            self.save_tab(self.terminal_platting_defect_tab, "TerminalPlatingTab", "device_inspection.json"),
            self.save_tab(self.terminal_black_spot_tab, "TerminalBlackSpotTab", "device_inspection.json"),
            self.save_tab(self.body_crack_tab, "BodyCrackTab", "device_inspection.json"),
            self.save_tab(self.terminal_corner_defect_tab, "TerminalCornerTab", "device_inspection.json"),
            self.save_tab(self.body_edge_effect_tab, "BodyEdgeTab", "device_inspection.json"),
            self.save_tab(self.color_inspection_tab, "ColorInspectionTab", "device_inspection.json"),
            self.accept()
        ))

        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_apply)
        btns.addSpacing(10)
        btns.addWidget(btn_ok)
        btns.addSpacing(10)
        btns.addWidget(btn_cancel)

        main.addLayout(btns)

    # unit parameter tab
    def _unit_parameters_tab(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background-color: white;")
        root = QHBoxLayout(container)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(20)

        # ================= LEFT MAIN GROUP =================
        grp = QGroupBox("Unit Parameters (um)")
        grp.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g = QGridLayout(grp)
        g.setHorizontalSpacing(15)
        g.setVerticalSpacing(10)
        g.setContentsMargins(12, 20, 12, 12)

        # Header styling
        header_font = QFont()
        header_font.setBold(True)

        # Header row with "um" label for read-only fields
        g.addWidget(self._create_label(""), 0, 0)
        g.addWidget(self._create_label(""), 0, 1)
        g.addWidget(self._create_label(""), 0, 2)
        um_header = QLabel("um")
        um_header.setFont(header_font)
        um_header.setAlignment(Qt.AlignCenter)
        um_header.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
        g.addWidget(um_header, 0, 3)

        # ---- Body Length ----
        g.addWidget(self._create_label("Body Length:"), 1, 0)
        g.addWidget(self._create_label("Min:"), 1, 1)
        le_body_length_min = self._create_line_edit("60", "body_length_min")
        g.addWidget(le_body_length_min, 1, 2)
        # Read-only um display for Body Length (Min) - no objectName, not saved
        le_body_length_min_um = self._create_readonly_line_edit("150")
        g.addWidget(le_body_length_min_um, 1, 3)

        g.addWidget(self._create_label("Max:"), 2, 1)
        le_body_length_max = self._create_line_edit("414", "body_length_max")
        g.addWidget(le_body_length_max, 2, 2)
        # Read-only um display for Body Length (Max) - no objectName, not saved
        le_body_length_max_um = self._create_readonly_line_edit("1035")
        g.addWidget(le_body_length_max_um, 2, 3)

        # ---- Body Width ----
        g.addWidget(self._create_label("Body Width:"), 3, 0)
        g.addWidget(self._create_label("Min:"), 3, 1)
        le_body_width_min = self._create_line_edit("30", "body_width_min")
        g.addWidget(le_body_width_min, 3, 2)
        # Read-only um display for Body Width (Min) - no objectName, not saved
        le_body_width_min_um = self._create_readonly_line_edit("80")
        g.addWidget(le_body_width_min_um, 3, 3)

        g.addWidget(self._create_label("Max:"), 4, 1)
        le_body_width_max = self._create_line_edit("207", "body_width_max")
        g.addWidget(le_body_width_max, 4, 2)
        # Read-only um display for Body Width (Max) - no objectName, not saved
        le_body_width_max_um = self._create_readonly_line_edit("552")
        g.addWidget(le_body_width_max_um, 4, 3)
        # ---- Terminal Width ----
        g.addWidget(self._create_label("Terminal Width:"), 5, 0)
        dimension_label = QLabel("Dimension")
        dimension_label.setFont(header_font)
        dimension_label.setAlignment(Qt.AlignCenter)
        dimension_label.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
        # Place Dimension header above editable value column
        g.addWidget(dimension_label, 5, 1)

        # Add 'um' header above the read-only column
        dim_um_header = QLabel("um")
        dim_um_header.setFont(header_font)
        dim_um_header.setAlignment(Qt.AlignCenter)
        dim_um_header.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
        g.addWidget(dim_um_header, 5, 2)

        pkg_label = QLabel("Pkg Location")
        pkg_label.setFont(header_font)
        pkg_label.setAlignment(Qt.AlignCenter)
        pkg_label.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
        # Keep Package Location header above its editable column
        g.addWidget(pkg_label, 5, 3)

        g.addWidget(self._create_label("Min:"), 6, 0)
        le_term_dim_min = self._create_line_edit("30", "terminal_width_min")
        g.addWidget(le_term_dim_min, 6, 1)
        # Read-only um display for Dimension (Min) - no objectName, not saved
        le_term_dim_min_um = self._create_readonly_line_edit("30")
        g.addWidget(le_term_dim_min_um, 6, 2)

        le_term_pkg = self._create_line_edit("30", "terminal_width_pkg_min")
        g.addWidget(le_term_pkg, 6, 3)

        g.addWidget(self._create_label("Max:"), 7, 0)
        le_term_dim_max = self._create_line_edit("207", "terminal_width_max")
        g.addWidget(le_term_dim_max, 7, 1)
        # Read-only um display for Dimension (Max) - no objectName, not saved
        le_term_dim_max_um = self._create_readonly_line_edit("207")
        g.addWidget(le_term_dim_max_um, 7, 2)

        le_term_pkg2 = self._create_line_edit("150", "terminal_width_pkg_max")
        g.addWidget(le_term_pkg2, 7, 3)

        # ---- Differences ----
        cb_term_length_diff = self._create_checkbox("Terminal Length Difference:")
        cb_term_length_diff.setObjectName("terminal_length_diff")
        g.addWidget(cb_term_length_diff, 10, 0)

        le_term_length_diff = self._create_line_edit("5", "terminal_length_diff_value")
        g.addWidget(le_term_length_diff, 10, 2)

        cb_body_width_diff = self._create_checkbox("Body Width Difference:")
        cb_body_width_diff.setObjectName("body_width_diff")
        g.addWidget(cb_body_width_diff, 11, 0)

        le_body_width_diff = self._create_line_edit("5", "body_width_diff_value")
        g.addWidget(le_body_width_diff, 11, 2)

        # ---- Body to Term Body Width ----
        grp_bw = QGroupBox("Body to Term Body Width")
        grp_bw.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gbw = QGridLayout(grp_bw)
        gbw.setContentsMargins(8, 15, 8, 8)
        gbw.setSpacing(8)

        cb_enable_body_width = self._create_checkbox("Enable Body Width")
        cb_enable_body_width.setObjectName("enable_body_width")
        gbw.addWidget(cb_enable_body_width, 0, 0, 1, 2)

        gbw.addWidget(self._create_label("Min:"), 1, 0)
        le_bw_min = self._create_line_edit("20", "body_to_term_min")
        gbw.addWidget(le_bw_min, 1, 1)

        gbw.addWidget(self._create_label("Max:"), 2, 0)
        le_bw_max = self._create_line_edit("40", "body_to_term_max")
        gbw.addWidget(le_bw_max, 2, 1)

        g.addWidget(grp_bw, 12, 0, 3, 4)
        root.addWidget(grp)

        # --- Auto-calc: Use old ChipCap system conversion formula ---
        # Old system formula: µm = pixels × (SENSOR_CONSTANT / lens_magnification)
        # SENSOR_CONSTANT: 7.4 (iTrue_USB3CT/MT) or 6.9 (others)
        # lens_magnification: default 1.0 (from registry in old system)
        
        # For now, use default values matching old system behavior
        SENSOR_CONSTANT = 7.4  # iTrue_USB3CT/MT default
        lens_magnification = 1.0  # Default lens mag
        
        # Calculate pixel-to-µm conversion factor (same for all dimensions)
        pixel_to_um = SENSOR_CONSTANT / lens_magnification

        def _bind_um(src_edit: QLineEdit, dst_edit: QLineEdit, factor: float):
            def _on_change(text: str):
                try:
                    val = float(text.strip()) if text.strip() else 0.0
                except Exception:
                    dst_edit.setText("")
                    return
                um_val = int(round(val * factor))
                dst_edit.setText(str(um_val))
            src_edit.textChanged.connect(_on_change)
            _on_change(src_edit.text())  # initial sync

        # Wire all dimensions with the same pixel_to_um factor (old ChipCap behavior)
        _bind_um(le_body_length_min, le_body_length_min_um, pixel_to_um)
        _bind_um(le_body_length_max, le_body_length_max_um, pixel_to_um)
        _bind_um(le_body_width_min, le_body_width_min_um, pixel_to_um)
        _bind_um(le_body_width_max, le_body_width_max_um, pixel_to_um)
        _bind_um(le_term_dim_min, le_term_dim_min_um, pixel_to_um)
        _bind_um(le_term_dim_max, le_term_dim_max_um, pixel_to_um)

        # ================= RIGHT SIDE =================
        right = QVBoxLayout()
        right.setSpacing(12)

        cb_no_terminal = self._create_checkbox("No Terminal")
        cb_no_terminal.setObjectName("no_terminal")
        right.addWidget(cb_no_terminal)

        cb_pkg_as_body = self._create_checkbox("Pkg Location Use as Body Length")
        cb_pkg_as_body.setObjectName("pkg_as_body")
        right.addWidget(cb_pkg_as_body)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self._create_label("Terminal Length Contrast:"))
        le_term_contrast = self._create_line_edit("0", "terminal_length_contrast")
        row.addWidget(le_term_contrast)
        right.addLayout(row)

        # ---- Terminal Length ----
        grp_term = QGroupBox("Terminal Length (um)")
        grp_term.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g2 = QGridLayout(grp_term)
        g2.setContentsMargins(10, 15, 10, 10)
        g2.setSpacing(8)

        # Header above read-only column
        term_len_um_header = QLabel("um")
        term_len_um_header.setFont(header_font)
        term_len_um_header.setAlignment(Qt.AlignCenter)
        term_len_um_header.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
        g2.addWidget(term_len_um_header, 0, 2)

        # Min row: editable pixels + read-only um
        le_term_len_min = self._create_line_edit("10", "terminal_length_min")
        g2.addWidget(self._create_label("Min:"), 1, 0)
        g2.addWidget(le_term_len_min, 1, 1)
        le_term_len_min_um = self._create_readonly_line_edit("10")
        g2.addWidget(le_term_len_min_um, 1, 2)

        # Max row: editable pixels + read-only um
        g2.addWidget(self._create_label("Max:"), 2, 0)
        le_term_len_max = self._create_line_edit("69", "terminal_length_max")
        g2.addWidget(le_term_len_max, 2, 1)
        le_term_len_max_um = self._create_readonly_line_edit("69")
        g2.addWidget(le_term_len_max_um, 2, 2)

        right.addWidget(grp_term)

        # Auto-calc um for Terminal Length min/max
        _bind_um(le_term_len_min, le_term_len_min_um, pixel_to_um)
        _bind_um(le_term_len_max, le_term_len_max_um, pixel_to_um)

        # ---- Term to Term Length ----
        grp_tt = QGroupBox("Term To Term Length (um)")
        grp_tt.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g3 = QGridLayout(grp_tt)
        g3.setContentsMargins(10, 15, 10, 10)
        g3.setSpacing(8)

        # Header above read-only column
        tt_um_header = QLabel("um")
        tt_um_header.setFont(header_font)
        tt_um_header.setAlignment(Qt.AlignCenter)
        tt_um_header.setStyleSheet("color: #2c3e50; background-color: #f8f9fa; padding: 4px; border-radius: 3px;")
        g3.addWidget(tt_um_header, 0, 2)

        # Min row: editable pixels + read-only um
        g3.addWidget(self._create_label("Min:"), 1, 0)
        le_tt_min = self._create_line_edit("20", "term_to_term_min")
        g3.addWidget(le_tt_min, 1, 1)
        le_tt_min_um = self._create_readonly_line_edit("20")
        g3.addWidget(le_tt_min_um, 1, 2)

        # Max row: editable pixels + read-only um
        g3.addWidget(self._create_label("Max:"), 2, 0)
        le_tt_max = self._create_line_edit("138", "term_to_term_max")
        g3.addWidget(le_tt_max, 2, 1)
        le_tt_max_um = self._create_readonly_line_edit("138")
        g3.addWidget(le_tt_max_um, 2, 2)

        # Max-Min difference (unchanged)
        le_tt_diff_min = self._create_line_edit("10", "term_to_term_diff_min")
        le_tt_diff_max = self._create_line_edit("69", "term_to_term_diff_max")
        g3.addWidget(self._create_label("Max - Min:"), 3, 0)
        g3.addWidget(le_tt_diff_min, 3, 1)
        g3.addWidget(le_tt_diff_max, 3, 2)

        right.addWidget(grp_tt)

        # Auto-calc um for Term-to-Term Length min/max
        _bind_um(le_tt_min, le_tt_min_um, pixel_to_um)
        _bind_um(le_tt_max, le_tt_max_um, pixel_to_um)

        # ---- Term to Body Gap ----
        grp_gap = QGroupBox("Term to Body Gap")
        grp_gap.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g4 = QGridLayout(grp_gap)
        g4.setContentsMargins(10, 15, 10, 10)
        g4.setSpacing(8)

        cb_gap_enable = self._create_checkbox("Enable")
        cb_gap_enable.setObjectName("term_body_gap_enable")
        g4.addWidget(cb_gap_enable, 0, 0)

        g4.addWidget(self._create_label("Edge Contrast:"), 1, 0)
        le_gap_edge = self._create_line_edit("0", "term_body_gap_edge")
        g4.addWidget(le_gap_edge, 1, 1)

        g4.addWidget(self._create_label("Min Gap:"), 2, 0)
        le_gap_min = self._create_line_edit("0", "term_body_gap_min")
        g4.addWidget(le_gap_min, 2, 1)

        right.addWidget(grp_gap)

        right.addStretch()
        root.addLayout(right)

        return container

    # Multi Terminal TAB
    def _multi_terminal_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QVBoxLayout(tab)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(15)

        # ==================================================
        # First Row
        # ==================================================
        row1 = QHBoxLayout()
        row1.setSpacing(20)

        # Top And Bottom Terminals
        grp_tb = QGroupBox("Top And Bottom Terminals")
        grp_tb.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        v_tb = QVBoxLayout(grp_tb)
        v_tb.setContentsMargins(10, 15, 10, 10)
        v_tb.setSpacing(8)

        cb_mid = self._create_checkbox("Enable Mid Terminal")
        cb_mid.setObjectName("mt_enable_mid_terminal")

        cb_multi = self._create_checkbox("Enable Multi Terminal")
        cb_multi.setObjectName("mt_enable_multi_terminal")

        v_tb.addWidget(cb_mid)
        v_tb.addWidget(cb_multi)
        row1.addWidget(grp_tb)

        # Inspection Image
        grp_img = QGroupBox("Insp Image")
        grp_img.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_img = QGridLayout(grp_img)
        g_img.setContentsMargins(10, 15, 10, 10)
        g_img.setHorizontalSpacing(10)
        g_img.setVerticalSpacing(6)

        radios = ["Merge", "Red", "Green", "Blue", "RGB", "RB", "GB"]
        bg_img = QButtonGroup(tab)
        bg_img.setObjectName("mt_insp_image_mode")
        bg_img.setExclusive(True)

        for i, name in enumerate(radios):
            rb = self._create_radio_button(name)
            bg_img.addButton(rb)
            g_img.addWidget(rb, i // 4, i % 4)

        bg_img.buttons()[0].setChecked(True)
        row1.addWidget(grp_img)

        root.addLayout(row1)

        # ==================================================
        # Second Row
        # ==================================================
        row2 = QHBoxLayout()
        row2.setSpacing(20)

        # Number Of Terminals
        grp_num = QGroupBox("Number of Terminals")
        grp_num.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_num = QGridLayout(grp_num)
        g_num.setContentsMargins(10, 15, 10, 10)
        g_num.setHorizontalSpacing(10)
        g_num.setVerticalSpacing(8)

        g_num.addWidget(self._create_label("Top"), 0, 0)
        le_top = self._create_line_edit("0", "mt_term_count_top")
        g_num.addWidget(le_top, 0, 1)

        g_num.addWidget(self._create_label("Left"), 0, 2)
        le_left = self._create_line_edit("0", "mt_term_count_left")
        g_num.addWidget(le_left, 0, 3)

        g_num.addWidget(self._create_label("Bottom"), 1, 0)
        le_bottom = self._create_line_edit("0", "mt_term_count_bottom")
        g_num.addWidget(le_bottom, 1, 1)

        g_num.addWidget(self._create_label("Right"), 1, 2)
        le_right = self._create_line_edit("0", "mt_term_count_right")
        g_num.addWidget(le_right, 1, 3)

        row2.addWidget(grp_num)

        # Package Offset
        grp_offset = QGroupBox("Package Offset")
        grp_offset.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_off = QGridLayout(grp_offset)
        g_off.setContentsMargins(10, 15, 10, 10)
        g_off.setHorizontalSpacing(10)
        g_off.setVerticalSpacing(8)

        g_off.addWidget(self._create_label("Left"), 0, 0)
        le_pkg_left = self._create_line_edit("0", "mt_pkg_offset_left")
        g_off.addWidget(le_pkg_left, 0, 1)

        g_off.addWidget(self._create_label("Right"), 1, 0)
        le_pkg_right = self._create_line_edit("0", "mt_pkg_offset_right")
        g_off.addWidget(le_pkg_right, 1, 1)

        row2.addWidget(grp_offset)

        # Terminal Gap
        grp_gap = QGroupBox("Terminal Gap")
        grp_gap.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_gap = QGridLayout(grp_gap)
        g_gap.setContentsMargins(10, 15, 10, 10)
        g_gap.setHorizontalSpacing(10)
        g_gap.setVerticalSpacing(8)

        cb_gap = self._create_checkbox("Enable Terminal Gap")
        cb_gap.setObjectName("mt_term_gap_enable")
        g_gap.addWidget(cb_gap, 0, 0, 1, 2)

        g_gap.addWidget(self._create_label("Min"), 1, 0)
        le_gap_min = self._create_line_edit("0", "mt_term_gap_min")
        g_gap.addWidget(le_gap_min, 1, 1)

        g_gap.addWidget(self._create_label("Max"), 2, 0)
        le_gap_max = self._create_line_edit("0", "mt_term_gap_max")
        g_gap.addWidget(le_gap_max, 2, 1)

        row2.addWidget(grp_gap)
        root.addLayout(row2)

        # ==================================================
        # Third Row
        # ==================================================
        row3 = QHBoxLayout()
        row3.setSpacing(20)

        # Terminal Length
        grp_len = QGroupBox("Terminal Length")
        grp_len.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_len = QGridLayout(grp_len)
        g_len.setContentsMargins(10, 15, 10, 10)
        g_len.setHorizontalSpacing(10)
        g_len.setVerticalSpacing(8)

        cb_len = self._create_checkbox("Enable Terminal Length")
        cb_len.setObjectName("mt_term_length_enable")
        g_len.addWidget(cb_len, 0, 0, 1, 4)

        g_len.addWidget(self._create_label("Top/Bot"), 1, 1)
        g_len.addWidget(self._create_label("Left/Rht"), 1, 3)

        g_len.addWidget(self._create_label("Min"), 2, 0)
        le_len_tb_min = self._create_line_edit("0", "mt_term_length_tb_min")
        g_len.addWidget(le_len_tb_min, 2, 1)

        le_len_lr_min = self._create_line_edit("0", "mt_term_length_lr_min")
        g_len.addWidget(le_len_lr_min, 2, 3)

        g_len.addWidget(self._create_label("Max"), 3, 0)
        le_len_tb_max = self._create_line_edit("0", "mt_term_length_tb_max")
        g_len.addWidget(le_len_tb_max, 3, 1)

        le_len_lr_max = self._create_line_edit("0", "mt_term_length_lr_max")
        g_len.addWidget(le_len_lr_max, 3, 3)

        row3.addWidget(grp_len)

        # Terminal Width
        grp_w = QGroupBox("Terminal Width")
        grp_w.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_w = QGridLayout(grp_w)
        g_w.setContentsMargins(10, 15, 10, 10)
        g_w.setHorizontalSpacing(10)
        g_w.setVerticalSpacing(8)

        cb_w = self._create_checkbox("Enable Terminal Width")
        cb_w.setObjectName("mt_term_width_enable")
        g_w.addWidget(cb_w, 0, 0, 1, 4)

        g_w.addWidget(self._create_label("Top/Bot"), 1, 1)
        g_w.addWidget(self._create_label("Left/Rht"), 1, 3)

        g_w.addWidget(self._create_label("Min"), 2, 0)
        le_w_tb_min = self._create_line_edit("0", "mt_term_width_tb_min")
        g_w.addWidget(le_w_tb_min, 2, 1)

        le_w_lr_min = self._create_line_edit("0", "mt_term_width_lr_min")
        g_w.addWidget(le_w_lr_min, 2, 3)

        g_w.addWidget(self._create_label("Max"), 3, 0)
        le_w_tb_max = self._create_line_edit("0", "mt_term_width_tb_max")
        g_w.addWidget(le_w_tb_max, 3, 1)

        le_w_lr_max = self._create_line_edit("0", "mt_term_width_lr_max")
        g_w.addWidget(le_w_lr_max, 3, 3)

        row3.addWidget(grp_w)

        # Terminal Pogo
        grp_pogo = QGroupBox("Terminal Pogo")
        grp_pogo.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_p = QGridLayout(grp_pogo)
        g_p.setContentsMargins(10, 15, 10, 10)
        g_p.setHorizontalSpacing(10)
        g_p.setVerticalSpacing(8)

        cb_pogo = self._create_checkbox("Enable Terminal Pogo")
        cb_pogo.setObjectName("mt_pogo_enable")
        g_p.addWidget(cb_pogo, 0, 0, 1, 3)

        g_p.addWidget(self._create_label("Contrast"), 1, 0)
        sl_pogo = QSlider(Qt.Horizontal)
        sl_pogo.setRange(0, 255)
        sl_pogo.setObjectName("mt_pogo_contrast_slider")
        le_pogo = self._create_line_edit("5", "mt_pogo_contrast")

        self._sync_slider_lineedit(sl_pogo, le_pogo)

        g_p.addWidget(sl_pogo, 1, 1)
        g_p.addWidget(le_pogo, 1, 2)

        g_p.addWidget(self._create_label("Min Area"), 2, 0)
        le_pogo_area = self._create_line_edit("100", "mt_pogo_min_area")
        g_p.addWidget(le_pogo_area, 2, 1)

        g_p.addWidget(self._create_label("Min Square Size"), 3, 0)
        le_pogo_sq = self._create_line_edit("10", "mt_pogo_min_square")
        g_p.addWidget(le_pogo_sq, 3, 1)

        g_p.addWidget(self._create_label("Corner Mask Left"), 4, 0)
        le_pogo_mask_l = self._create_line_edit("0", "mt_pogo_corner_mask_left")
        g_p.addWidget(le_pogo_mask_l, 4, 1)

        g_p.addWidget(self._create_label("Corner Mask Right"), 5, 0)
        le_pogo_mask_r = self._create_line_edit("0", "mt_pogo_corner_mask_right")
        g_p.addWidget(le_pogo_mask_r, 5, 1)

        row3.addWidget(grp_pogo)
        root.addLayout(row3)

        # ==================================================
        # Fourth Row
        # ==================================================
        row4 = QHBoxLayout()
        row4.setSpacing(20)

        # Term To Term Outer
        grp_tto = QGroupBox("Term To Term Outer")
        grp_tto.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_tto = QGridLayout(grp_tto)
        g_tto.setContentsMargins(10, 15, 10, 10)
        g_tto.setHorizontalSpacing(10)
        g_tto.setVerticalSpacing(8)

        cb_tto = self._create_checkbox("Enable Term to Term Outer")
        cb_tto.setObjectName("mt_tto_enable")
        g_tto.addWidget(cb_tto, 0, 0, 1, 4)

        g_tto.addWidget(self._create_label("Top/Bot"), 1, 1)
        g_tto.addWidget(self._create_label("Left/Rht"), 1, 3)

        g_tto.addWidget(self._create_label("Min"), 2, 0)
        le_tto_tb_min = self._create_line_edit("0", "mt_tto_tb_min")
        g_tto.addWidget(le_tto_tb_min, 2, 1)

        le_tto_lr_min = self._create_line_edit("0", "mt_tto_lr_min")
        g_tto.addWidget(le_tto_lr_min, 2, 3)

        g_tto.addWidget(self._create_label("Max"), 3, 0)
        le_tto_tb_max = self._create_line_edit("0", "mt_tto_tb_max")
        g_tto.addWidget(le_tto_tb_max, 3, 1)

        le_tto_lr_max = self._create_line_edit("0", "mt_tto_lr_max")
        g_tto.addWidget(le_tto_lr_max, 3, 3)

        row4.addWidget(grp_tto)

        # Term To Term Inner
        grp_tti = QGroupBox("Term To Term Inner")
        grp_tti.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_tti = QGridLayout(grp_tti)
        g_tti.setContentsMargins(10, 15, 10, 10)
        g_tti.setHorizontalSpacing(10)
        g_tti.setVerticalSpacing(8)

        cb_tti = self._create_checkbox("Enable Term to Term Inner")
        cb_tti.setObjectName("mt_tti_enable")
        g_tti.addWidget(cb_tti, 0, 0, 1, 4)

        g_tti.addWidget(self._create_label("Top/Bot"), 1, 1)
        g_tti.addWidget(self._create_label("Left/Rht"), 1, 3)

        g_tti.addWidget(self._create_label("Min"), 2, 0)
        le_tti_tb_min = self._create_line_edit("0", "mt_tti_tb_min")
        g_tti.addWidget(le_tti_tb_min, 2, 1)

        le_tti_lr_min = self._create_line_edit("0", "mt_tti_lr_min")
        g_tti.addWidget(le_tti_lr_min, 2, 3)

        row4.addWidget(grp_tti)

        # Incomplete Termination Check
        grp_inc = QGroupBox("Incomplete Termination Check")
        grp_inc.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_i = QGridLayout(grp_inc)
        g_i.setContentsMargins(10, 15, 10, 10)
        g_i.setHorizontalSpacing(10)
        g_i.setVerticalSpacing(8)

        cb_inc = self._create_checkbox("Enable Incomplete Termination Check")
        cb_inc.setObjectName("mt_inc_enable")
        g_i.addWidget(cb_inc, 0, 0, 1, 2)

        g_i.addWidget(self._create_label("Contrast"), 1, 0)
        le_inc_contrast = self._create_line_edit("0", "mt_inc_contrast")
        g_i.addWidget(le_inc_contrast, 1, 1)

        g_i.addWidget(self._create_label("Min Area"), 2, 0)
        le_inc_area = self._create_line_edit("0", "mt_inc_min_area")
        g_i.addWidget(le_inc_area, 2, 1)

        g_i.addWidget(self._create_label("Min Square Size"), 3, 0)
        le_inc_sq = self._create_line_edit("0", "mt_inc_min_square")
        g_i.addWidget(le_inc_sq, 3, 1)

        row4.addWidget(grp_inc)
        root.addLayout(row4)

        # ==================================================
        # Fifth Row
        # ==================================================
        row5 = QHBoxLayout()
        row5.setSpacing(20)

        # Excess Terminal Check
        grp_exc = QGroupBox("Excess Terminal Check")
        grp_exc.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_e = QGridLayout(grp_exc)
        g_e.setContentsMargins(10, 15, 10, 10)
        g_e.setHorizontalSpacing(10)
        g_e.setVerticalSpacing(8)

        cb_exc = self._create_checkbox("Enable Excess Terminal Check")
        cb_exc.setObjectName("mt_exc_enable")
        g_e.addWidget(cb_exc, 0, 0)

        g_e.addWidget(self._create_label("Min Square Size"), 1, 0)
        le_exc_sq = self._create_line_edit("0", "mt_exc_min_square")
        g_e.addWidget(le_exc_sq, 1, 1)

        g_e.addWidget(self._create_label("Min Area"), 2, 0)
        le_exc_area = self._create_line_edit("80", "mt_exc_min_area")
        g_e.addWidget(le_exc_area, 2, 1)

        row5.addWidget(grp_exc)

        # Terminal Mis Alignment
        grp_align = QGroupBox("Terminal Mis Alignment")
        grp_align.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        g_a = QGridLayout(grp_align)
        g_a.setContentsMargins(10, 15, 10, 10)
        g_a.setHorizontalSpacing(10)
        g_a.setVerticalSpacing(8)

        cb_align = self._create_checkbox("Enable Term Mis Alignment")
        cb_align.setObjectName("mt_align_enable")
        g_a.addWidget(cb_align, 0, 0, 1, 2)

        g_a.addWidget(self._create_label("Max Angle"), 1, 0)
        le_align_angle = self._create_line_edit("0", "mt_align_max_angle")
        g_a.addWidget(le_align_angle, 1, 1)

        g_a.addWidget(self._create_label("Degrees"), 1, 2)

        row5.addWidget(grp_align)

        row5.addStretch()
        root.addLayout(row5)
        root.addStretch()

        return tab

    # dimension measurement tab
    def _dimension_measurement_parameters_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QVBoxLayout(tab)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(15)

        # =================================================
        # TOP SECTION
        # =================================================
        top = QHBoxLayout()
        top.setSpacing(20)

        # -------- Enable checkboxes --------
        grp_enable = QGroupBox("Dimension Measurement Parameters")
        grp_enable.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gl = QVBoxLayout(grp_enable)
        gl.setContentsMargins(10, 15, 10, 10)
        gl.setSpacing(8)

        cb_body_len = self._create_checkbox("Enable Body Length")
        cb_body_len.setObjectName("dm_enable_body_length")

        cb_term_len = self._create_checkbox("Enable Terminal Length")
        cb_term_len.setObjectName("dm_enable_terminal_length")

        cb_ttl = self._create_checkbox("Enable Terminal-to-Terminal Length")
        cb_ttl.setObjectName("dm_enable_ttl")

        cb_body_w = self._create_checkbox("Enable Body Width")
        cb_body_w.setObjectName("dm_enable_body_width")

        cb_term_w = self._create_checkbox("Enable Terminal Width")
        cb_term_w.setObjectName("dm_enable_terminal_width")

        for cb in [cb_body_len, cb_term_len, cb_ttl, cb_body_w, cb_term_w]:
            gl.addWidget(cb)

        top.addWidget(grp_enable)

        # -------- Right side --------
        right = QVBoxLayout()
        right.setSpacing(12)

        # =================================================
        # Insp Image
        # =================================================
        grp_img = QGroupBox("Insp Image")
        grp_img.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gi = QGridLayout(grp_img)
        gi.setContentsMargins(10, 15, 10, 10)
        gi.setHorizontalSpacing(10)
        gi.setVerticalSpacing(6)

        radios = ["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]
        bg_img = QButtonGroup(tab)
        bg_img.setObjectName("dm_insp_image")

        for i, txt in enumerate(radios):
            rb = self._create_radio_button(txt)
            bg_img.addButton(rb)
            gi.addWidget(rb, i // 4, i % 4)

        bg_img.buttons()[0].setChecked(True)
        right.addWidget(grp_img)

        # =================================================
        # Terminal Contrast
        # =================================================
        tc = QHBoxLayout()
        tc.setSpacing(10)
        tc.addWidget(self._create_label("Terminal Contrast:"))

        le_tc = self._create_line_edit("10", "dm_terminal_contrast")

        sl_tc = QSlider(Qt.Horizontal)
        sl_tc.setRange(0, 255)
        sl_tc.setObjectName("dm_terminal_contrast_slider")

        self._sync_slider_lineedit(sl_tc, le_tc)

        tc.addWidget(le_tc)
        tc.addWidget(sl_tc)
        right.addLayout(tc)

        # =================================================
        # Pixels used
        # =================================================
        px = QHBoxLayout()
        px.setSpacing(10)
        px.addWidget(self._create_label("Number of Pixels Used for Detecting Edge:"))

        le_px = self._create_line_edit("10", "dm_edge_pixels")
        px.addWidget(le_px)
        px.addWidget(self._create_label("Pixels"))
        right.addLayout(px)

        # =================================================
        # Terminal Length
        # =================================================
        grp_tlen = QGroupBox("Terminal Length")
        grp_tlen.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gt = QGridLayout(grp_tlen)
        gt.setContentsMargins(10, 15, 10, 10)
        gt.setHorizontalSpacing(10)
        gt.setVerticalSpacing(8)

        labels = [
            ("Number of Measurement:", "dm_tlen_measure_count", "10"),
            ("Number Of Middle Measurement Skip:", "dm_tlen_middle_skip", "0"),
            ("Top Offset:", "dm_tlen_top_offset", "5"),
            ("Bottom Offset:", "dm_tlen_bottom_offset", "5"),
            ("Terminal Search Offset:", "dm_tlen_search_offset", "20"),
            ("Edge Min White Count:", "dm_tlen_edge_white", "5"),
            ("Edge Min Black Count:", "dm_tlen_edge_black", "5"),
        ]

        for r, (txt, name, val) in enumerate(labels):
            gt.addWidget(self._create_label(txt), r, 0)
            le = self._create_line_edit(val, name)
            gt.addWidget(le, r, 1)

        right.addWidget(grp_tlen)
        right.addStretch()

        top.addLayout(right)
        root.addLayout(top)

        # =================================================
        # Body Width
        # =================================================
        grp_bw = QGroupBox("Body Width")
        grp_bw.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gbw = QGridLayout(grp_bw)
        gbw.setContentsMargins(10, 15, 10, 10)
        gbw.setHorizontalSpacing(10)
        gbw.setVerticalSpacing(8)

        bw_fields = [
            ("Width Search Offset:", "dm_bw_search_offset", "30"),
            ("Left Offset:", "dm_bw_left_offset", "50"),
            ("Right Offset:", "dm_bw_right_offset", "50"),
        ]

        for r, (txt, name, val) in enumerate(bw_fields):
            gbw.addWidget(self._create_label(txt), r, 0)
            le = self._create_line_edit(val, name)
            gbw.addWidget(le, r, 1)

        root.addWidget(grp_bw)

        # =================================================
        # Terminal Width
        # =================================================
        grp_tw = QGroupBox("Terminal Width")
        grp_tw.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gtw = QGridLayout(grp_tw)
        gtw.setContentsMargins(10, 15, 10, 10)
        gtw.setHorizontalSpacing(10)
        gtw.setVerticalSpacing(8)

        tw_fields = [
            ("Top Offset:", "dm_tw_top_offset", "1"),
            ("Bottom Offset:", "dm_tw_bottom_offset", "1"),
        ]

        for r, (txt, name, val) in enumerate(tw_fields):
            gtw.addWidget(self._create_label(txt), r, 0)
            le = self._create_line_edit(val, name)
            gtw.addWidget(le, r, 1)

        root.addWidget(grp_tw)

        # =================================================
        # Adjust Pkg Loc By Body Height
        # =================================================
        grp_adj = QGroupBox("Adjust Pkg Loc By Body Height")
        grp_adj.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        ga = QVBoxLayout(grp_adj)
        ga.setContentsMargins(10, 15, 10, 10)
        ga.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(20)
        cb_adj = self._create_checkbox("Enable")
        cb_adj.setObjectName("dm_adj_enable")

        cb_avg = self._create_checkbox("Use Edge Average")
        cb_avg.setObjectName("dm_adj_use_edge_avg")

        row.addWidget(cb_adj)
        row.addWidget(cb_avg)
        ga.addLayout(row)

        grp_img2 = QGroupBox("Insp Image")
        grp_img2.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gi2 = QGridLayout(grp_img2)
        gi2.setContentsMargins(8, 12, 8, 8)
        gi2.setHorizontalSpacing(10)
        gi2.setVerticalSpacing(6)

        bg_img2 = QButtonGroup(tab)
        bg_img2.setObjectName("dm_adj_insp_image")

        for i, txt in enumerate(radios):
            rb = self._create_radio_button(txt)
            bg_img2.addButton(rb)
            gi2.addWidget(rb, i // 4, i % 4)

        bg_img2.buttons()[0].setChecked(True)
        ga.addWidget(grp_img2)

        bc = QHBoxLayout()
        bc.setSpacing(10)
        bc.addWidget(self._create_label("Body Contrast:"))

        le_bc = self._create_line_edit("15", "dm_body_contrast")

        sl_bc = QSlider(Qt.Horizontal)
        sl_bc.setRange(0, 255)
        sl_bc.setObjectName("dm_body_contrast_slider")

        self._sync_slider_lineedit(sl_bc, le_bc)

        bc.addWidget(le_bc)
        bc.addWidget(sl_bc)
        ga.addLayout(bc)

        root.addWidget(grp_adj)
        root.addStretch()

        return tab

    def _body_smear_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QVBoxLayout(tab)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(15)

        grp_main = QGroupBox("Body Smear")
        grp_main.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        main_layout = QHBoxLayout(grp_main)
        main_layout.setContentsMargins(10, 15, 10, 10)
        main_layout.setSpacing(20)

        def smear_column(idx: int, title: str, show_red_dot=False):
            prefix = f"bs{idx}_"
            col = QVBoxLayout()
            col.setSpacing(10)

            # =================================================
            # Insp Image
            # =================================================
            grp_img = QGroupBox(f"Insp Image ({title})")
            grp_img.setStyleSheet("""
                QGroupBox {
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            gi = QGridLayout(grp_img)
            gi.setContentsMargins(8, 12, 8, 8)
            gi.setHorizontalSpacing(10)
            gi.setVerticalSpacing(6)

            radios = ["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]
            bg = QButtonGroup(tab)
            bg.setObjectName(prefix + "insp_image")

            for i, txt in enumerate(radios):
                rb = self._create_radio_button(txt)
                bg.addButton(rb)
                gi.addWidget(rb, i // 4, i % 4)

            bg.buttons()[0].setChecked(True)
            col.addWidget(grp_img)

            # =================================================
            # Enable options
            # =================================================
            cb_enable = self._create_checkbox(f"Enable {title}")
            cb_enable.setObjectName(prefix + "enable")
            col.addWidget(cb_enable)

            cb_shot2 = self._create_checkbox("Enable Shot2")
            cb_shot2.setObjectName(prefix + "shot2")
            col.addWidget(cb_shot2)

            cb_avg = self._create_checkbox("Use Average Contrast")
            cb_avg.setObjectName(prefix + "use_avg_contrast")
            col.addWidget(cb_avg)

            # =================================================
            # Contrast
            # =================================================
            c_row = QHBoxLayout()
            c_row.setSpacing(10)
            c_row.addWidget(self._create_label("Contrast:"))

            sl = QSlider(Qt.Horizontal)
            sl.setRange(0, 255)
            sl.setObjectName(prefix + "contrast_slider")

            le = self._create_line_edit("30", prefix + "contrast")

            self._sync_slider_lineedit(sl, le)

            c_row.addWidget(sl)
            c_row.addWidget(le)
            col.addLayout(c_row)

            # =================================================
            # Params
            # =================================================
            grid = QGridLayout()
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(8)

            params = [
                ("Min. Area:", "min_area", "100"),
                ("Min. Sqr Size:", "min_square", "10"),
                ("Area Min %:", "area_min_pct", "5"),
                ("Size Min %:", "size_min_pct", "5"),
            ]

            for r, (lbl, name, val) in enumerate(params):
                grid.addWidget(self._create_label(lbl), r, 0)
                le = self._create_line_edit(val, prefix + name)
                grid.addWidget(le, r, 1)

            col.addLayout(grid)

            cb_or = self._create_checkbox("Apply (OR)")
            cb_or.setObjectName(prefix + "apply_or")
            col.addWidget(cb_or)

            # =================================================
            # Offset
            # =================================================
            grp_off = QGroupBox(f"{title} Offset")
            grp_off.setStyleSheet("""
                QGroupBox {
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            go = QGridLayout(grp_off)
            go.setContentsMargins(8, 12, 8, 8)
            go.setHorizontalSpacing(10)
            go.setVerticalSpacing(6)

            offsets = [
                ("Top:", "offset_top", "5"),
                ("Bottom:", "offset_bottom", "5"),
                ("Left:", "offset_left", "5"),
                ("Right:", "offset_right", "5"),
            ]

            for r, (lbl, name, val) in enumerate(offsets):
                go.addWidget(self._create_label(lbl), r, 0)
                le = self._create_line_edit(val, prefix + name)
                go.addWidget(le, r, 1)

            col.addWidget(grp_off)

            # =================================================
            # Red dot
            # =================================================
            if show_red_dot:
                rd = QHBoxLayout()
                rd.setSpacing(10)
                rd.addWidget(self._create_label("Red Dot Min. Count"))

                le_rd = self._create_line_edit("0", prefix + "red_dot_min")
                rd.addWidget(le_rd)

                col.addLayout(rd)

            col.addStretch()
            return col

        main_layout.addLayout(smear_column(1, "Body Smear 1"))
        main_layout.addLayout(smear_column(2, "Body Smear 2"))
        main_layout.addLayout(smear_column(3, "Body Smear 3", show_red_dot=True))

        root.addWidget(grp_main)

        # =================================================
        # Reverse Chip Check
        # =================================================
        grp_rev = QGroupBox("Reverse Chip Check")
        grp_rev.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gr = QVBoxLayout(grp_rev)
        gr.setContentsMargins(10, 15, 10, 10)
        gr.setSpacing(10)

        cb_rev = self._create_checkbox("Enable Reverse Chip Check")
        cb_rev.setObjectName("bs_reverse_enable")
        gr.addWidget(cb_rev)

        grp_white = QGroupBox("White")
        grp_white.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gw = QHBoxLayout(grp_white)
        gw.setContentsMargins(8, 12, 8, 8)
        gw.setSpacing(10)

        cb_white = self._create_checkbox("Enable")
        cb_white.setObjectName("bs_white_enable")

        le_white = self._create_line_edit("20", "bs_white_contrast")

        gw.addWidget(cb_white)
        gw.addWidget(self._create_label("Contrast (Difference):"))
        gw.addWidget(le_white)

        gr.addWidget(grp_white)
        root.addWidget(grp_rev)

        root.addStretch()
        return tab

    # Body stain tab
    def _body_stain_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QVBoxLayout(tab)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(15)

        grp_main = QGroupBox("Body Stain")
        grp_main.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        main = QVBoxLayout(grp_main)
        main.setContentsMargins(10, 15, 10, 10)
        main.setSpacing(15)

        # =================================================
        # Insp Image + Filter
        # =================================================
        top_row = QHBoxLayout()
        top_row.setSpacing(20)

        grp_img = QGroupBox("Insp Image")
        grp_img.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gi = QGridLayout(grp_img)
        gi.setContentsMargins(10, 15, 10, 10)
        gi.setHorizontalSpacing(10)
        gi.setVerticalSpacing(6)

        radios = ["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]
        bg_img = QButtonGroup(tab)
        bg_img.setObjectName("bs_insp_image")

        for i, txt in enumerate(radios):
            rb = self._create_radio_button(txt)
            bg_img.addButton(rb)
            gi.addWidget(rb, i // 4, i % 4)

        bg_img.buttons()[0].setChecked(True)
        top_row.addWidget(grp_img)

        grp_filter = QGroupBox("Filter Settings")
        grp_filter.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gf = QGridLayout(grp_filter)
        gf.setContentsMargins(10, 15, 10, 10)
        gf.setHorizontalSpacing(10)
        gf.setVerticalSpacing(8)

        cb_low = self._create_checkbox("Enable Filter Low Contrast")
        cb_low.setObjectName("bs_filter_low_enable")
        gf.addWidget(cb_low, 0, 0, 1, 2)

        gf.addWidget(self._create_label("Red:"), 1, 0)
        le_r = self._create_line_edit("60", "bs_filter_red")
        gf.addWidget(le_r, 1, 1)

        gf.addWidget(self._create_label("Green:"), 2, 0)
        le_g = self._create_line_edit("20", "bs_filter_green")
        gf.addWidget(le_g, 2, 1)

        gf.addWidget(self._create_label("Blue:"), 3, 0)
        le_b = self._create_line_edit("70", "bs_filter_blue")
        gf.addWidget(le_b, 3, 1)

        top_row.addWidget(grp_filter)
        main.addLayout(top_row)

        # =================================================
        # Body Stain 1 & 2
        # =================================================
        stain_row = QHBoxLayout()
        stain_row.setSpacing(20)

        def stain_block(title: str, prefix: str):
            grp = QGroupBox("")
            grp.setStyleSheet("""
                QGroupBox {
                    border: 1px solid #dddddd;
                    border-radius: 4px;
                    margin-top: 5px;
                    padding-top: 8px;
                    background-color: #f9f9f9;
                }
            """)
            v = QVBoxLayout(grp)
            v.setContentsMargins(10, 12, 10, 10)
            v.setSpacing(8)

            cb_enable = self._create_checkbox(title)
            cb_enable.setObjectName(f"{prefix}_enable")
            v.addWidget(cb_enable)

            c_row = QHBoxLayout()
            c_row.setSpacing(10)
            c_row.addWidget(self._create_label("Contrast:"))

            sl = QSlider(Qt.Horizontal)
            sl.setRange(0, 255)
            sl.setObjectName(f"{prefix}_contrast_slider")
            c_row.addWidget(sl)

            le_con = self._create_line_edit("40", f"{prefix}_contrast")
            c_row.addWidget(le_con)

            self._sync_slider_lineedit(sl, le_con)

            v.addLayout(c_row)

            grid = QGridLayout()
            grid.setHorizontalSpacing(10)
            grid.setVerticalSpacing(8)
            grid.addWidget(self._create_label("Min Area:"), 0, 0)
            le_area = self._create_line_edit("100", f"{prefix}_min_area")
            grid.addWidget(le_area, 0, 1)

            grid.addWidget(self._create_label("Min Square Size:"), 1, 0)
            le_sq = self._create_line_edit("10", f"{prefix}_min_square")
            grid.addWidget(le_sq, 1, 1)

            v.addLayout(grid)

            cb_or = self._create_checkbox("Apply (OR)")
            cb_or.setObjectName(f"{prefix}_apply_or")
            v.addWidget(cb_or)

            grp_off = QGroupBox("Offset")
            grp_off.setStyleSheet("""
                QGroupBox {
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            go = QGridLayout(grp_off)
            go.setContentsMargins(8, 12, 8, 8)
            go.setHorizontalSpacing(10)
            go.setVerticalSpacing(6)

            le_top = self._create_line_edit("5", f"{prefix}_off_top")
            go.addWidget(self._create_label("Top:"), 0, 0)
            go.addWidget(le_top, 0, 1)

            le_bottom = self._create_line_edit("5", f"{prefix}_off_bottom")
            go.addWidget(self._create_label("Bottom:"), 1, 0)
            go.addWidget(le_bottom, 1, 1)

            le_left = self._create_line_edit("5", f"{prefix}_off_left")
            go.addWidget(self._create_label("Left:"), 2, 0)
            go.addWidget(le_left, 2, 1)

            le_right = self._create_line_edit("5", f"{prefix}_off_right")
            go.addWidget(self._create_label("Right:"), 3, 0)
            go.addWidget(le_right, 3, 1)

            v.addWidget(grp_off)

            return grp

        stain_row.addWidget(stain_block("Enable Body Stain 1", "bs1"))

        grp2 = stain_block("Enable Body Stain 2", "bs2")

        v2 = grp2.layout()
        rd = QHBoxLayout()
        rd.setSpacing(10)
        rd.addWidget(self._create_label("Red Dot Min. Count"))
        le_rd = self._create_line_edit("0", "bs2_red_dot_min")
        rd.addWidget(le_rd)

        v2.addLayout(rd)

        stain_row.addWidget(grp2)
        main.addLayout(stain_row)

        # =================================================
        # Body Stand Stain
        # =================================================
        bottom = QHBoxLayout()
        bottom.setSpacing(20)

        grp_stand = QGroupBox("Body Stand Stain")
        grp_stand.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gs = QGridLayout(grp_stand)
        gs.setContentsMargins(10, 15, 10, 10)
        gs.setHorizontalSpacing(10)
        gs.setVerticalSpacing(8)

        cb_stand = self._create_checkbox("Enable Body Stand Stain")
        cb_stand.setObjectName("bs_stand_enable")
        gs.addWidget(cb_stand, 0, 0, 1, 2)

        gs.addWidget(self._create_label("Edge Contrast:"), 1, 0)
        le_edge = self._create_line_edit("125", "bs_stand_edge_contrast")
        gs.addWidget(le_edge, 1, 1)

        gs.addWidget(self._create_label("Difference:"), 2, 0)
        le_diff = self._create_line_edit("30", "bs_stand_difference")
        gs.addWidget(le_diff, 2, 1)

        bottom.addWidget(grp_stand)

        grp_off2 = QGroupBox("Offset")
        grp_off2.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        go2 = QGridLayout(grp_off2)
        go2.setContentsMargins(10, 15, 10, 10)
        go2.setHorizontalSpacing(10)
        go2.setVerticalSpacing(8)

        go2.addWidget(self._create_label("Top:"), 0, 0)
        le_top = self._create_line_edit("5", "bs_stand_off_top")
        go2.addWidget(le_top, 0, 1)

        go2.addWidget(self._create_label("Bottom:"), 1, 0)
        le_bottom = self._create_line_edit("5", "bs_stand_off_bottom")
        go2.addWidget(le_bottom, 1, 1)

        go2.addWidget(self._create_label("Left:"), 0, 2)
        le_left = self._create_line_edit("5", "bs_stand_off_left")
        go2.addWidget(le_left, 0, 3)

        go2.addWidget(self._create_label("Right:"), 1, 2)
        le_right = self._create_line_edit("5", "bs_stand_off_right")
        go2.addWidget(le_right, 1, 3)

        bottom.addWidget(grp_off2)

        main.addLayout(bottom)

        root.addWidget(grp_main)
        root.addStretch()

        return tab

    # Terminal plating deffect tab
    def _terminal_platting_defect_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QVBoxLayout(tab)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(15)

        grp_main = QGroupBox("Terminal Defect")
        grp_main.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        main = QVBoxLayout(grp_main)
        main.setContentsMargins(10, 15, 10, 10)
        main.setSpacing(15)

        # =================================================
        # Top Row
        # =================================================
        top = QHBoxLayout()
        top.setSpacing(20)

        grp_img = QGroupBox("Insp Image")
        grp_img.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gi = QGridLayout(grp_img)
        gi.setContentsMargins(10, 15, 10, 10)
        gi.setHorizontalSpacing(10)
        gi.setVerticalSpacing(6)

        radios = ["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]
        bg_img = QButtonGroup(tab)
        bg_img.setObjectName("tpd_insp_image")
        for i, txt in enumerate(radios):
            rb = self._create_radio_button(txt)
            bg_img.addButton(rb)
            gi.addWidget(rb, i // 4, i % 4)
        bg_img.buttons()[0].setChecked(True)
        top.addWidget(grp_img)

        opts = QVBoxLayout()
        opts.setSpacing(8)
        cb_bold = self._create_checkbox("Enable Terminal Bold")
        cb_bold.setObjectName("tpd_enable_bold")
        opts.addWidget(cb_bold)
        cb_device = self._create_checkbox("Use Device Contrast")
        cb_device.setObjectName("tpd_use_device_contrast")
        opts.addWidget(cb_device)
        top.addLayout(opts)

        main.addLayout(top)

        # =================================================
        # Two Columns
        # =================================================
        cols = QHBoxLayout()
        cols.setSpacing(20)

        def defect_column(title_left=True):
            prefix = "tpd_left_" if title_left else "tpd_right_"
            v = QVBoxLayout()
            v.setSpacing(10)

            cb_inc = self._create_checkbox(
                "Enable Incomplete Termination 1" if title_left
                else "Enable Incomplete Termination 2"
            )
            cb_inc.setObjectName(prefix + "incomplete_enable")
            v.addWidget(cb_inc)
            
            cb_shot2 = self._create_checkbox("Enable Shot2")
            cb_shot2.setObjectName(prefix + "shot2_enable")
            v.addWidget(cb_shot2)

            c_row = QHBoxLayout()
            c_row.setSpacing(10)
            c_row.addWidget(self._create_label("Contrast:"))
            sl = QSlider(Qt.Horizontal)
            sl.setRange(0, 255)
            sl.setObjectName(prefix + "contrast_slider")
            le_con = self._create_line_edit("10", prefix + "contrast")
            self._sync_slider_lineedit(sl, le_con)
            c_row.addWidget(sl)
            c_row.addWidget(le_con)
            v.addLayout(c_row)

            g = QGridLayout()
            g.setHorizontalSpacing(10)
            g.setVerticalSpacing(8)
            g.addWidget(self._create_label("Min Area:"), 0, 0)
            le_area = self._create_line_edit("100", prefix + "min_area")
            g.addWidget(le_area, 0, 1)
            
            g.addWidget(self._create_label("Min Square Size:"), 1, 0)
            le_sq = self._create_line_edit("10", prefix + "min_square")
            g.addWidget(le_sq, 1, 1)
            
            g.addWidget(self._create_label("Inspection Width:"), 2, 0)
            le_width = self._create_line_edit("5", prefix + "inspection_width")
            g.addWidget(le_width, 2, 1)
            
            g.addWidget(self._create_label("Corner Ellipse Mask Size:"), 3, 0)
            le_corner = self._create_line_edit("0", prefix + "corner_ellipse_mask")
            g.addWidget(le_corner, 3, 1)
            v.addLayout(g)

            cb_or = self._create_checkbox("Apply (OR)")
            cb_or.setObjectName(prefix + "apply_or")
            v.addWidget(cb_or)

            # Offset Group
            grp_off = QGroupBox(
                "Left Terminal Offset" if title_left else "Right Terminal Offset"
            )
            grp_off.setStyleSheet("""
                QGroupBox {
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            go = QGridLayout(grp_off)
            go.setContentsMargins(8, 12, 8, 8)
            go.setHorizontalSpacing(10)
            go.setVerticalSpacing(6)

            go.addWidget(self._create_label("Top:"), 0, 0)
            le_top = self._create_line_edit("5", prefix + "offset_top")
            go.addWidget(le_top, 0, 1)
            
            go.addWidget(self._create_label("Bottom:"), 1, 0)
            le_bottom = self._create_line_edit("5", prefix + "offset_bottom")
            go.addWidget(le_bottom, 1, 1)
            
            go.addWidget(self._create_label("Left:"), 2, 0)
            le_left = self._create_line_edit("5", prefix + "offset_left")
            go.addWidget(le_left, 2, 1)
            
            go.addWidget(self._create_label("Right:"), 2, 2)
            le_right = self._create_line_edit("5", prefix + "offset_right")
            go.addWidget(le_right, 2, 3)

            go.addWidget(self._create_label("Corner Offset X:"), 3, 0)
            le_corner_x = self._create_line_edit("2", prefix + "corner_offset_x")
            go.addWidget(le_corner_x, 3, 1)
            
            go.addWidget(self._create_label("Corner Offset Y:"), 4, 0)
            le_corner_y = self._create_line_edit("2", prefix + "corner_offset_y")
            go.addWidget(le_corner_y, 4, 1)

            v.addWidget(grp_off)

            return v

        cols.addLayout(defect_column(True))
        cols.addLayout(defect_column(False))

        main.addLayout(cols)
        root.addWidget(grp_main)
        root.addStretch()

        return tab

    # Terminal Black spot
    def _terminal_black_spot_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QVBoxLayout(tab)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(15)

        grp_main = QGroupBox("Terminal Pogo")
        grp_main.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        main = QVBoxLayout(grp_main)
        main.setContentsMargins(10, 15, 10, 10)
        main.setSpacing(15)

        # =================================================
        # Top row: Insp Image + Oxidation
        # =================================================
        top = QHBoxLayout()
        top.setSpacing(20)

        grp_img = QGroupBox("Insp Image")
        grp_img.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gi = QGridLayout(grp_img)
        gi.setContentsMargins(10, 15, 10, 10)
        gi.setHorizontalSpacing(10)
        gi.setVerticalSpacing(6)

        radios = ["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]
        bg_img = QButtonGroup(tab)
        bg_img.setObjectName("tbs_insp_image")
        for i, txt in enumerate(radios):
            rb = self._create_radio_button(txt)
            bg_img.addButton(rb)
            gi.addWidget(rb, i // 4, i % 4)
        bg_img.buttons()[0].setChecked(True)
        top.addWidget(grp_img)

        grp_oxid = QGroupBox("Oxidation")
        grp_oxid.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gox = QGridLayout(grp_oxid)
        gox.setContentsMargins(10, 15, 10, 10)
        gox.setHorizontalSpacing(10)
        gox.setVerticalSpacing(8)

        cb_oxid = self._create_checkbox("Enable Oxidation")
        cb_oxid.setObjectName("tbs_oxidation_enable")
        gox.addWidget(cb_oxid, 0, 0, 1, 2)
        
        gox.addWidget(self._create_label("Contrast Difference:"), 1, 0)
        le_oxid_contrast = self._create_line_edit("20", "tbs_oxidation_contrast")
        gox.addWidget(le_oxid_contrast, 1, 1)
        
        gox.addWidget(self._create_label("Top:"), 2, 0)
        le_oxid_top = self._create_line_edit("5", "tbs_oxidation_top")
        gox.addWidget(le_oxid_top, 2, 1)
        
        gox.addWidget(self._create_label("Bottom:"), 3, 0)
        le_oxid_bottom = self._create_line_edit("5", "tbs_oxidation_bottom")
        gox.addWidget(le_oxid_bottom, 3, 1)

        top.addWidget(grp_oxid)
        main.addLayout(top)

        # =================================================
        # Middle controls
        # =================================================
        mid = QHBoxLayout()
        mid.setSpacing(20)

        left = QVBoxLayout()
        left.setSpacing(8)
        cb_pogo = self._create_checkbox("Enable Terminal Pogo")
        cb_pogo.setObjectName("tbs_pogo_enable")
        left.addWidget(cb_pogo)
        
        cb_shot2 = self._create_checkbox("Enable Shot2")
        cb_shot2.setObjectName("tbs_shot2_enable")
        left.addWidget(cb_shot2)

        c_row = QHBoxLayout()
        c_row.setSpacing(10)
        c_row.addWidget(self._create_label("Contrast:"))
        sl_contrast = QSlider(Qt.Horizontal)
        sl_contrast.setRange(0, 255)
        sl_contrast.setObjectName("tbs_contrast_slider")
        le_contrast = self._create_line_edit("5", "tbs_contrast")
        self._sync_slider_lineedit(sl_contrast, le_contrast)
        c_row.addWidget(sl_contrast)
        c_row.addWidget(le_contrast)
        left.addLayout(c_row)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.addWidget(self._create_label("Min Area:"), 0, 0)
        le_area = self._create_line_edit("100", "tbs_min_area")
        grid.addWidget(le_area, 0, 1)
        
        grid.addWidget(self._create_label("Min Square Size:"), 1, 0)
        le_sq = self._create_line_edit("10", "tbs_min_square")
        grid.addWidget(le_sq, 1, 1)
        
        grid.addWidget(self._create_label("Inspection Width:"), 2, 0)
        le_width = self._create_line_edit("0", "tbs_inspection_width")
        grid.addWidget(le_width, 2, 1)
        left.addLayout(grid)

        mid.addLayout(left)
        main.addLayout(mid)

        # =================================================
        # Bottom: Left / Right Terminal Offset
        # =================================================
        offsets = QHBoxLayout()
        offsets.setSpacing(20)

        def offset_group(title, prefix):
            grp = QGroupBox(title)
            grp.setStyleSheet("""
                QGroupBox {
                    font-size: 12px;
                }
            """)
            g = QGridLayout(grp)
            g.setContentsMargins(10, 15, 10, 10)
            g.setHorizontalSpacing(10)
            g.setVerticalSpacing(8)

            g.addWidget(self._create_label("Top:"), 0, 0)
            le_top = self._create_line_edit("5", prefix + "offset_top")
            g.addWidget(le_top, 0, 1)
            
            g.addWidget(self._create_label("Left:"), 0, 2)
            le_left = self._create_line_edit("5", prefix + "offset_left")
            g.addWidget(le_left, 0, 3)

            g.addWidget(self._create_label("Bottom:"), 1, 0)
            le_bottom = self._create_line_edit("5", prefix + "offset_bottom")
            g.addWidget(le_bottom, 1, 1)
            
            g.addWidget(self._create_label("Right:"), 1, 2)
            le_right = self._create_line_edit("5", prefix + "offset_right")
            g.addWidget(le_right, 1, 3)

            g.addWidget(self._create_label("Corner Offset X:"), 2, 0)
            le_corner_x = self._create_line_edit("2", prefix + "corner_offset_x")
            g.addWidget(le_corner_x, 2, 1)
            
            g.addWidget(self._create_label("Corner Offset Y:"), 3, 0)
            le_corner_y = self._create_line_edit("2", prefix + "corner_offset_y")
            g.addWidget(le_corner_y, 3, 1)
            return grp

        offsets.addWidget(offset_group("Left Terminal Offset", "tbs_left_"))
        offsets.addWidget(offset_group("Right Terminal Offset", "tbs_right_"))

        main.addLayout(offsets)

        root.addWidget(grp_main)
        root.addStretch()

        return tab

    # body crack tab
    def _body_crack_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QVBoxLayout(tab)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(15)

        top = QHBoxLayout()
        top.setSpacing(20)

        # =================================================
        # LEFT: Body Crack (White Defect)
        # =================================================
        grp_left = QGroupBox("Body Crack (White Defect)")
        grp_left.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        l = QVBoxLayout(grp_left)
        l.setContentsMargins(10, 15, 10, 10)
        l.setSpacing(10)

        img = QGroupBox("Insp Image")
        img.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gi = QGridLayout(img)
        gi.setContentsMargins(8, 12, 8, 8)
        gi.setHorizontalSpacing(10)
        gi.setVerticalSpacing(6)

        bg_left = QButtonGroup(tab)
        bg_left.setObjectName("bc_left_insp_image")
        for i, t in enumerate(["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]):
            rb = self._create_radio_button(t)
            bg_left.addButton(rb)
            gi.addWidget(rb, i // 4, i % 4)
        bg_left.buttons()[0].setChecked(True)
        l.addWidget(img)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self._create_label("Parameter Set"))
        combo = QComboBox()
        combo.addItems(["High Contrast"])
        combo.setObjectName("bc_left_param_set")
        row.addWidget(combo)
        row.addStretch()
        l.addLayout(row)

        cb_enable = self._create_checkbox("Enable")
        cb_enable.setObjectName("bc_left_enable")
        l.addWidget(cb_enable)
        
        cb_reject = self._create_checkbox("Low And High Contrast Rejection")
        cb_reject.setObjectName("bc_left_reject_enable")
        l.addWidget(cb_reject)

        c = QHBoxLayout()
        c.setSpacing(10)
        c.addWidget(self._create_label("Contrast"))
        sl = QSlider(Qt.Horizontal)
        sl.setRange(0, 255)
        sl.setObjectName("bc_left_contrast_slider")
        le_con = self._create_line_edit("10", "bc_left_contrast")
        self._sync_slider_lineedit(sl, le_con)
        c.addWidget(sl)
        c.addWidget(le_con)
        l.addLayout(c)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.addWidget(self._create_label("Min. Length"), 0, 0)
        le_len = self._create_line_edit("20", "bc_left_min_length")
        grid.addWidget(le_len, 0, 1)
        
        grid.addWidget(self._create_label("Min. Elongation"), 1, 0)
        le_elong = self._create_line_edit("5", "bc_left_min_elongation")
        grid.addWidget(le_elong, 1, 1)
        
        grid.addWidget(self._create_label("Broken Connection"), 2, 0)
        le_broken = self._create_line_edit("0", "bc_left_broken_connection")
        grid.addWidget(le_broken, 2, 1)
        l.addLayout(grid)

        top.addWidget(grp_left)

        # =================================================
        # RIGHT: Hairline + Stain Crack
        # =================================================
        right = QVBoxLayout()
        right.setSpacing(15)

        # Hairline Crack
        grp_hair = QGroupBox("Body HairLine Crack")
        grp_hair.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        h = QVBoxLayout(grp_hair)
        h.setContentsMargins(10, 15, 10, 10)
        h.setSpacing(10)

        img2 = QGroupBox("Insp Image")
        img2.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gi2 = QGridLayout(img2)
        gi2.setContentsMargins(8, 12, 8, 8)
        gi2.setHorizontalSpacing(10)
        gi2.setVerticalSpacing(6)

        bg_hair = QButtonGroup(tab)
        bg_hair.setObjectName("bc_hair_insp_image")
        for i, t in enumerate(["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]):
            rb = self._create_radio_button(t)
            bg_hair.addButton(rb)
            gi2.addWidget(rb, i // 4, i % 4)
        bg_hair.buttons()[0].setChecked(True)
        h.addWidget(img2)

        cb_black = self._create_checkbox("Enable Black Defect")
        cb_black.setObjectName("bc_hair_black_enable")
        h.addWidget(cb_black)
        
        cb_white = self._create_checkbox("Enable White Defect")
        cb_white.setObjectName("bc_hair_white_enable")
        h.addWidget(cb_white)

        ch = QHBoxLayout()
        ch.setSpacing(10)
        ch.addWidget(self._create_label("Contrast"))
        sl_hair = QSlider(Qt.Horizontal)
        sl_hair.setRange(0, 255)
        sl_hair.setObjectName("bc_hair_contrast_slider")
        le_hair_con = self._create_line_edit("6", "bc_hair_contrast")
        self._sync_slider_lineedit(sl_hair, le_hair_con)
        ch.addWidget(sl_hair)
        ch.addWidget(le_hair_con)
        h.addLayout(ch)

        gh = QGridLayout()
        gh.setHorizontalSpacing(10)
        gh.setVerticalSpacing(8)
        gh.addWidget(self._create_label("Min. Length"), 0, 0)
        le_hair_len = self._create_line_edit("25", "bc_hair_min_length")
        gh.addWidget(le_hair_len, 0, 1)
        
        gh.addWidget(self._create_label("Noise Filtering Size"), 1, 0)
        le_noise = self._create_line_edit("5", "bc_hair_noise_filtering")
        gh.addWidget(le_noise, 1, 1)
        h.addLayout(gh)

        right.addWidget(grp_hair)

        # Body Stain Crack
        grp_stain = QGroupBox("Body Stain Crack")
        grp_stain.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        s = QVBoxLayout(grp_stain)
        s.setContentsMargins(10, 15, 10, 10)
        s.setSpacing(10)

        cb_stain = self._create_checkbox("Enable")
        cb_stain.setObjectName("bc_stain_enable")
        s.addWidget(cb_stain)

        cs = QHBoxLayout()
        cs.setSpacing(10)
        cs.addWidget(self._create_label("Contrast"))
        sl_stain = QSlider(Qt.Horizontal)
        sl_stain.setRange(0, 255)
        sl_stain.setObjectName("bc_stain_contrast_slider")
        le_stain_con = self._create_line_edit("150", "bc_stain_contrast")
        self._sync_slider_lineedit(sl_stain, le_stain_con)
        cs.addWidget(sl_stain)
        cs.addWidget(le_stain_con)
        s.addLayout(cs)

        gs = QGridLayout()
        gs.setHorizontalSpacing(10)
        gs.setVerticalSpacing(8)
        gs.addWidget(self._create_label("Min. Length"), 0, 0)
        le_stain_len = self._create_line_edit("10", "bc_stain_min_length")
        gs.addWidget(le_stain_len, 0, 1)
        
        gs.addWidget(self._create_label("Min. Area"), 1, 0)
        le_stain_area = self._create_line_edit("20", "bc_stain_min_area")
        gs.addWidget(le_stain_area, 1, 1)
        
        gs.addWidget(self._create_label("Corner Contrast Diff"), 2, 0)
        le_stain_corner = self._create_line_edit("12", "bc_stain_corner_contrast")
        gs.addWidget(le_stain_corner, 2, 1)
        s.addLayout(gs)

        right.addWidget(grp_stain)

        top.addLayout(right)
        root.addLayout(top)

        # =================================================
        # OFFSET
        # =================================================
        grp_off = QGroupBox("Offset")
        grp_off.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        go = QGridLayout(grp_off)
        go.setContentsMargins(10, 15, 10, 10)
        go.setHorizontalSpacing(10)
        go.setVerticalSpacing(8)

        go.addWidget(self._create_label("Top"), 0, 0)
        le_off_top = self._create_line_edit("5", "bc_offset_top")
        go.addWidget(le_off_top, 0, 1)
        
        go.addWidget(self._create_label("Left"), 0, 2)
        le_off_left = self._create_line_edit("5", "bc_offset_left")
        go.addWidget(le_off_left, 0, 3)
        
        go.addWidget(self._create_label("Bottom"), 1, 0)
        le_off_bottom = self._create_line_edit("5", "bc_offset_bottom")
        go.addWidget(le_off_bottom, 1, 1)
        
        go.addWidget(self._create_label("Right"), 1, 2)
        le_off_right = self._create_line_edit("5", "bc_offset_right")
        go.addWidget(le_off_right, 1, 3)

        root.addWidget(grp_off)
        root.addStretch()

        return tab

    # Terminal Corner Deffect
    def _terminal_corner_deffect_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QHBoxLayout(tab)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(20)

        # =================================================
        # LEFT: Inner Term Chipoff
        # =================================================
        grp_inner = QGroupBox("Inner Term Chipoff")
        grp_inner.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        li = QVBoxLayout(grp_inner)
        li.setContentsMargins(10, 15, 10, 10)
        li.setSpacing(10)

        def insp_image(prefix=""):
            g = QGroupBox("Insp Image")
            g.setStyleSheet("""
                QGroupBox {
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            gl = QGridLayout(g)
            gl.setContentsMargins(8, 12, 8, 8)
            gl.setHorizontalSpacing(10)
            gl.setVerticalSpacing(6)
            bg = QButtonGroup(tab)
            if prefix:
                bg.setObjectName(prefix + "insp_image")
            for i, t in enumerate(["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]):
                rb = self._create_radio_button(t)
                bg.addButton(rb)
                gl.addWidget(rb, i // 4, i % 4)
            if bg.buttons():
                bg.buttons()[0].setChecked(True)
            return g

        li.addWidget(insp_image("tcd_inner_"))

        cb_enable = self._create_checkbox("Enable")
        cb_enable.setObjectName("tcd_inner_enable")
        li.addWidget(cb_enable)
        
        cb_and = self._create_checkbox("Apply AND")
        cb_and.setObjectName("tcd_inner_apply_and")
        li.addWidget(cb_and)
        
        cb_black = self._create_checkbox("Black Pixels Count")
        cb_black.setObjectName("tcd_inner_black_pixels")
        li.addWidget(cb_black)
        
        cb_avg = self._create_checkbox("Use Average Contrast")
        cb_avg.setObjectName("tcd_inner_avg_contrast")
        li.addWidget(cb_avg)
        
        cb_device = self._create_checkbox("Use Device Contrast")
        cb_device.setObjectName("tcd_inner_device_contrast")
        li.addWidget(cb_device)

        c = QHBoxLayout()
        c.setSpacing(10)
        c.addWidget(self._create_label("Contrast"))
        sl_contrast = QSlider(Qt.Horizontal)
        sl_contrast.setRange(0, 255)
        sl_contrast.setObjectName("tcd_inner_contrast_slider")
        le_contrast = self._create_line_edit("20", "tcd_inner_contrast")
        self._sync_slider_lineedit(sl_contrast, le_contrast)
        c.addWidget(sl_contrast)
        c.addWidget(le_contrast)
        c.addWidget(self._create_label("Level"))
        li.addLayout(c)

        g = QGridLayout()
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.addWidget(self._create_label("Inspection Width X"), 0, 0)
        le_width_x = self._create_line_edit("20", "tcd_inner_width_x")
        g.addWidget(le_width_x, 0, 1)
        
        g.addWidget(self._create_label("Inspection Width Y"), 0, 2)
        le_width_y = self._create_line_edit("20", "tcd_inner_width_y")
        g.addWidget(le_width_y, 0, 3)

        g.addWidget(self._create_label("Tolerance X"), 1, 0)
        le_tol_x = self._create_line_edit("0", "tcd_inner_tolerance_x")
        g.addWidget(le_tol_x, 1, 1)
        
        g.addWidget(self._create_label("Min Area"), 1, 2)
        le_min_area = self._create_line_edit("25", "tcd_inner_min_area")
        g.addWidget(le_min_area, 1, 3)

        g.addWidget(self._create_label("Min Width"), 2, 0)
        le_min_width = self._create_line_edit("5", "tcd_inner_min_width")
        g.addWidget(le_min_width, 2, 1)
        
        g.addWidget(self._create_label("Min Height"), 2, 2)
        le_min_height = self._create_line_edit("5", "tcd_inner_min_height")
        g.addWidget(le_min_height, 2, 3)

        g.addWidget(self._create_label("Corner Ellipse Mask Size"), 3, 0)
        le_ellipse = self._create_line_edit("0", "tcd_inner_ellipse_mask")
        g.addWidget(le_ellipse, 3, 1)
        li.addLayout(g)

        grp_corner = QGroupBox("Corner Offset")
        grp_corner.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gc = QGridLayout(grp_corner)
        gc.setContentsMargins(8, 12, 8, 8)
        gc.setHorizontalSpacing(10)
        gc.setVerticalSpacing(6)
        cb_corner = self._create_checkbox("Enable")
        cb_corner.setObjectName("tcd_inner_corner_enable")
        gc.addWidget(cb_corner, 0, 0)
        
        gc.addWidget(self._create_label("X"), 0, 1)
        le_corner_x = self._create_line_edit("5", "tcd_inner_corner_x")
        gc.addWidget(le_corner_x, 0, 2)
        
        gc.addWidget(self._create_label("Y"), 0, 3)
        le_corner_y = self._create_line_edit("5", "tcd_inner_corner_y")
        gc.addWidget(le_corner_y, 0, 4)
        li.addWidget(grp_corner)

        grp_wo = QGroupBox("Without Corner Offset")
        grp_wo.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gwo = QGridLayout(grp_wo)
        gwo.setContentsMargins(8, 12, 8, 8)
        gwo.setHorizontalSpacing(10)
        gwo.setVerticalSpacing(6)
        gwo.addWidget(self._create_label("Top"), 0, 0)
        le_top = self._create_line_edit("5", "tcd_inner_wo_top")
        gwo.addWidget(le_top, 0, 1)
        
        gwo.addWidget(self._create_label("Bottom"), 0, 2)
        le_bottom = self._create_line_edit("5", "tcd_inner_wo_bottom")
        gwo.addWidget(le_bottom, 0, 3)
        
        gwo.addWidget(self._create_label("Left"), 1, 0)
        le_left = self._create_line_edit("5", "tcd_inner_wo_left")
        gwo.addWidget(le_left, 1, 1)
        
        gwo.addWidget(self._create_label("Right"), 1, 2)
        le_right = self._create_line_edit("5", "tcd_inner_wo_right")
        gwo.addWidget(le_right, 1, 3)
        li.addWidget(grp_wo)

        grp_cmp = QGroupBox("Compare Terminal Corners")
        grp_cmp.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gcmp = QGridLayout(grp_cmp)
        gcmp.setContentsMargins(8, 12, 8, 8)
        gcmp.setHorizontalSpacing(10)
        gcmp.setVerticalSpacing(6)
        cb_cmp = self._create_checkbox("Enable")
        cb_cmp.setObjectName("tcd_inner_compare_enable")
        gcmp.addWidget(cb_cmp, 0, 0)
        
        gcmp.addWidget(self._create_label("Intensity Difference"), 0, 1)
        le_intensity = self._create_line_edit("30", "tcd_inner_intensity_diff")
        gcmp.addWidget(le_intensity, 0, 2)
        li.addWidget(grp_cmp)

        li.addWidget(insp_image("tcd_inner_2_"))
        root.addWidget(grp_inner)

        # =================================================
        # RIGHT: Outer Term Chipoff
        # =================================================
        grp_outer = QGroupBox("Outer Term Chipoff")
        grp_outer.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        lo = QVBoxLayout(grp_outer)
        lo.setContentsMargins(10, 15, 10, 10)
        lo.setSpacing(10)

        lo.addWidget(insp_image("tcd_outer_"))
        
        cb_outer_enable = self._create_checkbox("Enable")
        cb_outer_enable.setObjectName("tcd_outer_enable")
        lo.addWidget(cb_outer_enable)
        
        cb_pocket = self._create_checkbox("Enable Pocket Edge Filter")
        cb_pocket.setObjectName("tcd_outer_pocket_filter")
        lo.addWidget(cb_pocket)

        c2 = QHBoxLayout()
        c2.setSpacing(10)
        c2.addWidget(self._create_label("Contrast (Background)"))
        sl_bg = QSlider(Qt.Horizontal)
        sl_bg.setRange(0, 255)
        sl_bg.setObjectName("tcd_outer_contrast_slider")
        le_bg = self._create_line_edit("20", "tcd_outer_contrast")
        self._sync_slider_lineedit(sl_bg, le_bg)
        c2.addWidget(sl_bg)
        c2.addWidget(le_bg)
        c2.addWidget(self._create_label("Level"))
        lo.addLayout(c2)

        g2 = QGridLayout()
        g2.setHorizontalSpacing(10)
        g2.setVerticalSpacing(8)
        g2.addWidget(self._create_label("Min Area"), 0, 0)
        le_outer_area = self._create_line_edit("10", "tcd_outer_min_area")
        g2.addWidget(le_outer_area, 0, 1)
        
        g2.addWidget(self._create_label("Min Sq Size"), 1, 0)
        le_outer_sq = self._create_line_edit("5", "tcd_outer_min_square")
        g2.addWidget(le_outer_sq, 1, 1)
        
        g2.addWidget(self._create_label("Minimum %"), 2, 0)
        le_outer_pct = self._create_line_edit("20", "tcd_outer_min_percent")
        g2.addWidget(le_outer_pct, 2, 1)
        lo.addLayout(g2)

        grp_w = QGroupBox("Inspection Width")
        grp_w.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gw = QGridLayout(grp_w)
        gw.setContentsMargins(8, 12, 8, 8)
        gw.setHorizontalSpacing(10)
        gw.setVerticalSpacing(6)
        for i, t in enumerate(["Left", "Right", "Top", "Bottom"]):
            cb_width = self._create_checkbox(t)
            cb_width.setObjectName(f"tcd_outer_width_{t.lower()}_enable")
            gw.addWidget(cb_width, i, 0)
            
            le_width = self._create_line_edit("10", f"tcd_outer_width_{t.lower()}")
            gw.addWidget(le_width, i, 1)
        lo.addWidget(grp_w)

        def offset_group(title, prefix):
            g = QGroupBox(title)
            g.setStyleSheet("""
                QGroupBox {
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            gl = QGridLayout(g)
            gl.setContentsMargins(8, 12, 8, 8)
            gl.setHorizontalSpacing(10)
            gl.setVerticalSpacing(6)
            gl.addWidget(self._create_label("Top"), 0, 0)
            le_top = self._create_line_edit("5", prefix + "offset_top")
            gl.addWidget(le_top, 0, 1)
            
            gl.addWidget(self._create_label("Left"), 0, 2)
            le_left = self._create_line_edit("5", prefix + "offset_left")
            gl.addWidget(le_left, 0, 3)
            
            gl.addWidget(self._create_label("Bottom"), 1, 0)
            le_bottom = self._create_line_edit("5", prefix + "offset_bottom")
            gl.addWidget(le_bottom, 1, 1)
            
            gl.addWidget(self._create_label("Right"), 1, 2)
            le_right = self._create_line_edit("5", prefix + "offset_right")
            gl.addWidget(le_right, 1, 3)
            return g

        lo.addWidget(offset_group("Left Terminal Offset", "tcd_outer_left_"))
        lo.addWidget(offset_group("Right Terminal Offset", "tcd_outer_right_"))

        grp_hi = QGroupBox("Inner Term Chipoff High Intensity")
        grp_hi.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        ghi = QGridLayout(grp_hi)
        ghi.setContentsMargins(8, 12, 8, 8)
        ghi.setHorizontalSpacing(10)
        ghi.setVerticalSpacing(6)
        cb_hi = self._create_checkbox("Enable")
        cb_hi.setObjectName("tcd_outer_hi_enable")
        ghi.addWidget(cb_hi, 0, 0)
        
        ghi.addWidget(self._create_label("Min. Intensity"), 0, 1)
        le_hi_intensity = self._create_line_edit("95", "tcd_outer_hi_intensity")
        ghi.addWidget(le_hi_intensity, 0, 2)
        lo.addWidget(grp_hi)

        grp_img2 = QGroupBox("Insp Image")
        grp_img2.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gi2 = QHBoxLayout(grp_img2)
        gi2.setContentsMargins(8, 12, 8, 8)
        gi2.setSpacing(10)
        bg_img2 = QButtonGroup(tab)
        bg_img2.setObjectName("tcd_outer_insp_image_rgb")
        for t in ["Red", "Green", "Blue"]:
            rb = self._create_radio_button(t)
            bg_img2.addButton(rb)
            gi2.addWidget(rb)
        if bg_img2.buttons():
            bg_img2.buttons()[0].setChecked(True)
        lo.addWidget(grp_img2)

        root.addWidget(grp_outer)

        return tab

    # Body Edge Effect
    def _body_edge_effect_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QHBoxLayout(tab)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(20)

        # ==================================================
        # LEFT SIDE — BLACK DEFECT
        # ==================================================
        grp_black = QGroupBox("Black Defect")
        grp_black.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        left = QVBoxLayout(grp_black)
        left.setContentsMargins(10, 15, 10, 10)
        left.setSpacing(10)

        # Insp Image
        grp_img_black = QGroupBox("Insp Image")
        grp_img_black.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        img_l = QGridLayout(grp_img_black)
        img_l.setContentsMargins(8, 12, 8, 8)
        img_l.setHorizontalSpacing(10)
        img_l.setVerticalSpacing(6)

        bg_left = QButtonGroup(tab)
        bg_left.setObjectName("bee_left_insp_image")
        for i, txt in enumerate(["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]):
            rb = self._create_radio_button(txt)
            bg_left.addButton(rb)
            img_l.addWidget(rb, i // 4, i % 4)
        bg_left.buttons()[0].setChecked(True)
        left.addWidget(grp_img_black)

        cb_enable = self._create_checkbox("Enable")
        cb_enable.setObjectName("bee_left_enable")
        left.addWidget(cb_enable)

        # Contrast
        c1 = QGridLayout()
        c1.setHorizontalSpacing(10)
        c1.setVerticalSpacing(8)
        c1.addWidget(self._create_label("Contrast (Top):"), 0, 0)
        sl_top = QSlider(Qt.Horizontal)
        sl_top.setRange(0, 255)
        sl_top.setObjectName("bee_left_contrast_top_slider")
        le_top = self._create_line_edit("20", "bee_left_contrast_top")
        self._sync_slider_lineedit(sl_top, le_top)
        c1.addWidget(sl_top, 0, 1)
        c1.addWidget(le_top, 0, 2)
        c1.addWidget(self._create_label("Levels"), 0, 3)

        c1.addWidget(self._create_label("Contrast (Bot):"), 1, 0)
        sl_bot = QSlider(Qt.Horizontal)
        sl_bot.setRange(0, 255)
        sl_bot.setObjectName("bee_left_contrast_bot_slider")
        le_bot = self._create_line_edit("20", "bee_left_contrast_bot")
        self._sync_slider_lineedit(sl_bot, le_bot)
        c1.addWidget(sl_bot, 1, 1)
        c1.addWidget(le_bot, 1, 2)
        c1.addWidget(self._create_label("Levels"), 1, 3)

        left.addLayout(c1)

        # Area
        g_area = QGridLayout()
        g_area.setHorizontalSpacing(10)
        g_area.setVerticalSpacing(8)
        g_area.addWidget(self._create_label("Min Area:"), 0, 0)
        le_area = self._create_line_edit("30", "bee_left_min_area")
        g_area.addWidget(le_area, 0, 1)
        g_area.addWidget(self._create_label("Min Sqr Size:"), 1, 0)
        le_sqr = self._create_line_edit("3", "bee_left_min_square")
        g_area.addWidget(le_sqr, 1, 1)
        left.addLayout(g_area)

        # Edge Width & Offset
        grp_edge = QGroupBox("Edge Width")
        grp_edge.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        ge = QGridLayout(grp_edge)
        ge.setContentsMargins(8, 12, 8, 8)
        ge.setHorizontalSpacing(10)
        ge.setVerticalSpacing(6)
        edge_labels = ["Top", "Bottom", "Left", "Right"]
        for r, lbl in enumerate(edge_labels):
            ge.addWidget(self._create_label(lbl), r, 0)
            le_edge = self._create_line_edit("10", f"bee_left_edge_width_{lbl.lower()}")
            ge.addWidget(le_edge, r, 1)
        left.addWidget(grp_edge)

        grp_offset = QGroupBox("Insp Offset")
        grp_offset.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        go = QGridLayout(grp_offset)
        go.setContentsMargins(8, 12, 8, 8)
        go.setHorizontalSpacing(10)
        go.setVerticalSpacing(6)
        offset_labels = ["Top", "Bottom", "Left", "Right"]
        for r, lbl in enumerate(offset_labels):
            go.addWidget(self._create_label(lbl), r, 0)
            le_off = self._create_line_edit("5", f"bee_left_offset_{lbl.lower()}")
            go.addWidget(le_off, r, 1)
        left.addWidget(grp_offset)

        grp_corner = QGroupBox("Corner Mask Size")
        grp_corner.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gc = QGridLayout(grp_corner)
        gc.setContentsMargins(8, 12, 8, 8)
        gc.setHorizontalSpacing(10)
        gc.setVerticalSpacing(6)
        gc.addWidget(self._create_label("Left"), 0, 0)
        le_corner_left = self._create_line_edit("5", "bee_left_corner_left")
        gc.addWidget(le_corner_left, 0, 1)
        gc.addWidget(self._create_label("Top"), 0, 2)
        le_corner_top = self._create_line_edit("5", "bee_left_corner_top")
        gc.addWidget(le_corner_top, 0, 3)
        gc.addWidget(self._create_label("Right"), 1, 0)
        le_corner_right = self._create_line_edit("5", "bee_left_corner_right")
        gc.addWidget(le_corner_right, 1, 1)
        gc.addWidget(self._create_label("Bottom"), 1, 2)
        le_corner_bot = self._create_line_edit("5", "bee_left_corner_bottom")
        gc.addWidget(le_corner_bot, 1, 3)
        left.addWidget(grp_corner)

        left.addStretch()

        # ==================================================
        # RIGHT SIDE — WHITE DEFECT
        # ==================================================
        grp_white = QGroupBox("White Defect")
        grp_white.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        right = QVBoxLayout(grp_white)
        right.setContentsMargins(10, 15, 10, 10)
        right.setSpacing(10)

        # Use Edge Average
        cb_edge_avg = self._create_checkbox("Use Edge Average")
        cb_edge_avg.setObjectName("bee_right_use_edge_avg")
        right.addWidget(cb_edge_avg)

        # Insp Image
        grp_img_white = QGroupBox("Insp Image")
        grp_img_white.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        img_r = QGridLayout(grp_img_white)
        img_r.setContentsMargins(8, 12, 8, 8)
        img_r.setHorizontalSpacing(10)
        img_r.setVerticalSpacing(6)

        bg_right = QButtonGroup(tab)
        bg_right.setObjectName("bee_right_insp_image")
        for i, txt in enumerate(["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]):
            rb = self._create_radio_button(txt)
            bg_right.addButton(rb)
            img_r.addWidget(rb, i // 4, i % 4)
        bg_right.buttons()[0].setChecked(True)
        right.addWidget(grp_img_white)

        cb_w_enable = self._create_checkbox("Enable")
        cb_w_enable.setObjectName("bee_right_enable")
        right.addWidget(cb_w_enable)
        
        cb_detect = self._create_checkbox("Detect to PASS")
        cb_detect.setObjectName("bee_right_detect_to_pass")
        right.addWidget(cb_detect)

        # Contrast
        c2 = QGridLayout()
        c2.setHorizontalSpacing(10)
        c2.setVerticalSpacing(8)
        c2.addWidget(self._create_label("Contrast (Top):"), 0, 0)
        sl_w_top = QSlider(Qt.Horizontal)
        sl_w_top.setRange(0, 255)
        sl_w_top.setObjectName("bee_right_contrast_top_slider")
        le_w_top = self._create_line_edit("35", "bee_right_contrast_top")
        self._sync_slider_lineedit(sl_w_top, le_w_top)
        c2.addWidget(sl_w_top, 0, 1)
        c2.addWidget(le_w_top, 0, 2)
        c2.addWidget(self._create_label("Levels"), 0, 3)

        c2.addWidget(self._create_label("Contrast (Bot):"), 1, 0)
        sl_w_bot = QSlider(Qt.Horizontal)
        sl_w_bot.setRange(0, 255)
        sl_w_bot.setObjectName("bee_right_contrast_bot_slider")
        le_w_bot = self._create_line_edit("35", "bee_right_contrast_bot")
        self._sync_slider_lineedit(sl_w_bot, le_w_bot)
        c2.addWidget(sl_w_bot, 1, 1)
        c2.addWidget(le_w_bot, 1, 2)
        c2.addWidget(self._create_label("Levels"), 1, 3)
        right.addLayout(c2)

        # Area
        g2 = QGridLayout()
        g2.setHorizontalSpacing(10)
        g2.setVerticalSpacing(8)
        g2.addWidget(self._create_label("Min Area:"), 0, 0)
        le_w_area = self._create_line_edit("20", "bee_right_min_area")
        g2.addWidget(le_w_area, 0, 1)
        g2.addWidget(self._create_label("Min Sqr Size:"), 0, 2)
        le_w_sqr = self._create_line_edit("3", "bee_right_min_square")
        g2.addWidget(le_w_sqr, 0, 3)
        right.addLayout(g2)

        # Ignore Reflection
        grp_ignore = QGroupBox("Ignore Reflection")
        grp_ignore.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gi = QGridLayout(grp_ignore)
        gi.setContentsMargins(8, 12, 8, 8)
        gi.setHorizontalSpacing(10)
        gi.setVerticalSpacing(6)
        cb_ignore = self._create_checkbox("Enable")
        cb_ignore.setObjectName("bee_right_ignore_reflection_enable")
        gi.addWidget(cb_ignore, 0, 0)
        gi.addWidget(self._create_label("Width %"), 0, 1)
        le_ignore_width = self._create_line_edit("30", "bee_right_ignore_reflection_width")
        gi.addWidget(le_ignore_width, 0, 2)
        right.addWidget(grp_ignore)

        # Ignore Vertical Line
        grp_vert = QGroupBox("Ignore Vertical Line")
        grp_vert.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gv = QGridLayout(grp_vert)
        gv.setContentsMargins(8, 12, 8, 8)
        gv.setHorizontalSpacing(10)
        gv.setVerticalSpacing(6)
        cb_vert = self._create_checkbox("Enable")
        cb_vert.setObjectName("bee_right_ignore_vertical_enable")
        gv.addWidget(cb_vert, 0, 0)
        gv.addWidget(self._create_label("Contrast"), 0, 1)
        le_vert_contrast = self._create_line_edit("5", "bee_right_ignore_vertical_contrast")
        gv.addWidget(le_vert_contrast, 0, 2)
        gv.addWidget(self._create_label("Height %"), 0, 3)
        le_vert_height = self._create_line_edit("30", "bee_right_ignore_vertical_height")
        gv.addWidget(le_vert_height, 0, 4)
        right.addWidget(grp_vert)

        # High Contrast
        grp_high = QGroupBox("High Contrast")
        grp_high.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gh = QGridLayout(grp_high)
        gh.setContentsMargins(8, 12, 8, 8)
        gh.setHorizontalSpacing(10)
        gh.setVerticalSpacing(6)
        cb_high = self._create_checkbox("Enable")
        cb_high.setObjectName("bee_right_high_contrast_enable")
        gh.addWidget(cb_high, 0, 0)
        gh.addWidget(self._create_label("Contrast:"), 1, 0)
        le_high_contrast = self._create_line_edit("62", "bee_right_high_contrast")
        gh.addWidget(le_high_contrast, 1, 1)
        gh.addWidget(self._create_label("Min Area:"), 1, 2)
        le_high_area = self._create_line_edit("25", "bee_right_high_min_area")
        gh.addWidget(le_high_area, 1, 3)
        gh.addWidget(self._create_label("Min Sqr Size:"), 1, 4)
        le_high_sqr = self._create_line_edit("4", "bee_right_high_min_square")
        gh.addWidget(le_high_sqr, 1, 5)
        right.addWidget(grp_high)

        # Offsets
        grp_offsets = QGroupBox("Insp Offset")
        grp_offsets.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        go2 = QGridLayout(grp_offsets)
        go2.setContentsMargins(8, 12, 8, 8)
        go2.setHorizontalSpacing(10)
        go2.setVerticalSpacing(6)
        for r, lbl in enumerate(["Top", "Bottom", "Left", "Right"]):
            go2.addWidget(self._create_label(lbl), r, 0)
            le_off2 = self._create_line_edit("5", f"bee_right_offset_{lbl.lower()}")
            go2.addWidget(le_off2, r, 1)
        right.addWidget(grp_offsets)

        grp_edge2 = QGroupBox("Edge Width")
        grp_edge2.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        ge2 = QGridLayout(grp_edge2)
        ge2.setContentsMargins(8, 12, 8, 8)
        ge2.setHorizontalSpacing(10)
        ge2.setVerticalSpacing(6)
        for r, lbl in enumerate(["Top", "Bottom", "Left", "Right"]):
            ge2.addWidget(self._create_label(lbl), r, 0)
            le_edge2 = self._create_line_edit("3", f"bee_right_edge_width_{lbl.lower()}")
            ge2.addWidget(le_edge2, r, 1)
        right.addWidget(grp_edge2)

        grp_corner2 = QGroupBox("Corner Mask Size")
        grp_corner2.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        gc2 = QGridLayout(grp_corner2)
        gc2.setContentsMargins(8, 12, 8, 8)
        gc2.setHorizontalSpacing(10)
        gc2.setVerticalSpacing(6)
        for r, lbl in enumerate(["Left", "Right", "Top", "Bottom"]):
            gc2.addWidget(self._create_label(lbl), r, 0)
            le_corner2 = self._create_line_edit("5", f"bee_right_corner_{lbl.lower()}")
            gc2.addWidget(le_corner2, r, 1)
        right.addWidget(grp_corner2)

        right.addStretch()

        # ==================================================
        root.addWidget(grp_black, 1)
        root.addWidget(grp_white, 1)

        return tab

    # color inspection tab
    def _color_inspection_tab(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        root = QHBoxLayout(tab)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(20)

        # =====================================
        # Body Color
        # =====================================
        grp_body = QGroupBox("Body Color")
        grp_body.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gb = QVBoxLayout(grp_body)
        gb.setContentsMargins(10, 15, 10, 10)
        gb.setSpacing(10)

        cb_body = self._create_checkbox("Enable")
        cb_body.setObjectName("ci_body_enable")
        gb.addWidget(cb_body)

        g1 = QGridLayout()
        g1.setHorizontalSpacing(10)
        g1.setVerticalSpacing(8)

        g1.addWidget(self._create_label("Contrast:"), 0, 0)
        le_body_contrast = self._create_line_edit("12", "ci_body_contrast")
        g1.addWidget(le_body_contrast, 0, 1)

        g1.addWidget(self._create_label("Width:"), 1, 0)
        le_body_width = self._create_line_edit("50", "ci_body_width")
        g1.addWidget(le_body_width, 1, 1)

        g1.addWidget(self._create_label("Height:"), 2, 0)
        le_body_height = self._create_line_edit("20", "ci_body_height")
        g1.addWidget(le_body_height, 2, 1)

        gb.addLayout(g1)
        gb.addStretch()

        # =====================================
        # Terminal Color
        # =====================================
        grp_term = QGroupBox("Terminal Color")
        grp_term.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        gt = QVBoxLayout(grp_term)
        gt.setContentsMargins(10, 15, 10, 10)
        gt.setSpacing(10)

        cb_term = self._create_checkbox("Enable")
        cb_term.setObjectName("ci_term_enable")
        gt.addWidget(cb_term)

        g2 = QGridLayout()
        g2.setHorizontalSpacing(10)
        g2.setVerticalSpacing(8)

        g2.addWidget(self._create_label("Contrast:"), 0, 0)
        le_term_contrast = self._create_line_edit("200", "ci_term_contrast")
        g2.addWidget(le_term_contrast, 0, 1)

        g2.addWidget(self._create_label("Left Width:"), 1, 0)
        le_term_left_width = self._create_line_edit("10", "ci_term_left_width")
        g2.addWidget(le_term_left_width, 1, 1)

        g2.addWidget(self._create_label("Right Width:"), 2, 0)
        le_term_right_width = self._create_line_edit("10", "ci_term_right_width")
        g2.addWidget(le_term_right_width, 2, 1)

        gt.addLayout(g2)

        # Offset group
        grp_offset = QGroupBox("Offset")
        grp_offset.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
            }
        """)
        go = QGridLayout(grp_offset)
        go.setContentsMargins(8, 12, 8, 8)
        go.setHorizontalSpacing(10)
        go.setVerticalSpacing(6)

        go.addWidget(self._create_label("Top:"), 0, 0)
        le_offset_top = self._create_line_edit("10", "ci_offset_top")
        go.addWidget(le_offset_top, 0, 1)
        
        go.addWidget(self._create_label("Left:"), 0, 2)
        le_offset_left = self._create_line_edit("10", "ci_offset_left")
        go.addWidget(le_offset_left, 0, 3)

        go.addWidget(self._create_label("Bottom:"), 1, 0)
        le_offset_bottom = self._create_line_edit("10", "ci_offset_bottom")
        go.addWidget(le_offset_bottom, 1, 1)
        
        go.addWidget(self._create_label("Right:"), 1, 2)
        le_offset_right = self._create_line_edit("10", "ci_offset_right")
        go.addWidget(le_offset_right, 1, 3)

        gt.addWidget(grp_offset)
        gt.addStretch()

        # =====================================
        root.addWidget(grp_body)
        root.addWidget(grp_term)
        root.addStretch()

        return tab

    # =================================================
    # Helper Methods for Styling
    # =================================================
    def _create_label(self, text):
        """Create a styled label"""
        label = QLabel(text)
        label.setStyleSheet("color: #333333;")
        return label

    def _create_line_edit(self, text, name=None):
        """Create a styled line edit"""
        e = QLineEdit(text)
        e.setFixedWidth(70)
        e.setAlignment(Qt.AlignCenter)
        e.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdcdc;
                border-radius: 3px;
                padding: 4px 6px;
                background-color: white;
                selection-background-color: #3498db;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        if name:
            e.setObjectName(name)
        return e

    def _create_readonly_line_edit(self, text, name=None):
        """Create a read-only styled line edit for displaying calculated values (um)."""
        e = QLineEdit(text)
        e.setFixedWidth(70)
        e.setAlignment(Qt.AlignCenter)
        e.setReadOnly(True)
        e.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdcdc;
                border-radius: 3px;
                padding: 4px 6px;
                background-color: #f5f5f5;
                color: #666666;
            }
        """)
        if name:
            e.setObjectName(name)
        return e

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
            }
            QCheckBox::indicator:hover {
                border: 1px solid #3498db;
            }
        """)
        return checkbox

    def _create_radio_button(self, text):
        """Create a styled radio button"""
        radio = QRadioButton(text)
        radio.setStyleSheet("""
            QRadioButton {
                color: #333333;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #cccccc;
                border-radius: 8px;
                background-color: white;
            }
            QRadioButton::indicator:checked {
                background-color: #3498db;
                border: 1px solid #2980b9;
            }
            QRadioButton::indicator:hover {
                border: 1px solid #3498db;
            }
        """)
        return radio

    def _make_scrollable(self, widget: QWidget) -> QWidget:
        scroll = QScrollArea(self)
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        return scroll

    def _sync_slider_lineedit(self, slider: QSlider, lineedit: QLineEdit):
        """Connect a slider and line edit so moving one updates the other."""
        slider.valueChanged.connect(lambda v: lineedit.setText(str(v)))
        lineedit.textChanged.connect(
            lambda text: slider.setValue(int(text) if text.isdigit() else slider.value())
        )

    # =================================================
    # JSON Save/Load Methods (Unchanged)
    # =================================================
    def save_to_json(self, filepath):
        import json
        data = {}
        for widget in self.findChildren(QLineEdit):
            if widget.objectName():
                data[widget.objectName()] = widget.text()
        for widget in self.findChildren(QCheckBox):
            if widget.objectName():
                data[widget.objectName()] = widget.isChecked()
        for widget in self.findChildren(QSlider):
            if widget.objectName():
                data[widget.objectName()] = widget.value()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_from_json(self, filepath):
        import json, os
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for widget in self.findChildren(QLineEdit):
            if widget.objectName() and widget.objectName() in data:
                widget.setText(str(data[widget.objectName()]))
        for widget in self.findChildren(QCheckBox):
            if widget.objectName() and widget.objectName() in data:
                widget.setChecked(bool(data[widget.objectName()]))
        for widget in self.findChildren(QSlider):
            if widget.objectName() and widget.objectName() in data:
                widget.setValue(int(data[widget.objectName()]))

    def save_tab(self, tab: QWidget, tab_key: str, filepath: str):
        import json, os

        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        tab_data = {}

        for w in tab.findChildren(QLineEdit):
            if w.objectName():
                tab_data[w.objectName()] = w.text()

        for w in tab.findChildren(QCheckBox):
            if w.objectName():
                tab_data[w.objectName()] = w.isChecked()

        for w in tab.findChildren(QSlider):
            if w.objectName():
                tab_data[w.objectName()] = w.value()

        for bg in tab.findChildren(QButtonGroup):
            if bg.objectName() and bg.checkedButton():
                tab_data[bg.objectName()] = bg.checkedButton().text()

        data[tab_key] = tab_data

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_tab(self, tab: QWidget, tab_key: str, filepath: str):
        import json, os

        if not os.path.exists(filepath):
            return

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if tab_key not in data:
            return

        tab_data = data[tab_key]

        for w in tab.findChildren(QLineEdit):
            if w.objectName() in tab_data:
                w.setText(str(tab_data[w.objectName()]))

        for w in tab.findChildren(QCheckBox):
            if w.objectName() in tab_data:
                w.setChecked(bool(tab_data[w.objectName()]))

        for w in tab.findChildren(QSlider):
            if w.objectName() in tab_data:
                w.setValue(int(tab_data[w.objectName()]))

        for bg in tab.findChildren(QButtonGroup):
            if bg.objectName() in tab_data:
                value = tab_data[bg.objectName()]
                for btn in bg.buttons():
                    if btn.text() == value:
                        btn.setChecked(True)
                        break