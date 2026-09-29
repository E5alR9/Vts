# -*- coding: utf-8 -*-
from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

script = """
Write-Output "=== 1. C:\\AI_Agents 核心檔案清單 ==="
Get-ChildItem -Path C:\\AI_Agents | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize

Write-Output "=== 2. mic_live_plugin 插件清單 ==="
if (Test-Path C:\\AI_Agents\\mic_live_plugin) {
    Get-ChildItem -Path C:\\AI_Agents\\mic_live_plugin | Select-Object Name, Length | Format-Table -AutoSize
}

Write-Output "=== 3. 7L_Memory_Vault 記憶庫清單 ==="
if (Test-Path C:\\AI_Agents\\7L_Memory_Vault) {
    Get-ChildItem -Path C:\\AI_Agents\\7L_Memory_Vault | Select-Object Name, Length | Format-Table -AutoSize
}

Write-Output "=== 4. 虛擬機桌面捷徑清單 ==="
Get-ChildItem -Path "C:\\Users\\qiwai\\OneDrive\\Desktop", "C:\\Users\\Public\\Desktop" | Select-Object Name | Format-Table -AutoSize

Write-Output "=== 5. Python 核心套件驗證 ==="
python -c "import edge_tts, discord, firebase_admin, websockets, pyautogui, mss, PIL, openai, google.genai, pyperclip, requests, dotenv, numpy, sounddevice; print('>> Python 核心依賴: 全部 100% 完整就緒！')"
"""

res = vm.exec(script)
print(res.get("stdout"))
