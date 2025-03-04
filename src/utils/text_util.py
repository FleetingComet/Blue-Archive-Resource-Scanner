import Levenshtein


def is_close_to_max(text: str, target: str = "MAX", threshold: float = 0.8) -> bool:
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
