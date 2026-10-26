"""Panels (major UI regions) composed by :mod:`gui.app`.

Each panel is a self-contained ``ttk.Frame`` that owns its own widgets and
exposes a small API to the app; cross-panel work is orchestrated by the app,
which passes callbacks instead of panel references where possible.
"""

from __future__ import annotations
