# -*- coding: utf-8 -*-
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

print("==================================================")
print(" 🧪 正在部署 DeepSeek Agent & Eval Harness 至虛擬機...")
print("==================================================")

# 1. 寫入 deepseek_harness.py
with open(r"c:\Users\qiwai\AI_Agents_Templates\deepseek_harness.py", "r", encoding="utf-8") as f:
    harness_code = f.read()

vm.write_file("C:\\AI_Agents\\deepseek_harness.py", harness_code)
print(" [✔️] 已同步: deepseek_harness.py")

# 2. 建立桌面捷徑
harness_bat = """@echo off
chcp 65001 >nul
title DeepSeek Agent & Eval Harness
cd /d C:\\AI_Agents
python deepseek_harness.py
pause
"""

vm.write_file(r"C:\Users\qiwai\OneDrive\Desktop\🧪_DeepSeek_Harness.bat", harness_bat)
vm.write_file(r"C:\Users\Public\Desktop\🧪_DeepSeek_Harness.bat", harness_bat)
print(" [✔️] 已建立桌面快捷圖示: 🧪_DeepSeek_Harness.bat")

print("==================================================")
print(" 🎉 DeepSeek Harness 框架部署完成！")
print("==================================================")
