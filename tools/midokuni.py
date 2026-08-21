"""
Usage: python -m tools.midokuni
"""

import argparse
from enum import Enum
from urllib.parse import urlencode

from rich.console import Console

from src.core.config import Config
from src.utils.data.io import read_json, write_json
from src.utils.sync.data_sync_manager import DataSyncManager

console = Console()


class State(str, Enum):
    UNSELECTED = "0"
    SELECTED = "1"
    BLUE = "2"
    BLACK = "3"


class MidokuniRosterExporter:
    """
    Transforms scanned student data into Midokuni site's roster URL format.
    """

    def __init__(self, output_filename: str = "midokuni_roster.json"):
        self.BASE_URL = "https://hina.loves.midokuni.com/Tool/Roster"
        self.BASE66_ALPHABET = (
            "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_.~"
        )
        self.CHAR_TO_VAL: dict[str, int] = {
            char: idx for idx, char in enumerate(self.BASE66_ALPHABET)
        }

        self.STATE_MAP = {
            "blue": State.BLUE,
            "black": State.BLACK,
            None: State.SELECTED,
        }

        self.input_file = Config.final_students
        self.output_file = Config.OUTPUT_DIR / output_filename

        # Map internal scanner IDs to valid IDs
        self.SITE_ID_MAP = {
            "10099": "10098",  # Hoshino (Armed): Dealer to Tank
            "10144": "10143",  # Shunling (Swimsuit) (T_T) to Shun (Swimsuit)
        }

    def to_base66(self, n: int) -> str:
        """Encodes a non-negative integer into a Base66 string."""
        if n == 0:
            return "0"

        digits = []
        while n:
            digits.append(self.BASE66_ALPHABET[n % 66])
            n //= 66

        return "".join(reversed(digits))

    def from_base66(self, s: str) -> int:
        """Decodes a Base66 string into an integer."""
        val = 0
        for char in s:
            val = val * 66 + self.CHAR_TO_VAL[char]
        return val

    def to_base5(n: int) -> str:
        """Converts a non-negative integer into a Base5 string."""
        if n == 0:
            return "0"

        digits = []
        while n:
            digits.append(str(n % 5))
            n //= 5

        return "".join(reversed(digits))

    def from_base5(s: str) -> int:
        value = 0
        for c in s:
            value *= 5
            value += int(c)
        return value

    def encode_category_states(self, states: list[int | str]) -> str:
        """
        Encodes an array of student states (0-4) into a Base66 URL parameter.
        If all states are 0, returns an empty string "".
        """
        if not states:
            return ""

        # Convert state elements to string digits
        str_states = [str(s) for s in states]

        # Reverse state array and join into base-5 string
        base5_str = "".join(reversed(str_states))

        # Base5 string to integer
        value = int(base5_str, 5) if base5_str else 0

        if value == 0:
            return ""

        # Integer to Base66
        return self.to_base66(value)

    @classmethod
    def decode_category_param(
        cls, param: str | None, buffer_size: int = 200
    ) -> list[str]:
        """
        Decodes a Base66 URL parameter into a list of student state strings.
        Appends buffer_size trailing "0" values.
        """
        if not param or param == "0":
            return [State.UNSELECTED.value] * buffer_size

        # Base66 to integer
        value = cls.from_base66(param)

        # Integer to Base5 string
        base5_str = cls.to_base5(value)

        # Reverse base5 string & append 200 zero safety buffer
        decoded_states = list(reversed(base5_str))
        decoded_states.extend([State.UNSELECTED.value] * buffer_size)

        return decoded_states

    @staticmethod
    def extract_student_category_and_index(student_id: int | str) -> tuple[str, int]:
        """
        Extracts category string and student index from student ID.
        Example: '10045' -> category 's10', index 45
        """
        sid_str = str(student_id)
        category = f"s{sid_str[:2]}"
        index = int(sid_str[2:])
        return category, index

    def build_roster_params(
        self,
        student_states: dict[int | str, int | str],
    ) -> dict[str, str]:
        """
        Builds URL query parameters from a dictionary of {student_id: state}.

        Example input: {'10000': 4, '10045': 2, '20059': 3}
        Returns: {'s10': '...', 's20': '...'}
        """
        category_buckets: dict[str, dict[int, str]] = {}

        for student_id, state in student_states.items():
            cat, idx = self.extract_student_category_and_index(student_id)
            if cat not in category_buckets:
                category_buckets[cat] = {}
            category_buckets[cat][idx] = str(state)

        params: dict[str, str] = {}

        for cat, idx_map in category_buckets.items():
            max_idx = max(idx_map.keys()) if idx_map else 0
            state_list = [State.UNSELECTED.value] * (max_idx + 1)
            for idx, val in idx_map.items():
                state_list[idx] = val

            encoded_val = self.encode_category_states(state_list)
            if encoded_val:
                params[cat] = encoded_val

        return params

    def process(self, state_name: str | None = None) -> str:
        """
        Processes scanned student data and generates the Midokuni Roster URL.
        """
        target_state = self.STATE_MAP.get(state_name, State.SELECTED)

        scanned_data = read_json(self.input_file)
        characters = scanned_data.get("characters", [])

        # Assign selected state to all scanned students
        student_states: dict[str, str] = {}
        for char in characters:
            char_id = str(char.get("id", ""))
            if char_id and char_id != "N/A":
                char_id = self.SITE_ID_MAP.get(char_id, char_id)
                student_states[char_id] = target_state.value

        roster_params = self.build_roster_params(student_states)
        query_string = urlencode(roster_params)
        full_url = f"{self.BASE_URL}?{query_string}" if query_string else self.BASE_URL

        # Save URL result to output file
        write_json(self.output_file, {"url": full_url, "params": roster_params})

        console.print(
            f"Selected State: [cyan]{'Selected (default)' if state_name is None else target_state.name}[/cyan]"
        )
        console.print(f"Scanned Students Count: [cyan]{len(student_states)}[/cyan]")
        console.print(f"Generated Parameters: {roster_params}")
        console.print(
            f"\n[bold green]Full Roster URL:[/bold green]\n"
            f"[link={full_url}][cyan]{full_url}[/cyan][/link]\n"
        )

        return full_url


def main():
    parser = argparse.ArgumentParser(
        description="Convert scanner output into Midokuni roster url format."
    )

    parser.add_argument(
        "-s",
        "--state",
        choices=["blue", "black"],
        help="Set all characters to the specified state (blue or black).",
    )

    parser.add_argument(
        "-o",
        "--online",
        action="store_true",
        help="Download the latest community-maintained data before processing.",
    )
    args = parser.parse_args()

    if args.online:
        try:
            DataSyncManager().update_from_online()

        except Exception as e:  # noqa: BLE001
            console.print(f"[yellow]Online sync warning: {e}[/yellow]")

    exporter = MidokuniRosterExporter()
    exporter.process(state_name=args.state)


if __name__ == "__main__":
    main()
