@echo off
chcp 65001 >nul
echo ================================================
echo           AI翻译脚本启动器
echo ================================================
echo.

cd /d "%~dp0"

echo 检查Python环境...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python环境
    echo 请安装Python或确保py命令可用
    pause
    exit /b 1
)

echo 检查依赖库...
py -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装requests库...
    py -m pip install requests
    if %errorlevel% neq 0 (
        echo 错误: 安装requests失败
        pause
        exit /b 1
    )
)

echo 检查待翻译文件...
py -c "
from pathlib import Path
total = len(list(Path('.').rglob('*.ipynb')))
translated = len(list(Path('notebooks-zh').rglob('*.ipynb'))) if Path('notebooks-zh').exists() else 0
print(f'总文件: {total}, 已翻译: {translated}, 待翻译: {total-translated}')
"

echo.
echo 准备启动翻译脚本...
echo 请确保已配置API密钥！
echo.
pause

py ai_translate_simple.py
pause