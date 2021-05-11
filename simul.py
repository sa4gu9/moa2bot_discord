from modules import reinforce
import numpy as np
import math

level = 1
cost = 0

costarray = np.array([])


while costarray.size != 100000:
    result = reinforce.DoReinfoce(level)[0]
    price = math.floor(1000 * ((50 * level) ** (0.05 * level)))

    cost += price

    if result == -10:
        level = 1
    else:
        level += result

    if level == 20:
        costarray = np.append(costarray, cost)
        cost = 0
        level = 1

print(np.percentile(costarray, 10))
print(np.percentile(costarray, 50))
print(np.percentile(costarray, 90))
