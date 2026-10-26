"""Project metadata for the About dialog.

Read from ``pyproject.toml`` (the same source ``pip``/``uv`` use) instead of
being hardcoded here, with a plain fallback for the unlikely case the file is
missing or unparsable.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from src.core.paths import Path_Config

FALLBACK_NAME = "blue-archive-scanner"
FALLBACK_VERSION = "unknown"
FALLBACK_DESCRIPTION = "Scan and count owned resources in Blue Archive."


@dataclass(frozen=True)
class ProjectMetadata:
    name: str
    version: str
    description: str
    readme: str | None
    requires_python: str | None
    urls: dict[str, str] = field(default_factory=dict)
    dependencies: tuple[str, ...] = ()


def load() -> ProjectMetadata:
    """The ``[project]`` table of pyproject.toml, with safe fallbacks."""
    data: dict = {}
    try:
        with open(Path_Config.PROJECT_ROOT / "pyproject.toml", "rb") as handle:
            data = tomllib.load(handle).get("project", {})
    except (OSError, tomllib.TOMLDecodeError, ValueError):
        data = {}

    urls = {
        str(key): str(value)
        for key, value in (data.get("urls") or {}).items()
        if isinstance(value, str)
    }
    return ProjectMetadata(
        name=str(data.get("name") or FALLBACK_NAME),
        version=str(data.get("version") or FALLBACK_VERSION),
        description=str(data.get("description") or FALLBACK_DESCRIPTION),
        readme=str(data["readme"]) if data.get("readme") else None,
        requires_python=(
            str(data["requires-python"]) if data.get("requires-python") else None
        ),
        urls=urls,
        dependencies=tuple(str(item) for item in (data.get("dependencies") or [])),
    )


def find_url(meta: ProjectMetadata, *keywords: str) -> str | None:
    """The first ``[project.urls]`` entry whose key contains any keyword."""
    for key, value in meta.urls.items():
        lowered = key.lower()
        if any(keyword in lowered for keyword in keywords):
            return value
    return None


def project_display_name() -> str:
    """Human title shown in the window/log: 'Blue Archive Resource Scanner'."""
    return "Blue Archive Resource Scanner"


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(Path_Config.PROJECT_ROOT))
    except ValueError:
        return str(path)
