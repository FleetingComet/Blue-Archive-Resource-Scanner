import concurrent
import logging

import cv2
import numpy as np

from src.core.area import Region
from src.core.config import Config, Path_Config
from src.core.script_transform import SCRIPT
from src.locations.search import SearchPattern
from src.services.workers import item_ocr_worker
from src.utils.data.io import read_json, write_json
from src.utils.device.interfaces import DeviceController
from src.utils.device.swipe_utils import swipe_with_verification
from src.utils.ocr.color_util import retain_colors
from src.utils.ocr.extract import crop_image
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
      1. Capture fresh grid screenshot (once per scroll, reused for item slot detection)
      2. Click item slot -> detail panel updates (the left side)
      3. If item slot is empty -> end of inventory (items are always packed left-to-right)
      4. Capture detail screenshot

    and then:
    5. Extract name and owned count
    6. Save extracted texts to a file

    After all cols in a row -> advance to next row.
    After all rows in a page -> swipe.

    Termination:
      - swipe_with_verification returns False (no scroll = truly at end)

    Args:
        device (DeviceController): Platform-agnostic device controller
        grid_type (str, optional): Identifier for what "Region" to use. Defaults to "Equipment".
        ocr_workers (int, optional): How many cpu to use. Defaults to max(1, (os.cpu_count() or 4) - 1).

    Returns:
        bool: returns True if the process is completed, False otherwise.
    """

    grid_region = (
        SearchPattern.EQUIPMENT.GRID.value
        if grid_type == "Equipment"
        else SearchPattern.ITEM.GRID.value
    )

    captured_images: list[np.ndarray] = []

    while True:
        screenshot = device.capture_screenshot()

        if screenshot is None:
            logger.error("Failed to capture grid screenshot.")
            return False

        grid = crop_image(
            screenshot,
            grid_region,
        )

        slots = process_grid(grid, grid_region)

        logger.debug(f"[dim]item_grid: found {len(slots)} slots[/dim]")

        # If no items are found at all, we're done
        if not slots:
            break

        for i, (_local_reg, global_reg) in enumerate(slots):
            if Config.settings.debug and i >= 5:
                break  # skip for debug

            point = global_reg.random_point(5)

            device.tap(int(point.x), int(point.y))
            wait(0.2)
            detail_img = device.capture_screenshot()

            if detail_img is not None:
                captured_images.append(detail_img)
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


def process_grid(image: np.ndarray, grid_region) -> list[tuple[Region, Region]]:
    """
    Detects slot boxes in image.
    Returns list of (local_region, global_region) tuples.

    Args:
        image (np.ndarray): cropped grid image
        grid_region (blablaba): grid's region from either equipment or item

    Returns:
        local_region: (x, y, w, h) relative to grid.
        global_region: (full_x, full_y, w, h) relative to image (used for drawing text & tapping).
    """
    manager = SCRIPT._manager
    scale = manager.scale if manager else 1.0

    hex_colors = ["c4cfd4"]
    crop_img, _ = retain_colors(image, hex_colors, tolerance=15)
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Clear the top and bottom 2 border pixels to prevent border bridging
    thresh[:2, :] = 0
    thresh[-2:, :] = 0

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_w = int(80 * scale)
    min_h = int(70 * scale)

    valid_boxes = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect = float(w) / max(1, h)

        # Ignore tiny noise, oversized outer borders, and cut-off bottom rows
        if (w >= min_w) and (h >= min_h) and (0.8 <= aspect <= 1.4):
            valid_boxes.append((x, y, w, h))
            # cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 1)

    # Group boxes whose Y centers are within half a box height of each other
    valid_boxes.sort(key=lambda b: b[1])  # sort by Y first
    rows: list[list[tuple[int, int, int, int]]] = []
    row_threshold = int(25 * scale)

    for box in valid_boxes:
        placed = False
        box_y_center = box[1] + box[3] // 2
        for row in rows:
            row_y_center = row[0][1] + row[0][3] // 2
            if abs(box_y_center - row_y_center) < row_threshold:
                row.append(box)
                placed = True
                break
        if not placed:
            rows.append([box])

    # Sort each row horizontally (Left -> Right) and flatten
    sorted_boxes = []
    for row in rows:
        row.sort(key=lambda b: b[0])
        sorted_boxes.extend(row)

    logger.debug(
        f"{__name__}: Found {len(sorted_boxes)} item boxes across {len(rows)} rows."
    )
    if manager is not None:
        grid_screen_x, grid_screen_y = manager.script_to_device(
            grid_region.x, grid_region.y
        )
    else:
        grid_screen_x, grid_screen_y = int(grid_region.x), int(grid_region.y)

    slots = []
    padding = int(5 * scale)

    for x, y, w, h in sorted_boxes:

        local_reg = Region(
            x=x + padding,
            y=y + padding,
            width=w - (padding * 2),
            height=h - (padding * 2),
        )

        global_reg = Region(
            x=grid_screen_x + x + padding,
            y=grid_screen_y + y + padding,
            width=w - (padding * 2),
            height=h - (padding * 2),
        )

        slots.append((local_reg, global_reg))

    return slots


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
