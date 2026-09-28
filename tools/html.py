"""
Usage: python -m tools.html
"""

import argparse
import html as html_mod
from pathlib import Path
from typing import Any

from rich.console import Console

from src.core.config import Path_Config
from src.utils.data.io import read_json
from src.utils.data.stat_normalization import (
    GEAR_LEVEL_CAP,
    TALENT_LEVEL_CAP,
    format_skill,
    format_student_line,
    normalize_stats,
    sanitize_level,
)
from src.utils.data.student_matching import effective_order, index_students, match_meta
from src.utils.sync.data_sync_manager import DataSyncManager
from tools.utils.grouping import GROUP_FIELDS, parse_group_arg, sort_key, walk_hierarchy

console = Console()

ATTACK_COLORS = {
    "Explosive": "#920008",
    "Piercing": "#bd8901",
    "Corrosive": "#137973",
    "Mystic": "#226f9b",
    "Sonic": "#9945a8",
    "Normal": "#485582",
}
ARMOR_COLORS = {
    "Light": "#920008",
    "Heavy": "#bd8901",
    "Composite": "#137973",
    "Special": "#226f9b",
    "Elastic": "#9945a8",
    "Normal": "#485582",
}

_CSS = """
body{font-family:system-ui,sans-serif;background:#15181e;color:#dde1e8;
     margin:24px auto;max-width:1100px;padding:0 16px}
h1{color:#fff}h2,h3,h4,h5{color:#aab4c4;border-bottom:1px solid #2a2f38;padding-bottom:4px;margin-top:28px}
.grid{display:flex;flex-wrap:wrap;gap:14px}
.card{background:#1d2129;border:1px solid #2a2f38;border-radius:10px;padding:8px;width:168px}
.thumb{position:relative;width:152px;height:152px}
.thumb img{width:100%;height:100%;object-fit:cover;border-radius:8px;display:block}
.badge{position:absolute;background:rgba(0,0,0,.72);color:#fff;font-size:11px;
       padding:1px 6px;border-radius:5px;line-height:1.5;font-variant-numeric:tabular-nums}
.b-tl{top:4px;left:4px}.b-tr{top:4px;right:4px;background:rgba(0,0,0,.72)}
.b-bl{bottom:4px;left:4px;letter-spacing:1px}
.b-br{bottom:4px;right:4px}
.ue{color:#8cf7ff;font-weight:700}
.stars{color:#ffee3f}
.name{margin-top:6px;font-weight:600;color:#fff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sub{font-size:12px;color:#8b94a3;display:flex;align-items:center;gap:5px;margin-top:2px}
.sub img{height:16px;width:16px;object-fit:contain}
.chips{margin-top:6px;display:flex;gap:5px}
.chip{color:#fff;font-size:11px;padding:1px 7px;border-radius:4px;text-shadow:0 1px 1px rgba(0,0,0,.55)}
.talents{margin-top:4px;font-size:12px;color:#9aa3b1}
"""


class HtmlExporter:
    """Export scanned student data into a self-contained HTML roster page."""

    TITLE = "Student Roster"
    IMAGE_BASE = "https://schaledb.com/images/student/collection/"
    SCHOOL_IMAGE_BASE = "https://schaledb.com/images/schoolicon/"
    BOND_GEAR_BASE = "https://schaledb.com/images/gear/icon/"

    def __init__(self):
        self.students_file = Path_Config.final_students
        self.output_file = Path_Config.OUTPUT_DIR / "students.html"

    def _chip(self, label: str, colors: dict[str, str], type: str) -> str:
        color = colors.get(label)
        if not color:
            return ""
        if type == "armor":
            image = """<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAMAAADW3miqAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAGnUExURQAAAP////////////////////////////////////////////7+/v////////////////////////////////////////////////////////////////////////////////////7+/v////////////////////////////////////////////////////////////////////////////////////////////////7+/v////7+/v////////////////////////7+/v////////////7+/v7+/v////////////////////////////////////////////////////////7+/v////////////////////////////////7+/v////////////////////7+/v////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////7+/ge/Hp0AAACLdFJOUwAhGgvX/W8BAwTg1vdgnPe0wPRfV1oM56rq71n+Ds6MHB3+xePeuwjRAiesrva+E8YtwVQ0cSnx+b10zdA+Ze7tbX6paOSiz/EcsNSgFaSL0vJGLNnTQniHieXfYiMPc33Qpvo/HtgCPEUJH/vD4si484/4BpL8mDnVChmz3UqCFCXoESSXIodWEFFiU8m7AAABuElEQVQ4y4XU5XvCMBAG8GJLYdiYAjOYG3N3d3d3d3f3hT963e5amtKx+3Zvf/Ak7SUcp6j1/iOe+6d0fQaasxXaJO9SoRK3Q5nNW/pb4RdZ6oBw+ZNnFOt4PkFtZVk6i9Pr9/tRGUYLjUT+/O7x4Tk7aY1SfwBRengwNidsRIsohz7ZfnMGCWVaskbkIsqVhAL9ZBGI7HIUn5qqinwy5I3TXt/I0T6iFAiEyLzoJjx/YtHvSCgTUTsklUmnGxmQJEQ1x9UACkekBxTGvrhGFpkAlbIoDFArtvWA6lgUCagBW3iT1KKKzNjmAYpmUTSLnICiWFQMaDDk7nDhI9h2AbKyyArIjm0TID0zZkY9oAXsa/HTu+VoCD/fMPadHdDHagOzrI2FzOUR/7kaf5XSK52aAowuM8SoRRyN7hIIVjLFZEZaaIxJzCraynhec27DOaFpMYFVVkljFl9u73EZxGGi4/L9ptPgElC6UX4wNWkqik6vMqeXePaCzZSGPeKEaBKVZiCbKC4Cwl3dM2R5Qqd2YZCXIodI8nyz6rcKIcbCd4ewfYPj9e2P205AHMd/fhQUfeUrHn0DUbQrGY52KagAAAAASUVORK5CYII=" alt="" width="14" height="14" />"""
        else:
            image = """<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAMAAADW3miqAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAGAUExURQAAAP////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////7+/v7+/v7+/v////////////////////////////////////////////////////7+/v////////////////7+/v7+/v////////////////////////////////////////7+/v////////////////////////////////////////////////////////////7+/v////////////////////////////////////////////////////////////////////////////////////////////////////7+/smIAEUAAAB+dFJOUwAE7xYC/voBA/336Pm9/Ajt1h4F7AtUlJMZ3BIu3n23QmTdKArQWywVYukGxwfLpT6SDhAvpPqFH6bycWoge9qd7jax8itB0+M8+B0j5WVP6yoNRcnhwoy48CekjmevNRP2P8q+cAkUPJ71InJjazGsm4SqQ7olqavfXhx3SzRGD9cAAAGWSURBVDjLddRVY8IwEADgAIUU3WCMKWMbM2DA3N3d3d3d9fjrS+hYw7jc07X5mlzTXAnJDFUlZSVb5ztHh35vdgGRhQ/+olpmcip1dCxDVboBp8TkjgnIpuIoZBaQZQM1DV7BgHkWRZ3iRAA9mMnK1kGCxSBiaCukIzuCGo3/kA9B9ZCGJhYR09YhTgOWAazs5rS1YAQzTS0iGhpH96hdrMjuofqIwZDKisV9nPOoAnpz1miJsiaY6WFVQCErvNdpE1l10zuvKIqO4mzI9cFPxLXlz/gLaFqxhi8XgPWRp0+2X1M+Sem/d/q2s/uxF5Zd1iZN4RTNQOQzxkbCdQoh0Ve2uLsG3Z/oPRuzXLHCDDeOQpPkXFdUOdhkzxGWVpukrUbukgXfygGlkTj/ngAXpYoUqQGXhsD6IFO5K9rJcPBj6dxDTdFSIhmQF+QNbtzF3sytmYQtSE8DbC/2yzLbNqfrF63yq21e2SbS3KXL3KxrG3QWZuUfICt2j7LH81Il1kI+Rfu2z9y/kLo4KZH8SsgM/jSPHwJzxHUk7mPpAAAAAElFTkSuQmCC" alt="" width="14" height="14" />"""
        return f'<span class="chip" style="background:{color}">{image}</span>'

    def _card(self, record: dict[str, Any]) -> str:
        stats = record["stats"]
        esc_name = html_mod.escape(record["name"], quote=True)

        # Overlays
        tl = f'<span class="badge b-tl">LV {stats["level"]}</span>'
        if stats["ue"] > 0:
            # tr = f'<span class="badge b-tr"><span class="ue">UE{stats["ue"]}·{stats["ue_level"]}</span></span>'
            tr = f'<span class="badge b-tr"><span class="ue">{"★" * stats["star"]}·LV {stats["ue_level"]}</span></span>'
        else:
            tr = f'<span class="badge b-tr"><span class="stars">{"★" * stats["star"]}</span></span>'
        skills = "".join(
            format_skill(stats[k]) for k in ("ex", "basic", "passive", "sub")
        )
        bl = f'<span class="badge b-bl">{skills}</span>'
        gear = "/".join(
            sanitize_level(stats[k], GEAR_LEVEL_CAP)
            for k in ("gear1", "gear2", "gear3")
        )
        br = f'<span class="badge b-br">{gear}</span>'

        portrait = f'{record["id"]}.webp'
        img = (
            f'<img src="{self.IMAGE_BASE.rstrip("/")}/{portrait}" alt="{esc_name}">'
            if self.IMAGE_BASE
            else '<div style="width:100%;height:100%;border-radius:8px;background:#2a2f38"></div>'
        )
        school_image = "".join(html_mod.escape(record["school"]).split())
        if record["id"] == "26011":  # Saten Ruiko
            school_image = "ETC"

        school_icon = (
            f'<img src="{self.SCHOOL_IMAGE_BASE.rstrip("/")}/{school_image}.png" '
            f'alt="{html_mod.escape(record["school"], quote=True)}">'
            if self.SCHOOL_IMAGE_BASE and record.get("school")
            else ""
        )

        talents = "/".join(
            sanitize_level(stats[k], TALENT_LEVEL_CAP)
            for k in ("book_hp", "book_atk", "book_heal")
        )
        talents_row = (
            f'<div class="talents">📖 {talents}</div>' if talents != "0/0/0" else ""
        )
        bond_gear_chip = (
            f'<span class="chip" style="background:#ffbed8; color:#3d4f66">Bond Gear T{stats["bond_gear"]}</span>'
            if int(stats["bond_gear"]) > 0
            else ""
        )

        attack_chip = self._chip(record.get("attack", ""), ATTACK_COLORS, "atk")
        armor_chip = self._chip(record.get("armor", ""), ARMOR_COLORS, "armor")

        return f"""<div class="card" title="{html_mod.escape(record["line"])}">
  <div class="thumb">{img}{tl}{tr}{bl}{br}</div>
  <div class="name">{esc_name}</div>
  <div class="sub">{school_icon}<span>{html_mod.escape(record.get("school", "") or "")}</span></div>
  <div class="chips">{attack_chip}{armor_chip}{bond_gear_chip}</div>
  {talents_row}
</div>"""

    def _render(self, records: list[dict[str, Any]], group_aliases: list[str]) -> str:
        parts = ["<main>", f"<h1>{self.TITLE}</h1>"]
        if not group_aliases:
            parts.append('<div class="grid">')
            parts.extend(self._card(r) for r in records)
            parts.append("</div>")
        else:
            open_grid = False
            for kind, payload in walk_hierarchy(records, group_aliases):
                if kind == "headers":
                    if open_grid:
                        parts.append("</div>")
                        open_grid = False
                    for alias, depth, value in payload:
                        icon = (
                            f'<img src="{self.IMAGE_BASE.rstrip("/")}/{html_mod.escape(value)}.png" '
                            f'alt="" style="height:22px;vertical-align:-4px;margin-right:6px">'
                            if alias == "school" and self.IMAGE_BASE
                            else ""
                        )
                        parts.append(
                            f"<h{min(depth + 2, 6)}>{icon}{html_mod.escape(value)}</h{min(depth + 2, 6)}>"
                        )
                else:
                    if not open_grid:
                        parts.append('<div class="grid">')
                        open_grid = True
                    parts.append(self._card(payload))
            if open_grid:
                parts.append("</div>")
        parts.append("</main>")
        return "\n".join(parts)

    def process(
        self, sort_mode: str = "order", group_by: list[str] | None = None
    ) -> Path:
        console.print("[bold yellow]Exporting students to HTML...[/bold yellow]")

        group_aliases = group_by or []
        characters = read_json(self.students_file).get("characters", [])
        by_id, by_name = index_students()

        records: list[dict[str, Any]] = []
        remapped = 0
        for char in characters:
            meta, base_id = match_meta(char, by_id, by_name)
            display_name = meta.get("name") or char.get("name", "")
            char_id = str(base_id) if base_id is not None else str(char.get("id", ""))
            remapped += str(char.get("id")) != char_id

            stats = normalize_stats(char.get("current", {}))
            record: dict[str, Any] = {
                "id": char_id,
                "name": display_name,
                "line": format_student_line(display_name, stats),
                "stats": stats,
                "school": str(meta.get("School", "")),
                "attack": str(meta.get("BulletType", "")),
                "armor": str(meta.get("ArmorType", "")),
                "_order": effective_order(meta),
            }
            for alias in group_aliases:
                record[alias] = str(meta.get(GROUP_FIELDS[alias], "Unknown"))
            records.append(record)

        if remapped:
            console.print(
                f"[yellow]Remapped {remapped} scan(s) to their base-form ids[/yellow]"
            )
        records.sort(key=lambda r: sort_key(r, sort_mode, group_aliases))

        doc = (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f"<title>{self.TITLE}</title>\n<style>{_CSS}</style>\n</head>\n<body>\n"
            + self._render(records, group_aliases)
            + "\n</body>\n</html>"
        )
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text(doc, encoding="utf-8")

        console.print(f"[bold green]✓ Exported {len(records)} entries[/bold green]")
        console.print(f"[dim]{self.output_file}[/dim]")
        return self.output_file


def main():
    parser = argparse.ArgumentParser(
        description="Convert scanner output into HTML format."
    )
    parser.add_argument(
        "-a", "--alphabetical", action="store_true", help="Sort alphabetically"
    )
    parser.add_argument(
        "-g",
        "--group",
        nargs="?",
        const="type,school",
        metavar="FIELDS",
        help=f"Grouping hierarchy, outermost first ({', '.join(GROUP_FIELDS)}). "
        "Flag alone = type,school.",
    )
    parser.add_argument(
        "--image-base",
        default=None,
        help="Base URL for {id}.webp / {School}.png assets. Omit -> grey placeholders.",
    )
    parser.add_argument("-o", "--online", action="store_true")
    args = parser.parse_args()

    if args.online:
        try:
            DataSyncManager().update_from_online()
        except Exception:  # noqa: BLE001, S110
            pass

    exporter = HtmlExporter()
    if args.image_base:
        exporter.IMAGE_BASE = args.image_base
    exporter.process(
        sort_mode="name" if args.alphabetical else "order",
        group_by=parse_group_arg(args.group) if args.group else None,
    )


if __name__ == "__main__":
    main()
