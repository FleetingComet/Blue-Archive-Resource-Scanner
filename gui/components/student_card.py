"""The student card: one student's portrait, name, level, stars and chips.

``StudentCard`` is a thin specialisation of :class:`~gui.components.card.
AssetCard` that knows how a scanned student record maps onto a card. The Data
tab asks :meth:`StudentCard.spec_for` for the plain data and the grid builds the
widget, so the layout and image handling stay in one place.
"""

from __future__ import annotations

from gui import icons
from gui.components.card import (
    BADGE_BG,
    CARD_GLYPHS,
    AssetCard,
    CardSpec,
    CardTag,
    Chip,
)
from gui.services.student_sort import bond_gear_tier, bond_level
from src.constant import ARMOR_COLORS, ATTACK_COLORS
from src.utils.data.stat_normalization import format_skill

# The heart is a darker rose so the white bond level reads inside it; the tag
# itself has no pill behind it, so it sits straight on the card.
BOND_HEART_COLOUR = "#c2255c"
BOND_VALUE_COLOUR = "#ffffff"

# Exact student role colors for STRIKER and SPECIAL
STRIKER_COLOR = "#ff2d51"
SPECIAL_COLOR = "#4c6cb3"
ROLE_COLORS = {
    "STRIKER": STRIKER_COLOR,
    "SPECIAL": SPECIAL_COLOR,
}


def student_role(info: dict) -> str:
    """Normalize student squad type to STRIKER or SPECIAL."""
    raw = str(info.get("SquadType") or "").upper()
    if raw in ("STRIKER", "MAIN"):
        return "STRIKER"
    if raw in ("SPECIAL", "SUPPORT"):
        return "SPECIAL"
    return ""


def bond_tags(record: dict) -> tuple[CardTag, ...]:
    """The student's single bond tag: the level in the heart, its gear tier after.

    One tag keeps the two bond facts together ("♥22 T2") and,
    reads as part of the school line instead of a third chip. They
    are still independent values: a student with a bond level but no gear shows
    only the heart, and a gear tier without a usable level only the ``T<n>``.
    """
    level = bond_level(record)
    tier = bond_gear_tier(record)
    if level is None and tier <= 0:
        return ()
    return (
        CardTag(
            text=f"T{tier}" if tier > 0 else "",
            icon="heart-fill" if level is not None else "",
            icon_colour=BOND_HEART_COLOUR,
            value=str(level) if level is not None else "",
            value_colour=BOND_VALUE_COLOUR,
        ),
    )


class StudentCard(AssetCard):
    """One student drawn as a card; ``update_student`` replaces its data."""

    def __init__(
        self,
        master,
        spec: CardSpec,
        *,
        images,
        palette,
        on_select=None,
        on_scroll=None,
        **kwargs,
    ):
        super().__init__(
            master,
            spec,
            images=images,
            palette=palette,
            on_select=on_select,
            on_scroll=on_scroll,
            **kwargs,
        )

    def update_student(self, record: dict, info: dict | None = None) -> None:
        """Refresh the card from an edited student record."""
        self.update_spec(self.spec_for(record, self.spec.key, info))

    @staticmethod
    def spec_for(record: dict, key: str, info: dict | None = None) -> CardSpec:
        """Turn one student record (plus its game-data entry) into a card spec."""
        info = info or {}
        student_name = str(record.get("name", ""))
        student_id = record.get("id")
        school = str(info.get("School") or "")
        skills = "/".join(
            _skill(_stat(record, stat)) for stat in ("ex", "basic", "passive", "sub")
        )
        gear = "/".join(
            _skill(_stat(record, stat)) for stat in ("gear1", "gear2", "gear3")
        )

        chips: list[Chip] = []
        attack = str(info.get("BulletType") or "")
        armor = str(info.get("ArmorType") or "")
        if attack in ATTACK_COLORS:
            chips.append(Chip(attack, ATTACK_COLORS[attack], "#ffffff", "attack"))
        if armor in ARMOR_COLORS:
            chips.append(Chip(armor, ARMOR_COLORS[armor], "#ffffff", "defense"))

        return CardSpec(
            key=key,
            name=student_name,
            kind="student",
            detail=school or f"ID {student_id}",
            tags=bond_tags(record),
            glyph=CARD_GLYPHS["student"],
            asset=icons.student_asset(student_id),
            fit=icons.FIT_COVER,
            emblem=icons.school_asset(school),
            badges=(
                ("tl", f"LV {_stat(record, 'level')}", BADGE_BG),
                ("bl", skills, BADGE_BG),
                ("br", gear, BADGE_BG),
            ),
            stars=(_stat(record, "star"), _stat(record, "ue")),
            chips=tuple(chips),
            quantity=None,
            search=f"{student_name} {student_id} {school}",
        )


def _stat(record: dict, key: str) -> object:
    current = record.get("current")
    if isinstance(current, dict) and key in current:
        return current[key]
    return ""


def _skill(value: object) -> str:
    try:
        return format_skill(int(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return str(value)
