"""A responsive, lazily drawn grid of :class:`AssetCard` widgets.

The grid only presents cards: filtering, sorting and searching happen in
:mod:`gui.panels.data_page`, so a refresh can never show stale or duplicated
rows. ``CardGrid`` adds the parts that are purely about presentation:

* the cards live inside the scrolling canvas (not beside it), so the wheel and
  the scrollbar reach the whole inventory,
* columns follow the viewport width and the block stays centred instead of
  stretching a handful of cards across a wide pane,
* cards are built in batches (an inventory can hold >1000 rows) and the next
  batch is appended when the user scrolls to the bottom or presses *Show more*,
* existing cards are updated in place - selecting or re-sorting never rebuilds
  the page or loses the scroll position.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Iterable

import ttkbootstrap as ttk
from ttkbootstrap.widgets.scrolled import ScrolledFrame

from gui.components.card import (
    CARD_PAD,
    CARD_PAGE,
    CARD_WIDTH,
    AssetCard,
    CardSpec,
    card_palette,
)
from gui.components.scroll import WheelRouter
from gui.components.student_card import StudentCard
from gui.services.image_service import ImageKey, ImageService
from gui.ui import MUTED, button

_CARD_CLASSES = {"student": StudentCard}
_COLUMN_PITCH = CARD_WIDTH + 2 * CARD_PAD


class CardGrid(ttk.Frame):
    """Shows ``CardSpec`` objects as cards, in viewport-sized columns."""

    def __init__(
        self,
        master,
        *,
        images: ImageService,
        on_select: Callable[[str], None] | None = None,
        on_view_changed: Callable[[], None] | None = None,
        page_size: int = CARD_PAGE,
        padding: tuple[int, int] = (10, 10),
    ):
        super().__init__(master)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._images = images
        self._on_select = on_select
        self._on_view_changed = on_view_changed
        self._page_size = max(1, int(page_size))
        self._limit = self._page_size
        self._specs: list[CardSpec] = []
        self._cards: dict[str, AssetCard] = {}
        self._order: list[str] = []
        self._positions: dict[str, tuple[int, int]] = {}
        self._columns = 0
        self._selected: str | None = None
        self._palette: dict[bool, dict[str, str]] | None = None
        self._empty_message = "Nothing loaded yet."
        self._theme: str | None = None
        self._extend_job: str | None = None
        self._notify_job: str | None = None

        self._scroll = ScrolledFrame(self, auto_hide=False, padding=padding)
        self._scroll.grid(row=0, column=0, sticky="nsew")

        # Geometry methods of a ScrolledFrame are delegated to its outer
        # container, so the cards are parented to the content frame itself.
        self._grid = ttk.Frame(self._scroll)
        self._grid.pack(anchor="n")

        self._canvas = getattr(self._scroll, "_canvas", None)
        self._router = WheelRouter(self._scroll, units=3, on_scroll=self._on_scrolled)
        self._router.attach_tree(self._grid)

        if self._canvas is not None:
            self._canvas.bind("<Configure>", self._on_viewport, add="+")
        else:  # pragma: no cover - every ttkbootstrap 2.x has a canvas
            self._scroll.bind("<Configure>", self._on_viewport, add="+")

        self._empty = ttk.Frame(self._grid)
        self._empty_label = ttk.Label(
            self._empty, style=MUTED, wraplength=460, justify="left"
        )
        self._empty_label.pack(anchor="w")
        self._empty_action: Callable[[], None] | None = None
        self._empty_button = button(
            self._empty,
            "Clear filters",
            "arrow-counterclockwise",
            style="secondary outline",
            command=self._run_empty_action,
            tip="Show the whole dataset again",
        )
        self._empty.grid(row=0, column=0, sticky="w", padx=8, pady=8)

        footer = ttk.Frame(self, padding=(12, 2, 12, 8))
        footer.grid(row=1, column=0, sticky="ew")
        self._notice = ttk.Label(footer, style=MUTED)
        self._notice.pack(side="left")
        self._more = button(
            footer,
            "Show more",
            "plus-circle",
            style="secondary outline",
            command=self.show_more,
            tip="Draw the next batch of cards",
        )
        self._more.pack(side="right")
        self._more.configure(state="disabled")

    # ------------------------------------------------------------------
    # Data in
    # ------------------------------------------------------------------
    def set_specs(
        self,
        specs: Iterable[CardSpec],
        *,
        reset: bool = True,
        selected: str | None = None,
    ) -> None:
        """Replace the rows; ``reset`` starts again at the first batch."""
        self._specs = list(specs)
        if reset:
            self._limit = self._page_size
        if selected is not None:
            self._selected = selected
        self.refresh()

    def set_empty_message(
        self, text: str, *, reset: Callable[[], None] | None = None
    ) -> None:
        """Set the text (and optional reset button) for an empty grid.

        ``reset=None`` removes a button left over from the previous dataset;
        the empty state must not offer to clear filters when there is nothing
        to filter.
        """
        self._empty_message = text
        self._empty_action = reset
        if not self._cards:
            self._sync_empty()

    def refresh(self) -> None:
        """Update the drawn cards in place (no full rebuild)."""
        if not self.winfo_exists():
            return
        columns = self._column_count()
        columns_changed = columns != self._columns
        self._columns = columns
        if columns_changed:
            self._positions.clear()

        visible = self._specs[: self._limit]
        wanted = {spec.key: spec for spec in visible}

        for key in list(self._cards):
            if key not in wanted:
                self._cards.pop(key).destroy()
                self._positions.pop(key, None)

        palette = self._palette_for()
        for position, spec in enumerate(visible):
            card = self._cards.get(spec.key)
            if card is None:
                card_class = _CARD_CLASSES.get(spec.kind, AssetCard)
                card = card_class(
                    self._grid,
                    spec,
                    images=self._images,
                    palette=palette[spec.key == self._selected],
                    on_select=(
                        self._card_clicked if self._on_select is not None else None
                    ),
                )
                self._cards[spec.key] = card
                self._router.attach_tree(card)
            else:
                card.update_spec(spec)
                card.set_selected(
                    spec.key == self._selected, palette[spec.key == self._selected]
                )
            self._place(spec.key, card, position, columns)

        self._order = [spec.key for spec in visible]
        self._sync_empty()
        self._sync_footer()
        self._notify()

    # ------------------------------------------------------------------
    # Data out
    # ------------------------------------------------------------------
    @property
    def selected(self) -> str | None:
        return self._selected

    @property
    def visible_count(self) -> int:
        return len(self._cards)

    def image_keys(self) -> list[ImageKey]:
        keys: list[ImageKey] = []
        for card in self._cards.values():
            keys.extend(card.image_keys())
        return keys

    def selected_spec(self) -> CardSpec | None:
        return next((s for s in self._specs if s.key == self._selected), None)

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------
    def select(self, key: str | None) -> None:
        if key == self._selected:
            return
        previous, self._selected = self._selected, key
        palette = self._palette_for()
        if previous in self._cards:
            self._cards[previous].set_selected(False, palette[False])
        if key in self._cards:
            self._cards[key].set_selected(True, palette[True])

    def show_more(self) -> None:
        if self._limit >= len(self._specs):
            return
        self._limit = min(len(self._specs), self._limit + self._page_size)
        self.refresh()

    def reveal(self, key: str) -> None:
        """Load the batch containing ``key`` (the row may be far down)."""
        keys = [spec.key for spec in self._specs]
        if key not in keys:
            return
        index = keys.index(key)
        if index >= self._limit:
            self._limit = min(
                len(keys),
                (index // self._page_size + 1) * self._page_size,
            )
            self.refresh()
        card = self._cards.get(key)
        if card is not None and self._canvas is not None:
            self.after_idle(lambda: self._router.scroll_to_widget(card))

    def scroll_to_top(self) -> None:
        self._router.scroll_to_top()

    # ------------------------------------------------------------------
    # Theme / images
    # ------------------------------------------------------------------
    def reload_images(self) -> None:
        for card in self._cards.values():
            card.reload_images()

    def restyle(self) -> None:
        self._palette = card_palette()
        self._theme = ttk.Style().theme_use()
        palette = self._palette
        for key, card in self._cards.items():
            card.set_palette(palette[key == self._selected])

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _place(self, key: str, card: AssetCard, position: int, columns: int) -> None:
        target = (position // columns, position % columns)
        if self._positions.get(key) == target:
            return
        card.grid(
            row=target[0],
            column=target[1],
            padx=CARD_PAD,
            pady=CARD_PAD,
            sticky="n",
        )
        self._positions[key] = target

    def _sync_empty(self) -> None:
        if self._cards:
            self._empty.grid_remove()
            return
        self._empty_label.configure(text=self._empty_message)
        if self._empty_action is not None:
            self._empty_button.pack(anchor="w", pady=(6, 0))
        else:
            self._empty_button.pack_forget()
        self._empty.grid(
            row=0, column=0, columnspan=max(1, self._columns), sticky="w",
            padx=8, pady=8,
        )  # fmt: skip

    def _run_empty_action(self) -> None:
        if self._empty_action is not None:
            self._empty_action()

    def _sync_footer(self) -> None:
        total = len(self._specs)
        shown = min(self._limit, total)
        if shown < total:
            self._notice.configure(text=f"Showing {shown} of {total}")
            self._more.configure(state="normal")
        else:
            self._notice.configure(text=f"{total} shown" if total else "")
            self._more.configure(state="disabled")

    def _column_count(self) -> int:
        width = 0
        if self._canvas is not None:
            try:
                width = self._canvas.winfo_width()
            except tk.TclError:
                width = 0
        if width <= 1:
            width = self.winfo_width()
        if width <= 1:
            width = 640
        available = max(CARD_WIDTH, width - 2 * CARD_PAD)
        return max(1, min(8, available // _COLUMN_PITCH))

    def _on_viewport(self, _event=None) -> None:
        columns = self._column_count()
        if columns == self._columns:
            return
        self._columns = columns
        self._positions.clear()
        if not self._cards:
            self._sync_empty()
            return
        for position, key in enumerate(self._order):
            card = self._cards.get(key)
            if card is not None:
                self._place(key, card, position, columns)

    def _on_scrolled(self) -> None:
        """Append the next batch when the user reaches the bottom."""
        if len(self._cards) >= len(self._specs) or self._extend_job is not None:
            return
        _first, last = self._router.view_fraction()
        if last >= 0.999:
            self._extend_job = self.after_idle(self._auto_extend)

    def _auto_extend(self) -> None:
        self._extend_job = None
        if self.winfo_exists():
            self.show_more()

    def _palette_for(self) -> dict[bool, dict[str, str]]:
        theme = ttk.Style().theme_use()
        if self._palette is None or theme != self._theme:
            self._palette = card_palette()
            self._theme = theme
        return self._palette

    def _notify(self) -> None:
        if self._on_view_changed is None or self._notify_job is not None:
            return
        self._notify_job = self.after_idle(self._deliver_view_changed)

    def _deliver_view_changed(self) -> None:
        self._notify_job = None
        if self._on_view_changed is not None and self.winfo_exists():
            self._on_view_changed()

    def _card_clicked(self, key: str) -> None:
        self.select(key)
        if self._on_select is not None:
            self._on_select(key)

    def destroy(self) -> None:
        for job in (self._extend_job, self._notify_job):
            if job is not None:
                try:
                    self.after_cancel(job)
                except (tk.TclError, ValueError):
                    pass
        self._extend_job = self._notify_job = None
        super().destroy()
