import cv2


def preprocess_image_for_ocr(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    h, w = binary.shape
    if h < 50 or w < 50:
        binary = cv2.resize(binary, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)

    # Noise removal
    denoised = cv2.fastNlMeansDenoising(binary, h=30)
    return denoised
