# plot_map.py
import networkx as nx
from map_data import DISTANCES

def build_graph():
    """Tạo đồ thị với trọng số từ danh sách khoảng cách giữa các tỉnh."""
    graph = nx.Graph()
    for (province1, province2), distance in DISTANCES.items():
        graph.add_edge(province1, province2, weight=distance)
    return graph
