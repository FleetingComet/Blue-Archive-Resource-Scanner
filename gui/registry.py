"""Registry of the runnable exporter/tool modules and their CLI options.

Each :class:`Tool` mirrors the ``argparse`` flags of one module in ``tools/``:
:class:`Option` carries the exact flags, defaults and help strings the module
declares, so the Tools tab can render one page per tool without a per-tool
layout. ``tool.module`` is passed to ``python -m <module>`` unchanged.

Adding an argument to a tool means adding one :class:`Option` here - nothing
else in the GUI needs to change.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.constant import MENU_TAB_KEYWORDS, USER_FACING_SCREENS, Screen
from src.core.paths import Path_Config

# Languages the navigator knows how to read the menu tab in.
LANGUAGES = sorted(MENU_TAB_KEYWORDS)

# Scan targets the user can pick. Screen.STUDENT rides along with Students and
# is never listed (or saved) on its own.
SELECTABLE_SCREENS = [s for s in USER_FACING_SCREENS if s is not Screen.STUDENT]

# Valid grouping dimensions ("pills" for the group (-g) option). Mirrors the
# key set of ``GROUP_FIELDS`` in tools/utils/grouping.py (tools/text.py
# TextProcessor.GROUP_FIELDS is the same set).
GROUP_FIELDS = ("type", "school", "club", "attack", "armor")

# Option kinds the Tools tab knows how to render.
BOOL, CHOICE, TEXT, FILE, GROUP = "bool", "choice", "text", "file", "group"

# Tool page copy for the shared "--online" flag (tools/html.py declares it
# without a help string; every other tool documents it this way).
ONLINE_HELP = "Download the latest community-maintained data before processing."

JSON_FILETYPES = (("JSON files", "*.json"), ("All files", "*.*"))


@dataclass(frozen=True)
class Option:
    """One command-line argument of a tool.

    ``flags`` are passed verbatim (the first is used as the flag when the
    option is enabled). ``help`` is the argument's own help string.
    """

    key: str
    flags: tuple[str, ...]
    label: str
    help: str
    kind: str = BOOL
    default: object = False
    # choice: (shown label, value passed to the tool); a value of None means
    # "do not pass the flag at all".
    choices: tuple[tuple[str, str], ...] = ()
    hint: str = ""  # placeholder / empty-field hint
    file_mode: str = "open"  # file: which tkinter dialog to open

    @property
    def flag(self) -> str:
        return self.flags[0]

    @property
    def declares(self) -> str:
        """``-m, --max-target`` - how the argument is written on the CLI."""
        return ", ".join(self.flags)


# --------------------------------------------------------------------------
# Argument definitions - mirrors each tools/*.py argparse block.
# --------------------------------------------------------------------------

MAX_TARGET_JUSTIN = Option(
    "max-target",
    ("-m", "--max-target"),
    "Max target",
    "Set target stats to MAX for newly added characters.",
)
MAX_TARGET_YUZU = Option(
    "max-target",
    ("-m", "--max-target"),
    "Max target",
    "Set target stats to MAX for every character.",
)
ONLINE = Option("online", ("-o", "--online"), "Online data sync", ONLINE_HELP)
ALPHABETICAL_HTML = Option(
    "alphabetical",
    ("-a", "--alphabetical"),
    "Alphabetical",
    "Sort alphabetically",
)
ALPHABETICAL_TEXT = Option(
    "alphabetical",
    ("-a", "--alphabetical"),
    "Alphabetical",
    "Sort their name into alphabetical",
)
GROUP_HTML = Option(
    "group",
    ("-g", "--group"),
    "Grouping",
    "Grouping hierarchy, outermost first "
    f"({', '.join(GROUP_FIELDS)}). Flag alone = type,school.",
    kind=GROUP,
    hint="Flag alone = type,school.",
)
GROUP_TEXT = Option(
    "group",
    ("-g", "--group"),
    "Grouping",
    "Grouping hierarchy, outermost first. Comma-separated from: "
    f"{', '.join(GROUP_FIELDS)}. Example: -g type,school,club,attack "
    "(flag alone = type,attack).",
    kind=GROUP,
    hint="Flag alone = type,attack.",
)

JUSTIN_FILE = Option(
    "file",
    ("-f", "--file"),
    "Base planner file",
    "Path to an existing Justin Planner export file to merge with. "
    "Leave it empty for default path",
    kind=FILE,
    default=None,
    hint=f"empty = {Path_Config.justin_planner_data.name} in input/",
    file_mode="open",
)

MIDOKUNI_STATE = Option(
    "state",
    ("-s", "--state"),
    "State",
    "Set all characters to the specified state (blue or black).",
    kind=CHOICE,
    default=None,
    choices=(("default (Selected)", None), ("blue", "blue"), ("black", "black")),
)

HTML_IMAGE_BASE = Option(
    "image-base",
    ("--image-base",),
    "Asset base URL",
    "Base URL for {id}.webp / {School}.png assets. " "Omit -> grey placeholders.",
    kind=TEXT,
    default=None,
    hint="empty = built-in schaledb.com URLs",
)

SYNC_NO_RETRIES = Option(
    "no-retries",
    ("--no-retries",),
    "No retries",
    "Disable retries (set retries to 1)",
)


@dataclass(frozen=True)
class Tool:
    """One runnable module from ``tools/``."""

    key: str
    label: str
    module: str
    description: str
    icon: str  # Bootstrap Icons name shown in the tool list
    options: tuple[Option, ...] = ()
    # Files the module reads / writes, resolved through Path_Config. Shown on
    # the page so the data flow between the Data tab and the tools is visible.
    reads: tuple[Path, ...] = ()
    writes: tuple[Path, ...] = ()

    @property
    def group_option(self) -> Option | None:
        return next((o for o in self.options if o.kind == GROUP), None)

    def option(self, key: str) -> Option:
        return next(o for o in self.options if o.key == key)


TOOLS: tuple[Tool, ...] = (
    Tool(
        "justin",
        "Justin Planner",
        "tools.justin_planner",
        "Merge the scan results with an existing Justin Planner export.",
        "calendar2-check",
        options=(MAX_TARGET_JUSTIN, JUSTIN_FILE, ONLINE),
        reads=(
            Path_Config.final_equipment,
            Path_Config.final_items,
            Path_Config.final_students,
            Path_Config.justin_planner_data,
        ),
        writes=(Path_Config.justin_planner_merged_output,),
    ),
    Tool(
        "midokuni",
        "Midokuni Roster",
        "tools.midokuni",
        "Build a Midokuni roster URL from the scanned students.",
        "people-fill",
        options=(MIDOKUNI_STATE, ONLINE),
        reads=(Path_Config.final_students,),
        writes=(Path_Config.OUTPUT_DIR / "midokuni_roster.json",),
    ),
    Tool(
        "schaledb",
        "Schale DB",
        "tools.schaledb",
        "Build a Schale DB import file from the scanned students.",
        "database-fill",
        options=(
            Option(
                "lock",
                ("-l", "--lock"),
                "Lock",
                "Set the 'lock' field to true for all characters.",
            ),
            ONLINE,
        ),
        reads=(Path_Config.final_students,),
        writes=(Path_Config.OUTPUT_DIR / "SchaleDB_import.txt",),
    ),
    Tool(
        "html",
        "HTML Report",
        "tools.html",
        "Render the final values as a browsable HTML report.",
        "filetype-html",
        options=(ALPHABETICAL_HTML, GROUP_HTML, HTML_IMAGE_BASE, ONLINE),
        reads=(Path_Config.final_students,),
        writes=(Path_Config.OUTPUT_DIR / "students.html",),
    ),
    Tool(
        "text",
        "Text Dump",
        "tools.text",
        "Write the final values as a plain-text listing.",
        "file-earmark-text",
        options=(ALPHABETICAL_TEXT, GROUP_TEXT, ONLINE),
        reads=(Path_Config.final_students,),
        writes=(Path_Config.OUTPUT_DIR / "students.txt",),
    ),
    Tool(
        "yuzu",
        "Yuzu Trends",
        "tools.yuzu_trends",
        "Convert the scan results into the YuzuTrends planner format.",
        "graph-up-arrow",
        options=(MAX_TARGET_YUZU, ONLINE),
        reads=(
            Path_Config.final_equipment,
            Path_Config.final_items,
            Path_Config.final_students,
        ),
        writes=(Path_Config.OUTPUT_DIR / "yuzu_trends_planner.json",),
    ),
    Tool(
        "sync",
        "Sync Data",
        "tools.sync_data",
        "Re-download assets/data/*_processed.json from the online dataset.",
        "cloud-arrow-down-fill",
        options=(SYNC_NO_RETRIES,),
        writes=(
            Path_Config.equipment_processed,
            Path_Config.items_processed,
            Path_Config.students_processed,
        ),
    ),
)

TOOLS_BY_KEY = {tool.key: tool for tool in TOOLS}
