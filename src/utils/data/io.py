import json
from pathlib import Path
from typing import Any, Dict


def read_json(path: Path) -> Dict:
    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def update_json_key(path: Path, key: str, value: Any):
    data = read_json(path)
    data[key] = value
    write_json(path, data)


# TODO: Remove this
def update_count(path: Path, name: str, value: Any) -> None:
    data = read_json(path)
    data[name] = value
    write_json(path, data)


def update_student(path: Path, name: str, stats: Dict) -> None:
    data = read_json(path)
    data.setdefault("characters", {})
    data["characters"][name] = {"current": stats}
    write_json(path, data)
