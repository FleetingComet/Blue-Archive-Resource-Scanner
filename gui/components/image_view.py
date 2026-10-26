"""A fixed-size image slot with a placeholder.

The widget never changes size: while no picture has arrived (or when images are
disabled) it shows the theme's glyph, and swapping in real artwork replaces the
glyph inside the same box. That is what keeps a preview - or any future image
slot - from pushing the surrounding layout around while it loads.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

import ttkbootstrap as ttk
from PIL import ImageTk

from gui import icons
from gui.services.image_service import ImageKey, ImageService, cache_key


class ImageView(ttk.Frame):
    """Square artwork slot of a fixed size, with a glyph placeholder."""

    def __init__(
        self,
        master,
        *,
        images: ImageService,
        size: int = 84,
        placeholder: str = "image",
        on_click: Callable[[], None] | None = None,
    ):
        super().__init__(master, width=size, height=size)
        self.pack_propagate(False)
        self.grid_propagate(False)
        self._images = images
        self._size = max(16, int(size))
        self._placeholder_name = placeholder
        self._asset: str | None = None
        self._fit = icons.FIT_CONTAIN
        self._tint: str | None = None
        self._token = 0
        self._photo: ImageTk.PhotoImage | None = None
        self._key: ImageKey | None = None

        self._placeholder = ttk.Label(
            self, icon=placeholder, icon_size=max(16, self._size // 2), anchor="center"
        )
        self._placeholder.pack(fill="both", expand=True)
        self._picture = ttk.Label(self, anchor="center")
        if on_click is not None:
            for widget in (self, self._placeholder, self._picture):
                widget.bind("<Button-1>", lambda _e: on_click())

    # ------------------------------------------------------------------
    def set_asset(
        self,
        asset: str | None,
        *,
        fit: str = icons.FIT_CONTAIN,
        tint: str | None = None,
    ) -> None:
        """Show ``asset`` (or the placeholder when it is ``None``)."""
        if asset == self._asset and fit == self._fit and tint == self._tint:
            self._request()
            return
        self._asset, self._fit, self._tint = asset, fit, tint
        self._token += 1
        self._photo = None
        self._key = None
        self._picture.pack_forget()
        self._placeholder.pack(fill="both", expand=True)
        self._request()

    def clear(self) -> None:
        self.set_asset(None)

    def reload(self) -> None:
        """Re-resolve the current asset (after an image-mode change)."""
        self._token += 1
        self._photo = None
        self._key = None
        self._picture.pack_forget()
        self._placeholder.pack(fill="both", expand=True)
        self._request()

    def image_keys(self) -> list[ImageKey]:
        return [self._key] if self._key is not None else []

    def destroy(self) -> None:
        # See AssetCard.destroy: release the picture while the main thread owns
        # the widget, not whenever the GC happens to collect this view.
        self._photo = None
        super().destroy()

    # ------------------------------------------------------------------
    def _request(self) -> None:
        asset = self._asset
        self._key = None
        if not asset or not self._images.enabled:
            return
        token = self._token
        self._key = cache_key(asset, self._size, self._fit, self._tint)

        def show(photo: ImageTk.PhotoImage) -> None:
            if token != self._token or not self._alive():
                return
            self._photo = photo
            self._placeholder.pack_forget()
            self._picture.configure(image=photo)
            self._picture.pack(fill="both", expand=True)

        photo = self._images.image(
            asset, self._size, fit=self._fit, tint=self._tint, on_ready=show
        )
        if photo is not None:
            show(photo)

    def _alive(self) -> bool:
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False
