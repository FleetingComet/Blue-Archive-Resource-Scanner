"""Processed-students DB access and dual-style id resolution."""

from pathlib import Path
from typing import Any

from src.core.config import Path_Config
from src.utils.data.io import read_json

UNKNOWN_ORDER = 10**9  # sorts below every known DefaultOrder


def index_students(
    path: Path | None = None,
) -> tuple[dict[int, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Index the processed DB by id and by exact name."""
    rows = read_json(path or Path_Config.students_processed) or []
    by_id: dict[int, dict[str, Any]] = {}
    by_name: dict[str, dict[str, Any]] = {}
    for row in rows:
        if (sid := row.get("id")) is not None:
            try:
                by_id[int(sid)] = row
            except (TypeError, ValueError):
                pass
        if name := row.get("name"):
            by_name[name] = row
    return by_id, by_name


def resolve_base_id(raw_id: Any, by_id: dict[int, dict[str, Any]]) -> int | None:
    """
    Resolve a scanned id to its canonical DB row (StyleId null or 0).

    Dual-mode students are TWO rows sharing one name that link to EACH
    OTHER via LinkedCharacterId; exactly one row has StyleId 0:

        10098  Hoshino (Armed)  StyleId: 0  ->  10099
        10099  Hoshino (Armed)  StyleId: 1  ->  10098

    Plain students have StyleId: null, LinkedCharacterId: null and resolve
    to themselves. Cycle guard is a corrupt-data backstop only.
    """
    current = raw_id
    seen: set[int] = set()
    while current is not None:
        try:
            key = int(current)
        except (TypeError, ValueError):
            return None
        if key in seen:
            return key
        seen.add(key)

        meta = by_id.get(key)
        if meta is None:
            return None

        if not meta.get("StyleId") or meta.get("LinkedCharacterId") is None:
            return key
        current = meta["LinkedCharacterId"]
    return None


def iter_style_ids(raw_id: Any, by_id: dict[int, dict[str, Any]]) -> list[int]:
    """
    Every id belonging to the same physical student: the canonical base
    plus any linked alternate styles (transitive, cycle-safe, base first).
    Single element for plain students; [] for unknown ids.

    Used by exporters that must emit one entry PER FORM (schaledb),
    as opposed to justin_planner / midokuni which use resolve_base_id.
    """
    base = resolve_base_id(raw_id, by_id)
    if base is None:
        return []

    ordered = [base]
    seen = {base}
    frontier = [base]
    while frontier:
        current = frontier.pop()
        partner_raw = by_id[current].get("LinkedCharacterId")
        try:
            partner = int(partner_raw) if partner_raw is not None else None
        except (TypeError, ValueError):
            partner = None
        if partner and partner not in seen and partner in by_id:
            seen.add(partner)
            ordered.append(partner)
            frontier.append(partner)
    return ordered


def match_meta(
    char: dict[str, Any],
    by_id: dict[int, dict[str, Any]],
    by_name: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], int | None]:
    """
    Match a scanned character to DB metadata.
    Order: id -> dual-mode base redirect -> exact name.
    Returns (metadata, resolved base id); ({}, None) if unmatched.
    """
    raw_id = char.get("id")
    if raw_id is not None:
        base_id = resolve_base_id(raw_id, by_id)
        if base_id is not None and (meta := by_id.get(base_id)):
            return meta, base_id
    return by_name.get(char.get("name", ""), {}), None


def effective_order(meta: dict[str, Any]) -> int:
    """DefaultOrder with a below-everything fallback for unknown students."""
    order = meta.get("DefaultOrder")
    return order if isinstance(order, int) else UNKNOWN_ORDER
