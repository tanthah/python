import streamlit as st
import matplotlib.pyplot as plt
from map_data import DISTANCES, PROVINCES
from matplotlib.patches import Rectangle
import heapq

# thuật toán xây dựng bản đồ
def build_graph_from_distances(distances):
    graph = {}
    for (start, end), weight in distances.items():
        if start not in graph:
            graph[start] = []
        if end not in graph:
            graph[end] = []
        graph[start].append((end, weight))
        graph[end].append((start, weight))
    return graph

# hàm dijkstra
def dijkstra(graph, start, end):
    
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

IMAGE_PATH = "mien-bac.jpg"
graph = build_graph_from_distances(DISTANCES)

st.sidebar.title("Tìm đường đi ngắn nhất giữa các tỉnh phía Bắc Việt Nam")

if 'show_path' not in st.session_state:
    st.session_state.show_path = False
if 'current_path' not in st.session_state:
    st.session_state.current_path = None
if 'reset_view' not in st.session_state:
    st.session_state.reset_view = False

map_container = st.container()

st.sidebar.write("Điều khiển thu phóng và di chuyển")
if st.session_state.reset_view:
    zoom_level = st.sidebar.slider("Mức độ thu phóng", 1.0, 5.0, 1.0, 0.1, key='zoom')
    x_center = st.sidebar.slider("Di chuyển ngang", 0.0, 15.0, 7.5, 0.1, key='x_center')
    y_center = st.sidebar.slider("Di chuyển dọc", 0.0, 12.0, 6.0, 0.1, key='y_center')
    st.session_state.reset_view = False
else:
    zoom_level = st.sidebar.slider("Mức độ thu phóng", 1.0, 5.0, 1.0, 0.1, key='zoom')
    x_center = st.sidebar.slider("Di chuyển ngang", 0.0, 15.0, 7.5, 0.1, key='x_center')
    y_center = st.sidebar.slider("Di chuyển dọc", 0.0, 12.0, 6.0, 0.1, key='y_center')

# hiển thị bản đồ 
def display_map(show_path=False):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    width = 15 / zoom_level
    height = 12 / zoom_level
    x_min = x_center - width/2
    x_max = x_center + width/2
    y_min = y_center - height/2
    y_max = y_center + height/2
    
    ax.imshow(plt.imread(IMAGE_PATH), extent=[0, 15, 0, 12], alpha=0.8)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    
    for province, coord in PROVINCES.items():
        if x_min <= coord[0] <= x_max and y_min <= coord[1] <= y_max:
            ax.text(coord[0], coord[1], province, fontsize=8*zoom_level, ha="center")
            #ax.scatter(coord[0], coord[1], color="blue", s=30*zoom_level)
    
    if show_path and st.session_state.current_path:
        path = st.session_state.current_path
        for i in range(len(path) - 1):
            x1, y1 = PROVINCES[path[i]]
            x2, y2 = PROVINCES[path[i + 1]]
            ax.plot([x1, x2], [y1, y2], color="red", linewidth=2*zoom_level)
    
    ax.axis("off")
    
    return fig

if st.sidebar.button("Reset bản đồ"):
    st.session_state.show_path = False
    st.session_state.reset_view = True
    st.rerun()

start = st.sidebar.selectbox("Chọn nơi đi", list(PROVINCES.keys()))
end = st.sidebar.selectbox("Chọn nơi đến", list(PROVINCES.keys()))

if st.sidebar.button("Tìm đường đi ngắn nhất"):
    try:
        length, path = dijkstra(graph, start, end)
        if path is None:
            st.sidebar.error(f"Không tìm thấy đường đi từ {start} đến {end}.")
        else:
            st.sidebar.success(f"Đường đi ngắn nhất từ {start} đến {end}: {' -> '.join(path)}")
            st.session_state.current_path = path
            st.session_state.show_path = True
    except Exception as e:
        st.sidebar.error(f"Lỗi: {e}")

with map_container:
    st.pyplot(display_map(st.session_state.show_path))