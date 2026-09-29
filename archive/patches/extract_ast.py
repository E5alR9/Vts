import ast

def get_node_lines(node):
    return node.lineno - 1, getattr(node, 'end_lineno')

with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    source = "".join(lines)

tree = ast.parse(source)

target_functions = {
    'get_seconds_until_pt_midnight',
    'record_model_failure',
    '_call_single_gemini',
    'fetch_ai_response',
    'fetch_fast_text_reply',
    'call_gemini_live_audience_reply',
    'summarize_search_to_speech',
    'execute_tool_dispatch',
    'get_available_gemini_channels',
    'get_lightweight_gemini_vision',
    'get_dynamic_live_key_candidates'
}

target_classes = {
    'DualHotStandbyLiveManager'
}

lines_to_extract = set()
nodes_found = []

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in target_functions:
        start, end = get_node_lines(node)
        nodes_found.append((start, end))
    elif isinstance(node, ast.ClassDef) and node.name in target_classes:
        start, end = get_node_lines(node)
        nodes_found.append((start, end))

# Sort nodes in reverse order so deleting doesn't shift indices
nodes_found.sort(key=lambda x: x[0], reverse=True)

extracted_code = []

# Also grab the global vars block. It's lines 193 to 221 roughly. 
# We'll just grab that specific block manually or let it be for now and copy it.

with open('llm_nodes_info.txt', 'w', encoding='utf-8') as f:
    for start, end in nodes_found:
        f.write(f"{start},{end}\n")
        extracted_code.append("".join(lines[start:end]))

extracted_code.reverse() # original order

with open('extracted_llm_funcs.py', 'w', encoding='utf-8') as f:
    f.write("\n\n".join(extracted_code))

print(f"Extracted {len(nodes_found)} nodes.")
