"""Context-aware, searchable filters for the Data tab.

The bar is driven by plain :class:`~gui.services.filters.FilterGroup` objects,
so the same widget serves students (school, club, attack, armour), equipment
(type, tier, rarity), items (rarity) and currencies (none). Nothing here knows
about a particular record shape: the Data page decides which groups exist and
this module only presents them.

Each group is a compact button that opens a popup with:

* an optional live search box (it narrows the *options*, never the cards -
  selections survive while the list is filtered),
* ``Select all`` / ``Clear`` shortcuts,
* icon-assisted rows (school crests, equipment artwork, rarity/element
  swatches) and a checkable row that can be toggled anywhere along its width.

Student roles (All / Striker / Special) are an exclusive segmented control, not
a multi-select: exactly one is active at a time.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Sequence

import ttkbootstrap as ttk
from PIL import Image, ImageDraw, ImageFont, ImageTk

from gui import icons
from gui.components.flow import FlowFrame
from gui.components.scroll import WheelRouter
from gui.services.filters import FilterGroup, FilterOption
from gui.services.image_service import ImageService
from gui.ui import MUTED, button, heading

# Rows use one size for every leading picture, so labels line up.
ICON_SIZE = 18
POPUP_WIDTH = 250
POPUP_MAX_HEIGHT = 340
# Short lists are easy to scan; a search box would only add chrome.
POPUP_SEARCH_MIN = 9

ROLE_OPTIONS = (("all", "All"), ("striker", "STRIKER"), ("special", "SPECIAL"))

PALETTE = ("#4d6fa8", "#6a5acd", "#8a5a44", "#4a7d6b", "#8a6d3b", "#7a4d6d")

_swatches: dict[tuple[str, int], ImageTk.PhotoImage] = {}
_glyph_badges: dict[tuple[str, str, int], ImageTk.PhotoImage] = {}
_monograms: dict[tuple[str, int], ImageTk.PhotoImage] = {}


# ---------------------------------------------------------------------------
# Leading pictures
# ---------------------------------------------------------------------------
def option_photo(
    option: FilterOption, images: ImageService | None
) -> ImageTk.PhotoImage | None:
    """The small picture drawn before ``option``'s label (or ``None``)."""
    if option.asset and images is not None:
        # School crests are white glyphs with alpha; tint them with the live
        # theme's foreground so they do not vanish in light mode.
        tint = ttk.Style().colors.fg if option.monochrome else None
        photo = images.local_photo(option.asset, ICON_SIZE, tint=tint)
        if photo is not None:
            return photo
    if option.colour:
        if option.glyph:
            return _glyph_badge(option.colour, option.glyph)
        return _swatch(option.colour)
    if option.asset:
        # Artwork is known but not available locally: a lettered tile keeps the
        # options distinguishable without making the popup wait on the network.
        return _monogram(option.label)
    return None


def _swatch(colour: str) -> ImageTk.PhotoImage:
    key = (colour, ICON_SIZE)
    photo = _swatches.get(key)
    if photo is None:
        image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        _rounded(ImageDraw.Draw(image), colour)
        photo = ImageTk.PhotoImage(image)
        _swatches[key] = photo
    return photo


def _glyph_badge(colour: str, glyph: str) -> ImageTk.PhotoImage:
    key = (colour, glyph, ICON_SIZE)
    photo = _glyph_badges.get(key)
    if photo is not None:
        return photo
    image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    _rounded(ImageDraw.Draw(image), colour)
    icon = icons.type_icon(glyph, size=ICON_SIZE - 5)
    if icon is not None:
        image.alpha_composite(
            icon,
            ((ICON_SIZE - icon.width) // 2, (ICON_SIZE - icon.height) // 2),
        )
    photo = ImageTk.PhotoImage(image)
    _glyph_badges[key] = photo
    return photo


def _monogram(text: str) -> ImageTk.PhotoImage:
    label = _initials(text)
    key = (label, ICON_SIZE)
    photo = _monograms.get(key)
    if photo is not None:
        return photo
    colour = PALETTE[sum(label.encode("utf-8")) % len(PALETTE)]
    image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    _rounded(draw, colour)
    try:
        font = ImageFont.load_default(size=ICON_SIZE - 8)
    except TypeError:  # Pillow < 10.1 has no sized default font
        font = ImageFont.load_default()
    draw.text(
        (ICON_SIZE / 2, ICON_SIZE / 2),
        label,
        font=font,
        fill="#ffffff",
        anchor="mm",
    )
    photo = ImageTk.PhotoImage(image)
    _monograms[key] = photo
    return photo


def _initials(text: str) -> str:
    words = [word for word in str(text).split() if word]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def _rounded(draw: ImageDraw.ImageDraw, colour: str) -> None:
    draw.rounded_rectangle((0, 0, ICON_SIZE - 1, ICON_SIZE - 1), radius=4, fill=colour)


# ---------------------------------------------------------------------------
# One multi-select group
# ---------------------------------------------------------------------------
class MultiSelectDropdown(ttk.Frame):
    """A filter button plus its searchable, multi-select popup."""

    def __init__(
        self,
        master,
        group: FilterGroup,
        *,
        images: ImageService | None,
        on_change: Callable[[], None],
        on_measure: Callable[[], None] | None = None,
    ):
        super().__init__(master)
        self._group = group
        self._images = images
        self._on_change = on_change
        self._on_measure = on_measure
        self._selected: set[str] = set()
        self._popup: tk.Toplevel | None = None
        self._outside_id: str | None = None
        self._escape_id: str | None = None
        self._rows: list[tuple[FilterOption, ttk.Frame]] = []
        self._vars: dict[str, tk.BooleanVar] = {}
        self._search_var = tk.StringVar()
        self._empty: ttk.Label | None = None
        self._list: ttk.Frame | None = None
        self._canvas: tk.Canvas | None = None
        self._header_count: ttk.Label | None = None

        self._button = ttk.Button(
            self,
            text=group.label,
            bootstyle="secondary outline",
            command=self._toggle,
        )
        self._button.pack(fill="x")
        self._sync_button()

    # -- state ---------------------------------------------------------
    @property
    def key(self) -> str:
        return self._group.key

    @property
    def selected(self) -> set[str]:
        return set(self._selected)

    def set_group(self, group: FilterGroup) -> None:
        """Adopt a new option set, keeping selections that still exist."""
        self.close()
        self._group = group
        allowed = {option.value for option in group.options}
        self._selected &= allowed
        self._sync_button()

    def clear(self) -> None:
        self._selected.clear()
        for var in self._vars.values():
            var.set(False)
        self._sync_button()

    def close(self) -> None:
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None
        self._rows.clear()
        self._vars.clear()
        self._header_count = None
        self._empty = None
        self._list = None
        self._canvas = None
        if self._outside_id is not None:
            try:
                self.winfo_toplevel().unbind("<Button-1>", self._outside_id)
            except tk.TclError:
                pass
            self._outside_id = None
        if self._escape_id is not None:
            try:
                self.winfo_toplevel().unbind("<Escape>", self._escape_id)
            except tk.TclError:
                pass
            self._escape_id = None

    # -- button --------------------------------------------------------
    def _sync_button(self) -> None:
        total = len(self._group.options)
        count = len(self._selected)
        if total == 0:
            text, style = f"{self._group.label}: —", "outline"
            state = "disabled"
        elif count == 0 or count == total:
            text, style, state = (
                f"{self._group.label}: All",
                "outline",
                "normal",
            )
        elif count == 1:
            value = next(iter(self._selected))
            label = next(
                (o.label for o in self._group.options if o.value == value), value
            )
            text = f"{self._group.label}: {_shorten(label)}"
            style, state = "info outline", "normal"
        else:
            text = f"{self._group.label}: {count} selected"
            style, state = "info outline", "normal"
        self._button.configure(text=text, bootstyle=style, state=state)
        # The button's requested width follows its caption; the wrapping flow
        # has to re-measure when "School: All" becomes "School: Trinity".
        if self._on_measure is not None:
            self._on_measure()

    # -- popup ---------------------------------------------------------
    def _toggle(self) -> None:
        if self._popup is not None and self._popup.winfo_exists():
            self.close()
        else:
            self._open()

    def _open(self) -> None:
        if not self._group.options:
            return
        self.close()
        self.update_idletasks()
        self._search_var.set("")

        popup = tk.Toplevel(self)
        popup.wm_overrideredirect(True)
        popup.attributes("-topmost", True)
        self._popup = popup

        body = ttk.Frame(popup, padding=(8, 6), relief="solid", borderwidth=1)
        body.pack(fill="both", expand=True)

        header = ttk.Frame(body)
        header.pack(fill="x", pady=(0, 4))
        ttk.Label(header, text=self._group.label, font=heading(9)).pack(side="left")
        self._header_count = ttk.Label(header, style=MUTED)
        self._header_count.pack(side="right")

        searchable = len(self._group.options) >= POPUP_SEARCH_MIN
        if searchable:
            search = ttk.Frame(body)
            search.pack(fill="x", pady=(0, 4))
            ttk.Label(search, image=ttk.Icon("search", 12), style=MUTED).pack(
                side="left", padx=(0, 4)
            )
            entry = ttk.Entry(search, textvariable=self._search_var)
            entry.pack(side="left", fill="x", expand=True)
            entry.bind("<KeyRelease>", lambda _e: self._filter_rows())
            entry.bind("<Return>", lambda _e: self._filter_rows())

        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=(0, 2))
        button(
            actions,
            "Select all",
            "check2-all",
            style="outline",
            command=self._select_all,
            padding=(6, 1),
        ).pack(side="left")
        button(
            actions,
            "Clear",
            "x-circle",
            style="outline",
            command=self._select_none,
            padding=(6, 1),
        ).pack(side="left", padx=(4, 0))

        ttk.Separator(body).pack(fill="x", pady=(4, 2))

        # A canvas keeps the popup a fixed maximum height for long lists.
        host = ttk.Frame(body)
        host.pack(fill="both", expand=True)
        canvas = tk.Canvas(
            host,
            highlightthickness=0,
            borderwidth=0,
            width=POPUP_WIDTH,
            height=min(POPUP_MAX_HEIGHT, len(self._group.options) * 30 + 4),
            background=ttk.Style().colors.bg,
        )
        bar = ttk.Scrollbar(host, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=bar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        bar.grid(row=0, column=1, sticky="ns")
        host.columnconfigure(0, weight=1)
        host.rowconfigure(0, weight=1)

        self._canvas = canvas
        self._list = ttk.Frame(canvas)
        window = canvas.create_window((0, 0), window=self._list, anchor="nw")
        self._list.bind(
            "<Configure>",
            lambda _e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(window, width=max(1, e.width)),
        )
        self._list.columnconfigure(0, weight=1)

        self._build_rows()
        self._empty = ttk.Label(self._list, text="No matches", style=MUTED)
        self._empty.grid(row=len(self._rows), column=0, sticky="w", padx=4, pady=6)
        self._empty.grid_remove()

        router = WheelRouter(canvas, units=2)
        router.attach(canvas)
        router.attach_tree(self._list)

        self._place(popup, body)
        self._filter_rows()
        # Returning "break" also keeps the app's bind_all Escape (stop the
        # scanner) from firing while the popup owns the keyboard focus.
        popup.bind("<Escape>", self._escape_popup)
        # Short lists have no search entry, so focus stays in the main window;
        # this binding makes Escape close the popup from there too.
        self._escape_id = self.winfo_toplevel().bind(
            "<Escape>", self._escape_pressed, add="+"
        )
        # Only this popup's own binding is removed on close (unlike bind_all).
        self._outside_id = self.winfo_toplevel().bind(
            "<Button-1>", self._check_outside, add="+"
        )
        if searchable:
            entry.focus_set()

    def _place(self, popup: tk.Toplevel, body: ttk.Frame) -> None:
        popup.update_idletasks()
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        # Long option captions may ask for more than POPUP_WIDTH; never let the
        # popup itself run off either edge of the screen.
        width = min(screen_w - 16, max(POPUP_WIDTH, body.winfo_reqwidth()))
        height = min(POPUP_MAX_HEIGHT + 120, max(120, body.winfo_reqheight() + 4))
        anchor_x = self._button.winfo_rootx()
        anchor_y = self._button.winfo_rooty() + self._button.winfo_height() + 2
        x = min(max(0, anchor_x), max(0, screen_w - width - 8))
        y = anchor_y
        if y + height > screen_h - 8:
            above = self._button.winfo_rooty() - height - 2
            y = above if above >= 8 else max(8, screen_h - height - 8)
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.lift()

    def _build_rows(self) -> None:
        assert self._list is not None
        self._rows.clear()
        for index, option in enumerate(self._group.options):
            row = ttk.Frame(self._list, padding=(3, 1))
            row.grid(row=index, column=0, sticky="ew", pady=0)
            row.columnconfigure(1, weight=1)

            photo = option_photo(option, self._images)
            if photo is not None:
                ttk.Label(row, image=photo).grid(
                    row=0, column=0, sticky="w", padx=(0, 6)
                )

            var = tk.BooleanVar(value=option.value in self._selected)
            self._vars[option.value] = var
            label = ttk.Label(row, text=option.label, anchor="w")
            label.grid(row=0, column=1, sticky="ew")
            check = ttk.Checkbutton(
                row,
                variable=var,
                bootstyle="success round toggle",
                command=self._changed,
            )
            check.grid(row=0, column=2, sticky="e", padx=(6, 0))

            for widget in (row, label):
                widget.bind(
                    "<Button-1>", lambda _e, v=option.value: self._toggle_value(v)
                )
            self._rows.append((option, row))

    def _changed(self) -> None:
        self._read_vars()
        self._sync_button()
        self._sync_header()
        if self._on_change is not None:
            self._on_change()

    def _toggle_value(self, value: str) -> None:
        var = self._vars.get(value)
        if var is not None:
            var.set(not var.get())
        self._changed()

    def _read_vars(self) -> None:
        self._selected = {value for value, var in self._vars.items() if var.get()}

    def _select_all(self) -> None:
        visible = {option.value for option, _row in self._visible_rows()}
        for value in visible:
            var = self._vars.get(value)
            if var is not None:
                var.set(True)
        self._changed()

    def _select_none(self) -> None:
        visible = {option.value for option, _row in self._visible_rows()}
        for value in visible:
            var = self._vars.get(value)
            if var is not None:
                var.set(False)
        self._changed()

    def _visible_rows(self) -> list[tuple[FilterOption, ttk.Frame]]:
        return [(option, row) for option, row in self._rows if bool(row.grid_info())]

    def _filter_rows(self) -> None:
        """Narrow the visible options; checked values are never changed."""
        query = self._search_var.get().strip().casefold()
        shown = 0
        for option, row in self._rows:
            match = (
                not query
                or query in option.label.casefold()
                or query in option.value.casefold()
            )
            if match:
                row.grid()
                shown += 1
            else:
                row.grid_remove()
        if self._empty is not None:
            if shown:
                self._empty.grid_remove()
            else:
                self._empty.grid()
        self._sync_header()

    def _sync_header(self) -> None:
        if self._header_count is None:
            return
        total = len(self._group.options)
        self._header_count.configure(text=f"{len(self._selected)} of {total} selected")

    def _check_outside(self, event: tk.Event) -> None:
        if self._popup is None or not self._popup.winfo_exists():
            return
        if _inside(self._popup, event) or _inside(self._button, event):
            return
        self.close()

    def _escape_popup(self, _event=None) -> str:
        self.close()
        return "break"

    def _escape_pressed(self, _event=None) -> str | None:
        """Close an open popup before the app's global Escape (stop) runs."""
        if self._popup is None or not self._popup.winfo_exists():
            return None
        return self._escape_popup()


def _inside(widget: tk.Misc, event: tk.Event) -> bool:
    try:
        x, y = widget.winfo_rootx(), widget.winfo_rooty()
        width, height = widget.winfo_width(), widget.winfo_height()
    except tk.TclError:
        return False
    return x <= event.x_root <= x + width and y <= event.y_root <= y + height


def _shorten(text: str, limit: int = 18) -> str:
    return text if len(text) <= limit else f"{text[: limit - 1]}…"


# ---------------------------------------------------------------------------
# The bar
# ---------------------------------------------------------------------------
class FilterBar(ttk.Frame):
    """Role selector, one dropdown per group, a result count and *Clear*."""

    def __init__(
        self,
        master,
        *,
        images: ImageService | None = None,
        on_change: Callable[[], None],
        on_clear: Callable[[], None],
    ):
        super().__init__(master)
        self._images = images
        self._on_change = on_change
        self._on_clear = on_clear
        self._groups: tuple[FilterGroup, ...] = ()
        self._dropdowns: dict[str, MultiSelectDropdown] = {}
        self._role_visible = False
        self._bond_visible = False

        self.columnconfigure(0, weight=1)
        self._flow = FlowFrame(self, spacing=6, row_spacing=4)
        self._flow.grid(row=0, column=0, sticky="ew")

        self._role_frame = ttk.Frame(self._flow)
        ttk.Label(self._role_frame, text="Role", style=MUTED).pack(
            side="left", padx=(0, 4)
        )
        self._role_var = tk.StringVar(value="all")
        for index, (value, label) in enumerate(ROLE_OPTIONS):
            rb_style = None
            if value == "striker":
                rb_style = "Striker.secondary.Toolbutton"
            elif value == "special":
                rb_style = "Special.secondary.Toolbutton"

            rb_kw = {"style": rb_style} if rb_style else {"bootstyle": "toolbutton"}
            ttk.Radiobutton(
                self._role_frame,
                text=label,
                value=value,
                variable=self._role_var,
                command=self._role_changed,
                **rb_kw,
            ).pack(side="left", padx=(0 if index == 0 else 1, 0))

        self._bond_var = tk.BooleanVar(value=False)
        self._bond_check = ttk.Checkbutton(
            self._flow,
            text="Has Bond Gear",
            variable=self._bond_var,
            bootstyle="round toggle",
            command=self._bond_changed,
            padding=(1, 5),
        )

        self._count = ttk.Label(self._flow, style=MUTED)
        self._clear = button(
            self._flow,
            "Clear filters",
            "arrow-counterclockwise",
            style="secondary-outline",
            command=self._on_clear,
            tip="Reset every filter and search (sorting is kept)",
        )
        self._clear.configure(state="disabled")

        self._relayout()

    # -- groups --------------------------------------------------------
    def set_groups(
        self,
        groups: Sequence[FilterGroup],
        *,
        role: bool = False,
        bond_gear: bool = False,
    ) -> None:
        """Show ``groups`` (plus the student-only role / bond-gear controls)."""
        groups = tuple(groups)
        self._role_visible = bool(role)
        self._bond_visible = bool(bond_gear)
        if not role:
            self._role_var.set("all")
        if not bond_gear:
            self._bond_var.set(False)
        if groups != self._groups:
            allowed = {group.key for group in groups}
            for key in list(self._dropdowns):
                if key not in allowed:
                    self._dropdowns.pop(key).destroy()
            ordered: dict[str, MultiSelectDropdown] = {}
            for group in groups:
                dropdown = self._dropdowns.get(group.key)
                if dropdown is None:
                    dropdown = MultiSelectDropdown(
                        self._flow,
                        group,
                        images=self._images,
                        on_change=self._on_change,
                        on_measure=self._flow.refresh,
                    )
                else:
                    dropdown.set_group(group)
                ordered[group.key] = dropdown
            self._dropdowns = ordered
            self._groups = groups
        else:
            for group in groups:
                self._dropdowns[group.key].set_group(group)
        self._relayout()

    def _relayout(self) -> None:
        items: list[tk.Widget] = []
        if self._role_visible:
            items.append(self._role_frame)
        if self._bond_visible:
            items.append(self._bond_check)
        items.extend(self._dropdowns.values())
        items.extend((self._count, self._clear))
        self._flow.set_items(items)
        self._flow.refresh()

    def restyle(self) -> None:
        """Re-measure after a theme change (fonts and padding can change)."""
        self._relayout()

    # -- state ---------------------------------------------------------
    def selection(self) -> dict[str, set[str]]:
        return {
            key: dropdown.selected
            for key, dropdown in self._dropdowns.items()
            if dropdown.selected
        }

    def role(self) -> str:
        return self._role_var.get()

    def set_role(self, role: str) -> None:
        self._role_var.set(role if role in {v for v, _ in ROLE_OPTIONS} else "all")
        self._flow.refresh()

    def bond_gear(self) -> bool:
        """Whether the student filter is limited to students with bond gear."""
        return bool(self._bond_var.get())

    def has_active(self) -> bool:
        return (
            self._role_var.get() != "all"
            or self.bond_gear()
            or any(dropdown.selected for dropdown in self._dropdowns.values())
        )

    def set_count(
        self,
        visible: int,
        total: int,
        noun: str,
        *,
        extra_active: bool = False,
    ) -> None:
        if visible == total:
            text = f"{total} {noun}"
        else:
            text = f"{visible} of {total} {noun}"
        self._count.configure(text=text)
        active = self.has_active() or extra_active
        self._clear.configure(state="normal" if active else "disabled")
        self._flow.refresh()

    def clear(self) -> None:
        """Reset every selection, the role and bond gear (does not re-filter)."""
        self._role_var.set("all")
        self._bond_var.set(False)
        for dropdown in self._dropdowns.values():
            dropdown.clear()
        self._clear.configure(state="disabled")
        self._flow.refresh()

    def close_popups(self) -> None:
        for dropdown in self._dropdowns.values():
            dropdown.close()

    def _role_changed(self) -> None:
        self._flow.refresh()
        self._on_change()

    def _bond_changed(self) -> None:
        self._flow.refresh()
        self._on_change()

    def destroy(self) -> None:
        self.close_popups()
        super().destroy()
