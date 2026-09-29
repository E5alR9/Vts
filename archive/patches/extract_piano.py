import re

def main():
    with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the start of the piano block
    start_marker = "# ────────────────────────────────────────────────────────\n# 🎹 8.1 88 鍵全音域真實平台鋼琴發聲與樂譜演奏引擎 (Virtual Piano 88K)"
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("Cannot find piano start marker!")
        return

    # Find the end of compose_and_play_original_piano
    end_marker = "async def compose_and_play_original_piano"
    end_func_idx = content.find(end_marker, start_idx)
    if end_func_idx == -1:
        print("Cannot find compose_and_play_original_piano!")
        return

    # We need to find the end of this function. Let's find the next function definition or the end of the block.
    # The next block is usually "# ────────────────────────────────────────────────────────" or "def control_microphone"
    next_func = "def control_microphone"
    end_idx = content.find(next_func, end_func_idx)
    
    if end_idx == -1:
        end_idx = content.find("# ────────────────────────────────────────────────────────", end_func_idx + len(end_marker))
    
    if end_idx == -1:
        print("Cannot find the end of the piano block!")
        return
        
    # The piano engine code
    piano_code = content[start_idx:end_idx].strip() + "\n"

    # Some variables inside piano code need to be replaced if they use global stuff? No, wait. 
    # The piano code uses `log_print`, `is_system_overloaded`, `execute_local_python_code`, `apply_spatial_position`
    # Let's add imports to the top of services/piano_engine.py
    piano_imports = """import os
import json
import time
import asyncio
import random
import math
import base64
import subprocess
import urllib.parse
import aiohttp
import numpy as np
import pygame
import pygame.sndarray
import pygame.midi
import socket
import re
import sys

from core.utils import log_print
from services.vts_client import apply_spatial_position

# If there are circular dependency issues, we can import them locally or pass them.
# The main file provides: DATA_DIR, is_system_overloaded, execute_local_python_code
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
GEMINI_KEYS = []

def is_system_overloaded():
    return False

async def execute_local_python_code(*args, **kwargs):
    pass

"""

    with open('services/piano_engine.py', 'w', encoding='utf-8') as f:
        f.write(piano_imports + "\n" + piano_code)

    # Now we remove it from vts_7L_test.py
    new_content = content[:start_idx] + "\n# [Virtual Piano Module has been extracted to services/piano_engine.py]\n\n" + content[end_idx:]

    # Add import services.piano_engine as pe to vts_7L_test.py
    import_statement = "import services.piano_engine as pe\n"
    new_content = re.sub(r'(from core\.db import \*\n)', r'\1' + import_statement, new_content)
    
    # Replace global variables used in vts_7L_test.py
    vars_to_replace = [
        "is_piano_active", "current_piano_task", "current_piano_process", 
        "current_piano_song_title", "PIANO_NOTE_FOCUS_X", "is_auto_playing_piano",
        "PIANO_SESSION_ID", "LAST_PIANO_OPEN_TIME"
    ]
    
    for v in vars_to_replace:
        # replace whole word matches
        new_content = re.sub(r'\b' + v + r'\b', 'pe.' + v, new_content)
        
    # We must fix global declarations again
    def clean_globals(match):
        prefix = match.group(1)
        vars_str = match.group(2)
        clean_vars = [v.strip() for v in vars_str.split(',') if 'pe.' not in v.strip() and v.strip()]
        if not clean_vars:
            return ''
        return prefix + ', '.join(clean_vars)

    new_content = re.sub(r'(global\s+)(.+?)(?=\n)', clean_globals, new_content)
    
    # There are also some function calls like play_virtual_piano, match_midi_with_ai that need pe. prefix
    funcs_to_replace = [
        "play_virtual_piano", "match_midi_with_ai", "mashup_virtual_piano", 
        "insert_virtual_piano", "compose_and_play_original_piano", "stop_virtual_piano",
        "generate_dynamic_piano_chatter", "resolve_piano_intent_by_ai", "sync_and_update_midi_catalog"
    ]
    
    for f_name in funcs_to_replace:
        # Note: some of them might have been caught by the regex above if we just did word boundary, but let's be sure.
        new_content = re.sub(r'\b' + f_name + r'\b', 'pe.' + f_name, new_content)
        
    # A small hack: pe.pe.var -> pe.var just in case
    new_content = new_content.replace('pe.pe.', 'pe.')

    with open('vts_7L_test.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Extraction successful.")

if __name__ == '__main__':
    main()
