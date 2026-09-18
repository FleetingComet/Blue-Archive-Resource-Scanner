"""
Helper shortcuts
"""

from collections.abc import Callable

from src.core.area import Location, Region
from src.core.script_transform import SCRIPT
from src.utils.math.lerp import lerp_object

TargetType = Location | Region | Callable[[], Location | Region]
# Exactly the wide_factor at 18:9 (2.0 aspect ratio):
# (2.0 - 16/9) / ((2348/1080) - 16/9) = 60 / 107 ≈ 0.56075
T_18 = (2.0 - (16 / 9)) / ((2348 / 1080) - (16 / 9))


def cx(value: Location | Region) -> Location | Region:
    if isinstance(value, Location):
        return SCRIPT.x_from_center(value)

    return SCRIPT.region_x_from_center(value)


def cy(value: Location | Region) -> Location | Region:
    if isinstance(value, Location):
        return SCRIPT.y_from_center(value)

    return SCRIPT.region_y_from_center(value)


def rx(value: Location | Region) -> Location | Region:
    if isinstance(value, Location):
        return SCRIPT.x_from_right(value)

    return SCRIPT.region_x_from_right(value)


def by(value: Location | Region) -> Location | Region:
    if isinstance(value, Location):
        return SCRIPT.y_from_bottom(value)

    return SCRIPT.region_y_from_bottom(value)


def cxy(value: Location | Region) -> Location | Region:
    """Offsets BOTH X and Y from screen center."""
    return cy(cx(value))


class AspectTarget:
    """
    Interpolates any Location or Region smoothly between 16:9 and 2.174:1 (Max Wide).
    """

    def __init__(
        self,
        standard: TargetType,
        max_wide: TargetType | None = None,
        wide_18_9: TargetType | None = None,
    ):
        self._standard = standard
        self._max_wide = max_wide if max_wide is not None else standard
        self._wide_18_9 = wide_18_9

    def resolve(self) -> Location | Region:
        std = self._standard() if callable(self._standard) else self._standard
        if self._max_wide is None:
            return std

        t = SCRIPT.wide_factor
        if t <= 0.0:
            return std

        max_w = self._max_wide() if callable(self._max_wide) else self._max_wide

        if self._wide_18_9 is not None:
            w18 = self._wide_18_9() if callable(self._wide_18_9) else self._wide_18_9
            if t <= T_18:
                segment_t = t / T_18
                return lerp_object(std, w18, segment_t)
            else:
                segment_t = (t - T_18) / (1.0 - T_18)
                return lerp_object(w18, max_w, segment_t)
            
        return lerp_object(std, max_w, t)

    # Forward attributes and methods (e.g. .random_point(), .contains_point())
    def __getattr__(self, name: str):
        return getattr(self.resolve(), name)

    # Provide explicit properties for IDE autocomplete and type hints
    @property
    def x(self) -> float:
        return self.resolve().x

    @property
    def y(self) -> float:
        return self.resolve().y

    @property
    def width(self) -> float:
        res = self.resolve()
        return res.width if isinstance(res, Region) else 0.0

    @property
    def height(self) -> float:
        res = self.resolve()
        return res.height if isinstance(res, Region) else 0.0

    @property
    def center(self) -> Location:
        return self.resolve().center

    @property
    def location(self) -> Location:
        res = self.resolve()
        return res.location if isinstance(res, Region) else res

    # Support tuple unpacking: `x, y, w, h = TARGET.value` or `x, y = TARGET.value`
    def __iter__(self):
        res = self.resolve()
        if isinstance(res, Region):
            return iter((res.x, res.y, res.width, res.height))
        return iter((res.x, res.y))

    def __add__(self, other):
        return self.resolve() + other

    def __sub__(self, other):
        return self.resolve() - other

    def __repr__(self) -> str:
        return repr(self.resolve())


AspectRegion = AspectTarget
AspectLocation = AspectTarget
