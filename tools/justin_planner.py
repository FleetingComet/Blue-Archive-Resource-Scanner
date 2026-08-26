"""
Usage: python -m tools.justin_planner
"""

import argparse
from pathlib import Path
from typing import Any, ClassVar

from rich.console import Console

from src.core.config import Path_Config
from src.utils.data.io import read_json, write_json
from src.utils.sync.data_sync_manager import DataSyncManager
from tools.utils.stats import normalize_stats
from tools.utils.students import index_students, match_meta

console = Console()


class JustinPlannerProcessor:
    """
    Transforms and merges scanned scanner outputs (Equipment, Items, Students)
    into a unified export file compatible with Justin's Blue Archive Planner.
    """

    CATEGORY_NAME_MAP: ClassVar[dict[str, str]] = {
        "WeaponExpGrowthA": "Spring",
        "WeaponExpGrowthB": "Hammer",
        "WeaponExpGrowthC": "Barrel",
        "WeaponExpGrowthZ": "Needle",
    }

    DEFAULT_TEMPLATE: ClassVar[dict[str, Any]] = {
        "exportVersion": 2,
        "characters": [],
        "character_order": [],
        "disabled_characters": [],
        "owned_materials": {},
        "groups": {
            "Binah": [],
            "Chesed": [],
            "Hod": [],
            "ShiroKuro": [],
            "Perorodzilla": [],
            "Goz": [],
            "Hieronymous": [],
            "Kaiten": [],
        },
        "language": "EN",
        "level_cap": 90,
        "server": "Global",
        "site_version": "1.4.22",
    }

    DEFAULT_ELEPH: ClassVar[dict[str, Any]] = {
        "owned": "0",
        "unlocked": True,
        "cost": "1",
        "purchasable": "20",
        "farm_nodes": "0",
        "node_refresh": False,
        "use_eligma": False,
        "use_shop": False,
    }

    def __init__(self):
        self.equipment_file = Path_Config.final_equipment
        self.items_file = Path_Config.final_items
        self.students_file = Path_Config.final_students
        self.input_file = Path_Config.justin_planner_data
        self.output_file = Path_Config.justin_planner_merged_output

    def _transform_equipment(
        self, grouped_data: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Transforms equipment and growth material keys to Justin Planner format."""
        transformed = {}
        for category, items in grouped_data.items():
            if not isinstance(items, dict):
                continue
            transformed_category = self.CATEGORY_NAME_MAP.get(category, category)
            for key, value in items.items():
                if category == "Exp":
                    new_key = f"GXP_{key}"
                else:
                    new_key = f"T{key}_{transformed_category}"
                transformed[new_key] = value
        return transformed

    def _get_target_stats(
        self,
        current_stats: dict[str, Any],
        set_max_target: bool,
        has_bond_gear: bool = False,
    ) -> dict[str, Any]:
        """Generates target stats (MAX stats or matching current stats)."""
        target = dict(current_stats)
        if set_max_target:
            target.update(
                {
                    "level": "90",
                    "ue_level": "60",
                    "bond": "100",
                    "ex": "5",
                    "basic": "10",
                    "passive": "10",
                    "sub": "10",
                    "gear1": "10",
                    "gear2": "10",
                    "gear3": "10",
                    "bond_gear": "2" if has_bond_gear else "0",
                    "book_hp": "25",
                    "book_atk": "25",
                    "book_heal": "25",
                    "star": 5,
                    "ue": 4,
                }
            )
        return target

    def process(
        self,
        set_max_target: bool = False,
        base_file_path: str | Path | None = None,
    ) -> Path:
        """
        Converts and merges scanned outputs into a single Justin Planner output file.

        Args:
            set_max_target: If True, sets new characters' target stats to MAX (90, EX 5, 10/10/10, etc.).
            base_file_path: Path to an existing Justin Planner JSON to merge into.
        """
        console.print("[bold yellow]Processing Justin Planner Export...[/bold yellow]")

        equipment_raw = read_json(self.equipment_file)
        items_raw = read_json(self.items_file)
        students_raw = read_json(self.students_file)

        # Shared lookups: dual-style scans resolve to their base form
        by_id, by_name = index_students()

        # Transform materials
        transformed_equipment = self._transform_equipment(equipment_raw)
        transformed_items = dict(items_raw)
        new_materials = {**transformed_equipment, **transformed_items}

        # Load base/existing Planner file or default template
        base_path = base_file_path or self.input_file
        planner_data = read_json(base_path)
        if not planner_data:
            planner_data = dict(self.DEFAULT_TEMPLATE)

        # Merge Owned Materials
        owned_materials = planner_data.get("owned_materials", {})
        planner_data["owned_materials"] = {**owned_materials, **new_materials}

        # Merge Character Stats
        existing_chars_map = {
            c["id"]: c
            for c in planner_data.get("characters", [])
            if isinstance(c, dict) and "id" in c
        }

        updated_characters: list[dict[str, Any]] = []
        scanned_characters = students_raw.get("characters", [])
        remapped = 0

        for char in scanned_characters:
            meta, base_id = match_meta(char, by_id, by_name)

            # Canonical id: resolved base form -> name-match id -> raw passthrough
            if base_id is not None:
                char_id = str(base_id)
            elif isinstance(meta.get("id"), int):
                char_id = str(meta["id"])
            else:
                char_id = str(char.get("id", ""))

            if str(char.get("id", "")) != char_id:
                remapped += 1

            display_name = meta.get("name") or char.get("name", "")
            # Look up StarGrade and hasBondGear metadata from students_processed.json
            has_bond_gear = bool(meta.get("hasBondGear", False))

            current_stats = normalize_stats(char.get("current", {}))

            if char_id in existing_chars_map:
                # Update existing character stats while preserving user's custom targets/settings
                existing_char = existing_chars_map[char_id]
                existing_char["current"] = current_stats
                existing_char["hasBondGear"] = has_bond_gear
                updated_characters.append(existing_char)
            else:
                # Add new character
                new_char = {
                    "id": char_id,
                    "name": display_name,
                    "current": current_stats,
                    "target": self._get_target_stats(
                        current_stats=current_stats,
                        set_max_target=set_max_target,
                        has_bond_gear=has_bond_gear,
                    ),
                    "eleph": dict(self.DEFAULT_ELEPH),
                    "enabled": True,
                    "hasBondGear": has_bond_gear,
                }
                updated_characters.append(new_char)

        planner_data["characters"] = updated_characters

        write_json(self.output_file, planner_data)
        if remapped:
            console.print(
                f"[yellow]Remapped {remapped} scan(s) to their base-form ids[/yellow]"
            )
        console.print(
            f"[bold green]✔ Successfully exported Justin Planner data to:[/bold green] \n{self.output_file}"
        )
        return self.output_file


def main():
    parser = argparse.ArgumentParser(
        description="Convert and merge scanner output into Justin Planner format."
    )
    parser.add_argument(
        "-m",
        "--max-target",
        action="store_true",
        help="Set target stats to MAX for newly added characters.",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        default=None,
        help="Path to an existing Justin Planner export file to merge with. Leave it empty for default path",
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

    processor = JustinPlannerProcessor()
    processor.process(set_max_target=args.max_target, base_file_path=args.file)


if __name__ == "__main__":
    main()
