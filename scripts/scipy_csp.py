# from simpleai.search import (CspProblem, backtrack, convert_to_binary,
#     min_conflicts, MOST_CONSTRAINED_VARIABLE)
import random
from collections import defaultdict
import hashlib
import sys 
from scipy.sparse.linalg import cg
import numpy as np

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
    
n = 200
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


def simplify_equations(buckets, assigned={}, constraints=None):
    def substitute_var_in_buckets(var, value):
        for bucket, items in buckets.items():
            if var in items['vars']:
                items['vars'].remove(var)
                items['sum'] -= value

    for var in assigned:
        substitute_var_in_buckets(var, assigned[var])

    reducible = True
    while reducible:
        reducible = False
        for bucket, items in buckets.items():
            if len(items['vars']) == 1:
                assigned[items['vars'][0]] = items['sum']
                substitute_var_in_buckets(items['vars'][0], items['sum'])
                reducible = True
				
    for bucket, items in buckets.items():
        if constraints and len(items['vars']) == 2:
            constraints.append((items['vars'], items['sum']))

    return assigned

def select_variable(constraints):
    d = {}
    for item in constraints:
        # print(item)
        for var in item[0]:
            try:
                d[var] += 1
            except KeyError:
                d[var] = 1
    # print(max(d, key=d.get), d[max(d, key=d.get)])
    return max(d, key=d.get)

def infer(assignment, constraints, domains):
    inferences = {}
    reducible = True
    while reducible:
        reducible = False
        for constraint in constraints:
            if len(constraint[0]) != 2:
                continue
            item1, item2 = constraint[0]
            if item1 in assignment.keys():
                if item2 in assignment or item2 in inferences or constraint[1] - assignment[item1] not in domains:
                    # print("*"*20,"FATAL ERROR!!!!!! INCOMPATIBLE VALUES","*"*20)
                    return False
                inferences[item2] = constraint[1] - assignment[item1]
                constraints.remove(constraint)
                reducible = True
            elif item2 in assignment.keys():
                if item1 in assignment or item1 in inferences or constraint[1] - assignment[item2] not in domains:
                    # print("*"*20,"FATAL ERROR!!!!!! INCOMPATIBLE VALUES","*"*20)
                    return False
                inferences[item1] = constraint[1] - assignment[item2]
                constraints.remove(constraint)
                reducible = True
            elif item1 in inferences.keys():
                if item2 in assignment or item2 in inferences or constraint[1] - inferences[item1] not in domains:
                    # print("*"*20,"FATAL ERROR!!!!!! INCOMPATIBLE VALUES","*"*20)
                    return False
                inferences[item2] = constraint[1] - inferences[item1]
                constraints.remove(constraint)
                reducible = True
            elif item2 in inferences.keys():
                if item1 in assignment or item1 in inferences or constraint[1] - inferences[item2] not in domains:
                    # print("*"*20,"FATAL ERROR!!!!!! INCOMPATIBLE VALUES","*"*20)
                    return False
                inferences[item1] = constraint[1] - inferences[item2]
                constraints.remove(constraint)
                reducible = True
    
    return inferences

"""def full_check(assignment, buckets, domains):
    check = {}
    reducible = True
    while reducible:
        reducible = False
        for bucket, items in buckets.items():
            if len(items['vars']) == 1:
                assigned[items['vars'][0]] = items['sum']
                substitute_var_in_buckets(items['vars'][0], items['sum'])
                reducible = True
    
    return check"""

def backtrack(assignment, buckets, constraints, domains):
    if len(constraints) == 0:
        return assignment

    var = select_variable(constraints) # mcv
    constraints_copy = constraints.copy()
    for i in range(len(domains)):
        assignment[var] = domains.pop()
        print("Setting ", var, "to ", assignment[var])
        print(len(constraints_copy))
        inferences = infer(assignment, constraints_copy, domains)
        print(len(constraints_copy))
        print(inferences)
        if inferences != False:
            for inf in inferences:
                domains.remove(inferences[inf])
                assignment[inf] = inferences[inf]
            #check = full_check(assignment, buckets, domains)
            #if check != False:
            assignment = simplify_equations(buckets.copy(), assignment, constraints)
            if all_diff(assignment):
                back = backtrack(assignment, buckets, constraints_copy, domains)
                if back != False:
                    return back
        domains.insert(0, assignment[var])
        assignment.pop(var)
        if inferences != False:
            for inf in inferences:
                domains.insert(0, inferences[inf])
                assignment.pop(inf)
    return False
    

def solve_binary(buckets, constraints, domains):
    return backtrack({}, buckets, constraints, domains)

"""def AC3(csp, queue=None):
    if queue == None:
        queue = [(Xi, Xk) for Xi in csp.vars for Xk in csp.neighbors[Xi]]
    while queue:
        (Xi, Xj) = queue.pop()
        if remove_inconsistent_values(csp, Xi, Xj):
            for Xk in csp.neighbors[Xi]:
                queue.append((Xk, Xi))

def remove_inconsistent_values(csp, Xi, Xj):
    "Return true if we remove a value."
    removed = False
    for x in csp.curr_domains[Xi][:]:
        # If Xi=x conflicts with Xj=y for every possible y, eliminate Xi=x
        if every(lambda y: not csp.constraints(Xi, x, Xj, y),
                csp.curr_domains[Xj]):
            csp.curr_domains[Xi].remove(x)
            removed = True
    return removed
"""


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

def check_assigned(assigned, ordered_vars):
    print("Checking assigned")
    li = sorted(list(assigned.keys()), key=lambda x: assigned[x])
    print(ordered_vars == li)
    return ordered_vars == li

def all_diff(assigned):
    return len(assigned.values()) == len(set(assigned.values()))

if __name__ == '__main__':
    variables = [random.getrandbits(256) for i in range(n)]
    ordered_vars = list(variables)
    random.shuffle(ordered_vars)
    sender_buckets = encode(ordered_vars)
    receiver_buckets = decode(variables, sender_buckets)
    rows = []
    sums = []
    for i in range(len(variables)):
        items = receiver_buckets.get(i)
        row = [0] * len(variables)
        if not items:
            rows.append(row)
            sums.append(0)
            continue
        for var in items['vars']:
            row[variables.index(var)] = 1
        rows.append(row)
        sums.append(items['sum'])
    print(rows)
    print(sums)
    rows = np.array(rows)
    sums = np.array(sums)
    print(rows.shape, sums.shape)
    # print(np.linalg.solve(rows, sums))
    print(cg(rows, sums))

    """assigned = simplify_equations(receiver_buckets)
    if len(assigned) == len(ordered_vars):
        check_assigned(assigned, ordered_vars)
    else:
        while True:
            print("Only %d simplified" % len(assigned))
            domains = sorted(list(set(range(n)) - set(assigned.values())))
            print("To guess: ", len(domains))
            constraints = []
            for bucket, items in receiver_buckets.items():
                # print(items)
                if len(items['vars']) == 2:
                    constraints.append((items['vars'], items['sum']))
            print("Binary Constraints: ", len(constraints))
            print ("Assigned: ", assigned)
            print ("Domains: ", domains)
            print ("Buckets: ", receiver_buckets)
            pre_length = len(assigned)
            solved = solve_binary(receiver_buckets, constraints, domains)
            print(solved)
            if solved:
                assigned.update(solved)
            assigned = simplify_equations(receiver_buckets, assigned)
            if len(assigned) == len(ordered_vars):
                check_assigned(assigned, ordered_vars)
                break
            if pre_length == len(assigned):
                print("No change in assigned, giving up")
                print(len(assigned))
                break
    """
    
