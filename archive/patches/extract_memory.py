import ast
import re

with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    source = f.read()

tree = ast.parse(source)

target_functions = {
    'init_unified_memory',
    'fetch_from_long_term_memory',
    'save_to_long_term_memory',
    'append_to_unified_memory',
    'clear_all_memories',
    'get_recent_100_memory_context',
    'get_viewer_profile',
    'save_viewer_profile',
    'record_bot_message',
    'get_cloud_knowledge',
    'update_cloud_prompt_field',
    'db_cleanup_task',
    '_save_unified_memory_to_disk'
}

kept_code = []
nodes_found = []

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in target_functions:
        start = node.lineno - 1
        end = getattr(node, 'end_lineno')
        nodes_found.append((start, end))
        kept_code.append('\n'.join(source.splitlines()[start:end]))

# We also need the memory globals block.
# Let's find it via string search
lines = source.splitlines()

# 1. UNIFIED MEMORY GLOBALS
start_idx_1 = -1
end_idx_1 = -1
for i, line in enumerate(lines):
    if 'UNIFIED_MEMORY_FILE = ' in line:
        start_idx_1 = i
    if 'STREAMER_MIND_BOARD: deque' in line:
        end_idx_1 = i
        break

if start_idx_1 != -1 and end_idx_1 != -1:
    nodes_found.append((start_idx_1, end_idx_1 + 1))
    kept_code.append('\n'.join(lines[start_idx_1:end_idx_1 + 1]))

# 2. VIEWER PROFILE GLOBALS
start_idx_2 = -1
end_idx_2 = -1
for i, line in enumerate(lines):
    if 'VIEWER_PROFILE_FILE = ' in line:
        start_idx_2 = i
    if 'VIEWER_PROFILES: Dict' in line:
        end_idx_2 = i
        break

if start_idx_2 != -1 and end_idx_2 != -1:
    nodes_found.append((start_idx_2, end_idx_2 + 1))
    kept_code.append('\n'.join(lines[start_idx_2:end_idx_2 + 1]))


if not nodes_found:
    print("No nodes found for memory.py")
else:
    imports = """import os
import json
import time
import asyncio
from collections import deque
from typing import List, Dict, Any, Optional

# Project imports
from core.utils import log_print, sys_notify, get_current_time_string
import services.piano_engine as pe
from core.db import db
from core.prompts import PromptTemplateEngine

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
"""
    
    with open('core/memory.py', 'w', encoding='utf-8') as f:
        f.write(imports + '\n\n' + '\n\n'.join(kept_code))
        
    print(f"Created core/memory.py with {len(nodes_found)} nodes.")
    
    # Remove from main file
    nodes_found.sort(key=lambda x: x[0], reverse=True)
    for start, end in nodes_found:
        del lines[start:end]
        
    # Inject import
    import_stmt = "from core.memory import init_unified_memory, fetch_from_long_term_memory, save_to_long_term_memory, append_to_unified_memory, clear_all_memories, get_recent_100_memory_context, get_viewer_profile, save_viewer_profile, record_bot_message, get_cloud_knowledge, update_cloud_prompt_field, db_cleanup_task, UNIFIED_LIVE_MEMORY, TIKTOK_CHATROOM_MEMORY, STREAMER_MIND_BOARD\n"
    
    pe_idx = -1
    for i, line in enumerate(lines):
        if 'import services.piano_engine' in line:
            pe_idx = i
            break
            
    if pe_idx != -1:
        lines.insert(pe_idx + 1, import_stmt)
    else:
        lines.insert(0, import_stmt)
        
    # Now we need to remove `global UNIFIED_LIVE_MEMORY` statements in vts_7L_test.py since it's now imported
    final_lines = []
    for line in lines:
        if 'global ' in line and ('UNIFIED_LIVE_MEMORY' in line or 'STREAMER_MIND_BOARD' in line or 'TIKTOK_CHATROOM_MEMORY' in line):
            line = line.replace('UNIFIED_LIVE_MEMORY', '')
            line = line.replace('STREAMER_MIND_BOARD', '')
            line = line.replace('TIKTOK_CHATROOM_MEMORY', '')
            # cleanup double commas
            line = re.sub(r',\\s*,', ',', line)
            line = re.sub(r'global\\s*,', 'global ', line)
            line = re.sub(r',\\s*$', '', line)
            if line.strip() == 'global':
                continue
        final_lines.append(line)
        
    with open('vts_7L_test.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_lines))
    print("Patched vts_7L_test.py for memory")
