"""Data tab: inspect and correct the JSON the scanner produced.

The tab owns one *active file* - by default the most recent scanner output -
and edits it in place. Every value is written back through the same JSON shape
``src.utils.data.processors`` produce, so the exporters keep working unchanged.
Raw scan files can be re-processed (``gui.scanner_files.reprocess``) to rebuild
their final values, and the raw JSON of any file stays editable.

Nothing here writes a new file format: the structure is discovered from the
loaded document and from :mod:`gui.scanner_files`.
"""

from __future__ import annotations

import json
import threading
import time
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog

import ttkbootstrap as ttk
from ttkbootstrap.widgets.scrolled import ScrolledFrame, ScrolledText

from gui import folders, gamedata, scanner_files
from gui.components.card import CardSpec
from gui.components.card_grid import CardGrid
from gui.components.catalog_card import currency_spec, equipment_spec, item_spec
from gui.components.filter_bar import FilterBar
from gui.components.image_view import ImageView
from gui.components.student_card import StudentCard
from gui.metadata import relative
from gui.registry import JSON_FILETYPES
from gui.scanner_files import ScanFile
from gui.services import catalog
from gui.services.image_service import ImageService
from gui.services.student_sort import (
    SORT_FIELDS,
    SortEntry,
    StudentFilterState,
    filter_student_entries,
    sort_student_entries,
)
from gui.ui import (
    MONO_FONT,
    MUTED,
    ask_save_discard_cancel,
    button,
    center_on_parent,
    confirm,
    heading,
    local_hotkey,
    show_error,
)
from src.core.config import AppSettings, Config
from src.core.paths import Path_Config
from src.utils.data.io import write_json
from src.utils.data.stat_normalization import (
    GEAR_LEVEL_CAP,
    TALENT_LEVEL_CAP,
    normalize_stats,
)

# How many nodes a read-only document counts (the Raw JSON tab edits it).
GENERIC_NODE_LIMIT = 2000

# The right-hand notebook's pages (kept as indices: they are used to decide
# whether the Raw JSON text needs refreshing).
_TAB_CARDS, _TAB_RAW = 0, 1

# The editor keeps a fixed request width, so a different form (a student's
# fields vs. a currency's one line) cannot move the split sash.
EDITOR_WIDTH = 380
PREVIEW_SIZE = 84


@dataclass(frozen=True)
class Field:
    """One editable numeric-or-text value inside a record."""

    key: str
    label: str
    store: str = "str"  # how the value is written back: "str" | "int"
    minimum: int = 0
    maximum: int | None = None
    help: str = ""


# Scanner final values keep stats as strings (except star/ue); raw scans keep
# ints. Both forms are accepted by normalize_stats, so each file keeps its own
# shape instead of being rewritten in a different one.
FINAL_STUDENT_FIELDS: tuple[Field, ...] = (
    Field("level", "Level", "str", 1, 90),
    Field("star", "Star", "int", 1, 5),
    Field("ue", "UE", "int", 0, 4),
    Field("ue_level", "UE level", "str", 0, 60),
    Field("bond", "Bond", "str", 0, 100),
    Field("ex", "EX skill", "str", 0, 10),
    Field("basic", "Basic skill", "str", 0, 10),
    Field("passive", "Passive skill", "str", 0, 10),
    Field("sub", "Sub skill", "str", 0, 10),
    Field("gear1", "Gear 1", "str", 0, GEAR_LEVEL_CAP),
    Field("gear2", "Gear 2", "str", 0, GEAR_LEVEL_CAP),
    Field("gear3", "Gear 3", "str", 0, GEAR_LEVEL_CAP),
    Field("bond_gear", "Bond gear", "str", 0, 2),
    Field("book_hp", "Talent HP", "str", 0, TALENT_LEVEL_CAP),
    Field("book_atk", "Talent ATK", "str", 0, TALENT_LEVEL_CAP),
    Field("book_heal", "Talent HEAL", "str", 0, TALENT_LEVEL_CAP),
)

RAW_STUDENT_FIELDS: tuple[Field, ...] = (
    Field("level", "Level", "int", 1, 90),
    Field("star", "Star", "int", 1, 5),
    Field("ue", "UE", "int", 0, 4),
    Field("ue_level", "UE level", "int", 0, 60),
    Field("bond", "Bond", "int", 0, 100),
    Field("ex", "EX skill", "int", 0, 10),
    Field("basic", "Basic skill", "int", 0, 10),
    Field("passive", "Passive skill", "int", 0, 10),
    Field("sub", "Sub skill", "int", 0, 10),
    Field("gear1", "Gear 1", "int", 0, GEAR_LEVEL_CAP),
    Field("gear2", "Gear 2", "int", 0, GEAR_LEVEL_CAP),
    Field("gear3", "Gear 3", "int", 0, GEAR_LEVEL_CAP),
    Field("gear_bond", "Bond gear", "int", 0, 2),
    Field("talent_hp", "Talent HP", "int", 0, TALENT_LEVEL_CAP),
    Field("talent_atk", "Talent ATK", "int", 0, TALENT_LEVEL_CAP),
    Field("talent_healing", "Talent HEAL", "int", 0, TALENT_LEVEL_CAP),
)

STUDENT_KINDS = (scanner_files.STUDENTS_FINAL, scanner_files.STUDENTS_RAW)


def student_fields(kind: str) -> tuple[Field, ...]:
    return (
        FINAL_STUDENT_FIELDS
        if kind == scanner_files.STUDENTS_FINAL
        else RAW_STUDENT_FIELDS
    )


def _stat(record: dict, key: str) -> object:
    current = record.get("current")
    if isinstance(current, dict) and key in current:
        return current[key]
    return ""


def _elide_middle(text: str, limit: int = 110) -> str:
    """Shorten a long path in the middle, so both its ends stay readable."""
    if len(text) <= limit:
        return text
    keep = (limit - 1) // 2
    return f"{text[:keep]}…{text[-keep:]}"


class DataPage(ttk.Frame):
    """Load, inspect, correct and save the scanner's JSON output."""

    # Page indices of the right-hand notebook (also used by the tests).
    TAB_CARDS, TAB_RAW = _TAB_CARDS, _TAB_RAW

    def __init__(
        self,
        master,
        *,
        on_post: Callable[[Callable[[], None]], None],
        on_log: Callable[[str, str], None],
        on_dirty_changed: Callable[[bool], None] | None = None,
        on_file_changed: Callable[[], None] | None = None,
    ):
        super().__init__(master)
        self._on_post = on_post
        self._on_log = on_log
        self._on_dirty_changed = on_dirty_changed
        self._on_file_changed = on_file_changed

        self.doc: object = None
        self.path: Path | None = None
        self.spec: ScanFile | None = None
        self.kind: str = scanner_files.GENERIC
        self.dirty = False
        self._loaded_mtime: float | None = None
        self._loading = False
        self._load_token = 0
        self._payloads: dict[str, object] = {}
        self._field_vars: dict[str, tk.Variable] = {}
        self._name_var: tk.StringVar | None = None
        self._id_var: tk.StringVar | None = None
        self._import_summary = ""
        self._card_specs: list[CardSpec] = []
        self._entries: list = []
        self._groups: tuple = ()
        self._noun = "entries"
        self._selected_iid: str | None = None
        self._selected_payload: object | None = None
        self._cards_filter_job: str | None = None
        self._images = ImageService(on_post)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._build_header()
        self._build_toolbar()
        self._build_body()
        # The saved mode is applied before the first load, so no request is
        # ever made for an image the user has switched off.
        self.apply_image_settings(Config.settings, initial=True)

    def destroy(self) -> None:
        job = getattr(self, "_cards_filter_job", None)
        if job is not None:
            try:
                self.after_cancel(job)
            except (tk.TclError, ValueError):
                pass
        self._images.close()
        super().destroy()

    # ------------------------------------------------------------------
    # Chrome
    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        header = ttk.Frame(self, padding=(18, 14, 18, 4))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Data", font=heading()).pack(anchor="w")
        ttk.Label(
            header,
            text="Review and correct the JSON the scanner wrote. Saving here updates the files "
            "the HTML, Text, Justin Planner and other tools read.",
            style=MUTED,
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, padding=(18, 8, 18, 0))
        bar.grid(row=1, column=0, sticky="ew")
        # A spacer column keeps the action buttons at the right edge without
        # letting a long file name (or a disabled button) move them.
        bar.columnconfigure(1, weight=1)
        ttk.Label(bar, text="File").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self._file_choice = tk.StringVar()
        self._file_combo = ttk.Combobox(
            bar, textvariable=self._file_choice, state="readonly", width=34
        )
        self._file_combo.grid(row=0, column=1, sticky="w")
        self._file_combo.bind("<<ComboboxSelected>>", self._on_file_picked)

        actions = ttk.Frame(bar)
        actions.grid(row=0, column=2, sticky="e")

        self._save_button = button(
            actions, "Save", "floppy-fill", style="success", command=self.save,
            tip="Write the corrected data back to this file (Ctrl+S)",
        )  # fmt: skip
        self._save_button.pack(side="right")
        self._save_as_button = button(
            actions, "Save As…", "floppy", command=self.save_as, tip="Write the data to another JSON file"
        )  # fmt: skip
        self._save_as_button.pack(side="right", padx=(0, 6))
        self._reload_button = button(
            actions, "Reload", "arrow-clockwise", command=self.reload, tip="Re-read the file, discarding unsaved edits"
        )  # fmt: skip
        self._reload_button.pack(side="left")
        button(
            actions,
            "Browse…",
            "folder2-open",
            command=self.browse,
            tip="Open any JSON file",
        ).pack(side="left", padx=(6, 0))
        self._add_button = button(
            actions, "Add", "plus-lg", command=self.add_entry,
            tip="Add a new entry to the loaded data",
        )  # fmt: skip
        self._add_button.pack(side="left", padx=(6, 0))
        self._reprocess_button = button(
            actions, "Re-run processor", "arrow-repeat", command=self.reprocess,
            tip="Rebuild the final values from this raw scan file",
        )  # fmt: skip
        self._reprocess_button.pack(side="left", padx=(6, 0))
        button(actions, "Open location", "folder2-open", command=self.reveal_active, tip="Show this file in the file manager").pack(
            side="left", padx=(6, 0)
        )  # fmt: skip

        info = ttk.Frame(self, padding=(18, 6, 18, 4))
        info.grid(row=2, column=0, sticky="ew")
        info.columnconfigure(0, weight=1)
        # One elided line: an unusually long path can never wrap the row and
        # push the editor down.
        self._info = ttk.Label(info, style=MUTED, anchor="w")
        self._info.grid(row=0, column=0, sticky="ew")
        self._dirty_label = ttk.Label(info, bootstyle="warning")
        self._dirty_label.grid(row=0, column=1, sticky="e", padx=(12, 0))

    def _build_body(self) -> None:
        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 10))
        self._panes = panes

        # Left pane: the preview and the editor for the selected row. A fixed
        # request width keeps the split where it is when another record (with a
        # wider form) is selected.
        edit_host = ttk.Frame(panes, width=EDITOR_WIDTH)
        edit_host.columnconfigure(0, weight=1)
        edit_host.rowconfigure(1, weight=1)
        edit_host.grid_propagate(False)
        self._editor_host = edit_host

        preview = ttk.Frame(edit_host, padding=(12, 10, 12, 4))
        preview.grid(row=0, column=0, sticky="ew")
        self._preview = ImageView(preview, images=self._images, size=PREVIEW_SIZE)
        self._preview.pack(side="left")
        preview_text = ttk.Frame(
            preview, height=PREVIEW_SIZE, width=EDITOR_WIDTH - PREVIEW_SIZE - 30
        )
        # The caption box is fixed too: a long generic path can be clipped but
        # can never wrap the row taller and push the editor down.
        preview_text.pack_propagate(False)
        preview_text.pack(side="left", fill="x", expand=True, padx=(12, 0))
        self._preview_title = ttk.Label(
            preview_text, text="Nothing selected", font=heading(11)
        )
        self._preview_title.pack(anchor="w")
        self._preview_subtitle = ttk.Label(
            preview_text,
            style=MUTED,
            wraplength=EDITOR_WIDTH - PREVIEW_SIZE - 50,
            justify="left",
        )
        self._preview_subtitle.pack(anchor="w", pady=(2, 0))

        self._editor = ScrolledFrame(edit_host, auto_hide=False, padding=(12, 10))
        self._editor.grid(row=1, column=0, sticky="nsew")
        panes.add(edit_host, weight=2)

        # Right pane: the card grid and the raw JSON, as tabs.
        right = ttk.Frame(panes)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        self._view_tabs = ttk.Notebook(right)
        self._view_tabs.grid(row=0, column=0, sticky="nsew")

        self._cards_host = self._build_cards_tab(self._view_tabs)
        self._view_tabs.add(self._cards_host, text=" Cards ")

        raw_host = ttk.Frame(self._view_tabs)
        raw_host.columnconfigure(0, weight=1)
        raw_host.rowconfigure(1, weight=1)
        raw_bar = ttk.Frame(raw_host, padding=(4, 6))
        raw_bar.grid(row=0, column=0, sticky="ew")
        button(
            raw_bar,
            "Apply JSON",
            "check-lg",
            style="success",
            command=self._apply_raw,
            tip="Replace the data with the edited JSON",
        ).pack(side="left")
        button(
            raw_bar,
            "Refresh",
            "arrow-clockwise",
            command=self._refresh_raw,
            tip="Re-read the JSON from the current data",
        ).pack(side="left", padx=6)
        ttk.Label(
            raw_bar,
            text="Edits apply to the in-memory data until you Save.",
            style=MUTED,
        ).pack(side="left", padx=10)
        self._raw = ScrolledText(
            raw_host, auto_hide=True, hbar=True, padding=0, height=10
        )
        self._raw.grid(row=1, column=0, sticky="nsew")
        self._raw.text.configure(wrap="none", font=MONO_FONT, undo=True)
        self._view_tabs.add(raw_host, text=" Raw JSON ")
        self._view_tabs.bind("<<NotebookTabChanged>>", self._on_view_changed)
        panes.add(right, weight=3)

        self._show_editor_placeholder()

    def _build_cards_tab(self, master) -> ttk.Frame:
        host = ttk.Frame(master)
        host.columnconfigure(0, weight=1)
        host.rowconfigure(2, weight=1)

        # Row 0: search on the left, ordering/display controls on the right.
        toolbar = ttk.Frame(host, padding=(6, 8, 6, 2))
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(0, weight=1)

        search = ttk.Frame(toolbar)
        search.grid(row=0, column=0, sticky="w")
        ttk.Label(search, text="Search", style=MUTED).pack(side="left", padx=(0, 6))
        self._cards_search = tk.StringVar()
        self._search_entry = ttk.Entry(
            search, textvariable=self._cards_search, width=22
        )
        self._search_entry.pack(side="left")
        self._search_entry.bind("<KeyRelease>", self._on_search_key)
        self._search_entry.bind("<Return>", lambda _e: self._on_cards_filter_changed())
        self._search_entry.bind("<Escape>", lambda _e: self._clear_search())
        self._search_clear = button(
            search,
            icon="x-circle",
            style="secondary-outline",
            command=self._clear_search,
            tip="Clear the search",
            padding=(3, 0),
        )

        controls = ttk.Frame(toolbar)
        controls.grid(row=0, column=1, sticky="e")

        self._cards_hide_empty = tk.BooleanVar(value=True)
        self._hide_empty_check = ttk.Checkbutton(
            controls,
            text="Hide empty",
            variable=self._cards_hide_empty,
            command=self._on_cards_filter_changed,
        )

        self._sort_label = ttk.Label(controls, text="Sort", style=MUTED)
        self._cards_sort = tk.StringVar(value=SORT_FIELDS[0][1])
        self._sort_combo = ttk.Combobox(
            controls,
            textvariable=self._cards_sort,
            state="readonly",
            width=16,
        )
        self._sort_combo.bind(
            "<<ComboboxSelected>>", lambda _e: self._on_cards_filter_changed()
        )
        self._sort_descending = False
        self._sort_dir_btn = button(
            controls,
            icon="sort-up",
            style="secondary-outline",
            command=self._toggle_sort_direction,
            padding=(3, 0),
        )
        self._sort_tip = ttk.ToolTip(
            self._sort_dir_btn, text="Ascending (click to sort Descending)"
        )
        for widget in (
            self._hide_empty_check,
            self._sort_label,
            self._sort_combo,
            self._sort_dir_btn,
        ):
            widget.grid_remove()  # _update_view_controls decides what fits

        # Row 1: the filters that match this document (hidden for generic files).
        self._filters = FilterBar(
            host,
            images=self._images,
            on_change=self._on_cards_filter_changed,
            on_clear=self._clear_filters,
        )
        self._filters.grid(row=1, column=0, sticky="ew", padx=6, pady=(2, 4))

        # Row 2: the scrolling cards.
        self._cards = CardGrid(
            host,
            images=self._images,
            on_select=self._select_card,
            on_view_changed=self._retain_images,
        )
        self._cards.grid(row=2, column=0, sticky="nsew")
        self._cards_filter_job: str | None = None
        self._sync_search_clear()
        return host

    def _card_kind(self) -> str:
        """The catalog shape behind the loaded file (``student``, ``items``…)."""
        return {
            scanner_files.STUDENTS_FINAL: "student",
            scanner_files.STUDENTS_RAW: "student",
            scanner_files.EQUIPMENT_FINAL: "equipment",
            scanner_files.ITEMS_FINAL: "items",
            scanner_files.COUNTS_RAW: "items",
            scanner_files.CURRENCIES_RAW: "currencies",
        }.get(self.kind, "generic")

    def _sort_fields(self) -> tuple[tuple[str, str], ...]:
        if self.kind in STUDENT_KINDS:
            return SORT_FIELDS
        return catalog.sort_fields(self._card_kind())

    def _update_view_controls(self) -> None:
        """Show only the controls that make sense for the loaded shape."""
        kind = self._card_kind()
        self._sort_combo.configure(
            values=[label for _key, label in self._sort_fields()]
        )
        if self._cards_sort.get() not in self._sort_combo.cget("values"):
            self._cards_sort.set(self._sort_combo.cget("values")[0])

        if kind != "generic":
            self._sort_label.grid(row=0, column=1, padx=(0, 6))
            self._sort_combo.grid(row=0, column=2)
            self._sort_dir_btn.grid(row=0, column=3, padx=(4, 0))
        else:
            self._sort_label.grid_remove()
            self._sort_combo.grid_remove()
            self._sort_dir_btn.grid_remove()

        if kind in ("equipment", "items"):
            self._hide_empty_check.grid(row=0, column=0, padx=(0, 14))
        else:
            self._hide_empty_check.grid_remove()

        self._search_entry.configure(
            state="normal" if kind != "generic" else "disabled"
        )
        if kind == "generic":
            self._filters.grid_remove()
        else:
            self._filters.grid()

    def _toggle_sort_direction(self) -> None:
        self._sort_descending = not self._sort_descending
        icon = "sort-down" if self._sort_descending else "sort-up"
        tip = (
            "Descending (click to sort Ascending)"
            if self._sort_descending
            else "Ascending (click to sort Descending)"
        )
        self._sort_dir_btn.configure(icon=icon)
        self._sort_tip.text = tip
        self._on_cards_filter_changed()

    def _current_sort_key(self) -> str:
        key = self._current_sort_key_for(self._cards_sort.get())
        return key

    def _current_sort_key_for(self, label: str) -> str:
        return {label_: key_ for key_, label_ in self._sort_fields()}.get(
            label, "default"
        )

    def _clear_filters(self) -> None:
        """Clear the search and every filter; Hide empty and the sort are kept."""
        self._cancel_filter_job()
        self._cards_search.set("")
        self._sync_search_clear()
        self._filters.clear()
        self._apply_view(reset=True)
        self._scroll_cards_to_top()

    def _clear_search(self) -> None:
        self._cards_search.set("")
        self._sync_search_clear()
        self._on_cards_filter_changed()

    def _sync_search_clear(self) -> None:
        if self._cards_search.get().strip():
            self._search_clear.pack(side="left", padx=(4, 0))
        else:
            self._search_clear.pack_forget()

    def _on_search_key(self, _event=None) -> None:
        self._sync_search_clear()
        self._schedule_cards_filter()

    def _on_cards_filter_changed(self) -> None:
        """Re-filter immediately (filters, sort, hide-empty, search Enter)."""
        self._cancel_filter_job()
        if self.doc is None:
            return
        self._apply_view(reset=True)
        self._scroll_cards_to_top()

    def _cancel_filter_job(self) -> None:
        if self._cards_filter_job is None:
            return
        try:
            self.after_cancel(self._cards_filter_job)
        except (tk.TclError, ValueError):
            pass
        self._cards_filter_job = None

    def _schedule_cards_filter(self) -> None:
        """Debounce typing in the search box (150 ms)."""
        self._cancel_filter_job()
        self._cards_filter_job = self.after(150, self._on_cards_filter_changed)

    def _load_entries(self) -> None:
        """Build the rows for the current document and its filter groups."""
        self._entries: list = []
        self._groups: tuple = ()
        self._noun = "entries"
        kind = self._card_kind()
        if self.doc is None or kind == "generic":
            self._filters.set_groups((), role=False)
            return

        if kind == "student":
            characters = (
                self.doc.get("characters", []) if isinstance(self.doc, dict) else []
            )
            entries: list[SortEntry] = []
            for index, record in enumerate(characters):
                if not isinstance(record, dict):
                    continue
                info = (
                    gamedata.student(record.get("id"))
                    or gamedata.student_by_name(record.get("name"))
                    or {}
                )
                entries.append((f"s{index}", record, info, index))
            self._entries = entries
            self._groups = catalog.student_groups(entries)
            self._noun = "students"
            self._filters.set_groups(self._groups, role=True, bond_gear=True)
        elif kind == "equipment":
            self._entries = catalog.equipment_entries(self.doc)
            self._groups = catalog.equipment_groups(self._entries)
            self._filters.set_groups(self._groups)
        elif kind == "items":
            self._entries = catalog.item_entries(
                self.doc, known=self.kind == scanner_files.ITEMS_FINAL
            )
            self._groups = catalog.item_groups(self._entries)
            self._noun = "items"
            self._filters.set_groups(self._groups)
        else:  # currencies
            self._entries = catalog.currency_entries(self.doc)
            self._noun = "currencies"
            self._filters.set_groups((), role=False)

    def _apply_view(self, *, reset: bool = True) -> None:
        """Filter, sort and hand the resulting cards to the grid."""
        kind = self._card_kind()
        query = self._cards_search.get()
        selected = self._filters.selection()
        # Hide empty only exists for equipment/items; a stale value left over
        # from another file must not enable Clear filters (or hide students).
        hide_empty = (
            self._cards_hide_empty.get() if kind in ("equipment", "items") else False
        )
        visible: list = []
        specs: list[CardSpec] = []

        if kind == "student":
            state = StudentFilterState(
                schools=selected.get("school", set()),
                clubs=selected.get("club", set()),
                role=self._filters.role(),
                attack_types=selected.get("attack", set()),
                armor_types=selected.get("armor", set()),
                has_bond_gear=self._filters.bond_gear(),
                search=query,
            )
            visible = filter_student_entries(self._entries, state)
            visible = sort_student_entries(
                visible,
                field=self._current_sort_key(),
                descending=self._sort_descending,
            )
            specs = [
                StudentCard.spec_for(record, iid, info)
                for iid, record, info, _index in visible
            ]
        elif kind == "equipment":
            visible = catalog.filter_equipment(
                self._entries, selected, query, hide_empty=hide_empty
            )
            visible = catalog.sort_entries(
                visible, self._current_sort_key(), self._sort_descending
            )
            specs = [equipment_spec(entry) for entry in visible]
        elif kind == "items":
            visible = catalog.filter_items(
                self._entries, selected, query, hide_empty=hide_empty
            )
            visible = catalog.sort_entries(
                visible, self._current_sort_key(), self._sort_descending
            )
            known = self.kind == scanner_files.ITEMS_FINAL
            specs = [item_spec(entry, known=known) for entry in visible]
        elif kind == "currencies":
            visible = catalog.filter_currencies(self._entries, query)
            visible = catalog.sort_entries(
                visible, self._current_sort_key(), self._sort_descending
            )
            specs = [currency_spec(entry) for entry in visible]

        self._card_specs = specs
        keys = {spec.key for spec in specs}
        if self._selected_iid is not None and self._selected_iid not in keys:
            # The selected row is filtered out: drop it rather than leaving an
            # editor for a card the grid no longer shows.
            self._selected_iid = None
            self._selected_payload = None
            self._clear_editor()
            self._show_editor_placeholder()
            self._update_preview(None)
        if kind != "generic":
            # Hide empty is a view option, not a filter: leave Clear filters to
            # the search/role/dropdowns (the empty state has its own reset that
            # also turns it off).
            self._filters.set_count(
                len(visible),
                len(self._entries),
                self._noun,
                extra_active=bool(query.strip()),
            )
        self._render_cards(reset=reset)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load_initial(self, preferred: Path | None = None) -> None:
        """Open ``preferred`` (or the most recent scanner output) at startup."""
        if preferred is not None and Path(preferred).is_file():
            self.load_path(preferred)
            return
        spec = scanner_files.newest_file()
        if spec is None:
            self._empty_state("No scanner output found yet. Run a scan or use Browse….")
            return
        self.load_path(spec.path)

    def load_path(self, path: Path, *, select_first: bool = True) -> None:
        """Read ``path`` off the UI thread and show it."""
        self._loading = True
        self._load_token += 1
        self._set_info(f"Loading {relative(path)}…")
        thread = threading.Thread(
            target=self._read_worker,
            args=(Path(path), select_first, self._load_token),
            daemon=True,
        )
        thread.start()

    def _read_worker(self, path: Path, select_first: bool, token: int) -> None:
        result: dict = {"path": path, "select_first": select_first, "token": token}
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            result["error"] = f"{relative(path)} does not exist yet."
        except OSError as exc:
            result["error"] = f"Could not read {relative(path)}: {exc}"
        else:
            try:
                result["doc"] = json.loads(text)
                result["mtime"] = path.stat().st_mtime
            except (ValueError, OSError) as exc:
                result["error"] = f"{relative(path)} is not valid JSON: {exc}"
        self._on_post(lambda: self._finish_load(result))

    def _finish_load(self, result: dict) -> None:
        if result.get("token") != self._load_token:
            return  # a newer load started while this one was reading
        if not self.winfo_exists():  # the page closed while the file was read
            return
        self._loading = False
        path: Path = result["path"]
        if error := result.get("error"):
            self.doc = None
            self.path = path
            self.spec = scanner_files.identify(path)
            self.kind = self.spec.kind if self.spec else scanner_files.GENERIC
            self._loaded_mtime = None
            self._reset_view_state()
            self._render()
            self.after_idle(self._scroll_cards_to_top)
            self._set_info(error)
            self._on_log(f"Data tab: {error}", "warn")
            return

        self.doc = result["doc"]
        self.path = path
        self.spec = scanner_files.identify(path)
        # A file loaded with Browse… keeps the shape of what it was saved from,
        # so Save As… on a scanner file stays editable.
        if self.spec is not None:
            self.kind = self.spec.kind
        elif self.kind not in (
            scanner_files.STUDENTS_FINAL, scanner_files.STUDENTS_RAW,
            scanner_files.EQUIPMENT_FINAL, scanner_files.ITEMS_FINAL,
            scanner_files.COUNTS_RAW, scanner_files.CURRENCIES_RAW,
        ):  # fmt: skip
            self.kind = scanner_files.GENERIC
        self._loaded_mtime = result.get("mtime")
        self._set_dirty(False)
        self._reset_view_state()
        self._render()
        # Select the first *visible* card, not the first document row: the
        # default order can put the last record first, and revealing it would
        # draw every batch before the window is even shown.
        if result.get("select_first") and self._card_specs:
            iid = self._card_specs[0].key
            payload = self._payloads.get(iid)
            if payload is not None and self._select_payload(payload) is not None:
                self._cards.select(iid)
        self.after_idle(self._scroll_cards_to_top)
        self._on_log(f"Data tab: loaded {relative(path)}", "dim")

    def open_path(self, path: Path) -> bool:
        """Load ``path`` for editing, guarding unsaved edits. True if it will load."""
        if not self._may_replace(f"opening {relative(path)}"):
            return False
        self.load_path(path)
        return True

    def browse(self) -> None:
        if not self._may_replace("opening another file"):
            return
        chosen = filedialog.askopenfilename(
            parent=self,
            title="Open a JSON file",
            initialdir=str(self.path.parent if self.path else Path_Config.OUTPUT_DIR),
            filetypes=list(JSON_FILETYPES),
        )
        if chosen:
            self.load_path(Path(chosen))

    def _on_file_picked(self, _event=None) -> None:
        spec = next(
            (s for s in scanner_files.SCAN_FILES if s.label == self._file_choice.get()),
            None,
        )
        if spec is None or spec.path == self.path:
            return
        if not self._may_replace(f"opening {spec.label}"):
            self._sync_file_choice()
            return
        self.load_path(spec.path)

    def _may_replace(self, action: str) -> bool:
        """Guard unsaved edits before ``action``; True when it may proceed."""
        if not self.dirty:
            return True
        answer = ask_save_discard_cancel(
            self,
            "Unsaved data changes",
            f"{self.path.name if self.path else 'The loaded data'} has unsaved edits. "
            f"Save them before {action}?",
            save="Save",
            discard="Discard edits",
        )
        if answer == "save":
            return self.save()
        return answer == "discard"

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _empty_state(self, message: str) -> None:
        self.doc = None
        self._reset_view_state()
        self._render()
        self._set_info(message)

    def _reset_view_state(self) -> None:
        """Start a newly loaded file with every filter cleared."""
        self._cancel_filter_job()
        self._filters.close_popups()
        self._cards_search.set("")
        self._sync_search_clear()
        self._cards_hide_empty.set(True)
        self._filters.clear()

    def _render(self, select: object | None = None) -> None:
        self._payloads.clear()
        self._selected_iid = None
        self._selected_payload = None
        self._clear_editor()
        self._import_summary = ""

        self._update_view_controls()
        self._load_entries()

        if self.doc is None:
            if self.path is not None and not self._info.cget("text"):
                self._set_info(f"{relative(self.path)} is not loaded.")
            self._apply_view()
            self._sync_file_choice()
            self._sync_buttons()
            self._notify_file_changed()
            self._show_editor_placeholder()
            self._update_preview(None)
            return

        renderers = {
            scanner_files.STUDENTS_FINAL: self._render_students,
            scanner_files.STUDENTS_RAW: self._render_students,
            scanner_files.EQUIPMENT_FINAL: self._render_equipment,
            scanner_files.ITEMS_FINAL: self._render_items,
            scanner_files.COUNTS_RAW: self._render_items,
            scanner_files.CURRENCIES_RAW: self._render_currencies,
            scanner_files.GENERIC: self._render_generic,
        }
        renderers.get(self.kind, self._render_generic)()
        # An edit keeps the card batch the user was on; loading another file
        # starts again at the first batch.
        self._apply_view(reset=select is None)
        self._update_info()
        self._sync_file_choice()
        self._sync_buttons()
        self._notify_file_changed()
        if self._view_tabs.index("current") == _TAB_RAW:
            self._refresh_raw()
        iid = self._select_payload(select) if select is not None else None
        if iid is None:
            self._show_editor_placeholder()
            self._update_preview(None)
        else:
            self._cards.reveal(iid)
            self._cards.select(iid)
        self._retain_images()

    def _render_students(self) -> None:
        characters = (
            self.doc.get("characters", []) if isinstance(self.doc, dict) else []
        )
        self._import_summary = f"{len(characters)} students"
        for index, record in enumerate(characters):
            if not isinstance(record, dict):
                continue
            self._payloads[f"s{index}"] = ("student", index)

    def _render_equipment(self) -> None:
        grouped = self.doc if isinstance(self.doc, dict) else {}
        total = 0
        for category, tiers in grouped.items():
            if not isinstance(tiers, dict):
                continue
            for tier, value in tiers.items():
                self._payloads[f"e{category}|{tier}"] = (
                    "equipment",
                    str(category),
                    str(tier),
                )
                if isinstance(value, int):
                    total += value
        self._import_summary = f"{len(grouped)} categories · {total} units"

    def _render_items(self) -> None:
        entries = self.doc if isinstance(self.doc, dict) else {}
        total = 0
        for index, (key, value) in enumerate(entries.items()):
            self._payloads[f"i{index}"] = ("entry", str(key))
            if isinstance(value, int):
                total += value
        self._import_summary = f"{len(entries)} entries · {total} units"

    def _render_currencies(self) -> None:
        entries = self.doc if isinstance(self.doc, dict) else {}
        for key in entries:
            self._payloads[f"cur{key}"] = ("currency", str(key))
        self._import_summary = f"{len(entries)} currencies"

    def _render_generic(self) -> None:
        """Count the nodes of an unknown document (the Raw JSON tab edits it)."""
        nodes = 0

        def walk(value: object) -> None:
            nonlocal nodes
            if nodes >= GENERIC_NODE_LIMIT:
                return
            nodes += 1
            if isinstance(value, dict):
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(self.doc)
        self._import_summary = (
            f"read-only preview ({nodes} nodes)"
            if nodes < GENERIC_NODE_LIMIT
            else f"read-only preview (first {GENERIC_NODE_LIMIT} nodes)"
        )

    def _select_payload(self, payload: object) -> str | None:
        for iid, stored in self._payloads.items():
            if stored == payload:
                self._selected_iid = iid
                # Build the editor now so it stays in step with the re-render
                # instead of flashing the placeholder first.
                self._on_select()
                return iid
        return None

    def _on_view_changed(self, _event=None) -> None:
        # An overrideredirect popup is not a child of the notebook, so it would
        # stay on top of the Raw JSON tab unless it is closed here.
        self._filters.close_popups()
        index = self._view_tabs.index("current")
        if index == _TAB_RAW:
            self._refresh_raw()
        elif index == _TAB_CARDS:
            self._cards.refresh()

    # ------------------------------------------------------------------
    # Cards
    # ------------------------------------------------------------------
    def _render_cards(self, *, reset: bool = True) -> None:
        """Push the current specs into the grid; it updates cards in place."""
        self._cards.set_empty_message(
            self._cards_empty_message(),
            reset=self._reset_empty_state if self._entries else None,
        )
        self._cards.set_specs(self._card_specs, reset=reset)
        self._cards.select(self._selected_iid)

    def _cards_empty_message(self) -> str:
        if self.doc is None:
            return "Nothing loaded yet."
        if self.kind == scanner_files.GENERIC:
            return (
                "Cards are available for students, items, equipment and currencies. "
                "This file is edited in the Raw JSON tab."
            )
        if not self._entries:
            return f"This file has no {self._noun}."
        return f"No {self._noun} match these filters."

    def _reset_empty_state(self) -> None:
        """The empty state's button: back to the full dataset."""
        # The toolbar's Clear filters leaves the Hide empty view option alone,
        # but this button promises the whole dataset, so undo that too.
        self._cards_hide_empty.set(False)
        self._clear_filters()

    def _scroll_cards_to_top(self) -> None:
        self._cards.scroll_to_top()

    def restyle_cards(self) -> None:
        """Recolour the hand-drawn parts after a theme switch."""
        self._cards.restyle()
        # A theme can change a button's font/padding, so the wrapping filter bar
        # needs fresh measurements too (otherwise its rows keep stale widths).
        # Popups are rebuilt on demand; close an open one so its tinted school
        # crests pick up the new foreground colour.
        self._filters.close_popups()
        self._filters.restyle()
        self._preview.reload()

    def apply_image_settings(
        self, settings: AppSettings, *, initial: bool = False
    ) -> None:
        """Adopt a new image mode / local folder (after Settings is saved).

        The service drops every pending load, so a request made under the old
        mode can never replace a card afterwards.
        """
        changed = self._images.configure(
            settings.image_mode, settings.local_image_dir or None
        )
        if initial or not changed:
            return
        self._cards.reload_images()
        self._preview.reload()
        self._retain_images()

    def reload_artwork(self) -> None:
        """Re-resolve pictures after the remote asset base URL changed."""
        self._images.invalidate()
        self._cards.reload_images()
        self._preview.reload()
        self._retain_images()

    def _select_card(self, iid: str) -> None:
        if iid not in self._payloads or iid == self._selected_iid:
            return
        self._selected_iid = iid
        self._on_select()

    def _highlight_card(self, iid: str | None) -> None:
        self._cards.select(iid)

    def _spec_for(self, iid: str | None) -> CardSpec | None:
        if iid is None:
            return None
        return next((spec for spec in self._card_specs if spec.key == iid), None)

    def _update_preview(self, iid: str | None) -> None:
        """Show the selected row beside the editor (fixed-size, so no shifting)."""
        spec = self._spec_for(iid)
        if spec is not None:
            self._preview_title.configure(text=spec.name or "(unnamed)")
            self._preview_subtitle.configure(text=spec.detail or spec.kind.title())
            self._preview.set_asset(spec.asset, fit=spec.fit, tint=spec.tint)
            return
        self._preview_title.configure(text="Nothing selected")
        self._preview_subtitle.configure(text="")
        self._preview.clear()

    def _retain_images(self) -> None:
        """Keep only the pictures the visible cards and the preview show."""
        self._images.retain([*self._cards.image_keys(), *self._preview.image_keys()])

    def _set_info(self, text: str) -> None:
        self._info.configure(text=text)

    def _update_info(self) -> None:
        parts: list[str] = []
        if self.path is not None:
            if self.spec is not None:
                parts.append(self.spec.label)
            parts.append(_elide_middle(str(self.path)))
        if self._loaded_mtime:
            parts.append(
                time.strftime(
                    "modified %Y-%m-%d %H:%M:%S", time.localtime(self._loaded_mtime)
                )
            )
        if self._import_summary:
            parts.append(self._import_summary)
        self._set_info("  ·  ".join(parts))

    def _sync_file_choice(self) -> None:
        labels = [spec.label for spec in scanner_files.SCAN_FILES]
        self._file_combo.configure(values=labels)
        if self.spec is not None:
            self._file_choice.set(self.spec.label)
        elif self.path is not None:
            self._file_choice.set(self.path.name)

    def _sync_buttons(self) -> None:
        loaded = self.doc is not None
        self._save_button.configure(state="normal" if loaded else "disabled")
        self._save_as_button.configure(state="normal" if loaded else "disabled")
        self._reload_button.configure(
            state="normal" if self.path is not None else "disabled"
        )
        addable = loaded and self.kind in (
            scanner_files.STUDENTS_FINAL, scanner_files.STUDENTS_RAW,
            scanner_files.ITEMS_FINAL, scanner_files.COUNTS_RAW,
            scanner_files.EQUIPMENT_FINAL,
        )  # fmt: skip
        self._add_button.configure(state="normal" if addable else "disabled")
        raw = (
            self.spec is not None
            and self.spec.processors
            and self.path == self.spec.path
        )
        self._reprocess_button.configure(
            state="normal" if raw and self.path and self.path.is_file() else "disabled"
        )

    def _notify_file_changed(self) -> None:
        if self._on_file_changed is not None:
            self._on_file_changed()

    def _set_dirty(self, dirty: bool) -> None:
        if dirty == self.dirty:
            return
        self.dirty = dirty
        self._dirty_label.configure(text="● unsaved changes" if dirty else "")
        if self._on_dirty_changed is not None:
            self._on_dirty_changed(dirty)

    def _mark_dirty(self) -> None:
        self._set_dirty(True)
        self._update_info()
        if self._view_tabs.index("current") == _TAB_RAW:
            self._refresh_raw()

    # ------------------------------------------------------------------
    # Editor
    # ------------------------------------------------------------------
    def _clear_editor(self) -> None:
        self._field_vars.clear()
        self._name_var = None
        self._id_var = None
        for child in self._editor.winfo_children():
            child.destroy()

    def _show_editor_placeholder(self) -> None:
        self._clear_editor()
        ttk.Label(
            self._editor,
            text="Select a card to edit it here.",
            style=MUTED,
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=8)

    def _editor_card(self, title: str) -> ttk.Labelframe:
        card = ttk.Labelframe(self._editor, text=title, padding=(12, 8))
        card.pack(fill="x", pady=(0, 12))
        return card

    def _on_select(self) -> None:
        iid = self._selected_iid
        self._highlight_card(iid)
        stored = self._payloads.get(iid) if iid is not None else None
        if stored == self._selected_payload:
            # Re-selecting the same row keeps the editor (and the user's
            # cursor) instead of redrawing it.
            return
        self._selected_payload = stored
        self._clear_editor()
        if stored is None:
            self._show_editor_placeholder()
            self._update_preview(None)
            return
        kind = stored[0]
        if kind == "student":
            self._build_student_editor(stored[1])
        elif kind == "equipment":
            self._build_equipment_editor(stored[1], stored[2])
        elif kind == "entry":
            self._build_entry_editor(stored[1])
        else:
            self._build_currency_editor(stored[1])
        self._update_preview(iid)
        self._retain_images()

    def _add_field_grid(
        self,
        card: ttk.Labelframe,
        fields: tuple[Field, ...],
        record: dict,
        *,
        row: int,
        columns: int = 2,
    ) -> int:
        """Lay ``fields`` out as a compact grid; returns the rows it used."""
        grid = ttk.Frame(card)
        grid.grid(row=row, column=0, columnspan=columns + 2, sticky="ew", pady=(6, 0))
        for column in range(columns):
            grid.columnconfigure(column, weight=1, uniform="fields")
        for index, field in enumerate(fields):
            cell = ttk.Frame(grid)
            cell.grid(
                row=index // columns,
                column=index % columns,
                sticky="ew",
                padx=(0, 10),
                pady=2,
            )
            label = field.label
            if field.maximum is not None:  # keep the accepted range visible
                label = f"{field.label} ({field.minimum}-{field.maximum})"
            ttk.Label(cell, text=label).pack(anchor="w")
            value = _stat(record, field.key)
            var = tk.StringVar(value="" if value is None else str(value))
            entry = ttk.Entry(cell, textvariable=var, width=10)
            entry.pack(fill="x")
            if field.help:
                ttk.ToolTip(entry, text=field.help)
            self._field_vars[field.key] = var
        return -(-len(fields) // columns)  # ceil

    def _build_student_editor(self, index: int) -> None:
        """Structured, readable inspector for an individual student record."""
        characters = (
            self.doc.get("characters", []) if isinstance(self.doc, dict) else []
        )
        if not (0 <= index < len(characters)):
            return
        record = characters[index]
        # current = (
        #     record.get("current") if isinstance(record.get("current"), dict) else {}
        # )

        # -------------------------------------------------------------
        # Helper to create a labeled entry with tooltip & bounds hint
        # -------------------------------------------------------------
        def create_field_cell(
            parent: ttk.Frame,
            field: Field,
            *,
            col: int,
            row: int,
            width: int = 6,
        ) -> None:
            cell = ttk.Frame(parent)
            cell.grid(row=row, column=col, sticky="ew", padx=(0, 6), pady=2)

            hint = (
                f" ({field.minimum}-{field.maximum})"
                if field.maximum is not None
                else ""
            )
            ttk.Label(cell, text=f"{field.label}{hint}").pack(anchor="w")

            val = _stat(record, field.key)
            var = tk.StringVar(value="" if val is None else str(val))
            entry = ttk.Entry(cell, textvariable=var, width=width)
            entry.pack(fill="x", pady=(1, 0))
            if field.help:
                ttk.ToolTip(entry, text=field.help)
            self._field_vars[field.key] = var

        # =============================================================
        # 1. Identity
        # =============================================================
        id_card = self._editor_card("Identity")
        id_card.columnconfigure(1, weight=1)

        ttk.Label(id_card, text="Name").grid(
            row=0, column=0, sticky="w", pady=2, padx=(0, 8)
        )
        self._name_var = tk.StringVar(value=str(record.get("name", "")))
        ttk.Entry(id_card, textvariable=self._name_var).grid(
            row=0, column=1, sticky="ew", pady=2
        )

        ttk.Label(id_card, text="ID").grid(
            row=1, column=0, sticky="w", pady=2, padx=(0, 8)
        )
        self._id_var = tk.StringVar(value=str(record.get("id", "")))
        id_row = ttk.Frame(id_card)
        id_row.grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Entry(id_row, textvariable=self._id_var, width=10).pack(side="left")
        ttk.Label(id_row, text=" (blank/N/A if unresolved)", style=MUTED).pack(
            side="left", padx=(4, 0)
        )

        # =============================================================
        # 2. Core Stats (Level, Stars, Bond)
        # =============================================================
        core_card = self._editor_card("Core Progression")
        for c in range(3):
            core_card.columnconfigure(c, weight=1, uniform="core")

        create_field_cell(
            core_card, Field("level", "Level", "str", 1, 90), col=0, row=0
        )
        create_field_cell(core_card, Field("star", "Star", "int", 1, 5), col=1, row=0)
        create_field_cell(core_card, Field("bond", "Bond", "str", 0, 100), col=2, row=0)

        # =============================================================
        # 3. Skills (EX, Basic, Passive, Sub)
        # =============================================================
        skill_card = self._editor_card("Skills")
        for c in range(4):
            skill_card.columnconfigure(c, weight=1, uniform="skills")

        create_field_cell(
            skill_card, Field("ex", "EX", "str", 1, 5), col=0, row=0, width=5
        )
        create_field_cell(
            skill_card, Field("basic", "Basic", "str", 1, 10), col=1, row=0, width=5
        )
        create_field_cell(
            skill_card, Field("passive", "Passive", "str", 0, 10), col=2, row=0, width=5
        )
        create_field_cell(
            skill_card, Field("sub", "Sub", "str", 0, 10), col=3, row=0, width=5
        )

        # =============================================================
        # 4. Gears & Unique Equipment
        # =============================================================
        gear_card = self._editor_card("Gears & Unique Equipment")
        for c in range(4):
            gear_card.columnconfigure(c, weight=1, uniform="gears")

        # Row 0: Unique Equipment
        ue_stars_field = Field("ue", "UE Stars", "int", 0, 4)
        ue_lvl_field = Field("ue_level", "UE Level", "str", 0, 60)
        create_field_cell(gear_card, ue_stars_field, col=0, row=0, width=6)
        create_field_cell(gear_card, ue_lvl_field, col=1, row=0, width=6)

        # Row 1: Gear Slots 1-3 & Bond Gear
        gear_bond_key = (
            "gear_bond" if self.kind == scanner_files.STUDENTS_RAW else "bond_gear"
        )
        create_field_cell(
            gear_card,
            Field("gear1", "Gear 1", "str", 0, GEAR_LEVEL_CAP),
            col=0,
            row=1,
            width=5,
        )
        create_field_cell(
            gear_card,
            Field("gear2", "Gear 2", "str", 0, GEAR_LEVEL_CAP),
            col=1,
            row=1,
            width=5,
        )
        create_field_cell(
            gear_card,
            Field("gear3", "Gear 3", "str", 0, GEAR_LEVEL_CAP),
            col=2,
            row=1,
            width=5,
        )
        create_field_cell(
            gear_card,
            Field(gear_bond_key, "Bond Gear", "str", 0, 2),
            col=3,
            row=1,
            width=5,
        )

        # =============================================================
        # 5. Talents (HP, ATK, HEAL)
        # =============================================================
        talent_card = self._editor_card("Talents")
        for c in range(3):
            talent_card.columnconfigure(c, weight=1, uniform="talents")

        hp_key = "talent_hp" if self.kind == scanner_files.STUDENTS_RAW else "book_hp"
        atk_key = (
            "talent_atk" if self.kind == scanner_files.STUDENTS_RAW else "book_atk"
        )
        heal_key = (
            "talent_healing" if self.kind == scanner_files.STUDENTS_RAW else "book_heal"
        )

        create_field_cell(
            talent_card, Field(hp_key, "HP", "str", 0, TALENT_LEVEL_CAP), col=0, row=0
        )
        create_field_cell(
            talent_card, Field(atk_key, "ATK", "str", 0, TALENT_LEVEL_CAP), col=1, row=0
        )
        create_field_cell(
            talent_card,
            Field(heal_key, "HEAL", "str", 0, TALENT_LEVEL_CAP),
            col=2,
            row=0,
        )

        # =============================================================
        # 6. Action Buttons
        # =============================================================
        actions = ttk.Frame(self._editor, padding=(0, 6, 0, 12))
        actions.pack(fill="x")
        button(
            actions,
            "Apply",
            "check-lg",
            style="success",
            command=lambda: self._apply_student(index),
            tip="Save edits to memory",
        ).pack(side="left")
        button(
            actions,
            "Remove",
            "trash3-fill",
            style="danger",
            command=lambda: self._remove_student(index),
            tip="Remove this student from the roster",
        ).pack(side="left", padx=8)

    def _build_equipment_editor(self, category: str, tier: str) -> None:
        grouped = self.doc if isinstance(self.doc, dict) else {}
        entry = gamedata.equipment(category, tier)
        card = self._editor_card("Equipment")
        title = (
            str(entry.get("name"))
            if entry
            else "(name not in equipment_processed.json)"
        )
        ttk.Label(card, text=title, font=heading(11)).grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        rarity = entry.get("rarity") if entry else None
        if rarity:
            ttk.Label(card, text=f"Rarity {rarity}", style=MUTED).grid(
                row=1, column=0, columnspan=3, sticky="w", pady=(0, 4)
            )
        ttk.Label(card, text="Category").grid(
            row=2, column=0, sticky="w", pady=3, padx=(0, 10)
        )
        ttk.Label(card, text=category).grid(row=2, column=1, sticky="w", pady=3)
        ttk.Label(card, text="Tier").grid(
            row=3, column=0, sticky="w", pady=3, padx=(0, 10)
        )
        tier_var = tk.StringVar(value=tier)
        ttk.Entry(card, textvariable=tier_var, width=14).grid(
            row=3, column=1, sticky="w", pady=3
        )
        self._field_vars["tier"] = tier_var
        ttk.Label(card, text="Quantity").grid(
            row=4, column=0, sticky="w", pady=3, padx=(0, 10)
        )
        qty_var = tk.StringVar(value=str(grouped.get(category, {}).get(tier, "")))
        ttk.Entry(card, textvariable=qty_var, width=14).grid(
            row=4, column=1, sticky="w", pady=3
        )
        self._field_vars["value"] = qty_var
        ttk.Label(card, text="whole number ≥ 0", style=MUTED).grid(
            row=4, column=2, sticky="w", padx=(12, 0)
        )

        actions = ttk.Frame(card)
        actions.grid(row=5, column=0, columnspan=3, sticky="w", pady=(10, 0))
        button(
            actions,
            "Apply",
            "check-lg",
            style="success",
            command=lambda: self._apply_equipment(category, tier),
        ).pack(side="left")
        button(
            actions,
            "Remove",
            "trash3-fill",
            style="danger",
            command=lambda: self._remove_equipment(category, tier),
        ).pack(side="left", padx=6)

    def _build_entry_editor(self, key: str) -> None:
        entries = self.doc if isinstance(self.doc, dict) else {}
        label = (
            "Item / equipment" if self.kind == scanner_files.COUNTS_RAW else "Item ID"
        )
        entry = gamedata.item(key) if self.kind == scanner_files.ITEMS_FINAL else None
        card = self._editor_card(label)
        row = 0
        if entry is not None:
            ttk.Label(card, text=str(entry.get("name")), font=heading(11)).grid(
                row=row, column=0, columnspan=3, sticky="w"
            )
            row += 1
            ttk.Label(
                card, text=f"Rarity {entry.get('rarity', '?')}", style=MUTED
            ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 4))
            row += 1
        ttk.Label(card, text=label).grid(
            row=row, column=0, sticky="w", pady=3, padx=(0, 10)
        )
        key_var = tk.StringVar(value=key)
        ttk.Entry(card, textvariable=key_var, width=30).grid(
            row=row, column=1, sticky="w", pady=3
        )
        self._field_vars["key"] = key_var
        row += 1
        ttk.Label(card, text="Quantity").grid(
            row=row, column=0, sticky="w", pady=3, padx=(0, 10)
        )
        qty_var = tk.StringVar(value=str(entries.get(key, "")))
        ttk.Entry(card, textvariable=qty_var, width=14).grid(
            row=row, column=1, sticky="w", pady=3
        )
        self._field_vars["value"] = qty_var
        ttk.Label(card, text="whole number ≥ 0", style=MUTED).grid(
            row=row, column=2, sticky="w", padx=(12, 0)
        )

        actions = ttk.Frame(card)
        actions.grid(row=row + 1, column=0, columnspan=3, sticky="w", pady=(10, 0))
        button(
            actions,
            "Apply",
            "check-lg",
            style="success",
            command=lambda: self._apply_entry(key),
        ).pack(side="left")
        button(
            actions,
            "Remove",
            "trash3-fill",
            style="danger",
            command=lambda: self._remove_entry(key),
        ).pack(side="left", padx=6)

    def _build_currency_editor(self, key: str) -> None:
        entries = self.doc if isinstance(self.doc, dict) else {}
        value = entries.get(key)
        card = self._editor_card("Currency")
        ttk.Label(card, text="Key").grid(
            row=0, column=0, sticky="w", pady=3, padx=(0, 10)
        )
        ttk.Label(card, text=key).grid(row=0, column=1, sticky="w", pady=3)
        row = 1
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                ttk.Label(card, text=sub_key).grid(
                    row=row, column=0, sticky="w", pady=3, padx=(0, 10)
                )
                var = tk.StringVar(value=str(sub_value))
                ttk.Entry(card, textvariable=var, width=20).grid(
                    row=row, column=1, sticky="w", pady=3
                )
                self._field_vars[sub_key] = var
                row += 1
        else:
            ttk.Label(card, text="Value").grid(
                row=row, column=0, sticky="w", pady=3, padx=(0, 10)
            )
            var = tk.StringVar(value=str(value))
            ttk.Entry(card, textvariable=var, width=20).grid(
                row=row, column=1, sticky="w", pady=3
            )
            self._field_vars["value"] = var
            row += 1
        ttk.Label(
            card, text="Stored exactly as scanned (commas kept).", style=MUTED
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(6, 0))
        button(
            card,
            "Apply",
            "check-lg",
            style="success",
            command=lambda: self._apply_currency(key),
        ).grid(row=row + 1, column=0, columnspan=3, sticky="w", pady=(10, 0))

    # ------------------------------------------------------------------
    # Applying edits
    # ------------------------------------------------------------------
    def _read_int(
        self, key: str, label: str, minimum: int = 0, maximum: int | None = None
    ) -> int:
        raw = self._field_vars[key].get().strip()
        try:
            value = int(raw)
        except ValueError:
            raise ValueError(f"{label} must be a whole number.") from None
        if value < minimum or (maximum is not None and value > maximum):
            span = (
                f"{minimum}-{maximum}" if maximum is not None else f"at least {minimum}"
            )
            raise ValueError(f"{label} must be {span}.")
        return value

    def _report_error(self, message: str) -> None:
        show_error(self, "Invalid value", message)

    def _apply_student(self, index: int) -> None:
        characters = (
            self.doc.get("characters", []) if isinstance(self.doc, dict) else []
        )
        if not (0 <= index < len(characters)):
            return
        record = characters[index]
        name = self._name_var.get().strip() if self._name_var else ""
        if not name:
            self._report_error("The student name cannot be empty.")
            return
        fields = student_fields(self.kind)
        try:
            values = {
                field.key: self._coerce(
                    field,
                    self._read_int(
                        field.key, field.label, field.minimum, field.maximum
                    ),
                )
                for field in fields
            }
        except ValueError as exc:
            self._report_error(str(exc))
            return
        record["name"] = name
        if self._id_var is not None:
            record["id"] = self._id_var.get().strip()
        current = record.get("current")
        if not isinstance(current, dict):
            current = {}
            record["current"] = current
        # Keep any extra keys the scanner wrote (unknown stats survive edits).
        for key, value in values.items():
            current[key] = value
        self._mark_dirty()
        self._render(select=("student", index))

    @staticmethod
    def _coerce(field: Field, value: int) -> object:
        return value if field.store == "int" else str(value)

    def _remove_student(self, index: int) -> None:
        characters = (
            self.doc.get("characters", []) if isinstance(self.doc, dict) else []
        )
        if not (0 <= index < len(characters)):
            return
        name = characters[index].get("name", "")
        if not confirm(
            self,
            "Remove student",
            f"Remove {name or 'this student'} from the data?",
            yes="Remove",
        ):
            return
        del characters[index]
        self._mark_dirty()
        self._render()

    def add_student(self) -> None:
        if self.kind not in STUDENT_KINDS or self.doc is None:
            return
        characters = self.doc.setdefault("characters", [])
        defaults = self._new_student_stats()
        characters.append({"id": "", "name": "New student", "current": defaults})
        self._mark_dirty()
        self._render(select=("student", len(characters) - 1))

    def _new_student_stats(self) -> dict:
        if self.kind == scanner_files.STUDENTS_FINAL:
            return dict(normalize_stats({}))
        return {field.key: max(field.minimum, 0) for field in RAW_STUDENT_FIELDS}

    def add_entry(self) -> None:
        """Add a row appropriate to the loaded document."""
        if self.doc is None:
            return
        if self.kind in STUDENT_KINDS:
            self.add_student()
        elif self.kind in (scanner_files.ITEMS_FINAL, scanner_files.COUNTS_RAW):
            label = (
                "Item / equipment name"
                if self.kind == scanner_files.COUNTS_RAW
                else "Item ID"
            )
            values = self._prompt_fields(
                "Add entry", (("key", label, "", ()), ("value", "Quantity", "0", ()))
            )
            if not values or not values["key"].strip():
                return
            try:
                quantity = int(values["value"])
            except ValueError:
                self._report_error("Quantity must be a whole number.")
                return
            self.doc[values["key"].strip()] = max(0, quantity)
            self._mark_dirty()
            self._render(select=("entry", values["key"].strip()))
        elif self.kind == scanner_files.EQUIPMENT_FINAL:
            categories = tuple(sorted(self.doc.keys()))
            values = self._prompt_fields(
                "Add equipment tier",
                (
                    (
                        "category",
                        "Category",
                        categories[0] if categories else "",
                        categories,
                    ),
                    ("tier", "Tier", "", ()),
                    ("value", "Quantity", "0", ()),
                ),
            )
            if (
                not values
                or not values["category"].strip()
                or not values["tier"].strip()
            ):
                return
            try:
                quantity = max(0, int(values["value"]))
            except ValueError:
                self._report_error("Quantity must be a whole number.")
                return
            category = values["category"].strip()
            tier = values["tier"].strip()
            self.doc.setdefault(category, {})[tier] = quantity
            self._mark_dirty()
            self._render(select=("equipment", category, tier))

    def _prompt_fields(self, title: str, specs: tuple) -> dict[str, str] | None:
        """A small themed form; ``specs`` are (key, label, initial, choices)."""
        dialog = ttk.Toplevel(title=title, master=self, transient=self)
        body = ttk.Frame(dialog, padding=(16, 12))
        body.pack(fill="both", expand=True)
        variables: dict[str, tk.StringVar] = {}
        for row, (key, label, initial, choices) in enumerate(specs):
            ttk.Label(body, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=3
            )
            var = tk.StringVar(value=initial)
            variables[key] = var
            if choices:
                ttk.Combobox(
                    body, textvariable=var, values=list(choices), width=28
                ).grid(row=row, column=1, sticky="ew", pady=3)
            else:
                ttk.Entry(body, textvariable=var, width=30).grid(
                    row=row, column=1, sticky="ew", pady=3
                )
        body.columnconfigure(1, weight=1)
        result: dict[str, str] = {}

        def accept() -> None:
            result.update({key: var.get() for key, var in variables.items()})
            dialog.destroy()

        actions = ttk.Frame(body)
        actions.grid(row=len(specs), column=0, columnspan=2, sticky="e", pady=(12, 0))
        button(actions, "Add", "plus-lg", style="success", command=accept).pack(
            side="right"
        )
        button(actions, "Cancel", "x-lg", command=dialog.destroy).pack(
            side="right", padx=(0, 6)
        )
        dialog.bind("<Return>", lambda _e: accept())
        dialog.bind("<Escape>", local_hotkey(dialog.destroy))
        dialog.update_idletasks()
        center_on_parent(dialog, self)
        dialog.grab_set()
        dialog.wait_window()
        return result or None

    def _apply_equipment(self, category: str, tier: str) -> None:
        grouped = self.doc if isinstance(self.doc, dict) else {}
        tiers = grouped.get(category)
        if not isinstance(tiers, dict):
            return
        new_tier = self._field_vars["tier"].get().strip()
        if not new_tier:
            self._report_error("The tier cannot be empty.")
            return
        try:
            quantity = self._read_int("value", "Quantity", 0)
        except ValueError as exc:
            self._report_error(str(exc))
            return
        if new_tier != tier:
            tiers.pop(tier, None)
        tiers[new_tier] = quantity
        self._mark_dirty()
        self._render(select=("equipment", category, new_tier))

    def _remove_equipment(self, category: str, tier: str) -> None:
        grouped = self.doc if isinstance(self.doc, dict) else {}
        tiers = grouped.get(category)
        if isinstance(tiers, dict) and tier in tiers:
            if not confirm(
                self, "Remove tier", f"Remove {category} tier {tier}?", yes="Remove"
            ):
                return
            del tiers[tier]
            self._mark_dirty()
            self._render()

    def _apply_entry(self, key: str) -> None:
        entries = self.doc if isinstance(self.doc, dict) else {}
        new_key = self._field_vars["key"].get().strip()
        if not new_key:
            self._report_error("The key cannot be empty.")
            return
        try:
            quantity = self._read_int("value", "Quantity", 0)
        except ValueError as exc:
            self._report_error(str(exc))
            return
        if new_key != key:
            entries.pop(key, None)
        entries[new_key] = quantity
        self._mark_dirty()
        self._render(select=("entry", new_key))

    def _remove_entry(self, key: str) -> None:
        entries = self.doc if isinstance(self.doc, dict) else {}
        if key in entries:
            if not confirm(self, "Remove entry", f"Remove {key}?", yes="Remove"):
                return
            del entries[key]
            self._mark_dirty()
            self._render()

    def _apply_currency(self, key: str) -> None:
        entries = self.doc if isinstance(self.doc, dict) else {}
        value = entries.get(key)
        if isinstance(value, dict):
            for sub_key in value:
                if sub_key in self._field_vars:
                    value[sub_key] = self._field_vars[sub_key].get().strip()
        elif "value" in self._field_vars:
            entries[key] = self._field_vars["value"].get().strip()
        self._mark_dirty()
        self._render(select=("currency", key))

    # ------------------------------------------------------------------
    # Raw JSON
    # ------------------------------------------------------------------
    def _raw_text(self) -> str:
        return json.dumps(self.doc, indent=4, ensure_ascii=False)

    def _refresh_raw(self) -> None:
        widget = self._raw.text
        widget.delete("1.0", "end")
        if self.doc is not None:
            widget.insert("1.0", self._raw_text())

    def _apply_raw(self) -> None:
        text = self._raw.text.get("1.0", "end-1c")
        try:
            parsed = json.loads(text)
        except ValueError as exc:
            self._report_error(f"Not valid JSON: {exc}")
            return
        if not isinstance(parsed, (dict, list)):
            self._report_error("The JSON root must be an object or an array.")
            return
        self.doc = parsed
        self._kind_for_document()
        self._mark_dirty()
        self._render()
        self._on_log("Data tab: applied the raw JSON edit.", "info")

    def _kind_for_document(self) -> None:
        """Keep the loaded schema when the shape still matches it."""
        doc = self.doc
        if self.kind in STUDENT_KINDS:
            if not (isinstance(doc, dict) and isinstance(doc.get("characters"), list)):
                self.kind = scanner_files.GENERIC
        elif (
            self.kind == scanner_files.CURRENCIES_RAW
            or self.kind
            in (
                scanner_files.ITEMS_FINAL,
                scanner_files.COUNTS_RAW,
                scanner_files.EQUIPMENT_FINAL,
            )
        ) and not isinstance(doc, dict):
            self.kind = scanner_files.GENERIC

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------
    def save(self) -> bool:
        if self.doc is None or self.path is None:
            return False
        target = self.path
        if self._changed_externally(target) and not confirm(
            self,
            "File changed on disk",
            f"{target.name} has changed since it was loaded. Overwrite it with the data shown here?",
            yes="Overwrite",
        ):
            return False
        return self._write(target)

    def save_as(self) -> bool:
        if self.doc is None:
            return False
        chosen = filedialog.asksaveasfilename(
            parent=self,
            title="Save data as",
            initialdir=str(self.path.parent if self.path else Path_Config.OUTPUT_DIR),
            initialfile=self.path.name if self.path else "scanned_data.json",
            defaultextension=".json",
            filetypes=list(JSON_FILETYPES),
        )
        if not chosen:
            return False
        target = Path(chosen)
        if self._changed_externally(target) and not confirm(
            self,
            "Overwrite file",
            f"{target.name} already exists. Overwrite it?",
            yes="Overwrite",
        ):
            return False
        return self._write(target)

    def _write(self, target: Path) -> bool:
        try:
            write_json(target, self.doc)
        except (OSError, PermissionError) as exc:
            show_error(self, "Could not save", f"Writing {target} failed: {exc}")
            self._on_log(f"Data tab: could not write {target}: {exc}", "error")
            return False
        self.path = target
        self.spec = scanner_files.identify(target)
        try:
            self._loaded_mtime = target.stat().st_mtime
        except OSError:
            self._loaded_mtime = None
        self._set_dirty(False)
        self._update_info()
        self._sync_buttons()
        self._on_log(f"Data tab: saved {relative(target)}", "ok")
        if self._view_tabs.index("current") == _TAB_RAW:
            self._refresh_raw()
        return True

    def reload(self) -> bool:
        if self.path is None:
            return False
        if not self._may_replace("reloading"):
            return False
        self.load_path(self.path)
        return True

    def _changed_externally(self, target: Path) -> bool:
        if self._loaded_mtime is None or not target.is_file():
            return False
        try:
            return target.stat().st_mtime > self._loaded_mtime + 1e-6
        except OSError:
            return False

    def reprocess(self) -> bool:
        """Rebuild the final values from the loaded raw scan file."""
        if self.spec is None or not self.spec.processors or self.path is None:
            return False
        if not self.path.is_file():
            show_error(self, "Missing file", f"{relative(self.path)} does not exist.")
            return False
        if self.dirty and not self._may_replace(
            "re-processing (the processor reads the saved file)"
        ):
            return False

        spec = self.spec
        self._reprocess_button.configure(state="disabled")
        self._set_info(f"Re-processing {relative(self.path)}…")
        self._on_log(f"Data tab: running {spec.label} processors…", "cmd")

        def work() -> None:
            try:
                outputs = scanner_files.reprocess(spec)
                error = None
            except Exception as exc:  # noqa: BLE001 - report, never crash the UI
                outputs, error = [], exc
            self._on_post(lambda: self._finish_reprocess(spec, outputs, error))

        threading.Thread(target=work, daemon=True).start()
        return True

    def _finish_reprocess(
        self, spec: ScanFile, outputs: list[Path], error: Exception | None
    ) -> None:
        self._sync_buttons()
        if error is not None:
            self._update_info()
            self._on_log(f"Data tab: re-processing failed: {error}", "error")
            show_error(self, "Re-processing failed", str(error))
            return
        names = ", ".join(relative(path) for path in outputs) or "nothing"
        self._on_log(f"Data tab: re-processed {spec.label} → {names}", "ok")
        final = (
            scanner_files.SCAN_FILES_BY_KEY.get(spec.final_key)
            if spec.final_key
            else None
        )
        if final is not None and final.path.is_file():
            self.load_path(final.path)
        elif outputs:
            self.load_path(outputs[0])

    # ------------------------------------------------------------------
    # Hooks used by the app
    # ------------------------------------------------------------------
    def active_path(self) -> Path | None:
        return self.path

    def has_unsaved_edits(self) -> bool:
        return self.dirty

    def prompt_save_before(self, action: str) -> bool:
        """Save-or-continue prompt before running something that reads the file."""
        if not self.dirty:
            return True
        answer = ask_save_discard_cancel(
            self,
            "Unsaved data changes",
            f"The Data tab has unsaved edits to {self.path.name if self.path else 'the loaded data'}. "
            f"Save them before {action}?",
            save="Save and continue",
            discard="Continue without saving",
        )
        if answer == "save":
            return self.save()
        return answer == "discard"

    def on_scan_completed(self, started_at: float) -> None:
        """Load the newest scanner output produced by a finished scan."""
        outputs = scanner_files.modified_since(started_at - 1.0)
        if not outputs:
            self._on_log(
                "Data tab: the scan did not update any known output file.", "warn"
            )
            return
        listed = ", ".join(spec.display for spec in outputs)
        self._on_log(f"Scan output: {listed}", "ok")
        primary = (
            next((s for s in outputs if s.kind == scanner_files.STUDENTS_FINAL), None)
            or next(
                (s for s in outputs if s.kind == scanner_files.EQUIPMENT_FINAL), None
            )
            or next((s for s in outputs if s.kind == scanner_files.ITEMS_FINAL), None)
            or outputs[0]
        )
        if self.dirty and not self._may_replace("loading the new scan output"):
            self._on_log(
                f"Data tab: kept your unsaved edits; {primary.display} is ready when you reload.",
                "warn",
            )
            return
        self.load_path(primary.path)

    def reveal_active(self) -> None:
        if self.path is None:
            return
        if error := folders.reveal(self.path):
            self._on_log(error, "error")
