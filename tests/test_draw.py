import cv2

def draw_test_result(image, lines, status):
    """
    Draw inspection result (PASS/FAIL only) on top-left of image.
    Returns tuple of (overlay_image, reason_text)
    
    Args:
        image: Input image
        lines: List of reason lines to be displayed in dialog
        status: "PASS" or "FAIL"
    
    Returns:
        Tuple of (overlay_image, reason_text)
    """
    overlay = image.copy()
    color = (0, 255, 0) if status == "PASS" else (0, 0, 255)

    # Draw only the status on the image
    cv2.putText(
        overlay,
        status,
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        color,
        2,
        cv2.LINE_AA
    )

    # Combine all reason lines into a single string for dialog display
    reason_text = "\n".join(lines) if isinstance(lines, list) else str(lines)

    return overlay, reason_text
