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

:: 統一切到腳本所在資料夾，確保相對路徑（data/ models/ .env）都能命中
cd /d "%~dp0"

:: 🎙️ 背景啟動 CosyVoice 本地 TTS 服務（非阻塞；載入約 25~60 秒，
::    期間 tts_router 會自動用 kokoro，就緒後下次合成會自動切過去）
if exist "%~dp0venvs\cosyvoice\Scripts\python.exe" (
    start "" /b powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0scripts\start_cosyvoice.ps1" >nul 2>&1
)

echo.
echo =========================================
echo          7L AI VTuber 啟動中...
echo =========================================
python vts_7L_test.py

pause