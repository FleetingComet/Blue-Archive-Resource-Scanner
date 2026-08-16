import concurrent.futures
import logging
import tempfile
import time
from pathlib import Path

import cv2

from src.core.area import Location, Region, Size
from src.core.config import Config
from src.services.workers import item_ocr_worker
from src.utils.data.io import read_json, write_json
from src.utils.device.interfaces import DeviceController
from src.utils.device.swipe_utils import swipe_with_verification
from src.utils.ocr.item_util import is_empty_slot
from src.utils.ocr.text_util import normalize_value

logger = logging.getLogger("BA-Scanner")


# TODO: Fix this
def item_grid(
    device: DeviceController,
    grid_type: str = "Equipment",
    grid_config: dict | None = None,
    ocr_workers=4,
) -> bool:
    """
    Capture a screenshot from the device and perform the ocr.
    Scan the item/equipment grid by iterating page by page, row by row, col by col.

    Flow per loop:
      1. Capture fresh grid screenshot (once per page, reused for all empty checks)
      2. If slot is empty -> end of inventory (items are always packed left-to-right)
      3. Click item -> detail panel updates (the left side)
      4. Capture detail screenshot

    and then:
    5. Extract name + owned count
    6. update_name_owned_counts

    After all cols in a row -> advance to next row.
    After all rows in a page -> swipe.

    Termination:
      - First empty slot hit (items are contiguous, so empty = tail end)
      - swipe_with_verification returns False (no scroll = truly at end)

    Args:
        device (DeviceController): Platform-agnostic device controller
        grid_type (str): "Equipment" or "Items".
        grid_config (dict): Grid configuration from screen_config.json
    Returns:
        bool: True if the process is completed, False otherwise.
    """

    config = grid_config or {
        # Starting coordinates and dimensions
        "start_x": 701 if grid_type == "Items" else 690,
        "start_y": 160,
        "item_width": 110,
        "item_height": 90,
        "cols_per_row": 5,
        "y_padding": 11,  # the padding is 10 but I need extra 1px because some shenanigans are happening
        # equipment_grid_end_y = 660  # Y-end for equipment grid
        # items_grid_end_y = 560  # Y-end for items grid
        "end_y": 560 if grid_type == "Items" else 660,
        # Perform the swipe
        # "swipe_distance": 450,
        # "rows_per_page": 5 if grid_type == "Equipment" else 4,
    }

    grid_start = Location(config["start_x"], config["start_y"])
    item_size = Size(config["item_width"], config["item_height"])
    cols_per_row = config["cols_per_row"]
    grid_end_y = config["end_y"]
    y_padding = config["y_padding"]
    stride_y = item_size.height + y_padding  # 101px per row

    rows_per_page = config.get(
        "rows_per_page",
        int((grid_end_y - grid_start.y) // stride_y),
    )

    # Auto-calculate swipe distance: exactly one full page scroll
    # Start: Bottom of the last row's first item
    # End:   Top of the first row's first item
    # swipe_start_x = grid_start.x + item_size.width // 2
    # swipe_start_y = grid_start.y + (rows_per_page - 1) * stride_y + item_size.height
    swipe_start_y = grid_end_y
    swipe_end_y = grid_start.y  # Top of first row

    with tempfile.TemporaryDirectory(prefix="ba_scanner_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        captured_paths = []
        screen_number = 0

        while True:
            screen_number += 1
            grid_image = device.capture_screenshot()
            if grid_image is None:
                logger.error("Failed to capture grid screenshot.")
                return False

            found_empty: bool = False
            for row in range(rows_per_page):
                if found_empty:
                    break

                current_y = grid_start.y + row * stride_y

                # boundary
                if current_y + item_size.height > grid_end_y:
                    break

                for col in range(cols_per_row):

                    if Config.DEBUG and col != 0:
                        continue  # skip for debug

                    current_x = grid_start.x + col * item_size.width

                    # boundary
                    if current_x + item_size.width > grid_image.shape[1]:
                        break

                    item_region = Region(
                        current_x, current_y, item_size.width, item_size.height
                    )

                    if is_empty_slot(grid_image, item_region):
                        logger.info("Empty slot detected. End of inventory.")
                        found_empty = True
                        break

                    point = item_region.random_point(10)

                    # Tap → minimal wait → capture → save
                    device.tap(int(point.x), int(point.y))
                    time.sleep(0.3 * Config.WAIT_TIME_MULTIPLIER)

                    detail_img = device.capture_screenshot()

                    if detail_img is None:
                        continue

                    save_name = f"p{screen_number}_r{row}_c{col}.png"
                    save_path = tmp_path / save_name
                    cv2.imwrite(str(save_path), detail_img)
                    captured_paths.append(save_path)

            # Stop entirely if an empty slot was hit - no point swiping
            if found_empty:
                break

            # Swipe
            if not swipe_with_verification(
                device,
                grid_start.x,
                grid_start.y,
                swipe_start_y,
                swipe_end_y,
                item_size.width,
                grid_end_y,
                cols_per_row,
            ):
                break
            time.sleep(1.5 * Config.WAIT_TIME_MULTIPLIER)

        logger.info(
            f"\nProcessing {len(captured_paths)} images with {ocr_workers} OCR workers..."
        )
        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=ocr_workers) as executor:
            futures = {
                executor.submit(item_ocr_worker, p, grid_type): p
                for p in captured_paths
            }
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                name, count = result["name"], result["count"]
                if name and count:
                    parsed = normalize_value(count)

                    if parsed is None:
                        logger.info(
                            f"[Scanner] result → name={name!r}, count={count!r}, parsed={parsed!r}"
                        )
                        # Skip malformed counts

                    results[name] = parsed

        if results:
            logger.info(
                f"Found {len(results)} unique items. Writing to {Config.scanned_counts}..."
            )

            existing = read_json(Config.scanned_counts)
            existing.update(results)
            write_json(Config.scanned_counts, existing)

    return True
