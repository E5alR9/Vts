# -*- coding: utf-8 -*-
import os
import sys
import io
import shutil

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("==================================================")
print(" 🚀 正在將 7L 智能體環境部署至本機 C:\\AI_Agents...")
print("==================================================")

# 1. 建立 C:\AI_Agents 與 記憶庫
DEST_DIR = r"C:\AI_Agents"
VAULT_DIR = os.path.join(DEST_DIR, "7L_Memory_Vault")
os.makedirs(DEST_DIR, exist_ok=True)
os.makedirs(VAULT_DIR, exist_ok=True)

# 2. 複製 .env
src_env = r"c:\Users\qiwai\.env"
dest_env = os.path.join(DEST_DIR, ".env")
if os.path.exists(src_env):
    shutil.copy2(src_env, dest_env)
    print(" [✔️] 已同步本機 .env 設定檔至 C:\\AI_Agents\\.env")

# 3. 複製 AI_Agents_Templates 下的所有腳本
SRC_DIR = r"c:\Users\qiwai\AI_Agents_Templates"
if os.path.exists(SRC_DIR):
    for fname in os.listdir(SRC_DIR):
        src_f = os.path.join(SRC_DIR, fname)
        dst_f = os.path.join(DEST_DIR, fname)
        if os.path.isfile(src_f):
            shutil.copy2(src_f, dst_f)
    print(" [✔️] 已同步所有 AI Agent 模組至 C:\\AI_Agents\\")

# 4. 建立本機專屬桌面捷徑
desktop_dirs = [
    r"C:\Users\qiwai\OneDrive\Desktop",
    r"C:\Users\qiwai\Desktop"
]

# 4.1 DeepSeek R1 捷徑
deepseek_bat = """@echo off
chcp 65001 >nul
title DeepSeek R1 專屬智能體 (本機版)
cd /d C:\\AI_Agents
python deepseek_agent.py
pause
"""

# 4.2 7L 自主生活與學習捷徑
life_bat = """@echo off
chcp 65001 >nul
title 7L 自主生活、探索與學習大腦 (本機版)
cd /d C:\\AI_Agents
python 7L_Autonomous_Life.py
pause
"""

# 4.3 7L 全功能啟動捷徑
launch_bat = """@echo off
chcp 65001 >nul
title 🌟 7L AI-VTuber 旗艦全功能系統 (本機版)

echo ╔═══════════════════════════════════════════════════════════════╗
echo   🌸 7L 全功能智慧一體化核心系統 (本機旗艦版)
echo   🎙️ 麥克風音訊直連 + 語音互動
echo   👁️ VTube Studio 本機連線 + 88 鍵平台鋼琴
echo   🧠 旗艦大腦: Google Gemini (3.7 / 3.6 / 3.1 Pro / 3.5) + DeepSeek
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

cd /d C:\\Users\\qiwai

REM 檢查 VTube Studio
tasklist /FI "IMAGENAME eq VTube Studio.exe" 2>NUL | find /I /N "VTube Studio.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] VTube Studio 已在運行中。
) else (
    echo [..] 正在自動啟動 VTube Studio...
    if exist "C:\\Program Files (x86)\\Steam\\steamapps\\common\\VTube Studio\\VTube Studio.exe" (
        start "" "C:\\Program Files (x86)\\Steam\\steamapps\\common\\VTube Studio\\VTube Studio.exe"
    )
)

echo.
echo [🚀] 正在啟動 7L AI-VTuber 本機主程式...
echo ─────────────────────────────────────────────────────────────
python vts_7L_test.py
pause
"""

for d in desktop_dirs:
    if os.path.exists(d):
        with open(os.path.join(d, "🧠_DeepSeek_智能體.bat"), "w", encoding="utf-8") as f:
            f.write(deepseek_bat)
        with open(os.path.join(d, "🌟_7L_自主生活與學習.bat"), "w", encoding="utf-8") as f:
            f.write(life_bat)
        with open(os.path.join(d, "🚀_啟動_7L_全功能大腦.bat"), "w", encoding="utf-8") as f:
            f.write(launch_bat)
        print(f" [✔️] 已在桌面 [{d}] 建立三大核心捷徑！")

print("==================================================")
print(" 🎉 本機 AI_Agents 與桌面捷徑部署完成！")
print("==================================================")
