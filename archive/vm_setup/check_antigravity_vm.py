# -*- coding: utf-8 -*-
from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

script = """
$p1 = "C:\\Users\\qiwai\\AppData\\Local\\Programs\\Antigravity IDE"
$p2 = "C:\\Program Files\\Antigravity IDE"
$setup = "C:\\AI_Agents\\Antigravity_IDE_Setup.exe"

Write-Output "Setup Exists: $(Test-Path $setup)"
Write-Output "P1 Exists: $(Test-Path $p1)"
Write-Output "P2 Exists: $(Test-Path $p2)"

if (Test-Path $setup) {
    Write-Output "Setup Size: $((Get-Item $setup).Length)"
}
"""

res = vm.exec(script)
print("STDOUT:", res.get("stdout"))
