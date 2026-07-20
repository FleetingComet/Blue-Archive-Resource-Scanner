import re

import Levenshtein


# ? Note: we leave this for some uses idk where/when
def is_close_to(text: str, target: str = "MAX", threshold: float = 0.8) -> bool:
    """
    Compares the given text to the target string (default "MAX")
    using the Levenshtein ratio. Returns True if the similarity is
    greater than or equal to the threshold, else False.

    Parameters:
      text: The string to compare.
      target: The reference string, default is "MAX".
      threshold: A float between 0 and 1 representing the minimum
                 similarity ratio required.

    Returns:
      bool: True if text is considered close to target, False otherwise.
    """
    normalized_text = text.strip().upper()

    # print("\n")
    similarity = Levenshtein.ratio(normalized_text, target)

    # For debugging
    # print(f"Similarity: {similarity:.2f}")

    return similarity >= threshold


def normalize_skill_value(value, max_level: int):
    """
    Convert a skill value to its numeric representation.
    Handles "MAX" (case-insensitive) and formats like "Lv.7".

    Args:
        value: The extracted skill value (could be a string like "MAX" or a numeric string).
        max_level: The maximum level for the skill slot or something can be indicated as MAX (e.g., 5 for EX skill, 10 for other skills).

    Returns:
        The normalized value.
    """
    if isinstance(value, str) and value.strip().upper() == "MAX":
        return max_level
    # Fallback to normalize_value to handle "Lv.X", plain numbers, etc.
    return normalize_value(value)


def normalize_value(value, default=0):
    """
    Remove non-digit characters from a value and convert it to an int.
    Automatically handles strings like "Lv.7", "LV. 8", "T9", or plain "81".

    Args:
        value: The value as extracted (e.g., "T9" or "9").
        default: The default value to return if conversion fails.

    Returns:
        int: The numeric value.
    """
    if value is None:
        return default

    try:
        val_str = str(value).strip()
        # \D matches ANY non-digit character. Removing it leaves only numbers.
        numeric_str = re.sub(r"\D", "", val_str)
        return int(numeric_str) if numeric_str else default

    except (ValueError, TypeError):
        return default


def get_tier_level(text: str) -> str:
    # Remove everything before and including some '(') + T
    text = re.sub(r".*?\(?T", "", text)
    # Remove ")"" and everything after
    text = re.sub(r"\).*", "", text)
    match = re.search(r"\d+", text)

    return match.group(0) if match else None
