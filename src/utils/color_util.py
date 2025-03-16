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


def remove_colors(image, hex_colors, tolerance=5, black_bg=False):
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

    if image is None:
        raise ValueError("Input image is None.")

    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    else:
        if image.shape[2] == 4:
            image = image[:, :, :3]

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
    
    if black_bg:
        result[combined_mask != 0] = (0, 0, 0)
    return result, combined_mask

def retain_colors(image, hex_colors, tolerance=5):
    """
    Retain only the pixels in the image that match any of the hex colors (with given tolerance).
    Pixels that don't match will be set to white.

    Parameters:
      image: Input image (BGR, 3-channel).
      hex_colors: List of hex strings (e.g., ["d8dadc", "dceffa", ...]).
      tolerance: Tolerance for each channel (default 5).

    Returns:
      result: The image with only the specified colors retained.
      combined_mask: The mask of pixels matching the specified colors.
    """
    if image.ndim == 3 and image.shape[2] == 4:
            image = image[:, :, :3]

    
    combined_mask = None

    for hex_color in hex_colors:
        # Convert hex to BGR tuple (assuming hex is in RGB order)
        target_bgr = hex_to_bgr(hex_color)
        # Build lower and upper bounds with tolerance
        lower = np.array([max(c - tolerance, 0) for c in target_bgr], dtype=np.uint8)
        upper = np.array([min(c + tolerance, 255) for c in target_bgr], dtype=np.uint8)

        # Create a mask for the current color
        mask = cv2.inRange(image, lower, upper)

        # Combine with previous masks using bitwise OR
        if combined_mask is None:
            combined_mask = mask
        else:
            combined_mask = cv2.bitwise_or(combined_mask, mask)

    # Create a black background
    result = np.full_like(image, (0, 0, 0))
    # Copy over only the pixels that match the specified colors
    result[combined_mask != 0] = image[combined_mask != 0]

    return result, combined_mask

def remove_non_white(image, tolerance=0):
    """
    Replace all non-white pixels in an image with black.
    
    Parameters:
        image (np.array): Input image (BGR, 3-channel).
        tolerance (int): How close to 255 a channel must be to be considered white.
                         Default is 0 (only pure white [255,255,255] is considered white).
                         For example, tolerance=10 considers pixels with each channel
                         >= 245 as white.
    
    Returns:
        np.array: The resulting image with non-white pixels set to white.
    """
    # Ensure the image is a 3-channel BGR image.
    if image.ndim == 2:  # grayscale
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.ndim == 3 and image.shape[2] == 4:  # has alpha channel
        image = image[:, :, :3]

    # Define the lower and upper bounds for white.
    lower = np.array([255 - tolerance, 255 - tolerance, 255 - tolerance], dtype=np.uint8)
    upper = np.array([255, 255, 255], dtype=np.uint8)
    
    # Create a mask of pixels that are considered white.
    white_mask = cv2.inRange(image, lower, upper)
    
    # Create a copy of the image. Replace pixels that are NOT white (mask==0) with black.
    result = image.copy()
    # result[white_mask == 0] = [255, 255, 255]
    result[white_mask == 0] = [0, 0, 0]
    
    return result

def retain_specific_color(image, hex_color, tolerance=5, black_bg=False):
    """
    Retain only the pixels in the image that match the specified hex color,
    and replace all other pixels with white.

    Parameters:
        image (np.array): Input image (BGR, 3-channel expected).
        hex_color (str): The hex color string to retain (e.g., "0f87bc").
        tolerance (int): Tolerance for each channel (default is 5).

    Returns:
        result (np.array): The image with only the specified color retained.
        mask (np.array): The mask of pixels matching the specified color.
    """
    # Ensure the image has 3 channels (remove alpha if necessary)
    if image.ndim == 3 and image.shape[2] == 4:
        image = image[:, :, :3]
    elif image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    # Convert hex to BGR using your existing function (assumed to be defined elsewhere)
    target_bgr = hex_to_bgr(hex_color)

    # Build lower and upper bounds for the target color
    lower = np.array([max(c - tolerance, 0) for c in target_bgr], dtype=np.uint8)
    upper = np.array([min(c + tolerance, 255) for c in target_bgr], dtype=np.uint8)

    # Create a mask: pixels within bounds will be 255, others 0
    mask = cv2.inRange(image, lower, upper)

    # Create a result image: start with a white background
    if black_bg:
        result = np.full_like(image, (0, 0, 0))
    else:
        result = np.full_like(image, (255, 255, 255))
    # Copy the original color pixels where the mask is non-zero
    result[mask != 0] = image[mask != 0]

    return result, mask