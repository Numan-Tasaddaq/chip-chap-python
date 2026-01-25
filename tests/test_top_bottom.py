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
from tests.body_smear import check_body_smear
import cv2

# Load device inspection thresholds
DEVICE_INSPECTION_FILE = Path("device_inspection.json")
POCKET_PARAMS_FILE = Path("pocket_params.json")

def load_device_thresholds():
    """Load device inspection thresholds from device_inspection.json"""
    if not DEVICE_INSPECTION_FILE.exists():
        return {}
    
    try:
        with open(DEVICE_INSPECTION_FILE, "r") as f:
            data = json.load(f)
        return data.get("UnitParameters", {})
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

def test_top_bottom(image, params, step_mode=False, step_callback=None):
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
    # Read from params.flags dictionary (shared across stations)
    inspection_checks = [
        # Package & Pocket
        ("Package Location", params.flags.get("enable_package_location", False), "enable_package_location", None),
        
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
        ("Reverse Chip", params.flags.get("check_reverse_chip", False), "check_reverse_chip", None),
        ("Smear White", params.flags.get("check_smear_white", False), "check_smear_white", None),
        
        # Body Edge
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
        elif attr_name in ("check_body_smear_1", "check_body_smear_2", "check_body_smear_3"):
            # Body Smear detection - check for white defects on body surface
            print(f"[INFO] Checking {test_name}...")
            
            # Determine which smear check (1, 2, or 3)
            smear_num = attr_name[-1]  # Extract '1', '2', or '3'
            
            # Get parameters from device_inspection.json BodySmearTab
            body_smear_tab = device_thresholds.get("BodySmearTab", {})
            
            contrast = int(body_smear_tab.get(f"bs{smear_num}_contrast", 255))
            min_area = int(body_smear_tab.get(f"bs{smear_num}_min_area", 255))
            use_avg_contrast = bool(body_smear_tab.get(f"bs{smear_num}_use_avg_contrast", True))
            apply_or = bool(body_smear_tab.get(f"bs{smear_num}_apply_or", True))
            offset_top = int(body_smear_tab.get(f"bs{smear_num}_offset_top", 5))
            offset_bottom = int(body_smear_tab.get(f"bs{smear_num}_offset_bottom", 5))
            offset_left = int(body_smear_tab.get(f"bs{smear_num}_offset_left", 5))
            offset_right = int(body_smear_tab.get(f"bs{smear_num}_offset_right", 5))
            
            # Check if parameters are configured (255 means not configured)
            if contrast == 255 or min_area == 255:
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue
            
            # Run body smear check
            defects_found, largest_area, is_pass, defect_rects = check_body_smear(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
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
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": f"Area < {min_area}px",
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Defects Found: {defects_found}\nLargest Area: {largest_area}px\nMin Area Threshold: {min_area}px\nContrast: {contrast}\n\nSuggested new min_area: {int(largest_area * 1.2)}"
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
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px, max={min_area}px)"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (defects={defects_found})")
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

def test_feed(image, params, step_mode=False, step_callback=None):
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

    # -----------------------------------------------
    # 1. Check Package Location
    # -----------------------------------------------
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
    else:
        print(f"[OK] Package taught: ({params.package_x}, {params.package_y}, {params.package_w}, {params.package_h})")

    # -----------------------------------------------
    # 2. Check Pocket Location (FEED specific)
    # -----------------------------------------------
    if params.flags.get("enable_pocket_location", False):
        if params.pocket_w <= 0 or params.pocket_h <= 0:
            print("[FAIL] Pocket not taught")
            overlay, reason = draw_test_result(
                image, ["Pocket not taught", "Please run Teach first"], "FAIL"
            )
            return TestResult(TestStatus.FAIL, "Pocket not taught", overlay)

        print(f"[OK] Pocket taught: ({params.pocket_x}, {params.pocket_y}, {params.pocket_w}, {params.pocket_h})")
    else:
        print("[SKIP] Pocket inspection disabled")
        skipped_tests.append("Pocket Location (disabled)")

    # -----------------------------------------------
    # 3. Build list of enabled inspections IN ORDER
    # -----------------------------------------------
    inspection_checks = [
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
        ("Reverse Chip", params.flags.get("check_reverse_chip", False), "check_reverse_chip", None),
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
        
        if measurement_func == "measure_body_width":
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
        elif attr_name in ("check_body_smear_1", "check_body_smear_2", "check_body_smear_3"):
            # Body Smear detection - check for white defects on body surface
            print(f"[INFO] Checking {test_name}...")
            
            # Determine which smear check (1, 2, or 3)
            smear_num = attr_name[-1]  # Extract '1', '2', or '3'
            
            # Get parameters from device_inspection.json BodySmearTab
            body_smear_tab = device_thresholds.get("BodySmearTab", {})
            
            contrast = int(body_smear_tab.get(f"bs{smear_num}_contrast", 255))
            min_area = int(body_smear_tab.get(f"bs{smear_num}_min_area", 255))
            use_avg_contrast = bool(body_smear_tab.get(f"bs{smear_num}_use_avg_contrast", True))
            apply_or = bool(body_smear_tab.get(f"bs{smear_num}_apply_or", True))
            offset_top = int(body_smear_tab.get(f"bs{smear_num}_offset_top", 5))
            offset_bottom = int(body_smear_tab.get(f"bs{smear_num}_offset_bottom", 5))
            offset_left = int(body_smear_tab.get(f"bs{smear_num}_offset_left", 5))
            offset_right = int(body_smear_tab.get(f"bs{smear_num}_offset_right", 5))
            
            # Check if parameters are configured (255 means not configured)
            if contrast == 255 or min_area == 255:
                print(f"[SKIP] {test_name} not configured (contrast={contrast}, min_area={min_area})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue
            
            # Run body smear check
            defects_found, largest_area, is_pass, defect_rects = check_body_smear(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                contrast=contrast,
                min_area=min_area,
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
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Defects={defects_found}, Largest={largest_area}px",
                    "expected": f"Area < {min_area}px",
                    "suggested_min": None,
                    "suggested_max": int(largest_area * 1.2) if largest_area > 0 else min_area,
                    "debug_info": f"Defects Found: {defects_found}\nLargest Area: {largest_area}px\nMin Area Threshold: {min_area}px\nContrast: {contrast}\n\nSuggested new min_area: {int(largest_area * 1.2)}"
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
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: {defects_found} defects (largest={largest_area}px, max={min_area}px)"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (defects={defects_found})")
        else:
            # For non-measurement tests, just mark as OK
            messages.append(f"{test_name} OK")

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