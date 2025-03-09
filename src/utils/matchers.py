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
