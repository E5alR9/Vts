import sys

with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Target block to delete:
# Starts at:     # 🎹 攔截模型在文字中輸出的裸 JSON 點歌指令 (例如 {"song_name": "..."})
# Ends before:     url_match = re.search(r'\[OPEN_BROWSER:\s*([^\]]+)\]', text, re.IGNORECASE)

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "# 🎹 攔截模型在文字中輸出的裸 JSON 點歌指令" in line:
        start_idx = i
    if "url_match = re.search(r'\\[OPEN_BROWSER:" in line:
        end_idx = i
        break

if start_idx == -1 or end_idx == -1:
    print(f"Failed to find markers! start={start_idx}, end={end_idx}")
    sys.exit(1)

new_lines = lines[:start_idx] + lines[end_idx:]

with open('vts_7L_test.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Done!")
