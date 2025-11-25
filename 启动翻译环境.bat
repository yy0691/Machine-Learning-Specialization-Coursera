@echo off
chcp 65001 >nul
echo ================================================
echo         AI翻译环境启动器 (虚拟环境)
echo ================================================
echo.

cd /d "%~dp0"

echo 检查虚拟环境...
if not exist "venv\Scripts\activate.bat" (
    echo 错误: 虚拟环境不存在
    echo 请先运行 setup_env.bat 创建环境
    pause
    exit /b 1
)

echo 激活虚拟环境...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo 错误: 激活虚拟环境失败
    pause
    exit /b 1
)

echo 检查依赖...
python -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装requests依赖...
    pip install requests
)

echo.
echo 检查项目状态...
python -c "
from pathlib import Path
import json

def check_status():
    root = Path('.')
    target = Path('notebooks-zh')
    
    # 统计文件
    source_notebooks = []
    for nb in root.rglob('*.ipynb'):
        if 'notebooks-zh' not in str(nb) and 'archive' not in str(nb).lower():
            source_notebooks.append(nb)
    
    translated = list(target.rglob('*.ipynb')) if target.exists() else []
    
    pending = []
    for nb in source_notebooks:
        rel_path = nb.relative_to(root)
        target_path = target / rel_path
        if not target_path.exists():
            pending.append(nb)
    
    return len(source_notebooks), len(translated), len(pending)

total, translated, pending = check_status()
print(f'项目状态:')
print(f'  总notebook文件: {total}')
print(f'  已翻译文件: {translated}')
print(f'  待翻译文件: {pending}')

if pending == 0:
    print('\\n状态: 所有文件都已翻译完成!')
else:
    print(f'\\n状态: 还有 {pending} 个文件需要翻译')
"

echo.
echo ================================================
echo 准备启动翻译脚本...
echo.
echo 注意事项:
echo 1. 请确保已在 ai_translate_simple.py 中配置API密钥
echo 2. 确保网络连接正常
echo 3. 建议首次使用先测试少量文件
echo ================================================
echo.
set /p choice=是否启动翻译脚本? (y/N): 
if /i "%choice%"=="y" (
    python ai_translate_simple.py
) else (
    echo 已取消启动
)

echo.
echo 要继续使用此环境，保持此窗口打开
echo 或重新运行此脚本激活环境
pause