@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 高畫質 Windows Terminal（有的話）
where wt >nul 2>&1
if %errorlevel% equ 0 (
    if "%WT_SESSION%"=="" (
        wt -d "%~dp0" "%~f0"
        exit
    )
)
title 7L 一鍵啟動

echo =========================================
echo          7L 一鍵啟動（VTS + 主程式）
echo =========================================

:: 1. Python 檢查（鎖定 3.12 真環境；3.14 是空殼，一個包都沒有）
py -3.12 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 找不到 py -3.12，請確認 Python 3.12 已安裝。
    pause
    exit /b 1
)

:: 2. VTube Studio 沒開就幫開（Steam 版路徑）
tasklist /fi "imagename eq VTube Studio.exe" | find /i "VTube Studio.exe" >nul
if %errorlevel% neq 0 (
    if exist "C:\Program Files (x86)\Steam\steamapps\common\VTube Studio\VTube Studio.exe" (
        echo [1/3] VTS 未運行，正在啟動...
        start "" "C:\Program Files (x86)\Steam\steamapps\common\VTube Studio\VTube Studio.exe"
    ) else (
        echo [1/3] 找不到 VTS，主程式會先跑、等你手動開 VTS 後自動連上。
    )
) else (
    echo [1/3] VTS 已在運行。
)

:: 3. 主程式（崩潰 5 秒自重啟，vts_7L_test.py 內建單實例防重開）
:run_loop
echo [2/2] 啟動 vts_7L_test.py ...（Ctrl+C 退出，後台要看自己開 http://localhost:7860）
py -3.12 vts_7L_test.py
echo.
echo 【⚠️ 主程式退出，5 秒後自動重啟...】（要退出請按 Ctrl+C）
timeout /t 5
goto run_loop
