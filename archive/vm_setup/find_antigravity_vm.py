# -*- coding: utf-8 -*-
from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

script = """
Get-ChildItem -Path "C:\\Users\\qiwai\\AppData\\Local\\Programs", "C:\\Program Files", "C:\\Users\\qiwai\\AppData\\Local", "C:\\Users\\qiwai\\Desktop", "C:\\Users\\Public\\Desktop", "C:\\Users\\qiwai\\OneDrive\\Desktop" -Filter "*antigravity*" -Recurse -Depth 3 -ErrorAction SilentlyContinue | Select-Object FullName
"""

res = vm.exec(script)
print("STDOUT:", res.get("stdout"))
