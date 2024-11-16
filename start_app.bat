@echo off
REM 切换到项目目录
cd /d "%~dp0"

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 启动 Streamlit 应用
streamlit run scripts\app.py

REM 保持窗口打开以查看日志
pause
