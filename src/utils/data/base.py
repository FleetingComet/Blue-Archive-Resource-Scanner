from dataclasses import fields
from pathlib import Path
from typing import Any

from src.utils.data.io import read_json, write_json
from src.utils.data.text_matcher import find_closest


class BaseProcessor:
    dataclass: type[Any] | None = None
    processed_file: Path | None = None
    owned_file: Path | None = None
    output_file: Path | None = None

    def load_processed_data(self) -> list[dict]:
        data = read_json(self.processed_file)

        return data if isinstance(data, list) else []

    def load_owned_data(self) -> dict:
        return read_json(self.owned_file)

    def process_json(self, raw_data: list[dict]) -> list[Any]:
        if not self.dataclass:
            return []
        return [self.dataclass(**item) for item in raw_data if self.validate_item(item)]

    def validate_item(self, item: dict) -> bool:
        if not self.dataclass:
            return False

        try:
            return all(field.name in item for field in fields(self.dataclass))
        except (KeyError, TypeError):
            return False

    def save_result(self, result: Any):
        write_json(self.output_file, result)

    def get_closest_value(
        self, name: str, name_map: dict[str, Any], threshold: float = 0.8
    ) -> Any:
        """Helper to match a name against dictionary keys using fuzzy matching."""
        if not isinstance(name_map, dict) or not name_map:
            return 0
        matched = find_closest(name, name_map.keys(), threshold)
        return name_map.get(matched, 0) if matched else 0

    def map_data(self, processed_items: list[Any], owned_data: dict) -> Any:
        raise NotImplementedError

    def process(self):
        processed_data = self.load_processed_data()
        items = self.process_json(processed_data)
        owned_data = self.load_owned_data()
        result = self.map_data(items, owned_data)
        self.save_result(result)
        print(f"Data saved to {self.output_file}")
