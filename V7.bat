@echo off
chcp 65001 >nul

:: 【啟動升級：自動切換至高畫質 Windows Terminal】
where wt >nul 2>&1
if %errorlevel% equ 0 (
    if "%WT_SESSION%"=="" (
        echo [系統] 偵測到傳統小黑窗，正在自動切換至高畫質 Windows Terminal...
        wt -d . "%~f0"
        exit
    )
)

title 7L AI VTuber

echo.
echo =========================================
echo          7L AI VTuber 啟動中...
echo =========================================
python vts_7L_test.py

pause