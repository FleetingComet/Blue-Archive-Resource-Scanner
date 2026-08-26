"""
Usage: python -m tools.text
"""

import argparse
from pathlib import Path
from typing import Any, ClassVar

from rich.console import Console

from src.core.config import Path_Config
from src.utils.data.io import read_json
from src.utils.sync.data_sync_manager import DataSyncManager

console = Console()


class TextProcessor:
    """Export scanned student data into text."""

    # Allowed grouping dimensions -> keys in the processed-students DB.
    GROUP_FIELDS: ClassVar[dict[str, str]] = {
        "type": "SquadType",
        "school": "School",
        "club": "Club",
        "attack": "BulletType",
        "armor": "ArmorType",
        # "star": "StarGrade",
    }

    # Display weight inside groups (STRIKER before SPECIAL).
    SQUAD_ORDER: ClassVar[dict[str, int]] = {"STRIKER": 0, "SPECIAL": 1}

    INDENT = "    "

    GEAR_LEVEL_CAP: int = 10  # T1..T10
    TALENT_LEVEL_CAP: int = 25  # idk

    def __init__(self):
        self.students_file = Path_Config.final_students
        self.processed_students_file = Path_Config.students_processed
        self.output_file = Path_Config.OUTPUT_DIR / "students.txt"

    def _load_db_lookups(
        self,
    ) -> tuple[dict[int, dict[str, Any]], dict[str, dict[str, Any]]]:
        """Index the processed DB by id and by exact name."""
        rows = read_json(self.processed_students_file) or []
        by_id: dict[int, dict[str, Any]] = {}
        by_name: dict[str, dict[str, Any]] = {}
        for row in rows:
            if (sid := row.get("id")) is not None:
                by_id[int(sid)] = row
            if name := row.get("name"):
                by_name[name] = row
        return by_id, by_name

    def _resolve_base_id(
        self, raw_id: Any, by_id: dict[int, dict[str, Any]]
    ) -> int | None:
        """
        Resolve a scanned id to its canonical DB row (StyleId null or 0).

        Dual-mode students are TWO rows sharing one name that link to EACH
        OTHER via LinkedCharacterId; exactly one row has StyleId 0:

            10098  Hoshino (Armed)  StyleId: 0  ->  10099
            10099  Hoshino (Armed)  StyleId: 1  ->  10098

        Plain students have StyleId: null, LinkedCharacterId: null and
        resolve to themselves. Walk links until the StyleId-0 row is hit;
        the cycle guard is a corrupt-data backstop only.
        """
        current = raw_id
        seen: set[int] = set()
        while current is not None:
            try:
                key = int(current)
            except (TypeError, ValueError):
                return None
            if key in seen:  # cycle guard against corrupt A <-> B links
                return key
            seen.add(key)

            meta = by_id.get(key)
            if meta is None:
                return None  # dangling link -> caller uses name fallback

            style_id = meta.get("StyleId")
            linked = meta.get("LinkedCharacterId")
            if not style_id or linked is None:  # base form reached
                return key

            current = linked  # hop toward the base form
        return None

    def _match_meta(
        self,
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
            base_id = self._resolve_base_id(raw_id, by_id)
            if base_id is not None and (meta := by_id.get(base_id)):
                return meta, base_id
        return by_name.get(char.get("name", ""), {}), None

    def _format_stats(self, raw_stats: dict[str, Any]) -> dict[str, Any]:
        """
        Formats character stat values, locking skills based on effective star grade:
        - 1-Star: Passive & Sub locked ('0')
        - 2-Star: Sub locked ('0')
        - 3-Star+: All skills unlocked ('1')

        Owning Unique Equipment implies 5-Star (scanner sometimes misreads
        the star for UE holders), so ue > 0 overrides the scanned star.
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
            "gear1": str(raw_stats.get("gear1", "0")),
            "gear2": str(raw_stats.get("gear2", "0")),
            "gear3": str(raw_stats.get("gear3", "0")),
            "bond_gear": str(
                raw_stats.get("gear_bond", raw_stats.get("bond_gear", "0"))
            ),
            "book_hp": str(raw_stats.get("book_hp", raw_stats.get("talent_hp", "0"))),
            "book_atk": str(
                raw_stats.get("book_atk", raw_stats.get("talent_atk", "0"))
            ),
            "book_heal": str(
                raw_stats.get("book_heal", raw_stats.get("talent_healing", "0"))
            ),
            "star": star_grade,
            "ue": ue,
        }

    @staticmethod
    def _format_skill(value: str | int, max_level=10) -> str:
        """Format skill level, using M for max level, default max level: 10."""
        level = int(value)
        return "M" if level == max_level else str(level)

    @classmethod
    def _sanitize_level(cls, value: str | int, cap: int) -> str:
        """
        Collapse impossible scanner readings down to a legal value.

        Readings within [0, cap] pass through untouched. Anything above the cap
        is treated as an OCR artifact and repeatedly reduced to its last digit
        until legal:  79 -> 9,  11 -> 1,  30 -> 0 (a lost cause either way).
        Legitimate high values (gear 10, talents 25) survive because they're <= cap.
        """
        level = int(value)
        while level > cap:
            level %= 10
        return str(level)

    def _format_student(self, character: dict[str, Any]) -> str:
        """
        Format a scanned student into text.

        For Example:
            Hina (Dress): UE*3-50 MMMM 10/10/10 25/25/25
            Satsuki: UE*4-60 MMMM 10/10/10 25/25/25

        """

        name = character["name"]
        stats = character["current"]

        if stats["ue"] > 0:
            prefix = f"UE*{stats['ue']}-{stats['ue_level']}"
        else:
            prefix = f"{stats['star']}*"

        skills = "".join(
            self._format_skill(stats[key]) for key in ("ex", "basic", "passive", "sub")
        )

        gear = "/".join(
            self._sanitize_level(stats[key], self.GEAR_LEVEL_CAP)
            for key in ("gear1", "gear2", "gear3")
        )

        bond_gear = int(stats["bond_gear"])

        talents = "/".join(
            self._sanitize_level(stats[key], self.TALENT_LEVEL_CAP)
            for key in ("book_hp", "book_atk", "book_heal")
        )
        parts = [prefix, skills, gear]

        if bond_gear != 0:
            parts.append(f"Bond Gear: {bond_gear}")

        if talents != "0/0/0":
            parts.append(talents)

        return f"{name}: " + " ".join(parts)

    @staticmethod
    def _sort_key(
        record: dict[str, Any],
        sort_mode: str,  # "name" | "order"
        group_aliases: list[str],
    ):
        """Deterministic sort: group hierarchy first, then name/order inside."""
        tokens: list[tuple[int, str]] = []
        for alias in group_aliases:
            value = str(record[alias])
            weight = (
                TextProcessor.SQUAD_ORDER.get(value, len(TextProcessor.SQUAD_ORDER))
                if alias == "squad"
                else 0
            )
            tokens.append((weight, value.casefold()))

        name = record["name"].casefold()
        if sort_mode == "name":
            return (*tokens, name)
        return (*tokens, record["_order"], name)

    def _render(
        self,
        records: list[dict[str, Any]],
        group_aliases: list[str],
    ) -> list[str]:
        """Render records, inserting hierarchical [headers] for group paths."""
        lines: list[str] = []
        open_path: list[str] = []

        for record in records:
            path = [str(record[alias]) for alias in group_aliases]

            shared = 0
            for old, new in zip(open_path, path):
                if old != new:
                    break
                shared += 1

            for depth, value in enumerate(path[shared:], start=shared):
                if depth == 0 and lines:
                    lines.append("")  # spacer between top-level sections
                lines.append(f"{self.INDENT * depth}[{value}]")

            open_path = path
            lines.append(f"{self.INDENT * len(group_aliases)}{record['line']}")

        return lines

    def process(
        self,
        sort_mode: str = "order",  # "name" (alphabetical) | "order" (DefaultOrder)
        group_by: list[str] | None = None,
    ) -> Path:
        """
        Converts and merges scanned outputs into a single text output file.

        Args:
            sort_mode: Sort students alphabetically ("name") or by DB DefaultOrder ("order").
            group_by: List of grouping dimensions, ordered outermost -> innermost.
                      Valid aliases live in GROUP_FIELDS (squad, school, club, bullet, armor, star).
        """
        console.print("[bold yellow]Exporting students...[/bold yellow]")

        group_aliases = group_by or []
        unknown = [g for g in group_aliases if g not in self.GROUP_FIELDS]
        if unknown:
            msg = ", ".join(unknown)
            raise ValueError(
                f"Unknown group dimension(s): {msg}. "
                f"Valid: {', '.join(self.GROUP_FIELDS)}"
            )
        students_raw = read_json(self.students_file)
        characters = students_raw.get("characters", [])
        by_id, by_name = self._load_db_lookups()

        records: list[dict[str, Any]] = []
        for char in characters:
            meta, base_id = self._match_meta(char, by_id, by_name)
            # Canonicalize to the DB base name
            display_name = meta.get("name") or char.get("name", "")
            current_stats = self._format_stats(char.get("current", {}))

            # The scan may land on either row of a dual-mode pair; surface the
            # normalization while it happens (delete this if it gets noisy).
            if base_id is not None and str(char.get("id")) != str(base_id):
                console.print(
                    f"[dim]{display_name}: alternate style captured "
                    f"(id {char.get('id')}, base {base_id})[/dim]"
                )

            line = self._format_student(
                {"name": display_name, "current": current_stats}
            )

            default_order = meta.get("DefaultOrder")
            record: dict[str, Any] = {
                "name": char.get("name", ""),
                "line": line,
                "_order": default_order if isinstance(default_order, int) else 10**9,
            }
            for alias in group_aliases:
                record[alias] = meta.get(self.GROUP_FIELDS[alias], "Unknown")

            records.append(record)

        records.sort(key=lambda r: self._sort_key(r, sort_mode, group_aliases))

        if group_aliases:
            lines = self._render(records, group_aliases)
        else:
            lines = [record["line"] for record in records]

        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        console.print(f"[bold green]✓ Exported {len(lines)} entries[/bold green]")
        console.print(f"[dim]{self.output_file}[/dim]")

        return self.output_file


def main():
    parser = argparse.ArgumentParser(
        description="Convert and merge scanner output into text format."
    )

    parser.add_argument(
        "-a",
        "--alphabetical",
        action="store_true",
        help="Sort their name into alphabetical",
    )

    parser.add_argument(
        "-g",
        "--group",
        nargs="?",
        const="squad,bullet",
        metavar="FIELDS",
        help=(
            "Grouping hierarchy, outermost first. Comma-separated from: "
            "squad, school, club, bullet, armor, star. "
            "Example: -g squad,school,club,bullet (flag alone = squad,bullet)."
        ),
    )

    parser.add_argument(
        "-o",
        "--online",
        action="store_true",
        help="Download the latest community-maintained data before processing.",
    )
    args = parser.parse_args()

    # try update processed data
    if args.online:
        try:
            DataSyncManager().update_from_online()
        except Exception:  # noqa: BLE001, S110
            pass

    group_by = None
    if args.group is not None:
        seen: set[str] = set()
        group_by = [
            token
            for token in (t.strip().lower() for t in args.group.split(","))
            if token and not (token in seen or seen.add(token))
        ]
        invalid = [g for g in group_by if g not in TextProcessor.GROUP_FIELDS]
        if invalid:
            parser.error(
                f"Invalid group field(s): {', '.join(invalid)} "
                f"(choose from: {', '.join(TextProcessor.GROUP_FIELDS)})"
            )

    processor = TextProcessor()
    processor.process(
        sort_mode="name" if args.alphabetical else "order",
        group_by=group_by,
    )


if __name__ == "__main__":
    main()
