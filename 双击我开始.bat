@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动字幕提取工具...
python "新手一键启动.py"
if errorlevel 1 (
  echo.
  echo 如果提示找不到 python,请先安装 Python:
  echo https://www.python.org/downloads/
  echo 安装时务必勾选 "Add Python to PATH"
  pause
)
