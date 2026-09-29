# -*- coding: utf-8 -*-
from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

script = """
# 1. 開啟遠端音訊錄製 (Remote Desktop Audio Capture)
reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp" /v fDisableAudioCapture /t REG_DWORD /d 0 /f
reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Terminal Services" /v fDisableAudioCapture /t REG_DWORD /d 0 /f

# 2. 開啟 Windows 麥克風全域隱私權限
reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\microphone" /v Value /t REG_SZ /d Allow /f

# 3. 確保 Windows Audio 服務正在執行
Set-Service -Name AudioSrv -StartupType Automatic
Restart-Service -Name AudioSrv -Force -ErrorAction SilentlyContinue

Write-Output "Windows 遠端音訊錄製註冊表與麥克風權限已全部啟用！"
"""

res = vm.exec(script)
print("STDOUT:", res.get("stdout"))
print("STDERR:", res.get("stderr"))
