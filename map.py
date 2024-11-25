# map.py
import streamlit as st
import matplotlib.pyplot as plt
from map_data import DISTANCES, PROVINCES



def build_graph_from_distances(distances):
    """Tạo đồ thị từ danh sách khoảng cách giữa các tỉnh."""
    graph = {}
    for (start, end), weight in distances.items():
        if start not in graph:
            graph[start] = []
        if end not in graph:
            graph[end] = []
        graph[start].append((end, weight))
        graph[end].append((start, weight))  # Đồ thị vô hướng
    return graph

# Hàm Dijkstra
def dijkstra(graph, start, end):
    import heapq
    distances = {node: float('inf') for node in graph}
    previous_nodes = {node: None for node in graph}
    distances[start] = 0
    priority_queue = [(0, start)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)
        if current_node == end:
            break
        if current_distance > distances[current_node]:
            continue
        for neighbor, weight in graph[current_node]:
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(priority_queue, (distance, neighbor))

    path = []
    current = end
    while current is not None:
        path.append(current)
        current = previous_nodes[current]
    path.reverse()
    if distances[end] == float('inf'):
        return None, None
    return distances[end], path

# Đường dẫn ảnh bản đồ
IMAGE_PATH = "mien-bac.jpg"

# Tạo đồ thị từ dữ liệu
graph = build_graph_from_distances(DISTANCES)

# Tiêu đề ứng dụng
st.sidebar.title("Tìm đường đi ngắn nhất giữa các tỉnh phía Bắc Việt Nam")

# Hiển thị bản đồ
if st.sidebar.button("bản đồ"):
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(plt.imread(IMAGE_PATH), extent=[0, 15, 0, 12], alpha=0.8)

    for province, coord in PROVINCES.items():
        ax.text(coord[0], coord[1], province, fontsize=8, ha="center")
       # ax.scatter(coord[0], coord[1], color="blue", s=30)

    ax.axis("off")
    st.pyplot(fig)

# Chọn nơi đi và nơi đến
start = st.sidebar.selectbox("Chọn nơi đi", list(PROVINCES.keys()))
end = st.sidebar.selectbox("Chọn nơi đến", list(PROVINCES.keys()))

# Xử lý tìm đường đi ngắn nhất
if st.sidebar.button("Tìm đường đi ngắn nhất"):
    try:
        length, path = dijkstra(graph, start, end)
        if path is None:
            st.sidebar.error(f"Không tìm thấy đường đi từ {start} đến {end}.")
        else:
            st.sidebar.success(f"Đường đi ngắn nhất từ {start} đến {end}: {' -> '.join(path)}" ) #(Tổng khoảng cách: {length:.2f} km)")

            # Vẽ đường đi trên bản đồ
            fig, ax = plt.subplots(figsize=(10, 8)) 
            ax.imshow(plt.imread(IMAGE_PATH), extent=[0, 15, 0, 12], alpha=0.8)

            for province, coord in PROVINCES.items():
                ax.text(coord[0], coord[1], province, fontsize=8, ha="center")
                ax.scatter(coord[0], coord[1], color="blue", s=30)

            for i in range(len(path) - 1):
                x1, y1 = PROVINCES[path[i]]
                x2, y2 = PROVINCES[path[i + 1]]
                ax.plot([x1, x2], [y1, y2], color="red", linewidth=2)

            ax.axis("off")
            st.pyplot(fig)

    except Exception as e:
        st.sidebar.error(f"Lỗi: {e}")
