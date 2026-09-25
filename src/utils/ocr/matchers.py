import logging
from pathlib import Path

import cv2
import numpy as np

from src.core.area import Region
from src.core.config import Config

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

            logger.debug(f"Max Value for {reference_path}: {max_value}")

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
    input_image,
    reference_image_path: Path,
    threshold=0.8,
    grayscale=False,
    scale: float = 1.0,
) -> Region | None:
    """
    Find the location of a template in the input image.

    Returns:
        Region class or None if not found
    """

    reference_image = cv2.imread(str(reference_image_path), cv2.IMREAD_UNCHANGED)
    if reference_image is None:
        logger.error(f"Failed to load reference image: {reference_image_path!s}")
        return None

    # Split off alpha as mask if present.
    mask = None
    if reference_image.ndim == 3 and reference_image.shape[2] == 4:
        mask = reference_image[:, :, 3]
        reference_image = reference_image[:, :, :3]
        # Fully-opaque alpha is redundant - drop it so we get the better matcher.
        if int(mask.min()) == 255:
            mask = None

    if mask is not None:
        # Binarize: only trust pixels that are (near) fully opaque.
        _, mask = cv2.threshold(mask, 250, 255, cv2.THRESH_BINARY)
        # Erode to drop the anti-aliased edge ring, which carries
        # blended-background color contamination, not real icon color.
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)

    # Optional scaling (scale the mask too).
    if scale != 1.0:
        new_w = round(reference_image.shape[1] * scale)
        new_h = round(reference_image.shape[0] * scale)
        reference_image = cv2.resize(
            reference_image, (new_w, new_h), interpolation=cv2.INTER_LINEAR
        )
        if mask is not None:
            mask = cv2.resize(mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST)

    # Ensure input image has 3 channels.
    if input_image.ndim == 3 and input_image.shape[2] == 4:
        input_image = input_image[:, :, :3]

    if grayscale:
        if input_image.ndim == 3:
            input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
        if reference_image.ndim == 3:
            reference_image = cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY)

    if mask is not None:
        result = cv2.matchTemplate(
            input_image, reference_image, cv2.TM_SQDIFF_NORMED, mask=mask
        )
        # Masked CCORR_NORMED can produce NaN/inf (uniform regions) or values >1.
        result = np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)
        result = np.clip(result, 0.0, 1.0)
        # SQDIFF: lower is better, so convert to a "higher is better" score
        # to keep the same threshold semantics as the rest of the function.
        min_val, _max_val, min_loc, _max_loc = cv2.minMaxLoc(result)
        max_val, max_loc = 1.0 - min_val, min_loc
    else:
        result = cv2.matchTemplate(input_image, reference_image, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)

    logger.debug(f"Max Value for {reference_image_path}: {max_val}")
    print(
        f"Match score for {reference_image_path.name}: {max_val:.4f} (threshold={threshold})"
    )

    # if max_val >= threshold:
    # if max_val >= mask_threshold:
    if max_val >= threshold and _verify_match(
        input_image, reference_image, mask, max_loc
    ):
        # Get the dimensions of the template
        h, w = reference_image.shape[:2]
        x, y = max_loc
        return Region(x=x, y=y, width=w, height=h)

    return None


def _verify_match(input_image, reference_image, mask, loc, max_mean_diff=25.0) -> bool:
    x, y = loc
    h, w = reference_image.shape[:2]
    crop = input_image[y : y + h, x : x + w]
    if crop.shape[:2] != (h, w):
        return False
    diff = cv2.absdiff(crop, reference_image)
    print(f"{diff=}")
    if mask is not None:
        m = mask.astype(bool)
        if not m.any():
            return False
        mean_diff = diff[m].mean()
    else:
        mean_diff = diff.mean()

    print(f"{mean_diff=}")
    return mean_diff <= max_mean_diff
