import logging
from pathlib import Path
from typing import Optional

import cv2

from src.core.area import Region

logger = logging.getLogger("BA-Scanner")


# * Will leave this here, maybe we can use this in future
def match_image_using_directory(
    input_image, reference_image_paths: list[Path], threshold=0.9, grayscale=False
):
    """Match the input image against reference images using template matching."""
    best_match_name = None
    current_max_value = -1

    if input_image is None or input_image.size == 0:
        return None

    if grayscale and len(input_image.shape) == 3:
        input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    # Ensure 3-channel if not grayscale (strips alpha)
    if input_image.ndim == 3 and input_image.shape[2] == 4:
        input_image = input_image[:, :, :3]

    inp_h, inp_w = input_image.shape[:2]

    for reference_path in reference_image_paths:
        ref_flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
        reference_image = cv2.imread(str(reference_path), ref_flag)

        if reference_image is None:
            continue

        # If template is larger, resize it to fit within the input image bounds
        ref_h, ref_w = reference_image.shape[:2]
        if ref_h > inp_h or ref_w > inp_w:
            scale = min(inp_h / ref_h, inp_w / ref_w)
            # We scale down slightly more (0.9) to ensure it fits comfortably
            # and leaves room for the sliding window matching
            new_size = (int(ref_w * scale), int(ref_h * scale))

            # If the calculated size is 0, skip
            if new_size[0] < 1 or new_size[1] < 1:
                continue

            reference_image = cv2.resize(
                reference_image, new_size, interpolation=cv2.INTER_AREA
            )

        try:
            result = cv2.matchTemplate(
                input_image, reference_image, cv2.TM_CCOEFF_NORMED
            )
            _, max_value, _, _ = cv2.minMaxLoc(result)

            logger.info(f"Max Value for {reference_path}: {max_value}")

            # Check if this is the best match so far
            if max_value > current_max_value:
                current_max_value = max_value
                best_match_name = reference_path
                if max_value >= 0.99:
                    break
        except cv2.error as e:
            logger.error(f"[red]Matcher: {e}[/red]")
            continue

    if current_max_value >= threshold:
        return best_match_name

    return None


def find_template_location(
    input_image, reference_image_path: Path, threshold=0.8, grayscale=False
) -> Optional[Region]:
    """
    Find the location of a template in the input image.

    Returns:
        Region class or None if not found
    """
    # Convert input image to grayscale if needed.
    if grayscale:
        input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    # Ensure input image has 3 channels if not in grayscale.
    if not grayscale and input_image.ndim == 3 and input_image.shape[2] == 4:
        input_image = input_image[:, :, :3]

    ref_flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
    reference_image = cv2.imread(str(reference_image_path), ref_flag)

    if reference_image is None:
        logger.error(f"Failed to load reference image: {str(reference_image_path)}")
        return None

    result = cv2.matchTemplate(input_image, reference_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    logger.info(f"Max Value for {reference_image_path}: {max_val}")

    if max_val >= threshold:
        # Get the dimensions of the template
        h, w = reference_image.shape[:2]
        x, y = max_loc
        return Region(x=x, y=y, width=w, height=h)

    return None
