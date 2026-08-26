"""Shared stat normalization all exporters."""

from typing import Any

# Highest legal reading per field. Tuned to game current stats (Global):
# legitimate gear 10 survives under cap 10; misreads gets deleted.
GEAR_LEVEL_CAP = 10
TALENT_LEVEL_CAP = 25


def sanitize_level(value: str | int, cap: int) -> str:
    """
    Collapse impossible readings to a legal value. Within-cap passes through;
    above-cap collapses to its last digit until legal (79 -> 9, 11 -> 1).
    Blind spot: a true max misread high (real 10 read as 19) is unrecoverable.
    """
    level = int(value)
    while level > cap:
        level %= 10
    return str(level)


def format_skill(value: str | int, max_level: int = 10) -> str:
    """Skill level, M for max (default max_level: 10)."""
    level = int(value)
    return "M" if level == max_level else str(level)


def normalize_stats(raw_stats: dict[str, Any]) -> dict[str, Any]:
    """
    Formats character stat values, locking skills based on effective star grade:
            - 1-Star: Passive & Sub locked ('0')
            - 2-Star: Sub locked ('0')
            - 3-Star+: All skills unlocked ('1')
    Owning Unique Equipment implies 5-Star regardless of the scanned star.
    """
    star_grade = int(raw_stats.get("star", 1))
    ue = int(raw_stats.get("ue", 0))

    if ue > 0:
        star_grade = 5

    default_passive = "1" if star_grade >= 2 else "0"
    default_sub = "1" if star_grade >= 3 else "0"

    return {
        "level": str(raw_stats.get("level", "1")),
        "ue_level": str(raw_stats.get("ue_level", "0")),
        "bond": str(raw_stats.get("bond", "1")),
        "ex": str(raw_stats.get("ex", "1")),
        "basic": str(raw_stats.get("basic", "1")),
        "passive": str(raw_stats.get("passive", default_passive)),
        "sub": str(raw_stats.get("sub", default_sub)),
        "gear1": sanitize_level(str(raw_stats.get("gear1", "0")), GEAR_LEVEL_CAP),
        "gear2": sanitize_level(str(raw_stats.get("gear2", "0")), GEAR_LEVEL_CAP),
        "gear3": sanitize_level(str(raw_stats.get("gear3", "0")), GEAR_LEVEL_CAP),
        "bond_gear": str(raw_stats.get("gear_bond", raw_stats.get("bond_gear", "0"))),
        "book_hp": sanitize_level(
            str(raw_stats.get("book_hp", raw_stats.get("talent_hp", "0"))),
            TALENT_LEVEL_CAP,
        ),
        "book_atk": sanitize_level(
            str(raw_stats.get("book_atk", raw_stats.get("talent_atk", "0"))),
            TALENT_LEVEL_CAP,
        ),
        "book_heal": sanitize_level(
            str(raw_stats.get("book_heal", raw_stats.get("talent_healing", "0"))),
            TALENT_LEVEL_CAP,
        ),
        "star": star_grade,
        "ue": ue,
    }


def format_student_line(name: str, stats: dict[str, Any]) -> str:
    """
    Compose the shared line shape:

        Hina (Dress): UE*3-50 MMMM 10/10/10 25/25/25
        Satsuki: 4* MMMM 10/10/10 25/25/25     <- no UE: star grade/rarity instead
    """
    if stats["ue"] > 0:
        prefix = f"UE*{stats['ue']}-{stats['ue_level']}"
    else:
        prefix = f"{stats['star']}*"

    skills = "".join(
        format_skill(stats[key]) for key in ("ex", "basic", "passive", "sub")
    )
    gear = "/".join(
        sanitize_level(stats[key], GEAR_LEVEL_CAP)
        for key in ("gear1", "gear2", "gear3")
    )
    talents = "/".join(
        sanitize_level(stats[key], TALENT_LEVEL_CAP)
        for key in ("book_hp", "book_atk", "book_heal")
    )

    parts = [prefix, skills, gear]
    if talents != "0/0/0":
        parts.append(talents)

    return f"{name}: " + " ".join(parts)
