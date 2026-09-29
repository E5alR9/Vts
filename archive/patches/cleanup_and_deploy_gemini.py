# -*- coding: utf-8 -*-
import sys
import io
import os

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

print("==================================================")
print(" 🧹 正在清理虛擬機多餘檔案，全面統一為 Gemini 旗艦大腦...")
print("==================================================")

# 1. 刪除 C:\AI_Agents\ 內多餘的測試與舊檔案
cleanup_agents_cmd = """
$dir = "C:\\AI_Agents"
if (Test-Path $dir) {
    Get-ChildItem -Path $dir -Include "test_*", "temp_*", "*deepseek*", "*autogen*", "*crew*", "*browser*", "*free_ai*", "*harness*" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
}
Write-Output "已清理 C:\\AI_Agents 內的多餘舊檔案"
"""
res1 = vm.exec(cleanup_agents_cmd)
print(f" [✔️] {res1.get('stdout').strip()}")

# 2. 同步核心 ai_client.py 與 7L_Autonomous_Life.py
with open(r"c:\Users\qiwai\AI_Agents_Templates\ai_client.py", "r", encoding="utf-8") as f:
    vm.write_file("C:\\AI_Agents\\ai_client.py", f.read())

with open(r"c:\Users\qiwai\AI_Agents_Templates\7L_Autonomous_Life.py", "r", encoding="utf-8") as f:
    vm.write_file("C:\\AI_Agents\\7L_Autonomous_Life.py", f.read())

print(" [✔️] 已同步 Gemini 核心中樞: ai_client.py & 7L_Autonomous_Life.py")

# 3. 清理桌面雜亂圖示，只保留最乾淨的圖示
cleanup_desktop_cmd = """
$desktops = @(
    "C:\\Users\\qiwai\\OneDrive\\Desktop",
    "C:\\Users\\Public\\Desktop",
    "C:\\Users\\qiwai\\Desktop"
)
foreach ($d in $desktops) {
    if (Test-Path $d) {
        Get-ChildItem -Path $d -Include "*DeepSeek*", "*OpenClaw*", "*Aider*", "*Harness*", "*7L_AI_Agent_Hub*" | Remove-Item -Force -ErrorAction SilentlyContinue
    }
}
Write-Output "已清理桌面多餘圖示"
"""
res2 = vm.exec(cleanup_desktop_cmd)
print(f" [✔️] {res2.get('stdout').strip()}")

# 4. 建立唯一的 7L 專屬生活與學習啟動圖示
life_bat = """@echo off
chcp 65001 >nul
title 7L 專屬生活與自我學習大腦 (Gemini Flagship Edition)
cd /d C:\\AI_Agents
python 7L_Autonomous_Life.py
pause
"""
vm.write_file(r"C:\Users\qiwai\OneDrive\Desktop\🌟_7L_專屬生活與學習.bat", life_bat)
vm.write_file(r"C:\Users\Public\Desktop\🌟_7L_專屬生活與學習.bat", life_bat)
print(" [✔️] 已在桌面建立【🌟_7L_專屬生活與學習.bat】")

# 5. 測試 Gemini 連線
test_script = """
from ai_client import get_gemini_client
client, model = get_gemini_client("fast")
resp = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "請用繁體中文熱情向 7L 的老爸打招呼！"}],
    max_tokens=60
)
print("Gemini 連線測試成功！回覆:")
print(resp.choices[0].message.content)
"""
vm.write_file("C:\\AI_Agents\\verify_gemini.py", test_script)
res_test = vm.exec("python C:\\AI_Agents\\verify_gemini.py", timeout=30)
vm.exec("Remove-Item C:\\AI_Agents\\verify_gemini.py -Force -ErrorAction SilentlyContinue")

print("\n==================================================")
print(" 📡 Gemini 虛擬機即時實測結果:")
print(res_test.get('stdout'))
if res_test.get('stderr'):
    print("STDERR:", res_test.get('stderr'))
print("==================================================")
