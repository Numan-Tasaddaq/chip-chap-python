"""
Device/Package Location Detection
Detects the location of the device package in the image using edge detection and blob analysis.
Based on ChipCap-Oldversion blob-based location method with comprehensive parameter support.
"""

import numpy as np
import cv2
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass


@dataclass
class DeviceLocationResult:
    """Result of device location detection"""
    detected: bool
    x: int
    y: int
    width: int
    height: int
    contrast: float
    confidence: float
    message: str
    method: str = "blob"  # blob, edge, or hybrid


class DeviceLocationDetector:
    """Comprehensive device location detector with all features"""
    
    def __init__(self, settings: Dict):
        """Initialize detector with settings"""
        self.settings = settings
        self.enable_edge_scan = settings.get("enable_edge_scan", True)
        self.enable_reverse_edge = settings.get("enable_reverse_edge", False)
        self.enable_4color = settings.get("enable_4color", True)
        self.enable_flip_check = settings.get("enable_flip_check", False)
        self.pkg_loc_recheck = settings.get("pkg_loc_recheck", True)
        self.contrast = settings.get("contrast", 50)
        self.contrast_plus = settings.get("contrast_plus", 0)
        self.max_parallel_angle = settings.get("max_parallel_angle", 10)
        self.terminal_height_diff = settings.get("terminal_height_diff", 10)
        self.dilate_size = settings.get("dilate_size", 3)
        self.edge_scan_mask_y = settings.get("edge_scan_mask_y", 50)
        self.edge_scan_angle = settings.get("edge_scan_angle", 90)
        self.reverse_edge_angle = settings.get("reverse_edge_angle", 180)
        self.x_sampling_size = settings.get("x_sampling_size", 1)
        self.y_sampling_size = settings.get("y_sampling_size", 1)
        self.index_gap_enable = settings.get("index_gap_enable", False)
        self.index_gap_min_y = settings.get("index_gap_min_y", 0)
        self.enable_pkg = settings.get("enable_pkg", True)
        self.enable_red_pkg_location = settings.get("enable_red_pkg_location", False)
        self.ignore_top = settings.get("ignore_top", False)
        self.ignore_bottom = settings.get("ignore_bottom", False)
        self.ignore_left = settings.get("ignore_left", False)
        self.ignore_right = settings.get("ignore_right", False)
        self.line_mask_count = settings.get("line_mask_count", 0)
        
    def detect(
        self,
        image: np.ndarray,
        debug: bool = False
    ) -> DeviceLocationResult:
        """Detect device location using configured methods"""
        
        if image is None or image.size == 0:
            return DeviceLocationResult(
                detected=False, x=0, y=0, width=0, height=0,
                contrast=0, confidence=0, message="Invalid image input", method="none"
            )

        if not self.enable_pkg:
            return DeviceLocationResult(
                detected=False, x=0, y=0, width=0, height=0,
                contrast=0, confidence=0, message="Package location disabled", method="none"
            )

        # Apply optional filters on color image
        proc = self.apply_filters(image, debug)

        # Select image mode for detection
        gray = self._select_gray(proc)

        # Flip check (use full-resolution gray)
        if self.enable_flip_check and self._check_flip(proc, gray, debug):
            return DeviceLocationResult(
                detected=False, x=0, y=0, width=0, height=0,
                contrast=0, confidence=0, message="Flip detected", method="none"
            )

        # Sampling (downscale) for speed
        scale_x = max(1, int(self.x_sampling_size))
        scale_y = max(1, int(self.y_sampling_size))
        if scale_x > 1 or scale_y > 1:
            new_w = max(1, gray.shape[1] // scale_x)
            new_h = max(1, gray.shape[0] // scale_y)
            gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_AREA)
            if debug:
                print(f"[DEBUG] Sampling: scaled to {gray.shape[1]}x{gray.shape[0]} (x{scale_x}, y{scale_y})")
        
        # Convert to grayscale
        if len(gray.shape) != 2:
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
        
        if debug:
            print(f"[DEBUG] Device Location: Image shape={image.shape}")
            print(f"[DEBUG] Methods enabled: edge_scan={self.enable_edge_scan}, "
                  f"reverse_edge={self.enable_reverse_edge}, 4color={self.enable_4color}")
        
        # Step 1: Try edge scan method if enabled
        if self.enable_edge_scan:
            edge_gray = gray
            angle = int(self.reverse_edge_angle if self.enable_reverse_edge else self.edge_scan_angle) % 360

            if angle != 0:
                edge_gray, rot_m, rot_size = self._rotate_image(gray, angle)
                if debug:
                    print(f"[DEBUG] Edge Scan: rotated image by {angle}° (size={rot_size})")
            else:
                rot_m, rot_size = None, None

            edge_result = self._detect_with_edge_scan(edge_gray, debug)

            if edge_result.detected and rot_m is not None:
                edge_result = self._map_affine_result(edge_result, rot_m, gray.shape, debug)

            if edge_result.detected:
                edge_result = self._apply_post_checks(edge_result, scale_x, scale_y, debug)
                return edge_result
        
        # Step 2: Fallback to blob-based detection
        blob_result = self._detect_with_blob(gray, debug)
        blob_result = self._apply_post_checks(blob_result, scale_x, scale_y, debug)
        return blob_result

    def _apply_post_checks(
        self,
        result: DeviceLocationResult,
        scale_x: int,
        scale_y: int,
        debug: bool = False
    ) -> DeviceLocationResult:
        """Apply post-detection validation and scaling."""

        if not result.detected:
            return result

        # Scale location back to original image size
        if scale_x > 1 or scale_y > 1:
            result.x *= scale_x
            result.y *= scale_y
            result.width *= scale_x
            result.height *= scale_y
            if debug:
                print(f"[DEBUG] Scaled result back: ({result.x}, {result.y}, {result.width}x{result.height})")

        # Index gap check
        if self.index_gap_enable and result.y < int(self.index_gap_min_y):
            if debug:
                print(f"[DEBUG] Index gap check failed: y={result.y} < min_y={self.index_gap_min_y}")
            return DeviceLocationResult(
                detected=False, x=0, y=0, width=0, height=0,
                contrast=result.contrast, confidence=0,
                message="Index gap check failed", method=result.method
            )

        return result

    def _select_gray(self, image: np.ndarray) -> np.ndarray:
        """Select grayscale image based on settings."""
        if len(image.shape) != 3:
            return image.copy()

        # Use red package location or explicit color selection
        if self.enable_red_pkg_location or self.settings.get("insp_img_red", False):
            return image[:, :, 2]
        if self.settings.get("insp_img_green", False):
            return image[:, :, 1]
        if self.settings.get("insp_img_blue", False):
            return image[:, :, 0]

        # Default: merge (grayscale)
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def _rotate_image(self, gray: np.ndarray, angle: int) -> Tuple[np.ndarray, np.ndarray, Tuple[int, int]]:
        """Rotate image by arbitrary angle and return rotated image and matrix."""
        h, w = gray.shape[:2]
        center = (w / 2.0, h / 2.0)
        rot_m = cv2.getRotationMatrix2D(center, angle, 1.0)

        cos = abs(rot_m[0, 0])
        sin = abs(rot_m[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))

        rot_m[0, 2] += (new_w / 2.0) - center[0]
        rot_m[1, 2] += (new_h / 2.0) - center[1]

        rotated = cv2.warpAffine(gray, rot_m, (new_w, new_h), flags=cv2.INTER_LINEAR)
        return rotated, rot_m, (new_w, new_h)

    def _map_affine_result(
        self,
        result: DeviceLocationResult,
        rot_m: np.ndarray,
        orig_shape: Tuple[int, int],
        debug: bool = False
    ) -> DeviceLocationResult:
        """Map rotated detection result back to original coordinates using inverse affine."""
        orig_h, orig_w = orig_shape[:2]
        inv_m = cv2.invertAffineTransform(rot_m)

        corners = np.array([
            [result.x, result.y],
            [result.x + result.width, result.y],
            [result.x, result.y + result.height],
            [result.x + result.width, result.y + result.height]
        ], dtype=np.float32)

        ones = np.ones((corners.shape[0], 1), dtype=np.float32)
        corners_h = np.hstack([corners, ones])
        mapped = (inv_m @ corners_h.T).T

        xs = mapped[:, 0]
        ys = mapped[:, 1]

        x_min = int(max(0, np.min(xs)))
        y_min = int(max(0, np.min(ys)))
        x_max = int(min(orig_w - 1, np.max(xs)))
        y_max = int(min(orig_h - 1, np.max(ys)))

        if debug:
            print(f"[DEBUG] Edge Scan: mapped bbox back to ({x_min}, {y_min}, {x_max - x_min}x{y_max - y_min})")

        result.x = x_min
        result.y = y_min
        result.width = max(1, x_max - x_min)
        result.height = max(1, y_max - y_min)
        return result
    
    def _detect_with_edge_scan(
        self,
        gray: np.ndarray,
        debug: bool = False
    ) -> DeviceLocationResult:
        """Detect using edge scanning method"""
        
        if debug:
            print(f"[DEBUG] Edge Scan: Using edge detection method")
        
        # Create binary image
        mean_intensity = np.mean(gray)
        lower = max(0, int(mean_intensity) - self.contrast)
        upper = min(255, int(mean_intensity) + self.contrast + self.contrast_plus)
        
        if self.enable_reverse_edge:
            # Reverse: non-focus is black, focus is white
            binary = cv2.inRange(gray, lower, upper)
        else:
            # Normal: focus is black, non-focus is white
            binary = cv2.inRange(gray, lower, upper)
            binary = cv2.bitwise_not(binary)

        binary = self._apply_ignore_masks(binary)
        
        if debug:
            white_pixels = np.count_nonzero(binary)
            print(f"[DEBUG] Edge Scan: White pixels={white_pixels} ({white_pixels/binary.size*100:.1f}%)")
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.dilate_size, self.dilate_size))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return DeviceLocationResult(
                detected=False, x=0, y=0, width=0, height=0,
                contrast=0, confidence=0, message="No edge contours found", method="edge"
            )
        
        # Find largest contour
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        
        if area < 100:
            return DeviceLocationResult(
                detected=False, x=0, y=0, width=0, height=0,
                contrast=0, confidence=0, message="Edge contour too small", method="edge"
            )
        
        x, y, w, h = cv2.boundingRect(largest)
        
        # Check rectangle regularity (parallel angle)
        is_regular = self._check_rectangle_regularity(largest, debug)
        if not is_regular:
            if debug:
                print(f"[DEBUG] Rectangle not regular, angle exceeds tolerance")
            return DeviceLocationResult(
                detected=False, x=0, y=0, width=0, height=0,
                contrast=0, confidence=0, message="Rectangle not regular", method="edge"
            )
        
        # Calculate confidence
        roi_gray = gray[max(0, y):min(gray.shape[0], y+h), max(0, x):min(gray.shape[1], x+w)]
        roi_contrast = np.std(roi_gray) if roi_gray.size > 0 else 0
        
        image_area = gray.shape[0] * gray.shape[1]
        area_ratio = area / image_area
        contrast_ratio = min(roi_contrast / 100.0, 1.0)
        confidence = (area_ratio * 0.6 + contrast_ratio * 0.4) * 100
        confidence = min(confidence, 100)
        
        if debug:
            print(f"[DEBUG] Edge Scan Result: ({x}, {y}, {w}x{h}), confidence={confidence:.1f}%")
        
        return DeviceLocationResult(
            detected=True, x=x, y=y, width=w, height=h,
            contrast=roi_contrast, confidence=confidence,
            message=f"Edge scan detection successful", method="edge"
        )
    
    def _detect_with_blob(
        self,
        gray: np.ndarray,
        debug: bool = False
    ) -> DeviceLocationResult:
        """Detect using blob-based method"""
        
        # Gate blob debug output by DEBUG_BLOB flag
        # Import here to avoid circular imports
        if debug:
            from config.debug_flags import DEBUG_BLOB
            from config.debug_runtime import get_debug_flags
            should_log_blob = bool(get_debug_flags() & DEBUG_BLOB)
            
            if should_log_blob:
                print(f"[DEBUG] Blob Detection: Using blob analysis method")
        
        mean_intensity = np.mean(gray)
        lower = max(0, int(mean_intensity) - self.contrast)
        upper = min(255, int(mean_intensity) + self.contrast + self.contrast_plus)
        
        binary = cv2.inRange(gray, lower, upper)
        binary = cv2.bitwise_not(binary)

        binary = self._apply_ignore_masks(binary)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.dilate_size, self.dilate_size))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return DeviceLocationResult(
                detected=False, x=0, y=0, width=0, height=0,
                contrast=0, confidence=0, message="No blobs found", method="blob"
            )
        
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        
        if area < 100:
            return DeviceLocationResult(
                detected=False, x=0, y=0, width=0, height=0,
                contrast=0, confidence=0, message="Blob too small", method="blob"
            )
        
        x, y, w, h = cv2.boundingRect(largest)
        
        roi_gray = gray[max(0, y):min(gray.shape[0], y+h), max(0, x):min(gray.shape[1], x+w)]
        roi_contrast = np.std(roi_gray) if roi_gray.size > 0 else 0
        
        image_area = gray.shape[0] * gray.shape[1]
        area_ratio = area / image_area
        contrast_ratio = min(roi_contrast / 100.0, 1.0)
        confidence = (area_ratio * 0.6 + contrast_ratio * 0.4) * 100
        confidence = min(confidence, 100)
        
        if debug:
            from config.debug_flags import DEBUG_BLOB
            from config.debug_runtime import get_debug_flags
            should_log_blob = bool(get_debug_flags() & DEBUG_BLOB)
            
            if should_log_blob:
                print(f"[DEBUG] Blob Result: ({x}, {y}, {w}x{h}), confidence={confidence:.1f}%")
        
        return DeviceLocationResult(
            detected=True, x=x, y=y, width=w, height=h,
            contrast=roi_contrast, confidence=confidence,
            message=f"Blob detection successful", method="blob"
        )
    
    def _check_rectangle_regularity(self, contour: np.ndarray, debug: bool = False) -> bool:
        """Check if contour forms a regular rectangle within angle tolerance"""
        
        # Fit rectangle
        rect = cv2.minAreaRect(contour)
        angle = rect[2]
        
        # Normalize angle to 0-90 range
        if angle < 0:
            angle = angle + 180
        if angle > 90:
            angle = 180 - angle
        
        # Check against max parallel angle tolerance
        is_regular = angle <= self.max_parallel_angle
        
        if debug:
            print(f"[DEBUG] Rectangle angle={angle:.1f}°, tolerance={self.max_parallel_angle}°, regular={is_regular}")
        
        return is_regular
    
    def _check_flip(self, image: np.ndarray, gray: np.ndarray, debug: bool = False) -> bool:
        """Detect if chip is flipped"""
        
        if not self.enable_flip_check:
            return False
        
        if debug:
            print(f"[DEBUG] Flip Check: Enabled")
        
        # Check if white body or black body
        mean_intensity = np.mean(gray)
        is_white_body = mean_intensity > 128
        
        if debug:
            print(f"[DEBUG] Body type: {'white' if is_white_body else 'black'}")
        
        # Flip detection: compare top/bottom brightness bands
        h = gray.shape[0]
        band = max(1, int(h * 0.1))
        top_mean = float(np.mean(gray[:band, :]))
        bot_mean = float(np.mean(gray[h - band:, :]))

        flip_white_body = self.settings.get("flip_white_body", True)
        flip_top = self.settings.get("flip_top", True)
        flip_bot = self.settings.get("flip_bot", True)
        tol_white = self.settings.get("flip_white_tol", 10)
        tol_bot = self.settings.get("flip_bot_tol", 5)

        flipped = False
        if flip_white_body:
            # White body: top/bottom should be bright and similar
            if flip_top and top_mean < (128 - tol_white):
                flipped = True
            if flip_bot and bot_mean < (128 - tol_white):
                flipped = True
        else:
            # Black body: top/bottom should be dark and similar
            if flip_top and top_mean > (128 + tol_bot):
                flipped = True
            if flip_bot and bot_mean > (128 + tol_bot):
                flipped = True

        if debug:
            print(
                f"[DEBUG] Flip Check: top={top_mean:.1f}, bottom={bot_mean:.1f}, "
                f"white_body={flip_white_body}, flipped={flipped}"
            )

        return flipped
    
    def apply_filters(
        self,
        image: np.ndarray,
        debug: bool = False
    ) -> np.ndarray:
        """Apply color filters and image processing"""
        
        result = image.copy()

        # 4-color enhancement (contrast adjustment)
        if self.settings.get("enable_4color", False):
            threshold = self.settings.get("four_color_threshold", 80)
            alpha = 1.0 + (float(threshold) / 255.0)
            result = cv2.convertScaleAbs(result, alpha=alpha, beta=0)
            if debug:
                print(f"[DEBUG] 4-color enhancement applied: threshold={threshold}")

        # Reflection mask (optional)
        if self.settings.get("enable_reflection_mask", False):
            mask_rects = self.settings.get("reflection_mask", [])
            for rect in mask_rects:
                try:
                    x, y, w, h = rect
                    result[y:y+h, x:x+w] = 0
                except Exception:
                    continue
            if debug and mask_rects:
                print(f"[DEBUG] Reflection mask applied: {len(mask_rects)} regions")

        # Line masks (optional)
        result = self._apply_line_masks(result, debug)
        
        # Blue filter
        if self.settings.get("ignore_blue", False):
            b, g, r = cv2.split(result)
            blue_threshold = self.settings.get("ignore_blue_threshold", 150)
            
            # Create mask for blue pixels below threshold
            blue_mask = b < blue_threshold
            
            # Set blue pixels to 0 in merge
            b[blue_mask] = 0
            result = cv2.merge([b, g, r])
            
            if debug:
                print(f"[DEBUG] Blue filter applied: threshold={blue_threshold}")
        
        # Red filter for mark detection
        if self.settings.get("filter_red_enable", False):
            b, g, r = cv2.split(result)
            red_threshold = self.settings.get("filter_red_value", 100)
            green_threshold = self.settings.get("filter_green_value", 100)
            
            # Filter red marks
            red_mask = (r >= red_threshold) & (g <= green_threshold)
            r[red_mask] = 0
            result = cv2.merge([b, g, r])
            
            if debug:
                print(f"[DEBUG] Red filter applied: red>={red_threshold}, green<={green_threshold}")
        
        return result

    def _apply_ignore_masks(self, binary: np.ndarray) -> np.ndarray:
        """Apply ignore scan masks to binary image."""
        mask_size = int(self.edge_scan_mask_y) if self.edge_scan_mask_y else 0
        if mask_size <= 0:
            return binary

        h, w = binary.shape[:2]

        if self.ignore_top:
            binary[:min(mask_size, h), :] = 0
        if self.ignore_bottom:
            binary[max(0, h - mask_size):h, :] = 0
        if self.ignore_left:
            binary[:, :min(mask_size, w)] = 0
        if self.ignore_right:
            binary[:, max(0, w - mask_size):w] = 0

        return binary

    def _apply_line_masks(self, image: np.ndarray, debug: bool = False) -> np.ndarray:
        """Apply line masks from settings if present."""
        if self.line_mask_count <= 0:
            return image

        mask_rects = self.settings.get("line_masks", [])
        if not mask_rects:
            return image

        masked = image.copy()
        for rect in mask_rects[: self.line_mask_count]:
            try:
                x, y, w, h = rect
                masked[y:y+h, x:x+w] = 0
            except Exception:
                continue

        if debug:
            print(f"[DEBUG] Line masks applied: {min(len(mask_rects), self.line_mask_count)} regions")

        return masked


def detect_device_location(
    image: np.ndarray,
    contrast_threshold: int = 50,
    x_shift_tol: int = 50,
    y_shift_tol: int = 50,
    recheck: bool = True,
    recheck_val: int = 50,
    use_red_detection: bool = False,
    settings_dict: Optional[Dict] = None,
    debug: bool = False
) -> DeviceLocationResult:
    """
    Detect the location of the device package in the image.
    
    Args:
        image: Input image (BGR format, uint8)
        contrast_threshold: Contrast threshold for detection
        x_shift_tol: X-axis shift tolerance in pixels
        y_shift_tol: Y-axis shift tolerance in pixels
        recheck: Whether to recheck the location
        recheck_val: Recheck threshold value
        use_red_detection: Enable red color-based detection
        settings_dict: Dictionary of all settings
        debug: Enable debug output
    
    Returns:
        DeviceLocationResult with detected location and confidence
    """
    
    if image is None or image.size == 0:
        return DeviceLocationResult(
            detected=False, x=0, y=0, width=0, height=0,
            contrast=0, confidence=0, message="Invalid image input"
        )
    
    # Create detector with settings
    if settings_dict is None:
        settings_dict = {}

    if use_red_detection:
        settings_dict["enable_red_pkg_location"] = True
    
    detector = DeviceLocationDetector(settings_dict)
    
    # Perform detection
    result = detector.detect(image, debug)
    
    # Recheck if enabled and initial detection successful
    if recheck and result.detected:
        rechecked = _recheck_location(image, result.x, result.y, result.width, result.height, recheck_val, debug)
        if rechecked:
            result.x, result.y, result.width, result.height = rechecked
            result.message += " (rechecked)"
    
    return result


def _recheck_location(
    image: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
    recheck_val: int,
    debug: bool = False
) -> Optional[Tuple[int, int, int, int]]:
    """Recheck and refine the detected location"""
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    # Expand search area
    margin = int(max(w, h) * 0.2)
    x_min = max(0, x - margin)
    y_min = max(0, y - margin)
    x_max = min(image.shape[1], x + w + margin)
    y_max = min(image.shape[0], y + h + margin)
    
    search_roi = gray[y_min:y_max, x_min:x_max]
    mean_in_roi = np.mean(search_roi)
    
    lower = max(0, int(mean_in_roi) - recheck_val)
    upper = min(255, int(mean_in_roi) + recheck_val)
    
    binary_recheck = cv2.inRange(search_roi, lower, upper)
    binary_recheck = cv2.bitwise_not(binary_recheck)
    
    contours_recheck, _ = cv2.findContours(binary_recheck, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours_recheck:
        return None
    
    largest = max(contours_recheck, key=cv2.contourArea)
    x_r, y_r, w_r, h_r = cv2.boundingRect(largest)
    
    x_refined = x_min + x_r
    y_refined = y_min + y_r
    
    if debug:
        print(f"[DEBUG] Recheck refined location: x={x_refined}, y={y_refined}, w={w_r}, h={h_r}")
    
    return (x_refined, y_refined, w_r, h_r)


def validate_device_location(
    location: Tuple[int, int, int, int],
    image_shape: Tuple[int, int, int],
    min_size: int = 50,
    max_size_ratio: float = 0.9,
    debug: bool = False
) -> bool:
    """
    Validate if detected location is reasonable.
    
    Args:
        location: (x, y, w, h)
        image_shape: (height, width, channels)
        min_size: Minimum width and height
        max_size_ratio: Maximum size relative to image
        debug: Debug flag
    
    Returns:
        True if location is valid
    """
    
    x, y, w, h = location
    img_h, img_w = image_shape[:2]
    
    # Check bounds
    if x < 0 or y < 0 or x + w > img_w or y + h > img_h:
        if debug:
            print(f"[DEBUG] Location out of bounds: x={x}, y={y}, w={w}, h={h} in {img_w}x{img_h}")
        return False
    
    # Check size
    if w < min_size or h < min_size:
        if debug:
            print(f"[DEBUG] Location too small: {w}x{h} < {min_size}")
        return False
    
    if w > img_w * max_size_ratio or h > img_h * max_size_ratio:
        if debug:
            print(f"[DEBUG] Location too large: {w}x{h} > {img_w * max_size_ratio}x{img_h * max_size_ratio}")
        return False
    
    # Check aspect ratio
    aspect_ratio = max(w, h) / min(w, h)
    if aspect_ratio > 3.0:
        if debug:
            print(f"[DEBUG] Aspect ratio too extreme: {aspect_ratio:.2f}")
        return False
    
    return True
