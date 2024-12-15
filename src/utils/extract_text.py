import pytesseract


def extract_text(image, isName: bool = False) -> str:
    """Extract text from preprocessed image"""
    if isName:
        config = "--psm 6"
        # config = "--psm 7"  # single word 8, 7 for single line
    else:
        config = "--psm 6 -c tessedit_char_whitelist=0123456789"
        # config = "--psm 8 -c tessedit_char_whitelist=0123456789"
    text: str = pytesseract.image_to_string(image, config=config)
    return text.strip()
