"""
Mark Inspection Configuration
Handles Mark Symbol Set and Mark Symbol parameters
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class MarkSymbolSetConfig:
    """Mark Symbol Set Configuration"""
    # Basic Mark Inspection Settings
    enable_mark_inspect: bool = False
    total_mark_set: int = 1  # Range: 1-3
    total_symbol_set: int = 1  # Range: 1-5
    inspect_color: bool = False
    enable_mark_inspect2: bool = True  # Controls if mark inspection can be enabled
    
    # Mark detection parameters
    mark_threshold: int = 128
    mark_min_area: int = 10
    mark_max_area: int = 5000
    mark_contrast: int = 50
    
    # Symbol set parameters (per symbol set)
    symbol_sets: Dict[int, Dict[str, Any]] = field(default_factory=lambda: {
        1: {
            "enable": True,
            "total_symbols": 1,
            "symbols": {
                1: {
                    "enable": True,
                    "name": "Symbol_1",
                    "threshold": 128,
                    "min_area": 10,
                    "max_area": 5000,
                    "contrast": 50,
                    "color_r": 0,
                    "color_g": 0,
                    "color_b": 0,
                }
            }
        }
    })


@dataclass
class MarkInspectionConfig:
    """Complete Mark Inspection Configuration"""
    symbol_set: MarkSymbolSetConfig = field(default_factory=MarkSymbolSetConfig)
    
    # Advanced Mark Inspection Settings
    enable_mark_verification: bool = False
    mark_detect_method: str = "threshold"  # "threshold", "color", "template"
    mark_rotation_tolerance: int = 45  # degrees
    mark_position_tolerance: int = 50  # pixels
    
    # Optical Character Recognition (if needed)
    enable_ocr: bool = False
    ocr_threshold: int = 128
    
    # Color detection for marks (if inspect_color is True)
    color_detection_enabled: bool = False
    color_target_r: int = 0
    color_target_g: int = 0
    color_target_b: int = 0
    color_tolerance: int = 30
    
    # Mark Parameters (from Mark Inspect Parameters dialog)
    # Symbol Shift
    user_define_teach_window: bool = True
    mark_rotation_tol: int = 5
    first_template_shift_x: int = 25
    first_template_shift_y: int = 25
    other_template_shift_x: int = 10
    other_template_shift_y: int = 10
    
    # Symbol Characteristics
    mark_color: str = "White"  # "White" or "Black"
    total_teach_rectangle: int = 1
    min_character_size: int = 10
    mark_min_x_size: int = 10
    mark_min_y_size: int = 10
    
    # Mark Hole Inspection
    hole_check: bool = False
    teach_mark_contrast: int = 100
    insp_mark_contrast: int = 130
    mark_min_area: int = 4
    mark_min_xy_size: int = 3
    
    # Symbol Inspection
    separate_parameters_first_template: bool = True
    
    # First Template Parameters
    first_gross_check_only: bool = False
    first_accept_score: int = 85
    first_reject_score: int = 40
    first_mismatch_excess_area: int = 5
    first_mismatch_missing_area: int = 5
    first_mismatch_detect_method: str = "Square Area"
    
    # Template Parameters
    template_gross_check_only: bool = False
    template_accept_score: int = 85
    template_reject_score: int = 40
    template_mismatch_excess_area: int = 5
    template_mismatch_missing_area: int = 5
    template_mismatch_detect_method: str = "Square Area"
