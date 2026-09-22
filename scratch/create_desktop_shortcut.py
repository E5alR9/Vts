import os
import subprocess

desktop_dir = r"C:\Users\qiwai\OneDrive\Desktop"
python_exe = r"C:\Users\qiwai\AppData\Local\Programs\Python\Python312\python.exe"
target_script = r"C:\Users\qiwai\auto_clicker_tool.py"
work_dir = r"C:\Users\qiwai"

# 1. Create pure ASCII batch files on Desktop and Workspace
bat_content = f'''@echo off
cd /d "{work_dir}"
"{python_exe}" "{target_script}"
if errorlevel 1 pause
'''

# Save Desktop batch files with ASCII encoding
for name in ["start_macro.bat", "run_autoclicker.bat"]:
    path = os.path.join(desktop_dir, name)
    with open(path, "w", encoding="ascii") as f:
        f.write(bat_content)
    print(f"Created {path}")

with open(os.path.join(work_dir, "start_macro.bat"), "w", encoding="ascii") as f:
    f.write(bat_content)

# 2. Create Windows .lnk Shortcut using PowerShell via subprocess
ps_cmd = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{os.path.join(desktop_dir, 'XMBC巨集連點工具.lnk')}")
$Shortcut.TargetPath = "{python_exe}"
$Shortcut.Arguments = '"{target_script}"'
$Shortcut.WorkingDirectory = "{work_dir}"
$Shortcut.Save()
'''

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
print("PS Output:", res.stdout, res.stderr)
print("[OK] Desktop launchers generated successfully!")
