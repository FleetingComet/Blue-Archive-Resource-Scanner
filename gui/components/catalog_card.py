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
    """Readable currency card, with the existing item-asset image pipeline."""
    if isinstance(entry.value, dict):
        # AP is stored as {"Remaining": "…", "Max": "…"}; other
        # multi-part currencies remain readable without special-casing keys.
        current = entry.value.get("Remaining", entry.value.get("remaining"))
        maximum = entry.value.get("Max", entry.value.get("max"))
        if current is not None and maximum is not None:
            detail = f"{current} / {maximum} available"
            badge_text = f"{current}/{maximum}"
        else:
            detail = " · ".join(f"{key}: {value}" for key, value in entry.value.items())
            badge_text = ""
    else:
        detail = f"ID {entry.key}" if entry.key.isdecimal() else "Scanned balance"
        badge_text = quantity_badge(entry.value) if entry.value is not None else ""

    return CardSpec(
        key=entry.iid,
        name=entry.name,
        kind="currency",
        detail=detail,
        glyph=CARD_GLYPHS["currency"],
        asset=icons.item_asset(entry.info.get("icon")),
        fit=icons.FIT_CONTAIN,
        badges=(("bl", badge_text, BADGE_BG),) if badge_text else (),
        quantity=entry.quantity,
        search=entry.search_text,
    )


def quantity_badge(value: object) -> str:
    """Human-friendly badge without changing the underlying JSON value type."""
    if isinstance(value, int) and not isinstance(value, bool):
        return f"×{value:,}"
    if isinstance(value, str):
        digits = value.strip().replace(",", "")
        if digits.isdecimal():
            return f"×{int(digits):,}"
    return str(value)


def equipment_glyph(category: str) -> str:
    if category == "Exp":
        return EQUIPMENT_GLYPHS["Exp"]
    if category.startswith("WeaponExpGrowth"):
        return EQUIPMENT_GLYPHS["WeaponExpGrowth"]
    return DEFAULT_EQUIPMENT_GLYPH
