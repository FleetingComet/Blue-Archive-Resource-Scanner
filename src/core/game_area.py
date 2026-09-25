from dataclasses import dataclass
from enum import Enum

from src.constant import SCRIPT_SIZE
from src.core.area import Location, Region, Size

# * Empirically measured cap on the game viewport's aspect ratio (width / height).
# * Derived from screenshots: at 2400x1080 the game area measured 2348x1080
# * (26px bars/side); the same ~2.174 ratio held at 2560x1080, 3440x1440, and
# * 3840x1600. At or below this ratio - including 1920x1200 (16:10), which is
# * `narrower` than 16:9 - the game fills the screen edge-to-edge, no bars.
MAX_GAME_ASPECT = 2348 / 1080  # ~2.174:1


class ScaleDimension(Enum):
    WIDTH = "width"
    HEIGHT = "height"


@dataclass
class GameAreaManager:
    """
    Manages the game area for any screen size, handling borders and aspect ratios.
    """

    screen_size: Size  # full device/window size in pixels
    window_pos: Location = None  # Top-left of window on desktop

    def __post_init__(self):
        if not self.window_pos:
            self.window_pos = Location(0, 0)

        self.screen_aspect = self.screen_size.width / self.screen_size.height
        self._scale_method, self.scale = self._decide_scale_method()
        self._game_area = self._compute_game_area()

    def _decide_scale_method(self) -> tuple[ScaleDimension, float]:
        """Fit inside screen while maintaining 16:9 script aspect ratio."""
        w_scale = self.screen_size.width / SCRIPT_SIZE.width
        h_scale = self.screen_size.height / SCRIPT_SIZE.height

        # If screen is wider than 16:9, scale by height (pillarboxing)
        # If screen is narrower than 16:9, scale by width (letterboxing)
        if w_scale <= h_scale:
            return ScaleDimension.WIDTH, w_scale
        else:
            return ScaleDimension.HEIGHT, h_scale

    @property
    def aspect_ratio(self) -> float:
        return self.game_area.width / self.game_area.height

    @property
    def is_wide(self) -> bool:
        return self.aspect_ratio > (16 / 9 + 0.01)

    @property
    def wide_factor(self) -> float:
        """Returns 0.0 at 16:9, scaling to 1.0 at 2.174:1 (Max Wide)."""
        min_aspect = 16 / 9
        if self.aspect_ratio <= min_aspect:
            return 0.0
        return max(
            0.0,
            min(1.0, (self.aspect_ratio - min_aspect) / (MAX_GAME_ASPECT - min_aspect)),
        )

    def _compute_game_area(self) -> Region:
        """Computes active game canvas minus pillarbox/letterbox bars."""
        if self.screen_aspect > MAX_GAME_ASPECT:
            # Pillarboxed (Blue/Black bars on left & right)
            game_width = round(self.screen_size.height * MAX_GAME_ASPECT)
            game_height = self.screen_size.height
            bar_w = round((self.screen_size.width - game_width) / 2)
            # return Region(bar_w, 0, game_width, game_height)
            return Region(
                self.window_pos.x + bar_w, self.window_pos.y, game_width, game_height
            )
        else:
            # Native full screen (16:9 to ~2.174:1)
            # return Region(0, 0, self.screen_size.width, self.screen_size.height)
            return Region(
                self.window_pos.x,
                self.window_pos.y,
                self.screen_size.width,
                self.screen_size.height,
            )

    # def _compute_game_area(self) -> Region:
    #     """Computes active game canvas minus pillarbox/letterbox bars."""
    #     if self.screen_aspect > MAX_GAME_ASPECT:
    #         # Pillarboxed (Blue/Black bars on left & right)
    #         game_width = round(self.screen_size.height * MAX_GAME_ASPECT)
    #         game_height = self.screen_size.height
    #         bar_w = round((self.screen_size.width - game_width) / 2)
    #         return Region(bar_w, 0, game_width, game_height)
    #     elif self.screen_aspect < 16 / 9 - 0.01:
    #         # Letterboxed (narrower than 16:9)
    #         game_width = self.screen_size.width
    #         game_height = round(game_width / (16 / 9))
    #         bar_h = round((self.screen_size.height - game_height) / 2)
    #         return Region(0, bar_h, game_width, game_height)
    #     else:
    #         # Native full screen (16:9 to ~2.174:1)
    #         return Region(0, 0, self.screen_size.width, self.screen_size.height)

    @property
    def game_area(self) -> Region:
        return self._game_area

    def script_to_device(self, x: float, y: float) -> tuple[int, int]:
        """Convert 720p virtual script coordinates to physical screen/window pixels."""
        screen_x = self.game_area.x + (x * self.scale)
        screen_y = self.game_area.y + (y * self.scale)
        return round(screen_x), round(screen_y)

    def device_to_script(self, x: float, y: float) -> tuple[int, int]:
        """Convert physical screen pixels back to 720p virtual script coordinates."""
        script_x = (x - self.game_area.x) / self.scale
        script_y = (y - self.game_area.y) / self.scale
        return round(script_x), round(script_y)
