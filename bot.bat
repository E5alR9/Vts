@echo off
chcp 65001 >nul
title 啟動 6.env Bot...

echo [1/3] 正在安裝 / 更新套件...
pip install -r https://raw.githubusercontent.com/E5alR9/E5s/refs/heads/main/requirements.txt

echo [2/3] 正在下載最新的 bot.py...
curl -s -o bot.py https://raw.githubusercontent.com/E5alR9/E5s/refs/heads/main/bot.py

echo [3/3] 正在使用 6.env 啟動程式...
python -c "from dotenv import load_dotenv; load_dotenv('6.env'); import runpy; runpy.run_path('bot.py', run_name='__main__')"

pause