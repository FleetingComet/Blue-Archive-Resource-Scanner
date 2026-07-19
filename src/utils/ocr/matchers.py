from pathlib import Path

import cv2


def match_image_using_directory(
    input_image, reference_image_paths: list[Path], threshold=0.9, grayscale=False
):
    """Match the input image against reference images using template matching."""
    best_match_name = None
    current_max_value = -1

    if input_image is None or input_image.size == 0:
        return None

    if grayscale and len(input_image.shape) == 3:
        input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)

    # Ensure 3-channel if not grayscale (strips alpha)
    if input_image.ndim == 3 and input_image.shape[2] == 4:
        input_image = input_image[:, :, :3]

    inp_h, inp_w = input_image.shape[:2]

    for reference_path in reference_image_paths:
        ref_flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
        reference_image = cv2.imread(str(reference_path), ref_flag)

        if reference_image is None:
            continue

        # If template is larger, resize it to fit within the input image bounds
        ref_h, ref_w = reference_image.shape[:2]
        if ref_h > inp_h or ref_w > inp_w:
            scale = min(inp_h / ref_h, inp_w / ref_w)
            # We scale down slightly more (0.9) to ensure it fits comfortably
            # and leaves room for the sliding window matching
            new_size = (int(ref_w * scale), int(ref_h * scale))

            # If the calculated size is 0, skip
            if new_size[0] < 1 or new_size[1] < 1:
                continue

            reference_image = cv2.resize(
                reference_image, new_size, interpolation=cv2.INTER_AREA
            )

        try:
            result = cv2.matchTemplate(
                input_image, reference_image, cv2.TM_CCOEFF_NORMED
            )
            _, max_value, _, _ = cv2.minMaxLoc(result)

            print(f"Max Value for {reference_path}: {max_value}")

            # Check if this is the best match so far
            if max_value > current_max_value:
                current_max_value = max_value
                best_match_name = reference_path
                if max_value >= 0.99:
                    break
        except cv2.error as e:
            print(f"Matcher: {e}")
            continue

    if current_max_value >= threshold:
        return best_match_name

    return None


def match_image_using_file(
    input_image, reference_image_path: Path, threshold=0.8, grayscale=False
) -> bool:
    """
    Match the input image against a single reference image using template matching.

    Parameters:
        input_image (np.array): The input image.
        reference_image_path (Path): Path to the reference image file.
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
        reference_image = cv2.imread(str(reference_image_path), cv2.IMREAD_GRAYSCALE)
        h, w = reference_image.shape[:2]
        if h < 50 or w < 50:
            reference_image = cv2.resize(
                reference_image, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR
            )
    else:
        reference_image = cv2.imread(str(reference_image_path), cv2.IMREAD_COLOR)

    if reference_image is None:
        print(f"Failed to load reference image: {str(reference_image_path)}")
        return None

    result = cv2.matchTemplate(input_image, reference_image, cv2.TM_CCOEFF_NORMED)
    _, max_value, _, _ = cv2.minMaxLoc(result)

    # print(f"Max Value for {reference_image_path}: {max_value}")

    if max_value >= threshold:
        return True
    return False
