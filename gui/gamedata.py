"""Read-only lookups into the game data the scanner keeps in ``assets/data``.

The scanner's *final values* store bare keys - item IDs for items, a
``{category: {tier: quantity}}`` shape for equipment - which are meaningless to
read. These helpers turn them back into the names, rarities and icon names the
rest of the game data uses, so the Data tab can show something readable.

Nothing is hardcoded: the tables are the same ``*_processed.json`` files the
processors match their OCR against, loaded lazily and cached for the session.
"""

from __future__ import annotations

from functools import lru_cache

from src.core.paths import Path_Config
from src.utils.data.io import read_json

# Equipment categories whose final-values key is *not* a tier.
_ENHANCEMENT = "Exp"
_WEAPON_GROWTH = "WeaponExpGrowth"


def item(item_id: object) -> dict | None:
    """The processed entry for an item ID (``items_processed.json``)."""
    key = _as_int(item_id)
    return _items().get(key) if key is not None else None


def equipment(category: object, key: object) -> dict | None:
    """The processed entry for one equipment cell of the final values.

    The key means different things per category, which mirrors how
    ``EquipmentProcessor`` writes them:

    * ``Exp``                - the equipment ID (1-4);
    * ``WeaponExpGrowth*``   - the rarity tier (1-4), encoded in the icon name;
    * anything else (gear)   - the equipment tier, preferring the gear itself
      over the crafting blueprint that shares the tier.
    """
    name = str(category)
    entries = _equipment().get(name)
    if not entries:
        return None

    if name == _ENHANCEMENT:
        wanted = _as_int(key)
        return next((entry for entry in entries if entry.get("id") == wanted), None)

    if name.startswith(_WEAPON_GROWTH):
        wanted = _as_int(key)
        if wanted is None:
            return None
        suffix = f"_{wanted - 1}"
        return next(
            (entry for entry in entries if str(entry.get("icon", "")).endswith(suffix)),
            None,
        )

    tier = _as_int(key)
    if tier is None:
        return None
    same_tier = [entry for entry in entries if entry.get("tier") == tier]
    return next(
        (
            entry
            for entry in same_tier
            if not str(entry.get("icon", "")).endswith("_piece")
        ),
        same_tier[0] if same_tier else None,
    )


@lru_cache(maxsize=1)
def _students_by_name() -> dict[str, dict]:
    return {
        str(entry["name"]).strip(): entry
        for entry in _load(Path_Config.students_processed)
        if isinstance(entry, dict) and entry.get("name")
    }


def student_by_name(name: object) -> dict | None:
    """The processed entry for a student name (fallback when ID is not yet resolved)."""
    if not name:
        return None
    return _students_by_name().get(str(name).strip())


def student(student_id: object) -> dict | None:
    """The processed entry for a student ID (``students_processed.json``)."""
    key = _as_int(student_id)
    return _students().get(key) if key is not None else None


def reset_cache() -> None:
    """Drop the cached tables (used by tests and after a data re-sync)."""
    for loader in (_items, _students, _students_by_name, _equipment):
        loader.cache_clear()


# ---------------------------------------------------------------------------
# Lazy, cached tables
# ---------------------------------------------------------------------------
def _as_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=1)
def _items() -> dict[int, dict]:
    return _by_id(_load(Path_Config.items_processed))


@lru_cache(maxsize=1)
def _students() -> dict[int, dict]:
    return _by_id(_load(Path_Config.students_processed))


@lru_cache(maxsize=1)
def _equipment() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for entry in _load(Path_Config.equipment_processed):
        grouped.setdefault(str(entry.get("category", "")), []).append(entry)
    return grouped


def _load(path) -> list[dict]:
    data = read_json(path)
    return (
        [entry for entry in data if isinstance(entry, dict)]
        if isinstance(data, list)
        else []
    )


def _by_id(entries: list[dict]) -> dict[int, dict]:
    return {
        key: entry for entry in entries if (key := _as_int(entry.get("id"))) is not None
    }
