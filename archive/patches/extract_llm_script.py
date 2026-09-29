import os

with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def find_block(start_str, end_str=None):
    start_idx = -1
    for i, line in enumerate(lines):
        if start_str in line:
            start_idx = i
            break
    if start_idx == -1: return -1, -1
    if not end_str: return start_idx, -1
    
    end_idx = -1
    for i in range(start_idx+1, len(lines)):
        if end_str in line:
            end_idx = i
            break
    return start_idx, end_idx

keys_start = find_block('# 🔐 1. 環境變數載入與金鑰矩陣分流初始化')[0]
keys_end = find_block('TAVILY_API_KEYS =', 'print(f"✅ 找到 {len(TAVILY_API_KEYS)} 把 Tavily 金鑰")')[1]

llm_start = find_block('def get_seconds_until_pt_midnight()')[0]
llm_end = find_block('async def process_chat_message')[0] - 1

if keys_start == -1 or keys_end == -1 or llm_start == -1 or llm_end == -1:
    print(f"Failed to find boundaries! keys: {keys_start}-{keys_end}, llm: {llm_start}-{llm_end}")
else:
    print(f"Keys block: {keys_start} to {keys_end}")
    print(f"LLM block: {llm_start} to {llm_end}")

    extracted = lines[keys_start:keys_end+1] + ["\n\n"] + lines[llm_start:llm_end]

    with open('extract_llm_full.py', 'w', encoding='utf-8') as f:
        f.writelines(extracted)
    print("Extracted to extract_llm_full.py")
