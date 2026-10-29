"""The project's dependencies and their licenses, for the About dialog.

The list comes from ``[project].dependencies`` in pyproject.toml (nothing is
hardcoded); each entry is then matched to its installed distribution so the
dialog can show the version in use and the license the package was published
under, with every license file the distribution ships.

Finding those files is fiddly, because wheels put them in different places and
``Distribution.read_text`` resolves names *inside* the ``.dist-info`` directory
(so a PEP 639 ``<pkg>.dist-info/licenses/LICENSE`` is never found by its bare
name). This module locates them through ``Distribution.files`` + ``locate_file``
instead, with a directory scan as a fallback for editable installs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib import metadata as importlib_metadata
from pathlib import Path, PurePosixPath

from gui.metadata import load as load_project

# A requirement starts with the distribution name, before any version
# specifier, extra or environment marker.
_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")

# File names that hold license text (any extension).
_LICENSE_PREFIXES = ("LICENSE", "LICENCE", "COPYING", "NOTICE")

# Preferred base names when a package ships several.
_CANONICAL = {
    "LICENSE",
    "LICENSE.TXT",
    "LICENSE.MD",
    "LICENSE.RST",
    "LICENCE",
    "LICENCE.TXT",
    "COPYING",
    "COPYING.TXT",
}

_MAX_FILE_BYTES = 400_000  # skip anything implausibly large
_MAX_FILES = 25


@dataclass(frozen=True)
class LicenseFile:
    """One license file: a display name and its text."""

    name: str
    text: str


@dataclass(frozen=True)
class Dependency:
    name: str
    version: str
    license: str
    summary: str = ""
    licenses: tuple[LicenseFile, ...] = ()

    @property
    def license_text(self) -> str | None:
        """The primary (first) license file's text, if any was found."""
        return self.licenses[0].text if self.licenses else None


def requirement_name(requirement: str) -> str:
    """``pywin32==312 ; sys_platform == 'win32'`` -> ``pywin32``."""
    match = _NAME_RE.match(requirement)
    return match.group(1) if match else requirement.strip()


def installed() -> list[Dependency]:
    """Every declared dependency, described from its installed distribution."""
    found: dict[str, Dependency] = {}
    for requirement in load_project().dependencies:
        name = requirement_name(requirement)
        found.setdefault(name.lower(), _describe(name))
    return list(found.values())


# --------------------------------------------------------------------------
# Per-distribution details
# --------------------------------------------------------------------------
def _describe(name: str) -> Dependency:
    try:
        dist = importlib_metadata.distribution(name)
    except importlib_metadata.PackageNotFoundError:
        return Dependency(name, "not installed", "unknown")
    meta = dist.metadata
    return Dependency(
        name=meta.get("Name") or name,
        version=dist.version or "unknown",
        license=_license(meta),
        summary=(meta.get("Summary") or "").strip(),
        licenses=_license_files(dist),
    )


def _license(meta) -> str:
    """Short licence name from PEP 639, the legacy field, or the classifiers."""
    expression = (meta.get("License-Expression") or "").strip()
    if expression:
        return expression
    value = (meta.get("License") or "").strip()
    if value and "\n" not in value and len(value) <= 60:
        return value
    for classifier in meta.get_all("Classifier") or []:
        if classifier.startswith("License ::"):
            return classifier.rsplit("::", 1)[-1].strip()
    if value:
        return value.splitlines()[0][:60].strip()
    return "unknown"


def _license_files(dist) -> tuple[LicenseFile, ...]:
    """Every license file the distribution ships, primary one first."""
    found: list[LicenseFile] = []
    for name in _candidate_paths(dist):
        text = _read_text(dist, name)
        if text:
            found.append(LicenseFile(name=name, text=text))
        if len(found) >= _MAX_FILES:
            break
    return tuple(found)


def _candidate_paths(dist) -> list[str]:
    """Candidate license paths, best match first."""
    entries = [str(path).replace("\\", "/") for path in (dist.files or ())]
    licensed = [
        path for path in entries if _looks_like_license(PurePosixPath(path).name)
    ]
    if not licensed:
        return _scan_info_dir(dist)

    declared = {
        str(name).replace("\\", "/")
        for name in (dist.metadata.get_all("License-File") or [])
    }
    info = _info_name(dist)

    def rank(path: str) -> tuple:
        base = PurePosixPath(path).name.upper()
        return (
            0 if any(path == d or path.endswith("/" + d) for d in declared) else 1,
            0 if info and path.startswith(info + "/") else 1,
            0 if base in _CANONICAL else 1,
            path.count("/"),
            len(path),
        )

    return sorted(licensed, key=rank)


def _scan_info_dir(dist) -> list[str]:
    """Fallback for installs without a file list (editable, legacy)."""
    base = getattr(dist, "_path", None)
    if base is None:
        return []
    base = Path(base)
    if not base.is_dir():
        return []
    found: list[str] = []
    for name in (
        "LICENSE",
        "LICENSE.txt",
        "LICENSE.md",
        "LICENCE",
        "COPYING",
        "NOTICE",
    ):
        candidate = base / name
        if candidate.is_file():
            found.append(str(candidate))
    licenses_dir = base / "licenses"
    if licenses_dir.is_dir():
        for candidate in sorted(licenses_dir.rglob("*")):
            if candidate.is_file() and _looks_like_license(candidate.name):
                found.append(str(candidate))
    return sorted(set(found))[:_MAX_FILES]


def _looks_like_license(filename: str) -> bool:
    return filename.upper().startswith(_LICENSE_PREFIXES)


def _info_name(dist) -> str:
    path = getattr(dist, "_path", None)
    return Path(path).name if path is not None else ""


def _read_text(dist, name: str) -> str | None:
    target = Path(name)
    if not target.is_absolute():  # names from Distribution.files are relative
        try:
            target = Path(dist.locate_file(name))
        except Exception:  # noqa: BLE001, S110
            pass
    try:
        if target.is_file() and target.stat().st_size <= _MAX_FILE_BYTES:
            return target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    # Last resort: Distribution.read_text resolves inside the .dist-info dir.
    try:
        return dist.read_text(name)
    except Exception:  # noqa: BLE001 - a broken package must not break About
        return None
