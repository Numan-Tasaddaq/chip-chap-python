import cv2
import numpy as np
from config.debug_runtime import resolve_debug


def check_terminal_pogo(image, roi, contrast, min_area, min_square=255,
                        offset_top=0, offset_bottom=0, offset_left=0, offset_right=0,
                        apply_or=True, debug=False):
    """
    Detect black defects (pogo) within the terminal region using package ROI offsets.

    Args:
        image: BGR or grayscale image
        roi: package ROI (x, y, w, h)
        contrast: threshold offset (avg - contrast)
        min_area/min_square: defect size limits (fail if >=)
        offset_*: margins to ignore edges of the package ROI
        apply_or: OR/AND logic for area vs size
        debug: verbose logging

    Returns: (defects_found, largest_area, is_pass, defect_rects)
    """
    x, y, w, h = roi
    ix = x + offset_left
    iy = y + offset_top
    iw = w - offset_left - offset_right
    ih = h - offset_top - offset_bottom
    if iw <= 0 or ih <= 0:
        if debug:
            print(f"[DEBUG] Terminal Pogo ROI invalid: ({ix},{iy},{iw},{ih})")
        return 0, 0, True, []

    crop = image[iy:iy+ih, ix:ix+iw]
    if crop.size == 0:
        return 0, 0, True, []

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop

    cnt, largest, rects = _detect_black_defects(gray, contrast, min_area, min_square, apply_or, debug)
    rects = [(ix + rx0, iy + ry0, rw0, rh0) for (rx0, ry0, rw0, rh0) in rects]

    defects_found = cnt
    largest_area = int(largest)
    is_pass = (defects_found == 0)

    if debug:
        print(f"[DEBUG] Terminal Pogo: defects={defects_found}, largest={largest_area}, ROI=({ix},{iy},{iw},{ih}), pass={is_pass}")

    return defects_found, largest_area, is_pass, rects


def check_terminal_oxidation(image, roi, 
                             teach_contrast=128, contrast_difference=20,
                             offset_top=0, offset_bottom=0, offset_left=0, offset_right=0,
                             corner_x=0, corner_y=0,
                             debug=False):
    """
    Detect terminal oxidation by comparing current terminal contrast against taught reference.
    
    Oxidation manifests as color change (darkening) of terminal surface. This check compares
    the measured contrast in the terminal regions against a taught reference value.

    Args:
        image: BGR or grayscale image
        roi: package ROI (x, y, w, h)
        teach_contrast: reference contrast value (taught during teach phase)
        contrast_difference: maximum acceptable difference from taught value
        offset_*: margins to ignore edges of terminal
        corner_x/corner_y: corner chamfer to ignore oxidation-free corners
        debug: verbose logging

    Returns: (measured_contrast, difference, is_pass)
    """
    x, y, w, h = roi
    
    # Define inspection region (full terminal area with offsets)
    ix = x + offset_left
    iy = y + offset_top
    iw = w - offset_left - offset_right
    ih = h - offset_top - offset_bottom
    
    if iw <= 0 or ih <= 0:
        if debug:
            print(f"[DEBUG] Oxidation ROI invalid: ({ix},{iy},{iw},{ih})")
        return teach_contrast, 0, True
    
    crop = image[iy:iy+ih, ix:ix+iw]
    if crop.size == 0:
        return teach_contrast, 0, True
    
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
    
    # Apply corner chamfer to ignore clean corners
    if corner_x > 0 and corner_y > 0:
        chx = min(corner_x, iw)
        chy = min(corner_y, ih)
        gray = gray.copy()
        # Zero out corners
        gray[0:chy, 0:chx] = 255  # TL
        gray[0:chy, iw - chx:iw] = 255  # TR
        gray[ih - chy:ih, 0:chx] = 255  # BL
        gray[ih - chy:ih, iw - chx:iw] = 255  # BR
    
    # Measure average contrast (intensity) in the region
    measured_contrast = int(np.mean(gray))
    difference = abs(measured_contrast - teach_contrast)
    is_pass = (difference <= contrast_difference)
    
    if debug:
        print(f"[DEBUG] Terminal Oxidation: taught={teach_contrast}, measured={measured_contrast}, diff={difference}, threshold={contrast_difference}, pass={is_pass}")
        print(f"[DEBUG] Oxidation ROI: ({ix},{iy},{iw},{ih}), corner_chamfer=({corner_x},{corner_y})")
    
    return measured_contrast, difference, is_pass


# -----------------------------------------------------------------------------
# Terminal Chipoff (Inner / Outer)
# -----------------------------------------------------------------------------

def check_terminal_chipoff_inner(image, roi, contrast, min_area, min_square=255,
                                 inspection_width_x=80, inspection_width_y=40,
                                 corner_ellipse_mask=0,
                                 enable_corner_offset=False, corner_offset_x=0, corner_offset_y=0,
                                 offset_top=0, offset_bottom=0, offset_left=0, offset_right=0,
                                 apply_or=True, 
                                 enable_pocket_edge_filter=False, pocket_roi=None,
                                 debug=False):
    """
    Detect missing material (chip-off) on inner terminal regions (4 corners of terminals).
    
    Inspects 4 terminal corners of the device for terminal defects. Each corner has
    inspection width X & Y that can be adjusted. Supports both corner offset (chamfered)
    and without corner offset (rectangular with margins) modes.

    Args:
        image: BGR or grayscale
        roi: package ROI (x,y,w,h)
        contrast: threshold delta (avg - contrast) for black chip-off
        min_area/min_square: size gates (fail if >=)
        inspection_width_x: width of corner inspection region (auto-limited to terminal length)
        inspection_width_y: height of corner inspection region
        corner_ellipse_mask: ellipse radius for curved corner masking (0=disabled)
        enable_corner_offset: if True, use chamfered corners; if False, use rectangular margins
        corner_offset_x/corner_offset_y: chamfer pixels (when enable_corner_offset=True)
        offset_top/bottom/left/right: rectangular margins (when enable_corner_offset=False)
        apply_or: OR/AND logic for area vs size
        enable_pocket_edge_filter: if True, filter defects touching pocket edges
        pocket_roi: pocket ROI (x,y,w,h) for edge filtering, None = use image edges
        debug: verbose logging
        
    Returns: (defects_found, largest_area, is_pass, defect_rects)
    """
    x, y, w, h = roi
    
    # Auto-adjust inspection_width_x to terminal length if greater
    # Assume terminals are on left/right edges, width ~25% of package
    terminal_width = max(1, int(w * 0.25))
    inspection_width_x = min(inspection_width_x, h)  # Limited to package height
    inspection_width_y = min(inspection_width_y, terminal_width)
    
    # Define 4 corner regions: Top-Left, Top-Right, Bottom-Left, Bottom-Right
    # Each corner is at the terminal edge with inspection_width_x (vertical) and inspection_width_y (horizontal)
    regions = [
        # Top-Left corner
        (x, y, inspection_width_y, inspection_width_x),
        # Top-Right corner  
        (x + w - inspection_width_y, y, inspection_width_y, inspection_width_x),
        # Bottom-Left corner
        (x, y + h - inspection_width_x, inspection_width_y, inspection_width_x),
        # Bottom-Right corner
        (x + w - inspection_width_y, y + h - inspection_width_x, inspection_width_y, inspection_width_x),
    ]
    
    return _inspect_chipoff_corners(
        image, regions, contrast, min_area, min_square,
        corner_ellipse_mask,
        enable_corner_offset, corner_offset_x, corner_offset_y,
        offset_top, offset_bottom, offset_left, offset_right,
        apply_or, enable_pocket_edge_filter, pocket_roi,
        debug, label="Inner"
    )


def check_terminal_chipoff_outer(image, roi, contrast, min_area, min_square=255,
                                 offset_top=0, offset_bottom=0, offset_left=0, offset_right=0,
                                 band_width_ratio=0.25, apply_or=True,
                                 enable_pocket_edge_filter=False, pocket_roi=None,
                                 debug=False):
    """
    Detect missing material (chip-off) on outer terminal regions (left & right bands).

    Args:
        image: BGR or grayscale
        roi: package ROI (x,y,w,h)
        contrast: threshold delta (avg - contrast) for black chip-off
        min_area/min_square: size gates (fail if >=)
        offsets: ignore margins inside each band
        band_width_ratio: fraction of package width for side bands
        apply_or: OR/AND logic for area vs size
        enable_pocket_edge_filter: if True, filter defects touching pocket edges
        pocket_roi: pocket ROI (x,y,w,h) for edge filtering, None = use image edges
        debug: verbose logging
    Returns: (defects_found, largest_area, is_pass, defect_rects)
    """
    x, y, w, h = roi
    band_w = max(1, int(w * band_width_ratio))
    regions = [
        (x, y, band_w, h),
        (x + w - band_w, y, band_w, h),
    ]
    return _inspect_chipoff_regions(image, regions, contrast, min_area, min_square,
                                    offset_top, offset_bottom, offset_left, offset_right,
                                    apply_or, enable_pocket_edge_filter, pocket_roi,
                                    debug, label="Outer")


def _inspect_chipoff_corners(image, regions, contrast, min_area, min_square,
                            corner_ellipse_mask,
                            enable_corner_offset, corner_offset_x, corner_offset_y,
                            offset_top, offset_bottom, offset_left, offset_right,
                            apply_or, enable_pocket_edge_filter, pocket_roi,
                            debug, label="Chipoff"):
    """
    Inspect chipoff defects in corner regions with optional ellipse masking or offset modes.
    
    Args:
        regions: list of corner ROIs [(x,y,w,h), ...]
        corner_ellipse_mask: ellipse radius for curved corner masking (0=disabled)
        enable_corner_offset: if True, use chamfered corners; if False, use rectangular margins
        corner_offset_x/y: chamfer pixels (when enable_corner_offset=True)
        offset_*: rectangular margins (when enable_corner_offset=False)
    """
    image = np.copy(image)
    total_defects = 0
    largest_area = 0
    all_rects = []

    for idx, region in enumerate(regions):
        rx, ry, rw, rh = region
        
        # Apply offsets based on mode
        if enable_corner_offset:
            # Chamfered corner mode - apply corner_offset from edges
            ix = rx + corner_offset_x
            iy = ry + corner_offset_y
            iw = rw - (corner_offset_x * 2)
            ih = rh - (corner_offset_y * 2)
        else:
            # Rectangular margin mode - apply directional offsets
            ix = rx + offset_left
            iy = ry + offset_top
            iw = rw - offset_left - offset_right
            ih = rh - offset_top - offset_bottom
        
        if iw <= 0 or ih <= 0:
            continue
            
        crop = image[iy:iy+ih, ix:ix+iw]
        if crop.size == 0:
            continue
            
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        
        # Apply corner ellipse mask if enabled
        if corner_ellipse_mask > 0:
            mask = np.ones(gray.shape, dtype=np.uint8) * 255
            # Create ellipse mask in center of region
            center_x = iw // 2
            center_y = ih // 2
            axes = (corner_ellipse_mask, corner_ellipse_mask)
            cv2.ellipse(mask, (center_x, center_y), axes, 0, 0, 360, 0, -1)
            # Set non-ellipse region to white (ignore)
            gray = np.where(mask == 0, gray, 255)

        cnt, largest, rects = _detect_black_defects(gray, contrast, min_area, min_square, apply_or, debug)
        
        # Apply pocket edge filter if enabled
        if enable_pocket_edge_filter and pocket_roi:
            rects = _filter_pocket_edge_defects(rects, (ix, iy), pocket_roi, debug)
            cnt = len(rects)
            largest = max([rw0 * rh0 for (_, _, rw0, rh0) in rects]) if rects else 0
        
        # Offset rects to image coordinates
        rects = [(ix + rx0, iy + ry0, rw0, rh0) for (rx0, ry0, rw0, rh0) in rects]

        total_defects += cnt
        largest_area = max(largest_area, largest)
        all_rects.extend(rects)

        if debug:
            corner_names = ["TL", "TR", "BL", "BR"]
            corner_label = corner_names[idx] if idx < 4 else f"C{idx}"
            print(f"[DEBUG] {label} Chipoff {corner_label}: defects={cnt}, largest={largest}, ROI=({ix},{iy},{iw},{ih})")

    is_pass = (total_defects == 0)
    return total_defects, int(largest_area), is_pass, all_rects


def _inspect_chipoff_regions(image, regions, contrast, min_area, min_square,
                             offset_top, offset_bottom, offset_left, offset_right,
                             apply_or, enable_pocket_edge_filter, pocket_roi,
                             debug, label="Chipoff"):
    image = np.copy(image)
    total_defects = 0
    largest_area = 0
    all_rects = []

    for idx, region in enumerate(regions):
        rx, ry, rw, rh = region
        ix = rx + offset_left
        iy = ry + offset_top
        iw = rw - offset_left - offset_right
        ih = rh - offset_top - offset_bottom
        if iw <= 0 or ih <= 0:
            continue
        crop = image[iy:iy+ih, ix:ix+iw]
        if crop.size == 0:
            continue
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop

        cnt, largest, rects = _detect_black_defects(gray, contrast, min_area, min_square, apply_or, debug)
        
        # Apply pocket edge filter if enabled
        if enable_pocket_edge_filter and pocket_roi:
            rects = _filter_pocket_edge_defects(rects, (ix, iy), pocket_roi, debug)
            cnt = len(rects)
            largest = max([rw0 * rh0 for (_, _, rw0, rh0) in rects]) if rects else 0
        
        # Offset rects to image coordinates
        rects = [(ix + rx0, iy + ry0, rw0, rh0) for (rx0, ry0, rw0, rh0) in rects]

        total_defects += cnt
        largest_area = max(largest_area, largest)
        all_rects.extend(rects)

        if debug:
            print(f"[DEBUG] {label} Chipoff region {idx}: defects={cnt}, largest={largest}, ROI=({ix},{iy},{iw},{ih})")

    is_pass = (total_defects == 0)
    return total_defects, int(largest_area), is_pass, all_rects


def _filter_pocket_edge_defects(rects, crop_offset, pocket_roi, debug=False):
    debug = resolve_debug(debug)
    """
    Filter out defects that touch the pocket edge.
    
    Defects touching the pocket boundaries are often false positives from
    pocket edge artifacts and should be ignored.
    
    Args:
        rects: list of defect rectangles in crop coordinates [(x,y,w,h), ...]
        crop_offset: (crop_x, crop_y) offset of crop in image coordinates
        pocket_roi: pocket ROI (px, py, pw, ph) in image coordinates
        debug: verbose logging
    
    Returns: filtered list of rectangles (still in crop coordinates)
    """
    if not pocket_roi or not rects:
        return rects
    
    px, py, pw, ph = pocket_roi
    crop_x, crop_y = crop_offset
    
    filtered = []
    for (rx, ry, rw, rh) in rects:
        # Convert rect to image coordinates
        img_x = crop_x + rx
        img_y = crop_y + ry
        
        # Check if defect touches any pocket edge (with 2px tolerance)
        edge_tolerance = 2
        touches_left = (img_x <= px + edge_tolerance)
        touches_right = (img_x + rw >= px + pw - edge_tolerance)
        touches_top = (img_y <= py + edge_tolerance)
        touches_bottom = (img_y + rh >= py + ph - edge_tolerance)
        
        touches_edge = touches_left or touches_right or touches_top or touches_bottom
        
        if not touches_edge:
            filtered.append((rx, ry, rw, rh))
        elif debug:
            print(f"[DEBUG] Filtered pocket edge defect at ({img_x},{img_y},{rw},{rh})")
    
    return filtered


def _detect_black_defects(gray, contrast, min_area, min_square, apply_or=True, debug=False):
    debug = resolve_debug(debug)
    """
    Common helper: binarize for black defects and collect qualifying contours.
    Returns (defects_found, largest_area, rects)
    """
    if gray.size == 0:
        return 0, 0, []

    # Adaptive threshold: terminal avg - contrast
    body_avg = int(np.mean(gray))
    threshold = max(0, min(255, body_avg - int(contrast)))
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)

    # Clean small noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    defects = []
    rects = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 10:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        area_fail = (min_area != 255) and (area >= int(min_area))
        size_fail = False
        if min_square != 255:
            size_fail = (w >= int(min_square)) or (h >= int(min_square))
        if apply_or:
            is_defect = area_fail or size_fail
        else:
            checks = []
            if min_area != 255:
                checks.append(area_fail)
            if min_square != 255:
                checks.append(size_fail)
            is_defect = all(checks) if checks else False
        if is_defect:
            defects.append({'area': area, 'rect': (x, y, w, h)})
            rects.append((x, y, w, h))

    count = len(defects)
    largest = int(max([d['area'] for d in defects]) if defects else 0)
    return count, largest, rects


def check_incomplete_termination_1(image, roi, contrast, min_area, min_square=255,
                                    offset_top=0, offset_bottom=0, offset_left=0, offset_right=0,
                                    corner_x=0, corner_y=0,
                                    apply_or=True, debug=False):
    """
    Incomplete Termination 1: detect black defects (poor plating) on terminal areas
    using fixed terminal regions (top and bottom bands).

    Args:
        image: BGR or grayscale image
        roi: package ROI (x, y, w, h)
        contrast: terminal contrast threshold (avg - contrast)
        min_area: maximum acceptable defect area (fail if >=)
        min_square: maximum acceptable defect width/height (fail if >=)
        offsets: edge ignore within terminal ROI
        corner_x/corner_y: chamfer offsets to ignore corners (pixels)
        apply_or: OR/AND logic for area vs size
        debug: verbose logging

    Returns: (defects_found, largest_area, is_pass, defect_rects)
    """
    image = np.copy(image)
    x, y, w, h = roi

    # Define terminal regions: top and bottom fixed bands (30% each)
    band_h = max(1, int(h * 0.30))
    top_roi = (x, y, w, band_h)
    bot_roi = (x, y + h - band_h, w, band_h)

    def inspect_region(region):
        rx, ry, rw, rh = region
        ix = rx + offset_left
        iy = ry + offset_top
        iw = rw - offset_left - offset_right
        ih = rh - offset_top - offset_bottom
        if iw <= 0 or ih <= 0:
            return 0, 0, []
        crop = image[iy:iy+ih, ix:ix+iw]
        if crop.size == 0:
            return 0, 0, []
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop

        # Apply corner chamfer by zeroing corner regions before thresholding
        if corner_x > 0 and corner_y > 0:
            chx = min(corner_x, iw)
            chy = min(corner_y, ih)
            gray = gray.copy()
            # TL, TR, BL, BR corners
            gray[0:chy, 0:chx] = 255
            gray[0:chy, iw - chx:iw] = 255
            gray[ih - chy:ih, 0:chx] = 255
            gray[ih - chy:ih, iw - chx:iw] = 255

        cnt, largest, rects = _detect_black_defects(gray, contrast, min_area, min_square, apply_or, debug)
        # offset rects to image coordinates
        rects = [(ix + rx0, iy + ry0, rw0, rh0) for (rx0, ry0, rw0, rh0) in rects]
        return cnt, largest, rects

    cnt_top, larg_top, rects_top = inspect_region(top_roi)
    cnt_bot, larg_bot, rects_bot = inspect_region(bot_roi)

    defects_found = cnt_top + cnt_bot
    largest_area = max(larg_top, larg_bot)
    is_pass = (defects_found == 0)

    if debug:
        print(f"[DEBUG] Incomplete Termination 1: top={cnt_top}, bottom={cnt_bot}, largest={largest_area}, pass={is_pass}")

    return defects_found, int(largest_area), is_pass, rects_top + rects_bot


def check_incomplete_termination_2(image, roi, contrast, min_area, min_square=255,
                                    left_top=0, left_bottom=0, left_left=0, left_right=0,
                                    right_top=0, right_bottom=0, right_left=0, right_right=0,
                                    corner_x=0, corner_y=0,
                                    apply_or=True, debug=False):
    """
    Incomplete Termination 2: per-electrode inspection with user-defined inspection areas.
    
    CRITICAL OFFSET INTERPRETATION (from old C++ app):
    - LEFT terminal: 
        left_left (A) = starting distance from package LEFT edge
        left_right (B) = inspection WIDTH (how far to extend from A)
    - RIGHT terminal:
        right_right (A) = starting distance from package RIGHT edge  
        right_left (B) = inspection WIDTH (how far to extend from A)
    - corner_x/corner_y: chamfer offsets to ignore corners

    Args:
        image: BGR or grayscale image
        roi: package ROI (x, y, w, h)
        contrast/min_area/min_square: thresholds
        left_*/right_*: offsets for each terminal ROI
        corner_x/corner_y: chamfer offsets to ignore corners (pixels)
        apply_or: OR/AND logic for area vs size
    Returns: (defects_found, largest_area, is_pass, defect_rects)
    """
    image = np.copy(image)
    x, y, w, h = roi

    # LEFT terminal: start from left edge + left_left (A), width = left_right (B)
    left_start_x = x + left_left
    left_width = left_right if left_right > 0 else max(1, int(w * 0.25))  # fallback
    left_roi = (left_start_x, y, left_width, h)

    # RIGHT terminal: start from right edge - right_right - right_left (A + B), width = right_left (B)
    right_width = right_left if right_left > 0 else max(1, int(w * 0.25))  # fallback
    right_start_x = x + w - right_right - right_width
    right_roi = (right_start_x, y, right_width, h)

    def inspect(region, t_off, b_off):
        rx, ry, rw, rh = region
        # Apply top/bottom offsets only (left/right already defined by A/B)
        iy = ry + t_off
        ih = rh - t_off - b_off
        if rw <= 0 or ih <= 0:
            return 0, 0, []
        crop = image[iy:iy+ih, rx:rx+rw]
        if crop.size == 0:
            return 0, 0, []
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop

        # Apply corner chamfer by zeroing corner regions
        if corner_x > 0 and corner_y > 0:
            chx = min(corner_x, rw)
            chy = min(corner_y, ih)
            gray = gray.copy()
            # TL, TR, BL, BR corners
            gray[0:chy, 0:chx] = 255
            gray[0:chy, rw - chx:rw] = 255
            gray[ih - chy:ih, 0:chx] = 255
            gray[ih - chy:ih, rw - chx:rw] = 255

        cnt, largest, rects = _detect_black_defects(gray, contrast, min_area, min_square, apply_or, debug)
        # offset rects to image coordinates
        rects = [(rx + rx0, iy + ry0, rw0, rh0) for (rx0, ry0, rw0, rh0) in rects]
        return cnt, largest, rects

    cnt_l, larg_l, rects_l = inspect(left_roi, left_top, left_bottom)
    cnt_r, larg_r, rects_r = inspect(right_roi, right_top, right_bottom)

    defects_found = cnt_l + cnt_r
    largest_area = max(larg_l, larg_r)
    is_pass = (defects_found == 0)

    if debug:
        print(f"[DEBUG] Incomplete Termination 2: left={cnt_l}, right={cnt_r}, largest={largest_area}, pass={is_pass}")
        print(f"[DEBUG] IT2 ROIs: left=({left_roi}), right=({right_roi})")

    return defects_found, int(largest_area), is_pass, rects_l + rects_r


def check_terminal_offset(image, roi, 
                         left_top=0, left_bottom=0, left_left=0, left_right=0, left_corner_x=0, left_corner_y=0,
                         right_top=0, right_bottom=0, right_left=0, right_right=0, right_corner_x=0, right_corner_y=0,
                         contrast=255, min_area=255, min_square=255,
                         apply_or=True, debug=False):
    """
    Check terminal dimensions against configured offset limits (inspection coverage area).
    Detects if terminals fall outside expected offset boundaries.

    OFFSET INTERPRETATION (per documentation):
    - LEFT terminal:
        left_left (A) = starting distance from package LEFT edge
        left_right (B) = inspection WIDTH (how far to extend from A)
    - RIGHT terminal:
        right_right (A) = starting distance from package RIGHT edge  
        right_left (B) = inspection WIDTH (how far to extend from A)
    - Top/Bottom: vertical margins within terminal height
    - corner_x/corner_y: chamfer offsets to ignore corners

    Args:
        image: BGR or grayscale image
        roi: package ROI (x, y, w, h)
        left_*/right_*: offset parameters for each terminal
        contrast/min_area/min_square: defect detection thresholds (optional)
        apply_or: OR/AND logic for area vs size
        debug: verbose logging

    Returns: (is_pass, debug_info_dict)
    """
    x, y, w, h = roi

    # Define left and right terminal ROIs based on offset parameters
    # LEFT terminal: start from left edge + left_left (A), width = left_right (B)
    left_start_x = x + left_left
    left_width = left_right if left_right > 0 else max(1, int(w * 0.25))
    left_roi = (left_start_x, y, left_width, h)

    # RIGHT terminal: start from right edge - right_right - right_left (A + B), width = right_left (B)
    right_width = right_left if right_left > 0 else max(1, int(w * 0.25))
    right_start_x = x + w - right_right - right_width
    right_roi = (right_start_x, y, right_width, h)

    # Check if terminals are within valid image bounds
    def check_terminal_bounds(term_roi, corner_x, corner_y):
        tx, ty, tw, th = term_roi
        
        # Apply top/bottom offsets
        iy = ty
        ih = th
        
        # Check actual terminal presence by looking for non-white pixels
        if tx < 0 or ty < 0 or tx + tw > image.shape[1] or ty + ih > image.shape[0]:
            if debug:
                print(f"[DEBUG] Terminal out of bounds: ({tx},{ty},{tw},{ih})")
            return False, {"error": "out_of_bounds"}
        
        crop = image[iy:iy+ih, tx:tx+tw]
        if crop.size == 0:
            return False, {"error": "empty_crop"}
        
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        
        # Apply corner chamfer
        if corner_x > 0 and corner_y > 0:
            chx = min(corner_x, tw)
            chy = min(corner_y, ih)
            gray = gray.copy()
            gray[0:chy, 0:chx] = 255
            gray[0:chy, tw - chx:tw] = 255
            gray[ih - chy:ih, 0:chx] = 255
            gray[ih - chy:ih, tw - chx:tw] = 255
        
        # Check for terminal signal (not all white)
        mean_intensity = int(np.mean(gray))
        is_valid = mean_intensity < 250  # Terminal should have some dark content
        
        return is_valid, {"mean_intensity": mean_intensity, "bounds": f"({tx},{ty},{tw},{ih})"}

    left_valid, left_info = check_terminal_bounds(left_roi, left_corner_x, left_corner_y)
    right_valid, right_info = check_terminal_bounds(right_roi, right_corner_x, right_corner_y)

    is_pass = left_valid and right_valid

    debug_info = {
        "left_valid": left_valid,
        "left_info": left_info,
        "right_valid": right_valid,
        "right_info": right_info,
        "left_roi": left_roi,
        "right_roi": right_roi
    }

    if debug:
        print(f"[DEBUG] Terminal Offset: left_valid={left_valid}, right_valid={right_valid}, pass={is_pass}")
        print(f"[DEBUG] Left ROI: {left_roi}, Right ROI: {right_roi}")
        print(f"[DEBUG] Left info: {left_info}, Right info: {right_info}")

    return is_pass, debug_info


def check_compare_terminal_corner(image, roi, manually_difference=20,
                                  offset_top=0, offset_bottom=0, offset_left=0, offset_right=0,
                                  corner_width_ratio=0.15, debug=False):
    """
    Compare left and right terminal corner brightness to detect plating differences.
    
    This check measures the average intensity in corner regions of left and right terminals
    and ensures they are within a specified tolerance. Used to catch uneven plating or
    oxidation affecting one terminal more than the other.

    Args:
        image: BGR or grayscale image
        roi: package ROI (x, y, w, h)
        manually_difference: maximum acceptable difference between left and right corners
        offset_*: margins to ignore from terminal edges
        corner_width_ratio: fraction of package width to use for corner sampling (default 0.15)
        debug: verbose logging

    Returns: (left_avg, right_avg, difference, is_pass)
    """
    x, y, w, h = roi
    
    # Define corner sampling width (default 15% of package width on each side)
    corner_w = max(1, int(w * corner_width_ratio))
    
    # LEFT terminal corner region
    lx = x + offset_left
    ly = y + offset_top
    lw = corner_w
    lh = h - offset_top - offset_bottom
    
    # RIGHT terminal corner region
    rx = x + w - corner_w - offset_right
    ry = y + offset_top
    rw = corner_w
    rh = h - offset_top - offset_bottom
    
    if lw <= 0 or lh <= 0 or rw <= 0 or rh <= 0:
        if debug:
            print(f"[DEBUG] Compare Corner ROI invalid")
        return 0, 0, 0, True
    
    # Sample left corner
    left_crop = image[ly:ly+lh, lx:lx+lw]
    if left_crop.size == 0:
        return 0, 0, 0, True
    left_gray = cv2.cvtColor(left_crop, cv2.COLOR_BGR2GRAY) if len(left_crop.shape) == 3 else left_crop
    left_avg = int(np.mean(left_gray))
    
    # Sample right corner
    right_crop = image[ry:ry+rh, rx:rx+rw]
    if right_crop.size == 0:
        return left_avg, 0, 0, True
    right_gray = cv2.cvtColor(right_crop, cv2.COLOR_BGR2GRAY) if len(right_crop.shape) == 3 else right_crop
    right_avg = int(np.mean(right_gray))
    
    # Calculate absolute difference
    difference = abs(left_avg - right_avg)
    is_pass = (difference <= manually_difference)
    
    if debug:
        print(f"[DEBUG] Compare Terminal Corner: left={left_avg}, right={right_avg}, diff={difference}, threshold={manually_difference}, pass={is_pass}")
        print(f"[DEBUG] Left ROI: ({lx},{ly},{lw},{lh}), Right ROI: ({rx},{ry},{rw},{rh})")
    
    return left_avg, right_avg, difference, is_pass


def check_black_pixels_count(image, roi, contrast, level, 
                             inspection_width_left=15, inspection_width_right=15,
                             inspection_width_top=15, inspection_width_bottom=15,
                             debug=False):
    """
    Count black pixels in terminal inspection bands and compare to threshold.
    
    Enabled Black Pixels Count to inspect 4 sides of terminal according to user's input setting.
    Inspects each side independently and counts pixels darker than (avg - contrast).
    Fails if any side exceeds the level threshold.

    Args:
        image: BGR or grayscale image
        roi: package ROI (x, y, w, h)
        contrast: threshold offset (pixels darker than avg - contrast are counted)
        level: maximum acceptable black pixel count per side
        inspection_width_*: band width for each side in pixels
        debug: verbose logging

    Returns: (total_black_pixels, max_side_count, is_pass, side_counts_dict)
    """
    x, y, w, h = roi
    
    # Define inspection bands for each side
    # Left band: vertical strip on left edge
    left_roi = (x, y, inspection_width_left, h)
    # Right band: vertical strip on right edge
    right_roi = (x + w - inspection_width_right, y, inspection_width_right, h)
    # Top band: horizontal strip on top edge
    top_roi = (x, y, w, inspection_width_top)
    # Bottom band: horizontal strip on bottom edge
    bottom_roi = (x, y + h - inspection_width_bottom, w, inspection_width_bottom)
    
    side_counts = {}
    
    def count_black_pixels_in_band(band_roi, label):
        bx, by, bw, bh = band_roi
        if bw <= 0 or bh <= 0:
            return 0
        
        crop = image[by:by+bh, bx:bx+bw]
        if crop.size == 0:
            return 0
        
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
        
        # Calculate threshold: avg - contrast
        avg = int(np.mean(gray))
        threshold = max(0, avg - int(contrast))
        
        # Count pixels below threshold (black defects)
        black_pixels = np.sum(gray < threshold)
        
        if debug:
            print(f"[DEBUG] Black Pixels {label}: count={black_pixels}, avg={avg}, threshold={threshold}, ROI=({bx},{by},{bw},{bh})")
        
        return int(black_pixels)
    
    # Count black pixels on each side
    side_counts['left'] = count_black_pixels_in_band(left_roi, 'Left')
    side_counts['right'] = count_black_pixels_in_band(right_roi, 'Right')
    side_counts['top'] = count_black_pixels_in_band(top_roi, 'Top')
    side_counts['bottom'] = count_black_pixels_in_band(bottom_roi, 'Bottom')
    
    total_black_pixels = sum(side_counts.values())
    max_side_count = max(side_counts.values())
    
    # Fail if any side exceeds the level threshold
    is_pass = (max_side_count <= level)
    
    if debug:
        print(f"[DEBUG] Black Pixels Count: total={total_black_pixels}, max={max_side_count}, level={level}, pass={is_pass}")
        print(f"[DEBUG] Side counts: {side_counts}")
    
    return total_black_pixels, max_side_count, is_pass, side_counts


def draw_chipoff_inspection_bands(image, roi, band_type='inner', 
                                  inspection_width_x=80, inspection_width_y=40,
                                  band_width_ratio=0.25,
                                  offset_top=0, offset_bottom=0, offset_left=0, offset_right=0,
                                  enable_corner_offset=False, corner_offset_x=0, corner_offset_y=0,
                                  color=(0, 255, 255), thickness=2):
    """
    Draw inspection band boundaries for visual feedback in step mode.
    
    Args:
        image: image to draw on (will be modified in-place)
        roi: package ROI (x,y,w,h)
        band_type: 'inner' (4 corners) or 'outer' (4 sides)
        inspection_width_x/y: corner inspection dimensions (for inner)
        band_width_ratio: band size ratio (for outer)
        offset_*: margins within bands/corners
        enable_corner_offset: use chamfered corners (for inner)
        corner_offset_x/y: chamfer dimensions (for inner)
        color: BGR color for drawing (default yellow)
        thickness: line thickness
    
    Returns: modified image
    """
    x, y, w, h = roi
    
    if band_type == 'inner':
        # Draw 4 corner regions
        terminal_width = max(1, int(w * 0.25))
        inspection_width_x = min(inspection_width_x, h)
        inspection_width_y = min(inspection_width_y, terminal_width)
        
        corners = [
            ("TL", x, y, inspection_width_y, inspection_width_x),
            ("TR", x + w - inspection_width_y, y, inspection_width_y, inspection_width_x),
            ("BL", x, y + h - inspection_width_x, inspection_width_y, inspection_width_x),
            ("BR", x + w - inspection_width_y, y + h - inspection_width_x, inspection_width_y, inspection_width_x),
        ]
        
        for label, cx, cy, cw, ch in corners:
            if enable_corner_offset:
                ix = cx + corner_offset_x
                iy = cy + corner_offset_y
                iw = cw - (corner_offset_x * 2)
                ih = ch - (corner_offset_y * 2)
            else:
                ix = cx + offset_left
                iy = cy + offset_top
                iw = cw - offset_left - offset_right
                ih = ch - offset_top - offset_bottom
            
            if iw > 0 and ih > 0:
                cv2.rectangle(image, (ix, iy), (ix + iw, iy + ih), color, thickness)
                cv2.putText(image, label, (ix + 2, iy + 12), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    elif band_type == 'outer':
        # Left and right bands
        band_w = max(1, int(w * band_width_ratio))
        
        # Left band
        left_x = x + offset_left
        left_y = y + offset_top
        left_w = band_w - offset_left - offset_right
        left_h = h - offset_top - offset_bottom
        if left_w > 0 and left_h > 0:
            cv2.rectangle(image, (left_x, left_y), (left_x + left_w, left_y + left_h), color, thickness)
            cv2.putText(image, "LEFT", (left_x + 5, left_y + 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Right band
        right_x = x + w - band_w + offset_left
        right_y = y + offset_top
        right_w = band_w - offset_left - offset_right
        right_h = h - offset_top - offset_bottom
        if right_w > 0 and right_h > 0:
            cv2.rectangle(image, (right_x, right_y), (right_x + right_w, right_y + right_h), color, thickness)
            cv2.putText(image, "RIGHT", (right_x + 5, right_y + 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    return image


def draw_terminal_corner_regions(image, roi, corner_width_ratio=0.15,
                                 offset_top=0, offset_bottom=0, offset_left=0, offset_right=0,
                                 color=(255, 255, 0), thickness=2):
    """
    Draw terminal corner sampling regions for visual feedback.
    
    Args:
        image: image to draw on (will be modified in-place)
        roi: package ROI (x,y,w,h)
        corner_width_ratio: fraction of width for corner sampling
        offset_*: margins
        color: BGR color (default cyan)
        thickness: line thickness
    
    Returns: modified image
    """
    x, y, w, h = roi
    corner_w = max(1, int(w * corner_width_ratio))
    
    # Left corner
    lx = x + offset_left
    ly = y + offset_top
    lw = corner_w
    lh = h - offset_top - offset_bottom
    if lw > 0 and lh > 0:
        cv2.rectangle(image, (lx, ly), (lx + lw, ly + lh), color, thickness)
        cv2.putText(image, "L", (lx + 5, ly + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # Right corner
    rx = x + w - corner_w - offset_right
    ry = y + offset_top
    rw = corner_w
    rh = h - offset_top - offset_bottom
    if rw > 0 and rh > 0:
        cv2.rectangle(image, (rx, ry), (rx + rw, ry + rh), color, thickness)
        cv2.putText(image, "R", (rx + rw - 15, ry + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    return image


def draw_black_pixels_bands(image, roi, 
                            inspection_width_left=15, inspection_width_right=15,
                            inspection_width_top=15, inspection_width_bottom=15,
                            color=(255, 0, 255), thickness=1):
    """
    Draw black pixels count inspection bands for visual feedback.
    
    Args:
        image: image to draw on (will be modified in-place)
        roi: package ROI (x,y,w,h)
        inspection_width_*: band widths for each side
        color: BGR color (default magenta)
        thickness: line thickness
    
    Returns: modified image
    """
    x, y, w, h = roi
    
    # Left band
    cv2.rectangle(image, (x, y), (x + inspection_width_left, y + h), color, thickness)
    
    # Right band
    cv2.rectangle(image, (x + w - inspection_width_right, y), (x + w, y + h), color, thickness)
    
    # Top band
    cv2.rectangle(image, (x, y), (x + w, y + inspection_width_top), color, thickness)
    
    # Bottom band
    cv2.rectangle(image, (x, y + h - inspection_width_bottom), (x + w, y + h), color, thickness)
    
    return image
