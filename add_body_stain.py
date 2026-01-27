#!/usr/bin/env python3
"""Add Body Stain detection to test_top_bottom.py for both TOP/BOTTOM and FEED functions"""

import re

body_stain_code = '''        elif attr_name in ("check_body_stain_1", "check_body_stain_2"):
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
                    "debug_info": f"Defects Found: {defects_found}\\nLargest Area: {largest_area}px\\nMin Area Threshold: {min_area}px\\nMin Square Threshold: {min_square}px\\nApply OR: {apply_or}\\nContrast: {contrast}\\n\\nSuggested new min_area: {int(largest_area * 1.2)}"
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
'''

with open('tests/test_top_bottom.py', 'r') as f:
    content = f.read()

# Find both occurrences (test_top_bottom and test_feed)
lines = content.split('\n')

# Find Terminal Length Diff lines and subsequent Body Smear pattern
replacements = []
for i in range(len(lines) - 1):
    if 'Terminal Length Diff exceeds tolerance' in lines[i]:
        # Found a Terminal Length context, now find the next check_body_smear in the same function
        for j in range(i, min(i + 50, len(lines))):
            if 'elif attr_name in ("check_body_smear_1"' in lines[j]:
                # Found it! Record this as a replacement point
                replacements.append(j)
                break

print(f"Found {len(replacements)} replacement points at lines: {replacements}")

if len(replacements) >= 2:
    # Replace from the end to the beginning to maintain line numbers
    for idx in sorted(replacements, reverse=True):
        lines.insert(idx, body_stain_code)
    
    with open('tests/test_top_bottom.py', 'w') as f:
        f.write('\n'.join(lines))
    
    print('✓ Body Stain check added to both test_top_bottom and test_feed functions')
elif len(replacements) == 1:
    lines.insert(replacements[0], body_stain_code)
    with open('tests/test_top_bottom.py', 'w') as f:
        f.write('\n'.join(lines))
    print('✓ Body Stain check added to test_top_bottom function')
else:
    print('✗ Could not find replacement points')
