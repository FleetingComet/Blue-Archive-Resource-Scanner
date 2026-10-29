"""About dialog: what this application is, which build is running, the links
that ship with the project, and the third-party dependencies it uses.

A compact modal dialog (the conventional desktop choice) rather than another
tab, since the main notebook is reserved for work. Everything shown here is
read from the project itself - ``pyproject.toml`` for the name/version/
description/links/dependencies and the installed distributions for the
dependency versions and licenses.
"""

from __future__ import annotations

import sys
import tkinter as tk
import webbrowser
from collections.abc import Callable

import ttkbootstrap as ttk
from ttkbootstrap.widgets.scrolled import ScrolledText

from gui import dependencies, metadata
from gui.ui import MONO_FONT, MUTED, button, center_on_parent, heading, local_hotkey
from src.core.paths import Path_Config

ABOUT_HOTKEY_HINT = (
    "F5 scanner · F6 tool · F2 / Esc stop · Ctrl+1/2/3 tabs · Ctrl+, settings"
)


def _row(parent, row: int, label: str, value: str, *, mono: bool = False) -> None:
    ttk.Label(parent, text=label).grid(
        row=row, column=0, sticky="nw", padx=(0, 14), pady=2
    )
    ttk.Label(
        parent,
        text=value,
        font=MONO_FONT if mono else None,
        wraplength=380,
        justify="left",
    ).grid(row=row, column=1, sticky="w", pady=2)


class AboutDialog(ttk.Toplevel):
    """Modal About window. ``on_closed`` runs once it is destroyed."""

    def __init__(
        self,
        parent,
        *,
        on_closed: Callable[[], None],
        on_open_folder: Callable[[str], None],
    ):
        super().__init__(
            title=f"About {metadata.project_display_name()}",
            master=parent,
            transient=parent,
            resizable=(False, False),
        )
        self._on_closed = on_closed
        self._on_open_folder = on_open_folder
        self._license_dialog: LicenseDialog | None = None
        meta = metadata.load()
        self._deps = dependencies.installed()

        body = ttk.Frame(self, padding=(22, 18))
        body.pack(fill="both", expand=True)

        self._build_header(body, meta)
        self._build_details(body, meta)
        self._build_links(body, meta)
        self._build_dependencies(body)
        ttk.Separator(body).pack(fill="x", pady=(14, 10))
        ttk.Label(body, text=ABOUT_HOTKEY_HINT, style=MUTED).pack(anchor="w")

        actions = ttk.Frame(self, padding=(22, 0, 22, 16))
        actions.pack(fill="x")
        button(actions, "Close", "x-lg", command=self.close, tip="Close (Esc)").pack(
            side="right"
        )
        button(
            actions,
            "Config folder",
            "folder2-open",
            command=lambda: self._open_folder("config"),
            tip="Open the configuration folder",
        ).pack(side="right", padx=(0, 6))
        button(
            actions,
            "Project folder",
            "folder2-open",
            command=lambda: self._open_folder("project"),
            tip="Open the project root",
        ).pack(side="right", padx=(0, 6))

        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", local_hotkey(self.close))

        self.update_idletasks()
        self.geometry(f"{max(560, self.winfo_reqwidth())}x{self.winfo_reqheight()}")
        center_on_parent(self, parent)
        self.grab_set()
        self.focus_set()

    # ------------------------------------------------------------------
    # Sections
    # ------------------------------------------------------------------
    def _build_header(self, body, meta) -> None:
        header = ttk.Frame(body)
        header.pack(fill="x")
        ttk.Label(header, icon="radar", icon_size=34, compound="left").pack(
            side="left", padx=(0, 12)
        )
        titles = ttk.Frame(header)
        titles.pack(side="left")
        ttk.Label(titles, text=metadata.project_display_name(), font=heading(15)).pack(
            anchor="w"
        )
        ttk.Label(titles, text=f"Version {meta.version}", style=MUTED).pack(anchor="w")

        ttk.Label(body, text=meta.description, wraplength=500, justify="left").pack(
            anchor="w", pady=(14, 4)
        )
        ttk.Label(
            body,
            text="Automates navigation of the game client and reads the inventory screens "
            "with OCR. It does not modify the game, its files, memory or network traffic.",
            style=MUTED,
            wraplength=500,
            justify="left",
        ).pack(anchor="w")

    def _build_details(self, body, meta) -> None:
        details = ttk.Frame(body)
        details.pack(fill="x", pady=(14, 0))
        details.columnconfigure(1, weight=1)
        rows = [
            ("Package", meta.name),
            (
                "Requires",
                (
                    f"Python {meta.requires_python}"
                    if meta.requires_python
                    else "Python 3"
                ),
            ),
            ("Running on", f"Python {sys.version.split()[0]}"),
            ("Project root", str(Path_Config.PROJECT_ROOT)),
            ("Configuration", str(Path_Config.CONFIG_DIR)),
            ("Output", str(Path_Config.OUTPUT_DIR)),
        ]
        for index, (label, value) in enumerate(rows):
            _row(
                details,
                index,
                label,
                value,
                mono=label in ("Project root", "Configuration", "Output"),
            )

    def _build_links(self, body, meta) -> None:
        repository = metadata.find_url(meta, "repo", "source", "homepage")
        documentation = metadata.find_url(meta, "doc")
        if not repository and not documentation:
            return
        links = ttk.Frame(body)
        links.pack(fill="x", pady=(12, 0))
        ttk.Label(links, text="Links", style=MUTED).pack(side="left", padx=(0, 10))
        if repository:
            button(
                links,
                "Repository",
                "github",
                command=lambda: self._open_url(repository),
                tip=repository,
            ).pack(side="left")
        if documentation:
            button(
                links,
                "Documentation",
                "book",
                command=lambda: self._open_url(documentation),
                tip=documentation,
            ).pack(side="left", padx=(6, 0))

    def _build_dependencies(self, body) -> None:
        card = ttk.Labelframe(
            body, text=f"Dependencies ({len(self._deps)})", padding=(10, 8)
        )
        card.pack(fill="x", pady=(14, 0))
        card.columnconfigure(0, weight=1)

        tree_frame = ttk.Frame(card)
        tree_frame.grid(row=0, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        # A dedicated style keeps this table compact: the tool list sets the
        # global "Treeview" row height to 34 for its icon rows.
        ttk.Style().configure("Dependencies.Treeview", rowheight=24)
        self._dep_tree = ttk.Treeview(
            tree_frame,
            columns=("name", "version", "license"),
            show="headings",
            height=7,
            selectmode="browse",
            style="Dependencies.Treeview",
        )
        for name, title, width in (
            ("name", "Package", 190),
            ("version", "Version", 90),
            ("license", "License", 190),
        ):
            self._dep_tree.heading(name, text=title)
            self._dep_tree.column(name, width=width, stretch=name == "license")
        scroll = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self._dep_tree.yview
        )
        self._dep_tree.configure(yscrollcommand=scroll.set)
        self._dep_tree.grid(row=0, column=0, sticky="ew")
        scroll.grid(row=0, column=1, sticky="ns")
        self._dep_rows: list[str] = []
        for dep in self._deps:
            iid = self._dep_tree.insert(
                "", "end", values=(dep.name, dep.version, dep.license)
            )
            self._dep_rows.append(iid)
        self._dep_tree.bind("<Double-Button-1>", lambda _e: self._show_license())
        self._dep_tree.bind("<Return>", lambda _e: self._show_license())

        actions = ttk.Frame(card)
        actions.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        button(
            actions,
            "Show license",
            "journal-text",
            command=self._show_license,
            tip="Show the license of the selected dependency",
        ).pack(side="left")
        ttk.Label(
            actions,
            text="Select a dependency (or double-click it) to read its license.",
            style=MUTED,
        ).pack(side="left", padx=(10, 0))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _open_folder(self, key: str) -> None:
        self._on_open_folder(key)

    def _open_url(self, url: str) -> None:
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001, S110
            # a missing browser must not crash the dialog
            pass

    def _show_license(self) -> None:
        # One license window at a time: re-focus it instead of stacking another.
        if self._license_dialog is not None and self._license_dialog.winfo_exists():
            self._license_dialog.lift()
            self._license_dialog.focus_force()
            return
        selection = self._dep_tree.selection()
        if not selection:
            return
        index = self._dep_rows.index(selection[0])
        if not (0 <= index < len(self._deps)):
            return
        self._license_dialog = LicenseDialog(
            self, self._deps[index], on_closed=self._license_closed
        )

    def _license_closed(self) -> None:
        self._license_dialog = None

    def close(self) -> None:
        if self._license_dialog is not None and self._license_dialog.winfo_exists():
            self._license_dialog.close()
        self.grab_release()
        self.destroy()
        self._on_closed()


class LicenseDialog(ttk.Toplevel):
    """The selected dependency's license: name, summary and bundled text.

    A package may ship several license files (e.g. per bundled component); the
    drop-down picks which one is shown. It holds its own grab so the About
    window behind it cannot be used to open a second copy, and hands the grab
    back when it closes.
    """

    def __init__(self, parent, dependency: dependencies.Dependency, *, on_closed=None):
        super().__init__(
            title=f"License - {dependency.name}", master=parent, transient=parent
        )
        self.minsize(560, 400)
        self._licenses = dependency.licenses
        self._parent = parent
        self._on_closed = on_closed

        body = ttk.Frame(self, padding=(16, 12))
        body.pack(fill="both", expand=True)
        ttk.Label(body, text=dependency.name, font=heading(12)).pack(anchor="w")
        ttk.Label(
            body,
            text=f"Version {dependency.version} · {dependency.license}",
            style=MUTED,
        ).pack(anchor="w")
        if dependency.summary:
            ttk.Label(
                body, text=dependency.summary, wraplength=600, justify="left"
            ).pack(anchor="w", pady=(6, 0))

        if len(self._licenses) > 1:
            picker = ttk.Frame(body)
            picker.pack(fill="x", pady=(10, 0))
            ttk.Label(picker, text=f"License files ({len(self._licenses)})").pack(
                side="left"
            )
            self._choice = tk.StringVar(value=self._licenses[0].name)
            combo = ttk.Combobox(
                picker,
                textvariable=self._choice,
                values=[item.name for item in self._licenses],
                state="readonly",
            )
            combo.pack(side="left", fill="x", expand=True, padx=(8, 0))
            combo.bind("<<ComboboxSelected>>", lambda _e: self._show_selected())
        else:
            self._choice = None

        self._text = ScrolledText(body, auto_hide=True, hbar=True, height=15)
        self._text.pack(fill="both", expand=True, pady=(10, 0))
        self._text.text.configure(wrap="word", font=MONO_FONT)

        if self._licenses:
            self._show_selected()
        else:
            self._set_text(
                f"No license file is bundled with {dependency.name}.\n"
                f"Declared license: {dependency.license}"
            )

        actions = ttk.Frame(self, padding=(16, 0, 16, 14))
        actions.pack(fill="x")
        button(actions, "Close", "x-lg", command=self.close, tip="Close (Esc)").pack(
            side="right"
        )
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", local_hotkey(self.close))

        self.update_idletasks()
        height = min(680, max(400, self.winfo_reqheight()))
        self.geometry(f"600x{height}")
        center_on_parent(self, parent)
        self.grab_set()
        self.focus_set()

    def close(self) -> None:
        """Close, then hand the grab back to the About window behind it."""
        try:
            self.grab_release()
            self.destroy()
        except tk.TclError:  # already gone
            pass
        parent = self._parent
        if parent is not None:
            try:
                if parent.winfo_exists():
                    parent.grab_set()
            except tk.TclError:
                pass
        self._parent = None
        if self._on_closed is not None:
            self._on_closed()

    def _show_selected(self) -> None:
        name = (
            self._choice.get() if self._choice is not None else self._licenses[0].name
        )
        item = next(
            (entry for entry in self._licenses if entry.name == name), self._licenses[0]
        )
        self._set_text(item.text)

    def _set_text(self, content: str) -> None:
        self._text.text.configure(state="normal")
        self._text.text.delete("1.0", "end")
        self._text.text.insert("1.0", content)
        self._text.text.configure(state="disabled")


def show_about(parent, *, on_closed: Callable[[], None], on_open_folder) -> None:
    """Open the About dialog unless one is already up (see ``app``)."""
    AboutDialog(parent, on_closed=on_closed, on_open_folder=on_open_folder)


__all__ = ["AboutDialog", "LicenseDialog", "show_about"]
