import ast
import re

with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    source = f.read()

idx_dci = source.find('DEFAULT_CHANNEL_ID = "vts_local_user"')
idx_rbm = source.find('RECENT_BOT_MESSAGES = []')
idx_dck_start = source.find('DEFAULT_CLOUD_KNOWLEDGE = {')
idx_dck_end = source.find('}', idx_dck_start)

tree = ast.parse(source)
funcs_code = []
nodes_found = []
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {'save_cloud_knowledge', 'get_unified_memory_context'}:
        start = node.lineno - 1
        end = getattr(node, 'end_lineno')
        nodes_found.append((start, end))
        funcs_code.append('\n'.join(source.splitlines()[start:end]))

mem_additions = [
    'DEFAULT_CHANNEL_ID = "vts_local_user"',
    'RECENT_BOT_MESSAGES = []',
    source[idx_dck_start:idx_dck_end+1]
] + funcs_code

with open('core/memory.py', 'r', encoding='utf-8') as f:
    mem_source = f.read()

mem_source = mem_source.replace('import json', 'import json\nimport re\nimport copy\nfrom datetime import datetime\nfrom zoneinfo import ZoneInfo')
mem_source += '\n\n' + '\n\n'.join(mem_additions) + '\n'

with open('core/memory.py', 'w', encoding='utf-8') as f:
    f.write(mem_source)

lines = source.splitlines()
nodes_found.sort(key=lambda x: x[0], reverse=True)
for start, end in nodes_found:
    del lines[start:end]

new_source = '\n'.join(lines)
new_source = new_source.replace('DEFAULT_CHANNEL_ID = "vts_local_user"', '')
new_source = new_source.replace('RECENT_BOT_MESSAGES = []', '')
new_source = new_source.replace(source[idx_dck_start:idx_dck_end+1], '')

new_source = re.sub(r'(from core\.memory import .*)', r'\1, DEFAULT_CHANNEL_ID, save_cloud_knowledge, get_unified_memory_context, RECENT_BOT_MESSAGES', new_source)

new_source = new_source.replace('RECENT_BOT_MESSAGES, ', '')
new_source = new_source.replace(', RECENT_BOT_MESSAGES', '')
new_source = new_source.replace('global RECENT_BOT_MESSAGES\n', '\n')
new_source = new_source.replace('global RECENT_BOT_MESSAGES', 'global ')

with open('vts_7L_test.py', 'w', encoding='utf-8') as f:
    f.write(new_source)

print('Done fixing memory2')
