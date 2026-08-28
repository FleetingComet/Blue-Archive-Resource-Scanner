import concurrent
import logging

import cv2
import numpy as np

from src.core.area import Region
from src.core.config import Config, Path_Config
from src.services.workers import item_ocr_worker
from src.utils.data.io import read_json, write_json
from src.utils.device.interfaces import DeviceController
from src.utils.device.swipe_utils import swipe_with_verification
from src.utils.ocr.color_util import retain_colors
from src.utils.ocr.extract import crop_image
from src.utils.ocr.item_util import is_empty_slot
from src.utils.ocr.text_util import normalize_value
from src.utils.wait_utils import wait

logger = logging.getLogger("BA-Scanner")


def item_grid(
    device: DeviceController,
    grid_type: str = "Equipment",
    ocr_workers: int = 2,
) -> bool:
    """
    Capture a screenshot from the device and perform the ocr.
    Scan the item/equipment grid by clicking item by item, then process them using ocr.

    Flow per loop:
      1. Capture fresh grid screenshot (once per scroll, reused for all empty checks and item slot detection)
      2. Click item slot -> detail panel updates (the left side)
      3. If item slot is empty -> end of inventory (items are always packed left-to-right)
      4. Capture detail screenshot

    and then:
    5. Extract name and owned count
    6. Save extracted texts to a file

    After all cols in a row -> advance to next row.
    After all rows in a page -> swipe.

    Termination:
      - First empty slot hit (items are contiguous, so empty = tail end)
      - swipe_with_verification returns False (no scroll = truly at end)

    Args:
        device (DeviceController): Platform-agnostic device controller
        grid_type (str, optional): Identifier for what "Region" to use. Defaults to "Equipment".
        ocr_workers (int, optional): How many cpu to use. Defaults to max(1, (os.cpu_count() or 4) - 1).

    Returns:
        bool: returns True if the process is completed, False otherwise.
    """

    grid_region = None

    if grid_type == "Equipment":
        grid_region = Region(x=660, y=150, width=572, height=530)  # equip
    else:
        grid_region = Region(x=663, y=150, width=573, height=450)  # items

    captured_images: list[np.ndarray] = []
    swipe_iteration = 0

    while True:
        swipe_iteration += 1
        image = device.capture_screenshot()

        if image is None:
            logger.error("Failed to capture grid screenshot.")
            return False

        grid = crop_image(
            image,
            grid_region,
        )

        found_empty: bool = False

        valid_regions = process_grid(grid, grid_region)
        logger.debug(
            f"[dim]item_grid: {swipe_iteration=}, found {len(valid_regions)} slots[/dim]"
        )

        for i, region in enumerate(valid_regions):
            if Config.settings.debug and i >= 5:
                break  # skip for debug

            if is_empty_slot(image, region):
                logger.info("Empty slot detected. End of inventory.")
                found_empty = True
                break

            point = region.random_point(5)

            # Tap -> minimal wait -> capture -> save
            device.tap(int(point.x), int(point.y))
            wait(0.3)
            detail_img = device.capture_screenshot()

            if detail_img is None:
                logger.debug(
                    f"[yellow]item_grid: slot {i} capture failed, skipping[/yellow]"
                )
                continue
            captured_images.append(detail_img)
            # save_name = f"s_{screen_number}_item_{i}.png"
            # save_path = tmp_path / save_name
            # cv2.imwrite(str(save_path), detail_img)
            # captured_paths.append(save_path)

        # Stop entirely if an empty slot was hit - no point swiping
        if found_empty:
            break
        # Swipe
        if not swipe_with_verification(device=device, grid_region=grid_region):
            break
        wait(1.5)

    results = process_ocr_results(captured_images, grid_type, ocr_workers)

    if results:
        logger.info(
            f"Found {len(results)} unique items. Writing to {Path_Config.scanned_counts}..."
        )

        existing = read_json(Path_Config.scanned_counts)
        existing.update(results)
        write_json(Path_Config.scanned_counts, existing)

    return True


def process_grid(image, grid_region):
    hex_colors = ["c4cfd4"]
    crop_img, _ = retain_colors(image, hex_colors, tolerance=6)
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    valid_boxes = []
    image_area = crop_img.shape[0] * crop_img.shape[1]

    for i, contour in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h

        # Basic shape validation
        if w < 70 or h < 80:
            continue

        aspect_ratio = float(w) / h

        # Filter out the massive outer border (must be less than 85% of image)
        # Filter out tiny noise (must be greater than 100 pixels)
        # Relaxed aspect ratio to catch slightly stretched/squashed boxes
        if 100 < area < (image_area * 0.85) and 0.2 < aspect_ratio < 4.0:
            valid_boxes.append((x, y, w, h))
            # cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Sort the boxes from top-left to bottom-right (useful for grid processing)
    # Sorting by Y (row) first, then X (column)
    # Divide by 80 (min box height) to group rows correctly
    valid_boxes = sorted(valid_boxes, key=lambda b: (b[1] // 80, b[0]))
    logger.info(f"Found {len(valid_boxes)} item boxes.")
    valid_regions = []

    for i, (x, y, w, h) in enumerate(valid_boxes):
        # Add a small padding
        padding = 5

        full_x = x + grid_region.x
        full_y = y + grid_region.y

        valid_regions.append(
            Region(
                x=full_x + padding,
                y=full_y + padding,
                width=w - padding * 2,
                height=h - padding * 2,
            )
        )

    return valid_regions


def process_ocr_results(
    captured_images: list, grid_type: str, ocr_workers: int
) -> dict:
    """
    Processes captured images using a ThreadPoolExecutor for OCR.
    """
    results = {}
    if not captured_images:
        return results

    logger.info(
        f"\nProcessing {len(captured_images)} images with {ocr_workers} OCR workers..."
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=ocr_workers) as executor:
        futures = {
            executor.submit(item_ocr_worker, img, grid_type): idx
            for idx, img in enumerate(captured_images)
        }

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                name, count = result["name"], result["count"]

                if name and count:
                    parsed = normalize_value(count, default=None)

                    if parsed is None:
                        logger.info(
                            f"[Scanner] result -> name={name!r}, count={count!r}, parsed={parsed!r}"
                        )
                        # Skip malformed counts
                        continue

                    results[name] = parsed
            except Exception as e:  # noqa: BLE001
                logger.error(f"OCR worker failed: {e}")

    return results
