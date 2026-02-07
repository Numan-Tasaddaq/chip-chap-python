"""
Mark Inspect Parameters Dialog

This dialog allows configuration of mark inspection parameters including:
- Symbol Shift settings
- Symbol Characteristics
- Mark Hole Inspection
- Symbol Inspection parameters
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSpinBox, QCheckBox, QComboBox, QPushButton,
    QMessageBox, QWidget, QGridLayout
)
from PySide6.QtCore import Qt
from config.mark_inspection_io import (
    load_mark_inspection_config,
    save_mark_inspection_config,
    MarkSymbolSetConfig
)


class MarkParametersDialog(QDialog):
    """Mark Inspect Parameters Dialog matching old C++ CMarkSymbolsDlg"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mark Inspect Parameters")
        self.setMinimumWidth(540)
        self.setMinimumHeight(480)
        
        # Create UI
        self._build_ui()
        
        # Load current configuration
        self._load_config()
    
    def _build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Mark Set selector
        mark_set_layout = QHBoxLayout()
        mark_set_label = QLabel("Mark Set")
        mark_set_label.setToolTip(
            "Select mark inspection parameter set:\n"
            "• Mark Set 1: Primary template parameters\n"
            "• Mark Set 2: Alternative template set\n"
            "• Mark Set 3: Additional template set\n"
            "• Each set can have different parameters"
        )
        mark_set_layout.addWidget(mark_set_label)
        self.mark_set_combo = QComboBox()
        self.mark_set_combo.addItems(["Mark Set 1", "Mark Set 2", "Mark Set 3"])
        self.mark_set_combo.setCurrentIndex(0)
        self.mark_set_combo.setToolTip(
            "Switch between different mark template sets\n"
            "Each set maintains its own configuration"
        )
        self.mark_set_combo.currentIndexChanged.connect(self._on_mark_set_changed)
        mark_set_layout.addWidget(self.mark_set_combo)
        mark_set_layout.addStretch()
        layout.addLayout(mark_set_layout)
        
        # Top row: Symbol Shift, Symbol Characteristics, Mark Hole Inspection
        top_layout = QHBoxLayout()
        
        # Symbol Shift group
        symbol_shift_group = QGroupBox("Symbol Shift")
        symbol_shift_layout = QGridLayout()
        
        self.user_define_window_cb = QCheckBox("User Define Teach Window")
        self.user_define_window_cb.setToolTip(
            "Enable/disable user-defined teach windows:\n"
            "• Checked: User manually defines regions\n"
            "• Unchecked: System auto-detects regions"
        )
        symbol_shift_layout.addWidget(self.user_define_window_cb, 0, 0, 1, 4)
        
        rotation_label = QLabel("Mark Rotation Tol")
        rotation_label.setToolTip(
            "Maximum allowable mark rotation:\n"
            "• In degrees (0-360)\n"
            "• Generates rotated templates for matching\n"
            "• Larger = handles more rotation variance\n"
            "• Default: 5°"
        )
        symbol_shift_layout.addWidget(rotation_label, 1, 0)
        self.mark_rotation_spin = QSpinBox()
        self.mark_rotation_spin.setRange(0, 360)
        self.mark_rotation_spin.setValue(5)
        self.mark_rotation_spin.setSuffix("°")
        self.mark_rotation_spin.setToolTip(
            "Range: 0-360 degrees\n"
            "Sets mark rotation tolerance"
        )
        symbol_shift_layout.addWidget(self.mark_rotation_spin, 1, 1)
        
        first_shift_label = QLabel("First Template Shift Tol")
        first_shift_label.setToolTip(
            "Search window expansion for first template:\n"
            "• Used in template matching\n"
            "• Larger = wider search area\n"
            "• Applied as InflateRect(X, Y)\n"
            "• Default: X=25, Y=25 pixels"
        )
        symbol_shift_layout.addWidget(first_shift_label, 2, 0)
        symbol_shift_layout.addWidget(QLabel("X:"), 2, 1)
        self.first_shift_x_spin = QSpinBox()
        self.first_shift_x_spin.setRange(0, 500)
        self.first_shift_x_spin.setValue(25)
        self.first_shift_x_spin.setToolTip(
            "X-axis shift tolerance (pixels)\n"
            "Expands search window left/right"
        )
        symbol_shift_layout.addWidget(self.first_shift_x_spin, 2, 2)
        
        symbol_shift_layout.addWidget(QLabel("Y:"), 2, 3)
        self.first_shift_y_spin = QSpinBox()
        self.first_shift_y_spin.setRange(0, 500)
        self.first_shift_y_spin.setValue(25)
        self.first_shift_y_spin.setToolTip(
            "Y-axis shift tolerance (pixels)\n"
            "Expands search window up/down"
        )
        symbol_shift_layout.addWidget(self.first_shift_y_spin, 2, 4)
        
        other_shift_label = QLabel("Other Template Shift Tol")
        other_shift_label.setToolTip(
            "Search window for templates after first:\n"
            "• Used for subsequent template matching\n"
            "• Typically smaller than first template\n"
            "• Default: X=10, Y=10 pixels"
        )
        symbol_shift_layout.addWidget(other_shift_label, 3, 0)
        symbol_shift_layout.addWidget(QLabel("X:"), 3, 1)
        self.other_shift_x_spin = QSpinBox()
        self.other_shift_x_spin.setRange(0, 500)
        self.other_shift_x_spin.setValue(10)
        self.other_shift_x_spin.setToolTip(
            "X-axis shift for other templates (pixels)\n"
            "Expands search window left/right"
        )
        symbol_shift_layout.addWidget(self.other_shift_x_spin, 3, 2)
        
        symbol_shift_layout.addWidget(QLabel("Y:"), 3, 3)
        self.other_shift_y_spin = QSpinBox()
        self.other_shift_y_spin.setRange(0, 500)
        self.other_shift_y_spin.setValue(10)
        self.other_shift_y_spin.setToolTip(
            "Y-axis shift for other templates (pixels)\n"
            "Expands search window up/down"
        )
        symbol_shift_layout.addWidget(self.other_shift_y_spin, 3, 4)
        
        symbol_shift_group.setLayout(symbol_shift_layout)
        top_layout.addWidget(symbol_shift_group)
        
        # Symbol Characteristics group
        symbol_char_group = QGroupBox("Symbol Characteristics")
        symbol_char_layout = QGridLayout()
        
        # Mark Color
        mark_color_label = QLabel("Mark Color")
        mark_color_label.setToolTip(
            "Color of the mark to detect:\n"
            "• White: Bright marks on dark background\n"
            "• Black: Dark marks on bright background\n"
            "This affects the thresholding algorithm"
        )
        symbol_char_layout.addWidget(mark_color_label, 0, 0)
        self.mark_color_combo = QComboBox()
        self.mark_color_combo.addItems(["White", "Black"])
        self.mark_color_combo.setCurrentIndex(0)
        self.mark_color_combo.setToolTip(
            "Select mark color:\n"
            "White: Binary threshold keeps white pixels\n"
            "Black: Binary threshold keeps black pixels"
        )
        symbol_char_layout.addWidget(self.mark_color_combo, 0, 1)
        
        # Total Teach Rectangle
        teach_rect_label = QLabel("Total Teach Rectangle")
        teach_rect_label.setToolTip(
            "Number of teaching regions for the mark:\n"
            "• 1: Single rectangular region\n"
            "• 2-4: Multiple regions (for complex marks)\n"
            "Sets the teach quantity for mark detection"
        )
        symbol_char_layout.addWidget(teach_rect_label, 1, 0)
        self.teach_rect_spin = QSpinBox()
        self.teach_rect_spin.setRange(1, 4)
        self.teach_rect_spin.setValue(1)
        self.teach_rect_spin.setToolTip(
            "Range: 1-4 rectangles\n"
            "More rectangles = more flexible mark detection\n"
            "Default: 1 (simple rectangular mark)"
        )
        symbol_char_layout.addWidget(self.teach_rect_spin, 1, 1)
        
        # Min Character Size
        min_char_label = QLabel("Min Character Size")
        min_char_label.setToolTip(
            "Minimum size of character for blob detection:\n"
            "• Used in blob segmentation algorithm\n"
            "• Smaller value = detects finer details\n"
            "• Larger value = ignores small noise\n"
            "Default: 10 pixels"
        )
        symbol_char_layout.addWidget(min_char_label, 2, 0)
        self.min_char_size_spin = QSpinBox()
        self.min_char_size_spin.setRange(1, 100)
        self.min_char_size_spin.setValue(10)
        self.min_char_size_spin.setToolTip(
            "Minimum character size in pixels\n"
            "Used for blob filtering in detection"
        )
        symbol_char_layout.addWidget(self.min_char_size_spin, 2, 1)
        
        # Mark Min X Size
        mark_min_x_label = QLabel("Mark Min X Size")
        mark_min_x_label.setToolTip(
            "Minimum X dimension of mark:\n"
            "• Filters out blobs smaller than this width\n"
            "• Used in blob validation\n"
            "• Default: 10 pixels"
        )
        symbol_char_layout.addWidget(mark_min_x_label, 3, 0)
        self.mark_min_x_spin = QSpinBox()
        self.mark_min_x_spin.setRange(1, 100)
        self.mark_min_x_spin.setValue(10)
        self.mark_min_x_spin.setToolTip(
            "Minimum X dimension (pixels)\n"
            "Rejects marks narrower than this value"
        )
        symbol_char_layout.addWidget(self.mark_min_x_spin, 3, 1)
        
        # Mark Min Y Size
        mark_min_y_label = QLabel("Mark Min Y Size")
        mark_min_y_label.setToolTip(
            "Minimum Y dimension of mark:\n"
            "• Filters out blobs smaller than this height\n"
            "• Used in blob validation\n"
            "• Default: 10 pixels"
        )
        symbol_char_layout.addWidget(mark_min_y_label, 4, 0)
        self.mark_min_y_spin = QSpinBox()
        self.mark_min_y_spin.setRange(1, 100)
        self.mark_min_y_spin.setValue(10)
        self.mark_min_y_spin.setToolTip(
            "Minimum Y dimension (pixels)\n"
            "Rejects marks shorter than this value"
        )
        symbol_char_layout.addWidget(self.mark_min_y_spin, 4, 1)
        
        symbol_char_group.setLayout(symbol_char_layout)
        top_layout.addWidget(symbol_char_group)
        
        # Mark Hole Inspection group
        mark_hole_group = QGroupBox("Mark Hole Inspection")
        mark_hole_layout = QGridLayout()
        
        self.hole_check_cb = QCheckBox("Hole Check")
        self.hole_check_cb.setToolTip(
            "Enable/disable mark hole verification:\n"
            "• Checked: Detects black regions (holes)\n"
            "• Unchecked: Skips hole inspection\n"
            "• Used for cavity or via detection\n"
            "• When enabled, shows contrast parameters"
        )
        mark_hole_layout.addWidget(self.hole_check_cb, 0, 0, 1, 2)
        self.hole_check_cb.stateChanged.connect(self._on_hole_check_changed)
        
        teach_contrast_label = QLabel("Teach Mark Contrast")
        teach_contrast_label.setToolTip(
            "Threshold for detecting holes during teaching:\n"
            "• Used when creating mark hole templates\n"
            "• MUST NOT exceed Insp Mark Contrast\n"
            "• If teach > insp → hole inspection fails\n"
            "• Range: 0-255 (default: 100)\n"
            "• Higher value = only darker holes detected"
        )
        mark_hole_layout.addWidget(teach_contrast_label, 1, 0)
        self.teach_mark_contrast_spin = QSpinBox()
        self.teach_mark_contrast_spin.setRange(0, 255)
        self.teach_mark_contrast_spin.setValue(100)
        self.teach_mark_contrast_spin.setToolTip(
            "Must be ≤ Insp Mark Contrast\n"
            "Higher = stricter hole detection"
        )
        self.teach_mark_contrast_spin.valueChanged.connect(self._validate_contrast_values)
        mark_hole_layout.addWidget(self.teach_mark_contrast_spin, 1, 1)
        
        insp_contrast_label = QLabel("Insp Mark Contrast")
        insp_contrast_label.setToolTip(
            "Threshold for detecting holes during inspection:\n"
            "• Used when checking parts for holes\n"
            "• Optimal range: 120-130\n"
            "• If value too high → holes missed\n"
            "• If value too low → false hole detection\n"
            "• Default: 130"
        )
        mark_hole_layout.addWidget(insp_contrast_label, 2, 0)
        self.insp_mark_contrast_spin = QSpinBox()
        self.insp_mark_contrast_spin.setRange(0, 255)
        self.insp_mark_contrast_spin.setValue(130)
        self.insp_mark_contrast_spin.setToolTip(
            "Range: 120-130 is correct\n"
            "Teach Contrast cannot exceed this"
        )
        self.insp_mark_contrast_spin.valueChanged.connect(self._validate_contrast_values)
        mark_hole_layout.addWidget(self.insp_mark_contrast_spin, 2, 1)
        
        min_area_label = QLabel("Mark Min Area")
        min_area_label.setToolTip(
            "Minimum hole area for recognition:\n"
            "• System generates mark area parameter\n"
            "• Blobs smaller than this ignored (noise)\n"
            "• If set too high → holes NOT detected\n"
            "• If set too low → false detections\n"
            "• Default: 4 pixels²"
        )
        mark_hole_layout.addWidget(min_area_label, 3, 0)
        self.mark_min_area_spin = QSpinBox()
        self.mark_min_area_spin.setRange(1, 1000)
        self.mark_min_area_spin.setValue(4)
        self.mark_min_area_spin.setToolTip(
            "Minimum pixels² for hole recognition\n"
            "Prevents noise from being detected"
        )
        mark_hole_layout.addWidget(self.mark_min_area_spin, 3, 1)
        
        min_xy_label = QLabel("Mark Min XY Size")
        min_xy_label.setToolTip(
            "Minimum hole dimensions:\n"
            "• Sets minimum X and Y pixel size\n"
            "• Both dimensions must meet requirement\n"
            "• Prevents detection of line-like defects\n"
            "• Default: 3 pixels (width & height)"
        )
        mark_hole_layout.addWidget(min_xy_label, 4, 0)
        self.mark_min_xy_size_spin = QSpinBox()
        self.mark_min_xy_size_spin.setRange(1, 100)
        self.mark_min_xy_size_spin.setValue(3)
        self.mark_min_xy_size_spin.setToolTip(
            "Minimum width/height in pixels\n"
            "Filters thin/elongated marks"
        )
        mark_hole_layout.addWidget(self.mark_min_xy_size_spin, 4, 1)
        
        mark_hole_group.setLayout(mark_hole_layout)
        top_layout.addWidget(mark_hole_group)
        
        layout.addLayout(top_layout)
        
        # Symbol Inspection group
        symbol_insp_group = QGroupBox("Symbol Inspection")
        symbol_insp_layout = QVBoxLayout()
        
        self.separate_params_cb = QCheckBox("Separate Parameters For First Template")
        self.separate_params_cb.setToolTip(
            "Use different parameters for first template:\n"
            "• Checked: First template has own settings\n"
            "• Unchecked: All templates use same parameters\n"
            "• Useful when first mark differs significantly\n"
            "• Allows fine-tuning per template type"
        )
        symbol_insp_layout.addWidget(self.separate_params_cb)
        self.separate_params_cb.stateChanged.connect(self._on_separate_params_changed)
        
        # First Template and Template in horizontal layout
        templates_layout = QHBoxLayout()
        
        # First Template group
        first_template_group = QGroupBox("First Template")
        first_template_layout = QGridLayout()
        
        self.first_gross_check_cb = QCheckBox("Do Gross Check Only")
        self.first_gross_check_cb.setToolTip(
            "Check only gross features (fast detection)\n"
            "Skips detailed mismatch analysis"
        )
        first_template_layout.addWidget(self.first_gross_check_cb, 0, 0, 1, 3)
        
        accept_label = QLabel("Accept Score")
        accept_label.setToolTip(
            "Confidence threshold for PASS:\n"
            "• If match score ≥ Accept Score → PASS\n"
            "• Higher value = stricter matching\n"
            "• System finds mark defects vs this score\n"
            "• Default: 85%"
        )
        first_template_layout.addWidget(accept_label, 1, 0)
        self.first_accept_score_spin = QSpinBox()
        self.first_accept_score_spin.setRange(0, 100)
        self.first_accept_score_spin.setValue(85)
        self.first_accept_score_spin.setSuffix(" %")
        self.first_accept_score_spin.setToolTip(
            "Range: 0-100%\n"
            "Must be > Reject Score\n"
            "Score ≥ this → PASS, Score ≤ Reject → FAIL"
        )
        first_template_layout.addWidget(self.first_accept_score_spin, 1, 1)
        
        reject_label = QLabel("Reject Score")
        reject_label.setToolTip(
            "Confidence threshold for FAIL:\n"
            "• If match score ≤ Reject Score → FAIL\n"
            "• Between Reject and Accept = UNCERTAIN\n"
            "• Lower value = more lenient matching\n"
            "• Default: 40%"
        )
        first_template_layout.addWidget(reject_label, 2, 0)
        self.first_reject_score_spin = QSpinBox()
        self.first_reject_score_spin.setRange(0, 100)
        self.first_reject_score_spin.setValue(40)
        self.first_reject_score_spin.setSuffix(" %")
        self.first_reject_score_spin.setToolTip(
            "Range: 0-100%\n"
            "Must be < Accept Score\n"
            "System decides: PASS/FAIL based on these"
        )
        first_template_layout.addWidget(self.first_reject_score_spin, 2, 1)
        
        excess_label = QLabel("Mismatch Excess Area")
        excess_label.setToolTip(
            "Maximum excess area allowed:\n"
            "• Gray level between body and mark defects\n"
            "• Detected excess pixels vs expected\n"
            "• Higher = more tolerance for excess\n"
            "• Default: 5 pixels"
        )
        first_template_layout.addWidget(excess_label, 3, 0)
        self.first_excess_area_spin = QSpinBox()
        self.first_excess_area_spin.setRange(0, 1000)
        self.first_excess_area_spin.setValue(5)
        self.first_excess_area_spin.setSuffix(" Pix")
        self.first_excess_area_spin.setToolTip(
            "Maximum excess area in pixels\n"
            "Gray level between body and mark"
        )
        first_template_layout.addWidget(self.first_excess_area_spin, 3, 1)
        
        missing_label = QLabel("Mismatch Missing Area")
        missing_label.setToolTip(
            "Acceptable mark loss:\n"
            "• Marks can have missing areas\n"
            "• Missing pixels loss of area\n"
            "• Higher = more tolerance for loss\n"
            "• Default: 5 pixels"
        )
        first_template_layout.addWidget(missing_label, 4, 0)
        self.first_missing_area_spin = QSpinBox()
        self.first_missing_area_spin.setRange(0, 1000)
        self.first_missing_area_spin.setValue(5)
        self.first_missing_area_spin.setSuffix(" Pix")
        self.first_missing_area_spin.setToolTip(
            "Acceptable mark loss in pixels\n"
            "Loss of the area is allowed"
        )
        first_template_layout.addWidget(self.first_missing_area_spin, 4, 1)
        
        method_label = QLabel("Mismatch Detect Method")
        method_label.setToolTip(
            "Algorithm for mismatch detection:\n"
            "• Square Area: Compare bounding box areas\n"
            "• Blob Area: Compare actual pixel areas\n"
            "Default: Square Area"
        )
        first_template_layout.addWidget(method_label, 5, 0)
        self.first_detect_method_combo = QComboBox()
        self.first_detect_method_combo.addItems(["Square Area", "Blob Area"])
        self.first_detect_method_combo.setToolTip(
            "Square Area: Bounding box comparison\n"
            "Blob Area: Actual pixel comparison"
        )
        first_template_layout.addWidget(self.first_detect_method_combo, 5, 1)
        
        first_template_group.setLayout(first_template_layout)
        templates_layout.addWidget(first_template_group)
        
        # Template group
        template_group = QGroupBox("Template")
        template_layout = QGridLayout()
        
        self.template_gross_check_cb = QCheckBox("Do Gross Check Only")
        self.template_gross_check_cb.setToolTip(
            "Check only gross features (fast detection)\n"
            "Skips detailed mismatch analysis"
        )
        template_layout.addWidget(self.template_gross_check_cb, 0, 0, 1, 3)
        
        template_accept_label = QLabel("Accept Score")
        template_accept_label.setToolTip(
            "Confidence threshold for PASS:\n"
            "• If match score ≥ Accept Score → PASS\n"
            "• Applied to all templates except first\n"
            "• Default: 85%"
        )
        template_layout.addWidget(template_accept_label, 1, 0)
        self.template_accept_score_spin = QSpinBox()
        self.template_accept_score_spin.setRange(0, 100)
        self.template_accept_score_spin.setValue(85)
        self.template_accept_score_spin.setSuffix(" %")
        self.template_accept_score_spin.setToolTip(
            "Template matching accept threshold\n"
            "Used for all templates after first one"
        )
        template_layout.addWidget(self.template_accept_score_spin, 1, 1)
        
        template_reject_label = QLabel("Reject Score")
        template_reject_label.setToolTip(
            "Confidence threshold for FAIL:\n"
            "• If match score ≤ Reject Score → FAIL\n"
            "• Applied to all templates except first\n"
            "• Default: 40%"
        )
        template_layout.addWidget(template_reject_label, 2, 0)
        self.template_reject_score_spin = QSpinBox()
        self.template_reject_score_spin.setRange(0, 100)
        self.template_reject_score_spin.setValue(40)
        self.template_reject_score_spin.setSuffix(" %")
        self.template_reject_score_spin.setToolTip(
            "Template matching reject threshold\n"
            "Used for all templates after first one"
        )
        template_layout.addWidget(self.template_reject_score_spin, 2, 1)
        
        template_excess_label = QLabel("Mismatch Excess Area")
        template_excess_label.setToolTip(
            "Maximum excess area allowed:\n"
            "• Gray level between body and mark defects\n"
            "• Applied to all templates except first\n"
            "• Default: 5 pixels"
        )
        template_layout.addWidget(template_excess_label, 3, 0)
        self.template_excess_area_spin = QSpinBox()
        self.template_excess_area_spin.setRange(0, 1000)
        self.template_excess_area_spin.setValue(5)
        self.template_excess_area_spin.setSuffix(" Pix")
        self.template_excess_area_spin.setToolTip(
            "Maximum excess area for other templates\n"
            "Gray level between body and mark"
        )
        template_layout.addWidget(self.template_excess_area_spin, 3, 1)
        
        template_missing_label = QLabel("Mismatch Missing Area")
        template_missing_label.setToolTip(
            "Acceptable mark loss:\n"
            "• Applied to all templates except first\n"
            "• Default: 5 pixels"
        )
        template_layout.addWidget(template_missing_label, 4, 0)
        self.template_missing_area_spin = QSpinBox()
        self.template_missing_area_spin.setRange(0, 1000)
        self.template_missing_area_spin.setValue(5)
        self.template_missing_area_spin.setSuffix(" Pix")
        self.template_missing_area_spin.setToolTip(
            "Acceptable mark loss for other templates\n"
            "Loss of the area is allowed"
        )
        template_layout.addWidget(self.template_missing_area_spin, 4, 1)
        
        template_method_label = QLabel("Mismatch Detect Method")
        template_method_label.setToolTip(
            "Algorithm for mismatch detection:\n"
            "• Square Area: Compare bounding box areas\n"
            "• Blob Area: Compare actual pixel areas\n"
            "Applied to all templates except first"
        )
        template_layout.addWidget(template_method_label, 5, 0)
        self.template_detect_method_combo = QComboBox()
        self.template_detect_method_combo.addItems(["Square Area", "Blob Area"])
        self.template_detect_method_combo.setToolTip(
            "Square Area: Bounding box comparison\n"
            "Blob Area: Actual pixel comparison"
        )
        template_layout.addWidget(self.template_detect_method_combo, 5, 1)
        
        template_group.setLayout(template_layout)
        templates_layout.addWidget(template_group)
        
        symbol_insp_layout.addLayout(templates_layout)
        symbol_insp_group.setLayout(symbol_insp_layout)
        
        layout.addWidget(symbol_insp_group)
        
        # OK and Cancel buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setMinimumWidth(80)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setMinimumWidth(80)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Store all controls for easy access
        self._first_template_controls = [
            self.first_gross_check_cb,
            self.first_accept_score_spin,
            self.first_reject_score_spin,
            self.first_excess_area_spin,
            self.first_missing_area_spin,
            self.first_detect_method_combo
        ]
        
        self._hole_check_controls = [
            self.teach_mark_contrast_spin,
            self.insp_mark_contrast_spin,
            self.mark_min_area_spin,
            self.mark_min_xy_size_spin
        ]
        
        # Apply initial enable/disable state
        self._on_separate_params_changed()
        self._on_hole_check_changed()
    
    def _on_mark_set_changed(self):
        """Handle mark set selection change"""
        # In a full implementation, this would load different parameters
        # for different mark sets. For now, we use the same parameters.
        pass
    
    def _on_separate_params_changed(self):
        """Enable/disable first template controls based on checkbox"""
        enabled = self.separate_params_cb.isChecked()
        for control in self._first_template_controls:
            control.setEnabled(enabled)
    
    def _on_hole_check_changed(self):
        """Enable/disable hole check controls based on checkbox"""
        enabled = self.hole_check_cb.isChecked()
        for control in self._hole_check_controls:
            control.setEnabled(enabled)
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            config = load_mark_inspection_config()
            
            # Note: Using symbol set 0 as default
            # Symbol Shift
            self.user_define_window_cb.setChecked(config.user_define_teach_window)
            self.mark_rotation_spin.setValue(config.mark_rotation_tol)
            self.first_shift_x_spin.setValue(config.first_template_shift_x)
            self.first_shift_y_spin.setValue(config.first_template_shift_y)
            self.other_shift_x_spin.setValue(config.other_template_shift_x)
            self.other_shift_y_spin.setValue(config.other_template_shift_y)
            
            # Symbol Characteristics
            self.mark_color_combo.setCurrentIndex(0 if config.mark_color == "White" else 1)
            self.teach_rect_spin.setValue(config.total_teach_rectangle)
            self.min_char_size_spin.setValue(config.min_character_size)
            self.mark_min_x_spin.setValue(config.mark_min_x_size)
            self.mark_min_y_spin.setValue(config.mark_min_y_size)
            
            # Mark Hole Inspection
            self.hole_check_cb.setChecked(config.hole_check)
            self.teach_mark_contrast_spin.setValue(config.teach_mark_contrast)
            self.insp_mark_contrast_spin.setValue(config.insp_mark_contrast)
            self.mark_min_area_spin.setValue(config.mark_min_area)
            self.mark_min_xy_size_spin.setValue(config.mark_min_xy_size)
            
            # Symbol Inspection
            self.separate_params_cb.setChecked(config.separate_parameters_first_template)
            
            # First Template
            self.first_gross_check_cb.setChecked(config.first_gross_check_only)
            self.first_accept_score_spin.setValue(config.first_accept_score)
            self.first_reject_score_spin.setValue(config.first_reject_score)
            self.first_excess_area_spin.setValue(config.first_mismatch_excess_area)
            self.first_missing_area_spin.setValue(config.first_mismatch_missing_area)
            self.first_detect_method_combo.setCurrentText(config.first_mismatch_detect_method)
            
            # Template
            self.template_gross_check_cb.setChecked(config.template_gross_check_only)
            self.template_accept_score_spin.setValue(config.template_accept_score)
            self.template_reject_score_spin.setValue(config.template_reject_score)
            self.template_excess_area_spin.setValue(config.template_mismatch_excess_area)
            self.template_missing_area_spin.setValue(config.template_mismatch_missing_area)
            self.template_detect_method_combo.setCurrentText(config.template_mismatch_detect_method)
            
        except Exception as e:
            print(f"Error loading mark parameters config: {e}")
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            config = load_mark_inspection_config()
            
            # Update config with dialog values
            # Symbol Shift
            config.user_define_teach_window = self.user_define_window_cb.isChecked()
            config.mark_rotation_tol = self.mark_rotation_spin.value()
            config.first_template_shift_x = self.first_shift_x_spin.value()
            config.first_template_shift_y = self.first_shift_y_spin.value()
            config.other_template_shift_x = self.other_shift_x_spin.value()
            config.other_template_shift_y = self.other_shift_y_spin.value()
            
            # Symbol Characteristics
            config.mark_color = self.mark_color_combo.currentText()
            config.total_teach_rectangle = self.teach_rect_spin.value()
            config.min_character_size = self.min_char_size_spin.value()
            config.mark_min_x_size = self.mark_min_x_spin.value()
            config.mark_min_y_size = self.mark_min_y_spin.value()
            
            # Mark Hole Inspection
            config.hole_check = self.hole_check_cb.isChecked()
            config.teach_mark_contrast = self.teach_mark_contrast_spin.value()
            config.insp_mark_contrast = self.insp_mark_contrast_spin.value()
            config.mark_min_area = self.mark_min_area_spin.value()
            config.mark_min_xy_size = self.mark_min_xy_size_spin.value()
            
            # Symbol Inspection
            config.separate_parameters_first_template = self.separate_params_cb.isChecked()
            
            # First Template
            config.first_gross_check_only = self.first_gross_check_cb.isChecked()
            config.first_accept_score = self.first_accept_score_spin.value()
            config.first_reject_score = self.first_reject_score_spin.value()
            config.first_mismatch_excess_area = self.first_excess_area_spin.value()
            config.first_mismatch_missing_area = self.first_missing_area_spin.value()
            config.first_mismatch_detect_method = self.first_detect_method_combo.currentText()
            
            # Template
            config.template_gross_check_only = self.template_gross_check_cb.isChecked()
            config.template_accept_score = self.template_accept_score_spin.value()
            config.template_reject_score = self.template_reject_score_spin.value()
            config.template_mismatch_excess_area = self.template_excess_area_spin.value()
            config.template_mismatch_missing_area = self.template_missing_area_spin.value()
            config.template_mismatch_detect_method = self.template_detect_method_combo.currentText()
            
            save_mark_inspection_config(config)
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
            return False
    
    def _validate_contrast_values(self):
        """Validate that Teach Mark Contrast <= Insp Mark Contrast"""
        teach_val = self.teach_mark_contrast_spin.value()
        insp_val = self.insp_mark_contrast_spin.value()
        
        # If teach exceeds inspection, auto-correct
        if teach_val > insp_val:
            self.teach_mark_contrast_spin.blockSignals(True)
            self.teach_mark_contrast_spin.setValue(insp_val)
            self.teach_mark_contrast_spin.blockSignals(False)
    
    def accept(self):
        """Handle OK button click"""
        if self._save_config():
            super().accept()
    
    def get_values(self):
        """Get all parameter values as a dictionary"""
        return {
            # Symbol Shift
            "user_define_teach_window": self.user_define_window_cb.isChecked(),
            "mark_rotation_tol": self.mark_rotation_spin.value(),
            "first_template_shift_x": self.first_shift_x_spin.value(),
            "first_template_shift_y": self.first_shift_y_spin.value(),
            "other_template_shift_x": self.other_shift_x_spin.value(),
            "other_template_shift_y": self.other_shift_y_spin.value(),
            
            # Symbol Characteristics
            "mark_color": self.mark_color_combo.currentText(),
            "total_teach_rectangle": self.teach_rect_spin.value(),
            "min_character_size": self.min_char_size_spin.value(),
            "mark_min_x_size": self.mark_min_x_spin.value(),
            "mark_min_y_size": self.mark_min_y_spin.value(),
            
            # Mark Hole Inspection
            "hole_check": self.hole_check_cb.isChecked(),
            "teach_mark_contrast": self.teach_mark_contrast_spin.value(),
            "insp_mark_contrast": self.insp_mark_contrast_spin.value(),
            "mark_min_area": self.mark_min_area_spin.value(),
            "mark_min_xy_size": self.mark_min_xy_size_spin.value(),
            
            # Symbol Inspection
            "separate_parameters_first_template": self.separate_params_cb.isChecked(),
            
            # First Template
            "first_gross_check_only": self.first_gross_check_cb.isChecked(),
            "first_accept_score": self.first_accept_score_spin.value(),
            "first_reject_score": self.first_reject_score_spin.value(),
            "first_mismatch_excess_area": self.first_excess_area_spin.value(),
            "first_mismatch_missing_area": self.first_missing_area_spin.value(),
            "first_mismatch_detect_method": self.first_detect_method_combo.currentText(),
            
            # Template
            "template_gross_check_only": self.template_gross_check_cb.isChecked(),
            "template_accept_score": self.template_accept_score_spin.value(),
            "template_reject_score": self.template_reject_score_spin.value(),
            "template_mismatch_excess_area": self.template_excess_area_spin.value(),
            "template_mismatch_missing_area": self.template_missing_area_spin.value(),
            "template_mismatch_detect_method": self.template_detect_method_combo.currentText(),
        }
