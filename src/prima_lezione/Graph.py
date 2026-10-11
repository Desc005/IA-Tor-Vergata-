class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node):
        if node not in self.nodes:
            self.nodes[node] = []
            self.edges[node] = []

    def add_edge(self, from_node, to_node):
        if from_node in self.nodes and to_node in self.nodes:
            self.edges[from_node].append(to_node)
            self.edges[to_node].append(from_node)

    def get_neighbors(self, node):
        return self.edges.get(node, [])

    def __str__(self):
        return f"Nodes: {list(self.nodes.keys())}, Edges: {self.edges}"