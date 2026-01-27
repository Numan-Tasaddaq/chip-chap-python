#!/usr/bin/env python3
"""Add red_dot_min parameter to Body Stain detection"""

import re

filepath = r"e:\Office Work\chip-chap-python\tests\test_top_bottom.py"

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track which Body Stain section we're in
in_top_bottom = False
in_feed = False
modified_count = 0

i = 0
while i < len(lines):
    # Detect which function we're in
    if 'def test_top_bottom' in lines[i]:
        in_top_bottom = True
        in_feed = False
    elif 'def test_feed' in lines[i]:
        in_top_bottom = False
        in_feed = True
    
    # In test_top_bottom Body Stain section
    if in_top_bottom and 'elif attr_name in ("check_body_stain_1", "check_body_stain_2"):' in lines[i]:
        # Find where we need to add red_dot_min parameter
        # Look for offset_right line
        j = i
        while j < min(i + 50, len(lines)):
            if 'offset_right = int(body_stain_tab.get' in lines[j] and 'off_right' in lines[j]:
                # Check if next non-empty line is the config check comment
                k = j + 1
                while k < len(lines) and lines[k].strip() == '':
                    k += 1
                if k < len(lines) and '# Check if parameters are configured' in lines[k]:
                    # Insert red_dot_min parameter loading
                    indent = '            '
                    lines.insert(j + 1, f'{indent}red_dot_min = int(body_stain_tab.get(f"bs{{stain_num}}_red_dot_min", 255))\n')
                    modified_count += 1
                    i = j  # Adjust index since we inserted
                break
            j += 1
        
        # Now find the check_body_stain function call and add red_dot_min
        j = i
        found_call = False
        while j < min(i + 100, len(lines)):
            if 'defects_found, largest_area, is_pass, defect_rects = check_body_stain(' in lines[j]:
                # Find the offset_right parameter
                k = j
                while k < min(j + 30, len(lines)):
                    if 'offset_right=offset_right,' in lines[k]:
                        # Add red_dot_min after offset_right
                        indent = lines[k][:len(lines[k]) - len(lines[k].lstrip())]
                        lines.insert(k + 1, f'{indent}red_dot_min=red_dot_min,\n')
                        modified_count += 1
                        found_call = True
                        break
                    k += 1
                break
            j += 1
        
        # Add red_dot_min check in step mode section
        j = i
        while j < min(i + 200, len(lines)):
            if 'if min_square != 255:' in lines[j] and 'expected_txt +=' in lines[j + 1]:
                # Find the line after the min_square check in test_top_bottom
                if 'step_result = {' in lines[j + 2]:
                    # Insert red_dot_min check before step_result
                    indent = '                '
                    lines.insert(j + 2, f'{indent}if red_dot_min != 255:\n')
                    lines.insert(j + 3, f'{indent}    expected_txt += f" and Count <= {{red_dot_min}}"\n')
                    modified_count += 1
                break
            j += 1
        
        # Add red_dot_min to debug_info
        j = i
        while j < min(i + 250, len(lines)):
            if '"debug_info": f"Defects Found:' in lines[j] and 'Red Dot Min Count' not in lines[j]:
                # Add Red Dot Min Count to debug_info
                if 'Contrast: {contrast}' in lines[j]:
                    lines[j] = lines[j].replace(
                        'Contrast: {contrast}',
                        'Red Dot Min Count: {red_dot_min}\\nApply OR: {apply_or}\\nContrast: {contrast}'
                    )
                    modified_count += 1
                break
            j += 1
        
        # Add red_dot_min check in final fail message
        j = i
        while j < min(i + 300, len(lines)):
            if 'if min_square != 255:' in lines[j] and 'limit_txt += f", max W/H' in lines[j + 1]:
                # Find the one in test_top_bottom (before Body Smear test)
                if 'overlay, reason = draw_test_result(' in lines[j + 2]:
                    # This is the fail section - add red_dot_min check
                    indent = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                    lines.insert(j + 2, f'{indent}if red_dot_min != 255:\n')
                    lines.insert(j + 3, f'{indent}    limit_txt += f", max count={{red_dot_min}}"\n')
                    modified_count += 1
                break
            j += 1

# Write back
with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"Modified {modified_count} locations in {filepath}")
