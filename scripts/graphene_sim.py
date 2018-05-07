import math
m = 0
n = 113

tau = 66
# c = 8 * 0.48
c = 8 * 0.48
alpha = n / (c * tau)
nBitsInBloom = n * -1 * math.log(alpha / abs(m - n)) / 0.48 # ln(2) ^ 2
nCells = 1.5 * alpha
print(alpha)
print(nBitsInBloom)
print(nCells)
