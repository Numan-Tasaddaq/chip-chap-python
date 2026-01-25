# Body Smear detection functions
"""
Body Smear Detection - detects white defects on the body surface.
Based on ChipCap old application logic from CCInsp.cpp lines 14980-15400
"""

import cv2
import numpy as np


def check_body_smear(image, roi, contrast, min_area, use_avg_contrast=True, 
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
        use_avg_contrast: If True, use adaptive threshold based on body average
        apply_or: If True, use OR logic for size checks (more lenient)
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
        print(f"[DEBUG] Body Smear: Contrast={contrast}, MinArea={min_area}")
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
        is_defect = False
        
        if apply_or:
            # OR logic: area OR size exceeds threshold (more lenient)
            if area >= min_area:
                is_defect = True
        else:
            # AND logic: area AND size must exceed threshold (stricter)
            if area >= min_area:
                is_defect = True
        
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
