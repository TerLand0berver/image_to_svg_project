# scripts/process_images.py

import os
import cv2
import subprocess
import logging
import yaml
import numpy as np

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def setup_logging(log_dir):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, 'process.log')
    logging.basicConfig(
        filename=log_file,
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)

def ensure_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def sharpen_image(image, intensity=1.0):
    """
    应用锐化滤波器增强图像细节。
    intensity: 锐化强度，默认值为1.0
    """
    # 锐化核：根据强度调整中心值
    kernel = np.array([[0, -1, 0],
                       [-1, 5 + intensity, -1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(image, -1, kernel)
    return sharpened

def binarize_image(image_path, output_path, method='otsu', threshold=127, sharpen_intensity=0.5):
    try:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            logging.error(f"无法加载图像: {image_path}")
            return False

        # 锐化处理
        image = sharpen_image(image, intensity=sharpen_intensity)

        if method == 'otsu':
            _, binary_image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == 'adaptive':
            binary_image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                                cv2.THRESH_BINARY, 11, 2)
        elif method == 'fixed':
            _, binary_image = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
        else:
            logging.error(f"未知的二值化方法: {method}")
            return False

        # 确保图像是单色的
        _, single_color_image = cv2.threshold(binary_image, 127, 255, cv2.THRESH_BINARY)
        cv2.imwrite(output_path, single_color_image)
        return True
    except Exception as e:
        logging.error(f"二色化处理失败: {image_path}，错误: {e}")
        return False

def crop_image(binary_image_path, output_path):
    try:
        image = cv2.imread(binary_image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            logging.error(f"无法加载二色图像: {binary_image_path}")
            return False

        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            logging.error(f"未找到轮廓: {binary_image_path}")
            return False

        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        cropped_image = image[y:y+h, x:x+w]
        cv2.imwrite(output_path, cropped_image)
        return True
    except Exception as e:
        logging.error(f"裁剪图像失败: {binary_image_path}，错误: {e}")
        return False

def smooth_image(binary_image_path, output_path, method='median', kernel_size=3):
    try:
        image = cv2.imread(binary_image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            logging.error(f"无法加载裁剪后的图像: {binary_image_path}")
            return False

        if method == 'median':
            smoothed_image = cv2.medianBlur(image, kernel_size)
        elif method == 'gaussian':
            smoothed_image = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        else:
            logging.error(f"未知的平滑方法: {method}")
            return False

        # 再次二值化以确保图像是单色的
        _, smoothed_binary = cv2.threshold(smoothed_image, 127, 255, cv2.THRESH_BINARY)
        # 保存为 BMP 格式，确保是单色
        bmp_output_path = os.path.splitext(output_path)[0] + '.bmp'
        cv2.imwrite(bmp_output_path, smoothed_binary)
        return bmp_output_path
    except Exception as e:
        logging.error(f"平滑处理失败: {binary_image_path}，错误: {e}")
        return False

def convert_to_svg(processed_image_path, svg_output_path, potrace_path, turdsize=2):
    try:
        # 构建 Potrace 命令
        cmd = [potrace_path, processed_image_path, '-s', '-o', svg_output_path, '--turdsize', str(turdsize)]
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Potrace转换失败: {processed_image_path}，错误: {e}")
        return False
    except FileNotFoundError:
        logging.error("Potrace未安装或未添加到系统PATH中。")
        return False

def process_image(image_path, config, processed_dir, output_dir, potrace_path):
    image_name = os.path.basename(image_path)
    name_without_ext = os.path.splitext(image_name)[0]

    # 定义中间处理图像的路径
    binary_image_path = os.path.join(processed_dir, f"binary_{name_without_ext}.png")
    cropped_image_path = os.path.join(processed_dir, f"cropped_{name_without_ext}.png")
    smoothed_image_path = os.path.join(processed_dir, f"smoothed_{name_without_ext}.png")

    # 输出SVG路径
    svg_output_path = os.path.join(output_dir, f"{name_without_ext}.svg")

    logging.info(f"开始处理: {image_name}")

    # 步骤1: 二色化
    if not binarize_image(image_path, binary_image_path, method=config['binarization_method'], 
                         threshold=config.get('binarization_threshold', 127),
                         sharpen_intensity=config.get('sharpen_intensity', 0.5)):
        logging.error(f"二色化失败: {image_name}")
        return None

    # 步骤2: 裁剪
    if not crop_image(binary_image_path, cropped_image_path):
        logging.error(f"裁剪失败: {image_name}")
        return None

    # 步骤3: 平滑处理（保存为 BMP）
    smoothed_bmp_path = smooth_image(cropped_image_path, smoothed_image_path, 
                           method=config['smoothing_method'], 
                           kernel_size=config['smoothing_kernel_size'])
    if not smoothed_bmp_path:
        logging.error(f"平滑处理失败: {image_name}")
        return None

    # 步骤4: 转换为SVG
    turdsize = config.get('svg_turdsize', 2)
    if not convert_to_svg(smoothed_bmp_path, svg_output_path, potrace_path, turdsize):
        logging.error(f"SVG转换失败: {image_name}")
        return None

    logging.info(f"成功生成SVG: {svg_output_path}")
    return svg_output_path
