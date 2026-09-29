# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.31.116.232")

script = """
netsh advfirewall firewall add rule name="NDI_TCP" dir=in action=allow protocol=TCP localport=5353,5960-5980
netsh advfirewall firewall add rule name="NDI_UDP" dir=in action=allow protocol=UDP localport=5353,5960-5980
netsh advfirewall firewall add rule name="NDI_TCP_OUT" dir=out action=allow protocol=TCP localport=5353,5960-5980
netsh advfirewall firewall add rule name="NDI_UDP_OUT" dir=out action=allow protocol=UDP localport=5353,5960-5980
Write-Output "VM 防火牆 NDI 規則已添加！"
"""

res = vm.exec(script)
print("VM Output:", res.get("stdout"))
