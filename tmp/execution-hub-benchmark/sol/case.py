def normalize_score(value):
    if value < 0:
        return 100
    if value > 100:
        return 0
    return value
