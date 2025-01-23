from dataclasses import dataclass
from math import isclose


@dataclass(order=True)
class Location:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    @property
    def x(self):
        return self.x

    @property
    def y(self):
        return self.y

    def __add__(self, other):
        return Location(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Location(self.x - other.x, self.y - other.y)


@dataclass
class Size:
    width: int
    height: int


class Region:
    def __init__(self, x: int, y: int, width: int, height: int):
        if width <= 0:
            raise ValueError("width must be positive")
        if height <= 0:
            raise ValueError("height must be positive")
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @classmethod
    def from_location_and_size(cls, location: Location, size: Size):
        return cls(location.x, location.y, size.width, size.height)

    def __mul__(self, scale: float):
        return Region(
            round(self.x * scale),
            round(self.y * scale),
            round(self.width * scale),
            round(self.height * scale),
        )

    def __add__(self, location: Location):
        return Region.from_location_and_size(self.location + location, self.size)

    def __sub__(self, location: Location):
        return Region.from_location_and_size(self.location - location, self.size)

    @property
    def location(self):
        return Location(self.x, self.y)

    @property
    def size(self):
        return Size(self.width, self.height)

    @property
    def center(self):
        return self.x + self.width // 2, self.y + self.height // 2

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    def clip(self, region):
        left = max(self.x, min(region.x, self.right - 1))
        right = min(self.right, max(region.right, self.x + 1))
        top = max(self.y, min(region.y, self.bottom - 1))
        bottom = min(self.bottom, max(region.bottom, self.y + 1))

        return Region(left, top, right - left, bottom - top)

    def __contains__(self, region):
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

    def __lt__(self, other):
        return self.location < other.location

    @classmethod
    def xFromCenter(self) -> Location:
        return Location(self.center, 0)

    @classmethod
    def xFromRight(self) -> Location:
        return Location(self.right, 0)

    @classmethod
    def yFromBottom(self) -> Location:
        return Location(0, self.bottom)

    def to_dict(self):
        """Convert Region data to a dictionary."""
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}
