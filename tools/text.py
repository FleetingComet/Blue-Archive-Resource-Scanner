"""
Usage: python -m tools.text
"""

import argparse
from pathlib import Path
from typing import Any, ClassVar

from rich.console import Console

from src.core.config import Path_Config
from src.utils.data.io import read_json
from src.utils.data.stat_normalization import format_student_line, normalize_stats
from src.utils.data.student_matching import effective_order, index_students, match_meta
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

    def __init__(self):
        self.students_file = Path_Config.final_students
        self.processed_students_file = Path_Config.students_processed
        self.output_file = Path_Config.OUTPUT_DIR / "students.txt"

    def _sort_key(
        self,
        record: dict[str, Any],
        sort_mode: str,  # "name" | "order"
        group_aliases: list[str],
    ):
        """Deterministic sort: group hierarchy first, then name/order inside."""
        tokens: list[tuple[int, str]] = []
        for alias in group_aliases:
            value = str(record[alias])
            weight = (
                self.SQUAD_ORDER.get(value, len(self.SQUAD_ORDER))
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

    @classmethod
    def parse_group_arg(cls, raw: str) -> list[str]:
        """Parse and validate a comma-separated group list."""
        seen: set[str] = set()
        aliases = [
            token
            for token in (t.strip().lower() for t in raw.split(","))
            if token and not (token in seen or seen.add(token))
        ]
        invalid = [g for g in aliases if g not in cls.GROUP_FIELDS]
        if invalid:
            raise ValueError(
                f"Invalid group field(s): {', '.join(invalid)} "
                f"(choose from: {', '.join(cls.GROUP_FIELDS)})"
            )
        return aliases

    def process(
        self,
        sort_mode: str = "order",  # "name" (alphabetical) | "order" (DefaultOrder)
        group_by: list[str] | None = None,
    ) -> Path:
        """
        Converts and merges scanned outputs into a single text output file.

        Args:
            sort_mode: Sort students alphabetically ("name") or by DB DefaultOrder ("order").
            group_by: Grouping dimensions, outermost first; keys of GROUP_FIELDS.
        """
        console.print("[bold yellow]Exporting students...[/bold yellow]")

        group_aliases = group_by or []
        students_raw = read_json(self.students_file)
        characters = students_raw.get("characters", [])
        by_id, by_name = index_students()

        records: list[dict[str, Any]] = []
        remapped = 0
        for char in characters:
            meta, base_id = match_meta(char, by_id, by_name)
            # Canonicalize to the DB base name
            display_name = meta.get("name") or char.get("name", "")
            char_id = str(base_id) if base_id is not None else str(char.get("id", ""))

            if str(char.get("id")) != char_id:
                remapped += 1
                if base_id is not None and str(char.get("id")) != str(base_id):
                    console.print(
                        f"[dim]{display_name}: alternate style captured "
                        f"(id {char.get('id')}, base {base_id})[/dim]"
                    )

            stats = normalize_stats(char.get("current", {}))

            record: dict[str, Any] = {
                "name": display_name,
                "id": char_id,
                "line": format_student_line(display_name, stats),
                "_order": effective_order(meta),
            }

            for alias in group_aliases:
                record[alias] = meta.get(self.GROUP_FIELDS[alias], "Unknown")

            records.append(record)

        if remapped:
            console.print(
                f"[yellow]Remapped {remapped} scan(s) to their base-form ids[/yellow]"
            )

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
            f"{', '.join(TextProcessor.GROUP_FIELDS)}. "
            "Example: -g type,school,club,attack (flag alone = type,attack)."
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

    processor = TextProcessor()
    processor.process(
        sort_mode="name" if args.alphabetical else "order",
        group_by=TextProcessor.parse_group_arg(args.group) if args.group else None,
    )


if __name__ == "__main__":
    main()
