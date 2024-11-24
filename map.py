# map.py
import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
import networkx as nx
from plot_map import build_graph
from map_data import PROVINCES

# Đường dẫn ảnh bản đồ và icon
IMAGE_PATH = "mien-bac.jpg"

# Tạo đồ thị từ dữ liệu
graph = build_graph()

# Tiêu đề ứng dụng
st.sidebar.title("Tìm đường đi ngắn nhất giữa các tỉnh phía Bắc Việt Nam")

# Nút hiển thị bản đồ ban đầu
if st.sidebar.button("bản đồ"):
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(plt.imread(IMAGE_PATH), extent=[0, 15, 0, 12], alpha=0.8)

    for province, coord in PROVINCES.items():
        ax.text(coord[0], coord[1], province, fontsize=8, ha="center")
        #ax.scatter(coord[0], coord[1], color="red", s=5)

    ax.axis("off")
    st.pyplot(fig)

# Chọn nơi đi và nơi đến
start = st.sidebar.selectbox("Chọn nơi đi", list(PROVINCES.keys()))
end = st.sidebar.selectbox("Chọn nơi đến", list(PROVINCES.keys()))

# Biến trạng thái kiểm tra vẽ đường đi
show_route = False

# Xử lý khi nhấn nút "Tìm đường đi ngắn nhất"
if st.sidebar.button("Tìm đường đi ngắn nhất"):
    try:
        # Tìm đường đi ngắn nhất
        length, route = nx.single_source_dijkstra(graph, source=start, target=end, weight='weight')
        st.sidebar.success(f"Đường đi ngắn nhất từ {start} đến {end}: {' -> '.join(route)} ")#(Tổng khoảng cách: {length:.2f} km)")

        # Hiển thị đường đi trên bản đồ
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.imshow(plt.imread(IMAGE_PATH), extent=[0, 15, 0, 12], alpha=0.8)

        # Vẽ các tỉnh
        for province, coord in PROVINCES.items():
            ax.text(coord[0], coord[1], province, fontsize=8, ha="center")
            ax.scatter(coord[0], coord[1], color="blue", s=30)

        # Vẽ đường đi
        for i in range(len(route) - 1):
            x1, y1 = PROVINCES[route[i]]
            x2, y2 = PROVINCES[route[i + 1]]
            ax.plot([x1, x2], [y1, y2], color="red", linewidth=2)

        ax.axis("off")
        st.pyplot(fig)

    except nx.NetworkXNoPath:
        st.sidebar.error(f"Không tìm thấy đường đi từ {start} đến {end}.")
