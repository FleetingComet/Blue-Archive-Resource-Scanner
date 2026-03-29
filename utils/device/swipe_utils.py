import cv2
import time
import numpy as np
from utils.device.adb_controller import ADBController
from utils.device.inputs.input_controller import InputController


def swipe(
    adb_controller: ADBController,
    swipe_distance: int,
    start_x: int,
    start_y: int,
    item_width: int,
):
    """
    Perform a swipe gesture to scroll down the screen.

    Args:
        adb_controller (ADBController): An instance of ADBController.
        swipe_distance (int): The vertical distance to swipe.
        start_x (int): The starting x-coordinate.
        start_y (int): The starting y-coordinate.
        item_width (int): The width of an item in the grid.
    """

    swipe_start_x = (
        start_x + item_width // 2
    )  # Center of the item, can't work if it's on the very x of the grid x
    swipe_start_y = start_y + swipe_distance  # Start from the bottom of the grid
    swipe_end_y = start_y  # Swipe to the top of the grid

    adb_controller.execute_command(
        f"shell input swipe {swipe_start_x} {swipe_start_y} {swipe_start_x} {swipe_end_y} 2000"
    )
    # adb_controller.execute_command(
    #     f"shell input swipe {start_x + item_width} {swipe_distance} {start_x + item_width} {start_y} 500"
    # )

    print(
        f"Swiped from ({swipe_start_x}, {swipe_start_y}) to ({swipe_start_x}, {swipe_end_y})."
    )


def verify_swipe(screenshot_path: str, previous_image) -> bool:
    """
    Verify that the swipe changed the screen by comparing screenshots.

    Args:
        screenshot_path (str): Path to save the new screenshot.
        previous_image: The previous screenshot.
    Returns:
        bool: True if the swipe changed the screen, False otherwise.
    """

    new_image = cv2.imread(screenshot_path)
    if new_image is None:
        print("new_image is None.")
        return False

    # Compare the previous and new screenshots
    if (previous_image == new_image).all():
        print("Screen did not change.")
        return False

    return True


def swipe_with_verification(
    input_controller: InputController,
    swipe_distance: int,
    start_x: int,
    start_y: int,
    item_width: int,
    max_retries: int = 2,
) -> bool:
    """
    Swipe with screenshot verification to ensure it actually scrolled.
    """
    swipe_start_x = start_x + item_width // 2
    swipe_start_y = start_y + swipe_distance
    swipe_end_y = start_y

    for attempt in range(max_retries):
        # Capture before swipe
        before = input_controller.capture_screenshot()

        # Perform swipe
        input_controller.swipe(
            swipe_start_x, swipe_start_y, swipe_start_x, swipe_end_y, duration_ms=2000
        )

        # Wait for animation
        time.sleep(2.5)

        # Capture after swipe
        after = input_controller.capture_screenshot()

        # Verify screen changed (compare first row of items)
        if _screens_are_different(before, after, start_x, start_y, item_width):
            return True

        print(f"[Swipe] Attempt {attempt + 1} failed, retrying...")

    return False


def _screens_are_different(
    before: np.ndarray,
    after: np.ndarray,
    start_x: int,
    start_y: int,
    item_width: int,
    threshold: float = 0.1,
) -> bool:
    """
    Compare the first row of items to detect if swipe actually changed content.
    """
    if before is None or after is None:
        return False

    # Sample region from first row
    sample_height = 630
    sample_width = item_width * 2

    before_sample = before[
        start_y : start_y + sample_height, start_x : start_x + sample_width
    ]
    after_sample = after[
        start_y : start_y + sample_height, start_x : start_x + sample_width
    ]

    if before_sample.shape != after_sample.shape:
        return True

    # Calculate difference ratio
    diff = np.abs(before_sample.astype(float) - after_sample.astype(float))
    diff_ratio = np.mean(diff) / 255.0

    return diff_ratio > threshold
