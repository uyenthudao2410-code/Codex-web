def select_timeout(value, default=30):
    if value is None or value <= 0:
        return default
    return value
