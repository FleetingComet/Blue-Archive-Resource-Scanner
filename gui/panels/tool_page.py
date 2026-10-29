"""One page per exporter/tool: its arguments, the exact command, the result.

The argument widgets are built from :mod:`gui.registry` (which mirrors each
module's ``argparse`` block), so a tool's page always shows the real flags,
defaults and help strings. Running happens from the window's action bar; the
page only describes and configures the run.
"""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable
from functools import partial
from pathlib import Path

import ttkbootstrap as ttk

from gui.components.file_selector import OPEN, FileSelector
from gui.metadata import relative
from gui.registry import (
    BOOL,
    CHOICE,
    FILE,
    GROUP,
    GROUP_FIELDS,
    Option,
    Tool,
)
from gui.ui import MUTED, OUTCOME_STYLE, Page, button
from src.core.paths import Path_Config


class ChipList(ttk.Frame):
    """Ordered comma-list editor: click a field to add it, drag a chip to
    reorder, double-click a chip (or press Clear) to remove it.

    All buttons are created once and only re-packed, so a drag in progress
    keeps receiving motion events. ``value()`` is the text passed to ``-g``.
    """

    def __init__(self, master, fields: tuple[str, ...], on_change: Callable[[], None]):
        super().__init__(master)
        self._on_change = on_change
        self._fundamental = tuple(fields)
        # Every field the widget can ever show, so a value copied from another
        # tool that uses a wider set still gets rendered.
        all_fields = tuple(dict.fromkeys((*fields, *GROUP_FIELDS)))
        self._chips: list[str] = []
        self._dragging: str | None = None

        self._chip_row, self._pill_row = ttk.Frame(self), ttk.Frame(self)
        self._chip_row.pack(anchor="w")
        self._pill_row.pack(anchor="w", pady=(4, 0))

        self._empty = ttk.Label(self._chip_row, text="default order", style=MUTED)
        self._clear = button(
            self._chip_row,
            "Clear",
            "x-lg",
            style="danger link",
            command=self.clear,
            tip="Remove all group fields",
        )
        self._pills = {
            f: button(
                self._pill_row,
                f,
                "plus-lg",
                command=partial(self._add, f),
                tip=f"Group by {f}",
            )
            for f in all_fields
        }
        self._chip_buttons: dict[str, ttk.Button] = {}
        for field in all_fields:
            chip = ttk.Button(
                self._chip_row,
                text=field,
                bootstyle="info",
                padding=(6, 1),
                cursor="hand2",
            )
            chip.bind("<Button-1>", partial(self._start_drag, field))
            chip.bind("<B1-Motion>", self._drag)
            chip.bind("<ButtonRelease-1>", lambda _e: setattr(self, "_dragging", None))
            chip.bind("<Double-Button-1>", partial(self._remove, field))
            self._chip_buttons[field] = chip
        self._layout()

    def value(self) -> str:
        return ",".join(self._chips)

    def fields(self) -> list[str]:
        return list(self._chips)

    def set_fields(self, fields: list[str]) -> None:
        """Replace the whole list (used by the copy-grouping action)."""
        self._chips = list(fields)
        self._changed()

    def clear(self) -> None:
        self._chips.clear()
        self._changed()

    def _add(self, field: str) -> None:
        self._chips.append(field)
        self._changed()

    def _remove(self, field: str, _event=None) -> None:
        if field in self._chips:
            self._chips.remove(field)
            self._changed()

    def _changed(self) -> None:
        self._layout()
        self._on_change()

    def _layout(self) -> None:
        widgets = (
            self._empty,
            self._clear,
            *self._chip_buttons.values(),
            *self._pills.values(),
        )
        for widget in widgets:
            widget.pack_forget()
        for field in self._chips:
            if field in self._chip_buttons:
                self._chip_buttons[field].pack(side="left", padx=(0, 3))
        (self._clear if self._chips else self._empty).pack(side="left")
        for field, pill in self._pills.items():
            if field not in self._chips:
                pill.pack(side="left", padx=(0, 3))

    def _start_drag(self, field: str, _event=None) -> None:
        self._dragging = field

    def _drag(self, event: tk.Event) -> None:
        field = self._dragging
        if field is None or len(self._chips) < 2:
            return
        # The chip slot under the pointer is where the dragged chip goes.
        slot = len(self._chips) - 1
        for index, name in enumerate(self._chips):
            chip = self._chip_buttons.get(name)
            if chip is None:
                continue
            if event.x_root < chip.winfo_rootx() + chip.winfo_width() / 2:
                slot = index
                break
        if slot != self._chips.index(field):
            self._chips.remove(field)
            self._chips.insert(slot, field)
            self._changed()


class ToolPage(Page):
    """What the tool does, its arguments, its command and its last result."""

    def __init__(
        self,
        master,
        tool: Tool,
        *,
        on_copy_grouping: Callable[[], None] | None = None,
        copy_grouping_label: str = "Copy grouping from…",
        on_notice: Callable[[str, str], None] | None = None,
        active_file: Callable[[], Path | None] | None = None,
        on_open_in_data: Callable[[Path], None] | None = None,
    ):
        super().__init__(master, tool.label, tool.description)
        self.tool = tool
        self._on_copy_grouping = on_copy_grouping
        self._on_notice = on_notice
        self._active_file = active_file
        self._on_open_in_data = on_open_in_data
        self._inputs: dict[str, ChipList | tk.Variable] = {}
        self._value_maps: dict[str, dict[str, str | None]] = {}
        self._file_widgets: dict[Path, tuple[ttk.Label, ttk.Button | None]] = {}

        self._build_options(copy_grouping_label)
        self._build_files_card()
        _card, self._preview = self.command_card()

        card = self.card("Last run")
        self._last_run = ttk.Label(card)
        self._last_run.grid(row=0, column=0, sticky="w")
        self.reset_last_run()

        self._sync_command()

    # ------------------------------------------------------------------
    # Options
    # ------------------------------------------------------------------
    def _build_options(self, copy_grouping_label: str) -> None:
        card = self.card("Arguments")
        if not self.tool.options:
            ttk.Label(card, text="This tool takes no arguments.", style=MUTED).pack(
                anchor="w"
            )
            return
        for option in self.tool.options:
            self._option_block(card, option, copy_grouping_label)

    def _option_block(
        self, card: ttk.Labelframe, option: Option, copy_grouping_label: str
    ) -> None:
        block = ttk.Frame(card)
        block.pack(fill="x", pady=(0, 10))
        controls = ttk.Frame(block)
        controls.pack(fill="x")

        if option.kind == BOOL:
            var = tk.BooleanVar(value=bool(option.default))
            ttk.Checkbutton(
                controls, text=option.label, variable=var, bootstyle="round toggle"
            ).pack(side="left")
            var.trace_add("write", self._sync_command)
            self._inputs[option.key] = var
        elif option.kind == CHOICE:
            ttk.Label(controls, text=option.label).pack(side="left", padx=(0, 8))
            labels = [label for label, _value in option.choices]
            mapping = {label: value for label, value in option.choices}
            default = mapping.get(str(option.default), option.default)
            selected = next(
                (label for label, value in option.choices if value == default),
                labels[0],
            )
            var = tk.StringVar(value=selected)
            ttk.Combobox(
                controls, textvariable=var, values=labels, state="readonly", width=22
            ).pack(side="left")
            var.trace_add("write", self._sync_command)
            self._inputs[option.key] = var
            self._value_maps[option.key] = mapping
        elif option.kind == GROUP:
            ttk.Label(controls, text=option.label).pack(side="left", padx=(0, 8))
            chips = ChipList(controls, GROUP_FIELDS, self._sync_command)
            chips.pack(side="left")
            self._inputs[option.key] = chips
            if self._on_copy_grouping is not None:
                button(
                    controls,
                    copy_grouping_label,
                    "arrow-left-right",
                    style="info outline",
                    command=self._copy_grouping,
                    tip="Transfer the grouping set from the other report tool",
                ).pack(side="left", padx=(10, 0))
            # The transfer message gets its own line so a long source tool name
            # cannot reflow the chip row.
            self._grouping_notice = ttk.Label(block, style=MUTED)
            self._grouping_notice.pack(anchor="w", pady=(4, 0))
        else:  # TEXT / FILE
            var = tk.StringVar(
                value="" if option.default is None else str(option.default)
            )
            if option.kind == FILE:
                FileSelector(
                    controls,
                    mode=OPEN,
                    textvariable=var,
                    title=f"Select {option.label}",
                    label=option.label,
                ).pack(side="left", fill="x", expand=True)
            else:
                ttk.Label(controls, text=option.label).pack(side="left", padx=(0, 8))
                ttk.Entry(controls, textvariable=var).pack(
                    side="left", fill="x", expand=True
                )
            var.trace_add("write", self._sync_command)
            self._inputs[option.key] = var

        note = option.hint or ""
        help_text = f"{option.declares} — {option.help}"
        if note:
            help_text = f"{help_text}  ({note})"
        ttk.Label(
            block, text=help_text, style=MUTED, wraplength=680, justify="left"
        ).pack(anchor="w", pady=(2, 0))

    # ------------------------------------------------------------------
    # Grouping transfer
    # ------------------------------------------------------------------
    def grouping_fields(self) -> list[str]:
        option = self.tool.group_option
        if option is None:
            return []
        return self._inputs[option.key].fields()

    def set_grouping(self, fields: list[str]) -> tuple[list[str], list[str]]:
        """Apply ``fields``; returns ``(kept, dropped)``."""
        option = self.tool.group_option
        if option is None:
            return [], list(fields)
        chips = self._inputs[option.key]
        kept: list[str] = []
        dropped: list[str] = []
        for field in fields:
            if field in GROUP_FIELDS and field not in kept:
                kept.append(field)
            elif field not in GROUP_FIELDS:
                dropped.append(field)
        chips.set_fields(kept)
        return kept, dropped

    def set_grouping_notice(self, text: str, *, error: bool = False) -> None:
        notice = getattr(self, "_grouping_notice", None)
        if notice is None:
            return
        # ``bootstyle`` takes a colour name, not a style name: the muted style
        # has to go through ``style=`` (MUTED is a full ttk style).
        if error:
            notice.configure(text=text, bootstyle="danger")
        else:
            notice.configure(text=text, style=MUTED)

    def _copy_grouping(self) -> None:
        if self._on_copy_grouping is not None:
            self._on_copy_grouping()

    # ------------------------------------------------------------------
    # Files the tool reads and writes
    # ------------------------------------------------------------------
    def _build_files_card(self) -> None:
        if not self.tool.reads and not self.tool.writes:
            return
        card = self.card("Files")
        if self.tool.reads:
            ttk.Label(card, text="Reads", style=MUTED).pack(anchor="w")
            for path in self.tool.reads:
                self._file_widgets[path] = self._file_row(card, path)
        if self.tool.writes:
            ttk.Label(card, text="Writes", style=MUTED).pack(anchor="w", pady=(8, 0))
            for path in self.tool.writes:
                ttk.Label(card, text=relative(path), font=("Consolas", 9)).pack(
                    anchor="w"
                )
        ttk.Label(
            card,
            text="Input files are the scanner outputs the Data tab edits; a tool with a file "
            "argument can also be pointed somewhere else.",
            style=MUTED,
            wraplength=680,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))
        self.refresh_files()

    def _file_row(
        self, card: ttk.Labelframe, path: Path
    ) -> tuple[ttk.Label, ttk.Button | None]:
        row = ttk.Frame(card)
        row.pack(fill="x")
        ttk.Label(row, text=relative(path), font=("Consolas", 9)).pack(side="left")
        status = ttk.Label(row, style=MUTED)
        status.pack(side="left", padx=(10, 0))
        open_button = None
        if self._on_open_in_data is not None:
            open_button = button(
                row,
                "Open",
                style="info link",
                command=partial(self._on_open_in_data, path),
                tip=f"Open {relative(path)} in the Data tab",
            )
            open_button.pack(side="right")
        return status, open_button

    def refresh_files(self) -> None:
        """Re-check existence and whether the Data tab has the same file open."""
        active = None
        if self._active_file is not None:
            try:
                active = self._active_file()
            except Exception:  # noqa: BLE001 - display only
                active = None
        for path, (label, open_button) in self._file_widgets.items():
            present = path.exists()
            if not present:
                label.configure(text="missing", bootstyle="danger")
            else:
                marker = (
                    "  ·  open in the Data tab"
                    if active is not None and path.resolve() == active.resolve()
                    else ""
                )
                # ``style=`` (not ``bootstyle=``): MUTED is a style, and passing
                # it as a bootstyle silently falls back to the plain label.
                label.configure(text=f"present{marker}", style=MUTED)
            if open_button is not None:
                open_button.configure(state="normal" if present else "disabled")

    # ------------------------------------------------------------------
    # Command
    # ------------------------------------------------------------------
    def tool_args(self) -> list[str]:
        """Turn the argument widgets into CLI args for ``tool.module``."""
        args: list[str] = []
        for option in self.tool.options:
            widget = self._inputs[option.key]
            if option.kind == BOOL:
                if widget.get():
                    args.append(option.flag)
            elif option.kind == CHOICE:
                value = self._value_maps[option.key].get(widget.get())
                if value is not None:
                    args += [option.flag, value]
            elif option.kind == GROUP:
                if value := widget.value():
                    args += [option.flag, value]
            else:
                if value := widget.get().strip():
                    args += [option.flag, value]
        return args

    def command(self) -> list[str]:
        return [sys.executable, "-m", self.tool.module, *self.tool_args()]

    def validate(self) -> str | None:
        """Return a problem description, or None when the arguments are usable."""
        for option in self.tool.options:
            if option.kind != FILE:
                continue
            raw = self._inputs[option.key].get().strip()
            if not raw:
                continue
            path = Path(raw)
            if not path.is_absolute():
                path = Path_Config.PROJECT_ROOT / path
            if path.is_dir():
                return f"{option.label}: {raw} is a folder, not a file."
            if path.suffix.lower() != ".json":
                return f"{option.label}: expected a .json file, got {path.name}."
            if not path.is_file():
                return f"{option.label}: {raw} does not exist."
        return None

    def missing_inputs(self) -> list[Path]:
        return [path for path in self.tool.reads if not path.is_file()]

    def set_last_run(self, text: str, tag: str = "info") -> None:
        self._last_run.configure(text=text, bootstyle=OUTCOME_STYLE.get(tag, "default"))

    def reset_last_run(self) -> None:
        self._last_run.configure(
            text="No run yet. Its output streams into the log.", style=MUTED
        )

    def _sync_command(self, *_args) -> None:
        """Keep the command preview in step with the argument widgets."""
        self._preview.set(" ".join([Path(sys.executable).name, *self.command()[1:]]))
