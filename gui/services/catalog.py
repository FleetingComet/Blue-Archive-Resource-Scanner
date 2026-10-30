"""Read-only catalog rows and filters for equipment, items and currencies.

The Data tab's final-value files are terse: items are ``{id: quantity}`` and
equipment is ``{category: {tier: quantity}}``.  These helpers resolve them
through :mod:`gui.gamedata` once and expose typed rows plus the filter groups
that make sense for each shape.  No Tk, no widgets - the Data page and the
filter bar only consume the results.
"""

from __future__ import annotations

from dataclasses import dataclass

from gui import gamedata, icons
from gui.services.filters import (
    FilterGroup,
    FilterOption,
    matches_selected,
    search_matches,
)
from src import constant

# Rarity order used by every card/filter (rarer last when sorting options).
RARITY_ORDER = ("N", "R", "SR", "SSR")
RARITY_COLOURS = {
    "N": "#6f7683",
    "R": "#3f7fb8",
    "SR": "#c79a25",
    "SSR": "#8b57bf",
}

EQUIPMENT_SHORT_NAMES = {
    "Exp": "Enhancement Stone",
    "WeaponExpGrowthA": "Weapon EXP A",
    "WeaponExpGrowthB": "Weapon EXP B",
    "WeaponExpGrowthC": "Weapon EXP C",
    "WeaponExpGrowthZ": "Weapon EXP Z",
}


def equipment_category_label(category: str) -> str:
    """A readable label for an equipment key (``WeaponExpGrowthA`` -> ...)."""
    if category in EQUIPMENT_SHORT_NAMES:
        return EQUIPMENT_SHORT_NAMES[category]
    # CamelCase fallback: "Hairpin" stays as is, "WeaponExpGrowthX" splits.
    spaced = "".join(
        f" {char}" if char.isupper() and index else char
        for index, char in enumerate(category)
    )
    return spaced.strip() or category


@dataclass(frozen=True)
class EquipmentEntry:
    iid: str
    category: str
    tier: str
    quantity: object
    info: dict

    @property
    def name(self) -> str:
        return str(self.info.get("name") or equipment_category_label(self.category))

    @property
    def rarity(self) -> str:
        return str(self.info.get("rarity") or "")

    @property
    def search_text(self) -> str:
        return f"{self.name} {self.category} {self.tier} {self.rarity}"

    @property
    def values(self) -> dict[str, str]:
        return {
            "category": self.category,
            "tier": self.tier,
            "rarity": self.rarity,
        }


@dataclass(frozen=True)
class ItemEntry:
    iid: str
    key: str
    quantity: object
    info: dict

    @property
    def name(self) -> str:
        return str(self.info.get("name") or self.key)

    @property
    def rarity(self) -> str:
        return str(self.info.get("rarity") or "")

    @property
    def search_text(self) -> str:
        return f"{self.name} {self.key} {self.rarity}"

    @property
    def values(self) -> dict[str, str]:
        return {"rarity": self.rarity}


@dataclass(frozen=True)
class CurrencyEntry:
    iid: str
    key: str
    value: object
    info: dict

    @property
    def name(self) -> str:
        return str(self.info.get("name") or self.key)

    @property
    def quantity(self) -> int | None:
        """Numeric balance for sorting and hide-empty; keep source JSON untouched."""
        if isinstance(self.value, dict):
            raw = self.value.get("Remaining", self.value.get("remaining"))
        else:
            raw = self.value
        try:
            return int(str(raw).replace(",", "").strip())
        except (ValueError, TypeError):
            return None

    @property
    def search_text(self) -> str:
        if isinstance(self.value, dict):
            detail = " ".join(f"{key} {value}" for key, value in self.value.items())
        else:
            detail = "" if self.value is None else str(self.value)
        return f"{self.key} {self.name} {self.info.get('desc', '')} {detail}"


# ---------------------------------------------------------------------------
# Row builders
# ---------------------------------------------------------------------------
def equipment_entries(doc: object) -> list[EquipmentEntry]:
    grouped = doc if isinstance(doc, dict) else {}
    entries: list[EquipmentEntry] = []
    for category, tiers in grouped.items():
        if not isinstance(tiers, dict):
            continue
        for tier, quantity in tiers.items():
            category_text, tier_text = str(category), str(tier)
            entries.append(
                EquipmentEntry(
                    iid=f"e{category_text}|{tier_text}",
                    category=category_text,
                    tier=tier_text,
                    quantity=quantity,
                    info=gamedata.equipment(category_text, tier_text) or {},
                )
            )
    return entries


def item_entries(doc: object, *, known: bool) -> list[ItemEntry]:
    entries = doc if isinstance(doc, dict) else {}
    return [
        ItemEntry(
            iid=f"i{index}",
            key=str(key),
            quantity=quantity,
            info=(gamedata.item(key) or {}) if known else {},
        )
        for index, (key, quantity) in enumerate(entries.items())
    ]


def currency_entries(doc: object, *, known: bool) -> list[CurrencyEntry]:
    entries = doc if isinstance(doc, dict) else {}

    return [
        CurrencyEntry(
            iid=f"cur{key}",
            key=str(key),
            value=value,
            info=(gamedata.currency(key) or {}) if known else {},
        )
        for key, value in entries.items()
    ]


# ---------------------------------------------------------------------------
# Filter groups
# ---------------------------------------------------------------------------
def equipment_groups(entries: list[EquipmentEntry]) -> tuple[FilterGroup, ...]:
    if not entries:
        return ()

    first_icon: dict[str, str | None] = {}
    categories: dict[str, str] = {}
    tiers: set[int] = set()
    rarities: set[str] = set()
    for entry in entries:
        categories.setdefault(entry.category, equipment_category_label(entry.category))
        if entry.category not in first_icon:
            first_icon[entry.category] = icons.equipment_asset(entry.info.get("icon"))
        tiers.add(_as_int(entry.tier))
        if entry.rarity:
            rarities.add(entry.rarity)

    category_options = tuple(
        FilterOption(
            value=category,
            label=label,
            asset=first_icon.get(category),
        )
        for category, label in sorted(
            categories.items(), key=lambda pair: pair[1].casefold()
        )
    )
    tier_options = tuple(
        FilterOption(str(value), f"Tier {value}") for value in sorted(tiers)
    )
    rarity_options = tuple(
        FilterOption(value, colour=RARITY_COLOURS.get(value))
        for value in _ordered_rarities(rarities)
    )

    groups: list[FilterGroup] = [
        FilterGroup("category", "Type", category_options),
        FilterGroup("tier", "Tier", tier_options),
    ]
    if rarity_options:
        groups.append(FilterGroup("rarity", "Rarity", rarity_options))
    return tuple(groups)


def item_groups(entries: list[ItemEntry]) -> tuple[FilterGroup, ...]:
    rarities = {entry.rarity for entry in entries if entry.rarity}
    if not rarities:
        return ()
    options = tuple(
        FilterOption(value, colour=RARITY_COLOURS.get(value))
        for value in _ordered_rarities(rarities)
    )
    return (FilterGroup("rarity", "Rarity", options),)


def student_groups(entries) -> tuple[FilterGroup, ...]:
    """Student filter groups with school crests and element swatches.

    This lives here instead of in the widget layer so the Data page can build
    the same groups whether or not the popup is open.  Entries are
    ``(iid, record, info, index)`` tuples from :mod:`gui.services.student_sort`.
    """
    from gui.services.student_sort import FILTER_FIELDS

    seen: dict[str, set[str]] = {key: set() for key in FILTER_FIELDS}
    for _iid, _record, info, _index in entries:
        row = info or {}
        for key, (attribute, _label) in FILTER_FIELDS.items():
            value = str(row.get(attribute) or "").strip()
            if value:
                seen[key].add(value)

    groups: list[FilterGroup] = []
    for key, (_attribute, label) in FILTER_FIELDS.items():
        values = seen[key]
        if not values:
            continue
        if key == "school":
            options = tuple(
                FilterOption(
                    value,
                    asset=icons.school_asset(value),
                    monochrome=True,
                )
                for value in sorted(values, key=str.casefold)
            )
        elif key == "attack":
            options = tuple(
                FilterOption(
                    value,
                    colour=constant.ATTACK_COLORS.get(value),
                    glyph="attack" if value in constant.ATTACK_COLORS else None,
                )
                for value in sorted(values, key=str.casefold)
            )
        elif key == "armor":
            options = tuple(
                FilterOption(
                    value,
                    colour=constant.ARMOR_COLORS.get(value),
                    glyph="defense" if value in constant.ARMOR_COLORS else None,
                )
                for value in sorted(values, key=str.casefold)
            )
        else:  # club has no bundled icon: show the label only
            options = tuple(
                FilterOption(value) for value in sorted(values, key=str.casefold)
            )
        groups.append(FilterGroup(key, label, options))
    return tuple(groups)


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------
def filter_equipment(
    entries: list[EquipmentEntry],
    selected: dict[str, set[str]],
    query: str,
    *,
    hide_empty: bool,
) -> list[EquipmentEntry]:
    return [
        entry
        for entry in entries
        if not (hide_empty and entry.quantity == 0)
        and search_matches(entry.search_text, query)
        and matches_selected(entry.values, selected)
    ]


def filter_items(
    entries: list[ItemEntry],
    selected: dict[str, set[str]],
    query: str,
    *,
    hide_empty: bool,
) -> list[ItemEntry]:
    return [
        entry
        for entry in entries
        if not (hide_empty and entry.quantity == 0)
        and search_matches(entry.search_text, query)
        and matches_selected(entry.values, selected)
    ]


def filter_currencies(
    entries: list[CurrencyEntry], query: str, *, hide_empty: bool = False
) -> list[CurrencyEntry]:
    return [
        entry
        for entry in entries
        if not (hide_empty and entry.quantity == 0)
        and search_matches(entry.search_text, query)
    ]


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------
# Only the fields that make sense for each shape; students keep the richer
# list in :mod:`gui.services.student_sort`.
SORT_FIELDS_BY_KIND: dict[str, tuple[tuple[str, str], ...]] = {
    "equipment": (
        ("default", "Default Order"),
        ("name", "Name"),
        ("tier", "Tier"),
        ("rarity", "Rarity"),
        ("quantity", "Quantity"),
    ),
    "items": (
        ("default", "Default Order"),
        ("name", "Name"),
        ("rarity", "Rarity"),
        ("quantity", "Quantity"),
    ),
    "currencies": (
        ("default", "Default Order"),
        ("name", "Name"),
        ("quantity", "Balance"),
    ),
}


def sort_fields(kind: str) -> tuple[tuple[str, str], ...]:
    """The (key, label) sort modes offered for a card kind."""
    return SORT_FIELDS_BY_KIND.get(kind, (("default", "Default Order"),))


class _Descending:
    """Reverse the order of one sortable value without reversing ties."""

    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value

    def __lt__(self, other: _Descending) -> bool:
        return self.value > other.value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Descending) and self.value == other.value


def sort_entries(
    entries: list,
    field: str = "default",
    descending: bool = False,
) -> list:
    """Sort catalog rows; rows missing the field always go last."""
    if not entries or field == "default":
        return list(entries)

    def order(value):
        return _Descending(value) if descending else value

    def key(entry):
        if field == "name":
            name = str(getattr(entry, "name", "") or "").strip()
            return (1, 0) if not name else (0, order(name.casefold()))
        if field == "rarity":
            rarity = str(getattr(entry, "rarity", "") or "").strip()
            if not rarity:
                return (1, 0)
            rank = (
                RARITY_ORDER.index(rarity)
                if rarity in RARITY_ORDER
                else len(RARITY_ORDER)
            )
            return (0, order(rank))
        if field == "tier":
            raw = getattr(entry, "tier", None)
            if raw in (None, ""):
                return (1, 0)
            return (0, order(_as_int(raw)))
        if field == "quantity":
            value = getattr(entry, "quantity", None)
            if not isinstance(value, int) or isinstance(value, bool):
                return (1, 0)
            return (0, order(value))
        return (0, 0)

    return sorted(entries, key=key)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _as_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _ordered_rarities(values: set[str]) -> list[str]:
    known = [value for value in RARITY_ORDER if value in values]
    return known + sorted(values.difference(RARITY_ORDER), key=str.casefold)
