from dataclasses import dataclass

from src.constant import SCRIPT_SIZE
from src.core.area import Location, Region
from src.core.game_area import GameAreaManager


@dataclass
class ScriptTransform:
    """
    Transforms coordinates relative to the dynamic game area (center, right, bottom).
    """

    _manager: GameAreaManager | None = None
    default_size = SCRIPT_SIZE

    def set_manager(self, manager) -> None:
        self._manager = manager

    @property
    def is_wide(self) -> bool:
        return self._manager.is_wide if self._manager else False

    @property
    def wide_factor(self) -> float:
        return self._manager.wide_factor if self._manager else 0.0

    # @property
    # def is_ultra_wide(self) -> bool:
    #     return self._manager.is_ultra_wide if self._manager else False

    @property
    def script_width(self) -> float:
        """Script-space width of the full screen, ignoring borders/insets.

        Use this for aspect-ratio decisions and UI interpolation.
        Use `game_width` (game-area based) for image cropping / game-area math.
        """
        if self._manager is not None:
            return self._manager.screen_size.width / self._manager.scale
        return self.default_size.width

    @property
    def script_height(self) -> float:
        """Script-space height of the full screen, ignoring borders/insets.

        Use this for aspect-ratio decisions and UI interpolation.
        Use `game_height` (game-area based) for image cropping / game-area math.
        """
        if self._manager is not None:
            return self._manager.screen_size.height / self._manager.scale
        return self.default_size.height

    @property
    def game_width(self) -> float:
        if self._manager is not None:
            return self._manager.game_area.width / self._manager.scale
        return self.default_size.width

    @property
    def game_height(self) -> float:
        if self._manager is not None:
            return self._manager.game_area.height / self._manager.scale
        return self.default_size.height

    @property
    def center(self) -> Location:
        return Location(self.game_width / 2, self.game_height / 2)

    @property
    def right(self) -> float:
        return self.game_width

    @property
    def bottom(self) -> float:
        return self.game_height

    def x_from_center(self, loc: Location) -> Location:
        return loc + Location(self.center.x, 0)

    def x_from_right(self, loc: Location) -> Location:
        return loc + Location(self.right, 0)

    def y_from_center(self, loc: Location) -> Location:
        return loc + Location(0, self.center.y)

    def y_from_bottom(self, loc: Location) -> Location:
        return loc + Location(0, self.bottom)

    # Region versions
    def region_x_from_center(self, region: Region) -> Region:
        return region + Location(self.center.x, 0)

    def region_x_from_right(self, region: Region) -> Region:
        return region + Location(self.right, 0)

    def region_y_from_center(self, region: Region) -> Region:
        return region + Location(0, self.center.y)

    def region_y_from_bottom(self, region: Region) -> Region:
        return region + Location(0, self.bottom)


SCRIPT = ScriptTransform()
