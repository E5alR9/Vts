@echo off
chcp 65001 >nul
title 7L Discord Bot 啟動中...

if not exist 7L.py (
    echo [1/3] 正在下載最新版 7L.py...
    curl -s -o 7L.py https://raw.githubusercontent.com/E5alR9/7L/refs/heads/main/7L.py
) else (
    echo [1/3] 偵測到本機 7L.py，保留本地最新模型配置！
)

echo [2/3] 正在檢查並安裝依賴套件...
pip install -r https://raw.githubusercontent.com/E5alR9/7L/refs/heads/main/requirements.txt

:run_loop
echo [3/3] 正在啟動 7L.py 機器人...
python 7L.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 【⚠️ 提示】機器人連線中斷或 Discord 官方伺服器暫時異常 (500/503)！
    echo 【🔄 自動重試】將在 10 秒後自動嘗試重新連線... (若要退出請按 Ctrl + C)
    timeout /t 10
    goto run_loop
)
pause