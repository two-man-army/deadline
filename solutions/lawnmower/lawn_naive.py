n, m = [int(p) for p in input().split()]
test_case_count = int(input())
lawn = []
for _ in range(n):
    lawn.append([int(p) for p in input().split()])
from datetime import datetime
st = datetime.now()
def sum_region(k, l, i, j):
    sum = 0
    for i in range(k, i+1):
        for j in range(l, j+1):
            sum += lawn[i][j]
    return sum


for _ in range(test_case_count):
    k, l, i, j = [int(p) for p in input().split()]
    print(sum_region(k, l, i, j))

#print(datetime.now()-st)