from PySide6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QHBoxLayout,
    QGroupBox, QGridLayout, QCheckBox, QLineEdit, QSlider, QScrollArea, 
    QWidget, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import json
import os

class PocketLocationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Pocket Location Parameters")
        self.resize(1100, 600)
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
                padding: 4px;
                background-color: white;
                min-height: 24px;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
                background-color: #f8f9fa;
            }
            QCheckBox {
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
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
            QPushButton#closeButton {
                background-color: #95a5a6;
            }
            QPushButton#closeButton:hover {
                background-color: #7f8c8d;
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
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self._build_ui()
        self.load_from_json("pocket_params.json")

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(10, 10, 10, 10)

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

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        container = QWidget()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setContentsMargins(15, 15, 15, 15)
        scroll_layout.setSpacing(15)

        scroll.setWidget(container)
        content_layout.addWidget(scroll)
        root.addWidget(content_frame)

        # ==================================================
        # GLOBAL MAIN ROW
        # ==================================================
        main_row = QHBoxLayout()
        main_row.setSpacing(20)
        scroll_layout.addLayout(main_row)

        # ==================================================
        # GLOBAL LEFT COLUMN
        # ==================================================
        left_col = QVBoxLayout()
        left_col.setSpacing(15)
        main_row.addLayout(left_col, 1)

        # -------- TOP FIXED CONTROLS --------
        cb_enable_pocket = self._create_checkbox("Enable Pocket Location")
        cb_enable_pocket.setObjectName("enable_pocket_location")
        left_col.addWidget(cb_enable_pocket)

        cb_enable_post_seal = self._create_checkbox("Enable Post Seal")
        cb_enable_post_seal.setObjectName("enable_post_seal")
        left_col.addWidget(cb_enable_post_seal)

        cb_enable_emboss = self._create_checkbox("Enable Emboss Tape")
        cb_enable_emboss.setObjectName("enable_emboss_tape")
        left_col.addWidget(cb_enable_emboss)

        # Edge Contrast row
        edge_row = QHBoxLayout()
        edge_row.setSpacing(10)
        edge_label = QLabel("Edge Contrast:")
        edge_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        edge_row.addWidget(edge_label)

        # Slider
        edge_slider = QSlider(Qt.Horizontal)
        edge_slider.setRange(0, 255)
        edge_slider.setValue(212)
        edge_slider.setFixedWidth(160)
        edge_slider.setObjectName("edge_contrast_slider")
        edge_row.addWidget(edge_slider)

        # Line edit for exact value
        edge_value = self._box("212", "edge_contrast_value")
        edge_value.setAlignment(Qt.AlignCenter)
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
                pass

        edge_slider.valueChanged.connect(sync_slider_to_edit)
        edge_value.editingFinished.connect(sync_edit_to_slider)
        # -------------------------------------------------

        edge_row.addStretch()
        left_col.addLayout(edge_row)

        # Post Seal Low Contrast row
        post_row = QHBoxLayout()
        post_row.setSpacing(10)
        post_label = QLabel("Post Seal Low Contrast:")
        post_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        post_row.addWidget(post_label)

        post_seal_low = self._box("10", "post_seal_low_contrast")
        post_seal_low.setAlignment(Qt.AlignCenter)
        post_row.addWidget(post_seal_low)

        post_row.addStretch()
        left_col.addLayout(post_row)

        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet("background-color: #e0e0e0; margin: 5px 0;")
        left_col.addWidget(separator1)

        # ==================================================
        # INNER LEFT–RIGHT SPLIT (INSIDE GLOBAL LEFT)
        # ==================================================
        inner_row = QHBoxLayout()
        inner_row.setSpacing(20)
        left_col.addLayout(inner_row)

        inner_left = QVBoxLayout()
        inner_left.setSpacing(15)
        inner_right = QVBoxLayout()
        inner_right.setSpacing(15)
        inner_row.addLayout(inner_left)
        inner_row.addLayout(inner_right)

        # ==================================================
        # INNER LEFT GROUPS
        # ==================================================
        # -------- Body Area Paper Dust Mask --------
        grp_body = self._create_group_box("Body Area Paper Dust Mask")
        g = QGridLayout(grp_body)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.setContentsMargins(10, 15, 10, 10)

        g.addWidget(self._create_label("Tolerance"), 0, 0)
        g.addWidget(self._box("70", "body_area_tolerance"), 0, 1)

        cb_body_enable = self._create_checkbox("Enable")
        cb_body_enable.setObjectName("body_area_enable")
        g.addWidget(cb_body_enable, 1, 0)

        g.addWidget(self._create_label("Left Offset"), 1, 1)
        g.addWidget(self._box("40", "body_area_left_offset"), 1, 2)

        g.addWidget(self._create_label("Right Offset"), 2, 1)
        g.addWidget(self._box("40", "body_area_right_offset"), 2, 2)

        inner_left.addWidget(grp_body)

        # -------- Direction --------
        grp_dir = self._create_group_box("Direction")
        l = QVBoxLayout(grp_dir)
        l.setSpacing(8)
        l.setContentsMargins(10, 15, 10, 10)

        cb_parallel = self._create_checkbox("Enable Parallel Chip")
        cb_parallel.setObjectName("direction_parallel_enable")
        l.addWidget(cb_parallel)

        cb_non_parallel = self._create_checkbox("Enable None Parallel Chip")
        cb_non_parallel.setObjectName("direction_non_parallel_enable")
        l.addWidget(cb_non_parallel)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self._create_label("Max Parallel Angle Tol"))
        tol_box = self._box("3", "direction_max_parallel_angle_tol")
        tol_box.setAlignment(Qt.AlignCenter)
        row.addWidget(tol_box)
        row.addStretch()
        l.addLayout(row)

        inner_left.addWidget(grp_dir)

        # -------- Pocket Dimension Inspection --------
        grp_dim = self._create_group_box("Pocket Dimension Inspection")
        g = QGridLayout(grp_dim)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.setContentsMargins(10, 15, 10, 10)

        cb_pocket_length = self._create_checkbox("Pocket Length")
        cb_pocket_length.setObjectName("pocket_dim_length_enable")
        g.addWidget(cb_pocket_length, 0, 0)

        cb_pocket_width = self._create_checkbox("Pocket Width")
        cb_pocket_width.setObjectName("pocket_dim_width_enable")
        g.addWidget(cb_pocket_width, 0, 1)

        g.addWidget(self._create_label("Pocket Length"), 1, 0)
        g.addWidget(self._box("100", "pocket_length_min"), 1, 1)
        g.addWidget(self._box("100", "pocket_length_max"), 1, 2)

        g.addWidget(self._create_label("Pocket Width"), 2, 0)
        g.addWidget(self._box("100", "pocket_width_min"), 2, 1)
        g.addWidget(self._box("100", "pocket_width_max"), 2, 2)

        inner_left.addWidget(grp_dim)

        # -------- Pocket Gap Inspection --------
        grp_gap = self._create_group_box("Pocket Gap Inspection")
        g = QGridLayout(grp_gap)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.setContentsMargins(10, 15, 10, 10)

        cb_gap_enable = self._create_checkbox("Enable Pocket Gap")
        cb_gap_enable.setObjectName("pocket_gap_enable")
        g.addWidget(cb_gap_enable, 0, 0)

        cb_gap_4_sides = self._create_checkbox("4 Sides")
        cb_gap_4_sides.setObjectName("pocket_gap_4_sides")
        g.addWidget(cb_gap_4_sides, 0, 1)

        cb_gap_left = self._create_checkbox("Left")
        cb_gap_left.setObjectName("pocket_gap_left_enable")
        g.addWidget(cb_gap_left, 1, 0)

        header_font = QFont()
        header_font.setBold(True)
        
        x_label = QLabel("X")
        x_label.setFont(header_font)
        x_label.setAlignment(Qt.AlignCenter)
        g.addWidget(x_label, 1, 1)
        
        y_label = QLabel("Y")
        y_label.setFont(header_font)
        y_label.setAlignment(Qt.AlignCenter)
        g.addWidget(y_label, 1, 2)

        g.addWidget(self._create_label("Pocket Gap Min"), 2, 0)
        g.addWidget(self._box("2", "pocket_gap_min_x"), 2, 1)
        g.addWidget(self._box("2", "pocket_gap_min_y"), 2, 2)

        inner_left.addWidget(grp_gap)

        # -------- Pocket Shift Log --------
        grp_shift = self._create_group_box("Pocket Shift Log")
        g = QGridLayout(grp_shift)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.setContentsMargins(10, 15, 10, 10)

        cb_shift_enable = self._create_checkbox("Enable")
        cb_shift_enable.setObjectName("pocket_shift_enable")
        g.addWidget(cb_shift_enable, 0, 0)

        pos_label = QLabel("Pos:[0][0]")
        pos_label.setStyleSheet("color: #666; font-style: italic;")
        g.addWidget(pos_label, 0, 1)

        g.addWidget(self._create_label("X(+Ve)"), 1, 0)
        g.addWidget(self._box("50", "pocket_shift_x_pos"), 1, 1)

        g.addWidget(self._create_label("X(-Ve)"), 1, 2)
        g.addWidget(self._box("50", "pocket_shift_x_neg"), 1, 3)

        g.addWidget(self._create_label("Y(+Ve)"), 2, 0)
        g.addWidget(self._box("50", "pocket_shift_y_pos"), 2, 1)

        g.addWidget(self._create_label("Y(-Ve)"), 2, 2)
        g.addWidget(self._box("50", "pocket_shift_y_neg"), 2, 3)

        inner_left.addWidget(grp_shift)
        inner_left.addStretch()

        # ==================================================
        # INNER RIGHT GROUPS
        # ==================================================
        # -------- Paper Dust Mask --------
        grp_paper = self._create_group_box("Paper Dust Mask")
        g = QGridLayout(grp_paper)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.setContentsMargins(10, 15, 10, 10)

        cb_paper_lr = self._create_checkbox("Left & Right")
        cb_paper_lr.setObjectName("paper_dust_left_right")
        g.addWidget(cb_paper_lr, 0, 0)

        cb_paper_tb = self._create_checkbox("Top & Bottom")
        cb_paper_tb.setObjectName("paper_dust_top_bottom")
        g.addWidget(cb_paper_tb, 0, 1)

        cb_paper_contrast = self._create_checkbox("Contrast+")
        cb_paper_contrast.setObjectName("paper_dust_contrast_plus")
        g.addWidget(cb_paper_contrast, 1, 0)

        inner_right.addWidget(grp_paper)

        # -------- Outer Pocket Stain Inspection --------
        grp_outer = self._create_group_box("Outer Pocket Stain Inspection")
        g = QGridLayout(grp_outer)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.setContentsMargins(10, 15, 10, 10)

        cb_outer_black = self._create_checkbox("Black")
        cb_outer_black.setObjectName("outer_stain_black")
        g.addWidget(cb_outer_black, 0, 0)

        cb_outer_white = self._create_checkbox("White")
        cb_outer_white.setObjectName("outer_stain_white")
        g.addWidget(cb_outer_white, 0, 1)

        g.addWidget(self._create_label("Contrast"), 1, 0)
        g.addWidget(self._box("10", "outer_stain_contrast_min"), 1, 1)
        g.addWidget(self._box("170", "outer_stain_contrast_max"), 1, 2)

        g.addWidget(self._create_label("Min Area"), 2, 0)
        g.addWidget(self._box("20", "outer_stain_min_area"), 2, 1)

        g.addWidget(self._create_label("Min Sq Size"), 3, 0)
        g.addWidget(self._box("5", "outer_stain_min_sq_size"), 3, 1)

        inner_right.addWidget(grp_outer)

        # -------- Inspection Width --------
        grp_w = self._create_group_box("Inspection Width")
        gw = QGridLayout(grp_w)
        gw.setHorizontalSpacing(10)
        gw.setVerticalSpacing(8)
        gw.setContentsMargins(10, 15, 10, 10)

        gw.addWidget(self._create_label("Left"), 0, 0)
        gw.addWidget(self._box("20", "inspect_width_left"), 0, 1)

        gw.addWidget(self._create_label("Top"), 0, 2)
        gw.addWidget(self._box("20", "inspect_width_top"), 0, 3)

        gw.addWidget(self._create_label("Right"), 1, 0)
        gw.addWidget(self._box("20", "inspect_width_right"), 1, 1)

        gw.addWidget(self._create_label("Bottom"), 1, 2)
        gw.addWidget(self._box("20", "inspect_width_bottom"), 1, 3)

        inner_right.addWidget(grp_w)

        # -------- Inspection Offset --------
        grp_o = self._create_group_box("Inspection Offset")
        go = QGridLayout(grp_o)
        go.setHorizontalSpacing(10)
        go.setVerticalSpacing(8)
        go.setContentsMargins(10, 15, 10, 10)

        go.addWidget(self._create_label("Left"), 0, 0)
        go.addWidget(self._box("10", "inspect_offset_left"), 0, 1)

        go.addWidget(self._create_label("Top"), 0, 2)
        go.addWidget(self._box("10", "inspect_offset_top"), 0, 3)

        go.addWidget(self._create_label("Right"), 1, 0)
        go.addWidget(self._box("10", "inspect_offset_right"), 1, 1)

        go.addWidget(self._create_label("Bottom"), 1, 2)
        go.addWidget(self._box("10", "inspect_offset_bottom"), 1, 3)

        inner_right.addWidget(grp_o)

        # -------- White Line Mask --------
        grp_white = self._create_group_box("White Line Mask")
        g = QGridLayout(grp_white)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.setContentsMargins(10, 15, 10, 10)

        cb_white_enable = self._create_checkbox("Enable")
        cb_white_enable.setObjectName("white_line_mask_enable")
        g.addWidget(cb_white_enable, 0, 0)

        g.addWidget(self._create_label("Mask Size"), 1, 0)
        g.addWidget(self._box("1", "white_line_mask_size"), 1, 1)

        inner_right.addWidget(grp_white)

        # -------- Emboss Tape Pick Up --------
        grp_emboss = self._create_group_box("Emboss Tape Pick Up")
        g = QGridLayout(grp_emboss)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.setContentsMargins(10, 15, 10, 10)

        cb_emboss_enable = self._create_checkbox("Enable Emboss Tape Pick Up")
        cb_emboss_enable.setObjectName("emboss_tape_pickup_enable")
        g.addWidget(cb_emboss_enable, 0, 0, 1, 2)

        g.addWidget(self._create_label("Contrast"), 1, 0)
        g.addWidget(self._box("100", "emboss_tape_contrast"), 1, 1)

        g.addWidget(self._create_label("Left Search Offset"), 2, 0)
        g.addWidget(self._box("50", "emboss_tape_left_search_offset"), 2, 1)

        inner_right.addWidget(grp_emboss)
        inner_right.addStretch()

        # ==================================================
        # RIGHT SIDE – Sealing / Dent Inspection
        # ==================================================
        right_col = QVBoxLayout()
        right_col.setSpacing(15)
        main_row.addLayout(right_col, 1)

        # ---------- Sealing Stain Inspection ----------
        grp_seal = self._create_group_box("Sealing Stain Inspection")
        g = QGridLayout(grp_seal)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.setContentsMargins(10, 15, 10, 10)

        cb_seal_enable = self._create_checkbox("Enable")
        cb_seal_enable.setObjectName("sealing_stain_enable")
        g.addWidget(cb_seal_enable, 0, 0)

        cb_seal_auto = self._create_checkbox("Enable Auto Adjust")
        cb_seal_auto.setObjectName("sealing_stain_auto_adjust")
        g.addWidget(cb_seal_auto, 0, 1)

        g.addWidget(self._create_label("Contrast Left"), 1, 0)
        g.addWidget(self._box("180", "sealing_stain_contrast_left"), 1, 1)

        g.addWidget(self._create_label("Right"), 1, 2)
        g.addWidget(self._box("180", "sealing_stain_contrast_right"), 1, 3)

        g.addWidget(self._create_label("Filter Contrast"), 2, 0)
        g.addWidget(self._box("50", "sealing_stain_filter_contrast"), 2, 1)

        g.addWidget(self._create_label("Min Area"), 3, 0)
        g.addWidget(self._box("20", "sealing_stain_min_area"), 3, 1)

        g.addWidget(self._create_label("Min Sq Size"), 4, 0)
        g.addWidget(self._box("5", "sealing_stain_min_sq_size"), 4, 1)

        # ---- Inspection Width ----
        grp_w = self._create_sub_group("Inspection Width")
        gw = QGridLayout(grp_w)
        gw.setHorizontalSpacing(10)
        gw.setVerticalSpacing(6)
        gw.setContentsMargins(8, 12, 8, 8)

        gw.addWidget(self._create_label("Left"), 0, 0)
        gw.addWidget(self._box("60", "sealing_width_left"), 0, 1)

        gw.addWidget(self._create_label("Top"), 0, 2)
        gw.addWidget(self._box("70", "sealing_width_top"), 0, 3)

        gw.addWidget(self._create_label("Right"), 1, 0)
        gw.addWidget(self._box("60", "sealing_width_right"), 1, 1)

        gw.addWidget(self._create_label("Bottom"), 1, 2)
        gw.addWidget(self._box("70", "sealing_width_bottom"), 1, 3)

        # ---- Inspection Offset ----
        grp_o = self._create_sub_group("Inspection Offset")
        go = QGridLayout(grp_o)
        go.setHorizontalSpacing(10)
        go.setVerticalSpacing(6)
        go.setContentsMargins(8, 12, 8, 8)

        go.addWidget(self._create_label("Left"), 0, 0)
        go.addWidget(self._box("65", "sealing_offset_left"), 0, 1)

        go.addWidget(self._create_label("Right"), 0, 2)
        go.addWidget(self._box("45", "sealing_offset_right"), 0, 3)

        g.addWidget(grp_w, 5, 0, 1, 4)
        g.addWidget(grp_o, 6, 0, 1, 4)

        right_col.addWidget(grp_seal)

        # ---------- Sealing Stain2 Inspection ----------
        grp_seal2 = self._create_group_box("Sealing Stain2 Inspection")
        g = QGridLayout(grp_seal2)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.setContentsMargins(10, 15, 10, 10)

        cb_seal2_enable = self._create_checkbox("Enable Sealing Stain2")
        cb_seal2_enable.setObjectName("sealing_stain2_enable")
        g.addWidget(cb_seal2_enable, 0, 0)

        g.addWidget(self._create_label("Contrast"), 1, 0)
        g.addWidget(self._box("255", "sealing_stain2_contrast"), 1, 1)

        g.addWidget(self._create_label("Min Area"), 2, 0)
        g.addWidget(self._box("20", "sealing_stain2_min_area"), 2, 1)

        g.addWidget(self._create_label("Min Sq Size"), 3, 0)
        g.addWidget(self._box("5", "sealing_stain2_min_sq_size"), 3, 1)

        # ---- Inspection Width ----
        grp_w2 = self._create_sub_group("Inspection Width")
        gw2 = QGridLayout(grp_w2)
        gw2.setHorizontalSpacing(10)
        gw2.setVerticalSpacing(6)
        gw2.setContentsMargins(8, 12, 8, 8)

        gw2.addWidget(self._create_label("Left"), 0, 0)
        gw2.addWidget(self._box("25", "sealing2_width_left"), 0, 1)

        gw2.addWidget(self._create_label("Right"), 1, 0)
        gw2.addWidget(self._box("35", "sealing2_width_right"), 1, 1)

        gw2.addWidget(self._create_label("Top"), 2, 0)
        gw2.addWidget(self._box("100", "sealing2_width_top"), 2, 1)

        gw2.addWidget(self._create_label("Bottom"), 3, 0)
        gw2.addWidget(self._box("100", "sealing2_width_bottom"), 3, 1)

        # ---- Inspection Offset ----
        grp_o2 = self._create_sub_group("Inspection Offset")
        go2 = QGridLayout(grp_o2)
        go2.setHorizontalSpacing(10)
        go2.setVerticalSpacing(6)
        go2.setContentsMargins(8, 12, 8, 8)

        go2.addWidget(self._create_label("Top"), 0, 0)
        go2.addWidget(self._box("0", "sealing2_offset_top"), 0, 1)

        go2.addWidget(self._create_label("Bottom"), 1, 0)
        go2.addWidget(self._box("5", "sealing2_offset_bottom"), 1, 1)

        g.addWidget(grp_w2, 4, 0, 1, 2)
        g.addWidget(grp_o2, 5, 0, 1, 2)

        right_col.addWidget(grp_seal2)

        # ---------- Sealing Shift Inspection ----------
        grp_shift = self._create_group_box("Sealing Shift Inspection")
        g = QGridLayout(grp_shift)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.setContentsMargins(10, 15, 10, 10)

        cb_seal_shift_enable = self._create_checkbox("Enable")
        cb_seal_shift_enable.setObjectName("sealing_shift_enable")
        g.addWidget(cb_seal_shift_enable, 0, 0)

        cb_bw_scar = self._create_checkbox("Black To White Scar")
        cb_bw_scar.setObjectName("sealing_shift_black_to_white_scar")
        g.addWidget(cb_bw_scar, 0, 1)

        cb_hole_ref = self._create_checkbox("Hole Ref")
        cb_hole_ref.setObjectName("sealing_shift_hole_ref")
        g.addWidget(cb_hole_ref, 1, 0)

        cb_wb_scar = self._create_checkbox("White To Black Scar")
        cb_wb_scar.setObjectName("sealing_shift_white_to_black_scar")
        g.addWidget(cb_wb_scar, 1, 1)

        g.addWidget(self._create_label("Cover Tape Dist"), 2, 0)
        g.addWidget(self._box("59", "sealing_shift_cover_tape_min"), 2, 1)
        g.addWidget(self._box("435", "sealing_shift_cover_tape_max"), 2, 2)

        g.addWidget(self._create_label("Sealing Mark Dist"), 3, 0)
        g.addWidget(self._box("190", "sealing_shift_mark_min"), 3, 1)
        g.addWidget(self._box("306", "sealing_shift_mark_max"), 3, 2)

        g.addWidget(self._create_label("Contrast"), 4, 0)
        g.addWidget(self._box("245", "sealing_shift_contrast_primary"), 4, 1)
        g.addWidget(self._box("180", "sealing_shift_contrast_secondary"), 4, 2)

        g.addWidget(self._create_label("Tolerance"), 5, 0)
        g.addWidget(self._box("25", "sealing_shift_tolerance_pos"), 5, 1)
        g.addWidget(self._box("25", "sealing_shift_tolerance_neg"), 5, 2)

        g.addWidget(self._create_label("Left Search Offset"), 6, 0)
        g.addWidget(self._box("40", "sealing_shift_left_search_offset"), 6, 1)

        g.addWidget(self._create_label("Top Search Offset"), 7, 0)
        g.addWidget(self._box("90", "sealing_shift_top_search_offset"), 7, 1)

        hole_label = self._create_label("Hole Side Shift")
        hole_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding-top: 8px;")
        g.addWidget(hole_label, 8, 0)

        g.addWidget(self._create_label("Contrast"), 9, 0)
        g.addWidget(self._box("123", "sealing_shift_hole_contrast"), 9, 1)

        g.addWidget(self._create_label("Min Width"), 9, 2)
        g.addWidget(self._box("102", "sealing_shift_hole_min_width"), 9, 3)

        g.addWidget(self._create_label("Offset"), 10, 0)
        g.addWidget(self._box("15", "sealing_shift_hole_offset"), 10, 1)

        g.addWidget(self._create_label("Edge Count"), 10, 2)
        g.addWidget(self._box("50", "sealing_shift_hole_edge_count"), 10, 3)

        right_col.addWidget(grp_shift)

        # ---------- Bottom Dent Inspection ----------
        grp_dent = self._create_group_box("Bottom Dent Inspection")
        g = QGridLayout(grp_dent)
        g.setHorizontalSpacing(10)
        g.setVerticalSpacing(8)
        g.setContentsMargins(10, 15, 10, 10)

        cb_dent_enable = self._create_checkbox("Enable Bottom Dent")
        cb_dent_enable.setObjectName("bottom_dent_enable")
        g.addWidget(cb_dent_enable, 0, 0)

        g.addWidget(self._create_label("Contrast"), 1, 0)
        g.addWidget(self._box("255", "bottom_dent_contrast"), 1, 1)

        g.addWidget(self._create_label("Min Area"), 2, 0)
        g.addWidget(self._box("20", "bottom_dent_min_area"), 2, 1)

        g.addWidget(self._create_label("Min Sq Size"), 3, 0)
        g.addWidget(self._box("5", "bottom_dent_min_sq_size"), 3, 1)

        g.addWidget(self._create_label("Empty Intensity Min"), 4, 0)
        g.addWidget(self._box("120", "bottom_dent_empty_intensity_min"), 4, 1)

        g.addWidget(self._create_label("Max"), 4, 2)
        g.addWidget(self._box("220", "bottom_dent_empty_intensity_max"), 4, 3)

        # ---- Inspection Offset ----
        grp_o3 = self._create_sub_group("Inspection Offset")
        go3 = QGridLayout(grp_o3)
        go3.setHorizontalSpacing(10)
        go3.setVerticalSpacing(6)
        go3.setContentsMargins(8, 12, 8, 8)

        go3.addWidget(self._create_label("L"), 0, 0)
        go3.addWidget(self._box("15", "bottom_dent_offset_left"), 0, 1)

        go3.addWidget(self._create_label("R"), 0, 2)
        go3.addWidget(self._box("15", "bottom_dent_offset_right"), 0, 3)

        go3.addWidget(self._create_label("T"), 1, 0)
        go3.addWidget(self._box("15", "bottom_dent_offset_top"), 1, 1)

        go3.addWidget(self._create_label("B"), 1, 2)
        go3.addWidget(self._box("15", "bottom_dent_offset_bottom"), 1, 3)

        g.addWidget(grp_o3, 5, 0, 1, 4)

        # ---- Search Edge Offset ----
        grp_search = self._create_sub_group("Search Edge Offset")
        gs = QGridLayout(grp_search)
        gs.setHorizontalSpacing(10)
        gs.setVerticalSpacing(6)
        gs.setContentsMargins(8, 12, 8, 8)

        gs.addWidget(self._create_label("X"), 0, 0)
        gs.addWidget(self._box("20", "bottom_dent_search_offset_x"), 0, 1)

        gs.addWidget(self._create_label("Y"), 0, 2)
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
        btn_close.setObjectName("closeButton")
        
        # Set fixed button sizes for consistency
        btn_ok.setFixedSize(90, 32)
        btn_apply.setFixedSize(90, 32)
        btn_close.setFixedSize(90, 32)
        
        btn_ok.clicked.connect(lambda: self.save_to_json("pocket_params.json"))
        btn_apply.clicked.connect(lambda: self.save_to_json("pocket_params.json"))
        btn_close.clicked.connect(self.close)

        btn_row.addWidget(btn_apply)
        btn_row.addSpacing(10)
        btn_row.addWidget(btn_ok)
        btn_row.addSpacing(10)
        btn_row.addWidget(btn_close)

        root.addLayout(btn_row)

    # =================================================
    # HELPER METHODS
    # =================================================
    def _create_group_box(self, title):
        """Create a styled group box"""
        grp = QGroupBox(title)
        grp.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
            }
        """)
        return grp

    def _create_sub_group(self, title):
        """Create a styled sub-group box"""
        grp = QGroupBox(title)
        grp.setStyleSheet("""
            QGroupBox {
                font-weight: normal;
                font-size: 11px;
                border: 1px solid #dddddd;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 8px;
                background-color: #f9f9f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                color: #555555;
            }
        """)
        return grp

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
            }
            QCheckBox::indicator:hover {
                border: 1px solid #3498db;
            }
        """)
        return checkbox

    def _box(self, text, name=None):
        """Create a styled input box"""
        e = QLineEdit(text)
        e.setFixedWidth(60)
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