import re

with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the hardcoded prompt inside tiktok_live_worker
target_1 = r"6\. 🎹 鋼琴點歌：若觀眾點歌，請【直接調用工具 `pe\.play_virtual_piano\(song_name='歌名'\)`】開彈！若觀眾要求妳自創曲、即興創作一首，請調用 `pe\.compose_and_play_original_piano`！"
replacement_1 = """6. 🛠️ 【系統直接指令調用 (極重要)】：若要執行動作，請直接在對話中輸出對應的 Python 指令碼（系統會自動攔截執行，不會唸出來）：
   - 🎹 點歌/彈琴：`pe.play_virtual_piano(song_name='歌名')`
   - 🎹 即興創作：`pe.compose_and_play_original_piano()`
   - 🎹 停止彈琴：`pe.stop_virtual_piano()`
   - 🚶 移動走位：`move_spatial_position('左側/右側/靠近/原位')`
   - 🎨 畫圖：`draw_illustration('畫面描述')`"""
content = re.sub(target_1, replacement_1, content)

# 2. Find and update the HARD_TECHNICAL_RULES which is used by build_chat_system_prompt
target_2 = r"3\. 🎹 鋼琴才藝：老爸若點歌，務必【直接調用 `pe\.play_virtual_piano` 工具】開彈！若老爸要求妳自創曲、即興創作，請調用 `pe\.compose_and_play_original_piano`！"
replacement_2 = """3. 🛠️ 【系統直接指令調用 (極重要)】：若要執行動作，請直接在對話中輸出對應的 Python 指令碼（系統會自動攔截執行，不會唸出來）：
   - 🎹 點歌/彈琴：`pe.play_virtual_piano(song_name='歌名')`
   - 🎹 即興創作：`pe.compose_and_play_original_piano()`
   - 🎹 停止彈琴：`pe.stop_virtual_piano()`
   - 🚶 移動走位：`move_spatial_position('左側/右側/靠近/原位')`
   - 🎨 畫圖：`draw_illustration('畫面描述')`
   - 💻 執行代碼：`execute_local_python_code('Python程式碼')`"""
content = re.sub(target_2, replacement_2, content)

# 3. Add regex parsing inside execute_actions for the python-like function calls
# We'll inject it right after the move_fn_m check.
action_parser_code = """
    # 🛠️ 通用 Python 函數直接調用攔截 (Universal Python Call Interceptor)
    universal_tool_calls = [
        (r'pe\.play_virtual_piano\(\s*(?:song_name\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: pe.play_virtual_piano(song_name=m.group(1))),
        (r'pe\.compose_and_play_original_piano\(\s*\)', lambda m: pe.compose_and_play_original_piano()),
        (r'pe\.stop_virtual_piano\(\s*\)', lambda m: pe.stop_virtual_piano()),
        (r'draw_illustration\(\s*(?:prompt\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: generate_ai_image(m.group(1))),
        (r'execute_local_python_code\(\s*(?:code_string\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: execute_local_python_code(m.group(1)))
    ]
    
    for pattern, func in universal_tool_calls:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            log_print(f"🛠️ [通用指令攔截] 檢測到 Python 呼叫: {match.group(0)}，立即自動執行！")
            asyncio.create_task(func(match))
            has_dispatched_tool = True
            text = text.replace(match.group(0), "")
"""

target_insert = r"move_fn_m = re\.search\(r'move_spatial_position\\s\*\\(\\s\*\[\\'\"\]\?\(\[^\\'\",\\\\\)\]\+\)\[\\'\"\]\?\\s\*\\)', text, re\.IGNORECASE\)\n    if move_fn_m:\n        raw_pos_arg = move_fn_m\.group\(1\)\.strip\(\)\n        log_print\(f\"🚶 \[走位代碼攔截\] 檢測到走位代碼: move_spatial_position\('\{raw_pos_arg\}'\)，立即平滑移動模型！\"\)\n        asyncio\.create_task\(apply_spatial_position\(raw_pos_arg\)\)\n        has_dispatched_tool = True\n        text = text\.replace\(move_fn_m\.group\(0\), \"\"\)"
if re.search(target_insert, content):
    content = re.sub(target_insert, target_insert + "\n" + action_parser_code, content)
else:
    print("Cannot find target_insert for action parser!")

with open('vts_7L_test.py', 'w', encoding='utf-8') as f:
    f.write(content)
