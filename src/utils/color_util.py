import cv2
import numpy as np


def hex_to_bgr(hex_color):
    """
    Convert a hex color string (e.g., "d8dadc") to a BGR tuple.

    Returns:
        b, g, r
    """
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    # OpenCV uses BGR
    return (b, g, r)


def remove_colors(image, hex_colors, tolerance=5):
    """
    Remove the pixels in the image that match any of the hex colors (with given tolerance).
    The removal is done by setting matching pixels to white.

    Parameters:
      image: Input image (BGR, 3-channel).
      hex_colors: List of hex strings (e.g., ["d8dadc", "dceffa", ...]).
      tolerance: Tolerance for each channel (default 10).

    Returns:
      :result: The image with the specified colors removed.
      :combined_mask: The mask of removed pixels.
    """
    combined_mask = None

    for hex_color in hex_colors:
        # Convert hex to BGR tuple
        target_bgr = hex_to_bgr(hex_color)
        # Build lower and upper bounds with tolerance
        lower = np.array([max(c - tolerance, 0) for c in target_bgr], dtype=np.uint8)
        upper = np.array([min(c + tolerance, 255) for c in target_bgr], dtype=np.uint8)

        # Create a mask for the current color
        mask = cv2.inRange(image, lower, upper)

        # Combine with previous masks
        if combined_mask is None:
            combined_mask = mask
        else:
            combined_mask = cv2.bitwise_or(combined_mask, mask)

    # Remove the color by setting those pixels to white
    result = image.copy()
    result[combined_mask != 0] = (255, 255, 255)
    return result, combined_mask
