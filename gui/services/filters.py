"""Filter metadata shared by the Data tab's students, equipment and items.

The widgets only know about :class:`FilterOption` / :class:`FilterGroup`; this
module keeps them free of Tk and of any particular dataset. Student-specific
attribute extraction stays in :mod:`gui.services.student_sort`, while the
equipment/item catalog lives in :mod:`gui.services.catalog`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class FilterOption:
    """One selectable value in a filter, plus optional artwork.

    ``asset`` is a schaledb-relative path (school crest, equipment icon, ...),
    ``colour`` paints a small rounded swatch (rarity / attack / armour) and
    ``glyph`` names a bundled glyph drawn inside that swatch.  ``monochrome``
    marks a white/alpha glyph that must be tinted with the theme foreground
    (school crests); full-colour artwork leaves it false.  Any of them may be
    missing, in which case the popup shows the label on its own.
    """

    value: str
    label: str = ""
    asset: str | None = None
    colour: str | None = None
    glyph: str | None = None
    monochrome: bool = False

    def __post_init__(self) -> None:
        if not self.label:
            object.__setattr__(self, "label", self.value)


@dataclass(frozen=True)
class FilterGroup:
    """One filter category (School, Rarity, Tier, ...)."""

    key: str
    label: str
    options: tuple[FilterOption, ...]


def groups_from_values(
    key: str,
    label: str,
    values: Iterable[str],
    *,
    decorate=None,
) -> FilterGroup:
    """Build a group from plain values, sorted case-insensitively.

    ``decorate`` receives a value and returns optional keyword arguments for
    :class:`FilterOption` (``asset``/``colour``/``glyph``/``label``).
    """
    options: list[FilterOption] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        value = str(value).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        options.append(FilterOption(value, **(decorate(value) if decorate else {})))
    options.sort(key=lambda option: option.label.casefold())
    return FilterGroup(key, label, tuple(options))


def matches_selected(
    values: Mapping[str, object], selected: Mapping[str, set[str]]
) -> bool:
    """OR inside one category, AND across categories.

    A blank selection means "no constraint"; missing/None entry values never
    match an active selection, so malformed records cannot sneak through.
    """
    for key, chosen in selected.items():
        if not chosen:
            continue
        value = str(values.get(key) or "").strip()
        if not value or value not in chosen:
            return False
    return True


def search_matches(text: object, query: str) -> bool:
    """Case-insensitive substring match; an empty query matches everything."""
    needle = query.strip().casefold()
    return not needle or needle in str(text or "").casefold()


def prune_selection(
    selected: Mapping[str, set[str]], groups: Iterable[FilterGroup]
) -> dict[str, set[str]]:
    """Drop values that no longer exist when the dataset changed."""
    allowed = {
        group.key: {option.value for option in group.options} for group in groups
    }
    return {
        key: {value for value in values if value in allowed.get(key, set())}
        for key, values in selected.items()
        if key in allowed
    }
