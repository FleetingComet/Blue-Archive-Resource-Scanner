"""Identifiers and local artwork for the Data tab's cards."""

from __future__ import annotations

import logging

from PIL import Image

from src.core.paths import Path_Config

logger = logging.getLogger("BA-Scanner")

ITEM_DIR = "item/icon/"
EQUIPMENT_DIR = "equipment/icon/"
STUDENT_DIR = "student/collection/"
SCHOOL_DIR = "schoolicon/"

# Explicit school alias mapping to icon filenames (case-insensitive lookup).
_SCHOOL_FILES = {
    "wildhunt": "WildHunt",
    "wild hunt": "WildHunt",
    "etc.": "ETC",
    "etc": "ETC",
    "red winter": "RedWinter",
    "redwinter": "RedWinter",
    "sakugawa": "ETC",
    "tokiwadai": "ETC",
}

# Icon filenames shipped by SchaleDB.
_KNOWN_SCHOOL_ICONS = frozenset(
    {
        "Abydos",
        "Arius",
        "ETC",
        "Gehenna",
        "Highlander",
        "Hyakkiyako",
        "Millennium",
        "RedWinter",
        "SRT",
        "Shanhaijing",
        "Trinity",
        "Valkyrie",
        "WildHunt",
    }
)
_KNOWN_SCHOOL_ICONS_BY_LOWER = {name.lower(): name for name in _KNOWN_SCHOOL_ICONS}

FIT_CONTAIN = "contain"
FIT_COVER = "cover"


def item_asset(icon: object) -> str | None:
    """Asset path for an ``items_processed.json`` icon name."""
    return _asset(ITEM_DIR, icon)


def equipment_asset(icon: object) -> str | None:
    """Asset path for an ``equipment_processed.json`` icon name."""
    return _asset(EQUIPMENT_DIR, icon)


def student_asset(student_id: object) -> str | None:
    """Portrait asset path for a student id."""
    return _asset(STUDENT_DIR, student_id)


def school_asset(school: object) -> str | None:
    """Asset path for a school emblem with consistent ETC fallback.

    Resolution order:
      1. Explicit `_SCHOOL_FILES` mapping (e.g. Sakugawa -> ETC, Tokiwadai -> ETC).
      2. Whitespace-stripped match against known icon filenames (case-insensitive).
      3. Fallback to `ETC` for any unknown school.
    """
    name = str(school or "").strip()
    if not name:
        return None

    lowered = name.lower()
    if lowered in _SCHOOL_FILES:
        file_name = _SCHOOL_FILES[lowered]
    else:
        file_name = name.replace(" ", "")

    matched = _KNOWN_SCHOOL_ICONS_BY_LOWER.get(file_name.lower())
    if matched:
        file_name = matched
    else:
        file_name = "ETC"

    return _asset(SCHOOL_DIR, file_name, extension=".png")


def _asset(directory: str, name: object, *, extension: str = ".webp") -> str | None:
    text = str(name or "").strip()
    return f"{directory}{text}{extension}" if text else None


_STAR_DIR = Path_Config.ASSETS_DIR / "images" / "star"
_star_cache: dict[tuple[int, int, int], Image.Image] = {}


def star_strip(star: object, ue: object, *, height: int = 13) -> Image.Image | None:
    gold = _clamp(star, 1, 5)
    blue = _clamp(ue, 0, 4)
    key = (gold, blue, height)
    cached = _star_cache.get(key)
    if cached is not None:
        return cached

    files = [_STAR_DIR / f"{gold}_star.png"]
    if blue:
        files.append(_STAR_DIR / f"{blue}_blue_star.png")

    parts: list[Image.Image] = []
    try:
        for path in files:
            with Image.open(path) as image:
                parts.append(image.convert("RGBA"))
    except OSError:
        logger.debug("star art missing: %s", [str(path) for path in files])
        return None

    strip = Image.new(
        "RGBA", (sum(part.width for part in parts), parts[0].height), (0, 0, 0, 0)
    )
    x = 0
    for part in parts:
        strip.alpha_composite(part, (x, 0))
        x += part.width

    ratio = height / strip.height
    strip = strip.resize((max(1, round(strip.width * ratio)), height), Image.LANCZOS)
    _star_cache[key] = strip
    return strip


def _clamp(value: object, low: int, high: int) -> int:
    try:
        number = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return low
    return max(low, min(high, number))


TYPE_ICONS = {"attack": "Type_Attack.png", "defense": "Type_Defense.png"}
_UI_DIR = Path_Config.IMAGES_DIR / "local" / "ui"
_type_cache: dict[tuple[str, int], Image.Image] = {}


def type_icon(kind: str, *, size: int = 11) -> Image.Image | None:
    name = TYPE_ICONS.get(kind)
    if not name:
        return None
    key = (kind, size)
    cached = _type_cache.get(key)
    if cached is not None:
        return cached
    try:
        with Image.open(_UI_DIR / name) as image:
            glyph = image.convert("RGBA")
    except OSError:
        logger.debug("type glyph missing: %s", _UI_DIR / name)
        return None
    ratio = size / max(glyph.width, glyph.height)
    glyph = glyph.resize(
        (max(1, round(glyph.width * ratio)), max(1, round(glyph.height * ratio))),
        Image.LANCZOS,
    )
    _type_cache[key] = glyph
    return glyph
