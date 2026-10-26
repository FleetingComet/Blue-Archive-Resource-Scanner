"""Reusable GUI components.

- ``card`` - ``CardSpec`` + ``AssetCard``: one entry drawn on a single canvas.
- ``student_card`` - ``StudentCard``: the student-specific card.
- ``card_grid`` - ``CardGrid``: a responsive, paged grid that updates in place.
- ``file_selector`` - ``FileSelector``: path entry with Browse/Clear.
- ``image_view`` - ``ImageView``: a fixed image slot with a placeholder.
"""

from __future__ import annotations

from gui.components.card import (
    CARD_HEIGHT,
    CARD_WIDTH,
    AssetCard,
    CardSpec,
    card_palette,
)
from gui.components.card_grid import CardGrid
from gui.components.file_selector import FileSelector
from gui.components.image_view import ImageView
from gui.components.student_card import StudentCard

__all__ = [
    "CARD_HEIGHT",
    "CARD_WIDTH",
    "AssetCard",
    "CardGrid",
    "CardSpec",
    "FileSelector",
    "ImageView",
    "StudentCard",
    "card_palette",
]
