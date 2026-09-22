import os

desktop_dir = r"C:\Users\qiwai\OneDrive\Desktop"
python_exe = r"C:\Users\qiwai\AppData\Local\Programs\Python\Python312\python.exe"
target_script = r"C:\Users\qiwai\auto_clicker_tool.py"
work_dir = r"C:\Users\qiwai"

bat_content = f"""@echo off
cd /d "{work_dir}"
"{python_exe}" "{target_script}"
if errorlevel 1 pause
"""

# Write clean bat files
for fname in ["XMBC巨集連點工具.bat", "啟動連點工具.bat", "start_macro.bat"]:
    fpath = os.path.join(desktop_dir, fname)
    with open(fpath, "w", encoding="ansi") as f:
        f.write(bat_content)
    print(f"Written: {fpath}")

with open(r"C:\Users\qiwai\啟動連點工具.bat", "w", encoding="ansi") as f:
    f.write(bat_content)

print("[OK] All bat files written in ANSI encoding!")
