"""One card: the artwork, corner badges, name, detail line and chips.

The Data tab draws an inventory as cards, mirroring the HTML report
(``tools/html.py``). A card is a single ``tk.Canvas`` - one widget instead of a
dozen - so a page of them is cheap to build, and it can place the badges exactly
where the report does.

``AssetCard`` owns its own presentation: it is given a :class:`CardSpec` (plain
data, built by the Data tab from the scanned record) and an
:class:`~gui.services.image_service.ImageService`, and it renders itself. It is
never rebuilt to show new data: ``update_spec``/``set_palette`` redraw the same
widget, which keeps the grid geometry and the scroll position stable.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import font as tkfont

import ttkbootstrap as ttk
from PIL import ImageTk

from gui import icons
from gui.services.image_service import ImageKey, ImageService, cache_key

# A card is one canvas, but drawing a whole inventory is still expensive; the
# rest are revealed with "Show more".
CARD_PAGE = 120
CARD_WIDTH = 172
# Only a fallback: a card is as tall as its own content (see ``_render``), so a
# one-line item does not keep a student-sized empty band under its name.
CARD_HEIGHT = 250
CARD_PAD = 8
CARD_RADIUS = 10
CARD_THUMB = CARD_WIDTH - 2 * CARD_PAD
CARD_INNER = CARD_WIDTH - 2 * CARD_PAD
THUMB_RADIUS = 8
EMBLEM_SIZE = 16

# Geometry inside a card, matching the HTML report's card (thumbnail on top,
# name, school line, chips underneath). Everything below the thumbnail is a
# stack: each line starts where the previous one ended, so the gaps are the same
# whatever the name wraps to.
THUMB_LEFT = CARD_PAD
THUMB_TOP = CARD_PAD
THUMB_RIGHT = THUMB_LEFT + CARD_THUMB
THUMB_BOTTOM = THUMB_TOP + CARD_THUMB
THUMB_CENTRE = ((THUMB_LEFT + THUMB_RIGHT) / 2, (THUMB_TOP + THUMB_BOTTOM) / 2)
BADGE_INSET = 4
NAME_GAP = 7  # thumbnail bottom -> name
DETAIL_GAP = 3  # name -> detail line (school / category / id)
CHIP_GAP = 5  # between chips, and before the first one
CHIP_ROW_GAP = 4  # between chip rows (wide type chips may not fit on one)
CHIP_HEIGHT = 17
CHIP_PAD = 6  # left/right padding inside a chip
CHIP_ICON = 11  # the attack/defence glyph inside its chip
CHIP_ICON_GAP = 3  # glyph -> chip text
NOTE_GAP = 5  # detail text -> the small note tag
NOTE_PAD = 5  # left/right padding inside the note tag
NOTE_ICON = 10  # a small glyph inside the note tag (the bond gear heart)
NOTE_ICON_GAP = 3  # note glyph -> its text
BOTTOM_PAD = 9  # empty space under the last line

# Stand-in glyph, shown until (or instead of) the real artwork arrives.
CARD_GLYPHS = {"student": "person-fill", "item": "box-seam-fill", "currency": "coin"}
DEFAULT_GLYPH = "box-seam-fill"

# Badges sit on top of the artwork, mirroring the HTML report's thumbnails.
BADGE_BG = "#141821"


@dataclass(frozen=True)
class Chip:
    """A small pill under the detail line (attack/armour type).

    ``icon`` names a bundled glyph (``"attack"`` / ``"defense"``) that is drawn
    before the text; ``None`` keeps the chip text-only.
    """

    text: str
    background: str
    foreground: str
    icon: str | None = None


@dataclass(frozen=True)
class CardSpec:
    """Everything one card needs to draw itself - no widgets, no I/O."""

    key: str  # stable id, shared with the selected row
    name: str  # the primary line: student name, item name, currency key
    kind: str = "item"  # "student" | "item" | "equipment" | "currency"
    # The muted line under the name: a student's school, an equipment
    # category/tier, an item id (blank hides it).
    detail: str = ""
    # Optional small tag drawn after ``detail`` on the same line.  Students use
    # it for the Bond Gear tier (a heart plus ``T<n>``); keeping it out of
    # ``chips`` stops that extra pill from wrapping the attack/armour chips onto
    # a second row.
    note: str = ""
    note_icon: str = ""  # bundled glyph drawn before the note text
    note_icon_colour: str = ""
    note_background: str = ""
    note_foreground: str = ""
    glyph: str = DEFAULT_GLYPH
    asset: str | None = None
    fit: str = icons.FIT_CONTAIN
    tint: str | None = None
    thumb_bg: str | None = None  # rarity-coloured backdrop behind the artwork
    emblem: str | None = None
    badges: tuple[tuple[str, str, str], ...] = ()
    stars: tuple[object, object] | None = None
    chips: tuple[Chip, ...] = ()
    quantity: object = None
    search: str = ""


def card_palette() -> dict[bool, dict[str, str]]:
    """The card colours for the live theme (cards are drawn, so plain hexes).

    Both states share the same ``muted``/``fg`` colours on purpose: the
    artwork, the placeholder glyph and the school emblem are tinted with them,
    so selecting a card must not change the tint (that would force a re-load of
    those pictures and make them blink out while the new colour is produced).
    """
    colours = ttk.Style().colors
    surface = _blend(colours.bg, colours.fg, 0.08)
    chosen = _blend(surface, colours.info, 0.35)
    muted = _blend(surface, colours.fg, 0.62)
    return {
        False: {
            "page": colours.bg,
            "surface": surface,
            "border": colours.border,
            "fg": colours.fg,
            "muted": muted,
        },
        True: {
            "page": colours.bg,
            "surface": chosen,
            "border": colours.info,
            "fg": colours.fg,
            "muted": muted,
        },
    }


class AssetCard(ttk.Frame):
    def __init__(
        self,
        master,
        spec: CardSpec,
        *,
        images: ImageService,
        palette: dict[str, str],
        on_select: Callable[[str], None] | None = None,
        on_scroll: Callable[[tk.Event], None] | None = None,
    ):
        super().__init__(master, width=CARD_WIDTH, height=CARD_HEIGHT)
        self._height = CARD_HEIGHT
        self.pack_propagate(False)
        self.grid_propagate(False)
        self._images = images
        self._on_select = on_select
        self._on_scroll = on_scroll
        self._spec = spec
        self._palette = palette
        self._selected = False
        self._card_item: int | None = None
        self._image_token = 0
        self._emblem_token = 0
        # Canvas items only keep the Tk *name* of a picture. Hold the Python
        # object too: the service may prune its cache (``retain``) while this
        # card still shows the picture, and a collected PhotoImage leaves the
        # item blank. That is what hid the school crests after a few redraws.
        self._image_photo: ImageTk.PhotoImage | None = None
        self._emblem_photo: ImageTk.PhotoImage | None = None
        self._keys: list[ImageKey] = []

        self._canvas = tk.Canvas(
            self,
            width=CARD_WIDTH,
            height=CARD_HEIGHT,
            background=palette["page"],
            highlightthickness=0,
            borderwidth=0,
        )
        self._canvas.pack(fill="both", expand=True)
        self._canvas.bind("<Button-1>", self._clicked)
        self._canvas.bind("<Enter>", lambda _e: self.configure(cursor="hand2"))
        self._canvas.bind("<Leave>", lambda _e: self.configure(cursor=""))

        # Forward mousewheel events so scrolling works over cards
        if on_scroll is not None:
            for w in (self, self._canvas):
                w.bind("<MouseWheel>", on_scroll)
                w.bind("<Button-4>", on_scroll)
                w.bind("<Button-5>", on_scroll)

        self._render()

    # -- data --------------------------------------------------------------
    @property
    def spec(self) -> CardSpec:
        return self._spec

    def update_spec(self, spec: CardSpec) -> None:
        """Show ``spec`` without recreating the widget."""
        if spec == self._spec:
            return
        self._spec = spec
        self._render()

    def image_keys(self) -> list[ImageKey]:
        """The pictures this card currently displays (for the service cache)."""
        return list(self._keys)

    def destroy(self) -> None:
        # A canvas item keeps only the Tk *name* of its picture, so these are
        # the only Python references. Release them while the main thread is
        # tearing the widget down: a card that is merely collected would drop
        # them whenever the GC happens to run, possibly on an image worker.
        self._image_photo = None
        self._emblem_photo = None
        super().destroy()

    def set_selected(self, selected: bool, palette: dict[str, str]) -> None:
        """Highlight/unhighlight in place.

        Only the surface and its border change between the two palettes (the
        tint, text and chips are shared), so a selection is a couple of canvas
        item updates instead of a full redraw - which also keeps the artwork
        from being re-requested and briefly vanishing.
        """
        if selected == self._selected and palette == self._palette:
            return
        self._selected = selected
        self._palette = palette
        if self._card_item is not None and _alive(self._canvas):
            self._canvas.itemconfigure(
                self._card_item,
                fill=palette["surface"],
                outline=palette["border"],
            )
            return
        self._render()

    def set_palette(self, palette: dict[str, str]) -> None:
        """Re-render after a theme switch (the palette holds the new colours)."""
        if palette == self._palette:
            return
        self._palette = palette
        self._render()

    def reload_images(self) -> None:
        """Re-resolve the artwork (after an image-mode or visibility change)."""
        self._render()

    def destroy(self) -> None:
        # A late load must not touch a dead canvas.
        self._image_token += 1
        self._emblem_token += 1
        self._keys = []
        super().destroy()

    # -- drawing -----------------------------------------------------------
    def _render(self) -> None:
        canvas = self._canvas
        canvas.delete("all")
        self._keys = []
        self._image_photo = None
        self._emblem_photo = None
        colours = self._palette
        spec = self._spec
        canvas.configure(background=colours["page"])

        self._card_item = _round_rect(
            canvas, 0, 0, CARD_WIDTH - 1, self._height - 1, CARD_RADIUS,
            fill=colours["surface"], outline=colours["border"], tags=("surface",),
        )  # fmt: skip

        self._thumb_item: int | None = None
        if spec.thumb_bg:
            # The rarity colour sits *behind* the artwork: icons are
            # transparent, so this is what colours the icon tile. The artwork
            # is raised just above it (see ``_load_art``) and the badges stay
            # on top.
            self._thumb_item = _round_rect(
                canvas, THUMB_LEFT, THUMB_TOP, THUMB_RIGHT, THUMB_BOTTOM,
                THUMB_RADIUS, fill=spec.thumb_bg, outline="",
            )  # fmt: skip

        self._glyph = _glyph_icon(spec.glyph, CARD_THUMB // 3, colours["muted"])

        self._placeholder: int | None = canvas.create_image(
            THUMB_CENTRE[0], THUMB_CENTRE[1], image=self._glyph
        )
        self._image_item: int | None = None
        self._emblem_item: int | None = None

        for place, text, colour in spec.badges:
            self._draw_badge(place, text, colour)

        if spec.stars is not None:
            self._draw_stars(spec.stars)

        name_font = self._name_font()
        name = _fit_lines(str(spec.name), name_font, CARD_INNER, 2)
        name_top = THUMB_BOTTOM + NAME_GAP
        canvas.create_text(
            CARD_WIDTH / 2, name_top, text=name, font=name_font, fill=colours["fg"],
            justify="center", anchor="n", tags=("fg",),
        )  # fmt: skip
        # The blocks below the thumbnail are a stack: each one starts where the
        # previous one really ended, so a one-line name does not reserve a
        # second line (which used to leave a blank band above the detail).
        cursor = name_top + (name.count("\n") + 1) * name_font.metrics("linespace")

        detail = str(spec.detail or "")
        note = str(spec.note or "")
        if detail or spec.emblem or note:
            small = self._small_font()
            line_height = small.metrics("linespace")
            detail_width = small.measure(detail) if detail else 0
            emblem_width = EMBLEM_SIZE + 5 if spec.emblem else 0
            note_photo = None
            note_icon_width = 0
            if note and spec.note_icon:
                note_photo = _note_icon(
                    spec.note_icon,
                    NOTE_ICON,
                    spec.note_icon_colour or colours["fg"],
                )
                if note_photo is not None:
                    note_icon_width = NOTE_ICON + NOTE_ICON_GAP
            note_width = (
                small.measure(note) + 2 * NOTE_PAD + note_icon_width if note else 0
            )
            note_gap = NOTE_GAP if note and (detail or spec.emblem) else 0
            left = (
                CARD_WIDTH - emblem_width - detail_width - note_gap - note_width
            ) / 2
            detail_top = cursor + DETAIL_GAP
            if spec.emblem:
                self._load_school_emblem(spec.emblem, left, detail_top, colours["fg"])
            if detail:
                canvas.create_text(
                    left + emblem_width, detail_top, text=detail, font=small,
                    fill=colours["muted"], anchor="nw", tags=("muted",),
                )  # fmt: skip
            if note:
                note_left = left + emblem_width + detail_width + note_gap
                note_height = line_height + 2  # 1 px of padding above/below the text
                note_top = detail_top - 1
                _round_rect(
                    canvas, note_left, note_top, note_left + note_width,
                    note_top + note_height, 3,
                    fill=spec.note_background or colours["surface"], outline="",
                )  # fmt: skip
                text_x = note_left + NOTE_PAD
                if note_photo is not None:
                    canvas.create_image(
                        text_x + NOTE_ICON / 2,
                        note_top + note_height / 2,
                        image=note_photo,
                        anchor="center",
                    )
                    text_x += note_icon_width
                canvas.create_text(
                    text_x, note_top + note_height / 2, text=note,
                    font=small, fill=spec.note_foreground or colours["fg"], anchor="w",
                )  # fmt: skip
            cursor = detail_top + line_height

        if spec.chips:
            small = self._small_font()
            photos = {
                chip.icon: _chip_photo(chip.icon) for chip in spec.chips if chip.icon
            }
            widths = [
                small.measure(chip.text)
                + 2 * CHIP_PAD
                + (CHIP_ICON + CHIP_ICON_GAP if photos.get(chip.icon) else 0)
                for chip in spec.chips
            ]
            top = cursor + CHIP_GAP
            rows = _chip_rows(widths, CARD_INNER, CHIP_GAP)
            for number, row in enumerate(rows):
                total = sum(widths[index] for index in row) + CHIP_GAP * (len(row) - 1)
                x = (CARD_WIDTH - total) / 2
                for index in row:
                    chip = spec.chips[index]
                    self._draw_chip(
                        chip, photos.get(chip.icon), x, top, widths[index], small
                    )
                    x += widths[index] + CHIP_GAP
                top += CHIP_HEIGHT
                if number < len(rows) - 1:
                    top += CHIP_ROW_GAP
            cursor = top

        self._resize(round(cursor + BOTTOM_PAD))
        self._load_art()

    def _draw_chip(self, chip, photo, x: float, top: float, width: int, font) -> None:
        """One pill: an optional type glyph, then the text."""
        _round_rect(
            self._canvas, x, top, x + width, top + CHIP_HEIGHT, 4,
            fill=chip.background, outline="",
        )  # fmt: skip
        text_x = x + CHIP_PAD
        if photo is not None:
            self._canvas.create_image(
                text_x + CHIP_ICON / 2,
                top + CHIP_HEIGHT / 2,
                image=photo,
                anchor="center",
            )
            text_x += CHIP_ICON + CHIP_ICON_GAP
        self._canvas.create_text(
            text_x, top + CHIP_HEIGHT / 2, text=chip.text, font=font,
            fill=chip.foreground, anchor="w",
        )  # fmt: skip

    def _badge_box(
        self, place: str, width: int, height: int
    ) -> tuple[float, float, float, float]:
        """The rectangle of a corner badge inside the thumbnail."""
        left, top = THUMB_LEFT + BADGE_INSET, THUMB_TOP + BADGE_INSET
        if place == "tl":
            x, y = left, top
        elif place == "tr":
            x, y = THUMB_RIGHT - BADGE_INSET - width, top
        elif place == "bl":
            x, y = left, THUMB_BOTTOM - BADGE_INSET - height
        else:
            x, y = (
                THUMB_RIGHT - BADGE_INSET - width,
                THUMB_BOTTOM - BADGE_INSET - height,
            )
        return x, y, x + width, y + height

    def _draw_badge(self, place: str, text: str, background: str) -> None:
        font = self._badge_font()
        width = font.measure(text) + 12
        height = font.metrics("linespace") + 3
        box = self._badge_box(place, width, height)
        # The rim keeps a rarity badge readable when it shares the tile colour.
        _round_rect(self._canvas, *box, 5, fill=background, outline=BADGE_BG, width=1)
        self._canvas.create_text(
            (box[0] + box[2]) / 2, (box[1] + box[3]) / 2,
            text=text, font=font, fill="#ffffff",
        )  # fmt: skip

    def _draw_stars(self, stars: tuple[object, object]) -> None:
        try:
            star_val = int(stars[0]) if stars[0] is not None else 1
            ue_val = int(stars[1]) if stars[1] is not None else 0
        except (TypeError, ValueError):
            return

        gold_count = max(1, min(5, star_val))
        ue_count = max(0, min(5, ue_val))

        # In-game logic: UE ranks convert gold stars into blue stars on a 5-star baseline
        if ue_count > 0:
            total_stars = 5
            blue_stars = ue_count
        else:
            total_stars = gold_count
            blue_stars = 0

        star_size = 11
        gap = 2
        pad_x = 5
        pad_y = 3

        badge_w = total_stars * star_size + (total_stars - 1) * gap + 2 * pad_x
        badge_h = star_size + 2 * pad_y
        box = self._badge_box("tr", badge_w, badge_h)

        # Draw rounded badge background
        _round_rect(self._canvas, *box, 5, fill=BADGE_BG, outline="")

        cy = (box[1] + box[3]) / 2
        x = box[0] + pad_x + star_size / 2

        # Draw blue stars first (UE rank), then remaining gold stars
        for i in range(total_stars):
            is_blue = i < blue_stars
            icon = _get_star_glyph(size=star_size, is_blue=is_blue)
            self._canvas.create_image(x, cy, image=icon, anchor="center")
            x += star_size + gap

    def _load_art(self) -> None:
        """Swap the stand-in glyph for the real artwork once it is available."""
        self._image_token += 1
        token = self._image_token
        asset = self._spec.asset
        if not asset:
            return
        key = cache_key(asset, CARD_THUMB, self._spec.fit, self._spec.tint)
        self._keys.append(key)

        def show(photo: ImageTk.PhotoImage) -> None:
            if token != self._image_token or not _alive(self._canvas):
                return
            self._image_photo = photo
            if self._image_item is not None:
                self._canvas.delete(self._image_item)
            self._image_item = self._canvas.create_image(
                THUMB_CENTRE[0], THUMB_CENTRE[1], image=photo
            )
            # Above the rarity backdrop, below the badges drawn later.
            self._canvas.tag_raise(
                self._image_item, self._thumb_item or self._card_item
            )
            if self._placeholder is not None:
                self._canvas.itemconfigure(self._placeholder, state="hidden")
                self._placeholder = None

        photo = self._images.image(
            asset, CARD_THUMB, fit=self._spec.fit, tint=self._spec.tint, on_ready=show
        )
        if photo is not None:
            show(photo)

    def _load_school_emblem(self, asset: str, x: float, top: float, tint: str) -> None:
        """Fill a small school crest slot (tinted: the art is a white glyph)."""
        self._emblem_token += 1
        token = self._emblem_token
        self._keys.append(cache_key(asset, EMBLEM_SIZE, tint=tint))
        centre = top + self._small_font().metrics("linespace") / 2

        def show(photo: ImageTk.PhotoImage) -> None:
            if token != self._emblem_token or not _alive(self._canvas):
                return
            self._emblem_photo = photo
            if self._emblem_item is not None:
                self._canvas.delete(self._emblem_item)
            self._emblem_item = self._canvas.create_image(
                x, centre, image=photo, anchor="w"
            )

        photo = self._images.image(asset, EMBLEM_SIZE, tint=tint, on_ready=show)
        if photo is not None:
            show(photo)

    # -- fonts (created once: fonts need a running Tk root) ----------------
    def _name_font(self):
        return _card_font(10, "bold")

    def _small_font(self):
        return _card_font(8)

    def _badge_font(self):
        return _card_font(8, "bold")

    def _resize(self, height: int) -> None:
        """Fit the card (and its border) to the text it actually drew."""
        if height == self._height:
            return
        self._height = height
        self.configure(width=CARD_WIDTH, height=height)
        if not _alive(self._canvas):
            return
        self._canvas.configure(height=height)
        if self._card_item is not None:
            self._canvas.coords(
                self._card_item,
                *_rect_points(0, 0, CARD_WIDTH - 1, height - 1, CARD_RADIUS),
            )

    # -- events ------------------------------------------------------------
    def _clicked(self, _event=None) -> None:
        if self._on_select is not None:
            self._on_select(self._spec.key)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_fonts: dict[tuple[int, str], tkfont.Font] = {}


def _card_font(size: int, weight: str = "normal") -> tkfont.Font:
    """A cached font on the theme's UI family (cards measure text with it)."""
    key = (size, weight)
    font = _fonts.get(key)
    if font is None:
        family = tkfont.nametofont("TkDefaultFont").actual("family")
        font = tkfont.Font(family=family, size=size, weight=weight)
        _fonts[key] = font
    return font


# Cached Bootstrap Icon glyphs for gold and blue (UE) stars
_star_icons: dict[tuple[int, str], object] = {}

STAR_GOLD_COLOR = "#ffee3f"
STAR_BLUE_COLOR = "#45c4ff"


def _get_star_glyph(size: int = 11, is_blue: bool = False) -> object:
    """Return a cached ttk.Icon for 'star-fill' in gold or UE cyan-blue."""
    color = STAR_BLUE_COLOR if is_blue else STAR_GOLD_COLOR
    key = (size, color)
    icon = _star_icons.get(key)
    if icon is None:
        icon = ttk.Icon("star-fill", size, color=color)
        _star_icons[key] = icon
    return icon


# Chip glyphs are shared too (the same two pictures on every student card).
_chip_photos: dict[tuple[str, int], ImageTk.PhotoImage] = {}


def _chip_photo(icon: str) -> ImageTk.PhotoImage | None:
    key = (icon, CHIP_ICON)
    photo = _chip_photos.get(key)
    if photo is None:
        glyph = icons.type_icon(icon, size=CHIP_ICON)
        if glyph is None:
            return None
        photo = ImageTk.PhotoImage(glyph)
        _chip_photos[key] = photo
    return photo


# Stand-in glyphs are shared between cards (and across redraws): creating a
# Tk image per card is measurable on a page of 120 of them.
_glyph_icons: dict[tuple[str, int, str], object] = {}


def _glyph_icon(name: str, size: int, colour: str):
    key = (name, size, colour)
    icon = _glyph_icons.get(key)
    if icon is None:
        icon = ttk.Icon(name, size, color=colour)
        _glyph_icons[key] = icon
    return icon


# The small heart on the bond-gear tag, shared by every student card.
_note_icons: dict[tuple[str, int, str], object] = {}


def _note_icon(name: str, size: int, colour: str):
    key = (name, size, colour)
    icon = _note_icons.get(key)
    if icon is None:
        icon = ttk.Icon(name, size, color=colour)
        _note_icons[key] = icon
    return icon


def _chip_rows(widths: list[int], width: int, gap: int) -> list[list[int]]:
    """Split chip indices into rows that fit inside ``width`` px."""
    rows: list[list[int]] = []
    current: list[int] = []
    used = 0
    for index, chip_width in enumerate(widths):
        extra = chip_width + (gap if current else 0)
        if current and used + extra > width:
            rows.append(current)
            current, used = [index], chip_width
            continue
        current.append(index)
        used += extra
    if current:
        rows.append(current)
    return rows


def _alive(widget) -> bool:
    """Whether a Tk widget still exists (a background fetch may outlive it)."""
    try:
        return bool(widget.winfo_exists())
    except tk.TclError:
        return False


def _blend(first: str, second: str, amount: float) -> str:
    """Mix two ``#rrggbb`` colours; ``amount`` is the share of ``second``."""
    try:
        left = [int(first[index : index + 2], 16) for index in (1, 3, 5)]
        right = [int(second[index : index + 2], 16) for index in (1, 3, 5)]
    except (TypeError, ValueError, IndexError):
        return first
    return "#" + "".join(
        f"{round(a + (b - a) * amount):02x}" for a, b in zip(left, right)
    )


def _rect_points(x1, y1, x2, y2, radius: int) -> tuple[float, ...]:
    """The smoothed polygon a rounded rectangle is drawn from."""
    return (
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    )  # fmt: skip


def _round_rect(canvas: tk.Canvas, x1, y1, x2, y2, radius: int, **options) -> int:
    """A rounded rectangle on a canvas (Tk only ships sharp ones)."""
    return canvas.create_polygon(
        _rect_points(x1, y1, x2, y2, radius), smooth=True, **options
    )


def _fit_lines(text: str, font, width: int, max_lines: int) -> str:
    """Wrap ``text`` to ``width`` px, trimming it to ``max_lines`` lines."""
    rows: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if not current or font.measure(candidate) <= width:
            current = candidate
            continue
        rows.append(current)
        current = word
    if current:
        rows.append(current)
    if len(rows) <= max_lines:
        return "\n".join(rows)
    rows = rows[:max_lines]
    last = rows[-1]
    while last and font.measure(f"{last}…") > width:
        last = last[:-1]
    rows[-1] = f"{last.rstrip()}…"
    return "\n".join(rows)
