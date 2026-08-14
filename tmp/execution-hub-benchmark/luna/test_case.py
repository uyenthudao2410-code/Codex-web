from case import normalize_score

assert normalize_score(-5) == 0
assert normalize_score(50) == 50
assert normalize_score(120) == 100
print("PASS")
