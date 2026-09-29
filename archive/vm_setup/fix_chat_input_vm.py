# -*- coding: utf-8 -*-
from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

script = """
# 1. 賦予 C:\\chat_input.txt 與 C:\\AI_Agents 全員完全讀寫權限
cmd.exe /c icacls "C:\\chat_input.txt" /grant Everyone:F /t /c
cmd.exe /c icacls "C:\\chat_input.txt" /grant Users:F /t /c

$aiChat = "C:\\AI_Agents\\chat_input.txt"
if (-not (Test-Path $aiChat)) {
    New-Item -Path $aiChat -ItemType File -Value ""
}
cmd.exe /c icacls "C:\\AI_Agents\\chat_input.txt" /grant Everyone:F /t /c
cmd.exe /c icacls "C:\\AI_Agents\\chat_input.txt" /grant Users:F /t /c

# 2. 建立桌面直接打開輸入的捷徑
$desktops = @("C:\\Users\\qiwai\\OneDrive\\Desktop", "C:\\Users\\Public\\Desktop", "C:\\Users\\qiwai\\Desktop")
$wsh = New-Object -ComObject WScript.Shell
foreach ($d in $desktops) {
    if (Test-Path $d) {
        $lnk = Join-Path $d "💬_打字給7L.lnk"
        $s = $wsh.CreateShortcut($lnk)
        $s.TargetPath = "notepad.exe"
        $s.Arguments = "C:\\AI_Agents\\chat_input.txt"
        $s.Description = "打開記事本打字給 7L"
        $s.Save()
    }
}
Write-Output "權限修復完成！"
"""

res = vm.exec(script)
print("STDOUT:", res.get("stdout"))
print("STDERR:", res.get("stderr"))
