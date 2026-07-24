import datetime
import logging
import os
import time
from enum import Enum, auto

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from tenacity import retry, stop_after_attempt, wait_fixed

from src.core.config import Config
from src.core.navigator import ScreenNavigator
from src.services.scanner import get_currencies, get_student_info, startMatching
from src.utils.data.io import read_json
from src.utils.log.plain_text_formatter import PlainTextFormatter


class NavState(Enum):
    INIT = auto()
    CHECKING_CONTEXT = auto()
    NAVIGATING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()


class ScreenState:
    """
    A state machine that manages screen navigation and triggers
    data collection/matching processes for each defined screen.
    """

    def __init__(self, navigator: ScreenNavigator, config_path: str | None = None):
        self.navigator = navigator
        self.console = Console()
        self.config = self._load_config(
            config_path or os.path.join("config", "screen_config.json")
        )

        self.visited: set[str] = set()
        self.current_state = NavState.INIT
        self.target_screen: str | None = None

        self._init_logging()

    def _init_logging(self):
        self.logger = logging.getLogger("BA-Scanner")
        self.logger.setLevel(logging.INFO)

        # Clear existing handlers to prevent duplicate logs on re-init
        if self.logger.handlers:
            self.logger.handlers.clear()

        rich_handler = RichHandler(
            console=self.console,
            show_path=False,
            rich_tracebacks=True,
            markup=True,
            omit_repeated_times=False,
        )
        # Console format: only the message (Rich adds the timestamp column itself)
        rich_handler.setFormatter(logging.Formatter("%(message)s"))

        log_path = (
            Config.LOGS_DIR / f"{datetime.date.today()}_scanner.log"  # noqa: DTZ011
        )  # I don't need timezone aware date because it lives in your local filesystem
        file_handler = logging.FileHandler(log_path, encoding="utf-8")

        file_format = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler.setFormatter(
            PlainTextFormatter(file_format._fmt, file_format.datefmt)
        )

        self.logger.addHandler(rich_handler)
        self.logger.addHandler(file_handler)
        self.logger.propagate = False

    def _load_config(self, path: str) -> dict:
        data = read_json(path)

        screens = data.get("screens", data)

        #  Load explicitly enabled screens
        enabled_screens = {
            name: info for name, info in screens.items() if info.get("enabled", False)
        }

        # AUTO-INJECT Student config if Students is enabled
        # This ensures chaining works even if "Student" is disabled in JSON
        if "Students" in enabled_screens and "Student" in screens:
            enabled_screens["Student"] = {**screens["Student"], "enabled": True}

        return enabled_screens

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        before_sleep=lambda rs: logging.getLogger("BA-Scanner").warning(
            f"[bold red]⚠ Match Failed.[/bold red] Retrying... (Attempt {rs.attempt_number}/3)"
        ),
    )
    def _safe_navigate(self, cfg):
        res = self.navigator.navigate_to_target(
            cfg["menu_location"], cfg["uses_menu_tab"]
        )
        time.sleep(
            2 * Config.WAIT_TIME_MULTIPLIER * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER
        )
        if not res.success:
            self.navigator.ensure_at_home()  # Go home on failure
            raise RuntimeError(f"Navigation to {self.target_screen} failed")

        # Verify OCR matches target
        detected = self.navigator.identify_screen()
        if detected != self.target_screen:
            raise RuntimeError(
                f"Verification failed: Expected {self.target_screen}, got {detected}"
            )

    def _execute_process(self, screen_name: str, cfg: dict):
        """Triggers the actual OCR work."""

        self.logger.info(f"[bold yellow]Scanning[/bold yellow] {screen_name}...")

        if screen_name in ["Currencies"]:
            get_currencies(self.navigator.device)

        if screen_name in ("Equipment", "Items"):
            startMatching(
                self.navigator.device,
                grid_type=cfg["grid_type"],
                grid_config=cfg["grid_config"],
            )

        elif screen_name == "Students":
            # Tap first student to enter detail view
            self.logger.info("Reached Students list, entering individual stat page...")

        elif screen_name == "Student":
            get_student_info(self.navigator.device)

    def _transition(self, progress: Progress, task_id: TaskID) -> NavState:
        """
        Transitions to the given state and initiates its associated process.
        """

        state = self.current_state

        if state == NavState.INIT:
            progress.update(
                task_id, description="[cyan]Checking current screen...[/cyan]"
            )
            # Identify what screen we are currently sitting on
            detected = self.navigator.identify_screen()
            if not detected and self.navigator.at_home():
                detected = "Currencies"

            # If current screen is enabled in config, set as target immediately
            if detected and detected in self.config:
                self.logger.info(
                    f"[bold green]Starting from current screen:[/bold green] {detected}"
                )
                self.target_screen = detected
                progress.update(
                    task_id, description=f"[cyan]Targeting:[/cyan] {self.target_screen}"
                )
                return NavState.NAVIGATING

            # Otherwise, fall back to default order
            return NavState.CHECKING_CONTEXT

        if state == NavState.CHECKING_CONTEXT:
            # Find next unvisited screen
            self.target_screen = next(
                (s for s in self.config if s not in self.visited), None
            )
            if not self.target_screen:
                return NavState.COMPLETED

            progress.update(
                task_id, description=f"[cyan]Targeting:[/cyan] {self.target_screen}"
            )
            return NavState.NAVIGATING

        if state == NavState.NAVIGATING:
            cfg = self.config[self.target_screen]

            try:

                # Check if ALREADY on target screen to bypass unnecessary navigation
                already_at_target = False
                if self.target_screen == "Currencies":
                    if self.navigator.at_home():
                        already_at_target = True

                else:
                    current = self.navigator.identify_screen()
                    if current == self.target_screen:
                        already_at_target = True

                if already_at_target:
                    self.logger.info(
                        f"[bold green]Already on[/bold green] {self.target_screen}. Skipping navigation."
                    )
                    if self.target_screen == "Currencies":
                        self.navigator.ensure_menu_state(should_open=False)
                    return NavState.PROCESSING

                # Ensure clean Home state for screens that require it
                if self.target_screen in ["Currencies", "Students"]:
                    progress.update(
                        task_id,
                        description=f"[bold blue]Going Home[/bold blue] for {self.target_screen}...",
                    )
                    self.navigator.ensure_at_home()
                    self.navigator.ensure_menu_state(should_open=False)
                    time.sleep(
                        2
                        * Config.WAIT_TIME_MULTIPLIER
                        * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER
                    )

                if self.target_screen != "Currencies":
                    progress.update(
                        task_id,
                        description=f"[bold blue]Navigating to[/bold blue] {self.target_screen}",
                    )
                    self._safe_navigate(cfg)

                return NavState.PROCESSING
            except Exception as e:  # noqa: BLE001
                self.logger.error(
                    f"[bold red]Error:[/bold red] Abandoning {self.target_screen} - {e!s}"
                )
                self.visited.add(self.target_screen)  # Skip it
                progress.advance(task_id)
                # Ensure we return home to clear any stuck menus before trying the next screen
                self.navigator.ensure_at_home()
                return NavState.CHECKING_CONTEXT

        if state == NavState.PROCESSING:
            cfg = self.config[self.target_screen]

            progress.update(
                task_id,
                description=f"[bold yellow]Processing[/bold yellow] {self.target_screen}",
            )

            if self.target_screen == "Students":
                # Tap first student to enter the stat view
                self.logger.info(
                    "[bold blue]Reached Students List.[/bold blue] Entering detail view..."
                )
                self.navigator.navigate_to_target("first_student", in_menu_tab=False)
                time.sleep(
                    2
                    * Config.WAIT_TIME_MULTIPLIER
                    * Config.WAIT_TIME_SCREEN_NAV_MULTIPLIER
                )

            else:
                self._execute_process(self.target_screen, cfg)

            self.visited.add(self.target_screen)
            progress.advance(task_id)
            if self.target_screen == "Students":
                # We are forcing the target screen to Student to avoid getting derailed
                self.target_screen = "Student"
                return NavState.NAVIGATING
            return NavState.CHECKING_CONTEXT

        return NavState.FAILED

    def run(self) -> bool:
        """
        Execute the loop until completion or failure.

        Returns:
            bool: True if all screens processed, False otherwise.
        """

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True,  # Collapses the bar when finished
        ) as progress:

            task_id = progress.add_task("[cyan]Initializing...", total=len(self.config))

            while self.current_state not in (NavState.COMPLETED, NavState.FAILED):
                self.current_state = self._transition(progress, task_id)
                time.sleep(0.1)  # Yield slightly to avoid tight loops

        if self.current_state == NavState.COMPLETED:
            self.console.print(
                "[bold green]✔ All tasks finished successfully.[/bold green]"
            )
            return True

        self.console.print("[bold red]✘ Scanning failed or aborted.[/bold red]")
        return False
