from collections import deque


class BoundableObject:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.width = x2 - x1
        self.height = y2 - y1
        self.mid_x = x1 + (self.width//2)
        self.mid_y = y1 + (self.height//2)

    def __repr__(self):
        return '{x1} {y1} {x2} {y2}'.format(x1=self.x1, y1=self.y1, x2=self.x2, y2=self.y2)

    def intersects(self, other):
        return (self.x1 <= other.x2
                and other.x1 <= self.x2
                and self.y1 >= other.y2
                and other.y1 >= self.y2)

    def overlaps(self, other):
        return (self.x2 <= other.x2
                and self.x1 >= other.x1
                and self.y2 <= other.y2
                and self.y1 >= other.y1)

islands_c, queries = [int(p) for p in input().split()]

graph = {}
islands = []
# save islands
for i in range(islands_c):
    ax, ay, bx, by = [int(p) for p in input().split()]
    islands.append((i+1, BoundableObject(ax, ay, bx, by)))


# build graph
for idx, log_pair in enumerate(islands):
    # print(lo)
    log1_key, log = log_pair
    for idx_2 in range(idx+1, len(islands)):
        log2_key, log_2 = islands[idx_2]
        if log.intersects(log_2):
            # add to graph
            if log1_key not in graph:
                graph[log1_key] = []
            if log2_key not in graph:
                graph[log2_key] = []
            graph[log1_key].append(log2_key)
            graph[log2_key].append(log1_key)

def get_component(graph, start_node, searched_node):
    visited = set()

    st = deque()
    st.append(start_node)
    while len(st) > 0:
        node = st.popleft()
        if node == searched_node:
            return True
        if node in graph:
            for child in graph[node]:
                if child not in visited:
                    st.append(child)
                    visited.add(child)

    return False
for _ in range(queries):
    start_node, end_node = [int(p) for p in input().split()]
    print('YES' if get_component(graph, start_node, end_node) else 'NO')

