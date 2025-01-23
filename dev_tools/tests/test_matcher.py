import cv2
from region import Region


def match_template(image_path, template_path, threshold=0.9) -> Region:
    """
    Match a template in an image and return the matched region.

    Args:
        image_path (str): Path to the main image.
        template_path (str): Path to the template image.
        threshold (float): Matching threshold (default is 0.8).

    Returns:
        Region: The matched region as a Region object, or None if no match is found.
    """
    # Load the main image and the template
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

    # Ensure images are loaded
    if image is None or template is None:
        raise ValueError("Could not load the image or template.")

    # Get template dimensions
    h, w = template.shape[:2]

    # Perform template matching
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Check if the match meets the threshold
    if max_val >= threshold:
        top_left = max_loc
        return Region(top_left[0], top_left[1], w, h)

    return None  # No match found above the threshold
