import json
import logging
import os
import time
from enum import Enum, auto
from typing import Optional, Set

from config import Config
from scanner import get_currencies, get_student_info, startMatching
from screen_navigator import ScreenNavigator


class NavState(Enum):
    INIT = auto()
    CHECKING_CONTEXT = auto()
    ENSURING_HOME = auto()
    NAVIGATING = auto()
    VERIFYING_TARGET = auto()
    PROCESSING = auto()
    CHAINING_STUDENTS = auto()
    FALLBACK = auto()
    NEXT_SCREEN = auto()
    COMPLETED = auto()
    FAILED = auto()


class ScreenState:
    """
    A state machine that manages screen navigation and triggers
    data collection/matching processes for each defined screen.
    """

    def __init__(self, navigator: ScreenNavigator, config_path: Optional[str] = None):
        self.navigator = navigator
        self.config = self._load_config(
            config_path or os.path.join("config", "screen_config.json")
        )
        self.visited: Set[str] = set()
        self.unvisited: Set[str] = set(self.config.keys())
        self.current_state = NavState.INIT
        self.target_screen: Optional[str] = None
        self.retry_count = 0
        self.max_retries = 3

        self._init_logging()

    def _init_logging(self):
        """Setup dual-channel logging: File (Config.LOGS_DIR) + Console"""
        self.logger = logging.getLogger("BA-Scanner.FSM")
        if not self.logger.handlers:  # Prevent duplicate handlers on reload
            self.logger.setLevel(logging.INFO)
            self.logger.propagate = False

            Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
            log_file = Config.LOGS_DIR / "scanner_state.log"

            # File Handler: Timestamps + Level + Message
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(
                logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")
            )
            self.logger.addHandler(fh)

            # Console Handler: Clean, exact format you requested
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(ch)

    def _load_config(self, path: str) -> dict:
        with open(path, "r") as file:
            data = json.load(file)

        screens = data.get("screens", data)

        #  Load explicitly enabled screens
        enabled_screens = {
            name: info for name, info in screens.items() if info.get("enabled", False)
        }

        # AUTO-INJECT Student config if Students is enabled
        # This ensures chaining works even if "Student" is disabled in JSON
        if "Students" in enabled_screens and "Student" in screens:
            student_cfg = screens["Student"].copy()
            student_cfg["enabled"] = True
            enabled_screens["Student"] = student_cfg

        return enabled_screens

    def _log(self, msg: str, level: str = "info"):
        """Routed through logging."""
        formatted = f"{msg} | Target: {self.target_screen} | Visited: {len(self.visited)}/{len(self.config)}"
        getattr(self.logger, level.lower(), self.logger.info)(formatted)

    def _transition(self, state: NavState) -> NavState:
        """
        Transitions to the given state and initiates its associated process.

        Args:
            state (NavState): Current screen state.
        """
        self._log(f"Entering state: {state.name}")

        if state == NavState.INIT:
            current = self.navigator.identify_screen()
            if current in self.config:
                self.target_screen = current
                return NavState.PROCESSING
            return NavState.CHECKING_CONTEXT

        if state == NavState.CHECKING_CONTEXT:
            # Find next unvisited screen
            for screen in self.config:
                if screen not in self.visited:
                    self.target_screen = screen
                    self.retry_count = 0
                    return NavState.NAVIGATING
            return NavState.COMPLETED

        if state == NavState.NAVIGATING:
            cfg = self.config[self.target_screen]

            if self.navigator.identify_screen() == self.target_screen:
                self._log("Already on target screen, skipping navigation.")
                self.retry_count = 0
                return NavState.PROCESSING

            # Currencies runs at Home, skip navigation entirely
            if self.target_screen == "Currencies":
                self.navigator.ensure_at_home()
                self.navigator.ensure_menu_state(False)
                return NavState.PROCESSING

            if not cfg["uses_menu_tab"]:
                self.navigator.ensure_at_home()
            self.navigator.ensure_menu_state(cfg["uses_menu_tab"])

            time.sleep(
                1.0
                * Config.WAIT_TIME_MULTIPLIER
                * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER
            )

            res = self.navigator.navigate_to_target(
                cfg["menu_location"], cfg["uses_menu_tab"]
            )
            return NavState.VERIFYING_TARGET if res.success else NavState.FALLBACK

        if state == NavState.VERIFYING_TARGET:
            time.sleep(0.8 * Config.WAIT_TIME_MULTIPLIER)
            detected = self.navigator.identify_screen()
            if detected == self.target_screen:
                self.retry_count = 0
                return NavState.PROCESSING

            # Soft retry for OCR flakiness before hard fallback
            if self.retry_count < 2:
                self.retry_count += 1
                self._log(
                    f"Verification mismatch (got '{detected}'), soft retry {self.retry_count}/2"
                )
                return NavState.VERIFYING_TARGET

            self._log("Hard verification failed after soft retries", "warning")
            self.retry_count += 1
            return NavState.FALLBACK

        if state == NavState.PROCESSING:
            cfg = self.config[self.target_screen]
            self._execute_process(self.target_screen, cfg)
            self.visited.add(self.target_screen)
            self.unvisited.discard(self.target_screen)

            # Auto-chain Students -> Student
            if (
                self.target_screen == "Students"
                and "Student" in self.config
                and "Student" not in self.visited
            ):
                return NavState.CHAINING_STUDENTS
            return NavState.NEXT_SCREEN

        if state == NavState.CHAINING_STUDENTS:
            self._log("Chaining Students -> Student detail flow")
            # We are already on the Students list. Just tap the first student.
            self.navigator.navigate_to_target("first_student", in_menu_tab=False)

            self.visited.add("Students")
            self.unvisited.discard("Students")

            # Extract all students automatically
            get_student_info(self.navigator.input_controller)

            self.visited.add("Student")
            self.unvisited.discard("Student")

            return NavState.NEXT_SCREEN

        if state == NavState.FALLBACK:
            if self.retry_count >= self.max_retries:
                self._log("Max retries reached. Skipping target.")
                self.unvisited.discard(self.target_screen)
                return NavState.NEXT_SCREEN

            self._log(
                f"Fallback: Resetting to Home (Attempt {self.retry_count + 1}/{self.max_retries})"
            )
            self.navigator.ensure_at_home()
            time.sleep(
                2.0
                * Config.WAIT_TIME_MULTIPLIER
                * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER
            )
            self.retry_count += 1
            return NavState.NAVIGATING

        if state == NavState.NEXT_SCREEN:
            return NavState.CHECKING_CONTEXT

        return NavState.FAILED

    def run(self) -> bool:
        """
        Execute the loop until completion or failure.

        Returns:
            bool: True if all screens processed, False otherwise.
        """

        while self.current_state not in (NavState.COMPLETED, NavState.FAILED):
            self.current_state = self._transition(self.current_state)
            time.sleep(0.1)  # Yield slightly to avoid tight loops

        if self.current_state == NavState.COMPLETED:
            print("All screens completed successfully.")
        else:
            print(f"Navigation aborted. Remaining unvisited: {self.unvisited}")
        return self.current_state == NavState.COMPLETED

    def _execute_process(self, screen_name: str, cfg: dict):
        """
        Handles what to do after navigating to a given screen.

        Args:
            screen_name (str): Name of the screen.
            cfg: grid_config
        """
        print(f"Processing: {screen_name}")

        if screen_name in ["Currencies"]:
            get_currencies(self.navigator.input_controller)

        if screen_name in ("Equipment", "Items"):
            startMatching(
                self.navigator.input_controller,
                grid_type=cfg["grid_type"],
                grid_config=cfg["grid_config"],
            )

        elif screen_name == "Students":
            # Tap first student to enter detail view
            self.navigator.navigate_to_target("first_student", in_menu_tab=False)

        elif screen_name == "Student":
            get_student_info(self.navigator.input_controller)
