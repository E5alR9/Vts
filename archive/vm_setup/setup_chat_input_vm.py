# -*- coding: utf-8 -*-
from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

script = """
# 1. 建立 C:\\AI_Agents\\chat_input.txt
$targetFile = "C:\\AI_Agents\\chat_input.txt"
Set-Content -Path $targetFile -Value "" -Encoding utf8
cmd.exe /c icacls "C:\\AI_Agents\\chat_input.txt" /grant Everyone:F

# 2. 在桌面建立實體 chat_input.txt
$desktops = @("C:\\Users\\qiwai\\OneDrive\\Desktop", "C:\\Users\\Public\\Desktop", "C:\\Users\\qiwai\\Desktop")
foreach ($d in $desktops) {
    if (Test-Path $d) {
        $desktopFile = Join-Path $d "chat_input.txt"
        Set-Content -Path $desktopFile -Value "" -Encoding utf8
        cmd.exe /c icacls "$desktopFile" /grant Everyone:F
    }
}

# 3. 解決 C:\\chat_input.txt
if (Test-Path "C:\\chat_input.txt") {
    cmd.exe /c icacls "C:\\chat_input.txt" /grant Everyone:F
}
Write-Output "已成功建立完全可讀寫的 chat_input.txt！"
"""

res = vm.exec(script)
print("STDOUT:", res.get("stdout"))
print("STDERR:", res.get("stderr"))
