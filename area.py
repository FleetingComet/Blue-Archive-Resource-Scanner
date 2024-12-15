# port from:
# https://github.com/Fate-Grand-Automata/FGA/blob/master/libautomata/src/main/java/io/github/lib_automata/Region.kt
# https://github.com/Fate-Grand-Automata/FGA/blob/master/libautomata/src/main/java/io/github/lib_automata/Location.kt
# and https://github.com/Fate-Grand-Automata/FGA/blob/master/libautomata/src/main/java/io/github/lib_automata/Size.kt

from math import isclose


class Location:
    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Location(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Location(self.x - other.x, self.y - other.y)

    def __mul__(self, scale: float):
        return Location(
            round(self.x * scale),
            round(self.y * scale),
        )

    # def x_from_center(self, screen_width):
    #     """Calculate x position from the center of the screen."""
    #     center_x = screen_width / 2
    #     return self.x - center_x

    # def x_from_right(self, screen_width):
    #     """Calculate x position from the right of the screen."""
    #     return screen_width - self.x

    def __repr__(self):
        return f"Location(x={self.x}, y={self.y})"


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

    # this function is for game area which is Soon™
    # @property
    # def xFromCenter(self) -> Location:
    #     return Location(self.center.x, 0)

    # @property
    # def xFromRight(self) -> Location:
    #     return Location(self.right, 0)

    # @property
    # def yFromBottom(self) -> Location:
    #     return Location(0, self.bottom)

    # @property
    # def yFromCenter(self) -> Location:
    #     return Location(0, self.center.y)

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
