"""The scanner's JSON output files and the processors behind them.

``main.run_post_processing`` writes one *final* file per scanned screen
(``output/*_final_values.json``) from the raw files under ``output/owned/``
that the scanners write during a run. The Data tab edits these files in place;
this module is the single place that knows which files exist, which raw file
each processor consumes, and which final file it produces.

Nothing here invents new paths - every path comes from :class:`Path_Config`,
the project's source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.core.paths import Path_Config

# Data kinds the Data tab can render and edit.
STUDENTS_FINAL = "students_final"
EQUIPMENT_FINAL = "equipment_final"
ITEMS_FINAL = "items_final"
STUDENTS_RAW = "students_raw"
COUNTS_RAW = "counts_raw"
CURRENCIES_RAW = "currencies_raw"
GENERIC = "generic"


@dataclass(frozen=True)
class ScanFile:
    """One JSON file the scanner or its processors own."""

    key: str
    label: str
    path: Path
    kind: str
    raw: bool = False
    # Processor classes that consume this file, as ``(module, class)``.
    processors: tuple[tuple[str, str], ...] = ()
    # :class:`ScanFile` key of the final file this raw file feeds (if any).
    final_key: str | None = None

    @property
    def display(self) -> str:
        """Path relative to the project root when possible."""
        try:
            return str(self.path.relative_to(Path_Config.PROJECT_ROOT))
        except ValueError:
            return str(self.path)


# Order matters: it is the order the Data tab lists the files in, and the
# priority used when a scan updates several of them at once.
SCAN_FILES: tuple[ScanFile, ...] = (
    ScanFile(
        STUDENTS_FINAL,
        "Students (final values)",
        Path_Config.final_students,
        STUDENTS_FINAL,
    ),
    ScanFile(
        EQUIPMENT_FINAL,
        "Equipment (final values)",
        Path_Config.final_equipment,
        EQUIPMENT_FINAL,
    ),
    ScanFile(
        ITEMS_FINAL,
        "Items (final values)",
        Path_Config.final_items,
        ITEMS_FINAL,
    ),
    ScanFile(
        STUDENTS_RAW,
        "Students (raw scan)",
        Path_Config.scanned_students,
        STUDENTS_RAW,
        raw=True,
        processors=(("src.utils.data.processors.student", "StudentProcessor"),),
        final_key=STUDENTS_FINAL,
    ),
    ScanFile(
        COUNTS_RAW,
        "Items & equipment (raw scan)",
        Path_Config.scanned_counts,
        COUNTS_RAW,
        raw=True,
        processors=(
            ("src.utils.data.processors.equipment", "EquipmentProcessor"),
            ("src.utils.data.processors.item", "ItemProcessor"),
        ),
    ),
    ScanFile(
        CURRENCIES_RAW,
        "Currencies (raw scan)",
        Path_Config.scanned_currencies,
        CURRENCIES_RAW,
        raw=True,
    ),
)

SCAN_FILES_BY_KEY = {spec.key: spec for spec in SCAN_FILES}
SCAN_FILES_BY_PATH = {spec.path.resolve(): spec for spec in SCAN_FILES}


def identify(path: Path) -> ScanFile | None:
    """The known scanner file at ``path``, if it is one."""
    try:
        return SCAN_FILES_BY_PATH.get(Path(path).resolve())
    except OSError:
        return None


def existing() -> list[ScanFile]:
    return [spec for spec in SCAN_FILES if spec.path.is_file()]


def modified_since(timestamp: float) -> list[ScanFile]:
    """Known files written at or after ``timestamp`` (newest scan outputs)."""
    found: list[tuple[float, ScanFile]] = []
    for spec in SCAN_FILES:
        try:
            mtime = spec.path.stat().st_mtime
        except OSError:
            continue
        if mtime >= timestamp:
            found.append((mtime, spec))
    found.sort(key=lambda pair: pair[0], reverse=True)
    return [spec for _mtime, spec in found]


def newest_file() -> ScanFile | None:
    """The most recently modified known file, for a first Data tab load."""
    candidates: list[tuple[float, ScanFile]] = []
    for spec in SCAN_FILES:
        try:
            candidates.append((spec.path.stat().st_mtime, spec))
        except OSError:
            continue
    if not candidates:
        return None
    return max(candidates, key=lambda pair: pair[0])[1]


def reprocess(spec: ScanFile) -> list[Path]:
    """Run the processors that consume ``spec`` and return the files written.

    Imports are local so starting the GUI never pulls the OCR/data stack in.
    """
    outputs: list[Path] = []
    for module_name, class_name in spec.processors:
        module = __import__(module_name, fromlist=[class_name])
        processor = getattr(module, class_name)()
        processor.process()
        outputs.append(processor.output_file)
    return outputs
