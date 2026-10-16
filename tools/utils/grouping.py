"""Shared grouping / sorting / record-building for roster exporters."""

from collections.abc import Iterator
from typing import Any

GROUP_FIELDS: dict[str, str] = {
    "type": "SquadType",
    "school": "School",
    "club": "Club",
    "attack": "BulletType",
    "armor": "ArmorType",
    # "star": "StarGrade",
}

# Display weight inside groups (STRIKER before SPECIAL).
SQUAD_ORDER: dict[str, int] = {"STRIKER": 0, "SPECIAL": 1}


def validate_groups(aliases: list[str]) -> None:
    unknown = [g for g in aliases if g not in GROUP_FIELDS]
    if unknown:
        raise ValueError(
            f"Unknown group dimension(s): {', '.join(unknown)}. "
            f"Valid: {', '.join(GROUP_FIELDS)}"
        )


def parse_group_arg(raw: str) -> list[str]:
    """Parse + dedupe a comma-separated group list, validating aliases."""
    seen: set[str] = set()
    aliases = [
        token
        for token in (t.strip().lower() for t in raw.split(","))
        if token and not (token in seen or seen.add(token))
    ]
    validate_groups(aliases)
    return aliases


def sort_key(
    record: dict[str, Any],
    sort_mode: str,  # "name" | "order"
    group_aliases: list[str],
):
    """Deterministic sort: group hierarchy first, then name/order inside."""
    tokens: list[tuple[int, str]] = []
    for alias in group_aliases:
        value = str(record[alias])
        weight = (
            SQUAD_ORDER.get(value, len(SQUAD_ORDER))
            if GROUP_FIELDS[alias] == "SquadType"
            else 0
        )
        tokens.append((weight, value.casefold()))

    name = record["name"].casefold()
    if sort_mode == "name":
        return (*tokens, name)
    return (*tokens, record["_order"], name)


def walk_hierarchy(
    records: list[dict[str, Any]], group_aliases: list[str]
) -> Iterator[tuple[str, Any]]:
    """
    Stream rendering events for a sorted, grouped record list:
      ("headers", [(alias, depth, value), ...])  <- emit these section headings
      ("item", record)                           <- then this student
    Only CHANGED heading suffixes are emitted as the group path evolves.
    """
    open_path: list[str] = []
    for record in records:
        path = [str(record[a]) for a in group_aliases]

        shared = 0
        for old, new in zip(open_path, path):
            if old != new:
                break
            shared += 1

        yield (
            "headers",
            [
                (alias, depth, value)
                for depth, (alias, value) in enumerate(
                    zip(group_aliases[shared:], path[shared:]), start=shared
                )
            ],
        )
        yield ("item", record)
        open_path = path
