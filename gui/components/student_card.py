"""The student card: one student's portrait, name, level, stars and chips.

``StudentCard`` is a thin specialisation of :class:`~gui.components.card.
AssetCard` that knows how a scanned student record maps onto a card. The Data
tab asks :meth:`StudentCard.spec_for` for the plain data and the grid builds the
widget, so the layout and image handling stay in one place.
"""

from __future__ import annotations

from gui import icons
from gui.components.card import BADGE_BG, CARD_GLYPHS, AssetCard, CardSpec, Chip
from gui.services.student_sort import bond_gear_tier
from src.constant import ARMOR_COLORS, ATTACK_COLORS
from src.utils.data.stat_normalization import format_skill

# Rarity tag colours the HTML report uses for bond gear; the heart is a darker
# rose so it still reads inside the pale pink tag.
BOND_TAG_BG, BOND_TAG_FG = "#ffbed8", "#3d4f66"
BOND_HEART_COLOUR = "#c2255c"


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
    ):
        super().__init__(
            master,
            spec,
            images=images,
            palette=palette,
            on_select=on_select,
            on_scroll=on_scroll,
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
        bond_tier = bond_gear_tier(record)
        bond_note = f"T{bond_tier}" if bond_tier > 0 else ""

        return CardSpec(
            key=key,
            name=student_name,
            kind="student",
            detail=school or f"ID {student_id}",
            note=bond_note,
            note_icon="heart-fill" if bond_note else "",
            note_icon_colour=BOND_HEART_COLOUR,
            note_background=BOND_TAG_BG,
            note_foreground=BOND_TAG_FG,
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
