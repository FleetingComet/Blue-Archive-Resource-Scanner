import logging
from pathlib import Path

import cv2
import numpy as np

from src.core.area import Region
from src.core.config import Config
from src.enums.ExtractionMode import ExtractionMode
from src.locations.search import SearchPattern
from src.utils.data.text_matcher import find_closest
from src.utils.ocr.color_util import (
    retain_colors,
)
from src.utils.ocr.matchers import find_template_location
from src.utils.ocr.ocr_helper import extract_text, extract_text_talent
from src.utils.ocr.preprocessor import preprocess_image_for_ocr
from src.utils.ocr.star_util import count_blue_stars_adaptive, count_stars
from src.utils.ocr.text_util import get_tier_level

logger = logging.getLogger("BA-Scanner")


def crop_image(image, region: Region):
    """Crop the image to the specified region."""
    return image[region.y : region.bottom, region.x : region.right]


def extract_from_region(image, region: Region, mode: ExtractionMode = None):
    """
    Extract text from a specific region in the screenshot.

    Args:
        image: OpenCV image (a NumPy array).
        region (Region): The region to extract text from.
        mode (ExtractionMode): The type of image. Supported types include:
            - BOND_LEVEL = "number_in_circle": For numeric values inside a circle (like bond level).
            - SKILL_LEVEL = "skill_level_indicator": For skill level indicators, hybrid type (e.g., matching "MAX" image then extract text).
            - LEVEL = "level_indicator" or NUMBER = "number": For level indicators or numbers.
            - MULTI_LINE_NAME = "multi_line_name": For multi line text labels (e.g. Names on Equipment and Items).
            - NAME = "name" or TEXT = "text": For text labels.
            - GEAR = "gear": For gear tiers (e.g., "T9", "T7").
            - UE_LEVEL = "ue_level": For removing non-white colors
            - TALENT = "talent": Special extract text method
            ## Shape-based modes (Counting)
            - STAR = "star"
            - UE_STAR = "ue_star"
            - Otherwise, default processing is applied.

    Returns:
        str: The extracted text, or None if extraction fails.
    """
    logger.debug(f"[dim]extract_from_region: {mode=}, {region=}[/dim]")

    crop_img = crop_image(image, region)

    if crop_img is None:
        logger.debug("[yellow]extract_from_region: empty crop, aborting[/yellow]")
        return None

    # * Non OCR Counting (shape-based, not text-based)
    if mode == ExtractionMode.STAR:
        hex_colors = ["fee424"]
        cleaned, _ = retain_colors(crop_img, hex_colors, tolerance=20)
        return count_stars(cleaned)

    if mode == ExtractionMode.UE_STAR:
        return count_blue_stars_adaptive(crop_img, debug=False)

    # * Match Template (image-based)
    if mode == ExtractionMode.SKILL_LEVEL:
        TEMPLATE_PATH = Path("assets/images/templates/max.png")
        if find_template_location(crop_img, TEMPLATE_PATH):
            return "MAX"

    processed_img = preprocess_image_for_ocr(crop_img, mode)

    if processed_img is None:
        return None

    # * Multi-line Text OCR
    if mode == ExtractionMode.MULTI_LINE_NAME:
        return extract_multiline_text(processed_img)

    if mode == ExtractionMode.TALENT:
        text = extract_text_talent(processed_img)
    else:
        text = extract_text(processed_img)

    if text is None:
        return None

    if mode == ExtractionMode.GEAR:
        return get_tier_level(text)

    if mode == ExtractionMode.SKILL_LEVEL and find_closest(text.upper(), ["MAX"]):
        return "MAX"

    logger.debug(f"[green]extract_from_region result:[/green] {text!r}")

    return (
        text.replace("\r", "")
        .replace("\n", " ")
        # for replacing left and right single quotes to '
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )


def extract_item_name(image, grid_type: str = "Equipment") -> str:
    """
    Extract the item name from a predetermined region in the screenshot.
    """
    pattern = (
        SearchPattern.EQUIPMENT.NAME.value
        if grid_type == "Equipment"
        else SearchPattern.ITEM.NAME.value
    )
    return extract_from_region(
        image,
        pattern,
        mode=ExtractionMode.MULTI_LINE_NAME,
    )


def extract_owned_count(image_path: str, grid_type: str = "Equipment") -> str:
    """
    Extract the owned count from a predetermined region in the screenshot.
    """
    pattern = (
        SearchPattern.EQUIPMENT.OWNED.value
        if grid_type == "Equipment"
        else SearchPattern.ITEM.OWNED.value
    )

    return extract_from_region(
        image_path,
        pattern,
    )


def split_text_lines(
    binary_image: np.ndarray,
    min_gap=2,
    min_line_height=3,
    min_pixels_per_row=20,
):
    """
    Split a thresholded image into horizontal text-line regions.

    Args:
        binary_image: Thresholded/preprocessed image where text pixels are non-zero.
        min_gap: Number of consecutive empty rows required to separate lines.
        min_line_height: Minimum height required for a detected line.
        min_pixels_per_row: Minimum number of non-zero pixels for a row
            to be considered part of a text line.

    Returns:
        List of (y_start, y_end) tuples.
    """
    row_pixel_count = np.count_nonzero(binary_image, axis=1)
    row_has_text = row_pixel_count >= min_pixels_per_row

    logger.debug(f"row_pixel_count={row_pixel_count}")
    logger.debug(f"row_has_text={row_has_text}")

    lines = []
    start = None
    gap = 0

    for y, has_text in enumerate(row_has_text):
        if has_text:
            if start is None:
                start = y
            gap = 0

        elif start is not None:
            gap += 1

            if gap >= min_gap:
                end = y - gap

                if end - start >= min_line_height:
                    lines.append((start, end))

                start = None

    # Handle text that reaches the bottom of the image.
    if start is not None:
        end = len(row_has_text) - 1

        if end - start >= min_line_height:
            lines.append((start, end))

    logger.debug(f"line_bounds={lines}")

    return lines


def extract_multiline_text(processed_img: np.ndarray):

    logger.debug(
        f"[dim]extract_multiline_text: image shape={processed_img.shape}[/dim]"
    )

    line_bounds = split_text_lines(processed_img)

    if Config.settings.debug:
        _debug_img = cv2.resize(
            processed_img,
            None,
            fx=2,
            fy=4,
            interpolation=cv2.INTER_NEAREST,
        )

    # No lines detected -> OCR the entire region.
    if not line_bounds:
        text = extract_text(processed_img)
        return text.strip() if text else None

    lines = []

    for y_start, y_end in line_bounds:
        pad = 2

        y1 = max(0, y_start - pad)
        y2 = min(processed_img.shape[0], y_end + pad)

        band = processed_img[y1:y2, :]

        if Config.settings.debug:
            logger.debug(f"OCR band: y={y1}:{y2}, shape={band.shape}")

            _debug_band = cv2.resize(
                band,
                None,
                fx=2,
                fy=4,
                interpolation=cv2.INTER_NEAREST,
            )

        text = extract_text(band)

        if text and text.strip():
            text = text.strip()
            lines.append(text)

            logger.debug(f"OCR line={text!r}")

    logger.debug(f"OCR lines={lines}")

    return " ".join(lines) if lines else None
