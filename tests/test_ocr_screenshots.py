"""End-to-end OCR tests driven by full-screen screenshots, per resolution.

Layout (see ``tests/screenshots/README.md``):

    tests/screenshots/<WxH>/<name>.png
    tests/screenshots/<WxH>/expected.json

Each resolution folder is auto-discovered, and every ``*.png`` inside it
becomes a parametrised case. The screenshot's own pixel size picks the
``GameAreaManager``, so the same UI region is cropped correctly whether the
device is 1280x720, 1920x1080, an ultra-wide 2400x1080, etc.

The filename prefix selects the worker:

    student*    -> student_ocr_worker   (name, level, bond, star, gear, UE, skills, talents)
    equipment*  -> item_ocr_worker      (name + owned count on an equipment screen)
    item*       -> item_ocr_worker      (name + owned count on an items screen)

``expected.json`` maps each filename to the fields/values that must be
extracted. Only the listed keys are asserted, so it is fine to check a subset.
"""

import json
from pathlib import Path

import cv2
import pytest

from src.constant import Screen
from src.core.paths import Path_Config
from src.services.workers import item_ocr_worker, student_ocr_worker
from src.utils.data.student_skill_helper import map_student_data_to_character
from src.utils.ocr.text_util import normalize_value

SCREENSHOTS_ROOT = Path(__file__).parent / "screenshots"


# Fixture discovery
def _parse_resolution(folder_name: str) -> tuple[int, int]:
    """Parse a ``<width>x<height>`` folder name (e.g. ``"1280x720"``)."""
    width, _, height = folder_name.lower().partition("x")
    if not (width.isdigit() and height.isdigit()):
        raise ValueError(f"Not a <width>x<height> resolution folder: {folder_name!r}")
    return int(width), int(height)


def _load_expected(res_dir: Path) -> dict | None:
    expected_file = res_dir / "expected.json"
    if not expected_file.exists():
        return None
    # utf-8-sig tolerates a BOM, which Windows editors/PowerShell often add.
    return json.loads(expected_file.read_text(encoding="utf-8-sig"))


def _discover_cases() -> list:
    """Collect one parametrised case per screenshot across all resolutions."""
    if not SCREENSHOTS_ROOT.is_dir():
        return []

    cases = []
    for res_dir in sorted(p for p in SCREENSHOTS_ROOT.iterdir() if p.is_dir()):
        try:
            _parse_resolution(res_dir.name)
        except ValueError:
            continue  # not a resolution folder (e.g. a stray docs dir)
        for image_path in sorted(res_dir.glob("*.png")):
            cases.append(
                pytest.param(image_path, id=f"{res_dir.name}/{image_path.stem}")
            )
    return cases


# Worker dispatch + comparison
def _run_worker(image, filename: str):
    """Run the extraction worker implied by the screenshot's filename."""
    stem = filename.lower()
    if stem.startswith("student"):
        return student_ocr_worker(image)
    if stem.startswith("equipment"):
        return item_ocr_worker(image, Screen.EQUIPMENT)
    if stem.startswith("item"):
        return item_ocr_worker(image, Screen.ITEMS)
    raise ValueError(
        f"Unrecognised screenshot name {filename!r}: prefix it with "
        "'student', 'equipment' or 'item'."
    )


def _normalise(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    return value


def _matches(actual, expected) -> bool:
    """Compare one extracted value against expected (scalar or list of options)."""
    actual = _normalise(actual)
    if isinstance(expected, list):
        return any(_matches(actual, option) for option in expected)
    if expected is None:
        return actual is None
    return actual is not None and str(actual) == str(_normalise(expected))


def _compare(expected: dict, actual) -> dict:
    if not isinstance(actual, dict):
        return {"<result>": ("dict", actual)}

    mismatches = {}
    for key, want in expected.items():
        if key not in actual:
            mismatches[key] = (want, "<missing>")
        elif not _matches(actual[key], want):
            mismatches[key] = (want, actual[key])
    return mismatches


# Tests
@pytest.mark.parametrize("image_path", _discover_cases())
def test_screenshot_extraction(image_path: Path, set_game_area, monkeypatch):
    # RapidOcrEngine resolves ./rapidocr/config.yaml relative to the CWD.
    monkeypatch.chdir(Path_Config.PROJECT_ROOT)

    res_dir = image_path.parent
    expected = _load_expected(res_dir)
    if expected is None:
        pytest.skip(f"no expected.json in tests/screenshots/{res_dir.name}/")
    if image_path.name not in expected:
        pytest.skip(
            f"{image_path.name} not listed in tests/screenshots/{res_dir.name}/expected.json"
        )

    image = cv2.imread(str(image_path))
    assert image is not None, f"cv2 could not read {image_path}"

    height, width = image.shape[:2]
    folder_resolution = _parse_resolution(res_dir.name)
    assert (width, height) == folder_resolution, (
        f"tests/screenshots/{res_dir.name}/ claims {folder_resolution[0]}x"
        f"{folder_resolution[1]} but {image_path.name} is {width}x{height}"
    )
    set_game_area(width, height)
    result = _run_worker(image, image_path.name)

    if image_path.name == "student_info.png":
        name, current_data = map_student_data_to_character(result)
        current_data["name"] = name
    else:
        name = result["name"]
        count = result["count"]

        current_data = {
            "name": name.lower(),
            "count": normalize_value(count, default=None),
        }

    mismatches = _compare(expected[image_path.name], current_data)
    if mismatches:
        lines = [f"OCR mismatch for {res_dir.name}/{image_path.name}:"]
        lines += [
            f"  {key}: expected {want!r}, got {got!r}"
            for key, (want, got) in mismatches.items()
        ]
        lines.append(f"  full result: {current_data}")
        pytest.fail("\n".join(lines))


def test_resolution_parser():
    assert _parse_resolution("1280x720") == (1280, 720)
    assert _parse_resolution("1920X1080") == (1920, 1080)
    with pytest.raises(ValueError):
        _parse_resolution("not-a-resolution")


def test_worker_dispatch_known_prefixes():
    # A None image short-circuits inside each worker, so this needs no OCR.
    assert _run_worker(None, "student_info.png") is None
    assert _run_worker(None, "equipment_grid.png") is None
    assert _run_worker(None, "items.png") is None


def test_worker_dispatch_unknown_prefix():
    with pytest.raises(ValueError):
        _run_worker(None, "mystery.png")
