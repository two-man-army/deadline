
"""
5 5
3 0 1 4 2
5 6 3 2 1
1 2 0 1 5
4 1 0 1 7
1 0 3 0 5
"""
n, m = [int(p) for p in input().split()]
test_case_count = int(input())
lawn = []
for _ in range(n):
    lawn.append([int(p) for p in input().split()])
from datetime import datetime
st = datetime.now()
sum_matrix = []
for i in range(len(lawn)+1):
    sum_matrix.append([0] * (len(lawn[0]) + 1))
from pprint import pprint


for i in range(1, len(sum_matrix)):
    for j in range(1, len(sum_matrix[0])):
        try:
            sum_matrix[i][j] = lawn[i - 1][j - 1] + sum_matrix[i][j - 1] + sum_matrix[i - 1][j] - sum_matrix[i - 1][j - 1]
        except IndexError:
            raise Exception(f'{i} {j} indices are max {len(sum_matrix)} {len(sum_matrix[0])} {len(sum_matrix[i])} )')


def sum_region(k, l, i, j):
    k, l, i, j = k+1, l+1, i+1, j+1
    return sum_matrix[i][j] - ((sum_matrix[k-1][j] + sum_matrix[i][l-1]) - sum_matrix[k-1][l-1])

for _ in range(test_case_count):
    k, l, i, j = [int(p) for p in input().split()]

    print(sum_region(k, l, i, j))
#print(datetime.now()-st)