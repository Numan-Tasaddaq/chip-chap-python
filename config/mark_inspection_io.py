"""
Mark Inspection Configuration I/O
Load and save Mark Symbol Set configuration from mark_inspection.json
"""
import json
from pathlib import Path
from typing import Dict, Any
from config.mark_inspection import MarkSymbolSetConfig, MarkInspectionConfig


MARK_INSPECTION_FILE = Path("mark_inspection.json")


def _get_default_mark_inspection_config() -> Dict[str, Any]:
    """Get default Mark Inspection configuration"""
    return {
        "enable_mark_inspect": False,
        "total_mark_set": 1,
        "total_symbol_set": 1,
        "inspect_color": False,
        "enable_mark_inspect2": True,
        "mark_threshold": 128,
        "mark_min_area": 10,
        "mark_max_area": 5000,
        "mark_contrast": 50,
        "symbol_sets": {
            "1": {
                "enable": True,
                "total_symbols": 1,
                "symbols": {
                    "1": {
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
        }
    }


def load_mark_inspection_config() -> MarkInspectionConfig:
    """
    Load Mark Inspection configuration from mark_inspection.json
    Returns MarkInspectionConfig with full symbol set data
    """
    config = MarkInspectionConfig()
    
    if not MARK_INSPECTION_FILE.exists():
        print(f"[INFO] Mark inspection file not found: {MARK_INSPECTION_FILE}")
        return config
    
    try:
        with open(MARK_INSPECTION_FILE, "r") as f:
            data = json.load(f)
        
        # Load MarkSymbolSetConfig
        symbol_set = MarkSymbolSetConfig()
        symbol_set.enable_mark_inspect = data.get("enable_mark_inspect", False)
        symbol_set.total_mark_set = data.get("total_mark_set", 1)
        symbol_set.total_symbol_set = data.get("total_symbol_set", 1)
        symbol_set.inspect_color = data.get("inspect_color", False)
        symbol_set.enable_mark_inspect2 = data.get("enable_mark_inspect2", True)
        symbol_set.mark_threshold = data.get("mark_threshold", 128)
        symbol_set.mark_min_area = data.get("mark_min_area", 10)
        symbol_set.mark_max_area = data.get("mark_max_area", 5000)
        symbol_set.mark_contrast = data.get("mark_contrast", 50)
        
        # Load symbol sets
        symbol_sets_data = data.get("symbol_sets", {})
        symbol_set.symbol_sets = {}
        for set_id, set_data in symbol_sets_data.items():
            try:
                set_id_int = int(set_id)
                symbol_set.symbol_sets[set_id_int] = set_data
            except (ValueError, TypeError):
                continue
        
        config.symbol_set = symbol_set
        
        # Load advanced settings
        config.enable_mark_verification = data.get("enable_mark_verification", False)
        config.mark_detect_method = data.get("mark_detect_method", "threshold")
        config.mark_rotation_tolerance = data.get("mark_rotation_tolerance", 45)
        config.mark_position_tolerance = data.get("mark_position_tolerance", 50)
        config.enable_ocr = data.get("enable_ocr", False)
        config.ocr_threshold = data.get("ocr_threshold", 128)
        config.color_detection_enabled = data.get("color_detection_enabled", False)
        config.color_target_r = data.get("color_target_r", 0)
        config.color_target_g = data.get("color_target_g", 0)
        config.color_target_b = data.get("color_target_b", 0)
        config.color_tolerance = data.get("color_tolerance", 30)
        
        # Load Mark Parameters
        config.user_define_teach_window = data.get("user_define_teach_window", True)
        config.mark_rotation_tol = data.get("mark_rotation_tol", 5)
        config.first_template_shift_x = data.get("first_template_shift_x", 25)
        config.first_template_shift_y = data.get("first_template_shift_y", 25)
        config.other_template_shift_x = data.get("other_template_shift_x", 10)
        config.other_template_shift_y = data.get("other_template_shift_y", 10)
        config.mark_color = data.get("mark_color", "White")
        config.total_teach_rectangle = data.get("total_teach_rectangle", 1)
        config.min_character_size = data.get("min_character_size", 10)
        config.mark_min_x_size = data.get("mark_min_x_size", 10)
        config.mark_min_y_size = data.get("mark_min_y_size", 10)
        config.hole_check = data.get("hole_check", False)
        config.teach_mark_contrast = data.get("teach_mark_contrast", 100)
        config.insp_mark_contrast = data.get("insp_mark_contrast", 130)
        config.mark_min_area = data.get("mark_min_area", 4)
        config.mark_min_xy_size = data.get("mark_min_xy_size", 3)
        config.separate_parameters_first_template = data.get("separate_parameters_first_template", True)
        config.first_gross_check_only = data.get("first_gross_check_only", False)
        config.first_accept_score = data.get("first_accept_score", 85)
        config.first_reject_score = data.get("first_reject_score", 40)
        config.first_mismatch_excess_area = data.get("first_mismatch_excess_area", 5)
        config.first_mismatch_missing_area = data.get("first_mismatch_missing_area", 5)
        config.first_mismatch_detect_method = data.get("first_mismatch_detect_method", "Square Area")
        config.template_gross_check_only = data.get("template_gross_check_only", False)
        config.template_accept_score = data.get("template_accept_score", 85)
        config.template_reject_score = data.get("template_reject_score", 40)
        config.template_mismatch_excess_area = data.get("template_mismatch_excess_area", 5)
        config.template_mismatch_missing_area = data.get("template_mismatch_missing_area", 5)
        config.template_mismatch_detect_method = data.get("template_mismatch_detect_method", "Square Area")
        
        print(f"[INFO] Mark inspection config loaded: {symbol_set.total_mark_set} sets, {symbol_set.total_symbol_set} symbols")
        return config
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse mark_inspection.json: {e}")
        return config
    except Exception as e:
        print(f"[ERROR] Failed to load mark_inspection.json: {e}")
        return config


def save_mark_inspection_config(config: MarkInspectionConfig) -> bool:
    """
    Save Mark Inspection configuration to mark_inspection.json
    """
    try:
        data = {
            "enable_mark_inspect": config.symbol_set.enable_mark_inspect,
            "total_mark_set": config.symbol_set.total_mark_set,
            "total_symbol_set": config.symbol_set.total_symbol_set,
            "inspect_color": config.symbol_set.inspect_color,
            "enable_mark_inspect2": config.symbol_set.enable_mark_inspect2,
            "mark_threshold": config.symbol_set.mark_threshold,
            "mark_min_area": config.symbol_set.mark_min_area,
            "mark_max_area": config.symbol_set.mark_max_area,
            "mark_contrast": config.symbol_set.mark_contrast,
            "symbol_sets": config.symbol_set.symbol_sets,
            "enable_mark_verification": config.enable_mark_verification,
            "mark_detect_method": config.mark_detect_method,
            "mark_rotation_tolerance": config.mark_rotation_tolerance,
            "mark_position_tolerance": config.mark_position_tolerance,
            "enable_ocr": config.enable_ocr,
            "ocr_threshold": config.ocr_threshold,
            "color_detection_enabled": config.color_detection_enabled,
            "color_target_r": config.color_target_r,
            "color_target_g": config.color_target_g,
            "color_target_b": config.color_target_b,
            "color_tolerance": config.color_tolerance,
            # Mark Parameters
            "user_define_teach_window": config.user_define_teach_window,
            "mark_rotation_tol": config.mark_rotation_tol,
            "first_template_shift_x": config.first_template_shift_x,
            "first_template_shift_y": config.first_template_shift_y,
            "other_template_shift_x": config.other_template_shift_x,
            "other_template_shift_y": config.other_template_shift_y,
            "mark_color": config.mark_color,
            "total_teach_rectangle": config.total_teach_rectangle,
            "min_character_size": config.min_character_size,
            "mark_min_x_size": config.mark_min_x_size,
            "mark_min_y_size": config.mark_min_y_size,
            "hole_check": config.hole_check,
            "teach_mark_contrast": config.teach_mark_contrast,
            "insp_mark_contrast": config.insp_mark_contrast,
            "mark_min_area": config.mark_min_area,
            "mark_min_xy_size": config.mark_min_xy_size,
            "separate_parameters_first_template": config.separate_parameters_first_template,
            "first_gross_check_only": config.first_gross_check_only,
            "first_accept_score": config.first_accept_score,
            "first_reject_score": config.first_reject_score,
            "first_mismatch_excess_area": config.first_mismatch_excess_area,
            "first_mismatch_missing_area": config.first_mismatch_missing_area,
            "first_mismatch_detect_method": config.first_mismatch_detect_method,
            "template_gross_check_only": config.template_gross_check_only,
            "template_accept_score": config.template_accept_score,
            "template_reject_score": config.template_reject_score,
            "template_mismatch_excess_area": config.template_mismatch_excess_area,
            "template_mismatch_missing_area": config.template_mismatch_missing_area,
            "template_mismatch_detect_method": config.template_mismatch_detect_method,
        }
        
        with open(MARK_INSPECTION_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"[INFO] Mark inspection config saved to {MARK_INSPECTION_FILE}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to save mark_inspection.json: {e}")
        return False


def create_default_mark_inspection_file() -> bool:
    """Create mark_inspection.json with default values if it doesn't exist"""
    if MARK_INSPECTION_FILE.exists():
        print(f"[INFO] Mark inspection file already exists: {MARK_INSPECTION_FILE}")
        return True
    
    try:
        default_config = _get_default_mark_inspection_config()
        with open(MARK_INSPECTION_FILE, "w") as f:
            json.dump(default_config, f, indent=2)
        print(f"[INFO] Created default mark_inspection.json")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create default mark_inspection.json: {e}")
        return False


def get_symbol_set(set_id: int, config: MarkInspectionConfig) -> Dict[str, Any]:
    """Get a specific symbol set by ID"""
    return config.symbol_set.symbol_sets.get(set_id, {})


def get_symbol(set_id: int, symbol_id: int, config: MarkInspectionConfig) -> Dict[str, Any]:
    """Get a specific symbol from a symbol set"""
    symbol_set = get_symbol_set(set_id, config)
    if not symbol_set:
        return {}
    
    symbols = symbol_set.get("symbols", {})
    return symbols.get(str(symbol_id), {})
