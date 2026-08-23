import json
from pathlib import Path
from typing import Any

from rich.console import Console
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

PathLike = str | Path
console = Console()


def _to_path(path: PathLike) -> Path:
    """Helper to ensure input is always a Path object."""
    return Path(path) if isinstance(path, str) else path


def read_json(path: PathLike) -> dict:
    p = _to_path(path)

    if not p.exists():
        return {}

    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        console.print(f"Corrupt or unreadable JSON at {p}: {e}")
        return {}


@retry(
    retry=retry_if_exception_type((PermissionError, OSError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.2),
)
def write_json(path: PathLike, data: Any) -> None:
    """Writes data to a JSON file, creating parent directories if needed."""
    p = _to_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    tmp.replace(p)


def write_text(path: PathLike, data: str) -> None:
    """Writes data to a TXT file, creating parent directories if needed."""
    p = _to_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(data, encoding="utf-8")


def update_json_key(path: PathLike, key: str, value: Any):
    """Updates a single top-level key in a JSON file."""
    data = read_json(path)
    data[key] = value
    write_json(path, data)


def update_count(path: PathLike, name: str, value: Any) -> None:
    """Updates a named count in a JSON file."""
    update_json_key(path, name, value)


def update_student(path: PathLike, name: str, stats: dict[str, Any]) -> None:
    """Updates or adds a student's stats under the 'characters' key."""
    data = read_json(path)
    characters = data.setdefault("characters", {})
    if not isinstance(characters, dict):
        characters = {}
        data["characters"] = characters

    characters[name] = {"current": stats}
    write_json(path, data)
