"""
Pocket Location Detection
Detects the pocket location in FEED station images.
Implements teach-based search with shift tolerance, contrast thresholding,
body area dust mask filtering, and direction (parallel/non-parallel) validation.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import cv2
import numpy as np


@dataclass
class PocketLocationResult:
    detected: bool
    x: int
    y: int
    width: int
    height: int
    contrast: float
    confidence: float
    message: str
    method: str = "auto"
    angle: float = 0.0
    parallel_mode: str = "none"  # "parallel", "non_parallel", or "none"


def _pp_int(params: Dict, key: str, default: int) -> int:
    raw = params.get(key, default)
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return default
    return default if val == 255 else val


def _pp_float(params: Dict, key: str, default: float) -> float:
    raw = params.get(key, default)
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return default
    return default if val == 255.0 else val


def _pp_bool(params: Dict, key: str, default: bool = False) -> bool:
    val = params.get(key, default)
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ('true', '1', 'yes')
    return bool(val)


def _find_best_contour(binary: np.ndarray) -> Optional[np.ndarray]:
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    return max(contours, key=cv2.contourArea)


def _score_contour(contour: np.ndarray, expected_area: Optional[float], expected_ratio: Optional[float]) -> float:
    area = cv2.contourArea(contour)
    if area <= 0:
        return 0.0
    x, y, w, h = cv2.boundingRect(contour)
    ratio = max(w, h) / max(1, min(w, h))
    score = area
    if expected_area is not None:
        area_ratio = min(area, expected_area) / max(area, expected_area)
        score *= (0.4 + 0.6 * area_ratio)
    if expected_ratio is not None:
        ratio_sim = min(ratio, expected_ratio) / max(ratio, expected_ratio)
        score *= (0.4 + 0.6 * ratio_sim)
    return score


def _apply_body_area_dust_mask(
    image: np.ndarray,
    pocket_location: Tuple[int, int, int, int],
    params: Dict,
    debug: bool = False
) -> np.ndarray:
    """
    Apply body area paper dust mask to filter out dust falling into body area.
    
    Parameters:
    - image: grayscale image
    - pocket_location: (x, y, width, height) of detected pocket
    - params: parameters dict containing:
      - body_area_enable: enable/disable dust mask
      - body_area_tolerance: tolerance for dust filtering (50-70 recommended)
      - body_area_left_offset: offset from left edge of pocket
      - body_area_right_offset: offset from right edge of pocket
    
    Returns masked image with dust filtering applied
    """
    if image is None or image.size == 0:
        return image
    
    # Check if body area dust mask is enabled
    if not _pp_bool(params, "body_area_enable", False):
        return image.copy()
    
    px, py, pw, ph = pocket_location
    tolerance = _pp_int(params, "body_area_tolerance", 70)
    left_offset = _pp_int(params, "body_area_left_offset", 40)
    right_offset = _pp_int(params, "body_area_right_offset", 40)
    
    # Create a copy to avoid modifying original
    masked = image.copy()
    
    # Define body area region (areas on left and right of pocket)
    img_h, img_w = image.shape[:2]
    
    # Left body area: from image left edge to pocket left edge - left_offset
    if px > left_offset:
        left_area_x1 = 0
        left_area_x2 = px - left_offset
        left_area_y1 = max(0, py)
        left_area_y2 = min(img_h, py + ph)
        
        if left_area_x2 > left_area_x1 and left_area_y2 > left_area_y1:
            body_left = masked[left_area_y1:left_area_y2, left_area_x1:left_area_x2]
            mean_val = float(np.mean(body_left))
            
            # Create dust mask based on tolerance
            low = max(0, int(mean_val - tolerance))
            high = min(255, int(mean_val + tolerance))
            dust_mask = cv2.inRange(body_left, low, high)
            
            # Dilate dust mask to include nearby dust
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            dust_mask = cv2.dilate(dust_mask, kernel, iterations=1)
            
            # Apply mask to suppress dust
            masked[left_area_y1:left_area_y2, left_area_x1:left_area_x2] = cv2.inpaint(
                body_left, dust_mask, 3, cv2.INPAINT_TELEA
            )
            
            if debug:
                print(f"[DEBUG] Body area dust mask applied to left area: "
                      f"({left_area_x1},{left_area_y1})-({left_area_x2},{left_area_y2})")
    
    # Right body area: from pocket right edge + right_offset to image right edge
    if px + pw + right_offset < img_w:
        right_area_x1 = px + pw + right_offset
        right_area_x2 = img_w
        right_area_y1 = max(0, py)
        right_area_y2 = min(img_h, py + ph)
        
        if right_area_x2 > right_area_x1 and right_area_y2 > right_area_y1:
            body_right = masked[right_area_y1:right_area_y2, right_area_x1:right_area_x2]
            mean_val = float(np.mean(body_right))
            
            # Create dust mask based on tolerance
            low = max(0, int(mean_val - tolerance))
            high = min(255, int(mean_val + tolerance))
            dust_mask = cv2.inRange(body_right, low, high)
            
            # Dilate dust mask to include nearby dust
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            dust_mask = cv2.dilate(dust_mask, kernel, iterations=1)
            
            # Apply mask to suppress dust
            masked[right_area_y1:right_area_y2, right_area_x1:right_area_x2] = cv2.inpaint(
                body_right, dust_mask, 3, cv2.INPAINT_TELEA
            )
            
            if debug:
                print(f"[DEBUG] Body area dust mask applied to right area: "
                      f"({right_area_x1},{right_area_y1})-({right_area_x2},{right_area_y2})")
    
    return masked


def _validate_direction_angle(
    best_contour: np.ndarray,
    params: Dict,
    debug: bool = False
) -> Tuple[bool, float, str]:
    """
    Validate pocket direction (parallel vs non-parallel chip orientation).
    
    Parameters:
    - best_contour: contour of detected pocket
    - params: parameters dict containing:
      - direction_parallel_enable: enable parallel chip detection
      - direction_non_parallel_enable: enable non-parallel chip detection
      - direction_max_parallel_angle_tol: max angle tolerance for parallel mode (degrees)
    
    Returns:
    - (is_valid: bool, angle: float, mode: str)
    - is_valid: True if angle passes validation
    - angle: computed angle in degrees
    - mode: "parallel", "non_parallel", or "none"
    """
    if best_contour is None:
        return True, 0.0, "none"
    
    # Calculate minimum area rectangle to get angle
    rect = cv2.minAreaRect(best_contour)
    angle = float(rect[2])  # angle in degrees
    
    # Normalize angle to 0-90 range (since 0-180 is same for rectangles)
    if angle < 0:
        angle += 180
    if angle > 90:
        angle = 180 - angle
    # Normalize to 0-45 for stability (old logic treats 90 as 0)
    if angle > 45:
        angle = 90 - angle
    
    # Get direction settings
    parallel_enable = _pp_bool(params, "direction_parallel_enable", False)
    non_parallel_enable = _pp_bool(params, "direction_non_parallel_enable", False)
    max_parallel_angle = _pp_int(params, "direction_max_parallel_angle_tol", 0)
    
    # If neither is enabled, accept all angles
    if not parallel_enable and not non_parallel_enable:
        if debug:
            print(f"[DEBUG] Direction validation: both modes disabled, angle={angle:.2f}°")
        return True, angle, "none"
    
    # Validate based on enabled modes
    mode = "none"
    is_valid = False
    
    if parallel_enable and angle <= max_parallel_angle:
        is_valid = True
        mode = "parallel"
        if debug:
            print(f"[DEBUG] Direction validation PASS (parallel): angle={angle:.2f}°, tolerance={max_parallel_angle}°")
    
    elif non_parallel_enable and angle > max_parallel_angle:
        is_valid = True
        mode = "non_parallel"
        if debug:
            print(f"[DEBUG] Direction validation PASS (non_parallel): angle={angle:.2f}°, tolerance={max_parallel_angle}°")
    
    else:
        if debug:
            print(f"[DEBUG] Direction validation FAIL: angle={angle:.2f}°, tolerance={max_parallel_angle}°, "
                  f"parallel_enable={parallel_enable}, non_parallel_enable={non_parallel_enable}")
    
    return is_valid, angle, mode


def _compute_black_white_thresholds(image: np.ndarray) -> Tuple[int, int]:
    """
    Compute black and white average thresholds using histogram percentiles.
    Mirrors old logic using white/black mean percentage thresholds.
    """
    if image is None or image.size == 0:
        return 0, 255

    hist = cv2.calcHist([image], [0], None, [256], [0, 256]).flatten()
    total = float(np.sum(hist))
    if total <= 0:
        return 0, 255

    # Compute white and black percentages based on image area
    # White percentage and black percentage split ~70/30 based on taught window ratio
    # Use 70% of each as old code does
    white_pct = 70.0
    black_pct = 30.0
    white_mean_pct = white_pct * 0.7
    black_mean_pct = black_pct * 0.7

    # White threshold: from high to low
    white_target = total * (white_mean_pct / 100.0)
    cum = 0.0
    white_avg = 255
    for i in range(255, -1, -1):
        cum += hist[i]
        if cum >= white_target:
            white_avg = i
            break

    # Black threshold: from low to high
    black_target = total * (black_mean_pct / 100.0)
    cum = 0.0
    black_avg = 0
    for i in range(0, 256):
        cum += hist[i]
        if cum >= black_target:
            black_avg = i
            break

    return black_avg, white_avg


def _threshold_percentages() -> Tuple[int, int, int]:
    """
    Old code uses three threshold percentages: 50, 35, 65.
    """
    return 50, 35, 65


def _compute_threshold_value(
    black_avg: int,
    white_avg: int,
    contrast_offset: int,
    threshold_percent: int
) -> int:
    """
    Compute threshold value using old logic:
    nThresVal = contrast_offset + black_avg + (white_avg - black_avg) * percent/100
    Clamped to <= 253.
    """
    base = float(black_avg) + (float(white_avg) - float(black_avg)) * (threshold_percent / 100.0)
    thres = int(round(base + contrast_offset))
    if thres > 253:
        thres = 253
    if thres < 0:
        thres = 0
    return thres


def _apply_post_seal_low_contrast_fallback(
    image: np.ndarray,
    best_contour: Optional[np.ndarray],
    edge_contrast_value: int,
    post_seal_low_contrast: int,
    debug: bool = False
) -> Tuple[bool, Optional[np.ndarray], str]:
    """
    Apply post-seal low contrast fallback when primary detection fails.
    Used on 2nd attempt when global contrast setting failed for first time.
    
    Parameters:
    - image: grayscale image
    - best_contour: result from primary detection
    - edge_contrast_value: primary contrast value (0-255)
    - post_seal_low_contrast: fallback contrast value when primary fails
    - debug: enable debug output
    
    Returns: (fallback_used, new_contour, message)
    """
    # If primary detection succeeded, no fallback needed
    if best_contour is not None:
        return False, best_contour, "Primary detection successful"
    
    # If fallback contrast value is disabled (255), cannot fallback
    if post_seal_low_contrast >= 255:
        return False, None, "Post-seal low contrast fallback disabled"
    
    if image is None or image.size == 0:
        return False, None, "Invalid image for fallback"
    
    # Apply lower contrast for post-seal situation using histogram-based thresholding
    fallback_contrast = max(0, min(255, post_seal_low_contrast))
    black_avg, white_avg = _compute_black_white_thresholds(image)
    percents = _threshold_percentages()

    fallback_contour = None
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    for pct in percents:
        thres = _compute_threshold_value(black_avg, white_avg, fallback_contrast, pct)
        _, bin_mask = cv2.threshold(image, thres, 255, cv2.THRESH_BINARY)
        bin_mask = cv2.morphologyEx(bin_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        inv_mask = cv2.bitwise_not(bin_mask)
        inv_mask = cv2.morphologyEx(inv_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        dark_contour = _find_best_contour(inv_mask)
        light_contour = _find_best_contour(bin_mask)

        if dark_contour is not None and light_contour is not None:
            dark_area = cv2.contourArea(dark_contour)
            light_area = cv2.contourArea(light_contour)
            fallback_contour = dark_contour if dark_area >= light_area else light_contour
        elif dark_contour is not None:
            fallback_contour = dark_contour
        elif light_contour is not None:
            fallback_contour = light_contour

        if fallback_contour is not None:
            break
    
    if fallback_contour is not None:
        if debug:
            print(f"[DEBUG] Post-seal low contrast fallback successful: "
                  f"primary_contrast={edge_contrast_value}, fallback_contrast={fallback_contrast}")
        return True, fallback_contour, "Post-seal low contrast fallback used"
    
    if debug:
        print(f"[DEBUG] Post-seal low contrast fallback failed: "
              f"no contour found with contrast={fallback_contrast}")
    
    return False, None, "Post-seal low contrast fallback failed"


def _apply_paper_dust_mask(
    image: np.ndarray,
    pocket_location: Tuple[int, int, int, int],
    params: Dict,
    debug: bool = False
) -> np.ndarray:
    """
    Apply paper dust mask to filter paper dust artifacts.
    User can flexibly mask dust from left & right or top & bottom.
    
    Parameters:
    - image: grayscale image
    - pocket_location: (x, y, width, height) of pocket
    - params: parameters dict containing:
      - paper_dust_left_right: mask left and right edges
      - paper_dust_top_bottom: mask top and bottom edges
      - paper_dust_contrast_plus: use additional contrast to enhance dust filtering
    - debug: enable debug output
    
    Returns: masked image with dust filtered
    """
    if image is None or image.size == 0:
        return image
    
    # Check if paper dust mask is enabled
    left_right_enable = _pp_bool(params, "paper_dust_left_right", False)
    top_bottom_enable = _pp_bool(params, "paper_dust_top_bottom", False)
    contrast_plus = _pp_bool(params, "paper_dust_contrast_plus", False)
    
    if not (left_right_enable or top_bottom_enable):
        return image
    
    x, y, w, h = pocket_location
    masked_image = image.copy()
    
    # Dust mask width/height - fixed offset for dust filtering
    dust_offset = 20  # pixels to filter
    
    # Mask left and right edges
    if left_right_enable:
        # Left dust mask
        left_x = max(0, x - dust_offset)
        left_w = min(dust_offset, x)
        if left_w > 0:
            masked_image[max(0, y-dust_offset):min(image.shape[0], y+h+dust_offset), 
                        left_x:left_x+left_w] = np.mean(masked_image)
        
        # Right dust mask
        right_x = min(image.shape[1], x + w)
        right_w = min(dust_offset, image.shape[1] - right_x)
        if right_w > 0:
            masked_image[max(0, y-dust_offset):min(image.shape[0], y+h+dust_offset),
                        right_x:right_x+right_w] = np.mean(masked_image)
        
        if debug:
            print(f"[DEBUG] Paper dust mask applied: left & right edges")
    
    # Mask top and bottom edges
    if top_bottom_enable:
        # Top dust mask
        top_y = max(0, y - dust_offset)
        top_h = min(dust_offset, y)
        if top_h > 0:
            masked_image[top_y:top_y+top_h,
                        max(0, x-dust_offset):min(image.shape[1], x+w+dust_offset)] = np.mean(masked_image)
        
        # Bottom dust mask
        bottom_y = min(image.shape[0], y + h)
        bottom_h = min(dust_offset, image.shape[0] - bottom_y)
        if bottom_h > 0:
            masked_image[bottom_y:bottom_y+bottom_h,
                        max(0, x-dust_offset):min(image.shape[1], x+w+dust_offset)] = np.mean(masked_image)
        
        if debug:
            print(f"[DEBUG] Paper dust mask applied: top & bottom edges")
    
    # Optional: enhance dust filtering with additional contrast
    if contrast_plus:
        # Apply slight contrast adjustment to better separate dust from background
        alpha = 1.1  # contrast factor
        beta = 5    # brightness adjustment
        masked_image = cv2.convertScaleAbs(masked_image, alpha=alpha, beta=beta)
        masked_image = np.clip(masked_image, 0, 255).astype(np.uint8)
        
        if debug:
            print(f"[DEBUG] Paper dust mask enhanced with contrast boost")
    
    return masked_image


def _apply_white_line_mask(
    image: np.ndarray,
    mask_size: int,
    debug: bool = False
) -> np.ndarray:
    """
    Mask thin white line residue using a small top-hat filter.
    Maximum recommended mask size is 3.
    """
    if image is None or image.size == 0:
        return image

    size = int(mask_size) if mask_size is not None else 0
    if size <= 0:
        return image
    if size > 3:
        size = 3

    k = size * 2 + 1
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (k, 1))
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, k))

    top_hat_h = cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel_h)
    top_hat_v = cv2.morphologyEx(image, cv2.MORPH_TOPHAT, kernel_v)
    top_hat = cv2.max(top_hat_h, top_hat_v)

    line_mask = top_hat > 0
    if not np.any(line_mask):
        return image

    blurred = cv2.medianBlur(image, 3)
    masked = image.copy()
    masked[line_mask] = blurred[line_mask]

    if debug:
        print(f"[DEBUG] White line mask applied (size={size})")

    return masked


def _build_outer_stain_mask(
    image_shape: Tuple[int, int],
    pocket_location: Tuple[int, int, int, int],
    widths: Tuple[int, int, int, int],
    offsets: Tuple[int, int, int, int]
) -> np.ndarray:
    h, w = image_shape
    x, y, pw, ph = pocket_location
    w_left, w_top, w_right, w_bottom = widths
    o_left, o_top, o_right, o_bottom = offsets

    mask = np.zeros((h, w), dtype=np.uint8)

    # Left band
    if w_left > 0:
        x1 = max(0, x - o_left - w_left)
        x2 = max(0, x - o_left)
        y1 = max(0, y - w_top)
        y2 = min(h, y + ph + w_bottom)
        if x2 > x1:
            mask[y1:y2, x1:x2] = 255

    # Right band
    if w_right > 0:
        x1 = min(w, x + pw + o_right)
        x2 = min(w, x + pw + o_right + w_right)
        y1 = max(0, y - w_top)
        y2 = min(h, y + ph + w_bottom)
        if x2 > x1:
            mask[y1:y2, x1:x2] = 255

    # Top band
    if w_top > 0:
        y1 = max(0, y - o_top - w_top)
        y2 = max(0, y - o_top)
        x1 = max(0, x - w_left)
        x2 = min(w, x + pw + w_right)
        if y2 > y1:
            mask[y1:y2, x1:x2] = 255

    # Bottom band
    if w_bottom > 0:
        y1 = min(h, y + ph + o_bottom)
        y2 = min(h, y + ph + o_bottom + w_bottom)
        x1 = max(0, x - w_left)
        x2 = min(w, x + pw + w_right)
        if y2 > y1:
            mask[y1:y2, x1:x2] = 255

    return mask


def check_outer_pocket_stain(
    image: np.ndarray,
    pocket_location: Tuple[int, int, int, int],
    pocket_params: Optional[Dict] = None,
    debug: bool = False
) -> Tuple[bool, Dict]:
    """
    Inspect black/white stains outside the pocket area.
    """
    params = pocket_params or {}
    if image is None or image.size == 0:
        return True, {"messages": ["Invalid image"], "pass": True}

    black_enable = _pp_bool(params, "outer_stain_black", False)
    white_enable = _pp_bool(params, "outer_stain_white", False)

    if not (black_enable or white_enable):
        return True, {"messages": ["Outer stain inspection disabled"], "pass": True}

    contrast_min = _pp_int(params, "outer_stain_contrast_min", 255)
    contrast_max = _pp_int(params, "outer_stain_contrast_max", 255)
    min_area = _pp_int(params, "outer_stain_min_area", 0)
    min_sq = _pp_int(params, "outer_stain_min_sq_size", 0)

    widths = (
        _pp_int(params, "inspect_width_left", 0),
        _pp_int(params, "inspect_width_top", 0),
        _pp_int(params, "inspect_width_right", 0),
        _pp_int(params, "inspect_width_bottom", 0),
    )
    offsets = (
        _pp_int(params, "inspect_offset_left", 0),
        _pp_int(params, "inspect_offset_top", 0),
        _pp_int(params, "inspect_offset_right", 0),
        _pp_int(params, "inspect_offset_bottom", 0),
    )

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # White line mask (reduce paper cut line residue)
    if _pp_bool(params, "white_line_mask_enable", False):
        mask_size = _pp_int(params, "white_line_mask_size", 0)
        gray = _apply_white_line_mask(gray, mask_size, debug=debug)

    mask = _build_outer_stain_mask(gray.shape[:2], pocket_location, widths, offsets)
    if not np.any(mask):
        return True, {"messages": ["Outer stain mask empty"], "pass": True}

    messages = []
    is_valid = True

    def _check_blob(binary: np.ndarray, label: str) -> None:
        nonlocal is_valid
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area > 0 and area < min_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            if min_sq > 0 and (w < min_sq or h < min_sq):
                continue
            is_valid = False
            messages.append(f"Outer stain {label}: area={int(area)} size={w}x{h}")
            if debug:
                print(f"[FAIL] Outer stain {label}: area={int(area)} size={w}x{h}")

    if black_enable and contrast_min < 255:
        black_mask = (gray < contrast_min).astype(np.uint8) * 255
        black_mask = cv2.bitwise_and(black_mask, mask)
        _check_blob(black_mask, "black")

    if white_enable and contrast_max < 255:
        white_mask = (gray > contrast_max).astype(np.uint8) * 255
        white_mask = cv2.bitwise_and(white_mask, mask)
        _check_blob(white_mask, "white")

    if is_valid:
        messages.append("Outer stain inspection OK")
        if debug:
            print("[PASS] Outer stain inspection OK")

    return is_valid, {
        "pass": is_valid,
        "messages": messages,
        "black_enable": black_enable,
        "white_enable": white_enable,
    }


def check_emboss_tape_pickup(
    image: np.ndarray,
    pocket_location: Tuple[int, int, int, int],
    package_location: Tuple[int, int, int, int],
    pocket_params: Optional[Dict] = None,
    debug: bool = False
) -> Tuple[bool, Dict]:
    """
    Emboss tape pickup inspection based on contrast difference between pocket and package.
    """
    params = pocket_params or {}
    contrast = _pp_int(params, "emboss_tape_contrast", 255)
    left_offset = _pp_int(params, "emboss_tape_left_search_offset", 0)

    if contrast == 255:
        return True, {"messages": ["Emboss tape pickup disabled"], "pass": True}

    if image is None or image.size == 0:
        return True, {"messages": ["Invalid image"], "pass": True}

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    px, py, pw, ph = pocket_location
    gx, gy, gw, gh = package_location

    gx = max(0, gx + left_offset)
    gw = max(1, gw - left_offset)

    pocket_roi = gray[py:py + ph, px:px + pw]
    pkg_roi = gray[gy:gy + gh, gx:gx + gw]

    pocket_mean = float(np.mean(pocket_roi)) if pocket_roi.size > 0 else 0.0
    pkg_mean = float(np.mean(pkg_roi)) if pkg_roi.size > 0 else 0.0
    diff = abs(pocket_mean - pkg_mean)

    is_valid = diff >= contrast
    if debug:
        print(f"[DEBUG] Emboss pickup: pocket_mean={pocket_mean:.1f}, pkg_mean={pkg_mean:.1f}, diff={diff:.1f}, contrast={contrast}")

    if not is_valid:
        return False, {
            "pass": False,
            "messages": [f"Emboss pickup contrast {diff:.1f} < {contrast}"],
            "pocket_mean": pocket_mean,
            "pkg_mean": pkg_mean,
            "diff": diff,
        }

    return True, {
        "pass": True,
        "messages": [f"Emboss pickup contrast OK ({diff:.1f} >= {contrast})"],
        "pocket_mean": pocket_mean,
        "pkg_mean": pkg_mean,
        "diff": diff,
    }


def _sealing_roi(
    pocket_location: Tuple[int, int, int, int],
    width_left: int,
    width_top: int,
    width_right: int,
    width_bottom: int,
    offset_left: int,
    offset_right: int,
    image_shape: Tuple[int, int]
) -> Tuple[Tuple[int, int, int, int], Tuple[int, int, int, int]]:
    x, y, w, h = pocket_location
    img_h, img_w = image_shape

    left_x1 = max(0, x - offset_left - width_left)
    left_x2 = max(0, x - offset_left)
    right_x1 = min(img_w, x + w + offset_right)
    right_x2 = min(img_w, x + w + offset_right + width_right)

    y1 = max(0, y - width_top)
    y2 = min(img_h, y + h + width_bottom)

    left = (left_x1, y1, max(0, left_x2 - left_x1), max(0, y2 - y1))
    right = (right_x1, y1, max(0, right_x2 - right_x1), max(0, y2 - y1))
    return left, right


def check_sealing_stain(
    image: np.ndarray,
    pocket_location: Tuple[int, int, int, int],
    pocket_params: Optional[Dict] = None,
    debug: bool = False
) -> Tuple[bool, Dict]:
    """
    Sealing stain inspection on left and right sides.
    """
    params = pocket_params or {}
    if image is None or image.size == 0:
        return True, {"messages": ["Invalid image"], "pass": True}

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    contrast_left = _pp_int(params, "sealing_stain_contrast_left", 255)
    contrast_right = _pp_int(params, "sealing_stain_contrast_right", 255)
    filter_contrast = _pp_int(params, "sealing_stain_filter_contrast", 0)
    min_area = _pp_int(params, "sealing_stain_min_area", 0)
    min_sq = _pp_int(params, "sealing_stain_min_sq_size", 0)

    width_left = _pp_int(params, "sealing_width_left", 0)
    width_top = _pp_int(params, "sealing_width_top", 0)
    width_right = _pp_int(params, "sealing_width_right", 0)
    width_bottom = _pp_int(params, "sealing_width_bottom", 0)
    offset_left = _pp_int(params, "sealing_offset_left", 0)
    offset_right = _pp_int(params, "sealing_offset_right", 0)

    if contrast_left == 255 and contrast_right == 255:
        return True, {"messages": ["Sealing stain inspection disabled"], "pass": True}

    if filter_contrast > 0 and filter_contrast < 255:
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

    left_roi, right_roi = _sealing_roi(
        pocket_location,
        width_left,
        width_top,
        width_right,
        width_bottom,
        offset_left,
        offset_right,
        gray.shape[:2]
    )

    def _check_side(roi: Tuple[int, int, int, int], contrast: int, label: str) -> Optional[str]:
        if contrast >= 255:
            return None
        rx, ry, rw, rh = roi
        if rw <= 0 or rh <= 0:
            return None
        roi_img = gray[ry:ry + rh, rx:rx + rw]
        stain_mask = (roi_img < contrast).astype(np.uint8) * 255
        contours, _ = cv2.findContours(stain_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area > 0 and area < min_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            if min_sq > 0 and (w < min_sq or h < min_sq):
                continue
            return f"{label} sealing stain area={int(area)} size={w}x{h}"
        return None

    messages = []
    is_valid = True

    left_fail = _check_side(left_roi, contrast_left, "Left")
    if left_fail:
        is_valid = False
        messages.append(left_fail)
        if debug:
            print(f"[FAIL] {left_fail}")

    right_fail = _check_side(right_roi, contrast_right, "Right")
    if right_fail:
        is_valid = False
        messages.append(right_fail)
        if debug:
            print(f"[FAIL] {right_fail}")

    if is_valid:
        messages.append("Sealing stain OK")
        if debug:
            print("[PASS] Sealing stain OK")

    return is_valid, {"pass": is_valid, "messages": messages}


def check_sealing_stain2(
    image: np.ndarray,
    pocket_location: Tuple[int, int, int, int],
    pocket_params: Optional[Dict] = None,
    debug: bool = False
) -> Tuple[bool, Dict]:
    """
    Sealing stain 2 inspection (alternate contrast and ROI).
    """
    params = pocket_params or {}
    contrast = _pp_int(params, "sealing_stain2_contrast", 255)
    min_area = _pp_int(params, "sealing_stain2_min_area", 0)
    min_sq = _pp_int(params, "sealing_stain2_min_sq_size", 0)

    if contrast == 255:
        return True, {"messages": ["Sealing stain 2 disabled"], "pass": True}

    if image is None or image.size == 0:
        return True, {"messages": ["Invalid image"], "pass": True}

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    width_left = _pp_int(params, "sealing2_width_left", 0)
    width_top = _pp_int(params, "sealing2_width_top", 0)
    width_right = _pp_int(params, "sealing2_width_right", 0)
    width_bottom = _pp_int(params, "sealing2_width_bottom", 0)
    offset_left = 0
    offset_right = 0

    left_roi, right_roi = _sealing_roi(
        pocket_location,
        width_left,
        width_top,
        width_right,
        width_bottom,
        offset_left,
        offset_right,
        gray.shape[:2]
    )

    messages = []
    is_valid = True

    for label, roi in [("Left", left_roi), ("Right", right_roi)]:
        rx, ry, rw, rh = roi
        if rw <= 0 or rh <= 0:
            continue
        roi_img = gray[ry:ry + rh, rx:rx + rw]
        stain_mask = (roi_img < contrast).astype(np.uint8) * 255
        contours, _ = cv2.findContours(stain_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area > 0 and area < min_area:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            if min_sq > 0 and (w < min_sq or h < min_sq):
                continue
            is_valid = False
            msg = f"{label} sealing stain2 area={int(area)} size={w}x{h}"
            messages.append(msg)
            if debug:
                print(f"[FAIL] {msg}")

    if is_valid:
        messages.append("Sealing stain 2 OK")
        if debug:
            print("[PASS] Sealing stain 2 OK")

    return is_valid, {"pass": is_valid, "messages": messages}


def check_sealing_shift(
    image: np.ndarray,
    pocket_location: Tuple[int, int, int, int],
    pocket_params: Optional[Dict] = None,
    package_location: Optional[Tuple[int, int, int, int]] = None,
    debug: bool = False
) -> Tuple[bool, Dict]:
    """
    Sealing shift inspection to detect shift of sealing mark left/right or top/bottom.
    
    The sealing consists of:
    - Cover tape (transparent cover on white paper carrier)
    - Sealing mark (white)
    - Pitch holes (for reference)
    
    Detects:
    - Black-to-white scan: for emboss tape (detects dark-to-light edge)
    - White-to-black scan: for paper carrier tape (detects light-to-dark edge)
    - Hole reference: validates sealing hasn't covered the pitch holes
    """
    params = pocket_params or {}
    enable = _pp_bool(params, "sealing_shift_enable", False)
    
    if not enable:
        return True, {"messages": ["Sealing shift inspection disabled"], "pass": True}
    
    if image is None or image.size == 0:
        return True, {"messages": ["Invalid image"], "pass": True}
    
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    x, y, w, h = pocket_location
    messages = []
    is_valid = True
    
    # Tape range (cover_tape_min/max define grayscale range of sealing mark)
    cover_tape_min = _pp_int(params, "sealing_shift_cover_tape_min", 59)
    cover_tape_max = _pp_int(params, "sealing_shift_cover_tape_max", 435)
    mark_min = _pp_int(params, "sealing_shift_mark_min", 190)
    mark_max = _pp_int(params, "sealing_shift_mark_max", 306)
    
    # Contrast thresholds for scan types
    contrast_primary = _pp_int(params, "sealing_shift_contrast_primary", 245)
    contrast_secondary = _pp_int(params, "sealing_shift_contrast_secondary", 180)
    
    # Tolerance for shift position
    tol_pos = _pp_int(params, "sealing_shift_tolerance_pos", 25)
    tol_neg = _pp_int(params, "sealing_shift_tolerance_neg", 25)
    
    # Search offsets to adjust inspection area
    left_search_offset = _pp_int(params, "sealing_shift_left_search_offset", 40)
    top_search_offset = _pp_int(params, "sealing_shift_top_search_offset", 90)
    
    # Check if parameters are disabled (value = 255)
    if cover_tape_min == 255 or cover_tape_max == 255:
        if debug:
            print("[DEBUG] Sealing shift tape range disabled")
        return True, {"messages": ["Sealing shift parameters disabled"], "pass": True}
    
    # Black-to-white scan (emboss tape detection)
    check_bw = _pp_bool(params, "sealing_shift_black_to_white_scar", False)
    if check_bw:
        # Scan for dark-to-light transition (black to white)
        # Detects sealing mark on emboss tape
        scan_roi = gray[y:y+h, max(0, x-left_search_offset):min(gray.shape[1], x+w+left_search_offset)]
        if scan_roi.size > 0:
            # Look for transition from dark (<100) to light (>200)
            dark_mask = (scan_roi < 100).astype(np.uint8)
            light_mask = (scan_roi > 200).astype(np.uint8)
            
            # If both dark and light regions exist in sealing area, mark as valid
            has_transition = (dark_mask.sum() > 0) and (light_mask.sum() > 0)
            if not has_transition:
                is_valid = False
                messages.append("Black-to-white scan: no sealing mark detected (emboss tape)")
                if debug:
                    print("[FAIL] No black-to-white transition detected")
            else:
                messages.append("Black-to-white scan OK")
                if debug:
                    print("[PASS] Black-to-white transition detected")
    
    # White-to-black scan (paper carrier tape detection)
    check_wb = _pp_bool(params, "sealing_shift_white_to_black_scar", False)
    if check_wb:
        # Scan for light-to-dark transition (white to black)
        # Detects sealing on paper carrier tape
        scan_roi = gray[y:y+h, max(0, x-left_search_offset):min(gray.shape[1], x+w+left_search_offset)]
        if scan_roi.size > 0:
            # Look for transition from light (>200) to dark (<100)
            light_mask = (scan_roi > 200).astype(np.uint8)
            dark_mask = (scan_roi < 100).astype(np.uint8)
            
            # If both light and dark regions exist in sealing area, mark as valid
            has_transition = (light_mask.sum() > 0) and (dark_mask.sum() > 0)
            if not has_transition:
                is_valid = False
                messages.append("White-to-black scan: no sealing mark detected (paper tape)")
                if debug:
                    print("[FAIL] No white-to-black transition detected")
            else:
                messages.append("White-to-black scan OK")
                if debug:
                    print("[PASS] White-to-black transition detected")
    
    # Hole reference check (if enabled, verify sealing doesn't cover pitch holes)
    check_hole = _pp_bool(params, "sealing_shift_hole_ref", False)
    if check_hole:
        hole_contrast = _pp_int(params, "sealing_shift_hole_contrast", 123)
        hole_min_width = _pp_int(params, "sealing_shift_hole_min_width", 102)
        hole_offset = _pp_int(params, "sealing_shift_hole_offset", 15)
        hole_edge_count = _pp_int(params, "sealing_shift_hole_edge_count", 50)
        
        if hole_contrast < 255:
            # Search for holes in the sealing area
            # Holes appear as dark areas (shadows) in the sealing band
            hole_search_y = max(0, y - hole_offset)
            hole_search_h = min(gray.shape[0], h + 2*hole_offset) - hole_search_y
            hole_search_roi = gray[hole_search_y:hole_search_y+hole_search_h, 
                                   max(0, x-left_search_offset):min(gray.shape[1], x+w+left_search_offset)]
            
            if hole_search_roi.size > 0:
                # Detect dark spots (holes)
                hole_mask = (hole_search_roi < hole_contrast).astype(np.uint8) * 255
                contours, _ = cv2.findContours(hole_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                hole_count = 0
                for cnt in contours:
                    x_hole, y_hole, w_hole, h_hole = cv2.boundingRect(cnt)
                    if w_hole >= hole_min_width:
                        hole_count += 1
                
                # Verify that holes are detected (sealing shouldn't cover them completely)
                if hole_count >= hole_edge_count // 100:  # At least some holes should be visible
                    messages.append(f"Hole reference OK: {hole_count} holes detected")
                    if debug:
                        print(f"[PASS] Hole reference: {hole_count} holes visible")
                else:
                    is_valid = False
                    messages.append(f"Hole reference FAIL: only {hole_count} holes detected (expect coverage)")
                    if debug:
                        print(f"[FAIL] Hole reference: {hole_count} holes (< {hole_edge_count})")
    
    if is_valid and not messages:
        messages.append("Sealing shift OK")
    
    return is_valid, {"pass": is_valid, "messages": messages}


def check_hole_side_shift(
    image: np.ndarray,
    pocket_location: Tuple[int, int, int, int],
    pocket_params: Optional[Dict] = None,
    debug: bool = False
) -> Tuple[bool, Dict]:
    """
    Hole side shift inspection - detect pitch hole position shift.
    
    If there is no sealing shift, the pitch hole should not be covered.
    Detects movement more than the min width as failure.
    
    Parameters:
    - Contrast: gray level to see pitch hole dimension
    - Min Width: system automatizes hole width value (fail if exceeded)
    - Offset: search hole offset from outer round edge to inner round
    - Edge Count: edge points for finding thin shift defects (fail if > threshold)
    """
    params = pocket_params or {}
    enable = _pp_bool(params, "sealing_shift_hole_ref", False)
    
    if not enable:
        return True, {"messages": ["Hole side shift inspection disabled"], "pass": True}
    
    if image is None or image.size == 0:
        return True, {"messages": ["Invalid image"], "pass": True}
    
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    x, y, w, h = pocket_location
    messages = []
    is_valid = True
    
    # Hole detection parameters
    hole_contrast = _pp_int(params, "sealing_shift_hole_contrast", 123)
    hole_min_width = _pp_int(params, "sealing_shift_hole_min_width", 102)
    hole_offset = _pp_int(params, "sealing_shift_hole_offset", 15)
    hole_edge_count = _pp_int(params, "sealing_shift_hole_edge_count", 50)
    
    if hole_contrast == 255:
        return True, {"messages": ["Hole side shift parameters disabled"], "pass": True}
    
    # Search for pitch holes in sealing area
    # Holes appear as dark circular areas in the tape
    hole_search_y = max(0, y - hole_offset)
    hole_search_h = min(gray.shape[0], y + h + hole_offset) - hole_search_y
    hole_search_x = max(0, x - hole_offset)
    hole_search_w = min(gray.shape[1], x + w + hole_offset) - hole_search_x
    
    if hole_search_h <= 0 or hole_search_w <= 0:
        return True, {"messages": ["Hole search area invalid"], "pass": True}
    
    hole_search_roi = gray[hole_search_y:hole_search_y+hole_search_h, 
                           hole_search_x:hole_search_x+hole_search_w]
    
    # Create mask for dark areas (holes)
    hole_mask = (hole_search_roi < hole_contrast).astype(np.uint8) * 255
    
    # Find hole contours
    contours, _ = cv2.findContours(hole_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    holes_detected = []
    edge_points_total = 0
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        x_hole, y_hole, w_hole, h_hole = cv2.boundingRect(cnt)
        
        # Count edge points (contour length approximation)
        edge_points = cv2.arcLength(cnt, True)
        
        # Check if hole dimensions exceed minimum width threshold
        if w_hole > hole_min_width or h_hole > hole_min_width:
            is_valid = False
            msg = f"Hole side shift: hole size {w_hole}x{h_hole} exceeds min_width={hole_min_width}"
            messages.append(msg)
            if debug:
                print(f"[FAIL] {msg}")
        else:
            holes_detected.append({
                'x': x_hole + hole_search_x,
                'y': y_hole + hole_search_y,
                'width': w_hole,
                'height': h_hole,
                'area': area,
                'edge_points': int(edge_points)
            })
            edge_points_total += int(edge_points)
    
    # Check edge count (sum of all edge points in offset region)
    # If edge count exceeds threshold, indicates thin shift defects
    if hole_edge_count < 255 and edge_points_total > hole_edge_count:
        is_valid = False
        msg = f"Hole side shift: edge count {edge_points_total} exceeds threshold {hole_edge_count}"
        messages.append(msg)
        if debug:
            print(f"[FAIL] {msg}")
    
    # Report valid holes detected
    if holes_detected:
        msg = f"Hole side shift: {len(holes_detected)} holes detected, edge_count={edge_points_total}"
        messages.append(msg)
        if debug:
            print(f"[INFO] {msg}")
    
    if is_valid and not messages:
        messages.append("Hole side shift OK")
    
    return is_valid, {
        "pass": is_valid,
        "messages": messages,
        "holes_detected": len(holes_detected),
        "edge_count": edge_points_total,
        "holes": holes_detected
    }


def check_sealing_distance_center(
    image: np.ndarray,
    pocket_location: Tuple[int, int, int, int],
    pocket_params: Optional[Dict] = None,
    debug: bool = False
) -> Tuple[bool, Dict]:
    """
    Sealing distance measurement from center point (alternative to hole reference).
    
    When hole reference is disabled, measures sealing dimensions from the center point
    to the edges of left sealing. Any movement more than the setting value is 
    considered as sealing shift to the left (fail).
    
    Parameters:
    - contrast_primary: to identify sealing mark edges
    - tolerance_pos/neg: tolerance for left/right side of sealing tape
    - left_search_offset: distance from center to search for sealing edge
    - top_search_offset: vertical search offset from center
    """
    params = pocket_params or {}
    
    # Check if hole reference is enabled (if yes, this measurement is disabled)
    use_hole_ref = _pp_bool(params, "sealing_shift_hole_ref", False)
    if use_hole_ref:
        return True, {"messages": ["Center-point measurement disabled (using hole reference)"], "pass": True}
    
    if image is None or image.size == 0:
        return True, {"messages": ["Invalid image"], "pass": True}
    
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    x, y, w, h = pocket_location
    messages = []
    is_valid = True
    
    # Sealing measurement parameters
    contrast_primary = _pp_int(params, "sealing_shift_contrast_primary", 245)
    tol_pos = _pp_int(params, "sealing_shift_tolerance_pos", 25)
    tol_neg = _pp_int(params, "sealing_shift_tolerance_neg", 25)
    left_search_offset = _pp_int(params, "sealing_shift_left_search_offset", 40)
    top_search_offset = _pp_int(params, "sealing_shift_top_search_offset", 90)
    
    if contrast_primary == 255:
        return True, {"messages": ["Center-point measurement disabled"], "pass": True}
    
    # Find center point of pocket
    center_x = x + w // 2
    center_y = y + h // 2
    
    # Search for sealing edges from center point
    # Look for transitions from sealing (light) to background (dark)
    
    # Left sealing edge search
    left_search_start = max(0, center_x - left_search_offset)
    left_search_end = center_x
    left_stripe = gray[max(0, center_y-top_search_offset):min(gray.shape[0], center_y+top_search_offset), 
                       left_search_start:left_search_end]
    
    # Right sealing edge search
    right_search_start = center_x
    right_search_end = min(gray.shape[1], center_x + left_search_offset)
    right_stripe = gray[max(0, center_y-top_search_offset):min(gray.shape[0], center_y+top_search_offset), 
                        right_search_start:right_search_end]
    
    measurements = {}
    
    # Measure left sealing edge distance from center
    if left_stripe.size > 0:
        # Find edge by looking for dark-to-light transition from left
        left_mean = left_stripe.mean()
        light_mask = (left_stripe > contrast_primary).astype(np.uint8)
        light_pixels = light_mask.sum(axis=0)  # Sum along height
        
        if light_pixels.sum() > 0:
            # Find leftmost column with light pixels (sealing edge)
            edge_col = np.where(light_pixels > 0)[0]
            if len(edge_col) > 0:
                left_distance = len(left_stripe[0]) - edge_col[0]
                measurements['left_distance'] = left_distance
                msg = f"Left sealing distance: {left_distance}px (tolerance: ±{tol_pos}px)"
                messages.append(msg)
                if debug:
                    print(f"[INFO] {msg}")
    
    # Measure right sealing edge distance from center
    if right_stripe.size > 0:
        right_mean = right_stripe.mean()
        light_mask = (right_stripe > contrast_primary).astype(np.uint8)
        light_pixels = light_mask.sum(axis=0)  # Sum along height
        
        if light_pixels.sum() > 0:
            # Find rightmost column with light pixels (sealing edge)
            edge_col = np.where(light_pixels > 0)[0]
            if len(edge_col) > 0:
                right_distance = edge_col[-1]
                measurements['right_distance'] = right_distance
                msg = f"Right sealing distance: {right_distance}px (tolerance: ±{tol_neg}px)"
                messages.append(msg)
                if debug:
                    print(f"[INFO] {msg}")
    
    # Validate distances against tolerances
    if 'left_distance' in measurements:
        if measurements['left_distance'] > tol_pos:
            is_valid = False
            msg = f"Left sealing shift exceeds tolerance: {measurements['left_distance']} > {tol_pos}"
            messages.append(msg)
            if debug:
                print(f"[FAIL] {msg}")
    
    if 'right_distance' in measurements:
        if measurements['right_distance'] > tol_neg:
            is_valid = False
            msg = f"Right sealing shift exceeds tolerance: {measurements['right_distance']} > {tol_neg}"
            messages.append(msg)
            if debug:
                print(f"[FAIL] {msg}")
    
    if is_valid and not measurements:
        messages.append("Center-point sealing distance: no sealing edges detected")
    
    if is_valid and measurements:
        messages.append("Sealing distance within tolerance")
    
    return is_valid, {
        "pass": is_valid,
        "messages": messages,
        "measurements": measurements
    }


def check_bottom_dent_inspection(
    image: np.ndarray,
    pocket_location: Tuple[int, int, int, int],
    pocket_params: Optional[Dict] = None,
    debug: bool = False
) -> Tuple[bool, Dict]:
    """
    Bottom dent inspection - detects dents in emboss tape at bottom station.
    
    Inspects for emboss tape denting, which indicates loss of tight control.
    
    Parameters:
    - contrast: minimum gray level to detect dent as defect
    - min_area: maximum acceptable dent defect area
    - min_sq_size: maximum acceptable dent width/height
    - offset_left/right/top/bottom: inspection area offset margins
    - search_offset_x/y: offset from pocket center for search area
    """
    params = pocket_params or {}
    enable = _pp_bool(params, "bottom_dent_enable", False)
    
    if not enable:
        return True, {"messages": ["Bottom dent inspection disabled"], "pass": True}
    
    if image is None or image.size == 0:
        return True, {"messages": ["Invalid image"], "pass": True}
    
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    x, y, w, h = pocket_location
    messages = []
    is_valid = True
    
    # Bottom dent parameters
    contrast = _pp_int(params, "bottom_dent_contrast", 255)
    min_area = _pp_int(params, "bottom_dent_min_area", 0)
    min_sq_size = _pp_int(params, "bottom_dent_min_sq_size", 0)
    offset_left = _pp_int(params, "bottom_dent_offset_left", 0)
    offset_right = _pp_int(params, "bottom_dent_offset_right", 0)
    offset_top = _pp_int(params, "bottom_dent_offset_top", 0)
    offset_bottom = _pp_int(params, "bottom_dent_offset_bottom", 0)
    search_offset_x = _pp_int(params, "bottom_dent_search_offset_x", 0)
    search_offset_y = _pp_int(params, "bottom_dent_search_offset_y", 0)
    
    if contrast == 255:
        return True, {"messages": ["Bottom dent parameters disabled"], "pass": True}
    
    # Build search ROI with offsets
    # Bottom dent inspection focuses on the bottom area of the emboss tape
    search_y = max(0, y + h - offset_bottom - search_offset_y)
    search_h = min(gray.shape[0], y + h + offset_bottom) - search_y
    search_x = max(0, x + offset_left)
    search_w = min(gray.shape[1], x + w - offset_right) - search_x
    
    if search_h <= 0 or search_w <= 0:
        return True, {"messages": ["Bottom dent search area invalid"], "pass": True}
    
    search_roi = gray[search_y:search_y+search_h, search_x:search_x+search_w]
    
    # Create mask for dark areas (dents appear as dark regions)
    dent_mask = (search_roi < contrast).astype(np.uint8) * 255
    
    # Find dent contours
    contours, _ = cv2.findContours(dent_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    dents_detected = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        x_dent, y_dent, w_dent, h_dent = cv2.boundingRect(cnt)
        
        # Skip very small contours
        if area < 5:
            continue
        
        # Check if dent is within acceptable limits
        is_dent_fail = False
        fail_reason = ""
        
        if min_area > 0 and area > min_area:
            is_dent_fail = True
            fail_reason = f"area {int(area)} > min_area {min_area}"
        
        if min_sq_size > 0 and (w_dent > min_sq_size or h_dent > min_sq_size):
            is_dent_fail = True
            fail_reason = f"size {w_dent}x{h_dent} > min_sq_size {min_sq_size}"
        
        if is_dent_fail:
            is_valid = False
            dents_detected.append({
                'x': x_dent + search_x,
                'y': y_dent + search_y,
                'width': w_dent,
                'height': h_dent,
                'area': area,
                'reason': fail_reason
            })
            msg = f"Bottom dent detected: {fail_reason}"
            messages.append(msg)
            if debug:
                print(f"[FAIL] {msg}")
    
    if is_valid and not messages:
        messages.append("Bottom dent inspection OK - no dents detected")
        if debug:
            print("[PASS] Bottom dent inspection OK")
    
    return is_valid, {
        "pass": is_valid,
        "messages": messages,
        "dents_detected": len(dents_detected),
        "dents": dents_detected
    }


def check_special_black_emboss_sealing(
    image: np.ndarray,
    pocket_location: Tuple[int, int, int, int],
    pocket_params: Optional[Dict] = None,
    debug: bool = False
) -> Tuple[bool, Dict]:
    """
    Special black emboss sealing tape inspection.
    
    Inspects sealing stains on black emboss tape, detecting:
    - Sealing mark position and integrity
    - Stain brightness levels on left and right sides
    - Sealing coverage area (width top/bottom)
    
    Parameters:
    - contrast_left/right: stain brightness threshold for each side
    - min_area: minimum acceptable stain area
    - min_sq_size: minimum acceptable stain dimensions
    - width_left/right/top/bottom: inspection width for sealing coverage
    - offset_left/right: offset from left edge of pocket
    """
    params = pocket_params or {}
    enable = _pp_bool(params, "sealing_stain_enable", False)
    
    if not enable:
        return True, {"messages": ["Special black emboss sealing disabled"], "pass": True}
    
    if image is None or image.size == 0:
        return True, {"messages": ["Invalid image"], "pass": True}
    
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    x, y, w, h = pocket_location
    messages = []
    is_valid = True
    
    # Special sealing stain parameters
    contrast_left = _pp_int(params, "sealing_stain_contrast_left", 255)
    contrast_right = _pp_int(params, "sealing_stain_contrast_right", 255)
    min_area = _pp_int(params, "sealing_stain_min_area", 0)
    min_sq_size = _pp_int(params, "sealing_stain_min_sq_size", 0)
    
    width_left = _pp_int(params, "sealing_width_left", 0)
    width_right = _pp_int(params, "sealing_width_right", 0)
    width_top = _pp_int(params, "sealing_width_top", 0)
    width_bottom = _pp_int(params, "sealing_width_bottom", 0)
    
    offset_left_val = _pp_int(params, "sealing_offset_left", 0)
    offset_right_val = _pp_int(params, "sealing_offset_right", 0)
    
    if contrast_left == 255 and contrast_right == 255:
        return True, {"messages": ["Special black emboss sealing parameters disabled"], "pass": True}
    
    # Define inspection areas on left and right sides of sealing mark
    # Left side inspection area
    left_x = max(0, x + offset_left_val)
    left_y = max(0, y + width_top)
    left_w = width_left
    left_h = h - width_top - width_bottom
    
    # Right side inspection area
    right_x = max(0, x + w - offset_right_val - width_right)
    right_y = max(0, y + width_top)
    right_w = width_right
    right_h = h - width_top - width_bottom
    
    stains_found = []
    
    # Check left side
    if left_w > 0 and left_h > 0 and contrast_left < 255:
        left_x_clamped = max(0, min(left_x, gray.shape[1]))
        left_x_end = max(0, min(left_x + left_w, gray.shape[1]))
        left_y_clamped = max(0, min(left_y, gray.shape[0]))
        left_y_end = max(0, min(left_y + left_h, gray.shape[0]))
        
        if left_x_clamped < left_x_end and left_y_clamped < left_y_end:
            left_roi = gray[left_y_clamped:left_y_end, left_x_clamped:left_x_end]
            
            # Create mask for stain areas (below contrast threshold)
            stain_mask = (left_roi < contrast_left).astype(np.uint8) * 255
            contours, _ = cv2.findContours(stain_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 5:
                    continue
                
                x_stain, y_stain, w_stain, h_stain = cv2.boundingRect(cnt)
                
                # Check stain validity
                is_stain_fail = False
                fail_reason = ""
                
                if min_area > 0 and area < min_area:
                    is_stain_fail = True
                    fail_reason = f"area {int(area)} < min_area {min_area}"
                
                if min_sq_size > 0 and (w_stain < min_sq_size or h_stain < min_sq_size):
                    is_stain_fail = True
                    fail_reason = f"size {w_stain}x{h_stain} < min_sq_size {min_sq_size}"
                
                if is_stain_fail:
                    is_valid = False
                    stains_found.append({
                        'side': 'left',
                        'x': x_stain + left_x_clamped,
                        'y': y_stain + left_y_clamped,
                        'width': w_stain,
                        'height': h_stain,
                        'area': area,
                        'reason': fail_reason
                    })
                    msg = f"Left sealing stain FAIL: {fail_reason}"
                    messages.append(msg)
                    if debug:
                        print(f"[FAIL] {msg}")
    
    # Check right side
    if right_w > 0 and right_h > 0 and contrast_right < 255:
        right_x_clamped = max(0, min(right_x, gray.shape[1]))
        right_x_end = max(0, min(right_x + right_w, gray.shape[1]))
        right_y_clamped = max(0, min(right_y, gray.shape[0]))
        right_y_end = max(0, min(right_y + right_h, gray.shape[0]))
        
        if right_x_clamped < right_x_end and right_y_clamped < right_y_end:
            right_roi = gray[right_y_clamped:right_y_end, right_x_clamped:right_x_end]
            
            # Create mask for stain areas
            stain_mask = (right_roi < contrast_right).astype(np.uint8) * 255
            contours, _ = cv2.findContours(stain_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 5:
                    continue
                
                x_stain, y_stain, w_stain, h_stain = cv2.boundingRect(cnt)
                
                # Check stain validity
                is_stain_fail = False
                fail_reason = ""
                
                if min_area > 0 and area < min_area:
                    is_stain_fail = True
                    fail_reason = f"area {int(area)} < min_area {min_area}"
                
                if min_sq_size > 0 and (w_stain < min_sq_size or h_stain < min_sq_size):
                    is_stain_fail = True
                    fail_reason = f"size {w_stain}x{h_stain} < min_sq_size {min_sq_size}"
                
                if is_stain_fail:
                    is_valid = False
                    stains_found.append({
                        'side': 'right',
                        'x': x_stain + right_x_clamped,
                        'y': y_stain + right_y_clamped,
                        'width': w_stain,
                        'height': h_stain,
                        'area': area,
                        'reason': fail_reason
                    })
                    msg = f"Right sealing stain FAIL: {fail_reason}"
                    messages.append(msg)
                    if debug:
                        print(f"[FAIL] {msg}")
    
    if is_valid and not messages:
        messages.append("Special black emboss sealing OK - no stain defects")
        if debug:
            print("[PASS] Special black emboss sealing OK")
    
    return is_valid, {
        "pass": is_valid,
        "messages": messages,
        "stains_detected": len(stains_found),
        "stains": stains_found
    }


def _apply_paper_dust_mask_binary(
    binary: np.ndarray,
    enable_left_right: bool,
    enable_top_bottom: bool,
    contrast_plus: bool,
    debug: bool = False
) -> np.ndarray:
    """
    Apply paper dust mask on a binary image by removing small edge-adjacent blobs.
    This mirrors the old behavior where dust near edges is masked before blob analysis.
    """
    if binary is None or binary.size == 0:
        return binary

    if not (enable_left_right or enable_top_bottom):
        return binary

    mask = binary.copy()
    h, w = mask.shape[:2]

    # Optional: enhance dust removal with a light open
    if contrast_plus:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if num_labels <= 1:
        return mask

    edge_margin = 5
    for label in range(1, num_labels):
        x, y, bw, bh, area = stats[label]
        if area <= 0:
            continue

        near_left = x <= edge_margin
        near_right = (x + bw) >= (w - edge_margin)
        near_top = y <= edge_margin
        near_bottom = (y + bh) >= (h - edge_margin)

        remove = False
        if enable_left_right and (near_left or near_right):
            if bh < int(h * 0.7):
                remove = True

        if enable_top_bottom and (near_top or near_bottom):
            if bw < int(w * 0.7):
                remove = True

        if remove:
            mask[labels == label] = 0

    if debug:
        print("[DEBUG] Paper dust mask (binary) applied")

    return mask


def detect_pocket_location(
    image: np.ndarray,
    teach_rect: Optional[Tuple[int, int, int, int]] = None,
    pocket_params: Optional[Dict] = None,
    debug: bool = False,
) -> PocketLocationResult:
    """
    Detect pocket location in image with advanced features.
    
    Features:
    1. Contrast-based thresholding (edge_contrast_value)
    2. Dark/Light hypothesis detection
    3. Shift tolerance search ROI
    4. Body area dust mask filtering
    5. Direction validation (parallel vs non-parallel chips)
    6. Angle regularity check
    
    Parameters:
    - image: input image (BGR or grayscale)
    - teach_rect: (x, y, width, height) of taught pocket location
    - pocket_params: dict of parameters from pocket_params.json
    - debug: enable debug output
    
    Returns PocketLocationResult with detection status and metrics
    """
    if image is None or image.size == 0:
        return PocketLocationResult(False, 0, 0, 0, 0, 0, 0, "Invalid image", "none")

    params = pocket_params or {}

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # Determine search ROI based on taught pocket and shift tolerance
    if teach_rect and teach_rect[2] > 0 and teach_rect[3] > 0:
        tx, ty, tw, th = teach_rect
        shift_x_pos = _pp_int(params, "pocket_shift_x_pos", 50)
        shift_x_neg = _pp_int(params, "pocket_shift_x_neg", 50)
        shift_y_pos = _pp_int(params, "pocket_shift_y_pos", 50)
        shift_y_neg = _pp_int(params, "pocket_shift_y_neg", 50)
        x1 = max(0, tx - shift_x_neg)
        y1 = max(0, ty - shift_y_neg)
        x2 = min(gray.shape[1], tx + tw + shift_x_pos)
        y2 = min(gray.shape[0], ty + th + shift_y_pos)
        search_roi = gray[y1:y2, x1:x2]
        roi_offset = (x1, y1)
        expected_area = float(tw * th)
        expected_ratio = max(tw, th) / max(1, min(tw, th))
    else:
        search_roi = gray
        roi_offset = (0, 0)
        expected_area = None
        expected_ratio = None

    if search_roi.size == 0:
        return PocketLocationResult(False, 0, 0, 0, 0, 0, 0, "Empty search ROI", "none")

    # Histogram-based contrast thresholding (old logic)
    contrast = _pp_int(params, "edge_contrast_value", 106)
    post_seal_contrast = _pp_int(params, "post_seal_low_contrast", 255)
    enable_post_seal = _pp_bool(params, "enable_post_seal", False)

    black_avg, white_avg = _compute_black_white_thresholds(search_roi)
    percents = _threshold_percentages()

    if debug:
        print(f"[DEBUG] Pocket detection: black_avg={black_avg}, white_avg={white_avg}, "
              f"edge_contrast={contrast}, post_seal_contrast={post_seal_contrast}")

    def _try_detect_with_contrast(contrast_offset: int, label: str) -> Tuple[Optional[np.ndarray], str]:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        method_local = "none"
        best_local = None
        for pct in percents:
            thres = _compute_threshold_value(black_avg, white_avg, contrast_offset, pct)
            if debug:
                print(f"[DEBUG] {label}: threshold_percent={pct}, threshold_value={thres}")

            _, bin_mask = cv2.threshold(search_roi, thres, 255, cv2.THRESH_BINARY)

            # Apply paper dust mask on binary image
            lr_enable = _pp_bool(params, "paper_dust_left_right", False)
            tb_enable = _pp_bool(params, "paper_dust_top_bottom", False)
            contrast_plus = _pp_bool(params, "paper_dust_contrast_plus", False)
            if lr_enable or tb_enable:
                bin_mask = _apply_paper_dust_mask_binary(bin_mask, lr_enable, tb_enable, contrast_plus, debug=debug)

            bin_mask = cv2.morphologyEx(bin_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
            inv_mask = cv2.bitwise_not(bin_mask)
            inv_mask = cv2.morphologyEx(inv_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

            dark_contour = _find_best_contour(inv_mask)
            light_contour = _find_best_contour(bin_mask)

            if dark_contour is not None and light_contour is not None:
                dark_score = _score_contour(dark_contour, expected_area, expected_ratio)
                light_score = _score_contour(light_contour, expected_area, expected_ratio)
                best_local = dark_contour if dark_score >= light_score else light_contour
                method_local = f"{label}_dark" if dark_score >= light_score else f"{label}_light"
            elif dark_contour is not None:
                best_local = dark_contour
                method_local = f"{label}_dark"
            elif light_contour is not None:
                best_local = light_contour
                method_local = f"{label}_light"

            if best_local is not None:
                break

        return best_local, method_local

    best_contour, method = _try_detect_with_contrast(contrast, "primary")

    # Try post-seal low contrast fallback if primary detection failed
    if best_contour is None and enable_post_seal and post_seal_contrast < 255:
        best_contour, method = _try_detect_with_contrast(post_seal_contrast, "post_seal")

    if best_contour is None:
        return PocketLocationResult(False, 0, 0, 0, 0, 0, 0,
                                   "Pocket contour not found (primary and fallback failed)", "none")

    x, y, w, h = cv2.boundingRect(best_contour)
    x += roi_offset[0]
    y += roi_offset[1]

    # Get initial pocket location for dust mask application
    pocket_location = (x, y, w, h)
    
    # Apply body area dust mask filtering
    if _pp_bool(params, "body_area_enable", False):
        gray = _apply_body_area_dust_mask(gray, pocket_location, params, debug=debug)
        
        # Re-detect with masked image if dust mask was applied
        if teach_rect and teach_rect[2] > 0 and teach_rect[3] > 0:
            tx, ty, tw, th = teach_rect
            x1 = max(0, tx - shift_x_neg)
            y1 = max(0, ty - shift_y_neg)
            x2 = min(gray.shape[1], tx + tw + shift_x_pos)
            y2 = min(gray.shape[0], ty + th + shift_y_pos)
            search_roi = gray[y1:y2, x1:x2]
        else:
            search_roi = gray
        
        # Re-detect pocket with masked image using histogram-based thresholding
        black_avg, white_avg = _compute_black_white_thresholds(search_roi)
        best_contour, method = _try_detect_with_contrast(contrast, "primary")
        if best_contour is None and enable_post_seal and post_seal_contrast < 255:
            best_contour, method = _try_detect_with_contrast(post_seal_contrast, "post_seal")

        if best_contour is not None:
            x, y, w, h = cv2.boundingRect(best_contour)
            x += roi_offset[0]
            y += roi_offset[1]
            pocket_location = (x, y, w, h)
    
    # Direction angle validation (parallel vs non-parallel)
    angle_valid, angle, parallel_mode = _validate_direction_angle(best_contour, params, debug=debug)
    
    if not angle_valid:
        reason = f"Pocket angle {angle:.2f}° out of tolerance"
        if debug:
            print(f"[FAIL] {reason}")
        return PocketLocationResult(
            False, x, y, w, h, 0, 0, reason, method, 
            angle=angle, parallel_mode=parallel_mode
        )

    # Calculate contrast and confidence
    roi_gray = gray[max(0, y):min(gray.shape[0], y + h), max(0, x):min(gray.shape[1], x + w)]
    roi_contrast = float(np.std(roi_gray)) if roi_gray.size > 0 else 0.0

    image_area = float(gray.shape[0] * gray.shape[1])
    area_ratio = (w * h) / image_area if image_area > 0 else 0.0
    contrast_ratio = min(roi_contrast / 100.0, 1.0)
    confidence = min((area_ratio * 0.6 + contrast_ratio * 0.4) * 100.0, 100.0)

    if debug:
        print(f"[DEBUG] Pocket Location PASS: method={method}, rect=({x},{y},{w}x{h}), "
              f"angle={angle:.2f}°, mode={parallel_mode}, contrast={roi_contrast:.1f}, confidence={confidence:.1f}%")

    return PocketLocationResult(
        True, x, y, w, h, roi_contrast, confidence, "Pocket detected", method,
        angle=angle, parallel_mode=parallel_mode
    )


def validate_pocket_location(
    location: Tuple[int, int, int, int],
    image_shape: Tuple[int, int, int],
    min_size: int = 20,
    max_size_ratio: float = 0.95,
    debug: bool = False,
) -> bool:
    x, y, w, h = location
    img_h, img_w = image_shape[:2]

    if x < 0 or y < 0 or x + w > img_w or y + h > img_h:
        if debug:
            print(f"[DEBUG] Pocket location out of bounds: {location}")
        return False

    if w < min_size or h < min_size:
        if debug:
            print(f"[DEBUG] Pocket location too small: {w}x{h}")
        return False

    if w > img_w * max_size_ratio or h > img_h * max_size_ratio:
        if debug:
            print(f"[DEBUG] Pocket location too large: {w}x{h}")
        return False

    return True

def check_pocket_dimension(
    pocket_location: Tuple[int, int, int, int],
    pocket_params: Optional[Dict] = None,
    debug: bool = False
) -> Tuple[bool, Dict]:
    """
    Check if pocket dimensions meet specifications.
    
    Parameters:
    - pocket_location: (x, y, width, height) of detected pocket
    - pocket_params: parameters dict containing:
      - pocket_dim_length_enable: enable length inspection
      - pocket_dim_width_enable: enable width inspection
      - pocket_length_min: minimum allowed length
      - pocket_length_max: maximum allowed length
      - pocket_width_min: minimum allowed width
      - pocket_width_max: maximum allowed width
    
    Returns:
    - (is_valid: bool, details: dict with pass/fail info)
    """
    params = pocket_params or {}
    x, y, w, h = pocket_location
    
    length_enable = _pp_bool(params, "pocket_dim_length_enable", False)
    width_enable = _pp_bool(params, "pocket_dim_width_enable", False)
    
    length_min = _pp_int(params, "pocket_length_min", 0)
    length_max = _pp_int(params, "pocket_length_max", 255)
    width_min = _pp_int(params, "pocket_width_min", 0)
    width_max = _pp_int(params, "pocket_width_max", 255)
    
    # Treat 255 as disabled
    if length_max == 255 and length_min == 255:
        length_enable = False
    if width_max == 255 and width_min == 255:
        width_enable = False
    
    details = {
        "length_pass": True,
        "width_pass": True,
        "length_value": w,
        "width_value": h,
        "length_range": (length_min, length_max),
        "width_range": (width_min, width_max),
        "messages": []
    }
    
    is_valid = True
    
    # Check length (width of pocket in image)
    if length_enable and length_min > 0 and length_max > 0:
        if not (length_min <= w <= length_max):
            details["length_pass"] = False
            is_valid = False
            details["messages"].append(
                f"Pocket length {w} out of range [{length_min}, {length_max}]"
            )
            if debug:
                print(f"[FAIL] Pocket Length: {w} not in [{length_min}, {length_max}]")
        else:
            details["messages"].append(f"Pocket length {w} OK [{length_min}, {length_max}]")
            if debug:
                print(f"[PASS] Pocket Length: {w} in [{length_min}, {length_max}]")
    
    # Check width (height of pocket in image)
    if width_enable and width_min > 0 and width_max > 0:
        if not (width_min <= h <= width_max):
            details["width_pass"] = False
            is_valid = False
            details["messages"].append(
                f"Pocket width {h} out of range [{width_min}, {width_max}]"
            )
            if debug:
                print(f"[FAIL] Pocket Width: {h} not in [{width_min}, {width_max}]")
        else:
            details["messages"].append(f"Pocket width {h} OK [{width_min}, {width_max}]")
            if debug:
                print(f"[PASS] Pocket Width: {h} in [{width_min}, {width_max}]")
    
    return is_valid, details


def check_pocket_gap(
    device_location: Tuple[int, int, int, int],
    pocket_location: Tuple[int, int, int, int],
    pocket_params: Optional[Dict] = None,
    debug: bool = False
) -> Tuple[bool, Dict]:
    """
    Check if gap between device and pocket meets specifications.
    
    Parameters:
    - device_location: (x, y, width, height) of detected device
    - pocket_location: (x, y, width, height) of pocket
    - pocket_params: parameters dict containing:
      - pocket_gap_enable: enable gap inspection
      - pocket_gap_4_sides: check all 4 corners
      - pocket_gap_left_enable: check left side (pickup stations 1 & 2 only)
      - pocket_gap_min_x: minimum gap in X direction
      - pocket_gap_min_y: minimum gap in Y direction
    
    Returns:
    - (is_valid: bool, details: dict with gap measurements)
    """
    params = pocket_params or {}
    
    gap_enable = _pp_bool(params, "pocket_gap_enable", False)
    gap_4_sides = _pp_bool(params, "pocket_gap_4_sides", False)
    gap_left_enable = _pp_bool(params, "pocket_gap_left_enable", False)
    gap_min_x = _pp_int(params, "pocket_gap_min_x", 0)
    gap_min_y = _pp_int(params, "pocket_gap_min_y", 0)
    
    if not gap_enable:
        return True, {"gap_enable": False, "messages": ["Gap inspection disabled"]}
    
    dev_x, dev_y, dev_w, dev_h = device_location
    pck_x, pck_y, pck_w, pck_h = pocket_location
    
    # Calculate gaps at 4 corners
    # Top-left gap
    gap_tl_x = dev_x - pck_x
    gap_tl_y = dev_y - pck_y
    
    # Top-right gap
    gap_tr_x = (pck_x + pck_w) - (dev_x + dev_w)
    gap_tr_y = dev_y - pck_y
    
    # Bottom-left gap
    gap_bl_x = dev_x - pck_x
    gap_bl_y = (pck_y + pck_h) - (dev_y + dev_h)
    
    # Bottom-right gap
    gap_br_x = (pck_x + pck_w) - (dev_x + dev_w)
    gap_br_y = (pck_y + pck_h) - (dev_y + dev_h)
    
    details = {
        "gap_enable": True,
        "gap_4_sides": gap_4_sides,
        "gap_left_enable": gap_left_enable,
        "gap_min_x": gap_min_x,
        "gap_min_y": gap_min_y,
        "gaps": {
            "top_left": (gap_tl_x, gap_tl_y),
            "top_right": (gap_tr_x, gap_tr_y),
            "bottom_left": (gap_bl_x, gap_bl_y),
            "bottom_right": (gap_br_x, gap_br_y)
        },
        "messages": [],
        "pass": True
    }
    
    is_valid = True
    
    if gap_4_sides:
        # All 4 corners must have sufficient gap
        corners = [
            ("TL", gap_tl_x, gap_tl_y),
            ("TR", gap_tr_x, gap_tr_y),
            ("BL", gap_bl_x, gap_bl_y),
            ("BR", gap_br_x, gap_br_y)
        ]
        
        for corner_name, gap_x, gap_y in corners:
            if gap_min_x > 0 and gap_x < gap_min_x:
                is_valid = False
                details["pass"] = False
                details["messages"].append(
                    f"Gap {corner_name} X: {gap_x} < min {gap_min_x}"
                )
                if debug:
                    print(f"[FAIL] Gap {corner_name} X: {gap_x} < min {gap_min_x}")
            
            if gap_min_y > 0 and gap_y < gap_min_y:
                is_valid = False
                details["pass"] = False
                details["messages"].append(
                    f"Gap {corner_name} Y: {gap_y} < min {gap_min_y}"
                )
                if debug:
                    print(f"[FAIL] Gap {corner_name} Y: {gap_y} < min {gap_min_y}")
        
        if is_valid:
            details["messages"].append(
                f"All 4 corners OK (min X={gap_min_x}, min Y={gap_min_y})"
            )
            if debug:
                print(f"[PASS] All 4 corners gap OK")
    
    elif gap_left_enable:
        # Only check left side gaps (pickup stations 1 & 2)
        left_gaps = [
            ("TL", gap_tl_x, gap_tl_y),
            ("BL", gap_bl_x, gap_bl_y)
        ]
        
        for corner_name, gap_x, gap_y in left_gaps:
            if gap_min_x > 0 and gap_x < gap_min_x:
                is_valid = False
                details["pass"] = False
                details["messages"].append(
                    f"Left Gap {corner_name} X: {gap_x} < min {gap_min_x}"
                )
                if debug:
                    print(f"[FAIL] Left Gap {corner_name} X: {gap_x} < min {gap_min_x}")
            
            if gap_min_y > 0 and gap_y < gap_min_y:
                is_valid = False
                details["pass"] = False
                details["messages"].append(
                    f"Left Gap {corner_name} Y: {gap_y} < min {gap_min_y}"
                )
                if debug:
                    print(f"[FAIL] Left Gap {corner_name} Y: {gap_y} < min {gap_min_y}")
        
        if is_valid:
            details["messages"].append(
                f"Left gaps OK (min X={gap_min_x}, min Y={gap_min_y})"
            )
            if debug:
                print(f"[PASS] Left gaps OK")
    
    return is_valid, details


@dataclass
class PocketShiftRecord:
    """Record pocket shift data for tracking"""
    device_count: int
    total_shift_x: float
    total_shift_y: float
    max_shift_x: float
    max_shift_y: float
    min_shift_x: float
    min_shift_y: float
    alerts: list = None  # List of alert messages
    
    def __post_init__(self):
        if self.alerts is None:
            self.alerts = []
    
    @property
    def avg_shift_x(self) -> float:
        return self.total_shift_x / max(1, self.device_count)
    
    @property
    def avg_shift_y(self) -> float:
        return self.total_shift_y / max(1, self.device_count)


def track_pocket_shift(
    current_pocket_x: float,
    current_pocket_y: float,
    taught_pocket_x: float,
    taught_pocket_y: float,
    pocket_params: Optional[Dict] = None,
    shift_record: Optional[PocketShiftRecord] = None,
    debug: bool = False
) -> Tuple[bool, PocketShiftRecord, Dict]:
    """
    Track and validate pocket shift based on average position.
    
    Parameters:
    - current_pocket_x/y: Current detected pocket position
    - taught_pocket_x/y: Original taught pocket position
    - pocket_params: parameters dict containing:
      - pocket_shift_enable: enable shift tracking
      - pocket_shift_x_pos: positive X tolerance
      - pocket_shift_x_neg: negative X tolerance
      - pocket_shift_y_pos: positive Y tolerance
      - pocket_shift_y_neg: negative Y tolerance
    - shift_record: Existing shift record to update (or None to create new)
    - debug: enable debug output
    
    Returns:
    - (is_valid: bool, updated_record: PocketShiftRecord, details: dict)
    """
    params = pocket_params or {}
    
    shift_enable = _pp_bool(params, "pocket_shift_enable", False)
    shift_x_pos = _pp_int(params, "pocket_shift_x_pos", 50)
    shift_x_neg = _pp_int(params, "pocket_shift_x_neg", 50)
    shift_y_pos = _pp_int(params, "pocket_shift_y_pos", 50)
    shift_y_neg = _pp_int(params, "pocket_shift_y_neg", 50)
    
    if not shift_enable:
        return True, shift_record or PocketShiftRecord(0, 0, 0, 0, 0, 0, 0), \
               {"shift_enable": False, "messages": ["Shift tracking disabled"]}
    
    # Calculate current shift
    shift_x = current_pocket_x - taught_pocket_x
    shift_y = current_pocket_y - taught_pocket_y
    
    # Initialize or update record
    if shift_record is None:
        record = PocketShiftRecord(
            device_count=1,
            total_shift_x=shift_x,
            total_shift_y=shift_y,
            max_shift_x=abs(shift_x),
            max_shift_y=abs(shift_y),
            min_shift_x=abs(shift_x),
            min_shift_y=abs(shift_y)
        )
    else:
        record = shift_record
        record.device_count += 1
        record.total_shift_x += shift_x
        record.total_shift_y += shift_y
        record.max_shift_x = max(record.max_shift_x, abs(shift_x))
        record.max_shift_y = max(record.max_shift_y, abs(shift_y))
        record.min_shift_x = min(record.min_shift_x, abs(shift_x))
        record.min_shift_y = min(record.min_shift_y, abs(shift_y))
    
    # Check tolerance
    avg_x = record.avg_shift_x
    avg_y = record.avg_shift_y
    
    is_valid = True
    messages = []
    alerts = []
    
    # Check X shift
    if avg_x > shift_x_pos or avg_x < -shift_x_neg:
        is_valid = False
        alert_msg = f"Pocket X shift {avg_x:.1f} exceeds tolerance"
        alerts.append(alert_msg)
        messages.append(alert_msg)
        if debug:
            print(f"[ALERT] {alert_msg}")
    else:
        messages.append(f"Pocket X shift {avg_x:.1f} OK (pos_tol={shift_x_pos}, neg_tol={shift_x_neg})")
        if debug:
            print(f"[PASS] Pocket X shift {avg_x:.1f} within tolerance")
    
    # Check Y shift
    if avg_y > shift_y_pos or avg_y < -shift_y_neg:
        is_valid = False
        alert_msg = f"Pocket Y shift {avg_y:.1f} exceeds tolerance"
        alerts.append(alert_msg)
        messages.append(alert_msg)
        if debug:
            print(f"[ALERT] {alert_msg}")
    else:
        messages.append(f"Pocket Y shift {avg_y:.1f} OK (pos_tol={shift_y_pos}, neg_tol={shift_y_neg})")
        if debug:
            print(f"[PASS] Pocket Y shift {avg_y:.1f} within tolerance")
    
    record.alerts.extend(alerts)
    
    details = {
        "shift_enable": True,
        "device_count": record.device_count,
        "current_shift": (shift_x, shift_y),
        "avg_shift": (avg_x, avg_y),
        "max_shift": (record.max_shift_x, record.max_shift_y),
        "min_shift": (record.min_shift_x, record.min_shift_y),
        "tolerance_x": (shift_x_pos, shift_x_neg),
        "tolerance_y": (shift_y_pos, shift_y_neg),
        "messages": messages,
        "alerts": alerts
    }
    
    return is_valid, record, details