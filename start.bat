@echo off
chcp 65001 >nul
title 启动本地服务器 - 夯拉排位工具

echo ===================================
echo   正在启动本地 HTTP 服务器...
echo   项目: xl_cardlist_tool
echo   浏览器打开 http://localhost:3000
echo ===================================

REM 切换到脚本所在目录（项目根目录）
cd /d "%~dp0"

REM 检查 npx 是否存在
where npx >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 npx 命令，请检查 Node.js 是否安装。
    pause
    exit /b 1
)

echo 正在启动 npx serve...
echo.
npx serve

REM 如果 npx 意外退出，暂停窗口
pause