# -*- coding: utf-8 -*-
from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

script = """
import sys

packages = [
    'websockets', 'pyautogui', 'mss', 'PIL', 'openai', 
    'google.genai', 'edge_tts', 'discord', 'firebase_admin', 
    'pyperclip', 'requests', 'dotenv', 'numpy', 'pyaudio', 'sounddevice'
]

installed = []
missing = []

for p in packages:
    try:
        __import__(p)
        installed.append(p)
    except ImportError:
        missing.append(p)

print(f"INSTALLED: {', '.join(installed)}")
print(f"MISSING: {', '.join(missing)}")
"""

res = vm.exec(f"python -c \"{script}\"")
print("VM Output:", res.get("stdout"))
