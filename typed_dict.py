from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypedDict


# if TYPE_CHECKING:
class OwnedDict(TypedDict):
    counts: Path
    students: Path
    currencies: Path

class ProcessedDataDict(TypedDict):
    equipment: Path
    items: Path
    students: Path

class OutputFilesDict(TypedDict):
    equipment: Path
    items: Path
    students: Path
    converter_justin: Path
    merger: Path

class MergerDict(TypedDict):
    input: Path
    to_file: Path
    output: Path