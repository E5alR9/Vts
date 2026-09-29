# -*- coding: utf-8 -*-
from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

ps_script = """
$ProgressPreference = 'SilentlyContinue'
$url = "http://172.22.208.1:8888/Downloads/Antigravity%20IDE.exe"
$dest = "C:\\AI_Agents\\Antigravity_IDE_Setup.exe"

Write-Output "開始下載..."
(New-Object System.Net.WebClient).DownloadFile($url, $dest)

if (Test-Path $dest) {
    $item = Get-Item $dest
    Write-Output "下載成功！大小: $($item.Length) bytes"
    
    Write-Output "開始靜默安裝 Antigravity IDE..."
    Start-Process -FilePath $dest -ArgumentList "/S", "/allusers" -Wait
    Write-Output "安裝命令已發送完畢！"
} else {
    Write-Output "下載失敗！"
}
"""

res = vm.exec(ps_script, timeout=180)
print("STDOUT:", res.get("stdout"))
print("STDERR:", res.get("stderr"))
