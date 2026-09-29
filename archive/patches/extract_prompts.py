import ast
import re

with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    source = f.read()

tree = ast.parse(source)

target_classes = {'TextCleanEngine', 'PromptTemplateEngine'}

kept_code = []
nodes_found = []

for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name in target_classes:
        start = node.lineno - 1
        end = getattr(node, 'end_lineno')
        nodes_found.append((start, end))
        kept_code.append('\n'.join(source.splitlines()[start:end]))

if not nodes_found:
    print("No nodes found for prompts.py")
else:
    imports = """import re
import random
import sys

# Project imports
from core.utils import log_print
import services.piano_engine as pe
"""
    
    with open('core/prompts.py', 'w', encoding='utf-8') as f:
        f.write(imports + '\n\n' + '\n\n'.join(kept_code))
        
    print(f"Created core/prompts.py with {len(nodes_found)} classes.")
    
    # Remove from main file
    lines = source.splitlines()
    # sort reverse
    nodes_found.sort(key=lambda x: x[0], reverse=True)
    for start, end in nodes_found:
        del lines[start:end]
        
    # Inject import
    import_stmt = "from core.prompts import TextCleanEngine, PromptTemplateEngine\n"
    # find where to insert
    pe_idx = -1
    for i, line in enumerate(lines):
        if 'import services.piano_engine' in line:
            pe_idx = i
            break
            
    if pe_idx != -1:
        lines.insert(pe_idx + 1, import_stmt)
    else:
        lines.insert(0, import_stmt)
        
    with open('vts_7L_test.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print("Patched vts_7L_test.py for prompts")
