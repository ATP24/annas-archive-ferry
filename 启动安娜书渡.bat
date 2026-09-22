@echo off
chcp 65001 >nul
title 安娜书渡 - 独立运行控制台

:MENU
cls
echo ============================================================
echo      [安娜书渡 / Anna's Archive Ferry] 独立控制台
echo ============================================================
echo.
echo   [1] 检索书籍并选择下载
echo   [2] 直接输入 MD5 码下载
echo   [3] 执行环境自检 (Doctor)
echo   [4] 打开下载保存目录
echo   [0] 退出
echo.
echo ============================================================
set /p opt="请选择操作编号 [0-4]: "

if "%opt%"=="1" goto SEARCH
if "%opt%"=="2" goto DOWNLOAD_MD5
if "%opt%"=="3" goto DOCTOR
if "%opt%"=="4" goto OPEN_DIR
if "%opt%"=="0" exit /b 0
goto MENU

:SEARCH
cls
echo ============================================================
echo   【检索书籍】
echo ============================================================
set /p q="请输入书名、作者或关键词: "
if "%q%"=="" goto MENU
echo.
python "%~dp0scripts\ferry_engine.py" search "%q%" --limit 8
echo.
set /p choice="请输入要下载的书籍 MD5 码 (直接按回车返回菜单): "
if "%choice%"=="" goto MENU
python "%~dp0scripts\ferry_engine.py" download --md5 %choice%
pause
goto MENU

:DOWNLOAD_MD5
cls
echo ============================================================
echo   【MD5 直连下载】
echo ============================================================
set /p md5code="请输入安娜档案书籍 32 位 MD5 码: "
if "%md5code%"=="" goto MENU
python "%~dp0scripts\ferry_engine.py" download --md5 %md5code%
pause
goto MENU

:DOCTOR
cls
python "%~dp0scripts\ferry_engine.py" doctor
pause
goto MENU

:OPEN_DIR
python -c "import json, os, subprocess; from pathlib import Path; p = json.load(open(r'%~dp0scripts\config.json', encoding='utf-8')).get('default_download_dir', '~/Downloads/AnnasFerry'); target = os.path.expandvars(os.path.expanduser(p)); os.makedirs(target, exist_ok=True); os.system(f'explorer \"{target}\"')"
goto MENU
