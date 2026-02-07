"""
Mark Inspection Parameter Integration

This module integrates the Mark Parameters dialog settings with the mark
inspection engine, matching the old C++ implementation behavior.
"""

from dataclasses import dataclass
from typing import Tuple, List, Dict, Any, Optional
import numpy as np


@dataclass
class MarkInspectionParameters:
    """
    Mark Inspection Parameters matching old C++ MARK_INSP_PARM structure
    Maps dialog parameters to inspection algorithm parameters
    """
    
    # Enable/Disable
    enable_mark_inspect: bool = False
    enable_color_inspect: bool = False
    total_mark_set: int = 1  # 1-3
    total_symbol_set: int = 1  # 1-5
    
    # Symbol Shift Parameters (from dialog)
    user_define_teach_window: bool = True
    mark_rotation_tol: int = 5  # degrees
    first_template_shift_x: int = 25  # pixels
    first_template_shift_y: int = 25  # pixels
    other_template_shift_x: int = 10  # pixels
    other_template_shift_y: int = 10  # pixels
    
    # Symbol Characteristics (from dialog)
    mark_color: int = 1  # 1=WHITE, 0=BLACK
    total_teach_rectangle: int = 1  # 1-4
    min_character_size: int = 10  # pixels
    mark_min_x_size: int = 10  # pixels
    mark_min_y_size: int = 10  # pixels
    template_contrast_tol: int = 20  # contrast tolerance
    
    # Mark Hole Inspection Parameters (from dialog)
    hole_check: bool = False
    teach_mark_contrast: int = 100  # 0-255
    insp_mark_contrast: int = 130  # 0-255
    mark_min_area: int = 4  # pixels
    mark_min_xy_size: int = 3  # pixels
    
    # Symbol Inspection - First Template (Logo) Parameters
    separate_parameters_first_template: bool = True
    first_gross_check_only: bool = False
    first_accept_score: int = 85  # percentage 0-100
    first_reject_score: int = 40  # percentage 0-100
    first_mismatch_excess_area: int = 5  # pixels
    first_mismatch_missing_area: int = 5  # pixels
    first_mismatch_detect_method: int = 2  # 1=BLOB_AREA, 2=SQUARE_AREA
    
    # Symbol Inspection - Other Template Parameters
    template_gross_check_only: bool = False
    template_accept_score: int = 85  # percentage 0-100
    template_reject_score: int = 40  # percentage 0-100
    template_mismatch_excess_area: int = 5  # pixels
    template_mismatch_missing_area: int = 5  # pixels
    template_mismatch_detect_method: int = 2  # 1=BLOB_AREA, 2=SQUARE_AREA
    
    # Additional parameters (not in dialog but used internally)
    mask_template: bool = False
    template_x_skip_factor: int = 3
    template_y_skip_factor: int = 3
    fast_template_x_skip_factor: int = 8
    fast_template_y_skip_factor: int = 8
    enable_fast_first: bool = False
    enable_fast_last: bool = False
    mark_mask_dilation_size: int = 1


def load_parameters_from_config(config) -> MarkInspectionParameters:
    """
    Load mark inspection parameters from configuration
    Matches old C++ GetMarkInspParm() function
    
    Args:
        config: MarkInspectionConfig instance
        
    Returns:
        MarkInspectionParameters with all values populated
    """
    params = MarkInspectionParameters()
    
    # Basic settings
    params.enable_mark_inspect = config.symbol_set.enable_mark_inspect
    params.enable_color_inspect = config.symbol_set.inspect_color
    params.total_mark_set = config.symbol_set.total_mark_set
    params.total_symbol_set = config.symbol_set.total_symbol_set
    
    # Symbol Shift
    params.user_define_teach_window = config.user_define_teach_window
    params.mark_rotation_tol = config.mark_rotation_tol
    params.first_template_shift_x = config.first_template_shift_x
    params.first_template_shift_y = config.first_template_shift_y
    params.other_template_shift_x = config.other_template_shift_x
    params.other_template_shift_y = config.other_template_shift_y
    
    # Symbol Characteristics
    # Convert color string to old C++ enum: WHITE=1, BLACK=0
    params.mark_color = 1 if config.mark_color == "White" else 0
    params.total_teach_rectangle = config.total_teach_rectangle
    params.min_character_size = config.min_character_size
    params.mark_min_x_size = config.mark_min_x_size
    params.mark_min_y_size = config.mark_min_y_size
    
    # Mark Hole Inspection
    params.hole_check = config.hole_check
    params.teach_mark_contrast = config.teach_mark_contrast
    params.insp_mark_contrast = config.insp_mark_contrast
    params.mark_min_area = config.mark_min_area
    params.mark_min_xy_size = config.mark_min_xy_size
    
    # First Template Parameters (Logo)
    params.separate_parameters_first_template = config.separate_parameters_first_template
    params.first_gross_check_only = config.first_gross_check_only
    params.first_accept_score = config.first_accept_score
    params.first_reject_score = config.first_reject_score
    params.first_mismatch_excess_area = config.first_mismatch_excess_area
    params.first_mismatch_missing_area = config.first_mismatch_missing_area
    
    # Convert method string to enum: "Square Area"=2, "Blob Area"=1
    if config.first_mismatch_detect_method == "Square Area":
        params.first_mismatch_detect_method = 2  # SQUARE_AREA
    else:
        params.first_mismatch_detect_method = 1  # BLOB_AREA
    
    # Other Template Parameters
    params.template_gross_check_only = config.template_gross_check_only
    params.template_accept_score = config.template_accept_score
    params.template_reject_score = config.template_reject_score
    params.template_mismatch_excess_area = config.template_mismatch_excess_area
    params.template_mismatch_missing_area = config.template_mismatch_missing_area
    
    # Convert method string to enum
    if config.template_mismatch_detect_method == "Square Area":
        params.template_mismatch_detect_method = 2  # SQUARE_AREA
    else:
        params.template_mismatch_detect_method = 1  # BLOB_AREA
    
    return params


def calculate_search_window(
    teach_rect: Tuple[int, int, int, int],
    package_offset: Tuple[int, int],
    shift_tolerance: Tuple[int, int],
    is_first_template: bool,
    params: MarkInspectionParameters,
    image_size: Tuple[int, int]
) -> Tuple[int, int, int, int]:
    """
    Calculate search window for template matching
    Matches old C++ logic for computing search rectangles
    
    Args:
        teach_rect: Taught template position (x, y, w, h)
        package_offset: Package location offset (dx, dy)
        shift_tolerance: Shift tolerance (x_tol, y_tol)
        is_first_template: True for first template, False for others
        params: Mark inspection parameters
        image_size: Image dimensions (width, height)
        
    Returns:
        Search window (x, y, w, h) clipped to image bounds
    """
    x, y, w, h = teach_rect
    dx, dy = package_offset
    x_tol, y_tol = shift_tolerance
    
    # Offset by package location (matches C++ code)
    search_x = x + dx
    search_y = y + dy
    
    # Inflate by shift tolerance (matches InflateRect() in C++)
    search_x -= x_tol
    search_y -= y_tol
    search_w = w + 2 * x_tol
    search_h = h + 2 * y_tol
    
    # Clip to image bounds (matches CheckRect() in C++)
    img_w, img_h = image_size
    search_x = max(0, min(search_x, img_w - 1))
    search_y = max(0, min(search_y, img_h - 1))
    search_w = min(search_w, img_w - search_x)
    search_h = min(search_h, img_h - search_y)
    
    return (search_x, search_y, search_w, search_h)


def apply_mark_rotation_tolerance(
    template: np.ndarray,
    rotation_tol: int
) -> List[np.ndarray]:
    """
    Generate rotated versions of template for matching
    Matches old C++ mark rotation handling
    
    Args:
        template: Template image
        rotation_tol: Rotation tolerance in degrees
        
    Returns:
        List of rotated templates
    """
    import cv2
    
    if rotation_tol <= 0:
        return [template]
    
    templates = [template]
    
    # Generate rotated versions from -rotation_tol to +rotation_tol
    # Matches old C++ CreateRotMarkTemplate logic
    for angle in range(-rotation_tol, rotation_tol + 1, 1):
        if angle == 0:
            continue
        
        h, w = template.shape[:2]
        center = (w // 2, h // 2)
        
        # Get rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Rotate template
        rotated = cv2.warpAffine(template, M, (w, h), 
                                 flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT,
                                 borderValue=0)
        templates.append(rotated)
    
    return templates


def check_mark_hole(
    image: np.ndarray,
    template_rect: Tuple[int, int, int, int],
    params: MarkInspectionParameters,
    is_teach: bool = False
) -> Dict[str, Any]:
    """
    Check for holes in mark using blob detection
    Matches old C++ GetBlackBlobCount() function
    
    Implements hole detection exactly as in old application:
    1. Apply threshold based on teach/insp mark contrast
    2. Detect blobs (holes) in binary image
    3. Filter by minimum area - if too high → no holes detected
    4. Filter by minimum XY size - both W and H must meet requirement
    
    Args:
        image: Input grayscale image
        template_rect: Template region (x, y, w, h)
        params: Mark inspection parameters
        is_teach: True if teaching, False if inspecting
        
    Returns:
        Dictionary with hole check results:
            - 'blob_count': Number of holes detected
            - 'detected': True if holes found
            - 'reason': Why holes were/weren't detected
    """
    import cv2
    
    x, y, w, h = template_rect
    
    # Validate ROI bounds
    if x < 0 or y < 0 or x + w > image.shape[1] or y + h > image.shape[0]:
        return {
            'blob_count': 0,
            'detected': False,
            'reason': 'ROI out of bounds'
        }
    
    roi = image[y:y+h, x:x+w]
    
    # Get threshold value
    if is_teach:
        threshold = params.teach_mark_contrast
    else:
        threshold = params.insp_mark_contrast
    
    # Threshold image (matches C++ mark detection)
    # Looking for DARK pixels (holes) in mark
    if params.mark_color == 1:  # WHITE mark (holes are darker)
        _, binary = cv2.threshold(roi, threshold, 255, cv2.THRESH_BINARY_INV)
    else:  # BLACK mark (holes are lighter)
        _, binary = cv2.threshold(roi, threshold, 255, cv2.THRESH_BINARY)
    
    # Find contours (blobs/holes)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, 
                                    cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter by minimum area and size
    valid_blobs = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        x_c, y_c, w_c, h_c = cv2.boundingRect(contour)
        
        # CRITICAL: Must meet BOTH area AND size requirements
        # If Mark Min Area is too high → no holes detected
        # Both width AND height must be >= Mark Min XY Size
        if area >= params.mark_min_area and \
           w_c >= params.mark_min_xy_size and \
           h_c >= params.mark_min_xy_size:
            valid_blobs.append({
                'area': area,
                'width': w_c,
                'height': h_c,
                'bbox': (x_c, y_c, w_c, h_c)
            })
    
    return {
        'blob_count': len(valid_blobs),
        'detected': len(valid_blobs) > 0,
        'blobs': valid_blobs,
        'reason': f"Found {len(valid_blobs)} holes" if valid_blobs else "No holes detected"
    }


def validate_mark_parameters(params: MarkInspectionParameters) -> Tuple[bool, str]:
    """
    Validate mark inspection parameters
    Matches old C++ parameter validation logic
    
    Args:
        params: Mark inspection parameters to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    
    # Check mark sets
    if params.total_mark_set < 1 or params.total_mark_set > 3:
        return False, "Total Mark Set must be between 1 and 3"
    
    # Check symbol sets
    if params.total_symbol_set < 1 or params.total_symbol_set > 5:
        return False, "Total Symbol Set must be between 1 and 5"
    
    # Check rotation tolerance
    if params.mark_rotation_tol < 0 or params.mark_rotation_tol > 360:
        return False, "Mark Rotation Tolerance must be between 0 and 360"
    
    # Check shift tolerances
    if params.first_template_shift_x < 0 or params.first_template_shift_y < 0:
        return False, "First Template Shift Tolerances must be positive"
    
    if params.other_template_shift_x < 0 or params.other_template_shift_y < 0:
        return False, "Other Template Shift Tolerances must be positive"
    
    # Check character sizes
    if params.min_character_size < 1:
        return False, "Min Character Size must be at least 1"
    
    if params.mark_min_x_size < 1 or params.mark_min_y_size < 1:
        return False, "Mark Min X/Y Size must be at least 1"
    
    # Check hole inspection parameters
    if params.hole_check:
        if params.teach_mark_contrast < 0 or params.teach_mark_contrast > 255:
            return False, "Teach Mark Contrast must be between 0 and 255"
        
        if params.insp_mark_contrast < 0 or params.insp_mark_contrast > 255:
            return False, "Insp Mark Contrast must be between 0 and 255"
        
        # CRITICAL: Teach contrast MUST NOT exceed Insp contrast
        # This prevents hole inspection failures
        if params.teach_mark_contrast > params.insp_mark_contrast:
            return False, "Teach Mark Contrast cannot exceed Insp Mark Contrast\n" \
                         f"Teach: {params.teach_mark_contrast}, Insp: {params.insp_mark_contrast}"
        
        # Insp contrast should be in optimal range
        if params.insp_mark_contrast < 120 or params.insp_mark_contrast > 130:
            # Warning, but not failure - allow it
            pass
        
        if params.mark_min_area < 1:
            return False, "Mark Min Area must be at least 1"
        
        if params.mark_min_xy_size < 1:
            return False, "Mark Min XY Size must be at least 1"
    
    # Check accept/reject scores
    if params.first_accept_score < 0 or params.first_accept_score > 100:
        return False, "First Accept Score must be between 0 and 100"
    
    if params.first_reject_score < 0 or params.first_reject_score > 100:
        return False, "First Reject Score must be between 0 and 100"
    
    if params.first_accept_score <= params.first_reject_score:
        return False, "First Accept Score must be greater than Reject Score"
    
    if params.template_accept_score < 0 or params.template_accept_score > 100:
        return False, "Template Accept Score must be between 0 and 100"
    
    if params.template_reject_score < 0 or params.template_reject_score > 100:
        return False, "Template Reject Score must be between 0 and 100"
    
    if params.template_accept_score <= params.template_reject_score:
        return False, "Template Accept Score must be greater than Reject Score"
    
    return True, ""


# Export main functions
__all__ = [
    'MarkInspectionParameters',
    'load_parameters_from_config',
    'calculate_search_window',
    'apply_mark_rotation_tolerance',
    'check_mark_hole',
    'validate_mark_parameters'
]
