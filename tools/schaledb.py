"""
Usage: python -m tools.schaledb
"""

import argparse
import base64
import json
from pathlib import Path
from typing import Any

from rich.console import Console

from src.core.config import Config
from src.utils.data.io import read_json, write_text
from src.utils.sync.data_sync_manager import DataSyncManager

console = Console()


class SchaleDBExporter:
    """
    Transforms scanned student data into SchaleDB import format.
    """

    def __init__(self, output_filename: str = "SchaleDB_import.txt"):
        self.input_file = Config.final_students
        self.output_file = Config.OUTPUT_DIR / output_filename

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
            "s": self._safe_int(current_stats.get("star"), 3),
            "l": self._safe_int(current_stats.get("level"), 1),
            "e1": self._safe_int(current_stats.get("gear1"), 1),
            "e2": self._safe_int(current_stats.get("gear2"), 1),
            "e3": self._safe_int(current_stats.get("gear3"), 1),
            "e4": self._safe_int(
                current_stats.get("gear_bond", current_stats.get("bond_gear")), 0
            ),
            "ws": self._safe_int(current_stats.get("ue"), 0),
            "wl": self._safe_int(current_stats.get("ue_level"), 0),
            "b": self._safe_int(current_stats.get("bond"), 1),
            "s1": self._safe_int(current_stats.get("ex"), 1),
            "s2": self._safe_int(current_stats.get("basic"), 1),
            "s3": self._safe_int(current_stats.get("passive"), 0),
            "s4": self._safe_int(current_stats.get("sub"), 0),
            "pm": self._safe_int(current_stats.get("talent_hp"), 0),
            "pa": self._safe_int(current_stats.get("talent_atk"), 0),
            "ph": self._safe_int(current_stats.get("talent_healing"), 0),
            "lock": lock,
        }

    def process(self, lock: bool = False) -> Path:
        """Processes final_students.json and exports to the Base64 Schale import format."""
        console.print("[bold yellow]Processing SchaleDB Export...[/bold yellow]")

        scanned_data = read_json(self.input_file)
        characters = scanned_data.get("characters", [])

        output_data: dict[str, dict[str, Any]] = {}

        for char in characters:
            char_id = str(char.get("id", ""))
            if not char_id or char_id == "N/A":
                continue

            current_stats = char.get("current", {})
            output_data[char_id] = self.transform_character(current_stats, lock=lock)

        # Serialize dict to JSON string -> encode bytes -> Base64 string
        json_str = json.dumps(output_data, ensure_ascii=False)
        encoded_output = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

        write_text(self.output_file, encoded_output)
        console.print(
            f"[bold green]:heavy_check_mark: Successfully exported ({len(output_data)} characters) to SchaleDB import format:[/bold green] \n"
            f"[cyan]{self.output_file}[/cyan]"
        )

        console.print(
            "Go to [link=https://schaledb.com][cyan]https://schaledb.com[/cyan][/link], open Settings, and scroll down to "
            '"Import Collection". Paste the contents of the exported file, then click Import.'
        )
        return self.output_file


def main():
    parser = argparse.ArgumentParser(
        description="Convert scanner output into SchaleDB import format."
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
        help="Download latest data online before processing.",
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
