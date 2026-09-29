import ast

target_functions = {'save_cloud_knowledge', 'get_unified_memory_context'}

with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    source = f.read()

tree = ast.parse(source)

nodes_found = []
kept_code = []

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in target_functions:
        start = node.lineno - 1
        end = getattr(node, 'end_lineno')
        nodes_found.append((start, end))
        kept_code.append('\n'.join(source.splitlines()[start:end]))

lines = source.splitlines()

# Search for globals
idx_dci = -1
idx_dck_start = -1
idx_dck_end = -1
idx_rbm = -1

for i, line in enumerate(lines):
    if 'DEFAULT_CHANNEL_ID =' in line: idx_dci = i
    if 'DEFAULT_CLOUD_KNOWLEDGE =' in line: idx_dck_start = i
    if idx_dck_start != -1 and idx_dck_end == -1 and '}' in line and i > idx_dck_start:
        # Assuming single dict block
        idx_dck_end = i
    if 'RECENT_BOT_MESSAGES = []' in line: idx_rbm = i

global_code = []
if idx_dci != -1: 
    nodes_found.append((idx_dci, idx_dci + 1))
    global_code.append(lines[idx_dci])
if idx_dck_start != -1 and idx_dck_end != -1:
    nodes_found.append((idx_dck_start, idx_dck_end + 1))
    global_code.append('\n'.join(lines[idx_dck_start:idx_dck_end + 1]))
if idx_rbm != -1:
    nodes_found.append((idx_rbm, idx_rbm + 1))
    global_code.append(lines[idx_rbm])

with open('core/memory.py', 'r', encoding='utf-8') as f:
    mem_code = f.read()

# Add imports
if 'import re' not in mem_code: mem_code = mem_code.replace('import json', 'import json\\nimport re\\nimport copy\\nfrom datetime import datetime\\nfrom zoneinfo import ZoneInfo')

mem_code += '\\n\\n' + '\\n'.join(global_code) + '\\n\\n' + '\\n\\n'.join(kept_code)

with open('core/memory.py', 'w', encoding='utf-8') as f:
    f.write(mem_code)

# Remove from main file
nodes_found.sort(key=lambda x: x[0], reverse=True)
for start, end in nodes_found:
    del lines[start:end]

# Update imports in main
import_stmt = 'from core.memory import DEFAULT_CHANNEL_ID, save_cloud_knowledge, get_unified_memory_context, RECENT_BOT_MESSAGES'
for i, line in enumerate(lines):
    if 'from core.memory import' in line:
        lines[i] = line.strip() + ', DEFAULT_CHANNEL_ID, save_cloud_knowledge, get_unified_memory_context, RECENT_BOT_MESSAGES\\n'
        break

# Clean up RECENT_BOT_MESSAGES in global statements
final_lines = []
for line in lines:
    if 'global ' in line and 'RECENT_BOT_MESSAGES' in line:
        line = line.replace('RECENT_BOT_MESSAGES', '')
        import re as regexp
        line = regexp.sub(r',\\s*,', ',', line)
        line = regexp.sub(r'global\\s*,', 'global ', line)
        line = regexp.sub(r',\\s*$', '', line)
        if line.strip() == 'global':
            continue
    final_lines.append(line)

with open('vts_7L_test.py', 'w', encoding='utf-8') as f:
    f.write('\\n'.join(final_lines))

print("Fixed memory missing parts.")
