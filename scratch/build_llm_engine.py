
import ast
import re

with open('extracted_llm_funcs.py', 'r', encoding='utf-8') as f:
    code = f.read()

tree = ast.parse(code)

funcs_to_keep = {
    'get_seconds_until_pt_midnight',
    'record_model_failure',
    '_call_single_gemini',
    'fetch_ai_response',
    'fetch_fast_text_reply',
    'call_gemini_live_audience_reply',
    'summarize_search_to_speech',
    'get_available_gemini_channels',
    'get_lightweight_gemini_vision',
    'get_dynamic_live_key_candidates',
    'DualHotStandbyLiveManager'
}

kept_code = []

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if node.name in funcs_to_keep:
            start = node.lineno - 1
            end = getattr(node, 'end_lineno')
            kept_code.append('\n'.join(code.splitlines()[start:end]))

imports = '''import os
import sys
import time
import asyncio
import traceback
import collections
import re
import math
import random
import base64
import io
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from PIL import Image

# Google GenAI imports
from google import genai
from google.genai import types

# Groq (for fast text replies)
from groq import AsyncGroq

# Project imports
from core.utils import log_print, sys_notify, get_current_time_string
import services.piano_engine as pe

# Globals
DEAD_GEMINI_MODELS = {}
MODEL_FAIL_COUNT = collections.defaultdict(int)

# Load Gemini Keys
GEMINI_KEYS = [k.strip() for k in re.split(r'[\s,;]+', os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or "") if k.strip() and len(k.strip()) < 150]
pe.GEMINI_KEYS = GEMINI_KEYS

KEYS_AUDIENCE_LIVE = GEMINI_KEYS[0:6] if len(GEMINI_KEYS) >= 6 else GEMINI_KEYS
KEYS_MIC_LIVE      = GEMINI_KEYS[6:12] if len(GEMINI_KEYS) >= 12 else GEMINI_KEYS
KEYS_VISION        = GEMINI_KEYS[12:18] if len(GEMINI_KEYS) >= 18 else GEMINI_KEYS
KEYS_PROACTIVE     = GEMINI_KEYS[18:24] if len(GEMINI_KEYS) >= 24 else GEMINI_KEYS
KEYS_DAD_MAIN      = GEMINI_KEYS

GROQ_KEYS = [k.strip() for k in re.split(r'[\s,;]+', os.getenv("GROQ_API_KEYS") or os.getenv("GROQ_API_KEY") or "") if k.strip()]
GROQ_CLIENTS = [AsyncGroq(api_key=key) for key in GROQ_KEYS] if GROQ_KEYS else []

# Memory/Search hooks (to avoid circular imports, these can be set by the main file)
fetch_from_long_term_memory_hook = None
save_to_long_term_memory_hook = None
get_recent_100_memory_context_hook = None
search_google_hook = None
'''

final_code = imports + '\n\n' + '\n\n'.join(kept_code)

# Now we need to patch the kept_code to use hooks and remove circular dependencies
# For `fetch_ai_response`, replace `execute_tool_dispatch` with a parameter or hook
final_code = re.sub(r'execute_tool_dispatch\(', 'tool_dispatcher(', final_code)

# Add `tool_dispatcher=None` to fetch_ai_response signature
final_code = final_code.replace(
    'async def fetch_ai_response(prompt: str, user_role_name="user", has_image=False, image_base64=None, audio_base64=None, tools=None, is_proactive=False, lock_target=None, lock_entire_model=False, situation_prompt=None, limit=None, custom_name=None):',
    'async def fetch_ai_response(prompt: str, user_role_name="user", has_image=False, image_base64=None, audio_base64=None, tools=None, is_proactive=False, lock_target=None, lock_entire_model=False, situation_prompt=None, limit=None, custom_name=None, tool_dispatcher=None):'
)

# For memories
final_code = final_code.replace('await fetch_from_long_term_memory(', 'await fetch_from_long_term_memory_hook(')
final_code = final_code.replace('await save_to_long_term_memory(', 'await save_to_long_term_memory_hook(')
final_code = final_code.replace('await get_recent_100_memory_context(', 'await get_recent_100_memory_context_hook(')
final_code = final_code.replace('await search_google(', 'await search_google_hook(')

with open('services/llm_engine.py', 'w', encoding='utf-8') as f:
    f.write(final_code)
