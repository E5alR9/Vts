# -*- coding: utf-8 -*-
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

script = """
$folders = @(
    "C:\\Users\\qiwai\\OneDrive\\Desktop",
    "C:\\Users\\Public\\Desktop",
    "C:\\Users\\qiwai\\Desktop"
)

foreach ($f in $folders) {
    if (Test-Path $f) {
        Get-ChildItem -Path $f | ForEach-Object {
            $name = $_.Name
            if ($name -match 'DeepSeek|OpenClaw|Aider|Harness|Hub|agent_collab|system_interpreter') {
                Remove-Item -Path $_.FullName -Force -Recurse -ErrorAction SilentlyContinue
                Write-Output "已刪除桌面檔案: $name"
            }
        }
    }
}

$agents = "C:\\AI_Agents"
if (Test-Path $agents) {
    Get-ChildItem -Path $agents | ForEach-Object {
        $name = $_.Name
        if ($name -match 'test_|temp_|collab|interpreter|harness|deepseek') {
            Remove-Item -Path $_.FullName -Force -Recurse -ErrorAction SilentlyContinue
            Write-Output "已刪除代理檔案: $name"
        }
    }
}
Write-Output "全部多餘項目清理完畢！"
"""

res = vm.exec(script)
print(res.get('stdout'))
