# -*- coding: utf-8 -*-
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

script = """
$wsh = New-Object -ComObject WScript.Shell
$desktopPaths = @(
    [Environment]::GetFolderPath('Desktop'),
    [Environment]::GetFolderPath('CommonDesktopDirectory')
)

foreach ($d in $desktopPaths) {
    # 1. Cursor AI IDE
    $cExe = "$env:LOCALAPPDATA\\Programs\\cursor\\Cursor.exe"
    if (Test-Path $cExe) {
        $sc = $wsh.CreateShortcut("$d\\Cursor_AI_IDE.lnk")
        $sc.TargetPath = $cExe
        $sc.Save()
    }

    # 2. Windsurf AI IDE
    $wExe = "$env:LOCALAPPDATA\\Programs\\Windsurf\\Windsurf.exe"
    if (Test-Path $wExe) {
        $sc = $wsh.CreateShortcut("$d\\Windsurf_AI_IDE.lnk")
        $sc.TargetPath = $wExe
        $sc.Save()
    }

    # 3. VS Code
    $vExe = "$env:LOCALAPPDATA\\Programs\\Microsoft VS Code\\Code.exe"
    if (!(Test-Path $vExe)) { $vExe = "C:\\Program Files\\Microsoft VS Code\\Code.exe" }
    if (Test-Path $vExe) {
        $sc = $wsh.CreateShortcut("$d\\VSCode_AI_IDE.lnk")
        $sc.TargetPath = $vExe
        $sc.Save()
    }
}
Write-Output "所有 AI IDE 官方桌面圖示已成功建立！"
"""

res = vm.exec(script)
print(res.get('stdout'))
