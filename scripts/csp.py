# from simpleai.search import (CspProblem, backtrack, convert_to_binary,
#     min_conflicts, MOST_CONSTRAINED_VARIABLE)
import random
from collections import defaultdict
import hashlib
import sys 

def compute_merkle_root(values):
    for i in range(0, len(values), 2):
        hashlib.sha256(values[i] + values[i + 1])
    pass

def sum_constraint_wrapper(sum_):
    def sum_equals(variables, values):
        return sum(values) == sum_
    return sum_equals

def all_diff(variables, values):
    return len(set(values)) == len(values)

def merkle_root(variables, values):
    pass
    
n = 250
k = 3
c = int(n * 1.0)
print("n Buckets: ", c)
print("\n")
extractor = 0xFFFF

def encode(variables):
    sender_buckets = defaultdict(int)
    for i, var in enumerate(variables):
        buckets = []
        j = 0
        while len(buckets) < k:
            byte_shift = 8 * j
            bucket = (var & (extractor << byte_shift)) >> byte_shift
            bucket = bucket % c
            if bucket not in buckets:
                buckets.append(bucket)
            j += 1

        for bucket in buckets:
            sender_buckets[bucket] += i
    return sender_buckets

def simplify_equations(buckets):
    assigned = {}
    def substitute_var_in_buckets(var, value):
        for bucket, items in buckets.items():
            if var in items['vars']:
                items['vars'].remove(var)
                items['sum'] -= value

    reducible = True
    while reducible:
        reducible = False
        for bucket, items in buckets.items():
            if len(items['vars']) == 1:
                assigned[items['vars'][0]] = items['sum']
                substitute_var_in_buckets(items['vars'][0], items['sum'])
                reducible = True

    return assigned

def decode(variables, sender_buckets):
    receiver_buckets = defaultdict(dict)
    for bucket, sum_ in sender_buckets.items():
        receiver_buckets[bucket]['sum'] = sum_
        receiver_buckets[bucket]['vars'] = []

    for var in variables:
        buckets = []
        j = 0
        while len(buckets) < k:
            byte_shift = 8 * j
            bucket = (var & (extractor << byte_shift)) >> byte_shift
            bucket = bucket % c
            if bucket not in buckets:
                buckets.append(bucket)
            j += 1

        for bucket in buckets:
            receiver_buckets[bucket]['vars'].append(var)
    return receiver_buckets

if __name__ == '__main__':
    variables = [random.getrandbits(256) for i in range(n)]
    ordered_vars = list(variables)
    random.shuffle(ordered_vars)
    sender_buckets = encode(ordered_vars)
    receiver_buckets = decode(variables, sender_buckets)
    assigned = simplify_equations(receiver_buckets)
    if len(assigned) == len(ordered_vars):
        li = sorted(list(assigned.keys()), key=lambda x: assigned[x])
        print(ordered_vars == li)
        print("No need to guess")
        sys.exit(0)
    else:
        print("Only %d simplified" % len(assigned))
        domains = set(range(n)) - set(assigned.values())
        print("To guess: ", len(domains))
        constraints = []
        for bucket, items in receiver_buckets.items():
            if len(items['vars']) == 2:
                constraints.append((items['vars'], items['sum']))
        print("Constraints: ", len(constraints))
        sys.exit(1)

  '''      
        constraints.append((variables, all_diff))
        domains = {var: list(range(n)) for var in variables}
        problem = CspProblem(variables, domains, constraints)
        # print(convert_to_binary(variables, domains, constraints))
        print("Initial Assignments", len(assignment))
        print("Constraints", len(constraints))
        inf_assignment = backtrack(problem,
            variable_heuristic=MOST_CONSTRAINED_VARIABLE)
        print(inf_assignment)
        print(assignment)
        assignment.update(inf_assignment)
        print(len(assignment))
   '''
