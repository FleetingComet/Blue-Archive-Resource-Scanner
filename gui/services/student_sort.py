"""Sorting and filtering for the Data tab's student list.

Each student entry in the Data page is a ``(iid, record, info)`` tuple:

* ``iid``    - the grid's stable payload id (``"s<index>"``),
* ``record`` - the raw scanner output (the dict inside ``characters``),
* ``info``   - the processed-students row from ``assets/data``.

This module is the single place that knows how those values map to sort
modes and filter attributes. No Tk, no data loading - just reordering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Sort fields: (key, UI display label)
SORT_FIELDS: tuple[tuple[str, str], ...] = (
    ("default", "Default Order"),
    ("name", "Name"),
    ("level", "Level"),
    ("rarity", "Rarity"),
    ("ue_stars", "UE Stars"),
    ("ue_level", "UE Level"),
    ("bond", "Bond Level"),
)

SORT_FIELD_KEYS: tuple[str, ...] = tuple(k for k, _ in SORT_FIELDS)
SORT_FIELD_LABELS: dict[str, str] = dict(SORT_FIELDS)
SORT_LABEL_TO_KEY: dict[str, str] = {v: k for k, v in SORT_FIELDS}

# Filter attribute -> (DB field name, display label)
FILTER_FIELDS: dict[str, tuple[str, str]] = {
    "school": ("School", "School"),
    "club": ("Club", "Club"),
    "attack": ("BulletType", "Attack Type"),
    "armor": ("ArmorType", "Armor Type"),
}

# (iid, record_dict, info_dict, original_index)
SortEntry = tuple[str, dict[str, Any], dict[str, Any], int]


@dataclass
class StudentFilterState:
    """Active filter selections for the student grid."""

    schools: set[str] = field(default_factory=set)
    clubs: set[str] = field(default_factory=set)
    role: str = "all"  # "all" | "striker" | "special"
    attack_types: set[str] = field(default_factory=set)
    armor_types: set[str] = field(default_factory=set)
    has_bond_gear: bool = False
    search: str = ""

    def is_active(self) -> bool:
        return bool(
            self.schools
            or self.clubs
            or self.role != "all"
            or self.attack_types
            or self.armor_types
            or self.has_bond_gear
            or self.search.strip()
        )

    def clear(self) -> None:
        self.schools.clear()
        self.clubs.clear()
        self.role = "all"
        self.attack_types.clear()
        self.armor_types.clear()
        self.has_bond_gear = False
        self.search = ""


def bond_gear_tier(record: dict[str, Any]) -> int:
    """The student's bond-gear tier (0 when absent).

    The scanner's final file calls it ``bond_gear`` while the editor exposes
    the raw students file as ``gear_bond``; accept either so the card tag and
    the "Has Bond Gear" filter agree with what the editor shows.
    """
    for key in ("bond_gear", "gear_bond"):
        tier = _safe_int(_stat(record, key))
        if tier is not None:
            return tier
    return 0


def filter_student_entries(
    entries: list[SortEntry], filters: StudentFilterState
) -> list[SortEntry]:
    """Filter entries according to criteria: AND across dimensions, OR within."""
    if not filters.is_active():
        return list(entries)

    search_query = filters.search.strip().lower()
    selected_role = filters.role.lower()

    result: list[SortEntry] = []
    for entry in entries:
        _iid, record, info, _orig_idx = entry
        info = info or {}

        # Search query check
        if search_query:
            name = str(record.get("name") or "").lower()
            sid = str(record.get("id") or "").lower()
            school = str(info.get("School") or "").lower()
            if (
                search_query not in name
                and search_query not in sid
                and search_query not in school
            ):
                continue

        # Role filter: All / Striker / Special
        if selected_role != "all":
            raw_role = str(info.get("SquadType") or "").upper()
            if selected_role == "striker" and raw_role not in ("STRIKER", "MAIN"):
                continue
            if selected_role == "special" and raw_role not in ("SPECIAL", "SUPPORT"):
                continue

        # Bond gear is a checkbox, not a category: it is either present or not.
        if filters.has_bond_gear and bond_gear_tier(record) <= 0:
            continue

        # School filter (OR within attribute)
        if filters.schools:
            school_val = str(info.get("School") or "").strip()
            if not school_val or school_val not in filters.schools:
                continue

        # Club filter (OR within attribute)
        if filters.clubs:
            club_val = str(info.get("Club") or "").strip()
            if not club_val or club_val not in filters.clubs:
                continue

        # Attack Type filter (OR within attribute)
        if filters.attack_types:
            atk_val = str(info.get("BulletType") or "").strip()
            if not atk_val or atk_val not in filters.attack_types:
                continue

        # Armor Type filter (OR within attribute)
        if filters.armor_types:
            arm_val = str(info.get("ArmorType") or "").strip()
            if not arm_val or arm_val not in filters.armor_types:
                continue

        result.append(entry)

    return result


class _DescStr:
    """Helper to sort strings descending without reversing the entire tuple."""

    __slots__ = ("val",)

    def __init__(self, val: str):
        self.val = val

    def __lt__(self, other: _DescStr) -> bool:
        return self.val > other.val

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _DescStr) and self.val == other.val


def _stat(record: dict[str, Any], key: str) -> object:
    current = record.get("current")
    return current.get(key) if isinstance(current, dict) else None


def _safe_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        val = int(value)  # type: ignore[arg-type]
        return val if val >= 0 else None
    except (TypeError, ValueError):
        return None


def sort_student_entries(
    entries: list[SortEntry],
    field: str = "default",
    descending: bool = False,
) -> list[SortEntry]:
    """Sort entries stably: valid values first, ties broken by original_index."""
    if not entries:
        return []

    def key_func(entry: SortEntry) -> tuple:
        _iid, record, info, orig_idx = entry
        info = info or {}

        if field == "default":
            order = info.get("DefaultOrder")
            val = order if isinstance(order, int) else orig_idx
            return (0, -val if descending else val, orig_idx)

        if field == "name":
            raw_name = str(record.get("name") or "").strip()
            if not raw_name:
                return (1, 0, orig_idx)  # Missing values sort last
            folded = raw_name.casefold()
            val_term = _DescStr(folded) if descending else folded
            return (0, val_term, orig_idx)

        if field == "level":
            val = _safe_int(_stat(record, "level"))
            if val is None:
                return (1, 0, orig_idx)
            return (0, -val if descending else val, orig_idx)

        if field == "rarity":
            # Primary: star count (1-5). Progression tie-breaker: UE blue stars (0-4).
            star = _safe_int(_stat(record, "star"))
            if star is None:
                return (1, 0, 0, orig_idx)
            ue = _safe_int(_stat(record, "ue")) or 0
            if descending:
                return (0, -star, -ue, orig_idx)
            return (0, star, ue, orig_idx)

        if field == "ue_stars":
            # Primary: UE blue stars (0-4). Progression tie-breaker: regular stars.
            ue = _safe_int(_stat(record, "ue"))
            if ue is None:
                return (1, 0, 0, orig_idx)
            star = _safe_int(_stat(record, "star")) or 0
            if descending:
                return (0, -ue, -star, orig_idx)
            return (0, ue, star, orig_idx)

        if field == "ue_level":
            val = _safe_int(_stat(record, "ue_level"))
            if val is None:
                return (1, 0, orig_idx)
            return (0, -val if descending else val, orig_idx)

        if field == "bond":
            val = _safe_int(_stat(record, "bond"))
            if val is None:
                return (1, 0, orig_idx)
            return (0, -val if descending else val, orig_idx)

        # Fallback to original index
        return (0, -orig_idx if descending else orig_idx, orig_idx)

    return sorted(entries, key=key_func)
