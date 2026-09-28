"""
Usage: python -m tools.yuzu_trends
"""

import argparse
import random
import time
from pathlib import Path
from typing import Any, ClassVar

from rich.console import Console
from rich.panel import Panel

from src.core.config import Path_Config
from src.utils.data.io import read_json, write_json
from src.utils.data.stat_normalization import normalize_stats
from src.utils.data.student_matching import index_students, match_meta
from src.utils.sync.data_sync_manager import DataSyncManager

console = Console()


class YuzuTrendsExporter:
    """
    Transforms scanned outputs into YuzuTrends' native full planner format.

    Native material namespaces (from externalImportConverters.ts):
      Equipment_{id}   equipment-domain items (enhancement stones, blueprints)
      Item_{id}        generic items (materials, reports, eleph)
      ownedGifts["x"]  gifts, IDs 5000..5999
    """

    EXPORT_VERSION = "2.0.1"

    # Categories from equipment_processed.json whose game items live in the
    # generic `Item_` namespace instead of `Equipment_`.
    ITEM_NAMESPACE_CATEGORIES: ClassVar[set[str]] = {
        "WeaponExpGrowthA",
        "WeaponExpGrowthB",
        "WeaponExpGrowthC",
        "WeaponExpGrowthZ",
    }

    GIFT_ID_MIN: ClassVar[int] = 5000
    GIFT_ID_MAX: ClassVar[int] = 6000

    DEFAULT_ELIGMA_INFO: ClassVar[dict[str, int]] = {"price": 1, "stock": 20}

    def __init__(self, output_filename: str = "yuzu_trends_planner.json"):
        self.equipment_file = Path_Config.final_equipment
        self.items_file = Path_Config.final_items
        self.students_file = Path_Config.final_students
        self.equipment_processed_file = Path_Config.equipment_processed
        self.output_file = Path_Config.OUTPUT_DIR / output_filename

        # category -> {tier: game_item_id}
        self.id_by_cat_tier: dict[str, dict[int, int]] = {}
        self._build_lookups()

    def _build_lookups(self) -> None:
        equipment_processed = read_json(self.equipment_processed_file) or []

        by_cat: dict[str, list[dict[str, Any]]] = {}
        for entry in equipment_processed:
            if not isinstance(entry, dict):
                continue
            cat = entry.get("category")
            if cat is not None:
                by_cat.setdefault(cat, []).append(entry)

        for cat, entries in by_cat.items():
            entries.sort(key=lambda e: e.get("id", 0))
            table = self.id_by_cat_tier.setdefault(cat, {})

            tiers = {e.get("tier") for e in entries}

            if tiers == {0}:
                # All entries are unranked in the source; assign 1..N by id order.
                for idx, entry in enumerate(entries):
                    if "id" in entry:
                        table[idx + 1] = entry["id"]
            else:
                for entry in entries:
                    tier = entry.get("tier")
                    item_id = entry.get("id")
                    if tier is not None and item_id is not None:
                        table[tier] = item_id

    def _resolve_material_key(self, category: str, tier: int) -> str | None:
        table = self.id_by_cat_tier.get(category)
        if not table:
            return None
        item_id = table.get(tier)
        if item_id is None:
            return None
        if category in self.ITEM_NAMESPACE_CATEGORIES:
            return f"Item_{item_id}"
        return f"Equipment_{item_id}"

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _equipment_to_materials(
        self, grouped: dict[str, dict[str, Any]]
    ) -> tuple[dict[str, int], set[str]]:
        """Returns (materials, unresolved_categories)."""
        materials: dict[str, int] = {}
        unresolved: set[str] = set()
        if not isinstance(grouped, dict):
            return materials, unresolved

        for category, items in grouped.items():
            if not isinstance(items, dict) or not items:
                continue

            resolved_any = False
            for key, value in items.items():
                qty = self._safe_int(value)
                if qty <= 0:
                    continue
                tier = self._safe_int(key)
                out = self._resolve_material_key(category, tier)
                if out is None:
                    continue
                resolved_any = True
                materials[out] = materials.get(out, 0) + qty

            if not resolved_any:
                unresolved.add(category)

        return materials, unresolved

    def _items_to_inventory(
        self, items: dict[str, Any]
    ) -> tuple[dict[str, int], dict[str, int]]:
        """Splits items_processed keys into (materials, gifts)."""
        materials: dict[str, int] = {}
        gifts: dict[str, int] = {}
        if not isinstance(items, dict):
            return materials, gifts

        for key, value in items.items():
            if not str(key).isdigit():
                continue
            qty = self._safe_int(value)
            if qty <= 0:
                continue
            item_id = int(key)

            if self.GIFT_ID_MIN <= item_id < self.GIFT_ID_MAX:
                gifts[str(item_id)] = gifts.get(str(item_id), 0) + qty
            else:
                out = f"Item_{item_id}"
                materials[out] = materials.get(out, 0) + qty

        return materials, gifts

    def _to_current(self, stats: dict[str, Any]) -> dict[str, Any]:
        """YuzuTrends 'current' object."""
        return {
            "level": self._safe_int(stats.get("level"), 1),
            "star": self._safe_int(stats.get("star"), 1),
            "uw": self._safe_int(stats.get("ue"), 0),
            "uwLevel": self._safe_int(stats.get("ue_level"), 0),
            "ex": self._safe_int(stats.get("ex"), 1),
            "normal": self._safe_int(stats.get("basic"), 1),
            "passive": self._safe_int(stats.get("passive"), 1),
            "sub": self._safe_int(stats.get("sub"), 0),
            "eleph": self._safe_int(stats.get("eleph"), 0),
            "affection": self._safe_int(stats.get("bond"), 1),
            "affectionExp": 0,
            "equipment": [
                self._safe_int(stats.get("gear1"), 0),
                self._safe_int(stats.get("gear2"), 0),
                self._safe_int(stats.get("gear3"), 0),
            ],
            "gear": self._safe_int(stats.get("bond_gear"), 0),
            "potential": {
                "hp": self._safe_int(stats.get("book_hp"), 0),
                "atk": self._safe_int(stats.get("book_atk"), 0),
                "heal": self._safe_int(stats.get("book_heal"), 0),
            },
        }

    def _max_target(self, has_bond_gear: bool) -> dict[str, Any]:
        return {
            "level": 90,
            "star": 5,
            "uw": 4,
            "uwLevel": 60,
            "ex": 5,
            "normal": 10,
            "passive": 10,
            "sub": 10,
            "affection": 100,
            "equipment": [10, 10, 10],
            "gear": 2 if has_bond_gear else 0,
            "potential": {"hp": 25, "atk": 25, "heal": 25},
        }

    @staticmethod
    def _current_to_target(current: dict[str, Any]) -> dict[str, Any]:
        return {
            "level": current["level"],
            "star": current["star"],
            "uw": current["uw"],
            "uwLevel": current["uwLevel"],
            "ex": current["ex"],
            "normal": current["normal"],
            "passive": current["passive"],
            "sub": current["sub"],
            "affection": current["affection"],
            "equipment": list(current["equipment"]),
            "gear": current["gear"],
            "potential": dict(current["potential"]),
        }

    def process(self, set_max_target: bool = False) -> Path:
        console.print("[bold yellow]Processing YuzuTrends Export...[/bold yellow]")

        equipment_raw = read_json(self.equipment_file)
        items_raw = read_json(self.items_file)
        students_raw = read_json(self.students_file)

        by_id, by_name = index_students()

        materials, unresolved = self._equipment_to_materials(equipment_raw)
        item_materials, gifts = self._items_to_inventory(items_raw)
        materials.update(item_materials)

        global_plans: list[dict[str, Any]] = []
        scanned_characters = students_raw.get("characters", [])
        remapped = 0

        for char in scanned_characters:
            meta, base_id = match_meta(char, by_id, by_name)

            if base_id is not None:
                char_id = str(base_id)
            elif isinstance(meta.get("id"), int):
                char_id = str(meta["id"])
            else:
                char_id = str(char.get("id", ""))

            if str(char.get("id", "")) != char_id:
                remapped += 1

            has_bond_gear = bool(meta.get("hasBondGear", False))
            stats = normalize_stats(char.get("current", {}))
            current = self._to_current(stats)

            target = (
                self._max_target(has_bond_gear)
                if set_max_target
                else self._current_to_target(current)
            )

            if current["eleph"] > 0:
                materials[f"Item_{char_id}"] = current["eleph"]

            uid = (
                f"import-{char_id}-{int(time.time() * 1000)}"
                f"-{random.randint(0, 10**9)}"
            )
            global_plans.append(
                {
                    "uuid": uid,
                    "studentId": self._safe_int(char_id, 0),
                    "current": current,
                    "target": target,
                    "includedInEvents": [],
                    "useEligmaForStar": False,
                    "eligmaInfo": dict(self.DEFAULT_ELIGMA_INFO),
                    "isSelected": True,
                }
            )

        payload = {
            "eventPlans": {},
            "globalPlans": global_plans,
            "ownedGifts": gifts,
            "materialInventory": materials,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "version": self.EXPORT_VERSION,
        }

        write_json(self.output_file, payload)

        if remapped:
            console.print(
                f"[yellow]Remapped {remapped} scan(s) to their base-form ids[/yellow]"
            )

        if unresolved:
            console.print(
                f"[yellow]Skipped categories absent from equipment_processed.json: "
                f"{', '.join(sorted(unresolved))}[/yellow]"
            )

        console.print(
            Panel(
                f"[bold green]:heavy_check_mark: Export complete![/bold green]\n\n"
                f"[bold]Characters:[/bold] {len(global_plans)}\n"
                f"[bold]Materials:[/bold] {len(materials)}\n"
                f"[bold]Gift types:[/bold] {len(gifts)}\n\n"
                f'[bold]Output:[/bold] [cyan]"{self.output_file!s}"[/cyan]',
                title="[bold green]Data Export[/bold green]",
                border_style="green",
            )
        )
        console.print(
            Panel(
                "[bold cyan]1.[/bold cyan] Go to "
                "[bold]Planner → Student Growth Planner[/bold]\n\n"
                "[bold cyan]2.[/bold cyan] Scroll to "
                "[bold]Data Export/Import[/bold]\n\n"
                "[bold cyan]3.[/bold cyan] Click/Tap the [bold]Import[/bold] tab\n\n"
                "[bold cyan]4.[/bold cyan] Choose [bold]Load File[/bold] and select:\n"
                f'    [cyan]"{self.output_file!s}"[/cyan]\n\n'
                "[bold cyan]5.[/bold cyan] Alternatively, copy the contents of the file "
                "and paste them into the [bold]TextArea[/bold]\n\n"
                "[bold cyan]6.[/bold cyan] Click [bold green]Apply Data[/bold green]",
                title="[bold yellow]Import Instructions[/bold yellow]",
                border_style="yellow",
            )
        )
        return self.output_file


def main():
    parser = argparse.ArgumentParser(
        description="Convert scanner output into YuzuTrends native planner format."
    )
    parser.add_argument(
        "-m",
        "--max-target",
        action="store_true",
        help="Set target stats to MAX for every character.",
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
        except Exception:  # noqa: BLE001, S110
            pass

    exporter = YuzuTrendsExporter()
    exporter.process(set_max_target=args.max_target)


if __name__ == "__main__":
    main()
