import cv2
import numpy as np

from src.core.area import Region
from src.utils.ocr.color_util import hex_to_bgr


def is_empty_slot(
    image,
    region: Region,
    empty_slot_hex="c4cfd4",
    tolerance=10,
    coverage_threshold=0.90,
):
    """
    Check if the given region is an empty slot by verifying
    that the majority of pixels match the known empty slot background color.

    Parameters:
        image: Input BGR image.
        region: Object with .x, .y, .width, .height attributes.
        empty_slot_hex: Hex color of the empty slot background.
        tolerance: Per-channel tolerance for color matching.
        coverage_threshold: Fraction of pixels that must match to be considered empty (0.0-1.0).

    Returns:
        bool: True if the slot appears empty.
    """
    rx = int(region.x)
    ry = int(region.y)
    rw = int(region.right)
    rh = int(region.bottom)

    roi = image[ry:rh, rx:rw]
    
    if roi is None or roi.size == 0:
        return True

    if roi.ndim == 3 and roi.shape[2] == 4:
        roi = roi[:, :, :3]

    target_bgr = hex_to_bgr(empty_slot_hex)
    lower = np.array([max(c - tolerance, 0) for c in target_bgr], dtype=np.uint8)
    upper = np.array([min(c + tolerance, 255) for c in target_bgr], dtype=np.uint8)

    mask = cv2.inRange(roi, lower, upper)
    matching_ratio = np.count_nonzero(mask) / mask.size

    return matching_ratio >= coverage_threshold
