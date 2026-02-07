"""
Mark Inspection Detection Module
Implements mark detection, verification, and validation based on old C++ logic
"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Dict, Any, Optional
from config.mark_inspection_io import MarkInspectionConfig
from imaging.mark_inspection_params import (
    MarkInspectionParameters,
    load_parameters_from_config,
    calculate_search_window,
    validate_mark_parameters
)
from imaging.symbol_template_matcher import SymbolTemplateMatcher


@dataclass
class MarkDetectionResult:
    """Result of mark detection"""
    detected: bool
    marks: List[Dict[str, Any]] = None
    confidence: float = 0.0
    method: str = "none"
    error_message: str = ""
    debug_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.marks is None:
            self.marks = []
        if self.debug_info is None:
            self.debug_info = {}


def detect_marks(
    image: np.ndarray,
    config: MarkInspectionConfig,
    roi: Optional[Tuple[int, int, int, int]] = None,
    debug: bool = False
) -> MarkDetectionResult:
    """
    Detect marks in the image using configured detection method
    
    Args:
        image: Input image (grayscale or BGR)
        config: Mark Inspection Configuration
        roi: Region of Interest (x, y, w, h) - if None, uses entire image
        debug: Enable debug output
    
    Returns:
        MarkDetectionResult with detected marks
    """
    
    # Load and validate parameters (matches old C++ InitMarkInspParm)
    params = load_parameters_from_config(config)
    is_valid, error_msg = validate_mark_parameters(params)
    
    if not is_valid:
        return MarkDetectionResult(
            detected=False,
            error_message=f"Invalid parameters: {error_msg}",
            method="error"
        )
    
    if not params.enable_mark_inspect:
        return MarkDetectionResult(
            detected=False,
            error_message="Mark inspection disabled",
            method="disabled"
        )
    
    if image is None or image.size == 0:
        return MarkDetectionResult(
            detected=False,
            error_message="Invalid input image",
            method="error"
        )
    
    # Convert to grayscale if needed
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Apply ROI if specified
    if roi:
        x, y, w, h = roi
        if x >= 0 and y >= 0 and x + w <= gray.shape[1] and y + h <= gray.shape[0]:
            gray = gray[y:y+h, x:x+w]
            roi_offset = (x, y)
        else:
            roi_offset = (0, 0)
    else:
        roi_offset = (0, 0)
    
    # Select detection method
    if config.mark_detect_method == "color" and config.symbol_set.inspect_color:
        result = _detect_marks_by_color(image, config, roi, debug)
    elif config.mark_detect_method == "template":
        result = _detect_marks_by_template(gray, config, debug)
    else:
        # Default: threshold-based detection
        result = _detect_marks_by_threshold(gray, config, debug)
    
    # Apply ROI offset to detected marks
    if result.detected and result.marks:
        for mark in result.marks:
            if 'x' in mark and 'y' in mark:
                mark['x'] += roi_offset[0]
                mark['y'] += roi_offset[1]
    
    if debug:
        print(f"[DEBUG] Mark detection result:")
        print(f"  - Detected: {result.detected}")
        print(f"  - Method: {result.method}")
        print(f"  - Mark count: {len(result.marks)}")
        print(f"  - Confidence: {result.confidence:.1f}%")
        if result.error_message:
            print(f"  - Error: {result.error_message}")
    
    return result


def _detect_marks_by_threshold(
    gray: np.ndarray,
    config: MarkInspectionConfig,
    debug: bool = False
) -> MarkDetectionResult:
    """
    Detect marks using threshold-based method (like old C++ application)
    """
    try:
        threshold = config.symbol_set.mark_threshold
        contrast = config.symbol_set.mark_contrast
        
        # Apply adaptive contrast enhancement
        if contrast > 0:
            # Increase contrast
            alpha = 1.0 + (contrast / 100.0)
            beta = contrast / 2.0
            gray_enhanced = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
            gray_enhanced = np.clip(gray_enhanced, 0, 255).astype(np.uint8)
        else:
            gray_enhanced = gray
        
        # Apply threshold (respect mark color)
        thresh_type = cv2.THRESH_BINARY
        if hasattr(config, "mark_color") and config.mark_color == "Black":
            # Black marks on bright background
            thresh_type = cv2.THRESH_BINARY_INV

        ret, binary = cv2.threshold(gray_enhanced, threshold, 255, thresh_type)
        
        if not ret:
            return MarkDetectionResult(
                detected=False,
                error_message="Threshold operation failed",
                method="threshold"
            )
        
        # Find contours (marks are white regions)
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            if debug:
                print("[DEBUG] No contours found in threshold image")
            return MarkDetectionResult(
                detected=False,
                error_message="No marks detected",
                method="threshold",
                debug_info={"threshold": threshold, "contours_found": 0}
            )
        
        # Filter contours by area
        marks = []
        min_area = config.symbol_set.mark_min_area
        max_area = config.symbol_set.mark_max_area
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Check area bounds
            if area < min_area or area > max_area:
                continue
            
            # Get bounding rectangle and moments
            x, y, w, h = cv2.boundingRect(contour)
            M = cv2.moments(contour)
            
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx = x + w // 2
                cy = y + h // 2
            
            # Calculate mark properties
            mark = {
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "center_x": cx,
                "center_y": cy,
                "area": area,
                "aspect_ratio": float(w) / h if h > 0 else 0,
                "solidity": area / (w * h) if (w * h) > 0 else 0,
            }
            
            marks.append(mark)
        
        if not marks:
            if debug:
                print(f"[DEBUG] {len(contours)} contours found, but none passed area filter")
            return MarkDetectionResult(
                detected=False,
                error_message=f"No marks within area range ({min_area}-{max_area})",
                method="threshold",
                debug_info={
                    "threshold": threshold,
                    "contours_found": len(contours),
                    "marks_passed_filter": 0
                }
            )
        
        # Sort marks by area (largest first)
        marks.sort(key=lambda m: m['area'], reverse=True)
        
        confidence = min(100.0, 50.0 + (len(marks) * 10.0))  # Confidence based on mark count
        
        if debug:
            print(f"[DEBUG] Threshold detection: {len(marks)} marks found")
            for i, mark in enumerate(marks[:3]):
                print(f"  Mark {i+1}: area={mark['area']}, pos=({mark['x']},{mark['y']}), size={mark['width']}x{mark['height']}")
        
        return MarkDetectionResult(
            detected=True,
            marks=marks,
            confidence=confidence,
            method="threshold",
            debug_info={
                "threshold": threshold,
                "contrast": contrast,
                "marks_found": len(marks),
                "threshold_binary_white_pixels": np.count_nonzero(binary)
            }
        )
        
    except Exception as e:
        return MarkDetectionResult(
            detected=False,
            error_message=f"Threshold detection failed: {str(e)}",
            method="threshold"
        )


def _detect_marks_by_color(
    image: np.ndarray,
    config: MarkInspectionConfig,
    roi: Optional[Tuple[int, int, int, int]] = None,
    debug: bool = False
) -> MarkDetectionResult:
    """
    Detect marks using color-based method
    """
    try:
        if len(image.shape) != 3:
            return MarkDetectionResult(
                detected=False,
                error_message="Color detection requires BGR image",
                method="color"
            )
        
        # Extract target color
        target_r = config.color_target_r
        target_g = config.color_target_g
        target_b = config.color_target_b
        tolerance = config.color_tolerance
        
        # Create color mask (mark pixels match target color ±tolerance)
        b, g, r = cv2.split(image)
        
        mask_r = cv2.inRange(r, target_r - tolerance, target_r + tolerance)
        mask_g = cv2.inRange(g, target_g - tolerance, target_g + tolerance)
        mask_b = cv2.inRange(b, target_b - tolerance, target_b + tolerance)
        
        # Combine masks (AND operation - all channels must match)
        color_mask = cv2.bitwise_and(mask_r, cv2.bitwise_and(mask_g, mask_b))
        
        # Find contours
        contours, hierarchy = cv2.findContours(color_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return MarkDetectionResult(
                detected=False,
                error_message="No color-matching marks detected",
                method="color"
            )
        
        # Filter and process contours (same as threshold method)
        marks = []
        min_area = config.symbol_set.mark_min_area
        max_area = config.symbol_set.mark_max_area
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area or area > max_area:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            M = cv2.moments(contour)
            
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx = x + w // 2
                cy = y + h // 2
            
            mark = {
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "center_x": cx,
                "center_y": cy,
                "area": area,
                "aspect_ratio": float(w) / h if h > 0 else 0,
                "color_match": 100.0,
            }
            marks.append(mark)
        
        if not marks:
            return MarkDetectionResult(
                detected=False,
                error_message="No marks passed area filter",
                method="color"
            )
        
        marks.sort(key=lambda m: m['area'], reverse=True)
        confidence = 80.0 + (len(marks) * 5.0)
        
        if debug:
            print(f"[DEBUG] Color detection: {len(marks)} marks found")
        
        return MarkDetectionResult(
            detected=True,
            marks=marks,
            confidence=min(100.0, confidence),
            method="color"
        )
        
    except Exception as e:
        return MarkDetectionResult(
            detected=False,
            error_message=f"Color detection failed: {str(e)}",
            method="color"
        )


def _detect_marks_by_template(
    gray: np.ndarray,
    config: MarkInspectionConfig,
    debug: bool = False
) -> MarkDetectionResult:
    """
    Detect marks using template matching
    (Placeholder - requires pre-trained templates)
    """
    return MarkDetectionResult(
        detected=False,
        error_message="Template matching not yet implemented",
        method="template"
    )


def validate_mark_position(
    mark: Dict[str, Any],
    expected_x: int,
    expected_y: int,
    config: MarkInspectionConfig,
    debug: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate mark position against expected location
    
    Returns:
        (is_valid, validation_info)
    """
    tolerance = config.mark_position_tolerance
    
    actual_x = mark.get('center_x', mark.get('x', 0))
    actual_y = mark.get('center_y', mark.get('y', 0))
    
    distance = np.sqrt((actual_x - expected_x)**2 + (actual_y - expected_y)**2)
    is_valid = distance <= tolerance
    
    validation_info = {
        "expected_x": expected_x,
        "expected_y": expected_y,
        "actual_x": actual_x,
        "actual_y": actual_y,
        "distance": distance,
        "tolerance": tolerance,
        "is_valid": is_valid,
    }
    
    if debug:
        print(f"[DEBUG] Mark position validation:")
        print(f"  Expected: ({expected_x}, {expected_y})")
        print(f"  Actual: ({actual_x}, {actual_y})")
        print(f"  Distance: {distance:.1f} (tolerance: {tolerance})")
        print(f"  Valid: {is_valid}")
    
    return is_valid, validation_info


def verify_marks(
    marks: List[Dict[str, Any]],
    config: MarkInspectionConfig,
    image: Optional[np.ndarray] = None,
    debug: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify detected marks meet all requirements.
    
    If image and templates are provided, also performs symbol recognition.
    Matches detected blobs against taught symbol templates using correlation.
    
    Args:
        marks: List of detected mark blobs
        config: Mark inspection configuration
        image: Source image for symbol template matching (optional)
        debug: Enable debug output
    
    Returns:
        (verification_passed, verification_info)
    """
    if not marks:
        return False, {"error": "No marks detected"}
    
    # Check minimum number of symbols required
    total_symbols = config.symbol_set.total_symbol_set
    if len(marks) < total_symbols:
        return False, {
            "error": f"Insufficient marks: {len(marks)} found, {total_symbols} required"
        }
    
    # All marks must have valid properties
    for i, mark in enumerate(marks):
        if 'area' not in mark or 'center_x' not in mark or 'center_y' not in mark:
            return False, {
                "error": f"Mark {i+1} missing required properties"
            }
    
    # Prepare base verification info
    marks_detail = [
        {
            "id": i + 1,
            "area": mark.get('area', 0),
            "position": (mark.get('center_x', 0), mark.get('center_y', 0)),
            "symbol": mark.get('symbol'),
            "score": mark.get('score', 0)
        }
        for i, mark in enumerate(marks)
    ]
    
    verification_info = {
        "total_marks": len(marks),
        "required_symbols": total_symbols,
        "verification_passed": True,
        "marks_detail": marks_detail,
        "symbol_recognition": "not_attempted"
    }
    
    # Attempt symbol template matching if image provided
    if image is not None:
        matcher = SymbolTemplateMatcher()
        
        if matcher.has_templates():
            # Extract blob ROIs for template matching
            blob_rects = [
                {
                    "x": mark.get('x', int(mark.get('center_x', 0))),
                    "y": mark.get('y', int(mark.get('center_y', 0))),
                    "w": mark.get('width', mark.get('w', 20)),
                    "h": mark.get('height', mark.get('h', 20))
                }
                for mark in marks
            ]
            
            # Convert to grayscale if needed
            gray = image
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Match all blobs
            matched = matcher.match_all_blobs(
                gray,
                blob_rects,
                accept_score=config.insp_mark_contrast,
                reject_score=config.teach_mark_contrast
            )
            
            # Update marks with symbol info
            for i, match in enumerate(matched):
                marks_detail[i]["symbol"] = match.get("symbol")
                marks_detail[i]["score"] = match.get("score", 0)
            
            # Count successful symbol recognitions
            recognized_count = sum(1 for m in matched if m.get("symbol") is not None)
            
            verification_info["symbol_recognition"] = {
                "method": "template_matching",
                "recognized": recognized_count,
                "total": len(matched),
                "symbols": "".join([m.get("symbol") or "?" for m in matched])
            }
            
            if debug:
                print(f"[DEBUG] Symbol recognition:")
                print(f"  Recognized: {recognized_count}/{len(matched)}")
                print(f"  Sequence: {verification_info['symbol_recognition']['symbols']}")
        else:
            verification_info["symbol_recognition"] = "no_templates_taught"
            if debug:
                print(f"[DEBUG] No symbol templates taught yet")
    
    if debug:
        print(f"[DEBUG] Mark verification:")
        print(f"  Total marks: {len(marks)}")
        print(f"  Required symbols: {total_symbols}")
        print(f"  Verification: PASS" if len(marks) >= total_symbols else "  Verification: FAIL")
    
    return len(marks) >= total_symbols, verification_info
