"""Shared GUI services.

``image_service`` is the single place that decides where artwork comes from
(local folder, schaledb, or nowhere) and how it is cached and loaded.
"""

from __future__ import annotations

from gui.services.image_service import ImageMode, ImageService, ImageSource

__all__ = ["ImageMode", "ImageService", "ImageSource"]
