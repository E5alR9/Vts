# -*- coding: utf-8 -*-
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

print("==================================================")
print(" 🧹 正在清理虛擬機桌面，打造純淨 DeepSeek 專屬環境...")
print("==================================================")

# 1. 建立專屬 DeepSeek 批次檔
deepseek_bat = """@echo off
chcp 65001 >nul
title DeepSeek R1 專屬智能體控制台
cd /d C:\\AI_Agents
python deepseek_agent.py
pause
"""

# 2. 同步最新的 deepseek_agent.py
with open(r"c:\Users\qiwai\AI_Agents_Templates\deepseek_agent.py", "r", encoding="utf-8") as f:
    deepseek_code = f.read()

vm.write_file("C:\\AI_Agents\\deepseek_agent.py", deepseek_code)
print(" [✔️] 已部署精簡版 deepseek_agent.py")

# 3. 清理桌面上多餘的雜亂圖示
cleanup_script = """
$targets = @(
    "C:\\Users\\qiwai\\OneDrive\\Desktop",
    "C:\\Users\\Public\\Desktop",
    "C:\\Users\\qiwai\\Desktop"
)
foreach ($t in $targets) {
    if (Test-Path $t) {
        Get-ChildItem -Path $t -Filter "*AI_Agent*" | Remove-Item -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path $t -Filter "*Aider*" | Remove-Item -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path $t -Filter "*VSCode_AI*" | Remove-Item -Force -ErrorAction SilentlyContinue
    }
}
Write-Output "桌面雜亂檔案已清理完畢！"
"""
res_clean = vm.exec(cleanup_script)
print(f" [✔️] {res_clean.get('stdout').strip()}")

# 4. 放置唯一的 DeepSeek 智能體桌面捷徑
vm.write_file("C:\\Users\\qiwai\\OneDrive\\Desktop\\🧠_DeepSeek_智能體.bat", deepseek_bat)
vm.write_file("C:\\Users\\Public\\Desktop\\🧠_DeepSeek_智能體.bat", deepseek_bat)
print(" [✔️] 已在桌面建立唯一的【🧠_DeepSeek_智能體.bat】捷徑！")

print("==================================================")
print(" 🎉 DeepSeek 專屬極簡環境配置完成！")
print("==================================================")
