from pathlib import Path

import pytest

from src.core.area import Size
from src.core.game_area import GameAreaManager
from src.core.paths import Path_Config
from src.core.script_transform import SCRIPT


@pytest.fixture
def path_config(tmp_path, monkeypatch):
    """Rebase the global ``Path_Config`` onto a per-test ``tmp_path``.

    Every path attribute keeps its relative location (e.g.
    ``assets/data/items_processed.json``) but resolves under ``tmp_path``, so
    processors and other consumers that read ``Path_Config.<attr>`` read and
    write inside the sandbox. Parent directories are created up front.
    """
    root = Path_Config.PROJECT_ROOT

    for name, value in list(vars(Path_Config).items()):
        if name == "PROJECT_ROOT" or not isinstance(value, Path):
            continue
        target = tmp_path / value.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(Path_Config, name, target)

    monkeypatch.setattr(Path_Config, "PROJECT_ROOT", tmp_path)
    return Path_Config


@pytest.fixture
def set_game_area(monkeypatch):
    """Point the global ``SCRIPT`` transform at a given device resolution.

    Region lookups are in 1280x720 script space and only resolve correctly
    once ``SCRIPT`` knows the device size, so screenshot tests call this with
    the width/height of the image under test. Restored automatically.
    """

    def _set(width: int, height: int) -> GameAreaManager:
        manager = GameAreaManager(Size(width, height))
        monkeypatch.setattr(SCRIPT, "_manager", manager)
        return manager

    return _set
