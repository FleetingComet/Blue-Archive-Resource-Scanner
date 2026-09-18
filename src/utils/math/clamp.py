# @see https://stackoverflow.com/questions/4092528/how-can-i-clamp-clip-restrict-a-number-to-some-range#comment53230306_4092550
def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    return max(min_val, min(max_val, value))
