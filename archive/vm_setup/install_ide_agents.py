# -*- coding: utf-8 -*-
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

print("==================================================")
print(" 🚀 正在安裝 IDE 智能體 (Cline, Roo Code, Aider, Claude Code)...")
print("==================================================")

# 1. 安裝 VS Code 智能體擴充
print("\n[1/3] 安裝 VS Code 智能體擴充套件 (Cline, Roo Code, Continue)...")
cmd_ext = """
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
code --install-extension saoudrizwan.claude-dev --force
code --install-extension RooVeterinaryInc.roo-cline --force
code --install-extension Continue.continue --force
"""
res_ext = vm.exec(cmd_ext, timeout=120)
print(f" [✔️] VS Code 擴充套件安裝完畢！\n{res_ext.get('stdout')}")

# 2. 安裝 Aider
print("\n[2/3] 安裝 Aider 終端自主全棧編程智能體 (Aider AI Pair Programmer)...")
cmd_aider = "python -m pip install aider-chat --timeout 180"
res_aider = vm.exec(cmd_aider, timeout=300)
print(f" [✔️] Aider 安裝結果: {res_aider.get('success')}")

# 3. 安裝 Claude Code
print("\n[3/3] 安裝 Claude Code CLI 智能體...")
cmd_claude = """
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
npm install -g @anthropic-ai/claude-code
"""
res_claude = vm.exec(cmd_claude, timeout=180)
print(f" [✔️] Claude Code 安裝結果: {res_claude.get('success')}")

# 4. 在虛擬機桌面建立便捷啟動捷徑
print("\n[4] 正在建立桌面快速啟動圖示...")
aider_bat = """@echo off
chcp 65001 >nul
title Aider AI Autonomous Coding Agent
cd /d C:\\AI_Agents
echo ======================================================
echo    🤖 Aider AI 終端自主編程智能體 (支援 DeepSeek / Gemini / Claude)
echo ======================================================
echo.
echo [1] 以 DeepSeek R1 啟動 Aider:
echo     aider --model deepseek/deepseek-r1
echo.
echo [2] 以 Gemini 2.5 Pro 啟動 Aider:
echo     aider --model gemini/gemini-2.5-pro
echo.
echo [3] 啟動 Aider Web GUI 瀏覽器圖形介面:
echo     aider --gui
echo ======================================================
echo.
aider --gui
pause
"""

vm.write_file(r"C:\Users\qiwai\OneDrive\Desktop\Aider_AI_Agent.bat", aider_bat)
vm.write_file(r"C:\Users\Public\Desktop\Aider_AI_Agent.bat", aider_bat)

vscode_agent_bat = """@echo off
title VS Code (Cline / Roo Code AI Agent IDE)
code C:\\AI_Agents
"""
vm.write_file(r"C:\Users\qiwai\OneDrive\Desktop\VSCode_AI_Agent_IDE.bat", vscode_agent_bat)
vm.write_file(r"C:\Users\Public\Desktop\VSCode_AI_Agent_IDE.bat", vscode_agent_bat)

print("==================================================")
print(" 🎉 所有 IDE 級別智能體程式安裝與設定完成！")
print("==================================================")
