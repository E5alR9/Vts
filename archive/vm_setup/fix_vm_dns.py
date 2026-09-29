# -*- coding: utf-8 -*-
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

script = """
Set-DnsClientServerAddress -InterfaceIndex 14 -ServerAddresses ('8.8.8.8', '1.1.1.1', '172.22.208.1')
ipconfig /flushdns
Test-NetConnection -ComputerName models.inference.ai.azure.com -Port 443
"""

res = vm.exec(script, timeout=30)
print(res.get('stdout'))
