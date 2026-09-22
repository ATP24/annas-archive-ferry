@echo off
chcp 65001 >nul
title 安娜书渡 - 一键环境配置
echo ============================================================
echo   [安娜书渡 / Anna's Archive Ferry] 环境一键配置工具
echo ============================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [-] 未检测到 Python，请先安装 Python 3.8 或以上版本，并勾选 Add Python to PATH。
    pause
    exit /b 1
)

echo [*] 正在检查并安装必要的核心依赖库...
python -m pip install -r "%~dp0scripts\requirements.txt"
if %errorlevel% neq 0 (
    echo [-] 依赖安装异常，尝试使用国内清华镜像重试...
    python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r "%~dp0scripts\requirements.txt"
)

echo.
echo [*] 正在执行环境健康自检...
python "%~dp0scripts\ferry_engine.py" doctor

echo.
echo ============================================================
echo   配置完毕！你可以直接双击 "启动安娜书渡.bat" 开始搜书。
echo ============================================================
pause
