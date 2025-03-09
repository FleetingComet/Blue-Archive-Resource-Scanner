import os
from pathlib import Path

import cv2

from src.utils.text_util import normalize_value


def match_tier(cropped_image, grayscale) -> str:
    tier_directory = r"assets\images\tier"
    tiers = [os.path.join(tier_directory, tier) for tier in os.listdir(tier_directory)]
    best_match = match_image_using_directory(cropped_image, tiers, grayscale=grayscale)
    if not best_match:
        return None
    # return os.path.basename(best_match)
    return Path(best_match).stem


def match_star(cropped_image, blue=False, debug=False) -> str:
    star_directory = r"assets\images\star"
    stars = [
        os.path.join(star_directory, star)
        for star in os.listdir(star_directory)
        if ("blue" in star) == blue
    ]
    best_match = match_image_using_directory(cropped_image, stars, threshold=0.8)
    if not best_match:
        return None
    if debug:
        print(f"Best Match: {best_match}")
        cv2.imwrite("cropped_image.png", cropped_image)
    return normalize_value(Path(best_match).stem)


def match_image_using_directory(
    input_image, reference_image_paths, threshold=0.9, grayscale=False
):
    """Match the input image against reference images using template matching."""
    best_match_name = None
    current_max_value = -1

    if grayscale:
        input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
        h, w = input_image.shape[:2]
        if h < 50 or w < 50:
            input_image = cv2.resize(
                input_image, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR
            )

    if input_image.ndim == 3 and input_image.shape[2] == 4:
        input_image = input_image[:, :, :3]

    for reference_path in reference_image_paths:
        if grayscale:
            reference_image = cv2.imread(reference_path, cv2.IMREAD_GRAYSCALE)
        else:
            reference_image = cv2.imread(reference_path, cv2.IMREAD_COLOR)
            # h, w = reference_image.shape[:2]
            # if h < 50 or w < 50:
            #     reference_image = cv2.resize(
            #         reference_image, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR
            #     )

        result = cv2.matchTemplate(input_image, reference_image, cv2.TM_CCOEFF_NORMED)
        _, max_value, _, _ = cv2.minMaxLoc(result)

        # print(f"Max Value for {reference_path}: {max_value}")

        # Check if this is the best match so far
        if max_value > current_max_value:
            current_max_value = max_value
            best_match_name = reference_path
            if max_value >= 0.99:
                break

    if not current_max_value >= threshold:
        return None

    return best_match_name


def match_image_using_file(
    input_image, reference_image_path, threshold=0.8, grayscale=False
) -> bool:
    """
    Match the input image against a single reference image using template matching.

    Parameters:
        input_image (np.array): The input image.
        reference_image_path (str): Path to the reference image file.
        threshold (float): The matching threshold. Only matches with a max value
                           above this threshold are considered valid.
        grayscale (bool): Whether to perform matching in grayscale.

    Returns:
        bool : True if the match is above threshold; otherwise, False.
    """
    # Convert input image to grayscale if needed.
    if grayscale:
        input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
        h, w = input_image.shape[:2]
        if h < 50 or w < 50:
            input_image = cv2.resize(
                input_image, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR
            )

    # Ensure input image has 3 channels if not in grayscale.
    if not grayscale and input_image.ndim == 3 and input_image.shape[2] == 4:
        input_image = input_image[:, :, :3]

    # Load the reference image.
    if grayscale:
        reference_image = cv2.imread(reference_image_path, cv2.IMREAD_GRAYSCALE)
        h, w = reference_image.shape[:2]
        if h < 50 or w < 50:
            reference_image = cv2.resize(
                reference_image, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR
            )
    else:
        reference_image = cv2.imread(reference_image_path, cv2.IMREAD_COLOR)

    if reference_image is None:
        print(f"Failed to load reference image: {reference_image_path}")
        return None

    result = cv2.matchTemplate(input_image, reference_image, cv2.TM_CCOEFF_NORMED)
    _, max_value, _, _ = cv2.minMaxLoc(result)

    # print(f"Max Value for {reference_image_path}: {max_value}")

    if max_value >= threshold:
        return True
    return False
