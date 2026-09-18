from typing import TypeAlias

from src.core.area import Location, Region

T: TypeAlias = Location | Region | float  # noqa: UP040 for Python 3.12 below


# @see https://en.cppreference.com/cpp/numeric/lerp
def lerp(a: float, b: float, t: float) -> float:
    """
    Computes linear interpolation between a and b.
    Clamps exact boundary values to prevent floating-point drift.
    """
    if t <= 0.0:
        return float(a)
    if t >= 1.0:
        return float(b)

    return a + (t * (b - a))


def lerp_object(a: T, b: T, t: float, round_pixels: bool = True) -> T:
    """
    Interpolate between two objects of the same type (float, int, Location, Region).
    For Location and Region, rounds to integer pixels by default.
    """
    if type(a) is not type(b):
        raise TypeError(
            f"Cannot lerp different types: {type(a).__name__} and {type(b).__name__}"
        )

    # Fast-path boundaries
    if t <= 0.0:
        return a
    if t >= 1.0:
        return b

    if isinstance(a, Location) and isinstance(b, Location):
        rx = lerp(a.x, b.x, t)
        ry = lerp(a.y, b.y, t)
        return Location(
            round(rx) if round_pixels else rx, round(ry) if round_pixels else ry
        )

    if isinstance(a, Region):
        rx = lerp(a.x, b.x, t)
        ry = lerp(a.y, b.y, t)
        rw = lerp(a.width, b.width, t)
        rh = lerp(a.height, b.height, t)
        if round_pixels:
            return Region(x=round(rx), y=round(ry), width=round(rw), height=round(rh))

        return Region(x=rx, y=ry, width=rw, height=rh)

    # Primitive numbers (float / int)
    val = lerp(float(a), float(b), t)
    return round(val) if isinstance(a, int) and round_pixels else val