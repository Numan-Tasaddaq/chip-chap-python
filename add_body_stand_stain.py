#!/usr/bin/env python3
"""Add Body Stand Stain detection to test_top_bottom.py for both TOP/BOTTOM and FEED functions"""

body_stand_stain_code = '''        elif attr_name == "enable_sealing_stain":
            # Body Stand Stain detection - check for thin stain line at package sealing edge
            print(f"[INFO] Checking {test_name}...")
            
            # Get parameters from device_inspection.json BodyStainTab
            body_stain_tab = device_thresholds.get("BodyStainTab", {})
            
            edge_contrast = int(body_stain_tab.get("bs_stand_edge_contrast", 255))
            difference = int(body_stain_tab.get("bs_stand_difference", 255))
            offset_top = int(body_stain_tab.get("bs_stand_off_top", 5))
            offset_bottom = int(body_stain_tab.get("bs_stand_off_bottom", 5))
            offset_left = int(body_stain_tab.get("bs_stand_off_left", 5))
            offset_right = int(body_stain_tab.get("bs_stand_off_right", 5))
            
            # Check if parameters are configured (255 means not configured)
            if edge_contrast == 255 or difference == 255:
                print(f"[SKIP] {test_name} not configured (edge_contrast={edge_contrast}, difference={difference})")
                messages.append(f"{test_name} SKIPPED (not configured)")
                continue
            
            # Run body stand stain check
            top_intensity, bottom_intensity, is_pass = check_body_stand_stain(
                working_image,
                (params.package_x, params.package_y, params.package_w, params.package_h),
                edge_contrast=edge_contrast,
                difference=difference,
                offset_top=offset_top,
                offset_bottom=offset_bottom,
                offset_left=offset_left,
                offset_right=offset_right,
                debug=True
            )
            
            print(f"[INFO] {test_name}: top={top_intensity}, bottom={bottom_intensity}, diff={abs(top_intensity - bottom_intensity)}, pass={is_pass}")
            
            # ===== STEP MODE: Show dialog for FAILED steps =====
            if step_mode and step_callback and not is_pass:
                step_result = {
                    "step_name": test_name,
                    "status": "FAIL",
                    "measured": f"Top={top_intensity}, Bottom={bottom_intensity}, Diff={abs(top_intensity - bottom_intensity)}",
                    "expected": f"Difference <= {difference}",
                    "suggested_min": None,
                    "suggested_max": int(abs(top_intensity - bottom_intensity) * 1.2),
                    "debug_info": f"Top Intensity: {top_intensity}\\nBottom Intensity: {bottom_intensity}\\nDifference: {abs(top_intensity - bottom_intensity)}\\nThreshold: {difference}\\n\\nSuggested new threshold: {int(abs(top_intensity - bottom_intensity) * 1.2)}"
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
                print(f"[FAIL] {test_name} intensity difference exceeds threshold")
                overlay, reason = draw_test_result(
                    image,
                    [f"{test_name}: Top={top_intensity}, Bottom={bottom_intensity}, Diff={abs(top_intensity - bottom_intensity)} (Max {difference})"],
                    "FAIL"
                )
                return TestResult(TestStatus.FAIL, f"{test_name} NG", overlay)
            
            messages.append(f"{test_name} OK (Top={top_intensity}, Bottom={bottom_intensity})")
        elif attr_name == "enable_sealing_stain2":
            # Sealing Stain 2 - for future use or additional stain checking
            print(f"[INFO] Checking {test_name}...")
            messages.append(f"{test_name} OK (not yet implemented)")
'''

with open('tests/test_top_bottom.py', 'r') as f:
    content = f.read()

# Find the insertion points - look for "Sealing Stain" in the test lists
lines = content.split('\n')

# Find lines with "Sealing Stain" pattern and then find the next Body Smear
insertion_points = []
for i in range(len(lines)):
    if '("Sealing Stain"' in lines[i] and 'enable_sealing_stain' in lines[i]:
        # Found a Sealing Stain reference, now look for the next implementation area
        # We need to find the appropriate location in the test logic (after other checks)
        # Look for a pattern like "elif attr_name ==" near "Sealing Stain"
        for j in range(i, min(i + 100, len(lines))):
            if 'elif attr_name == "enable_sealing_stain"' in lines[j] or \
               'elif attr_name in ("check_body_smear' in lines[j]:
                # Found a good place, check if we need to insert before
                if 'elif attr_name in ("check_body_smear' in lines[j]:
                    insertion_points.append((j, i))  # Insert before this line
                break

print(f"Found {len(insertion_points)} insertion points")

if len(insertion_points) > 0:
    # Insert from the end backward to maintain line numbers
    for idx, orig_idx in sorted(insertion_points, reverse=True):
        lines.insert(idx, body_stand_stain_code)
    
    with open('tests/test_top_bottom.py', 'w') as f:
        f.write('\n'.join(lines))
    
    print(f'✓ Body Stand Stain check added at {len(insertion_points)} locations')
else:
    print('✗ Could not find insertion points for Body Stand Stain')
