"""
Usage: python -m tools.schaledb
"""

import argparse
import base64
import json
from pathlib import Path
from typing import Any

from rich.console import Console

from src.core.config import Path_Config
from src.utils.data.io import read_json, write_text
from src.utils.data.stat_normalization import normalize_stats
from src.utils.data.student_matching import index_students, iter_style_ids
from src.utils.sync.data_sync_manager import DataSyncManager

console = Console()


class SchaleDBExporter:
    """
    Transforms scanned student data into SchaleDB import format.
    """

    def __init__(self, output_filename: str = "SchaleDB_import.txt"):
        self.input_file = Path_Config.final_students
        self.output_file = Path_Config.OUTPUT_DIR / output_filename

    def _safe_int(self, value: Any, default: int = 0) -> int:
        """Safely parses string/int values to integer."""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def transform_character(
        self, current_stats: dict[str, Any], lock: bool = False
    ) -> dict[str, Any]:
        """Transforms character stats into the target site format."""
        return {
            "s": self._safe_int(current_stats.get("star"), 1),
            "l": self._safe_int(current_stats.get("level"), 1),
            "e1": self._safe_int(current_stats.get("gear1"), 0),
            "e2": self._safe_int(current_stats.get("gear2"), 0),
            "e3": self._safe_int(current_stats.get("gear3"), 0),
            "e4": self._safe_int(current_stats.get("bond_gear"), 0),
            "ws": self._safe_int(current_stats.get("ue"), 0),
            "wl": self._safe_int(current_stats.get("ue_level"), 0),
            "b": self._safe_int(current_stats.get("bond"), 1),
            "s1": self._safe_int(current_stats.get("ex"), 1),
            "s2": self._safe_int(current_stats.get("basic"), 1),
            "s3": self._safe_int(current_stats.get("passive"), 0),
            "s4": self._safe_int(current_stats.get("sub"), 0),
            "pm": self._safe_int(current_stats.get("book_hp"), 0),
            "pa": self._safe_int(current_stats.get("book_atk"), 0),
            "ph": self._safe_int(current_stats.get("book_heal"), 0),
            "lock": lock,
        }

    def process(self, lock: bool = False) -> Path:
        """Processes final_students.json and exports to the Base64 Schale import format."""
        console.print("[bold yellow]Processing SchaleDB Export...[/bold yellow]")

        scanned_data = read_json(self.input_file)
        characters = scanned_data.get("characters", [])

        by_id, _by_name = index_students()

        output_data: dict[str, dict[str, Any]] = {}
        expanded = 0

        for char in characters:
            raw_id = str(char.get("id", ""))
            if not raw_id or raw_id == "N/A":
                continue

            transformed_stats = self.transform_character(
                normalize_stats(char.get("current", {})), lock=lock
            )
            # Every id belonging to this student; [raw_id] for unknown ones
            style_ids = iter_style_ids(raw_id, by_id) or [raw_id]
            if len(style_ids) > 1:
                expanded += 1

            for sid in style_ids:
                output_data[str(sid)] = transformed_stats

        # Serialize dict to JSON string -> encode bytes -> Base64 string
        json_str = json.dumps(output_data, ensure_ascii=False)
        encoded_output = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

        write_text(self.output_file, encoded_output)
        console.print(
            f"[bold green]:heavy_check_mark: Successfully exported ({len(output_data)} characters) to SchaleDB import format:[/bold green] \n"
            f"[cyan]{self.output_file}[/cyan]"
        )

        if expanded:
            console.print(
                f"[yellow]Expanded {expanded} dual-style student(s) into entries for both form ids[/yellow]"
            )

        console.print(
            "Go to [link=https://schaledb.com][cyan]https://schaledb.com[/cyan][/link], open Settings, and scroll down to "
            '"Import Collection". Paste the contents of the exported file, then click Import.'
        )
        return self.output_file


def main():
    parser = argparse.ArgumentParser(
        description="Convert scanner output into Schale DB import format."
    )
    parser.add_argument(
        "-l",
        "--lock",
        action="store_true",
        help="Set the 'lock' field to true for all characters.",
    )

    parser.add_argument(
        "-o",
        "--online",
        action="store_true",
        help="Download the latest community-maintained data before processing.",
    )
    args = parser.parse_args()

    if args.online:
        try:
            DataSyncManager().update_from_online()

        except Exception as e:  # noqa: BLE001
            console.print(f"[yellow]Online sync warning: {e}[/yellow]")

    processor = SchaleDBExporter()
    processor.process(lock=args.lock)


if __name__ == "__main__":
    main()
