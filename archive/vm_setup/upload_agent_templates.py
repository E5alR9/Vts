# -*- coding: utf-8 -*-
import os
import io
import sys

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

src_dir = r"c:\Users\qiwai\AI_Agents_Templates"
target_dir = r"C:\AI_Agents"

print("==================================================")
print(" 📁 正在同步純免費智能體腳本至虛擬機 C:\\AI_Agents...")
print("==================================================")

vm.exec(f"New-Item -ItemType Directory -Path '{target_dir}' -Force")

# 同步所有免費腳本
for filename in os.listdir(src_dir):
    local_path = os.path.join(src_dir, filename)
    if os.path.isfile(local_path) and not filename.startswith("."):
        with open(local_path, "r", encoding="utf-8") as f:
            content = f.read()
        remote_path = os.path.join(target_dir, filename).replace("/", "\\")
        res = vm.write_file(remote_path, content)
        print(f" [✔️] 已同步: {filename} -> {remote_path}")

print("\n==================================================")
print(" 🎉 所有免費智能體腳本已成功部署至虛擬機！")
print("==================================================")
