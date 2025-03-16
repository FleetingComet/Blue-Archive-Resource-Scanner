import json
from dataclasses import fields
from pathlib import Path
from typing import Any, Dict, List


class BaseProcessor:
    dataclass = None
    processed_file: Path = None
    owned_file: Path = None
    output_file: Path = None

    def load_processed_data(self) -> List[Dict]:
        with open(self.processed_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_owned_data(self) -> Dict:
        with open(self.owned_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def process_json(self, raw_data: List[Dict]) -> List[Any]:
        return [self.dataclass(**item) for item in raw_data if self.validate_item(item)]

    def validate_item(self, item: Dict) -> bool:
        try:
            return all(field.name in item for field in fields(self.dataclass))
        except KeyError:
            return False

    def save_result(self, result: Any):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

    def map_data(self, processed_items: List[Any], owned_data: Dict) -> Any:
        raise NotImplementedError

    def process(self):
        processed_data = self.load_processed_data()
        items = self.process_json(processed_data)
        owned_data = self.load_owned_data()
        result = self.map_data(items, owned_data)
        self.save_result(result)
        print(f"Data saved to {self.output_file}")
