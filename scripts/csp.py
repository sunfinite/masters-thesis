from simpleai.search import CspProblem, backtrack, convert_to_binary
import random
from collections import defaultdict
import sys 

def sum_constraint_wrapper(sum_):
    def sum_equals(variables, values):
        return sum(values) == sum_
    return sum_equals

def all_diff(variables, values):
    return len(set(values)) == len(values)
    
n = 100
k = 3
c = 150

variables = [random.getrandbits(40) for i in range(n)]
ordered_vars = list(variables)
random.shuffle(ordered_vars)
bucket_map = defaultdict(dict)
for var in variables:
    print(var)
    cells = []
    while len(cells) < k:
        byte_shift = 8 * len(cells)
        cell = (var & (0xFF << byte_shift)) >> byte_shift
        if cell not in cells:
            cells.append(cell)

    for cell in cells:
        bucket_map[cell][var] = ordered_vars.index(var)

domains = {var: list(range(n)) for var in variables}
constraints = []
for key, items in bucket_map.items():
    vars_ = items.keys()
    indices = items.values()
    constraints.append((vars_, 
        sum_constraint_wrapper(sum(indices))))

constraints.append((variables, all_diff))

problem = CspProblem(variables, domains, constraints)
# print(convert_to_binary(variables, domains, constraints))
for constraint in constraints:
    if len(constraint[0]) == 1:
        print("Unary")
    elif len(constraint[0]) == 2:
        print("Binary")
print(len(constraints))
print(backtrack(problem))
print(ordered_vars)
