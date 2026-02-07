# Body Smear detection functions
"""
Body Smear Detection - detects white defects on the body surface.
Based on ChipCap old application logic from CCInsp.cpp lines 14980-15400

Reverse Chip Check - detects if chip is accidentally placed upside down (reversed).
Based on ChipCap old application logic from CCInsp.cpp lines 31870-31960
"""

import cv2
import numpy as np
from config.debug_runtime import resolve_debug


def check_body_smear(image, roi, contrast, min_area, min_square=255, use_avg_contrast=True,
                     apply_or=True, offset_top=0, offset_bottom=0,
                     offset_left=0, offset_right=0, debug=False):
    """
    Check for body smear (white defects) on package surface.
    
    Algorithm from old ChipCap:
    1. Create body mask (excluding terminal areas if present)
    2. Calculate average body intensity
    3. Apply threshold: avg + contrast to detect white defects
    4. Find white blobs (smears)
    5. Check if blobs meet minimum area criteria
    
    Args:
        image: Input BGR image
        roi: Package ROI (x, y, w, h)
        contrast: Contrast threshold value (30 typical)
        min_area: Minimum acceptable defect area in pixels (100 typical)
        min_square: Minimum acceptable defect width/height in pixels (aka Min. Sqr Size)
        use_avg_contrast: If True, use adaptive threshold based on body average
        apply_or: If True, fail if ANY enabled threshold is exceeded (area OR size). If False, require ALL enabled thresholds.
        offset_top/bottom/left/right: ROI offsets to exclude edges
        debug: If True, print debug information
    
    Returns:
        dict with:
        - 'defects_found': number of defects
        - 'largest_area': area of largest defect in pixels
        - 'pass': True if no significant defects found
        - 'defect_rects': list of defect bounding boxes
    """
    # CRITICAL: Create independent copy to prevent memory corruption
    image = np.copy(image)
    
    x, y, w, h = roi
    
    # Apply offsets to create inspection ROI
    inspect_x = x + offset_left
    inspect_y = y + offset_top
    inspect_w = w - offset_left - offset_right
    inspect_h = h - offset_top - offset_bottom
    
    if inspect_w <= 0 or inspect_h <= 0:
        if debug:
            print(f"[DEBUG] Body Smear: Invalid inspection ROI after offsets")
        return {'defects_found': 0, 'largest_area': 0, 'pass': True, 'defect_rects': []}
    
    if debug:
        print(f"[DEBUG] Body Smear: Original ROI=({x}, {y}, {w}, {h})")
        print(f"[DEBUG] Body Smear: Inspection ROI=({inspect_x}, {inspect_y}, {inspect_w}, {inspect_h})")
        print(f"[DEBUG] Body Smear: Contrast={contrast}, MinArea={min_area}, MinSquare={min_square}")
        print(f"[DEBUG] Body Smear: UseAvgContrast={use_avg_contrast}, ApplyOR={apply_or}")
    
    # Crop inspection region
    crop = image[inspect_y:inspect_y+inspect_h, inspect_x:inspect_x+inspect_w]
    
    if crop.size == 0:
        if debug:
            print(f"[DEBUG] Body Smear: Empty crop")
        return 0, 0, True, []
    
    # Convert to grayscale if needed
    if len(crop.shape) == 3:
        # Color image
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    else:
        # Already grayscale
        gray = crop
    
    # Calculate threshold
    if use_avg_contrast:
        # Adaptive: body average + contrast
        body_avg = int(np.mean(gray))
        threshold = min(255, max(0, body_avg + contrast))
        if debug:
            print(f"[DEBUG] Body Smear: Body avg={body_avg}, Adaptive threshold={threshold}")
    else:
        # Fixed contrast value
        threshold = min(255, max(0, contrast))
        if debug:
            print(f"[DEBUG] Body Smear: Fixed threshold={threshold}")
    
    # Binarize: detect white (bright) defects
    # Pixels ABOVE threshold are considered defects (white smears)
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    
    if debug:
        white_pct = (np.sum(binary == 255) / binary.size) * 100
        print(f"[DEBUG] Body Smear: Binary white%={white_pct:.1f}")
    
    # Clean up noise with morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Find contours (blobs)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if debug:
        print(f"[DEBUG] Body Smear: Found {len(contours)} contours")
    
    # Analyze defects
    defects = []
    defect_rects = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # Skip very small noise
        if area < 10:
            continue
        
        # Get bounding rectangle
        bx, by, bw, bh = cv2.boundingRect(contour)
        
        # Check if defect meets criteria
        area_fail = (min_area != 255) and (area >= min_area)
        size_fail = False
        if min_square != 255:
            size_fail = (bw >= min_square) or (bh >= min_square)

        if apply_or:
            # OR logic: fail if ANY enabled threshold is exceeded
            is_defect = area_fail or size_fail
        else:
            # AND logic: fail only if ALL enabled thresholds are exceeded
            checks = []
            if min_area != 255:
                checks.append(area_fail)
            if min_square != 255:
                checks.append(size_fail)
            is_defect = all(checks) if checks else False
        
        if is_defect:
            defects.append({
                'area': area,
                'width': bw,
                'height': bh,
                'rect': (inspect_x + bx, inspect_y + by, bw, bh)
            })
            defect_rects.append((inspect_x + bx, inspect_y + by, bw, bh))
    
    # Determine pass/fail
    defects_found = len(defects)
    largest_area = max([d['area'] for d in defects]) if defects else 0
    
    # Pass if no defects found
    is_pass = (defects_found == 0)
    
    if debug:
        print(f"[DEBUG] Body Smear: Defects found={defects_found}, Largest area={largest_area:.0f}")
        print(f"[DEBUG] Body Smear: Result={'PASS' if is_pass else 'FAIL'}")
        if defects:
            print(f"[DEBUG] Body Smear: Defect details:")
            for i, d in enumerate(defects):
                print(f"  [{i}] Area={d['area']:.0f}, Size={d['width']}x{d['height']}, Rect={d['rect']}")
    
    return defects_found, int(largest_area), is_pass, defect_rects


def check_body_stain(image, roi, contrast, min_area, min_square=255, use_avg_contrast=True,
                    apply_or=True, offset_top=0, offset_bottom=0,
                    offset_left=0, offset_right=0, red_dot_min=255, debug=False):
    """
    Check for body stain (black defects) on package surface.
    
    Algorithm from old ChipCap:
    1. Create body mask (excluding terminal areas if present)
    2. Calculate average body intensity
    3. Apply threshold: avg - contrast to detect black defects (INVERTED from Body Smear)
    4. Find black blobs (stains)
    5. Check if blobs meet minimum area criteria
    6. Check defect count against red_dot_min threshold
    
    Args:
        image: Input BGR image
        roi: Package ROI (x, y, w, h)
        contrast: Contrast threshold value (30 typical) - inverted direction from Body Smear
        min_area: Minimum acceptable defect area in pixels (100 typical)
        min_square: Minimum acceptable defect width/height in pixels (aka Min. Sqr Size)
        use_avg_contrast: If True, use adaptive threshold based on body average
        apply_or: If True, fail if ANY enabled threshold is exceeded (area OR size). If False, require ALL enabled thresholds.
        offset_top/bottom/left/right: ROI offsets to exclude edges
        red_dot_min: Maximum acceptable number of defects (255 = disabled)
        debug: If True, print debug information
    
    Returns:
        tuple: (defects_found, largest_area, is_pass, defect_rects)
            - defects_found: number of black stains detected
            - largest_area: area of largest defect in pixels
            - is_pass: True if no significant stains found and defect count within limit
            - defect_rects: list of defect bounding boxes
    """
    # CRITICAL: Create independent copy to prevent memory corruption
    image = np.copy(image)
    
    x, y, w, h = roi
    
    # Apply offsets to create inspection ROI
    inspect_x = x + offset_left
    inspect_y = y + offset_top
    inspect_w = w - offset_left - offset_right
    inspect_h = h - offset_top - offset_bottom
    
    if inspect_w <= 0 or inspect_h <= 0:
        if debug:
            print(f"[DEBUG] Body Stain: Invalid inspection ROI after offsets")
        return 0, 0, True, []
    
    if debug:
        print(f"[DEBUG] Body Stain: Original ROI=({x}, {y}, {w}, {h})")
        print(f"[DEBUG] Body Stain: Inspection ROI=({inspect_x}, {inspect_y}, {inspect_w}, {inspect_h})")
        print(f"[DEBUG] Body Stain: Contrast={contrast}, MinArea={min_area}, MinSquare={min_square}")
        print(f"[DEBUG] Body Stain: UseAvgContrast={use_avg_contrast}, ApplyOR={apply_or}")
    
    # Crop inspection region
    crop = image[inspect_y:inspect_y+inspect_h, inspect_x:inspect_x+inspect_w]
    
    if crop.size == 0:
        if debug:
            print(f"[DEBUG] Body Stain: Empty crop")
        return 0, 0, True, []
    
    # Convert to grayscale if needed
    if len(crop.shape) == 3:
        # Color image
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    else:
        # Already grayscale
        gray = crop
    
    # Calculate threshold
    if use_avg_contrast:
        # Adaptive: body average - contrast (INVERTED from Body Smear)
        body_avg = int(np.mean(gray))
        threshold = min(255, max(0, body_avg - contrast))
        if debug:
            print(f"[DEBUG] Body Stain: Body avg={body_avg}, Adaptive threshold={threshold}")
    else:
        # Fixed contrast value
        threshold = min(255, max(0, contrast))
        if debug:
            print(f"[DEBUG] Body Stain: Fixed threshold={threshold}")
    
    # Binarize: detect black (dark) defects
    # Pixels BELOW threshold are considered defects (black stains)
    # Use THRESH_BINARY_INV to invert the result
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    
    if debug:
        black_pct = (np.sum(binary == 255) / binary.size) * 100
        print(f"[DEBUG] Body Stain: Binary black%={black_pct:.1f}")
    
    # Clean up noise with morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Find contours (blobs)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if debug:
        print(f"[DEBUG] Body Stain: Found {len(contours)} contours")
    
    # Analyze defects
    defects = []
    defect_rects = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # Skip very small noise
        if area < 10:
            continue
        
        # Get bounding rectangle
        bx, by, bw, bh = cv2.boundingRect(contour)
        
        # Check if defect meets criteria
        area_fail = (min_area != 255) and (area >= min_area)
        size_fail = False
        if min_square != 255:
            size_fail = (bw >= min_square) or (bh >= min_square)

        if apply_or:
            # OR logic: fail if ANY enabled threshold is exceeded
            is_defect = area_fail or size_fail
        else:
            # AND logic: fail only if ALL enabled thresholds are exceeded
            checks = []
            if min_area != 255:
                checks.append(area_fail)
            if min_square != 255:
                checks.append(size_fail)
            is_defect = all(checks) if checks else False
        
        if is_defect:
            defects.append({
                'area': area,
                'width': bw,
                'height': bh,
                'rect': (inspect_x + bx, inspect_y + by, bw, bh)
            })
            defect_rects.append((inspect_x + bx, inspect_y + by, bw, bh))
    
    # Determine pass/fail
    defects_found = len(defects)
    largest_area = max([d['area'] for d in defects]) if defects else 0
    
    # Pass if no defects found
    is_pass = (defects_found == 0)
    
    # Check red dot min count (defect count threshold)
    if red_dot_min != 255 and defects_found > red_dot_min:
        is_pass = False
        if debug:
            print(f"[DEBUG] Body Stain: Red Dot Min check FAILED - found {defects_found} defects, max allowed {red_dot_min}")
    
    if debug:
        print(f"[DEBUG] Body Stain: Defects found={defects_found}, Largest area={largest_area:.0f}")
        if red_dot_min != 255:
            print(f"[DEBUG] Body Stain: Red Dot Min check={red_dot_min}, Defect count check={'PASS' if defects_found <= red_dot_min else 'FAIL'}")
        print(f"[DEBUG] Body Stain: Result={'PASS' if is_pass else 'FAIL'}")
        if defects:
            print(f"[DEBUG] Body Stain: Defect details:")
            for i, d in enumerate(defects):
                print(f"  [{i}] Area={d['area']:.0f}, Size={d['width']}x{d['height']}, Rect={d['rect']}")
    
    return defects_found, int(largest_area), is_pass, defect_rects


def check_reverse_chip(image, roi, teach_intensity, contrast_diff, debug=False):
    debug = resolve_debug(debug)
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


def check_body_stand_stain(image, roi, edge_contrast, difference, 
                          offset_top=0, offset_bottom=0,
                          offset_left=0, offset_right=0, debug=False):
    debug = resolve_debug(debug)
    """
    Check for body stand stain (thin stain line at package sealing edge).
    
    Algorithm from old ChipCap:
    1. Extract top and bottom edge regions with specified offsets
    2. Calculate edge intensity at top and bottom
    3. Compare intensity difference
    4. If difference exceeds threshold, stain is detected
    
    Args:
        image: Input BGR image
        roi: Package ROI (x, y, w, h)
        edge_contrast: Edge contrast threshold for binarization
        difference: Maximum acceptable intensity difference between top and bottom
        offset_top/bottom/left/right: ROI offsets to exclude edges
        debug: If True, print debug information
    
    Returns:
        tuple: (top_intensity, bottom_intensity, is_pass)
            - top_intensity: Measured intensity at top edge
            - bottom_intensity: Measured intensity at bottom edge
            - is_pass: True if stain not detected (difference within threshold)
    """
    # CRITICAL: Create independent copy to prevent memory corruption
    image = np.copy(image)
    
    x, y, w, h = roi
    
    # Apply offsets to create inspection ROI
    inspect_x = x + offset_left
    inspect_y = y + offset_top
    inspect_w = w - offset_left - offset_right
    inspect_h = h - offset_top - offset_bottom
    
    if inspect_w <= 0 or inspect_h <= 0:
        if debug:
            print(f"[DEBUG] Body Stand Stain: Invalid inspection ROI after offsets")
        return 0, 0, True
    
    if debug:
        print(f"[DEBUG] Body Stand Stain: Original ROI=({x}, {y}, {w}, {h})")
        print(f"[DEBUG] Body Stand Stain: Inspection ROI=({inspect_x}, {inspect_y}, {inspect_w}, {inspect_h})")
        print(f"[DEBUG] Body Stand Stain: Edge Contrast={edge_contrast}, Difference Threshold={difference}")
    
    # Crop inspection region
    crop = image[inspect_y:inspect_y+inspect_h, inspect_x:inspect_x+inspect_w]
    
    if crop.size == 0:
        if debug:
            print(f"[DEBUG] Body Stand Stain: Empty crop")
        return 0, 0, True
    
    # Convert to grayscale if needed
    if len(crop.shape) == 3:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    else:
        gray = crop
    
    # Extract top edge region (scan top rows for edge detection)
    # Typically top 10-20% of height
    top_region_height = max(1, inspect_h // 10)
    top_region = gray[:top_region_height, :]
    
    # Extract bottom edge region
    bottom_region = gray[-top_region_height:, :]
    
    # Calculate intensities from edge regions
    top_intensity = int(np.mean(top_region))
    bottom_intensity = int(np.mean(bottom_region))
    
    if debug:
        print(f"[DEBUG] Body Stand Stain: Top Intensity={top_intensity}")
        print(f"[DEBUG] Body Stand Stain: Bottom Intensity={bottom_intensity}")
    
    # Check if intensity difference exceeds threshold
    intensity_diff = abs(top_intensity - bottom_intensity)
    is_pass = intensity_diff <= difference
    
    if debug:
        print(f"[DEBUG] Body Stand Stain: Intensity Difference={intensity_diff}, Threshold={difference}")
        print(f"[DEBUG] Body Stand Stain: Result={'PASS' if is_pass else 'FAIL'}")
    
    return top_intensity, bottom_intensity, is_pass
