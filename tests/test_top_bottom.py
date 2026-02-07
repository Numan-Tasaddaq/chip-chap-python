import json
from pathlib import Path
from tests.test_runner import TestResult, TestStatus
from tests.test_draw import draw_test_result
from tests.measurements import (measure_body_width, measure_body_length, 
                                measure_terminal_width, measure_terminal_length,
                                measure_term_to_term_length,
                                measure_body_to_term_width,
                                measure_term_to_body_gap,
                                check_body_width_difference,
                                check_terminal_length_difference)
from tests.measurement_draw import draw_measurement_result, add_status_text
from tests.body_smear import check_body_smear, check_body_stain, check_body_stand_stain, check_reverse_chip
from tests.body_crack import check_body_crack, check_body_hairline_crack, check_edge_chipoff, draw_edge_chipoff_bands
from tests.terminal_defects import (
    check_terminal_pogo,
    check_terminal_offset,
    check_terminal_oxidation,
    check_incomplete_termination_1,
    check_incomplete_termination_2,
    check_terminal_chipoff_inner,
    check_terminal_chipoff_outer,
    check_compare_terminal_corner,
    check_black_pixels_count,
    draw_chipoff_inspection_bands,
    draw_terminal_corner_regions,
    draw_black_pixels_bands,
)
from imaging.device_location import detect_device_location, validate_device_location
from imaging.pocket_location import (
    detect_pocket_location, validate_pocket_location,
    check_pocket_dimension, check_pocket_gap, track_pocket_shift,
    PocketShiftRecord,
    check_outer_pocket_stain,
    check_emboss_tape_pickup,
    check_sealing_stain,
    check_sealing_stain2,
    check_sealing_shift,
    check_hole_side_shift,
    check_sealing_distance_center,
    check_bottom_dent_inspection,
    check_special_black_emboss_sealing,
)
from imaging.pocket_shift_log import get_shift_log_manager
from imaging.mark_inspection import detect_marks, verify_marks, validate_mark_position
from config.mark_inspection_io import load_mark_inspection_config
from config.debug_flags import (
    DEBUG_DRAW, DEBUG_PRINT, DEBUG_PRINT_EXT, DEBUG_EDGE,
    DEBUG_BLOB, DEBUG_HIST, DEBUG_TIME, DEBUG_TIME_EXT
)
import cv2

# Load device inspection thresholds
DEVICE_INSPECTION_FILE = Path("device_inspection.json")
POCKET_PARAMS_FILE = Path("pocket_params.json")


def _safe_roi_mean_gray(image, roi):
    """Return the mean grayscale intensity for a clamped ROI; None if empty."""
    x, y, w, h = roi
    h = max(1, h)
    w = max(1, w)
    x = max(0, x)
    y = max(0, y)
    x2 = min(image.shape[1], x + w)
    y2 = min(image.shape[0], y + h)
    if x2 <= x or y2 <= y:
        return None
    roi_img = image[y:y2, x:x2]
    if roi_img.size == 0:
        return None
    if len(roi_img.shape) == 3:
        roi_img = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    return float(roi_img.mean())


def _resolve_intensity_window(measured, teach_min, teach_max, contrast):
    """Resolve min/max thresholds from taught values or contrast tolerance."""
    if teach_min is not None and teach_max is not None and not (teach_min == 0 and teach_max == 255):
        return int(teach_min), int(teach_max)
    if contrast != 255:
        tol = max(1, int(contrast))
        return max(0, int(measured - tol)), min(255, int(measured + tol))
    return None, None


def _draw_color_roi(image, roi, is_pass, label):
    color = (0, 255, 0) if is_pass else (0, 0, 255)
    x, y, w, h = roi
    cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
    cv2.putText(image, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)


def _ci_val(ci_tab, key, default=0):
    raw = ci_tab.get(key, "255")
    try:
        val = int(raw)
    except (ValueError, TypeError):
        return default
    return default if val == 255 else val


def load_device_thresholds():
    """Load device inspection thresholds from device_inspection.json"""
    if not DEVICE_INSPECTION_FILE.exists():
        return {}
    
    try:
        with open(DEVICE_INSPECTION_FILE, "r") as f:
            data = json.load(f)
        # Merge UnitParameters into top-level for backward compatibility
        unit = data.get("UnitParameters", {})
        merged = dict(unit)
        merged.update(data)
        return merged
    except Exception as e:
        print(f"[WARN] Failed to load device_inspection.json: {e}")
        return {}

def load_pocket_params():
    """Load pocket parameters from pocket_params.json"""
    if not POCKET_PARAMS_FILE.exists():
        return {}
    
    try:
        with open(POCKET_PARAMS_FILE, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[WARN] Failed to load pocket_params.json: {e}")
        return {}

def test_top_bottom(image, params, step_mode=False, step_callback=None, debug_flags=0):
    debug_enabled = bool(debug_flags & (
        DEBUG_PRINT | DEBUG_PRINT_EXT | DEBUG_EDGE |
        DEBUG_BLOB | DEBUG_HIST | DEBUG_TIME | DEBUG_TIME_EXT
    ))
    debug_draw = bool(debug_flags & DEBUG_DRAW)
    if not debug_enabled:
        def print(*args, **kwargs):
            return None
    print("\n[TEST] Top / Bottom inspection started")
    
    # Debug: Check image at function entry
    mean_at_entry = cv2.mean(image)[0]
    print(f"[DEBUG] test_top_bottom entry - image id={id(image)}, mean={mean_at_entry:.1f}")

    # Create a working copy for measurements to prevent visualization from corrupting measurements
    # The original 'image' will be used for visualization, working_image for measurements
    import numpy as np
    working_image = np.copy(image)

    messages = []
    enabled_tests = []
    skipped_tests = []
    
    # Load device inspection thresholds and pocket parameters
    device_thresholds = load_device_thresholds()
    pocket_params = load_pocket_params()
    
    # Initialize pocket shift tracking
    pocket_shift_record = None  # Will be created on first use if tracking enabled
    
    # Check if device has no terminal (body-only device)
    no_terminal = bool(device_thresholds.get("no_terminal", False))
    
    if no_terminal:
        print("[INFO] No Terminal mode ENABLED - device has body only, skipping all terminal inspections")
    
    # Get edge_contrast_value from pocket_params (default 106)
    edge_contrast_value = int(pocket_params.get("edge_contrast_value", 106))
    
    print(f"[INFO] Device thresholds loaded: {bool(device_thresholds)}")
    print(f"[INFO] Pocket parameters loaded, edge_contrast={edge_contrast_value}")

    # -------------------------------
    # 1. Check Package Location (REQUIRED)
    # -------------------------------
    print("[CHECK] Validating teach data...")
    
    if params.package_w <= 0 or params.package_h <= 0:
        print("[FAIL] Package not taught")
        overlay, reason = draw_test_result(
            image, ["Package not taught", "Please run Teach first"], "FAIL"
        )
        return TestResult(TestStatus.FAIL, "Package not taught", overlay)

    if not params.flags.get("enable_package_location", False):
        print("[SKIP] Package inspection disabled")
        skipped_tests.append("Package Location (disabled)")

    print("[OK] Package location available")

    # -------------------------------
    # 2. Build list of enabled inspections IN ORDER
    # -------------------------------
    # 2. Build list of enabled inspections IN ORDER
    # -----------------------------------------------
    # Read from params.flags dictionary (shared across stations)
    inspection_checks = [
        # Package & Pocket
        ("Package Location", params.flags.get("enable_package_location", False), "enable_package_location", "detect_package_location"),
        
        # Dimension Measurements (primary)
        ("Body Length", params.flags.get("check_body_length", False), "check_body_length", "measure_body_length"),
        ("Body Width", params.flags.get("check_body_width", False), "check_body_width", "measure_body_width"),
        # Terminal inspections - skip if no_terminal is enabled
        ("Terminal Width", params.flags.get("check_terminal_width", False) and not no_terminal, "check_terminal_width", "measure_terminal_width"),
        ("Terminal Length", params.flags.get("check_terminal_length", False) and not no_terminal, "check_terminal_length", "measure_terminal_length"),
        ("Term-Term Length", params.flags.get("check_term_term_length", False) and not no_terminal, "check_term_term_length", "measure_term_to_term_length"),
        ("Terminal Length Diff", params.flags.get("check_terminal_length_diff", False) and not no_terminal, "check_terminal_length_diff", "check_terminal_length_diff"),
        
        # Terminal Inspections - all skipped if no_terminal
        ("Terminal Pogo", params.flags.get("check_terminal_pogo", False) and not no_terminal, "check_terminal_pogo", None),
        ("Terminal Offset", params.flags.get("check_terminal_offset", False) and not no_terminal, "check_terminal_offset", None),
        ("Incomplete Termination 1", params.flags.get("check_incomplete_termination_1", False) and not no_terminal, "check_incomplete_termination_1", None),
        ("Incomplete Termination 2", params.flags.get("check_incomplete_termination_2", False) and not no_terminal, "check_incomplete_termination_2", None),
        ("Terminal to Body Gap", params.flags.get("check_terminal_to_body_gap", False) and not no_terminal, "check_terminal_to_body_gap", "measure_term_to_body_gap"),
        ("Terminal Color", params.flags.get("check_terminal_color", False) and not no_terminal, "check_terminal_color", None),
        ("Terminal Oxidation", params.flags.get("check_terminal_oxidation", False) and not no_terminal, "check_terminal_oxidation", None),
        ("Inner Terminal Chipoff", params.flags.get("check_inner_term_chipoff", False) and not no_terminal, "check_inner_term_chipoff", None),
        ("Outer Terminal Chipoff", params.flags.get("check_outer_term_chipoff", False) and not no_terminal, "check_outer_term_chipoff", None),
        
        # Body Inspections
        ("Body Stain 1", params.flags.get("check_body_stain_1", False), "check_body_stain_1", None),
        ("Body Stain 2", params.flags.get("check_body_stain_2", False), "check_body_stain_2", None),
        ("Body Color", params.flags.get("check_body_color", False), "check_body_color", None),
        ("Body to Term Width", params.flags.get("check_body_to_term_width", False), "check_body_to_term_width", "measure_body_to_term_width"),
        ("Body Width Diff", params.flags.get("check_body_width_diff", False), "check_body_width_diff", "check_body_width_diff"),
        ("Body Crack", params.flags.get("check_body_crack", False), "check_body_crack", None),
        ("Low/High Contrast", params.flags.get("check_low_high_contrast", False), "check_low_high_contrast", None),
        ("Black Defect", params.flags.get("check_black_defect", False), "check_black_defect", None),
        ("White Defect", params.flags.get("check_white_defect", False), "check_white_defect", None),
        
        # Body Smear
        ("Body Smear 1", params.flags.get("check_body_smear_1", False), "check_body_smear_1", None),
        ("Body Smear 2", params.flags.get("check_body_smear_2", False), "check_body_smear_2", None),
        ("Body Smear 3", params.flags.get("check_body_smear_3", False), "check_body_smear_3", None),
        ("Reverse Chip", params.flags.get("check_reverse_chip", False), "check_reverse_chip", "check_reverse_chip"),
        ("Smear White", params.flags.get("check_smear_white", False), "check_smear_white", None),
        
        # Body Edge
        ("Edge Chipoff", params.flags.get("check_edge_chipoff", False), "check_edge_chipoff", None),
        ("Body Edge Black", params.flags.get("check_body_edge_black", False), "check_body_edge_black", None),
        ("Body Edge White", params.flags.get("check_body_edge_white", False), "check_body_edge_white", None),
    ]

    # Filter enabled tests
    for test_name, is_enabled, attr_name, measurement_func in inspection_checks:
        if is_enabled:
            enabled_tests.append((test_name, attr_name, measurement_func))
            print(f"[ENABLED] {test_name}")
        else:
            # Add reason for why test is skipped
            if no_terminal and "Terminal" in test_name:
                skipped_tests.append(f"{test_name} (no terminal mode)")
                print(f"[SKIPPED] {test_name} - no terminal mode")
            else:
                skipped_tests.append(f"{test_name} (disabled)")
                print(f"[SKIPPED] {test_name} - not enabled")

    # Log skipped tests
    if skipped_tests:
        print(f"\n[INFO] Skipped tests: {', '.join(skipped_tests)}")

    # If no tests enabled, return PASS with message
    if not enabled_tests:
        print("[PASS] No inspections enabled")
        message = "No inspections enabled\n\nSkipped:\n" + "\n".join(skipped_tests)
        overlay, reason = draw_test_result(image, [message], "PASS")
        return TestResult(TestStatus.PASS, "No tests enabled", overlay)

    # -------------------------------
    # 3. RUN ENABLED INSPECTIONS
    # -------------------------------
    print("\n[TEST] Running enabled inspections...")

    for test_name, attr_name, measurement_func in enabled_tests:
        print(f"\n[TEST] {test_name} inspection")
        
        if measurement_func is None:
            # Skip tests with no measurement function (placeholder tests)
            messages.append(f"{test_name} OK (no action)")
            continue
        
        if measurement_func == "detect_package_location":
            # Package Location detection with Mark Inspection
            print(f"[DEBUG] Processing Package Location detection")
            from config.device_location_setting_io import load_device_location_setting
            dev_loc_settings = load_device_location_setting()
            
            # Check if using taught position mode (fixed location, no detection)
            use_teach_pos = dev_loc_settings.get("teach_pos", False)
            
            if use_teach_pos:
                # Use taught package position without detection
                print(f"[INFO] Using taught package position (teach_pos mode enabled)")
                print(f"[INFO] Package location: ({params.package_x}, {params.package_y}, {params.package_w}x{params.package_h})")
                
                # Validate taught position
                is_valid = validate_device_location(
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    image.shape,
                    min_size=20,
                    max_size_ratio=0.95,
                    debug=True
                )
                
                if not is_valid:
                    print(f"[FAIL] Taught package location validation failed")
                    overlay, reason = draw_test_result(
                        image,
                        ["Taught package location validation failed", 
                         f"Location: ({params.package_x}, {params.package_y}, {params.package_w}x{params.package_h})"],
                        "FAIL"
                    )
                    return TestResult(TestStatus.FAIL, "Package location validation failed", overlay)
                
                print(f"[PASS] Package location validated (taught position mode)")
                messages.append(f"{test_name} OK (taught position)")
                
                # ========================================
                # Mark Inspection (after device location - teach_pos mode)
                # ========================================
                mark_config = load_mark_inspection_config()
                
                # Check if mark inspection is enabled
                if mark_config.symbol_set.enable_mark_inspect:
                    print(f"[INFO] Mark Inspection enabled - running detection...")
                    
                    # Use taught package position for mark detection
                    device_roi = (params.package_x, params.package_y, params.package_w, params.package_h)
                    
                    # Detect marks
                    mark_result = detect_marks(
                        working_image,
                        config=mark_config,
                        roi=device_roi,
                        debug=True
                    )
                    
                    if mark_result.detected:
                        # Verify marks
                        verify_passed, verify_details = verify_marks(
                            mark_result.marks,
                            mark_config,
                            debug=True
                        )
                        
                        if verify_passed:
                            print(f"[PASS] Mark Inspection: {len(mark_result.marks)} marks detected")
                            print(f"[INFO] Mark confidence: {mark_result.confidence:.1f}%, method: {mark_result.method}")
                            messages.append(f"Mark Inspection OK ({len(mark_result.marks)} marks, {mark_result.confidence:.0f}%)")
                        else:
                            print(f"[WARN] Mark verification failed: {verify_details.get('message', 'unknown')}")
                            messages.append(f"Mark Inspection WARN (verification failed)")
                    else:
                        print(f"[WARN] No marks detected: {mark_result.error_message}")
                        messages.append(f"Mark Inspection WARN (no marks)")
                else:
                    print(f"[INFO] Mark Inspection disabled")
            
            continue  # Skip the measurement processing below
        
        if measurement_func == "measure_body_width":
            # Debug: Check image integrity right before calling measurement
            x, y, w, h = params.package_x, params.package_y, params.package_w, params.package_h
            test_roi = working_image[y:y+h, x:x+w]
            test_roi_mean = cv2.mean(test_roi)[0]
            print(f"[DEBUG] Before measure_body_width - image id={id(working_image)}, ROI mean={test_roi_mean:.1f}")
            
            value = measure_body_width(
                working_image,
                (params.package_x, params.package_y,
                 params.package_w, params.package_h),
                body_contrast=params.ranges.get("body_contrast", 75),
                debug=True  # Enable debug for troubleshooting
            )

            metric_key_min = "body_width_min"
            metric_key_max_from_dev = "body_width_max"
            fallback_min = params.body_width_min
            fallback_max = params.body_width_max
        elif measurement_func == "measure_body_length":
            # If configured to use package location as body length, use taught width
            use_pkg_as_body = bool(device_thresholds.get("pkg_as_body", False))
            if use_pkg_as_body:
                value = int(params.package_w)
                print(f"[INFO] Using package width as Body Length (pkg_as_body)")
            else:
                value = measure_body_length(
                    working_image,
                    (params.package_x, params.package_y,
                     params.package_w, params.package_h),
                    body_contrast=params.ranges.get("body_contrast", 75),
                    debug=True  # Enable debug for troubleshooting
                )

            metric_key_min = "body_length_min"
            metric_key_max_from_dev = "body_length_max"
            fallback_min = params.body_length_min
            fallback_max = params.body_length_max
        elif measurement_func == "measure_terminal_width":
            # Terminal Width: find leftmost/rightmost terminal edges
            # Estimate terminal ROI as top region of package (typical for TOP/BOTTOM terminals)
            terminal_roi = (params.package_x, params.package_y, params.package_w, int(params.package_h * 0.3))
            
            # Try both top and bottom regions for terminal detection
            top_terminal_roi = (params.package_x, params.package_y, params.package_w, int(params.package_h * 0.3))
            bottom_terminal_roi = (params.package_x, params.package_y + int(params.package_h * 0.7), params.package_w, int(params.package_h * 0.3))
            
            # Try top terminal first
            value = measure_terminal_width(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                top_terminal_roi,
                edge_contrast=edge_contrast_value,
                debug=debug_enabled
            )
            
            # If top fails, try bottom terminal
            if value is None:
                print(f"[INFO] Top terminal width not detected, trying bottom terminal...")
                value = measure_terminal_width(
                    working_image,
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    bottom_terminal_roi,
                    edge_contrast=edge_contrast_value,
                    debug=True
                )
            
            metric_key_min = "terminal_width_min"
            metric_key_max_from_dev = "terminal_width_max"
            fallback_min = params.terminal_width_min if hasattr(params, 'terminal_width_min') else 10
            fallback_max = params.terminal_width_max if hasattr(params, 'terminal_width_max') else 100
        elif measurement_func == "measure_terminal_length":
            # Terminal Length: multi-scan edge detection
            # Try both top and bottom regions for terminal detection
            top_terminal_roi = (params.package_x, params.package_y, params.package_w, int(params.package_h * 0.3))
            bottom_terminal_roi = (params.package_x, params.package_y + int(params.package_h * 0.7), params.package_w, int(params.package_h * 0.3))
            
            # Try top terminal first
            value = measure_terminal_length(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                top_terminal_roi,
                edge_contrast=edge_contrast_value,
                num_scans=100,
                debug=True
            )
            
            # If top fails, try bottom terminal
            if value is None:
                print(f"[INFO] Top terminal length not detected, trying bottom terminal...")
                value = measure_terminal_length(
                    working_image,
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    bottom_terminal_roi,
                    edge_contrast=edge_contrast_value,
                    num_scans=100,
                    debug=True
                )
            
            metric_key_min = "terminal_length_min"
            metric_key_max_from_dev = "terminal_length_max"
            fallback_min = device_thresholds.get("terminal_length_min", 10)
            fallback_max = device_thresholds.get("terminal_length_max", 100)
        elif measurement_func == "measure_term_to_term_length":
            # Term-to-Term Length: gap between left and right terminals
            # Estimate left and right terminal ROIs
            left_terminal_roi = (params.package_x, params.package_y, int(params.package_w * 0.3), int(params.package_h * 0.3))
            right_terminal_roi = (params.package_x + int(params.package_w * 0.7), params.package_y, int(params.package_w * 0.3), int(params.package_h * 0.3))
            
            value = measure_term_to_term_length(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                left_terminal_roi,
                right_terminal_roi,
                edge_contrast=edge_contrast_value,
                num_scans=100,
                debug=True
            )
            
            metric_key_min = "term_to_term_length_min"
            metric_key_max_from_dev = "term_to_term_length_max"
            fallback_min = int(device_thresholds.get("term_to_term_length_min", 20))
            fallback_max = int(device_thresholds.get("term_to_term_length_max", 200))
        elif measurement_func == "measure_body_to_term_width":
            # Measure top and bottom body band thickness and enforce range
            result = measure_body_to_term_width(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                edge_contrast=edge_contrast_value,
                num_scans=60,
                debug=True
            )
            top_v = result.get('top')
            bot_v = result.get('bottom')

            metric_key_min = "body_to_term_min"
            metric_key_max_from_dev = "body_to_term_max"
            fallback_min = int(device_thresholds.get("body_to_term_min", 10))
            fallback_max = int(device_thresholds.get("body_to_term_max", 50))

            if top_v is None or bot_v is None:
                print(f"[FAIL] {test_name} not detected")
                overlay, reason = draw_test_result(image, [f"{test_name} not detected"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} detect fail", overlay)

            # thresholds from device
            min_threshold = None
            max_threshold = None
            threshold_source = "params"
            if device_thresholds:
                try:
                    min_val = device_thresholds.get(metric_key_min, "")
                    max_val = device_thresholds.get(metric_key_max_from_dev, "")
                    if min_val and min_val != "255":
                        min_threshold = int(min_val)
                    if max_val and max_val != "255":
                        max_threshold = int(max_val)
                    if (min_threshold is not None) or (max_threshold is not None):
                        threshold_source = "device_inspection.json"
                except ValueError:
                    pass
            if min_threshold is None:
                min_threshold = fallback_min
            if max_threshold is None:
                max_threshold = fallback_max

            print(f"[INFO] {test_name} top={top_v}, bottom={bot_v} allowed={min_threshold}-{max_threshold} ({threshold_source})")

            top_ok = min_threshold <= top_v <= max_threshold
            bot_ok = min_threshold <= bot_v <= max_threshold
            is_pass = top_ok and bot_ok

            if step_mode and step_callback and not is_pass:
                worst_v = top_v if not top_ok else bot_v
                tol = max(5, int(worst_v * 0.2))
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"top={top_v}, bottom={bot_v}",
                    "expected": f"{min_threshold}-{max_threshold} pixels (both)",
                    "suggested_min": max(1, min(top_v, bot_v) - tol),
                    "suggested_max": max(top_v, bot_v) + tol,
                    "debug_info": f"Top: {top_v}\nBottom: {bot_v}\n"
                }
                if not step_callback(step_result):
                    overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                overlay, reason = draw_test_result(
                    image, [f"{test_name}: top={top_v}, bottom={bot_v} (Allowed {min_threshold}-{max_threshold})"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (top={top_v}, bottom={bot_v})")

        elif measurement_func == "measure_term_to_body_gap":
            # Measure worst-case (minimum) terminal-to-body gap and compare with min requirement
            gap_val = measure_term_to_body_gap(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                edge_contrast=edge_contrast_value,
                num_scans=60,
                debug=True
            )
            if gap_val is None:
                print(f"[FAIL] {test_name} not detected")
                overlay, reason = draw_test_result(image, [f"{test_name} not detected"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} detect fail", overlay)

            # only min threshold for gap
            min_key = "term_body_gap_min"
            edge_key = "term_body_gap_edge"
            min_required = device_thresholds.get(min_key, "255") if device_thresholds else "255"
            try:
                min_required = None if (min_required == "255" or min_required == "") else int(min_required)
            except ValueError:
                min_required = None

            # Prefer explicit gap edge contrast if provided
            gap_edge = device_thresholds.get(edge_key, "255") if device_thresholds else "255"
            if gap_edge not in ("255", "", None):
                try:
                    edge_contrast_value = int(gap_edge)
                except ValueError:
                    pass

            if min_required is None:
                # If not configured, just report and continue
                print(f"[SKIP] {test_name} min not configured; measured={gap_val}")
                messages.append(f"{test_name} SKIPPED (measured {gap_val})")
            else:
                is_pass = gap_val >= min_required
                if step_mode and step_callback and not is_pass:
                    step_result = {
                        "step_name": test_name,
                        "status": "FAIL",
                        "measured": f"gap={gap_val}",
                        "expected": f">= {min_required} px",
                        "suggested_min": max(1, gap_val - 1),
                        "suggested_max": None,
                        "debug_info": f"Measured minimum gap: {gap_val}\nCurrent minimum: {min_required}"
                    }
                    if not step_callback(step_result):
                        overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                        return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

                if not is_pass:
                    overlay, reason = draw_test_result(image, [f"{test_name}: gap={gap_val} (Min {min_required})"], "FAIL")
                    return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

                messages.append(f"{test_name} OK (gap={gap_val})")

        else:
            value = None

        if measurement_func in ("measure_body_width", "measure_body_length", "measure_terminal_width", 
                               "measure_terminal_length", "measure_term_to_term_length"):
            if value is None:
                print(f"[FAIL] {test_name} not detected")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name} not detected"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} detect fail", overlay)

            print(f"[INFO] {test_name} measured = {value}")

            # thresholds from device_inspection.json first
            min_threshold = None
            max_threshold = None
            threshold_source = "params"

            if device_thresholds:
                try:
                    min_val = device_thresholds.get(metric_key_min, "")
                    max_val = device_thresholds.get(metric_key_max_from_dev, "")
                    if min_val and min_val != "255":
                        min_threshold = int(min_val)
                    if max_val and max_val != "255":
                        max_threshold = int(max_val)
                    if (min_threshold is not None) or (max_threshold is not None):
                        threshold_source = "device_inspection.json"
                except ValueError:
                    pass

            # fallback to params
            if min_threshold is None:
                min_threshold = int(fallback_min) if fallback_min else None
            else:
                min_threshold = int(min_threshold)
            if max_threshold is None:
                max_threshold = int(fallback_max) if fallback_max else None
            else:
                max_threshold = int(max_threshold)

            # Scale-aware sanity check: adjust thresholds if they are
            # unrealistic for current image resolution.
            # IMPORTANT: Only apply if thresholds came from params fallback.
            # If they came from device_inspection.json, trust them explicitly.
            roi_w = params.package_w
            if roi_w and (min_threshold is not None) and (max_threshold is not None) and threshold_source == "params":
                too_large = (int(min_threshold) > int(roi_w * 1.2)) or (int(max_threshold) > int(roi_w * 1.2))
                if too_large:
                    min_threshold = int(roi_w * 0.55)
                    max_threshold = int(roi_w * 0.90)
                    threshold_source = "scaled_by_roi"

            print(f"[INFO] Allowed = {min_threshold} - {max_threshold} (from {threshold_source})")

            # ===== STEP MODE: Only show dialog for FAILED steps =====
            is_pass = (min_threshold <= value <= max_threshold)
            if step_mode and step_callback and not is_pass:
                # Calculate suggested thresholds based on measured value
                # Add tolerance buffer (±20% or ±10 pixels, whichever is larger)
                tolerance = max(10, int(value * 0.20))
                suggested_min = max(1, value - tolerance)
                suggested_max = value + tolerance
                
                # Only show dialog for FAIL with suggested adjustments
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"{value} pixels",
                    "expected": f"{min_threshold} - {max_threshold} pixels",
                    "suggested_min": suggested_min,
                    "suggested_max": suggested_max,
                    "debug_info": f"Measured: {value}\nCurrent Min: {min_threshold}\nCurrent Max: {max_threshold}\n\nSuggested Min: {suggested_min}\nSuggested Max: {suggested_max}\n\nSource: {threshold_source}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
            # =====================================================

            # Draw green boxes for PASS, red for FAIL
            if is_pass and step_mode:
                # For PASS: draw the measurement overlays
                points_data = {}
                if measurement_func == "measure_body_length":
                    points_data = {
                        "left_x": params.package_x + (params.package_w * 0.25),
                        "right_x": params.package_x + (params.package_w * 0.75),
                        "center_y": params.package_y + (params.package_h / 2)
                    }
                elif measurement_func == "measure_body_width":
                    points_data = {
                        "top_y": params.package_y + (params.package_h * 0.25),
                        "bottom_y": params.package_y + (params.package_h * 0.75),
                        "center_x": params.package_x + (params.package_w / 2)
                    }

                image = draw_measurement_result(
                    image,
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    test_name,
                    "PASS",
                    value,
                    min_threshold,
                    max_threshold,
                    points_data
                )

            if not is_pass:
                print(f"[FAIL] {test_name} out of range")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {value} (Expected: {min_threshold}-{max_threshold})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK ({value})")
        elif measurement_func == "measure_body_to_term_width":
            result = measure_body_to_term_width(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                edge_contrast=edge_contrast_value,
                num_scans=60,
                debug=True
            )
            top_v = result.get('top')
            bot_v = result.get('bottom')
            if top_v is None or bot_v is None:
                overlay, reason = draw_test_result(image, [f"{test_name} not detected"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} detect fail", overlay)

            min_threshold = device_thresholds.get("body_to_term_min", "255") if device_thresholds else "255"
            max_threshold = device_thresholds.get("body_to_term_max", "255") if device_thresholds else "255"
            try:
                min_threshold = int(min_threshold) if min_threshold != "255" and min_threshold != "" else 10
                max_threshold = int(max_threshold) if max_threshold != "255" and max_threshold != "" else 50
            except ValueError:
                min_threshold, max_threshold = 10, 50

            print(f"[INFO] {test_name} top={top_v}, bottom={bot_v} allowed={min_threshold}-{max_threshold}")
            is_pass = (min_threshold <= top_v <= max_threshold) and (min_threshold <= bot_v <= max_threshold)

            if step_mode and step_callback and not is_pass:
                worst_v = top_v if not (min_threshold <= top_v <= max_threshold) else bot_v
                tol = max(5, int(worst_v * 0.2))
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"top={top_v}, bottom={bot_v}",
                    "expected": f"{min_threshold}-{max_threshold}",
                    "suggested_min": max(1, min(top_v, bot_v) - tol),
                    "suggested_max": max(top_v, bot_v) + tol,
                }
                if not step_callback(step_result):
                    overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                overlay, reason = draw_test_result(image, [f"{test_name}: top={top_v}, bottom={bot_v} (Allowed {min_threshold}-{max_threshold})"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            messages.append(f"{test_name} OK (top={top_v}, bottom={bot_v})")

        elif measurement_func == "measure_term_to_body_gap":
            gap_val = measure_term_to_body_gap(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                edge_contrast=edge_contrast_value,
                num_scans=60,
                debug=True
            )
            if gap_val is None:
                overlay, reason = draw_test_result(image, [f"{test_name} not detected"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} detect fail", overlay)

            min_required = device_thresholds.get("term_body_gap_min", "255") if device_thresholds else "255"
            try:
                min_required = int(min_required) if min_required != "255" and min_required != "" else None
            except ValueError:
                min_required = None
            if min_required is None:
                print(f"[SKIP] {test_name} min not configured; measured={gap_val}")
                messages.append(f"{test_name} SKIPPED (measured {gap_val})")
            else:
                is_pass = gap_val >= min_required
                if step_mode and step_callback and not is_pass:
                    step_result = {
                        "step_name": test_name,
                        "status": "FAIL",
                        "measured": f"gap={gap_val}",
                        "expected": f">= {min_required} px",
                        "suggested_min": max(1, gap_val - 1),
                    }
                    if not step_callback(step_result):
                        overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                        return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
                if not is_pass:
                    overlay, reason = draw_test_result(image, [f"{test_name}: gap={gap_val} (Min {min_required})"], "FAIL")
                    return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
                messages.append(f"{test_name} OK (gap={gap_val})")
        elif measurement_func == "check_body_width_diff":
            # Body Width Difference: measure top and bottom body widths separately
            print(f"[INFO] Measuring Body Width Difference...")
            
            # Get tolerance from device_inspection.json
            tolerance_str = device_thresholds.get("body_width_diff_value", "255") if device_thresholds else "255"
            if tolerance_str == "255" or not tolerance_str:
                print(f"[SKIP] Body Width Diff tolerance not configured (value={tolerance_str})")
                messages.append(f"{test_name} SKIPPED (tolerance not set)")
                continue
            
            tolerance = float(tolerance_str)
            
            # Measure body width at top 25% region
            top_roi_height = int(params.package_h * 0.25)
            top_roi = (params.package_x, params.package_y, params.package_w, top_roi_height)
            top_width = measure_body_width(
                working_image,
                top_roi,
                body_contrast=params.ranges.get("body_contrast", 75),
                debug=True
            )
            
            # Measure body width at bottom 25% region
            bottom_roi_height = int(params.package_h * 0.25)
            bottom_roi = (params.package_x, params.package_y + params.package_h - bottom_roi_height, 
                         params.package_w, bottom_roi_height)
            bottom_width = measure_body_width(
                working_image,
                bottom_roi,
                body_contrast=params.ranges.get("body_contrast", 75),
                debug=True
            )
            
            if top_width is None or bottom_width is None:
                print(f"[FAIL] Body Width Diff measurement failed")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Measurement failed"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} measurement fail", overlay)
            
            # Check difference
            result = check_body_width_difference(top_width, bottom_width, tolerance, debug=True)
            
            print(f"[INFO] Top Width: {result['top']:.2f}, Bottom Width: {result['bottom']:.2f}")
            print(f"[INFO] Difference: {result['difference']:.2f}, Tolerance: {result['tolerance']:.2f}")
            
            # ===== STEP MODE: Show dialog for FAILED steps =====
            if step_mode and step_callback and not result['is_pass']:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Diff={result['difference']:.2f} (Top={result['top']:.2f}, Bottom={result['bottom']:.2f})",
                    "expected": f"< {tolerance:.2f} pixels",
                    "suggested_min": 0,
                    "suggested_max": int(result['difference'] * 1.5),
                    "debug_info": f"Top Width: {result['top']:.2f}\nBottom Width: {result['bottom']:.2f}\nDifference: {result['difference']:.2f}\nTolerance: {result['tolerance']:.2f}\n\nSuggested new tolerance: {int(result['difference'] * 1.5)}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
            
            if not result['is_pass']:
                print(f"[FAIL] Body Width Diff exceeds tolerance")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Diff={result['difference']:.2f} (Tolerance: {tolerance:.2f})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (Diff={result['difference']:.2f})")
        elif measurement_func == "check_terminal_length_diff":
            # Terminal Length Difference: measure left and right terminal lengths
            print(f"[INFO] Measuring Terminal Length Difference...")
            
            # Get tolerance from device_inspection.json
            tolerance_str = device_thresholds.get("terminal_length_diff_value", "255") if device_thresholds else "255"
            if tolerance_str == "255" or not tolerance_str:
                print(f"[SKIP] Terminal Length Diff tolerance not configured (value={tolerance_str})")
                messages.append(f"{test_name} SKIPPED (tolerance not set)")
                continue
            
            tolerance = float(tolerance_str)
            
            # Get edge contrast from pocket_params
            pocket_params = load_pocket_params()
            edge_contrast_value = 106  # default
            if pocket_params:
                edge_contrast_value = int(pocket_params.get("edge_contrast", 106))
            
            # Measure left terminal lengths (multiple scan lines)
            # Left terminal ROI: leftmost 30% of package, top 30% height
            left_terminal_roi = (
                params.package_x, 
                params.package_y, 
                int(params.package_w * 0.3), 
                int(params.package_h * 0.3)
            )
            
            # Right terminal ROI: rightmost 30% of package, top 30% height
            right_terminal_roi = (
                params.package_x + int(params.package_w * 0.7), 
                params.package_y, 
                int(params.package_w * 0.3), 
                int(params.package_h * 0.3)
            )
            
            # For now, measure single values for left and right
            # In the future, this should be enhanced to collect multiple measurements per side
            left_length = measure_terminal_length(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                left_terminal_roi,
                edge_contrast=edge_contrast_value,
                num_scans=100,
                debug=True
            )
            
            right_length = measure_terminal_length(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                right_terminal_roi,
                edge_contrast=edge_contrast_value,
                num_scans=100,
                debug=True
            )
            
            if left_length is None or right_length is None:
                print(f"[FAIL] Terminal Length Diff measurement failed")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Measurement failed"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} measurement fail", overlay)
            
            # For single measurement, create arrays with one element
            left_lengths = [left_length]
            right_lengths = [right_length]
            
            # Check difference
            result = check_terminal_length_difference(left_lengths, right_lengths, tolerance, debug=True)
            
            print(f"[INFO] Left Length: {result.get('worst_left', 0):.2f}, Right Length: {result.get('worst_right', 0):.2f}")
            print(f"[INFO] Max Difference: {result['max_difference']:.2f}, Tolerance: {result['tolerance']:.2f}")
            
            # ===== STEP MODE: Show dialog for FAILED steps =====
            if step_mode and step_callback and not result['is_pass']:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Diff={result['max_difference']:.2f} (Left={result.get('worst_left', 0):.2f}, Right={result.get('worst_right', 0):.2f})",
                    "expected": f"< {tolerance:.2f} pixels",
                    "suggested_min": 0,
                    "suggested_max": int(result['max_difference'] * 1.5),
                    "debug_info": f"Left Length: {result.get('worst_left', 0):.2f}\nRight Length: {result.get('worst_right', 0):.2f}\nMax Difference: {result['max_difference']:.2f}\nTolerance: {result['tolerance']:.2f}\n\nSuggested new tolerance: {int(result['max_difference'] * 1.5)}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
            
            if not result['is_pass']:
                print(f"[FAIL] Terminal Length Diff exceeds tolerance")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Diff={result['max_difference']:.2f} (Tolerance: {tolerance:.2f})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (Diff={result['max_difference']:.2f})")
        elif attr_name == "check_terminal_color":
            print(f"[INFO] Checking {test_name}...")

            ci_tab = device_thresholds.get("ColorInspectionTab", {}) if device_thresholds else {}
            contrast = int(ci_tab.get("ci_term_contrast", 255))
            left_width_cfg = int(ci_tab.get("ci_term_left_width", 255))
            right_width_cfg = int(ci_tab.get("ci_term_right_width", 255))
            offset_top = _ci_val(ci_tab, "ci_offset_top", 0)
            offset_bottom = _ci_val(ci_tab, "ci_offset_bottom", 0)
            offset_left = _ci_val(ci_tab, "ci_offset_left", 0)
            offset_right = _ci_val(ci_tab, "ci_offset_right", 0)

            if contrast == 255 and left_width_cfg == 255 and right_width_cfg == 255:
                print(f"[SKIP] {test_name} not configured")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            base_x = params.package_x + offset_left
            base_y = params.package_y + offset_top
            base_w = params.package_w - offset_left - offset_right
            base_h = params.package_h - offset_top - offset_bottom
            if base_w <= 0 or base_h <= 0:
                overlay, reason = draw_test_result(image, [f"{test_name}: Invalid ROI after offsets"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            left_w = left_width_cfg if left_width_cfg != 255 else int(base_w * 0.3)
            right_w = right_width_cfg if right_width_cfg != 255 else int(base_w * 0.3)

            left_roi = (base_x, base_y, left_w, base_h)
            right_roi = (base_x + base_w - right_w, base_y, right_w, base_h)

            left_mean = _safe_roi_mean_gray(working_image, left_roi)
            right_mean = _safe_roi_mean_gray(working_image, right_roi)
            if left_mean is None or right_mean is None:
                overlay, reason = draw_test_result(image, [f"{test_name}: ROI not found"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            window_min, window_max = _resolve_intensity_window(
                (left_mean + right_mean) / 2.0,
                getattr(params, "terminal_intensity_min", None),
                getattr(params, "terminal_intensity_max", None),
                contrast,
            )

            if window_min is None or window_max is None:
                print(f"[SKIP] {test_name} thresholds not set")
                messages.append(f"{test_name} SKIPPED (thresholds not set)")
                continue

            left_ok = window_min <= left_mean <= window_max
            right_ok = window_min <= right_mean <= window_max
            is_pass = left_ok and right_ok

            if step_mode:
                _draw_color_roi(image, left_roi, left_ok, "L")
                _draw_color_roi(image, right_roi, right_ok, "R")

            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"L={left_mean:.1f}, R={right_mean:.1f}",
                    "expected": f"{window_min}-{window_max}",
                    "suggested_min": max(0, int(min(left_mean, right_mean) - 5)),
                    "suggested_max": min(255, int(max(left_mean, right_mean) + 5)),
                    "debug_info": f"Left={left_mean:.1f}\nRight={right_mean:.1f}\nWindow={window_min}-{window_max}\nContrast={contrast}"
                }
                if not step_callback(step_result):
                    overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: L={left_mean:.1f}, R={right_mean:.1f} (Allowed {window_min}-{window_max})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (L={left_mean:.1f}, R={right_mean:.1f})")

        elif attr_name == "check_body_color":
            print(f"[INFO] Checking {test_name}...")

            ci_tab = device_thresholds.get("ColorInspectionTab", {}) if device_thresholds else {}
            contrast = int(ci_tab.get("ci_body_contrast", 255))
            roi_w_cfg = int(ci_tab.get("ci_body_width", 255))
            roi_h_cfg = int(ci_tab.get("ci_body_height", 255))
            offset_top = _ci_val(ci_tab, "ci_offset_top", 0)
            offset_bottom = _ci_val(ci_tab, "ci_offset_bottom", 0)
            offset_left = _ci_val(ci_tab, "ci_offset_left", 0)
            offset_right = _ci_val(ci_tab, "ci_offset_right", 0)

            if contrast == 255 and roi_w_cfg == 255 and roi_h_cfg == 255:
                print(f"[SKIP] {test_name} not configured")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            base_x = params.package_x + offset_left
            base_y = params.package_y + offset_top
            base_w = params.package_w - offset_left - offset_right
            base_h = params.package_h - offset_top - offset_bottom
            if base_w <= 0 or base_h <= 0:
                overlay, reason = draw_test_result(image, [f"{test_name}: Invalid ROI after offsets"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            roi_w = roi_w_cfg if roi_w_cfg != 255 else int(base_w * 0.5)
            roi_h = roi_h_cfg if roi_h_cfg != 255 else int(base_h * 0.5)

            roi_x = base_x + (base_w - roi_w) // 2
            roi_y = base_y + (base_h - roi_h) // 2
            roi = (roi_x, roi_y, roi_w, roi_h)

            mean_intensity = _safe_roi_mean_gray(working_image, roi)
            if mean_intensity is None:
                overlay, reason = draw_test_result(image, [f"{test_name}: ROI not found"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            window_min, window_max = _resolve_intensity_window(
                mean_intensity,
                getattr(params, "body_intensity_min", None),
                getattr(params, "body_intensity_max", None),
                contrast,
            )

            if window_min is None or window_max is None:
                print(f"[SKIP] {test_name} thresholds not set")
                messages.append(f"{test_name} SKIPPED (thresholds not set)")
                continue

            is_pass = window_min <= mean_intensity <= window_max

            if step_mode:
                _draw_color_roi(image, roi, is_pass, "BODY")

            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"{mean_intensity:.1f}",
                    "expected": f"{window_min}-{window_max}",
                    "suggested_min": max(0, int(mean_intensity - 5)),
                    "suggested_max": min(255, int(mean_intensity + 5)),
                    "debug_info": f"Mean={mean_intensity:.1f}\nWindow={window_min}-{window_max}\nContrast={contrast}"
                }
                if not step_callback(step_result):
                    overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {mean_intensity:.1f} (Allowed {window_min}-{window_max})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (mean={mean_intensity:.1f})")

        elif attr_name == "check_body_crack":
            # Body Crack - detect white cracks on body surface
            print(f"[INFO] Checking {test_name}...")
            
            # Parameters from device_inspection.json BodyCrackTab section
            bc_tab = device_thresholds.get("BodyCrackTab", {})
            contrast = int(bc_tab.get("bc_left_contrast", 255))
            min_length = int(bc_tab.get("bc_left_min_length", 255))
            min_elongation = float(bc_tab.get("bc_left_min_elongation", 255))
            broken_connection = int(bc_tab.get("bc_left_broken_connection", 0))
            offset_top = int(bc_tab.get("bc_offset_top", 0))
            offset_bottom = int(bc_tab.get("bc_offset_bottom", 0))
            offset_left = int(bc_tab.get("bc_offset_left", 0))
            offset_right = int(bc_tab.get("bc_offset_right", 0))
            low_high_enable = bool(bc_tab.get("bc_left_reject_enable", False))
            
            # Check if parameters are configured (255 = disabled/not configured)
            if contrast == 255 or (min_length == 255 and min_elongation == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_length={min_length}, min_elongation={min_elongation})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue
            
            # Provide defaults for unconfigured parameters
            if contrast == 255:
                contrast = 30  # default contrast
            if min_length == 255:
                min_length = 20  # default minimum length in pixels
            if min_elongation == 255:
                min_elongation = 5.0  # default elongation ratio
            if offset_top == 255:
                offset_top = 0
            if offset_bottom == 255:
                offset_bottom = 0
            if offset_left == 255:
                offset_left = 0
            if offset_right == 255:
                offset_right = 0
            
            defects_found, largest_length, is_pass, defect_rects = check_body_crack(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_length=min_length,
                min_elongation=min_elongation,
                broken_connection=broken_connection,
                detect_low_high=low_high_enable,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                debug=True
            )
            
            print(f"[INFO] {test_name}: defects={defects_found}, largest_length={largest_length}, pass={is_pass}")
            
            # Step mode dialog when failed
            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Cracks={defects_found}, Longest={largest_length}px",
                    "expected": f"Min Length < {min_length}px, Elongation > {min_elongation:.1f}",
                    "suggested_min": None,
                    "suggested_max": int(largest_length * 1.2) if largest_length > 0 else min_length,
                    "debug_info": f"Cracks Found: {defects_found}\nLongest Length: {largest_length}px\nMin Length Threshold: {min_length}px\nMin Elongation: {min_elongation:.1f}\nContrast: {contrast}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
            
            # Visualize defects on failure
            if not is_pass and defect_rects:
                print(f"[DEBUG] Drawing {len(defect_rects)} crack boxes")
                for rx, ry, rw, rh in defect_rects:
                    cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)
            
            if not is_pass:
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} cracks detected (longest={largest_length}px)"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK ({defects_found} cracks, max_length={largest_length}px)")
            
            # ---------------------------------
            # Body Hairline Crack (same tab)
            # ---------------------------------
            hair_contrast = int(bc_tab.get("bc_hair_contrast", 255))
            hair_min_length = int(bc_tab.get("bc_hair_min_length", 255))
            hair_noise = int(bc_tab.get("bc_hair_noise_filtering", 0))
            hair_white_enable = bool(bc_tab.get("bc_hair_white_enable", False))
            hair_black_enable = bool(bc_tab.get("bc_hair_black_enable", False))

            # Run hairline only if either polarity enabled
            if hair_white_enable or hair_black_enable:
                # Provide defaults if not configured
                if hair_contrast == 255:
                    hair_contrast = 30
                if hair_min_length == 255:
                    hair_min_length = 15
                if hair_noise == 255:
                    hair_noise = 0

                hl_defects, hl_length, hl_pass, hl_rects = check_body_hairline_crack(
                    working_image,
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    contrast=hair_contrast,
                    min_length=hair_min_length,
                    noise_filter_size=hair_noise,
                    detect_white=hair_white_enable,
                    detect_black=hair_black_enable,
                    offset_top=offset_top,
                    offset_bottom=offset_bottom,
                    offset_left=offset_left,
                    offset_right=offset_right,
                    debug=True
                )

                print(f"[INFO] Body Hairline Crack: defects={hl_defects}, longest={hl_length}, pass={hl_pass}")

                if step_mode and step_callback and not hl_pass:
                    step_result = {
                        "step_name": "Body Hairline Crack",
                        "status": "FAIL",
                        "measured": f"Cracks={hl_defects}, Longest={hl_length}px",
                        "expected": f"Min Length < {hair_min_length}px",
                        "suggested_min": None,
                        "suggested_max": int(hl_length * 1.2) if hl_length > 0 else hair_min_length,
                        "debug_info": f"Hairline Defects: {hl_defects}\nLongest: {hl_length}px\nContrast: {hair_contrast}\nMin Length: {hair_min_length}\nNoise Filter: {hair_noise}\nWhiteEnable: {hair_white_enable}\nBlackEnable: {hair_black_enable}"
                    }
                    if not step_callback(step_result):
                        print("[STEP] Test aborted by user at Body Hairline Crack")
                        overlay, reason = draw_test_result(
                            image,
                            ["Body Hairline Crack: Test paused for parameter adjustment"],
                            "PAUSE"
                        )
                        return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

                if not hl_pass:
                    if hl_rects:
                        for rx, ry, rw, rh in hl_rects:
                            cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)

                    overlay, reason = draw_test_result(
                        image,
                        [f"Body Hairline Crack: {hl_defects} cracks (longest={hl_length}px)"],
                        "FAIL"
                    )
                    return TestResult(TestStatus.FAIL, "Body Hairline Crack NG", overlay)

                messages.append(f"Body Hairline Crack OK ({hl_defects} cracks, max_length={hl_length}px)")
        
        elif attr_name == "check_edge_chipoff":
            # Edge Chipoff - detect broken defects on body edges (top/bottom)
            print(f"[INFO] Checking {test_name}...")

            ec_tab = device_thresholds.get("EdgeChipoff", {}) if device_thresholds else {}

            cb_top = int(ec_tab.get("ec_contrast_black_top", 20))
            cb_bot = int(ec_tab.get("ec_contrast_black_bot", 20))
            cw_top = int(ec_tab.get("ec_contrast_white_top", 25))
            cw_bot = int(ec_tab.get("ec_contrast_white_bot", 25))
            min_area = int(ec_tab.get("ec_min_area", 50))
            min_square = int(ec_tab.get("ec_min_square", 5))
            edge_width_top = int(ec_tab.get("ec_edge_width_top", 10))
            edge_width_bot = int(ec_tab.get("ec_edge_width_bot", 10))
            insp_offset_top = int(ec_tab.get("ec_insp_offset_top", 5))
            insp_offset_bot = int(ec_tab.get("ec_insp_offset_bot", 5))
            corner_mask_left = int(ec_tab.get("ec_corner_mask_left", 5))
            corner_mask_right = int(ec_tab.get("ec_corner_mask_right", 5))
            ignore_reflection = bool(ec_tab.get("ec_ignore_reflection", False))
            ignore_vertical_line = bool(ec_tab.get("ec_ignore_vertical_line", False))
            enable_high_contrast = bool(ec_tab.get("ec_enable_high_contrast", False))
            high_contrast_value = int(ec_tab.get("ec_high_contrast_value", 50))

            # Check if configured (any contrast value set)
            if cb_top == 255 and cb_bot == 255 and cw_top == 255 and cw_bot == 255:
                print(f"[SKIP] {test_name} not configured")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            # Apply defaults if needed
            if cb_top == 255:
                cb_top = 20
            if cb_bot == 255:
                cb_bot = 20
            if cw_top == 255:
                cw_top = 25
            if cw_bot == 255:
                cw_bot = 25
            if min_area == 255:
                min_area = 50
            if min_square == 255:
                min_square = 5

            defects_found, largest_area, is_pass, defect_rects = check_edge_chipoff(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast_black_top=cb_top,
                contrast_black_bot=cb_bot,
                contrast_white_top=cw_top,
                contrast_white_bot=cw_bot,
                min_area=min_area,
                min_square=min_square,
                edge_width_top=edge_width_top,
                edge_width_bot=edge_width_bot,
                insp_offset_top=insp_offset_top,
                insp_offset_bot=insp_offset_bot,
                corner_mask_left=corner_mask_left,
                corner_mask_right=corner_mask_right,
                ignore_reflection=ignore_reflection,
                ignore_vertical_line=ignore_vertical_line,
                enable_high_contrast=enable_high_contrast,
                high_contrast_value=high_contrast_value,
                debug=True
            )

            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}")

            # Draw inspection bands in step mode
            if step_mode:
                draw_edge_chipoff_bands(
                    image,
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    edge_width_top=edge_width_top,
                    edge_width_bot=edge_width_bot,
                    insp_offset_top=insp_offset_top,
                    insp_offset_bot=insp_offset_bot,
                    corner_mask_left=corner_mask_left,
                    corner_mask_right=corner_mask_right,
                    color=(0, 255, 0),
                    thickness=2
                )

            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": f"Area < {min_area}, Size < {min_square}",
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Contrast Black T{cb_top} B{cb_bot}\nContrast White T{cw_top} B{cw_bot}\nMinArea={min_area}\nMinSquare={min_square}\nEdge Width T{edge_width_top} B{edge_width_bot}\nInsp Offset T{insp_offset_top} B{insp_offset_bot}\nCorner Mask L{corner_mask_left} R{corner_mask_right}\nIgnore Reflection={ignore_reflection}\nIgnore Vertical Line={ignore_vertical_line}\nHigh Contrast={enable_high_contrast} ({high_contrast_value})"
                }
                if not step_callback(step_result):
                    overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                # Draw defect rectangles
                if defect_rects:
                    for rx, ry, rw, rh in defect_rects:
                        cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)
                
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px)"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK ({defects_found} defects, largest={largest_area}px)")
        
        elif attr_name == "check_terminal_pogo":
            # Terminal Pogo - detect black defects (pogo holes) in terminal areas
            print(f"[INFO] Checking {test_name}...")

            # Parameters from device_inspection.json MultiTerminal section
            mt_tab = device_thresholds.get("MultiTerminal", {})
            contrast = int(mt_tab.get("mt_pogo_contrast", 255))
            min_area = int(mt_tab.get("mt_pogo_min_area", 255))
            min_square = int(mt_tab.get("mt_pogo_min_square", 255))
            offset_left = int(mt_tab.get("mt_pogo_corner_mask_left", 0))
            offset_right = int(mt_tab.get("mt_pogo_corner_mask_right", 0))

            # Check if parameters are configured
            if contrast == 255 or (min_area == 255 and min_square == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area}, min_square={min_square})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            defects_found, largest_area, is_pass, defect_rects = check_terminal_pogo(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
                min_square=min_square,
                offset_top=0,
                offset_bottom=0,
                offset_left=offset_left,
                offset_right=offset_right,
                apply_or=True,
                debug=True
            )

            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}")

            # Step mode dialog when failed
            if step_mode and step_callback and not is_pass:
                expected_txt = f"Area < {min_area}px"
                if min_square != 255:
                    expected_txt += f" and W/H < {min_square}px"
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": expected_txt,
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Defects Found: {defects_found}\nLargest Area: {largest_area}px\nMin Area Threshold: {min_area}px\nMin Square Threshold: {min_square}px\nContrast: {contrast}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            # Visualize defects on failure
            if not is_pass and defect_rects:
                print(f"[DEBUG] Drawing {len(defect_rects)} defect boxes")
                for rx, ry, rw, rh in defect_rects:
                    cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)

            if not is_pass:
                limit_txt = f"max area={min_area}px"
                if min_square != 255:
                    limit_txt += f", max W/H={min_square}px"
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px, {limit_txt})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (defects={defects_found})")
        elif attr_name == "check_inner_term_chipoff":
            print(f"[INFO] Checking {test_name}...")

            tc_tab = device_thresholds.get("TerminalChipoff", {}) if device_thresholds else {}

            contrast = int(tc_tab.get("tc_inner_contrast", 255))
            min_area = int(tc_tab.get("tc_inner_min_area", 255))
            min_square = int(tc_tab.get("tc_inner_min_square", 255))
            inspection_width_x = int(tc_tab.get("tc_inner_inspection_width_x", 80))
            inspection_width_y = int(tc_tab.get("tc_inner_inspection_width_y", 40))
            corner_ellipse_mask = int(tc_tab.get("tc_inner_corner_ellipse_mask", 0))
            enable_corner_offset = bool(tc_tab.get("tc_inner_enable_corner_offset", False))
            corner_offset_x = int(tc_tab.get("tc_inner_corner_offset_x", 0))
            corner_offset_y = int(tc_tab.get("tc_inner_corner_offset_y", 0))
            offset_top = int(tc_tab.get("tc_inner_offset_top", 0))
            offset_bottom = int(tc_tab.get("tc_inner_offset_bottom", 0))
            offset_left = int(tc_tab.get("tc_inner_offset_left", 0))
            offset_right = int(tc_tab.get("tc_inner_offset_right", 0))

            if contrast == 255 or (min_area == 255 and min_square == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area}, min_square={min_square})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            if contrast == 255:
                contrast = 30
            if min_area == 255:
                min_area = 50
            if min_square == 255:
                min_square = 5

            # Check if pocket edge filter is enabled
            enable_pocket_filter = bool(tc_tab.get("tc_inner_enable_pocket_filter", False))
            pocket_roi = (params.pocket_x, params.pocket_y, params.pocket_w, params.pocket_h) if enable_pocket_filter and hasattr(params, 'pocket_x') else None

            defects_found, largest_area, is_pass, defect_rects = check_terminal_chipoff_inner(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
                min_square=min_square,
                inspection_width_x=inspection_width_x,
                inspection_width_y=inspection_width_y,
                corner_ellipse_mask=corner_ellipse_mask,
                enable_corner_offset=enable_corner_offset,
                corner_offset_x=corner_offset_x,
                corner_offset_y=corner_offset_y,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                apply_or=True,
                enable_pocket_edge_filter=enable_pocket_filter,
                pocket_roi=pocket_roi,
                debug=True
            )

            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}, pocket_filter={enable_pocket_filter}")

            # Draw inspection bands in step mode
            if step_mode:
                draw_chipoff_inspection_bands(
                    image, 
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    band_type='inner',
                    inspection_width_x=inspection_width_x,
                    inspection_width_y=inspection_width_y,
                    offset_top=offset_top,
                    offset_bottom=offset_bottom,
                    offset_left=offset_left,
                    offset_right=offset_right,
                    enable_corner_offset=enable_corner_offset,
                    corner_offset_x=corner_offset_x,
                    corner_offset_y=corner_offset_y,
                    color=(0, 255, 255),
                    thickness=2
                )

            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": f"Area < {min_area}, Size < {min_square}",
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Contrast={contrast}\nMinArea={min_area}\nMinSquare={min_square}\nInspection Width X={inspection_width_x} Y={inspection_width_y}\nCorner Ellipse Mask={corner_ellipse_mask}\nCorner Offset Mode={'Chamfered' if enable_corner_offset else 'Rectangular'}\nOffsets T{offset_top} B{offset_bottom} L{offset_left} R{offset_right}"
                }
                if not step_callback(step_result):
                    overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                if defect_rects:
                    for rx, ry, rw, rh in defect_rects:
                        cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px)"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK ({defects_found} defects, largest={largest_area}px)")

        elif attr_name == "check_outer_term_chipoff":
            print(f"[INFO] Checking {test_name}...")

            tc_tab = device_thresholds.get("TerminalChipoff", {}) if device_thresholds else {}

            contrast = int(tc_tab.get("tc_outer_contrast", 255))
            min_area = int(tc_tab.get("tc_outer_min_area", 255))
            min_square = int(tc_tab.get("tc_outer_min_square", 255))
            offset_top = int(tc_tab.get("tc_outer_offset_top", 0))
            offset_bottom = int(tc_tab.get("tc_outer_offset_bottom", 0))
            offset_left = int(tc_tab.get("tc_outer_offset_left", 0))
            offset_right = int(tc_tab.get("tc_outer_offset_right", 0))
            band_width_ratio = float(tc_tab.get("tc_outer_band_width_ratio", 0.25))

            if contrast == 255 or (min_area == 255 and min_square == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area}, min_square={min_square})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            if contrast == 255:
                contrast = 30
            if min_area == 255:
                min_area = 50
            if min_square == 255:
                min_square = 5
            if band_width_ratio <= 0 or band_width_ratio > 0.5:
                band_width_ratio = 0.25

            # Check if pocket edge filter is enabled
            enable_pocket_filter = bool(tc_tab.get("tc_outer_enable_pocket_filter", False))
            pocket_roi = (params.pocket_x, params.pocket_y, params.pocket_w, params.pocket_h) if enable_pocket_filter and hasattr(params, 'pocket_x') else None

            defects_found, largest_area, is_pass, defect_rects = check_terminal_chipoff_outer(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
                min_square=min_square,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                band_width_ratio=band_width_ratio,
                apply_or=True,
                enable_pocket_edge_filter=enable_pocket_filter,
                pocket_roi=pocket_roi,
                debug=True
            )

            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}, pocket_filter={enable_pocket_filter}")

            # Draw inspection bands in step mode
            if step_mode:
                draw_chipoff_inspection_bands(
                    image, 
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    band_type='outer',
                    band_width_ratio=band_width_ratio,
                    offset_top=offset_top,
                    offset_bottom=offset_bottom,
                    offset_left=offset_left,
                    offset_right=offset_right,
                    color=(0, 255, 255),
                    thickness=2
                )

            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": f"Area < {min_area}, Size < {min_square}",
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Contrast={contrast}\nMinArea={min_area}\nMinSquare={min_square}\nOffsets T{offset_top} B{offset_bottom} L{offset_left} R{offset_right}\nBandWidthRatio={band_width_ratio}"
                }
                if not step_callback(step_result):
                    overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                if defect_rects:
                    for rx, ry, rw, rh in defect_rects:
                        cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px)"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK ({defects_found} defects, largest={largest_area}px)")

        elif attr_name == "check_compare_terminal_corner":
            # Compare Terminal Corner - compare left/right terminal brightness
            print(f"[INFO] Checking {test_name}...")

            tc_tab = device_thresholds.get("TerminalChipoff", {}) if device_thresholds else {}

            manually_difference = int(tc_tab.get("tc_compare_corner_diff", 20))
            offset_top = int(tc_tab.get("tc_compare_offset_top", 0))
            offset_bottom = int(tc_tab.get("tc_compare_offset_bottom", 0))
            offset_left = int(tc_tab.get("tc_compare_offset_left", 0))
            offset_right = int(tc_tab.get("tc_compare_offset_right", 0))
            corner_width_ratio = float(tc_tab.get("tc_compare_corner_width_ratio", 0.15))

            if manually_difference == 255:
                print(f"[SKIP] {test_name} not configured (manually_difference={manually_difference})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            if manually_difference == 255:
                manually_difference = 20
            if corner_width_ratio <= 0 or corner_width_ratio > 0.5:
                corner_width_ratio = 0.15

            left_avg, right_avg, difference, is_pass = check_compare_terminal_corner(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                manually_difference=manually_difference,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                corner_width_ratio=corner_width_ratio,
                debug=True
            )

            print(f"[INFO] {test_name}: left={left_avg}, right={right_avg}, diff={difference}, threshold={manually_difference}, pass={is_pass}")

            # Draw corner regions in step mode
            if step_mode:
                draw_terminal_corner_regions(
                    image,
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    corner_width_ratio=corner_width_ratio,
                    offset_top=offset_top,
                    offset_bottom=offset_bottom,
                    offset_left=offset_left,
                    offset_right=offset_right,
                    color=(255, 255, 0),
                    thickness=2
                )

            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Left={left_avg}, Right={right_avg}, Diff={difference}",
                    "expected": f"Difference <= {manually_difference}",
                    "suggested_min": None,
                    "suggested_max": int(difference * 1.2) if difference > 0 else manually_difference,
                    "debug_info": f"Left Average={left_avg}\nRight Average={right_avg}\nDifference={difference}\nThreshold={manually_difference}\nCorner Width Ratio={corner_width_ratio}"
                }
                if not step_callback(step_result):
                    overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: L={left_avg}, R={right_avg}, diff={difference} (max={manually_difference})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (L={left_avg}, R={right_avg}, diff={difference})")

        elif attr_name == "check_black_pixels_count":
            # Black Pixels Count - count black pixels in terminal bands
            print(f"[INFO] Checking {test_name}...")

            tc_tab = device_thresholds.get("TerminalChipoff", {}) if device_thresholds else {}

            contrast = int(tc_tab.get("tc_black_pixels_contrast", 255))
            level = int(tc_tab.get("tc_black_pixels_level", 255))
            width_left = int(tc_tab.get("tc_black_pixels_width_left", 15))
            width_right = int(tc_tab.get("tc_black_pixels_width_right", 15))
            width_top = int(tc_tab.get("tc_black_pixels_width_top", 15))
            width_bottom = int(tc_tab.get("tc_black_pixels_width_bottom", 15))

            if contrast == 255 or level == 255:
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, level={level})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            if contrast == 255:
                contrast = 30
            if level == 255:
                level = 100

            total_black, max_side, is_pass, side_counts = check_black_pixels_count(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                level=level,
                inspection_width_left=width_left,
                inspection_width_right=width_right,
                inspection_width_top=width_top,
                inspection_width_bottom=width_bottom,
                debug=True
            )

            print(f"[INFO] {test_name}: total={total_black}, max_side={max_side}, level={level}, pass={is_pass}")

            # Draw black pixels bands in step mode
            if step_mode:
                draw_black_pixels_bands(
                    image,
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    inspection_width_left=width_left,
                    inspection_width_right=width_right,
                    inspection_width_top=width_top,
                    inspection_width_bottom=width_bottom,
                    color=(255, 0, 255),
                    thickness=1
                )

            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Total={total_black}, Max Side={max_side}",
                    "expected": f"Max Side <= {level}",
                    "suggested_min": None,
                    "suggested_max": int(max_side * 1.2) if max_side > 0 else level,
                    "debug_info": f"Total Black Pixels={total_black}\nMax Side Count={max_side}\nLevel Threshold={level}\nContrast={contrast}\nSide Counts: {side_counts}"
                }
                if not step_callback(step_result):
                    overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: max_side={max_side} exceeds level={level}", f"Sides: {side_counts}"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (total={total_black}, max={max_side})")

        elif attr_name == "check_terminal_offset":
            # Terminal Offset - verify terminals are within expected offset boundaries
            print(f"[INFO] Checking {test_name}...")

            # Parameters from device_inspection.json TerminalPlatingTab
            tp_tab = device_thresholds.get("TerminalPlatingTab", {})
            
            # LEFT terminal offsets
            left_top = int(tp_tab.get("tpd_left_off_top", 0))
            left_bottom = int(tp_tab.get("tpd_left_off_bottom", 0))
            left_left = int(tp_tab.get("tpd_left_off_left", 0))
            left_right = int(tp_tab.get("tpd_left_off_right", 0))
            left_corner_x = int(tp_tab.get("tpd_left_corner_mask_x", 0))
            left_corner_y = int(tp_tab.get("tpd_left_corner_mask_y", 0))
            
            # RIGHT terminal offsets
            right_top = int(tp_tab.get("tpd_right_off_top", left_top))
            right_bottom = int(tp_tab.get("tpd_right_off_bottom", left_bottom))
            right_left = int(tp_tab.get("tpd_right_off_left", left_left))
            right_right = int(tp_tab.get("tpd_right_off_right", left_right))
            right_corner_x = int(tp_tab.get("tpd_right_corner_mask_x", left_corner_x))
            right_corner_y = int(tp_tab.get("tpd_right_corner_mask_y", left_corner_y))

            # Check if parameters are configured
            if all(x == 0 for x in [left_top, left_bottom, left_left, left_right, right_top, right_bottom, right_left, right_right]):
                print(f"[SKIP] {test_name} not configured (all offsets=0)")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            is_pass, debug_info = check_terminal_offset(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                left_top=left_top,
                left_bottom=left_bottom,
                left_left=left_left,
                left_right=left_right,
                left_corner_x=left_corner_x,
                left_corner_y=left_corner_y,
                right_top=right_top,
                right_bottom=right_bottom,
                right_left=right_left,
                right_right=right_right,
                right_corner_x=right_corner_x,
                right_corner_y=right_corner_y,
                debug=True
            )

            print(f"[INFO] {test_name}: left_valid={debug_info['left_valid']}, right_valid={debug_info['right_valid']}, pass={is_pass}")

            # Step mode dialog when failed
            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Left Valid: {debug_info['left_valid']}, Right Valid: {debug_info['right_valid']}",
                    "expected": "Both terminals within offset boundaries",
                    "suggested_min": None,
                    "suggested_max": None,
                    "debug_info": f"Left Info: {debug_info['left_info']}\nRight Info: {debug_info['right_info']}\nLeft ROI: {debug_info['left_roi']}\nRight ROI: {debug_info['right_roi']}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                failed_msg = []
                if not debug_info['left_valid']:
                    failed_msg.append(f"Left terminal invalid ({debug_info['left_info']})")
                if not debug_info['right_valid']:
                    failed_msg.append(f"Right terminal invalid ({debug_info['right_info']})")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: " + ", ".join(failed_msg)],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (terminals within bounds)")
        elif attr_name == "check_incomplete_termination_1":
            # Incomplete Termination 1 - black defects in terminal bands (top/bottom)
            print(f"[INFO] Checking {test_name}...")

            # Parameters from Inspection Range dialog (min/max). Use 'max' as configured threshold.
            contrast = int(params.ranges.get("incomplete_termination_contrast_max", 255))
            min_area = int(params.ranges.get("incomplete_termination_min_area_max", 255))
            min_square = int(params.ranges.get("incomplete_termination_min_sqr_size_max", 255))
            offset_top = int(params.ranges.get("incomplete_termination_top_max", 0))
            offset_bottom = int(params.ranges.get("incomplete_termination_bottom_max", 0))
            offset_left = int(params.ranges.get("incomplete_termination_left_max", 0))
            offset_right = int(params.ranges.get("incomplete_termination_right_max", 0))
            corner_x = int(params.ranges.get("corner_offset_x_max", 0))
            corner_y = int(params.ranges.get("corner_offset_y_max", 0))

            if contrast == 255 or (min_area == 255 and min_square == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area}, min_square={min_square})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            defects_found, largest_area, is_pass, defect_rects = check_incomplete_termination_1(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
                min_square=min_square,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                corner_x=corner_x,
                corner_y=corner_y,
                apply_or=True,
                debug=True
            )

            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}")

            # Step mode dialog when failed
            if step_mode and step_callback and not is_pass:
                expected_txt = f"Area < {min_area}px"
                if min_square != 255:
                    expected_txt += f" and W/H < {min_square}px"
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": expected_txt,
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Defects Found: {defects_found}\nLargest Area: {largest_area}px\nMin Area Threshold: {min_area}px\nMin Square Threshold: {min_square}px\nContrast: {contrast}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            # Visualize defects on failure
            if not is_pass and defect_rects:
                print(f"[DEBUG] Drawing {len(defect_rects)} defect boxes")
                for rx, ry, rw, rh in defect_rects:
                    cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)

            if not is_pass:
                limit_txt = f"max area={min_area}px"
                if min_square != 255:
                    limit_txt += f", max W/H={min_square}px"
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px, {limit_txt})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (defects={defects_found})")
        elif attr_name == "check_incomplete_termination_2":
            # Incomplete Termination 2 - per terminal with corner offsets
            print(f"[INFO] Checking {test_name}...")

            contrast = int(params.ranges.get("incomplete_termination_contrast_max", 255))
            min_area = int(params.ranges.get("incomplete_termination_min_area_max", 255))
            min_square = int(params.ranges.get("incomplete_termination_min_sqr_size_max", 255))
            # Left terminal offsets
            left_top = int(params.ranges.get("left_terminal_top_max", params.ranges.get("incomplete_termination_top_max", 0)))
            left_bottom = int(params.ranges.get("left_terminal_bottom_max", params.ranges.get("incomplete_termination_bottom_max", 0)))
            left_left = int(params.ranges.get("left_terminal_left_max", params.ranges.get("incomplete_termination_left_max", 0)))
            left_right = int(params.ranges.get("left_terminal_right_max", params.ranges.get("incomplete_termination_right_max", 0)))
            # Right terminal offsets
            right_top = int(params.ranges.get("right_terminal_top_max", left_top))
            right_bottom = int(params.ranges.get("right_terminal_bottom_max", left_bottom))
            right_left = int(params.ranges.get("right_terminal_left_max", left_left))
            right_right = int(params.ranges.get("right_terminal_right_max", left_right))
            # Corner chamfer offsets
            corner_x = int(params.ranges.get("corner_offset_x_max", 0))
            corner_y = int(params.ranges.get("corner_offset_y_max", 0))

            if contrast == 255 or (min_area == 255 and min_square == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area}, min_square={min_square})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            defects_found, largest_area, is_pass, defect_rects = check_incomplete_termination_2(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
                min_square=min_square,
                left_top=left_top,
                left_bottom=left_bottom,
                left_left=left_left,
                left_right=left_right,
                right_top=right_top,
                right_bottom=right_bottom,
                right_left=right_left,
                right_right=right_right,
                corner_x=corner_x,
                corner_y=corner_y,
                apply_or=True,
                debug=True
            )

            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}")

            if step_mode and step_callback and not is_pass:
                expected_txt = f"Area < {min_area}px"
                if min_square != 255:
                    expected_txt += f" and W/H < {min_square}px"
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": expected_txt,
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Defects Found: {defects_found}\nLargest Area: {largest_area}px\nMin Area Threshold: {min_area}px\nMin Square Threshold: {min_square}px\nContrast: {contrast}\nCorner Offsets: {corner_x},{corner_y}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass and defect_rects:
                for rx, ry, rw, rh in defect_rects:
                    cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)

            if not is_pass:
                limit_txt = f"max area={min_area}px"
                if min_square != 255:
                    limit_txt += f", max W/H={min_square}px"
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px, {limit_txt})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (defects={defects_found})")
        elif attr_name == "check_incomplete_termination_2":
            # Incomplete Termination 2 - per terminal with corner offsets (FEED)
            print(f"[INFO] Checking {test_name}...")

            contrast = int(params.ranges.get("incomplete_termination_contrast_max", 255))
            min_area = int(params.ranges.get("incomplete_termination_min_area_max", 255))
            min_square = int(params.ranges.get("incomplete_termination_min_sqr_size_max", 255))
            left_top = int(params.ranges.get("left_terminal_top_max", params.ranges.get("incomplete_termination_top_max", 0)))
            left_bottom = int(params.ranges.get("left_terminal_bottom_max", params.ranges.get("incomplete_termination_bottom_max", 0)))
            left_left = int(params.ranges.get("left_terminal_left_max", params.ranges.get("incomplete_termination_left_max", 0)))
            left_right = int(params.ranges.get("left_terminal_right_max", params.ranges.get("incomplete_termination_right_max", 0)))
            right_top = int(params.ranges.get("right_terminal_top_max", left_top))
            right_bottom = int(params.ranges.get("right_terminal_bottom_max", left_bottom))
            right_left = int(params.ranges.get("right_terminal_left_max", left_left))
            right_right = int(params.ranges.get("right_terminal_right_max", left_right))
            corner_x = int(params.ranges.get("corner_offset_x_max", 0))
            corner_y = int(params.ranges.get("corner_offset_y_max", 0))

            if contrast == 255 or (min_area == 255 and min_square == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area}, min_square={min_square})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            defects_found, largest_area, is_pass, defect_rects = check_incomplete_termination_2(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
                min_square=min_square,
                left_top=left_top,
                left_bottom=left_bottom,
                left_left=left_left,
                left_right=left_right,
                right_top=right_top,
                right_bottom=right_bottom,
                right_left=right_left,
                right_right=right_right,
                corner_x=corner_x,
                corner_y=corner_y,
                apply_or=True,
                debug=True
            )

            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}")

            if step_mode and step_callback and not is_pass:
                expected_txt = f"Area < {min_area}px"
                if min_square != 255:
                    expected_txt += f" and W/H < {min_square}px"
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": expected_txt,
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Defects Found: {defects_found}\nLargest Area: {largest_area}px\nMin Area Threshold: {min_area}px\nMin Square Threshold: {min_square}px\nContrast: {contrast}\nCorner Offsets: {corner_x},{corner_y}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass and defect_rects:
                for rx, ry, rw, rh in defect_rects:
                    cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)

            if not is_pass:
                limit_txt = f"max area={min_area}px"
                if min_square != 255:
                    limit_txt += f", max W/H={min_square}px"
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px, {limit_txt})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (defects={defects_found})")
        elif attr_name == "check_terminal_oxidation":
            # Terminal Oxidation - detect color change (oxidation) in terminal
            print(f"[INFO] Checking {test_name}...")

            # Parameters from device_inspection.json TerminalPlatingTab
            tp_tab = device_thresholds.get("TerminalPlatingTab", {})
            
            teach_contrast = int(tp_tab.get("tpd_oxidation_teach_contrast", 128))
            contrast_difference = int(tp_tab.get("tpd_oxidation_contrast_diff", 20))
            offset_top = int(tp_tab.get("tpd_oxidation_off_top", 0))
            offset_bottom = int(tp_tab.get("tpd_oxidation_off_bottom", 0))
            offset_left = int(tp_tab.get("tpd_oxidation_off_left", 0))
            offset_right = int(tp_tab.get("tpd_oxidation_off_right", 0))
            corner_x = int(tp_tab.get("tpd_oxidation_corner_x", 0))
            corner_y = int(tp_tab.get("tpd_oxidation_corner_y", 0))

            # Check if parameters are configured
            if teach_contrast == 255 or contrast_difference == 255:
                print(f"[SKIP] {test_name} not configured (teach={teach_contrast}, diff={contrast_difference})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            measured_contrast, difference, is_pass = check_terminal_oxidation(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                teach_contrast=teach_contrast,
                contrast_difference=contrast_difference,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                corner_x=corner_x,
                corner_y=corner_y,
                debug=True
            )

            print(f"[INFO] {test_name}: measured={measured_contrast}, taught={teach_contrast}, diff={difference}, threshold={contrast_difference}, pass={is_pass}")

            # Step mode dialog when failed
            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Contrast={measured_contrast}, Diff={difference}",
                    "expected": f"Within ±{contrast_difference} of {teach_contrast}",
                    "suggested_min": None,
                    "suggested_max": None,
                    "debug_info": f"Taught Contrast: {teach_contrast}\nMeasured Contrast: {measured_contrast}\nDifference: {difference}\nThreshold: {contrast_difference}\n\nSuggested new teach_contrast: {measured_contrast}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                print(f"[FAIL] {test_name} - oxidation detected")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Oxidation detected (Contrast={measured_contrast}, Expected={teach_contrast}±{contrast_difference})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (contrast={measured_contrast}, diff={difference})")
        elif attr_name in ("check_body_stain_1", "check_body_stain_2"):
            # Body Stain detection - check for black defects on body surface
            print(f"[INFO] Checking {test_name}...")
            
            # Determine which stain check (1 or 2)
            stain_num = attr_name[-1]  # Extract '1' or '2'
            
            # Get parameters from device_inspection.json BodyStainTab
            body_stain_tab = device_thresholds.get("BodyStainTab", {})
            
            contrast = int(body_stain_tab.get(f"bs{stain_num}_contrast", 255))
            min_area = int(body_stain_tab.get(f"bs{stain_num}_min_area", 255))
            min_square = int(body_stain_tab.get(f"bs{stain_num}_min_square", 255))
            apply_or = bool(body_stain_tab.get(f"bs{stain_num}_apply_or", True))
            offset_top = int(body_stain_tab.get(f"bs{stain_num}_off_top", 5))
            offset_bottom = int(body_stain_tab.get(f"bs{stain_num}_off_bottom", 5))
            offset_left = int(body_stain_tab.get(f"bs{stain_num}_off_left", 5))
            offset_right = int(body_stain_tab.get(f"bs{stain_num}_off_right", 5))
            red_dot_min = int(body_stain_tab.get(f"bs{stain_num}_red_dot_min", 255))
            
            # Check if parameters are configured (255 means not configured)
            if contrast == 255 or (min_area == 255 and min_square == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area}, min_square={min_square})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue
            
            # Run body stain check
            defects_found, largest_area, is_pass, defect_rects = check_body_stain(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
                min_square=min_square,
                apply_or=apply_or,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                red_dot_min=red_dot_min,
                debug=True
            )
            
            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}")
            
            # ===== STEP MODE: Show dialog for FAILED steps =====
            if step_mode and step_callback and not is_pass:
                expected_txt = f"Area < {min_area}px"
                if min_square != 255:
                    expected_txt += f" and W/H < {min_square}px" if not apply_or else f" or W/H < {min_square}px"
                if red_dot_min != 255:
                    expected_txt += f" and Count <= {red_dot_min}"
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": expected_txt,
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Defects Found: {defects_found}\nLargest Area: {largest_area}px\nMin Area Threshold: {min_area}px\nMin Square Threshold: {min_square}px\nRed Dot Min Count: {red_dot_min}\nApply OR: {apply_or}\nContrast: {contrast}\n\nSuggested new min_area: {int(largest_area * 1.2)}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
            
            # Draw defect boxes on visualization if failed
            if not is_pass and defect_rects:
                print(f"[DEBUG] Drawing {len(defect_rects)} defect boxes")
                import numpy as np
                for rect in defect_rects:
                    x, y, w, h = rect
                    # Draw red rectangle around defect
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            if not is_pass:
                print(f"[FAIL] {test_name} detected defects")
                limit_txt = f"max area={min_area}px"
                if min_square != 255:
                    limit_txt += f", max W/H={min_square}px"
                if red_dot_min != 255:
                    limit_txt += f", max count={red_dot_min}"
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px, {limit_txt})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (defects={defects_found})")

        elif attr_name in ("check_body_smear_1", "check_body_smear_2", "check_body_smear_3"):
            # Body Smear detection - check for white defects on body surface
            print(f"[INFO] Checking {test_name}...")
            
            # Determine which smear check (1, 2, or 3)
            smear_num = attr_name[-1]  # Extract '1', '2', or '3'
            
            # Get parameters from device_inspection.json BodySmearTab
            body_smear_tab = device_thresholds.get("BodySmearTab", {})
            
            contrast = int(body_smear_tab.get(f"bs{smear_num}_contrast", 255))
            min_area = int(body_smear_tab.get(f"bs{smear_num}_min_area", 255))
            min_square = int(body_smear_tab.get(f"bs{smear_num}_min_square", 255))
            use_avg_contrast = bool(body_smear_tab.get(f"bs{smear_num}_use_avg_contrast", True))
            apply_or = bool(body_smear_tab.get(f"bs{smear_num}_apply_or", True))
            offset_top = int(body_smear_tab.get(f"bs{smear_num}_offset_top", 5))
            offset_bottom = int(body_smear_tab.get(f"bs{smear_num}_offset_bottom", 5))
            offset_left = int(body_smear_tab.get(f"bs{smear_num}_offset_left", 5))
            offset_right = int(body_smear_tab.get(f"bs{smear_num}_offset_right", 5))
            
            # Check if parameters are configured (255 means not configured)
            if contrast == 255 or (min_area == 255 and min_square == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area}, min_square={min_square})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue
            
            # Run body smear check
            defects_found, largest_area, is_pass, defect_rects = check_body_smear(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
                min_square=min_square,
                use_avg_contrast=use_avg_contrast,
                apply_or=apply_or,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                debug=True
            )
            
            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}")
            
            # ===== STEP MODE: Show dialog for FAILED steps =====
            if step_mode and step_callback and not is_pass:
                expected_txt = f"Area < {min_area}px"
                if min_square != 255:
                    expected_txt += f" and W/H < {min_square}px" if not apply_or else f" or W/H < {min_square}px"
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": expected_txt,
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Defects Found: {defects_found}\nLargest Area: {largest_area}px\nMin Area Threshold: {min_area}px\nMin Square Threshold: {min_square}px\nApply OR: {apply_or}\nContrast: {contrast}\n\nSuggested new min_area: {int(largest_area * 1.2)}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
            
            # Draw defect boxes on visualization if failed
            if not is_pass and defect_rects:
                print(f"[DEBUG] Drawing {len(defect_rects)} defect boxes")
                import numpy as np
                for rect in defect_rects:
                    x, y, w, h = rect
                    # Draw red rectangle around defect
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            if not is_pass:
                print(f"[FAIL] {test_name} detected defects")
                limit_txt = f"max area={min_area}px"
                if min_square != 255:
                    limit_txt += f", max W/H={min_square}px"
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px, {limit_txt})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (defects={defects_found})")
        elif attr_name == "check_reverse_chip":
            # Reverse Chip Check - detects if chip is accidentally reversed
            print(f"[INFO] Checking {test_name}...")
            
            # Get parameters from device_inspection.json BodySmearTab
            body_smear_tab = device_thresholds.get("BodySmearTab", {})
            
            teach_intensity = int(body_smear_tab.get("reverse_teach_intensity", 128))
            contrast_diff = int(body_smear_tab.get("reverse_contrast_diff", 20))
            
            # Run reverse chip check
            measured_intensity, is_reversed, is_pass = check_reverse_chip(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                teach_intensity=teach_intensity,
                contrast_diff=contrast_diff,
                debug=True
            )
            
            print(f"[INFO] {test_name}: measured={measured_intensity}, reversed={is_reversed}, pass={is_pass}")
            
            # ===== STEP MODE: Show dialog for FAILED steps =====
            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Intensity={measured_intensity}",
                    "expected": f"Within {contrast_diff} of {teach_intensity}",
                    "suggested_min": None,
                    "suggested_max": None,
                    "debug_info": f"Taught Intensity: {teach_intensity}\nMeasured Intensity: {measured_intensity}\nDifference: {abs(measured_intensity - teach_intensity)}\nThreshold: {contrast_diff}\n\nChip appears REVERSED!\n\nSuggested new teach_intensity: {measured_intensity}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
            
            if not is_pass:
                print(f"[FAIL] {test_name} - chip appears reversed")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Reversed! (intensity={measured_intensity}, expected={teach_intensity}±{contrast_diff})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (intensity={measured_intensity})")
        else:
            messages.append(f"{test_name} OK")

    # -------------------------------
    # 4. ALL ENABLED TESTS PASSED
    # -------------------------------
    print("\n[PASS] All enabled inspections passed")

    test_summary = f"Enabled Tests:\n" + "\n".join([f"✓ {msg}" for msg in messages])
    if skipped_tests:
        test_summary += f"\n\nSkipped Tests:\n" + "\n".join([f"• {test}" for test in skipped_tests])

    # draw_test_result already adds PASS indicator in corner
    overlay, reason = draw_test_result(
        image,
        [test_summary],
        "PASS"
    )

    return TestResult(TestStatus.PASS, "OK", overlay)

def test_feed(image, params, step_mode=False, step_callback=None, debug_flags=0):
    debug_enabled = bool(debug_flags & (
        DEBUG_PRINT | DEBUG_PRINT_EXT | DEBUG_EDGE |
        DEBUG_BLOB | DEBUG_HIST | DEBUG_TIME | DEBUG_TIME_EXT
    ))
    debug_draw = bool(debug_flags & DEBUG_DRAW)
    if not debug_enabled:
        def print(*args, **kwargs):
            return None
    """Test for FEED station - validates pocket location and all enabled inspections"""
    print("\n[TEST] Feed station inspection started")

    # Create a working copy for measurements to prevent visualization from corrupting measurements
    # The original 'image' will be used for visualization, working_image for measurements
    import numpy as np
    working_image = np.copy(image)

    messages = []
    enabled_tests = []
    skipped_tests = []
    
    # Load device inspection thresholds
    device_thresholds = load_device_thresholds()
    print(f"[INFO] Device thresholds loaded: {bool(device_thresholds)}")
    
    # Check if device has no terminal (body-only device)
    no_terminal = bool(device_thresholds.get("no_terminal", False))
    
    if no_terminal:
        print("[INFO] No Terminal mode ENABLED - device has body only, skipping all terminal inspections")
    
    # Load pocket parameters for edge contrast value
    pocket_params = load_pocket_params()
    edge_contrast_value = int(pocket_params.get("edge_contrast_value", 106)) if pocket_params else 106
    enable_post_seal = bool(params.flags.get("enable_pocket_post_seal", False) or pocket_params.get("enable_post_seal", False))
    enable_emboss_tape = bool(pocket_params.get("enable_emboss_tape", False))

    def _save_post_seal_image(reason: str) -> None:
        if not enable_post_seal:
            return
        try:
            import os
            from datetime import datetime
            base_dir = r"D:\PostSealed"
            os.makedirs(base_dir, exist_ok=True)
            safe_reason = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in reason)[:40]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"PostSeal_{timestamp}_{safe_reason}.bmp"
            cv2.imwrite(os.path.join(base_dir, filename), image)
        except Exception as e:
            print(f"[WARN] PostSeal image save failed: {e}")

    def _post_seal_fail(title: str, lines):
        _save_post_seal_image(title)
        overlay, reason = draw_test_result(image, lines, "FAIL")
        return TestResult(TestStatus.FAIL, title, overlay)

    # -----------------------------------------------
    # 1. Check Package Location
    # -----------------------------------------------
    print("[CHECK] Validating teach data...")

    if params.package_w <= 0 or params.package_h <= 0:
        print("[FAIL] Package not taught")
        return _post_seal_fail("Package not taught", ["Package not taught", "Please run Teach first"])

    if not params.flags.get("enable_package_location", False):
        print("[SKIP] Package inspection disabled")
        skipped_tests.append("Package Location (disabled)")
    else:
        print(f"[OK] Package taught: ({params.package_x}, {params.package_y}, {params.package_w}, {params.package_h})")

    # -----------------------------------------------
    # 2. Check Pocket Location (FEED specific)
    # -----------------------------------------------
    if params.flags.get("enable_pocket_location", False):
        if params.pocket_w <= 0 or params.pocket_h <= 0:
            print("[FAIL] Pocket not taught")
            return _post_seal_fail("Pocket not taught", ["Pocket not taught", "Please run Teach first"])

        print(f"[OK] Pocket taught: ({params.pocket_x}, {params.pocket_y}, {params.pocket_w}, {params.pocket_h})")
    else:
        print("[SKIP] Pocket inspection disabled")
        skipped_tests.append("Pocket Location (disabled)")

    # -----------------------------------------------
    # 3. Build list of enabled inspections IN ORDER
    # -----------------------------------------------
    inspection_checks = [
        # Package Location
        ("Package Location", params.flags.get("enable_package_location", False), "enable_package_location", "detect_package_location"),

        # Pocket Location
        ("Pocket Location", params.flags.get("enable_pocket_location", False), "enable_pocket_location", "detect_pocket_location"),
        ("Outer Pocket Stain", bool(pocket_params.get("outer_stain_black", False) or pocket_params.get("outer_stain_white", False)), "outer_pocket_stain", None),
        
        # Pocket
        ("Pocket Post Seal", params.flags.get("enable_pocket_post_seal", False) and not no_terminal, "enable_pocket_post_seal", None),
        
        # Dimension Measurements
        ("Body Length", params.flags.get("check_body_length", False), "check_body_length", "measure_body_length"),
        ("Body Width", params.flags.get("check_body_width", False), "check_body_width", "measure_body_width"),
        # Terminal inspections - skip if no_terminal is enabled
        ("Terminal Width", params.flags.get("check_terminal_width", False) and not no_terminal, "check_terminal_width", "measure_terminal_width"),
        ("Terminal Length", params.flags.get("check_terminal_length", False) and not no_terminal, "check_terminal_length", "measure_terminal_length"),
        ("Term-Term Length", params.flags.get("check_term_term_length", False) and not no_terminal, "check_term_term_length", "measure_term_to_term_length"),
        ("Terminal Length Diff", params.flags.get("check_terminal_length_diff", False) and not no_terminal, "check_terminal_length_diff", "check_terminal_length_diff"),
        
        # Terminal Inspections - all skipped if no_terminal
        ("Terminal Pogo", params.flags.get("check_terminal_pogo", False) and not no_terminal, "check_terminal_pogo", None),
        ("Terminal Offset", params.flags.get("check_terminal_offset", False) and not no_terminal, "check_terminal_offset", None),
        ("Incomplete Termination 1", params.flags.get("check_incomplete_termination_1", False) and not no_terminal, "check_incomplete_termination_1", None),
        ("Incomplete Termination 2", params.flags.get("check_incomplete_termination_2", False) and not no_terminal, "check_incomplete_termination_2", None),
        ("Terminal to Body Gap", params.flags.get("check_terminal_to_body_gap", False) and not no_terminal, "check_terminal_to_body_gap", "measure_term_to_body_gap"),
        ("Terminal Color", params.flags.get("check_terminal_color", False) and not no_terminal, "check_terminal_color", None),
        ("Terminal Oxidation", params.flags.get("check_terminal_oxidation", False) and not no_terminal, "check_terminal_oxidation", None),
        ("Inner Terminal Chipoff", params.flags.get("check_inner_term_chipoff", False) and not no_terminal, "check_inner_term_chipoff", None),
        ("Outer Terminal Chipoff", params.flags.get("check_outer_term_chipoff", False) and not no_terminal, "check_outer_term_chipoff", None),
        
        # Body Inspections
        ("Body Stain 1", params.flags.get("check_body_stain_1", False), "check_body_stain_1", None),
        ("Body Stain 2", params.flags.get("check_body_stain_2", False), "check_body_stain_2", None),
        ("Body Color", params.flags.get("check_body_color", False), "check_body_color", None),
        ("Body to Term Width", params.flags.get("check_body_to_term_width", False), "check_body_to_term_width", "measure_body_to_term_width"),
        ("Body Width Diff", params.flags.get("check_body_width_diff", False), "check_body_width_diff", None),
        ("Body Crack", params.flags.get("check_body_crack", False), "check_body_crack", None),
        ("Low/High Contrast", params.flags.get("check_low_high_contrast", False), "check_low_high_contrast", None),
        ("Black Defect", params.flags.get("check_black_defect", False), "check_black_defect", None),
        ("White Defect", params.flags.get("check_white_defect", False), "check_white_defect", None),
        
        # Body Smear
        ("Body Smear 1", params.flags.get("check_body_smear_1", False), "check_body_smear_1", None),
        ("Body Smear 2", params.flags.get("check_body_smear_2", False), "check_body_smear_2", None),
        ("Body Smear 3", params.flags.get("check_body_smear_3", False), "check_body_smear_3", None),
        ("Reverse Chip", params.flags.get("check_reverse_chip", False), "check_reverse_chip", "check_reverse_chip"),
        ("Smear White", params.flags.get("check_smear_white", False), "check_smear_white", None),
        
        # Body Edge
        ("Body Edge Black", params.flags.get("check_body_edge_black", False), "check_body_edge_black", None),
        ("Body Edge White", params.flags.get("check_body_edge_white", False), "check_body_edge_white", None),
        
        # TQS Inspections (FEED specific)
        ("Sealing Stain", params.flags.get("enable_sealing_stain", False), "enable_sealing_stain", None),
        ("Sealing Stain 2", params.flags.get("enable_sealing_stain2", False), "enable_sealing_stain2", None),
        ("Sealing Shift", params.flags.get("enable_sealing_shift", False), "enable_sealing_shift", None),
        ("Black to White Scar", params.flags.get("enable_black_to_white_scar", False), "enable_black_to_white_scar", None),
        ("Hole Reference", params.flags.get("enable_hole_reference", False), "enable_hole_reference", None),
        ("White to Black Scan", params.flags.get("enable_white_to_black_scan", False), "enable_white_to_black_scan", None),
        ("Emboss Tape Pickup", params.flags.get("enable_emboss_tape_pickup", False), "enable_emboss_tape_pickup", None),
    ]

    # Filter enabled tests
    for test_name, is_enabled, attr_name, measurement_func in inspection_checks:
        if is_enabled:
            enabled_tests.append((test_name, attr_name, measurement_func))
            print(f"[ENABLED] {test_name}")
        else:
            # Add reason for why test is skipped
            if no_terminal and ("Terminal" in test_name or test_name == "Pocket Post Seal"):
                skipped_tests.append(f"{test_name} (no terminal mode)")
                print(f"[SKIPPED] {test_name} - no terminal mode")
            else:
                skipped_tests.append(f"{test_name} (disabled)")
                print(f"[SKIPPED] {test_name} - not enabled")

    # If emboss tape enabled, only allow pocket-related inspections
    if enable_emboss_tape:
        pocket_only = []
        for test_name, attr_name, measurement_func in enabled_tests:
            if "Pocket" in test_name:
                pocket_only.append((test_name, attr_name, measurement_func))
            else:
                skipped_tests.append(f"{test_name} (emboss tape)")
                print(f"[SKIPPED] {test_name} - emboss tape enabled")
        enabled_tests = pocket_only

    # Log skipped tests
    if skipped_tests:
        print(f"\n[INFO] Skipped tests: {', '.join(skipped_tests)}")

    # If no tests enabled, return PASS with message
    if not enabled_tests:
        print("[PASS] No inspections enabled")
        message = "No inspections enabled\n\nSkipped:\n" + "\n".join(skipped_tests)
        overlay, reason = draw_test_result(image, [message], "PASS")
        return TestResult(TestStatus.PASS, "No tests enabled", overlay)

    # -----------------------------------------------
    # 4. RUN ENABLED INSPECTIONS
    # -----------------------------------------------
    print("\n[TEST] Running enabled inspections...")

    for test_name, attr_name, measurement_func in enabled_tests:
        print(f"\n[TEST] {test_name} inspection")
        
        if measurement_func == "detect_package_location":
            print(f"[DEBUG] Processing Package Location detection")
            # Load device location settings
            from config.device_location_setting_io import load_device_location_setting
            dev_loc_settings = load_device_location_setting()
            
            # Check if using taught position mode (fixed location, no detection)
            use_teach_pos = dev_loc_settings.get("teach_pos", False)
            
            if use_teach_pos:
                # Use taught package position without detection
                print(f"[INFO] Using taught package position (teach_pos mode enabled)")
                print(f"[INFO] Package location: ({params.package_x}, {params.package_y}, {params.package_w}x{params.package_h})")
                
                # Validate taught position
                is_valid = validate_device_location(
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    image.shape,
                    min_size=20,
                    max_size_ratio=0.95,
                    debug=True
                )
                
                if not is_valid:
                    print(f"[FAIL] Taught package location validation failed")
                    return _post_seal_fail(
                        "Package location validation failed",
                        ["Taught package location validation failed", 
                         f"Location: ({params.package_x}, {params.package_y}, {params.package_w}x{params.package_h})"]
                    )
                
                print(f"[PASS] Package location validated (taught position mode)")
                messages.append(f"{test_name} OK (taught position)")
                
                # ========================================
                # Mark Inspection (after device location - teach_pos mode)
                # ========================================
                mark_config = load_mark_inspection_config()
                
                # Check if mark inspection is enabled
                if mark_config.symbol_set.enable_mark_inspect:
                    print(f"[INFO] Mark Inspection enabled - running detection...")
                    
                    # Use taught package position for mark detection
                    device_roi = (params.package_x, params.package_y, params.package_w, params.package_h)
                    
                    # Detect marks
                    mark_result = detect_marks(
                        working_image,
                        config=mark_config,
                        roi=device_roi,
                        debug=True
                    )
                    
                    if mark_result.detected:
                        # Verify marks
                        verify_passed, verify_details = verify_marks(
                            mark_result.marks,
                            mark_config,
                            debug=True
                        )
                        
                        if verify_passed:
                            print(f"[PASS] Mark Inspection: {len(mark_result.marks)} marks detected")
                            print(f"[INFO] Mark confidence: {mark_result.confidence:.1f}%, method: {mark_result.method}")
                            messages.append(f"Mark Inspection OK ({len(mark_result.marks)} marks, {mark_result.confidence:.0f}%)")
                        else:
                            print(f"[WARN] Mark verification failed: {verify_details.get('message', 'unknown')}")
                            messages.append(f"Mark Inspection WARN (verification failed)")
                    else:
                        print(f"[WARN] No marks detected: {mark_result.error_message}")
                        messages.append(f"Mark Inspection WARN (no marks)")
                else:
                    print(f"[INFO] Mark Inspection disabled")
                
            else:
                # Auto-detect package location using comprehensive detector
                from imaging.device_location import detect_device_location
                
                # Detect package location with all configured parameters
                result = detect_device_location(
                    image,
                    contrast_threshold=dev_loc_settings.get("contrast", 50),
                    x_shift_tol=dev_loc_settings.get("x_pkg_shift_tol", 50),
                    y_shift_tol=dev_loc_settings.get("y_pkg_shift_tol", 50),
                    recheck=dev_loc_settings.get("pkg_loc_recheck", True),
                    recheck_val=dev_loc_settings.get("pkg_loc_recheck_val", 30),
                    use_red_detection=dev_loc_settings.get("enable_red_pkg_location", False),
                    settings_dict=dev_loc_settings,
                    debug=True
                )
                
                # Validate location if detected
                if result.detected:
                    is_valid = validate_device_location(
                        (result.x, result.y, result.width, result.height),
                        image.shape,
                        min_size=20,
                        max_size_ratio=0.95,
                        debug=True
                    )
                    
                    if not is_valid:
                        print(f"[FAIL] Package location validation failed")
                        return _post_seal_fail(
                            "Package location validation failed",
                            ["Package location validation failed", 
                             f"Location: ({result.x}, {result.y}, {result.width}x{result.height})"]
                        )
                    
                    print(f"[PASS] Package location detected: ({result.x}, {result.y}, {result.width}x{result.height})")
                    print(f"[INFO] Method: {result.method}, Confidence: {result.confidence:.1f}%, Contrast: {result.contrast:.1f}")
                    messages.append(f"{test_name} OK (method={result.method}, confidence={result.confidence:.0f}%)")
                    
                    # ========================================
                    # Mark Inspection (after device location)
                    # ========================================
                    # Load mark inspection configuration
                    mark_config = load_mark_inspection_config()
                    
                    # Check if mark inspection is enabled (matching old C++ logic)
                    if mark_config.symbol_set.enable_mark_inspect:
                        print(f"[INFO] Mark Inspection enabled - running detection...")
                        
                        # Get device location for mark detection
                        device_roi = (result.x, result.y, result.width, result.height)
                        
                        # Detect marks using configured method
                        mark_result = detect_marks(
                            working_image,
                            config=mark_config,
                            roi=device_roi,
                            debug=True
                        )
                        
                        if mark_result.detected:
                            # Verify marks meet symbol requirements
                            verify_passed, verify_details = verify_marks(
                                mark_result.marks,
                                mark_config,
                                debug=True
                            )
                            
                            if verify_passed:
                                print(f"[PASS] Mark Inspection: {len(mark_result.marks)} marks detected")
                                print(f"[INFO] Mark confidence: {mark_result.confidence:.1f}%, method: {mark_result.method}")
                                messages.append(f"Mark Inspection OK ({len(mark_result.marks)} marks, {mark_result.confidence:.0f}%)")
                                
                                # Optional: Validate mark position if expected position configured
                                # Note: expected_mark_position not in current config structure
                                # This can be added if needed in future
                            else:
                                # Mark verification failed
                                print(f"[FAIL] Mark Inspection verification failed: {verify_details.get('message', 'unknown')}")
                                # Check if mark inspection is required (fail test) or just warning
                                # For now, treat as warning and continue
                                print(f"[WARN] Mark verification failed - continuing")
                                messages.append(f"Mark Inspection WARN (verification failed)")
                        else:
                            # Mark detection returned False
                            print(f"[FAIL] Mark Inspection: {mark_result.error_message}")
                            # Treat as warning for now
                            print(f"[WARN] No marks detected - continuing")
                            messages.append(f"Mark Inspection WARN (no marks)")
                    else:
                        print(f"[INFO] Mark Inspection disabled")
                    
                else:
                    print(f"[FAIL] {result.message}")
                    return _post_seal_fail(
                        f"{test_name} detection failed",
                        ["Package location detection failed", result.message]
                    )
            
            continue  # Skip the measurement processing below

        if measurement_func == "detect_pocket_location":
            if not params.flags.get("enable_pocket_location", False):
                messages.append(f"{test_name} SKIP (disabled)")
                continue

            teach_rect = (params.pocket_x, params.pocket_y, params.pocket_w, params.pocket_h)
            result = detect_pocket_location(
                image,
                teach_rect=teach_rect,
                pocket_params=pocket_params,
                debug=True
            )

            if not result.detected:
                print(f"[FAIL] Pocket location detection failed: {result.message}")
                return _post_seal_fail(
                    "Pocket location detection failed",
                    ["Pocket location detection failed", result.message]
                )

            is_valid = validate_pocket_location(
                (result.x, result.y, result.width, result.height),
                image.shape,
                min_size=20,
                max_size_ratio=0.95,
                debug=True
            )

            if not is_valid:
                print("[FAIL] Pocket location validation failed")
                return _post_seal_fail(
                    "Pocket location validation failed",
                    ["Pocket location validation failed",
                     f"Location: ({result.x}, {result.y}, {result.width}x{result.height})"]
                )

            # Update pocket location with detected values
            params.pocket_x = result.x
            params.pocket_y = result.y
            params.pocket_w = result.width
            params.pocket_h = result.height

            # Log detailed detection info with new fields
            detail_msg = f"method={result.method}, confidence={result.confidence:.0f}%"
            if result.angle > 0:
                detail_msg += f", angle={result.angle:.2f}°, mode={result.parallel_mode}"
            
            print(f"[PASS] Pocket location detected: ({result.x}, {result.y}, {result.width}x{result.height})")
            print(f"[INFO] {detail_msg}")
            messages.append(f"{test_name} OK ({detail_msg})")
            
            # ========================================
            # Check Pocket Dimension
            # ========================================
            dim_enabled = pocket_params.get("pocket_dim_length_enable") or pocket_params.get("pocket_dim_width_enable")
            if dim_enabled:
                dim_valid, dim_details = check_pocket_dimension(
                    (result.x, result.y, result.width, result.height),
                    pocket_params=pocket_params,
                    debug=True
                )
                
                if not dim_valid:
                    print("[FAIL] Pocket dimension inspection failed")
                    for msg in dim_details["messages"]:
                        print(f"  [FAIL] {msg}")
                    return _post_seal_fail(
                        "Pocket dimension inspection failed",
                        ["Pocket dimension inspection failed"] + dim_details["messages"]
                    )
                else:
                    for msg in dim_details["messages"]:
                        print(f"  [PASS] {msg}")
                        messages.append(msg)
            
            # ========================================
            # Check Pocket Gap
            # ========================================
            gap_enabled = pocket_params.get("pocket_gap_enable")
            if gap_enabled:
                # Use device location if available, otherwise use pocket
                device_loc = (params.device_x, params.device_y, params.device_w, params.device_h) \
                    if hasattr(params, 'device_x') and params.device_x > 0 else \
                    (result.x + 10, result.y + 10, result.width - 20, result.height - 20)
                
                gap_valid, gap_details = check_pocket_gap(
                    device_loc,
                    (result.x, result.y, result.width, result.height),
                    pocket_params=pocket_params,
                    debug=True
                )
                
                if not gap_valid:
                    print("[FAIL] Pocket gap inspection failed")
                    for msg in gap_details["messages"]:
                        print(f"  [FAIL] {msg}")
                    return _post_seal_fail(
                        "Pocket gap inspection failed",
                        ["Pocket gap inspection failed"] + gap_details["messages"]
                    )
                else:
                    for msg in gap_details["messages"]:
                        print(f"  [PASS] {msg}")
                        messages.append(msg)
            
            # ========================================
            # Track Pocket Shift
            # ========================================
            shift_enabled = pocket_params.get("pocket_shift_enable")
            if shift_enabled:
                pocket_shift_valid, pocket_shift_record, shift_details = track_pocket_shift(
                    result.x,
                    result.y,
                    params.pocket_x,  # taught position
                    params.pocket_y,
                    pocket_params=pocket_params,
                    shift_record=pocket_shift_record,
                    debug=True
                )
                
                # Log to shift log file
                shift_log = get_shift_log_manager()
                if shift_log.get_current_session() is not None:
                    shift_log.log_measurement(
                        shift_x=shift_details["current_shift"][0],
                        shift_y=shift_details["current_shift"][1],
                        avg_x=shift_details["avg_shift"][0],
                        avg_y=shift_details["avg_shift"][1],
                        tolerance_x=shift_details["tolerance_x"],
                        tolerance_y=shift_details["tolerance_y"],
                        valid=pocket_shift_valid
                    )
                
                for msg in shift_details["messages"]:
                    print(f"  [INFO] {msg}")
                    messages.append(msg)
                
                if not pocket_shift_valid:
                    # Alert but don't fail
                    for alert in shift_details["alerts"]:
                        print(f"  [ALERT] {alert}")
            
            continue
        
        elif measurement_func == "measure_body_width":
            value = measure_body_width(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                body_contrast=params.ranges.get("body_contrast", 75),
                debug=True
            )

            metric_key_min = "body_width_min"
            metric_key_max_from_dev = "body_width_max"
            fallback_min = params.body_width_min
            fallback_max = params.body_width_max
            
        elif measurement_func == "measure_body_length":
            # If configured to use package location as body length, use taught width
            use_pkg_as_body = bool(device_thresholds.get("pkg_as_body", False))
            if use_pkg_as_body:
                value = int(params.package_w)
                print(f"[INFO] Using package width as Body Length (pkg_as_body)")
            else:
                value = measure_body_length(
                    image,
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    body_contrast=params.ranges.get("body_contrast", 75),
                    debug=True
                )

            metric_key_min = "body_length_min"
            metric_key_max_from_dev = "body_length_max"
            fallback_min = params.body_length_min
            fallback_max = params.body_length_max
        elif measurement_func == "measure_terminal_width":
            # Terminal Width: find leftmost/rightmost terminal edges
            # Try both top and bottom regions for terminal detection
            top_terminal_roi = (params.package_x, params.package_y, params.package_w, int(params.package_h * 0.3))
            bottom_terminal_roi = (params.package_x, params.package_y + int(params.package_h * 0.7), params.package_w, int(params.package_h * 0.3))
            
            # Try top terminal first
            value = measure_terminal_width(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                top_terminal_roi,
                edge_contrast=edge_contrast_value,
                debug=True
            )
            
            # If top fails, try bottom terminal
            if value is None:
                print(f"[INFO] Top terminal width not detected, trying bottom terminal...")
                value = measure_terminal_width(
                    working_image,
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    bottom_terminal_roi,
                    edge_contrast=edge_contrast_value,
                    debug=True
                )
            
            metric_key_min = "terminal_width_min"
            metric_key_max_from_dev = "terminal_width_max"
            fallback_min = int(device_thresholds.get("terminal_width_min", 10))
            fallback_max = int(device_thresholds.get("terminal_width_max", 100))
        elif measurement_func == "measure_terminal_length":
            # Terminal Length: multi-scan edge detection
            # Try both top and bottom regions for terminal detection
            top_terminal_roi = (params.package_x, params.package_y, params.package_w, int(params.package_h * 0.3))
            bottom_terminal_roi = (params.package_x, params.package_y + int(params.package_h * 0.7), params.package_w, int(params.package_h * 0.3))
            
            # Try top terminal first
            value = measure_terminal_length(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                top_terminal_roi,
                edge_contrast=edge_contrast_value,
                num_scans=100,
                debug=True
            )
            
            # If top fails, try bottom terminal
            if value is None:
                print(f"[INFO] Top terminal length not detected, trying bottom terminal...")
                value = measure_terminal_length(
                    working_image,
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    bottom_terminal_roi,
                    edge_contrast=edge_contrast_value,
                    num_scans=100,
                    debug=True
                )
            
            metric_key_min = "terminal_length_min"
            metric_key_max_from_dev = "terminal_length_max"
            fallback_min = int(device_thresholds.get("terminal_length_min", 10))
            fallback_max = int(device_thresholds.get("terminal_length_max", 100))
        elif measurement_func == "measure_term_to_term_length":
            # Term-to-Term Length: gap between left and right terminals
            left_terminal_roi = (params.package_x, params.package_y, int(params.package_w * 0.3), int(params.package_h * 0.3))
            right_terminal_roi = (params.package_x + int(params.package_w * 0.7), params.package_y, int(params.package_w * 0.3), int(params.package_h * 0.3))
            
            value = measure_term_to_term_length(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                left_terminal_roi,
                right_terminal_roi,
                edge_contrast=edge_contrast_value,
                num_scans=100,
                debug=True
            )
            
            metric_key_min = "term_to_term_length_min"
            metric_key_max_from_dev = "term_to_term_length_max"
            fallback_min = int(device_thresholds.get("term_to_term_length_min", 20))
            fallback_max = int(device_thresholds.get("term_to_term_length_max", 200))
        else:
            value = None

        # Process measurements
        if measurement_func in ("measure_body_width", "measure_body_length", "measure_terminal_width",
                               "measure_terminal_length", "measure_term_to_term_length"):
            if value is None:
                print(f"[FAIL] {test_name} not detected")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name} not detected"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} detect fail", overlay)

            print(f"[INFO] {test_name} measured = {value}")

            # Get thresholds
            min_threshold = None
            max_threshold = None
            threshold_source = "params"

            if device_thresholds:
                try:
                    min_val = device_thresholds.get(metric_key_min, "")
                    max_val = device_thresholds.get(metric_key_max_from_dev, "")
                    if min_val and min_val != "255":
                        min_threshold = int(min_val)
                    if max_val and max_val != "255":
                        max_threshold = int(max_val)
                    if (min_threshold is not None) or (max_threshold is not None):
                        threshold_source = "device_inspection.json"
                except ValueError:
                    pass

            if min_threshold is None:
                min_threshold = fallback_min
            if max_threshold is None:
                max_threshold = fallback_max

            print(f"[INFO] Thresholds: {min_threshold} - {max_threshold} (from {threshold_source})")

            is_pass = (min_threshold <= value <= max_threshold)
            
            if step_mode and step_callback and not is_pass:
                # Calculate suggested thresholds based on measured value
                tolerance = max(10, int(value * 0.20))
                suggested_min = max(1, value - tolerance)
                suggested_max = value + tolerance
                
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"{value} pixels",
                    "expected": f"{min_threshold} - {max_threshold} pixels",
                    "suggested_min": suggested_min,
                    "suggested_max": suggested_max,
                    "debug_info": f"Measured: {value}\nCurrent Min: {min_threshold}\nCurrent Max: {max_threshold}\n\nSuggested Min: {suggested_min}\nSuggested Max: {suggested_max}\n\nSource: {threshold_source}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if is_pass and step_mode:
                points_data = {}
                if measurement_func == "measure_body_length":
                    points_data = {
                        "left_x": params.package_x + (params.package_w * 0.25),
                        "right_x": params.package_x + (params.package_w * 0.75),
                        "center_y": params.package_y + (params.package_h / 2)
                    }
                elif measurement_func == "measure_body_width":
                    points_data = {
                        "top_y": params.package_y + (params.package_h * 0.25),
                        "bottom_y": params.package_y + (params.package_h * 0.75),
                        "center_x": params.package_x + (params.package_w / 2)
                    }

                # Draw on the original image for visualization (returns modified copy)
                image = draw_measurement_result(
                    image,
                    (params.package_x, params.package_y, params.package_w, params.package_h),
                    test_name,
                    "PASS",
                    value,
                    min_threshold,
                    max_threshold,
                    points_data
                )

            if not is_pass:
                print(f"[FAIL] {test_name} out of range")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {value} (Expected: {min_threshold}-{max_threshold})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK ({value})")
        elif measurement_func == "check_body_width_diff":
            # Body Width Difference: measure top and bottom body widths separately
            print(f"[INFO] Measuring Body Width Difference...")
            
            # Get tolerance from device_inspection.json
            tolerance_str = device_thresholds.get("body_width_diff_value", "255") if device_thresholds else "255"
            if tolerance_str == "255" or not tolerance_str:
                print(f"[SKIP] Body Width Diff tolerance not configured (value={tolerance_str})")
                messages.append(f"{test_name} SKIPPED (tolerance not set)")
                continue
            
            tolerance = float(tolerance_str)
            
            # Measure body width at top 25% region
            top_roi_height = int(params.package_h * 0.25)
            top_roi = (params.package_x, params.package_y, params.package_w, top_roi_height)
            top_width = measure_body_width(
                working_image,
                top_roi,
                body_contrast=params.ranges.get("body_contrast", 75),
                debug=True
            )
            
            # Measure body width at bottom 25% region
            bottom_roi_height = int(params.package_h * 0.25)
            bottom_roi = (params.package_x, params.package_y + params.package_h - bottom_roi_height, 
                         params.package_w, bottom_roi_height)
            bottom_width = measure_body_width(
                working_image,
                bottom_roi,
                body_contrast=params.ranges.get("body_contrast", 75),
                debug=True
            )
            
            if top_width is None or bottom_width is None:
                print(f"[FAIL] Body Width Diff measurement failed")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Measurement failed"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} measurement fail", overlay)
            
            # Check difference
            result = check_body_width_difference(top_width, bottom_width, tolerance, debug=True)
            
            print(f"[INFO] Top Width: {result['top']:.2f}, Bottom Width: {result['bottom']:.2f}")
            print(f"[INFO] Difference: {result['difference']:.2f}, Tolerance: {result['tolerance']:.2f}")
            
            # ===== STEP MODE: Show dialog for FAILED steps =====
            if step_mode and step_callback and not result['is_pass']:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Diff={result['difference']:.2f} (Top={result['top']:.2f}, Bottom={result['bottom']:.2f})",
                    "expected": f"< {tolerance:.2f} pixels",
                    "suggested_min": 0,
                    "suggested_max": int(result['difference'] * 1.5),
                    "debug_info": f"Top Width: {result['top']:.2f}\nBottom Width: {result['bottom']:.2f}\nDifference: {result['difference']:.2f}\nTolerance: {result['tolerance']:.2f}\n\nSuggested new tolerance: {int(result['difference'] * 1.5)}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
            
            if not result['is_pass']:
                print(f"[FAIL] Body Width Diff exceeds tolerance")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Diff={result['difference']:.2f} (Tolerance: {tolerance:.2f})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (Diff={result['difference']:.2f})")
        elif measurement_func == "check_terminal_length_diff":
            # Terminal Length Difference: measure left and right terminal lengths
            print(f"[INFO] Measuring Terminal Length Difference...")
            
            # Get tolerance from device_inspection.json
            tolerance_str = device_thresholds.get("terminal_length_diff_value", "255") if device_thresholds else "255"
            if tolerance_str == "255" or not tolerance_str:
                print(f"[SKIP] Terminal Length Diff tolerance not configured (value={tolerance_str})")
                messages.append(f"{test_name} SKIPPED (tolerance not set)")
                continue
            
            tolerance = float(tolerance_str)
            
            # Measure left terminal lengths (multiple scan lines)
            # Left terminal ROI: leftmost 30% of package, top 30% height
            left_terminal_roi = (
                params.package_x, 
                params.package_y, 
                int(params.package_w * 0.3), 
                int(params.package_h * 0.3)
            )
            
            # Right terminal ROI: rightmost 30% of package, top 30% height
            right_terminal_roi = (
                params.package_x + int(params.package_w * 0.7), 
                params.package_y, 
                int(params.package_w * 0.3), 
                int(params.package_h * 0.3)
            )
            
            # For now, measure single values for left and right
            # In the future, this should be enhanced to collect multiple measurements per side
            left_length = measure_terminal_length(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                left_terminal_roi,
                edge_contrast=edge_contrast_value,
                num_scans=100,
                debug=True
            )
            
            right_length = measure_terminal_length(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                right_terminal_roi,
                edge_contrast=edge_contrast_value,
                num_scans=100,
                debug=True
            )
            
            if left_length is None or right_length is None:
                print(f"[FAIL] Terminal Length Diff measurement failed")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Measurement failed"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} measurement fail", overlay)
            
            # For single measurement, create arrays with one element
            left_lengths = [left_length]
            right_lengths = [right_length]
            
            # Check difference
            result = check_terminal_length_difference(left_lengths, right_lengths, tolerance, debug=True)
            
            print(f"[INFO] Left Length: {result.get('worst_left', 0):.2f}, Right Length: {result.get('worst_right', 0):.2f}")
            print(f"[INFO] Max Difference: {result['max_difference']:.2f}, Tolerance: {result['tolerance']:.2f}")
            
            # ===== STEP MODE: Show dialog for FAILED steps =====
            if step_mode and step_callback and not result['is_pass']:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Diff={result['max_difference']:.2f} (Left={result.get('worst_left', 0):.2f}, Right={result.get('worst_right', 0):.2f})",
                    "expected": f"< {tolerance:.2f} pixels",
                    "suggested_min": 0,
                    "suggested_max": int(result['max_difference'] * 1.5),
                    "debug_info": f"Left Length: {result.get('worst_left', 0):.2f}\nRight Length: {result.get('worst_right', 0):.2f}\nMax Difference: {result['max_difference']:.2f}\nTolerance: {result['tolerance']:.2f}\n\nSuggested new tolerance: {int(result['max_difference'] * 1.5)}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
            
            if not result['is_pass']:
                print(f"[FAIL] Terminal Length Diff exceeds tolerance")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Diff={result['max_difference']:.2f} (Tolerance: {tolerance:.2f})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (Diff={result['max_difference']:.2f})")
        elif attr_name == "check_terminal_color":
            print(f"[INFO] Checking {test_name}...")

            ci_tab = device_thresholds.get("ColorInspectionTab", {}) if device_thresholds else {}
            contrast = int(ci_tab.get("ci_term_contrast", 255))
            left_width_cfg = int(ci_tab.get("ci_term_left_width", 255))
            right_width_cfg = int(ci_tab.get("ci_term_right_width", 255))
            offset_top = _ci_val(ci_tab, "ci_offset_top", 0)
            offset_bottom = _ci_val(ci_tab, "ci_offset_bottom", 0)
            offset_left = _ci_val(ci_tab, "ci_offset_left", 0)
            offset_right = _ci_val(ci_tab, "ci_offset_right", 0)

            if contrast == 255 and left_width_cfg == 255 and right_width_cfg == 255:
                print(f"[SKIP] {test_name} not configured")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            base_x = params.package_x + offset_left
            base_y = params.package_y + offset_top
            base_w = params.package_w - offset_left - offset_right
            base_h = params.package_h - offset_top - offset_bottom
            if base_w <= 0 or base_h <= 0:
                overlay, reason = draw_test_result(image, [f"{test_name}: Invalid ROI after offsets"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            left_w = left_width_cfg if left_width_cfg != 255 else int(base_w * 0.3)
            right_w = right_width_cfg if right_width_cfg != 255 else int(base_w * 0.3)

            left_roi = (base_x, base_y, left_w, base_h)
            right_roi = (base_x + base_w - right_w, base_y, right_w, base_h)

            left_mean = _safe_roi_mean_gray(working_image, left_roi)
            right_mean = _safe_roi_mean_gray(working_image, right_roi)
            if left_mean is None or right_mean is None:
                overlay, reason = draw_test_result(image, [f"{test_name}: ROI not found"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            window_min, window_max = _resolve_intensity_window(
                (left_mean + right_mean) / 2.0,
                getattr(params, "terminal_intensity_min", None),
                getattr(params, "terminal_intensity_max", None),
                contrast,
            )

            if window_min is None or window_max is None:
                print(f"[SKIP] {test_name} thresholds not set")
                messages.append(f"{test_name} SKIPPED (thresholds not set)")
                continue

            left_ok = window_min <= left_mean <= window_max
            right_ok = window_min <= right_mean <= window_max
            is_pass = left_ok and right_ok

            if step_mode:
                _draw_color_roi(image, left_roi, left_ok, "L")
                _draw_color_roi(image, right_roi, right_ok, "R")

            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"L={left_mean:.1f}, R={right_mean:.1f}",
                    "expected": f"{window_min}-{window_max}",
                    "suggested_min": max(0, int(min(left_mean, right_mean) - 5)),
                    "suggested_max": min(255, int(max(left_mean, right_mean) + 5)),
                    "debug_info": f"Left={left_mean:.1f}\nRight={right_mean:.1f}\nWindow={window_min}-{window_max}\nContrast={contrast}"
                }
                if not step_callback(step_result):
                    overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: L={left_mean:.1f}, R={right_mean:.1f} (Allowed {window_min}-{window_max})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (L={left_mean:.1f}, R={right_mean:.1f})")

        elif attr_name == "check_body_color":
            print(f"[INFO] Checking {test_name}...")

            ci_tab = device_thresholds.get("ColorInspectionTab", {}) if device_thresholds else {}
            contrast = int(ci_tab.get("ci_body_contrast", 255))
            roi_w_cfg = int(ci_tab.get("ci_body_width", 255))
            roi_h_cfg = int(ci_tab.get("ci_body_height", 255))
            offset_top = _ci_val(ci_tab, "ci_offset_top", 0)
            offset_bottom = _ci_val(ci_tab, "ci_offset_bottom", 0)
            offset_left = _ci_val(ci_tab, "ci_offset_left", 0)
            offset_right = _ci_val(ci_tab, "ci_offset_right", 0)

            if contrast == 255 and roi_w_cfg == 255 and roi_h_cfg == 255:
                print(f"[SKIP] {test_name} not configured")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            base_x = params.package_x + offset_left
            base_y = params.package_y + offset_top
            base_w = params.package_w - offset_left - offset_right
            base_h = params.package_h - offset_top - offset_bottom
            if base_w <= 0 or base_h <= 0:
                overlay, reason = draw_test_result(image, [f"{test_name}: Invalid ROI after offsets"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            roi_w = roi_w_cfg if roi_w_cfg != 255 else int(base_w * 0.5)
            roi_h = roi_h_cfg if roi_h_cfg != 255 else int(base_h * 0.5)

            roi_x = base_x + (base_w - roi_w) // 2
            roi_y = base_y + (base_h - roi_h) // 2
            roi = (roi_x, roi_y, roi_w, roi_h)

            mean_intensity = _safe_roi_mean_gray(working_image, roi)
            if mean_intensity is None:
                overlay, reason = draw_test_result(image, [f"{test_name}: ROI not found"], "FAIL")
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            window_min, window_max = _resolve_intensity_window(
                mean_intensity,
                getattr(params, "body_intensity_min", None),
                getattr(params, "body_intensity_max", None),
                contrast,
            )

            if window_min is None or window_max is None:
                print(f"[SKIP] {test_name} thresholds not set")
                messages.append(f"{test_name} SKIPPED (thresholds not set)")
                continue

            is_pass = window_min <= mean_intensity <= window_max

            if step_mode:
                _draw_color_roi(image, roi, is_pass, "BODY")

            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"{mean_intensity:.1f}",
                    "expected": f"{window_min}-{window_max}",
                    "suggested_min": max(0, int(mean_intensity - 5)),
                    "suggested_max": min(255, int(mean_intensity + 5)),
                    "debug_info": f"Mean={mean_intensity:.1f}\nWindow={window_min}-{window_max}\nContrast={contrast}"
                }
                if not step_callback(step_result):
                    overlay, reason = draw_test_result(image, [f"{test_name}: Test paused"], "PAUSE")
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {mean_intensity:.1f} (Allowed {window_min}-{window_max})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (mean={mean_intensity:.1f})")
        elif attr_name == "check_terminal_pogo":
            # Terminal Pogo - detect black defects (pogo holes) in terminal areas (FEED station)
            print(f"[INFO] Checking {test_name}...")

            # Parameters from device_inspection.json MultiTerminal section
            mt_tab = device_thresholds.get("MultiTerminal", {})
            contrast = int(mt_tab.get("mt_pogo_contrast", 255))
            min_area = int(mt_tab.get("mt_pogo_min_area", 255))
            min_square = int(mt_tab.get("mt_pogo_min_square", 255))
            offset_left = int(mt_tab.get("mt_pogo_corner_mask_left", 0))
            offset_right = int(mt_tab.get("mt_pogo_corner_mask_right", 0))

            # Check if parameters are configured
            if contrast == 255 or (min_area == 255 and min_square == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area}, min_square={min_square})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            defects_found, largest_area, is_pass, defect_rects = check_terminal_pogo(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
                min_square=min_square,
                offset_top=0,
                offset_bottom=0,
                offset_left=offset_left,
                offset_right=offset_right,
                apply_or=True,
                debug=True
            )

            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}")

            # Step mode dialog when failed
            if step_mode and step_callback and not is_pass:
                expected_txt = f"Area < {min_area}px"
                if min_square != 255:
                    expected_txt += f" and W/H < {min_square}px"
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": expected_txt,
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Defects Found: {defects_found}\nLargest Area: {largest_area}px\nMin Area Threshold: {min_area}px\nMin Square Threshold: {min_square}px\nContrast: {contrast}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            # Visualize defects on failure
            if not is_pass and defect_rects:
                print(f"[DEBUG] Drawing {len(defect_rects)} defect boxes")
                for rx, ry, rw, rh in defect_rects:
                    cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)

            if not is_pass:
                limit_txt = f"max area={min_area}px"
                if min_square != 255:
                    limit_txt += f", max W/H={min_square}px"
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px, {limit_txt})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (defects={defects_found})")
        elif attr_name == "check_terminal_offset":
            # Terminal Offset - verify terminals are within expected offset boundaries (FEED)
            print(f"[INFO] Checking {test_name}...")

            # Parameters from device_inspection.json TerminalPlatingTab
            tp_tab = device_thresholds.get("TerminalPlatingTab", {})
            
            # LEFT terminal offsets
            left_top = int(tp_tab.get("tpd_left_off_top", 0))
            left_bottom = int(tp_tab.get("tpd_left_off_bottom", 0))
            left_left = int(tp_tab.get("tpd_left_off_left", 0))
            left_right = int(tp_tab.get("tpd_left_off_right", 0))
            left_corner_x = int(tp_tab.get("tpd_left_corner_mask_x", 0))
            left_corner_y = int(tp_tab.get("tpd_left_corner_mask_y", 0))
            
            # RIGHT terminal offsets
            right_top = int(tp_tab.get("tpd_right_off_top", left_top))
            right_bottom = int(tp_tab.get("tpd_right_off_bottom", left_bottom))
            right_left = int(tp_tab.get("tpd_right_off_left", left_left))
            right_right = int(tp_tab.get("tpd_right_off_right", left_right))
            right_corner_x = int(tp_tab.get("tpd_right_corner_mask_x", left_corner_x))
            right_corner_y = int(tp_tab.get("tpd_right_corner_mask_y", left_corner_y))

            # Check if parameters are configured
            if all(x == 0 for x in [left_top, left_bottom, left_left, left_right, right_top, right_bottom, right_left, right_right]):
                print(f"[SKIP] {test_name} not configured (all offsets=0)")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            is_pass, debug_info = check_terminal_offset(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                left_top=left_top,
                left_bottom=left_bottom,
                left_left=left_left,
                left_right=left_right,
                left_corner_x=left_corner_x,
                left_corner_y=left_corner_y,
                right_top=right_top,
                right_bottom=right_bottom,
                right_left=right_left,
                right_right=right_right,
                right_corner_x=right_corner_x,
                right_corner_y=right_corner_y,
                debug=True
            )

            print(f"[INFO] {test_name}: left_valid={debug_info['left_valid']}, right_valid={debug_info['right_valid']}, pass={is_pass}")

            # Step mode dialog when failed
            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Left Valid: {debug_info['left_valid']}, Right Valid: {debug_info['right_valid']}",
                    "expected": "Both terminals within offset boundaries",
                    "suggested_min": None,
                    "suggested_max": None,
                    "debug_info": f"Left Info: {debug_info['left_info']}\nRight Info: {debug_info['right_info']}\nLeft ROI: {debug_info['left_roi']}\nRight ROI: {debug_info['right_roi']}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                failed_msg = []
                if not debug_info['left_valid']:
                    failed_msg.append(f"Left terminal invalid ({debug_info['left_info']})")
                if not debug_info['right_valid']:
                    failed_msg.append(f"Right terminal invalid ({debug_info['right_info']})")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: " + ", ".join(failed_msg)],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (terminals within bounds)")
        elif attr_name == "check_incomplete_termination_1":
            # Incomplete Termination 1 - black defects in terminal bands (top/bottom)
            print(f"[INFO] Checking {test_name}...")

            contrast = int(params.ranges.get("incomplete_termination_contrast_max", 255))
            min_area = int(params.ranges.get("incomplete_termination_min_area_max", 255))
            min_square = int(params.ranges.get("incomplete_termination_min_sqr_size_max", 255))
            offset_top = int(params.ranges.get("incomplete_termination_top_max", 0))
            offset_bottom = int(params.ranges.get("incomplete_termination_bottom_max", 0))
            offset_left = int(params.ranges.get("incomplete_termination_left_max", 0))
            offset_right = int(params.ranges.get("incomplete_termination_right_max", 0))
            corner_x = int(params.ranges.get("corner_offset_x_max", 0))
            corner_y = int(params.ranges.get("corner_offset_y_max", 0))

            if contrast == 255 or (min_area == 255 and min_square == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area}, min_square={min_square})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            defects_found, largest_area, is_pass, defect_rects = check_incomplete_termination_1(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
                min_square=min_square,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                corner_x=corner_x,
                corner_y=corner_y,
                apply_or=True,
                debug=True
            )

            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}")

            if step_mode and step_callback and not is_pass:
                expected_txt = f"Area < {min_area}px"
                if min_square != 255:
                    expected_txt += f" and W/H < {min_square}px"
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": expected_txt,
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Defects Found: {defects_found}\nLargest Area: {largest_area}px\nMin Area Threshold: {min_area}px\nMin Square Threshold: {min_square}px\nContrast: {contrast}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass and defect_rects:
                for rx, ry, rw, rh in defect_rects:
                    cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)

            if not is_pass:
                limit_txt = f"max area={min_area}px"
                if min_square != 255:
                    limit_txt += f", max W/H={min_square}px"
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px, {limit_txt})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (defects={defects_found})")
        elif attr_name == "check_terminal_oxidation":
            # Terminal Oxidation - detect color change (oxidation) in terminal (FEED)
            print(f"[INFO] Checking {test_name}...")

            # Parameters from device_inspection.json TerminalPlatingTab
            tp_tab = device_thresholds.get("TerminalPlatingTab", {})
            
            teach_contrast = int(tp_tab.get("tpd_oxidation_teach_contrast", 128))
            contrast_difference = int(tp_tab.get("tpd_oxidation_contrast_diff", 20))
            offset_top = int(tp_tab.get("tpd_oxidation_off_top", 0))
            offset_bottom = int(tp_tab.get("tpd_oxidation_off_bottom", 0))
            offset_left = int(tp_tab.get("tpd_oxidation_off_left", 0))
            offset_right = int(tp_tab.get("tpd_oxidation_off_right", 0))
            corner_x = int(tp_tab.get("tpd_oxidation_corner_x", 0))
            corner_y = int(tp_tab.get("tpd_oxidation_corner_y", 0))

            # Check if parameters are configured
            if teach_contrast == 255 or contrast_difference == 255:
                print(f"[SKIP] {test_name} not configured (teach={teach_contrast}, diff={contrast_difference})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue

            measured_contrast, difference, is_pass = check_terminal_oxidation(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                teach_contrast=teach_contrast,
                contrast_difference=contrast_difference,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                corner_x=corner_x,
                corner_y=corner_y,
                debug=True
            )

            print(f"[INFO] {test_name}: measured={measured_contrast}, taught={teach_contrast}, diff={difference}, threshold={contrast_difference}, pass={is_pass}")

            # Step mode dialog when failed
            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Contrast={measured_contrast}, Diff={difference}",
                    "expected": f"Within ±{contrast_difference} of {teach_contrast}",
                    "suggested_min": None,
                    "suggested_max": None,
                    "debug_info": f"Taught Contrast: {teach_contrast}\nMeasured Contrast: {measured_contrast}\nDifference: {difference}\nThreshold: {contrast_difference}\n\nSuggested new teach_contrast: {measured_contrast}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)

            if not is_pass:
                print(f"[FAIL] {test_name} - oxidation detected")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Oxidation detected (Contrast={measured_contrast}, Expected={teach_contrast}±{contrast_difference})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)

            messages.append(f"{test_name} OK (contrast={measured_contrast}, diff={difference})")
        elif attr_name in ("check_body_stain_1", "check_body_stain_2"):
            # Body Stain detection - check for black defects on body surface
            print(f"[INFO] Checking {test_name}...")
            
            # Determine which stain check (1 or 2)
            stain_num = attr_name[-1]  # Extract '1' or '2'
            
            # Get parameters from device_inspection.json BodyStainTab
            body_stain_tab = device_thresholds.get("BodyStainTab", {})
            
            contrast = int(body_stain_tab.get(f"bs{stain_num}_contrast", 255))
            min_area = int(body_stain_tab.get(f"bs{stain_num}_min_area", 255))
            min_square = int(body_stain_tab.get(f"bs{stain_num}_min_square", 255))
            apply_or = bool(body_stain_tab.get(f"bs{stain_num}_apply_or", True))
            offset_top = int(body_stain_tab.get(f"bs{stain_num}_off_top", 5))
            offset_bottom = int(body_stain_tab.get(f"bs{stain_num}_off_bottom", 5))
            offset_left = int(body_stain_tab.get(f"bs{stain_num}_off_left", 5))
            offset_right = int(body_stain_tab.get(f"bs{stain_num}_off_right", 5))
            red_dot_min = int(body_stain_tab.get(f"bs{stain_num}_red_dot_min", 255))
            
            # Check if parameters are configured (255 means not configured)
            if contrast == 255 or (min_area == 255 and min_square == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area}, min_square={min_square})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue
            
            # Run body stain check
            defects_found, largest_area, is_pass, defect_rects = check_body_stain(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
                min_square=min_square,
                apply_or=apply_or,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                red_dot_min=red_dot_min,
                debug=True
            )
            
            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}")
            
            # ===== STEP MODE: Show dialog for FAILED steps =====
            if step_mode and step_callback and not is_pass:
                expected_txt = f"Area < {min_area}px"
                if min_square != 255:
                    expected_txt += f" and W/H < {min_square}px" if not apply_or else f" or W/H < {min_square}px"
                if red_dot_min != 255:
                    expected_txt += f" and Count <= {red_dot_min}"
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": expected_txt,
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Defects Found: {defects_found}\nLargest Area: {largest_area}px\nMin Area Threshold: {min_area}px\nMin Square Threshold: {min_square}px\nRed Dot Min Count: {red_dot_min}\nApply OR: {apply_or}\nContrast: {contrast}\n\nSuggested new min_area: {int(largest_area * 1.2)}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
            
            # Draw defect boxes on visualization if failed
            if not is_pass and defect_rects:
                print(f"[DEBUG] Drawing {len(defect_rects)} defect boxes")
                import numpy as np
                for rect in defect_rects:
                    x, y, w, h = rect
                    # Draw red rectangle around defect
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            if not is_pass:
                print(f"[FAIL] {test_name} detected defects")
                limit_txt = f"max area={min_area}px"
                if min_square != 255:
                    limit_txt += f", max W/H={min_square}px"
                if red_dot_min != 255:
                    limit_txt += f", max count={red_dot_min}"
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px, {limit_txt})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (defects={defects_found})")

        elif attr_name in ("check_body_smear_1", "check_body_smear_2", "check_body_smear_3"):
            # Body Smear detection - check for white defects on body surface
            print(f"[INFO] Checking {test_name}...")
            
            # Determine which smear check (1, 2, or 3)
            smear_num = attr_name[-1]  # Extract '1', '2', or '3'
            
            # Get parameters from device_inspection.json BodySmearTab
            body_smear_tab = device_thresholds.get("BodySmearTab", {})
            
            contrast = int(body_smear_tab.get(f"bs{smear_num}_contrast", 255))
            min_area = int(body_smear_tab.get(f"bs{smear_num}_min_area", 255))
            min_square = int(body_smear_tab.get(f"bs{smear_num}_min_square", 255))
            use_avg_contrast = bool(body_smear_tab.get(f"bs{smear_num}_use_avg_contrast", True))
            apply_or = bool(body_smear_tab.get(f"bs{smear_num}_apply_or", True))
            offset_top = int(body_smear_tab.get(f"bs{smear_num}_offset_top", 5))
            offset_bottom = int(body_smear_tab.get(f"bs{smear_num}_offset_bottom", 5))
            offset_left = int(body_smear_tab.get(f"bs{smear_num}_offset_left", 5))
            offset_right = int(body_smear_tab.get(f"bs{smear_num}_offset_right", 5))
            
            # Check if parameters are configured (255 means not configured)
            if contrast == 255 or (min_area == 255 and min_square == 255):
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area}, min_square={min_square})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue
            
            # Run body smear check
            defects_found, largest_area, is_pass, defect_rects = check_body_smear(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
                min_square=min_square,
                use_avg_contrast=use_avg_contrast,
                apply_or=apply_or,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                debug=True
            )
            
            print(f"[INFO] {test_name}: defects={defects_found}, largest={largest_area}, pass={is_pass}")
            
            # ===== STEP MODE: Show dialog for FAILED steps =====
            if step_mode and step_callback and not is_pass:
                expected_txt = f"Area < {min_area}px"
                if min_square != 255:
                    expected_txt += f" and W/H < {min_square}px" if not apply_or else f" or W/H < {min_square}px"
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": expected_txt,
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Defects Found: {defects_found}\nLargest Area: {largest_area}px\nMin Area Threshold: {min_area}px\nMin Square Threshold: {min_square}px\nApply OR: {apply_or}\nContrast: {contrast}\n\nSuggested new min_area: {int(largest_area * 1.2)}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
            
            # Draw defect boxes on visualization if failed
            if not is_pass and defect_rects:
                print(f"[DEBUG] Drawing {len(defect_rects)} defect boxes")
                import numpy as np
                for rect in defect_rects:
                    x, y, w, h = rect
                    # Draw red rectangle around defect
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            if not is_pass:
                print(f"[FAIL] {test_name} detected defects")
                limit_txt = f"max area={min_area}px"
                if min_square != 255:
                    limit_txt += f", max W/H={min_square}px"
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px, {limit_txt})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (defects={defects_found})")
        elif attr_name == "check_reverse_chip":
            # Reverse Chip Check - detects if chip is accidentally reversed
            print(f"[INFO] Checking {test_name}...")
            
            # Get parameters from device_inspection.json BodySmearTab
            body_smear_tab = device_thresholds.get("BodySmearTab", {})
            
            teach_intensity = int(body_smear_tab.get("reverse_teach_intensity", 128))
            contrast_diff = int(body_smear_tab.get("reverse_contrast_diff", 20))
            
            # Run reverse chip check
            measured_intensity, is_reversed, is_pass = check_reverse_chip(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                teach_intensity=teach_intensity,
                contrast_diff=contrast_diff,
                debug=True
            )
            
            print(f"[INFO] {test_name}: measured={measured_intensity}, reversed={is_reversed}, pass={is_pass}")
            
            # ===== STEP MODE: Show dialog for FAILED steps =====
            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Intensity={measured_intensity}",
                    "expected": f"Within {contrast_diff} of {teach_intensity}",
                    "suggested_min": None,
                    "suggested_max": None,
                    "debug_info": f"Taught Intensity: {teach_intensity}\nMeasured Intensity: {measured_intensity}\nDifference: {abs(measured_intensity - teach_intensity)}\nThreshold: {contrast_diff}\n\nChip appears REVERSED!\n\nSuggested new teach_intensity: {measured_intensity}"
                }
                should_continue = step_callback(step_result)
                if not should_continue:
                    print(f"[STEP] Test aborted by user at {test_name}")
                    overlay, reason = draw_test_result(
                        image,
                        [f"{test_name}: Test paused for parameter adjustment"],
                        "PAUSE"
                    )
                    return TestResult(TestStatus.FAIL, "Test paused by user", overlay)
            
            if not is_pass:
                print(f"[FAIL] {test_name} - chip appears reversed")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Reversed! (intensity={measured_intensity}, expected={teach_intensity}±{contrast_diff})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (intensity={measured_intensity})")
        elif attr_name == "outer_pocket_stain":
            print(f"[INFO] Checking {test_name}...")

            pocket_loc = (params.pocket_x, params.pocket_y, params.pocket_w, params.pocket_h)
            if pocket_loc[2] <= 0 or pocket_loc[3] <= 0:
                print(f"[FAIL] {test_name} - pocket not available")
                return _post_seal_fail(
                    f"{test_name} failed",
                    ["Pocket location not available"]
                )

            stain_valid, stain_details = check_outer_pocket_stain(
                image,
                pocket_loc,
                pocket_params=pocket_params,
                debug=True
            )

            if not stain_valid:
                print(f"[FAIL] {test_name} failed")
                for msg in stain_details.get("messages", []):
                    print(f"  [FAIL] {msg}")
                return _post_seal_fail(
                    f"{test_name} failed",
                    [f"{test_name} failed"] + stain_details.get("messages", [])
                )

            for msg in stain_details.get("messages", []):
                print(f"  [PASS] {msg}")
                messages.append(msg)

        elif attr_name == "enable_emboss_tape_pickup":
            print(f"[INFO] Checking {test_name}...")

            pocket_loc = (params.pocket_x, params.pocket_y, params.pocket_w, params.pocket_h)
            pkg_loc = (params.package_x, params.package_y, params.package_w, params.package_h)

            emboss_valid, emboss_details = check_emboss_tape_pickup(
                image,
                pocket_loc,
                pkg_loc,
                pocket_params=pocket_params,
                debug=True
            )

            if not emboss_valid:
                print(f"[FAIL] {test_name} failed")
                return _post_seal_fail(
                    f"{test_name} failed",
                    [f"{test_name} failed"] + emboss_details.get("messages", [])
                )

            for msg in emboss_details.get("messages", []):
                print(f"  [PASS] {msg}")
                messages.append(msg)

        elif attr_name == "enable_sealing_stain":
            print(f"[INFO] Checking {test_name}...")

            pocket_loc = (params.pocket_x, params.pocket_y, params.pocket_w, params.pocket_h)
            if pocket_loc[2] <= 0 or pocket_loc[3] <= 0:
                print(f"[FAIL] {test_name} - pocket not available")
                return _post_seal_fail(
                    f"{test_name} failed",
                    ["Pocket location not available"]
                )

            stain_valid, stain_details = check_sealing_stain(
                image,
                pocket_loc,
                pocket_params=pocket_params,
                debug=True
            )

            if not stain_valid:
                print(f"[FAIL] {test_name} failed")
                for msg in stain_details.get("messages", []):
                    print(f"  [FAIL] {msg}")
                return _post_seal_fail(
                    f"{test_name} failed",
                    [f"{test_name} failed"] + stain_details.get("messages", [])
                )

            for msg in stain_details.get("messages", []):
                print(f"  [PASS] {msg}")
                messages.append(msg)

        elif attr_name == "enable_sealing_stain2":
            print(f"[INFO] Checking {test_name}...")

            pocket_loc = (params.pocket_x, params.pocket_y, params.pocket_w, params.pocket_h)
            if pocket_loc[2] <= 0 or pocket_loc[3] <= 0:
                print(f"[FAIL] {test_name} - pocket not available")
                return _post_seal_fail(
                    f"{test_name} failed",
                    ["Pocket location not available"]
                )

            stain_valid, stain_details = check_sealing_stain2(
                image,
                pocket_loc,
                pocket_params=pocket_params,
                debug=True
            )

            if not stain_valid:
                print(f"[FAIL] {test_name} failed")
                for msg in stain_details.get("messages", []):
                    print(f"  [FAIL] {msg}")
                return _post_seal_fail(
                    f"{test_name} failed",
                    [f"{test_name} failed"] + stain_details.get("messages", [])
                )

            for msg in stain_details.get("messages", []):
                print(f"  [PASS] {msg}")
                messages.append(msg)
        
        elif attr_name == "enable_sealing_shift":
            print(f"[INFO] Checking {test_name}...")

            pocket_loc = (params.pocket_x, params.pocket_y, params.pocket_w, params.pocket_h)
            if pocket_loc[2] <= 0 or pocket_loc[3] <= 0:
                print(f"[FAIL] {test_name} - pocket not available")
                return _post_seal_fail(
                    f"{test_name} failed",
                    ["Pocket location not available"]
                )

            shift_valid, shift_details = check_sealing_shift(
                image,
                pocket_loc,
                pocket_params=pocket_params,
                debug=True
            )

            if not shift_valid:
                print(f"[FAIL] {test_name} failed")
                for msg in shift_details.get("messages", []):
                    print(f"  [FAIL] {msg}")
                return _post_seal_fail(
                    f"{test_name} failed",
                    [f"{test_name} failed"] + shift_details.get("messages", [])
                )

            for msg in shift_details.get("messages", []):
                print(f"  [PASS] {msg}")
                messages.append(msg)

            # For non-measurement tests, just mark as OK
            messages.append(f"{test_name} OK")
        
        elif attr_name == "hole_side_shift":
            print(f"[INFO] Checking {test_name}...")

            pocket_loc = (params.pocket_x, params.pocket_y, params.pocket_w, params.pocket_h)
            if pocket_loc[2] <= 0 or pocket_loc[3] <= 0:
                print(f"[FAIL] {test_name} - pocket not available")
                return _post_seal_fail(
                    f"{test_name} failed",
                    ["Pocket location not available"]
                )

            hole_valid, hole_details = check_hole_side_shift(
                image,
                pocket_loc,
                pocket_params=pocket_params,
                debug=True
            )

            if not hole_valid:
                print(f"[FAIL] {test_name} failed")
                for msg in hole_details.get("messages", []):
                    print(f"  [FAIL] {msg}")
                return _post_seal_fail(
                    f"{test_name} failed",
                    [f"{test_name} failed"] + hole_details.get("messages", [])
                )

            for msg in hole_details.get("messages", []):
                print(f"  [PASS] {msg}")
                messages.append(msg)
        
        elif attr_name == "sealing_distance_center":
            print(f"[INFO] Checking {test_name}...")

            pocket_loc = (params.pocket_x, params.pocket_y, params.pocket_w, params.pocket_h)
            if pocket_loc[2] <= 0 or pocket_loc[3] <= 0:
                print(f"[FAIL] {test_name} - pocket not available")
                return _post_seal_fail(
                    f"{test_name} failed",
                    ["Pocket location not available"]
                )

            dist_valid, dist_details = check_sealing_distance_center(
                image,
                pocket_loc,
                pocket_params=pocket_params,
                debug=True
            )

            if not dist_valid:
                print(f"[FAIL] {test_name} failed")
                for msg in dist_details.get("messages", []):
                    print(f"  [FAIL] {msg}")
                return _post_seal_fail(
                    f"{test_name} failed",
                    [f"{test_name} failed"] + dist_details.get("messages", [])
                )

            for msg in dist_details.get("messages", []):
                print(f"  [PASS] {msg}")
                messages.append(msg)
        
        elif attr_name == "bottom_dent":
            print(f"[INFO] Checking {test_name}...")

            pocket_loc = (params.pocket_x, params.pocket_y, params.pocket_w, params.pocket_h)
            if pocket_loc[2] <= 0 or pocket_loc[3] <= 0:
                print(f"[FAIL] {test_name} - pocket not available")
                return _post_seal_fail(
                    f"{test_name} failed",
                    ["Pocket location not available"]
                )

            dent_valid, dent_details = check_bottom_dent_inspection(
                image,
                pocket_loc,
                pocket_params=pocket_params,
                debug=True
            )

            if not dent_valid:
                print(f"[FAIL] {test_name} failed")
                for msg in dent_details.get("messages", []):
                    print(f"  [FAIL] {msg}")
                return _post_seal_fail(
                    f"{test_name} failed",
                    [f"{test_name} failed"] + dent_details.get("messages", [])
                )

            for msg in dent_details.get("messages", []):
                print(f"  [PASS] {msg}")
                messages.append(msg)
        
        elif attr_name == "special_black_emboss_sealing":
            print(f"[INFO] Checking {test_name}...")

            pocket_loc = (params.pocket_x, params.pocket_y, params.pocket_w, params.pocket_h)
            if pocket_loc[2] <= 0 or pocket_loc[3] <= 0:
                print(f"[FAIL] {test_name} - pocket not available")
                return _post_seal_fail(
                    f"{test_name} failed",
                    ["Pocket location not available"]
                )

            emboss_valid, emboss_details = check_special_black_emboss_sealing(
                image,
                pocket_loc,
                pocket_params=pocket_params,
                debug=True
            )

            if not emboss_valid:
                print(f"[FAIL] {test_name} failed")
                for msg in emboss_details.get("messages", []):
                    print(f"  [FAIL] {msg}")
                return _post_seal_fail(
                    f"{test_name} failed",
                    [f"{test_name} failed"] + emboss_details.get("messages", [])
                )

            for msg in emboss_details.get("messages", []):
                print(f"  [PASS] {msg}")
                messages.append(msg)

    # -----------------------------------------------
    # 5. ALL ENABLED TESTS PASSED
    # -----------------------------------------------
    print("\n[PASS] All enabled inspections passed for FEED station")

    test_summary = f"Enabled Tests:\n" + "\n".join([f"✓ {msg}" for msg in messages])
    if skipped_tests:
        test_summary += f"\n\nSkipped Tests:\n" + "\n".join([f"• {test}" for test in skipped_tests])

    print(f"[INFO] Tests run: {len(messages)}, Skipped: {len(skipped_tests)}")

    # draw_test_result already adds PASS indicator in corner
    overlay, reason = draw_test_result(
        image,
        [test_summary],
        "PASS"
    )

    return TestResult(TestStatus.PASS, "OK", overlay)