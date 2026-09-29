import re

with open(r'c:\Users\qiwai\services\piano_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add missing standard imports at the top
imports_to_add = """
from typing import Optional, Dict, List, Tuple, Union
from collections import deque
import collections
import ctypes
import glob
from google import genai
from google.genai import types
import services.vts_client as vc
from services.vts_client import move_vts_spatial, set_vts_expression

import __main__

# Dynamic proxies for main module objects
class MainProxy:
    def __getattr__(self, name):
        return getattr(__main__, name, None)

main_obj = MainProxy()
"""

# We will replace all references to undefined main variables with main_obj.XYZ
main_vars = [
    'os_desktop_sensor',
    'realtime_task_mgr',
    'update_subtitle',
    'append_to_unified_memory',
    'HIGH_IQ_GEMINI_MODELS',
    'DEAD_GEMINI_MODELS',
    'is_model_locked',
    'get_pingpong_ring_indices',
    'get_user_profile',
    'DEFAULT_USER_TITLE',
    'get_pingpong_alternating_index',
    'speech_queue'
]

for v in main_vars:
    # only replace when it's a standalone variable (not part of another word)
    # e.g., update_subtitle(...) -> main_obj.update_subtitle(...)
    content = re.sub(r'(?<![\w\.])' + v + r'\b', f'main_obj.{v}', content)

# Insert imports after the first few lines of imports
import_idx = content.find('import sys')
if import_idx != -1:
    insert_idx = content.find('\n', import_idx) + 1
    content = content[:insert_idx] + imports_to_add + content[insert_idx:]
else:
    content = imports_to_add + content

with open(r'c:\Users\qiwai\services\piano_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
