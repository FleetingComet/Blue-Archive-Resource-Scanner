# port from:
# https://github.com/Fate-Grand-Automata/FGA/blob/master/libautomata/src/main/java/io/github/lib_automata/Region.kt
# https://github.com/Fate-Grand-Automata/FGA/blob/master/libautomata/src/main/java/io/github/lib_automata/Location.kt
# and https://github.com/Fate-Grand-Automata/FGA/blob/master/libautomata/src/main/java/io/github/lib_automata/Size.kt

import random
from dataclasses import dataclass
from functools import total_ordering
from math import isclose


@dataclass(frozen=True, slots=True)
@total_ordering
class Location:
    x: float = 0
    y: float = 0

    def __add__(self, other: "Location") -> "Location":
        return Location(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Location") -> "Location":
        return Location(self.x - other.x, self.y - other.y)

    def __mul__(self, scale: float) -> "Location":
        return Location(
            round(self.x * scale),
            round(self.y * scale),
        )

    def __lt__(self, other: "Location"):
        if not isinstance(other, Location):
            return NotImplemented
        return (self.x, self.y) < (other.x, other.y)

    def __eq__(self, other: "Location"):
        if not isinstance(other, Location):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)

    @property
    def center(self) -> "Location":
        """A Location is already a point, so its center is itself."""
        return self

    @property
    def right(self):
        """A Location is already a point"""
        return self

    @property
    def bottom(self):
        """A Location is already a point"""
        return self

    def random_point(self, offset: int = 5) -> "Location":
        return Location(
            self.x + random.randint(-offset, offset),
            self.y + random.randint(-offset, offset),
        )

    def __repr__(self):
        return f"Location(x={self.x}, y={self.y})"

    def x_from_center(self, width: float) -> "Location":
        return Location(self.x - (width / 2), self.y)

    def x_from_right(self, width: float) -> "Location":
        return Location(width - self.x, self.y)

    def y_from_center(self, height: float) -> "Location":
        return Location(self.x, self.y - (height / 2))

    def y_from_bottom(self, height: float) -> "Location":
        return Location(self.x, height - self.y)


class Size:
    def __init__(self, width: int, height: int):
        if not isinstance(width, (int, float)):
            raise TypeError(
                f"Width must be a number, got {type(width).__name__} instead."
            )
        if not isinstance(height, (int, float)):
            raise TypeError(
                f"Height must be a number, got {type(height).__name__} instead."
            )

        self.width = width
        self.height = height

    def __mul__(self, scale):
        return Size(round(self.width * scale), round(self.height * scale))

    # game area screen stuffs
    # def wider_than(self, x, y):
    #     """Checks if the size is wider than the given aspect ratio x:y."""
    #     return self.width / self.height > x / y

    def __repr__(self):
        return f"Size(width={self.width}, height={self.height})"


@dataclass(frozen=True, slots=True)
class Region:
    x: float
    y: float
    width: float
    height: float

    @classmethod
    def from_location_and_size(cls, location: Location, size: Size):
        return cls(location.x, location.y, size.width, size.height)

    @property
    def location(self):
        return Location(self.x, self.y)

    @property
    def size(self):
        return Size(self.width, self.height)

    @property
    def center(self):
        center_x = self.x + self.width / 2
        center_y = self.y + self.height / 2
        return Location(center_x, center_y)

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    def __iter__(self):
        return iter((self.x, self.y, self.width, self.height))

    def __add__(self, location: Location):
        return Region.from_location_and_size(self.location + location, self.size)

    def __sub__(self, location: Location):
        return Region.from_location_and_size(self.location - location, self.size)

    def __mul__(self, scale: float):
        return Region(
            round(self.x * scale),
            round(self.y * scale),
            round(self.width * scale),
            round(self.height * scale),
        )

    def __contains__(self, region: "Region"):
        return (
            self.x <= region.x
            and self.y <= region.y
            and self.right >= region.right
            and self.bottom >= region.bottom
        )

    def __eq__(self, other):
        return (
            isinstance(other, Region)
            and isclose(self.x, other.x)
            and isclose(self.y, other.y)
            and isclose(self.width, other.width)
            and isclose(self.height, other.height)
        )

    def __lt__(self, other: "Region"):
        return self.location < other.location

    def __gt__(self, other: "Region"):
        return self.location > other.location

    def __repr__(self):
        return (
            f"Region(x={self.x}, y={self.y}, width={self.width}, height={self.height})"
        )

    def clip(self, region):
        left = max(self.x, min(region.x, self.right - 1))
        right = min(self.right, max(region.right, self.x + 1))
        top = max(self.y, min(region.y, self.bottom - 1))
        bottom = min(self.bottom, max(region.bottom, self.y + 1))

        return Region(left, top, right - left, bottom - top)

    def contains_point(self, loc: Location):
        return self.x <= loc.x <= self.right and self.y <= loc.y <= self.bottom

    def random_point(self, offset: int = 5) -> Location:
        dx = random.randint(-offset, offset)
        dy = random.randint(-offset, offset)
        return self.center + Location(dx, dy)

    def x_from_center(self, screen_width: float) -> "Region":
        return Region(
            x=self.x - (screen_width / 2),
            y=self.y,
            width=self.width,
            height=self.height,
        )

    def x_from_right(self, screen_width: float) -> "Region":
        return Region(
            x=screen_width - self.x,
            y=self.y,
            width=self.width,
            height=self.height,
        )

    def y_from_center(self, screen_height: float) -> "Region":
        return Region(
            x=self.x,
            y=self.y - (screen_height / 2),
            width=self.width,
            height=self.height,
        )

    def y_from_bottom(self, screen_height: float) -> "Region":
        return Region(
            x=self.x,
            y=screen_height - self.y,
            width=self.width,
            height=self.height,
        )
