from typing import List, Optional

from rapidfuzz import fuzz, process


def find_closest(query: str, choices: List[str], threshold: float = 0.8) -> Optional[str]:
    """Return the closest match or None if below threshold."""
    if not query or not choices:
        return None
    match = process.extractOne(query, choices, scorer=fuzz.ratio, score_cutoff=threshold * 100)
    return match[0] if match else None