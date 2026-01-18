from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton,
    QGroupBox, QTabWidget, QWidget,QRadioButton,QSlider,QSizePolicy,QComboBox,QButtonGroup
)


TAB_UNIT = "UnitParameters"
TAB_MULTI = "MultiTerminal"
TAB_DIM = "DimensionMeasurement"
TAB_BODYS="BodySmearTab"
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
        self.resize(1100, 650)

        # Enable maximize
        self.setWindowFlags(
            self.windowFlags()
            | Qt.Window
            | Qt.WindowMinMaxButtonsHint
        )

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

        self.tabs = QTabWidget()
        main.addWidget(self.tabs)

        # ---------- Tabs ----------
        self.unit_tab = self._unit_parameters_tab()
        self.tabs.addTab(self.unit_tab, "Unit Parameters")

        self.multi_tab = self._multi_terminal_tab()
        self.tabs.addTab(self.multi_tab, "Multi Terminal")

        self.dimensionmeasurement_tab = self._dimension_measurement_parameters_tab()
        self.tabs.addTab(self.dimensionmeasurement_tab, "Dimension Measurement")

        # Body Smear
        self.body_smear_tab = self._body_smear_tab()
        self.tabs.addTab(self.body_smear_tab, "Body Missing Solder")

        # Body Stain
        self.body_stain_tab = self._body_stain_tab()
        self.tabs.addTab(self.body_stain_tab, "Body Stain")

        # Terminal Plating Defect
        self.terminal_platting_defect_tab = self._terminal_platting_defect_tab()
        self.tabs.addTab(self.terminal_platting_defect_tab, "Terminal Plating Defect")

        # Terminal Black Spot
        self.terminal_black_spot_tab = self._terminal_black_spot_tab()
        self.tabs.addTab(self.terminal_black_spot_tab, "Terminal Black Spot")

        # Body Crack
        self.body_crack_tab = self._body_crack_tab()
        self.tabs.addTab(self.body_crack_tab, "Body Crack")

        # Terminal Corner Defect
        self.terminal_corner_defect_tab = self._terminal_corner_deffect_tab()
        self.tabs.addTab(self.terminal_corner_defect_tab, "Terminal Corner Defect")

        # Body Edge Defect
        self.body_edge_effect_tab = self._body_edge_effect_tab()
        self.tabs.addTab(self.body_edge_effect_tab, "Body Edge Defect")

        # Color Inspection
        self.color_inspection_tab = self._color_inspection_tab()
        self.tabs.addTab(self.color_inspection_tab, "Color Inspection")

        self.tabs.setCurrentIndex(0)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()

        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_apply = QPushButton("Apply")

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

        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_apply)

        main.addLayout(btns)
        # unit parameter tab
    def _unit_parameters_tab(self) -> QWidget:
        tab = QWidget()
        root = QHBoxLayout(tab)
        root.setSpacing(20)

        # ================= LEFT MAIN GROUP =================
        grp = QGroupBox("Unit Parameters (um)")
        g = QGridLayout(grp)
        g.setHorizontalSpacing(12)
        g.setVerticalSpacing(8)

        # ---- Header ----
        g.addWidget(QLabel(""), 0, 1)
        g.addWidget(QLabel(""), 0, 2)
        g.addWidget(QLabel("um"), 0, 3)

        # ---- Body Length ----
        g.addWidget(QLabel("Body Length:"), 1, 0)
        g.addWidget(QLabel("Min:"), 1, 1)
        le_body_length_min = QLineEdit("60")
        le_body_length_min.setObjectName("body_length_min")
        le_body_length_min.setFixedWidth(60)
        g.addWidget(le_body_length_min, 1, 2)

        le_body_length_max = QLineEdit("414")
        le_body_length_max.setObjectName("body_length_max")
        le_body_length_max.setFixedWidth(60)
        g.addWidget(le_body_length_max, 1, 3)

        g.addWidget(QLabel("Max:"), 2, 1)
        le_body_length_min2 = QLineEdit("150")
        le_body_length_min2.setObjectName("body_length_min2")
        le_body_length_min2.setFixedWidth(60)
        g.addWidget(le_body_length_min2, 2, 2)

        le_body_length_max2 = QLineEdit("1035")
        le_body_length_max2.setObjectName("body_length_max2")
        le_body_length_max2.setFixedWidth(60)
        g.addWidget(le_body_length_max2, 2, 3)

        # ---- Body Width ----
        g.addWidget(QLabel("Body Width:"), 3, 0)
        g.addWidget(QLabel("Min:"), 3, 1)
        le_body_width_min = QLineEdit("30")
        le_body_width_min.setObjectName("body_width_min")
        le_body_width_min.setFixedWidth(60)
        g.addWidget(le_body_width_min, 3, 2)

        le_body_width_max = QLineEdit("207")
        le_body_width_max.setObjectName("body_width_max")
        le_body_width_max.setFixedWidth(60)
        g.addWidget(le_body_width_max, 3, 3)

        g.addWidget(QLabel("Max:"), 4, 1)
        le_body_width_min2 = QLineEdit("80")
        le_body_width_min2.setObjectName("body_width_min2")
        le_body_width_min2.setFixedWidth(60)
        g.addWidget(le_body_width_min2, 4, 2)

        le_body_width_max2 = QLineEdit("552")
        le_body_width_max2.setObjectName("body_width_max2")
        le_body_width_max2.setFixedWidth(60)
        g.addWidget(le_body_width_max2, 4, 3)

        # ---- Terminal Width ----
        g.addWidget(QLabel("Terminal Width:"), 5, 0)
        g.addWidget(QLabel("Dimension"), 5, 2, alignment=Qt.AlignCenter)
        g.addWidget(QLabel("Pkg Location"), 5, 4, alignment=Qt.AlignCenter)

        g.addWidget(QLabel("Min:"), 6, 1)
        le_term_dim_min = QLineEdit("30")
        le_term_dim_min.setObjectName("term_dim_min")
        le_term_dim_min.setFixedWidth(60)
        g.addWidget(le_term_dim_min, 6, 2)

        le_term_dim_max = QLineEdit("207")
        le_term_dim_max.setObjectName("term_dim_max")
        le_term_dim_max.setFixedWidth(60)
        g.addWidget(le_term_dim_max, 6, 3)

        le_term_pkg = QLineEdit("30")
        le_term_pkg.setObjectName("term_pkg_min")
        le_term_pkg.setFixedWidth(60)
        g.addWidget(le_term_pkg, 6, 4)

        g.addWidget(QLabel("Max:"), 7, 1)
        le_term_dim_min2 = QLineEdit("80")
        le_term_dim_min2.setObjectName("term_dim_min2")
        le_term_dim_min2.setFixedWidth(60)
        g.addWidget(le_term_dim_min2, 7, 2)

        le_term_dim_max2 = QLineEdit("552")
        le_term_dim_max2.setObjectName("term_dim_max2")
        le_term_dim_max2.setFixedWidth(60)
        g.addWidget(le_term_dim_max2, 7, 3)

        le_term_pkg2 = QLineEdit("150")
        le_term_pkg2.setObjectName("term_pkg_max")
        le_term_pkg2.setFixedWidth(60)
        g.addWidget(le_term_pkg2, 7, 4)

        # ---- Differences ----
        cb_term_length_diff = QCheckBox("Terminal Length Difference:")
        cb_term_length_diff.setObjectName("terminal_length_diff")
        g.addWidget(cb_term_length_diff, 10, 0)

        le_term_length_diff = QLineEdit("5")
        le_term_length_diff.setObjectName("terminal_length_diff_value")
        le_term_length_diff.setFixedWidth(60)
        g.addWidget(le_term_length_diff, 10, 2)

        cb_body_width_diff = QCheckBox("Body Width Difference:")
        cb_body_width_diff.setObjectName("body_width_diff")
        g.addWidget(cb_body_width_diff, 11, 0)

        le_body_width_diff = QLineEdit("5")
        le_body_width_diff.setObjectName("body_width_diff_value")
        le_body_width_diff.setFixedWidth(60)
        g.addWidget(le_body_width_diff, 11, 2)

        # ---- Body to Term Body Width ----
        grp_bw = QGroupBox("Body to Term Body Width")
        gbw = QGridLayout(grp_bw)
        cb_enable_body_width = QCheckBox("Enable Body Width")
        cb_enable_body_width.setObjectName("enable_body_width")
        gbw.addWidget(cb_enable_body_width, 0, 0, 1, 2)

        gbw.addWidget(QLabel("Min:"), 1, 0)
        le_bw_min = QLineEdit("20")
        le_bw_min.setObjectName("body_to_term_min")
        le_bw_min.setFixedWidth(60)
        gbw.addWidget(le_bw_min, 1, 1)

        gbw.addWidget(QLabel("Max:"), 2, 0)
        le_bw_max = QLineEdit("40")
        le_bw_max.setObjectName("body_to_term_max")
        le_bw_max.setFixedWidth(60)
        gbw.addWidget(le_bw_max, 2, 1)

        g.addWidget(grp_bw, 12, 0, 3, 4)
        root.addWidget(grp)

        # ================= RIGHT SIDE =================
        right = QVBoxLayout()
        right.setSpacing(10)

        cb_no_terminal = QCheckBox("No Terminal")
        cb_no_terminal.setObjectName("no_terminal")
        right.addWidget(cb_no_terminal)

        cb_pkg_as_body = QCheckBox("Pkg Location Use as Body Length")
        cb_pkg_as_body.setObjectName("pkg_as_body")
        right.addWidget(cb_pkg_as_body)

        row = QHBoxLayout()
        row.addWidget(QLabel("Terminal Length Contrast:"))
        le_term_contrast = QLineEdit("0")
        le_term_contrast.setObjectName("terminal_length_contrast")
        le_term_contrast.setFixedWidth(60)
        row.addWidget(le_term_contrast)
        right.addLayout(row)

        # ---- Terminal Length ----
        grp_term = QGroupBox("Terminal Length (um)")
        g2 = QGridLayout(grp_term)
        le_term_len_min = QLineEdit("10")
        le_term_len_min.setObjectName("terminal_length_min")
        le_term_len_min.setFixedWidth(60)
        g2.addWidget(QLabel("Min:"), 0, 0)
        g2.addWidget(le_term_len_min, 0, 1)

        le_term_len_max = QLineEdit("69")
        le_term_len_max.setObjectName("terminal_length_max")
        le_term_len_max.setFixedWidth(60)
        g2.addWidget(le_term_len_max, 0, 2)

        g2.addWidget(QLabel("Max:"), 1, 0)
        le_term_len_max2 = QLineEdit("70")
        le_term_len_max2.setObjectName("terminal_length_max2")
        le_term_len_max2.setFixedWidth(60)
        g2.addWidget(le_term_len_max2, 1, 1)

        le_term_len_max3 = QLineEdit("483")
        le_term_len_max3.setObjectName("terminal_length_max3")
        le_term_len_max3.setFixedWidth(60)
        g2.addWidget(le_term_len_max3, 1, 2)

        right.addWidget(grp_term)

        # ---- Term to Term Length ----
        grp_tt = QGroupBox("Term To Term Length (um)")
        g3 = QGridLayout(grp_tt)

        le_tt_min = QLineEdit("20")
        le_tt_min.setObjectName("term_to_term_min")
        le_tt_min.setFixedWidth(60)
        le_tt_max = QLineEdit("138")
        le_tt_max.setObjectName("term_to_term_max")
        le_tt_max.setFixedWidth(60)
        g3.addWidget(QLabel("Min:"), 0, 0)
        g3.addWidget(le_tt_min, 0, 1)
        g3.addWidget(le_tt_max, 0, 2)

        le_tt_max2 = QLineEdit("120")
        le_tt_max2.setObjectName("term_to_term_min2")
        le_tt_max2.setFixedWidth(60)
        le_tt_max3 = QLineEdit("828")
        le_tt_max3.setObjectName("term_to_term_max2")
        le_tt_max3.setFixedWidth(60)
        g3.addWidget(QLabel("Max:"), 1, 0)
        g3.addWidget(le_tt_max2, 1, 1)
        g3.addWidget(le_tt_max3, 1, 2)

        le_tt_diff_min = QLineEdit("10")
        le_tt_diff_min.setObjectName("term_to_term_diff_min")
        le_tt_diff_min.setFixedWidth(60)
        le_tt_diff_max = QLineEdit("69")
        le_tt_diff_max.setObjectName("term_to_term_diff_max")
        le_tt_diff_max.setFixedWidth(60)
        g3.addWidget(QLabel("Max - Min:"), 2, 0)
        g3.addWidget(le_tt_diff_min, 2, 1)
        g3.addWidget(le_tt_diff_max, 2, 2)

        right.addWidget(grp_tt)

        # ---- Term to Body Gap ----
        grp_gap = QGroupBox("Term to Body Gap")
        g4 = QGridLayout(grp_gap)
        cb_gap_enable = QCheckBox("Enable")
        cb_gap_enable.setObjectName("term_body_gap_enable")
        g4.addWidget(cb_gap_enable, 0, 0)

        g4.addWidget(QLabel("Edge Contrast:"), 1, 0)
        le_gap_edge = QLineEdit("0")
        le_gap_edge.setObjectName("term_body_gap_edge")
        le_gap_edge.setFixedWidth(60)
        g4.addWidget(le_gap_edge, 1, 1)

        g4.addWidget(QLabel("Min Gap:"), 2, 0)
        le_gap_min = QLineEdit("0")
        le_gap_min.setObjectName("term_body_gap_min")
        le_gap_min.setFixedWidth(60)
        g4.addWidget(le_gap_min, 2, 1)

        right.addWidget(grp_gap)

        right.addStretch()
        root.addLayout(right)

        return tab

    #Multi Terminal TAB
    def _multi_terminal_tab(self) -> QWidget:
        tab = QWidget()
        root = QGridLayout(tab)
        root.setHorizontalSpacing(15)
        root.setVerticalSpacing(10)
        # ==================================================
        # Top And Bottom Terminals
        # ==================================================
        grp_tb = QGroupBox("Top And Bottom Terminals")
        v_tb = QVBoxLayout(grp_tb)

        cb_mid = QCheckBox("Enable Mid Terminal")
        cb_mid.setObjectName("mt_enable_mid_terminal")

        cb_multi = QCheckBox("Enable Multi Terminal")
        cb_multi.setObjectName("mt_enable_multi_terminal")

        v_tb.addWidget(cb_mid)
        v_tb.addWidget(cb_multi)

        root.addWidget(grp_tb, 0, 0)


        # ==================================================
        # Inspection Image
        # ==================================================
        grp_img = QGroupBox("Insp Image")
        g_img = QGridLayout(grp_img)

        radios = ["Merge", "Red", "Green", "Blue", "RGB", "RB", "GB"]

        bg_img = QButtonGroup(tab)
        bg_img.setObjectName("mt_insp_image_mode")
        bg_img.setExclusive(True)

        for i, name in enumerate(radios):
            rb = QRadioButton(name)
            bg_img.addButton(rb)
            g_img.addWidget(rb, i // 4, i % 4)

        # default
        bg_img.buttons()[0].setChecked(True)

        root.addWidget(grp_img, 0, 1, 1, 2)
        # ==================================================
        # Number Of Terminals
        # ==================================================
        grp_num = QGroupBox("Number of Terminals")
        g_num = QGridLayout(grp_num)

        g_num.addWidget(QLabel("Top"), 0, 0)
        le_top = QLineEdit("0")
        le_top.setObjectName("mt_term_count_top")
        g_num.addWidget(le_top, 0, 1)

        g_num.addWidget(QLabel("Left"), 0, 2)
        le_left = QLineEdit("0")
        le_left.setObjectName("mt_term_count_left")
        g_num.addWidget(le_left, 0, 3)

        g_num.addWidget(QLabel("Bottom"), 1, 0)
        le_bottom = QLineEdit("0")
        le_bottom.setObjectName("mt_term_count_bottom")
        g_num.addWidget(le_bottom, 1, 1)

        g_num.addWidget(QLabel("Right"), 1, 2)
        le_right = QLineEdit("0")
        le_right.setObjectName("mt_term_count_right")
        g_num.addWidget(le_right, 1, 3)

        root.addWidget(grp_num, 1, 0)


        # ==================================================
        # Package Offset
        # ==================================================
        grp_offset = QGroupBox("Package Offset")
        g_off = QGridLayout(grp_offset)

        g_off.addWidget(QLabel("Left"), 0, 0)
        le_pkg_left = QLineEdit("0")
        le_pkg_left.setObjectName("mt_pkg_offset_left")
        g_off.addWidget(le_pkg_left, 0, 1)

        g_off.addWidget(QLabel("Right"), 1, 0)
        le_pkg_right = QLineEdit("0")
        le_pkg_right.setObjectName("mt_pkg_offset_right")
        g_off.addWidget(le_pkg_right, 1, 1)

        root.addWidget(grp_offset, 1, 1)


        # ==================================================
        # Terminal Gap
        # ==================================================
        grp_gap = QGroupBox("Terminal Gap")
        g_gap = QGridLayout(grp_gap)

        cb_gap = QCheckBox("Enable Terminal Gap")
        cb_gap.setObjectName("mt_term_gap_enable")
        g_gap.addWidget(cb_gap, 0, 0, 1, 2)

        g_gap.addWidget(QLabel("Min"), 1, 0)
        le_gap_min = QLineEdit("0")
        le_gap_min.setObjectName("mt_term_gap_min")
        g_gap.addWidget(le_gap_min, 1, 1)

        g_gap.addWidget(QLabel("Max"), 2, 0)
        le_gap_max = QLineEdit("0")
        le_gap_max.setObjectName("mt_term_gap_max")
        g_gap.addWidget(le_gap_max, 2, 1)

        root.addWidget(grp_gap, 1, 2)

        # ==================================================
        # Terminal Length
        # ==================================================
        grp_len = QGroupBox("Terminal Length")
        g_len = QGridLayout(grp_len)

        cb_len = QCheckBox("Enable Terminal Length")
        cb_len.setObjectName("mt_term_length_enable")
        g_len.addWidget(cb_len, 0, 0, 1, 4)

        g_len.addWidget(QLabel("Top/Bot"), 1, 1)
        g_len.addWidget(QLabel("Left/Rht"), 1, 3)

        g_len.addWidget(QLabel("Min"), 2, 0)
        le_len_tb_min = QLineEdit("0")
        le_len_tb_min.setObjectName("mt_term_length_tb_min")
        g_len.addWidget(le_len_tb_min, 2, 1)

        le_len_lr_min = QLineEdit("0")
        le_len_lr_min.setObjectName("mt_term_length_lr_min")
        g_len.addWidget(le_len_lr_min, 2, 3)

        g_len.addWidget(QLabel("Max"), 3, 0)
        le_len_tb_max = QLineEdit("0")
        le_len_tb_max.setObjectName("mt_term_length_tb_max")
        g_len.addWidget(le_len_tb_max, 3, 1)

        le_len_lr_max = QLineEdit("0")
        le_len_lr_max.setObjectName("mt_term_length_lr_max")
        g_len.addWidget(le_len_lr_max, 3, 3)

        root.addWidget(grp_len, 2, 0)

        # ==================================================
        # Terminal Width
        # ==================================================
        grp_w = QGroupBox("Terminal Width")
        g_w = QGridLayout(grp_w)

        cb_w = QCheckBox("Enable Terminal Width")
        cb_w.setObjectName("mt_term_width_enable")
        g_w.addWidget(cb_w, 0, 0, 1, 4)

        g_w.addWidget(QLabel("Top/Bot"), 1, 1)
        g_w.addWidget(QLabel("Left/Rht"), 1, 3)

        g_w.addWidget(QLabel("Min"), 2, 0)
        le_w_tb_min = QLineEdit("0")
        le_w_tb_min.setObjectName("mt_term_width_tb_min")
        g_w.addWidget(le_w_tb_min, 2, 1)

        le_w_lr_min = QLineEdit("0")
        le_w_lr_min.setObjectName("mt_term_width_lr_min")
        g_w.addWidget(le_w_lr_min, 2, 3)

        g_w.addWidget(QLabel("Max"), 3, 0)
        le_w_tb_max = QLineEdit("0")
        le_w_tb_max.setObjectName("mt_term_width_tb_max")
        g_w.addWidget(le_w_tb_max, 3, 1)

        le_w_lr_max = QLineEdit("0")
        le_w_lr_max.setObjectName("mt_term_width_lr_max")
        g_w.addWidget(le_w_lr_max, 3, 3)

        root.addWidget(grp_w, 2, 1)

        # ==================================================
        # Terminal Pogo
        # ==================================================
        grp_pogo = QGroupBox("Terminal Pogo")
        g_p = QGridLayout(grp_pogo)

        cb_pogo = QCheckBox("Enable Terminal Pogo")
        cb_pogo.setObjectName("mt_pogo_enable")
        g_p.addWidget(cb_pogo, 0, 0, 1, 3)

        g_p.addWidget(QLabel("Contrast"), 1, 0)
        sl_pogo = QSlider(Qt.Horizontal)
        sl_pogo.setRange(0, 255)
        sl_pogo.setObjectName("mt_pogo_contrast_slider")
        le_pogo = QLineEdit("5")
        le_pogo.setObjectName("mt_pogo_contrast")

        self._sync_slider_lineedit(sl_pogo, le_pogo)

        g_p.addWidget(sl_pogo, 1, 1)
        g_p.addWidget(le_pogo, 1, 2)

        g_p.addWidget(QLabel("Min Area"), 2, 0)
        le_pogo_area = QLineEdit("100")
        le_pogo_area.setObjectName("mt_pogo_min_area")
        g_p.addWidget(le_pogo_area, 2, 1)

        g_p.addWidget(QLabel("Min Square Size"), 3, 0)
        le_pogo_sq = QLineEdit("10")
        le_pogo_sq.setObjectName("mt_pogo_min_square")
        g_p.addWidget(le_pogo_sq, 3, 1)

        g_p.addWidget(QLabel("Corner Mask Left"), 4, 0)
        le_pogo_mask_l = QLineEdit("0")
        le_pogo_mask_l.setObjectName("mt_pogo_corner_mask_left")
        g_p.addWidget(le_pogo_mask_l, 4, 1)

        g_p.addWidget(QLabel("Corner Mask Right"), 5, 0)
        le_pogo_mask_r = QLineEdit("0")
        le_pogo_mask_r.setObjectName("mt_pogo_corner_mask_right")
        g_p.addWidget(le_pogo_mask_r, 5, 1)

        root.addWidget(grp_pogo, 2, 2)


        # ==================================================
        # Term to Term / Incomplete / Excess
        # ==================================================
# ==================================================
# Term To Term Outer
# ==================================================
        grp_tto = QGroupBox("Term To Term Outer")
        g_tto = QGridLayout(grp_tto)

        cb_tto = QCheckBox("Enable Term to Term Outer")
        cb_tto.setObjectName("mt_tto_enable")
        g_tto.addWidget(cb_tto, 0, 0, 1, 4)

        g_tto.addWidget(QLabel("Top/Bot"), 1, 1)
        g_tto.addWidget(QLabel("Left/Rht"), 1, 3)

        g_tto.addWidget(QLabel("Min"), 2, 0)
        le_tto_tb_min = QLineEdit("0")
        le_tto_tb_min.setObjectName("mt_tto_tb_min")
        g_tto.addWidget(le_tto_tb_min, 2, 1)

        le_tto_lr_min = QLineEdit("0")
        le_tto_lr_min.setObjectName("mt_tto_lr_min")
        g_tto.addWidget(le_tto_lr_min, 2, 3)

        g_tto.addWidget(QLabel("Max"), 3, 0)
        le_tto_tb_max = QLineEdit("0")
        le_tto_tb_max.setObjectName("mt_tto_tb_max")
        g_tto.addWidget(le_tto_tb_max, 3, 1)

        le_tto_lr_max = QLineEdit("0")
        le_tto_lr_max.setObjectName("mt_tto_lr_max")
        g_tto.addWidget(le_tto_lr_max, 3, 3)

        root.addWidget(grp_tto, 3, 0)


        # ==================================================
        # Term To Term Inner
        # ==================================================
        grp_tti = QGroupBox("Term To Term Inner")
        g_tti = QGridLayout(grp_tti)

        cb_tti = QCheckBox("Enable Term to Term Inner")
        cb_tti.setObjectName("mt_tti_enable")
        g_tti.addWidget(cb_tti, 0, 0, 1, 4)

        g_tti.addWidget(QLabel("Top/Bot"), 1, 1)
        g_tti.addWidget(QLabel("Left/Rht"), 1, 3)

        g_tti.addWidget(QLabel("Min"), 2, 0)
        le_tti_tb_min = QLineEdit("0")
        le_tti_tb_min.setObjectName("mt_tti_tb_min")
        g_tti.addWidget(le_tti_tb_min, 2, 1)

        le_tti_lr_min = QLineEdit("0")
        le_tti_lr_min.setObjectName("mt_tti_lr_min")
        g_tti.addWidget(le_tti_lr_min, 2, 3)

        root.addWidget(grp_tti, 3, 1)


        # ==================================================
        # Incomplete Termination Check
        # ==================================================
        grp_inc = QGroupBox("Incomplete Termination Check")
        g_i = QGridLayout(grp_inc)

        cb_inc = QCheckBox("Enable Incomplete Termination Check")
        cb_inc.setObjectName("mt_inc_enable")
        g_i.addWidget(cb_inc, 0, 0, 1, 2)

        g_i.addWidget(QLabel("Contrast"), 1, 0)
        le_inc_contrast = QLineEdit("0")
        le_inc_contrast.setObjectName("mt_inc_contrast")
        g_i.addWidget(le_inc_contrast, 1, 1)

        g_i.addWidget(QLabel("Min Area"), 2, 0)
        le_inc_area = QLineEdit("0")
        le_inc_area.setObjectName("mt_inc_min_area")
        g_i.addWidget(le_inc_area, 2, 1)

        g_i.addWidget(QLabel("Min Square Size"), 3, 0)
        le_inc_sq = QLineEdit("0")
        le_inc_sq.setObjectName("mt_inc_min_square")
        g_i.addWidget(le_inc_sq, 3, 1)

        root.addWidget(grp_inc, 4, 0)

        # ==================================================
        # Excess Terminal Check
        # ==================================================
        grp_exc = QGroupBox("Excess Terminal Check")
        g_e = QGridLayout(grp_exc)

        cb_exc = QCheckBox("Enable Excess Terminal Check")
        cb_exc.setObjectName("mt_exc_enable")
        g_e.addWidget(cb_exc, 0, 0)

        g_e.addWidget(QLabel("Min Square Size"), 1, 0)
        le_exc_sq = QLineEdit("0")
        le_exc_sq.setObjectName("mt_exc_min_square")
        g_e.addWidget(le_exc_sq, 1, 1)

        g_e.addWidget(QLabel("Min Area"), 2, 0)
        le_exc_area = QLineEdit("80")
        le_exc_area.setObjectName("mt_exc_min_area")
        g_e.addWidget(le_exc_area, 2, 1)

        root.addWidget(grp_exc, 4, 1)

        # ==================================================
        # Terminal Mis Alignment
        # ==================================================
        grp_align = QGroupBox("Terminal Mis Alignment")
        g_a = QGridLayout(grp_align)

        cb_align = QCheckBox("Enable Term Mis Alignment")
        cb_align.setObjectName("mt_align_enable")
        g_a.addWidget(cb_align, 0, 0, 1, 2)

        g_a.addWidget(QLabel("Max Angle"), 1, 0)
        le_align_angle = QLineEdit("0")
        le_align_angle.setObjectName("mt_align_max_angle")
        g_a.addWidget(le_align_angle, 1, 1)

        g_a.addWidget(QLabel("Degrees"), 1, 2)

        root.addWidget(grp_align, 4, 2)


        root.setRowStretch(5, 1)
        return tab
    # dimension measurement tab
    def _dimension_measurement_parameters_tab(self) -> QWidget:
        tab = QWidget()
        root = QVBoxLayout(tab)

        # =================================================
        # TOP SECTION
        # =================================================
        top = QHBoxLayout()

        # -------- Enable checkboxes --------
        grp_enable = QGroupBox("Dimension Measurement Parameters")
        gl = QVBoxLayout(grp_enable)

        cb_body_len = QCheckBox("Enable Body Length")
        cb_body_len.setObjectName("dm_enable_body_length")

        cb_term_len = QCheckBox("Enable Terminal Length")
        cb_term_len.setObjectName("dm_enable_terminal_length")

        cb_ttl = QCheckBox("Enable Terminal-to-Terminal Length")
        cb_ttl.setObjectName("dm_enable_ttl")

        cb_body_w = QCheckBox("Enable Body Width")
        cb_body_w.setObjectName("dm_enable_body_width")

        cb_term_w = QCheckBox("Enable Terminal Width")
        cb_term_w.setObjectName("dm_enable_terminal_width")

        for cb in [cb_body_len, cb_term_len, cb_ttl, cb_body_w, cb_term_w]:
            gl.addWidget(cb)

        grp_enable.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # -------- Right side --------
        right = QVBoxLayout()

        # =================================================
        # Insp Image
        # =================================================
        grp_img = QGroupBox("Insp Image")
        gi = QGridLayout(grp_img)

        radios = ["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]
        bg_img = QButtonGroup(tab)
        bg_img.setObjectName("dm_insp_image")

        for i, txt in enumerate(radios):
            rb = QRadioButton(txt)
            bg_img.addButton(rb)
            gi.addWidget(rb, i // 4, i % 4)

        bg_img.buttons()[0].setChecked(True)
        right.addWidget(grp_img)

        # =================================================
        # Terminal Contrast
        # =================================================
        tc = QHBoxLayout()
        tc.addWidget(QLabel("Terminal Contrast:"))

        le_tc = QLineEdit("10")
        le_tc.setObjectName("dm_terminal_contrast")

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
        px.addWidget(QLabel("Number of Pixels Used for Detecting Edge:"))

        le_px = QLineEdit("10")
        le_px.setObjectName("dm_edge_pixels")

        px.addWidget(le_px)
        px.addWidget(QLabel("Pixels"))
        right.addLayout(px)

        # =================================================
        # Terminal Length
        # =================================================
        grp_tlen = QGroupBox("Terminal Length")
        gt = QGridLayout(grp_tlen)

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
            gt.addWidget(QLabel(txt), r, 0)
            le = QLineEdit(val)
            le.setObjectName(name)
            gt.addWidget(le, r, 1)

        grp_tlen.setMinimumHeight(260)
        grp_tlen.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right.addWidget(grp_tlen)

        right.addStretch()

        top.addWidget(grp_enable, 1)
        top.addLayout(right, 3)
        root.addLayout(top)

        # =================================================
        # Body Width
        # =================================================
        grp_bw = QGroupBox("Body Width")
        gbw = QGridLayout(grp_bw)

        bw_fields = [
            ("Width Search Offset:", "dm_bw_search_offset", "30"),
            ("Left Offset:", "dm_bw_left_offset", "50"),
            ("Right Offset:", "dm_bw_right_offset", "50"),
        ]

        for r, (txt, name, val) in enumerate(bw_fields):
            gbw.addWidget(QLabel(txt), r, 0)
            le = QLineEdit(val)
            le.setObjectName(name)
            gbw.addWidget(le, r, 1)

        grp_bw.setMaximumWidth(300)
        root.addWidget(grp_bw)

        # =================================================
        # Terminal Width
        # =================================================
        grp_tw = QGroupBox("Terminal Width")
        gtw = QGridLayout(grp_tw)

        tw_fields = [
            ("Top Offset:", "dm_tw_top_offset", "1"),
            ("Bottom Offset:", "dm_tw_bottom_offset", "1"),
        ]

        for r, (txt, name, val) in enumerate(tw_fields):
            gtw.addWidget(QLabel(txt), r, 0)
            le = QLineEdit(val)
            le.setObjectName(name)
            gtw.addWidget(le, r, 1)

        grp_tw.setMaximumWidth(300)
        root.addWidget(grp_tw)

        # =================================================
        # Adjust Pkg Loc By Body Height
        # =================================================
        grp_adj = QGroupBox("Adjust Pkg Loc By Body Height")
        ga = QVBoxLayout(grp_adj)

        row = QHBoxLayout()
        cb_adj = QCheckBox("Enable")
        cb_adj.setObjectName("dm_adj_enable")

        cb_avg = QCheckBox("Use Edge Average")
        cb_avg.setObjectName("dm_adj_use_edge_avg")

        row.addWidget(cb_adj)
        row.addWidget(cb_avg)
        ga.addLayout(row)

        grp_img2 = QGroupBox("Insp Image")
        gi2 = QGridLayout(grp_img2)

        bg_img2 = QButtonGroup(tab)
        bg_img2.setObjectName("dm_adj_insp_image")

        for i, txt in enumerate(radios):
            rb = QRadioButton(txt)
            bg_img2.addButton(rb)
            gi2.addWidget(rb, i // 4, i % 4)

        bg_img2.buttons()[0].setChecked(True)
        ga.addWidget(grp_img2)

        bc = QHBoxLayout()
        bc.addWidget(QLabel("Body Contrast:"))

        le_bc = QLineEdit("15")
        le_bc.setObjectName("dm_body_contrast")

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
        root = QVBoxLayout(tab)

        grp_main = QGroupBox("Body Smear")
        main_layout = QHBoxLayout(grp_main)

        def smear_column(idx: int, title: str, show_red_dot=False):
            prefix = f"bs{idx}_"
            col = QVBoxLayout()

            # =================================================
            # Insp Image
            # =================================================
            grp_img = QGroupBox(f"Insp Image ({title})")
            gi = QGridLayout(grp_img)

            radios = ["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]
            bg = QButtonGroup(tab)
            bg.setObjectName(prefix + "insp_image")

            for i, txt in enumerate(radios):
                rb = QRadioButton(txt)
                bg.addButton(rb)
                gi.addWidget(rb, i // 4, i % 4)

            bg.buttons()[0].setChecked(True)
            col.addWidget(grp_img)

            # =================================================
            # Enable options
            # =================================================
            cb_enable = QCheckBox(f"Enable {title}")
            cb_enable.setObjectName(prefix + "enable")
            col.addWidget(cb_enable)

            cb_shot2 = QCheckBox("Enable Shot2")
            cb_shot2.setObjectName(prefix + "shot2")
            col.addWidget(cb_shot2)

            cb_avg = QCheckBox("Use Average Contrast")
            cb_avg.setObjectName(prefix + "use_avg_contrast")
            col.addWidget(cb_avg)

            # =================================================
            # Contrast
            # =================================================
            c_row = QHBoxLayout()
            c_row.addWidget(QLabel("Contrast:"))

            sl = QSlider(Qt.Horizontal)
            sl.setRange(0, 255)
            sl.setObjectName(prefix + "contrast_slider")

            le = QLineEdit("30")
            le.setObjectName(prefix + "contrast")

            self._sync_slider_lineedit(sl, le)

            c_row.addWidget(sl)
            c_row.addWidget(le)
            col.addLayout(c_row)

            # =================================================
            # Params
            # =================================================
            grid = QGridLayout()

            params = [
                ("Min. Area:", "min_area", "100"),
                ("Min. Sqr Size:", "min_square", "10"),
                ("Area Min %:", "area_min_pct", "5"),
                ("Size Min %:", "size_min_pct", "5"),
            ]

            for r, (lbl, name, val) in enumerate(params):
                grid.addWidget(QLabel(lbl), r, 0)
                le = QLineEdit(val)
                le.setObjectName(prefix + name)
                grid.addWidget(le, r, 1)

            col.addLayout(grid)

            cb_or = QCheckBox("Apply (OR)")
            cb_or.setObjectName(prefix + "apply_or")
            col.addWidget(cb_or)

            # =================================================
            # Offset
            # =================================================
            grp_off = QGroupBox(f"{title} Offset")
            go = QGridLayout(grp_off)

            offsets = [
                ("Top:", "offset_top", "5"),
                ("Bottom:", "offset_bottom", "5"),
                ("Left:", "offset_left", "5"),
                ("Right:", "offset_right", "5"),
            ]

            for r, (lbl, name, val) in enumerate(offsets):
                go.addWidget(QLabel(lbl), r, 0)
                le = QLineEdit(val)
                le.setObjectName(prefix + name)
                go.addWidget(le, r, 1)

            col.addWidget(grp_off)

            # =================================================
            # Red dot
            # =================================================
            if show_red_dot:
                rd = QHBoxLayout()
                rd.addWidget(QLabel("Red Dot Min. Count"))

                le_rd = QLineEdit("0")
                le_rd.setObjectName(prefix + "red_dot_min")
                rd.addWidget(le_rd)

                col.addLayout(rd)

            return col

        main_layout.addLayout(smear_column(1, "Body Smear 1"))
        main_layout.addLayout(smear_column(2, "Body Smear 2"))
        main_layout.addLayout(smear_column(3, "Body Smear 3", show_red_dot=True))

        root.addWidget(grp_main)

        # =================================================
        # Reverse Chip Check
        # =================================================
        grp_rev = QGroupBox("Reverse Chip Check")
        gr = QVBoxLayout(grp_rev)

        cb_rev = QCheckBox("Enable Reverse Chip Check")
        cb_rev.setObjectName("bs_reverse_enable")
        gr.addWidget(cb_rev)

        grp_white = QGroupBox("White")
        gw = QHBoxLayout(grp_white)

        cb_white = QCheckBox("Enable")
        cb_white.setObjectName("bs_white_enable")

        le_white = QLineEdit("20")
        le_white.setObjectName("bs_white_contrast")

        gw.addWidget(cb_white)
        gw.addWidget(QLabel("Contrast (Difference):"))
        gw.addWidget(le_white)

        gr.addWidget(grp_white)
        root.addWidget(grp_rev)

        root.addStretch()
        return tab

    # Body stain tab
    def _body_stain_tab(self) -> QWidget:
        tab = QWidget()
        root = QVBoxLayout(tab)

        grp_main = QGroupBox("Body Stain")
        main = QVBoxLayout(grp_main)

        # =================================================
        # Insp Image + Filter
        # =================================================
        top_row = QHBoxLayout()

        grp_img = QGroupBox("Insp Image")
        gi = QGridLayout(grp_img)

        radios = ["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]

        bg_img = QButtonGroup(tab)
        bg_img.setObjectName("bs_insp_image")

        for i, txt in enumerate(radios):
            rb = QRadioButton(txt)
            bg_img.addButton(rb)
            gi.addWidget(rb, i // 4, i % 4)


        grp_filter = QGroupBox("")
        gf = QGridLayout(grp_filter)

        cb_low = QCheckBox("Enable Filter Low Contrast")
        cb_low.setObjectName("bs_filter_low_enable")
        gf.addWidget(cb_low, 0, 0, 1, 2)

        gf.addWidget(QLabel("Red:"), 1, 0)
        le_r = QLineEdit("60")
        le_r.setObjectName("bs_filter_red")
        gf.addWidget(le_r, 1, 1)

        gf.addWidget(QLabel("Green:"), 2, 0)
        le_g = QLineEdit("20")
        le_g.setObjectName("bs_filter_green")
        gf.addWidget(le_g, 2, 1)

        gf.addWidget(QLabel("Blue:"), 3, 0)
        le_b = QLineEdit("70")
        le_b.setObjectName("bs_filter_blue")
        gf.addWidget(le_b, 3, 1)


        main.addLayout(top_row)

        # =================================================
        # Body Stain 1 & 2
        # =================================================
        stain_row = QHBoxLayout()

        def stain_block(title: str, prefix: str):
            grp = QGroupBox("")
            v = QVBoxLayout(grp)

            cb_enable = QCheckBox(title)
            cb_enable.setObjectName(f"{prefix}_enable")
            v.addWidget(cb_enable)

            c_row = QHBoxLayout()
            c_row.addWidget(QLabel("Contrast:"))

            sl = QSlider(Qt.Horizontal)
            sl.setRange(0, 255)
            sl.setObjectName(f"{prefix}_contrast_slider")
            c_row.addWidget(sl)

            le_con = QLineEdit("40")
            le_con.setObjectName(f"{prefix}_contrast")
            c_row.addWidget(le_con)

            self._sync_slider_lineedit(sl, le_con)

            v.addLayout(c_row)

            grid = QGridLayout()
            grid.addWidget(QLabel("Min Area:"), 0, 0)
            le_area = QLineEdit("100")
            le_area.setObjectName(f"{prefix}_min_area")
            grid.addWidget(le_area, 0, 1)

            grid.addWidget(QLabel("Min Square Size:"), 1, 0)
            le_sq = QLineEdit("10")
            le_sq.setObjectName(f"{prefix}_min_square")
            grid.addWidget(le_sq, 1, 1)

            v.addLayout(grid)

            cb_or = QCheckBox("Apply (OR)")
            cb_or.setObjectName(f"{prefix}_apply_or")
            v.addWidget(cb_or)

            grp_off = QGroupBox("Offset")
            go = QGridLayout(grp_off)

            le_top = QLineEdit("5")
            le_top.setObjectName(f"{prefix}_off_top")
            go.addWidget(QLabel("Top:"), 0, 0)
            go.addWidget(le_top, 0, 1)

            le_bottom = QLineEdit("5")
            le_bottom.setObjectName(f"{prefix}_off_bottom")
            go.addWidget(QLabel("Bottom:"), 1, 0)
            go.addWidget(le_bottom, 1, 1)

            le_left = QLineEdit("5")
            le_left.setObjectName(f"{prefix}_off_left")
            go.addWidget(QLabel("Left:"), 2, 0)
            go.addWidget(le_left, 2, 1)

            le_right = QLineEdit("5")
            le_right.setObjectName(f"{prefix}_off_right")
            go.addWidget(QLabel("Right:"), 3, 0)
            go.addWidget(le_right, 3, 1)

            v.addWidget(grp_off)

            return grp



        stain_row.addWidget(stain_block("Enable Body Stain 1", "bs1"))

        grp2 = stain_block("Enable Body Stain 2", "bs2")

        v2 = grp2.layout()
        rd = QHBoxLayout()
        rd.addWidget(QLabel("Red Dot Min. Count"))
        le_rd = QLineEdit("0")
        le_rd.setObjectName("bs2_red_dot_min")
        rd.addWidget(le_rd)

        v2.addLayout(rd)

        stain_row.addWidget(grp2)
        main.addLayout(stain_row)

        # =================================================
        # Body Stand Stain
        # =================================================
        bottom = QHBoxLayout()

        grp_stand = QGroupBox("Body Stand Stain")
        gs = QGridLayout(grp_stand)
        cb_stand = QCheckBox("Enable Body Stand Stain")
        cb_stand.setObjectName("bs_stand_enable")
        gs.addWidget(cb_stand, 0, 0, 1, 2)

        gs.addWidget(QLabel("Edge Contrast:"), 1, 0)
        le_edge = QLineEdit("125")
        le_edge.setObjectName("bs_stand_edge_contrast")
        gs.addWidget(le_edge, 1, 1)

        gs.addWidget(QLabel("Difference:"), 2, 0)
        le_diff = QLineEdit("30")
        le_diff.setObjectName("bs_stand_difference")
        gs.addWidget(le_diff, 2, 1)

        bottom.addWidget(grp_stand)

        grp_off2 = QGroupBox("Offset")
        go2 = QGridLayout(grp_off2)
        go2.addWidget(QLabel("Top:"), 0, 0)
        le_top = QLineEdit("5")
        le_top.setObjectName("bs_stand_off_top")
        go2.addWidget(le_top, 0, 1)

        go2.addWidget(QLabel("Bottom:"), 1, 0)
        le_bottom = QLineEdit("5")
        le_bottom.setObjectName("bs_stand_off_bottom")
        go2.addWidget(le_bottom, 1, 1)

        go2.addWidget(QLabel("Left:"), 0, 2)
        le_left = QLineEdit("5")
        le_left.setObjectName("bs_stand_off_left")
        go2.addWidget(le_left, 0, 3)

        go2.addWidget(QLabel("Right:"), 1, 2)
        le_right = QLineEdit("5")
        le_right.setObjectName("bs_stand_off_right")
        go2.addWidget(le_right, 1, 3)

        bottom.addWidget(grp_off2)

        main.addLayout(bottom)

        root.addWidget(grp_main)
        root.addStretch()

        return tab

    # Terminal plating deffect tab
    def _terminal_platting_defect_tab(self) -> QWidget:
        tab = QWidget()
        root = QVBoxLayout(tab)

        grp_main = QGroupBox("Terminal Defect")
        main = QVBoxLayout(grp_main)

        # =================================================
        # Top Row
        # =================================================
        top = QHBoxLayout()

        grp_img = QGroupBox("Insp Image")
        gi = QGridLayout(grp_img)
        radios = ["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]
        bg_img = QButtonGroup(tab)
        bg_img.setObjectName("tpd_insp_image")
        for i, txt in enumerate(radios):
            rb = QRadioButton(txt)
            bg_img.addButton(rb)
            gi.addWidget(rb, i // 4, i % 4)
        bg_img.buttons()[0].setChecked(True)
        top.addWidget(grp_img)

        opts = QVBoxLayout()
        cb_bold = QCheckBox("Enable Terminal Bold")
        cb_bold.setObjectName("tpd_enable_bold")
        opts.addWidget(cb_bold)
        cb_device = QCheckBox("Use Device Contrast")
        cb_device.setObjectName("tpd_use_device_contrast")
        opts.addWidget(cb_device)
        top.addLayout(opts)

        main.addLayout(top)

        # =================================================
        # Two Columns
        # =================================================
        cols = QHBoxLayout()

        def defect_column(title_left=True):
            prefix = "tpd_left_" if title_left else "tpd_right_"
            v = QVBoxLayout()

            cb_inc = QCheckBox(
                "Enable Incomplete Termination 1" if title_left
                else "Enable Incomplete Termination 2"
            )
            cb_inc.setObjectName(prefix + "incomplete_enable")
            v.addWidget(cb_inc)
            
            cb_shot2 = QCheckBox("Enable Shot2")
            cb_shot2.setObjectName(prefix + "shot2_enable")
            v.addWidget(cb_shot2)

            c_row = QHBoxLayout()
            c_row.addWidget(QLabel("Contrast:"))
            sl = QSlider(Qt.Horizontal)
            sl.setRange(0, 255)
            sl.setObjectName(prefix + "contrast_slider")
            le_con = QLineEdit("10")
            le_con.setObjectName(prefix + "contrast")
            self._sync_slider_lineedit(sl, le_con)
            c_row.addWidget(sl)
            c_row.addWidget(le_con)
            v.addLayout(c_row)

            g = QGridLayout()
            g.addWidget(QLabel("Min Area:"), 0, 0)
            le_area = QLineEdit("100")
            le_area.setObjectName(prefix + "min_area")
            g.addWidget(le_area, 0, 1)
            
            g.addWidget(QLabel("Min Square Size:"), 1, 0)
            le_sq = QLineEdit("10")
            le_sq.setObjectName(prefix + "min_square")
            g.addWidget(le_sq, 1, 1)
            
            g.addWidget(QLabel("Inspection Width:"), 2, 0)
            le_width = QLineEdit("5")
            le_width.setObjectName(prefix + "inspection_width")
            g.addWidget(le_width, 2, 1)
            
            g.addWidget(QLabel("Corner Ellipse Mask Size:"), 3, 0)
            le_corner = QLineEdit("0")
            le_corner.setObjectName(prefix + "corner_ellipse_mask")
            g.addWidget(le_corner, 3, 1)
            v.addLayout(g)

            cb_or = QCheckBox("Apply (OR)")
            cb_or.setObjectName(prefix + "apply_or")
            v.addWidget(cb_or)

            # Offset Group
            grp_off = QGroupBox(
                "Left Terminal Offset" if title_left else "Right Terminal Offset"
            )
            go = QGridLayout(grp_off)

            go.addWidget(QLabel("Top:"), 0, 0)
            le_top = QLineEdit("5")
            le_top.setObjectName(prefix + "offset_top")
            go.addWidget(le_top, 0, 1)
            
            go.addWidget(QLabel("Bottom:"), 1, 0)
            le_bottom = QLineEdit("5")
            le_bottom.setObjectName(prefix + "offset_bottom")
            go.addWidget(le_bottom, 1, 1)
            
            go.addWidget(QLabel("Left:"), 2, 0)
            le_left = QLineEdit("5")
            le_left.setObjectName(prefix + "offset_left")
            go.addWidget(le_left, 2, 1)
            
            go.addWidget(QLabel("Right:"), 2, 2)
            le_right = QLineEdit("5")
            le_right.setObjectName(prefix + "offset_right")
            go.addWidget(le_right, 2, 3)

            go.addWidget(QLabel("Corner Offset X:"), 3, 0)
            le_corner_x = QLineEdit("2")
            le_corner_x.setObjectName(prefix + "corner_offset_x")
            go.addWidget(le_corner_x, 3, 1)
            
            go.addWidget(QLabel("Corner Offset Y:"), 4, 0)
            le_corner_y = QLineEdit("2")
            le_corner_y.setObjectName(prefix + "corner_offset_y")
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
        root = QVBoxLayout(tab)

        grp_main = QGroupBox("Terminal Pogo")
        main = QVBoxLayout(grp_main)

        # =================================================
        # Top row: Insp Image + Oxidation
        # =================================================
        top = QHBoxLayout()

        grp_img = QGroupBox("Insp Image")
        gi = QGridLayout(grp_img)
        radios = ["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]
        bg_img = QButtonGroup(tab)
        bg_img.setObjectName("tbs_insp_image")
        for i, txt in enumerate(radios):
            rb = QRadioButton(txt)
            bg_img.addButton(rb)
            gi.addWidget(rb, i // 4, i % 4)
        bg_img.buttons()[0].setChecked(True)
        top.addWidget(grp_img)

        grp_oxid = QGroupBox("Oxidation")
        gox = QGridLayout(grp_oxid)
        cb_oxid = QCheckBox("Enable Oxidation")
        cb_oxid.setObjectName("tbs_oxidation_enable")
        gox.addWidget(cb_oxid, 0, 0, 1, 2)
        
        gox.addWidget(QLabel("Contrast Difference:"), 1, 0)
        le_oxid_contrast = QLineEdit("20")
        le_oxid_contrast.setObjectName("tbs_oxidation_contrast")
        gox.addWidget(le_oxid_contrast, 1, 1)
        
        gox.addWidget(QLabel("Top:"), 2, 0)
        le_oxid_top = QLineEdit("5")
        le_oxid_top.setObjectName("tbs_oxidation_top")
        gox.addWidget(le_oxid_top, 2, 1)
        
        gox.addWidget(QLabel("Bottom:"), 3, 0)
        le_oxid_bottom = QLineEdit("5")
        le_oxid_bottom.setObjectName("tbs_oxidation_bottom")
        gox.addWidget(le_oxid_bottom, 3, 1)

        top.addWidget(grp_oxid)
        main.addLayout(top)

        # =================================================
        # Middle controls
        # =================================================
        mid = QHBoxLayout()

        left = QVBoxLayout()
        cb_pogo = QCheckBox("Enable Terminal Pogo")
        cb_pogo.setObjectName("tbs_pogo_enable")
        left.addWidget(cb_pogo)
        
        cb_shot2 = QCheckBox("Enable Shot2")
        cb_shot2.setObjectName("tbs_shot2_enable")
        left.addWidget(cb_shot2)

        c_row = QHBoxLayout()
        c_row.addWidget(QLabel("Contrast:"))
        sl_contrast = QSlider(Qt.Horizontal)
        sl_contrast.setRange(0, 255)
        sl_contrast.setObjectName("tbs_contrast_slider")
        le_contrast = QLineEdit("5")
        le_contrast.setObjectName("tbs_contrast")
        self._sync_slider_lineedit(sl_contrast, le_contrast)
        c_row.addWidget(sl_contrast)
        c_row.addWidget(le_contrast)
        left.addLayout(c_row)

        grid = QGridLayout()
        grid.addWidget(QLabel("Min Area:"), 0, 0)
        le_area = QLineEdit("100")
        le_area.setObjectName("tbs_min_area")
        grid.addWidget(le_area, 0, 1)
        
        grid.addWidget(QLabel("Min Square Size:"), 1, 0)
        le_sq = QLineEdit("10")
        le_sq.setObjectName("tbs_min_square")
        grid.addWidget(le_sq, 1, 1)
        
        grid.addWidget(QLabel("Inspection Width:"), 2, 0)
        le_width = QLineEdit("0")
        le_width.setObjectName("tbs_inspection_width")
        grid.addWidget(le_width, 2, 1)
        left.addLayout(grid)

        mid.addLayout(left)
        main.addLayout(mid)

        # =================================================
        # Bottom: Left / Right Terminal Offset
        # =================================================
        offsets = QHBoxLayout()

        def offset_group(title, prefix):
            grp = QGroupBox(title)
            g = QGridLayout(grp)
            g.addWidget(QLabel("Top:"), 0, 0)
            le_top = QLineEdit("5")
            le_top.setObjectName(prefix + "offset_top")
            g.addWidget(le_top, 0, 1)
            
            g.addWidget(QLabel("Left:"), 0, 2)
            le_left = QLineEdit("5")
            le_left.setObjectName(prefix + "offset_left")
            g.addWidget(le_left, 0, 3)

            g.addWidget(QLabel("Bottom:"), 1, 0)
            le_bottom = QLineEdit("5")
            le_bottom.setObjectName(prefix + "offset_bottom")
            g.addWidget(le_bottom, 1, 1)
            
            g.addWidget(QLabel("Right:"), 1, 2)
            le_right = QLineEdit("5")
            le_right.setObjectName(prefix + "offset_right")
            g.addWidget(le_right, 1, 3)

            g.addWidget(QLabel("Corner Offset X:"), 2, 0)
            le_corner_x = QLineEdit("2")
            le_corner_x.setObjectName(prefix + "corner_offset_x")
            g.addWidget(le_corner_x, 2, 1)
            
            g.addWidget(QLabel("Corner Offset Y:"), 3, 0)
            le_corner_y = QLineEdit("2")
            le_corner_y.setObjectName(prefix + "corner_offset_y")
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
        root = QVBoxLayout(tab)

        top = QHBoxLayout()

        # =================================================
        # LEFT: Body Crack (White Defect)
        # =================================================
        grp_left = QGroupBox("Body Crack (White Defect)")
        l = QVBoxLayout(grp_left)

        img = QGroupBox("Insp Image")
        gi = QGridLayout(img)
        bg_left = QButtonGroup(tab)
        bg_left.setObjectName("bc_left_insp_image")
        for i, t in enumerate(["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]):
            rb = QRadioButton(t)
            bg_left.addButton(rb)
            gi.addWidget(rb, i // 4, i % 4)
        bg_left.buttons()[0].setChecked(True)
        l.addWidget(img)

        row = QHBoxLayout()
        row.addWidget(QLabel("Parameter Set"))
        combo = QComboBox()
        combo.addItems(["High Contrast"])
        combo.setObjectName("bc_left_param_set")
        row.addWidget(combo)
        row.addStretch()
        l.addLayout(row)

        cb_enable = QCheckBox("Enable")
        cb_enable.setObjectName("bc_left_enable")
        l.addWidget(cb_enable)
        
        cb_reject = QCheckBox("Low And High Contrast Rejection")
        cb_reject.setObjectName("bc_left_reject_enable")
        l.addWidget(cb_reject)

        c = QHBoxLayout()
        c.addWidget(QLabel("Contrast"))
        sl = QSlider(Qt.Horizontal)
        sl.setRange(0, 255)
        sl.setObjectName("bc_left_contrast_slider")
        le_con = QLineEdit("10")
        le_con.setObjectName("bc_left_contrast")
        self._sync_slider_lineedit(sl, le_con)
        c.addWidget(sl)
        c.addWidget(le_con)
        l.addLayout(c)

        grid = QGridLayout()
        grid.addWidget(QLabel("Min. Length"), 0, 0)
        le_len = QLineEdit("20")
        le_len.setObjectName("bc_left_min_length")
        grid.addWidget(le_len, 0, 1)
        
        grid.addWidget(QLabel("Min. Elongation"), 1, 0)
        le_elong = QLineEdit("5")
        le_elong.setObjectName("bc_left_min_elongation")
        grid.addWidget(le_elong, 1, 1)
        
        grid.addWidget(QLabel("Broken Connection"), 2, 0)
        le_broken = QLineEdit("0")
        le_broken.setObjectName("bc_left_broken_connection")
        grid.addWidget(le_broken, 2, 1)
        l.addLayout(grid)

        top.addWidget(grp_left)

        # =================================================
        # RIGHT: Hairline + Stain Crack
        # =================================================
        right = QVBoxLayout()

        # Hairline Crack
        grp_hair = QGroupBox("Body HairLine Crack")
        h = QVBoxLayout(grp_hair)

        img2 = QGroupBox("Insp Image")
        gi2 = QGridLayout(img2)
        bg_hair = QButtonGroup(tab)
        bg_hair.setObjectName("bc_hair_insp_image")
        for i, t in enumerate(["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]):
            rb = QRadioButton(t)
            bg_hair.addButton(rb)
            gi2.addWidget(rb, i // 4, i % 4)
        bg_hair.buttons()[0].setChecked(True)
        h.addWidget(img2)

        cb_black = QCheckBox("Enable Black Defect")
        cb_black.setObjectName("bc_hair_black_enable")
        h.addWidget(cb_black)
        
        cb_white = QCheckBox("Enable White Defect")
        cb_white.setObjectName("bc_hair_white_enable")
        h.addWidget(cb_white)

        ch = QHBoxLayout()
        ch.addWidget(QLabel("Contrast"))
        sl_hair = QSlider(Qt.Horizontal)
        sl_hair.setRange(0, 255)
        sl_hair.setObjectName("bc_hair_contrast_slider")
        le_hair_con = QLineEdit("6")
        le_hair_con.setObjectName("bc_hair_contrast")
        self._sync_slider_lineedit(sl_hair, le_hair_con)
        ch.addWidget(sl_hair)
        ch.addWidget(le_hair_con)
        h.addLayout(ch)

        gh = QGridLayout()
        gh.addWidget(QLabel("Min. Length"), 0, 0)
        le_hair_len = QLineEdit("25")
        le_hair_len.setObjectName("bc_hair_min_length")
        gh.addWidget(le_hair_len, 0, 1)
        
        gh.addWidget(QLabel("Noise Filtering Size"), 1, 0)
        le_noise = QLineEdit("5")
        le_noise.setObjectName("bc_hair_noise_filtering")
        gh.addWidget(le_noise, 1, 1)
        h.addLayout(gh)

        right.addWidget(grp_hair)

        # Body Stain Crack
        grp_stain = QGroupBox("Body Stain Crack")
        s = QVBoxLayout(grp_stain)

        cb_stain = QCheckBox("Enable")
        cb_stain.setObjectName("bc_stain_enable")
        s.addWidget(cb_stain)

        cs = QHBoxLayout()
        cs.addWidget(QLabel("Contrast"))
        sl_stain = QSlider(Qt.Horizontal)
        sl_stain.setRange(0, 255)
        sl_stain.setObjectName("bc_stain_contrast_slider")
        le_stain_con = QLineEdit("150")
        le_stain_con.setObjectName("bc_stain_contrast")
        self._sync_slider_lineedit(sl_stain, le_stain_con)
        cs.addWidget(sl_stain)
        cs.addWidget(le_stain_con)
        s.addLayout(cs)

        gs = QGridLayout()
        gs.addWidget(QLabel("Min. Length"), 0, 0)
        le_stain_len = QLineEdit("10")
        le_stain_len.setObjectName("bc_stain_min_length")
        gs.addWidget(le_stain_len, 0, 1)
        
        gs.addWidget(QLabel("Min. Area"), 1, 0)
        le_stain_area = QLineEdit("20")
        le_stain_area.setObjectName("bc_stain_min_area")
        gs.addWidget(le_stain_area, 1, 1)
        
        gs.addWidget(QLabel("Corner Contrast Diff"), 2, 0)
        le_stain_corner = QLineEdit("12")
        le_stain_corner.setObjectName("bc_stain_corner_contrast")
        gs.addWidget(le_stain_corner, 2, 1)
        s.addLayout(gs)

        right.addWidget(grp_stain)

        top.addLayout(right)
        root.addLayout(top)

        # =================================================
        # OFFSET
        # =================================================
        grp_off = QGroupBox("Offset")
        go = QGridLayout(grp_off)
        go.addWidget(QLabel("Top"), 0, 0)
        le_off_top = QLineEdit("5")
        le_off_top.setObjectName("bc_offset_top")
        go.addWidget(le_off_top, 0, 1)
        
        go.addWidget(QLabel("Left"), 0, 2)
        le_off_left = QLineEdit("5")
        le_off_left.setObjectName("bc_offset_left")
        go.addWidget(le_off_left, 0, 3)
        
        go.addWidget(QLabel("Bottom"), 1, 0)
        le_off_bottom = QLineEdit("5")
        le_off_bottom.setObjectName("bc_offset_bottom")
        go.addWidget(le_off_bottom, 1, 1)
        
        go.addWidget(QLabel("Right"), 1, 2)
        le_off_right = QLineEdit("5")
        le_off_right.setObjectName("bc_offset_right")
        go.addWidget(le_off_right, 1, 3)

        root.addWidget(grp_off)
        root.addStretch()

        return tab
    # Terminal Corner Deffect
    def _terminal_corner_deffect_tab(self) -> QWidget:
        tab = QWidget()
        root = QHBoxLayout(tab)

        # =================================================
        # LEFT: Inner Term Chipoff
        # =================================================
        grp_inner = QGroupBox("Inner Term Chipoff")
        li = QVBoxLayout(grp_inner)

        def insp_image(prefix=""):
            g = QGroupBox("Insp Image")
            gl = QGridLayout(g)
            bg = QButtonGroup(tab)
            if prefix:
                bg.setObjectName(prefix + "insp_image")
            for i, t in enumerate(["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]):
                rb = QRadioButton(t)
                bg.addButton(rb)
                gl.addWidget(rb, i // 4, i % 4)
            if bg.buttons():
                bg.buttons()[0].setChecked(True)
            return g

        li.addWidget(insp_image("tcd_inner_"))

        cb_enable = QCheckBox("Enable")
        cb_enable.setObjectName("tcd_inner_enable")
        li.addWidget(cb_enable)
        
        cb_and = QCheckBox("Apply AND")
        cb_and.setObjectName("tcd_inner_apply_and")
        li.addWidget(cb_and)
        
        cb_black = QCheckBox("Black Pixels Count")
        cb_black.setObjectName("tcd_inner_black_pixels")
        li.addWidget(cb_black)
        
        cb_avg = QCheckBox("Use Average Contrast")
        cb_avg.setObjectName("tcd_inner_avg_contrast")
        li.addWidget(cb_avg)
        
        cb_device = QCheckBox("Use Device Contrast")
        cb_device.setObjectName("tcd_inner_device_contrast")
        li.addWidget(cb_device)

        c = QHBoxLayout()
        c.addWidget(QLabel("Contrast"))
        sl_contrast = QSlider(Qt.Horizontal)
        sl_contrast.setRange(0, 255)
        sl_contrast.setObjectName("tcd_inner_contrast_slider")
        le_contrast = QLineEdit("20")
        le_contrast.setObjectName("tcd_inner_contrast")
        self._sync_slider_lineedit(sl_contrast, le_contrast)
        c.addWidget(sl_contrast)
        c.addWidget(le_contrast)
        c.addWidget(QLabel("Level"))
        li.addLayout(c)

        g = QGridLayout()
        g.addWidget(QLabel("Inspection Width X"), 0, 0)
        le_width_x = QLineEdit("20")
        le_width_x.setObjectName("tcd_inner_width_x")
        g.addWidget(le_width_x, 0, 1)
        
        g.addWidget(QLabel("Inspection Width Y"), 0, 2)
        le_width_y = QLineEdit("20")
        le_width_y.setObjectName("tcd_inner_width_y")
        g.addWidget(le_width_y, 0, 3)

        g.addWidget(QLabel("Tolerance X"), 1, 0)
        le_tol_x = QLineEdit("0")
        le_tol_x.setObjectName("tcd_inner_tolerance_x")
        g.addWidget(le_tol_x, 1, 1)
        
        g.addWidget(QLabel("Min Area"), 1, 2)
        le_min_area = QLineEdit("25")
        le_min_area.setObjectName("tcd_inner_min_area")
        g.addWidget(le_min_area, 1, 3)

        g.addWidget(QLabel("Min Width"), 2, 0)
        le_min_width = QLineEdit("5")
        le_min_width.setObjectName("tcd_inner_min_width")
        g.addWidget(le_min_width, 2, 1)
        
        g.addWidget(QLabel("Min Height"), 2, 2)
        le_min_height = QLineEdit("5")
        le_min_height.setObjectName("tcd_inner_min_height")
        g.addWidget(le_min_height, 2, 3)

        g.addWidget(QLabel("Corner Ellipse Mask Size"), 3, 0)
        le_ellipse = QLineEdit("0")
        le_ellipse.setObjectName("tcd_inner_ellipse_mask")
        g.addWidget(le_ellipse, 3, 1)
        li.addLayout(g)

        grp_corner = QGroupBox("Corner Offset")
        gc = QGridLayout(grp_corner)
        cb_corner = QCheckBox("Enable")
        cb_corner.setObjectName("tcd_inner_corner_enable")
        gc.addWidget(cb_corner, 0, 0)
        
        gc.addWidget(QLabel("X"), 0, 1)
        le_corner_x = QLineEdit("5")
        le_corner_x.setObjectName("tcd_inner_corner_x")
        gc.addWidget(le_corner_x, 0, 2)
        
        gc.addWidget(QLabel("Y"), 0, 3)
        le_corner_y = QLineEdit("5")
        le_corner_y.setObjectName("tcd_inner_corner_y")
        gc.addWidget(le_corner_y, 0, 4)
        li.addWidget(grp_corner)

        grp_wo = QGroupBox("Without Corner Offset")
        gwo = QGridLayout(grp_wo)
        gwo.addWidget(QLabel("Top"), 0, 0)
        le_top = QLineEdit("5")
        le_top.setObjectName("tcd_inner_wo_top")
        gwo.addWidget(le_top, 0, 1)
        
        gwo.addWidget(QLabel("Bottom"), 0, 2)
        le_bottom = QLineEdit("5")
        le_bottom.setObjectName("tcd_inner_wo_bottom")
        gwo.addWidget(le_bottom, 0, 3)
        
        gwo.addWidget(QLabel("Left"), 1, 0)
        le_left = QLineEdit("5")
        le_left.setObjectName("tcd_inner_wo_left")
        gwo.addWidget(le_left, 1, 1)
        
        gwo.addWidget(QLabel("Right"), 1, 2)
        le_right = QLineEdit("5")
        le_right.setObjectName("tcd_inner_wo_right")
        gwo.addWidget(le_right, 1, 3)
        li.addWidget(grp_wo)

        grp_cmp = QGroupBox("Compare Terminal Corners")
        gcmp = QGridLayout(grp_cmp)
        cb_cmp = QCheckBox("Enable")
        cb_cmp.setObjectName("tcd_inner_compare_enable")
        gcmp.addWidget(cb_cmp, 0, 0)
        
        gcmp.addWidget(QLabel("Intensity Difference"), 0, 1)
        le_intensity = QLineEdit("30")
        le_intensity.setObjectName("tcd_inner_intensity_diff")
        gcmp.addWidget(le_intensity, 0, 2)
        li.addWidget(grp_cmp)

        li.addWidget(insp_image("tcd_inner_2_"))
        root.addWidget(grp_inner)

        # =================================================
        # RIGHT: Outer Term Chipoff
        # =================================================
        grp_outer = QGroupBox("Outer Term Chipoff")
        lo = QVBoxLayout(grp_outer)

        lo.addWidget(insp_image("tcd_outer_"))
        
        cb_outer_enable = QCheckBox("Enable")
        cb_outer_enable.setObjectName("tcd_outer_enable")
        lo.addWidget(cb_outer_enable)
        
        cb_pocket = QCheckBox("Enable Pocket Edge Filter")
        cb_pocket.setObjectName("tcd_outer_pocket_filter")
        lo.addWidget(cb_pocket)

        c2 = QHBoxLayout()
        c2.addWidget(QLabel("Contrast (Background)"))
        sl_bg = QSlider(Qt.Horizontal)
        sl_bg.setRange(0, 255)
        sl_bg.setObjectName("tcd_outer_contrast_slider")
        le_bg = QLineEdit("20")
        le_bg.setObjectName("tcd_outer_contrast")
        self._sync_slider_lineedit(sl_bg, le_bg)
        c2.addWidget(sl_bg)
        c2.addWidget(le_bg)
        c2.addWidget(QLabel("Level"))
        lo.addLayout(c2)

        g2 = QGridLayout()
        g2.addWidget(QLabel("Min Area"), 0, 0)
        le_outer_area = QLineEdit("10")
        le_outer_area.setObjectName("tcd_outer_min_area")
        g2.addWidget(le_outer_area, 0, 1)
        
        g2.addWidget(QLabel("Min Sq Size"), 1, 0)
        le_outer_sq = QLineEdit("5")
        le_outer_sq.setObjectName("tcd_outer_min_square")
        g2.addWidget(le_outer_sq, 1, 1)
        
        g2.addWidget(QLabel("Minimum %"), 2, 0)
        le_outer_pct = QLineEdit("20")
        le_outer_pct.setObjectName("tcd_outer_min_percent")
        g2.addWidget(le_outer_pct, 2, 1)
        lo.addLayout(g2)

        grp_w = QGroupBox("Inspection Width")
        gw = QGridLayout(grp_w)
        for i, t in enumerate(["Left", "Right", "Top", "Bottom"]):
            cb_width = QCheckBox(t)
            cb_width.setObjectName(f"tcd_outer_width_{t.lower()}_enable")
            gw.addWidget(cb_width, i, 0)
            
            le_width = QLineEdit("10")
            le_width.setObjectName(f"tcd_outer_width_{t.lower()}")
            gw.addWidget(le_width, i, 1)
        lo.addWidget(grp_w)

        def offset_group(title, prefix):
            g = QGroupBox(title)
            gl = QGridLayout(g)
            gl.addWidget(QLabel("Top"), 0, 0)
            le_top = QLineEdit("5")
            le_top.setObjectName(prefix + "offset_top")
            gl.addWidget(le_top, 0, 1)
            
            gl.addWidget(QLabel("Left"), 0, 2)
            le_left = QLineEdit("5")
            le_left.setObjectName(prefix + "offset_left")
            gl.addWidget(le_left, 0, 3)
            
            gl.addWidget(QLabel("Bottom"), 1, 0)
            le_bottom = QLineEdit("5")
            le_bottom.setObjectName(prefix + "offset_bottom")
            gl.addWidget(le_bottom, 1, 1)
            
            gl.addWidget(QLabel("Right"), 1, 2)
            le_right = QLineEdit("5")
            le_right.setObjectName(prefix + "offset_right")
            gl.addWidget(le_right, 1, 3)
            return g

        lo.addWidget(offset_group("Left Terminal Offset", "tcd_outer_left_"))
        lo.addWidget(offset_group("Right Terminal Offset", "tcd_outer_right_"))

        grp_hi = QGroupBox("Inner Term Chipoff High Intensity")
        ghi = QGridLayout(grp_hi)
        cb_hi = QCheckBox("Enable")
        cb_hi.setObjectName("tcd_outer_hi_enable")
        ghi.addWidget(cb_hi, 0, 0)
        
        ghi.addWidget(QLabel("Min. Intensity"), 0, 1)
        le_hi_intensity = QLineEdit("95")
        le_hi_intensity.setObjectName("tcd_outer_hi_intensity")
        ghi.addWidget(le_hi_intensity, 0, 2)
        lo.addWidget(grp_hi)

        grp_img2 = QGroupBox("Insp Image")
        gi2 = QHBoxLayout(grp_img2)
        bg_img2 = QButtonGroup(tab)
        bg_img2.setObjectName("tcd_outer_insp_image_rgb")
        for t in ["Red", "Green", "Blue"]:
            rb = QRadioButton(t)
            bg_img2.addButton(rb)
            gi2.addWidget(rb)
        if bg_img2.buttons():
            bg_img2.buttons()[0].setChecked(True)
        lo.addWidget(grp_img2)

        root.addWidget(grp_outer)

        return tab
    #Body Edge Effect
    def _body_edge_effect_tab(self) -> QWidget:
        tab = QWidget()
        root = QHBoxLayout(tab)
        root.setSpacing(20)

        # ==================================================
        # LEFT SIDE — BLACK DEFECT
        # ==================================================
        grp_black = QGroupBox("Black Defect")
        left = QVBoxLayout(grp_black)
        left.setSpacing(10)

        # Insp Image
        grp_img_black = QGroupBox("Insp Image")
        img_l = QGridLayout(grp_img_black)
        bg_left = QButtonGroup(tab)
        bg_left.setObjectName("bee_left_insp_image")
        for i, txt in enumerate(["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]):
            rb = QRadioButton(txt)
            bg_left.addButton(rb)
            img_l.addWidget(rb, i // 4, i % 4)
        bg_left.buttons()[0].setChecked(True)
        left.addWidget(grp_img_black)

        cb_enable = QCheckBox("Enable")
        cb_enable.setObjectName("bee_left_enable")
        left.addWidget(cb_enable)

        # Contrast
        c1 = QGridLayout()
        c1.addWidget(QLabel("Contrast (Top):"), 0, 0)
        sl_top = QSlider(Qt.Horizontal)
        sl_top.setRange(0, 255)
        sl_top.setObjectName("bee_left_contrast_top_slider")
        le_top = QLineEdit("20")
        le_top.setObjectName("bee_left_contrast_top")
        self._sync_slider_lineedit(sl_top, le_top)
        c1.addWidget(sl_top, 0, 1)
        c1.addWidget(le_top, 0, 2)
        c1.addWidget(QLabel("Levels"), 0, 3)

        c1.addWidget(QLabel("Contrast (Bot):"), 1, 0)
        sl_bot = QSlider(Qt.Horizontal)
        sl_bot.setRange(0, 255)
        sl_bot.setObjectName("bee_left_contrast_bot_slider")
        le_bot = QLineEdit("20")
        le_bot.setObjectName("bee_left_contrast_bot")
        self._sync_slider_lineedit(sl_bot, le_bot)
        c1.addWidget(sl_bot, 1, 1)
        c1.addWidget(le_bot, 1, 2)
        c1.addWidget(QLabel("Levels"), 1, 3)

        left.addLayout(c1)

        # Area
        g_area = QGridLayout()
        g_area.addWidget(QLabel("Min Area:"), 0, 0)
        le_area = QLineEdit("30")
        le_area.setObjectName("bee_left_min_area")
        g_area.addWidget(le_area, 0, 1)
        g_area.addWidget(QLabel("Min Sqr Size:"), 1, 0)
        le_sqr = QLineEdit("3")
        le_sqr.setObjectName("bee_left_min_square")
        g_area.addWidget(le_sqr, 1, 1)
        left.addLayout(g_area)

        # Edge Width & Offset
        grp_edge = QGroupBox("Edge Width")
        ge = QGridLayout(grp_edge)
        edge_labels = ["Top", "Bottom", "Left", "Right"]
        for r, lbl in enumerate(edge_labels):
            ge.addWidget(QLabel(lbl), r, 0)
            le_edge = QLineEdit("10")
            le_edge.setObjectName(f"bee_left_edge_width_{lbl.lower()}")
            ge.addWidget(le_edge, r, 1)
        left.addWidget(grp_edge)

        grp_offset = QGroupBox("Insp Offset")
        go = QGridLayout(grp_offset)
        offset_labels = ["Top", "Bottom", "Left", "Right"]
        for r, lbl in enumerate(offset_labels):
            go.addWidget(QLabel(lbl), r, 0)
            le_off = QLineEdit("5")
            le_off.setObjectName(f"bee_left_offset_{lbl.lower()}")
            go.addWidget(le_off, r, 1)
        left.addWidget(grp_offset)

        grp_corner = QGroupBox("Corner Mask Size")
        gc = QGridLayout(grp_corner)
        gc.addWidget(QLabel("Left"), 0, 0)
        le_corner_left = QLineEdit("5")
        le_corner_left.setObjectName("bee_left_corner_left")
        gc.addWidget(le_corner_left, 0, 1)
        gc.addWidget(QLabel("Top"), 0, 2)
        le_corner_top = QLineEdit("5")
        le_corner_top.setObjectName("bee_left_corner_top")
        gc.addWidget(le_corner_top, 0, 3)
        gc.addWidget(QLabel("Right"), 1, 0)
        le_corner_right = QLineEdit("5")
        le_corner_right.setObjectName("bee_left_corner_right")
        gc.addWidget(le_corner_right, 1, 1)
        gc.addWidget(QLabel("Bottom"), 1, 2)
        le_corner_bot = QLineEdit("5")
        le_corner_bot.setObjectName("bee_left_corner_bottom")
        gc.addWidget(le_corner_bot, 1, 3)
        left.addWidget(grp_corner)

        left.addStretch()

        # ==================================================
        # RIGHT SIDE — WHITE DEFECT
        # ==================================================
        grp_white = QGroupBox("White Defect")
        right = QVBoxLayout(grp_white)
        right.setSpacing(10)

        # Use Edge Average
        cb_edge_avg = QCheckBox("Use Edge Average")
        cb_edge_avg.setObjectName("bee_right_use_edge_avg")
        right.addWidget(cb_edge_avg)

        # Insp Image
        grp_img_white = QGroupBox("Insp Image")
        img_r = QGridLayout(grp_img_white)
        bg_right = QButtonGroup(tab)
        bg_right.setObjectName("bee_right_insp_image")
        for i, txt in enumerate(["Merge", "Red", "Green", "Blue", "RG", "RB", "GB"]):
            rb = QRadioButton(txt)
            bg_right.addButton(rb)
            img_r.addWidget(rb, i // 4, i % 4)
        bg_right.buttons()[0].setChecked(True)
        right.addWidget(grp_img_white)

        cb_w_enable = QCheckBox("Enable")
        cb_w_enable.setObjectName("bee_right_enable")
        right.addWidget(cb_w_enable)
        
        cb_detect = QCheckBox("Detect to PASS")
        cb_detect.setObjectName("bee_right_detect_to_pass")
        right.addWidget(cb_detect)

        # Contrast
        c2 = QGridLayout()
        c2.addWidget(QLabel("Contrast (Top):"), 0, 0)
        sl_w_top = QSlider(Qt.Horizontal)
        sl_w_top.setRange(0, 255)
        sl_w_top.setObjectName("bee_right_contrast_top_slider")
        le_w_top = QLineEdit("35")
        le_w_top.setObjectName("bee_right_contrast_top")
        self._sync_slider_lineedit(sl_w_top, le_w_top)
        c2.addWidget(sl_w_top, 0, 1)
        c2.addWidget(le_w_top, 0, 2)
        c2.addWidget(QLabel("Levels"), 0, 3)

        c2.addWidget(QLabel("Contrast (Bot):"), 1, 0)
        sl_w_bot = QSlider(Qt.Horizontal)
        sl_w_bot.setRange(0, 255)
        sl_w_bot.setObjectName("bee_right_contrast_bot_slider")
        le_w_bot = QLineEdit("35")
        le_w_bot.setObjectName("bee_right_contrast_bot")
        self._sync_slider_lineedit(sl_w_bot, le_w_bot)
        c2.addWidget(sl_w_bot, 1, 1)
        c2.addWidget(le_w_bot, 1, 2)
        c2.addWidget(QLabel("Levels"), 1, 3)
        right.addLayout(c2)

        # Area
        g2 = QGridLayout()
        g2.addWidget(QLabel("Min Area:"), 0, 0)
        le_w_area = QLineEdit("20")
        le_w_area.setObjectName("bee_right_min_area")
        g2.addWidget(le_w_area, 0, 1)
        g2.addWidget(QLabel("Min Sqr Size:"), 0, 2)
        le_w_sqr = QLineEdit("3")
        le_w_sqr.setObjectName("bee_right_min_square")
        g2.addWidget(le_w_sqr, 0, 3)
        right.addLayout(g2)

        # Ignore Reflection
        grp_ignore = QGroupBox("Ignore Reflection")
        gi = QGridLayout(grp_ignore)
        cb_ignore = QCheckBox("Enable")
        cb_ignore.setObjectName("bee_right_ignore_reflection_enable")
        gi.addWidget(cb_ignore, 0, 0)
        gi.addWidget(QLabel("Width %"), 0, 1)
        le_ignore_width = QLineEdit("30")
        le_ignore_width.setObjectName("bee_right_ignore_reflection_width")
        gi.addWidget(le_ignore_width, 0, 2)
        right.addWidget(grp_ignore)

        # Ignore Vertical Line
        grp_vert = QGroupBox("Ignore Vertical Line")
        gv = QGridLayout(grp_vert)
        cb_vert = QCheckBox("Enable")
        cb_vert.setObjectName("bee_right_ignore_vertical_enable")
        gv.addWidget(cb_vert, 0, 0)
        gv.addWidget(QLabel("Contrast"), 0, 1)
        le_vert_contrast = QLineEdit("5")
        le_vert_contrast.setObjectName("bee_right_ignore_vertical_contrast")
        gv.addWidget(le_vert_contrast, 0, 2)
        gv.addWidget(QLabel("Height %"), 0, 3)
        le_vert_height = QLineEdit("30")
        le_vert_height.setObjectName("bee_right_ignore_vertical_height")
        gv.addWidget(le_vert_height, 0, 4)
        right.addWidget(grp_vert)

        # High Contrast
        grp_high = QGroupBox("High Contrast")
        gh = QGridLayout(grp_high)
        cb_high = QCheckBox("Enable")
        cb_high.setObjectName("bee_right_high_contrast_enable")
        gh.addWidget(cb_high, 0, 0)
        gh.addWidget(QLabel("Contrast:"), 1, 0)
        le_high_contrast = QLineEdit("62")
        le_high_contrast.setObjectName("bee_right_high_contrast")
        gh.addWidget(le_high_contrast, 1, 1)
        gh.addWidget(QLabel("Min Area:"), 1, 2)
        le_high_area = QLineEdit("25")
        le_high_area.setObjectName("bee_right_high_min_area")
        gh.addWidget(le_high_area, 1, 3)
        gh.addWidget(QLabel("Min Sqr Size:"), 1, 4)
        le_high_sqr = QLineEdit("4")
        le_high_sqr.setObjectName("bee_right_high_min_square")
        gh.addWidget(le_high_sqr, 1, 5)
        right.addWidget(grp_high)

        # Offsets
        grp_offsets = QGroupBox("Insp Offset")
        go2 = QGridLayout(grp_offsets)
        for r, lbl in enumerate(["Top", "Bottom", "Left", "Right"]):
            go2.addWidget(QLabel(lbl), r, 0)
            le_off2 = QLineEdit("5")
            le_off2.setObjectName(f"bee_right_offset_{lbl.lower()}")
            go2.addWidget(le_off2, r, 1)
        right.addWidget(grp_offsets)

        grp_edge2 = QGroupBox("Edge Width")
        ge2 = QGridLayout(grp_edge2)
        for r, lbl in enumerate(["Top", "Bottom", "Left", "Right"]):
            ge2.addWidget(QLabel(lbl), r, 0)
            le_edge2 = QLineEdit("3")
            le_edge2.setObjectName(f"bee_right_edge_width_{lbl.lower()}")
            ge2.addWidget(le_edge2, r, 1)
        right.addWidget(grp_edge2)

        grp_corner2 = QGroupBox("Corner Mask Size")
        gc2 = QGridLayout(grp_corner2)
        for r, lbl in enumerate(["Left", "Right", "Top", "Bottom"]):
            gc2.addWidget(QLabel(lbl), r, 0)
            le_corner2 = QLineEdit("5")
            le_corner2.setObjectName(f"bee_right_corner_{lbl.lower()}")
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
        root = QHBoxLayout(tab)
        root.setSpacing(20)

        # =====================================
        # Body Color
        # =====================================
        grp_body = QGroupBox("Body Color")
        gb = QVBoxLayout(grp_body)

        cb_body = QCheckBox("Enable")
        cb_body.setObjectName("ci_body_enable")
        gb.addWidget(cb_body)

        g1 = QGridLayout()
        g1.setHorizontalSpacing(10)
        g1.setVerticalSpacing(6)

        g1.addWidget(QLabel("Contrast:"), 0, 0)
        le_body_contrast = QLineEdit("12")
        le_body_contrast.setObjectName("ci_body_contrast")
        g1.addWidget(le_body_contrast, 0, 1)

        g1.addWidget(QLabel("Width:"), 1, 0)
        le_body_width = QLineEdit("50")
        le_body_width.setObjectName("ci_body_width")
        g1.addWidget(le_body_width, 1, 1)

        g1.addWidget(QLabel("Height:"), 2, 0)
        le_body_height = QLineEdit("20")
        le_body_height.setObjectName("ci_body_height")
        g1.addWidget(le_body_height, 2, 1)

        gb.addLayout(g1)
        gb.addStretch()

        # =====================================
        # Terminal Color
        # =====================================
        grp_term = QGroupBox("Terminal Color")
        gt = QVBoxLayout(grp_term)

        cb_term = QCheckBox("Enable")
        cb_term.setObjectName("ci_term_enable")
        gt.addWidget(cb_term)

        g2 = QGridLayout()
        g2.setHorizontalSpacing(10)
        g2.setVerticalSpacing(6)

        g2.addWidget(QLabel("Contrast:"), 0, 0)
        le_term_contrast = QLineEdit("200")
        le_term_contrast.setObjectName("ci_term_contrast")
        g2.addWidget(le_term_contrast, 0, 1)

        g2.addWidget(QLabel("Left Width:"), 1, 0)
        le_term_left_width = QLineEdit("10")
        le_term_left_width.setObjectName("ci_term_left_width")
        g2.addWidget(le_term_left_width, 1, 1)

        g2.addWidget(QLabel("Right Width:"), 2, 0)
        le_term_right_width = QLineEdit("10")
        le_term_right_width.setObjectName("ci_term_right_width")
        g2.addWidget(le_term_right_width, 2, 1)

        gt.addLayout(g2)

        # Offset group
        grp_offset = QGroupBox("Offset")
        go = QGridLayout(grp_offset)
        go.setHorizontalSpacing(10)
        go.setVerticalSpacing(6)

        go.addWidget(QLabel("Top:"), 0, 0)
        le_offset_top = QLineEdit("10")
        le_offset_top.setObjectName("ci_offset_top")
        go.addWidget(le_offset_top, 0, 1)
        
        go.addWidget(QLabel("Left:"), 0, 2)
        le_offset_left = QLineEdit("10")
        le_offset_left.setObjectName("ci_offset_left")
        go.addWidget(le_offset_left, 0, 3)

        go.addWidget(QLabel("Bottom:"), 1, 0)
        le_offset_bottom = QLineEdit("10")
        le_offset_bottom.setObjectName("ci_offset_bottom")
        go.addWidget(le_offset_bottom, 1, 1)
        
        go.addWidget(QLabel("Right:"), 1, 2)
        le_offset_right = QLineEdit("10")
        le_offset_right.setObjectName("ci_offset_right")
        go.addWidget(le_offset_right, 1, 3)

        gt.addWidget(grp_offset)
        gt.addStretch()

        # =====================================
        root.addWidget(grp_body)
        root.addWidget(grp_term)
        root.addStretch()

        return tab

    # =================================================
    # Helpers
    # =================================================
    def _minmax(self, grid, row, name, min1, max1, min2, max2):
        grid.addWidget(QLabel(name + ":"), row, 0)
        grid.addWidget(QLabel("Min:"), row, 1)
        grid.addWidget(QLineEdit(min1), row, 2)
        grid.addWidget(QLineEdit(max1), row, 3)
        grid.addWidget(QLabel("Max:"), row + 1, 1)
        grid.addWidget(QLineEdit(min2), row + 1, 2)
        grid.addWidget(QLineEdit(max2), row + 1, 3)

    def _simple_minmax(self, grid, label, v1, v2, row):
        grid.addWidget(QLabel(label + ":"), row, 0)
        grid.addWidget(QLineEdit(v1), row, 1)
        grid.addWidget(QLineEdit(v2), row, 2)

    def _stub_tab(self, text):
        w = QWidget()
        l = QVBoxLayout(w)
        lbl = QLabel(f"{text}\n(UI not implemented yet)")
        lbl.setStyleSheet("color:gray;")
        l.addWidget(lbl)
        l.addStretch()
        return w
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
    def _sync_slider_lineedit(self, slider: QSlider, lineedit: QLineEdit):
        """Connect a slider and line edit so moving one updates the other."""
        slider.valueChanged.connect(lambda v: lineedit.setText(str(v)))
        lineedit.textChanged.connect(
            lambda text: slider.setValue(int(text) if text.isdigit() else slider.value())
        )
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

        # >>> ADD THIS <<<
        for bg in tab.findChildren(QButtonGroup):
            if bg.objectName() and bg.checkedButton():
                tab_data[bg.objectName()] = bg.checkedButton().text()
        # <<< END ADD >>>

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

        # >>> ADD THIS <<<
        for bg in tab.findChildren(QButtonGroup):
            if bg.objectName() in tab_data:
                value = tab_data[bg.objectName()]
                for btn in bg.buttons():
                    if btn.text() == value:
                        btn.setChecked(True)
                        break
        # <<< END ADD >>>

