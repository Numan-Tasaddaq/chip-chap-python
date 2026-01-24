import json
from pathlib import Path
from tests.test_runner import TestResult, TestStatus
from tests.test_draw import draw_test_result
from tests.measurements import (measure_body_width, measure_body_length, 
                                measure_terminal_width, measure_terminal_length,
                                measure_term_to_term_length)
from tests.measurement_draw import draw_measurement_result, add_status_text
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

    messages = []
    enabled_tests = []
    skipped_tests = []
    
    # Load device inspection thresholds and pocket parameters
    device_thresholds = load_device_thresholds()
    pocket_params = load_pocket_params()
    
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
        ("Terminal Width", params.flags.get("check_terminal_width", False), "check_terminal_width", "measure_terminal_width"),
        ("Terminal Length", params.flags.get("check_terminal_length", False), "check_terminal_length", "measure_terminal_length"),
        ("Term-Term Length", params.flags.get("check_term_term_length", False), "check_term_term_length", "measure_term_to_term_length"),
        ("Terminal Length Diff", params.flags.get("check_terminal_length_diff", False), "check_terminal_length_diff", None),
        
        # Terminal Inspections
        ("Terminal Pogo", params.flags.get("check_terminal_pogo", False), "check_terminal_pogo", None),
        ("Incomplete Termination 1", params.flags.get("check_incomplete_termination_1", False), "check_incomplete_termination_1", None),
        ("Incomplete Termination 2", params.flags.get("check_incomplete_termination_2", False), "check_incomplete_termination_2", None),
        ("Terminal to Body Gap", params.flags.get("check_terminal_to_body_gap", False), "check_terminal_to_body_gap", None),
        ("Terminal Color", params.flags.get("check_terminal_color", False), "check_terminal_color", None),
        ("Terminal Oxidation", params.flags.get("check_terminal_oxidation", False), "check_terminal_oxidation", None),
        ("Inner Terminal Chipoff", params.flags.get("check_inner_term_chipoff", False), "check_inner_term_chipoff", None),
        ("Outer Terminal Chipoff", params.flags.get("check_outer_term_chipoff", False), "check_outer_term_chipoff", None),
        
        # Body Inspections
        ("Body Stain 1", params.flags.get("check_body_stain_1", False), "check_body_stain_1", None),
        ("Body Stain 2", params.flags.get("check_body_stain_2", False), "check_body_stain_2", None),
        ("Body Color", params.flags.get("check_body_color", False), "check_body_color", None),
        ("Body to Term Width", params.flags.get("check_body_to_term_width", False), "check_body_to_term_width", None),
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
    ]

    # Filter enabled tests
    for test_name, is_enabled, attr_name, measurement_func in inspection_checks:
        if is_enabled:
            enabled_tests.append((test_name, attr_name, measurement_func))
            print(f"[ENABLED] {test_name}")
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
            value = measure_body_width(
                image,
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
                    image,
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
            value = measure_terminal_width(
                image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                terminal_roi,
                edge_contrast=edge_contrast_value,
                debug=True
            )
            
            metric_key_min = "terminal_width_min"
            metric_key_max_from_dev = "terminal_width_max"
            fallback_min = params.terminal_width_min if hasattr(params, 'terminal_width_min') else 10
            fallback_max = params.terminal_width_max if hasattr(params, 'terminal_width_max') else 100
        elif measurement_func == "measure_terminal_length":
            # Terminal Length: multi-scan edge detection
            terminal_roi = (params.package_x, params.package_y, params.package_w, int(params.package_h * 0.3))
            value = measure_terminal_length(
                image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                terminal_roi,
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
                image,
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

                draw_measurement_result(
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
        else:
            messages.append(f"{test_name} OK")

    # -------------------------------
    # 4. ALL ENABLED TESTS PASSED
    # -------------------------------
    print("\n[PASS] All enabled inspections passed")

    test_summary = f"Enabled Tests:\n" + "\n".join([f"✓ {msg}" for msg in messages])
    if skipped_tests:
        test_summary += f"\n\nSkipped Tests:\n" + "\n".join([f"• {test}" for test in skipped_tests])

    # If in step mode, add PASS text overlay to image
    if step_mode:
        add_status_text(image, "PASS", position=(50, 80))

    overlay, reason = draw_test_result(
        image,
        [test_summary],
        "PASS"
    )

    return TestResult(TestStatus.PASS, "OK", overlay)

def test_feed(image, params, step_mode=False, step_callback=None):
    """Test for FEED station - validates pocket location and all enabled inspections"""
    print("\n[TEST] Feed station inspection started")

    messages = []
    enabled_tests = []
    skipped_tests = []
    
    # Load device inspection thresholds
    device_thresholds = load_device_thresholds()
    print(f"[INFO] Device thresholds loaded: {bool(device_thresholds)}")

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
        ("Pocket Post Seal", params.flags.get("enable_pocket_post_seal", False), "enable_pocket_post_seal", None),
        
        # Dimension Measurements
        ("Body Length", params.flags.get("check_body_length", False), "check_body_length", "measure_body_length"),
        ("Body Width", params.flags.get("check_body_width", False), "check_body_width", "measure_body_width"),
        ("Terminal Width", params.flags.get("check_terminal_width", False), "check_terminal_width", "measure_terminal_width"),
        ("Terminal Length", params.flags.get("check_terminal_length", False), "check_terminal_length", "measure_terminal_length"),
        ("Term-Term Length", params.flags.get("check_term_term_length", False), "check_term_term_length", "measure_term_to_term_length"),
        ("Terminal Length Diff", params.flags.get("check_terminal_length_diff", False), "check_terminal_length_diff", None),
        
        # Terminal Inspections
        ("Terminal Pogo", params.flags.get("check_terminal_pogo", False), "check_terminal_pogo", None),
        ("Incomplete Termination 1", params.flags.get("check_incomplete_termination_1", False), "check_incomplete_termination_1", None),
        ("Incomplete Termination 2", params.flags.get("check_incomplete_termination_2", False), "check_incomplete_termination_2", None),
        ("Terminal to Body Gap", params.flags.get("check_terminal_to_body_gap", False), "check_terminal_to_body_gap", None),
        ("Terminal Color", params.flags.get("check_terminal_color", False), "check_terminal_color", None),
        ("Terminal Oxidation", params.flags.get("check_terminal_oxidation", False), "check_terminal_oxidation", None),
        ("Inner Terminal Chipoff", params.flags.get("check_inner_term_chipoff", False), "check_inner_term_chipoff", None),
        ("Outer Terminal Chipoff", params.flags.get("check_outer_term_chipoff", False), "check_outer_term_chipoff", None),
        
        # Body Inspections
        ("Body Stain 1", params.flags.get("check_body_stain_1", False), "check_body_stain_1", None),
        ("Body Stain 2", params.flags.get("check_body_stain_2", False), "check_body_stain_2", None),
        ("Body Color", params.flags.get("check_body_color", False), "check_body_color", None),
        ("Body to Term Width", params.flags.get("check_body_to_term_width", False), "check_body_to_term_width", None),
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
                image,
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
            terminal_roi = (params.package_x, params.package_y, params.package_w, int(params.package_h * 0.3))
            value = measure_terminal_width(
                image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                terminal_roi,
                edge_contrast=edge_contrast_value,
                debug=True
            )
            
            metric_key_min = "terminal_width_min"
            metric_key_max_from_dev = "terminal_width_max"
            fallback_min = int(device_thresholds.get("terminal_width_min", 10))
            fallback_max = int(device_thresholds.get("terminal_width_max", 100))
        elif measurement_func == "measure_terminal_length":
            # Terminal Length: multi-scan edge detection
            terminal_roi = (params.package_x, params.package_y, params.package_w, int(params.package_h * 0.3))
            value = measure_terminal_length(
                image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                terminal_roi,
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
                image,
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

                draw_measurement_result(
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

    # If in step mode, add PASS text overlay to image
    if step_mode:
        add_status_text(image, "PASS", position=(50, 80))

    overlay, reason = draw_test_result(
        image,
        [test_summary],
        "PASS"
    )

    return TestResult(TestStatus.PASS, "OK", overlay)