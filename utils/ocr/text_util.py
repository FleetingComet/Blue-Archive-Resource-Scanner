import re
import Levenshtein


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
    Convert a skill value to its numeric representation if it's "MAX".

    Args:
        value: The extracted skill value (could be a string like "MAX" or a numeric string).
        max_level: The maximum level for the skill slot or something can be indicated as MAX (e.g., 5 for EX skill, 10 for other skills).

    Returns:
        The normalized value.
    """
    if isinstance(value, str) and value.strip().upper() == "MAX":
        return max_level
    return value


def normalize_value(value, default=0):
    """
    Remove non-digit characters from a value and convert it to an int.

    Args:
        value: The value as extracted (e.g., "T9" or "9").
        default: The default value to return if conversion fails.

    Returns:
        int: The numeric value.
    """
    if not value:
        return 0

    try:
        numeric_str = re.sub(r"\D", "", str(value))
        return int(numeric_str) if numeric_str else default
    except Exception:
        return default
