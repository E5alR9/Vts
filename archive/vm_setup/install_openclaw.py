# -*- coding: utf-8 -*-
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

print("==================================================")
print(" 🦞 正在為 7L 虛擬機安裝 OpenClaw (自主個人 Agent 服務)...")
print("==================================================")

cmd = """
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
npm install -g openclaw
"""
res = vm.exec(cmd, timeout=180)
print(f" [✔️] 安裝結果:\n{res.get('stdout')}\n{res.get('stderr')}")

# 建立桌面捷徑
openclaw_bat = """@echo off
chcp 65001 >nul
title OpenClaw 24/7 AI Autonomous Agent
cd /d C:\\AI_Agents
echo ======================================================
echo    🦞 OpenClaw 24/7 自主 AI 智能體服務
echo ======================================================
echo.
openclaw --help
echo.
pause
"""

vm.write_file(r"C:\Users\qiwai\OneDrive\Desktop\🦞_OpenClaw_Agent.bat", openclaw_bat)
vm.write_file(r"C:\Users\Public\Desktop\🦞_OpenClaw_Agent.bat", openclaw_bat)
print(" [✔️] 已在桌面建立【🦞_OpenClaw_Agent.bat】快捷啟動圖示！")

print("==================================================")
print(" 🎉 OpenClaw 安裝與配置完成！")
print("==================================================")
