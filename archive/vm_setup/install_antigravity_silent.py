# -*- coding: utf-8 -*-
from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

script = """
$setup = "C:\\AI_Agents\\Antigravity_IDE_Setup.exe"
Write-Output "執行 InnoSetup 靜默安裝..."
$p = Start-Process -FilePath $setup -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-" -PassThru -Wait
Write-Output "InnoSetup ExitCode: $($p.ExitCode)"

if ($p.ExitCode -ne 0) {
    Write-Output "嘗試 NSIS 靜默安裝 (/S)..."
    $p2 = Start-Process -FilePath $setup -ArgumentList "/S" -PassThru -Wait
    Write-Output "NSIS ExitCode: $($p2.ExitCode)"
}

Start-Sleep -Seconds 3

# 尋找安裝目錄
$found = Get-ChildItem -Path "C:\\Users\\qiwai\\AppData\\Local\\Programs", "C:\\Program Files" -Filter "*Antigravity*" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 5 FullName
Write-Output "搜尋到的安裝路徑:"
$found | ForEach-Object { Write-Output $_.FullName }
"""

res = vm.exec(script, timeout=120)
print("STDOUT:", res.get("stdout"))
print("STDERR:", res.get("stderr"))
