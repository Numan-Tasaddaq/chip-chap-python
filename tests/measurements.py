import cv2
from config.debug_runtime import resolve_debug
import numpy as np

def _binary_from_edge_contrast(gray, edge_contrast, debug=False):
    debug = resolve_debug(debug)
    """Build a binary image using two polarities and choose the one with reasonable fill."""
    _, binary_inv = cv2.threshold(gray, int(edge_contrast), 255, cv2.THRESH_BINARY_INV)
    _, binary_norm = cv2.threshold(gray, int(edge_contrast), 255, cv2.THRESH_BINARY)

    white_inv = (np.sum(binary_inv == 255) / binary_inv.size) * 100 if binary_inv.size else 0
    white_norm = (np.sum(binary_norm == 255) / binary_norm.size) * 100 if binary_norm.size else 0

    if debug:
        print(f"[DEBUG] Binary fill%% inv={white_inv:.1f}, norm={white_norm:.1f}")

    # Prefer a reasonable fill 10-70%; otherwise pick closer to 40%
    if 10 < white_inv <= 70:
        chosen = binary_inv
    elif 10 < white_norm <= 70:
        chosen = binary_norm
    else:
        chosen = binary_inv if abs(white_inv - 40) < abs(white_norm - 40) else binary_norm

    # Clean a bit
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    chosen = cv2.morphologyEx(chosen, cv2.MORPH_CLOSE, kernel, iterations=1)
    return chosen

def _measure_band_thickness_top_bottom(gray, edge_contrast=106, num_scans=60, debug=False):
    debug = resolve_debug(debug)
    """
    Estimate thickness of top and bottom body bands between terminal inner edge and central body area.
    Returns (top_thickness, bottom_thickness) in pixels, or (None, None) if failed.
    """
    h, w = gray.shape[:2]
    if h == 0 or w == 0:
        return None, None

    binary = _binary_from_edge_contrast(gray, edge_contrast, debug)
    sobel_y = cv2.Sobel(binary, cv2.CV_64F, 0, 1, ksize=3)

    # Regions: top 35%, bottom 35%
    top_h = int(h * 0.35)
    bot_h = int(h * 0.35)
    top_region = sobel_y[0:top_h, :]
    bot_region = sobel_y[h - bot_h:h, :]

    skip = max(1, w // max(10, num_scans))

    def thickness_in_region(grad_region, offset_y, is_top=True):
        vals = []
        for col in range(0, grad_region.shape[1], skip):
            col_data = grad_region[:, col]
            # Find candidate edges by prominence
            # For top: terminal inner edge tends to be a negative peak first, central body edge positive after
            # For bottom: polarity can flip; try both orders and pick plausible distances
            peaks_pos = np.argwhere(col_data > 5).flatten()
            peaks_neg = np.argwhere(col_data < -5).flatten()
            best = None
            if is_top:
                for n in peaks_neg:
                    # find next positive after n
                    p_after = peaks_pos[peaks_pos > n]
                    if p_after.size:
                        dist = int(p_after[0] - n)
                        if 4 <= dist <= int(h * 0.5):
                            best = dist
                            break
            else:
                # bottom: try positive then negative after
                for p in peaks_pos[::-1]:  # start from bottom side by reversing
                    n_before = peaks_neg[peaks_neg < p]
                    if n_before.size:
                        dist = int(p - n_before[-1])
                        if 4 <= dist <= int(h * 0.5):
                            best = dist
                            break
                # fallback: try negative then positive
                if best is None:
                    for n in peaks_neg:
                        p_after = peaks_pos[peaks_pos > n]
                        if p_after.size:
                            dist = int(p_after[0] - n)
                            if 4 <= dist <= int(h * 0.5):
                                best = dist
                                break
            if best is not None:
                vals.append(best)
        if not vals:
            return None
        # use median for robustness
        return float(np.median(vals))

    top_t = thickness_in_region(top_region, 0, is_top=True)
    bot_t = thickness_in_region(bot_region, h - bot_h, is_top=False)
    if debug:
        print(f"[DEBUG] Band thickness top={top_t}, bottom={bot_t}")
    return top_t, bot_t

def measure_body_to_term_width(image, roi, edge_contrast=106, num_scans=60, debug=False):
    debug = resolve_debug(debug)
    """
    Measure the thickness of the body bands adjacent to terminals (top and bottom).
    Returns dict: { 'top': value(px) or None, 'bottom': value(px) or None }
    """
    # CRITICAL: Create independent copy to prevent memory corruption
    image = np.copy(image)
    
    x, y, w, h = roi
    crop = image[y:y+h, x:x+w].copy()
    if crop.size == 0:
        return {'top': None, 'bottom': None}
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    top_t, bot_t = _measure_band_thickness_top_bottom(gray, edge_contrast, num_scans, debug)
    return {'top': top_t, 'bottom': bot_t}

def measure_term_to_body_gap(image, roi, edge_contrast=106, num_scans=60, debug=False):
    debug = resolve_debug(debug)
    """
    Measure the minimum gap between terminal inner edge and body area (top and bottom),
    returning the worst-case (minimum) gap in pixels.
    """
    # CRITICAL: Create independent copy to prevent memory corruption
    image = np.copy(image)
    
    x, y, w, h = roi
    crop = image[y:y+h, x:x+w].copy()
    if crop.size == 0:
        return None
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    binary = _binary_from_edge_contrast(gray, edge_contrast, debug)
    sobel_y = cv2.Sobel(binary, cv2.CV_64F, 0, 1, ksize=3)

    top_h = int(h * 0.35)
    bot_h = int(h * 0.35)
    top_region = sobel_y[0:top_h, :]
    bot_region = sobel_y[h - bot_h:h, :]
    skip = max(1, w // max(20, num_scans))

    def min_gap_region(grad_region, is_top=True):
        gaps = []
        for col in range(0, grad_region.shape[1], skip):
            col_data = grad_region[:, col]
            peaks_pos = np.argwhere(col_data > 5).flatten()
            peaks_neg = np.argwhere(col_data < -5).flatten()
            # Try both polarities; take smaller plausible gap
            best = None
            # negative then positive
            for n in peaks_neg:
                p_after = peaks_pos[peaks_pos > n]
                if p_after.size:
                    dist = int(p_after[0] - n)
                    if 2 <= dist <= int(h * 0.5):
                        best = dist
                        break
            # positive then negative
            if best is None:
                for p in peaks_pos:
                    n_after = peaks_neg[peaks_neg > p]
                    if n_after.size:
                        dist = int(n_after[0] - p)
                        if 2 <= dist <= int(h * 0.5):
                            best = dist
                            break
            if best is not None:
                gaps.append(best)
        if not gaps:
            return None
        return int(np.min(gaps))

    g_top = min_gap_region(top_region, True)
    g_bot = min_gap_region(bot_region, False)
    if debug:
        print(f"[DEBUG] Term-to-body gaps top={g_top}, bottom={g_bot}")
    # return worst-case (minimum) across both
    candidates = [g for g in [g_top, g_bot] if g is not None]
    if not candidates:
        return None
    return int(min(candidates))

def measure_body_width(image, roi, body_contrast=75, debug=False):
    debug = resolve_debug(debug)
    """
    Measure body width using edge scanning method similar to old system.
    Scans top and bottom regions, detects edges, fits lines, and calculates distance.
    
    Args:
        image: Input BGR image
        roi: Package ROI (x, y, w, h)
        body_contrast: Threshold for binarization (default 75)
        debug: If True, print debug information
        
    Returns:
        Body width in pixels (distance between top and bottom edges), or None if failed
    """
    x, y, w, h = roi
    
    if debug:
        print(f"[DEBUG] Body Width: ROI=({x}, {y}, {w}, {h})")
        # Debug: Check input image integrity BEFORE copy
        print(f"[DEBUG] Body Width: Image id={id(image)}, shape={image.shape}, dtype={image.dtype}")
        full_roi_before = image[y:y+h, x:x+w]
        full_roi_mean_before = cv2.mean(full_roi_before)[0]
        print(f"[DEBUG] Body Width: Input ROI BGR mean (BEFORE copy)={full_roi_mean_before:.1f}")
    
    # CRITICAL: Create independent copy to prevent any memory corruption from QImage or other sources
    image = np.copy(image)
    
    if debug:
        # Verify copy worked
        print(f"[DEBUG] Body Width: Copied image id={id(image)}, shape={image.shape}")
        full_roi_after = image[y:y+h, x:x+w]
        full_roi_mean_after = cv2.mean(full_roi_after)[0]
        print(f"[DEBUG] Body Width: Input ROI BGR mean (AFTER copy)={full_roi_mean_after:.1f}")
    
    crop = image[y:y+h, x:x+w].copy()

    if crop.size == 0:
        if debug:
            print(f"[DEBUG] Body Width: Empty crop")
        return None

    # Convert to grayscale
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    
    if debug:
        gray_mean = np.mean(gray)
        print(f"[DEBUG] Body Width: Gray shape={gray.shape}, dtype={gray.dtype}, mean={gray_mean:.1f}")
    
    # Define search regions: top 25% and bottom 25% of the package (matching old system)
    top_region_height = int(h * 0.25)
    bottom_region_height = int(h * 0.25)
    
    if debug:
        print(f"[DEBUG] Body Width: Top region height={top_region_height}, Bottom region height={bottom_region_height}")
    
    top_region = gray[0:top_region_height, :]
    bottom_region = gray[h-bottom_region_height:h, :]
    
    if top_region.size == 0 or bottom_region.size == 0:
        if debug:
            print(f"[DEBUG] Body Width: Empty regions - top.size={top_region.size}, bottom.size={bottom_region.size}")
        return None
    
    # Adaptive thresholding: adjust based on region mean intensity
    top_mean = np.mean(top_region)
    bottom_mean = np.mean(bottom_region)
    
    # For bright regions (mean > 90), use 75% of mean to separate body from background
    top_threshold = int(top_mean * 0.75) if top_mean > 90 else body_contrast
    bottom_threshold = int(bottom_mean * 0.75) if bottom_mean > 90 else body_contrast
    
    if debug:
        print(f"[DEBUG] Body Width: Region means - top={top_mean:.1f}, bottom={bottom_mean:.1f}")
        print(f"[DEBUG] Body Width: Adaptive thresholds - top={top_threshold}, bottom={bottom_threshold}")
    
    # Binarize both regions with adaptive thresholds
    _, top_binary = cv2.threshold(top_region, top_threshold, 255, cv2.THRESH_BINARY)
    _, bottom_binary = cv2.threshold(bottom_region, bottom_threshold, 255, cv2.THRESH_BINARY)
    
    if debug:
        top_white_pct = (np.sum(top_binary == 255) / top_binary.size) * 100
        bottom_white_pct = (np.sum(bottom_binary == 255) / bottom_binary.size) * 100
        print(f"[DEBUG] Body Width: Binary white% - top={top_white_pct:.1f}, bottom={bottom_white_pct:.1f}")
    
    # Apply Gaussian smoothing (similar to binomial filter)
    top_binary = cv2.GaussianBlur(top_binary, (5, 5), 1.0)
    bottom_binary = cv2.GaussianBlur(bottom_binary, (5, 5), 1.0)
    
    # Detect edges using Sobel gradient
    top_edges = cv2.Sobel(top_binary, cv2.CV_64F, 0, 1, ksize=3)  # Vertical gradient
    bottom_edges = cv2.Sobel(bottom_binary, cv2.CV_64F, 0, 1, ksize=3)
    
    # Find edge points by scanning columns
    top_edge_points = []
    bottom_edge_points = []
    
    skip_factor = max(1, w // 30)  # Scan ~30 columns for better sampling
    
    def collect_edge_points(top_sign="neg", bottom_sign="pos", threshold=5):
        """Collect edge points with configurable gradient directions."""
        top_pts = []
        bottom_pts = []

        for col in range(0, top_region.shape[1], skip_factor):
            column_data = top_edges[:, col]
            edge_idx = np.argmin(column_data) if top_sign == "neg" else np.argmax(column_data)
            grad_val = column_data[edge_idx]
            if (top_sign == "neg" and grad_val < -threshold) or (top_sign == "pos" and grad_val > threshold):
                top_pts.append([col, edge_idx])

        for col in range(0, bottom_region.shape[1], skip_factor):
            column_data = bottom_edges[:, col]
            edge_idx = np.argmax(column_data) if bottom_sign == "pos" else np.argmin(column_data)
            grad_val = column_data[edge_idx]
            if (bottom_sign == "pos" and grad_val > threshold) or (bottom_sign == "neg" and grad_val < -threshold):
                bottom_pts.append([col, edge_idx + (h - bottom_region_height)])

        return top_pts, bottom_pts

    # Primary attempt: bright background → dark body at top, dark body → bright background at bottom
    top_edge_points, bottom_edge_points = collect_edge_points("neg", "pos", threshold=5)

    # Fallback: try opposite gradient polarity with an even lower threshold
    if len(top_edge_points) < 3 or len(bottom_edge_points) < 3:
        alt_top, alt_bottom = collect_edge_points("pos", "neg", threshold=3)
        if debug:
            print(f"[DEBUG] Fallback polarity used: top={len(alt_top)} bottom={len(alt_bottom)}")
        top_edge_points = top_edge_points if len(top_edge_points) >= 3 else alt_top
        bottom_edge_points = bottom_edge_points if len(bottom_edge_points) >= 3 else alt_bottom

    if debug:
        print(f"[DEBUG] Edge points: top={len(top_edge_points)}, bottom={len(bottom_edge_points)}")
    
    if len(top_edge_points) < 3 or len(bottom_edge_points) < 3:
        if debug:
            print(f"[WARN] Insufficient edge points: top={len(top_edge_points)}, bottom={len(bottom_edge_points)}")
        return None
    
    # Convert to numpy arrays
    top_edge_points = np.array(top_edge_points)
    bottom_edge_points = np.array(bottom_edge_points)
    
    # Fit lines and remove outliers iteratively (5 iterations with decreasing tolerance)
    top_edge_points = _fit_line_with_outlier_removal(top_edge_points, iterations=5, initial_tolerance=15)
    bottom_edge_points = _fit_line_with_outlier_removal(bottom_edge_points, iterations=5, initial_tolerance=15)
    
    if len(top_edge_points) < 2 or len(bottom_edge_points) < 2:
        if debug:
            print(f"[WARN] Too few points after outlier removal")
        return None
    
    # Final line fitting
    top_line = _fit_line(top_edge_points)
    bottom_line = _fit_line(bottom_edge_points)
    
    if top_line is None or bottom_line is None:
        return None
    
    # Calculate vertical distance between lines at center of image
    center_x = w / 2
    top_y = top_line[0] * center_x + top_line[1]
    bottom_y = bottom_line[0] * center_x + bottom_line[1]
    
    body_width = abs(bottom_y - top_y)
    
    if debug:
        print(f"[DEBUG] Top edge points: {len(top_edge_points)}, Bottom edge points: {len(bottom_edge_points)}")
        print(f"[DEBUG] Top line: y = {top_line[0]:.3f}x + {top_line[1]:.3f}")
        print(f"[DEBUG] Bottom line: y = {bottom_line[0]:.3f}x + {bottom_line[1]:.3f}")
        print(f"[DEBUG] Body width at center: {body_width:.1f} pixels")
    
    return int(round(body_width))


def measure_body_length(image, roi, body_contrast=75, debug=False):
    debug = resolve_debug(debug)
    """
    Measure body length (left-to-right) using edge scanning.
    Scans left and right regions, detects edges, fits lines, and calculates distance.

    Args:
        image: Input BGR image
        roi: Package ROI (x, y, w, h)
        body_contrast: Threshold for binarization (default 75)
        debug: If True, print debug information

    Returns:
        Body length in pixels (distance between left and right edges), or None if failed
    """
    # CRITICAL: Create independent copy to prevent memory corruption
    image = np.copy(image)
    
    x, y, w, h = roi
    crop = image[y:y+h, x:x+w].copy()

    if crop.size == 0:
        return None

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    if debug:
        print(f"[DEBUG] Body Length: ROI=({x}, {y}, {w}, {h})")
        print(f"[DEBUG] Body Length: Gray shape={gray.shape}, dtype={gray.dtype}")

    # Define search regions: scan from center outward to find body edges
    # Left region: search from center-left toward left edge
    # Right region: search from center-right toward right edge
    center_x = w // 2
    left_region_width = int(w * 0.5)  # 50% from center toward left
    right_region_width = int(w * 0.5)  # 50% from center toward right

    left_region = gray[:, max(0, center_x - left_region_width):center_x]
    right_region = gray[:, center_x:min(w, center_x + right_region_width)]

    if left_region.size == 0 or right_region.size == 0:
        return None

    # Adaptive thresholding based on region brightness
    left_mean = float(np.mean(left_region))
    right_mean = float(np.mean(right_region))
    
    # Adaptive thresholding: use region mean - 20 to 40 to create contrast
    # If region is bright (mean > 90), threshold around 70-80% of mean to create body/background separation
    left_threshold = int(left_mean * 0.75) if left_mean > 90 else body_contrast
    right_threshold = int(right_mean * 0.75) if right_mean > 90 else body_contrast
    
    if debug:
        print(f"[DEBUG] Body Length: Left region width={left_region_width}, Right region width={right_region_width}")
        print(f"[DEBUG] Body Length: left_mean={left_mean:.1f}, right_mean={right_mean:.1f}")
        print(f"[DEBUG] Body Length: left_threshold={left_threshold}, right_threshold={right_threshold}")

    # Binarize both regions
    _, left_binary = cv2.threshold(left_region, left_threshold, 255, cv2.THRESH_BINARY)
    _, right_binary = cv2.threshold(right_region, right_threshold, 255, cv2.THRESH_BINARY)
    
    if debug:
        left_white_pct = (np.sum(left_binary == 255) / left_binary.size) * 100
        right_white_pct = (np.sum(right_binary == 255) / right_binary.size) * 100
        print(f"[DEBUG] Body Length: Binary left white%={left_white_pct:.1f}, right white%={right_white_pct:.1f}")

    # Smooth
    left_binary = cv2.GaussianBlur(left_binary, (5, 5), 1.0)
    right_binary = cv2.GaussianBlur(right_binary, (5, 5), 1.0)

    # Horizontal gradient (dx)
    left_edges = cv2.Sobel(left_binary, cv2.CV_64F, 1, 0, ksize=3)
    right_edges = cv2.Sobel(right_binary, cv2.CV_64F, 1, 0, ksize=3)

    left_edge_points = []
    right_edge_points = []

    skip_factor = max(1, h // 30)  # sample ~30 rows

    def collect_edge_points(left_sign="pos", right_sign="neg", threshold=5):
        lpts = []
        rpts = []

        # iterate rows
        for row in range(0, left_region.shape[0], skip_factor):
            row_data = left_edges[row, :]
            edge_idx = int(np.argmax(row_data)) if left_sign == "pos" else int(np.argmin(row_data))
            grad_val = row_data[edge_idx]
            if (left_sign == "pos" and grad_val > threshold) or (left_sign == "neg" and grad_val < -threshold):
                lpts.append([edge_idx, row])

        for row in range(0, right_region.shape[0], skip_factor):
            row_data = right_edges[row, :]
            edge_idx = int(np.argmin(row_data)) if right_sign == "neg" else int(np.argmax(row_data))
            grad_val = row_data[edge_idx]
            if (right_sign == "neg" and grad_val < -threshold) or (right_sign == "pos" and grad_val > threshold):
                rpts.append([edge_idx + (w - right_region_width), row])

        return lpts, rpts

    # Primary polarity: rising edge on left, falling edge on right
    left_edge_points, right_edge_points = collect_edge_points("pos", "neg", threshold=5)

    # Fallback polarity
    if len(left_edge_points) < 3 or len(right_edge_points) < 3:
        alt_left, alt_right = collect_edge_points("neg", "pos", threshold=3)
        if debug:
            print(f"[DEBUG] Length fallback polarity used: left={len(alt_left)} right={len(alt_right)}")
        left_edge_points = left_edge_points if len(left_edge_points) >= 3 else alt_left
        right_edge_points = right_edge_points if len(right_edge_points) >= 3 else alt_right

    if debug:
        print(f"[DEBUG] Length edge points: left={len(left_edge_points)}, right={len(right_edge_points)}")
        if len(left_edge_points) > 0:
            print(f"[DEBUG] Left edge sample points (first 5): {left_edge_points[:5]}")
        if len(right_edge_points) > 0:
            print(f"[DEBUG] Right edge sample points (first 5): {right_edge_points[:5]}")

    if len(left_edge_points) < 3 or len(right_edge_points) < 3:
        return None

    left_edge_points = np.array(left_edge_points)
    right_edge_points = np.array(right_edge_points)

    if debug:
        print(f"[DEBUG] Before outlier removal: left={len(left_edge_points)}, right={len(right_edge_points)}")

    # Fit lines with outlier removal
    left_edge_points = _fit_line_with_outlier_removal(left_edge_points, iterations=5, initial_tolerance=15)
    right_edge_points = _fit_line_with_outlier_removal(right_edge_points, iterations=5, initial_tolerance=15)

    if debug:
        print(f"[DEBUG] After outlier removal: left={len(left_edge_points)}, right={len(right_edge_points)}")
        if len(left_edge_points) > 0:
            print(f"[DEBUG] Left points after cleanup (first 5): {left_edge_points[:5].tolist()}")
        if len(right_edge_points) > 0:
            print(f"[DEBUG] Right points after cleanup (first 5): {right_edge_points[:5].tolist()}")

    if len(left_edge_points) < 2 or len(right_edge_points) < 2:
        return None

    left_line = _fit_line(left_edge_points)   # returns [slope, intercept] for y(x)
    right_line = _fit_line(right_edge_points)

    if left_line is None or right_line is None:
        return None

    # Compute x at center_y using inverse of y(x): x = (y - intercept) / slope
    center_y = h / 2
    left_slope, left_intercept = left_line
    right_slope, right_intercept = right_line

    # Guard against near-zero slopes to avoid division errors
    eps = 1e-6
    if abs(left_slope) < eps or abs(right_slope) < eps:
        return None

    left_x = (center_y - left_intercept) / left_slope
    right_x = (center_y - right_intercept) / right_slope

    body_length = abs(right_x - left_x)

    if debug:
        print(f"[DEBUG] Left line: x = {left_line[0]:.3f}y + {left_line[1]:.3f}")
        print(f"[DEBUG] Right line: x = {right_line[0]:.3f}y + {right_line[1]:.3f}")
        print(f"[DEBUG] Body length at center: {body_length:.1f} pixels")

    return int(round(body_length))


def _fit_line(points):
    """
    Fit a line to points using least squares.
    
    Args:
        points: Nx2 array of [x, y] coordinates
        
    Returns:
        [slope, intercept] or None if fitting fails
    """
    if len(points) < 2:
        return None
    
    x = points[:, 0].reshape(-1, 1)
    y = points[:, 1]
    
    # Use linear regression: y = slope * x + intercept
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    
    numerator = np.sum((x.flatten() - x_mean) * (y - y_mean))
    denominator = np.sum((x.flatten() - x_mean) ** 2)
    
    if denominator == 0:
        return None
    
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    
    return [slope, intercept]


def _fit_line_with_outlier_removal(points, iterations=5, initial_tolerance=15):
    """
    Iteratively fit line and remove outliers.
    
    Args:
        points: Nx2 array of [x, y] coordinates
        iterations: Number of outlier removal iterations
        initial_tolerance: Initial distance threshold in pixels
        
    Returns:
        Filtered points array
    """
    tolerance = initial_tolerance
    
    for i in range(iterations):
        if len(points) < 3:
            break
        
        line = _fit_line(points)
        if line is None:
            break
        
        slope, intercept = line
        
        # Calculate distance of each point from fitted line
        x = points[:, 0]
        y = points[:, 1]
        predicted_y = slope * x + intercept
        distances = np.abs(y - predicted_y)
        
        # Keep only points within tolerance
        mask = distances < tolerance
        points = points[mask]
        
        # Decrease tolerance for next iteration
        tolerance -= 2
        if tolerance < 5:
            tolerance = 5
    
    return points

def measure_terminal_width(image, roi, terminal_roi, edge_contrast=106, debug=False):
    debug = resolve_debug(debug)
    """
    Measure terminal width using blob contour detection and projection onto package edges.
    Matches old ChipCap algorithm: finds leftmost/rightmost terminal edges and calculates distance.
    
    Args:
        image: Input BGR image
        roi: Package ROI (x, y, w, h)
        terminal_roi: Terminal ROI (x, y, w, h) within package
        edge_contrast: Contrast threshold from pocket_params (default 106)
        debug: If True, print debug information
    
    Returns:
        Terminal width in pixels, or None if failed
    """
    # CRITICAL: Create independent copy to prevent memory corruption
    image = np.copy(image)
    
    x, y, w, h = roi
    tx, ty, tw, th = terminal_roi
    
    if debug:
        print(f"[DEBUG] Terminal Width: Package ROI=({x}, {y}, {w}, {h}), Terminal ROI=({tx}, {ty}, {tw}, {th})")
    
    # Crop terminal region from image
    crop = image[ty:ty+th, tx:tx+tw]
    
    if crop.size == 0:
        if debug:
            print(f"[DEBUG] Terminal Width: Empty crop")
        return None
    
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    
    # Use edge contrast from pocket_params
    contrast_threshold = edge_contrast
    
    # Binarize: terminals should be darker than background in most cases
    _, binary = cv2.threshold(gray, contrast_threshold, 255, cv2.THRESH_BINARY_INV)
    
    # Apply morphological operations to clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    
    if debug:
        white_pct = (np.sum(binary == 255) / binary.size) * 100
        print(f"[DEBUG] Terminal Width: Binary white%={white_pct:.1f}")
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) == 0:
        if debug:
            print(f"[DEBUG] Terminal Width: No contours found")
        return None
    
    # Find largest contour (terminal blob)
    largest_contour = max(contours, key=cv2.contourArea)
    
    if cv2.contourArea(largest_contour) < 10:
        if debug:
            print(f"[DEBUG] Terminal Width: Contour area too small")
        return None
    
    # Find extreme points (leftmost and rightmost)
    leftmost = tuple(largest_contour[largest_contour[:, :, 0].argmin()][0])
    rightmost = tuple(largest_contour[largest_contour[:, :, 0].argmax()][0])
    
    if debug:
        print(f"[DEBUG] Terminal Width: Leftmost={leftmost}, Rightmost={rightmost}")
    
    # Calculate Euclidean distance (old ChipCap method)
    dist = np.sqrt((rightmost[0] - leftmost[0])**2 + (rightmost[1] - leftmost[1])**2)
    
    if debug:
        print(f"[DEBUG] Terminal Width: Distance={dist:.1f} pixels")
    
    return int(round(dist))


def measure_terminal_length(image, roi, terminal_roi, edge_contrast=106, num_scans=100, debug=False):
    debug = resolve_debug(debug)
    """
    Measure terminal length using multi-scan edge detection.
    Matches old ChipCap algorithm: scans multiple lines perpendicular to terminal, 
    detects inner and outer edges, calculates length = outer - inner.
    
    Args:
        image: Input BGR image
        roi: Package ROI (x, y, w, h)
        terminal_roi: Terminal ROI (x, y, w, h)
        edge_contrast: Contrast threshold from pocket_params (default 106)
        num_scans: Number of scan lines (default 100)
        debug: If True, print debug information
    
    Returns:
        Terminal length in pixels (median of all scan measurements), or None if failed
    """
    # CRITICAL: Create independent copy to prevent memory corruption
    image = np.copy(image)
    
    x, y, w, h = roi
    tx, ty, tw, th = terminal_roi
    
    if debug:
        print(f"[DEBUG] Terminal Length: Package ROI=({x}, {y}, {w}, {h}), Terminal ROI=({tx}, {ty}, {tw}, {th})")
    
    crop = image[ty:ty+th, tx:tx+tw]
    
    if crop.size == 0:
        if debug:
            print(f"[DEBUG] Terminal Length: Empty crop")
        return None
    
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    
    # Try two binarization approaches: inverted and non-inverted
    binary_inv = None
    binary_normal = None
    
    # Approach 1: Dark terminal on bright background (THRESH_BINARY_INV)
    _, binary_inv = cv2.threshold(gray, edge_contrast, 255, cv2.THRESH_BINARY_INV)
    white_pct_inv = (np.sum(binary_inv == 255) / binary_inv.size) * 100 if binary_inv.size > 0 else 0
    
    # Approach 2: Bright terminal on dark background (THRESH_BINARY)
    _, binary_normal = cv2.threshold(gray, edge_contrast, 255, cv2.THRESH_BINARY)
    white_pct_normal = (np.sum(binary_normal == 255) / binary_normal.size) * 100 if binary_normal.size > 0 else 0
    
    if debug:
        print(f"[DEBUG] Terminal Length: white_inv={white_pct_inv:.1f}%, white_normal={white_pct_normal:.1f}%")
    
    # Choose the binary image with more reasonable white percentage (not too extreme)
    # Terminals should occupy 10-70% of the ROI
    if 10 < white_pct_inv <= 70:
        binary = binary_inv
        polarity_used = "inverted"
    elif 10 < white_pct_normal <= 70:
        binary = binary_normal
        polarity_used = "normal"
    else:
        # If neither is ideal, prefer the one closest to 40%
        binary = binary_inv if abs(white_pct_inv - 40) < abs(white_pct_normal - 40) else binary_normal
        polarity_used = "inverted" if abs(white_pct_inv - 40) < abs(white_pct_normal - 40) else "normal"
    
    # Apply morphological operations to clean up noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    if debug:
        print(f"[DEBUG] Terminal Length: Using {polarity_used} polarity")
    
    # Perform edge detection on each scan line
    measurements = []
    skip_factor = max(1, tw // num_scans)
    
    # Scan horizontally across terminal width
    for col in range(0, tw, skip_factor):
        if col >= binary.shape[1]:
            continue
            
        column_data = binary[:, col]
        
        # Find white regions (terminal) in this column
        white_pixels = np.where(column_data == 255)[0]
        
        if len(white_pixels) < 2:
            continue
        
        # Inner edge = first white pixel, Outer edge = last white pixel
        inner_edge = white_pixels[0]
        outer_edge = white_pixels[-1]
        
        length = outer_edge - inner_edge
        
        if length > 2:  # Only count valid measurements
            measurements.append(length)
    
    if len(measurements) < 3:
        if debug:
            print(f"[DEBUG] Terminal Length: Insufficient measurements ({len(measurements)}), trying Sobel")
        
        # Fallback: use Sobel edge detection
        gray_norm = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
        sobelx = cv2.Sobel(gray_norm, cv2.CV_64F, 0, 1, ksize=3)
        sobel_edges = np.abs(sobelx)
        sobel_thresh = cv2.threshold(sobel_edges.astype(np.uint8), 30, 255, cv2.THRESH_BINARY)[1]
        
        measurements = []
        for col in range(0, tw, skip_factor):
            if col >= sobel_thresh.shape[1]:
                continue
            column_data = sobel_thresh[:, col]
            edge_pixels = np.where(column_data == 255)[0]
            
            if len(edge_pixels) >= 2:
                # Find the two strongest edges (likely boundaries)
                measurements.append(edge_pixels[-1] - edge_pixels[0])
        
        if len(measurements) < 3:
            if debug:
                print(f"[DEBUG] Terminal Length: Still insufficient measurements after Sobel")
            return None
    
    # Return median measurement (robust to outliers, like old system)
    median_length = np.median(measurements)
    
    if debug:
        print(f"[DEBUG] Terminal Length: Measurements count={len(measurements)}, median={median_length:.1f}")
        print(f"[DEBUG] Terminal Length: Min={np.min(measurements)}, Max={np.max(measurements)}, Mean={np.mean(measurements):.1f}")
    
    return int(round(median_length))


def measure_term_to_term_length(image, roi, left_terminal_roi, right_terminal_roi, 
                               edge_contrast=106, num_scans=100, debug=False):
    """
    Measure terminal-to-terminal length (gap between opposing terminals).
    Matches old ChipCap algorithm: scans multiple lines, finds outer edge of left terminal
    and inner edge of right terminal, calculates gap = inner_right - outer_left.
    
    Args:
        image: Input BGR image
        roi: Package ROI (x, y, w, h)
        left_terminal_roi: Left terminal ROI (x, y, w, h)
        right_terminal_roi: Right terminal ROI (x, y, w, h)
        edge_contrast: Contrast threshold from pocket_params (default 106)
        num_scans: Number of scan lines (default 100)
        debug: If True, print debug information
    
    Returns:
        Terminal-to-terminal length in pixels (median gap), or None if failed
    """
    # CRITICAL: Create independent copy to prevent memory corruption
    image = np.copy(image)
    
    x, y, w, h = roi
    ltx, lty, ltw, lth = left_terminal_roi
    rtx, rty, rtw, rth = right_terminal_roi
    
    if debug:
        print(f"[DEBUG] Term-Term Length: Left={left_terminal_roi}, Right={right_terminal_roi}")
    
    # Crop left terminal
    left_crop = image[lty:lty+lth, ltx:ltx+ltw]
    right_crop = image[rty:rty+rth, rtx:rtx+rtw]
    
    if left_crop.size == 0 or right_crop.size == 0:
        if debug:
            print(f"[DEBUG] Term-Term Length: Empty crop")
        return None
    
    left_gray = cv2.cvtColor(left_crop, cv2.COLOR_BGR2GRAY)
    right_gray = cv2.cvtColor(right_crop, cv2.COLOR_BGR2GRAY)
    
    # Try two binarization approaches for both terminals
    def get_best_binary(gray, edge_contrast, debug=False):
        debug = resolve_debug(debug)
        """Choose best binary representation based on white percentage"""
        _, binary_inv = cv2.threshold(gray, edge_contrast, 255, cv2.THRESH_BINARY_INV)
        _, binary_normal = cv2.threshold(gray, edge_contrast, 255, cv2.THRESH_BINARY)
        
        white_inv = (np.sum(binary_inv == 255) / binary_inv.size) * 100 if binary_inv.size > 0 else 0
        white_normal = (np.sum(binary_normal == 255) / binary_normal.size) * 100 if binary_normal.size > 0 else 0
        
        if 10 < white_inv <= 70:
            return binary_inv
        elif 10 < white_normal <= 70:
            return binary_normal
        else:
            return binary_inv if abs(white_inv - 40) < abs(white_normal - 40) else binary_normal
    
    # Get best binary representations for both terminals
    left_binary = get_best_binary(left_gray, edge_contrast, debug)
    right_binary = get_best_binary(right_gray, edge_contrast, debug)
    
    # Apply morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    left_binary = cv2.morphologyEx(left_binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    right_binary = cv2.morphologyEx(right_binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    measurements = []
    skip_factor = max(1, ltw // num_scans)
    
    # Scan horizontally through both terminals
    for col in range(0, min(ltw, rtw), skip_factor):
        # Left terminal: find rightmost edge (outer edge)
        if col < left_binary.shape[1]:
            left_column = left_binary[:, col]
            left_white = np.where(left_column == 255)[0]
            
            if len(left_white) == 0:
                continue
            
            left_outer_edge = left_white[-1]  # rightmost (outer) edge
        else:
            continue
        
        # Right terminal: find leftmost edge (inner edge)
        if col < right_binary.shape[1]:
            right_column = right_binary[:, col]
            right_white = np.where(right_column == 255)[0]
            
            if len(right_white) == 0:
                continue
            
            right_inner_edge = right_white[0]  # leftmost (inner) edge
        else:
            continue
        
        # Gap = distance between right terminal's inner edge and left terminal's outer edge
        # We need to account for the offset between the two ROIs
        roi_offset = rtx - (ltx + ltw)
        gap = (right_inner_edge + roi_offset) - left_outer_edge
        
        if gap > 1:  # Only count positive gaps
            measurements.append(gap)
    
    if len(measurements) < 3:
        if debug:
            print(f"[DEBUG] Term-Term Length: Insufficient measurements ({len(measurements)})")
        return None
    
    median_gap = np.median(measurements)
    
    if debug:
        print(f"[DEBUG] Term-Term Length: Measurements count={len(measurements)}, median={median_gap:.1f}")
        print(f"[DEBUG] Term-Term Length: Min={np.min(measurements)}, Max={np.max(measurements)}, Mean={np.mean(measurements):.1f}")
    
    return int(round(median_gap))


def check_body_width_difference(top_body_width, bottom_body_width, tolerance, debug=False):
    debug = resolve_debug(debug)
    """
    Check if top and bottom body widths differ by more than tolerance.
    
    FOR SPECIAL DEVICES: Used when device body might be asymmetric top-to-bottom.
    Matches old ChipCap system (CCInsp.cpp lines 2116-2131).
    
    Args:
        top_body_width: Body width measured at top edge (pixels)
        bottom_body_width: Body width measured at bottom edge (pixels)
        tolerance: Maximum allowable difference (pixels)
        debug: If True, print debug information
    
    Returns:
        dict with 'difference', 'is_pass', 'tolerance', 'top', 'bottom'
    """
    difference = abs(top_body_width - bottom_body_width)
    
    # Old system uses >= for fail condition (fails if difference >= tolerance)
    is_pass = difference < tolerance
    
    if debug:
        print(f"[DEBUG] Body Width Difference:")
        print(f"  Top Width: {top_body_width:.2f} pixels")
        print(f"  Bottom Width: {bottom_body_width:.2f} pixels")
        print(f"  Difference: {difference:.2f} pixels")
        print(f"  Tolerance: {tolerance:.2f} pixels")
        print(f"  Result: {'PASS' if is_pass else 'FAIL'}")
    
    return {
        'difference': difference,
        'is_pass': is_pass,
        'tolerance': tolerance,
        'top': top_body_width,
        'bottom': bottom_body_width
    }


def check_terminal_length_difference(left_terminal_lengths, right_terminal_lengths, 
                                     tolerance, ignore_start=0, ignore_end=0, debug=False):
    """
    Check if any left/right terminal length pair differs by more than tolerance.
    
    Ensures left/right terminal symmetry across all measurements.
    Matches old ChipCap system (CCInsp.cpp lines 4177-4203).
    
    Args:
        left_terminal_lengths: List of left terminal measurements (pixels)
        right_terminal_lengths: List of right terminal measurements (pixels)
        tolerance: Maximum allowable difference (pixels)
        ignore_start: Number of initial measurements to skip
        ignore_end: Number of final measurements to skip
        debug: If True, print debug information
    
    Returns:
        dict with 'max_difference', 'is_pass', 'tolerance', 'failed_index', 
        'worst_left', 'worst_right'
    """
    max_difference = 0.0
    failed_index = -1
    is_pass = True
    worst_left = 0.0
    worst_right = 0.0
    
    num_measurements = min(len(left_terminal_lengths), len(right_terminal_lengths))
    
    if debug:
        print(f"[DEBUG] Terminal Length Difference Check:")
        print(f"  Total measurements: {num_measurements}")
        print(f"  Ignore start: {ignore_start}, Ignore end: {ignore_end}")
        print(f"  Tolerance: {tolerance:.2f} pixels")
    
    for i in range(num_measurements):
        # Skip ignored measurements
        if i < ignore_start or i >= (num_measurements - ignore_end):
            continue
        
        left_length = left_terminal_lengths[i]
        right_length = right_terminal_lengths[i]
        
        # Skip invalid measurements (old system checks for -1000 or 0)
        if left_length <= 0 or right_length <= 0:
            continue
        
        difference = abs(left_length - right_length)
        
        if difference > max_difference:
            max_difference = difference
            worst_left = left_length
            worst_right = right_length
        
        # Old system uses >= for fail condition (fails if difference >= tolerance)
        if difference >= tolerance:
            is_pass = False
            failed_index = i
            if debug:
                print(f"  [FAIL] Measurement #{i}: Left={left_length:.2f}, Right={right_length:.2f}, Diff={difference:.2f}")
            break
    
    if debug:
        print(f"  Max difference: {max_difference:.2f} pixels")
        print(f"  Worst pair: Left={worst_left:.2f}, Right={worst_right:.2f}")
        print(f"  Result: {'PASS' if is_pass else 'FAIL'}")
        if failed_index >= 0:
            print(f"  Failed at measurement #{failed_index}")
    
    return {
        'max_difference': max_difference,
        'is_pass': is_pass,
        'tolerance': tolerance,
        'failed_index': failed_index,
        'worst_left': worst_left,
        'worst_right': worst_right
    }