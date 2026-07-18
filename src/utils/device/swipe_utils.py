import logging
import time

import numpy as np

from src.utils.device.interfaces import DeviceController

logger = logging.getLogger("BA-Scanner")


def swipe_with_verification(
    device: DeviceController,
    start_x: int,
    start_y: int,
    swipe_start_y: int,
    swipe_end_y: int,
    item_width: int,
    grid_end_y: int,
    cols_per_row: int = 5,
    max_retries: int = 2,
) -> bool:
    """
    Swipe with screenshot verification to ensure it actually scrolled.
    """
    swipe_start_x = start_x + item_width // 2

    for attempt in range(max_retries):
        # Capture before swipe
        before = device.capture_screenshot()

        # Perform swipe
        device.swipe(
            swipe_start_x,
            swipe_start_y - 5,
            swipe_start_x,
            swipe_end_y,
            duration_ms=2000,
        )

        # Wait for animation
        time.sleep(2.5)

        # Capture after swipe
        after = device.capture_screenshot()

        # Verify screen changed using full grid region
        if _screens_are_different(
            before, after, start_x, start_y, item_width, grid_end_y, cols_per_row
        ):
            return True
        logger.warning(
            "[bold yellow]Swipe: [/bold yellow] Attempt {attempt + 1} failed, retrying..."
        )

    return False


def _screens_are_different(
    before: np.ndarray,
    after: np.ndarray,
    start_x: int,
    start_y: int,
    item_width: int,
    grid_end_y: int,
    cols_per_row: int = 5,
    threshold: float = 0.05,
) -> bool:
    """
    Compare the full grid region to detect if swipe actually changed content.
    """
    if before is None or after is None:
        return False

    grid_height = grid_end_y - start_y
    grid_width = item_width * cols_per_row

    before_sample = before[
        start_y : start_y + grid_height, start_x : start_x + grid_width
    ]
    after_sample = after[
        start_y : start_y + grid_height, start_x : start_x + grid_width
    ]

    if before_sample.shape != after_sample.shape:
        return True

    diff = np.abs(before_sample.astype(float) - after_sample.astype(float))
    diff_ratio = np.mean(diff) / 255.0

    logger.info(
        f"[bold yellow]Swipe: [/bold yellow] diff_ratio = {diff_ratio:.4f}  (threshold = {threshold})"
    )

    return diff_ratio > threshold
