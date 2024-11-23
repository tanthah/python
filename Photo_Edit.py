
import os
import io
import numpy as np
import streamlit as st
from rembg import remove
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ImageFilter


# Tiêu đề ứng dụng
st.title("✨ Ứng dụng chỉnh sửa ảnh ✨")

# Tải ảnh lên
uploaded_file = st.file_uploader("📂 Tải ảnh lên", type=["jpg", "jpeg", "png"])


if uploaded_file:
    # Mở ảnh và chuyển đổi sang định dạng RGBA
    try:
        image = Image.open(uploaded_file).convert("RGBA")
    except Exception as e:
        st.error("Tệp không phải là hình ảnh hợp lệ!")


    # Tạo một slider cho người dùng để điều chỉnh tỷ lệ thu nhỏ/phóng to ảnh
    scale_factor = st.slider("Chỉnh tỷ lệ ảnh:", 0.01, 1.5, 1.0, 0.05)  # Từ 10% đến 150% với bước 10%

    # Tính toán kích thước mới
    width, height = image.size
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)

    # Thu nhỏ hoặc phóng to ảnh theo tỷ lệ
    image_resized = image.resize((new_width, new_height))

    # Hiển thị ảnh cần chỉnh sửa
    #st.image(image_resized, caption="Ảnh gốc", use_container_width=False)

    # Tạo ảnh tạm để lưu thay đổi
    edited_image = image.copy()
        
    # Tiêu đề thanh bên
    st.sidebar.title("🎨 Tùy chỉnh ảnh")

    if st.sidebar.checkbox("✂️ Cắt ảnh"):
        st.sidebar.write("Kéo thả lớp phủ để chọn vùng cắt.")
        image_back = edited_image
        # Chọn loại cắt
        shape_option = st.sidebar.radio(
            "Chọn hình dạng cắt",
            ["Hình chữ nhật", "Hình tròn"]
        )

        # Nếu người dùng chọn cắt hình chữ nhật
        if shape_option == "Hình chữ nhật":
            st.sidebar.write("Kéo thả lớp phủ để chọn vùng cắt.")
            canvas_result = st_canvas(
                fill_color="rgba(0, 0, 0, 0.1)",        # màu lớp phủ
                stroke_width=1,                         # độ dày viền
                stroke_color="#FFFFFF",                 # màu viền 
                background_image=image_back,          
                update_streamlit=True,
                height=image_back.height,
                width=image_back.width,
                drawing_mode="rect",                    # chế độ vẽ hình chữ nhật
                key="crop_canvas_rect",                 # khóa 
            )
            if canvas_result.json_data is not None:
                rects = canvas_result.json_data.get('objects', [])
                if rects:
                    rect = rects[0]
                    x1, y1 = rect['left'], rect['top']
                    width, height = rect['width'], rect['height']
                    x2, y2 = x1 + width, y1 + height
                    edited_image = edited_image.crop((x1, y1, x2, y2))

        # Nếu người dùng chọn cắt hình tròn
        elif shape_option == "Hình tròn":
            st.sidebar.write("Kéo thả lớp phủ để chọn vùng cắt hình tròn.")
            canvas_result = st_canvas(
                fill_color="rgba(0, 0, 0, 0.1)",  
                stroke_width=1,                  
                stroke_color="#FFFFFF",        
                background_image=image_back,   
                update_streamlit=True,
                height=image_back.height,
                width=image_back.width,
                drawing_mode="circle",  
                key="crop_canvas_circle",
            )
            
            if canvas_result.json_data is not None:
                circles = canvas_result.json_data.get('objects', [])
                if circles:
                    # Lấy đối tượng vòng tròn đầu tiên
                    circle = circles[0]
                    x, y = circle['left'], circle['top']
                    radius = circle['radius']
                    
                    # Đảm bảo bán kính là dương, khác 0 và chuyển đổi nó thành số nguyên
                    if radius <= 0:
                        st.error("Hình tròn không hợp lệ.")
                    else:
                        radius = int(radius)
                        
                        # Tạo mặt nạ hình tròn
                        mask = Image.new("L", (2 * radius, 2 * radius), 0)
                        draw = ImageDraw.Draw(mask)
                        draw.ellipse((0, 0, 2 * radius, 2 * radius), fill=255)
                        
                        # Cắt hình ảnh bằng mặt nạ hình tròn
                        cropped_image = edited_image.crop((x, y, x + 2 * radius, y + 2 * radius))
                        
                        # Tạo ảnh mới nền trong suốt cho ảnh cắt hình tròn
                        circular_image = Image.new("RGBA", (2 * radius, 2 * radius), (255, 255, 255, 0))
                        circular_image.paste(cropped_image, (0, 0), mask)
                        
                        # Update the edited image
                        edited_image = circular_image

    
    # Bộ lọc chỉnh sửa
    if st.sidebar.checkbox("🎛️ Bộ lọc"):
        st.sidebar.write("🔧 Điều chỉnh các thông số ảnh.")
        
        # Lưu ảnh gốc để khôi phục lại
        image_goc = image.copy()
        st.session_state.original_image = edited_image.copy()

        # Thiết lập giá trị trung tính cho các thông số
        if "filters" not in st.session_state:
            st.session_state.filters = {
                "brightness": 1.0,
                "exposure": 0.0,
                "contrast": 1.0,
                "highlight": 0.0,
                "shadow": 0.0,
                "saturation": 1.0,
                "hue_shift": 0,
                "temperature": 0
            }

        # Tạo các thanh trượt với giá trị từ session state
        brightness = st.sidebar.slider("🌞 Độ sáng:", 0.0, 2.0, st.session_state.filters["brightness"], key="brightness")
        exposure = st.sidebar.slider("🔆 Độ phơi sáng:", -1.0, 1.0, st.session_state.filters["exposure"], key="exposure")
        contrast = st.sidebar.slider("🌓 Tương phản:", 0.0, 2.0, st.session_state.filters["contrast"], key="contrast")
        highlight = st.sidebar.slider("✨ Vùng sáng:", 0.0, 1.0, st.session_state.filters["highlight"], key="highlight")
        shadow = st.sidebar.slider("🌑 Đổ bóng:", 0.0, 1.0, st.session_state.filters["shadow"], key="shadow")
        saturation = st.sidebar.slider("🎨 Độ bão hòa:", 0.0, 2.0, st.session_state.filters["saturation"], key="saturation")
        hue_shift = st.sidebar.slider("🎭 Sắc thái:", -180, 180, st.session_state.filters["hue_shift"], key="hue_shift")
        temperature = st.sidebar.slider("🔥 Nhiệt độ:", -100, 100, st.session_state.filters["temperature"], key="temperature")

        # Cập nhật session state khi thanh trượt thay đổi
        st.session_state.filters.update({
            "brightness": brightness,
            "exposure": exposure,
            "contrast": contrast,
            "highlight": highlight,
            "shadow": shadow,
            "saturation": saturation,
            "hue_shift": hue_shift,
            "temperature": temperature
        })

        # Áp dụng các chỉnh sửa trực tiếp
        temp_image = st.session_state.original_image.copy()

        # Chỉnh độ sáng
        enhancer = ImageEnhance.Brightness(temp_image)
        temp_image = enhancer.enhance(st.session_state.filters["brightness"])

        # Chỉnh độ phơi sáng
        if st.session_state.filters["exposure"] != 0:
            enhancer = ImageEnhance.Brightness(temp_image)
            temp_image = enhancer.enhance(1 + st.session_state.filters["exposure"])

        # Chỉnh tương phản
        enhancer = ImageEnhance.Contrast(temp_image)
        temp_image = enhancer.enhance(st.session_state.filters["contrast"])

        # Chỉnh vùng sáng
        highlight_enhanced = ImageEnhance.Brightness(temp_image)
        temp_image = highlight_enhanced.enhance(1 + st.session_state.filters["highlight"] * 0.5)

        # Chỉnh đổ bóng
        shadow_enhanced = ImageEnhance.Brightness(temp_image)
        temp_image = shadow_enhanced.enhance(1 - st.session_state.filters["shadow"] * 0.5)

        # Chỉnh độ bão hòa
        enhancer = ImageEnhance.Color(temp_image)
        temp_image = enhancer.enhance(st.session_state.filters["saturation"])

        # Chỉnh sắc thái
        if st.session_state.filters["hue_shift"] != 0:
            hsv_image = temp_image.convert("HSV")
            hsv_array = np.array(hsv_image)
            hsv_array[..., 0] = (hsv_array[..., 0].astype(int) + st.session_state.filters["hue_shift"]) % 360
            temp_image = Image.fromarray(hsv_array, mode="HSV").convert("RGBA")

        # Chỉnh nhiệt độ
        if st.session_state.filters["temperature"] != 0:
            r, g, b, a = temp_image.split()
            if st.session_state.filters["temperature"] > 0:  # Tăng nhiệt độ (ấm hơn)
                r = r.point(lambda i: min(255, i + st.session_state.filters["temperature"]))
            elif st.session_state.filters["temperature"] < 0:  # Giảm nhiệt độ (lạnh hơn)
                b = b.point(lambda i: min(255, i + abs(st.session_state.filters["temperature"])))
            temp_image = Image.merge("RGBA", (r, g, b, a))

        # Cập nhật ảnh đã chỉnh sửa
        edited_image = temp_image

        # Nút trở về ảnh gốc
        if st.sidebar.button("↩️ Trở về ảnh gốc"):
            # Đặt lại session state và thanh trượt
            st.session_state.filters.update( {
                "brightness": 1.0,
                "exposure": 0.0,
                "contrast": 1.0,
                "highlight": 0.0,
                "shadow": 0.0,
                "saturation": 1.0,
                "hue_shift": 0,
                "temperature": 0
            })
            st.rerun()  # Tải lại giao diện để đồng bộ
            edited_image = image_goc
            
    # Làm mờ
    if st.sidebar.checkbox("🌫️ Làm mờ"):
        blur_radius = st.sidebar.slider("Độ mờ :", 0, 10, 2)
        edited_image = edited_image.filter(ImageFilter.GaussianBlur(blur_radius))


    # Xóa nền
    if st.sidebar.checkbox("🚫 Xóa nền"):
        st.sidebar.write("⏳ Xóa nền đang được thực hiện...")
        image_bytes = io.BytesIO()
        edited_image.save(image_bytes, format="PNG")
        image_bytes = image_bytes.getvalue()
        edited_image = Image.open(io.BytesIO(remove(image_bytes)))

    # Vẽ tự do
    if st.sidebar.checkbox("🖌️ Vẽ tự do"):
        st.sidebar.write("🖱️ Nhấn chuột và kéo để vẽ.")
        
        # Điều chỉnh thông số vẽ
        stroke_width = st.sidebar.slider("🖍️ Độ rộng nét vẽ:", 1, 20, 3)
        stroke_color = st.sidebar.color_picker("🎨 Màu nét vẽ:", "#ff0000")

        image_back = edited_image
        
        # Thực hiện vẽ tự do
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Màu tô
            stroke_width=stroke_width,           # Độ rộng nét vẽ
            stroke_color=stroke_color,           # Màu nét vẽ
            background_image=image_back,       # Ảnh nền
            update_streamlit=True,
            height=image_back.height,
            width=image_back.width,
            drawing_mode="freedraw",
            key="canvas",
        )

        # Kiểm tra nếu có dữ liệu từ canvas
        if canvas_result and canvas_result.image_data is not None:
            # Lấy các nét vẽ từ canvas
            drawing_data = canvas_result.image_data.astype(np.uint8)

            # Kết hợp nét vẽ với ảnh gốc
            drawing_image = Image.fromarray(drawing_data)
            combined_image = Image.alpha_composite(edited_image.convert("RGBA"), drawing_image.convert("RGBA"))
            
            # Cập nhật ảnh đã chỉnh sửa
            edited_image = combined_image.convert("RGB")

    # Thêm chữ
    if st.sidebar.checkbox("✍️ Thêm chữ"):
        text = st.sidebar.text_input("Nhập văn bản:")
        x = st.sidebar.slider("X:", 0, edited_image.width, 10)
        y = st.sidebar.slider("Y:", 0, edited_image.height, 10)
        font_size = st.sidebar.slider("Kích thước chữ:", 10, 200, 20)
        text_color = st.sidebar.color_picker("🎨 Màu chữ:", "#000000")  # Chọn màu chữ
        
        font = ImageFont.load_default(font_size)
        
        # Thêm chữ vào ảnh
        draw = ImageDraw.Draw(edited_image)
        if text:
            draw.text((x, y), text, font=font, fill=text_color)  # Áp dụng màu chữ

    # Kiểm tra nếu có checkbox "Thêm icon"
    if st.sidebar.checkbox("📍 Thêm icon"):
        
         # Đường dẫn đến thư mục chứa các icon
        icons_path = "icon/"

        # Lấy danh sách file icon từ thư mục
        icon_files = [f for f in os.listdir(icons_path) if f.endswith(('.png', '.jpg'))]

        # Hiển thị tất cả icon dưới dạng lưới nhỏ (preview)
        st.sidebar.write("## Preview Icon:")
        col1, col2, col3, col4 = st.sidebar.columns(4)  # Hiển thị icon trong 4 cột
        selected_icons = []  # Danh sách các icon được chọn

        # Hiển thị icon và thêm checkbox kèm số thứ tự
        for i, icon_file in enumerate(icon_files):
            icon_path = os.path.join(icons_path, icon_file)
            icon_thumbnail = Image.open(icon_path).convert("RGBA").resize((40, 40))

            # Hiển thị icon trong các cột
            with [col1, col2, col3, col4][i % 4]:
                st.image(icon_thumbnail, use_container_width=True)
                
                # Checkbox với số thứ tự
                if st.checkbox(f"{i + 1}", key=icon_file):
                    selected_icons.append((i + 1, icon_file))

        # Hiển thị thanh điều chỉnh kích thước cho từng icon được chọn
        if selected_icons:
            for index, selected_icon in selected_icons:
                st.sidebar.write(f"### Icon {index}")
                icon_path = os.path.join(icons_path, selected_icon)
                icon = Image.open(icon_path).convert("RGBA")

                # Cho phép người dùng điều chỉnh kích thước cho mỗi icon
                icon_size = st.sidebar.slider(f"Kích thước icon {index}:", 10, 400, 50, key=f"size_{selected_icon}")
                icon = icon.resize((icon_size, icon_size))

                # Cập nhật thanh trượt với giá trị nhập vào (X và Y)
                x_input = st.sidebar.text_input(f"Nhập tọa độ X cho icon {index}:", "0")
                y_input = st.sidebar.text_input(f"Nhập tọa độ Y cho icon {index}:", "0")

                try:
                    x = int(x_input)
                except ValueError:
                    x = 0

                try:
                    y = int(y_input)
                except ValueError:
                    y = 0

                # Điều chỉnh thanh trượt X và Y
                x = st.sidebar.slider(f"X cho icon {index}:", 0, 2000, x, key=f"x_{selected_icon}")
                y = st.sidebar.slider(f"Y cho icon {index}:", 0, 2000, y, key=f"y_{selected_icon}")

                edited_image.paste(icon, (x, y), icon)
                
        st.sidebar.write("🖼️ Chọn các icon từ thư viện hoặc tải lên icon mới.")

        # Chức năng tải lên nhiều ảnh icon từ máy tính người dùng
        uploaded_files = st.sidebar.file_uploader("Tải ảnh icon từ máy tính", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        
        if uploaded_files:
            # Lặp qua từng tệp được tải lên
            for index, uploaded_file in enumerate(uploaded_files, start=1):
                # Mở ảnh tải lên và hiển thị
                uploaded_icon = Image.open(uploaded_file).convert("RGBA")
                st.sidebar.image(uploaded_icon, caption=f"Ảnh tải lên {index}", use_container_width=True)

                # Cho phép người dùng điều chỉnh kích thước ảnh tải lên
                icon_size = st.sidebar.slider(f"Kích thước ảnh tải lên {index}:", 10, 400, 50, key=f"size_uploaded_icon_{index}")
                uploaded_icon = uploaded_icon.resize((icon_size, icon_size))

                # Nhập tọa độ và cập nhật thanh trượt
                x_input = st.sidebar.text_input(f"Nhập tọa độ X cho ảnh tải lên {index}:", "0", key=f"x_input_uploaded_icon_{index}")
                y_input = st.sidebar.text_input(f"Nhập tọa độ Y cho ảnh tải lên {index}:", "0", key=f"y_input_uploaded_icon_{index}")

                try:
                    x = int(x_input)
                except ValueError:
                    x = 0

                try:
                    y = int(y_input)
                except ValueError:
                    y = 0

                # Điều chỉnh thanh trượt X và Y
                x = st.sidebar.slider(f"X cho ảnh tải lên {index}:", 0, 2000, x, key=f"x_uploaded_icon_{index}")
                y = st.sidebar.slider(f"Y cho ảnh tải lên {index}:", 0, 2000, y, key=f"y_uploaded_icon_{index}")

                # Dán ảnh tải lên vào ảnh gốc (giả sử ảnh gốc là `edited_image`)
                edited_image.paste(uploaded_icon, (x, y), uploaded_icon)

    # Lật ảnh
    flip_vertical = st.sidebar.checkbox("🔁 Lật dọc")
    flip_horizontal = st.sidebar.checkbox("🔄 Lật ngang")
    if flip_vertical:
        edited_image = edited_image.transpose(Image.FLIP_TOP_BOTTOM)
    if flip_horizontal:
        edited_image = edited_image.transpose(Image.FLIP_LEFT_RIGHT)
        
   # Xoay ảnh
    if st.sidebar.checkbox("🌫️ Xoay ảnh"):
        # Lưu ảnh gốc để khôi phục lại
        if "original__image" not in st.session_state:
            st.session_state.original__image = edited_image.copy()
        rotation_angle = st.sidebar.slider("🎡 Xoay ảnh (độ):", -180, 180, 0)
        if rotation_angle != 0:
            edited_image = edited_image.rotate(rotation_angle, expand=True)

        if st.sidebar.button("↩️ Trở về ảnh gốc"):
            edited_image = st.session_state.original__image.copy()

    # Tính toán kích thước mới
    width, height = edited_image.size
    edited_image_resized = edited_image.resize((new_width, new_height))
       
    # Hiển thị ảnh đã chỉnh sửa
    st.image(edited_image_resized, caption="Ảnh đã chỉnh sửa", use_container_width=False)

    # Lựa chọn định dạng tải xuống
    download_format = st.sidebar.selectbox("Chọn định dạng tải xuống", ["PNG", "JPG"])
    if download_format == "JPG":
        buf = io.BytesIO()
        edited_image.convert("RGB").save(buf, format="JPEG")  # Chuyển sang JPEG nếu chọn
    else:
        buf = io.BytesIO()
        edited_image.save(buf, format="PNG")  # Mặc định là PNG
    byte_im = buf.getvalue()
    st.download_button(
        label="💾 Tải ảnh đã chỉnh sửa",
        data=byte_im,
        file_name=f"edited_image.{download_format.lower()}",
        mime=f"image/{download_format.lower()}",
    )
