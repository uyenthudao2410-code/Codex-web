def select_timeout(value, default=30):
    if value is None:
        return default
    if value <= 0:
        return default
    return value
