import re

with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "走位指令標籤攔截 [MOVE:" in line:
        start_idx = i
    if "語音合成與嘴型同步 (TTS & Lip Sync)" in line:
        end_idx = i
        break

if start_idx == -1 or end_idx == -1:
    print('Could not find markers!')
    import sys
    sys.exit(1)

new_block = """    # 🛠️ 通用 Python 函數直接調用攔截 (Universal Python Call Interceptor)
    universal_tool_calls = [
        (r'pe\.play_virtual_piano\(\s*(?:song_name\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: pe.play_virtual_piano(song_name=m.group(1))),
        (r'pe\.compose_and_play_original_piano\(\s*\)', lambda m: pe.compose_and_play_original_piano()),
        (r'pe\.stop_virtual_piano\(\s*\)', lambda m: pe.stop_virtual_piano()),
        (r'pe\.mashup_virtual_piano\(\s*(?:[^=]+=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: pe.mashup_virtual_piano(m.group(1))),
        (r'pe\.insert_virtual_piano\(\s*(?:song_name\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: pe.insert_virtual_piano(song_name=m.group(1))),
        (r'draw_illustration\(\s*(?:prompt\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: draw_illustration(m.group(1))),
        (r'execute_local_python_code\(\s*(?:code_string\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: execute_local_python_code(m.group(1))),
        (r'move_spatial_position\(\s*(?:target_position\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: apply_spatial_position(m.group(1)))
    ]
    
    for pattern, func in universal_tool_calls:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            log_print(f"🛠️ [通用指令攔截] 檢測到 Python 呼叫: {match.group(0)}，立即自動執行！")
            asyncio.create_task(func(match))
            has_dispatched_tool = True
            text = text.replace(match.group(0), "")

"""

new_lines = lines[:start_idx] + [new_block] + lines[end_idx:]

with open('vts_7L_test.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done!')
