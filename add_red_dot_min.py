#!/usr/bin/env python3
"""Script to add red_dot_min parameter to Body Stain tests"""

import re

def update_test_top_bottom():
    """Update Body Stain section in test_top_bottom function"""
    filepath = r"e:\Office Work\chip-chap-python\tests\test_top_bottom.py"
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Count occurrences to find test_top_bottom section
    terminal_length_count = content.count("Terminal Length Diff exceeds tolerance")
    print(f"Found {terminal_length_count} occurrences of 'Terminal Length Diff exceeds tolerance'")
    
    # Split by this marker - first occurrence is in test_top_bottom, second in test_feed
    parts = content.split("Terminal Length Diff exceeds tolerance")
    print(f"Split into {len(parts)} parts")
    
    if len(parts) < 3:
        print("ERROR: Could not find correct split point")
        return
    
    # Process the first section (test_top_bottom)
    section1 = parts[0] + "Terminal Length Diff exceeds tolerance" + parts[1]
    
    # Find Body Stain section in first part and add red_dot_min parameter
    # Pattern: "offset_right = int(body_stain_tab.get..." followed by check for config
    pattern1 = r'(offset_right = int\(body_stain_tab\.get\(f"bs\{stain_num\}_off_right", 5\)\))\n(\s+# Check if parameters are configured)'
    replacement1 = r'\1\n            red_dot_min = int(body_stain_tab.get(f"bs{stain_num}_red_dot_min", 255))\n\2'
    section1 = re.sub(pattern1, replacement1, section1)
    
    # Add red_dot_min to function call
    pattern2 = r'(offset_right=offset_right,)\n(\s+debug=True)\n(\s+\))'
    # Only match in test_top_bottom section (before "check_body_smear_1")
    if "check_body_smear_1" in section1:
        # Find the first occurrence in test_top_bottom
        idx = section1.find("check_body_stain")
        if idx > 0:
            before_smear = section1[:idx]
            # Replace only in this section
            pattern2_match = r'(offset_right=offset_right,)\n(\s+debug=True)\n(\s+\))'
            section1_updated = re.sub(
                pattern2_match,
                r'\1\n\2\n                red_dot_min=red_dot_min,\n\2\n\3',
                before_smear,
                count=1
            ) + section1[idx:]
            section1 = section1_updated
    
    # Reconstruct content
    new_content = section1 + "Terminal Length Diff exceeds tolerance" + parts[2]
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print("Updated test_top_bottom.py")

if __name__ == "__main__":
    update_test_top_bottom()
