# -*- coding: utf-8 -*-
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

print("==================================================")
print(" 🌟 正在部署 7L 自主生活與自我學習大腦至專屬電腦...")
print("==================================================")

# 1. 部署 7L_Autonomous_Life.py
with open(r"c:\Users\qiwai\AI_Agents_Templates\7L_Autonomous_Life.py", "r", encoding="utf-8") as f:
    life_code = f.read()

vm.write_file("C:\\AI_Agents\\7L_Autonomous_Life.py", life_code)
print(" [✔️] 已同步: 7L_Autonomous_Life.py")

# 2. 建立桌面捷徑
life_bat = """@echo off
chcp 65001 >nul
title 7L 自主生活、探索與學習大腦 (Autonomous Life Engine)
cd /d C:\\AI_Agents
python 7L_Autonomous_Life.py
pause
"""

vm.write_file(r"C:\Users\qiwai\OneDrive\Desktop\🌟_7L_自主生活與學習.bat", life_bat)
vm.write_file(r"C:\Users\Public\Desktop\🌟_7L_自主生活與學習.bat", life_bat)
print(" [✔️] 已建立桌面快捷圖示: 🌟_7L_自主生活與學習.bat")

print("==================================================")
print(" 🎉 7L 專屬自主電腦生活系統部署完成！")
print("==================================================")
