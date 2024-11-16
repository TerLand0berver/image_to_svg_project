# Project README file 
```markdown
# 黑白图像转SVG转换器

## 简介

本项目旨在将大量的黑白图像自动转换为精确、平滑且无背景的SVG矢量图。通过一个直观的Streamlit图形用户界面（GUI），用户可以轻松上传图像、配置处理参数，并下载生成的SVG文件。

## 项目结构

```
image_to_svg_project/
├── input_images/          # 输入的黑白图像（可选，主要用于批量处理）
├── output_svgs/           # 输出的SVG文件
├── processed_images/      # 中间处理后的图像
├── scripts/
│   ├── process_images.py  # 后端处理脚本
│   └── app.py             # Streamlit前端应用
├── config/
│   └── config.yaml        # 配置文件
├── logs/                  # 日志文件
├── requirements.txt       # Python依赖包列表
├── README.md              # 项目说明文档
└── .gitignore             # Git忽略文件
```

## 安装指南

### 1. 克隆仓库

```bash
git clone <repository_url>
cd image_to_svg_project
```

### 2. 创建并激活虚拟环境

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖包

```bash
pip install -r requirements.txt
```

### 4. 安装 Potrace

请参考 [Potrace 官方网站](http://potrace.sourceforge.net/) 进行安装，并确保 `potrace` 命令在系统的 `PATH` 中可用。

- **Windows**：
  1. 下载预编译的Potrace可执行文件。
  2. 将 `potrace.exe` 放在项目的根目录下，或者添加到系统的环境变量 `PATH` 中。

- **macOS**：

  ```bash
  brew install potrace
  ```

- **Linux**：

  ```bash
  sudo apt-get update
  sudo apt-get install potrace
  ```

### 5. 配置参数

编辑 `config/config.yaml` 文件，根据需要调整处理参数：

- **supported_extensions**：支持的图像文件扩展名。
- **binarization_method**：选择二色化方法，`otsu` 或 `adaptive`。
- **smoothing_method**：选择平滑处理方法，`median` 或 `gaussian`。
- **smoothing_kernel_size**：平滑处理的卷积核大小（必须为奇数）。
- **max_workers**：并行处理的最大线程数，根据系统性能调整。

## 使用方法

### 启动Streamlit应用

在命令行中导航到 `scripts/` 文件夹并运行 Streamlit 应用：

```bash
cd image_to_svg_project/scripts
streamlit run app.py
```

### 使用Streamlit界面

1. **参数配置**：
   - 在侧边栏中选择二色化方法、平滑处理方法、卷积核大小和并行处理线程数。

2. **上传图像**：
   - 点击“上传黑白图像”按钮，选择一个或多个支持的图像文件（PNG, JPG, JPEG, BMP, TIFF）。
   - 上传完成后，页面会显示已上传的图像数量。

3. **开始转换**：
   - 点击“开始转换”按钮，应用将开始处理上传的图像。
   - 处理过程中，页面会显示加载指示器（spinner）。
   - 处理完成后，页面会显示成功消息，并为每个生成的SVG文件提供下载按钮和预览。

4. **下载SVG**：
   - 对于每个生成的SVG文件，点击“下载 SVG”按钮即可下载文件。
   - SVG预览会在页面下方显示，方便用户查看。

## 注意事项

- **输入图像要求**：确保输入图像为黑白配色，以获得最佳转换效果。如果输入图像包含灰度或其他颜色，请调整二色化方法或预处理图像。
- **Potrace安装**：确保 `potrace` 已正确安装，并且命令行中可调用。如果 Potrace 未安装或未添加到 `PATH` 中，应用将无法进行矢量化处理。
- **处理参数调整**：根据图像的具体情况，可能需要调整 `config/config.yaml` 中的参数（如二色化方法、平滑处理方法和卷积核大小）以优化处理效果。
- **性能优化**：对于大量图像处理，可以适当增加 `max_workers` 参数的值，以充分利用多核CPU资源。但请注意，过高的线程数可能导致系统资源紧张。

## 许可证

本项目使用MIT许可证。详细信息请参阅 [LICENSE](LICENSE) 文件。