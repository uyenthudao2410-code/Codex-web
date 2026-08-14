from case import select_timeout

assert select_timeout(None) == 30
assert select_timeout(0) == 30
assert select_timeout(-5) == 30
assert select_timeout(15) == 15
print("PASS")
