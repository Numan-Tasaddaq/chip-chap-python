# Reverse Chip Check
"""
Reverse Chip Check - detects if chip is accidentally placed upside down (reversed).
Based on ChipCap old application logic from CCInsp.cpp lines 31870-31960
"""

import cv2
import numpy as np


def check_reverse_chip(image, roi, teach_intensity, contrast_diff, debug=False):
    """
    Check if chip is reversed (accidentally placed upside down).
    
    Algorithm from old ChipCap:
    1. Extract body ROI with 40px margins on left/right
    2. Calculate histogram of body region
    3. Get average intensity from 70-90th percentile
    4. Compare with taught intensity
    5. If difference exceeds threshold, chip is likely reversed
    
    Args:
        image: Input grayscale or BGR image
        roi: Package ROI (x, y, w, h)
        teach_intensity: Taught body intensity during teaching (recorded from good chip)
        contrast_diff: Maximum acceptable difference in intensity (e.g., 20)
        debug: If True, print debug information
    
    Returns:
        tuple: (measured_intensity, is_reversed, is_pass)
            - measured_intensity: Current body average intensity
            - is_reversed: True if chip appears reversed
            - is_pass: True if check passes (not reversed or within tolerance)
    """
    x, y, w, h = roi
    
    # Apply 40px margin on left and right (from old code)
    margin_lr = 40
    inspect_x = x + margin_lr
    inspect_w = w - (2 * margin_lr)
    
    if inspect_w <= 0:
        if debug:
            print(f"[DEBUG] Reverse Chip: Invalid ROI after margins")
        return 0, False, True
    
    if debug:
        print(f"[DEBUG] Reverse Chip: Original ROI=({x}, {y}, {w}, {h})")
        print(f"[DEBUG] Reverse Chip: Inspection ROI=({inspect_x}, {y}, {inspect_w}, {h})")
        print(f"[DEBUG] Reverse Chip: Teach Intensity={teach_intensity}, Threshold={contrast_diff}")
    
    # Crop inspection region
    crop = image[y:y+h, inspect_x:inspect_x+inspect_w]
    
    if crop.size == 0:
        if debug:
            print(f"[DEBUG] Reverse Chip: Empty crop")
        return 0, False, True
    
    # Convert to grayscale if needed
    if len(crop.shape) == 3:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    else:
        gray = crop
    
    # Calculate histogram
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.flatten()
    
    # Calculate average intensity from 70-90th percentile (from old code)
    # This filters out extreme values (very dark and very bright pixels)
    total_pixels = gray.size
    cumsum = np.cumsum(hist)
    
    # Find 70th and 90th percentile intensity values
    percentile_70 = np.searchsorted(cumsum, total_pixels * 0.70)
    percentile_90 = np.searchsorted(cumsum, total_pixels * 0.90)
    
    # Calculate average intensity in this range
    if percentile_70 < percentile_90:
        # Create mask for pixels in 70-90th percentile range
        mask = (gray >= percentile_70) & (gray <= percentile_90)
        if np.any(mask):
            body_avg = int(np.mean(gray[mask]))
        else:
            body_avg = int(np.mean(gray))
    else:
        body_avg = int(np.mean(gray))
    
    if debug:
        print(f"[DEBUG] Reverse Chip: Measured Intensity={body_avg}")
        print(f"[DEBUG] Reverse Chip: Percentile Range={percentile_70}-{percentile_90}")
    
    # Check if difference exceeds threshold
    intensity_diff = abs(body_avg - teach_intensity)
    is_reversed = intensity_diff > contrast_diff
    is_pass = not is_reversed
    
    if debug:
        print(f"[DEBUG] Reverse Chip: Intensity Diff={intensity_diff}, Threshold={contrast_diff}")
        print(f"[DEBUG] Reverse Chip: Reversed={is_reversed}, Pass={is_pass}")
    
    return body_avg, is_reversed, is_pass
