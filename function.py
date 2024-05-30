import math

class PairingHeapNode:
    def __init__(self, key, value):
        self.key: int = key
        self.value = value
        self.child = None
        self.sibling = None
        self.parent = None
        self.active = True  # Indicates if the node is still active in the heap
    
class PairingHeap:
    def __init__(self):
        self.root = None
        self.node_map = {}  # Maps values to nodes for quick access

    def is_empty(self):
        return self.root is None

    def merge(self, heap1, heap2):
        if not heap1:
            return heap2
        if not heap2:
            return heap1

        if heap1.key < heap2.key:
            heap2.parent = heap1
            heap2.sibling = heap1.child
            heap1.child = heap2
            return heap1
        else:
            heap1.parent = heap2
            heap1.sibling = heap2.child
            heap2.child = heap1
            return heap2

    def insert(self, key, value):
        new_node = PairingHeapNode(key, value)
        self.root = self.merge(self.root, new_node)
        self.node_map[value] = new_node

    def decrease_key(self, value, new_key):
        node = self.node_map.get(value)
        if node and node.active and node.key > new_key:
            node.key = new_key
            # Cut the node if it's not the root and merge it with the root
            if node.parent:
                # Detach from parent and siblings
                if node.sibling:
                    node.parent.child = node.sibling
                else:
                    node.parent.child = None
                node.parent = None
                node.sibling = None
                self.root = self.merge(self.root, node)

    def delete_min(self):
        if self.is_empty():
            return None

        min_node = self.root
        min_node.active = False  # Mark the node as inactive
        min_key, min_value = min_node.key, min_node.value
        self.node_map.pop(min_value, None)  # Remove from map

        if not self.root.child:
            self.root = None
        else:
            # Combine children into a new heap
            new_heap = None
            current = self.root.child
            while current:
                next_sibling = current.sibling
                current.sibling = None
                current.parent = None
                new_heap = self.merge(new_heap, current)
                current = next_sibling
            self.root = new_heap

        return min_key, min_value

    def display(self):
        def _display_helper(node):
            if not node:
                return []
            result = [node.value]
            result.extend(_display_helper(node.child))
            result.extend(_display_helper(node.sibling))
            return result
        return _display_helper(self.root)

    def find_min(self):
        if self.is_empty():
            return None
        return self.root.key, self.root.value
# #Example usage of pairing heap
# heap = PairingHeap()
# heap.insert(5, "apple")
# heap.insert(3, "banana")
# heap.insert(7, "cherry")
# heap.insert(1, "date")
# heap.insert(4, "elderberry")

# print(heap.find_min())  # (1, 'date')
# print(f"deleted: {heap.delete_min()}")
# print(heap.find_min())  # (3, 'banana')
# print(heap.display())   # ['banana', ('cherry', 'elderberry', 'apple']


def haversine(lon1, lat1, lon2, lat2):
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371 # Radius of Earth in kilometers. Use 3956 for miles
    return c * r

def find_closest_node(locations, current_location):
    closest_node = None
    min_distance = float('inf')
    
    for node, coords in locations.items():
        distance = haversine(current_location[0], current_location[1], coords['coords'][0], coords['coords'][1])
        if distance < min_distance:
            closest_node = node
            min_distance = distance
            
    return closest_node, min_distance

def dijkstra_with_path(graph, source, locations):
    inf = float('inf')
    distances = {vertex: inf for vertex in graph}
    distances[source] = 0
    previous = {vertex: None for vertex in graph}
    pairing_heap = PairingHeap()

    for vertex in graph:
        pairing_heap.insert(distances[vertex], vertex)

    while not pairing_heap.is_empty():
        min_distance, min_vertex = pairing_heap.delete_min()
        for neighbor in graph[min_vertex]:
            lat1, lon1 = locations[min_vertex]["coords"]
            lat2, lon2 = locations[neighbor]["coords"]
            weight = haversine(lon1, lat1, lon2, lat2)
            new_distance = min_distance + weight
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = min_vertex
                pairing_heap.decrease_key(neighbor, new_distance)

    return distances, previous


def reconstruct_path(previous, start, end):
    path = []
    current = end
    while current != start:
        path.append(current)
        current = previous[current]
        if current is None:
            return []  # No path exists
    path.append(start)
    path.reverse()
    return path