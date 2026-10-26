"""CardSpec builders for the equipment, item and currency rows.

The Data page owns the *documents*; these helpers own the *presentation* of one
catalog row, so the three shapes stay consistent (same badges, same rarity
tile, same searchable text) without the page growing another branch per kind.
"""

from __future__ import annotations

from gui import icons
from gui.components.card import BADGE_BG, CARD_GLYPHS, CardSpec
from gui.services.catalog import (
    RARITY_COLOURS,
    CurrencyEntry,
    EquipmentEntry,
    ItemEntry,
    equipment_category_label,
)

# Stand-in glyphs for equipment without artwork (damage is rare, but keeps the
# card readable in `local`/`disabled` image modes).
EQUIPMENT_GLYPHS = {"Exp": "gem", "WeaponExpGrowth": "gear"}
DEFAULT_EQUIPMENT_GLYPH = "shield-fill"


def equipment_spec(entry: EquipmentEntry) -> CardSpec:
    """One equipment tier as a card."""
    rarity = entry.rarity
    badges: list[tuple[str, str, str]] = [
        ("bl", quantity_badge(entry.quantity), BADGE_BG)
    ]
    if rarity:
        badges.append(("tl", rarity, RARITY_COLOURS.get(rarity, BADGE_BG)))
    return CardSpec(
        key=entry.iid,
        name=entry.name,
        kind="equipment",
        detail=f"{equipment_category_label(entry.category)} · Tier {entry.tier}",
        glyph=equipment_glyph(entry.category),
        asset=icons.equipment_asset(entry.info.get("icon")),
        fit=icons.FIT_CONTAIN,
        thumb_bg=RARITY_COLOURS.get(rarity) if rarity else None,
        badges=tuple(badges),
        quantity=entry.quantity,
        search=entry.search_text,
    )


def item_spec(entry: ItemEntry, *, known: bool) -> CardSpec:
    """One item quantity as a card (``known`` resolves the processed name)."""
    rarity = entry.rarity
    badges: list[tuple[str, str, str]] = [
        ("bl", quantity_badge(entry.quantity), BADGE_BG)
    ]
    if rarity:
        badges.append(("tl", rarity, RARITY_COLOURS.get(rarity, BADGE_BG)))
    return CardSpec(
        key=entry.iid,
        name=entry.name,
        kind="item",
        detail=f"ID {entry.key}" if known else "",
        glyph=CARD_GLYPHS["item"],
        asset=icons.item_asset(entry.info.get("icon")),
        fit=icons.FIT_CONTAIN,
        thumb_bg=RARITY_COLOURS.get(rarity) if rarity else None,
        badges=tuple(badges),
        quantity=entry.quantity,
        search=entry.search_text,
    )


def currency_spec(entry: CurrencyEntry) -> CardSpec:
    """One currency row (a plain value or a small keyed breakdown)."""
    if isinstance(entry.value, dict):
        detail = " / ".join(str(part) for part in entry.value.values())
        badges: tuple[tuple[str, str, str], ...] = ()
    else:
        detail = "Currency"
        badges = (("bl", quantity_badge(entry.value), BADGE_BG),)
    quantity = None if isinstance(entry.value, dict) else entry.value
    return CardSpec(
        key=entry.iid,
        name=entry.key,
        kind="currency",
        detail=detail,
        glyph=CARD_GLYPHS["currency"],
        fit=icons.FIT_CONTAIN,
        badges=badges,
        quantity=quantity,
        search=entry.search_text,
    )


def quantity_badge(value: object) -> str:
    return f"×{value:,}" if isinstance(value, int) else str(value)


def equipment_glyph(category: str) -> str:
    if category == "Exp":
        return EQUIPMENT_GLYPHS["Exp"]
    if category.startswith("WeaponExpGrowth"):
        return EQUIPMENT_GLYPHS["WeaponExpGrowth"]
    return DEFAULT_EQUIPMENT_GLYPH
