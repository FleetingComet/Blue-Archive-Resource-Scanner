import cv2
import numpy as np
# import numpy as np

def is_item_empty(image, region, threshold=20):
    """
    Check if the given region of the image is empty.
    Returns True if the standard deviation of pixel intensities is below threshold.
    """
    # Extract region of interest (ROI)
    roi = image[region.y : region.y + region.height, region.x : region.x + region.width]
    if roi.size == 0:
        return True
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # mean, std_dev = cv2.meanStdDev(gray)
    std_dev = cv2.meanStdDev(gray)[1][0][0]
    # If the region is nearly uniform, consider it empty.
    return np.all(std_dev <= threshold)

# def is_item_empty(item_image, threshold=20):
#     gray = cv2.cvtColor(item_image, cv2.COLOR_BGR2GRAY)
#     cv2.namedWindow("Detected Region", cv2.WINDOW_AUTOSIZE)
#     cv2.imshow("Detected Region", gray)
#     cv2.waitKey(0)
#     mean, std_dev = cv2.meanStdDev(gray)
#     print(f"mean : {mean}")
#     print(f"std_dev : {std_dev}")
#     npall = np.all(std_dev < threshold)
#     print(f"all: {npall}")
#     return npall