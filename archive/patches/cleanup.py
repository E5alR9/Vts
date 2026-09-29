import re

with open('vts_7L_test_mod.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the global variables initialization block
content = re.sub(r'vc\.target_look_x = 0\.0\nvc\.target_look_y = 0\.0\nvc\.current_look_x = 0\.0\nvc\.current_look_y = 0\.0\nvc\.is_tracking_mouse = False\nvc\.force_blink_trigger = 0\nvc\.eye_roll_timer = 0\.0\nvc\.shock_timer = 0\.0\nvc\.wink_timer = 0\.0\nvc\.wink_side = "left"\nvc\.frown_timer = 0\.0\n', '', content)

content = re.sub(r'vc\.vts_lock = asyncio\.Lock\(\)\n', '', content)
content = re.sub(r'vc\.GLOBAL_VTS = None\n', '', content)
content = re.sub(r'vc\.MY_CONTROLLED_EXPS = \[.*?\]\n', '', content)
content = re.sub(r'vc\.CURRENT_ACTIVE_EXP = None\n', '', content)

# Remove the VTS block (from 'class RobustVTSClient:' to end of 'trigger_vts_expression')
content = re.sub(r'class RobustVTSClient:.*?async def trigger_vts_expression[^\n]*?:\n(?:    [^\n]*\n|\s*\n)*?(?=\n# ──+)', '', content, flags=re.DOTALL)
content = re.sub(r'EXPRESSION_HOLD_SECONDS = 3\.5[^\n]*\n', '', content)
content = re.sub(r'VTS_EXPRESSION_MAP = \{.*?\n\}\n', '', content, flags=re.DOTALL)
content = re.sub(r'vc\.CURRENT_SPATIAL_LOCATION = "center"\nIS_AUTO_WANDER_ENABLED = True\nLAST_WANDER_TIME = time\.time\(\)\n\nBASE_VTS_MODEL_X = 0\.65\nBASE_VTS_MODEL_Y = -1\.28\nBASE_VTS_MODEL_SIZE = -54\.8\nCURRENT_VTS_MODEL_X = None\nCURRENT_VTS_MODEL_Y = None\nCURRENT_VTS_MODEL_SIZE = None\n', '', content)

# Also remove global declarations that might be leftover
content = re.sub(r'global current_ai_state, vc\.target_look_x, vc\.target_look_y, vc\.current_look_x, vc\.current_look_y, vc\.is_tracking_mouse, vc\.force_blink_trigger, vc\.eye_roll_timer, PIANO_NOTE_FOCUS_X, vc\.frown_timer, IS_MP3_PLAYING, vc\.shock_timer, CURRENT_PLAYING_VOICE_TASK', 'global current_ai_state, PIANO_NOTE_FOCUS_X, IS_MP3_PLAYING, CURRENT_PLAYING_VOICE_TASK', content)

content = re.sub(r'global vc\.CURRENT_ACTIVE_EXP', '', content)

imports = """import services.vts_client as vc
from services.vts_client import RobustVTSClient, move_vts_spatial, apply_spatial_position, set_vts_expression, trigger_vts_expression
"""
content = re.sub(r'(from core\.db import \*\n)', r'\1' + imports, content)

with open('vts_7L_test.py', 'w', encoding='utf-8') as f:
    f.write(content)
