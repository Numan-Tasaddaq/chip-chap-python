# tests/measurement_draw.py
"""
Drawing utilities for measurement visualization.
Draws green/red boxes and lines on images to show detected regions.
"""

import cv2
import numpy as np


def draw_measurement_result(image, roi, measurement_name, status, measured_value,
                            expected_min, expected_max, points_data=None):
    """
    Draw measurement result on image with overlays.
    
    Args:
        image: Input BGR image (will be copied to avoid modifying original)
        roi: Package ROI (x, y, w, h)
        measurement_name: Name like "Body Length" or "Body Width"
        status: "PASS" or "FAIL"
        measured_value: Measured value (int or float)
        expected_min: Minimum threshold
        expected_max: Maximum threshold
        points_data: Optional dict with edge detection data:
            {
                "left_x": x_coord,
                "right_x": x_coord,
                "top_y": y_coord,
                "bottom_y": y_coord,
                "center_y": y_coord (for length),
                "center_x": x_coord (for width)
            }
    
    Returns:
        New image with overlays (original image not modified)
    """
    # CRITICAL: Create a copy to avoid modifying the original image
    # This prevents visualization from affecting subsequent measurements
    image = np.copy(image)
    
    x, y, w, h = roi
    color = (0, 255, 0) if status == "PASS" else (0, 0, 255)  # Green or Red in BGR
    thickness = 2

    if measurement_name == "Body Length" and points_data:
        # Draw vertical lines at left and right edges
        left_x = int(points_data.get("left_x", x))
        right_x = int(points_data.get("right_x", x + w))
        center_y = int(points_data.get("center_y", y + h / 2))
        roi_top = y
        roi_bottom = y + h

        # Draw left edge line (vertical)
        cv2.line(image, (left_x, roi_top), (left_x, roi_bottom), color, thickness)
        # Draw right edge line (vertical)
        cv2.line(image, (right_x, roi_top), (right_x, roi_bottom), color, thickness)
        # Draw measurement line at center
        cv2.line(image, (left_x, center_y), (right_x, center_y), color, thickness + 1)

        # Add text label with value
        label = f"{measurement_name}: {measured_value}px"
        cv2.putText(image, label, (left_x + 10, center_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    elif measurement_name == "Body Width" and points_data:
        # Draw horizontal lines at top and bottom edges
        top_y = int(points_data.get("top_y", y))
        bottom_y = int(points_data.get("bottom_y", y + h))
        center_x = int(points_data.get("center_x", x + w / 2))
        roi_left = x
        roi_right = x + w

        # Draw top edge line (horizontal)
        cv2.line(image, (roi_left, top_y), (roi_right, top_y), color, thickness)
        # Draw bottom edge line (horizontal)
        cv2.line(image, (roi_left, bottom_y), (roi_right, bottom_y), color, thickness)
        # Draw measurement line at center
        cv2.line(image, (center_x, top_y), (center_x, bottom_y), color, thickness + 1)

        # Add text label with value
        label = f"{measurement_name}: {measured_value}px"
        cv2.putText(image, label, (center_x + 10, top_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Draw ROI rectangle as border
    roi_rect_color = (100, 255, 100) if status == "PASS" else (100, 100, 255)
    cv2.rectangle(image, (x, y), (x + w, y + h), roi_rect_color, 2)

    return image


def add_status_text(image, status, position=(50, 50)):
    """
    Add large PASS/FAIL text to image.
    
    Args:
        image: Input BGR image
        status: "PASS" or "FAIL"
        position: (x, y) tuple for text position
    
    Returns:
        Modified image
    """
    color = (0, 255, 0) if status == "PASS" else (0, 0, 255)  # Green or Red
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2.0
    thickness = 3

    # Add semi-transparent background for text readability
    text = status
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = position
    cv2.rectangle(image, (x - 5, y - text_h - 5), (x + text_w + 5, y + baseline + 5),
                  (0, 0, 0), -1)  # Black background

    cv2.putText(image, text, position, font, font_scale, color, thickness)
    return image
