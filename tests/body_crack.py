# Body Crack detection functions
"""
Body Crack Detection - detects white cracks and defects on the body surface.
Based on ChipCap old application logic (CCInsp.cpp crack detection algorithms).

Algorithm Overview:
1. Extract body region with offset constraints
2. Normalize intensity across the region
3. Apply contrast-based binarization to find white pixels
4. Use edge detection (TB/LR directional analysis) to find crack structures
5. Apply morphological operations to connect broken segments
6. Filter candidates by:
   - Minimum length requirement
   - Minimum elongation (length/width ratio)
   - Broken connection tolerance
7. Verify defects don't touch boundaries (edge validation)
"""

import cv2
import numpy as np
from config.debug_runtime import resolve_debug


def check_body_crack(image, roi, contrast, min_length, min_elongation, broken_connection=0,
                     offset_top=0, offset_bottom=0, offset_left=0, offset_right=0,
                     detect_low_high=False, debug=False):
    """
    Check for body cracks (white cracks/breaks) on package surface.
    
    Uses edge detection and connected component analysis to find linear crack structures.
    
    Algorithm from old ChipCap:
    1. Extract body region with specified offsets
    2. Calculate average body intensity
    3. Apply threshold: avg + contrast to detect white pixels
    4. Use Top-Bottom and Left-Right edge detection
    5. Combine edge results via dilation/morphological operations
    6. Find connected components (cracks)
    7. Filter by minimum length, elongation, and edge touch constraints
    
    Args:
        image: Input BGR image
        roi: Package ROI (x, y, w, h)
        contrast: Contrast threshold for crack detection (30-80 typical)
        min_length: Minimum acceptable crack length in pixels (20-25 typical)
        min_elongation: Minimum length/width ratio (5 typical - must be slender)
        broken_connection: Maximum allowed gap in crack structure (pixels, 0=no gaps)
        offset_top/bottom/left/right: ROI offsets to exclude edges
        debug: If True, print debug information
    
    Returns:
        tuple: (defects_found, largest_length, is_pass, defect_rects)
            - defects_found: number of cracks detected
            - largest_length: length of longest crack in pixels
            - is_pass: True if no significant cracks found
            - defect_rects: list of crack bounding boxes
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
            print(f"[DEBUG] Body Crack: Invalid inspection ROI after offsets")
        return 0, 0, True, []
    
    if debug:
        print(f"[DEBUG] Body Crack: Original ROI=({x}, {y}, {w}, {h})")
        print(f"[DEBUG] Body Crack: Inspection ROI=({inspect_x}, {inspect_y}, {inspect_w}, {inspect_h})")
        print(f"[DEBUG] Body Crack: Contrast={contrast}, MinLength={min_length}, MinElongation={min_elongation}")
    
    # Crop inspection region
    crop = image[inspect_y:inspect_y+inspect_h, inspect_x:inspect_x+inspect_w]
    
    if crop.size == 0:
        if debug:
            print(f"[DEBUG] Body Crack: Empty crop")
        return 0, 0, True, []
    
    # Convert to grayscale if needed
    if len(crop.shape) == 3:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    else:
        gray = crop
    
    # Calculate average intensity to normalize for contrast detection
    body_avg = int(np.mean(gray))
    
    # Thresholds for white (high) and black (low) defects
    white_th = min(255, max(0, body_avg + contrast))
    black_th = min(255, max(0, body_avg - contrast))

    if debug:
        print(f"[DEBUG] Body Crack: Body avg={body_avg}, ThHigh={white_th}, ThLow={black_th}, LowHigh={'ON' if detect_low_high else 'OFF'}")
    
    # ============================================
    # Edge Detection: Combine TB (vertical) and LR (horizontal) analysis
    # ============================================
    
    # 1. VERTICAL EDGE DETECTION (Top-Bottom)
    tb_high = _detect_tb_edges(gray, white_th, mode="white", debug=debug)
    lr_high = _detect_lr_edges(gray, white_th, mode="white", debug=debug)

    edge_combined = cv2.add(tb_high, lr_high)

    if detect_low_high:
        tb_low = _detect_tb_edges(gray, black_th, mode="black", debug=debug)
        lr_low = _detect_lr_edges(gray, black_th, mode="black", debug=debug)
        edge_combined = cv2.add(edge_combined, cv2.add(tb_low, lr_low))

    edge_combined = cv2.threshold(edge_combined, 127, 255, cv2.THRESH_BINARY)[1]
    
    if debug:
        white_pct = (np.sum(edge_combined == 255) / edge_combined.size) * 100
        print(f"[DEBUG] Body Crack: Combined edge white%={white_pct:.1f}")
    
    # ============================================
    # Morphological Operations: Connect and clean
    # ============================================
    
    # Dilation to connect broken crack segments
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated = cv2.dilate(edge_combined, kernel, iterations=2)

    # Additional gap-bridging based on broken_connection (pixels)
    if broken_connection and broken_connection > 0:
        k = max(3, int(broken_connection))
        if k % 2 == 0:
            k += 1
        gap_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        dilated = cv2.dilate(dilated, gap_kernel, iterations=1)
    
    # Closing to fill small holes
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel_close, iterations=1)
    
    # ============================================
    # Find Connected Components (Cracks)
    # ============================================
    
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if debug:
        print(f"[DEBUG] Body Crack: Found {len(contours)} contours")
    
    # Analyze defects
    defects = []
    defect_rects = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # Skip very small noise
        if area < 10:
            continue
        
        # Get bounding rectangle for size analysis
        bx, by, bw, bh = cv2.boundingRect(contour)
        
        # Calculate crack properties
        crack_length = max(bw, bh)  # Longest dimension
        crack_width = min(bw, bh)   # Shortest dimension
        
        # Elongation = length/width ratio (must be > min_elongation to be a crack)
        elongation = crack_length / max(crack_width, 1.0)
        
        # Check if meets minimum requirements
        length_ok = crack_length >= min_length
        elongation_ok = elongation >= min_elongation
        
        # Edge touch validation: check if crack touches image boundary
        # If crack touches edge, it's likely a scanning artifact, not a true defect
        touches_edge = (bx == 0 or (bx + bw) >= inspect_w or
                       by == 0 or (by + bh) >= inspect_h)
        
        is_valid_crack = length_ok and elongation_ok and not touches_edge
        
        if is_valid_crack:
            defects.append({
                'length': crack_length,
                'width': crack_width,
                'elongation': elongation,
                'area': area,
                'rect': (inspect_x + bx, inspect_y + by, bw, bh)
            })
            defect_rects.append((inspect_x + bx, inspect_y + by, bw, bh))
            
            if debug:
                print(f"[DEBUG] Body Crack: Crack found - Length={crack_length}, Width={crack_width}, "
                      f"Elongation={elongation:.2f}, Area={area:.0f}, Rect={(bx, by, bw, bh)}")
    
    # Determine pass/fail
    defects_found = len(defects)
    largest_length = max([d['length'] for d in defects]) if defects else 0
    
    # Pass if no defects found
    is_pass = (defects_found == 0)
    
    if debug:
        print(f"[DEBUG] Body Crack: Defects found={defects_found}, Largest length={largest_length:.0f}")
        print(f"[DEBUG] Body Crack: Result={'PASS' if is_pass else 'FAIL'}")
    
    return defects_found, int(largest_length), is_pass, defect_rects


def _detect_tb_edges(gray, threshold, mode="white", debug=False):
    debug = resolve_debug(debug)
    """
    Detect Top-Bottom edges (vertical intensity changes).
    These help find horizontal cracks.
    
    Algorithm:
    1. Binarize above threshold (white pixels)
    2. Extract top region (rows 0 to height/3)
    3. Extract bottom region (rows 2*height/3 to height)
    4. Detect edges at region boundaries
    5. Return binary image of detected edges
    
    Args:
        gray: Grayscale image
        threshold: Intensity threshold
        debug: Print debug info
    
    Returns:
        Binary image with TB edges marked
    """
    # Binarize with polarity
    thresh_type = cv2.THRESH_BINARY if mode == "white" else cv2.THRESH_BINARY_INV
    _, binary = cv2.threshold(gray, threshold, 255, thresh_type)
    
    if debug:
        white_pct = (np.sum(binary == 255) / binary.size) * 100
        print(f"[DEBUG] TB Edge: Binary white%={white_pct:.1f}")
    
    # Split into regions
    h = gray.shape[0]
    top_region = gray[:h//3, :]
    bottom_region = gray[2*h//3:, :]
    
    # Detect edges in each region using Sobel
    top_edges = cv2.Sobel(top_region, cv2.CV_8U, 0, 1, ksize=3)
    bottom_edges = cv2.Sobel(bottom_region, cv2.CV_8U, 0, 1, ksize=3)
    
    # Threshold edges
    _, top_binary = cv2.threshold(top_edges, 50, 255, cv2.THRESH_BINARY)
    _, bottom_binary = cv2.threshold(bottom_edges, 50, 255, cv2.THRESH_BINARY)
    
    # Reconstruct full image with detected edges
    tb_result = np.zeros_like(gray)
    tb_result[:h//3, :] = top_binary
    tb_result[2*h//3:, :] = bottom_binary
    
    return tb_result


def _detect_lr_edges(gray, threshold, mode="white", debug=False):
    debug = resolve_debug(debug)
    """
    Detect Left-Right edges (horizontal intensity changes).
    These help find vertical cracks.
    
    Algorithm:
    1. Binarize above threshold (white pixels)
    2. Extract left region (cols 0 to width/3)
    3. Extract right region (cols 2*width/3 to width)
    4. Detect edges at region boundaries
    5. Return binary image of detected edges
    
    Args:
        gray: Grayscale image
        threshold: Intensity threshold
        debug: Print debug info
    
    Returns:
        Binary image with LR edges marked
    """
    # Binarize with polarity
    thresh_type = cv2.THRESH_BINARY if mode == "white" else cv2.THRESH_BINARY_INV
    _, binary = cv2.threshold(gray, threshold, 255, thresh_type)
    
    if debug:
        white_pct = (np.sum(binary == 255) / binary.size) * 100
        print(f"[DEBUG] LR Edge: Binary white%={white_pct:.1f}")
    
    # Split into regions
    w = gray.shape[1]
    left_region = gray[:, :w//3]
    right_region = gray[:, 2*w//3:]
    
    # Detect edges in each region using Sobel
    left_edges = cv2.Sobel(left_region, cv2.CV_8U, 1, 0, ksize=3)
    right_edges = cv2.Sobel(right_region, cv2.CV_8U, 1, 0, ksize=3)
    
    # Threshold edges
    _, left_binary = cv2.threshold(left_edges, 50, 255, cv2.THRESH_BINARY)
    _, right_binary = cv2.threshold(right_edges, 50, 255, cv2.THRESH_BINARY)
    
    # Reconstruct full image with detected edges
    lr_result = np.zeros_like(gray)
    lr_result[:, :w//3] = left_binary
    lr_result[:, 2*w//3:] = right_binary
    
    return lr_result


def check_body_hairline_crack(image, roi, contrast, min_length, noise_filter_size=0,
                              detect_white=True, detect_black=False,
                              offset_top=0, offset_bottom=0, offset_left=0, offset_right=0,
                              debug=False):
    """
    Detect hairline cracks (very thin lines) on the package body.

    Based on old ChipCap hairline crack logic: uses gradient emphasis and polarity-aware
    thresholding to find thin linear defects. Supports white and black hairline modes.

    Args:
        image: Input BGR image
        roi: Package ROI (x, y, w, h)
        contrast: Contrast delta against body average (typical 20-50)
        min_length: Minimum crack length in pixels to consider as defect
        noise_filter_size: Kernel size for noise filtering (0 disables, else NxN open)
        detect_white: Enable detection of bright hairline cracks
        detect_black: Enable detection of dark hairline cracks
        offset_top/bottom/left/right: ROI offsets to ignore edges
        debug: If True, print debug information

    Returns:
        tuple: (defects_found, longest_length, is_pass, defect_rects)
    """
    image = np.copy(image)

    x, y, w, h = roi
    inspect_x = x + offset_left
    inspect_y = y + offset_top
    inspect_w = w - offset_left - offset_right
    inspect_h = h - offset_top - offset_bottom

    if inspect_w <= 0 or inspect_h <= 0:
        if debug:
            print("[DEBUG] Hairline: invalid ROI after offsets")
        return 0, 0, True, []

    crop = image[inspect_y:inspect_y+inspect_h, inspect_x:inspect_x+inspect_w]
    if crop.size == 0:
        if debug:
            print("[DEBUG] Hairline: empty crop")
        return 0, 0, True, []

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
    body_avg = int(np.mean(gray))

    white_th = min(255, max(0, body_avg + contrast))
    black_th = min(255, max(0, body_avg - contrast))

    # Gradient magnitude to emphasize thin lines
    grad_x = cv2.Sobel(gray, cv2.CV_16S, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_16S, 0, 1, ksize=3)
    grad_mag = cv2.convertScaleAbs(cv2.absdiff(grad_x, grad_y))

    masks = []
    if detect_white:
        _, bw = cv2.threshold(gray, white_th, 255, cv2.THRESH_BINARY)
        masks.append(bw)
    if detect_black:
        _, bb = cv2.threshold(gray, black_th, 255, cv2.THRESH_BINARY_INV)
        masks.append(bb)

    if not masks:
        if debug:
            print("[DEBUG] Hairline: no polarity enabled")
        return 0, 0, True, []

    polarity_mask = masks[0]
    for m in masks[1:]:
        polarity_mask = cv2.bitwise_or(polarity_mask, m)

    # Focus gradient to candidate pixels only
    candidate = cv2.bitwise_and(grad_mag, grad_mag, mask=polarity_mask)

    # Noise filtering
    if noise_filter_size and noise_filter_size > 1:
        k = max(3, int(noise_filter_size))
        if k % 2 == 0:
            k += 1
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
        candidate = cv2.morphologyEx(candidate, cv2.MORPH_OPEN, kernel, iterations=1)

    # Thin structure emphasis
    _, binary = cv2.threshold(candidate, 30, 255, cv2.THRESH_BINARY)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=1)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    defects = []
    defect_rects = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 5:
            continue

        bx, by, bw, bh = cv2.boundingRect(contour)
        crack_length = max(bw, bh)

        if crack_length < min_length:
            continue

        touches_edge = (bx == 0 or (bx + bw) >= inspect_w or by == 0 or (by + bh) >= inspect_h)
        if touches_edge:
            continue

        defects.append({
            "length": crack_length,
            "area": area,
            "rect": (inspect_x + bx, inspect_y + by, bw, bh)
        })
        defect_rects.append((inspect_x + bx, inspect_y + by, bw, bh))

    defects_found = len(defects)
    longest_length = max([d["length"] for d in defects]) if defects else 0
    is_pass = defects_found == 0

    if debug:
        pol = []
        if detect_white:
            pol.append("white")
        if detect_black:
            pol.append("black")
        print(f"[DEBUG] Hairline: body_avg={body_avg}, th_w={white_th}, th_b={black_th}, polarity={'+'.join(pol)}")
        print(f"[DEBUG] Hairline: contours={len(contours)}, defects={defects_found}, longest={longest_length}")

    return defects_found, int(longest_length), is_pass, defect_rects


def check_edge_chipoff(image, roi, 
                       contrast_black_top=20, contrast_black_bot=20,
                       contrast_white_top=25, contrast_white_bot=25,
                       min_area=50, min_square=5,
                       edge_width_top=10, edge_width_bot=10,
                       insp_offset_top=5, insp_offset_bot=5,
                       corner_mask_left=5, corner_mask_right=5,
                       ignore_reflection=False, ignore_vertical_line=False,
                       enable_high_contrast=False, high_contrast_value=50,
                       debug=False):
    """
    Check for edge chipoff defects on top and bottom body edges.
    
    Inspects the edge of the device to detect broken defects in edge of body surfaces.
    Supports both black and white defect detection with separate contrast thresholds.
    
    Args:
        image: BGR or grayscale image
        roi: package ROI (x, y, w, h)
        contrast_black_top/bot: black defect contrast threshold for top/bottom edges
        contrast_white_top/bot: white defect contrast threshold for top/bottom edges
        min_area: minimum defect area in pixels (fail if >=)
        min_square: minimum defect width/height in pixels (fail if >=)
        edge_width_top/bot: inspection band width in pixels for top/bottom
        insp_offset_top/bot: starting distance from body edge (gap before inspection)
        corner_mask_left/right: corner chamfer pixels (length of detection area from sides)
        ignore_reflection: filter out reflections at package edge
        ignore_vertical_line: filter out vertical lines on body
        enable_high_contrast: enable additional high contrast edge inspection
        high_contrast_value: contrast threshold for high contrast mode
        debug: verbose logging
    
    Returns: (total_defects, largest_area, is_pass, defect_rects)
    """
    x, y, w, h = roi
    
    # Define top and bottom edge inspection regions
    # Top edge: y + insp_offset_top, height = edge_width_top
    top_region = (x, y + insp_offset_top, w, edge_width_top)
    # Bottom edge: y + h - insp_offset_bot - edge_width_bot, height = edge_width_bot
    bot_region = (x, y + h - insp_offset_bot - edge_width_bot, w, edge_width_bot)
    
    regions = [
        ("Top", top_region, contrast_black_top, contrast_white_top),
        ("Bottom", bot_region, contrast_black_bot, contrast_white_bot)
    ]
    
    total_defects = 0
    largest_area = 0
    all_rects = []
    
    for label, region, cb_contrast, cw_contrast in regions:
        rx, ry, rw, rh = region
        
        if rw <= 0 or rh <= 0:
            continue
        
        crop = image[ry:ry+rh, rx:rx+rw]
        if crop.size == 0:
            continue
        
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        
        # Apply corner mask (chamfer left and right corners)
        if corner_mask_left > 0 or corner_mask_right > 0:
            gray = gray.copy()
            mask_left = min(corner_mask_left, rw // 2)
            mask_right = min(corner_mask_right, rw // 2)
            
            # Mask left corner (triangular region)
            if mask_left > 0:
                for i in range(min(mask_left, rh)):
                    gray[i, 0:mask_left-i] = 255
            
            # Mask right corner (triangular region)
            if mask_right > 0:
                for i in range(min(mask_right, rh)):
                    gray[i, rw-mask_right+i:rw] = 255
        
        # Detect black defects (darker than average - cb_contrast)
        black_defects, black_largest, black_rects = _detect_edge_defects(
            gray, cb_contrast, min_area, min_square, polarity='black', 
            ignore_reflection=ignore_reflection, ignore_vertical_line=ignore_vertical_line,
            debug=debug
        )
        
        # Detect white defects (brighter than average + cw_contrast)
        white_defects, white_largest, white_rects = _detect_edge_defects(
            gray, cw_contrast, min_area, min_square, polarity='white',
            ignore_reflection=ignore_reflection, ignore_vertical_line=ignore_vertical_line,
            debug=debug
        )
        
        # High contrast additional inspection
        if enable_high_contrast and high_contrast_value > 0:
            hc_defects, hc_largest, hc_rects = _detect_edge_defects(
                gray, high_contrast_value, min_area, min_square, polarity='black',
                ignore_reflection=ignore_reflection, ignore_vertical_line=ignore_vertical_line,
                debug=debug
            )
            black_defects += hc_defects
            black_largest = max(black_largest, hc_largest)
            black_rects.extend(hc_rects)
        
        # Combine defects
        region_defects = black_defects + white_defects
        region_largest = max(black_largest, white_largest)
        region_rects = black_rects + white_rects
        
        # Offset rects to image coordinates
        region_rects = [(rx + dx, ry + dy, dw, dh) for (dx, dy, dw, dh) in region_rects]
        
        total_defects += region_defects
        largest_area = max(largest_area, region_largest)
        all_rects.extend(region_rects)
        
        if debug:
            print(f"[DEBUG] Edge Chipoff {label}: black={black_defects}, white={white_defects}, largest={region_largest}, ROI=({rx},{ry},{rw},{rh})")
    
    is_pass = (total_defects == 0)
    return total_defects, int(largest_area), is_pass, all_rects


def _detect_edge_defects(gray, contrast, min_area, min_square, polarity='black',
                         ignore_reflection=False, ignore_vertical_line=False, debug=False):
    """
    Detect edge defects (black or white) using contrast thresholding.
    
    Args:
        gray: grayscale image
        contrast: contrast threshold
        min_area/min_square: size thresholds
        polarity: 'black' or 'white'
        ignore_reflection: filter reflections (horizontal bright lines)
        ignore_vertical_line: filter vertical lines
    
    Returns: (defect_count, largest_area, rects)
    """
    if gray.size == 0:
        return 0, 0, []
    
    avg = int(np.mean(gray))
    
    if polarity == 'black':
        # Black defects: darker than avg - contrast
        threshold = max(0, avg - int(contrast))
        _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    else:
        # White defects: brighter than avg + contrast
        threshold = min(255, avg + int(contrast))
        _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    
    # Clean noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    # Ignore reflection: remove horizontal lines (high aspect ratio)
    if ignore_reflection:
        binary = _filter_horizontal_reflections(binary)
    
    # Ignore vertical line: remove vertical structures
    if ignore_vertical_line:
        binary = _filter_vertical_lines(binary)
    
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    defects = []
    rects = []
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 5:  # Minimum noise threshold
            continue
        
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Check thresholds
        area_fail = (min_area != 255) and (area >= int(min_area))
        size_fail = False
        if min_square != 255:
            size_fail = (w >= int(min_square)) or (h >= int(min_square))
        
        # OR logic: fail if either condition is met
        if area_fail or size_fail:
            defects.append({'area': area, 'rect': (x, y, w, h)})
            rects.append((x, y, w, h))
    
    count = len(defects)
    largest = int(max([d['area'] for d in defects]) if defects else 0)
    
    return count, largest, rects


def _filter_horizontal_reflections(binary):
    """
    Filter out horizontal reflection lines (high width/height ratio).
    Reflections typically appear as thin horizontal bright lines at edges.
    """
    contours, _ = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if h > 0:
            aspect_ratio = w / h
            # If very wide and thin (aspect > 10), likely a reflection
            if aspect_ratio > 10 and h < 5:
                cv2.drawContours(binary, [cnt], -1, 0, -1)
    
    return binary


def _filter_vertical_lines(binary):
    """
    Filter out vertical lines on body (high height/width ratio).
    Some packages have vertical surface features that should be ignored.
    """
    contours, _ = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 0:
            aspect_ratio = h / w
            # If very tall and thin (aspect > 10), likely a vertical line
            if aspect_ratio > 10 and w < 5:
                cv2.drawContours(binary, [cnt], -1, 0, -1)
    
    return binary


def draw_edge_chipoff_bands(image, roi, 
                            edge_width_top=10, edge_width_bot=10,
                            insp_offset_top=5, insp_offset_bot=5,
                            corner_mask_left=5, corner_mask_right=5,
                            color=(0, 255, 0), thickness=2):
    """
    Draw edge chipoff inspection bands for visualization in step mode.
    
    Args:
        image: image to draw on (modified in-place)
        roi: package ROI (x,y,w,h)
        edge_width_top/bot: inspection band heights
        insp_offset_top/bot: offset from body edge
        corner_mask_left/right: corner chamfer sizes
        color: BGR color (default green)
        thickness: line thickness
    
    Returns: modified image
    """
    x, y, w, h = roi
    
    # Top edge band
    top_y = y + insp_offset_top
    top_h = edge_width_top
    if top_h > 0:
        # Main rectangle
        cv2.rectangle(image, (x, top_y), (x + w, top_y + top_h), color, thickness)
        
        # Draw corner mask regions (triangular chamfer)
        if corner_mask_left > 0:
            pts_left = np.array([
                [x, top_y],
                [x + corner_mask_left, top_y],
                [x, top_y + min(corner_mask_left, top_h)]
            ], np.int32)
            cv2.polylines(image, [pts_left], True, (255, 0, 0), thickness)
        
        if corner_mask_right > 0:
            pts_right = np.array([
                [x + w, top_y],
                [x + w - corner_mask_right, top_y],
                [x + w, top_y + min(corner_mask_right, top_h)]
            ], np.int32)
            cv2.polylines(image, [pts_right], True, (255, 0, 0), thickness)
        
        cv2.putText(image, "Top", (x + w // 2 - 15, top_y + top_h // 2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # Bottom edge band
    bot_y = y + h - insp_offset_bot - edge_width_bot
    bot_h = edge_width_bot
    if bot_h > 0:
        # Main rectangle
        cv2.rectangle(image, (x, bot_y), (x + w, bot_y + bot_h), color, thickness)
        
        # Draw corner mask regions
        if corner_mask_left > 0:
            pts_left = np.array([
                [x, bot_y + bot_h],
                [x + corner_mask_left, bot_y + bot_h],
                [x, bot_y + bot_h - min(corner_mask_left, bot_h)]
            ], np.int32)
            cv2.polylines(image, [pts_left], True, (255, 0, 0), thickness)
        
        if corner_mask_right > 0:
            pts_right = np.array([
                [x + w, bot_y + bot_h],
                [x + w - corner_mask_right, bot_y + bot_h],
                [x + w, bot_y + bot_h - min(corner_mask_right, bot_h)]
            ], np.int32)
            cv2.polylines(image, [pts_right], True, (255, 0, 0), thickness)
        
        cv2.putText(image, "Bottom", (x + w // 2 - 25, bot_y + bot_h // 2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    return image
