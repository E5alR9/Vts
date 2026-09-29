# -*- coding: utf-8 -*-
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

bat_content = """@echo off
chcp 65001 >nul
title OpenClaw 24/7 AI Autonomous Agent
set "PATH=%APPDATA%\\npm;%ProgramFiles%\\nodejs;%PATH%"
cd /d C:\\AI_Agents
echo ======================================================
echo    🦞 OpenClaw 24/7 自主 AI 智能體服務 (Gateway & SubAgents)
echo ======================================================
echo.
echo [1] 啟動 OpenClaw 互動式 Agent:
echo     openclaw
echo.
echo [2] 啟動 24/7 背景 Gateway 網關服務:
echo     openclaw gateway
echo.
echo [3] 查看所有支援指令:
echo     openclaw --help
echo ======================================================
echo.
call openclaw
pause
"""

vm.write_file(r"C:\Users\qiwai\OneDrive\Desktop\🦞_OpenClaw_Agent.bat", bat_content)
vm.write_file(r"C:\Users\Public\Desktop\🦞_OpenClaw_Agent.bat", bat_content)
print("OpenClaw 啟動批次檔已成功同步至虛擬機桌面！")
