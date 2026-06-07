import cv2
import numpy as np


def count_blue_stars_adaptive(cropped_image, debug=False):
    """
    Count blue stars in a cropped image using adaptive contour detection.
    Works for both large images and tiny crops.
    """

    if cropped_image is None or cropped_image.size == 0:
        if debug:
            print("Error: empty image passed to count_blue_stars_adaptive")
        return 0

    h, w = cropped_image.shape[:2]
    total_pixels = h * w

    if debug:
        print(f"\nImage size: {w}x{h} (total {total_pixels} pixels)")

    # Thresholds relative to image size
    min_star_area = max(10, total_pixels * 0.01)  # at least 10px or 1% of crop
    max_star_area = total_pixels * 0.8  # at most 80% of crop

    if debug:
        print(f"Area thresholds: min={min_star_area:.0f}, max={max_star_area:.0f}")

    # HSV range for blue stars (tuned and working)
    lower = np.array([95, 80, 80])
    upper = np.array([135, 255, 255])

    # Create mask
    hsv = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)

    # Clean mask with small kernel (adapts to image size)
    kernel_size = max(1, min(3, h // 10, w // 10))
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    if debug:
        cv2.imwrite("debug_mask_blue.png", mask)
        print(f"Mask non-zero pixels: {np.count_nonzero(mask)}")

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if debug:
        print(f"Raw contours found: {len(contours)}")

    # Filter by area
    valid_contours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if min_star_area <= area <= max_star_area:
            valid_contours.append(contour)
            if debug:
                print(f"  Accepted area={area:.0f}")
        else:
            if debug and area > 0:
                print(
                    f"  Rejected area={area:.0f} (need {min_star_area:.0f}-{max_star_area:.0f})"
                )

    star_count = len(valid_contours)

    # Special case: if mask covers >30% of a reasonably sized image, it's likely one star
    if star_count == 0 and total_pixels > 100:
        mask_ratio = np.count_nonzero(mask) / total_pixels
        if mask_ratio > 0.3:
            star_count = 1
            if debug:
                print(f"  → Special case: mask covers {mask_ratio:.1%} -> 1 star")

    # Fallback for tiny crops: simple colour coverage
    if star_count == 0 and total_pixels < 5000:
        color_ratio = np.count_nonzero(mask) / total_pixels
        if color_ratio > 0.15:
            star_count = 1
            if debug:
                print(f"  → Fallback: colour coverage {color_ratio:.1%} -> 1 star")

    if debug and star_count > 0:
        debug_img = cropped_image.copy()
        for i, contour in enumerate(valid_contours):
            x, y, cw, ch = cv2.boundingRect(contour)
            cv2.rectangle(debug_img, (x, y), (x + cw, y + ch), (0, 255, 0), 2)
            cv2.putText(
                debug_img,
                f"★{i+1}",
                (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
            )
        cv2.imwrite("stars_adaptive_blue.png", debug_img)

    return star_count
