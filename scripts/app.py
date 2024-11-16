# scripts/app.py

import streamlit as st
import os
import tempfile
import shutil
import sys
from process_images import load_config, setup_logging, ensure_folder, process_image
import logging
import re
import base64
import zipfile
from io import BytesIO

def sanitize_filename(filename):
    """
    将文件名中的非字母、数字、下划线、点和短横线的字符替换为下划线。
    """
    return re.sub(r'[^A-Za-z0-9_.-]', '_', filename)

def initialize():
    # 将项目根目录添加到系统路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    # 加载配置
    config_path = os.path.join(parent_dir, 'config', 'config.yaml')
    config = load_config(config_path)
    
    # 设置日志
    log_dir = os.path.join(parent_dir, 'logs')
    setup_logging(log_dir)
    
    # 确保文件夹存在
    processed_dir = os.path.join(parent_dir, 'processed_images')
    output_dir = os.path.join(parent_dir, 'output_svgs')
    ensure_folder(processed_dir)
    ensure_folder(output_dir)
    
    # 定位 Potrace 可执行文件
    potrace_path = os.path.join(parent_dir, 'potrace.exe')
    if not os.path.exists(potrace_path):
        logging.error(f"Potrace 可执行文件未找到: {potrace_path}")
        st.error("Potrace 可执行文件未找到，请将 `potrace.exe` 放置在项目根目录。")
    
    return config, processed_dir, output_dir, potrace_path

def create_zip(svg_paths):
    """
    创建包含所有SVG文件的ZIP包并返回其字节内容。
    """
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for svg_path in svg_paths:
            svg_filename = os.path.basename(svg_path)
            zip_file.write(svg_path, arcname=svg_filename)
    zip_buffer.seek(0)
    return zip_buffer.read()

def main():
    st.set_page_config(page_title="图像转SVG转换器", layout="wide")
    st.title("🖼️ 黑白图像转SVG转换器")
    
    config, processed_dir, output_dir, potrace_path = initialize()
    
    st.sidebar.header("参数配置")
    
    # 添加更多可调设置
    binarization_method = st.sidebar.selectbox(
        "二色化方法",
        options=['otsu', 'adaptive', 'fixed'],
        index=['otsu', 'adaptive', 'fixed'].index(config.get('binarization_method', 'otsu'))
    )
    
    # 添加固定阈值设置
    binarization_threshold = None
    if binarization_method == 'fixed':
        binarization_threshold = st.sidebar.slider(
            "固定二色化阈值",
            min_value=0,
            max_value=255,
            value=config.get('binarization_threshold', 127),
            help="固定阈值进行二色化"
        )
    
    smoothing_method = st.sidebar.selectbox(
        "平滑处理方法",
        options=['median', 'gaussian', 'none'],
        index=['median', 'gaussian', 'none'].index(config.get('smoothing_method', 'median'))
    )
    
    smoothing_kernel_size = 1  # 设置默认为1
    if smoothing_method != 'none':
        smoothing_kernel_size = st.sidebar.slider(
            "平滑处理卷积核大小",
            min_value=1,
            max_value=15,
            step=2,
            value=config.get('smoothing_kernel_size', 1),
            help="必须为奇数"
        )
    
    # 添加锐化参数
    sharpen_intensity = st.sidebar.slider(
        "锐化强度",
        min_value=0.0,
        max_value=5.0,
        step=0.1,
        value=config.get('sharpen_intensity', 0.5),
        help="调整锐化滤波器的强度"
    )
    
    max_workers = st.sidebar.slider(
        "并行处理线程数",
        min_value=1,
        max_value=16,
        step=1,
        value=config.get('max_workers', 4),
        help="根据系统性能调整"
    )
    
    # 添加 SVG 输出污点大小（turdsize）
    svg_turdsize = st.sidebar.slider(
        "SVG 输出污点大小（turdsize）",
        min_value=0,
        max_value=100,
        step=1,
        value=config.get('svg_turdsize', 2),
        help="忽略小于此大小的污点"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**支持的图像格式**: PNG, JPG, JPEG, BMP, TIFF")
    
    # 用户上传图像
    uploaded_files = st.file_uploader(
        "上传黑白图像",
        type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # 初始化 svg_paths 和 error_messages
        svg_paths = []
        error_messages = []
        
        # 临时保存上传的图像
        temp_input_dir = tempfile.mkdtemp()
        
        # 存储原始文件名和重命名后的文件名的映射
        filename_mapping = {}
        
        # 更新配置
        config['binarization_method'] = binarization_method
        if binarization_threshold is not None:
            config['binarization_threshold'] = binarization_threshold
        config['smoothing_method'] = smoothing_method
        config['smoothing_kernel_size'] = smoothing_kernel_size
        config['sharpen_intensity'] = sharpen_intensity
        config['max_workers'] = max_workers
        config['svg_turdsize'] = svg_turdsize  # 假设在 config 中添加此参数
        
        # 开始转换按钮放在图像列表顶部
        st.subheader("上传的图像")
        start_conversion = st.button("开始转换")
        
        # 显示上传的图像列表
        if not start_conversion:
            st.markdown("### 已上传的图像")
            cols = st.columns(3)  # 每行显示3个缩略图
            for idx, uploaded_file in enumerate(uploaded_files):
                sanitized_name = sanitize_filename(uploaded_file.name)
                file_path = os.path.join(temp_input_dir, sanitized_name)
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                filename_mapping[uploaded_file.name] = sanitized_name
                with cols[idx % 3]:
                    with st.expander(uploaded_file.name):
                        st.image(file_path, caption=uploaded_file.name, use_container_width=True)
        
        if start_conversion:
            with st.spinner("正在处理图像..."):
                # 确保所有文件已保存
                for uploaded_file in uploaded_files:
                    sanitized_name = filename_mapping.get(uploaded_file.name)
                    if not sanitized_name:
                        sanitized_name = sanitize_filename(uploaded_file.name)
                        file_path = os.path.join(temp_input_dir, sanitized_name)
                        with open(file_path, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        filename_mapping[uploaded_file.name] = sanitized_name
                
                total = len(filename_mapping)
                progress_bar = st.progress(0)
                current = 0
                for original_name, sanitized_name in filename_mapping.items():
                    image_path = os.path.join(temp_input_dir, sanitized_name)
                    svg_path = process_image(image_path, config, processed_dir, output_dir, potrace_path)
                    if svg_path:
                        svg_paths.append(svg_path)
                    else:
                        error_messages.append(f"{original_name}: 转换失败")
                    current += 1
                    progress_bar.progress(current / total)
            
            # 显示转换结果
            if svg_paths:
                st.success("图像转换完成！")
                st.subheader("转换后的图像和 SVG")
                cols = st.columns(2)  # 左右两栏显示
                for original_name, svg_path in zip(filename_mapping.keys(), svg_paths):
                    original_file = os.path.join(temp_input_dir, filename_mapping[original_name])
                    svg_file = svg_path
                    with cols[0]:
                        with st.expander(f"原始图像: {original_name}"):
                            st.image(original_file, caption=original_name, use_container_width=True)
                    with cols[1]:
                        svg_filename = os.path.basename(svg_file)
                        with st.expander(f"生成的 SVG: {svg_filename}"):
                            with open(svg_file, 'rb') as f:
                                svg_bytes = f.read()
                            encoded_svg = base64.b64encode(svg_bytes).decode()
                            svg_display = f'<iframe src="data:image/svg+xml;base64,{encoded_svg}" width="100%" height="400"></iframe>'
                            st.markdown(svg_display, unsafe_allow_html=True)
                            st.download_button(
                                label=f"下载 {svg_filename}",
                                data=svg_bytes,
                                file_name=svg_filename,
                                mime='image/svg+xml'
                            )
                
                # 提供批量下载 ZIP
                if svg_paths:
                    zip_bytes = create_zip(svg_paths)
                    st.download_button(
                        label="下载所有 SVG (ZIP)",
                        data=zip_bytes,
                        file_name="converted_svgs.zip",
                        mime="application/zip"
                    )
            
            # 显示错误消息
            if error_messages:
                st.error("以下图像转换失败：")
                for msg in error_messages:
                    st.error(msg)
            
            # 清理临时目录
            shutil.rmtree(temp_input_dir)

if __name__ == "__main__":
    main()
