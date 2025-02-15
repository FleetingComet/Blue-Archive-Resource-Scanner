import cv2
from src.utils.adb_controller import ADBController


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
    swipe_end_y = start_y # Swipe to the top of the grid

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
