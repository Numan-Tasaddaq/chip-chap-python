from PySide6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QHBoxLayout,
    QGroupBox, QGridLayout, QCheckBox, QLineEdit,QSlider,QScrollArea, QWidget,QPushButton
)
from PySide6.QtCore import Qt
import json
import os



class PocketLocationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Pocket Location Parameters")
        self.resize(1100, 750)
        self.setWindowFlags(
    Qt.Window
    | Qt.WindowMinimizeButtonHint
    | Qt.WindowCloseButtonHint
)


        self._build_ui()
        self.load_from_json("pocket_params.json")


    def _build_ui(self):
        root = QVBoxLayout(self)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        container = QWidget()
        scroll_layout = QVBoxLayout(container)

        root.addWidget(scroll)
        scroll.setWidget(container)


        # ==================================================
        # GLOBAL MAIN ROW
        # ==================================================
        main_row = QHBoxLayout()
        scroll_layout.addLayout(main_row)


        # ==================================================
        # GLOBAL LEFT COLUMN
        # ==================================================
        left_col = QVBoxLayout()
        main_row.addLayout(left_col, 1)

            # -------- TOP FIXED CONTROLS --------
        cb_enable_pocket = QCheckBox("Enable Pocket Location")
        cb_enable_pocket.setObjectName("enable_pocket_location")
        left_col.addWidget(cb_enable_pocket)

        cb_enable_post_seal = QCheckBox("Enable Post Seal")
        cb_enable_post_seal.setObjectName("enable_post_seal")
        left_col.addWidget(cb_enable_post_seal)

        cb_enable_emboss = QCheckBox("Enable Emboss Tape")
        cb_enable_emboss.setObjectName("enable_emboss_tape")
        left_col.addWidget(cb_enable_emboss)

        # Edge Contrast row
        edge_row = QHBoxLayout()
        edge_row.addWidget(QLabel("Edge Contrast"))

        # Slider
        edge_slider = QSlider(Qt.Horizontal)
        edge_slider.setRange(0, 255)
        edge_slider.setValue(212)
        edge_slider.setFixedWidth(140)
        edge_slider.setObjectName("edge_contrast_slider")
        edge_row.addWidget(edge_slider)

        # Line edit for exact value
        edge_value = self._box("212", "edge_contrast_value")
        edge_row.addWidget(edge_value)

        # --------- Connect slider <-> line edit ----------
        def sync_slider_to_edit(value):
            edge_value.setText(str(value))

        def sync_edit_to_slider():
            try:
                val = int(edge_value.text())
                if 0 <= val <= 255:
                    edge_slider.setValue(val)
            except ValueError:
                pass  # ignore non-integer input

        edge_slider.valueChanged.connect(sync_slider_to_edit)
        edge_value.editingFinished.connect(sync_edit_to_slider)
        # -------------------------------------------------

        edge_row.addStretch()
        left_col.addLayout(edge_row)

        # Post Seal Low Contrast row
        post_row = QHBoxLayout()
        post_row.addWidget(QLabel("Post Seal Low Contrast"))

        post_seal_low = self._box("10", "post_seal_low_contrast")
        post_row.addWidget(post_seal_low)

        post_row.addStretch()
        left_col.addLayout(post_row)


        # ==================================================
        # INNER LEFT–RIGHT SPLIT (INSIDE GLOBAL LEFT)
        # ==================================================
        inner_row = QHBoxLayout()
        left_col.addLayout(inner_row)

        inner_left = QVBoxLayout()
        inner_right = QVBoxLayout()
        inner_row.addLayout(inner_left)
        inner_row.addLayout(inner_right)

        # ==================================================
        # INNER LEFT GROUPS
        # ==================================================
       # -------- Body Area Paper Dust Mask --------
        grp_body = QGroupBox("Body Area Paper Dust Mask")
        g = QGridLayout(grp_body)

        g.addWidget(QLabel("Tolerance"), 0, 0)
        g.addWidget(self._box("70", "body_area_tolerance"), 0, 1)

        cb_body_enable = QCheckBox("Enable")
        cb_body_enable.setObjectName("body_area_enable")
        g.addWidget(cb_body_enable, 1, 0)

        g.addWidget(QLabel("Left Offset"), 1, 1)
        g.addWidget(self._box("40", "body_area_left_offset"), 1, 2)

        g.addWidget(QLabel("Right Offset"), 2, 1)
        g.addWidget(self._box("40", "body_area_right_offset"), 2, 2)

        inner_left.addWidget(grp_body)


        # -------- Direction --------
        grp_dir = QGroupBox("Direction")
        l = QVBoxLayout(grp_dir)

        cb_parallel = QCheckBox("Enable Parallel Chip")
        cb_parallel.setObjectName("direction_parallel_enable")
        l.addWidget(cb_parallel)

        cb_non_parallel = QCheckBox("Enable None Parallel Chip")
        cb_non_parallel.setObjectName("direction_non_parallel_enable")
        l.addWidget(cb_non_parallel)

        row = QHBoxLayout()
        row.addWidget(QLabel("Max Parallel Angle Tol"))
        row.addWidget(self._box("3", "direction_max_parallel_angle_tol"))
        row.addStretch()
        l.addLayout(row)

        inner_left.addWidget(grp_dir)


        # -------- Pocket Dimension Inspection --------
        grp_dim = QGroupBox("Pocket Dimension Inspection")
        g = QGridLayout(grp_dim)

        cb_pocket_length = QCheckBox("Pocket Length")
        cb_pocket_length.setObjectName("pocket_dim_length_enable")
        g.addWidget(cb_pocket_length, 0, 0)

        cb_pocket_width = QCheckBox("Pocket Width")
        cb_pocket_width.setObjectName("pocket_dim_width_enable")
        g.addWidget(cb_pocket_width, 0, 1)

        g.addWidget(QLabel("Pocket Length"), 1, 0)
        g.addWidget(self._box("100", "pocket_length_min"), 1, 1)
        g.addWidget(self._box("100", "pocket_length_max"), 1, 2)

        g.addWidget(QLabel("Pocket Width"), 2, 0)
        g.addWidget(self._box("100", "pocket_width_min"), 2, 1)
        g.addWidget(self._box("100", "pocket_width_max"), 2, 2)

        inner_left.addWidget(grp_dim)


        # -------- Pocket Gap Inspection --------
       # -------- Pocket Gap Inspection --------
        grp_gap = QGroupBox("Pocket Gap Inspection")
        g = QGridLayout(grp_gap)

        cb_gap_enable = QCheckBox("Enable Pocket Gap")
        cb_gap_enable.setObjectName("pocket_gap_enable")
        g.addWidget(cb_gap_enable, 0, 0)

        cb_gap_4_sides = QCheckBox("4 Sides")
        cb_gap_4_sides.setObjectName("pocket_gap_4_sides")
        g.addWidget(cb_gap_4_sides, 0, 1)

        cb_gap_left = QCheckBox("Left")
        cb_gap_left.setObjectName("pocket_gap_left_enable")
        g.addWidget(cb_gap_left, 1, 0)

        g.addWidget(QLabel("X"), 1, 1)
        g.addWidget(QLabel("Y"), 1, 2)

        g.addWidget(QLabel("Pocket Gap Min"), 2, 0)
        g.addWidget(self._box("2", "pocket_gap_min_x"), 2, 1)
        g.addWidget(self._box("2", "pocket_gap_min_y"), 2, 2)

        inner_left.addWidget(grp_gap)


        # -------- Pocket Shift Log --------
        grp_shift = QGroupBox("Pocket Shift Log")
        g = QGridLayout(grp_shift)

        cb_shift_enable = QCheckBox("Enable")
        cb_shift_enable.setObjectName("pocket_shift_enable")
        g.addWidget(cb_shift_enable, 0, 0)

        g.addWidget(QLabel("Pos:[0][0]"), 0, 1)

        g.addWidget(QLabel("X(+Ve)"), 1, 0)
        g.addWidget(self._box("50", "pocket_shift_x_pos"), 1, 1)

        g.addWidget(QLabel("X(-Ve)"), 1, 2)
        g.addWidget(self._box("50", "pocket_shift_x_neg"), 1, 3)

        g.addWidget(QLabel("Y(+Ve)"), 2, 0)
        g.addWidget(self._box("50", "pocket_shift_y_pos"), 2, 1)

        g.addWidget(QLabel("Y(-Ve)"), 2, 2)
        g.addWidget(self._box("50", "pocket_shift_y_neg"), 2, 3)

        inner_left.addWidget(grp_shift)
        inner_left.addStretch()

        # ==================================================
        # INNER RIGHT GROUPS
        # ==================================================
            # -------- Paper Dust Mask --------
        grp_paper = QGroupBox("Paper Dust Mask")
        g = QGridLayout(grp_paper)

        cb_paper_lr = QCheckBox("Left & Right")
        cb_paper_lr.setObjectName("paper_dust_left_right")
        g.addWidget(cb_paper_lr, 0, 0)

        cb_paper_tb = QCheckBox("Top & Bottom")
        cb_paper_tb.setObjectName("paper_dust_top_bottom")
        g.addWidget(cb_paper_tb, 0, 1)

        cb_paper_contrast = QCheckBox("Contrast+")
        cb_paper_contrast.setObjectName("paper_dust_contrast_plus")
        g.addWidget(cb_paper_contrast, 1, 0)

        inner_right.addWidget(grp_paper)


        # -------- Outer Pocket Stain Inspection --------
        grp_outer = QGroupBox("Outer Pocket Stain Inspection")
        g = QGridLayout(grp_outer)

        cb_outer_black = QCheckBox("Black")
        cb_outer_black.setObjectName("outer_stain_black")
        g.addWidget(cb_outer_black, 0, 0)

        cb_outer_white = QCheckBox("White")
        cb_outer_white.setObjectName("outer_stain_white")
        g.addWidget(cb_outer_white, 0, 1)

        g.addWidget(QLabel("Contrast"), 1, 0)
        g.addWidget(self._box("10", "outer_stain_contrast_min"), 1, 1)
        g.addWidget(self._box("170", "outer_stain_contrast_max"), 1, 2)

        g.addWidget(QLabel("Min Area"), 2, 0)
        g.addWidget(self._box("20", "outer_stain_min_area"), 2, 1)

        g.addWidget(QLabel("Min Sq Size"), 3, 0)
        g.addWidget(self._box("5", "outer_stain_min_sq_size"), 3, 1)

        inner_right.addWidget(grp_outer)


        # -------- Inspection Width --------
        grp_w = QGroupBox("Inspection Width")
        gw = QGridLayout(grp_w)

        gw.addWidget(QLabel("Left"), 0, 0)
        gw.addWidget(self._box("20", "inspect_width_left"), 0, 1)

        gw.addWidget(QLabel("Top"), 0, 2)
        gw.addWidget(self._box("20", "inspect_width_top"), 0, 3)

        gw.addWidget(QLabel("Right"), 1, 0)
        gw.addWidget(self._box("20", "inspect_width_right"), 1, 1)

        gw.addWidget(QLabel("Bottom"), 1, 2)
        gw.addWidget(self._box("20", "inspect_width_bottom"), 1, 3)

        inner_right.addWidget(grp_w)


        # -------- Inspection Offset --------
        grp_o = QGroupBox("Inspection Offset")
        go = QGridLayout(grp_o)

        go.addWidget(QLabel("Left"), 0, 0)
        go.addWidget(self._box("10", "inspect_offset_left"), 0, 1)

        go.addWidget(QLabel("Top"), 0, 2)
        go.addWidget(self._box("10", "inspect_offset_top"), 0, 3)

        go.addWidget(QLabel("Right"), 1, 0)
        go.addWidget(self._box("10", "inspect_offset_right"), 1, 1)

        go.addWidget(QLabel("Bottom"), 1, 2)
        go.addWidget(self._box("10", "inspect_offset_bottom"), 1, 3)

        inner_right.addWidget(grp_o)


        # -------- White Line Mask --------
        grp_white = QGroupBox("White Line Mask")
        g = QGridLayout(grp_white)

        cb_white_enable = QCheckBox("Enable")
        cb_white_enable.setObjectName("white_line_mask_enable")
        g.addWidget(cb_white_enable, 0, 0)

        g.addWidget(QLabel("Mask Size"), 1, 0)
        g.addWidget(self._box("1", "white_line_mask_size"), 1, 1)

        inner_right.addWidget(grp_white)


        # -------- Emboss Tape Pick Up --------
        grp_emboss = QGroupBox("Emboss Tape Pick Up")
        g = QGridLayout(grp_emboss)

        cb_emboss_enable = QCheckBox("Enable Emboss Tape Pick Up")
        cb_emboss_enable.setObjectName("emboss_tape_pickup_enable")
        g.addWidget(cb_emboss_enable, 0, 0, 1, 2)

        g.addWidget(QLabel("Contrast"), 1, 0)
        g.addWidget(self._box("100", "emboss_tape_contrast"), 1, 1)

        g.addWidget(QLabel("Left Search Offset"), 2, 0)
        g.addWidget(self._box("50", "emboss_tape_left_search_offset"), 2, 1)

        inner_right.addWidget(grp_emboss)
        inner_right.addStretch()


    
        
                # ==================================================
        # RIGHT SIDE – Sealing / Dent Inspection
        # ==================================================
        right_col = QVBoxLayout()
        main_row.addLayout(right_col, 1)

        # ---------- Sealing Stain Inspection ----------
        # ---------- Sealing Stain Inspection ----------
        grp_seal = QGroupBox("Sealing Stain Inspection")
        g = QGridLayout(grp_seal)

        cb_seal_enable = QCheckBox("Enable")
        cb_seal_enable.setObjectName("sealing_stain_enable")
        g.addWidget(cb_seal_enable, 0, 0)

        cb_seal_auto = QCheckBox("Enable Auto Adjust")
        cb_seal_auto.setObjectName("sealing_stain_auto_adjust")
        g.addWidget(cb_seal_auto, 0, 1)

        g.addWidget(QLabel("Contrast Left"), 1, 0)
        g.addWidget(self._box("180", "sealing_stain_contrast_left"), 1, 1)

        g.addWidget(QLabel("Right"), 1, 2)
        g.addWidget(self._box("180", "sealing_stain_contrast_right"), 1, 3)

        g.addWidget(QLabel("Filter Contrast"), 2, 0)
        g.addWidget(self._box("50", "sealing_stain_filter_contrast"), 2, 1)

        g.addWidget(QLabel("Min Area"), 3, 0)
        g.addWidget(self._box("20", "sealing_stain_min_area"), 3, 1)

        g.addWidget(QLabel("Min Sq Size"), 4, 0)
        g.addWidget(self._box("5", "sealing_stain_min_sq_size"), 4, 1)


        # ---- Inspection Width ----
        grp_w = QGroupBox("Inspection Width")
        gw = QGridLayout(grp_w)

        gw.addWidget(QLabel("Left"), 0, 0)
        gw.addWidget(self._box("60", "sealing_width_left"), 0, 1)

        gw.addWidget(QLabel("Top"), 0, 2)
        gw.addWidget(self._box("70", "sealing_width_top"), 0, 3)

        gw.addWidget(QLabel("Right"), 1, 0)
        gw.addWidget(self._box("60", "sealing_width_right"), 1, 1)

        gw.addWidget(QLabel("Bottom"), 1, 2)
        gw.addWidget(self._box("70", "sealing_width_bottom"), 1, 3)


        # ---- Inspection Offset ----
        grp_o = QGroupBox("Inspection Offset")
        go = QGridLayout(grp_o)

        go.addWidget(QLabel("Left"), 0, 0)
        go.addWidget(self._box("65", "sealing_offset_left"), 0, 1)

        go.addWidget(QLabel("Right"), 0, 2)
        go.addWidget(self._box("45", "sealing_offset_right"), 0, 3)


        g.addWidget(grp_w, 5, 0, 1, 4)
        g.addWidget(grp_o, 6, 0, 1, 4)

        right_col.addWidget(grp_seal)


       # ---------- Sealing Stain2 Inspection ----------
        grp_seal2 = QGroupBox("Sealing Stain2 Inspection")
        g = QGridLayout(grp_seal2)

        cb_seal2_enable = QCheckBox("Enable Sealing Stain2")
        cb_seal2_enable.setObjectName("sealing_stain2_enable")
        g.addWidget(cb_seal2_enable, 0, 0)

        g.addWidget(QLabel("Contrast"), 1, 0)
        g.addWidget(self._box("255", "sealing_stain2_contrast"), 1, 1)

        g.addWidget(QLabel("Min Area"), 2, 0)
        g.addWidget(self._box("20", "sealing_stain2_min_area"), 2, 1)

        g.addWidget(QLabel("Min Sq Size"), 3, 0)
        g.addWidget(self._box("5", "sealing_stain2_min_sq_size"), 3, 1)


        # ---- Inspection Width ----
        grp_w2 = QGroupBox("Inspection Width")
        gw2 = QGridLayout(grp_w2)

        gw2.addWidget(QLabel("Left"), 0, 0)
        gw2.addWidget(self._box("25", "sealing2_width_left"), 0, 1)

        gw2.addWidget(QLabel("Right"), 1, 0)
        gw2.addWidget(self._box("35", "sealing2_width_right"), 1, 1)

        gw2.addWidget(QLabel("Top"), 2, 0)
        gw2.addWidget(self._box("100", "sealing2_width_top"), 2, 1)

        gw2.addWidget(QLabel("Bottom"), 3, 0)
        gw2.addWidget(self._box("100", "sealing2_width_bottom"), 3, 1)


        # ---- Inspection Offset ----
        grp_o2 = QGroupBox("Inspection Offset")
        go2 = QGridLayout(grp_o2)

        go2.addWidget(QLabel("Top"), 0, 0)
        go2.addWidget(self._box("0", "sealing2_offset_top"), 0, 1)

        go2.addWidget(QLabel("Bottom"), 1, 0)
        go2.addWidget(self._box("5", "sealing2_offset_bottom"), 1, 1)


        g.addWidget(grp_w2, 4, 0, 1, 2)
        g.addWidget(grp_o2, 5, 0, 1, 2)

        right_col.addWidget(grp_seal2)


        # ---------- Sealing Shift Inspection ----------
        grp_shift = QGroupBox("Sealing Shift Inspection")
        g = QGridLayout(grp_shift)

        cb_seal_shift_enable = QCheckBox("Enable")
        cb_seal_shift_enable.setObjectName("sealing_shift_enable")
        g.addWidget(cb_seal_shift_enable, 0, 0)

        cb_bw_scar = QCheckBox("Black To White Scar")
        cb_bw_scar.setObjectName("sealing_shift_black_to_white_scar")
        g.addWidget(cb_bw_scar, 0, 1)

        cb_hole_ref = QCheckBox("Hole Ref")
        cb_hole_ref.setObjectName("sealing_shift_hole_ref")
        g.addWidget(cb_hole_ref, 1, 0)

        cb_wb_scar = QCheckBox("White To Black Scar")
        cb_wb_scar.setObjectName("sealing_shift_white_to_black_scar")
        g.addWidget(cb_wb_scar, 1, 1)

        g.addWidget(QLabel("Cover Tape Dist"), 2, 0)
        g.addWidget(self._box("59", "sealing_shift_cover_tape_min"), 2, 1)
        g.addWidget(self._box("435", "sealing_shift_cover_tape_max"), 2, 2)

        g.addWidget(QLabel("Sealing Mark Dist"), 3, 0)
        g.addWidget(self._box("190", "sealing_shift_mark_min"), 3, 1)
        g.addWidget(self._box("306", "sealing_shift_mark_max"), 3, 2)

        g.addWidget(QLabel("Contrast"), 4, 0)
        g.addWidget(self._box("245", "sealing_shift_contrast_primary"), 4, 1)
        g.addWidget(self._box("180", "sealing_shift_contrast_secondary"), 4, 2)

        g.addWidget(QLabel("Tolerance"), 5, 0)
        g.addWidget(self._box("25", "sealing_shift_tolerance_pos"), 5, 1)
        g.addWidget(self._box("25", "sealing_shift_tolerance_neg"), 5, 2)

        g.addWidget(QLabel("Left Search Offset"), 6, 0)
        g.addWidget(self._box("40", "sealing_shift_left_search_offset"), 6, 1)

        g.addWidget(QLabel("Top Search Offset"), 7, 0)
        g.addWidget(self._box("90", "sealing_shift_top_search_offset"), 7, 1)

        g.addWidget(QLabel("Hole Side Shift"), 8, 0)

        g.addWidget(QLabel("Contrast"), 9, 0)
        g.addWidget(self._box("123", "sealing_shift_hole_contrast"), 9, 1)

        g.addWidget(QLabel("Min Width"), 9, 2)
        g.addWidget(self._box("102", "sealing_shift_hole_min_width"), 9, 3)

        g.addWidget(QLabel("Offset"), 10, 0)
        g.addWidget(self._box("15", "sealing_shift_hole_offset"), 10, 1)

        g.addWidget(QLabel("Edge Count"), 10, 2)
        g.addWidget(self._box("50", "sealing_shift_hole_edge_count"), 10, 3)

        right_col.addWidget(grp_shift)


       # ---------- Bottom Dent Inspection ----------
        grp_dent = QGroupBox("Bottom Dent Inspection")
        g = QGridLayout(grp_dent)

        cb_dent_enable = QCheckBox("Enable Bottom Dent")
        cb_dent_enable.setObjectName("bottom_dent_enable")
        g.addWidget(cb_dent_enable, 0, 0)

        g.addWidget(QLabel("Contrast"), 1, 0)
        g.addWidget(self._box("255", "bottom_dent_contrast"), 1, 1)

        g.addWidget(QLabel("Min Area"), 2, 0)
        g.addWidget(self._box("20", "bottom_dent_min_area"), 2, 1)

        g.addWidget(QLabel("Min Sq Size"), 3, 0)
        g.addWidget(self._box("5", "bottom_dent_min_sq_size"), 3, 1)

        g.addWidget(QLabel("Empty Intensity Min"), 4, 0)
        g.addWidget(self._box("120", "bottom_dent_empty_intensity_min"), 4, 1)

        g.addWidget(QLabel("Max"), 4, 2)
        g.addWidget(self._box("220", "bottom_dent_empty_intensity_max"), 4, 3)


        # ---- Inspection Offset ----
        grp_o3 = QGroupBox("Inspection Offset")
        go3 = QGridLayout(grp_o3)

        go3.addWidget(QLabel("L"), 0, 0)
        go3.addWidget(self._box("15", "bottom_dent_offset_left"), 0, 1)

        go3.addWidget(QLabel("R"), 0, 2)
        go3.addWidget(self._box("15", "bottom_dent_offset_right"), 0, 3)

        go3.addWidget(QLabel("T"), 1, 0)
        go3.addWidget(self._box("15", "bottom_dent_offset_top"), 1, 1)

        go3.addWidget(QLabel("B"), 1, 2)
        go3.addWidget(self._box("15", "bottom_dent_offset_bottom"), 1, 3)

        g.addWidget(grp_o3, 5, 0, 1, 4)


        # ---- Search Edge Offset ----
        grp_search = QGroupBox("Search Edge Offset")
        gs = QGridLayout(grp_search)

        gs.addWidget(QLabel("X"), 0, 0)
        gs.addWidget(self._box("20", "bottom_dent_search_offset_x"), 0, 1)

        gs.addWidget(QLabel("Y"), 0, 2)
        gs.addWidget(self._box("40", "bottom_dent_search_offset_y"), 0, 3)

        g.addWidget(grp_search, 6, 0, 1, 4)

        right_col.addWidget(grp_dent)
        right_col.addStretch()


# ---------- BUTTONS (NON-SCROLLING) ----------
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_ok = QPushButton("OK")
        btn_apply = QPushButton("Apply")
        btn_close = QPushButton("Close")
        btn_ok.clicked.connect(lambda: self.save_to_json("pocket_params.json"))
        btn_apply.clicked.connect(lambda: self.save_to_json("pocket_params.json"))
        btn_close.clicked.connect(self.close)


        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_apply)
        btn_row.addWidget(btn_close)

        root.addLayout(btn_row)
    def save_to_json(self, filepath):
        data = {}

        # Collect all relevant widgets
        widgets = []
        widgets.extend(self.findChildren(QLineEdit))
        widgets.extend(self.findChildren(QCheckBox))
        widgets.extend(self.findChildren(QSlider))

        for widget in widgets:
            name = widget.objectName()
            if not name:
                continue

            if isinstance(widget, QLineEdit):
                data[name] = widget.text()

            elif isinstance(widget, QCheckBox):
                data[name] = widget.isChecked()

            elif isinstance(widget, QSlider):
                data[name] = widget.value()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


    def load_from_json(self, filepath):
        if not os.path.exists(filepath):
            return

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Collect all relevant widgets
        widgets = []
        widgets.extend(self.findChildren(QLineEdit))
        widgets.extend(self.findChildren(QCheckBox))
        widgets.extend(self.findChildren(QSlider))

        for widget in widgets:
            name = widget.objectName()
            if not name or name not in data:
                continue

            if isinstance(widget, QLineEdit):
                widget.setText(str(data[name]))

            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(data[name]))

            elif isinstance(widget, QSlider):
                widget.setValue(int(data[name]))


    # =================================================
    # HELPERS
    # =================================================
    def _box(self, text, name=None):
        e = QLineEdit(text)
        e.setFixedWidth(45)
        if name:
            e.setObjectName(name)
        return e

