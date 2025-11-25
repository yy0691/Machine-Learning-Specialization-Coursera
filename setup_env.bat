@echo off
chcp 65001 >nul
echo ================================================
echo      Python虚拟环境 & AI翻译环境设置
echo ================================================
echo.

cd /d "%~dp0"

echo [1/4] 检查Python环境...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python环境
    echo 请先安装Python 3.8+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('py --version') do set PYTHON_VERSION=%%i
echo Python版本: %PYTHON_VERSION%

echo.
echo [2/4] 创建虚拟环境...
if exist "venv" (
    echo 虚拟环境已存在，跳过创建
) else (
    echo 正在创建虚拟环境...
    py -m venv venv
    if %errorlevel% neq 0 (
        echo 错误: 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo 虚拟环境创建成功
)

echo.
echo [3/4] 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo 错误: 激活虚拟环境失败
    pause
    exit /b 1
)

echo 当前Python路径: 
where python

echo 安装required依赖...
pip install requests
if %errorlevel% neq 0 (
    echo 错误: 安装依赖失败
    pause
    exit /b 1
)

echo.
echo [4/4] 验证环境...
python -c "
import sys
import requests
print(f'Python版本: {sys.version}')
print(f'Python路径: {sys.executable}')
print(f'requests版本: {requests.__version__}')
print('环境设置成功！')
"

echo.
echo ================================================
echo           环境设置完成！
echo ================================================
echo.
echo 下次使用时运行: 启动翻译环境.bat
echo 或手动激活: venv\Scripts\activate.bat
echo.
pause