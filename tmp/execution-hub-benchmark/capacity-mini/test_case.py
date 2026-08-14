from case import remaining_capacity

assert remaining_capacity(10, 3) == 7
assert remaining_capacity(10, 10) == 0
assert remaining_capacity(10, 15) == 0
print("PASS")
