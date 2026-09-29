# -*- coding: utf-8 -*-
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

script = """
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User') + ';' + "$env:APPDATA\\npm"
Write-Output "=== OpenClaw Models Status ==="
openclaw models status
Write-Output "`n=== OpenClaw Config File / Path ==="
openclaw config file
"""

res = vm.exec(script)
print("STDOUT:\n", res.get('stdout'))
