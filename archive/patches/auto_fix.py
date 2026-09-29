import re

with open('flake_out.txt', 'r', encoding='utf-16') as f:
    flake_output = f.readlines()

with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Fix missing import
for i, line in enumerate(lines):
    if 'get_unified_memory_context' in line and 'core.memory' in line:
        if 'RECENT_BOT_MESSAGES' not in line:
            lines[i] = line.replace('get_unified_memory_context', 'get_unified_memory_context, RECENT_BOT_MESSAGES')
        break

# 2. Fix warnings
unused_globals = {}
f_string_lines = []
unused_imports = []

for out_line in flake_output:
    match = re.match(r'vts_7L_test\.py:(\d+):.*`global (.*)` is unused', out_line)
    if match:
        lineno = int(match.group(1)) - 1
        var_name = match.group(2).strip()
        if lineno not in unused_globals:
            unused_globals[lineno] = []
        unused_globals[lineno].append(var_name)
    
    match_f = re.match(r'vts_7L_test\.py:(\d+):.*f-string is missing placeholders', out_line)
    if match_f:
        f_string_lines.append(int(match_f.group(1)) - 1)
        
    match_imp = re.match(r'vts_7L_test\.py:(\d+):.*\'(.*)\' imported but unused', out_line)
    if match_imp:
        unused_imports.append((int(match_imp.group(1)) - 1, match_imp.group(2).strip()))
        
    match_redef = re.match(r'vts_7L_test\.py:(\d+):.*redefinition of unused \'(.*)\' from line', out_line)
    if match_redef:
        unused_imports.append((int(match_redef.group(1)) - 1, match_redef.group(2).strip()))

# Apply unused globals
for lineno, vars_to_remove in unused_globals.items():
    line = lines[lineno]
    if 'global' in line:
        # extract global statement
        m = re.search(r'global\s+(.+)', line)
        if m:
            declared_vars = [v.strip() for v in m.group(1).split(',')]
            remaining_vars = [v for v in declared_vars if v not in vars_to_remove]
            if not remaining_vars:
                # Remove the whole global keyword
                # The line might be just "        global x\n", if so, we leave it blank or just indent.
                lines[lineno] = line[:m.start()] + '\n'
            else:
                lines[lineno] = line[:m.start()] + 'global ' + ', '.join(remaining_vars) + '\n'

# Apply f-strings
for lineno in f_string_lines:
    line = lines[lineno]
    # Simple replace: find f" or f' and replace with " or ' (careful not to replace normal characters)
    line = re.sub(r'\bf(["\'])', r'\1', line)
    lines[lineno] = line

with open('vts_7L_test.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixes applied.")
