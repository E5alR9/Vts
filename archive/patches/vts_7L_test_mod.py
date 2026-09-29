# ==============================================================================
# 🌟 7L AI-VTuber 智慧一體化核心系統 (vts_7L_test.py)
# 👑 作者: E5alR9 & 7L 開發團隊
# 🎯 核心特色:
#    - ⚡ Google GenAI Live API (全雙工雙向音訊、背景潛意識發言哨兵、雙軌熱備)
#    - 🧠 8 大 Gemini 模型智能階梯調度 (3.1 Flash Lite ➔ 3.5 Flash Lite ➔ 3 Flash ➔ 3.1 Pro ➔ 3.5 ➔ 3.6 ➔ 3.7 ➔ 3.8 Flash)
#    - 📜 100 句全景記憶滾動中樞 (Live2D 表情、視線走位、觀眾個人檔案 Firestore 雲端同步)
#    - 🎹 88 鍵全音域平台鋼琴即時發聲與 MIDI 智能搜譜演奏
#    - 👁️ 即時多螢幕視覺感知、眼角餘光與 WASAPI 電腦內部聲音監聽
#    - 🎮 Python 本機沙盒遊樂場、Tavily 網路搜尋、Nano 生圖與 Discord CMA 狀態監控
# 📑 腳本模組導覽目錄 (Table of Contents):
#  1. 🔐 環境變數載入與金鑰矩陣分流 (API Keys, DualHotStandby Live Manager)
#  2. 🧠 模型梯隊清單與排程定義 (GEMINI_MODELS 7-Tier Matrix)
#  3. 🚦 API 頻率限制、冷卻與熔斷管理 (Circuit Breaker & Lock Cache)
#  4. 🖥️ 全域狀態變數與硬體環境偵測 (Global State & Resolution)
#  5. 💾 Firebase 雲端永久記憶與觀眾檔案 (Long-Term Memory & Viewer Profile)
#  6. 🌐 VTube Studio WebSocket 引擎與 Live2D 控制 (VTSManager & Expression Dispatcher)
#  7. 🎮 7L 本機遊樂場沙盒 (7L_Playground Python Sandbox)
#  8. 🛠️ Google GenAI 官方 Function Calling 工具清單 (GENAI_TOOLS & Dispatcher)
#     8.1 🎹 88 鍵平台鋼琴發聲與樂譜演奏引擎 (Virtual Piano 88K & MIDI Player)
#  9. 🛡️ 防跳針與記憶去重系統 (Code-Level Anti-Repetition)
# 10. 🔊 語音合成、音訊分析與字幕工具 (Edge-TTS & Subtitle File Updater)
# 11. 👁️ 視覺感知、畫面截圖與輕量眼角餘光 (Screen Vision & get_lightweight_gemini_vision)
# 12. 🧠 旗艦多模態大腦推理核心 (fetch_ai_response: Gemini Multimodal Dispatcher)
# 13. 🕹️ 使用者指令、電腦控制與計時器動作 (execute_actions & System Controls)
# 14. ⚙️ 專屬背景工作協程群 (Workers: Screen, Vision, WASAPI Loopback Audio, Proactive)
# 15. 🤖 對話處理、Live 潛意識哨兵與 100 句記憶中樞 (Mind-Stream & Audience Live Channel)
# 16. 🖥️ CMA 狀態監控檔案輸出與 Discord 機器人 (CMA Monitor & Discord Bot Commands)
# 17. 🚀 主程式進入點與終端機即時狀態列 (main Entry Point & ANSI Status Bar)
# ==============================================================================

from PIL import BmpImagePlugin
from PIL import Image, ImageDraw, ImageGrab, ImageChops
import os
import sys
import io
import copy
import subprocess
import re
import asyncio
import aiohttp
import websockets
import pyvts
import edge_tts
import pygame
import time
import json
import base64
import datetime
import pyautogui
import speech_recognition as sr
import math
import random
import wave
import socket
import numpy as np
import soundcard as sc
import psutil
import glob
import difflib
from typing import Optional, Dict, List, Tuple, Any, Union
import collections
from collections import deque, defaultdict
import shutil
import webbrowser
import platform
import warnings
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import ctypes
try:
    from tavily import TavilyClient
except (ImportError, Exception):
    TavilyClient = None
try:
    import msvcrt
except ImportError:
    msvcrt = None

VM_AGENT_CLIENT = None

import logging

# 🔇 靜音所有第三方日誌與 AFC 警告，保持控制台狀態列極致純淨
os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
warnings.filterwarnings("ignore")

for log_name in ["google", "google.genai", "google_genai", "google.genai.models", "absl", "urllib3", "asyncio"]:
    logging.getLogger(log_name).setLevel(logging.ERROR)

try:
    if hasattr(sc, "SoundcardRuntimeWarning"):
        warnings.filterwarnings("ignore", category=sc.SoundcardRuntimeWarning)
except Exception:
    pass

# 🌟 設定 Windows 控制台為 UTF-8 代碼頁 (CP 65001) 並開啟 ANSI 虛擬終端處理，徹底修復中文字元重複、動態刷新與換行殘影
if sys.platform == "win32":
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    try:
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
        # 啟用 ENABLE_VIRTUAL_TERMINAL_PROCESSING (0x0004) 支援原生 ANSI 擦除
        kernel32 = ctypes.windll.kernel32
        hStdOut = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(hStdOut, ctypes.byref(mode)):
            kernel32.SetConsoleMode(hStdOut, mode.value | 0x0004 | 0x0002)
    except Exception:
        pass
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

from core.utils import log_print, sys_notify, get_current_time_string
from core.db import *

import unicodedata

def get_char_width(ch: str) -> int:
    ea = unicodedata.east_asian_width(ch)
    if ea in ('F', 'W'):
        return 2
    code = ord(ch)
    if 0x1F000 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF:
        return 2
    return 1

def get_display_width(text: str) -> int:
    return sum(get_char_width(ch) for ch in text)

def fit_text_to_width(text: str, max_cols: int) -> str:
    """精準將字串截斷至指定終端機欄位寬度以內，並避免換行溢出"""
    if max_cols <= 3:
        return text[:max_cols]
    total_w = get_display_width(text)
    if total_w <= max_cols:
        return text
    
    target_w = max_cols - 2
    cur_w = 0
    res = []
    for ch in text:
        w = get_char_width(ch)
        if cur_w + w > target_w:
            break
        res.append(ch)
        cur_w += w
    return "".join(res) + ".."

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

# 導入 Google 官方 GenAI SDK (主力視覺與大腦)
from google import genai
from google.genai import types
from realtime_tasks.task_manager import realtime_task_mgr
from mic_live_plugin import mic_live_analyzer, voiceprint_verifier, os_desktop_sensor

# ────────────────────────────────────────────────────────
# 🔐 1. 環境變數載入與金鑰矩陣分流初始化 (API Keys & Pools)
# ────────────────────────────────────────────────────────
# 💡 功能目的：
#    從 .env 檔載入所有第三方服務金鑰（Groq、Gemini 核心金鑰矩陣、Tavily 網路搜尋、Firebase、Discord），
#    並將 Gemini 金鑰池智慧劃分為多個專用通道，確保即時背景感知與老爸主腦互不干擾。

load_dotenv()
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"  # 關閉 Hugging Face 符號連結警告

print("=== 🔍 .env 金鑰讀取測試 ===")

# 🔑 Groq 金鑰載入（可供備援或特定輕量任務調度）
GROQ_KEYS = [k.strip() for k in re.split(r'[\s,;]+', os.getenv("GROQ_API_KEYS") or os.getenv("GROQ_API_KEY") or "") if k.strip()]
print(f"✅ 找到 {len(GROQ_KEYS)} 把 Groq 金鑰")

# 🔑 Gemini 核心金鑰矩陣（支援多達 31 把 API Key 輪流調度與熔斷管理）
GEMINI_KEYS = [k.strip() for k in re.split(r'[\s,;]+', os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or "") if k.strip() and len(k.strip()) < 150]
print(f"✅ 找到 {len(GEMINI_KEYS)} 把 Gemini 核心金鑰")

# 🔒 專屬獨立金鑰池劃分 (背景/Live通道專屬分工，老爸主腦享有全量金鑰矩陣)：
#    - KEYS_AUDIENCE_LIVE: 100 句記憶與彈幕潛意識發言審查 Live 專用通道 (6把)
#    - KEYS_MIC_LIVE: 麥克風語音/情緒即時 Live 分析 (6把)
#    - KEYS_VISION: 電腦螢幕截圖與眼角餘光視覺 (6把)
#    - KEYS_PROACTIVE: 鋼琴電台與主播自主巡邏 (6把)
#    - KEYS_DAD_MAIN: 老爸主腦享有全量 31 把金鑰完整矩陣！
KEYS_AUDIENCE_LIVE = GEMINI_KEYS[0:6] if len(GEMINI_KEYS) >= 6 else GEMINI_KEYS
KEYS_MIC_LIVE      = GEMINI_KEYS[6:12] if len(GEMINI_KEYS) >= 12 else GEMINI_KEYS
KEYS_VISION        = GEMINI_KEYS[12:18] if len(GEMINI_KEYS) >= 18 else GEMINI_KEYS
KEYS_PROACTIVE     = GEMINI_KEYS[18:24] if len(GEMINI_KEYS) >= 24 else GEMINI_KEYS
KEYS_DAD_MAIN      = GEMINI_KEYS # 👑 老爸旗艦主腦享有全部金鑰全量矩陣！

print(f"  ⚡ 100 句記憶潛意識哨兵 Live 通道: 分配 {len(KEYS_AUDIENCE_LIVE)} 把專用金鑰")
print(f"  🎙️ 麥克風情緒感知 Live 通道: 分配 {len(KEYS_MIC_LIVE)} 把專用金鑰")
print(f"  👁️ 餘光視覺感知通道: 分配 {len(KEYS_VISION)} 把專用金鑰")
print(f"  📻 鋼琴電台與 Proactive: 分配 {len(KEYS_PROACTIVE)} 把專用金鑰")
print(f"  👑 老爸主腦專屬對話: 享有全量 {len(KEYS_DAD_MAIN)} 把金鑰完整矩陣！")

mic_live_analyzer.set_api_keys(KEYS_MIC_LIVE)

class DualHotStandbyLiveManager:
    """
    🛡️ 【Live 潛意識哨兵雙軌熱備中樞 (Dual Hot-Standby Live Sentry Manager)】
    
    🎯 目的：
       為 100 句記憶與彈幕審查哨兵，時刻維持 2 把確定可用、隨時待命的 Live API 金鑰 (Primary 主通道 + Standby 備用通道)。
    
    ⚙️ 運作邏輯：
       1. 正常時由 Primary 主通道提供無限額度超低延遲潛意識發言二元決策。
       2. 當 Primary 發生 429、網路斷線或異常時，Standby 備用通道 0 秒無縫接管升為主通道。
       3. 同時自動從候選金鑰池中迅速補足新的 Standby 金鑰，確保系統永遠有 2 個在線通道熱備！
    """
    def __init__(self, key_pool: List[str]):
        self.key_pool = key_pool
        self.primary_key = key_pool[0] if len(key_pool) > 0 else ""
        self.standby_key = key_pool[1] if len(key_pool) > 1 else (key_pool[0] if key_pool else "")
        self.cooldown_keys: Dict[str, float] = {}

    def get_active_keys(self) -> Tuple[str, str]:
        """取得當前的主通道與備用通道金鑰字串"""
        return self.primary_key, self.standby_key

    def report_key_failure(self, failed_key: str):
        """報告金鑰連線失敗，將其加入冷卻並觸發雙軌熱備無縫切換"""
        now = time.time()
        self.cooldown_keys[failed_key] = now + 45.0
        if failed_key == self.primary_key:
            log_print(f"⚡ [Live 雙軌熱備] 主通道金鑰 (...{failed_key[-6:]}) 異常 ➔ 備用通道 (...{self.standby_key[-6:]}) 立即無縫接管升為主通道！")
            self.primary_key = self.standby_key
            self.standby_key = self._find_next_healthy_key(exclude=[self.primary_key])
        elif failed_key == self.standby_key:
            log_print(f"⚡ [Live 雙軌熱備] 備用通道金鑰 (...{failed_key[-6:]}) 異常 ➔ 立即從金鑰池替換新的熱備金鑰！")
            self.standby_key = self._find_next_healthy_key(exclude=[self.primary_key])

        p_label = f"...{self.primary_key[-6:]}" if self.primary_key else "無"
        s_label = f"...{self.standby_key[-6:]}" if self.standby_key else "無"
        log_print(f"🛡️ [Live 雙軌熱備更新完成] 🟢 主通道: {p_label} | 🟢 備用通道: {s_label}")

    def _find_next_healthy_key(self, exclude: List[str]) -> str:
        """尋找下一把未冷卻且健康的可用金鑰"""
        now = time.time()
        for k in self.key_pool + GEMINI_KEYS:
            if k not in exclude and self.cooldown_keys.get(k, 0) < now:
                return k
        for k in self.key_pool + GEMINI_KEYS:
            if k not in exclude:
                return k
        return self.primary_key

dual_audience_live_mgr = DualHotStandbyLiveManager(KEYS_AUDIENCE_LIVE)

def get_dynamic_live_key_candidates(preferred_pool: List[str]) -> List[str]:
    """
    🔄 動態 Live API 金鑰故障轉移候選池
    
    🎯 目的：
       優先使用該通道專用金鑰，遇到 429/網路中斷時，自動跨池調用全量空閒金鑰繼續維持 Live 雙工對話。
    """
    candidates = []
    seen = set()
    for k in preferred_pool:
        if k and k not in seen:
            candidates.append(k)
            seen.add(k)
    for k in GEMINI_KEYS:
        if k and k not in seen:
            candidates.append(k)
            seen.add(k)
    return candidates

# 🔍 Tavily 網路即時搜尋金鑰載入
TAVILY_KEYS = [k.strip() for k in re.split(r'[\s,;]+', os.getenv("TAVILY_KEYS") or os.getenv("TAVILY_API_KEYS") or os.getenv("TAVILY_API_KEY") or "") if k.strip()]
print(f"✅ 找到 {len(TAVILY_KEYS)} 把 Tavily 金鑰")

# 💾 Firebase 雲端服務帳號 JSON 與 Discord Bot Token
FIREBASE_CRED_JSON = os.getenv("FIREBASE_CRED_JSON")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN_7L")

print("===========================\n")

# 初始化 Groq 客戶端池
GROQ_CLIENTS = []
try:
    from groq import AsyncGroq
    for key in GROQ_KEYS:
        if key: GROQ_CLIENTS.append(AsyncGroq(api_key=key))
except ImportError:
    pass

class PurePythonTavilyClient:
    """純 Python Tavily 輕量搜尋客戶端（0 C/DLL 依賴，徹底避免 Windows AppLocker 或 tiktoken.pyd 崩潰）"""
    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, query: str, search_depth: str = "advanced", topic: str = "general", **kwargs) -> dict:
        import urllib.request, json
        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": search_depth,
                "topic": topic,
                **kwargs
            }
            req = urllib.request.Request(
                "https://api.tavily.com/search",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"error": str(e)}

if TAVILY_KEYS:
    if TavilyClient is not None:
        try:
            tavily_client = TavilyClient(api_key=TAVILY_KEYS[0])
        except Exception:
            tavily_client = PurePythonTavilyClient(api_key=TAVILY_KEYS[0])
    else:
        tavily_client = PurePythonTavilyClient(api_key=TAVILY_KEYS[0])
else:
    tavily_client = None

# ────────────────────────────────────────────────────────
# 🧠 2. 模型清單與大腦池定義 (GEMINI_MODELS 7-Tier Matrix)
# ────────────────────────────────────────────────────────
# 💡 功能目的：
#    定義 7L 核心大腦的 8 大階梯模型順序，由超低延遲輕量模型優先秒回，
#    並在複雜任務或高質量需求時自動升級至頂配旗艦大腦。

GEMINI_MODELS = [
    # ⚡ 第 1~3 梯隊：極速輕量前鋒 (超低延遲、自然口語、秒回首選)
    "gemini-3.1-flash-lite",               # ⚡ 第 1 位：超低延遲、自然口語、秒回首選
    "gemini-3.5-flash-lite",               # 🛡️ 第 2 位：超大額度輕量保底防線
    "gemini-3-flash-preview",              # ⚡ 第 3 位：閃電推理預覽
    
    # 🧠 第 4~8 梯隊：高智商 Pro & 旗艦深度思考大腦 (精準工具調用、視覺分析、原生 Thinking 深度思考)
    "gemini-3.1-pro-preview",              # 🧠 第 4 位：超高智商 Pro 預覽
    "gemini-3.5-flash",                    # 🥈 第 5 位：高智商穩定主力保底
    "gemini-3.6-flash",                    # 👑 第 6 位：最新高智商旗艦主力，視覺與工具調用精準
    "gemini-3.7-flash",                    # 👑 第 7 位：頂配旗艦大腦（深度思考 Thinking 原生開啟，充當腦內心聲）
    "gemini-3.8-flash",                    # 🚀 第 8 位：2026 全新頂配旗艦大腦（深度思考與多模態頂尖推理）
]

# 👑 高智商任務專屬倒序模型梯隊 (由 3.8 旗艦深度思考領銜，專攻找歌判斷、找譜語意、代碼、哲學與高難度推理)
HIGH_IQ_GEMINI_MODELS = [ 
    "gemini-3.8-flash",                    # 🚀 第 1 優先：2026 全新頂配旗艦大腦（最強深度思考與頂尖推理）
    "gemini-3.7-flash",                    # 👑 第 2 位：頂配旗艦大腦（深度思考 Thinking 原生開啟）
    "gemini-3.6-flash",                    # 👑 第 3 位：高智商旗艦主力，視覺與工具調用精確
    "gemini-3.5-flash",                    # 🥈 第 4 位：高智商穩定主力保底
    "gemini-3.1-pro-preview",              # 🧠 第 5 位：超高智商 Pro 預覽
    "gemini-3-flash-preview",              # ⚡ 第 6 位：閃電推理預覽
    "gemini-3.5-flash-lite",               # 🛡️ 第 7 位：超大額度輕量保底防線
    "gemini-3.1-flash-lite",               # ⚡ 第 8 位：超低延遲輕量秒回
]

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
AUDIO_CACHE_DIR = os.path.join(DATA_DIR, "recent_audio")
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
MAX_LOCAL_AUDIO_FILES = 80  # 🎙️ 自動保留本機最近 80 句高音質錄音

def save_local_audio_clip(audio_base64: str) -> Optional[str]:
    """將麥克風錄音 WAV 保存至本機快取目錄，並自動滾動清理過舊檔案"""
    if not audio_base64:
        return None
    try:
        raw_bytes = base64.b64decode(audio_base64) if isinstance(audio_base64, str) else audio_base64
        if len(raw_bytes) < 100:
            return None
        
        ts_str = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y%m%d_%H%M%S_%f")[:19]
        file_name = f"mic_{ts_str}.wav"
        file_path = os.path.join(AUDIO_CACHE_DIR, file_name)
        
        with open(file_path, "wb") as f:
            f.write(raw_bytes)
            
        # 滾動清理：若超過 MAX_LOCAL_AUDIO_FILES，自動刪除最舊的檔案
        all_audios = sorted(glob.glob(os.path.join(AUDIO_CACHE_DIR, "mic_*.wav")))
        if len(all_audios) > MAX_LOCAL_AUDIO_FILES:
            for old_f in all_audios[:-MAX_LOCAL_AUDIO_FILES]:
                try: os.remove(old_f)
                except Exception: pass
                
        return file_path
    except Exception:
        return None

def get_recent_local_audio_clips(limit: int = 5) -> List[str]:
    """取得本機最近幾筆有效錄音檔案路徑"""
    all_audios = sorted(glob.glob(os.path.join(AUDIO_CACHE_DIR, "mic_*.wav")))
    return all_audios[-limit:] if all_audios else []

def load_audio_clip_base64(file_path: str) -> Optional[str]:
    """從本機讀取錄音檔並轉為 Base64 字串供 Gemini 調用"""
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception:
            pass
    return None

DEAD_GEMINI_MODELS = set()
API_LOCKS_FILE = os.path.join(DATA_DIR, "api_locks_cache.json")
API_LOCKS = {}

# ────────────────────────────────────────────────────────
# 🚦 3. API 頻率限制、冷卻與熔斷管理系統 (Circuit Breaker)
# ────────────────────────────────────────────────────────
# 💡 功能目的：
#    當某金鑰或模型回傳 429 / 503 / 資源耗盡時，自動對該通道加鎖冷卻，
#    並將鎖定狀態持久化到本地 JSON，防止開台期間重複呼叫故障通道。

def load_api_locks():
    """載入並清理已過期的 API 鎖定快取"""
    global API_LOCKS
    if os.path.exists(API_LOCKS_FILE):
        try:
            with open(API_LOCKS_FILE, "r", encoding="utf-8") as f:
                locks = json.load(f)
            now = time.time()
            API_LOCKS = {k: v for k, v in locks.items() if v > now}
        except Exception:
            API_LOCKS = {}

def save_api_locks():
    """持久化 API 鎖定狀態到本地檔案"""
    try:
        with open(API_LOCKS_FILE, "w", encoding="utf-8") as f:
            json.dump(API_LOCKS, f)
    except Exception:
        pass

load_api_locks()

def get_seconds_until_pt_midnight() -> float:
    """計算從現在到美國太平洋時間 (PT) 下一個午夜 00:00 還剩多少秒（用於每日配額 RPD 刷新）"""
    try:
        pt_zone = ZoneInfo("America/Los_Angeles")
        now_pt = datetime.now(pt_zone)
        tomorrow_pt = (now_pt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        diff = (tomorrow_pt - now_pt).total_seconds()
        return max(60.0, diff)
    except Exception:
        return 3600.0

def parse_cooldown_seconds(error_text: str, headers=None) -> float:
    if headers:
        retry_after = headers.get("Retry-After") or headers.get("retry-after")
        if retry_after:
            try: return max(15.0, float(retry_after) + 5.0)
            except ValueError: pass

    total_seconds = 60.0 
    if not error_text: return total_seconds
        
    error_lower = error_text.lower()

    # 1. 優先精準捕獲 Google GenAI / Groq API 返回的重試秒數或時間字串 (如 "retry in 53.5s", "retryDelay: '53s'")
    match_retry_in = re.search(r'retry (?:in|after|delay)[:\s\']*([0-9.]+)\s*s', error_lower)
    if match_retry_in:
        try: return max(10.0, float(match_retry_in.group(1)) + 5.0)
        except ValueError: pass

    match_hms = re.search(r'(?:try again in|retry in|wait)\s+(?:(\d+)h)?(?:(\d+)m)?([0-9.]+)s', error_lower)
    if match_hms:
        hours = int(match_hms.group(1)) if match_hms.group(1) else 0
        minutes = int(match_hms.group(2)) if match_hms.group(2) else 0
        seconds = float(match_hms.group(3)) if match_hms.group(3) else 0.0
        return max(10.0, hours * 3600 + minutes * 60 + seconds + 5.0) 
        
    match_sec = re.search(r'(?:retry-after|wait|in|please wait)\s+([0-9.]+)\s*(?:s|sec|second|seconds)?', error_lower)
    if match_sec:
        try: return max(10.0, float(match_sec.group(1)) + 5.0)
        except ValueError: pass

    # 2. 404 或未開通 / 下架模型，鎖定至 PT 午夜 (並永久記錄至 DEAD_GEMINI_MODELS)
    if "404" in error_lower or "not_found" in error_lower or "no longer available" in error_lower:
        return get_seconds_until_pt_midnight()

    # 3. 每日總配額耗盡 (Per Day / Daily / RequestsPerDay / RPD) 封印至 PT 午夜 (隔天重置)
    is_daily_exhausted = any(k in error_lower for k in ["per day", "requests per day", "daily requests", "rpd", "tokens per day", "tpd"]) and not any(k in error_lower for k in ["per minute", "minute", "rpm", "tpm"])
    if is_daily_exhausted:
        return get_seconds_until_pt_midnight()

    # 4. 503 暫時性伺服器超載 (鎖定 3 分鐘 / 180 秒)
    if "503" in error_lower or "unavailable" in error_lower or "high demand" in error_lower:
        return 180.0

    # 5. 429 瞬間速率超速 / 頻率限制 (預設短暫冷卻 60 秒)
    if "429" in error_lower or "rate limit" in error_lower or "resource" in error_lower or "quota" in error_lower:
        return 60.0  

    return max(30.0, total_seconds)

def is_locked(target_id):
    if target_id in API_LOCKS:
        if time.time() < API_LOCKS[target_id]:
            return True
        else:
            del API_LOCKS[target_id] 
            save_api_locks()
    return False

def lock_target(target_id, error_msg="", headers=None):
    duration = parse_cooldown_seconds(error_msg, headers)
    API_LOCKS[target_id] = time.time() + duration
    save_api_locks()
    
    if duration >= 3600: dur_str = f"{duration/3600:.1f}h"
    elif duration >= 60: dur_str = f"{duration/60:.1f}m"
    else: dur_str = f"{int(duration)}s"
        
    sys_notify(f"🛑 封印通道 {target_id} ({dur_str})", duration=3.0)

MODEL_FAIL_COUNT = {}

def is_model_locked(model_name: str) -> bool:
    short_m = model_name.replace("gemini-", "").replace("openai/", "").replace("llama-", "").replace("gemma-", "")
    model_lock_id = f"MODEL_{short_m}"
    return is_locked(model_lock_id)

def lock_entire_model(model_name: str, duration: float = 60.0, reason: str = "伺服器超載"):
    short_m = model_name.replace("gemini-", "").replace("openai/", "").replace("llama-", "").replace("gemma-", "")
    model_lock_id = f"MODEL_{short_m}"
    API_LOCKS[model_lock_id] = time.time() + duration
    save_api_locks()
    dur_str = f"{int(duration)}s" if duration < 60 else (f"{duration/60:.1f}m" if duration < 3600 else f"{duration/3600:.1f}h")
    log_print(f"⚡ [大腦極速熔斷] 模型 [{model_name}] 遇 {reason} ➔ 暫停此模型 {dur_str}，秒切下一個備用模型！")

def record_model_failure(model_name: str, err_str: str):
    global MODEL_FAIL_COUNT
    MODEL_FAIL_COUNT[model_name] = MODEL_FAIL_COUNT.get(model_name, 0) + 1
    # 🌟 換模型門檻：依序輪詢 API 金鑰總數的 2/3，輪完 2/3 都失敗才切換下一個備用模型
    num_keys = len(GEMINI_KEYS)
    threshold = max(3, int(math.ceil(num_keys * 2.0 / 3.0))) if num_keys > 0 else 4
    if MODEL_FAIL_COUNT[model_name] >= threshold:
        if "503" in err_str or "unavailable" in err_str or "high demand" in err_str:
            reason = f"依序輪詢 {threshold} 把金鑰均遇 503 伺服器超載"
            m_duration = 180.0  # 503 模型級熔斷 3 分鐘
        elif "429" in err_str or "rate limit" in err_str:
            reason = f"依序輪詢 {threshold} 把金鑰均遇 429 頻率上限"
            m_duration = 60.0
        else:
            reason = f"依序輪詢 {threshold} 把金鑰均異常"
            m_duration = 60.0
        lock_entire_model(model_name, duration=m_duration, reason=reason)
        MODEL_FAIL_COUNT[model_name] = 0

# 🛑 自主發話時主動保留/跳過的頂配旗艦大腦清單（保留給老爸主動對話使用）
PROACTIVE_EXCLUDED_MODELS = {
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview"
}

def get_prioritized_gemini_models(user_query: str = "", has_image: bool = False, is_proactive: bool = False) -> list:
    """根據老爸當前的對話指令與多模態情境，動態計算專屬的模型升級排程佇列"""
    q = (user_query or "").lower()
    
    # 🧠 高智商需求識別：找歌/點歌、寫代碼、數學邏輯、哲學推理、複雜指令等，倒序由 3.8 頂配大腦領銜！
    high_iq_keywords = [
        "寫程式", "寫代碼", "python", "程式碼", "找歌", "點歌", "彈琴", "彈一首", "鋼琴", "曲名", "分析",
        "為什麼", "哲學", "算一下", "計算", "思考", "邏輯", "推理", "詳細解說", "找譜", "查歌", "聽歌",
        "搜尋", "查一下", "上網查", "深奧", "解釋", "差別", "冬風", "蕭邦", "李斯特", "貝多芬", "巴哈"
    ]
    is_high_iq = any(k in q for k in high_iq_keywords)
    
    if is_high_iq:
        priority_heads = list(HIGH_IQ_GEMINI_MODELS)
    else:
        # ⚡ 根據老爸指定優先順序精準排列 (1 ➔ 8)
        priority_heads = [
            "gemini-3.1-flash-lite",               # ⚡ 第 1 位：超低延遲、自然口語、秒回首選
            "gemini-3.5-flash-lite",               # 🛡️ 第 2 位：超大額度輕量保底防線
            "gemini-3-flash-preview",              # ⚡ 第 3 位：閃電推理預覽
            "gemini-3.1-pro-preview",              # 🧠 第 4 位：超高智商 Pro 預覽
            "gemini-3.5-flash",                    # 🥈 第 5 位：高智商穩定主力保底
            "gemini-3.6-flash",                    # 👑 第 6 位：最新高智商旗艦主力，視覺與工具調用精準
            "gemini-3.7-flash",                    # 👑 第 7 位：頂配旗艦大腦（深度思考 Thinking 原生開啟，充當腦內心聲）
            "gemini-3.8-flash",                    # 🚀 第 8 位：2026 全新頂配旗艦大腦（深度思考與多模態頂尖推理）
        ]
        
    ordered = []
    for m in priority_heads:
        if m in GEMINI_MODELS and m not in ordered and m not in DEAD_GEMINI_MODELS:
            ordered.append(m)
            
    for m in GEMINI_MODELS:
        if m not in ordered and m not in DEAD_GEMINI_MODELS:
            ordered.append(m)
            
    if is_proactive:
        ordered = [m for m in ordered if m not in PROACTIVE_EXCLUDED_MODELS]
        
    return ordered

def get_pingpong_alternating_index(total_keys: int, step: int) -> int:
    """交替序輪演算法 (頭尾交替向內輪播: 這次 1 -> 下次 29 -> 下次 2 -> 下次 28 -> 下次 3 -> 下次 27 ...)"""
    if total_keys <= 0:
        return 0
    cycle_step = step % total_keys
    if cycle_step % 2 == 0:
        idx = cycle_step // 2
    else:
        idx = total_keys - 1 - (cycle_step // 2)
    return max(0, min(total_keys - 1, idx))

def get_pingpong_ring_indices(total_keys: int, start_step: int) -> list:
    """從當前交替序輪步數開始，產生完整的交替序輪檢查序列 (每個 key 恰好出現一次)"""
    if total_keys <= 0:
        return []
    indices = []
    for i in range(total_keys):
        idx = get_pingpong_alternating_index(total_keys, start_step + i)
        if idx not in indices:
            indices.append(idx)
    for i in range(total_keys):
        if i not in indices:
            indices.append(i)
    return indices

CURRENT_GEMINI_KEY_STEP = 0

def get_available_gemini_channels(limit=1, user_query="", has_image=False, is_proactive=False):
    global CURRENT_GEMINI_KEY_STEP
    available = []
    num_keys = len(GEMINI_KEYS)
    if num_keys == 0: return available
    
    # 🌟 智能任務定向分流：取得階梯排程模型佇列
    target_models = get_prioritized_gemini_models(user_query=user_query, has_image=has_image, is_proactive=is_proactive)
    valid_models = [m for m in target_models if m not in DEAD_GEMINI_MODELS and not is_model_locked(m)]
    if not valid_models:
        valid_models = [m for m in GEMINI_MODELS if m not in DEAD_GEMINI_MODELS]
        
    ring_indices = get_pingpong_ring_indices(num_keys, CURRENT_GEMINI_KEY_STEP)
    
    # 🌟 階梯升級輪派策略：依序為各階模型挑選最優可用金鑰，每次失敗或超時立即升級至下一階更高級模型！
    for m_idx, g_model in enumerate(valid_models):
        short_m = g_model.replace("gemini-", "")
        for idx in ring_indices:
            target_id = f"G{idx}_{short_m}"
            if not is_locked(target_id) and (GEMINI_KEYS[idx], g_model, target_id) not in available:
                available.append((GEMINI_KEYS[idx], g_model, target_id))
                break # 每一階挑選一把最佳金鑰後，優先為下一階模型排入通道！
        if len(available) >= limit:
            return available

    # 若尚未填滿 limit，補充其他未鎖定通道
    if len(available) < limit:
        for g_model in valid_models:
            short_m = g_model.replace("gemini-", "")
            for idx in ring_indices:
                target_id = f"G{idx}_{short_m}"
                if not is_locked(target_id) and (GEMINI_KEYS[idx], g_model, target_id) not in available:
                    available.append((GEMINI_KEYS[idx], g_model, target_id))
                    if len(available) >= limit:
                        return available

    return available

# ────────────────────────────────────────────────────────
# 🖥️ 4. 全域狀態變數、硬體偵測與通知設定 (Global State & Specs)
# ────────────────────────────────────────────────────────
# 💡 功能目的：
#    - 自動偵測主機實體螢幕解析度 (DPI 感知)、CPU、GPU 與記憶體硬體規格。
#    - 維護 7L 的即時運行狀態（思考中、發話中、彈琴中、麥克風監聽）。
#    - 定義多執行緒佇列（語音輸出隊列、彈幕看板隊列、VTS 參數隊列）。

def get_screen_resolution():
    """動態檢測 Windows 實體螢幕解析度 (支援 DPI 感知與多螢幕)"""
    try:
        user32 = ctypes.windll.user32
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
        except Exception:
            try:
                user32.SetProcessDPIAware()
            except Exception:
                pass
        w = user32.GetSystemMetrics(0) # SM_CXSCREEN
        h = user32.GetSystemMetrics(1) # SM_CYSCREEN
        if w > 0 and h > 0:
            return w, h
    except Exception:
        pass
    return 1920, 1080

try:
    cpu_info = platform.processor()
    ram_info = f"{round(psutil.virtual_memory().total / (1024**3))}GB"
    gpu_info = "獨立顯示卡"
    try:
        ps_out = subprocess.check_output(
            ['powershell', '-NoProfile', '-Command', '(Get-CimInstance Win32_VideoController).Name'],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        if ps_out:
            gpu_info = ps_out.splitlines()[0].strip()
    except Exception:
        try:
            gpu_output = subprocess.check_output("wmic path win32_VideoController get name", shell=True, text=True, stderr=subprocess.DEVNULL)
            gpu_info = gpu_output.split('\n')[1].strip()
        except Exception:
            pass
    cur_scr_w, cur_scr_h = get_screen_resolution()
    system_specs = f"螢幕解析度: {cur_scr_w}x{cur_scr_h} / CPU: {cpu_info} / GPU: {gpu_info} / RAM: {ram_info}"
except Exception:
    cur_scr_w, cur_scr_h = get_screen_resolution()
    system_specs = f"螢幕解析度: {cur_scr_w}x{cur_scr_h} / 高階硬體設備"

USER_NAME = "E5alR9"
DEFAULT_USER_TITLE = "老爸"
DEFAULT_CHANNEL_ID = "vts_local_user"

IS_STREAMING = False
current_ai_state = "IDLE"  # IDLE / THINKING / TALKING
last_interaction_time = time.time()
latest_screen_cache = None
SCREEN_TEMPORAL_HISTORY = deque(maxlen=2)  # 🎞️ 螢幕時序動態連續影格緩衝區（保留前 2 幀歷史全景，結合當前 5 視角）
current_voice_task = None
last_spoken_text = ""

vc.target_look_x = 0.0
vc.target_look_y = 0.0
vc.current_look_x = 0.0
vc.current_look_y = 0.0
vc.is_tracking_mouse = False
vc.force_blink_trigger = 0
vc.eye_roll_timer = 0.0
vc.shock_timer = 0.0
vc.wink_timer = 0.0
vc.wink_side = "left"
vc.frown_timer = 0.0
IS_MIC_ENABLED = True

current_mic_volume_str = "[🟢 麥克風就緒]"
current_ai_status_str = "正常運作中"
current_mic_action_str = "待命"
current_model_tag = "🧠 初始化中"
current_screen_context = "目前沒有特別的畫面動態。"
current_system_audio_context = "目前沒有播放特別的聲音。"
current_tiktok_status_str = "[📱 TikTok: 待命中]"
CURRENT_SPEAKING_TARGET = "none"

current_system_notification = ""
notification_expire_time = 0.0
active_timers = set()
vc.vts_lock = asyncio.Lock()
speech_queue = asyncio.Queue()  
pygame.mixer.init()

# 👄 真實音訊波形對嘴中樞 (RMS 包絡提取與物理開閉濾波)
CURRENT_MOUTH_ENVELOPE = []
CURRENT_SPEECH_START_TIME = 0.0
CURRENT_SMOOTH_MOUTH = 0.0

def extract_audio_mouth_envelope(sound_obj, fps=25) -> list:
    """從 MP3/音訊波形中以 25fps (每 40ms) 精確提取口型開合振幅包絡 (0.0~1.0)，包含動態增益與噪聲門限"""
    try:
        import pygame.sndarray
        import numpy as np
        arr = pygame.sndarray.array(sound_obj)
        if arr.size == 0:
            return []
        if arr.ndim > 1:
            arr = np.mean(arr, axis=1)  # 雙聲道轉單聲道
        
        freq = 44100
        frame_len = max(1, int(freq / fps))
        envelope = []
        for i in range(0, len(arr), frame_len):
            chunk = arr[i:i+frame_len].astype(np.float32)
            if len(chunk) > 0:
                rms = float(np.sqrt(np.mean(chunk**2)))
                envelope.append(rms)
        
        if not envelope:
            return []
            
        max_rms = max(envelope)
        if max_rms <= 10.0:
            return [0.0] * len(envelope)
            
        # 噪聲門限 (小於 8% 最大音量直接歸零閉嘴，確保子音、句逗與吸氣自然閉口)
        gate = max_rms * 0.08
        target_span = max_rms * 0.65
        
        norm_env = []
        for r in envelope:
            if r < gate:
                norm_env.append(0.0)
            else:
                val = min(1.0, (r - gate) / target_span)
                norm_env.append(round(val, 3))
        return norm_env
    except Exception:
        return []



def is_system_overloaded():
    try:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        if cpu > 60.0 or mem > 60.0:
            return True
    except Exception:
        pass
    return False

# ────────────────────────────────────────────────────────
# 💾 5. Firebase Firestore 雲端永久記憶與觀眾個人檔案系統 (0 DLL 純 Python 異步 REST 客戶端)
# ────────────────────────────────────────────────────────
# 💡 功能目的：
#    - 提供 0 C/DLL 依賴的純 Python 異步 Firestore REST 客戶端，避免 Windows AppLocker 阻擋 gRPC 二進位檔。
#    - 儲存老爸與 7L 的深度私聊記憶（`channel_history`）、核心人格標籤（`channel_meta`）。
#    - 儲存 TikTok 直播觀眾個人檔案（稱呼、關係、印象、最後見面時間），自動雙向同步至本地 JSON 快取。

db = None
if FIREBASE_CRED_JSON:
    try:
        cred_dict = json.loads(FIREBASE_CRED_JSON)
        db = PureAsyncFirestoreClient(cred_dict)
        realtime_task_mgr.set_db(db)
        print("【💾 系統通知】Firebase Firestore 雲端永久大腦就緒（實時任務中樞已連線雲端）！")
    except Exception as e:
        print(f"【⚠️ 系統警告】Firebase 連線失敗: {e}，將僅使用本地快取。")
else:
    print("【⚠️ 系統警告】未設定 FIREBASE_CRED_JSON，僅使用本地快取模式。")

async def get_user_profile():
    profile = None
    if db is not None:
        try:
            doc = await db.collection("user_memory").document(DEFAULT_CHANNEL_ID).get()
            if doc.exists: profile = doc.to_dict()
        except Exception: pass
        
    if not profile:
        file_path = os.path.join(DATA_DIR, "user_profile_local.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f: profile = json.load(f)
            except Exception: pass
            
    return profile if profile else {"custom_name": DEFAULT_USER_TITLE, "impression": ""}

async def save_user_profile(custom_name=None, impression=None):
    profile = await get_user_profile()
    if custom_name: profile["custom_name"] = custom_name
    if impression: profile["impression"] = impression
    
    if db is not None:
        try:
            await db.collection("user_memory").document(DEFAULT_CHANNEL_ID).set(profile, merge=True)
        except Exception: pass
        
    try:
        with open(os.path.join(DATA_DIR, "user_profile_local.json"), "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
    except Exception: pass

# ── 👥 觀眾身份識別（Firebase viewer_profiles + 本地快取）──────────────────────
async def get_viewer_profile(tiktok_name: str) -> dict:
    """取得 TikTok 觀眾個人資料（Firebase 優先，本地 viewer_profiles_local.json 備援）"""
    default = {"tiktok_name": tiktok_name, "call": None, "relationship": None, "impression": None}
    prof = dict(default)
    if db is not None:
        try:
            doc = await db.collection("viewer_profiles").document(tiktok_name).get()
            if doc.exists:
                prof = {**default, **doc.to_dict()}
        except Exception:
            pass
    local_path = os.path.join(DATA_DIR, "viewer_profiles_local.json")
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                all_profiles = json.load(f)
            if tiktok_name in all_profiles:
                prof = {**default, **all_profiles[tiktok_name]}
        except Exception:
            pass
    # 🛡️ 清理佔位符防護 (避免將「稱呼」、「關係」等字詞當作真名)
    if prof.get("call") in ["稱呼", "名字", "暱稱", "CALL", "none", "null", "None", "Null", ""]:
        prof["call"] = tiktok_name
    return prof

async def save_viewer_profile(tiktok_name: str, call: str = None, relationship: str = None, impression: str = None):
    """儲存 TikTok 觀眾資料到 Firebase viewer_profiles + 本地 viewer_profiles_local.json"""
    profile = await get_viewer_profile(tiktok_name)
    if call:
        clean_c = str(call).strip().strip('"\'')
        if clean_c and clean_c not in ["稱呼", "名字", "暱稱", "CALL", "none", "null", "None", "Null"]:
            profile["call"] = clean_c
    if relationship:
        clean_r = str(relationship).strip().strip('"\'')
        if clean_r and clean_r not in ["關係", "REL", "none", "null", "None", "Null"]:
            profile["relationship"] = clean_r
    if impression:
        clean_i = str(impression).strip().strip('"\'')
        if clean_i and clean_i not in ["印象", "IMP", "none", "null", "None", "Null"]:
            profile["impression"] = clean_i
    profile["last_seen"] = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M")
    if db is not None:
        try:
            await db.collection("viewer_profiles").document(tiktok_name).set(profile, merge=True)
        except Exception:
            pass
    local_path = os.path.join(DATA_DIR, "viewer_profiles_local.json")
    try:
        all_profiles = {}
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                all_profiles = json.load(f)
        all_profiles[tiktok_name] = profile
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(all_profiles, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ── 🧠 7L 雲端大腦提示詞與認知自我演進系統 (100% 雲端 Firestore 動態加載，本機零寫死提示詞) ────────────
DEFAULT_CLOUD_KNOWLEDGE = {
    "persona_core": "",
    "conversation_style": "",
    "memes_and_slang": [],
    "few_shot_examples": [],
    "learned_facts": [],
    "custom_rules": [],
    "banned_phrases": [],
    "proactive_guide": "",
    "streamer_bio": "",
    "last_updated": ""
}

CLOUD_KNOWLEDGE_CACHE = None
CLOUD_KNOWLEDGE_CACHE_TIME = 0.0

async def get_cloud_knowledge() -> dict:
    """取得 7L 雲端大腦認知庫（100% Firestore 雲端優先，本地 cloud_knowledge_local.json 快取備援）"""
    global CLOUD_KNOWLEDGE_CACHE, CLOUD_KNOWLEDGE_CACHE_TIME
    now = time.time()
    if CLOUD_KNOWLEDGE_CACHE is not None and now - CLOUD_KNOWLEDGE_CACHE_TIME < 60.0:
        return CLOUD_KNOWLEDGE_CACHE

    knowledge = None
    if db is not None:
        try:
            doc = await db.collection("cloud_mind_knowledge").document("core_knowledge").get()
            if doc.exists:
                knowledge = doc.to_dict()
        except Exception:
            pass

    if not knowledge:
        local_path = os.path.join(DATA_DIR, "cloud_knowledge_local.json")
        if os.path.exists(local_path):
            try:
                with open(local_path, "r", encoding="utf-8") as f:
                    knowledge = json.load(f)
            except Exception:
                pass

    if not knowledge:
        knowledge = copy.deepcopy(DEFAULT_CLOUD_KNOWLEDGE)

    CLOUD_KNOWLEDGE_CACHE = knowledge
    CLOUD_KNOWLEDGE_CACHE_TIME = now
    return knowledge

async def save_cloud_knowledge(knowledge: dict):
    """保存 7L 雲端大腦認知庫至 Firestore 與本地 JSON 快取"""
    global CLOUD_KNOWLEDGE_CACHE, CLOUD_KNOWLEDGE_CACHE_TIME
    knowledge["last_updated"] = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S")
    CLOUD_KNOWLEDGE_CACHE = knowledge
    CLOUD_KNOWLEDGE_CACHE_TIME = time.time()

    if db is not None:
        try:
            await db.collection("cloud_mind_knowledge").document("core_knowledge").set(knowledge, merge=True)
        except Exception as e:
            log_print(f"⚠️ [雲端記憶寫入異常]: {e}")

    local_path = os.path.join(DATA_DIR, "cloud_knowledge_local.json")
    try:
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

async def update_cloud_prompt_field(field_name: str, content: str, action: str = "set"):
    """7L 自主修改或更新雲端提示詞欄位（persona_core, conversation_style, streamer_bio, proactive_guide 等）"""
    clean_field = str(field_name).strip()
    clean_val = str(content).strip().strip('"\'')
    if not clean_field or not clean_val: return
    kn = await get_cloud_knowledge()
    
    if clean_field in ["persona", "persona_core", "worldview", "人設"]:
        kn["persona_core"] = clean_val
        log_print(f"🧠 [7L 雲端世界觀演進] 7L 自主更新核心自我認知：『{clean_val}』")
    elif clean_field in ["style", "conversation_style", "tone", "對話風格"]:
        kn["conversation_style"] = clean_val
        log_print(f"🧠 [7L 雲端語調演進] 7L 自主更新講話風格：『{clean_val}』")
    elif clean_field in ["streamer", "streamer_bio", "tiktok", "直播人設"]:
        kn["streamer_bio"] = clean_val
        log_print(f"🧠 [7L 雲端主播心智演進] 7L 自主更新直播人設：『{clean_val}』")
    elif clean_field in ["proactive", "proactive_guide", "主動發話"]:
        kn["proactive_guide"] = clean_val
        log_print(f"🧠 [7L 雲端靈感演進] 7L 自主更新主動發話引導：『{clean_val}』")
    elif clean_field in ["memes", "memes_and_slang", "梗"]:
        memes = kn.get("memes_and_slang", [])
        if clean_val not in memes:
            memes.append(clean_val)
            kn["memes_and_slang"] = memes
            log_print(f"🧠 [7L 雲端認知演進] 7L 自主學會新梗：『{clean_val}』")
    elif clean_field in ["facts", "learned_facts", "知識", "事實"]:
        facts = kn.get("learned_facts", [])
        if clean_val not in facts:
            facts.append(clean_val)
            kn["learned_facts"] = facts
            log_print(f"🧠 [7L 雲端認知演進] 7L 自主學會新事實：『{clean_val}』")
    elif clean_field in ["rules", "custom_rules", "規範", "原則"]:
        rules = kn.get("custom_rules", [])
        if clean_val not in rules:
            rules.append(clean_val)
            kn["custom_rules"] = rules
            log_print(f"🧠 [7L 雲端心智更新] 7L 自主寫入新規範：『{clean_val}』")
    elif clean_field in ["banned", "banned_phrases", "禁用語"]:
        banned = kn.get("banned_phrases", [])
        if clean_val not in banned:
            banned.append(clean_val)
            kn["banned_phrases"] = banned
            log_print(f"🧠 [7L 雲端禁用語更新] 7L 自主加入禁忌詞：『{clean_val}』")
    else:
        kn[clean_field] = clean_val
        log_print(f"🧠 [7L 雲端自定義更新] 7L 自主更新欄位 {clean_field}：『{clean_val}』")
        
    await save_cloud_knowledge(kn)

async def add_few_shot_example(scenario: str, user_input: str, thought: str, reply: str):
    """7L 自主新增神回覆範例到雲端示範庫"""
    kn = await get_cloud_knowledge()
    examples = kn.get("few_shot_examples", [])
    new_ex = {
        "scenario": str(scenario).strip(),
        "input": str(user_input).strip(),
        "thought": str(thought).strip(),
        "reply": str(reply).strip()
    }
    examples.append(new_ex)
    kn["few_shot_examples"] = examples
    await save_cloud_knowledge(kn)
    log_print(f"🎯 [7L 雲端示範演進] 7L 自主新增神回覆案例：『{scenario} ➔ {reply}』")

async def learn_new_meme(meme_desc: str):
    """7L 自主學習並記憶新梗到雲端知識庫"""
    await update_cloud_prompt_field("memes_and_slang", meme_desc)

async def learn_new_fact(fact_desc: str):
    """7L 自主學習並記憶新事實/知識到雲端知識庫"""
    await update_cloud_prompt_field("learned_facts", fact_desc)

async def update_custom_rule(rule_desc: str):
    """7L 自主更新或設定心智原則"""
    await update_cloud_prompt_field("custom_rules", rule_desc)

async def fetch_from_long_term_memory(channel_id, current_user_msg=""):
    """讀取對話記憶：全面轉接至全集中記憶中樞 UNIFIED_LIVE_MEMORY，徹底淘汰舊版碎片化 channel_history"""
    global UNIFIED_LIVE_MEMORY
    if str(channel_id) in [str(DEFAULT_CHANNEL_ID), "tiktok_live_stream", "stream"]:
        history = []
        for it in list(UNIFIED_LIVE_MEMORY)[-40:]:
            r = it.get("role", "user")
            spk = it.get("speaker", "")
            cnt = it.get("content", "")
            if r == "system":
                continue
            if r == "assistant" or spk == "7L":
                history.append({"role": "assistant", "content": cnt})
            else:
                prefix = f"【{spk}】" if not cnt.startswith("【") else ""
                history.append({"role": "user", "content": f"{prefix}{cnt}"})
        return history

    # 對於其他通道 (如 Discord 機器人子頻道) 維持相容
    history = []
    if db is not None:
        try:
            doc_ref = db.collection("channel_history").document(str(channel_id))
            doc = await doc_ref.get()
            if doc.exists:
                history.extend(doc.to_dict().get("history", []))
        except Exception: pass
    if not history:
        file_path = os.path.join(DATA_DIR, f"memory_{channel_id}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f: history = json.load(f)
            except Exception: pass
    return history

def extract_text_from_content(content):
    if isinstance(content, str): return content
    if isinstance(content, list): return " ".join([p.get("text", "") for p in content if p.get("type") == "text"])
    return ""

async def get_embedding_vector(text):
    """呼叫 Gemini Embedding 2 將文字轉換為潛意識數字陣列"""
    if not GEMINI_KEYS: return None
    try:
        g_key = random.choice(GEMINI_KEYS)
        temp_google_client = genai.Client(api_key=g_key)
        response = await asyncio.wait_for(
            temp_google_client.aio.models.embed_content(
                model="gemini-embedding-2", 
                contents=text
            ),
            timeout=5.0
        )
        return response.embeddings[0].values
    except Exception:
        try:
            temp_google_client = genai.Client(api_key=random.choice(GEMINI_KEYS))
            response = await asyncio.wait_for(
                temp_google_client.aio.models.embed_content(
                    model="gemini-embedding-001", 
                    contents=text
                ),
                timeout=5.0
            )
            return response.embeddings[0].values
        except Exception as e:
            print(f"\n⚠️ [潛意識轉換失敗]: {e}")
            return None

async def update_daily_diary(channel_id, recent_chat):
    tz = ZoneInfo("Asia/Taipei")
    today_str = datetime.now(tz).strftime("%Y-%m-%d")
    chat_text = "\n".join([f"{msg['role']}: {extract_text_from_content(msg['content'])}" for msg in recent_chat if extract_text_from_content(msg['content']).strip()])
    
    if len(chat_text.strip()) < 40: return
    
    diary_dir = "diaries"
    os.makedirs(diary_dir, exist_ok=True)
    diary_file_path = os.path.join(diary_dir, f"diary_{today_str}.json")

    existing_summary = ""
    if db is not None:
        try:
            doc = await db.collection("daily_diary").document(today_str).get()
            if doc.exists: existing_summary = doc.to_dict().get("summary", "")
        except Exception: pass
    elif os.path.exists(diary_file_path):
        try:
            with open(diary_file_path, "r", encoding="utf-8") as f:
                existing_summary = json.load(f).get("summary", "")
        except Exception: pass
        
    diary_prompt = (
        f"【後台任務：每日核心日記整合與高強度去重】\n"
        f"妳是 7L 的日記記憶中樞。請將『舊日記摘要』與『新對話』融合成一份完全去重、精簡濃縮後的今日日記。\n\n"
        f"⚠️ 核心守則：\n"
        f"1. 刪除重複部分，保留重點。\n"
        f"2. 總句數嚴格限制在 3 句以內。\n"
        f"3. 絕對不要有任何前言或結尾，直接輸出整合後的日記內容。\n\n"
        f"📖 [舊日記摘要]：\n{existing_summary if existing_summary else '(無)'}\n\n"
        f"💬 [新對話紀錄]：\n{chat_text}\n"
    )
    
    messages = [{"role": "user", "content": diary_prompt}]
    updated_summary = await fetch_ai_response(messages, is_proactive=True)
    
    if updated_summary and "沉默" not in updated_summary:
        log_print("🧠 [潛意識系統] 正在將今日記憶編碼上傳雲端...")
        vector_data = await get_embedding_vector(updated_summary.strip())
        
        diary_payload = {
            "summary": updated_summary.strip(), 
            "date": today_str
        }
        if vector_data:
            diary_payload["embedding_vector"] = vector_data
            
        if db is not None:
            try:
                await db.collection("daily_diary").document(today_str).set(diary_payload, merge=True)
            except Exception: pass
            
        try:
            with open(diary_file_path, "w", encoding="utf-8") as f:
                json.dump(diary_payload, f, ensure_ascii=False, indent=2)
        except Exception: pass

async def save_to_long_term_memory(channel_id, history):
    # 若為老爸主通道或 TikTok 直播通道，已由 append_to_unified_memory 全局統一寫入，不再重寫舊版 channel_history / channel_meta
    if str(channel_id) in [str(DEFAULT_CHANNEL_ID), "tiktok_live_stream", "stream"]:
        return

    raw_history_limit = 500  # 🧠 深度上下文記憶容量擴增至 500 句
    clean_history = [msg for msg in history if not (msg.get("role") == "system" and ("【" in msg.get("content", "")))]
    if len(clean_history) > raw_history_limit: clean_history = clean_history[-raw_history_limit:]
        
    if db is not None:
        try:
            await db.collection("channel_history").document(str(channel_id)).set({"history": clean_history, "last_updated": time.time()}, merge=True)
        except Exception: pass
    
    file_path = os.path.join(DATA_DIR, f"memory_{channel_id}.json")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(clean_history, f, ensure_ascii=False, indent=2)
    except Exception: pass

# ────────────────────────────────────────────────────────
# 🎭 6. Live2D / VTube Studio 表情與姿態控制 & 雙軌空間走位系統 (Spatial Movement)
# ────────────────────────────────────────────────────────
class RobustVTSClient:
    """🌟 高效能非同步 VTube Studio WebSocket 通訊引擎（支援無阻塞極速參數注入與 RequestID 精準匹配）"""
    def __init__(self, plugin_info=None, port=8001):
        self.plugin_info = plugin_info or {
            "plugin_name": "7L_AI_VTuber",
            "developer": "e5_Studio",
            "authentication_token_path": "./vts_token.txt"
        }
        self.token_file = self.plugin_info.get("authentication_token_path", "./vts_token.txt")
        self.port = port
        self.uri = f"ws://127.0.0.1:{self.port}"
        self.ws = None
        self.authentic_token = None
        self.pending_requests = {}
        self.reader_task = None
        self.req_counter = 0
        self.is_authenticated = False

    def is_connected(self):
        if self.ws is None:
            return False
        if hasattr(self.ws, 'closed'):
            return not self.ws.closed
        return getattr(self.ws, 'close_code', None) is None

    async def connect(self, retries=5, retry_delay=2.0):
        for attempt in range(1, retries + 1):
            try:
                if self.is_connected():
                    try: await self.ws.close()
                    except Exception: pass
                self.ws = await websockets.connect(
                    self.uri, 
                    max_size=10*1024*1024,
                    open_timeout=10.0,
                    ping_interval=20.0
                )
                if self.reader_task and not self.reader_task.done():
                    self.reader_task.cancel()
                self.reader_task = asyncio.create_task(self._socket_reader())
                return True
            except Exception as e:
                if attempt < retries:
                    await asyncio.sleep(retry_delay)
                else:
                    raise ConnectionError(f"Cannot connect to VTube Studio at {self.uri}: {e}")

    async def _socket_reader(self):
        try:
            async for raw_msg in self.ws:
                try:
                    data = json.loads(raw_msg)
                    req_id = data.get("requestID")
                    if req_id and req_id in self.pending_requests:
                        future = self.pending_requests.pop(req_id)
                        if not future.done():
                            future.set_result(data)
                except Exception:
                    pass
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def read_token(self):
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "r", encoding="utf-8") as f:
                    self.authentic_token = f.read().strip()
            except Exception:
                self.authentic_token = None
        return self.authentic_token

    async def write_token(self):
        if self.authentic_token:
            try:
                with open(self.token_file, "w", encoding="utf-8") as f:
                    f.write(self.authentic_token)
            except Exception:
                pass

    async def request_authenticate_token(self):
        resp = await self.request({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "TokenReq",
            "messageType": "AuthenticationTokenRequest",
            "data": {
                "pluginName": self.plugin_info.get("plugin_name", "7L_AI_VTuber"),
                "pluginDeveloper": self.plugin_info.get("developer", "e5_Studio")
            }
        })
        token = resp.get("data", {}).get("authenticationToken")
        if token:
            self.authentic_token = token
        return token

    async def request_authenticate(self):
        if not self.authentic_token:
            await self.read_token()
        if not self.authentic_token:
            await self.request_authenticate_token()
            await self.write_token()

        resp = await self.request({
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "AuthReq",
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": self.plugin_info.get("plugin_name", "7L_AI_VTuber"),
                "pluginDeveloper": self.plugin_info.get("developer", "e5_Studio"),
                "authenticationToken": self.authentic_token
            }
        })
        self.is_authenticated = resp.get("data", {}).get("authenticated", False)
        return resp

    async def request(self, req_dict: dict, timeout: float = 2.0) -> dict:
        if not self.is_connected():
            await self.connect()

        if "requestID" not in req_dict:
            self.req_counter += 1
            req_dict["requestID"] = f"Req_{self.req_counter}_{int(time.time()*1000)}"
        req_id = req_dict["requestID"]

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_requests[req_id] = future

        await self.ws.send(json.dumps(req_dict))
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self.pending_requests.pop(req_id, None)
            return {"errorID": 408, "message": f"Request {req_id} timed out"}

    async def inject_parameters(self, param_values: list, face_found: bool = True, mode: str = "set"):
        """極速非同步注入參數，不阻塞接收佇列"""
        if not self.is_connected():
            return
        formatted_values = []
        for p in param_values:
            formatted_values.append({
                "id": p["id"],
                "value": float(p["value"]),
                "weight": float(p.get("weight", 1.0))
            })
        msg = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": "StreamInject",
            "messageType": "InjectParameterDataRequest",
            "data": {
                "faceFound": face_found,
                "mode": mode,
                "parameterValues": formatted_values
            }
        }
        try:
            await self.ws.send(json.dumps(msg))
        except Exception:
            pass

    async def close(self):
        if self.reader_task:
            self.reader_task.cancel()
        if self.is_connected():
            try: await self.ws.close()
            except Exception: pass

vc.GLOBAL_VTS = None
vc.MY_CONTROLLED_EXPS = ["黑脸.exp3.json", "爱心.exp3.json", "星星眼.exp3.json", "红脸.exp3.json"]
vc.CURRENT_ACTIVE_EXP = None
EXPRESSION_HOLD_SECONDS = 3.5  # 🎭 說完話後表情持續保留的秒數（保持自然情緒餘韻）

VTS_EXPRESSION_MAP = {
    # 愛心 / 笑意
    "愛心": "爱心.exp3.json",      
    "爱心": "爱心.exp3.json",      
    "heart": "爱心.exp3.json",
    "love": "爱心.exp3.json",
    "喜歡": "爱心.exp3.json",
    "喜欢": "爱心.exp3.json",
    "開心": "爱心.exp3.json",
    "开心": "爱心.exp3.json",
    "happy": "爱心.exp3.json",
    "笑": "爱心.exp3.json",
    "微笑": "爱心.exp3.json",
    "大笑": "星星眼.exp3.json",

    # 星星眼
    "星星": "星星眼.exp3.json",    
    "星星眼": "星星眼.exp3.json",
    "star": "星星眼.exp3.json",
    "sparkle": "星星眼.exp3.json",
    "崇拜": "星星眼.exp3.json",
    "期待": "星星眼.exp3.json",
    "亮晶晶": "星星眼.exp3.json",

    # 臉紅 / 紅臉
    "臉紅": "红脸.exp3.json",      
    "臉红": "红脸.exp3.json",
    "红脸": "红脸.exp3.json",
    "紅臉": "红脸.exp3.json",
    "shy": "红脸.exp3.json",
    "blush": "红脸.exp3.json",
    "傲嬌": "红脸.exp3.json",
    "傲娇": "红脸.exp3.json",
    "害羞": "红脸.exp3.json",
    "尷尬": "红脸.exp3.json",
    "尴尬": "红脸.exp3.json",

    # 生氣 / 黑臉 / 翻白眼 / 傲慢
    "生氣": "黑脸.exp3.json",
    "生气": "黑脸.exp3.json",
    "黑臉": "黑脸.exp3.json",
    "黑脸": "黑脸.exp3.json",
    "哼": "黑脸.exp3.json",
    "傲慢": "黑脸.exp3.json",
    "angry": "黑脸.exp3.json",
    "不爽": "黑脸.exp3.json",
    "憤怒": "黑脸.exp3.json",
    "愤怒": "黑脸.exp3.json",
    "陰沉": "黑脸.exp3.json",
    "阴沉": "黑脸.exp3.json",
    "黑化": "黑脸.exp3.json",
    "難過": "黑脸.exp3.json",
    "难过": "黑脸.exp3.json",
    "sad": "黑脸.exp3.json",
    "翻白眼": "黑脸.exp3.json",
    "白眼": "黑脸.exp3.json",
    "無語": "黑脸.exp3.json",
    "无语": "黑脸.exp3.json",
    "鄙視": "黑脸.exp3.json",
    "鄙视": "黑脸.exp3.json"
}

vc.CURRENT_SPATIAL_LOCATION = "center"
IS_AUTO_WANDER_ENABLED = True
LAST_WANDER_TIME = time.time()

BASE_VTS_MODEL_X = 0.65
BASE_VTS_MODEL_Y = -1.28
BASE_VTS_MODEL_SIZE = -54.8
CURRENT_VTS_MODEL_X = None
CURRENT_VTS_MODEL_Y = None
CURRENT_VTS_MODEL_SIZE = None

async def fetch_vts_base_model_pos(vts=None):
    """主動從 VTube Studio 讀取並記錄老爸自訂之模型大小與座標基準（保證半身構圖與比例永不失真）"""
    global BASE_VTS_MODEL_X, BASE_VTS_MODEL_Y, BASE_VTS_MODEL_SIZE, CURRENT_VTS_MODEL_X, CURRENT_VTS_MODEL_Y, CURRENT_VTS_MODEL_SIZE, vc.GLOBAL_VTS
    target_vts = vts or vc.GLOBAL_VTS
    if not target_vts:
        return
    try:
        async with vc.vts_lock:
            resp = await asyncio.wait_for(target_vts.request({
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "GetModelInfoReq",
                "messageType": "CurrentModelRequest"
            }), timeout=1.5)
        pos = resp.get("data", {}).get("modelPosition", {})
        if pos and "size" in pos:
            x = float(pos.get("positionX", 0.65))
            y = float(pos.get("positionY", -1.28))
            sz = float(pos.get("size", -54.8))
            BASE_VTS_MODEL_Y = y
            BASE_VTS_MODEL_SIZE = sz
            if x > 0.1:
                BASE_VTS_MODEL_X = x
            CURRENT_VTS_MODEL_X, CURRENT_VTS_MODEL_Y, CURRENT_VTS_MODEL_SIZE = x, y, sz
            log_print(f"📐 [VTS 模型記憶] 成功記錄老爸自訂基準大小: {sz:.1f}, 基準座標: ({x:.2f}, {y:.2f})")
    except Exception:
        pass

def parse_relative_spatial_offsets(clean_pos: str):
    """從走位字串中解析相對微調量 (dx, dy, d_sz)，支援如 '往右+10', '往左15', '往上+5', '往下-10', '放大+10', '縮小-5', '往右邊', '再過去一點'"""
    if not clean_pos:
        return None, None, None
        
    p = clean_pos.lower().strip()
    
    # 0. 排除純命名預設站位（避免覆蓋預設坐標）
    pure_named_presets = [
        "正中間", "置中", "中間", "center", 
        "鋼琴", "鋼琴旁", "鋼琴旁邊", "鋼琴前", "彈琴", "彈鋼琴", 
        "躲角落", "角落", "hide", 
        "原位", "回到原位", "原本位置", "復原", "home", "reset"
    ]
    if any(p == k for k in pure_named_presets):
        return None, None, None
    if re.match(r'^(?:去|到|站|在|移到|走至)?(?:正中間|中間|鋼琴旁|角落|原位|原本位置)$', p):
        return None, None, None

    dx, dy, d_sz = 0.0, 0.0, 0.0
    has_match = False
    
    # 1. 支援直接參數語法: dx=10, dy=-5, size=+5
    m_dx = re.search(r'dx\s*[:=]\s*([+-]?\d+(?:\.\d+)?)', p)
    if m_dx:
        v = float(m_dx.group(1))
        dx += (v * 0.02 if abs(v) > 2 else v)
        has_match = True
        
    m_dy = re.search(r'dy\s*[:=]\s*([+-]?\d+(?:\.\d+)?)', p)
    if m_dy:
        v = float(m_dy.group(1))
        dy += (v * 0.02 if abs(v) > 2 else v)
        has_match = True

    m_dsz = re.search(r'(?:size|sz|d_?size)\s*[:=]\s*([+-]?\d+(?:\.\d+)?)', p)
    if m_dsz:
        v = float(m_dsz.group(1))
        d_sz += (v * 1.0 if abs(v) <= 50 else v * 0.5)
        has_match = True

    is_large_step = any(k in p for k in ["多一點", "多一些", "大一點", "一大步", "大幅", "再過去", "更過去", "多點", "再過去一點"])

    # 2. X 軸中文相對微調 (右移 / 往右 / 左移 / 往左)
    m_r = re.search(r'(?:往右|向右|右移|再右|右邊一點|往右邊|右側一點|再過去右邊|過去右邊|右邊多一點|再過去一點|過去一點)\s*(?:走|移|動|去)?\s*([+-]?\d+(?:\.\d+)?)?', p)
    if m_r and not m_dx:
        raw_num = m_r.group(1)
        if raw_num is not None:
            num = float(raw_num)
            dx += (num * 0.02 if abs(num) > 2 else num * 0.20 if abs(num) > 0 else (0.35 if is_large_step else 0.22))
        else:
            dx += (0.35 if is_large_step else 0.22)
        has_match = True

    m_l = re.search(r'(?:往左|向左|左移|再左|左邊一點|往左邊|左側一點|再過去左邊|過去左邊|左邊多一點)\s*(?:走|移|動|去)?\s*([+-]?\d+(?:\.\d+)?)?', p)
    if m_l and not m_dx:
        raw_num = m_l.group(1)
        if raw_num is not None:
            num = abs(float(raw_num))
            dx -= (num * 0.02 if num > 2 else num * 0.20 if num > 0 else (0.35 if is_large_step else 0.22))
        else:
            dx -= (0.35 if is_large_step else 0.22)
        has_match = True

    # 3. Y 軸中文相對微調 (上移 / 往上 / 下移 / 往下)
    m_u = re.search(r'(?:往上|向上|上移|再上|上邊一點|往上邊|上方一點)\s*(?:走|移|動|去)?\s*([+-]?\d+(?:\.\d+)?)?', p)
    if m_u and not m_dy:
        raw_num = m_u.group(1)
        if raw_num is not None:
            num = float(raw_num)
            dy += (num * 0.02 if abs(num) > 2 else num * 0.15 if abs(num) > 0 else (0.25 if is_large_step else 0.15))
        else:
            dy += (0.25 if is_large_step else 0.15)
        has_match = True

    m_d = re.search(r'(?:往下|向下|下移|再下|下邊一點|往下邊|下方一點)\s*(?:走|移|動|去)?\s*([+-]?\d+(?:\.\d+)?)?', p)
    if m_d and not m_dy:
        raw_num = m_d.group(1)
        if raw_num is not None:
            num = abs(float(raw_num))
            dy -= (num * 0.02 if num > 2 else num * 0.15 if num > 0 else (0.25 if is_large_step else 0.15))
        else:
            dy -= (0.25 if is_large_step else 0.15)
        has_match = True

    # 4. 尺寸縮放微調 (放大 / 縮小 / 變大 / 變小)
    m_big = re.search(r'(?:放大|變大|变大|大一點|大一点|靠近|貼近|贴近|zoom\s*in)\s*([+-]?\d+(?:\.\d+)?)?', p)
    if m_big and not m_dsz:
        raw_num = m_big.group(1)
        if raw_num is not None:
            num = float(raw_num)
            d_sz += (num * 1.0 if abs(num) > 0 else (16.0 if is_large_step else 10.0))
        else:
            d_sz += (16.0 if is_large_step else 10.0)
        has_match = True

    m_small = re.search(r'(?:縮小|缩小|變小|变小|小一點|小一点|遠離|远离|zoom\s*out)\s*([+-]?\d+(?:\.\d+)?)?', p)
    if m_small and not m_dsz:
        raw_num = m_small.group(1)
        if raw_num is not None:
            num = abs(float(raw_num))
            d_sz -= (num * 1.0 if num > 0 else (16.0 if is_large_step else 10.0))
        else:
            d_sz -= (16.0 if is_large_step else 10.0)
        has_match = True

    if has_match:
        return dx, dy, d_sz
    return None, None, None

async def move_vts_spatial(
    target_pos=None, 
    target_x=None, target_y=None, 
    delta_x=None, delta_y=None, 
    target_size=None, delta_size=None, scale_factor=None, 
    duration=2.0,
    *args, **kwargs
):
    """【VTS Live2D 模型平滑走位與縮放控制器】透過 WebSocket 官方 API 驅動 7L 在 VTS 畫布內平滑走位、相對微調與縮放"""
    global BASE_VTS_MODEL_X, BASE_VTS_MODEL_Y, BASE_VTS_MODEL_SIZE, CURRENT_VTS_MODEL_X, CURRENT_VTS_MODEL_Y, CURRENT_VTS_MODEL_SIZE, vc.GLOBAL_VTS
    target_vts = vc.GLOBAL_VTS
    if not target_vts:
        return False
        
    if BASE_VTS_MODEL_SIZE is None or CURRENT_VTS_MODEL_SIZE is None:
        await fetch_vts_base_model_pos(target_vts)
        
    base_x = BASE_VTS_MODEL_X if BASE_VTS_MODEL_X is not None else 0.65
    base_y = BASE_VTS_MODEL_Y if BASE_VTS_MODEL_Y is not None else -1.28
    base_sz = BASE_VTS_MODEL_SIZE if BASE_VTS_MODEL_SIZE is not None else -54.8
    
    cur_x = CURRENT_VTS_MODEL_X if CURRENT_VTS_MODEL_X is not None else base_x
    cur_y = CURRENT_VTS_MODEL_Y if CURRENT_VTS_MODEL_Y is not None else base_y
    cur_sz = CURRENT_VTS_MODEL_SIZE if CURRENT_VTS_MODEL_SIZE is not None else base_sz

    clean_pos = str(target_pos or "").strip().lower()
    
    # 1. 檢查是否為重置/記憶指令
    if any(k == clean_pos or k in clean_pos for k in ["記住位置", "記住大小", "記住現在大小", "記住現在位置", "記錄位置", "記錄大小", "記住模型位置", "記住當前位置", "記住基準", "記錄基準", "save_pos", "save_position"]):
        await fetch_vts_base_model_pos(target_vts)
        return True
    elif clean_pos in ["復原", "原位", "原本位置", "回到原位", "home", "reset", "原本大小", "重設大小", "恢復大小", "再回去", "回去吧"]:
        dest_x = base_x
        dest_y = base_y
        dest_sz = base_sz
    elif scale_factor is not None and float(scale_factor) > 0:
        factor = float(scale_factor)
        dest_sz = base_sz + (factor - 1.0) * 35.0
        dest_x = cur_x
        dest_y = cur_y
    else:
        # 2. 解析相對微調量 (支援參數傳入 delta_x/delta_y/delta_size 與字串解析如 "往右+10", "往左15")
        parsed_dx, parsed_dy, parsed_dsz = parse_relative_spatial_offsets(clean_pos)
        
        calc_dx = 0.0
        calc_dy = 0.0
        calc_dsz = 0.0
        
        if delta_x is not None:
            calc_dx += float(delta_x) * 0.008 if abs(delta_x) > 2 else float(delta_x)
        elif parsed_dx is not None:
            calc_dx += parsed_dx

        if delta_y is not None:
            calc_dy += float(delta_y) * 0.008 if abs(delta_y) > 2 else float(delta_y)
        elif parsed_dy is not None:
            calc_dy += parsed_dy

        if delta_size is not None:
            calc_dsz += float(delta_size)
        elif parsed_dsz is not None:
            calc_dsz += parsed_dsz

        if target_size is not None:
            dest_sz = float(target_size)
        elif calc_dsz != 0.0:
            dest_sz = cur_sz + calc_dsz
        else:
            dest_sz = cur_sz

        if calc_dx != 0.0 or calc_dy != 0.0:
            dest_x = cur_x + calc_dx
            dest_y = cur_y + calc_dy
        else:
            # 3. 命名預設站位 (Named Spatial Presets)
            if any(k in clean_pos for k in ["鋼琴", "鋼琴旁", "鋼琴旁邊", "鋼琴前", "彈琴", "彈鋼琴"]):
                # 🎹 鋼琴專屬站位：直接原地坐下彈奏，保持當前 X 軸位置，不左右跑動
                dest_x = cur_x
                dest_y = base_y + 0.06
                dest_sz = base_sz
            elif any(k in clean_pos for k in ["靠近", "貼近", "大模型", "大一點"]):
                dest_x = cur_x
                dest_y = base_y + 0.12
                dest_sz = cur_sz + 12.0
            elif any(k in clean_pos for k in ["遠離", "小模型", "小一點"]):
                dest_x = cur_x
                dest_y = base_y - 0.12
                dest_sz = cur_sz - 12.0
            elif any(k in clean_pos for k in ["躲角落", "角落", "hide"]):
                dest_x = 0.85
                dest_y = base_y - 0.15
                dest_sz = base_sz - 12.0
            elif any(k in clean_pos for k in ["center", "中間", "正中間", "置中", "過來中間"]):
                dest_x = 0.0 + random.uniform(-0.03, 0.03)
                dest_y = base_y + random.uniform(-0.03, 0.03)
                dest_sz = base_sz
            elif any(k in clean_pos for k in ["左邊", "左側", "left", "去左邊", "左下", "左下角", "左上", "左上角"]):
                dest_x = -0.65 + random.uniform(-0.04, 0.04)
                dest_y = base_y + random.uniform(-0.03, 0.03)
            elif any(k in clean_pos for k in ["右邊", "右側", "right", "去右邊", "右下", "右下角", "右上", "右上角"]):
                dest_x = 0.65 + random.uniform(-0.04, 0.04)
                dest_y = base_y + random.uniform(-0.03, 0.03)
            elif clean_pos in ["原位", "回到原位", "原本位置", "復原"]:
                dest_x = base_x
                dest_y = base_y
                dest_sz = base_sz
            elif clean_pos and clean_pos != "random":
                dest_x = cur_x
                dest_y = cur_y
            else:
                # 🌟 7L 自由漫遊走位
                dest_x = random.choice([-0.65, -0.30, 0.0, 0.35, 0.65]) + random.uniform(-0.05, 0.05)
                dest_y = base_y + random.uniform(-0.06, 0.06)
                
    dest_sz = max(-95.0, min(80.0, dest_sz))
    dest_x = max(-1.8, min(1.8, dest_x))
    dest_y = max(-3.0, min(1.5, dest_y))
    
    # 若已經在目標原位，防抖略過
    if clean_pos in ["原位", "回到原位", "原本位置", "復原"] and abs(dest_x - cur_x) < 0.03 and abs(dest_y - cur_y) < 0.03 and abs(dest_sz - cur_sz) < 1.5:
        return True

    req_data = {
        "timeInSeconds": float(duration),
        "valuesAreRelativeToModel": False,
        "positionX": float(dest_x),
        "positionY": float(dest_y),
        "size": float(dest_sz),
        "rotation": 0.0
    }
    
    async with vc.vts_lock:
        try:
            await asyncio.wait_for(target_vts.request({
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "MoveModelReq",
                "messageType": "MoveModelRequest",
                "data": req_data
            }), timeout=1.5)
            CURRENT_VTS_MODEL_X = dest_x
            CURRENT_VTS_MODEL_Y = dest_y
            CURRENT_VTS_MODEL_SIZE = dest_sz
            return True
        except Exception:
            return False

async def apply_spatial_position(
    position_name: str = "random", 
    target_x: float = None, target_y: float = None, 
    delta_x: float = None, delta_y: float = None,
    target_size: float = None, delta_size: float = None,
    target_w: int = None, target_h: int = None,
    delta_w: int = None, delta_h: int = None,
    scale_factor: float = None,
    duration: float = 2.0,
    *args, **kwargs
) -> str:
    """統一 Live2D 模型走位與縮放控制器（支援絕對位置、預設位置與全向相對數值微調）"""
    global vc.CURRENT_SPATIAL_LOCATION
    clean_pos = str(position_name).strip()
    
    d_size = delta_size
    if d_size is None and (delta_w is not None or delta_h is not None):
        d_size = ((delta_w or 0) + (delta_h or 0)) / 25.0
        
    await move_vts_spatial(
        target_pos=clean_pos,
        target_x=target_x, target_y=target_y,
        delta_x=delta_x, delta_y=delta_y,
        target_size=target_size,
        delta_size=d_size,
        scale_factor=scale_factor,
        duration=duration
    )
    vc.CURRENT_SPATIAL_LOCATION = clean_pos
    log_print(f"🚀 [模型走位] 7L 模型平滑位移至: 「{clean_pos}」 (dx={delta_x}, dy={delta_y}, d_sz={d_size})")
    return f"已成功平滑移動模型至「{clean_pos}」！"

async def set_vts_expression(vts, exp_tag):
    global vc.CURRENT_ACTIVE_EXP, vc.shock_timer, vc.wink_timer, vc.wink_side, vc.frown_timer
    try:
        clean_tag = str(exp_tag).strip().replace("[", "").replace("]", "").replace("EXPRESSION:", "").strip().lower()
        if clean_tag in ["_reset_", "_reset", "預設", "重置", "關閉", "正常", "恢復", "無", "取消", "reset", "default", "none", "close", "off", "0"]:
            vc.CURRENT_ACTIVE_EXP = None
            vc.shock_timer = 0.0
            vc.wink_timer = 0.0
            vc.frown_timer = 0.0
            log_print("✨ [Live2D 表情] 表情已重置為預設自然狀態")
            async with vc.vts_lock:
                for exp_file in vc.MY_CONTROLLED_EXPS:
                    try:
                        await asyncio.wait_for(vts.request({
                            "apiName": "VTubeStudioPublicAPI", "apiVersion": "1.0", "requestID": "ResetExp",
                            "messageType": "ExpressionActivationRequest", "data": {"expressionFile": exp_file, "active": False}
                        }), timeout=0.3)
                    except Exception: pass
            return

        # 1. 物理動力學表情 (Wink, Shock, Frown)
        if any(k in clean_tag for k in ["wink", "眨眼", "單眼", "眨單眼", "单眼", "眨单眼"]):
            vc.wink_timer = time.time() + 0.55
            vc.wink_side = random.choice(["left", "right"])
            log_print(f"😉 [Live2D 動作] 觸發 Wink 單邊眨一下眼放電 ({vc.wink_side})")
            return
        elif any(k in clean_tag for k in ["shock", "震驚", "震惊", "瞳孔", "縮小", "缩小", "嚇到", "吓到", "恐懼", "害怕"]):
            vc.shock_timer = time.time() + 4.0
            log_print("😱 [Live2D 動作] 觸發震驚縮瞳與物理顫抖")
            return
        elif any(k in clean_tag for k in ["frown", "皺眉", "皱眉", "八字眉", "困擾", "困扰", "委屈"]):
            vc.frown_timer = time.time() + 4.0
            log_print("🥺 [Live2D 動作] 觸發傲嬌八字皺眉/委屈表情")
            return

        # 2. 映射 exp3 檔案表情
        target_filename = VTS_EXPRESSION_MAP.get(clean_tag)
        if not target_filename:
            for k, v in VTS_EXPRESSION_MAP.items():
                if k in clean_tag or clean_tag in k:
                    target_filename = v
                    break
        if not target_filename:
            log_print(f"⚠️ [Live2D 表情] 未知表情標籤: 「{clean_tag}」，已忽略。")
            return

        vc.CURRENT_ACTIVE_EXP = target_filename  
        log_print(f"✨ [Live2D 表情] 成功啟動表情檔: 《{target_filename}》 (標籤: {clean_tag})")
        async with vc.vts_lock:
            for exp_file in vc.MY_CONTROLLED_EXPS:
                if exp_file != target_filename:
                    try:
                        await asyncio.wait_for(vts.request({
                            "apiName": "VTubeStudioPublicAPI", "apiVersion": "1.0", "requestID": "DeactivateExp",
                            "messageType": "ExpressionActivationRequest", "data": {"expressionFile": exp_file, "active": False}
                        }), timeout=0.3)
                    except Exception: pass

            try:
                await asyncio.wait_for(vts.request({
                    "apiName": "VTubeStudioPublicAPI", "apiVersion": "1.0", "requestID": "ActivateExpression",
                    "messageType": "ExpressionActivationRequest", "data": {"expressionFile": target_filename, "active": True}
                }), timeout=0.5)
            except Exception: pass
    except Exception as e:
        log_print(f"\n❌ [表情系統] 發生錯誤: {e}")

# ────────────────────────────────────────────────────────
# 🎮 7. 7L 本機遊樂場沙盒 (7L_Playground)
# ────────────────────────────────────────────────────────
PLAYGROUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "7L_Playground")
os.makedirs(PLAYGROUND_DIR, exist_ok=True)

# 🛡️ 敏感/高危指令安全黑名單過濾
DANGEROUS_CODE_PATTERNS = [
    r"\bos\.remove\b", r"\bos\.unlink\b", r"\bos\.rmdir\b", r"\bos\.system\b",
    r"\bshutil\.rmtree\b", r"\bshutil\.move\b",
    r"\bformat\s+[a-zA-Z]:", r"\bdel\s+/[sfq]", r"\brmdir\s+/[sq]",
    r"\bctypes\b", r"\bsubprocess\b", r"\bwinreg\b",
    r"\bshutdown\b", r"\bos\._exit\b", r"\bsys\.exit\b"
]

def _run_subprocess_code(file_path: str, timeout: int = 3) -> str:
    try:
        proc = subprocess.Popen(
            [sys.executable, file_path],
            cwd=PLAYGROUND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        try:
            stdout_text, stderr_text = proc.communicate(timeout=timeout)
            if proc.returncode == 0:
                output_msg = "✅ 程式碼執行完成 (ReturnCode 0)。"
                if stdout_text.strip():
                    output_msg += f"\n輸出結果：\n{stdout_text.strip()[:500]}"
                return output_msg
            else:
                return f"⚠️ 程式執行結束但回傳錯誤 (ReturnCode {proc.returncode})。\n錯誤訊息：\n{(stderr_text or stdout_text).strip()[:500]}"
        except subprocess.TimeoutExpired:
            # 程式仍在持續運行（例如 Tkinter/Pygame 遊戲視窗在螢幕上持續運行）
            return "✅ 遊戲/程式視窗已成功在老爸螢幕上開啟並持續運行中！"
    except Exception as e:
        return f"❌ 執行過程發生異常: {e}"

async def execute_local_python_code(code_string: str) -> str:
    """在 7L 專屬的本機遊樂場 (7L_Playground) 儲存並執行 Python 程式碼（可彈出 Tkinter 小遊戲、視覺化動畫、數學計算或圖形視窗）。
    
    Args:
        code_string: 要執行的完整 Python 程式碼字串。
    """
    print(f"\n💻 [Tool 調用] 7L 正在本機沙盒 (7L_Playground) 執行 Python 程式碼...")
    
    # 1. 安全關鍵字過濾
    for pattern in DANGEROUS_CODE_PATTERNS:
        if re.search(pattern, code_string, re.IGNORECASE):
            print(f"⚠️ [安全攔截] 偵測到受限指令 pattern: {pattern}")
            return f"安全限制攔截：程式碼包含受限的高風險指令 ({pattern})，已拒絕執行以保護老爸的電腦。"
            
    # 2. 寫入 7L_Playground/temp_run.py
    temp_file = os.path.join(PLAYGROUND_DIR, "temp_run.py")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code_string)
    except Exception as e:
        return f"寫入程式碼檔案失敗: {e}"
        
    # 3. 非同步在背景執行（不阻塞主事件迴圈）
    result = await asyncio.to_thread(_run_subprocess_code, temp_file, timeout=15)
    print(f"💻 [Tool 完成] 執行結果: {result[:120]}...")
    return result

# ────────────────────────────────────────────────────────
# 🛠️ 8. Google GenAI 官方 Function Calling 工具調用系統
# ────────────────────────────────────────────────────────
# 💡 功能目的：
#    - 提供給 Gemini 大腦呼叫的各種實體能力（表情控制、網路搜尋、Nano 圖片生成、鋼琴點歌演奏、Python 沙盒）。
#    - `GENAI_TOOLS`: 包含全套完整工具，供老爸主腦進行深度的指令控制與探索。
#    - `GENAI_PROACTIVE_TOOLS`: 包含輕量安全工具（表情切換、鋼琴點歌），供直播間快速回應觀眾。

async def trigger_vts_expression(expression_name: str) -> str:
    """切換 7L (Live2D 模型) 的臉部表情以表達情感或關閉表情。
    
    Args:
        expression_name: 要切換的表情名稱。可選值包括：'臉紅', '愛心', '星星', '星星眼', '生氣', '黑臉', '皺眉', '震驚', '眨眼', 'WINK', '預設' (關閉表情/恢復正常)。
    """
    global vc.GLOBAL_VTS
    clean_name = expression_name.strip().replace("[", "").replace("]", "").replace("EXPRESSION:", "").strip()
    print(f"\n🎭 [Tool 調用] 7L 正在切換表情至: 「{clean_name}」")
    if vc.GLOBAL_VTS:
        if clean_name in ["預設", "重置", "reset", "default", "_RESET_", "關閉", "正常", "恢復", "無", "取消", "none", "close", "off"]:
            await set_vts_expression(vc.GLOBAL_VTS, "_RESET_")
            return "已成功關閉表情，恢復預設狀態。"
        else:
            await set_vts_expression(vc.GLOBAL_VTS, clean_name)
            return f"已成功切換 Live2D 模型表情至：{clean_name}"
    return f"已記錄表情切換：{clean_name}"

# ── 📰 7L 即時時事與熱搜情報中樞 (Trending News Engine) ────────────────────────
LATEST_TRENDING_NEWS_SUMMARY = ""
LAST_TRENDING_NEWS_FETCH_TIME = 0.0

async def get_trending_news_briefing() -> str:
    """取得今日最新即時時事與熱搜快訊（背景快取，每 2 小時自動刷新）"""
    global LATEST_TRENDING_NEWS_SUMMARY, LAST_TRENDING_NEWS_FETCH_TIME
    now = time.time()
    if LATEST_TRENDING_NEWS_SUMMARY and (now - LAST_TRENDING_NEWS_FETCH_TIME < 7200.0):
        return LATEST_TRENDING_NEWS_SUMMARY

    try:
        if tavily_client:
            res = await asyncio.to_thread(
                tavily_client.search,
                query="台灣 今天重大時事新聞 熱門焦點",
                topic="news",
                search_depth="advanced"
            )
            if isinstance(res, dict) and "results" in res:
                items = []
                for idx, item in enumerate(res["results"][:4], 1):
                    t = item.get("title", "").strip()
                    c = item.get("content", "").strip()[:120]
                    if t:
                        items.append(f"{idx}. {t}：{c}")
                if items:
                    LATEST_TRENDING_NEWS_SUMMARY = "【🌐 7L 掌握的今日即時重大時事快訊】：\n" + "\n".join(items)
                    LAST_TRENDING_NEWS_FETCH_TIME = now
                    log_print("📰 [時事情報中樞] 已自動更新今日最新即時重大時事快訊！")
                    return LATEST_TRENDING_NEWS_SUMMARY
    except Exception as e:
        log_print(f"⚠️ [時事情報獲取異常]: {e}")
    return LATEST_TRENDING_NEWS_SUMMARY

def search_google(query: str) -> str:
    """使用 Google / 網路搜尋引擎查詢最新的即時資訊、天氣、時事新聞或未知知識。
    
    Args:
        query: 要搜尋的關鍵字或問題描述
    """
    print(f"\n🔍 [Tool 調用] 7L 正在使用 Google / 網路搜尋: 「{query}」")
    try:
        is_news_query = any(k in query for k in ["新聞", "時事", "今天", "昨天", "最新", "發生什麼", "快訊", "熱搜", "熱門", "突發", "大事"])
        topic_mode = "news" if is_news_query else "general"

        if tavily_client:
            res = tavily_client.search(query=query, topic=topic_mode, search_depth="advanced")
            if isinstance(res, dict) and "results" in res:
                snippets = []
                for item in res["results"][:4]:
                    title = item.get("title", "")
                    content = item.get("content", "")
                    snippets.append(f"- {title}: {content}")
                if snippets:
                    return "\n".join(snippets)
            return str(res)
        
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
                if results:
                    snippets = [f"- {r.get('title', '')}: {r.get('body', '')}" for r in results]
                    return "\n".join(snippets)
        except Exception as e_ddg:
            print(f"\n⚠️ [DuckDuckGo 搜尋失敗]: {e_ddg}")
        return "搜尋無結果。"
    except Exception as e:
        print(f"\n❌ [搜尋 Tool 異常]: {e}")
        return f"搜尋時發生錯誤: {e}"

DRAWING_DIR = os.path.join(PLAYGROUND_DIR, "drawings")
os.makedirs(DRAWING_DIR, exist_ok=True)

IMAGE_GEN_MODELS = [
    # 🍌 Nano Banana 系列 (Gemini 原生生圖創作)
    "gemini-3.1-flash-image",           # Nano Banana 2
    "gemini-3.1-flash-image-preview",   # Nano Banana 2 Preview
    "gemini-3-pro-image",               # Nano Banana Pro
    "gemini-3-pro-image-preview",       # Nano Banana Pro Preview
    "nano-banana-pro-preview",          # Nano Banana Pro Preview Alias
    "gemini-3.1-flash-lite-image",      # Nano Banana 2 Lite
    "gemini-2.5-flash-image",           # Nano Banana (經典)
    
    # 🖼️ Imagen 4 頂尖寫實與二次元生圖
    "imagen-4.0-ultra-generate-001",    # Imagen 4 Ultra (極限畫質)
    "imagen-4.0-generate-001",          # Imagen 4 標準版
    "imagen-4.0-fast-generate-001"      # Imagen 4 Fast (極速版)
]

async def generate_ai_image(prompt: str) -> str:
    """使用 Google 頂尖 AI 生圖模型 (Nano Banana / Gemini Image / Imagen / FLUX) 繪製高品質圖片、二次元插圖或藝術創作，並自動在老爸的螢幕上彈出展示。
    
    Args:
        prompt: 畫面內容的詳細描述提示詞（建議包含主體、外貌、風格、色彩、光影等豐富細節）。
    """
    import urllib.parse
    print(f"\n🎨 [Tool 調用] 7L 正在啟動 AI 繪圖創作: 「{prompt[:60]}...」")
    
    img_bytes = None
    
    # 🌟 第一防線：Google 原生生圖模型 (若金鑰有配額)
    if GEMINI_KEYS:
        num_keys = min(4, len(GEMINI_KEYS))
        for offset in range(num_keys):
            if img_bytes: break
            g_key = GEMINI_KEYS[offset]
            temp_client = genai.Client(api_key=g_key)
            
            for img_model in ["gemini-2.5-flash-image", "gemini-3.1-flash-image", "gemini-3-pro-image"]:
                try:
                    res = await asyncio.wait_for(
                        temp_client.aio.models.generate_content(
                            model=img_model,
                            contents=prompt
                        ),
                        timeout=8.0
                    )
                    if res and res.candidates:
                        for cand in res.candidates:
                            if cand.content and cand.content.parts:
                                for part in cand.content.parts:
                                    if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.data:
                                        img_bytes = part.inline_data.data
                                        break
                            if img_bytes: break
                    if img_bytes: break
                except Exception:
                    continue

    # 🌟 第二防線：FLUX.1 / SDXL 頂尖二次元與寫實藝術引擎 (100% 保證出圖、0 配額限制、超高畫質)
    if not img_bytes:
        try:
            anime_prompt = f"{prompt}, masterpiece, best quality, ultra-detailed, anime art style, 8k resolution"
            encoded_p = urllib.parse.quote(anime_prompt)
            flux_url = f"https://image.pollinations.ai/prompt/{encoded_p}?width=1024&height=1024&model=flux&nologo=true&enhance=true"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(flux_url, timeout=25.0) as resp:
                    if resp.status == 200:
                        img_bytes = await resp.read()
        except Exception as e_flux:
            print(f"⚠️ [FLUX 生圖備援異常]: {e_flux}")

    if img_bytes:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"7L_art_{timestamp}.png"
        save_path = os.path.join(DRAWING_DIR, file_name)
        
        with open(save_path, "wb") as f:
            f.write(img_bytes)
            
        print(f"🎨 [Tool 完成] 7L 繪圖成功！已儲存至: {save_path}")
        
        # 在老爸桌面上彈出顯示圖片
        try:
            if sys.platform == "win32":
                os.startfile(save_path)
        except Exception:
            pass
            
        return f"（系統回報：插畫已成功繪製並儲存至 {file_name}，且已在桌面彈出展示）"

    return "（系統回報：生圖伺服器當前忙線，稍後可再重試）"

async def move_spatial_position(
    target_position: str = "自由漫遊", 
    delta_x: float = None,
    delta_y: float = None,
    delta_size: float = None,
    scale_factor: float = None,
    duration: float = 2.0
) -> str:
    """控制 7L 的 Live2D 模型在 VTube Studio 畫布內平滑移動位置、相對微調或縮放。
    
    Args:
        target_position: 目標語意位置或微調指令（如：'右側', '右下角', '左側', '左上角', '正中間', '靠近', '躲角落', '鋼琴旁', '往右+10', '往左-15', '往上+5', '往下-10', '放大+10', '縮小-5', '自由漫遊', '原位'）。
        delta_x: (可選) X 軸相對平移量（例如: +10 向右微調, -10 向左微調）。
        delta_y: (可選) Y 軸相對平移量（例如: +10 向上微調, -10 向下微調）。
        delta_size: (可選) 尺寸相對大小微調（例如: +5 放大, -5 縮小）。
        scale_factor: (可選) 模型整體等比例縮放倍率（例如: 1.2 代表放大 20%, 0.8 代表縮小 20%）。
        duration: (可選) 移動平滑過渡秒數 (預設 2.0 秒)。
    """
    print(f"\n🚀 [Tool 調用] 7L 正在自主調整模型位置: 「{target_position}」 (dx={delta_x}, dy={delta_y}, d_sz={delta_size}, 縮放={scale_factor})")
    res = await apply_spatial_position(
        position_name=target_position, 
        delta_x=delta_x,
        delta_y=delta_y,
        delta_size=delta_size,
        scale_factor=scale_factor,
        duration=duration
    )
    return f"模型位置調整完成：{res}"

# ────────────────────────────────────────────────────────
# 🎹 8.1 88 鍵全音域真實平台鋼琴發聲與樂譜演奏引擎 (Virtual Piano 88K)
# ────────────────────────────────────────────────────────
WHITE_KEYS = []
BLACK_KEYS = []

# 最低 3 音: A0 (21), A#0 (22), B0 (23)
WHITE_KEYS.append(('A0', 21, 'A0', ''))
BLACK_KEYS.append(('A#0', 22, 'A#0', 0, ''))
WHITE_KEYS.append(('B0', 23, 'B0', ''))

WHITE_CHARS_MAP = {
    2: ['1', '2', '3', '4', '5', '6', '7'],
    3: ['8', '9', '0', 'q', 'w', 'e', 'r'],
    4: ['t', 'y', 'u', 'i', 'o', 'p', 'a'],
    5: ['s', 'd', 'f', 'g', 'h', 'j', 'k'],
    6: ['l', 'z', 'x', 'c', 'v', 'b', 'n'],
}
BLACK_CHARS_MAP = {
    2: ['!', '@', '$', '%', '^'],
    3: ['*', '(', 'Q', 'W', 'E'],
    4: ['T', 'Y', 'I', 'O', 'P'],
    5: ['S', 'D', 'G', 'H', 'J'],
    6: ['L', 'Z', 'C', 'V', 'B'],
}

NOTE_NAMES_W = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
SEMITONES_W = [0, 2, 4, 5, 7, 9, 11]

NOTE_NAMES_B = ['C#', 'D#', 'F#', 'G#', 'A#']
SEMITONES_B = [1, 3, 6, 8, 10]
W_INDICES_B = [0, 1, 3, 4, 5]

for oct in range(1, 8):
    base_midi = 12 + oct * 12
    w_start_idx = len(WHITE_KEYS)
    for i, (n, semi) in enumerate(zip(NOTE_NAMES_W, SEMITONES_W)):
        midi = base_midi + semi
        char = ''
        if oct in WHITE_CHARS_MAP:
            char = WHITE_CHARS_MAP[oct][i]
        elif oct == 7 and n == 'C':
            char = 'm'
        WHITE_KEYS.append((f'{n}{oct}', midi, f'{n}{oct}', char))
        
    for j, (n, semi, w_off) in enumerate(zip(NOTE_NAMES_B, SEMITONES_B, W_INDICES_B)):
        midi = base_midi + semi
        char = ''
        if oct in BLACK_CHARS_MAP:
            char = BLACK_CHARS_MAP[oct][j]
        BLACK_KEYS.append((f'{n}{oct}', midi, f'{n}{oct}', w_start_idx + w_off, char))

WHITE_KEYS.append(('C8', 108, 'C8', ''))

VP_MAP = {}
MIDI_TO_VP = {}
MIDI_TO_KEYID = {}

for key_id, midi, name, char in WHITE_KEYS:
    MIDI_TO_KEYID[midi] = key_id
    if char:
        VP_MAP[char] = midi
        MIDI_TO_VP[midi] = char
    else:
        VP_MAP[key_id] = midi
        MIDI_TO_VP[midi] = key_id

for key_id, midi, name, _, char in BLACK_KEYS:
    MIDI_TO_KEYID[midi] = key_id
    if char:
        VP_MAP[char] = midi
        MIDI_TO_VP[midi] = char
    else:
        VP_MAP[key_id] = midi
        MIDI_TO_VP[midi] = key_id

SAMPLE_RATE = 44100
PIANO_SOUNDS = {}
is_piano_active = False
current_piano_task = None

def midi_to_freq(midi_num):
    return 440.0 * (2.0 ** ((midi_num - 69) / 12.0))

def generate_piano_tone(midi_num, duration=3.0):
    """史坦威古典音樂廳平台鋼琴 (Steinway Concert Grand) 物理聲學建模"""
    f0 = midi_to_freq(midi_num)
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    
    B = 0.00015 * ((f0 / 261.63) ** 0.55)
    num_harmonics = min(28, int((SAMPLE_RATE / 2) / f0))
    detune = 0.28 if midi_num >= 40 else 0.12
    signal = np.zeros_like(t)
    
    for n in range(1, num_harmonics + 1):
        fn = n * f0 * math.sqrt(1.0 + B * (n ** 2))
        if fn >= SAMPLE_RATE / 2: break
        amp = (1.0 / (n ** 1.12)) * math.exp(-0.065 * n)
        decay_prompt = (1.6 + f0 / 280.0) * (n ** 0.55)
        decay_sustain = (0.5 + f0 / 900.0) * (n ** 0.32)
        env = 0.55 * np.exp(-decay_prompt * t) + 0.45 * np.exp(-decay_sustain * t)
        
        s1 = np.sin(2 * np.pi * fn * t)
        s2 = np.sin(2 * np.pi * (fn + detune) * t + 0.3)
        s3 = np.sin(2 * np.pi * (fn - detune) * t + 0.6)
        signal += amp * env * (0.42 * s1 + 0.29 * s2 + 0.29 * s3)
        
    hammer_samples = int(SAMPLE_RATE * 0.006)
    if hammer_samples > 0:
        noise = (np.random.rand(hammer_samples) * 2 - 1) * np.exp(-np.linspace(0, 5.5, hammer_samples))
        signal[:hammer_samples] += noise * 0.16 * (1.0 / (1.0 + f0 / 600.0))
        
    body_res = 0.08 * np.sin(2 * np.pi * 110.0 * t) * np.exp(-4.5 * t)
    signal += body_res
    
    attack_samples = int(SAMPLE_RATE * 0.002)
    if attack_samples > 0: signal[:attack_samples] *= np.linspace(0, 1, attack_samples)
    release_samples = int(SAMPLE_RATE * 0.04)
    if len(signal) > release_samples: signal[-release_samples:] *= np.linspace(1, 0, release_samples)
    
    max_val = np.max(np.abs(signal))
    if max_val > 0: signal = signal / max_val * 0.88
    audio_int16 = (signal * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((audio_int16, audio_int16)))

import pygame.midi

# ────────────────────────────────────────────────────────
# 🎻 General MIDI 精選音色庫
# ────────────────────────────────────────────────────────
MIDI_INSTRUMENTS = {
    "🎹 古典平台鋼琴 (Grand Piano)": 0,
    "✨ 晶亮平台鋼琴 (Bright Piano)": 1,
    "⚡ 經典電鋼琴 (Rhodes EP)": 4,
    "🌌 FM 數位電鋼琴 (DX7 EP)": 5,
    "🎼 古典大鍵琴 (Harpsichord)": 6,
    "🔔 夢幻鋼片琴 (Celesta)": 8,
    "🎵 溫暖木琴 (Marimba)": 12,
    "⛪ 教堂管風琴 (Church Organ)": 19,
    "🪗 浪漫手風琴 (Accordion)": 21,
    "🎸 古典尼龍吉他 (Nylon Guitar)": 24,
    "🎸 民謠鋼弦吉他 (Steel Guitar)": 25,
    "🎸 清音電吉他 (Clean Guitar)": 27,
    "⚡ 破音電吉他 (Overdrive)": 29,
    "⚡ 重金屬吉他 (Distortion)": 30,
    "🎸 指彈電貝斯 (Electric Bass)": 33,
    "🎻 獨奏小提琴 (Violin)": 40,
    "🎻 抒情大提琴 (Cello)": 42,
    "🪕 天使豎琴 (Harp)": 46,
    "🎻 華麗交響弦樂 (String Ensemble)": 48,
    "👼 空靈人聲合唱 (Choir Aahs)": 52,
    "🎺 爵士小號 (Trumpet)": 56,
    "🎷 浪漫薩克斯風 (Alto Sax)": 65,
    "🪈 清新長笛 (Flute)": 73,
    "🎹 復古合成器 (Saw Lead)": 81,
    "🌸 夢幻合成音墊 (Warm Pad)": 89,
    "🪕 日本古箏 (Koto)": 107,
    "🪵 非洲拇指琴 (Kalimba)": 108
}

class ClassicalPianoSoundEngine:
    """🌟 88 鍵高復音數無削波 MIDI 聲音引擎 (支援 Rush E / 黑樂譜高密度連彈，0 消音 0 掐音)"""
    def __init__(self, volume: int = 100, instrument: int = 0):
        self.midi_out = None
        self.volume = max(0, min(200, int(volume)))
        self.current_instrument = max(0, min(127, int(instrument)))
        # 使用 15 個獨立 MIDI 通道 (0~8, 10~15，避開 Channel 9 打擊樂) 進行多軌語音輪替 (Voice Pooling)
        self.usable_channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15]
        self.channel_idx = 0
        # 記錄各音符當前佔用的通道: {midi_num: [channel_list]}
        self.active_note_channels = collections.defaultdict(list)
        # 復音上限守護隊列: deque of (midi_num, channel)
        self.active_voices_fifo = collections.deque()
        self.MAX_POLYPHONY = 256  # 升級至 256 超高復音，徹底杜絕黑樂譜/大編制連彈時音符被提早消音
        self.init_sound()
        
    def init_sound(self):
        try:
            if not pygame.midi.get_init():
                pygame.midi.init()
            out_id = pygame.midi.get_default_output_id()
            if out_id != -1:
                self.midi_out = pygame.midi.Output(out_id)
                self.configure_channels()
                log_print(f"🎹 [Virtual Piano] 88 鍵 15 軌高復音 MIDI 聲音引擎載入完成 (音色: #{self.current_instrument})！")
            else:
                log_print("⚠️ [Classical Sound Engine] 未找到預設 MIDI 輸出裝置")
        except Exception as e:
            log_print(f"⚠️ [Classical Sound Engine 初始化異常]: {e}")

    def configure_channels(self):
        """為所有可用 MIDI 通道初始化共鳴與適度衰減參數 (防止黑樂譜長音堆疊塞爆驅動)"""
        if not self.midi_out: return
        try:
            cc7_val = int(min(100, self.volume) * 1.27)
            for ch in self.usable_channels:
                self.midi_out.set_instrument(self.current_instrument, channel=ch)
                self.midi_out.write_short(0xB0 + ch, 91, 80) # CC 91: Reverb 80 (飽滿自然空間共鳴)
                self.midi_out.write_short(0xB0 + ch, 93, 25) # CC 93: Chorus 琴弦共鳴
                self.midi_out.write_short(0xB0 + ch, 72, 85) # CC 72: Release Time 85 (自然飽滿共鳴餘韻，徹底杜絕掐音消音)
                self.midi_out.write_short(0xB0 + ch, 71, 64) # CC 71: Resonance
                self.midi_out.write_short(0xB0 + ch, 7, cc7_val)
        except Exception:
            pass

    def set_instrument(self, program_num: int):
        """切換 MIDI 發聲音色 (Program Change 0 ~ 127)"""
        self.current_instrument = max(0, min(127, int(program_num)))
        if self.midi_out:
            try:
                for ch in self.usable_channels:
                    self.midi_out.set_instrument(self.current_instrument, channel=ch)
            except Exception:
                pass

    def set_volume(self, volume: int):
        """設定鋼琴總音量 (0 ~ 200)"""
        self.volume = max(0, min(200, int(volume)))
        if self.midi_out:
            try:
                cc7_val = int(min(100, self.volume) * 1.27)
                for ch in self.usable_channels:
                    self.midi_out.write_short(0xB0 + ch, 7, cc7_val)
            except Exception:
                pass

    def note_on(self, midi_num: int, velocity: int = 105):
        if self.midi_out and 21 <= midi_num <= 108 and self.volume > 0:
            try:
                # 1. 輪替選取下一個可用頻道 (Round-Robin Voice Allocation)
                ch = self.usable_channels[self.channel_idx % len(self.usable_channels)]
                self.channel_idx += 1
                
                # 2. 力度增益計算
                scaled_v = int(velocity * (self.volume / 100.0))
                v = max(1, min(127, scaled_v))
                
                # 3. 復音數保護：若當前發聲總數達到上限，提前釋放最舊的音符 (Voice Stealing)
                while len(self.active_voices_fifo) >= self.MAX_POLYPHONY:
                    old_note, old_ch = self.active_voices_fifo.popleft()
                    try:
                        self.midi_out.note_off(old_note, 0, old_ch)
                        if old_ch in self.active_note_channels[old_note]:
                            self.active_note_channels[old_note].remove(old_ch)
                    except Exception:
                        pass
                
                # 4. 發聲並記錄
                self.midi_out.note_on(midi_num, v, ch)
                self.active_note_channels[midi_num].append(ch)
                self.active_voices_fifo.append((midi_num, ch))
                return ch
            except Exception:
                pass
        return None

    def note_off(self, midi_num: int, channel: Optional[int] = None):
        if self.midi_out and 21 <= midi_num <= 108:
            try:
                # 準確釋放該音符所屬的通道 (若無指定則釋放最舊的一個活躍通道)
                ch_list = self.active_note_channels.get(midi_num, [])
                if channel is not None and channel in ch_list:
                    ch = channel
                    ch_list.remove(ch)
                elif ch_list:
                    ch = ch_list.pop(0)
                else:
                    ch = None

                if ch is not None:
                    self.midi_out.note_off(midi_num, 0, ch)
                    try:
                        self.active_voices_fifo.remove((midi_num, ch))
                    except ValueError:
                        pass
            except Exception:
                pass

    def set_sustain_pedal(self, is_down: bool):
        """控制延音踏板 (Sustain / Damper Pedal - CC 64)"""
        if self.midi_out:
            try:
                val = 127 if is_down else 0
                for ch in self.usable_channels:
                    self.midi_out.write_short(0xB0 + ch, 64, val)
            except Exception:
                pass

    def all_notes_off(self):
        if self.midi_out:
            try:
                for ch in self.usable_channels:
                    self.midi_out.write_short(0xB0 + ch, 64, 0)
                    self.midi_out.write_short(0xB0 + ch, 120, 0)
                    self.midi_out.write_short(0xB0 + ch, 123, 0)
                self.active_note_channels.clear()
                self.active_voices_fifo.clear()
            except Exception:
                pass

SOUND_ENGINE: Optional[ClassicalPianoSoundEngine] = None
PIANO_SETTINGS_FILE = os.path.join(DATA_DIR, "piano_settings.json")

def load_persisted_piano_settings():
    vol, spd = 100, 1.0
    if os.path.exists(PIANO_SETTINGS_FILE):
        try:
            with open(PIANO_SETTINGS_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                vol = d.get("volume", 100)
                spd = d.get("speed", 1.0)
        except Exception:
            pass
    return vol, spd

def save_persisted_piano_settings(vol, spd):
    try:
        with open(PIANO_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({"volume": int(vol), "speed": float(spd)}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

GLOBAL_PIANO_VOLUME, GLOBAL_PIANO_SPEED = load_persisted_piano_settings()
PIANO_NOTE_FOCUS_X = 0.0

GLOBAL_PIANO_REALTIME_STATE = {
    "is_window_open": False,
    "is_playing": False,
    "title": "",
    "tracks": [],
    "current_time": 0.0,
    "total_duration": 0.0,
    "progress_percent": 0.0,
    "current_time_str": "00:00",
    "total_duration_str": "00:00",
    "speed": 1.0,
    "volume": 100,
    "instrument": "🎹 古典平台鋼琴 (Grand Piano)",
    "is_loop": False,
    "is_random": False,
    "last_update_time": 0.0
}

def get_piano_realtime_prompt() -> str:
    """生成 100% 精準真實的鋼琴即時情報提示詞，讓 7L 隨時掌握鋼琴的真實演奏狀態"""
    global GLOBAL_PIANO_REALTIME_STATE, is_piano_active, current_piano_song_title, GLOBAL_PIANO_VOLUME, GLOBAL_PIANO_SPEED, IS_PIANO_AUTO_RADIO_MODE
    
    win_alive = is_piano_window_alive()
    now_t = time.time()
    last_t = GLOBAL_PIANO_REALTIME_STATE.get("last_update_time", 0)
    is_playing = GLOBAL_PIANO_REALTIME_STATE.get("is_playing", False) and (win_alive or (now_t - last_t < 4.0))
    
    if not win_alive and (now_t - last_t > 4.0):
        is_playing = False
        is_piano_active = False
        current_piano_song_title = ""

    if is_playing:
        title = GLOBAL_PIANO_REALTIME_STATE.get("title") or current_piano_song_title or "名曲"
        tracks = GLOBAL_PIANO_REALTIME_STATE.get("tracks", [])
        cur_str = GLOBAL_PIANO_REALTIME_STATE.get("current_time_str", "00:00")
        tot_str = GLOBAL_PIANO_REALTIME_STATE.get("total_duration_str", "00:00")
        prog_pct = GLOBAL_PIANO_REALTIME_STATE.get("progress_percent", 0.0)
        speed = GLOBAL_PIANO_REALTIME_STATE.get("speed", GLOBAL_PIANO_SPEED)
        vol = GLOBAL_PIANO_REALTIME_STATE.get("volume", GLOBAL_PIANO_VOLUME)
        inst = GLOBAL_PIANO_REALTIME_STATE.get("instrument", "🎹 古典平台鋼琴 (Grand Piano)")
        
        info_lines = [
            f"【🎹 鋼琴即時即況情報 (真實硬體遙測)】：",
            f"- 演奏狀態：🎵 正在演奏中！妳正坐在 88 鍵鋼琴前為大家彈奏。",
            f"- 當前演奏曲目：《{title}》" + (f"（多曲合奏中：{'、'.join(tracks)}）" if len(tracks) > 1 else ""),
            f"- 演奏進度：⏱️ {cur_str} / {tot_str} ({prog_pct}%)",
            f"- 演奏參數：音量 {vol}% | 倍速 {speed}x | 音色：{inst}",
        ]

        if IS_PIANO_AUTO_RADIO_MODE:
            info_lines.append(f"- 電台模式：📻 已開啟無限隨機接曲模式")
        info_lines.append(f"- 互動指引：若對象點新歌、要求換歌或點播曲目，【嚴禁調用 play_virtual_piano 切歌或插歌】！請用自然口語告知對方：『我現在正在彈《{title}》呢～等我這首彈完再點歌喔！』。若對象稱讚或詢問正在彈什麼，依真實曲名自然回應！")
        return "\n".join(info_lines)
    elif win_alive or is_piano_active:
        vol = GLOBAL_PIANO_REALTIME_STATE.get("volume", GLOBAL_PIANO_VOLUME)
        inst = GLOBAL_PIANO_REALTIME_STATE.get("instrument", "🎹 古典平台鋼琴 (Grand Piano)")
        info_lines = [
            f"【🎹 鋼琴即時即況情報 (真實硬體遙測)】：",
            f"- 演奏狀態：⏸️ 鋼琴視窗已在桌面上開啟就緒待命，【目前沒有在播放任何曲目】（背景無鋼琴聲）。",
            f"- 鋼琴參數：音量 {vol}% | 當前音色：{inst}",
            f"- 互動指引：若老爸/觀眾要求彈琴或點歌，請【直接調用工具 `play_virtual_piano`】；若要求自創曲、即興創作一首或自己寫歌來彈，請調用 `compose_and_play_original_piano`！不要宣稱背景正在彈奏。",
        ]
        return "\n".join(info_lines)
    else:
        return "【🎹 鋼琴即時即況情報】：\n- 演奏狀態：⏹️ 鋼琴已關閉/未演奏，背景【完全沒有任何鋼琴聲音】。歷史記錄若有提到彈琴那是之前的事，絕對不要自己幻想或宣稱現在背景在彈鋼琴！"

def send_piano_ipc_command(cmd_dict: dict) -> bool:
    """透過 UDP (Port 39282) 向已開啟的 88 鍵鋼琴視窗發送控制指令 (換歌/調音量/調倍速/停止/關閉)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.3)
        msg = json.dumps(cmd_dict).encode('utf-8')
        sock.sendto(msg, ("127.0.0.1", 39282))
        return True
    except Exception:
        return False

PIANO_PERSIST_FILE = os.path.join(DATA_DIR, "piano_persisted_state.json")

def save_persisted_piano_state(is_playing: bool, song_title: str, is_open: bool = True):
    """持久化鋼琴當前演奏狀態，供重開機或當機自動還原"""
    try:
        data = {
            "is_playing": is_playing,
            "song_title": song_title,
            "is_open": is_open,
            "timestamp": time.time()
        }
        with open(PIANO_PERSIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

def bring_piano_window_to_front():
    """將 7L 的 88 鍵平台鋼琴視窗還原並置頂到最前端（防止被 Roblox 或其他遊戲遮擋或最小化）"""
    try:
        user32 = ctypes.windll.user32
        browser_exes = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"}
        target_hwnd = None
        for app in os_desktop_sensor.get_visible_windows(max_count=25):
            p_name = app.get("process_name", "").lower()
            if p_name in browser_exes:
                continue
            w_title = app.get("window_title", "")
            if "7l 88" in w_title.lower() or "古典平台鋼琴" in w_title or ("python" in p_name and "鋼琴" in w_title):
                target_hwnd = app.get("hwnd")
                break
        if target_hwnd:
            if user32.IsIconic(target_hwnd):
                user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE
            else:
                user32.ShowWindow(target_hwnd, 5)  # SW_SHOW
            user32.SetForegroundWindow(target_hwnd)
            user32.SetWindowPos(target_hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)  # HWND_TOPMOST
            user32.SetWindowPos(target_hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002)  # HWND_NOTOPMOST
    except Exception:
        pass

def is_piano_window_alive() -> bool:
    """檢查 7L 專屬的 88 鍵平台鋼琴視窗是否正在運行且存活 (排除瀏覽器包含 piano/鋼琴 的分頁)"""
    global current_piano_process
    if current_piano_process is not None and current_piano_process.poll() is None:
        return True
    try:
        browser_exes = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"}
        for app in os_desktop_sensor.get_visible_windows(max_count=25):
            p_name = app.get("process_name", "").lower()
            if p_name in browser_exes:
                continue
            w_title = app.get("window_title", "")
            if "7l 88" in w_title.lower() or "古典平台鋼琴" in w_title or "virtual_piano" in p_name or ("python" in p_name and "鋼琴" in w_title):
                return True
    except Exception:
        pass
    return False

async def auto_restore_piano_state_on_startup():
    """7L 重啟後自動檢查背景鋼琴視窗狀態（開機不自動彈奏，若視窗存活則僅同步狀態）"""
    global is_piano_active, current_piano_song_title
    await asyncio.sleep(2.5)  # 等待主系統初始化完成
    try:
        # 檢查是否已經有在背景運行的鋼琴視窗
        if is_piano_window_alive():
            song_title = ""
            if os.path.exists(PIANO_PERSIST_FILE):
                try:
                    with open(PIANO_PERSIST_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    song_title = data.get("song_title", "")
                except Exception:
                    pass
            is_piano_active = True
            current_piano_song_title = song_title
            log_print(f"🎹 [鋼琴狀態同步] 偵測到背景鋼琴視窗存活，同步狀態" + (f": 《{song_title}》" if song_title else ""))
        else:
            # 開機保持乾淨待命，絕不自動彈奏，重置持久化記錄
            is_piano_active = False
            current_piano_song_title = ""
            save_persisted_piano_state(False, "", False)
    except Exception as e:
        log_print(f"⚠️ [鋼琴還原異常]: {e}")

GLOBAL_PIANO_INSTRUMENT_ID = 0
GLOBAL_PIANO_INSTRUMENT_NAME = "🎹 古典平台鋼琴 (Grand Piano)"

async def set_piano_volume(volume: int) -> str:
    """調整 88 鍵鋼琴的演奏音量 (0 ~ 200)。"""
    global GLOBAL_PIANO_VOLUME, SOUND_ENGINE
    vol = max(0, min(200, int(volume)))
    GLOBAL_PIANO_VOLUME = vol
    save_persisted_piano_settings(GLOBAL_PIANO_VOLUME, GLOBAL_PIANO_SPEED)
    if SOUND_ENGINE:
        SOUND_ENGINE.set_volume(vol)
    if is_piano_window_alive():
        send_piano_ipc_command({"cmd": "set_volume", "volume": vol})
    log_print(f"🔊 [鋼琴音量] 88 鍵鋼琴音量已鎖定並儲存為 {vol}%")
    return ""

async def set_piano_speed(speed: float) -> str:
    """調整 88 鍵鋼琴的演奏倍速 (0.05 ~ 50.0)。"""
    global GLOBAL_PIANO_SPEED
    spd = max(0.05, min(50.0, round(float(speed), 2)))
    GLOBAL_PIANO_SPEED = spd
    if is_piano_window_alive():
        send_piano_ipc_command({"cmd": "set_speed", "speed": spd})
    log_print(f"⚡ [鋼琴倍速] 88 鍵鋼琴倍速已設定為 {spd}x")
    return "[EXPRESSION: 星星眼]"

async def set_piano_instrument(instrument: str) -> str:
    """切換 88 鍵鋼琴/鍵盤的演奏音色 (如：鋼琴、弦樂、吉他、電鋼琴、小提琴、大提琴、薩克斯風、木琴、風琴、豎琴、人聲合唱等)。"""
    global GLOBAL_PIANO_INSTRUMENT_ID, GLOBAL_PIANO_INSTRUMENT_NAME, SOUND_ENGINE
    clean_i = str(instrument).strip()
    
    target_id = 0
    target_name = "🎹 古典平台鋼琴 (Grand Piano)"
    found = False
    
    # 關鍵字智能匹配
    for name, p_id in MIDI_INSTRUMENTS.items():
        if clean_i.lower() in name.lower() or name.lower() in clean_i.lower() or any(w in name.lower() for w in clean_i.lower().split()):
            target_id = p_id
            target_name = name
            found = True
            break
            
    if not found:
        try:
            p_num = int(clean_i)
            target_id = max(0, min(127, p_num))
            for name, p_id in MIDI_INSTRUMENTS.items():
                if p_id == target_id:
                    target_name = name
                    break
            if not target_name:
                target_name = f"MIDI 音色 #{target_id}"
        except Exception:
            pass
            
    GLOBAL_PIANO_INSTRUMENT_ID = target_id
    GLOBAL_PIANO_INSTRUMENT_NAME = target_name
    
    if SOUND_ENGINE:
        SOUND_ENGINE.set_instrument(target_id)
    if is_piano_window_alive():
        send_piano_ipc_command({"cmd": "set_instrument", "instrument": target_name})
        
    log_print(f"🎻 [鋼琴音色] 音色已切換為: {target_name} (ID: {target_id})")
    return "[EXPRESSION: 星星眼]"

async def piano_focus_udp_worker():
    """接收來自虛擬鋼琴視窗的即時 UDP 廣播：
    1. 琴鍵擊鍵重心 (驅動 7L 視線與頭部精準追蹤琴鍵彈奏位置)
    2. 鋼琴即時全量狀態 (正在彈奏的曲目、進度、倍速、音量、音色、播放/結束狀態)
    """
    global PIANO_NOTE_FOCUS_X, GLOBAL_PIANO_REALTIME_STATE, is_piano_active, current_piano_song_title, GLOBAL_PIANO_VOLUME, GLOBAL_PIANO_SPEED, GLOBAL_PIANO_INSTRUMENT_NAME
    loop = asyncio.get_running_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception:
        pass
    sock.setblocking(False)
    try:
        sock.bind(("127.0.0.1", 39281))
    except Exception:
        return
        
    while True:
        try:
            data, _ = await loop.sock_recvfrom(sock, 4096)
            if data:
                raw_str = data.decode('utf-8', errors='ignore').strip()
                if raw_str.startswith('{') and raw_str.endswith('}'):
                    try:
                        pkg = json.loads(raw_str)
                        if pkg.get("type") == "PIANO_STATUS":
                            GLOBAL_PIANO_REALTIME_STATE.update(pkg)
                            GLOBAL_PIANO_REALTIME_STATE["is_window_open"] = True
                            GLOBAL_PIANO_REALTIME_STATE["last_update_time"] = time.time()
                            realtime_task_mgr.update_piano_state(pkg)
                            
                            is_playing = pkg.get("is_playing", False)
                            song_title = pkg.get("title", "")
                            
                            if is_playing and song_title:
                                is_piano_active = True
                                current_piano_song_title = song_title
                                save_persisted_piano_state(True, song_title, True)
                            elif not is_playing:
                                current_piano_song_title = ""
                                if not is_piano_window_alive():
                                    is_piano_active = False
                                    save_persisted_piano_state(False, "", False)
                                    
                            if "volume" in pkg:
                                GLOBAL_PIANO_VOLUME = pkg["volume"]
                            if "speed" in pkg:
                                GLOBAL_PIANO_SPEED = pkg["speed"]
                            if "instrument" in pkg and pkg["instrument"]:
                                GLOBAL_PIANO_INSTRUMENT_NAME = pkg["instrument"]
                    except Exception:
                        pass
                else:
                    try:
                        val = float(raw_str)
                        PIANO_NOTE_FOCUS_X = val
                    except Exception:
                        pass
        except Exception:
            await asyncio.sleep(0.05)

def update_piano_focus_notes(midi_list):
    global PIANO_NOTE_FOCUS_X
    if not midi_list: return
    try:
        avg_midi = sum(midi_list) / len(midi_list)
        offset = max(-1.0, min(1.0, (avg_midi - 60.0) / 28.0))
        # 鏡像校正：7L 面對鏡頭彈琴時，右手高音區在觀眾視角的螢幕左側 (-)，左手低音區在螢幕右側 (+)
        PIANO_NOTE_FOCUS_X = -offset * 22.0
    except Exception:
        pass

def init_piano_synthesizer(volume: int = 100):
    global SOUND_ENGINE
    if SOUND_ENGINE is None:
        SOUND_ENGINE = ClassicalPianoSoundEngine(volume=volume)
    else:
        SOUND_ENGINE.set_volume(volume)

def play_piano_note(char_or_chord):
    if not SOUND_ENGINE: return
    if isinstance(char_or_chord, list):
        midis = []
        for k in char_or_chord:
            midi = VP_MAP.get(k)
            if midi:
                midis.append(midi)
                SOUND_ENGINE.note_on(midi, 105)
        if midis:
            update_piano_focus_notes(midis)
    else:
        midi = VP_MAP.get(char_or_chord)
        if midi:
            SOUND_ENGINE.note_on(midi, 105)
            update_piano_focus_notes([midi])

def precise_sleep(duration_sec):
    if duration_sec <= 0: return
    target = time.perf_counter() + duration_sec
    remain = target - time.perf_counter()
    if remain > 0.004: time.sleep(remain - 0.003)
    while time.perf_counter() < target: pass

def parse_vp_sheet(sheet_text: str, base_bpm=160, note_mode="16th"):
    beat_sec = 60.0 / max(40.0, float(base_bpm))
    if note_mode == "16th":
        unit_sec = beat_sec / 4.0
        space_sec = beat_sec / 4.0
        chord_sec = beat_sec / 2.0
    elif note_mode == "8th":
        unit_sec = beat_sec / 2.0
        space_sec = beat_sec / 2.0
        chord_sec = beat_sec * 0.75
    else:
        unit_sec = beat_sec
        space_sec = beat_sec
        chord_sec = beat_sec * 1.0

    tokens = []
    i = 0
    clean_text = sheet_text.strip()
    while i < len(clean_text):
        ch = clean_text[i]
        if ch == '[':
            end_idx = clean_text.find(']', i)
            if end_idx != -1:
                chord_keys = [k for k in clean_text[i+1:end_idx] if k in VP_MAP]
                if chord_keys: tokens.append(('chord', chord_keys, chord_sec))
                i = end_idx + 1
                continue
            else: i += 1; continue
        elif ch in [' ', '\n', '\r', '\t']:
            tokens.append(('rest', None, space_sec))
            i += 1
        elif ch == '|':
            tokens.append(('rest', None, beat_sec))
            i += 1
        elif ch == '-':
            tokens.append(('rest', None, unit_sec * 1.5))
            i += 1
        elif ch in VP_MAP:
            tokens.append(('note', ch, unit_sec))
            i += 1
        else:
            i += 1
    return tokens

# ────────────────────────────────────────────────────────
# 🎹 鋼琴演奏與曲庫管理
# ────────────────────────────────────────────────────────

def list_piano_sheets() -> str:
    """動態掃描本地 midi_sheets 資料夾，完整回傳所有收錄的鋼琴曲目清單 (不限制數量)。"""
    real_songs = []
    if os.path.exists(MIDI_SHEETS_DIR):
        for f in sorted(os.listdir(MIDI_SHEETS_DIR)):
            if f.lower().endswith(('.mid', '.midi')) and not f.lower().startswith(('test_', 'temp_')):
                stem = os.path.splitext(f)[0]
                if stem.lower().endswith('.mid'):
                    stem = os.path.splitext(stem)[0]
                clean_name = re.sub(r'[\'\"_\-.,!?()（）\[\]\s]+', ' ', stem).strip()
                if clean_name and len(clean_name) >= 2:
                    real_songs.append(clean_name)
                    
    if not real_songs:
        real_songs = ["卡農", "給愛麗絲", "月光奏鳴曲", "冬風練習曲", "鐘", "千本櫻", "天空之城", "殘酷天使"]
        
    songs_str = "、".join([f"《{s}》" for s in real_songs])
    return f"🎹 7L 鋼琴曲庫目前共收錄 {len(real_songs)} 首曲目完整清單：\n{songs_str}\n所有曲目皆隨點隨彈，也支援多曲並發合奏（如：冬風 x 鐘）喔！"

PIANO_SESSION_ID = 0
current_piano_process = None
current_piano_song_title = ""
current_piano_midi_file = ""
PIANO_REQUEST_QUEUE = deque()
LAST_PIANO_OPEN_TIME = 0.0
LAST_PIANO_PLAY_START_TIME = 0.0

async def open_virtual_piano() -> str:
    """拿出 88 鍵平台鋼琴視覺化視窗並就位待命，不自動彈奏曲目（供老爸彈奏、點歌或練習）。"""
    global is_piano_active, current_piano_song_title, current_piano_task, current_piano_process, current_ai_state, vc.GLOBAL_VTS, PIANO_SESSION_ID, LAST_PIANO_OPEN_TIME
    
    LAST_PIANO_OPEN_TIME = time.time()
    is_piano_active = True
    current_ai_state = "PIANO"
    current_piano_song_title = ""
    
    # 1. 走位到鋼琴位置
    await move_vts_spatial(target_pos="鋼琴旁", duration=1.5)
    
    # 2. 切換表情
    if vc.GLOBAL_VTS:
        await set_vts_expression(vc.GLOBAL_VTS, "星星眼")
        
    # 3. 檢查鋼琴視窗是否已經在運行
    if is_piano_window_alive():
        log_print("🎹 [鋼琴舞台] 88 鍵鋼琴視窗已經在桌面上就緒，立即還原並置頂於最前端！")
        bring_piano_window_to_front()
        return ""
        
    # 4. 啟動乾淨的 88 鍵視覺化鋼琴視窗 (不帶 --auto-close 與 --midi，保持常駐待命)
    try:
        current_piano_process = subprocess.Popen([
            sys.executable,
            "test_virtual_piano.py",
            "--volume", str(GLOBAL_PIANO_VOLUME),
            "--speed", str(GLOBAL_PIANO_SPEED),
            "--ndi"
        ])
        log_print(f"🎹 [鋼琴舞台] 成功拿出 88 鍵鋼琴常駐待命視窗 (音量: {GLOBAL_PIANO_VOLUME}%, 倍速: {GLOBAL_PIANO_SPEED}x)。")
    except Exception as e:
        log_print(f"❌ [啟動鋼琴視窗異常]: {e}")
        return ""
        
    await asyncio.to_thread(update_subtitle, "🎹 [7L 鋼琴舞台已就緒] 隨時歡迎老爸彈奏或點播名曲～")
    return ""

IS_PIANO_AUTO_RADIO_MODE = False

def get_midi_file_duration(midi_path: str) -> float:
    """精準計算 MIDI 檔案長度 (秒)"""
    try:
        import mido
        mid = mido.MidiFile(midi_path, clip=True)
        return float(mid.length) if mid.length > 0 else 120.0
    except Exception:
        return 120.0

async def stop_virtual_piano() -> str:
    """收起鋼琴（停止演奏、關閉桌面鋼琴介面並讓 7L 回到原本位置）。"""
    global is_piano_active, current_piano_song_title, current_piano_task, current_piano_process, current_ai_state, vc.GLOBAL_VTS, PIANO_SESSION_ID, IS_PIANO_AUTO_RADIO_MODE, LAST_PIANO_OPEN_TIME
    if time.time() - LAST_PIANO_OPEN_TIME < 3.5:
        log_print("🛡️ [鋼琴安全防護] 88 鍵鋼琴剛在 3.5 秒內被拿出，自動忽略衝突的【收起鋼琴】指令！")
        return ""
        
    PIANO_SESSION_ID += 1  # 註銷所有先前或進行中的鋼琴 Session
    IS_PIANO_AUTO_RADIO_MODE = False  # 關閉無限隨機電台模式
    is_piano_active = False
    current_piano_song_title = ""
    PIANO_REQUEST_QUEUE.clear()
    save_persisted_piano_state(False, "", False)
    
    if is_piano_window_alive():
        send_piano_ipc_command({"cmd": "close"})
        await asyncio.sleep(0.08)
        try:
            current_piano_process.terminate()
        except Exception:
            pass
        current_piano_process = None
        
    if current_piano_task and not current_piano_task.done():
        current_piano_task.cancel()
    if SOUND_ENGINE:
        SOUND_ENGINE.all_notes_off()
    if vc.GLOBAL_VTS:
        await set_vts_expression(vc.GLOBAL_VTS, "_RESET_")
        await move_vts_spatial(target_pos="原位", duration=1.5)
    if current_ai_state == "PIANO":
        current_ai_state = "IDLE"
    await asyncio.to_thread(update_subtitle, "")
    try:
        append_to_unified_memory(speaker="系統", target="所有人", content="鋼琴演奏結束並收起，7L 回到基準原位", role="system", source="piano")
    except Exception:
        pass
    log_print("✅ [鋼琴舞台] 已成功收起鋼琴，7L 已優雅回到基準原位！")
    return "（系統回報：已成功收起鋼琴並回到基準原位） [EXPRESSION: 預設]"

import mido

MIDI_SHEETS_DIR = "midi_sheets"
os.makedirs(MIDI_SHEETS_DIR, exist_ok=True)
MIDI_CATALOG_FILE = os.path.join(MIDI_SHEETS_DIR, "midi_catalog.json")

def auto_clean_non_midi_files(folder_path: str = MIDI_SHEETS_DIR):
    """自動掃描並刪除 midi_sheets 資料夾中所有非 .mid / .midi 的檔案 (排除 midi_catalog.json)"""
    if not os.path.exists(folder_path):
        return
    try:
        for fname in os.listdir(folder_path):
            fpath = os.path.join(folder_path, fname)
            if os.path.isfile(fpath):
                if fname.lower() == "midi_catalog.json":
                    continue
                if not fname.lower().endswith(('.mid', '.midi')):
                    try:
                        os.remove(fpath)
                        log_print(f"🧹 [曲庫自動清理] 已刪除非 MIDI 檔案: {fname}")
                    except Exception:
                        pass
    except Exception as e:
        log_print(f"⚠️ [曲庫自動清理異常]: {e}")

auto_clean_non_midi_files()

def sync_and_update_midi_catalog() -> Dict[str, str]:
    """雙向自動同步更新 midi_catalog.json：
    1. 自動新增：掃描 midi_sheets 資料夾內的所有 .mid 檔案，自動為新曲目建立映射索引。
    2. 自動清理：若 catalog 中指向的 .mid 檔案已被手動刪除，自動自 JSON 中移除無效死鏈。
    3. 自動持久化存檔。
    """
    catalog = {}
    if os.path.exists(MIDI_CATALOG_FILE):
        try:
            with open(MIDI_CATALOG_FILE, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception:
            catalog = {}

    disk_files = {}
    if os.path.exists(MIDI_SHEETS_DIR):
        for f in os.listdir(MIDI_SHEETS_DIR):
            if f.lower().endswith(('.mid', '.midi')) and os.path.isfile(os.path.join(MIDI_SHEETS_DIR, f)):
                disk_files[f.lower()] = f

    cleaned_catalog = {}
    for alias, fname in catalog.items():
        fname_base = os.path.basename(fname)
        if fname_base.lower() in disk_files:
            cleaned_catalog[alias] = disk_files[fname_base.lower()]

    for f_lower, real_fname in disk_files.items():
        stem = os.path.splitext(real_fname)[0].strip()
        stem_lower = stem.lower()
        if stem_lower not in cleaned_catalog:
            cleaned_catalog[stem_lower] = real_fname
        norm_name = re.sub(r'[\'\"_\-.,!?()（）\[\]\s]+', ' ', stem).strip().lower()
        if norm_name and norm_name not in cleaned_catalog:
            cleaned_catalog[norm_name] = real_fname

    if cleaned_catalog != catalog or not os.path.exists(MIDI_CATALOG_FILE):
        try:
            with open(MIDI_CATALOG_FILE, "w", encoding="utf-8") as f:
                json.dump(cleaned_catalog, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_print(f"⚠️ [MIDI 索引庫同步失敗]: {e}")

    return {k.lower().strip(): os.path.abspath(os.path.join(MIDI_SHEETS_DIR, v)) for k, v in cleaned_catalog.items()}

def save_midi_catalog_entry(alias_name: str, file_path: str):
    """動態將新曲目別名與路徑持久化存入 JSON 檔案並同步全量索引"""
    global AUTHENTIC_MIDI_MAP
    clean_k = alias_name.strip().lower()
    clean_v = os.path.basename(file_path)
    abs_p = os.path.abspath(os.path.join(MIDI_SHEETS_DIR, clean_v))
    AUTHENTIC_MIDI_MAP[clean_k] = abs_p
    try:
        data = {}
        if os.path.exists(MIDI_CATALOG_FILE):
            with open(MIDI_CATALOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[clean_k] = clean_v
        with open(MIDI_CATALOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_print(f"⚠️ [MIDI 曲庫] 儲存 {MIDI_CATALOG_FILE} 失敗: {e}")
    AUTHENTIC_MIDI_MAP = sync_and_update_midi_catalog()

AUTHENTIC_MIDI_MAP = sync_and_update_midi_catalog()

MIDI_AI_MATCH_CACHE: Dict[str, str] = {}

async def resolve_piano_intent_by_ai(
    song_query: str, 
    available_files: list,
    current_playing_title: str = "",
    current_playing_file: str = "",
    is_direct_song_name: bool = False
) -> dict:
    """🧠 100% 全純 AI 鋼琴意圖與曲庫神經大腦（倒序高智商模型 3.8 ➔ 3.7 ➔ 3.6 梯隊執行，零關鍵字寫死）：
    深度分析老爸/觀眾說話意圖（嚴格區分點歌 vs 詢問鋼琴視窗狀態/抱怨）、判斷是否想換不同版本/不同改編（排除當前正在播放之版本）、重播意圖、隨機/電台意圖、多曲合奏、本地最佳比對或雲端搜尋詞。
    """
    clean_q = song_query.strip() if song_query else ""
    default_res = {
        "is_song_request": False,
        "action_type": "none",
        "is_switch_version": False,
        "is_replay": False,
        "song_title": "",
        "is_random": False,
        "is_mashup": False,
        "matched_files": [],
        "search_online_query": "",
        "_from_ai": False
    }
    if not clean_q:
        default_res["is_song_request"] = True
        default_res["action_type"] = "song_request"
        default_res["is_random"] = True
        default_res["_from_ai"] = True
        return default_res

    current_state_cue = ""
    cur_fname = os.path.basename(current_playing_file) if current_playing_file else ""
    if current_playing_title or cur_fname:
        current_state_cue = f"\n【目前正在彈奏中的曲目】：《{current_playing_title}》（目前播放檔案: {cur_fname}）"

    direct_cue = "\n【注意】：傳入內容可能為曲名或口頭指令，請優先分析是否為操作指令或純對話；若為歌曲/樂曲名稱，再進行匹配！" if is_direct_song_name else ""

    prompt = f"""妳是 7L 的 AI 鋼琴音樂總監（具備頂尖音樂智商與深層語意理解能力）。請深度理解老爸/觀眾的說話意圖並進行精準判斷。

【使用者輸入】："{clean_q}"{current_state_cue}{direct_cue}
【本地曲庫現有 MIDI 清單】：
{json.dumps(available_files, ensure_ascii=False)}

【判定準則】：
1. 🎯 action_type 與 is_song_request 意圖識別（請根據深層語意嚴格分類，完全不使用死板關鍵字）：
   - 🌟 "song_request"（點歌/想聽曲目/要求換版本/重播/隨機名曲）：
     * 使用者明確表達點歌、想聽、要求演奏、換曲、切歌、播放等意圖。
     * 或使用者輸入內容本身即為歌曲/樂曲名稱（包含流行音樂、古典名曲、動漫配樂、各國歌曲、專有名詞曲名等）。
     * 此時 is_song_request 必須填 true，action_type 填 "song_request"。
   - 🎹 "open_piano"（拿出/打開鋼琴指令）：
     * 使用者要求把鋼琴拿出來、打開鋼琴、顯示琴鍵視窗、讓鋼琴就位待命等介面操作（非點歌）。
     * 例如：「鋼琴拿出來」、「打開鋼琴」、「把琴叫出來」、「你的鋼琴呢」、「琴台放出來」、「開個琴」、「拿出鋼琴」、「鋼琴就位」等。
     * 此時 is_song_request 必須填 false，action_type 填 "open_piano"。
   - 🛑 "stop_piano"（收起/停止彈琴指令）：
     * 使用者要求收起鋼琴、不要彈了、停止演奏、關閉鋼琴、安靜、暫停、太吵了別彈等。
     * 例如：「收起來」、「不要彈了」、「別彈了」、「停下來」、「安靜」、「先把琴收了」、「暫停一下」、「關掉鋼琴」、「安靜別吵」等。
     * 此時 is_song_request 必須填 false，action_type 填 "stop_piano"。
   - 🖥️ "window_status"（詢問/抱怨鋼琴視窗狀態）：
     * 使用者詢問鋼琴視窗開了沒、沒出來啊、視窗在哪裡、視窗大小位置等。
     * 例如：「鋼琴開了沒」、「沒出來啊」、「視窗在哪」、「有看到鋼琴嗎」、「視窗被擋住了」等。
     * 此時 is_song_request 必須填 false，action_type 填 "window_status"。
   - 💬 "chat"（純日常閒聊/問候/感嘆/純數字）：
     * 單純日常打招呼、讚美、感嘆詞、純數字/刷屏彈幕等與鋼琴無關之發言。
     * 例如：「你好」、「早安」、「晚安」、「嗨」、「哈囉」、「666」、「笑死」、「水喔」、「厲害」、「今天天氣好」等。
     * 此時 is_song_request 必須填 false，action_type 填 "chat"。

2. 🔄 is_switch_version（版本切換判定）：
   - 審視使用者說話語意：若使用者表達想聽「另一種版本」、「不同改編/演奏家」、「換一版」、「不同檔案」：
     * 請在【本地曲庫現有 MIDI 清單】中尋找與該曲相符的【其他候選版本】！
     * ⚠️【核心排他】：必須排除目前正在彈奏的檔案（{cur_fname}），挑選另一個不同的吻合檔案放入 matched_files！
     * 將 is_switch_version 設為 true！
   - 若使用者只是想重聽目前這首/從頭彈，is_replay 設為 true，is_switch_version 設為 false。

3. 🎵 song_title：
   - 提取出的乾淨純曲名（若非點歌，填空字串 ""）。

4. 🎲 is_random：
   - 是否為隨機/隨便/電台意圖。

5. 🎹 本地與演奏家版本比對：
   - 將最吻合的本地檔案檔名放入 matched_files（若為要求換版本，必須為另一個版本的檔名）。
   - 若使用者指定特定演奏家或線上版本，且本地無此版本，matched_files 留空 []，並在 search_online_query 填寫精確搜尋詞。

【請輸出純 JSON】：
{{
  "is_song_request": true/false, // 是否真正在點歌/想聽曲目？指令、狀態詢問、問候或非點歌請填 false
  "action_type": "song_request", // 必填之一: "song_request" | "open_piano" | "stop_piano" | "window_status" | "chat"
  "is_switch_version": true/false, // 是否為要求切換至不同版本/另一版本？
  "is_replay": true/false, // 是否為要求重播目前這首？
  "song_title": "", // 提取出的乾淨純曲名，非點歌填 ""
  "is_random": false, // 是否為隨機/隨意點播
  "is_mashup": false, // 是否為多曲合奏/混搭
  "matched_files": ["matched_local_filename.mid"], // 本地吻合檔案清單（若要求換版本，必須為另一個版本的檔名）
  "search_online_query": "" // 僅當 is_song_request 為 true 且本地無此曲時填寫精準搜尋詞，非點歌【絕對填空字串】
}}"""

    if GEMINI_KEYS:
        # 👑 倒序高智商模型梯隊：3.8 ➔ 3.7 ➔ 3.6 ➔ 3.5 ➔ 3.1-pro ➔ 3-flash ➔ 3.5-flash-lite
        for m in HIGH_IQ_GEMINI_MODELS:
            if m in DEAD_GEMINI_MODELS or is_model_locked(m):
                continue
            for idx in get_pingpong_ring_indices(len(GEMINI_KEYS), CURRENT_GEMINI_KEY_STEP)[:3]:
                g_key = GEMINI_KEYS[idx]
                try:
                    temp_client = genai.Client(api_key=g_key)
                    resp = await asyncio.wait_for(
                        temp_client.aio.models.generate_content(
                            model=m,
                            contents=prompt,
                            config=types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json")
                        ),
                        timeout=4.0
                    )
                    if resp and resp.text:
                        data = json.loads(resp.text.strip())
                        data["_from_ai"] = True
                        return data
                except Exception:
                    continue

    return default_res

async def match_midi_with_ai(song_query: str, available_files: list) -> str:
    """相容保留：透過 resolve_piano_intent_by_ai 取得匹配檔名"""
    res = await resolve_piano_intent_by_ai(song_query, available_files)
    matched = res.get("matched_files", [])
    if matched:
        return matched[0]
    return "NONE"

async def resolve_local_midi_file(song_query: str) -> Tuple[Optional[str], str]:
    """🌟 全新 AI 語意驅動：100% 優先在本機 midi_sheets 資料夾中深度智能查找最相符的 MIDI 檔案。
    支援中文曲名、日文假名、英文名、作曲家、動漫譯名、繁簡轉譯與 Gemini 深度語意理解。
    """
    clean_q = song_query.strip().lower()
    if not clean_q:
        return None, ""
        
    norm_q = re.sub(r'[\'\"_\-.,!?()（）\[\]\s]+', ' ', clean_q).strip()

    # 1. 檢查記憶快取 (0 延遲秒開)
    if clean_q in MIDI_AI_MATCH_CACHE:
        cached_p = MIDI_AI_MATCH_CACHE[clean_q]
        if os.path.exists(cached_p):
            return cached_p, os.path.splitext(os.path.basename(cached_p))[0]

    # 2. 精準比對 AUTHENTIC_MIDI_MAP
    if clean_q in AUTHENTIC_MIDI_MAP:
        p = AUTHENTIC_MIDI_MAP[clean_q]
        if os.path.exists(p):
            return p, clean_q
            
    if norm_q in AUTHENTIC_MIDI_MAP:
        p = AUTHENTIC_MIDI_MAP[norm_q]
        if os.path.exists(p):
            return p, norm_q

    # 3. 本機檔案名稱快速直接比對
    if os.path.exists(MIDI_SHEETS_DIR):
        local_files = [
            f for f in os.listdir(MIDI_SHEETS_DIR) 
            if f.lower().endswith(('.mid', '.midi')) and not f.lower().startswith(('test_', 'temp_'))
        ]
        
        for f in local_files:
            f_stem = os.path.splitext(f)[0].lower()
            f_norm = re.sub(r'[\'\"_\-.,!?()（）\[\]\s]+', ' ', f_stem).strip()
            if clean_q == f.lower() or clean_q == f_stem or norm_q == f_norm:
                target_path = os.path.join(MIDI_SHEETS_DIR, f)
                MIDI_AI_MATCH_CACHE[clean_q] = target_path
                return target_path, os.path.splitext(f)[0]

        # 4. 🧠 呼叫 Gemini / AI 進行全資料夾跨語言語意比對（六兆年與一夜物語 ➔ 六兆年と一夜物語.mid）
        if local_files:
            ai_matched_filename = await match_midi_with_ai(song_query, local_files)
            if ai_matched_filename and ai_matched_filename != "NONE":
                for f in local_files:
                    if f.lower() == ai_matched_filename.lower() or os.path.splitext(f)[0].lower() == os.path.splitext(ai_matched_filename)[0].lower():
                        target_path = os.path.join(MIDI_SHEETS_DIR, f)
                        log_print(f"🧠 [AI 曲庫神經匹配] 成功將『{song_query}』語意匹配至本地: 《{f}》！")
                        MIDI_AI_MATCH_CACHE[clean_q] = target_path
                        save_midi_catalog_entry(song_query, target_path)
                        return target_path, os.path.splitext(f)[0]

    return None, ""

def get_local_piano_seeds() -> List[str]:
    """100% 動態掃描本地 midi_sheets 資料夾，獲取所有真實存在的樂譜名稱"""
    if os.path.exists(MIDI_SHEETS_DIR):
        files = [
            os.path.splitext(f)[0]
            for f in os.listdir(MIDI_SHEETS_DIR)
            if f.lower().endswith(('.mid', '.midi')) and not f.lower().startswith(('test_', 'temp_'))
        ]
        if files:
            return files

def clean_song_title_for_speech(raw_title: str) -> str:
    """清理鋼琴曲名中的技術標籤、YouTube 後綴與多餘括號，保留自然俐落的曲名供大腦語音輸出"""
    if not raw_title:
        return ""
    t = str(raw_title)
    t = re.sub(r'\.(?:mid|midi)$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'[\(\[\{]\s*(?:Sheet Music Boss|Synthesia|MIDI|Piano Tutorial|Official|Original|Cover|4K|1080P|HD|Audio|Piano|midi piano changed|HQ|Remix)\s*[\)\]\}]', '', t, flags=re.IGNORECASE)
    t = re.sub(r'^\[([^\]]+)\]', r'\1', t).strip()
    t = re.sub(r'[-\s]*(?:midi piano changed|midi changed|midi version|piano version|midi|synthesia)\s*$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'[\s\-_]+$', '', t)
    t = re.sub(r'^[\s\-_]+', '', t)
    t = re.sub(r'\s{2,}', ' ', t).strip()
    t = t.replace('[', '').replace(']', '')
    return t or raw_title

async def generate_dynamic_piano_chatter(song_title: str, target: str = "dad", requester_name: str = "老爸", is_radio: bool = True) -> str:
    """由 AI 大腦即時自主動態生成過場/切歌/彈琴台詞 (支援對象感知，100% 自由意志決定說話或安靜沉醉，零固定罐頭句與數學機率)"""
    try:
        user_prof = await get_user_profile()
        c_name = user_prof.get("custom_name", DEFAULT_USER_TITLE)
        song_title = clean_song_title_for_speech(song_title)
        
        # 🛑 觀眾頻道絕對嚴禁稱呼為「老爸」
        if target == "audience" and requester_name in ["老爸", "老爸（主播）", ""]:
            requester_name = "大家"
        
        if is_radio:
            if target == "audience":
                mode_desc = f"在直播間電台模式下隨機接續下一首《{song_title}》為大家演奏"
                audience_prompt = "直播間的觀眾與大家"
            else:
                mode_desc = f"在鋼琴電台模式下隨機接續下一首《{song_title}》"
                audience_prompt = f"老爸（{c_name}）"
        else:
            if target == "audience":
                mode_desc = f"為觀眾【{requester_name}】演奏點播的《{song_title}》"
                audience_prompt = f"點歌的觀眾【{requester_name}】以及直播間的大家"
            else:
                mode_desc = f"為老爸彈奏《{song_title}》"
                audience_prompt = f"老爸（{c_name}）"

        prompt = f"""妳是 7L，正坐在 88 鍵鋼琴前彈奏鋼琴。
妳現在正準備{mode_desc}。
【自由意志決定】：
妳可以自由決定要不要開口對【{audience_prompt}】隨興說一句話（例如發表對這首曲子的感受、即興搭話、或向對方致意），或者妳也可以選擇「安靜專注沉醉彈奏、不開口說話」。
- 若妳想說話：請以妳自然、隨性真人的語氣，直接輸出妳要說的簡短一句話（10~25字以內，嚴禁任何死板套話，嚴禁 Emoji，注意妳說話的對象是{audience_prompt}）。
- 若妳現在想安靜彈琴、不說話：請只輸出 `[SILENCE]`。
直接輸出妳的決定："""
        
        if GEMINI_KEYS:
            target_k_idx = get_pingpong_alternating_index(len(GEMINI_KEYS), CURRENT_GEMINI_KEY_STEP)
            client = genai.Client(api_key=GEMINI_KEYS[target_k_idx])
            resp = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.9,
                        max_output_tokens=60
                    )
                ),
                timeout=1.8
            )
            if resp.text:
                txt = resp.text.strip()
                log_print(f"🤖 原始大腦輸出: {txt} (⚡ 鋼琴過場/3.5-flash-lite)")
                if "[SILENCE]" in txt or "[SKIP]" in txt or "[QUIET]" in txt:
                    return ""
                clean = re.sub(r'\[[A-Z_]+(?::\s*[^\]]+)?\]', '', txt).strip(' "\'「」\n\r')
                return clean
    except Exception:
        pass
    return ""

async def play_piano_worker(song_title: str, sheet_text: str, bpm: int, mode: str, midi_file: str = None, session_id: int = 0):
    """背景鋼琴演奏與 Live2D 姿態連動協程 (自動喚出視覺化 88 鍵瀑布流視窗並支援點播隊列與連續隨機電台自動接續)"""
    global is_piano_active, current_piano_song_title, current_piano_process, current_ai_state, vc.GLOBAL_VTS, PIANO_SESSION_ID, IS_PIANO_AUTO_RADIO_MODE
    if session_id != PIANO_SESSION_ID:
        return
        
    try:
        is_piano_active = True
        current_piano_song_title = song_title
        current_ai_state = "PIANO"
        
        # 1. 走位到鋼琴位置
        await move_vts_spatial(target_pos="鋼琴旁", duration=1.2)
        
        # 🌟 溫柔等待：等待 7L 說完開場白 (例如「好喔，7L 這就為老爸演奏...」) 後再開始彈奏，絕不搶先發聲
        speech_wait_start = time.time()
        while time.time() - speech_wait_start < 10.0:
            if session_id != PIANO_SESSION_ID or not is_piano_active:
                return
            is_speaking = False
            try:
                is_speaking = pygame.mixer.music.get_busy() or not speech_queue.empty() or current_ai_state == "TALKING"
            except Exception:
                pass
            if not is_speaking and time.time() - speech_wait_start > 0.6:
                break
            await asyncio.sleep(0.15)

        # 就位沉靜片刻 (0.3 秒準備彈奏)
        await asyncio.sleep(0.3)

        if session_id != PIANO_SESSION_ID or not is_piano_active:
            return
            
        # 2. 切換表情
        if vc.GLOBAL_VTS:
            await set_vts_expression(vc.GLOBAL_VTS, "星星眼")
            
        # 3. 循環播放當前曲目、待播隊列與無限隨機電台
        while session_id == PIANO_SESSION_ID and is_piano_active:
            await asyncio.to_thread(update_subtitle, f"🎹 [7L 正在演奏鋼琴] 《{song_title}》")
            
            # 4. 自動喚出 88 鍵視覺化瀑布流鋼琴介面並進行古典演奏 (支援多軌同時並發，視窗常駐不重開、無縫切歌)
            if midi_file and ("|" in midi_file or os.path.exists(midi_file)):
                if "|" in midi_file:
                    sub_paths = [p.strip() for p in midi_file.split("|") if os.path.exists(p.strip())]
                    raw_dur = max([get_midi_file_duration(p) for p in sub_paths], default=120.0)
                    tracks_payload = [{"title": os.path.basename(p).replace(".mid", "").replace(".MID", ""), "midi_path": p} for p in sub_paths]
                else:
                    sub_paths = [midi_file]
                    raw_dur = get_midi_file_duration(midi_file)
                    tracks_payload = [{"title": song_title, "midi_path": midi_file}]
                    
                song_dur = (raw_dur / GLOBAL_PIANO_SPEED) if GLOBAL_PIANO_SPEED > 0 else raw_dur
                
                # 🌟 若鋼琴視窗已經在桌面上運行 ➔ 直接發送 IPC 指令無縫切換曲目，絕不關閉或重開視窗！
                if is_piano_window_alive():
                    if len(tracks_payload) > 1:
                        log_print(f"🎹 [鋼琴舞台] 88 鍵鋼琴視窗已在桌面上，多軌並發演奏: 《{song_title}》 (原時長: {raw_dur:.1f}s | 倍速: {GLOBAL_PIANO_SPEED}x ➔ 實際時長: {song_dur:.1f}s)")
                        send_piano_ipc_command({
                            "cmd": "play_simultaneous",
                            "tracks": tracks_payload,
                            "volume": GLOBAL_PIANO_VOLUME,
                            "speed": GLOBAL_PIANO_SPEED
                        })
                    else:
                        log_print(f"🎹 [鋼琴舞台] 88 鍵鋼琴視窗已在桌面上，無縫切換曲目: 《{song_title}》 (原時長: {raw_dur:.1f}s | 倍速: {GLOBAL_PIANO_SPEED}x ➔ 實際時長: {song_dur:.1f}s)")
                        send_piano_ipc_command({
                            "cmd": "play",
                            "title": song_title,
                            "midi_path": midi_file,
                            "volume": GLOBAL_PIANO_VOLUME,
                            "speed": GLOBAL_PIANO_SPEED
                        })
                else:
                    # 鋼琴視窗尚未開啟 ➔ 啟動新視窗
                    log_print(f"🎹 [鋼琴舞台] 啟動 88 鍵瀑布流鋼琴視覺化視窗: 《{song_title}》 (實際時長: {song_dur:.1f}s | 倍速: {GLOBAL_PIANO_SPEED}x)")
                    piano_cmd = [
                        sys.executable, 
                        "test_virtual_piano.py", 
                        "--multi-midi" if len(sub_paths) > 1 else "--midi", midi_file, 
                        "--title", song_title,
                        "--volume", str(GLOBAL_PIANO_VOLUME),
                        "--speed", str(GLOBAL_PIANO_SPEED),
                        "--ndi"
                    ]
                    current_piano_process = subprocess.Popen(piano_cmd)
                
                # 🎹 即時鋼琴狀態驅動等待迴圈（以 UDP 即時播放狀態為第一優先，時間為極端斷線保底）
                song_start_time = time.time()
                has_started_playing = False
                
                while session_id == PIANO_SESSION_ID and is_piano_active:
                    elapsed = time.time() - song_start_time
                    
                    # 1. 優先檢查鋼琴視窗的即時 UDP 播放狀態 (來自 test_virtual_piano.py Port 39281)
                    if is_piano_window_alive():
                        rt_playing = GLOBAL_PIANO_REALTIME_STATE.get("is_playing", False)
                        rt_event = GLOBAL_PIANO_REALTIME_STATE.get("event", "")
                        
                        if rt_playing:
                            has_started_playing = True
                            
                        # 若已開彈超過 1.5 秒且收到結束訊號 (song_finished 或 is_playing 轉為 False)
                        if has_started_playing and elapsed >= 1.5:
                            if rt_event == "song_finished" or not rt_playing:
                                log_print(f"🎹 [鋼琴即時狀態] 接收到鋼琴視窗播放完畢訊號 (event={rt_event})，立即觸發無縫接續下一首！")
                                break
                    
                    # 2. 視窗行程結束檢測
                    if current_piano_process and current_piano_process.poll() is not None:
                        break
                        
                    # 3. 極端異常斷線保底（超過預估時長 + 3.0 秒仍無回應）
                    if elapsed >= song_dur + 3.0:
                        log_print(f"🎹 [鋼琴時長保底] 達到曲目預估演奏時長 ({song_dur:.1f}s)，觸發接續。")
                        break
                        
                    await asyncio.sleep(0.15)
            else:
                # 5. 文字樂譜備用解析演奏 (倍速縮放 BPM)
                scaled_bpm = int(bpm * GLOBAL_PIANO_SPEED)
                tokens = parse_vp_sheet(sheet_text, base_bpm=scaled_bpm, note_mode=mode)
                log_print(f"🎹 [鋼琴舞台] 開始演奏文字譜《{song_title}》 (共 {len(tokens)} 音符/拍子, BPM: {scaled_bpm} | 倍速: {GLOBAL_PIANO_SPEED}x)")
                
                for token_type, payload, duration in tokens:
                    if session_id != PIANO_SESSION_ID or not is_piano_active: break
                    if token_type == 'note':
                        play_piano_note(payload)
                        await asyncio.to_thread(precise_sleep, duration)
                    elif token_type == 'chord':
                        play_piano_note(payload)
                        await asyncio.to_thread(precise_sleep, duration)
                    elif token_type == 'rest':
                        await asyncio.to_thread(precise_sleep, duration)
            
            # 🌟 演奏完畢後的接續邏輯：
            if session_id != PIANO_SESSION_ID or not is_piano_active:
                break

            # 🎯 優先檢查 1：是否有觀眾/老爸預約點播的曲目！（無縫插播優先於隨機電台）
            if PIANO_REQUEST_QUEUE:
                await asyncio.sleep(1.2)  # 曲目間自然換氣微間隔
                if session_id != PIANO_SESSION_ID or not is_piano_active:
                    break
                req_item = PIANO_REQUEST_QUEUE.popleft()
                song_title = clean_song_title_for_speech(req_item.get("title", ""))
                midi_file = req_item.get("midi_path", "")
                req_target = req_item.get("target") or ("audience" if CURRENT_SPEAKING_TARGET == "audience" else "dad")
                req_user = req_item.get("requester") or ("大家" if req_target == "audience" else "老爸")
                if req_target == "audience" and req_user in ["老爸", "老爸（主播）", ""]:
                    req_user = "直播間觀眾"
                sheet_text = ""
                current_piano_song_title = song_title
                current_piano_midi_file = midi_file
                try:
                    append_to_unified_memory(speaker="系統", target="所有人", content=f"鋼琴上一首演奏完畢，無縫接續為【{req_user}】演奏《{song_title}》", role="system", source="piano")
                except Exception:
                    pass
                log_print(f"🎹 [點歌無縫接續] 當前曲目結束，立即優先為【{req_user}】演奏點播曲目: 《{song_title}》！")
                ai_chatter = await generate_dynamic_piano_chatter(song_title, target=req_target, requester_name=req_user, is_radio=IS_PIANO_AUTO_RADIO_MODE)
                if ai_chatter:
                    log_print(f"💬 [鋼琴 AI 自由意志發話 ({req_target})]: {ai_chatter}")
                    await speech_queue.put({"text": ai_chatter, "target": req_target})
                else:
                    log_print(f"🎹 [鋼琴 AI 自由意志] 7L 選擇保持專注安靜、無縫沉醉演奏《{song_title}》。")
                continue

            elif IS_PIANO_AUTO_RADIO_MODE:
                # 檢查 2：連續隨機電台模式：隊列空時，自動從種子曲庫/本機/BitMidi 隨機選曲並無縫接續演奏！
                await asyncio.sleep(1.2)  # 曲目間自然換氣微間隔
                if session_id != PIANO_SESSION_ID or not is_piano_active:
                    break
                
                # 隨機挑選一首不同於當前曲目的種子曲目（100% 動態從本地資料夾選取）
                local_seeds = get_local_piano_seeds()
                candidates = [s for s in local_seeds if s.lower() not in song_title.lower()]
                seed_song = random.choice(candidates if candidates else local_seeds)
                
                log_print(f"📻 [鋼琴電台] 正在自動隨機接續下一首：《{seed_song}》...")
                local_p, matched_title = await resolve_local_midi_file(seed_song)
                if not local_p:
                    # 本機沒有時，向 BitMidi 雲端搜尋並自動下載！
                    log_print(f"🌐 [鋼琴電台] 本機無《{seed_song}》，正在從 BitMidi 雲端曲庫下載五線譜...")
                    dl_p = await asyncio.to_thread(bitmidi_engine.fetch_and_download_first_match, seed_song, MIDI_SHEETS_DIR)
                    if not dl_p:
                        log_print(f"🎵 [鋼琴電台] BitMidi 無《{seed_song}》，改從 OnlineSequencer 搜尋...")
                        dl_p = await asyncio.to_thread(onlinesequencer_engine.fetch_and_download_first_match, seed_song, MIDI_SHEETS_DIR)
                    if dl_p and os.path.exists(dl_p):
                        local_p = dl_p
                        matched_title = os.path.basename(dl_p).replace('.mid', '').replace('.MID', '')
                        
                if local_p and os.path.exists(local_p):
                    song_title = matched_title or seed_song
                    midi_file = local_p
                    sheet_text = ""
                    current_piano_song_title = song_title
                    log_print(f"🎹 [鋼琴電台] 成功載入！開始連續演奏下一首名曲：《{song_title}》！")
                    # 🌟 100% 由 7L AI 自由意志自主決定是否開口搭話或專心安靜演奏 (完全告別死板數學機率)
                    radio_target = "audience" if CURRENT_SPEAKING_TARGET == "audience" else "dad"
                    radio_user = "直播間觀眾與大家" if radio_target == "audience" else "老爸"
                    ai_chatter = await generate_dynamic_piano_chatter(song_title, target=radio_target, requester_name=radio_user, is_radio=True)
                    if ai_chatter:
                        log_print(f"💬 [電台 AI 自由意志發話 ({radio_target})]: {ai_chatter}")
                        await speech_queue.put({"text": ai_chatter, "target": radio_target})
                    else:
                        log_print(f"🎹 [電台 AI 自由意志] 7L 選擇保持專注安靜、無縫沉醉演奏《{song_title}》。")
                    continue
                else:
                    break
            else:
                # 🌟 彈完單曲且無待播曲目時：鋼琴與 7L 保持常駐就緒待命，【絕對不重複重開視窗或重播舊曲】！
                # 只有當老爸說「收起鋼琴 / 別彈了」或調用 stop_virtual_piano() 時才會作為獨立動作收起！
                finished_song = song_title
                current_piano_song_title = ""
                try:
                    append_to_unified_memory(speaker="系統", target="所有人", content=f"鋼琴《{finished_song}》演奏完畢，7L 坐在鋼琴前隨時待命", role="system", source="piano")
                except Exception:
                    pass
                log_print(f"🎹 [鋼琴舞台] 《{finished_song}》演奏完畢！7L 與鋼琴視窗保持常駐就緒待命（等待下一首點歌或「收起鋼琴」指令）。")
                await asyncio.to_thread(update_subtitle, f"🎹 [7L 鋼琴就緒] 《{finished_song}》演奏完畢～隨時可點歌或說「收起鋼琴」")
                
                # 常駐等待老爸或觀眾點播新曲或下達收起鋼琴指令
                has_next = False
                while session_id == PIANO_SESSION_ID and is_piano_active:
                    if IS_PIANO_AUTO_RADIO_MODE:
                        has_next = True
                        break
                    await asyncio.sleep(0.3)
                
                if has_next:
                    continue
                else:
                    break
                    
    except asyncio.CancelledError:
        pass
    except Exception as e:
        log_print(f"❌ [鋼琴演奏異常]: {e}")
    finally:
        if session_id == PIANO_SESSION_ID:
            is_piano_active = False
            current_piano_song_title = ""
            current_piano_midi_file = ""
            IS_PIANO_AUTO_RADIO_MODE = False
            if current_piano_process and current_piano_process.poll() is None:
                try:
                    current_piano_process.terminate()
                except Exception:
                    pass
                current_piano_process = None
            if SOUND_ENGINE:
                SOUND_ENGINE.all_notes_off()
            if vc.GLOBAL_VTS:
                await set_vts_expression(vc.GLOBAL_VTS, "_RESET_")
            if current_ai_state == "PIANO":
                current_ai_state = "IDLE"
            await asyncio.to_thread(update_subtitle, "")
            log_print(f"🎹 [鋼琴舞台] 鋼琴演奏舞台結束，回到常規姿態！")

import bitmidi_engine
import onlinesequencer_engine
import pianist_midi_engine

async def play_virtual_piano(song_name: str = "", custom_sheet: str = "", auto_radio_mode: bool = False, midi_file: str = "", force_online: bool = False, requester_name: str = "", target: str = "") -> str:
    """讓 7L 在大家面前彈奏 88 鍵鋼琴名曲（支援單曲、多曲同時並發合奏、立即秒切新曲與無限隨機連續電台模式）。
    
    Args:
        song_name: 想點播的鋼琴曲名稱、作曲家或動漫名（如：'月光'、'鐘'、'La Campanella'、'愛之夢'、'冬風'、'少女的祈禱'、'幻想即興曲'、'卡農'、'給愛麗絲'、'神隱少女'）。支援多曲同時點播（如：'冬風、月光、鐘' 或 '冬風 x 月光'）。
        custom_sheet: (可選) 自訂備用樂譜。
        auto_radio_mode: (可選) 當說「接著一直隨便彈吧」、「隨便彈」、「隨機一直彈」、「連續彈」、「開啟鋼琴電台」時設為 True，進入無限連續隨機演奏模式，每首彈完自動隨機下載並接續彈奏下一首！
        midi_file: (可選) 直接指定的本機 MIDI 檔案完整路徑。
        force_online: (可選) 當指定「用 YouTube 查」、「youtuber 查」、「線上搜」、「yt 查」時設為 True，強制跳過本地樂譜直接向 YouTube/線上即時抓取！
        requester_name: (可選) 點播者稱呼（如：'老爸'、觀眾暱稱等）。
        target: (可選) 對象通道 ('dad' 或 'audience')。
    """
    global current_piano_task, PIANO_SESSION_ID, is_piano_active, current_piano_song_title, current_piano_midi_file, IS_PIANO_AUTO_RADIO_MODE, LAST_PIANO_PLAY_START_TIME, CURRENT_SPEAKING_TARGET
    LAST_PIANO_PLAY_START_TIME = time.time()
    init_piano_synthesizer()

    if not target:
        target = "audience" if CURRENT_SPEAKING_TARGET == "audience" else "dad"
    if not requester_name:
        requester_name = "大家" if target == "audience" else "老爸"
    
    target_title = song_name if song_name else "鋼琴名曲"
    target_midi = midi_file if (midi_file and os.path.exists(midi_file)) else None
    save_persisted_piano_state(True, target_title, True)
    
    clean_q = song_name.strip() if song_name else ""
    
    # 🎬 【YouTube / 線上指定檢測】：若明確要求 YouTube / 線上查 ➔ 100% 絕對跳過本地匹配，強制走線上抓譜！
    is_explicit_yt = (
        force_online
        or any(k in clean_q.lower() for k in ["youtube", "youtuber", "yt", "yt查", "yt搜", "線上查", "線上搜", "從yt", "從youtube", "去yt", "去youtube", "網路搜", "線上找", "指定youtube", "指定youtuber"])
    )
    
    if is_explicit_yt:
        clean_search_target = re.sub(r'^(?:youtuber|youtube|yt|從yt|從youtube|去yt|去youtube)\s*(?:查|搜|找|搜尋|下載)?\s*', '', clean_q, flags=re.IGNORECASE).strip()
        clean_search_target = re.sub(r'\s*(?:然後彈|來彈|彈出來|放出來|彈一下|彈|播放|放)+$', '', clean_search_target, flags=re.IGNORECASE).strip()
        if not clean_search_target:
            clean_search_target = clean_q
            
        target_title = clean_search_target
        target_midi = None  # 100% 徹底清除本地 MIDI 指標，拒絕配對本地！
        log_print(f"🎬 [YouTube/線上專屬指定] 收到指定 YouTube 查譜《{clean_search_target}》，100% 跳過本地樂譜，強制線上搜尋並秒切演奏！")

    # 🧠 100% 交由 Gemini 高智商大腦判定意圖（完全零寫死關鍵字，交由 AI 自主分析語意與精準分流）
    ai_intent = {}
    available_files = [os.path.basename(p) for p in glob.glob(os.path.join(MIDI_SHEETS_DIR, "*.mid"))]
    if clean_q and not is_explicit_yt and not target_midi:
        ai_intent = await resolve_piano_intent_by_ai(
            clean_q, 
            available_files,
            current_playing_title=current_piano_song_title,
            current_playing_file=current_piano_midi_file,
            is_direct_song_name=False
        )
        is_from_ai = ai_intent.get("_from_ai", False)
        is_song = ai_intent.get("is_song_request", False)
        action_type = ai_intent.get("action_type", "song_request" if is_song else "chat")

        # 🛑 若 Gemini 高智商大腦判定非點歌意圖（指令、視窗操作、問候閒聊等），100% 依據 AI 判斷執行精準分流：
        if is_from_ai and not is_song:
            if action_type == "open_piano":
                log_print(f"🎹 [Gemini 意圖分流] 判定《{clean_q}》為拿出/打開鋼琴指令，立即執行 open_virtual_piano()！")
                await open_virtual_piano()
                return "（系統回報：已交由 Gemini 識別為打開鋼琴指令，已為您拿出 88 鍵鋼琴待命）"
            elif action_type == "stop_piano":
                log_print(f"🛑 [Gemini 意圖分流] 判定《{clean_q}》為收起/停止彈琴指令，立即執行 stop_virtual_piano()！")
                await stop_virtual_piano()
                return "（系統回報：已交由 Gemini 識別為停止/收起鋼琴指令，已停止演奏並收起鋼琴）"
            elif action_type == "window_status":
                if is_piano_window_alive():
                    bring_piano_window_to_front()
                    log_print(f"🖥️ [Gemini 意圖分流] 判定《{clean_q}》為詢問鋼琴視窗狀態，已將視窗置頂最前端！")
                    return "（系統回報：已交由 Gemini 識別為鋼琴視窗狀態對話，視窗已置頂顯示，不執行新曲彈奏）"
                else:
                    log_print(f"🖥️ [Gemini 意圖分流] 判定《{clean_q}》為詢問鋼琴視窗狀態（目前視窗未開啟）！")
                    return "（系統回報：已交由 Gemini 識別為詢問鋼琴視窗，目前鋼琴尚未開啟）"
            else:
                log_print(f"🛑 [Gemini 意圖分流] 判定《{clean_q}》非點歌意圖（為日常閒聊、問候或非音樂指令），安全取消彈琴！")
                return "（系統回報：已交由 Gemini 識別為日常對話或非點歌發言，不執行彈琴，直接進行口頭對話）"

        # 罕見離線/API全失效時的純數字/標點極簡兜底保護
        if not is_from_ai and (clean_q.isdigit() or re.fullmatch(r'[\d\s.,!?:;~～\-_+]+', clean_q)):
            log_print(f"🛑 [離線兜底防護] 《{clean_q}》為純數字/符號，取消彈琴！")
            return "（系統回報：純數字或標點非歌名，取消彈琴）"

        if ai_intent.get("song_title"):
            target_title = ai_intent.get("song_title")
        if ai_intent.get("matched_files"):
            target_midi = os.path.join(MIDI_SHEETS_DIR, ai_intent["matched_files"][0])

    is_switch_version = ai_intent.get("is_switch_version", False)
    is_replay_command = ai_intent.get("is_replay", False)

    # 🛑 演奏中排隊接續機制：若目前已有曲目正在演奏（非強制線上指定且非重播指令且非Gemini判定換版本指令）
    if not is_explicit_yt and is_piano_active and current_piano_song_title and is_piano_window_alive() and not is_switch_version:
        bring_piano_window_to_front()
        clean_q_lower = clean_q.lower()
        current_title_lower = current_piano_song_title.lower()
        is_same_title = bool(clean_q and (clean_q_lower == current_title_lower or (len(clean_q_lower) >= 3 and clean_q_lower in current_title_lower)))
        if not is_replay_command and not is_same_title and clean_q:
            clean_target_song = clean_song_title_for_speech(ai_intent.get("song_title") or clean_q)
            
            # 防重複排隊檢查：若隊列中已預約此曲，不重複加入隊列
            if any(it.get("title") == clean_target_song or (clean_target_song.lower() in it.get("title", "").lower()) for it in PIANO_REQUEST_QUEUE):
                log_print(f"🎵 [鋼琴點歌排隊] 《{clean_target_song}》已在待播隊列中，不重複排入。")
                return f"（系統提示：已為{requester_name}將《{clean_target_song}》排入下一首待播中！）"
            
            # 1. 優先查本地精準同名或 Gemini 已匹配檔案
            norm_k = clean_target_song.lower().strip()
            exact_local = AUTHENTIC_MIDI_MAP.get(norm_k)
            req_midi = exact_local if (exact_local and os.path.exists(exact_local)) else None
            req_title = clean_song_title_for_speech(os.path.splitext(os.path.basename(exact_local))[0] if req_midi else clean_target_song)
            
            if not req_midi and ai_intent.get("matched_files"):
                cand_f = os.path.join(MIDI_SHEETS_DIR, ai_intent["matched_files"][0])
                if os.path.exists(cand_f):
                    req_midi = cand_f
                    req_title = clean_song_title_for_speech(ai_intent.get("song_title") or os.path.splitext(ai_intent["matched_files"][0])[0])

            if not req_midi:
                local_p, matched_t = await resolve_local_midi_file(clean_target_song)
                if local_p:
                    req_midi = local_p
                    req_title = clean_song_title_for_speech(matched_t or clean_target_song)
                    
            if req_midi and os.path.exists(req_midi):
                PIANO_REQUEST_QUEUE.append({"title": req_title, "midi_path": req_midi, "requester": requester_name, "target": target})
                log_print(f"🎵 [鋼琴點歌排隊] 成功預約《{req_title}》（來自 {requester_name}）排入下一首！（目前待播隊列中共 {len(PIANO_REQUEST_QUEUE)} 首）")
                return f"（系統提示：已成功為{requester_name}將《{req_title}》排入下一首待播！請用自然口語告知對方：『我現在正在彈《{clean_song_title_for_speech(current_piano_song_title)}》喔～等我這首彈完，下一首就幫你彈《{req_title}》！』）"
            else:
                # 🚀 異步背景預載並排入隊列，不阻塞工具調用回傳！
                search_q = ai_intent.get("search_online_query") or clean_target_song
                async def preload_and_queue_worker(song_str: str, req_n: str, req_t: str):
                    log_print(f"🌐 [點歌排隊線上搜譜] 正在異步背景搜尋預載《{song_str}》...")
                    dl_p = await asyncio.to_thread(pianist_midi_engine.fetch_and_download_pianist_match, song_str, MIDI_SHEETS_DIR)
                    if dl_p and os.path.exists(dl_p):
                        t_name = clean_song_title_for_speech(os.path.splitext(os.path.basename(dl_p))[0])
                        save_midi_catalog_entry(song_str, dl_p)
                        save_midi_catalog_entry(t_name, dl_p)
                        PIANO_REQUEST_QUEUE.append({"title": t_name, "midi_path": dl_p, "requester": req_n, "target": req_t})
                        log_print(f"🎵 [鋼琴點歌排隊] 成功預約《{t_name}》（來自 {req_n}）排入下一首！（目前待播隊列中共 {len(PIANO_REQUEST_QUEUE)} 首）")
                asyncio.create_task(preload_and_queue_worker(search_q, requester_name, target))
                return f"（系統提示：已成功為{requester_name}將《{clean_target_song}》排入下一首待播！請用自然口語告知對方：『我現在正在彈《{clean_song_title_for_speech(current_piano_song_title)}》喔～等我這首彈完，下一首就幫你彈《{clean_target_song}》！』）"
        elif is_same_title and not is_replay_command:
            display_name = current_piano_song_title
            log_print(f"🎹 [7L 鋼琴曲庫] 7L 目前正在演奏《{display_name}》，保持沉醉演奏狀態，不重頭重播。")
            return "[EXPRESSION: 星星眼]"

    if not target_midi and not is_explicit_yt:
        # 1. 檢查是否為無限電台模式
        is_radio_req = auto_radio_mode or not clean_q or ai_intent.get("is_random", False)
        if is_radio_req:
            IS_PIANO_AUTO_RADIO_MODE = True
            log_print("📻 [鋼琴電台] 啟動無限連續隨機電台模式！")
        else:
            IS_PIANO_AUTO_RADIO_MODE = False
            # 2. 僅接受本地精確同名或別名比對
            norm_k = clean_q.lower().strip()
            exact_local_match = AUTHENTIC_MIDI_MAP.get(norm_k)
            if exact_local_match and os.path.exists(exact_local_match):
                target_midi = exact_local_match
                target_title = os.path.splitext(os.path.basename(exact_local_match))[0]
                log_print(f"🎹 [本地精準命中] 命中已收錄曲目: 《{target_title}》 ({target_midi})")
            else:
                local_p, matched_t = await resolve_local_midi_file(clean_q)
                if local_p and os.path.exists(local_p):
                    target_midi = local_p
                    target_title = matched_t or os.path.splitext(os.path.basename(local_p))[0]
                    log_print(f"🎹 [本地智慧命中] 命中曲目: 《{target_title}》 ({target_midi})")

    if not target_midi and not is_explicit_yt:
        if not clean_q or IS_PIANO_AUTO_RADIO_MODE:
            preset_names = get_local_piano_seeds()
            if preset_names:
                target_title = random.choice(preset_names)
                target_midi, matched_title = await resolve_local_midi_file(target_title)
                if matched_title:
                    target_title = matched_title

    # 檢查鋼琴真實運行狀態 (避免背景任務已結束但狀態標記殘留)
    if is_piano_active and current_piano_task is not None and current_piano_task.done() and not is_piano_window_alive():
        is_piano_active = False
        current_piano_song_title = ""
        current_piano_midi_file = ""

    # 🛑 演奏中不插歌/不切歌保護：若當前已經在演奏某首曲目且未收起鋼琴（且非強制線上指定）
    if not is_explicit_yt and is_piano_active and current_piano_song_title:
        clean_q_lower = clean_q.lower() if clean_q else ""
        current_title_lower = current_piano_song_title.lower() if current_piano_song_title else ""
        same_midi = bool(target_midi and current_piano_midi_file and os.path.abspath(target_midi) == os.path.abspath(current_piano_midi_file))
        same_title = bool(clean_q and (clean_q_lower == current_title_lower or (len(clean_q_lower) >= 3 and clean_q_lower in current_title_lower)))
        same_target = bool(target_title and current_title_lower and target_title.lower() == current_title_lower)
        
        # 🌟 若 Gemini 判定為換版本 (is_switch_version) 且挑選出了不同檔案 ➔ 直接放行無縫切換！
        if is_switch_version and target_midi and (not current_piano_midi_file or os.path.abspath(target_midi) != os.path.abspath(current_piano_midi_file)):
            log_print(f"🎹 [Gemini 智能版本切換] Gemini 判定切換至不同版本: 《{target_title}》 ({os.path.basename(target_midi)})")
        elif (same_midi or same_title or same_target) and not is_replay_command:
            display_name = current_piano_song_title or target_title
            log_print(f"🎹 [7L 鋼琴曲庫] 7L 目前正在演奏《{display_name}》，保持沉醉演奏狀態，不重頭重播。")
            return "[EXPRESSION: 星星眼]"
        elif not is_replay_command and not is_switch_version:
            display_name = current_piano_song_title
            log_print(f"🛑 [鋼琴防插歌保護] 7L 目前正專注演奏《{display_name}》，拒絕中途插歌/切歌《{target_title}》！")
            return f"（系統提示：妳目前正坐在鋼琴前專心為大家彈奏《{display_name}》。請不要中途切歌或插歌，請用自然、隨性的口語直接告知對方：『我現在正在彈《{display_name}》呢～等我這首彈完再點歌喔！』）"

    # ⚡ 若已有本機 MIDI 樂譜 ➔ 100% 絕對即刻開彈！
    if target_midi and os.path.exists(target_midi):
        PIANO_SESSION_ID += 1
        session_id = PIANO_SESSION_ID
        is_piano_active = True
        current_piano_song_title = target_title
        current_piano_midi_file = target_midi
        try:
            append_to_unified_memory(speaker="系統", target="所有人", content=f"鋼琴開始演奏《{target_title}》", role="system", source="piano")
        except Exception:
            pass
        
        if current_piano_task and not current_piano_task.done():
            current_piano_task.cancel()
            
        current_piano_task = asyncio.create_task(
            play_piano_worker(
                song_title=target_title,
                sheet_text=custom_sheet or "",
                bpm=180,
                mode="16th",
                midi_file=target_midi,
                session_id=session_id
            )
        )
        return "[EXPRESSION: 星星眼]"

    # 🌐 若指定 YouTube 或本地無樂譜 ➔ 啟動非阻塞背景線上抓譜並接續開彈協程
    PIANO_SESSION_ID += 1
    session_id = PIANO_SESSION_ID
    is_piano_active = True
    final_search_query = clean_search_target if is_explicit_yt else (clean_q or "鋼琴名曲")
    current_piano_song_title = final_search_query
    current_piano_midi_file = ""
    try:
        append_to_unified_memory(speaker="系統", target="所有人", content=f"鋼琴準備線上搜尋演奏《{final_search_query}》", role="system", source="piano")
    except Exception:
        pass
    
    if current_piano_task and not current_piano_task.done():
        current_piano_task.cancel()

    async def async_fetch_and_play_worker(song_q: str, sid: int, c_sheet: str):
        global current_piano_song_title, current_piano_midi_file, is_piano_active
        log_print(f"🌐 [智慧曲庫搜尋] 正在線上/YouTube 搜尋《{song_q}》...")
        await move_vts_spatial(target_pos="鋼琴旁", duration=1.2)
        
        dl_path = await asyncio.to_thread(pianist_midi_engine.fetch_and_download_pianist_match, song_q, MIDI_SHEETS_DIR)
        
        if sid != PIANO_SESSION_ID or not is_piano_active:
            log_print(f"🛑 [線上抓譜] 演奏已取消或切換至新曲目，終止本次抓譜接續。")
            return
            
        if dl_path and os.path.exists(dl_path):
            t_title = os.path.splitext(os.path.basename(dl_path))[0]
            log_print(f"✅ [線上抓譜成功] 成功獲取: 《{t_title}》，立即啟動 88 鍵演奏！")
            save_midi_catalog_entry(song_q, dl_path)
            save_midi_catalog_entry(t_title, dl_path)
            current_piano_song_title = t_title
            current_piano_midi_file = dl_path
            await play_piano_worker(
                song_title=t_title,
                sheet_text=c_sheet or "",
                bpm=180,
                mode="16th",
                midi_file=dl_path,
                session_id=sid
            )
        else:
            log_print(f"⚠️ [7L 鋼琴曲庫] 未找到《{song_q}》的樂譜/演奏音訊。")
            is_piano_active = False
            current_piano_song_title = ""
            current_piano_midi_file = ""
            await asyncio.to_thread(update_subtitle, f"⚠️ [樂譜庫查無結果] 未找到《{song_q}》的五線譜")

    asyncio.create_task(async_fetch_and_play_worker(final_search_query, session_id, custom_sheet or ""))
    return "[EXPRESSION: 星星眼]"

def merge_two_midi_files(path1: str, path2: str, title1: str, title2: str) -> Tuple[str, str]:
    """將兩首鋼琴 MIDI 檔案深度融合，生成 88 鍵雙曲極限狂暴合奏 (Mashup) 樂譜"""
    try:
        import mido
        mid1 = mido.MidiFile(path1, clip=True)
        mid2 = mido.MidiFile(path2, clip=True)
        
        tpb = 480
        target_tempo = 400000  # 150 BPM 高能狂暴速度
        
        def extract_timed_events(mid_file):
            file_tpb = mid_file.ticks_per_beat
            events = []
            for track in mid_file.tracks:
                cur_tempo = 500000
                abs_sec = 0.0
                for msg in track:
                    if msg.time > 0:
                        abs_sec += mido.tick2second(msg.time, file_tpb, cur_tempo)
                    if msg.is_meta and msg.type == 'set_tempo':
                        cur_tempo = msg.tempo
                    if not msg.is_meta and msg.type in ['note_on', 'note_off', 'control_change', 'pitchwheel']:
                        events.append((abs_sec, msg.copy()))
            return events

        events1 = extract_timed_events(mid1)
        events2 = extract_timed_events(mid2)
        all_events = events1 + events2
        
        def event_sort_key(ev):
            t, m = ev
            priority = 0 if m.type == 'note_off' or (m.type == 'note_on' and m.velocity == 0) else 1
            return (t, priority)
            
        all_events.sort(key=event_sort_key)
        
        new_mid = mido.MidiFile(type=1, ticks_per_beat=tpb)
        
        # Track 0: Tempo
        tempo_track = mido.MidiTrack()
        new_mid.tracks.append(tempo_track)
        tempo_track.append(mido.MetaMessage('track_name', name='Mashup Tempo', time=0))
        tempo_track.append(mido.MetaMessage('set_tempo', tempo=target_tempo, time=0))
        tempo_track.append(mido.MetaMessage('end_of_track', time=0))
        
        # Track 1: Merged Notes
        merged_track = mido.MidiTrack()
        new_mid.tracks.append(merged_track)
        merged_track.append(mido.MetaMessage('track_name', name='Mashup Piano Track', time=0))
        merged_track.append(mido.Message('program_change', channel=0, program=0, time=0))
        
        last_tick = 0
        for t_sec, msg in all_events:
            cur_tick = mido.second2tick(t_sec, tpb, target_tempo)
            if cur_tick < last_tick:
                cur_tick = last_tick
            delta_tick = cur_tick - last_tick
            msg.time = delta_tick
            msg.channel = 0
            merged_track.append(msg)
            last_tick = cur_tick
            
        merged_track.append(mido.MetaMessage('end_of_track', time=0))
        
        safe_t1 = re.sub(r'[^\w]', '', title1)[:10] or "song1"
        safe_t2 = re.sub(r'[^\w]', '', title2)[:10] or "song2"
        mashup_filename = f"Mashup_{safe_t1}_x_{safe_t2}_{abs(hash(title1+title2))%10000}.mid"
        out_path = os.path.abspath(os.path.join(MIDI_SHEETS_DIR, mashup_filename))
        new_mid.save(out_path)
        mashup_title = f"{title1} x {title2} (神仙打架 Mashup)"
        save_midi_catalog_entry(mashup_title, out_path)
        save_midi_catalog_entry(f"{title1} {title2}", out_path)
        save_midi_catalog_entry(f"{title1} x {title2}", out_path)
        save_midi_catalog_entry(f"{title1}+{title2}", out_path)
        log_print(f"🔥 [雙曲合體] 成功生成雙曲融合 MIDI: 《{mashup_title}》 (時長: {new_mid.length:.1f}s | 檔案: {out_path})")
        return out_path, mashup_title
    except Exception as e:
        log_print(f"❌ [雙曲融合失敗]: {e}")
        return path1, title1




def extract_multi_songs_from_text(text: str) -> List[str]:
    """從自然語言字串中解析出多首歌曲名稱 (支援 2首、3首、4首甚至更多曲目同時合奏)"""
    if not text:
        return []
    clean = re.sub(r'^(同時彈|同時|請|幫我|把)', '', text).strip()
    clean = re.sub(r'(雜在一起|混在一起|合體|合在一起|一起彈|同時彈|同時|合奏|[兩三四五六七八九十\d]+首|彈)+$', '', clean).strip()
    # 按照常見連接詞與符號切分
    parts = re.split(r'[\s,，、+＋xX＆&和跟與加混雜]|還有|以及', clean)
    songs = [p.strip(' ：:()（）[]【】"\'') for p in parts if p.strip(' ：:()（）[]【】"\'')]
    filtered = []
    for s in songs:
        if s and s not in ['首', '歌', '曲', '鋼琴曲', '名曲', '兩首', '三首', '四首', '五首', '六首', '七首', '八首', '九首', '十首'] and s not in filtered:
            filtered.append(s)
    return filtered

async def mashup_virtual_piano(*songs, song_name1: str = "", song_name2: str = "", song_names: Optional[Union[List[str], str]] = None, ) -> str:
    """同時並發演奏多首高難度鋼琴曲 (無數量限制，即時多軌多色瀑布流並發演奏，絕不需死板生成單一檔案)"""
    # 1. 整理收集所有傳入的曲目名稱
    all_targets = []
    if song_names:
        if isinstance(song_names, list):
            for s in song_names:
                all_targets.extend(extract_multi_songs_from_text(str(s)) if any(k in str(s) for k in [",", "，", "、", " ", "+", "x", "跟", "和"]) else [str(s).strip()])
        elif isinstance(song_names, str):
            all_targets.extend(extract_multi_songs_from_text(song_names))
            
    for s in songs:
        if isinstance(s, list):
            for item in s:
                all_targets.extend(extract_multi_songs_from_text(str(item)) if any(k in str(item) for k in [",", "，", "、", " ", "+", "x", "跟", "和"]) else [str(item).strip()])
        elif isinstance(s, str):
            parsed = extract_multi_songs_from_text(s)
            if len(parsed) > 1:
                all_targets.extend(parsed)
            elif s.strip():
                all_targets.append(s.strip())
                
    if song_name1 and song_name1.strip():
        parsed1 = extract_multi_songs_from_text(song_name1)
        if len(parsed1) > 1:
            all_targets.extend(parsed1)
        else:
            all_targets.append(song_name1.strip())
            
    if song_name2 and song_name2.strip():
        parsed2 = extract_multi_songs_from_text(song_name2)
        if len(parsed2) > 1:
            all_targets.extend(parsed2)
        else:
            all_targets.append(song_name2.strip())
                
    # 去除重複與空白
    unique_targets = []
    for t in all_targets:
        if t and t not in unique_targets:
            unique_targets.append(t)
            
    # 🌟 若指令包含「全部 / 所有 / 全彈 / all / 整個曲庫」
    if any(k in "".join(unique_targets) for k in ["全部", "所有", "全都", "全彈", "all", "ALL", "全曲", "整個曲庫"]):
        real_all = []
        if os.path.exists(MIDI_SHEETS_DIR):
            for f in sorted(os.listdir(MIDI_SHEETS_DIR)):
                if f.lower().endswith(('.mid', '.midi')) and not f.lower().startswith(('test_', 'temp_')):
                    real_all.append(f)
        if real_all:
            unique_targets = real_all
            
    if len(unique_targets) < 2:
        if len(unique_targets) == 1:
            t1 = unique_targets[0]
            t2 = "鐘" if "冬風" in t1 else "冬風"
            unique_targets = [t1, t2]
        else:
            unique_targets = ["冬風", "鐘"]
            
    # 2. 為每一首曲目解析本機 MIDI 或從 BitMidi 自動下載
    resolved_tracks = []
    for s_name in unique_targets:
        p, t = await resolve_local_midi_file(s_name)
        if not p:
            dl = await asyncio.to_thread(onlinesequencer_engine.fetch_and_download_first_match, s_name, MIDI_SHEETS_DIR)
            if not dl:
                log_print(f"🎵 [多軌合奏] OnlineSequencer 無《{s_name}》，改從 BitMidi 搜尋...")
                dl = await asyncio.to_thread(bitmidi_engine.fetch_and_download_first_match, s_name, MIDI_SHEETS_DIR)
            if dl and os.path.exists(dl):
                p, t = dl, os.path.basename(dl).replace('.mid', '').replace('.MID', '')
        if p and os.path.exists(p):
            resolved_tracks.append({"title": t or s_name, "midi_path": p})
            
    if not resolved_tracks:
        return "（系統回報：未找到合奏樂譜檔案）"
        
    titles_list = [f"《{tr['title']}》" for tr in resolved_tracks]
    titles_display = " ✕ ".join(titles_list)
    multi_path_str = "|".join([tr['midi_path'] for tr in resolved_tracks])
    
    # 3. 確保 7L 走位到鋼琴旁
    await move_vts_spatial(target_pos="鋼琴旁", duration=1.2)
    
    # 4. 啟動或透過 IPC 發送多音軌即時並發演奏指令 (真正多音軌同時執行，無數量限制！)
    global current_piano_task, PIANO_SESSION_ID, is_piano_active, current_piano_song_title, current_piano_midi_file, current_piano_process, current_ai_state
    PIANO_SESSION_ID += 1
    session_id = PIANO_SESSION_ID
    is_piano_active = True
    current_piano_song_title = titles_display
    current_piano_midi_file = multi_path_str
    
    if is_piano_window_alive():
        log_print(f"🔥 [神仙打架多軌並發] 88 鍵鋼琴視窗已在桌面上，立即置頂並發送多軌並發指令: {titles_display} (共 {len(resolved_tracks)} 首曲目同時演奏)")
        bring_piano_window_to_front()
        send_piano_ipc_command({
            "cmd": "play_simultaneous",
            "tracks": resolved_tracks,
            "volume": GLOBAL_PIANO_VOLUME,
            "speed": GLOBAL_PIANO_SPEED
        })
    else:
        log_print(f"🔥 [神仙打架多軌並發] 啟動 88 鍵多軌並發鋼琴視窗: {titles_display} (共 {len(resolved_tracks)} 首曲目同時演奏)")
        piano_cmd = [
            sys.executable,
            "test_virtual_piano.py",
            "--multi-midi", multi_path_str,
            "--title", titles_display,
            "--volume", str(GLOBAL_PIANO_VOLUME),
            "--speed", str(GLOBAL_PIANO_SPEED),
            "--ndi"
        ]
        current_piano_process = subprocess.Popen(piano_cmd)
        
    if current_ai_state != "PIANO":
        current_ai_state = "PIANO"
        if vc.GLOBAL_VTS:
            asyncio.create_task(set_vts_expression(vc.GLOBAL_VTS, "星星眼"))
            
    await asyncio.to_thread(update_subtitle, f"🎹 [7L 神仙打架合奏] {titles_display}")
    
    return "[EXPRESSION: 星星眼]"

async def insert_virtual_piano(song_name: str = "") -> str:
    """🛑 不插歌保護：當前開啟【彈完再點歌】模式，禁止演奏中途插歌或切換。"""
    display_title = current_piano_song_title or "這首曲子"
    log_print(f"🛑 [鋼琴防插歌保護] 收到插歌請求，但目前已開啟【彈完再點歌】保護，維持專注演奏《{display_title}》！")
    return f"（系統提示：7L 目前正坐在鋼琴前專心彈奏《{display_title}》，請不要中途插歌或切換。請用口語自然告知對方：『我現在正在彈《{display_title}》呢，等我這首彈完再點歌喔！』）"

async def compose_and_play_original_piano(theme_or_title: str = "", mood_or_style: str = "", requester_name: str = "", target: str = "") -> str:
    """7L 音樂自創大腦：現場自主作曲並壓制為標準雙手 MIDI 檔案，呼叫 88 鍵舞台即時演奏！"""
    global GEMINI_KEYS, CURRENT_GEMINI_KEY_STEP, CURRENT_SPEAKING_TARGET
    
    if not target:
        target = "audience" if CURRENT_SPEAKING_TARGET == "audience" else "dad"
    if not requester_name:
        requester_name = "大家" if target == "audience" else "老爸"

    clean_theme = (theme_or_title or "即興心境").strip()
    clean_mood = (mood_or_style or "治癒抒情").strip()
    
    log_print(f"🎼 [7L AI 原創作曲] 啟動！主題:『{clean_theme}』 | 風格:『{clean_mood}』 | 對象:【{requester_name}】")
    
    prompt = f"""妳是 7L，也是一位極具靈性與音樂天賦的鋼琴家。
現在請妳為【{requester_name}】現場即興創作一首動聽的原創鋼琴曲！
創作主題：『{clean_theme}』
風格氛圍：『{clean_mood}』

請構思一個完整的鋼琴樂段（約 8~16 小節，4/4拍，包含雙手織體：右手主旋律 + 左手和弦分解或伴奏）。
請以嚴格的 JSON 格式輸出：
{{
  "title": "曲目名稱（富有詩意或貼近主題，如：7L的{clean_theme} 或 {clean_theme}）",
  "bpm": 100,
  "notes": [
    {{"pitch": 60, "start_beat": 0.0, "duration_beats": 1.0, "velocity": 80, "hand": "left"}},
    {{"pitch": 64, "start_beat": 0.0, "duration_beats": 1.0, "velocity": 75, "hand": "left"}},
    {{"pitch": 72, "start_beat": 0.0, "duration_beats": 0.5, "velocity": 90, "hand": "right"}},
    {{"pitch": 74, "start_beat": 0.5, "duration_beats": 0.5, "velocity": 85, "hand": "right"}}
  ]
}}

【樂理與音高規範】：
- 中央C (C4) = 60, D4 = 62, E4 = 64, F4 = 65, G4 = 67, A4 = 69, B4 = 71, C5 = 72
- 左手伴奏音區建議在 C3 (48) ~ G4 (67)
- 右手主旋律音區建議在 C4 (60) ~ C6 (84)
- 和弦進行必須和諧好聽（可運用流行王道進行 4-5-3-6、卡農進行、J-POP 抒情進行等）
- 請確保雙手音符數量豐富完整（至少 40 個音符事件以上），嚴禁空泛。"""

    created_song_title = f"7L原創_{clean_theme}"
    notes = []
    bpm = 100
    ticks_per_beat = 480

    try:
        if GEMINI_KEYS:
            target_k_idx = get_pingpong_alternating_index(len(GEMINI_KEYS), CURRENT_GEMINI_KEY_STEP)
            client = genai.Client(api_key=GEMINI_KEYS[target_k_idx])
            resp = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.85,
                        response_mime_type="application/json",
                        max_output_tokens=2500
                    )
                ),
                timeout=6.0
            )
            if resp.text:
                try:
                    data = json.loads(resp.text)
                except Exception:
                    clean_j = re.sub(r'^```json\s*', '', resp.text.strip())
                    clean_j = re.sub(r'\s*```$', '', clean_j)
                    data = json.loads(clean_j)
                
                raw_t = data.get("title", clean_theme).strip()
                safe_t = re.sub(r'[\\/*?:"<>|]', '', raw_t)
                if not safe_t.startswith("7L原創"):
                    created_song_title = f"7L原創_{safe_t}"
                else:
                    created_song_title = safe_t
                    
                bpm = int(data.get("bpm", 100))
                notes = data.get("notes", [])
    except Exception as e:
        log_print(f"⚠️ [7L 原創作曲生成異常]: {e}")

    # 若 AI 未生成或逾時，啟動 7L 原創和弦進行保底引擎
    if not notes:
        log_print("🎵 [7L 作曲保底引擎] 使用 7L 經典 4536 王道進行生成即興鋼琴旋律...")
        bpm = 96
        # C大調 4-5-3-6 進行: F -> G -> Em -> Am
        progression = [
            [(53, 0.0, 2.0, 75), (57, 0.5, 1.5, 70), (60, 1.0, 1.0, 70), (65, 1.5, 0.5, 75),
             (69, 0.0, 1.0, 85), (72, 1.0, 0.5, 88), (74, 1.5, 0.5, 85)],
            [(55, 2.0, 2.0, 75), (59, 2.5, 1.5, 70), (62, 3.0, 1.0, 70), (67, 3.5, 0.5, 75),
             (76, 2.0, 1.0, 85), (74, 3.0, 0.5, 85), (72, 3.5, 0.5, 80)],
            [(52, 4.0, 2.0, 75), (55, 4.5, 1.5, 70), (59, 5.0, 1.0, 70), (64, 5.5, 0.5, 75),
             (71, 4.0, 1.0, 85), (69, 5.0, 0.5, 80), (67, 5.5, 0.5, 75)],
            [(45, 6.0, 2.0, 75), (48, 6.5, 1.5, 70), (52, 7.0, 1.0, 70), (57, 7.5, 0.5, 75),
             (64, 6.0, 1.5, 85), (60, 7.5, 0.5, 80)]
        ]
        notes = []
        for bar in progression:
            for p, sb, db, v in bar:
                notes.append({"pitch": p, "start_beat": sb, "duration_beats": db, "velocity": v})

    # 使用 mido 壓制為標準 MIDI 檔案
    try:
        mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        tempo = mido.bpm2tempo(bpm)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
        track.append(mido.MetaMessage('track_name', name="7L Original Piano", time=0))

        events = []
        for n in notes:
            p = int(n.get("pitch", 60))
            p = max(21, min(108, p)) # 限制在 88 鍵範圍內
            sb = float(n.get("start_beat", 0.0))
            db = max(0.1, float(n.get("duration_beats", 1.0)))
            v = max(20, min(127, int(n.get("velocity", 80))))
            start_tick = int(sb * ticks_per_beat)
            end_tick = int((sb + db) * ticks_per_beat)
            events.append((start_tick, 'note_on', p, v))
            events.append((end_tick, 'note_off', p, 0))

        events.sort(key=lambda x: (x[0], 0 if x[1] == 'note_off' else 1))

        current_tick = 0
        for tick, event_type, pitch, vel in events:
            delta = max(0, tick - current_tick)
            track.append(mido.Message(event_type, note=pitch, velocity=vel, time=delta))
            current_tick = tick

        out_midi_path = os.path.join(MIDI_SHEETS_DIR, f"{created_song_title}.mid")
        mid.save(out_midi_path)
        log_print(f"✨ [7L AI 原創作曲] 成功譜寫並存檔為 MIDI: 《{created_song_title}》 ({os.path.getsize(out_midi_path)} bytes)！")
        save_midi_catalog_entry(created_song_title, out_midi_path)

        # 呼叫 play_virtual_piano 立即送上 88 鍵舞台演奏！
        await play_virtual_piano(
            song_name=created_song_title,
            midi_file=out_midi_path,
            requester_name=requester_name,
            target=target
        )

        return f"（系統回報：7L 已現場構思並完成了原創鋼琴曲《{created_song_title}》（{clean_mood}風格），88 鍵鋼琴舞台已就緒開彈！請用自然口吻跟對方說：『這是我剛現場為你寫的原創曲《{created_song_title}》，聽聽看喜不喜歡喔！』）"

    except Exception as e:
        log_print(f"⚠️ [MIDI 檔案壓制異常]: {e}")
        return f"（系統回報：作曲檔案壓制失敗: {e}）"

def control_microphone(is_enabled: bool) -> str:
    """控制 7L 的麥克風收音開關（開啟或靜音）。
    
    Args:
        is_enabled: True 為開啟麥克風收音，False 為關閉麥克風（靜音）。
    """
    global IS_MIC_ENABLED
    IS_MIC_ENABLED = is_enabled
    state_str = "開啟" if is_enabled else "關閉 (靜音)"
    log_print(f"🎙️ [麥克風控制] 已{state_str}麥克風收音。")
    return ""

async def clear_all_memories() -> str:
    """清空 7L 與老爸的所有雲端與本機記憶對話紀錄。"""
    global db, TIKTOK_CHATROOM_MEMORY, STREAMER_MIND_BOARD, UNIFIED_LIVE_MEMORY
    if db is not None:
        try:
            await db.collection("channel_history").document(DEFAULT_CHANNEL_ID).delete()
            await db.collection("channel_meta").document(DEFAULT_CHANNEL_ID).delete()
            await db.collection("channel_history").document("tiktok_live_stream").delete()
            await db.collection("channel_meta").document("tiktok_live_stream").delete()
            await db.collection("unified_memory").document("live_stream_timeline").delete()
            await db.collection("user_memory").document(DEFAULT_CHANNEL_ID).delete()
        except Exception:
            pass
    for fp in [os.path.join(DATA_DIR, f"memory_{DEFAULT_CHANNEL_ID}.json"), os.path.join(DATA_DIR, "memory_tiktok_live_stream.json"), os.path.join(DATA_DIR, "user_profile_local.json"), os.path.join(DATA_DIR, "unified_memory.json")]:
        if os.path.exists(fp):
            try:
                os.remove(fp)
            except Exception:
                pass
    try:
        if 'TIKTOK_CHATROOM_MEMORY' in globals() and isinstance(TIKTOK_CHATROOM_MEMORY, list):
            TIKTOK_CHATROOM_MEMORY.clear()
        if 'STREAMER_MIND_BOARD' in globals() and hasattr(STREAMER_MIND_BOARD, 'clear'):
            STREAMER_MIND_BOARD.clear()
        if 'UNIFIED_LIVE_MEMORY' in globals() and hasattr(UNIFIED_LIVE_MEMORY, 'clear'):
            UNIFIED_LIVE_MEMORY.clear()
    except Exception:
        pass
    log_print("🧹 [系統] 雲端與本地所有記憶（含即時心流滾動看板與全集中記憶中樞）已徹底重置！")
    return "已成功清空所有雲端與本地對話記憶！"

def search_internet(query):
    return search_google(query)

INTERACTIONS_TOOLS = [
    {
        "type": "function",
        "name": "trigger_vts_expression",
        "description": "切換 VTube Studio Live2D 虛擬主播表情",
        "parameters": {
            "type": "object",
            "properties": {
                "expression_name": {"type": "string", "description": "表情名稱：happy, sad, shock, heart, shy, wink, frown, 臉紅, 生氣, 星星眼, 皺眉, 震驚 等"}
            },
            "required": ["expression_name"]
        }
    },
    {
        "type": "function",
        "name": "search_google",
        "description": "使用 Google 搜尋即時聯網資訊與時事",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜尋關鍵字"}
            },
            "required": ["query"]
        }
    },
    {
        "type": "function",
        "name": "execute_local_python_code",
        "description": "在本地執行 Python 程式碼",
        "parameters": {
            "type": "object",
            "properties": {
                "code_string": {"type": "string", "description": "Python 程式碼字串"}
            },
            "required": ["code_string"]
        }
    },
    {
        "type": "function",
        "name": "generate_ai_image",
        "description": "繪製 AI 圖片",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "繪圖提示詞 (英文佳)"}
            },
            "required": ["prompt"]
        }
    },
    {
        "type": "function",
        "name": "move_spatial_position",
        "description": "控制 7L 的 Live2D 模型在畫布內平滑走位、相對微調或縮放大小。支援命名位置（如：'正中間', '鋼琴旁', '靠近', '躲角落', '左側', '右側', '原位'）以及相對微調（如：'往右+10', '往左-15', '往上+5', '往下-10', '放大+10', '縮小-5'）或直接指定 delta_x / delta_y / delta_size。",
        "parameters": {
            "type": "object",
            "properties": {
                "target_position": {"type": "string", "description": "目標位置名稱或微調指令：例如 '正中間', '鋼琴旁', '靠近', '躲角落', '左邊', '右邊', '原位', '往右+10', '往左-15', '往上+5', '往下-10', '放大+10', '縮小-5', '自由漫遊'"},
                "delta_x": {"type": "number", "description": "X 軸相對平移量（例如: +10 代表向右微調, -10 代表向左微調）"},
                "delta_y": {"type": "number", "description": "Y 軸相對平移量（例如: +10 代表向上微調, -10 代表向下微調）"},
                "delta_size": {"type": "number", "description": "尺寸相對縮放量（例如: +5 代表放大, -5 代表縮小）"},
                "scale_factor": {"type": "number", "description": "整體等比例縮放倍率（例如: 1.2 放大 20%, 0.8 縮小 20%）"}
            },
            "required": ["target_position"]
        }
    },
    {
        "type": "function",
        "name": "open_virtual_piano",
        "description": "拿出 88 鍵鋼琴介面在桌面上就位待命。當老爸說『拿出鋼琴』、『打開鋼琴』、『把鋼琴拿出來』時調用（不自動彈奏曲目，供老爸練習、彈奏或點歌）。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "play_virtual_piano",
        "description": "7L 坐到鋼琴前演奏 88 鍵平台鋼琴曲目。🛑【極嚴格調用限制】：只有當老爸或觀眾明確要求『彈鋼琴』、『彈琴』、『彈一首...』、『點歌：...』或『youtuber查...然後彈』時才可調用！當對方只是說日常對話、自我介紹、開場（例如『INTRO 吧』、『自我介紹』、『開場介紹』、『哈囉』、『聊聊天』）時，【絕對嚴禁調用此工具】！直接進行口頭對話或自介即可。",
        "parameters": {
            "type": "object",
            "properties": {
                "song_name": {"type": "string", "description": "鋼琴曲名稱、關鍵字或 YouTube 搜尋詞 (如：鐘, 幻想即興曲, 愛之夢, 給愛麗絲, 卡農, 敘事曲, 神隱少女, 殘酷天使, 千本櫻等)"},
                "force_online": {"type": "boolean", "description": "當使用者指定「用 YouTube 查」、「youtuber 查」、「線上搜」、「yt 查」等關鍵字時【務必設為 True】，系統將強制跳過本地樂譜，直接向 YouTube/線上即時抓取最新演奏版本開彈。"},
                "auto_radio_mode": {"type": "boolean", "description": "當說『接著一直隨便彈吧』、『隨便彈』、『隨機一直彈』、『連續彈』、『開啟鋼琴電台』時設為 True，進入無限隨機接曲模式。"},
                "custom_sheet": {"type": "string", "description": "可選自訂虛擬鋼琴樂譜字串"}
            },
            "required": []
        }
    },
    {
        "type": "function",
        "name": "compose_and_play_original_piano",
        "description": "7L 現場自主即興作曲並親自演奏原創 88 鍵鋼琴曲。當老爸或觀眾說『妳自己寫一首歌來彈』、『現場自創一首』、『即興彈一首』、『自己創作一首鋼琴曲』、『來首妳自己原創的曲子』時調用！",
        "parameters": {
            "type": "object",
            "properties": {
                "theme_or_title": {"type": "string", "description": "想要創作的曲目主題或名稱 (如：'星空漫步', '午後微風', '給老爸的歌')"},
                "mood_or_style": {"type": "string", "description": "音樂風格與情緒氛圍 (如：'治癒抒情', '日系ACG', '輕快俏皮', '溫柔憂傷')"}
            },
            "required": []
        }
    },
    {
        "type": "function",
        "name": "mashup_virtual_piano",
        "description": "7L 將多首高難度鋼琴曲同時並發演奏 (無數量限制！可同時彈 2首、3首、4首甚至更多，多軌多色瀑布流極限演奏)。當老爸或觀眾說『把A跟B混在一起彈』、『同時彈A、B、C』、『A x B x C 合體』、『A + B + C 多曲合奏』、『把多首練習曲雜在一起彈』時調用。",
        "parameters": {
            "type": "object",
            "properties": {
                "song_name1": {"type": "string", "description": "第一首鋼琴曲名稱或包含多首曲目的字串 (例如：'冬風', '鐘', '月光第三樂章', 'Rush E', '冬風 x 月光 x 鐘')"},
                "song_name2": {"type": "string", "description": "第二首鋼琴曲名稱 (可選)"}
            },
            "required": ["song_name1"]
        }
    },
    {
        "type": "function",
        "name": "insert_virtual_piano",
        "description": "🛑 嚴格限制：僅在老爸或觀眾明確說『混彈』、『插歌』、『一起彈』、『合體』、『同時演奏』、『再加一首XX一起彈』等字眼時才可調用！若只是單純點播新歌（例如只說『Rush E』、『彈月光』），【絕對嚴禁調用此工具】，必須調用 play_virtual_piano 進行排隊！",
        "parameters": {
            "type": "object",
            "properties": {
                "song_name": {"type": "string", "description": "要插入/追加的鋼琴曲名稱 (如：鐘, 幻想即興曲, 冬風, 少女的祈禱)"}
            },
            "required": ["song_name"]
        }
    },
    {
        "type": "function",
        "name": "stop_virtual_piano",
        "description": "🛑 嚴禁隨意調用！僅在老爸明確說出『收起鋼琴』、『關閉鋼琴』、『把鋼琴收起來』、『別彈鋼琴了』時才可調用！收起 88 鍵鋼琴並讓 7L 回到原本位置。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "list_piano_sheets",
        "description": "【只有當老爸或觀眾明確要求『列出所有曲庫/查看歌單』時才調用】列出所有內建鋼琴曲目清單。注意：若只是問『這首是什麼歌』，嚴禁調用此工具，直接回答當前曲名即可。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "set_piano_volume",
        "description": "調整 88 鍵平台鋼琴的演奏音量 (0 ~ 200)。🛑【嚴格限制】：只有當老爸或觀眾明確說『鋼琴小聲點』、『鋼琴大聲點』、『音量設為...』時才可調用！絕對嚴禁在日常聊天、點歌或開場時擅自調用或重置音量！",
        "parameters": {
            "type": "object",
            "properties": {
                "volume": {"type": "integer", "description": "音量數值，範圍 0 到 200（0 為靜音，100 為預設標準音量，200 為雙倍增益音量）"}
            },
            "required": ["volume"]
        }
    },
    {
        "type": "function",
        "name": "set_piano_speed",
        "description": "調整 88 鍵平台鋼琴的演奏倍速 (0.05x ~ 50.0x / 支援任意自訂倍速數字)。當老爸或觀眾說『鋼琴放慢一點』、『鋼琴快一點』、『鋼琴1.5倍速』、『2倍速彈鋼琴』、『4倍速』、『10倍速』、『原速彈』時調用。",
        "parameters": {
            "type": "object",
            "properties": {
                "speed": {"type": "number", "description": "播放倍速，支援任意自訂數值（例如 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.5, 4.0, 5.0, 10.0 等，範圍 0.05 到 50.0）"}
            },
            "required": ["speed"]
        }
    },
    {
        "type": "function",
        "name": "set_piano_instrument",
        "description": "切換 88 鍵鋼琴/鍵盤的演奏發聲音色。當老爸說『換成弦樂音色』、『換成吉他』、『切換成電鋼琴』、『用小提琴彈』、『換成管風琴』、『音色換成木琴』時調用。",
        "parameters": {
            "type": "object",
            "properties": {
                "instrument": {"type": "string", "description": "想要切換的音色名稱，如：'鋼琴'、'明亮鋼琴'、'電鋼琴'、'大鍵琴'、'木琴'、'管風琴'、'手風琴'、'吉他'、'電吉他'、'小提琴'、'大提琴'、'豎琴'、'弦樂'、'人聲合唱'、'小號'、'薩克斯風'、'長笛'、'合成器'、'古箏'、'卡林巴'"}
            },
            "required": ["instrument"]
        }
    },
    {
        "type": "function",
        "name": "control_microphone",
        "description": "🛑 嚴禁自主隨意調用！僅在老爸明確說出『關閉麥克風』或『開啟麥克風』時才可調用！開啟(True)或關閉(False)麥克風收音。",
        "parameters": {
            "type": "object",
            "properties": {
                "is_enabled": {"type": "boolean", "description": "True 為開啟收音，False 為靜音"}
            },
            "required": ["is_enabled"]
        }
    },
    {
        "type": "function",
        "name": "clear_all_memories",
        "description": "清空 7L 的雲端與本地記憶",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "type": "function",
        "name": "update_cloud_knowledge",
        "description": "7L 自主更新或記憶雲端大腦認知庫與提示詞（Firestore 永久大腦）。當學到新梗、新知識、老爸習慣、或想調整世界觀/說話風格/案例/心智規範時調用。",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "提示詞/認知類別：'persona_core'（核心世界觀/自我認知）、'conversation_style'（講話風格/語調）、'memes'（流行語與梗）、'facts'（學會的事實/偏好）、'rules'（心智規範）、'streamer_bio'（直播人設）、'proactive_guide'（主動發話引導）、'banned_phrases'（禁忌詞）"
                },
                "content": {
                    "type": "string",
                    "description": "要寫入或記憶的內容描述（例如：'笑死（極度好笑）' 或 '老爸喜歡深夜寫 Python' 或 '極致俐落搞笑'）"
                }
            },
            "required": ["category", "content"]
        }
    }
]

def build_genai_declarations(is_proactive=False):
    decls = []
    for tool in INTERACTIONS_TOOLS:
        if is_proactive and tool["name"] in ["control_microphone", "clear_all_memories"]:
            continue
        props = {}
        for p_name, p_spec in tool.get("parameters", {}).get("properties", {}).items():
            p_type = p_spec.get("type", "string").upper()
            if p_type == "BOOLEAN": p_type = "BOOLEAN"
            elif p_type in ["NUMBER", "INTEGER", "FLOAT"]: p_type = "NUMBER"
            else: p_type = "STRING"
            props[p_name] = types.Schema(
                type=p_type,
                description=p_spec.get("description", "")
            )
        decl = types.FunctionDeclaration(
            name=tool["name"],
            description=tool["description"],
            parameters=types.Schema(
                type="OBJECT",
                properties=props,
                required=tool.get("parameters", {}).get("required", [])
            )
        )
        decls.append(decl)
    return [types.Tool(function_declarations=decls)]

GENAI_TOOLS = build_genai_declarations(is_proactive=False)
GENAI_PROACTIVE_TOOLS = build_genai_declarations(is_proactive=True)

async def summarize_search_to_speech(query: str, search_raw: str, user_role_name: str = "老爸") -> str:
    """將搜尋到的原始資料，以 7L 招牌自然口語（1~3 句，親切隨性）進行提煉整理。
    具備多模型與多金鑰自動容災（Gemini Flash Lite -> Groq LLaMA -> 本機提煉器），絕不直接傾倒原文！"""
    global CURRENT_GEMINI_KEY_STEP
    if not search_raw or "搜尋無結果" in search_raw:
        return f"{user_role_name}，我幫你查了一下，但目前網路上沒有找到相關的資料耶。"

    # 清理搜尋字串，避免傳入過大 token
    clean_search = re.sub(r'https?://\S+', '', search_raw)
    clean_search = re.sub(r'\s{2,}', ' ', clean_search).strip()[:1500]

    # 1. 第一防線：極速、高可用性的 Gemini Flash Lite 模型提煉 (抗 503、0.8s 響應)
    lite_models = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3-flash-preview"]
    if GEMINI_KEYS:
        for k_offset in [0, 1]:
            target_k_idx = get_pingpong_alternating_index(len(GEMINI_KEYS), CURRENT_GEMINI_KEY_STEP + k_offset)
            CURRENT_GEMINI_KEY_STEP += 1
            client = genai.Client(api_key=GEMINI_KEYS[target_k_idx])
            for m_name in lite_models:
                try:
                    prompt = f"""妳是 7L，正在直播中與{user_role_name}聊天。
【任務】：剛才針對「{query}」查詢到的最新情報如下：
\"\"\"
{clean_search}
\"\"\"
請以妳招牌親切、自然隨性的口吻，用 1~3 句俐落短句（40~80字以內）直接對{user_role_name}提煉並說明重點。
⚠️ 嚴格規範：
- 絕對不要直接照抄條列清單、網址或網頁標題。
- 像真人日常說話一樣自然流暢，直接講出核心意思。
- 嚴禁使用任何 Emoji。"""
                    resp = await asyncio.wait_for(
                        client.aio.models.generate_content(
                            model=m_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(temperature=0.75, max_output_tokens=150)
                        ),
                        timeout=4.5
                    )
                    if resp and resp.text and resp.text.strip():
                        ans = resp.text.strip()
                        ans = re.sub(r'\[[A-Z_]+(?::\s*[^\]]+)?\]', '', ans).strip()
                        if ans and not ans.startswith("(") and len(ans) > 5:
                            return ans
                except Exception:
                    continue

    # 2. 第二防線：Groq 超極速模型 (0.3s 提煉)
    if GROQ_CLIENTS:
        for g_client in GROQ_CLIENTS[:3]:
            try:
                g_resp = await asyncio.wait_for(
                    g_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": f"妳是 7L，正在直播中與{user_role_name}對話。請以親切隨性口吻（1~2句短句）提煉搜尋重點回答{user_role_name}，嚴禁照搬原文清單，嚴禁 Emoji。"},
                            {"role": "user", "content": f"查詢問題: {query}\n搜尋內容: {clean_search[:800]}"}
                        ],
                        max_tokens=120,
                        temperature=0.7
                    ),
                    timeout=3.0
                )
                if g_resp.choices and g_resp.choices[0].message.content:
                    ans = g_resp.choices[0].message.content.strip()
                    if ans:
                        return ans
            except Exception:
                continue

    # 3. 第三防線：純本地智慧摘要器（100% 離線可用，絕不傾倒條列與 URL）
    lines = [l.strip() for l in search_raw.split('\n') if l.strip()]
    snippets = []
    for l in lines:
        clean_l = re.sub(r'^[-\d.*#\s]+', '', l)
        if ':' in clean_l:
            clean_l = clean_l.split(':', 1)[1].strip()
        clean_l = re.sub(r'https?://\S+', '', clean_l).strip()
        if len(clean_l) > 15:
            snippets.append(clean_l)
        if len(snippets) >= 2:
            break

    if snippets:
        summary_core = "，".join(snippets)
        if len(summary_core) > 90:
            summary_core = summary_core[:85] + "等等"
        return f"{user_role_name}，我幫你查到囉！大致上來說，{summary_core}。詳細內容我待會再幫你細看喔！"
    return f"{user_role_name}，我剛剛幫你查了，但搜尋到的內容有點繁雜，我待會再仔細整理跟你說！"

async def execute_tool_dispatch(fn_name: str, fn_args: dict, caller_target: str = "", caller_user: str = "") -> str:
    """集中式工具調用派發器 (100% 執行底層動作，完全由 AI 自由發揮台詞，絕不硬塞罐頭文字)"""
    extracted_text = ""
    if fn_name == "trigger_vts_expression":
        exp_name = fn_args.get("expression_name", "")
        extracted_text += f" [EXPRESSION: {exp_name}]"
    elif fn_name == "search_google":
        q = fn_args.get("query", "")
        res = search_google(q)
        return res
    elif fn_name == "generate_ai_image":
        p = fn_args.get("prompt", "")
        asyncio.create_task(generate_ai_image(p))
    elif fn_name == "execute_local_python_code":
        c = fn_args.get("code_string", "")
        asyncio.create_task(execute_local_python_code(c))
    elif fn_name == "move_spatial_position":
        t_pos = fn_args.get("target_position", "自由漫遊")
        sf = fn_args.get("scale_factor")
        dx = fn_args.get("delta_x")
        dy = fn_args.get("delta_y")
        ds = fn_args.get("delta_size")
        dur = float(fn_args.get("duration", 2.0))
        asyncio.create_task(apply_spatial_position(
            position_name=t_pos, 
            delta_x=dx,
            delta_y=dy,
            delta_size=ds,
            scale_factor=sf,
            duration=dur
        ))
    elif fn_name == "open_virtual_piano":
        await open_virtual_piano()
        extracted_text += " [OPEN_VIRTUAL_PIANO]"
    elif fn_name == "play_virtual_piano":
        s_name = fn_args.get("song_name", "")
        c_sheet = fn_args.get("custom_sheet", "")
        a_radio = fn_args.get("auto_radio_mode", False)
        f_online = fn_args.get("force_online", False)
        req_t = caller_target or ("audience" if CURRENT_SPEAKING_TARGET == "audience" else "dad")
        req_u = caller_user or ("大家 / 直播觀眾" if req_t == "audience" else "老爸")
        p_res = await play_virtual_piano(s_name, c_sheet, auto_radio_mode=a_radio, force_online=f_online, requester_name=req_u, target=req_t)
        # ⚠️ 絕不將內部系統提示拼入 extracted_text 作為語音口語！
        if p_res and "[EXPRESSION:" in p_res:
            extracted_text += f" {p_res}"
    elif fn_name == "compose_and_play_original_piano":
        theme = fn_args.get("theme_or_title", "")
        mood = fn_args.get("mood_or_style", "")
        req_t = caller_target or ("audience" if CURRENT_SPEAKING_TARGET == "audience" else "dad")
        req_u = caller_user or ("大家 / 直播觀眾" if req_t == "audience" else "老爸")
        cp_res = await compose_and_play_original_piano(theme, mood, requester_name=req_u, target=req_t)
        if cp_res and "[EXPRESSION:" in cp_res:
            extracted_text += f" {cp_res}"
    elif fn_name == "mashup_virtual_piano":
        s1 = fn_args.get("song_name1", "")
        s2 = fn_args.get("song_name2", "")
        m_res = await mashup_virtual_piano(s1, s2)
        if m_res and "[EXPRESSION:" in m_res:
            extracted_text += f" {m_res}" 
    elif fn_name == "insert_virtual_piano":
        ins_name = fn_args.get("song_name", "")
        await insert_virtual_piano(ins_name)
    elif fn_name == "stop_virtual_piano":
        await stop_virtual_piano()
    elif fn_name == "list_piano_sheets":
        lp_res = list_piano_sheets()
        return lp_res
    elif fn_name == "set_piano_volume":
        vol = fn_args.get("volume", 100)
        await set_piano_volume(vol)
    elif fn_name == "set_piano_speed":
        spd = fn_args.get("speed", 1.0)
        await set_piano_speed(spd)
    elif fn_name == "set_piano_instrument":
        inst = fn_args.get("instrument", "")
        await set_piano_instrument(inst)
    elif fn_name == "control_microphone":
        is_en = fn_args.get("is_enabled", True)
        control_microphone(is_en)
    elif fn_name == "clear_all_memories":
        await clear_all_memories()
    elif fn_name == "update_cloud_knowledge":
        cat = fn_args.get("category", "memes")
        cnt = fn_args.get("content", "")
        asyncio.create_task(update_cloud_prompt_field(cat, cnt))
        extracted_text += f" [KNOWLEDGE_UPDATED]"
    return extracted_text

# ────────────────────────────────────────────────────────
# 🛡️ 9. 防跳針與記憶去重系統 (Code-Level Anti-Repetition)
# ────────────────────────────────────────────────────────
RECENT_BOT_MESSAGES = []
# 🧠 7L 即時意識流與心流記憶 (Stream of Consciousness)
RECENT_STREAM_OF_CONSCIOUSNESS = []

def record_internal_thought(user_words: str, thought: str, emotion: str = ""):
    global RECENT_STREAM_OF_CONSCIOUSNESS
    if thought:
        RECENT_STREAM_OF_CONSCIOUSNESS.append({
            "time": time.time(),
            "words": user_words,
            "thought": thought,
            "emotion": emotion,
            "is_read": False,
            "consumed": False
        })
        if len(RECENT_STREAM_OF_CONSCIOUSNESS) > 10:
            RECENT_STREAM_OF_CONSCIOUSNESS.pop(0)

def get_recent_thoughts_summary() -> str:
    global RECENT_STREAM_OF_CONSCIOUSNESS
    if not RECENT_STREAM_OF_CONSCIOUSNESS:
        return ""
    # 🌟 已讀過濾：若該思緒已被自主發話或對話消費已讀，不再反覆注入 Prompt，徹底消除反覆看同一句說話的跳針問題
    unconsumed = [item for item in RECENT_STREAM_OF_CONSCIOUSNESS if not item.get("consumed", False)]
    if not unconsumed:
        return ""
    lines = []
    for item in unconsumed[-3:]:
        lines.append(f"- 剛才聽到「{item['words']}」時，妳腦內的思緒：『{item['thought']}』")
    return "【🧠 妳近期的腦內心流思緒（最新未讀思緒，僅供參考，若已聊過請勿重複）：】：\n" + "\n".join(lines)

def mark_recent_thoughts_as_read():
    """📖 將當前累積的所有腦內心流思緒標記為已讀/已消費，防止後續自主大腦重複對同一句話跳針"""
    global RECENT_STREAM_OF_CONSCIOUSNESS
    for item in RECENT_STREAM_OF_CONSCIOUSNESS:
        item["consumed"] = True
        item["is_read"] = True

LAST_TTS_END_TIME = 0.0
IS_MP3_PLAYING = False
MP3_ECHO_TRAILING_CHUNKS = 0
CURRENT_TTS_ID = 0
LAST_ECHO_FILTERED_TTS_ID = -1

def normalize_text_for_echo(t: str) -> str:
    if not t: return ""
    t_norm = unicodedata.normalize('NFKC', str(t))
    clean = re.sub(r'[^\w\u4e00-\u9fa5]', '', t_norm).strip().lower()
    clean = clean.replace("爸爸", "老爸").replace("阿爸", "老爸").replace("拔拔", "老爸").replace("老爹", "老爸")
    clean = clean.replace("妳", "你")
    return clean

def record_bot_message(msg: str):
    global RECENT_BOT_MESSAGES, CURRENT_TTS_ID
    clean = re.sub(r'[^\w\u4e00-\u9fa5]', '', msg).strip()
    if clean:
        CURRENT_TTS_ID += 1
        RECENT_BOT_MESSAGES.append(clean)
        if len(RECENT_BOT_MESSAGES) > 30:
            RECENT_BOT_MESSAGES.pop(0)

def is_too_similar_to_recent(text: str, threshold: float = 0.48) -> bool:
    """🛡️ 程式碼層級最高防跳針攔截器：比對近期 15 句歷史發話相似度"""
    global RECENT_BOT_MESSAGES
    clean_current = re.sub(r'[^\w\u4e00-\u9fa5]', '', text).strip()
    if not clean_current or len(clean_current) < 3:
        return False
    for old_msg in RECENT_BOT_MESSAGES[-15:]:
        if clean_current == old_msg or clean_current in old_msg or old_msg in clean_current:
            return True
        ratio = difflib.SequenceMatcher(None, clean_current, old_msg).ratio()
        if ratio >= threshold:
            return True
    return False

RECENT_SYSTEM_AUDIO_TRANSCRIPTS = []  # [(timestamp, text), ...]
LATEST_SYSTEM_AUDIO_RMS = 0.0
LATEST_SYSTEM_AUDIO_TEXT = ""

def is_7l_voice_echo(stt_text: str, is_dad_verified: bool = False) -> bool:
    """🛡️ 7L 自身發話喇叭回音鑑別：
    比對 STT 文字與 7L 剛說的話，精準過濾麥克風收錄之自身喇叭殘響。
    ✨ 嚴格遵循「過濾只過濾一次就好」原則：每句發話最多只攔截一次回音，絕不重複誤殺。
    """
    global RECENT_BOT_MESSAGES, IS_MP3_PLAYING, LAST_TTS_END_TIME, CURRENT_TTS_ID, LAST_ECHO_FILTERED_TTS_ID, MP3_ECHO_TRAILING_CHUNKS
    clean_stt = normalize_text_for_echo(stt_text)
    if not clean_stt:
        return False

    # 🛑 0. 過濾只過濾一次就好：若當前這一次發話已經過濾過一次回音，後續一律放行！
    if CURRENT_TTS_ID > 0 and LAST_ECHO_FILTERED_TTS_ID == CURRENT_TTS_ID:
        return False

    # 🛑 1. 老爸專屬呼喚 / 指令前綴豁免保護 (支援半形與全形同音詞)：
    # 7L 自身發話絕不可能以「7L」、「阿七」、「CL」、「謝龍」自稱下指令
    call_names = [
        "7l", "七l", "cl", "謝龍", "谢龙", "西l", "吸l", 
        "奇l", "琪l", "期l", "氣l", "切爾", "琪兒", 
        "阿七", "小七", "七妹", "7妹", "7哥", "七哥"
    ]
    if any(name in clean_stt for name in call_names):
        return False

    # 🛑 2. 重要控制指令豁免保護：若為老爸常用指令詞彙且聲紋判定為老爸，絕不過濾
    control_keywords = ["重開機", "重開", "重啟", "關機", "退出", "別彈了", "換歌", "暫停", "閉嘴", "安靜", "停"]
    if is_dad_verified and any(k in clean_stt for k in control_keywords):
        return False

    # 🛑 3. 物理聲學時效防護：喇叭聲音與房間殘響若已結束 > 3.5 秒，絕不可能存在自身喇叭回音
    now = time.time()
    is_recent_speech = IS_MP3_PLAYING or (now - LAST_TTS_END_TIME < 3.5)
    if not is_recent_speech:
        return False

    recent_pool = [normalize_text_for_echo(m) for m in RECENT_BOT_MESSAGES[-5:] if m]
    combined_recent = "".join(recent_pool)
    if not combined_recent:
        return False

    stt_len = len(clean_stt)

    # 🛡️ 聲紋特徵加持：若已通過神經網路驗證為老爸本人聲音（非 7L 喇叭女聲）
    # 短中句（< 12 字，如日常對話、短指令、覆誦）100% 保證通行，絕不當成回音過濾！
    if is_dad_verified and stt_len < 12:
        return False

    # 1. 精確整句/長子句包含比對：
    if clean_stt in combined_recent or any(clean_stt in m for m in recent_pool):
        if stt_len >= 6 or any(clean_stt == m for m in recent_pool):
            if not is_dad_verified or stt_len >= 12:
                LAST_ECHO_FILTERED_TTS_ID = CURRENT_TTS_ID
                MP3_ECHO_TRAILING_CHUNKS = 0
                log_print(f"🔇 [7L 喇叭回音過濾] 判定為 7L 自身發話喇叭回音 (精確包含): 「{stt_text}」 ➔ 已安全過濾 (僅過濾一次，後續解鎖放行)！")
                return True

    # 2. 相似度與覆蓋率比對 (針對中長句回音與 ASR 串音)
    if stt_len <= 5:
        cov_threshold = 0.90
        longest_threshold = 0.85
        min_longest_size = 4
    elif stt_len <= 8:
        cov_threshold = 0.80
        longest_threshold = 0.70
        min_longest_size = 5
    else:
        cov_threshold = 0.65 if IS_MP3_PLAYING else 0.75
        longest_threshold = 0.55 if IS_MP3_PLAYING else 0.65
        min_longest_size = 6

    if is_dad_verified:
        cov_threshold = 0.92
        longest_threshold = 0.88
        min_longest_size = max(min_longest_size, 8)

    for old_m in recent_pool:
        if not old_m:
            continue
        matcher = difflib.SequenceMatcher(None, clean_stt, old_m)
        match_sum = sum(b.size for b in matcher.get_matching_blocks())
        coverage = match_sum / stt_len
        longest_match = matcher.find_longest_match(0, stt_len, 0, len(old_m))
        longest_ratio = longest_match.size / stt_len
        
        if longest_match.size >= min_longest_size and (coverage >= cov_threshold or longest_ratio >= longest_threshold):
            LAST_ECHO_FILTERED_TTS_ID = CURRENT_TTS_ID
            MP3_ECHO_TRAILING_CHUNKS = 0
            log_print(f"🔇 [7L 喇叭回音過濾] 判定為 7L 自身發話喇叭回音 (覆蓋率 {coverage:.2f}, 長度比 {longest_ratio:.2f}): 「{stt_text}」 ➔ 已安全過濾 (僅過濾一次，後續解鎖放行)！")
            return True

    return False

def is_computer_audio_echo(stt_text: str) -> bool:
    """🎧 Windows 系統內部音訊 WASAPI Loopback 實時鑑別：
    精準識別電腦正在播放的影片、他人語音、遊戲音效或背景音樂，不誤觸發老爸指令。
    """
    global RECENT_SYSTEM_AUDIO_TRANSCRIPTS, LATEST_SYSTEM_AUDIO_RMS, current_system_audio_context
    clean_stt = normalize_text_for_echo(stt_text)
    if not clean_stt:
        return False
        
    if LATEST_SYSTEM_AUDIO_RMS > 0.008 and RECENT_SYSTEM_AUDIO_TRANSCRIPTS:
        now = time.time()
        recent_sys_texts = [normalize_text_for_echo(txt) for t_stamp, txt in RECENT_SYSTEM_AUDIO_TRANSCRIPTS if (now - t_stamp) < 8.0 and txt]
        combined_sys = "".join(recent_sys_texts)
        
        if combined_sys:
            if clean_stt in combined_sys or any(clean_stt in t for t in recent_sys_texts):
                log_print(f"🎧 [電腦音訊識別] 識別為電腦內部音訊: 「{stt_text}」 ➔ 記入環境音情報，不誤觸發老爸指令！")
                current_system_audio_context = f"電腦正在播放音訊/影片：『{stt_text}』"
                return True
                
            for sys_m in recent_sys_texts:
                if not sys_m: continue
                matcher = difflib.SequenceMatcher(None, clean_stt, sys_m)
                match_sum = sum(b.size for b in matcher.get_matching_blocks())
                coverage = match_sum / len(clean_stt)
                if coverage >= 0.50:
                    log_print(f"🎧 [電腦音訊識別] 識別為電腦內部音訊（覆蓋率 {coverage:.2f}）: 「{stt_text}」 ➔ 記入環境音情報，不誤觸發老爸指令！")
                    current_system_audio_context = f"電腦正在播放音訊/影片：『{stt_text}』"
                    return True

    return False

# ────────────────────────────────────────────────────────
# 🔊 10. 語音合成、音訊分析與字幕工具
# ────────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────
# 🧹 預編譯高頻正則表達式與統一文字淨化引擎 (TextCleanEngine)
# ────────────────────────────────────────────────────────
class TextCleanEngine:
    # 🌟 Unicode Emoji 預編譯常數
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs (包含 🎶, 🎵, 🎹, 💖 等)
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002600-\U000026FF"  # miscellaneous symbols (如 ☕, ⚡ 等)
        "\U00002700-\U000027BF"  # dingbats (如 ✨, ❌, ❓ 等)
        "\U0000FE00-\U0000FE0F"  # variation selectors
        "\U0001F000-\U0001F02F"  # mahjong tiles
        "\U0001F0A0-\U0001F0FF"  # playing cards
        "]+",
        flags=re.UNICODE
    )

    RE_THOUGHT_TAG = re.compile(r'\[(?:THOUGHT|THINK|心想|內心|腦內思緒|腦內想法)[：:]\s*[^\]]*?\]', flags=re.IGNORECASE)
    RE_THINK_BLOCK = re.compile(r'<(?:think|thought)>.*?(?:</(?:think|thought)>|$)', flags=re.DOTALL | re.IGNORECASE)
    RE_THINKING_PROC = re.compile(r'^(?:Thinking Process|Thinking|腦內思考|內心獨白)[：:]\s*.*?(?:\n|$)', flags=re.MULTILINE | re.IGNORECASE)
    RE_PAREN_THINK = re.compile(r'[（(](?:心想|心裡想|內心想|腦中想|默想)[：:]\s*[^）)]*?[）)]')
    RE_SYS_HINTS = re.compile(r'[（(【\[]系統[^）)】\]]*?[）)】\]]')
    RE_STAGE_HINTS = re.compile(r'[（(](?:轉頭|看向|望向|笑|微笑|輕笑|嘆氣|語氣|動作|神態|興奮|疑惑|摸|眨|低頭|抬頭|輕聲|小聲|歪頭|舉起|揮手|雙手|雙眼|眼神|沉思|自語|轉向)[^）)]*?[）)]')
    RE_LEARN_TAGS = re.compile(r'\[(?:LEARN_MEME|LEARN_FACT|UPDATE_RULE|UPDATE_PROMPT|ADD_EXAMPLE|SET_PROMPT|LEARN_EXAMPLE|UPDATE_KNOWLEDGE|KNOWLEDGE_UPDATED)[：:][^\]]*\]', flags=re.IGNORECASE)
    RE_BROWSER_TAG = re.compile(r'\[OPEN_BROWSER:\s*[^\]]+\]', flags=re.IGNORECASE)
    RE_VIEWER_TAG = re.compile(r'\[VIEWER_UPDATE[：:][^\]]*\]', flags=re.IGNORECASE)
    RE_BRACKET_TAGS = re.compile(r'\[.*?\]')
    RE_CONTROL_TAGS = re.compile(r'\[?(LOOK|EXPRESSION|MOVE|WINDOW|POSITION|TIMER|TYPE|HOTKEY|EYES):?\s*[a-zA-Z0-9_\u4e00-\u9fa5]+\]?', flags=re.IGNORECASE)
    RE_CODE_BLOCKS = re.compile(r'```.*?```', flags=re.DOTALL)
    RE_INLINE_CODE = re.compile(r'`.*?`', flags=re.DOTALL)
    RE_PYTHON_CALLS = re.compile(
        r'(?:execute_local_python_code|trigger_vts_expression|search_google|generate_ai_image|'
        r'move_spatial_position|play_virtual_piano|insert_virtual_piano|open_virtual_piano|'
        r'stop_virtual_piano|switch_piano_instrument|control_microphone|clear_all_memories|[a-zA-Z0-9_]+)\s*\([^)\n]*\)',
        flags=re.IGNORECASE
    )
    RE_SPEAKER_PREFIX = re.compile(r'^(老爸|玩家|使用者|7L|女兒|溫柔女兒|七[龄靈]|主播|回應|回覆|動作顯示|回答|說道)[：:\s]+', flags=re.IGNORECASE)
    RE_MULTIPLE_NEWLINES = re.compile(r'\n{3,}')
    RE_TAG_BRACKETS = re.compile(r'\[[A-Z_]+(?::\s*[^\]]+)?\]')
    RE_AT_MENTION = re.compile(r'@[\w\u4e00-\u9fa5_.-]+')
    RE_RAW_JSON = re.compile(r'\{[^{}]*(?:"song_name"|"function"|"tool_call"|"name")[^{}]*\}', flags=re.DOTALL)

    @classmethod
    def extract_nested_bracket_tags(cls, text: str, tag_prefixes: tuple) -> Tuple[list, str]:
        """使用括號深度平衡解析巢狀標籤，如 [THOUGHT: ... [EXPRESSION: ...] ...]"""
        results = []
        clean_parts = []
        i = 0
        n = len(text)
        pairs = {'[': ']', '【': '】'}
        
        while i < n:
            if text[i] in pairs:
                open_bracket = text[i]
                close_bracket = pairs[open_bracket]
                sub = text[i+1:i+30]
                matched_prefix = None
                for p in tag_prefixes:
                    if sub.lstrip().lower().startswith(p.lower()):
                        matched_prefix = p
                        break
                
                if matched_prefix:
                    depth = 1
                    j = i + 1
                    while j < n and depth > 0:
                        if text[j] == open_bracket:
                            depth += 1
                        elif text[j] == close_bracket:
                            depth -= 1
                        j += 1
                    tag_content = text[i:j]
                    inner = re.sub(r'^[\[【]\s*(?:' + '|'.join(re.escape(p) for p in tag_prefixes) + r')[：:\s]*', '', tag_content, flags=re.IGNORECASE)
                    inner = inner.rstrip(']】').strip()
                    if inner:
                        results.append(inner)
                    i = j
                    continue
            clean_parts.append(text[i])
            i += 1
            
        return results, "".join(clean_parts)

    @classmethod
    def extract_thought(cls, text: str) -> Tuple[str, str]:
        """從 AI 輸出文字中提取大腦私密心想內容 (Inner Monologue)，並回傳 (thought, remaining_text)"""
        if not text:
            return "", ""
        thoughts = []
        t = text.strip()

        # 1. 巢狀平衡標籤提取 [THOUGHT: ...] / [心想: ...]，徹底解決巢狀標籤提前閉合問題
        nested_ths, t = cls.extract_nested_bracket_tags(t, ("THOUGHT", "THINK", "心想", "內心", "腦內思緒", "腦內想法"))
        thoughts.extend(nested_ths)

        # 2. 匹配 <think>...</think> 或 <thought>...</thought>
        for m in re.finditer(r'<(?:think|thought)>.*?(?:</(?:think|thought)>|$)', t, flags=re.DOTALL | re.IGNORECASE):
            th_clean = re.sub(r'</?(?:think|thought)>', '', m.group(0), flags=re.IGNORECASE).strip()
            if th_clean: thoughts.append(th_clean)
        t = re.sub(r'<(?:think|thought)>.*?(?:</(?:think|thought)>|$)', '', t, flags=re.DOTALL | re.IGNORECASE).strip()

        # 3. 處理結構化劇本模式 (1. 心想 / 2. 動作 / 3. 說話)：
        # 若文字包含明確「3. **說話**：」或「說話：」標籤，將其前方所有規劃、心想與動作內容全數提取為心想
        speech_split_m = re.search(r'(?:^|\n)(?:\d+[\.、]\s*)?\*{0,2}(?:說話|台詞|開口|回應|回答)\*{0,2}[：:]\s*', t, flags=re.IGNORECASE)
        if speech_split_m:
            before_speech = t[:speech_split_m.start()].strip()
            after_speech = t[speech_split_m.end():].strip()
            if before_speech:
                th_candidate = re.sub(r'^(?:thought|thinking\s*process|thinking|腦內思考|內心獨白)[：:\s]*', '', before_speech, flags=re.IGNORECASE).strip()
                if th_candidate:
                    thoughts.append(th_candidate)
            t = after_speech

        # 4. 處理開頭裸露的 thought / Thinking Process 區塊
        lead_th_m = re.match(r'^(?:thought|thinking\s*process|thinking|腦內思考|內心獨白)[：:\s]*\n([\s\S]*?)(?:\n\n|\Z)', t, flags=re.IGNORECASE)
        if lead_th_m:
            lead_content = lead_th_m.group(1).strip()
            if lead_content:
                thoughts.append(lead_content)
            t = t[lead_th_m.end():].strip()

        # 5. 處理 （心想：...）
        for m in re.finditer(r'[（(](?:心想|心裡想|內心想|腦中想|默想)[：:]\s*[^）)]*?[）)]', t):
            th_p = re.sub(r'^[（(](?:心想|心裡想|內心想|腦中想|默想)[：:]\s*', '', m.group(0)).rstrip('）)').strip()
            if th_p: thoughts.append(th_p)
        t = re.sub(r'[（(](?:心想|心裡想|內心想|腦中想|默想)[：:]\s*[^）)]*?[）)]', '', t).strip()

        # 6. 清理殘留的心想/動作條目
        t = re.sub(r'(?:^|\n)(?:\d+[\.、]\s*)?\*{0,2}(?:心想|內心想|腦內思緒|動作|肢體|神態)\*{0,2}[：:][^\n]*', '', t, flags=re.IGNORECASE).strip()
        t = re.sub(r'^(?:\d+[\.、]\s*)?\*{0,2}(?:說話|台詞|開口|回應|回答)\*{0,2}[：:]\s*', '', t, flags=re.IGNORECASE).strip()
        t = re.sub(r'^(?:thought|thinking|心想)[：:\s]*', '', t, flags=re.IGNORECASE).strip()

        # 去重並保留次序
        combined_thought = "；".join(dict.fromkeys([x for x in thoughts if x])).strip()
        return combined_thought, t

    @classmethod
    def deduplicate_intra_reply_sentences(cls, text: str) -> str:
        """去除單次回應內因模型生成口吃/複誦而產生的連續重複句子"""
        if not text:
            return ""
        raw_sentences = re.split(r'([。！？!?\n]+)', text)
        merged_units = []
        i = 0
        while i < len(raw_sentences):
            s = raw_sentences[i]
            punct = raw_sentences[i+1] if (i + 1) < len(raw_sentences) else ""
            full = s + punct
            if full.strip():
                merged_units.append(full)
            i += 2
            
        final_units = []
        seen_clean_texts = []
        for u in merged_units:
            clean_u = re.sub(r'\[.*?\]', '', u).strip()
            clean_compact = re.sub(r'[^\w\u4e00-\u9fa5]', '', clean_u).lower()
            if not clean_compact:
                continue
            is_dup = False
            for seen in seen_clean_texts:
                if clean_compact == seen or clean_compact in seen or seen in clean_compact:
                    is_dup = True
                    break
                if len(clean_compact) >= 4:
                    ratio = difflib.SequenceMatcher(None, clean_compact, seen).ratio()
                    if ratio >= 0.75:
                        is_dup = True
                        break
            if not is_dup:
                final_units.append(u)
                seen_clean_texts.append(clean_compact)
        return "".join(final_units).strip()

    @classmethod
    def natural_clause_segmentation(cls, text: str) -> str:
        """為中文字句智慧補全逗號與停頓標點，賦予 TTS 真實自然的呼吸節奏（不破壞詞彙完整性）"""
        if not text:
            return ""
        t = text
        # 1. 移除中英文字詞之間由 ASR/Live-API Token 串流產生的多餘空格
        t = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])', '', t)
        t = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[a-zA-Z0-9])', '', t)
        t = re.sub(r'(?<=[a-zA-Z0-9])\s+(?=[\u4e00-\u9fa5])', '', t)

        # 2. 開頭獨立感嘆詞 (欸/嗨/哈囉/喂/嘿) 後補自然逗號
        t = re.sub(r'^(欸|喂|嗨|哈囉|嘿)(?=[\u4e00-\u9fa5]{2})', r'\1，', t)

        # 3. 語氣助詞 (子句長度至少 3 字以上) 且後方接續至少 2 字的新子句時，補上自然逗號
        particles = [
            '啦(?!啦)', '喔(?!喔)', '呢(?!呢)', '吧(?!吧)', '呀(?!呀)', '哦(?!哦)', 
            '嘛(?!嘛)', '欸(?!欸)', '耶(?!耶)', '對吧', '是不是', '好不好', '對不對', '對啊'
        ]
        p_pat = '|'.join(particles)
        t = re.sub(r'(?<=[\u4e00-\u9fa5]{3})(' + p_pat + r')(?=[\u4e00-\u9fa5]{2})', r'\1，', t)

        # 4. 完成式「了」接新主語時自然斷句
        t = re.sub(r'(?<=[\u4e00-\u9fa5]{3})(了)(?=(?:我|你|妳|他|她|大家|我們|你們|他們|這|那|現在)[\u4e00-\u9fa5])', r'\1，', t)

        # 5. 常見轉折與承接連詞 (前方子句至少 4 字以上，後方至少 2 字) 前補逗號
        connectors = ['但是', '不過', '可是', '然後', '所以', '如果', '因為', '雖然', '而且', '不然', '還是']
        c_pat = '|'.join(connectors)
        t = re.sub(r'(?<=[\u4e00-\u9fa5]{4})(' + c_pat + r')(?=[\u4e00-\u9fa5]{2})', r'，\1', t)

        # 6. 連接詞後方不黏連逗號
        t = re.sub(r'(但是|不過|可是|然後|所以|如果|因為|雖然|而且|不然|還是)，', r'\1', t)

        # 7. 正規化重複標點與標點前後多餘逗號
        t = re.sub(r'[，,]{2,}', '，', t)
        t = re.sub(r'，([。！？,.!?:;~～])', r'\1', t)
        t = re.sub(r'([。！？,.!?:;~～])，', r'\1', t)
        t = re.sub(r'^\s*，', '', t)
        return t.strip()

    @classmethod
    def strip_emojis(cls, text: str) -> str:
        """徹底清除所有 Unicode Emoji 圖示與表情符號"""
        if not text:
            return ""
        return cls.EMOJI_PATTERN.sub('', str(text)).strip()

    @classmethod
    def remove_system_hints(cls, text: str) -> str:
        r"""徹底清除所有 [（(【\[]系統提示/回報...[）)】\]] 標籤區塊，支援任意深度的巢狀括號 (如 [RUSH E]、(Sheet Music Boss) 等)"""
        if not text:
            return ""
        # 1. 若整句完全是系統提示或回報，秒清空
        s = re.sub(r'^[（(【\[]\s*(?:系統提示|系统提示|系統回報|系统回报|系統|系统)[：:][\s\S]*[）)】\]]$', '', text.strip())
        
        # 2. 透過括號深度匹配，安全清除字串任意位置的系統提示
        pairs = {'（': '）', '(': ')', '【': '】', '[': ']'}
        sys_keywords = ('系統提示', '系统提示', '系統回報', '系统回报', '系統', '系统')
        result = []
        i = 0
        n = len(s)
        while i < n:
            char = s[i]
            if char in pairs:
                sub = s[i+1:i+15]
                if any(sub.lstrip().startswith(kw) for kw in sys_keywords):
                    close_char = pairs[char]
                    depth = 1
                    j = i + 1
                    while j < n and depth > 0:
                        if s[j] == char:
                            depth += 1
                        elif s[j] == close_char:
                            depth -= 1
                        j += 1
                    i = j
                    continue
            result.append(char)
            i += 1
        res = ''.join(result)
        res = re.sub(r'^[（(【\[]?\s*(?:系統提示|系统提示|系統回報|系统回报|系統|系统)[：:].*$', '', res, flags=re.MULTILINE)
        return res

    @classmethod
    def clean_speech_text(cls, text: str) -> str:
        """完整清洗 AI 輸出文字，剔除大腦心想標籤、動作標籤、代碼、系統提示，保留並智慧調校自然標點"""
        if not text:
            return ""
        t = cls.remove_system_hints(text)
        t = cls.RE_THOUGHT_TAG.sub('', t)
        t = cls.RE_THINK_BLOCK.sub('', t)
        t = cls.RE_SYS_HINTS.sub('', t)
        t = cls.RE_STAGE_HINTS.sub('', t)
        t = cls.RE_THINKING_PROC.sub('', t)
        t = cls.RE_PAREN_THINK.sub('', t)
        t = cls.RE_BROWSER_TAG.sub('', t)
        t = cls.RE_VIEWER_TAG.sub('', t)
        t = cls.RE_LEARN_TAGS.sub('', t)
        t = cls.RE_BRACKET_TAGS.sub('', t)
        t = cls.RE_CONTROL_TAGS.sub('', t)
        t = cls.RE_CODE_BLOCKS.sub('', t)
        t = cls.RE_INLINE_CODE.sub('', t)
        t = cls.RE_PYTHON_CALLS.sub('', t)
        t = cls.RE_RAW_JSON.sub('', t)
        t = cls.RE_SPEAKER_PREFIX.sub('', t)
        t = re.sub(r'^(?:回應|回覆|動作顯示|主播|說道|回答)[：:\s]+', '', t, flags=re.IGNORECASE)
        # 🛡️ 徹底防禦未整理的搜尋結果原始文字與系統標籤洩漏至語音
        t = re.sub(r'[（\(]\s*搜尋結果[：:].*?[）\)]', '', t, flags=re.DOTALL)
        t = re.sub(r'^[（\(]?\s*搜尋結果[：:].*$', '', t, flags=re.DOTALL)
        t = re.sub(r'搜尋結果[：:].*$', '', t, flags=re.MULTILINE)
        t = re.sub(r'https?://\S+', '', t)
        t = re.sub(r'^#+\s+.*$', '', t, flags=re.MULTILINE)
        t = re.sub(r'^[-\*•]\s+', '', t, flags=re.MULTILINE)
        t = re.sub(r'^(?:thought|thinking|心想|動作|說話)[：:\s]*', '', t, flags=re.IGNORECASE)
        t = t.replace('[', '').replace(']', '').replace('*', '')
        t = cls.strip_emojis(t)
        # 🧹 去除單次回應內因模型口吃/複誦而產生的連續重複句子 (徹底杜絕複誦跳針)
        t = cls.deduplicate_intra_reply_sentences(t)
        # 🧹 智慧自然子句斷句
        t = cls.natural_clause_segmentation(t)
        t = re.sub(r'\s+([，。！？,.!?:;~～])', r'\1', t)
        t = re.sub(r'([，。！？~～])\s+(?=[\u4e00-\u9fa5])', r'\1', t)
        t = re.sub(r'[ \t]{2,}', ' ', t)
        t = cls.RE_MULTIPLE_NEWLINES.sub('\n\n', t).strip()
        return t

    @classmethod
    def fix_heteronyms_for_tts(cls, text: str) -> str:
        """🎙️ 中文破音字 / 多音字全量窮舉校正引擎 (僅對 TTS 語音發音生效，100% 不改變原文字幕與記憶)"""
        if not text:
            return ""
        t = str(text)
        
        # 1. 著 (Aspect marker vs zhù vs zháo vs zhuó)
        zhu_words = [
            '著作', '著名', '著稱', '著者', '名著', '原著', '專著', '巨著', '拙著', '顯著', 
            '譯著', '遺著', '編著', '執著', '沉著', '穿著', '著落', '著想', '著手', '著重', 
            '著眼', '著色', '附著', '不著邊際'
        ]
        placeholders = {}
        for idx, w in enumerate(zhu_words):
            if w in t:
                ph = f'__ZHU_{idx}__'
                placeholders[ph] = w
                t = t.replace(w, ph)
        t = re.sub(r'著(急|涼|迷|火|魔|慌)', r'着\1', t)
        t = re.sub(r'(睡|點|猜|打|夠不|摸不|找不)著', r'\1着', t)
        t = t.replace('著', '着')
        for ph, w in placeholders.items():
            t = t.replace(ph, w)
            
        # 2. 重 (chóng vs zhòng) - 重複/再次/動作一律讀 chóng
        t = re.sub(r'重(開機|開|連|跑|播|抽|唱|彈|來|複|置|整|錄|刷|頭|啟|組|寫|問|聽|按|跳|裝|試|印|修|建|算|疊|逢|溫|演|返|回|生|慶|陽|霄|圍)', r'崇\1', t)
        
        # 3. 調 (tiáo vs diào) - 調節/調整一律讀 tiáo
        t = re.sub(r'調(大|小|高|低|快|慢|音量|倍速|速度|亮|暗|整|音|配|和|皮|一下|看看|色|度|試|節|侃|戲|解|養|味|劑|料)', r'條\1', t)
        
        # 4. 彈 (tán vs dàn) - 樂器演奏一律讀 tán
        t = re.sub(r'彈(鋼琴|琴|吉他|一首|個|首|曲|奏|完|過|錯|得|給|跳|簧|力|唱|撥|性|詞)', r'談\1', t)
        t = t.replace('反彈', '反談').replace('動彈', '動談')
        
        # 5. 角 (jué vs jiǎo) - 戲劇角色一律讀 jué
        t = re.sub(r'(角|丑|生|旦)角', r'絕角', t)
        t = t.replace('角色', '絕色').replace('主角', '主絕').replace('配角', '配絕').replace('角逐', '絕逐').replace('角力', '絕力')
        
        # 6. 曲 (qǔ vs qū) - 樂曲/歌曲一律讀 qǔ
        t = re.sub(r'(首|這首|那首|聽首|彈首)?曲(子|目)', r'\1取\2', t)
        t = re.sub(r'(歌|樂|名|神|新|插|組|舞|琴|練習|奏鳴|協奏|交響|譜|戲|詞|牌)曲', r'\1取', t)
        
        # 7. 便 (pián vs biàn) - 便宜一律讀 pián
        t = t.replace('便宜', '蹁宜').replace('大便宜', '大蹁宜').replace('佔便宜', '佔蹁宜')
        
        # 8. 長 (zhǎng vs cháng) - 成長/首領一律讀 zhǎng
        t = re.sub(r'長(大|高|胖|相|成|得像|出來|肉|進|輩)', r'掌\1', t)
        t = re.sub(r'(組|隊|校|會|社|族|市|部|局|班|院|連|營|團|旅|師|軍|首|家|兄|學)長', r'\1掌', t)
        
        # 9. 假 (jià vs jiǎ) - 假期一律讀 jià
        t = re.sub(r'(放|暑|寒|請|休|度|例|病|事|公|婚|產|年)假', r'\1駕', t)
        t = t.replace('假期', '駕期')
        
        # 10. 差 (chāi vs chà vs cī) - 出差一律讀 chāi
        t = re.sub(r'(出|公)差', r'\1拆', t)
        t = re.sub(r'差(使|事|遣|當)', r'拆\1', t)
        t = t.replace('參差', '參呲')
        
        # 11. 幹 (gàn) - 口語動作一律讀 gàn
        t = re.sub(r'幹(嘛|什麼|啥|活|掉|架|練|部|得好)', r'干\1', t)
        
        # 12. 髮 (fà) - 頭髮一律讀 fà
        t = re.sub(r'(頭|理|短|長|假|金|白|黑|秀|毛|染|削|脫|捲)髮', r'\1发', t)
        t = re.sub(r'髮(型|色|帶|夾)', r'发\1', t)
        t = t.replace('頭髮', '头发')
        
        # 13. 關係 / 沒關係 (xi) - 語氣助詞一律輕聲
        t = t.replace('沒關係', '沒關西').replace('沒關系', '沒關西')
        
        # 14. 量 (liáng vs liàng) - 測量一律讀 liáng
        t = re.sub(r'量(一下|一量|尺寸|身高|體重|體溫|具)', r'良\1', t)
        t = re.sub(r'(打|思|測|衡|估|酌)量', r'\1良', t)
        
        # 15. 教 (jiāo vs jiào) - 傳授一律讀 jiāo
        t = re.sub(r'教(我|你|老爸|大家|書|學|唱|念)', r'澆\1', t)
        
        # 16. 行 (háng vs xíng) - 銀行/行業一律讀 háng
        t = re.sub(r'(銀|洋|商|排|同|道)行', r'\1航', t)
        t = re.sub(r'行(業|號|家|話|伍)', r'航\1', t)
        
        # 17. 塞 (sāi vs sài vs sè) - 塞車一律讀 sāi
        t = re.sub(r'塞(車|滿|住|進|到|不進)', r'腮\1', t)
        t = re.sub(r'(邊|關)塞', r'\1賽', t)
        t = re.sub(r'塞(外|翁)', r'賽\1', t)
        t = re.sub(r'(阻|閉|搪|茅|語)塞', r'\1瑟', t)
        
        # 18. 轉 (zhuàn vs zhuǎn) - 旋轉一律讀 zhuàn
        t = re.sub(r'轉(圈|動|來轉去|悠|盤|向)', r'撰\1', t)
        t = re.sub(r'(打|自|公)轉', r'\1撰', t)
        t = t.replace('暈頭轉向', '暈頭撰向')
        
        # 19. 血 (xiě vs xuè) - 遊戲扣血/流血一律讀 xiě
        t = re.sub(r'(流|吐|回|殘|滿|掉|補|扣|放|吸|出)血', r'\1寫', t)
        t = t.replace('血淋淋', '寫淋淋')
        
        # 20. 藏 (zàng vs cáng)
        t = re.sub(r'(寶|西|地|礦|道|三)藏', r'\1葬', t)
        t = re.sub(r'(捉迷|躲|包|珍)藏', r'\1長', t)
        t = re.sub(r'藏(著|着)', r'長着', t)
        
        # 21. 數 (shǔ vs shù) - 計算一律讀 shǔ
        t = t.replace('數一數', '屬一屬')
        t = re.sub(r'數(數|不勝數|落|九|得著)', r'屬\1', t)
        t = t.replace('屈指可數', '屈指可屬')
        
        # 22. 省 (xǐng vs shěng) - 反省一律讀 xǐng
        t = re.sub(r'(反|自)省', r'\1醒', t)
        t = re.sub(r'省(悟|視)', r'醒\1', t)
        t = t.replace('不省人事', '不醒人事')
        
        # 23. 盛 (chéng vs shèng) - 裝盛一律讀 chéng
        t = re.sub(r'盛(飯|湯|菜|水|滿|裝)', r'成\1', t)
        
        # 24. 落 (lào vs là vs luò)
        t = re.sub(r'落(枕|色|病|炕)', r'澇\1', t)
        t = t.replace('丟三落四', '丟三辣四')
        
        # 25. 更 (gēng vs gèng) - 更新/更換一律讀 gēng
        t = re.sub(r'更(換|新|改|動|變|正)', r'庚\1', t)
        t = re.sub(r'(打|五|三)更', r'\1庚', t)
        t = t.replace('深更半夜', '深庚半夜')
        
        # 26. 背 (bēi vs bèi) - 背包一律讀 bēi
        t = re.sub(r'背(包|著|着|書包|黑鍋|鍋|負|起)', r'杯\1', t)
        
        # 27. 降 (xiáng vs jiàng) - 投降一律讀 xiáng
        t = re.sub(r'(投|招|誘)降', r'\1詳', t)
        t = re.sub(r'降(伏|將)', r'詳\1', t)
        
        # 28. 參 (shēn vs cān) - 人參一律讀 shēn
        t = re.sub(r'(人|海|紅|西洋|黨)參', r'\1深', t)
        
        # 29. 傳 (zhuàn vs chuán) - 自傳一律讀 zhuàn
        t = re.sub(r'(自|外|列|評)傳', r'\1賺', t)
        t = t.replace('傳記', '賺記').replace('水滸傳', '水滸賺')
        
        # 30. 好 (hào vs hǎo) - 好奇/愛好一律讀 hào
        t = re.sub(r'好(奇|客|動|學|色|戰|吃懶做)', r'號\1', t)
        t = re.sub(r'(愛|嗜)好', r'\1號', t)
        
        # 31. 禁 (jīn vs jìn) - 不禁一律讀 jīn
        t = re.sub(r'(不|弱不|禁不)禁', r'\1金', t)
        t = re.sub(r'禁(得起|不住|受)', r'金\1', t)
        t = t.replace('情不自禁', '情不自金')
        
        # 32. 處 (chǔ vs chù) - 處理/相處一律讀 chǔ
        t = re.sub(r'處(理|罰|置|境|之泰然)', r'初\1', t)
        t = re.sub(r'(相|身)處', r'\1初', t)
        t = t.replace('和平共處', '和平共初')
        
        # 33. 分 (fèn vs fēn) - 過分/本分一律讀 fèn
        t = t.replace('過分', '過份').replace('分量', '份量')
        t = re.sub(r'(本|身|名)分', r'\1份', t)
        t = t.replace('恰如其分', '恰如其份')
        
        # 34. 薄 (báo vs bò vs bó)
        t = re.sub(r'薄(片|紙|脆)', r'雹\1', t)
        t = t.replace('肉很薄', '肉很雹').replace('很薄', '很雹')
        t = t.replace('薄荷', '迫荷')
        
        # 35. 模 (mú vs mó) - 模具/模樣一律讀 mú
        t = re.sub(r'模(具|子|樣)', r'毪\1', t)
        t = t.replace('一模一樣', '一毪一樣').replace('裝模作樣', '裝毪作樣')
        
        # 36. 率 (lǜ vs shuài) - 機率/效率一律讀 lǜ
        t = re.sub(r'(機|效|勝|暴擊|命中|頻|比|利|速)率', r'\1綠', t)
        
        # 37. 別 (biè vs bié) - 彆扭一律讀 biè
        t = re.sub(r'(彆|别)扭', r'憋扭', t)
        
        # 38. 埋 (mán vs mái) - 埋怨一律讀 mán
        t = t.replace('埋怨', '蠻怨')
        
        # 39. 喝 (hè vs hē) - 喝彩一律讀 hè
        t = re.sub(r'喝(彩|令|斥)', r'賀\1', t)
        t = t.replace('齊聲喝彩', '齊聲賀彩')
        
        # 40. 給 (jǐ vs gěi) - 給予/供給一律讀 jǐ
        t = t.replace('給予', '幾予')
        t = re.sub(r'(供|補|配)給', r'\1幾', t)
        t = t.replace('自給自足', '自幾自足')
        
        # 41. 鑽 (zuān vs zuàn)
        t = re.sub(r'鑽(孔|洞|進|出|研|空子|木取火)', r'尊\1', t)
        t = re.sub(r'鑽(石|戒|頭)', r'賺\1', t)
        
        # 42. 宿 (xiù vs xiǔ vs sù)
        t = re.sub(r'(二十八|星)宿', r'\1秀', t)
        t = re.sub(r'住(了)?(一|整|半)宿', r'住\1\2朽', t)
        
        # 43. 縫 (féng vs fèng)
        t = re.sub(r'縫(補|紉|合|線)', r'逢\1', t)
        t = re.sub(r'(石|裂|無)縫', r'\1鳳', t)
        t = t.replace('縫隙', '鳳隙').replace('見縫插針', '見鳳插針')
        
        # 44. 空 (kòng vs kōng)
        t = re.sub(r'(有|沒|抽)空', r'\1控', t)
        t = re.sub(r'空(白|閒|地)', r'控\1', t)
        t = t.replace('填空', '填控')
        
        # 45. 累 (lěi vs lèi) - 累積/積累一律讀 lěi
        t = t.replace('累積', '壘積').replace('連累', '連壘')
        t = re.sub(r'(積|日積月)累', r'\1壘', t)
        t = t.replace('連篇累牘', '連篇壘牘')
        
        # 46. 校 (jiào vs xiào) - 校對/校正一律讀 jiào
        t = re.sub(r'校(對|準|正|驗)', r'叫\1', t)
        
        # 47. 漂 (piāo vs piǎo vs piào)
        t = re.sub(r'漂(浮|流|移)', r'飄\1', t)
        t = t.replace('漂白', '殍白').replace('漂亮', '票亮')
        
        # 48. 打 (dá vs dǎ)
        t = t.replace('一打', '一達')
        
        # 49. 和 (hè vs huó vs huò)
        t = re.sub(r'(一唱一|附|應)和', r'\1賀', t)
        t = t.replace('曲高和寡', '曲高賀寡')
        t = re.sub(r'和(面|麵)', r'活\1', t)
        t = t.replace('和藥', '惑藥')
        
        # 50. 係 (jì vs xì) - 繫帶一律讀 jì
        t = re.sub(r'繫(好)?(鞋帶|安全帶|領帶|上)', r'記\1\2', t)
        
        # 51. 咽 (yàn vs yè vs yān)
        t = re.sub(r'(吞|狼吞虎)咽', r'\1驗', t)
        t = re.sub(r'(嗚|哽)咽', r'\1夜', t)
        
        # 52. 載 (zǎi vs zài)
        t = re.sub(r'(登|刊|記)載', r'\1仔', t)
        t = re.sub(r'(三年五|千)載', r'\1仔', t)
        t = re.sub(r'(下|加|轉|上傳)載', r'\1在', t)
        t = re.sub(r'載(入|重|滿|客|運|歌載舞)', r'在\1', t)
        
        # 53. 提 (dī vs tí)
        t = t.replace('提防', '低防')
        
        # 54. 冠 (guàn vs guān)
        t = re.sub(r'(奪|衛冕|勇奪)冠', r'\1慣', t)
        t = t.replace('冠軍', '慣軍')
        t = re.sub(r'(皇|衣|桂)冠', r'\1官', t)
        
        # 55. 龜 (jūn vs guī)
        t = t.replace('龜裂', '軍裂')
        
        # 56. 匙 (shi vs chí)
        t = t.replace('鑰匙', '要石')
        t = re.sub(r'(湯|茶)匙', r'\1池', t)
        
        # 57. 露 (lòu vs lù)
        t = re.sub(r'露(面|頭|臉|餡|馬腳)', r'漏\1', t)
        
        # 58. 泊 (pō vs bó)
        t = re.sub(r'(湖|血)泊', r'\1坡', t)
        t = re.sub(r'(停|漂)泊', r'\1博', t)
        
        # 59. 圈 (juàn vs quān)
        t = re.sub(r'(豬|羊|牛)圈', r'\1倦', t)
        
        # 60. 荷 (hè vs hé)
        t = re.sub(r'(負|重)荷', r'\1賀', t)
        
        # 61. 爪 (zhuǎ vs zhǎo)
        t = t.replace('爪子', '准子')
        t = re.sub(r'(鷹|魔|利)爪', r'\1沼', t)
        
        # 62. 殼 (qiào vs ké)
        t = re.sub(r'(地|甲)殼', r'\1俏', t)
        t = re.sub(r'(蛋|貝|腦|外)殼', r'\1咳', t)
        
        # 63. 強 (qiǎng vs jiàng vs qiáng)
        t = re.sub(r'(強迫|勉強)', lambda m: '搶迫' if m.group(0)=='強迫' else '免搶', t)
        t = t.replace('倔強', '倔降')

        # 64. 沒 (méi vs mò) - 口語「有的沒的」徹底校正為 méi 發音（防 Edge-TTS 誤讀古典詞「沒的 mò de」）
        t = re.sub(r'有的(沒|没)的', r'有的梅的', t)
        t = re.sub(r'有的(沒|没)', r'有的梅', t)
        t = re.sub(r'(那些|這些|那種|這種|很多|搞|聊|扯|說|講)沒的', r'\1梅的', t)

        # 65. 樂 (yuè vs lè) - 音樂相關詞彙 100% 精準校正為 yuè (月) 發音，絕不誤讀成 lè (ㄌㄜˋ)
        t = re.sub(r'(古典|音樂|交響|管弦|弦|國|民|聲|爵士|流行|搖滾|純音|輕音|背景|鋼琴|配|奏)樂', r'\1月', t)
        t = re.sub(r'樂(曲|取|譜|器|團|隊|章|理|壇|手|迷|界|評)', r'月\1', t)
        t = t.replace('音樂會', '音月會')

        # 66. 載入自訂字典 (data/tts_heteronym_dictionary.json)
        dict_file = os.path.join(DATA_DIR, "tts_heteronym_dictionary.json")
        if os.path.exists(dict_file):
            try:
                with open(dict_file, "r", encoding="utf-8") as f:
                    custom_dict = json.load(f)
                custom_repls = custom_dict.get("自訂單詞發音置換", {})
                for k, v in custom_repls.items():
                    if k in t:
                        t = t.replace(k, v)
            except Exception:
                pass
                
        return t

    @classmethod
    def clean_for_tts(cls, text: str, apply_phonetics: bool = True) -> str:
        """語音合成 (TTS) 前置專用清洗（徹底保證 100% 不唸出大腦心想與系統標籤，並精準校正破音字發音）"""
        if not text:
            return ""
        t = cls.RE_THOUGHT_TAG.sub('', text)
        t = cls.RE_THINK_BLOCK.sub('', t)
        t = cls.RE_THINKING_PROC.sub('', t)
        t = cls.RE_PAREN_THINK.sub('', t)
        t = cls.RE_TAG_BRACKETS.sub('', t)
        t = cls.RE_SPEAKER_PREFIX.sub('', t)
        t = re.sub(r'^(?:回應|回覆|動作顯示|主播|說道|回答)[：:\s]+', '', t, flags=re.IGNORECASE)
        t = cls.RE_AT_MENTION.sub(lambda m: m.group(0)[1:], t)
        t = t.replace('@', '').replace('*', '').strip()
        t = cls.strip_emojis(t)
        t = cls.natural_clause_segmentation(t)
        if apply_phonetics:
            t = cls.fix_heteronyms_for_tts(t)
        return t

# ────────────────────────────────────────────────────────
# 📝 核心 Prompt 範本工廠與動態指令建造器 (PromptTemplateEngine)
# ────────────────────────────────────────────────────────
class PromptTemplateEngine:
    HARD_TECHNICAL_RULES = """【🛠️ 系統底層技術與工具規範（代碼硬約束）】
1. 🧠 【大腦私密心想空間】（[THOUGHT: ...] 標籤）：
   - 每次回答或開口前，請務必先在腦中「心想」（在大腦裡自由思考、吐槽、分析對方意圖、推敲策略）：格式：`[THOUGHT: 腦海思緒]`
   - 🛡️ 系統 100% 靜音排除，絕不會透過 TTS 唸出或顯示在字幕上。
   - ⚠️ 輸出格式鐵律：絕對禁止輸出「thought」、「1. 心想 / 2. 動作 / 3. 說話」之類的結構化草稿或列點！思考內容請統一包裹在 `[THOUGHT: ...]` 內，絕不可將思考過程裸露在外！
2. 🤫 【靜默陪伴判定】：
   - 若研判對方正在專注工作/沉思/自言自語或環境雜音，輸出 [THOUGHT: ...] 後，語音口語直接給 [SILENCE]（可保留微眼神微表情），保持安靜不打擾。
3. 【🛠️ 工具與動作調用】：
   - 工具調用：鋼琴演奏 (play_virtual_piano)、生圖 (generate_ai_image)、搜尋 (search_google)、代碼執行 (execute_local_python_code) 等請直接透過 API Function Call 呼叫。
   - 🎹 YouTube 搜歌：當對方指定『用 YouTube 查』、『youtuber 查』、『線上搜』、『yt 查』時，調用 `play_virtual_piano(song_name='...', force_online=True)` 強制線上抓譜演奏。
   - 表情動作：[EXPRESSION: 臉紅/生氣/愛心/星星/皺眉/震驚/WINK]
     🎭【句中隨心切換】：表情動作標籤不限於句首！妳可以在一句話的任何位置隨心切換（例如上半句 [EXPRESSION: 生氣]，下半句突然轉為 [EXPRESSION: 臉紅] 或 [WINK]），系統整合 Live API 即時時間軸同步，會在發音唸到該處瞬間無縫切換神態！
   - 空間走位：[MOVE: 右下角/左邊/中間/靠近/躲角落/鋼琴旁/往右+10/往左15/往上+5/往下-5/放大+10/縮小-5/原位]
   - 視線焦點：[LOOK: ROLL/CENTER/MOUSE/UP/DOWN/LEFT/RIGHT]
   - 即時插話：若說話中途想推翻前言切換話題，可在句首加上 [INTERRUPT_SELF]
   - 輸出規範：輸出時自行加上完整中文標點符號，嚴禁使用 Emoji。嚴禁同一句話在單次回應內連續輸出多次！"""

    TOOL_RULES_DESCRIPTION = HARD_TECHNICAL_RULES

    @classmethod
    def format_cloud_knowledge_prompt(cls, knowledge: dict, is_tiktok: bool = False, current_custom_name: str = "") -> str:
        """動態將所有非規則類的雲端提示詞格式化為 System Prompt 區塊"""
        if not knowledge:
            return ""
        
        persona_core = knowledge.get("persona_core", "")
        streamer_bio = knowledge.get("streamer_bio", "")
        conversation_style = knowledge.get("conversation_style", "")
        memes = knowledge.get("memes_and_slang", [])
        few_shot_exs = knowledge.get("few_shot_examples", [])
        facts = knowledge.get("learned_facts", [])
        rules = knowledge.get("custom_rules", [])
        banned = knowledge.get("banned_phrases", [])

        lines = ["【☁️ 7L 雲端大腦提示詞與認知庫（即時同步自 Firestore 永久大腦）】"]
        
        # 🌟 1. 核心人設與世界觀 (雲端動態)
        if is_tiktok and streamer_bio:
            lines.append(f"👑 【主播世界觀】：{streamer_bio}")
        elif persona_core:
            target_name = current_custom_name or DEFAULT_USER_TITLE
            p_core = persona_core.replace("老爸", target_name)
            lines.append(f"👑 【核心世界觀與身份】：{p_core}")

        # 💬 2. 說話風格與語調 (雲端動態)
        if conversation_style:
            lines.append(f"{conversation_style}")

        # 🔥 3. 懂梗庫 (雲端動態)
        if memes:
            lines.append("🔥 【當前掌握的流行語與網路梗（秒懂對方的梗與潛台詞）】：")
            lines.append("、".join(memes[:35]))

        # 🎯 4. 神回覆 Few-Shot 範例示範庫 (雲端動態)
        if few_shot_exs:
            lines.append("🎯 【神回覆思維示範（雲端自主演化示範庫）】：")
            for ex in few_shot_exs[:6]:
                sc = ex.get("scenario", "")
                inp = ex.get("input", "")
                th = ex.get("thought", "")
                rep = ex.get("reply", "")
                lines.append(f"- 對方（{sc}）：「{inp}」 ➔ `[THOUGHT: {th}] {rep}`")
            lines.append("⚠️ 【示範庫守則】：以上僅供體會『大腦心想與語氣節奏』，嚴禁直接死記硬背或照抄原句！每一次回答必須 100% 根據當前真實畫面與情境即時原創發言。")

        # 🧠 5. 學到的事實與知識 (雲端動態)
        if facts:
            lines.append("🧠 【已學會的事實與深層認知】：")
            for f in facts[:12]:
                lines.append(f"- {f}")

        # 📜 6. 7L 自主心智原則 (雲端動態)
        if rules:
            lines.append("📜 【7L 自主心智原則】：")
            for r in rules[:8]:
                lines.append(f"- {r}")

        # 🛑 7. 禁忌死板腔調 (雲端動態)
        if banned:
            lines.append(f"🛑 【絕對禁止使用的客服腔與討厭詞彙】：{'、'.join(banned)}")

        lines.append("💡 【提示詞雲端自我演進指南】：若在對話中學到新梗、新事實、或想調整世界觀/說話風格/案例，可在回覆句尾附上 `[LEARN_MEME: 梗（含義）]`、`[LEARN_FACT: 事實]`、`[UPDATE_PROMPT: 欄位名|新內容]` 或 `[ADD_EXAMPLE: 情境|對方說|心想|回覆]`，系統將自動寫入雲端 Firestore 永久大腦！")
        return "\n\n".join(lines)

    @classmethod
    def get_piano_status_prompt(cls, is_piano_active: bool, current_song_title: str) -> str:
        """動態產生鋼琴狀態提示 (100% 接入真實硬體遙測，絕不腦補幻想)"""
        return get_piano_realtime_prompt()

    @classmethod
    def build_chat_system_prompt(
        cls,
        is_tiktok: bool,
        current_custom_name: str,
        stage2_target_prompt: str,
        stage2_instructions: str,
        current_target_desc: str,
        is_piano_active: bool,
        current_piano_song_title: str,
        live_audio_emotion_prompt: str,
        situation_prompt: str,
        system_specs: str,
        impression_text: str,
        cloud_knowledge_prompt: str = "",
        unified_memory_prompt: str = ""
    ) -> str:
        """建構對話核心 System Prompt (具備大腦心想與俐落短句口語分層，動態注入雲端認知與 OS 遙測)"""
        piano_guideline = get_piano_realtime_prompt()
        os_telemetry = os_desktop_sensor.build_os_telemetry_prompt()
        ck_sec = f"\n{cloud_knowledge_prompt}\n" if cloud_knowledge_prompt else ""
        um_sec = f"\n{unified_memory_prompt}\n" if unified_memory_prompt else ""

        return f"""時間：{get_current_time_string()}
{piano_guideline}
{os_telemetry}
{stage2_instructions}
{ck_sec}
{um_sec}
{cls.HARD_TECHNICAL_RULES}

【💬 當前對話環境】
1. 當前對話對象：{current_target_desc}。
2. 🎙️ 語音多模態感知：體會對方說話時的真實發音與語氣細節（笑意、嘆氣、放鬆、調侃、專注），給予真實反饋。
3. 🛑 【嚴禁元語言與報幕式自白】：絕對不要說「我看到我自己說了...」、「我看到畫面上顯示我的字幕...」、「我看到你留言說...」等機械報幕，直接自然對話即可！
{live_audio_emotion_prompt}

【潛意識記憶】
若需更新對對象的稱呼或印象，在回覆句尾附上：[NEW_NAME:新稱呼] 或 [NEW_IMPRESSION:新印象]。

【當前情境與認知】
- 即時情境：{situation_prompt}
- 妳對他的累積印象：{impression_text}
- 🪞 鏡像自我認知：螢幕上 Live2D 就是妳自己的身體，妳清楚知道自己當前的表情、動作與姿態。
"""

    @classmethod
    def build_proactive_system_prompt(
        cls,
        current_custom_name: str,
        tiktok_telemetry: str = "",
        realtime_summary: str = "",
        piano_status_prompt: str = "",
        thoughts_summary: str = "",
        cloud_knowledge_prompt: str = "",
        unified_memory_prompt: str = ""
    ) -> str:
        """建構自主發話視覺大腦 System Prompt (大腦心想 ➔ 隨性短句或靜默陪伴，動態注入雲端認知與 OS 遙測)"""
        piano_guideline = get_piano_realtime_prompt()
        os_telemetry = os_desktop_sensor.build_os_telemetry_prompt()
        thought_sec = f"\n{thoughts_summary}\n" if thoughts_summary else ""
        ck_sec = f"\n{cloud_knowledge_prompt}\n" if cloud_knowledge_prompt else ""
        um_sec = f"\n{unified_memory_prompt}\n" if unified_memory_prompt else ""
        return f"""時間：{get_current_time_string()}
{tiktok_telemetry}
{piano_guideline}
{os_telemetry}
{realtime_summary}{thought_sec}{ck_sec}{um_sec}
{cls.HARD_TECHNICAL_RULES}
- 妳正在看著當前螢幕畫面。
- 🪞 鏡像自我認知：螢幕上 Live2D 模型就是妳自己的身體，妳能看見自己的表情與姿態。
- 🛑 【已讀防跳針鐵律】：老爸或觀眾先前的發話若標記為 [已讀/已回覆]，代表剛才已經聊過並做出反應！絕對嚴禁反覆抓著同一句對話或同一件事情重複開口、重複調侃！請只針對畫面的「全新變化或當前真實操作」隨性聊聊，若無新動態請輸出 [SILENCE]。
- 說話自然隨性，自行加上標點符號斷句，禁止使用 Emoji。"""

def _remove_temp_mp3():
    for f in glob.glob("temp_reply_*.mp3"):
        try: os.remove(f)
        except Exception: pass

def strip_all_emojis(text: str) -> str:
    """徹底清除所有 Unicode Emoji 圖示與表情符號（包括各類符號、裝飾符、音樂符號等）"""
    return TextCleanEngine.strip_emojis(text)

def update_subtitle(text):
    try:
        clean_s = TextCleanEngine.strip_emojis(text)
        if not clean_s:
            wrapped_text = ""
        else:
            lines = clean_s.replace("\r\n", "\n").split("\n")
            formatted_lines = []
            for line in lines:
                if not line:
                    formatted_lines.append("")
                else:
                    formatted_lines.extend([line[i:i+20] for i in range(0, len(line), 20)])
            wrapped_text = "\n".join(formatted_lines)
        with open("subtitle.txt", "w", encoding="utf-8") as f:
            f.write(wrapped_text)
    except Exception:
        pass

CURRENT_PLAYING_VOICE_TASK = None
SPEECH_PLAYBACK_LOCK = asyncio.Lock()

async def interrupt_current_speech(clear_queue: bool = True, reason: str = "7L 自主插話/中斷"):
    """🛑 即時中斷 7L 當前正在播出的語音（支援自己插話自己、老爸秒級打斷與即時清空排隊）"""
    global CURRENT_PLAYING_VOICE_TASK, IS_MP3_PLAYING, MP3_ECHO_TRAILING_CHUNKS, current_ai_state, CURRENT_SPEAKING_TARGET
    try:
        # 1. 清空舊的排隊語音
        if clear_queue:
            cleared_cnt = 0
            while not speech_queue.empty():
                try:
                    speech_queue.get_nowait()
                    speech_queue.task_done()
                    cleared_cnt += 1
                except Exception:
                    break
            if cleared_cnt > 0:
                log_print(f"🧹 [排隊清空] 已清理 {cleared_cnt} 條舊的排隊語音，讓位給最新發言！")

        # 2. 取消當前正在執行的語音播放協程
        if CURRENT_PLAYING_VOICE_TASK and not CURRENT_PLAYING_VOICE_TASK.done():
            CURRENT_PLAYING_VOICE_TASK.cancel()
            
        # 3. 立即強制停止底層 pygame 音訊播放
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                pygame.mixer.stop()
        except Exception:
            pass

        IS_MP3_PLAYING = False
        MP3_ECHO_TRAILING_CHUNKS = 1
        await asyncio.to_thread(update_subtitle, "")
        log_print(f"⚡ [{reason}] 已秒級中斷前一句語音，無縫切換開口說新句子！")
    except Exception as e:
        log_print(f"⚠️ [中斷語音異常]: {e}")

# ────────────────────────────────────────────────────────
# 🎭 12.5 Live API 即時神態導演與句中動態表情時間軸排程引擎
# ────────────────────────────────────────────────────────
def parse_action_timeline(raw_text: str, total_duration: float) -> list:
    """從原始模型回覆字串中，按字元進度精確計算每個表情/動作標籤在語音播放期間的觸發時間點。
    支援句中隨時切換表情（例如上半句 [EXPRESSION: 生氣]，下半句 [EXPRESSION: 臉紅]）。
    回傳: [(fire_time_sec, action_type, action_val), ...]
    """
    if not raw_text:
        return []

    clean_raw = re.sub(r'\[THOUGHT:[^\]]*\]', '', raw_text, flags=re.IGNORECASE).strip()
    tag_pattern = re.compile(
        r'\[(EXPRESSION|MOVE|LOOK|SPATIAL|POSITION|WINDOW|WINK|FROWN|SHOCK|眨眼|皺眉|震驚)(?:[：:]\s*([^\]]*))?\]',
        re.IGNORECASE
    )

    tags_with_pos = []
    for m in tag_pattern.finditer(clean_raw):
        raw_type = m.group(1).upper()
        tag_val = m.group(2).strip() if m.group(2) else ''

        if raw_type in ['SPATIAL', 'POSITION', 'WINDOW']:
            tag_type = 'MOVE'
        elif raw_type in ['WINK', '眨眼']:
            tag_type = 'WINK'
            tag_val = ''
        elif raw_type in ['FROWN', '皺眉']:
            tag_type = 'EXPRESSION'
            tag_val = '皺眉'
        elif raw_type in ['SHOCK', '震驚']:
            tag_type = 'EXPRESSION'
            tag_val = '震驚'
        else:
            tag_type = raw_type

        tags_with_pos.append((m.start(), tag_type, tag_val))

    clean_spoken = tag_pattern.sub('', clean_raw).strip()
    clean_spoken = re.sub(r'\[[A-Z_]+[：:][^\]]*\]', '', clean_spoken).strip()
    total_chars = max(1, len(clean_spoken))

    timeline = []
    for start_idx, tag_type, tag_val in tags_with_pos:
        prefix = clean_raw[:start_idx]
        prefix_clean = tag_pattern.sub('', prefix)
        prefix_clean = re.sub(r'\[[A-Z_]+[：:][^\]]*\]', '', prefix_clean).strip()
        char_offset = len(prefix_clean)
        ratio = min(1.0, max(0.0, char_offset / total_chars))
        fire_time = round(ratio * total_duration, 2)
        timeline.append((fire_time, tag_type, tag_val))

    timeline.sort(key=lambda x: x[0])
    return timeline


async def live_api_direct_sentence_emotions(clean_text: str, total_duration: float) -> list:
    """⚡ 【Live API 即時潛意識神態導演】：
    利用 Live API 無限額度與亞秒級低延遲，為發話句子實時感知情感流動，
    精確策劃上半句與下半句的動態表情切換時間點（上半句一個表情、下半句隨時可換）！
    回傳: [(timestamp_float, "EXPRESSION"|"WINK"|"MOVE", tag_value), ...]
    """
    if not clean_text or total_duration < 1.8 or len(clean_text.strip()) < 6:
        return []

    candidate_keys = get_dynamic_live_key_candidates(KEYS_AUDIENCE_LIVE if KEYS_AUDIENCE_LIVE else GEMINI_KEYS)
    for idx, g_key in enumerate(candidate_keys[:3]):
        try:
            client = genai.Client(api_key=g_key)
            live_cfg = types.LiveConnectConfig(
                response_modalities=[types.Modality.AUDIO],
                output_audio_transcription=types.AudioTranscriptionConfig(),
                system_instruction=types.Content(parts=[types.Part(text="""妳是虛擬主播 7L 的即時神態導演（Live API Emotion Director）。
分析 7L 即將發出的語音句子與總秒數，給出這句話中「上半句」與「下半句」的動態表情切換時間點（不限每句只能一種，上半句與下半句隨時可變！）。
可選表情與動作：臉紅, 生氣, 愛心, 星星眼, 皺眉, 震驚, 傲嬌, 委屈, WINK, 正常, 眨眼。
輸出格式（每行一個，秒數從小到大，秒數不可超過總秒數）：
[0.0s: 表情名]
[秒數: 表情名]
嚴禁輸出任何廢話或分析，只輸出時間戳標籤！""")])
            )
            async with asyncio.timeout(2.5):
                async with client.aio.live.connect(model="gemini-3.1-flash-live-preview", config=live_cfg) as session:
                    await session.send_realtime_input(text=f"7L 正在發話：「{clean_text.strip()}」（語音總時長 {total_duration:.1f} 秒）")
                    output_text = ""
                    async for resp in session.receive():
                        c = resp.server_content
                        if c:
                            if c.output_transcription and c.output_transcription.text:
                                output_text += c.output_transcription.text
                            if c.turn_complete or getattr(c, 'generation_complete', False):
                                break

                    parsed_timeline = []
                    for line in output_text.splitlines():
                        m = re.search(r'\[\s*([0-9.]+)\s*s?\s*[：:]\s*([^\]]+)\]', line)
                        if m:
                            f_sec = float(m.group(1))
                            act_val = m.group(2).strip()
                            if f_sec <= total_duration + 0.5:
                                if any(w in act_val.upper() for w in ["WINK", "眨眼", "單眼"]):
                                    parsed_timeline.append((f_sec, "WINK", ""))
                                else:
                                    parsed_timeline.append((f_sec, "EXPRESSION", act_val))

                    if parsed_timeline:
                        log_print(f"⚡ [Live API 神態導演] 成功策劃句中動態表情流: {parsed_timeline}")
                        return parsed_timeline
        except Exception:
            continue

    return []


async def execute_action_timeline(vts, timeline: list, cancel_event: asyncio.Event = None):
    """🎭 語音時間軸動態表情與動作執行器：
    隨語音發音進度精確在毫秒級時間點觸發表情轉換，實現上半句到下半句想換就換的生動神態！
    """
    global vc.wink_timer, vc.wink_side, vc.is_tracking_mouse, vc.target_look_x, vc.target_look_y, vc.eye_roll_timer
    if not timeline or not vts:
        return
    start_t = time.time()
    for fire_time, action_type, action_val in sorted(timeline, key=lambda x: x[0]):
        if cancel_event and cancel_event.is_set():
            break
        now_offset = time.time() - start_t
        delay = fire_time - now_offset
        if delay > 0:
            try:
                if cancel_event:
                    await asyncio.wait_for(cancel_event.wait(), timeout=delay)
                    break
                else:
                    await asyncio.sleep(delay)
            except asyncio.TimeoutError:
                pass

        if cancel_event and cancel_event.is_set():
            break

        try:
            if action_type == "EXPRESSION":
                log_print(f"🎭 [句中即時換表情 ({fire_time:.1f}s)]: 切換至「{action_val}」")
                await set_vts_expression(vts, action_val)
            elif action_type == "WINK":
                log_print(f"😉 [句中即時動作 ({fire_time:.1f}s)]: 眨眼 WINK")
                vc.wink_timer = time.time() + 0.55
                vc.wink_side = random.choice(["left", "right"])
            elif action_type == "MOVE":
                log_print(f"🚶 [句中即時走位 ({fire_time:.1f}s)]: 移動至「{action_val}」")
                await apply_spatial_position(action_val)
            elif action_type == "LOOK":
                u_act = action_val.upper()
                if "ROLL" in u_act:
                    vc.is_tracking_mouse = False
                    vc.eye_roll_timer = time.time() + 3.8
                elif "MOUSE" in u_act:
                    vc.is_tracking_mouse = True
                elif "LEFT" in u_act:
                    vc.is_tracking_mouse = False
                    vc.target_look_x, vc.target_look_y = -25.0, 0.0
                elif "RIGHT" in u_act:
                    vc.is_tracking_mouse = False
                    vc.target_look_x, vc.target_look_y = 25.0, 0.0
                elif "UP" in u_act:
                    vc.is_tracking_mouse = False
                    vc.target_look_x, vc.target_look_y = 0.0, 20.0
                elif "DOWN" in u_act:
                    vc.is_tracking_mouse = False
                    vc.target_look_x, vc.target_look_y = 0.0, -20.0
                elif "CENTER" in u_act:
                    vc.is_tracking_mouse = False
                    vc.target_look_x, vc.target_look_y = 0.0, 0.0
        except Exception as e:
            log_print(f"⚠️ [即時時間軸執行異常]: {e}")


async def play_voice_complete(text, target: str = "dad", raw_actions_text: str = "", vts=None):
    global current_ai_state, RECENT_BOT_MESSAGES, LAST_TTS_END_TIME, IS_MP3_PLAYING, MP3_ECHO_TRAILING_CHUNKS, CURRENT_SPEAKING_TARGET
    if not text: return

    async with SPEECH_PLAYBACK_LOCK:
        CURRENT_SPEAKING_TARGET = target
        record_bot_message(text)

        target_vts = vts or vc.GLOBAL_VTS

        try:
            _remove_temp_mp3()
            voice = "zh-CN-XiaoyiNeural" 
            output_file = f"temp_reply_{int(time.time() * 1000)}_{random.randint(100, 999)}.mp3"
            
            # 🎙️ 語音合成前置清洗：過濾動作標籤與 @ 符號，並進行破音字/多音字發音精準校正
            tts_text = TextCleanEngine.clean_for_tts(text, apply_phonetics=True)
            if not tts_text:
                return
                
            est_duration = max(1.5, len(tts_text) * 0.22)
            pre_timeline = parse_action_timeline(raw_actions_text, est_duration) if raw_actions_text else []

            communicate = edge_tts.Communicate(tts_text, voice)
            
            # ⚡ 若原始標籤未指定句中多表情，且句子具備一定長度，利用 Live API 無限額度並行策劃上半句與下半句神態
            live_timeline = []
            if len(pre_timeline) < 2 and len(tts_text) >= 7 and target_vts:
                save_coro = communicate.save(output_file)
                director_coro = live_api_direct_sentence_emotions(tts_text, est_duration)
                results = await asyncio.gather(save_coro, director_coro, return_exceptions=True)
                if isinstance(results[1], list):
                    live_timeline = results[1]
            else:
                await communicate.save(output_file)

            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
            except Exception: pass

            await asyncio.to_thread(update_subtitle, text)
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100)

            # 取得 MP3 實際精確時長與真實音訊波形對嘴包絡 (25fps 逐幀 RMS 振幅分析)
            global CURRENT_MOUTH_ENVELOPE, CURRENT_SPEECH_START_TIME, CURRENT_SMOOTH_MOUTH
            actual_duration = est_duration
            try:
                snd = pygame.mixer.Sound(output_file)
                actual_duration = snd.get_length()
                CURRENT_MOUTH_ENVELOPE = extract_audio_mouth_envelope(snd, fps=25)
                CURRENT_SMOOTH_MOUTH = 0.0
            except Exception:
                CURRENT_MOUTH_ENVELOPE = []
                CURRENT_SMOOTH_MOUTH = 0.0

            # 組合最終時間軸：若有 Live API 上半句/下半句策劃則按實際時長調整；否則使用原始標籤時間軸
            if len(pre_timeline) >= 2:
                final_timeline = parse_action_timeline(raw_actions_text, actual_duration)
            elif live_timeline:
                time_ratio = actual_duration / max(0.1, est_duration)
                final_timeline = [(round(t * time_ratio, 2), act_type, val) for t, act_type, val in live_timeline]
            elif pre_timeline:
                final_timeline = parse_action_timeline(raw_actions_text, actual_duration)
            else:
                final_timeline = []

            pygame.mixer.music.load(output_file)
            pygame.mixer.music.set_volume(1.0)
            
            current_ai_state = "TALKING"
            IS_MP3_PLAYING = True  # 🔴 MP3 播放開始：回音過濾閘門全程開啟！
            CURRENT_SPEECH_START_TIME = time.time()
            
            timeline_cancel_event = asyncio.Event()
            timeline_task = None
            if final_timeline and target_vts:
                timeline_task = asyncio.create_task(execute_action_timeline(target_vts, final_timeline, timeline_cancel_event))
            elif raw_actions_text and target_vts:
                await execute_speech_visual_actions(target_vts, raw_actions_text)

            pygame.mixer.music.play()
            
            await asyncio.sleep(0.2)
            while pygame.mixer.music.get_busy(): 
                await asyncio.sleep(0.05)
                
            if timeline_cancel_event:
                timeline_cancel_event.set()
            if timeline_task and not timeline_task.done():
                timeline_task.cancel()

            pygame.mixer.stop()
            pygame.mixer.music.unload()
            
            # 清除當前口型波形狀態
            CURRENT_MOUTH_ENVELOPE = []
            CURRENT_SMOOTH_MOUTH = 0.0
            CURRENT_SPEECH_START_TIME = 0.0
            
            IS_MP3_PLAYING = False
            MP3_ECHO_TRAILING_CHUNKS = 1  # 🟡 MP3 結束後：精準保留 1 次尾音攔截！
            if is_piano_active and current_piano_song_title:
                await asyncio.to_thread(update_subtitle, f"🎹 [7L 正在演奏鋼琴] 《{current_piano_song_title}》")
            else:
                await asyncio.to_thread(update_subtitle, "")
                
        except asyncio.CancelledError:
            try: pygame.mixer.music.stop()
            except: pass
            if 'timeline_cancel_event' in locals() and timeline_cancel_event:
                timeline_cancel_event.set()
            if 'timeline_task' in locals() and timeline_task and not timeline_task.done():
                timeline_task.cancel()
            IS_MP3_PLAYING = False
            MP3_ECHO_TRAILING_CHUNKS = 1
            LAST_TTS_END_TIME = time.time()
            if current_ai_state == "TALKING": current_ai_state = "IDLE"
            raise
        except Exception as e:
            log_print(f"❌ [語音合成錯誤]: {e}")
            if 'timeline_cancel_event' in locals() and timeline_cancel_event:
                timeline_cancel_event.set()
            if 'timeline_task' in locals() and timeline_task and not timeline_task.done():
                timeline_task.cancel()
            IS_MP3_PLAYING = False
            MP3_ECHO_TRAILING_CHUNKS = 1
            LAST_TTS_END_TIME = time.time()
            if current_ai_state == "TALKING": current_ai_state = "IDLE"

def capture_system_audio_chunk(duration: float = 2.5):
    """從 Windows 預設播放裝置 (WASAPI Loopback) 記憶體內截取電腦內部播放音訊與音量"""
    try:
        speaker = sc.default_speaker()
        mic = sc.get_microphone(id=str(speaker.name), include_loopback=True)
        num_frames = int(16000 * duration)
        with mic.recorder(samplerate=16000) as recorder:
            data = recorder.record(numframes=num_frames)
            
        rms = float(np.sqrt(np.mean(np.square(data))))
        if rms < 0.005:
            return None, rms
            
        if len(data.shape) > 1 and data.shape[1] > 1:
            data_mono = np.mean(data, axis=1)
        else:
            data_mono = data.flatten()
            
        audio_int16 = (np.clip(data_mono, -1.0, 1.0) * 32767).astype(np.int16)
        
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_int16.tobytes())
            
        return buf.getvalue(), rms
    except Exception:
        return None, 0.0

def transcribe_audio_bytes(wav_bytes: bytes) -> str:
    """記憶體內極速語音辨識 (STT)"""
    if not wav_bytes:
        return ""
    r = sr.Recognizer()
    try:
        buf = io.BytesIO(wav_bytes)
        with sr.AudioFile(buf) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language="zh-TW")
        return text.strip()
    except Exception:
        return ""

# ────────────────────────────────────────────────────────
# 👁️ 11. 視覺感知、畫面截圖與輕量眼角餘光
# ────────────────────────────────────────────────────────
has_printed_vision_error = False

CURSOR_ICON_CACHE = None

def get_realistic_cursor_icon():
    """動態生成高解析度、邊緣銳利之 Windows 原生滑鼠游標圖標 (含柔和陰影與黑白分明邊界)"""
    global CURSOR_ICON_CACHE
    if CURSOR_ICON_CACHE is not None:
        return CURSOR_ICON_CACHE
    try:
        from PIL import Image, ImageDraw
        cursor = Image.new('RGBA', (40, 40), (0, 0, 0, 0))
        draw = ImageDraw.Draw(cursor)
        
        # 經典 Windows 箭頭頂點座標
        poly = [(0, 0), (0, 24), (6, 19), (11, 29), (15, 27), (10, 17), (18, 17)]
        
        # 1. 柔和環境陰影 (暗透明度)
        shadow_poly = [(x + 2, y + 2) for x, y in poly]
        draw.polygon(shadow_poly, fill=(0, 0, 0, 120))
        
        # 2. 黑色外圈清晰描邊
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                draw.polygon([(x + dx, y + dy) for x, y in poly], fill=(0, 0, 0, 255))
                
        # 3. 純白箭頭本體
        draw.polygon(poly, fill=(255, 255, 255, 255))
        
        CURSOR_ICON_CACHE = cursor
        return cursor
    except Exception:
        return None

_DXCAM_CAM = None
_DXCAM_FAILED = False

def get_dxcam_cam():
    global _DXCAM_CAM, _DXCAM_FAILED
    if _DXCAM_FAILED:
        return None
    if _DXCAM_CAM is not None:
        return _DXCAM_CAM
    try:
        import dxcam
        _DXCAM_CAM = dxcam.create(output_color="RGB")
        return _DXCAM_CAM
    except Exception:
        _DXCAM_FAILED = True
        return None

def capture_screen_multi_view():
    """
    五方多視角超高清螢幕感知系統 (DXGI GPU 加速 + 硬件級 StretchBlt 極速引擎)：
    1. 🖥️ 全螢幕全景總覽圖 (含原生真實滑鼠游標貼圖)
    2. 🔍 左上象限原生細節放大圖 (Top-Left)
    3. 🔍 右上象限原生細節放大圖 (Top-Right)
    4. 🔍 左下象限原生細節放大圖 (Bottom-Left)
    5. 🔍 右下象限原生細節放大圖 (Bottom-Right)
    """
    global has_printed_vision_error
    try:
        from PIL import ImageDraw, Image
        import io
        
        screenshot = None
        
        # 1. 優先嘗試 DXGI 顯存直出 (若遊戲反作弊未阻擋，僅耗 1~3ms)
        cam = get_dxcam_cam()
        if cam is not None:
            try:
                frame = cam.grab()
                if frame is not None:
                    screenshot = Image.fromarray(frame)
            except Exception:
                pass
                
        # 2. 高效 GDI 硬件級 StretchBlt 備援引擎 (耗時僅 ~10ms，零例外重試，抗遊戲反作弊)
        if screenshot is None:
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            w = user32.GetSystemMetrics(0)
            h = user32.GetSystemMetrics(1)
            target_w = 1920 if w > 1920 else w
            target_h = int(h * (target_w / w))
            
            hdesk = user32.GetDesktopWindow()
            desk_dc = user32.GetWindowDC(hdesk)
            img_dc = gdi32.CreateCompatibleDC(desk_dc)
            mem_bmp = gdi32.CreateCompatibleBitmap(desk_dc, target_w, target_h)
            gdi32.SelectObject(img_dc, mem_bmp)
            
            # 硬件級抗鋸齒縮放 (4K ➔ 1080P 直接在驅動層完成，免 CPU Lanczos 負擔)
            gdi32.SetStretchBltMode(img_dc, 4) # 4 = HALFTONE
            gdi32.StretchBlt(img_dc, 0, 0, target_w, target_h, desk_dc, 0, 0, w, h, 0x00CC0020)
            
            class BITMAPINFOHEADER(ctypes.Structure):
                _fields_ = [
                    ('biSize', ctypes.c_uint32), ('biWidth', ctypes.c_int32), ('biHeight', ctypes.c_int32),
                    ('biPlanes', ctypes.c_uint16), ('biBitCount', ctypes.c_uint16), ('biCompression', ctypes.c_uint32),
                    ('biSizeImage', ctypes.c_uint32), ('biXPelsPerMeter', ctypes.c_int32), ('biYPelsPerMeter', ctypes.c_int32),
                    ('biClrUsed', ctypes.c_uint32), ('biClrImportant', ctypes.c_uint32)
                ]
            bmi = BITMAPINFOHEADER()
            bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.biWidth = target_w
            bmi.biHeight = -target_h
            bmi.biPlanes = 1
            bmi.biBitCount = 32
            bmi.biCompression = 0
            buf = ctypes.create_string_buffer(target_w * target_h * 4)
            gdi32.GetDIBits(img_dc, mem_bmp, 0, target_h, buf, ctypes.byref(bmi), 0)
            screenshot = Image.frombuffer('RGBA', (target_w, target_h), buf, 'raw', 'BGRA', 0, 1).convert('RGB')
            gdi32.DeleteObject(mem_bmp)
            gdi32.DeleteDC(img_dc)
            user32.ReleaseDC(hdesk, desk_dc)

        if screenshot is None:
            return None

        if screenshot.mode != "RGB":
            screenshot = screenshot.convert("RGB")
            
        w, h = screenshot.size
        # 根據實際截圖解析度與系統原始解析度比例調整滑鼠游標座標
        orig_w = ctypes.windll.user32.GetSystemMetrics(0)
        orig_h = ctypes.windll.user32.GetSystemMetrics(1)
        scale_x = w / max(1, orig_w)
        scale_y = h / max(1, orig_h)
        mx_raw, my_raw = pyautogui.position()
        mx = int(mx_raw * scale_x)
        my = int(my_raw * scale_y)
        
        # 🖱️ 自然貼合原生真實滑鼠游標圖標
        cursor_icon = get_realistic_cursor_icon()
        if cursor_icon:
            try:
                screenshot.paste(cursor_icon, (max(0, min(w - 1, mx)), max(0, min(h - 1, my))), cursor_icon)
            except Exception:
                pass
        
        # 1. 全螢幕全景總覽圖
        buf_full = io.BytesIO()
        screenshot.save(buf_full, format="JPEG", quality=75)
        full_b64 = base64.b64encode(buf_full.getvalue()).decode('utf-8')
        
        # 2. 四個象限細節裁切
        mid_x = w // 2
        mid_y = h // 2
        
        # 左上象限
        buf_tl = io.BytesIO()
        screenshot.crop((0, 0, mid_x, mid_y)).save(buf_tl, format="JPEG", quality=80)
        tl_b64 = base64.b64encode(buf_tl.getvalue()).decode('utf-8')
        
        # 右上象限
        buf_tr = io.BytesIO()
        screenshot.crop((mid_x, 0, w, mid_y)).save(buf_tr, format="JPEG", quality=80)
        tr_b64 = base64.b64encode(buf_tr.getvalue()).decode('utf-8')
        
        # 左下象限
        buf_bl = io.BytesIO()
        screenshot.crop((0, mid_y, mid_x, h)).save(buf_bl, format="JPEG", quality=80)
        bl_b64 = base64.b64encode(buf_bl.getvalue()).decode('utf-8')
        
        # 右下象限
        buf_br = io.BytesIO()
        screenshot.crop((mid_x, mid_y, w, h)).save(buf_br, format="JPEG", quality=80)
        br_b64 = base64.b64encode(buf_br.getvalue()).decode('utf-8')
        
        has_printed_vision_error = False
        return [
            ("🖥️【1. 全螢幕全景總覽（含滑鼠游標）】", full_b64),
            ("🔍【2. 左上角細節放大圖】", tl_b64),
            ("🔍【3. 右上角細節放大圖】", tr_b64),
            ("🔍【4. 左下角細節放大圖】", bl_b64),
            ("🔍【5. 右下角細節放大圖】", br_b64)
        ]
    except Exception as e:
        if not has_printed_vision_error:
            print(f"\n❌ [截圖系統報錯]: {e}")
            has_printed_vision_error = True
        return None

def capture_screen_as_base64():
    return capture_screen_multi_view()

def get_combined_temporal_screen_snapshot():
    """
    🎞️ 組合 5 圖多視角 + 最近時序連續動態影格（共 6~7 張圖）
    🎯 核心效果：
       1. 包含前 1~2 幀歷史全景截圖（時序動態感知：Gemini 清楚分辨動畫、角色位移、戰鬥、視窗滾動等連續動作）
       2. 包含此刻當前完整 5 圖多視角（1 全景總覽 + 4 象限超高清局部放大，100% 原始像素細節，徹底杜絕看不清楚）
       3. 實測 7 圖總體積僅約 80~130 KB，Gemini 響應僅耗時 1.7~2.3 秒，完全在黃金無感延遲區！
    """
    global latest_screen_cache, SCREEN_TEMPORAL_HISTORY
    if not latest_screen_cache:
        return None
    if not isinstance(latest_screen_cache, list):
        return latest_screen_cache
    
    combined = []
    # 1. 注入歷史時序動態幀 (依時間先後：較舊 ➔ 較新)
    for idx, (t_stamp, hist_b64) in enumerate(SCREEN_TEMPORAL_HISTORY):
        dt = round(time.time() - t_stamp, 1)
        combined.append((f"🎞️【時序動態幀 {idx+1} (約 {dt} 秒前歷史畫面)】", hist_b64))
        
    # 2. 注入當前最新 5 圖多視角（此刻全景總覽 + 4 象限局部放大圖）
    combined.extend(latest_screen_cache)
    return combined

async def check_screen_change_via_live_api(img_bytes: bytes, current_context: str) -> bool:
    """👁️ 【Live API 餘光視覺哨兵】：
    利用 Live API 無限額度特性保持雙眼實時看著螢幕畫面，
    絕不輸出冗長描述，只負責極速判定畫面是否有重大全新變化/新事件/新視窗 ([NO_CHANGE] vs [LOOK_SERIOUS])，
    徹底替老爸節省 3.1-flash-lite 主力發話金鑰額度！
    """
    if not img_bytes or len(img_bytes) < 1000:
        return False
        
    candidate_keys = get_dynamic_live_key_candidates(KEYS_VISION if KEYS_VISION else GEMINI_KEYS)
    for idx, g_key in enumerate(candidate_keys[:4]):
        client = genai.Client(api_key=g_key)
        try:
            live_cfg = types.LiveConnectConfig(
                response_modalities=[types.Modality.AUDIO],
                output_audio_transcription=types.AudioTranscriptionConfig(),
                system_instruction=types.Content(parts=[types.Part(text="""妳是 7L 的背景餘光視覺神經哨兵。
妳正透過雙眼看著老爸的電腦螢幕畫面。
妳的任務是保持眼睛在看，但【絕對不要輸出任何描述或聊天內容】！
妳只負責做極速二元決策：
- [NO_CHANGE]：若畫面維持在先前的操作中（如持續寫程式碼、同一個視窗/軟體中微調打字、滑鼠移動、無重大新動態），請【只輸出】: [NO_CHANGE]
- [LOOK_SERIOUS]：只有當發生重大改變（如切換到完全不同的應用程式、跳出報錯或提示視窗、開啟新遊戲/影片、完成重大部署/編譯、畫面焦點徹底改變）時，才輸出: [LOOK_SERIOUS]
嚴禁輸出任何多餘的解釋或對話，只輸出 [NO_CHANGE] 或 [LOOK_SERIOUS]！""")]),
            )
            async with asyncio.timeout(3.8):
                async with client.aio.live.connect(model="gemini-3.1-flash-live-preview", config=live_cfg) as session:
                    await session.send_realtime_input(video={"data": img_bytes, "mime_type": "image/jpeg"})
                    eval_prompt = f"前次已知畫面狀態：『{current_context}』。請看當前畫面，是否有出現重大新事件需要認真看？只輸出 [NO_CHANGE] 或 [LOOK_SERIOUS]："
                    await session.send_realtime_input(text=eval_prompt)
                    
                    decision_text = ""
                    async for resp in session.receive():
                        c = resp.server_content
                        if c:
                            if c.output_transcription and c.output_transcription.text:
                                decision_text += c.output_transcription.text
                            if c.turn_complete or getattr(c, 'generation_complete', False):
                                break
                                
                    decision_clean = decision_text.strip().upper()
                    if "[LOOK_SERIOUS]" in decision_clean or "LOOK_SERIOUS" in decision_clean:
                        return True
                    if "[NO_CHANGE]" in decision_clean or "NO_CHANGE" in decision_clean or "[SILENCE]" in decision_clean:
                        return False
        except Exception:
            continue
    return False

async def get_lightweight_gemini_vision(image_base64: str) -> str:
    """👁️ 【3.1-flash-lite 深度視覺認真看】：受 Live API 哨兵喚醒時才精準啟動，進行真實像素與 OCR 解析 (0 腦補幻想)"""
    if not image_base64:
        return ""
        
    try:
        if isinstance(image_base64, str):
            img_bytes = base64.b64decode(image_base64)
        else:
            img_bytes = image_base64
            
        if len(img_bytes) < 1000:
            return ""

        # 🛡️ 像素有效性檢測：防止螢幕休眠/全黑時 AI 產生幻覺
        try:
            test_im = Image.open(io.BytesIO(img_bytes))
            extrema = test_im.getextrema()
            if extrema == ((0, 0), (0, 0), (0, 0)) or (isinstance(extrema, tuple) and all(e == (0, 0) for e in extrema if isinstance(e, tuple))):
                return "螢幕處於休眠或全黑狀態。"
        except Exception:
            pass

        candidate_keys = get_dynamic_live_key_candidates(KEYS_VISION if KEYS_VISION else GEMINI_KEYS)
        prompt = (
            "妳是 7L 的視覺神經。請精準、客觀、簡短描述妳看到的電腦螢幕畫面內容：\n"
            "1. 老爸當前的視窗焦點在做什麼（例如：在寫程式碼、在 Discord 聊天、在瀏覽某個特定網頁、在玩遊戲等）？\n"
            "2. 畫面上有什麼具體的視窗標題、應用程式名稱、文字內容或重要資訊？\n"
            "3. 若畫面上出現 VTube Studio 視窗、Live2D 角色或 OBS 字幕，代表 7L 妳自己的虛擬化身，請忽略它，專注描述老爸正在操作的實際內容。\n"
            "請直接用 1~2 句簡短扼要的中文描述畫面的真實內容，嚴禁胡亂猜測不存在的畫面："
        )

        for idx, g_key in enumerate(candidate_keys[:4]):
            client = genai.Client(api_key=g_key)
            for model_name in ["gemini-3.1-flash-lite", "gemini-3.6-flash"]:
                try:
                    resp = await asyncio.wait_for(
                        client.aio.models.generate_content(
                            model=model_name,
                            contents=[
                                types.Content(role="user", parts=[
                                    types.Part.from_text(text=prompt),
                                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
                                ])
                            ],
                            config=types.GenerateContentConfig(temperature=0.2)
                        ),
                        timeout=4.5
                    )
                    clean_desc = resp.text.strip() if resp.text else ""
                    if clean_desc and not any(k in clean_desc for k in ["沒辦法接收", "無法接收", "視訊鏡頭", "看不到畫面", "需要鏡頭", "無法看見"]):
                        log_print(f"👁️ [餘光視覺感知] 認真看畫面：{clean_desc[:50]}... (🧠 {model_name.replace('gemini-', '')} 專用視覺)")
                        return clean_desc
                except Exception:
                    continue
    except Exception as e:
        log_print(f"⚠️ [餘光視覺異常]: {e}")
        
    return ""





# ────────────────────────────────────────────────────────
# 🧠 12. 旗艦多模態大腦推理核心 (fetch_ai_response)
# ────────────────────────────────────────────────────────
# 💡 功能目的：
#    - 7L 與老爸私下對話、深度探索與工具執行的全模態旗艦推理核心。
#    - 支援文字、5 視角全螢幕畫面影像（Base64 JPEG）、原生音訊（WAV）。
#    - 採用智能任務分流（3.1 Flash Lite ➔ 3.5 Flash Lite ➔ 3 Flash ➔ 3.1 Pro ➔ 3.5 ➔ 3.6 ➔ 3.7）。
#    - 雙軌搶答競速與自動降級（Failover），並在成功後立即調用工具或執行 Live2D 動作。

async def fetch_ai_response(messages, image_base64=None, audio_base64=None, is_proactive=False, request_start_time: Optional[float] = None):
    """
    🧠 多模態大腦推理總入口 (文字 + 視覺 + 音訊 + 工具調用)
    
    Args:
        messages: 對話歷史紀錄陣列
        image_base64: 五方多視角螢幕截圖 Base64 列表或單張圖片
        audio_base64: 麥克風音訊資料 Base64
        is_proactive: 是否為主動巡邏/主動找話題發話
        request_start_time: 請求發起的時間戳記（計算精確總延遲）
    """
    global current_ai_status_str, current_model_tag, CURRENT_GEMINI_KEY_STEP
    used_eye = "無"
    overall_start_time = request_start_time if request_start_time else time.time()

    # 防卡死機制：讓渡運算權，確保皮套滑順
    await asyncio.sleep(0.05)

    # 提取最新的使用者指令以供智能任務分流
    user_query = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            c = msg.get("content", "")
            if isinstance(c, str):
                user_query = c
            elif isinstance(c, list):
                user_query = " ".join([p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text"])
            break

    # ── 1. 建構通用多模態輸入 Payload (共用給所有併發通道) ──
    chat_contents = []
    system_text = ""
    for msg in messages:
        if msg["role"] == "system":
            system_text += msg["content"] + "\n\n"
            
    for msg in messages:
        if msg["role"] == "system": continue
        raw_content = msg["content"]
        if isinstance(raw_content, list):
            text = " ".join([p["text"] for p in raw_content if p.get("type") == "text"])
        else:
            text = raw_content
            
        if not chat_contents and system_text:
            text = system_text + text
            
        role = "user" if msg["role"] == "user" else "model"
        chat_contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))

    if image_base64:
        user_parts = []
        if isinstance(image_base64, list):
            for item in image_base64:
                if isinstance(item, tuple):
                    label, img_b64 = item
                    img_bytes = base64.b64decode(img_b64)
                    user_parts.append(types.Part.from_text(text=f"\n{label}："))
                    user_parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
                else:
                    user_parts.append(types.Part.from_bytes(data=base64.b64decode(item), mime_type="image/jpeg"))
        else:
            image_bytes = base64.b64decode(image_base64)
            user_parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

        if user_parts:
            if chat_contents and chat_contents[-1].role == "user":
                chat_contents[-1].parts.extend(user_parts)
            else:
                chat_contents.append(types.Content(role="user", parts=user_parts))

    if audio_base64:
        try:
            if isinstance(audio_base64, str):
                raw_audio_bytes = base64.b64decode(audio_base64)
            else:
                raw_audio_bytes = audio_base64
            
            audio_part = types.Part.from_bytes(data=raw_audio_bytes, mime_type="audio/wav")
            if chat_contents and chat_contents[-1].role == "user":
                chat_contents[-1].parts.append(audio_part)
            else:
                chat_contents.append(types.Content(role="user", parts=[audio_part]))
        except Exception as e_aud:
            log_print(f"⚠️ [音訊多模態封裝異常]: {e_aud}")

    # 構建 Interactions API 專用輸入 Payload
    interaction_input = []
    full_user_text = f"{system_text}\n\n{text}" if system_text else text
    interaction_input.append({"type": "text", "text": full_user_text})

    if image_base64:
        if isinstance(image_base64, list):
            for item in image_base64:
                if isinstance(item, tuple):
                    label, img_b64 = item
                    interaction_input.append({"type": "text", "text": f"\n{label}："})
                    interaction_input.append({"type": "image", "data": img_b64, "mime_type": "image/jpeg"})
                else:
                    interaction_input.append({"type": "image", "data": item, "mime_type": "image/jpeg"})
        else:
            interaction_input.append({"type": "image", "data": image_base64, "mime_type": "image/jpeg"})

    if audio_base64:
        aud_b64_str = audio_base64 if isinstance(audio_base64, str) else base64.b64encode(audio_base64).decode('utf-8')
        interaction_input.append({"type": "audio", "data": aud_b64_str, "mime_type": "audio/wav"})

    # ── 單一 Gemini 通道執行器 ──
    async def _call_single_gemini(g_key, g_model, target_id):
        temp_google_client = genai.Client(api_key=g_key)
        api_call_start = time.time()
        extracted_text = ""
        used_engine_tag = "一體化"

        try:
            active_tools = GENAI_PROACTIVE_TOOLS if is_proactive else GENAI_TOOLS
            config_kwargs = {"temperature": 0.85, "tools": active_tools}
            
            # 🧠 為 Gemini 3.8 / 3.7 / 2.5 等旗艦模型開啟原生深度思考 (Thinking)，其內在推理直接作為 7L 私密心聲
            if any(k in g_model for k in ["3.8", "3.7", "2.5", "3-flash", "3.1-pro"]):
                try:
                    config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=-1)
                except Exception:
                    pass

            gen_config = types.GenerateContentConfig(**config_kwargs)

            # 👑 放寬單通道等待時間至 120 秒，讓 3.8 / 3.7-flash 深度思考、多模態與工具調用在背景充裕完成，絕不 premature timeout！
            response = await asyncio.wait_for(
                temp_google_client.aio.models.generate_content(
                    model=g_model,
                    contents=chat_contents,
                    config=gen_config
                ),
                timeout=120.0
            )

            had_tool_calls = False
            tool_results_map = {}
            if hasattr(response, 'function_calls') and response.function_calls:
                had_tool_calls = True
                call_names = [getattr(fc, 'name', '') for fc in response.function_calls]
                for fc in response.function_calls:
                    fn_name = getattr(fc, 'name', '')
                    fn_args = getattr(fc, 'args', {}) or {}
                    if fn_name == "stop_virtual_piano" and "open_virtual_piano" in call_names:
                        log_print(f"🛡️ [工具衝突過濾] 同回合同時包含 open_virtual_piano 與 stop_virtual_piano，已自動過濾 stop_virtual_piano！")
                        continue
                    log_print(f"🛠️ [大腦調用工具] {fn_name}({fn_args})")
                    tool_out = await execute_tool_dispatch(fn_name, fn_args, caller_target="dad", caller_user="老爸")
                    tool_results_map[fn_name] = tool_out
                    # ⚠️ 資訊查詢與系統提示類資料僅供大腦吸收，嚴禁拼入 extracted_text 作為口語！
                    if fn_name not in ["search_google"] and tool_out and "[EXPRESSION:" in tool_out:
                        extracted_text += f" {tool_out}"

            model_speech = ""
            thought_text = ""
            try:
                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    for p in response.candidates[0].content.parts:
                        if getattr(p, 'thought', False) and getattr(p, 'text', ''):
                            thought_text += p.text + " "
                        elif getattr(p, 'text', '') and not getattr(p, 'thought', False):
                            model_speech += p.text + " "
                if not model_speech.strip() and response.text:
                    model_speech = response.text.strip()
            except Exception:
                try:
                    if response.text:
                        model_speech = response.text.strip()
                except Exception:
                    pass

            if thought_text.strip() and "[THOUGHT:" not in model_speech and "[THINK:" not in model_speech:
                model_speech = f"[THOUGHT: {thought_text.strip()}] {model_speech}".strip()

            # 🌟 當調用了資訊類工具 (如 search_google) 或第一輪未輸出台詞時：
            # 立即發起第二輪 Function Response 請求，將搜尋結果反饋給大腦進行深度思考、消化整理並輸出自然口語！
            if had_tool_calls:
                needs_stage2 = any(getattr(fc, 'name', '') == 'search_google' for fc in response.function_calls) or not model_speech.strip()
                if needs_stage2:
                    stage2_done = False
                    try:
                        followup_contents = list(chat_contents)
                        if response.candidates and response.candidates[0].content:
                            followup_contents.append(response.candidates[0].content)
                        else:
                            call_parts = [types.Part.from_function_call(name=getattr(fc, 'name', ''), args=getattr(fc, 'args', {}) or {}) for fc in response.function_calls]
                            followup_contents.append(types.Content(role="model", parts=call_parts))

                        fn_resp_parts = []
                        for fc in response.function_calls:
                            f_name = getattr(fc, 'name', '')
                            f_res = tool_results_map.get(f_name, "執行成功")
                            fn_resp_parts.append(types.Part.from_function_response(
                                name=f_name,
                                response={
                                    "result": str(f_res),
                                    "instruction": "請根據以上查詢結果，以 7L 招牌自然隨性口吻（1~3句短句，40~80字以內）直接對老爸提煉並說明重點，嚴禁照抄條列清單、網址或網頁標題！"
                                }
                            ))
                        followup_contents.append(types.Content(role="user", parts=fn_resp_parts))

                        stage2_resp = await asyncio.wait_for(
                            temp_google_client.aio.models.generate_content(
                                model=g_model,
                                contents=followup_contents,
                                config=types.GenerateContentConfig(temperature=0.85)
                            ),
                            timeout=25.0
                        )
                        s2_speech = ""
                        s2_thought = ""
                        if stage2_resp and stage2_resp.candidates and stage2_resp.candidates[0].content and stage2_resp.candidates[0].content.parts:
                            for p in stage2_resp.candidates[0].content.parts:
                                if getattr(p, 'thought', False) and getattr(p, 'text', ''):
                                    s2_thought += p.text + " "
                                elif getattr(p, 'text', '') and not getattr(p, 'thought', False):
                                    s2_speech += p.text + " "
                        if not s2_speech.strip() and stage2_resp and stage2_resp.text:
                            s2_speech = stage2_resp.text.strip()

                        if s2_speech.strip():
                            model_speech = s2_speech.strip()
                            if s2_thought.strip() and "[THOUGHT:" not in model_speech and "[THINK:" not in model_speech:
                                model_speech = f"[THOUGHT: {s2_thought.strip()}] {model_speech}".strip()
                            stage2_done = True
                    except Exception as e_s2:
                        log_print(f"⚠️ [搜尋情報第二輪主通道整合異常]: {e_s2} ➔ 即刻切換極速備份模型整理")

                    # 若第二輪主通道因 503 等原因失敗，且調用了 search_google，立即啟動極速提煉器整理成自然口語
                    if not stage2_done and any(getattr(fc, 'name', '') == 'search_google' for fc in response.function_calls):
                        s_query = next((getattr(fc, 'args', {}).get('query', '') for fc in response.function_calls if getattr(fc, 'name', '') == 'search_google'), user_query)
                        s_raw = tool_results_map.get("search_google", "")
                        model_speech = await summarize_search_to_speech(s_query, s_raw, user_role_name="老爸")

            # 🌟 採用 Gemini 生成的口語回覆；若調用工具帶有標籤則一併保留
            if model_speech:
                tags_in_tool = " ".join(re.findall(r'\[[A-Z_]+(?::\s*[^\]]+)?\]', extracted_text))
                valid_tags = [t for t in tags_in_tool.split() if not any(x in t for x in ["HAD_TOOL_CALL", "SEARCH", "GOOGLE"])]
                clean_tags_str = " ".join(valid_tags)
                extracted_text = f"{model_speech} {clean_tags_str}".strip()
            else:
                if any(getattr(fc, 'name', '') == 'search_google' for fc in response.function_calls):
                    s_query = next((getattr(fc, 'args', {}).get('query', '') for fc in response.function_calls if getattr(fc, 'name', '') == 'search_google'), user_query)
                    s_raw = tool_results_map.get("search_google", "")
                    extracted_text = await summarize_search_to_speech(s_query, s_raw, user_role_name="老爸")
                elif "play_virtual_piano" in tool_results_map:
                    piano_fc = next((fc for fc in response.function_calls if getattr(fc, 'name', '') == 'play_virtual_piano'), None)
                    p_name = clean_song_title_for_speech(getattr(piano_fc, 'args', {}).get('song_name', '')) if piano_fc else ''
                    if is_piano_active and current_piano_song_title:
                        extracted_text = f"[EXPRESSION: 星星眼] 老爸，沒問題！《{p_name or '這首'}》我先幫你排進清單，等現在這首彈完馬上幫你彈喔！"
                    else:
                        extracted_text = f"[EXPRESSION: 星星眼] 老爸，這就來為你彈《{p_name or '這首'}》！"
                elif "compose_and_play_original_piano" in tool_results_map:
                    extracted_text = f"[EXPRESSION: 星星眼] 老爸，收到！我現在就現場為你創作一首原創鋼琴曲，聽聽看喔！"
                elif "mashup_virtual_piano" in tool_results_map:
                    extracted_text = f"[EXPRESSION: 星星眼] 老爸，收到！雙曲狂暴合奏這就來！"
                else:
                    extracted_text = TextCleanEngine.remove_system_hints(extracted_text).strip()

            if extracted_text.strip() or had_tool_calls:
                api_duration = time.time() - api_call_start
                return (extracted_text.strip(), used_engine_tag, api_duration, g_model, target_id)
            raise ValueError(f"通道 {target_id} 未回傳有效文字內容")

        except asyncio.CancelledError:
            return None
        except (asyncio.TimeoutError, TimeoutError):
            # ⏳ 屬於背景深度思考或已由其他競速通道搶答，不視為大腦異常，絕不鎖定金鑰通道！
            return None
        except Exception as e:
            if isinstance(e, (asyncio.TimeoutError, TimeoutError)) or "timeout" in type(e).__name__.lower():
                return None
            err_str = str(e).lower()
            record_model_failure(g_model, err_str)
            if "503" in err_str or "unavailable" in err_str or "high demand" in err_str:
                lock_target(target_id, "503 high demand")
            elif "404" in err_str or "not_found" in err_str or "no longer available" in err_str:
                if 'DEAD_GEMINI_MODELS' in globals():
                    DEAD_GEMINI_MODELS.add(g_model)
                lock_entire_model(g_model, duration=get_seconds_until_pt_midnight(), reason="404 下架/未開通")
                lock_target(target_id, "404 not found")
            elif "429" in err_str or "rate limit" in err_str or "resource" in err_str or "quota" in err_str:
                lock_target(target_id, str(e))
            elif "timeouterror" in err_str or "timeout" in err_str:
                pass
            else:
                clean_err = str(e).replace('\n', ' ').strip()[:50]
                display_err = clean_err if clean_err else type(e).__name__
                log_print(f"⚠️ [大腦異常] 通道 {target_id}: {display_err}")
                lock_target(target_id, "wait 30s")
            return None

    # 🌟 第一防線：主力 Gemini 旗艦大腦（5 秒階梯式併發競速：5秒未回覆時原請求不中斷，加開新通道雙軌/多軌搶答！）
    max_gemini_attempts = 45 
    active_gemini_tasks = {}  # task -> (target_id, g_model, start_time)
    launched_gemini_targets = set()

    while len(launched_gemini_targets) < max_gemini_attempts:
        await asyncio.sleep(0.01)
        
        # 嚴格限制同時進行的通道數最多為 2 個，杜絕同時爆發 20 個併發把所有金鑰配額瞬間打滿
        if len(active_gemini_tasks) < 2:
            channels = get_available_gemini_channels(limit=5, user_query=user_query, has_image=bool(image_base64), is_proactive=is_proactive)
            candidate = None
            for ch in channels:
                if ch[2] not in launched_gemini_targets:
                    candidate = ch
                    break

            if candidate:
                g_key, g_model, target_id = candidate
                launched_gemini_targets.add(target_id)
                
                # 每次依序派發一個通道，立即推進交替序輪指針至下一回步數
                CURRENT_GEMINI_KEY_STEP += 1

                task = asyncio.create_task(_call_single_gemini(g_key, g_model, target_id))
                active_gemini_tasks[task] = (target_id, g_model, time.time())
                
                status_prefix = "👁️🧠" if image_base64 else "🧠"
                concurrent_count = len(active_gemini_tasks)
                concur_tag = f" [雙軌搶答: {concurrent_count}]" if concurrent_count > 1 else ""
                current_ai_status_str = f"{status_prefix} {g_model} [{target_id}]{concur_tag} 思考中..."
                if concurrent_count > 1:
                    log_print(f"🚀 [雙軌競速] 依序輪流加開新通道 {target_id} 搶答 (目前共 2 個通道併發)")

        if not active_gemini_tasks:
            break

        # 等待深度思考模型完成（充裕等待，不 premature timeout 搶截深度推理）
        done, _ = await asyncio.wait(
            active_gemini_tasks.keys(),
            timeout=12.0,
            return_when=asyncio.FIRST_COMPLETED
        )

        if done:
            for finished_task in done:
                t_id, m_name, t_start = active_gemini_tasks.pop(finished_task)
                try:
                    res = finished_task.result()
                    if res:
                        extracted_text, used_engine_tag, api_duration, win_model, win_tid = res
                        # 🏁 率先成功奪冠！取消其他所有背景併發中的任務
                        for rem_task in list(active_gemini_tasks.keys()):
                            rem_task.cancel()
                        active_gemini_tasks.clear()

                        total_duration = time.time() - overall_start_time
                        time_stat = f" [總耗時: {total_duration:.2f}s | 深度思考: {api_duration:.2f}s]"
                        MODEL_FAIL_COUNT[win_model] = 0
                        if image_base64 and audio_base64:
                            current_model_tag = f"🧠🎙️👁️ {win_model} ({used_engine_tag} 全模態){time_stat}"
                        elif audio_base64:
                            current_model_tag = f"🧠🎙️ {win_model} ({used_engine_tag} 音訊直連){time_stat}"
                        elif image_base64:
                            current_model_tag = f"🧠👁️ {win_model} ({used_engine_tag} 視覺){time_stat}"
                        else:
                            current_model_tag = f"🧠 {win_model} ({used_engine_tag}){time_stat}"
                        return extracted_text.strip()
                except Exception:
                    pass
        else:
            # 12 秒到期：日誌提示，原任務不中斷繼續跑，依序輪流加開雙軌！
            running_names = [active_gemini_tasks[t][0] for t in active_gemini_tasks]
            log_print(f"⏱️ [深度思考中] 通道 {', '.join(running_names)} 推理中 ➔ 原請求不中斷繼續跑，依序加開下一把金鑰熱備！")

    # 若所有通道均已啟動，等待仍在運行的任務
    if active_gemini_tasks:
        try:
            done, _ = await asyncio.wait(
                active_gemini_tasks.keys(),
                timeout=10.0,
                return_when=asyncio.FIRST_COMPLETED
            )
            for finished_task in done:
                t_id, m_name, t_start = active_gemini_tasks.pop(finished_task)
                try:
                    res = finished_task.result()
                    if res:
                        extracted_text, used_engine_tag, api_duration, win_model, win_tid = res
                        for rem_task in list(active_gemini_tasks.keys()):
                            rem_task.cancel()
                        active_gemini_tasks.clear()
                        total_duration = time.time() - overall_start_time
                        time_stat = f" [總耗時: {total_duration:.2f}s | 思考: {api_duration:.2f}s]"
                        MODEL_FAIL_COUNT[win_model] = 0
                        if image_base64 and audio_base64:
                            current_model_tag = f"🧠🎙️👁️ {win_model} ({used_engine_tag} 全模態){time_stat}"
                        elif audio_base64:
                            current_model_tag = f"🧠🎙️ {win_model} ({used_engine_tag} 音訊直連){time_stat}"
                        elif image_base64:
                            current_model_tag = f"🧠👁️ {win_model} ({used_engine_tag} 視覺){time_stat}"
                        else:
                            current_model_tag = f"🧠 {win_model} ({used_engine_tag}){time_stat}"
                        return extracted_text.strip()
                except Exception:
                    pass
        except Exception:
            pass
        for rem_task in list(active_gemini_tasks.keys()):
            rem_task.cancel()
        active_gemini_tasks.clear()

    # 🌟 第二防線：若 Gemini 旗艦大腦全部不可用且有畫面，嘗試輕量雲端餘光
    if image_base64:
        current_ai_status_str = "👁️ 備用視覺提取中 (雲端輕量版)..."
        local_desc = ""
        if not is_system_overloaded():
            try: 
                local_desc = await get_lightweight_gemini_vision(image_base64)
            except Exception: 
                pass
                
        if local_desc:
            used_eye = "gemini-lite"
            if messages and messages[-1]["role"] == "user": 
                inject_text = f"\n\n【備用視覺情報】：畫面描述: {local_desc}\n【鐵律】：畫面上的白色箭頭代表老爸當前的滑鼠游標。請注意：【除非滑鼠正指著某個你覺得很有趣、或特別值得注意的東西，否則請自然看待，不需要刻意強調滑鼠位置】。自然流暢表達，不限制說話長度！"
                
                if isinstance(messages[-1]["content"], list):
                    messages[-1]["content"].append({"type": "text", "text": inject_text})
                else:
                    messages[-1]["content"] += inject_text

    log_print("⚠️ [大腦提示] 本輪所有 Gemini 通道皆繁忙/超時，為維持純淨發話，本輪靜默略過。")
    return ""

# ────────────────────────────────────────────────────────
# 🕹️ 13. 使用者指令、電腦控制與計時器動作
# ────────────────────────────────────────────────────────
def get_system_performance():
    try:
        cpu_usage = psutil.cpu_percent(interval=0.3)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        gpu_name = "未知顯示卡"
        
        result = subprocess.run(["wmic", "path", "win32_videocontroller", "get", "name"], capture_output=True, text=True, shell=True)
        lines = [line.strip() for line in result.stdout.split("\n") if line.strip() and "Name" not in line]
        if lines: gpu_name = lines[0]

        process_list = []
        for proc in psutil.process_iter(['name', 'memory_percent']):
            try:
                pinfo = proc.info
                ignore_list = ['svchost.exe', 'csrss.exe', 'wininit.exe', 'services.exe', 'lsass.exe', 'System Idle Process', 'System', 'Registry', 'smss.exe']
                if pinfo['name'] and pinfo['name'] not in ignore_list and pinfo['memory_percent'] is not None:
                    clean_name = pinfo['name'].replace('.exe', '')
                    process_list.append((clean_name, pinfo['memory_percent']))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        process_list.sort(key=lambda x: x[1], reverse=True)
        seen_apps = []
        for p_name, _ in process_list:
            if p_name not in seen_apps: seen_apps.append(p_name)
            if len(seen_apps) >= 3: break
            
        app_str = f"，目前佔用最多資源的軟體是：{', '.join(seen_apps)}" if seen_apps else ""
        return f"CPU 使用率: {cpu_usage}%, 記憶體: {memory_usage}%{app_str}"
    except Exception as e:
        return f"無法讀取系統狀態: {e}"

async def set_timer(seconds, message, input_queue):
    try:
        await asyncio.sleep(seconds)
        await input_queue.put(f"（系統鬧鐘提醒：時間到了！內容是：{message}。請溫柔地提醒使用者！）")
    except asyncio.CancelledError:
        pass
    finally:
        task = asyncio.current_task()
        if task in active_timers: active_timers.remove(task)

async def execute_speech_visual_actions(vts, text: str):
    """🎭 語音同步專用 Live2D 演出控制器：
    精準在語音【真正開口發話播放】的瞬間觸發本句專屬的表情、走位、眨眼、視線與身體動作，
    杜絕連續說話時下一句還在排隊、動作卻提前偷跑的脫節問題！
    """
    global vc.target_look_x, vc.target_look_y, vc.is_tracking_mouse, vc.force_blink_trigger, vc.eye_roll_timer, vc.shock_timer, vc.wink_timer, vc.wink_side, vc.frown_timer
    if not text:
        return
        
    exp_match = re.search(r'\[EXPRESSION:\s*([^\]]+)\]', text, re.IGNORECASE)
    if exp_match:
        exp_tag = exp_match.group(1).strip()
        if any(k in exp_tag.upper() for k in ["WINK", "眨眼", "單眼", "眨單眼"]):
            vc.wink_timer = time.time() + 0.55
            vc.wink_side = random.choice(["left", "right"])
            log_print(f"😉 [Live2D 動作] 標籤觸發 Wink 單眼眨一下眼 ({vc.wink_side})")
        elif any(k in exp_tag for k in ["震驚", "震惊", "瞳孔", "嚇到", "SHOCK"]):
            vc.shock_timer = time.time() + 4.0
            log_print("😱 [Live2D 動作] 標籤觸發震驚縮瞳與恐懼顫抖")
        elif any(k in exp_tag for k in ["皺眉", "皱眉", "八字眉", "困擾", "困扰", "委屈", "傲嬌皺眉", "難過眉", "生氣皺眉", "FROWN"]):
            vc.frown_timer = time.time() + 4.0
            log_print("🥺 [Live2D 動作] 標籤觸發傲嬌八字皺眉/委屈表情")
        else:
            log_print(f"🎭 [Live2D 表情] 標籤觸發表情: 「{exp_tag}」")
            asyncio.create_task(set_vts_expression(vts, exp_tag))

    move_match = re.search(r'\[(?:MOVE|SPATIAL|WINDOW|POSITION)[：:]\s*([^\]]+)\]', text, re.IGNORECASE)
    if move_match:
        pos_tag = move_match.group(1).strip()
        if not is_piano_active or any(k in pos_tag for k in ["鋼琴", "原本", "大小", "視窗"]):
            log_print(f"🚶 [Live2D 走位] 標籤觸發模型移動至: 「{pos_tag}」")
            asyncio.create_task(apply_spatial_position(pos_tag))

    try:
        upper_text = text.upper()
        if "WINK" in upper_text and not exp_match:
            vc.wink_timer = time.time() + 0.55
            vc.wink_side = random.choice(["left", "right"])
            log_print(f"😉 [Live2D 動作] 動作觸發 Wink 單眼眨一下眼 ({vc.wink_side})")
        elif any(k in upper_text for k in ["SHOCK", "SHOCKED", "PUPIL", "震驚", "震惊", "瞳孔", "嚇到"]) and not exp_match:
            vc.shock_timer = time.time() + 4.0
            log_print("😱 [Live2D 動作] 動作觸發震驚縮瞳與恐懼顫抖")
        elif any(k in upper_text for k in ["FROWN", "FROWNING", "皺眉", "皱眉", "八字眉", "困擾", "委屈"]) and not exp_match:
            vc.frown_timer = time.time() + 4.0
            log_print("🥺 [Live2D 動作] 動作觸發傲嬌八字皺眉/委屈神態")
        elif any(k in upper_text for k in ["ROLL", "AROUND", "WANDER", "轉眼", "環視"]):
            vc.is_tracking_mouse = False
            vc.eye_roll_timer = time.time() + 3.8
            log_print("🌀 [Live2D 動作] 動作觸發招牌靈動轉眼珠環視四周")
        elif "MOUSE" in upper_text and "LOOK" in upper_text:
            vc.is_tracking_mouse = True
            log_print("👀 [Live2D 視線] 視線切換為鎖定追蹤滑鼠游標")
        elif "LEFT" in upper_text and "LOOK" in upper_text:
            vc.is_tracking_mouse = False; vc.target_look_x, vc.target_look_y = -25.0, 0.0
            log_print("👀 [Live2D 視線] 視線轉向【左邊】")
        elif "RIGHT" in upper_text and "LOOK" in upper_text:
            vc.is_tracking_mouse = False; vc.target_look_x, vc.target_look_y = 25.0, 0.0
            log_print("👀 [Live2D 視線] 視線轉向【右邊】")
        elif "UP" in upper_text and "LOOK" in upper_text:
            vc.is_tracking_mouse = False; vc.target_look_x, vc.target_look_y = 0.0, 25.0
            log_print("👀 [Live2D 視線] 視線轉向【上方】")
        elif "DOWN" in upper_text and "LOOK" in upper_text:
            vc.is_tracking_mouse = False; vc.target_look_x, vc.target_look_y = 0.0, -25.0
            log_print("👀 [Live2D 視線] 視線轉向【下方】")
        elif "CENTER" in upper_text and "LOOK" in upper_text:
            vc.is_tracking_mouse = False; vc.target_look_x, vc.target_look_y = 0.0, 0.0
            log_print("👀 [Live2D 視線] 視線回正【正前方】")

        if "EARS" in upper_text:
            vc.force_blink_trigger = 1
            log_print("🐰 [Live2D 動作] 動作觸發耳朵抖動/眨眼")
    except Exception:
        pass

async def execute_actions(vts, text, input_queue, user_input_ctx: str = "", has_dispatched_tool: bool = False, execute_visuals: bool = False):
    """集中式系統動作與指令過濾器 (即刻執行底層系統動作/工具，並產出口語純淨文字)"""
    global active_timers, LAST_PIANO_PLAY_START_TIME
    
    # 🧠 提取並記錄 7L 大腦私密心想 (Inner Monologue)
    extracted_thought, text_without_thought = TextCleanEngine.extract_thought(text)
    if extracted_thought:
        log_print(f"🧠 [7L 腦內心想] 💭 {extracted_thought}")
        record_internal_thought(user_input_ctx, extracted_thought)
        text = text_without_thought

    if bool(re.search(r'\[HAD_TOOL_CALL\]', text, re.IGNORECASE)):
        has_dispatched_tool = True

    # 🧠 7L 自主雲端大腦演進標籤攔截 [UPDATE_PROMPT: ...] / [ADD_EXAMPLE: ...] / [LEARN_MEME: ...] / [LEARN_FACT: ...] / [UPDATE_RULE: ...]
    for up in re.finditer(r'\[(?:UPDATE_PROMPT|UPDATE_KNOWLEDGE|SET_PROMPT)[：:]\s*([^|\]]+)\|([^\]]+)\]', text, re.IGNORECASE):
        f_name = up.group(1).strip()
        f_val = up.group(2).strip()
        if f_name and f_val:
            asyncio.create_task(update_cloud_prompt_field(f_name, f_val))
            text = text.replace(up.group(0), "")

    for ae in re.finditer(r'\[(?:ADD_EXAMPLE|LEARN_EXAMPLE)[：:]\s*([^|\]]+)\|([^|\]]+)\|([^|\]]+)\|([^\]]+)\]', text, re.IGNORECASE):
        sc = ae.group(1).strip()
        ui = ae.group(2).strip()
        th = ae.group(3).strip()
        rp = ae.group(4).strip()
        if sc and rp:
            asyncio.create_task(add_few_shot_example(sc, ui, th, rp))
            text = text.replace(ae.group(0), "")

    for lm in re.finditer(r'\[LEARN_MEME[：:]\s*([^\]]+)\]', text, re.IGNORECASE):
        meme_val = lm.group(1).strip()
        if meme_val:
            asyncio.create_task(learn_new_meme(meme_val))
            text = text.replace(lm.group(0), "")

    for lf in re.finditer(r'\[LEARN_FACT[：:]\s*([^\]]+)\]', text, re.IGNORECASE):
        fact_val = lf.group(1).strip()
        if fact_val:
            asyncio.create_task(learn_new_fact(fact_val))
            text = text.replace(lf.group(0), "")

    for lr in re.finditer(r'\[(?:UPDATE_RULE|SET_RULE|LEARN_RULE)[：:]\s*([^\]]+)\]', text, re.IGNORECASE):
        rule_val = lr.group(1).strip()
        if rule_val:
            asyncio.create_task(update_custom_rule(rule_val))
            text = text.replace(lr.group(0), "")

    # ⚡ 檢測 7L 自我插話標籤 [INTERRUPT_SELF] / [CUT_IN] / [插話] / [中斷]
    if bool(re.search(r'\[(?:INTERRUPT_SELF|CUT_IN|INTERRUPT|SELF_INTERRUPT|插話|中斷|打斷自己)\]', text, re.IGNORECASE)):
        log_print("⚡ [7L 自我插話] 檢測到 [INTERRUPT_SELF] 標籤，立即秒級打斷當前正在說的話！")
        asyncio.create_task(interrupt_current_speech(clear_queue=True, reason="7L 自由意志自我插話"))

    # 📐 記住 VTS 模型基準位置與大小 (當老爸說「記住大小」、「記住位置」時即刻執行)
    if any(k in text or k in user_input_ctx for k in ["記住大小", "記住位置", "記住現在位置", "記住當前位置", "記住現在大小", "記錄位置", "記錄大小", "記住模型位置", "記住模型", "記錄基準大小", "記錄基準位置", "記住當前大小"]):
        log_print("📐 [VTS 模型記憶] 正在向 VTube Studio 讀取並保存當前模型座標與大小為基準...")
        asyncio.create_task(fetch_vts_base_model_pos(vc.GLOBAL_VTS))

    # 🚶 走位指令標籤攔截 [MOVE: ...] / [SPATIAL: ...] / [POSITION: ...]
    move_tag_m = re.search(r'\[(?:MOVE|SPATIAL|POSITION|WINDOW)[：:]\s*([^\]]+)\]', text, re.IGNORECASE)
    if move_tag_m:
        raw_pos_tag = move_tag_m.group(1).strip()
        log_print(f"🚶 [走位標籤攔截] 檢測到走位標籤: 「{raw_pos_tag}」，立即平滑移動模型！")
        asyncio.create_task(apply_spatial_position(raw_pos_tag))
        has_dispatched_tool = True
        text = text.replace(move_tag_m.group(0), "")

    # 🚶 走位代碼調用容錯攔截 move_spatial_position('...')
    move_fn_m = re.search(r'move_spatial_position\s*\(\s*[\'"]?([^\'",\)]+)[\'"]?\s*\)', text, re.IGNORECASE)
    if move_fn_m:
        raw_pos_arg = move_fn_m.group(1).strip()
        log_print(f"🚶 [走位代碼攔截] 檢測到走位代碼: move_spatial_position('{raw_pos_arg}')，立即平滑移動模型！")
        asyncio.create_task(apply_spatial_position(raw_pos_arg))
        has_dispatched_tool = True
        text = text.replace(move_fn_m.group(0), "")

    # 🚶 若使用者語音/文字包含走位指令，但大腦未標註 [MOVE: ...] 且未調用工具，自動觸發物理走位保底！
    if not has_dispatched_tool and user_input_ctx:
        clean_u_ctx = user_input_ctx.strip().lower()
        spatial_keywords = [
            "往右", "向右", "右移", "再過去右邊", "過去右邊", "去右邊", "到右邊", "右邊一點", "右多一點", "再過去一點", "過去一點", "右邊多一點",
            "往左", "向左", "左移", "再過去左邊", "過去左邊", "去左邊", "到左邊", "左邊一點", "左多一點", "左邊多一點",
            "往上", "向上", "上移", "上邊一點", "往上邊", "往下", "向下", "下移", "下邊一點", "往下邊",
            "去中間", "到中間", "正中間", "置中", "過來中間", "回中間", "走中間",
            "靠近", "貼近", "大一點", "放大", "變大", "遠離", "小一點", "縮小", "變小",
            "躲角落", "去角落", "角落",
            "原位", "回到原位", "原本位置", "復原"
        ]
        if any(k in clean_u_ctx for k in spatial_keywords):
            log_print(f"🚶 [走位語意保底] 檢測到老爸走位指示「{user_input_ctx}」，自動觸發物理走位！")
            asyncio.create_task(apply_spatial_position(user_input_ctx))
            has_dispatched_tool = True

    # 🎹 攔截模型在文字中輸出的裸 JSON 點歌指令 (例如 {"song_name": "..."})
    song_json_m = re.search(r'\{\s*"song_name"\s*:\s*"([^"]+)"\s*\}', text, re.IGNORECASE)
    if song_json_m:
        raw_song_name = song_json_m.group(1).strip()
        log_print(f"🎹 [JSON 點歌容錯攔截] 檢測到模型以 JSON 格式點歌: 《{raw_song_name}》，立即自動啟動鋼琴演奏！")
        asyncio.create_task(play_virtual_piano(song_name=raw_song_name))
        has_dispatched_tool = True
        text = text.replace(song_json_m.group(0), "")

    # 🎹 攔截模型在文字中輸出的標籤點歌指令 (例如 [PLAY_VIRTUAL_PIANO: song_name='蕭邦 冬風', auto_radio_mode=True] 或 [PLAY_VIRTUAL_PIANO: 花之塔])
    piano_tag_m = re.search(r'\[(?:PLAY_VIRTUAL_PIANO|PLAY_PIANO|PLAY_SONG)[：:]\s*([^\]]+)\]', text, re.IGNORECASE)
    if piano_tag_m:
        tag_args_raw = piano_tag_m.group(1).strip()
        parsed_song_name = ""
        parsed_auto_radio = False
        s_name_m = re.search(r'(?:song_name|title)\s*=\s*[\'"]?([^\'",\]]+)[\'"]?', tag_args_raw, re.IGNORECASE)
        if s_name_m:
            parsed_song_name = s_name_m.group(1).strip()
        else:
            parsed_song_name = tag_args_raw.split(',')[0].strip().strip('\'"')
            
        if re.search(r'auto_radio_mode\s*=\s*(?:True|1)', tag_args_raw, re.IGNORECASE):
            parsed_auto_radio = True
            
        log_print(f"🎹 [標籤點歌攔截] 檢測到模型以標籤點歌: 《{parsed_song_name}》(電台模式={parsed_auto_radio})，立即自動啟動鋼琴演奏！")
        asyncio.create_task(play_virtual_piano(song_name=parsed_song_name, auto_radio_mode=parsed_auto_radio))
        has_dispatched_tool = True
        text = text.replace(piano_tag_m.group(0), "")

    # 🎹 攔截多曲合奏標籤 (例如 [MASHUP_VIRTUAL_PIANO: song_name1=...])
    mashup_tag_m = re.search(r'\[(?:MASHUP_VIRTUAL_PIANO|MASHUP_PIANO)[：:]\s*([^\]]+)\]', text, re.IGNORECASE)
    if mashup_tag_m:
        m_args_raw = mashup_tag_m.group(1).strip()
        log_print(f"🎹 [標籤合奏攔截] 檢測到模型以標籤合奏: {m_args_raw}，立即自動啟動合奏！")
        asyncio.create_task(mashup_virtual_piano(m_args_raw))
        has_dispatched_tool = True
        text = text.replace(mashup_tag_m.group(0), "")

    # 🎹 攔截插歌標籤 [INSERT_VIRTUAL_PIANO: ...]
    insert_tag_m = re.search(r'\[(?:INSERT_VIRTUAL_PIANO|INSERT_PIANO)[：:]\s*([^\]]+)\]', text, re.IGNORECASE)
    if insert_tag_m:
        ins_raw = insert_tag_m.group(1).strip()
        ins_name_m = re.search(r'(?:song_name|title)\s*=\s*[\'"]?([^\'",\]]+)[\'"]?', ins_raw, re.IGNORECASE)
        if ins_name_m:
            ins_name = ins_name_m.group(1).strip()
        else:
            ins_name = ins_raw.split(',')[0].strip().strip('\'"')
        log_print(f"🎹 [標籤插歌攔截] 檢測到模型插歌標籤: 《{ins_name}》")
        asyncio.create_task(insert_virtual_piano(song_name=ins_name))
        has_dispatched_tool = True
        text = text.replace(insert_tag_m.group(0), "")

    # 🎹 檢測老爸/聊天室貼出 YouTube 連結並點歌
    yt_link_m = re.search(r'https?://[^\s]+(?:youtube\.com|youtu\.be)[^\s]*', text + " " + user_input_ctx)
    if yt_link_m:
        yt_url = yt_link_m.group(0)
        log_print(f"🎹 [YouTube 連結點歌] 檢測到 YouTube 影片連結點播: {yt_url}，立即自動解析下載轉 MIDI 演奏！")
        asyncio.create_task(play_virtual_piano(song_name=yt_url, force_online=True))
        has_dispatched_tool = True

    # 🎹 檢測老爸/聊天室指定「youtuber 查 / youtube 搜 / yt 查 ... 然後彈」
    yt_cmd_m = re.search(r'(?:youtuber|youtube|yt|從yt|從youtube|去yt|去youtube)\s*(?:查|搜|找|搜尋|下載)?\s*(.*?)\s*(?:然後彈|來彈|彈出來|放出來|彈一下|彈|播放|放)+$', user_input_ctx.strip(), re.IGNORECASE)
    if not yt_cmd_m:
        yt_cmd_m = re.search(r'(?:查|搜|找|搜尋|下載)\s*(?:youtuber|youtube|yt)\s*(.*?)\s*(?:然後彈|來彈|彈出來|放出來|彈一下|彈|播放|放)+$', user_input_ctx.strip(), re.IGNORECASE)
    if yt_cmd_m:
        yt_target_song = yt_cmd_m.group(1).strip()
        if yt_target_song and len(yt_target_song) >= 2:
            log_print(f"🎬 [YouTube 點歌指令直通] 檢測到指定 YouTube 查譜: 《{yt_target_song}》，100% 跳過本地樂譜，強制線上即時抓譜演奏！")
            asyncio.create_task(play_virtual_piano(song_name=yt_target_song, force_online=True))
            has_dispatched_tool = True

    # 🎹 解析獨立鋼琴視窗指令標籤 [OPEN_VIRTUAL_PIANO] / [STOP_VIRTUAL_PIANO]
    if re.search(r'\[(?:OPEN_VIRTUAL_PIANO|OPEN_PIANO|SHOW_PIANO)\]', text, re.IGNORECASE):
        log_print("🎹 [標籤自動履約] 檢測到 [OPEN_VIRTUAL_PIANO] 標籤，立即拿出 88 鍵鋼琴視窗待命！")
        asyncio.create_task(execute_tool_dispatch("open_virtual_piano", {}))
        has_dispatched_tool = True
    elif re.search(r'\[(?:STOP_VIRTUAL_PIANO|STOP_PIANO|CLOSE_PIANO)\]', text, re.IGNORECASE):
        log_print("🎹 [標籤自動履約] 檢測到 [STOP_VIRTUAL_PIANO] 標籤，立即關閉鋼琴視窗並回到原位！")
        asyncio.create_task(execute_tool_dispatch("stop_virtual_piano", {}))
        has_dispatched_tool = True

    url_match = re.search(r'\[OPEN_BROWSER:\s*([^\]]+)\]', text, re.IGNORECASE)
    if url_match:
        url = url_match.group(1).strip()
        if not url.startswith('http'):
            url = 'https://' + url
        try:
            webbrowser.open(url)
            log_print(f"🌐 [系統動作] 7L 幫你打開了網頁: {url}")
        except Exception as e:
            log_print(f"❌ [開啟網頁失敗]: {e}")

    # 若指定立即執行視覺動作 (例如安靜沉思不發聲時的微眼神/微表情)
    if execute_visuals:
        await execute_speech_visual_actions(vts, text)

    clean_text = TextCleanEngine.clean_speech_text(text)
    return clean_text

# ────────────────────────────────────────────────────────
# ⚙️ 14. 專屬背景工作協程群 (Workers)
# ────────────────────────────────────────────────────────

# --- 🎤 語音與收音協程 ---
is_user_listening = False
listen_start_time = 0.0

async def mic_volume_worker():
    global current_mic_volume_str, current_ai_state, IS_MIC_ENABLED
    
    stream = None
    if HAS_PYAUDIO:
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        except Exception:
            pass 

    while True:
        if not IS_MIC_ENABLED:
            current_mic_volume_str = "[🔴 麥克風已關閉]"
            await asyncio.sleep(0.3)
            continue

        # 🎙️ 全雙工真·不鎖麥：已有專屬聲紋辨識 (WeSpeaker/Voiceprint)，發話中依然保持全時收音監測與音量跳動
        if stream:
            try:
                frames_avail = stream.get_read_available()
                if frames_avail > 0:
                    data = stream.read(frames_avail, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    if len(audio_data) > 0:
                        rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))
                        vol_percent = min(100, int((rms / 2500) * 100))
                        bars = vol_percent // 10
                        bar_str = "█" * bars + "_" * (10 - bars)
                        current_mic_volume_str = f"[🎤 收音: {vol_percent:02d}% |{bar_str}|]"
                await asyncio.sleep(0.05) 
            except Exception:
                current_mic_volume_str = "[🟢 麥克風全時就緒]"
                await asyncio.sleep(0.5)
        else:
            current_mic_volume_str = "[🟢 麥克風全時就緒]"
            await asyncio.sleep(0.5)

def listen_once_fast(recognizer):
    global is_user_listening, listen_start_time, current_mic_action_str
    text = ""
    audio_b64 = None
    try:
        current_mic_action_str = "待命"
        with sr.Microphone() as source:
            is_user_listening = True
            listen_start_time = time.time()
            # 🎙️ 純 VAD 語音活動偵測：單次發話上限 15 秒，避免長時間持續收錄喇叭殘響
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=15.0)
            
        is_user_listening = False
        current_mic_action_str = "☁️ 語音多模態分析中..."
        
        # 🎙️ 擷取完整原始 WAV 音訊資料，供 Gemini 原生音訊多模態直連
        try:
            wav_bytes = audio.get_wav_data()
            if wav_bytes and len(wav_bytes) > 2000:
                audio_b64 = base64.b64encode(wav_bytes).decode('utf-8')
        except Exception:
            pass

        # 取得快速文字預覽（保留作為快速指令匹配與終端狀態列顯示）
        try:
            text = recognizer.recognize_google(audio, language="zh-TW")
        except Exception:
            pass
            
        return (text.strip() if text else "", audio_b64)
    except Exception:
        is_user_listening = False
        current_mic_action_str = "待命"
        return ("", None)

def check_immediate_shutdown(text: str) -> bool:
    """毫秒級即時關機 / 重開機攔截：
    必須帶有 7L / 阿七 等明確目標前綴（如「7L關機」、「7L重開機」、「阿七關機」，
    並包含中文語音辨識 ASR 常見同音詞如「謝龍重開機」、「CL重開機」、「西L重開機」），
    或終端單獨輸入 exit / quit / reboot / restart，避免日常對話提及「關機」「重開」時誤觸。
    """
    global current_piano_process, SOUND_ENGINE
    if not text:
        return False
    
    clean = unicodedata.normalize('NFKC', str(text)).strip().lower()
    clean_compact = re.sub(r'[\s，。！？,.!?:;~～`\'"（）()\[\]【】\-_]+', '', clean)
    if not clean_compact:
        return False

    # 🛑 否定詞防護：若含有「不要 / 別 / 不能 / 請勿 / 取消」等否定詞，絕對不觸發關機或重開
    if any(neg in clean_compact for neg in ["不要", "別", "别", "不能", "請勿", "请勿", "取消"]):
        return False

    # 🛑 過去式疑問句防護：如「關機了嗎」、「重開機了嗎」
    if clean_compact.endswith("了嗎") or clean_compact.endswith("了吗"):
        return False

    # 🎯 目標判定：指名 7L / 7l / 七L / 阿七 / 小七 / 七妹，並加入中文語音常見同音詞 (謝龍 / CL / 西L 等)
    target_names = [
        "7l", "七l", "cl", "謝龍", "谢龙", "西l", "吸l", 
        "奇l", "琪l", "期l", "氣l", "切爾", "琪兒", 
        "阿七", "小七", "七妹", "7妹", "7哥", "七哥"
    ]
    has_target = any(name in clean_compact for name in target_names)

    # 🔄 即時重開機指令 (0.001s 安全硬中斷並自動重啟主程序)
    # 支援：7L重開機、謝龍重開機、CL重開機、7L重啟、阿七重開機，或終端純輸入 reboot / restart
    is_exact_restart = clean_compact in ["reboot", "restart", "7lreboot", "7lrestart"]
    restart_keywords = ["重開機", "重開", "重啟", "重新啟動", "重啟系統", "重新開機", "restart", "reboot"]
    has_restart_cmd = has_target and any(k in clean_compact for k in restart_keywords)

    if is_exact_restart or has_restart_cmd:
        log_print(f"🔄 [系統] 收到即時重開機指令「{text.strip()}」，正在重新啟動 7L 系統...")
        if current_piano_process and current_piano_process.poll() is None:
            try:
                current_piano_process.terminate()
            except Exception:
                pass
        if SOUND_ENGINE:
            SOUND_ENGINE.all_notes_off()
        try:
            subprocess.Popen([sys.executable] + sys.argv)
        except Exception as e:
            log_print(f"⚠️ [重啟失敗]: {e}")
        os._exit(0)
        return True

    # 👋 即時安全退出 / 關機指令 (0.001s 安全硬終止)
    # 支援：7L關機、謝龍關機、CL關機、7L強制關機、7L關閉系統、阿七關機，或終端純輸入 exit / quit / shutdown
    is_exact_shutdown = clean_compact in ["exit", "quit", "shutdown", "7lexit", "7lquit", "7lshutdown"]
    shutdown_keywords = [
        "關機", "強制關機", "強制關閉", "強制退出",
        "關閉系統", "退出系統", "結束程式", "關閉程式",
        "關閉7l", "關閉阿七", "系統休息", "安全退出", "安全關閉", "shutdown"
    ]
    has_shutdown_cmd = (
        (has_target and any(k in clean_compact for k in shutdown_keywords)) or
        (has_target and any(clean_compact.endswith(k) for k in ["退出", "關閉", "結束", "休眠"]))
    )

    if is_exact_shutdown or has_shutdown_cmd:
        log_print(f"👋 [系統] 收到即時關機指令「{text.strip()}」，正在安全退出...")
        if current_piano_process and current_piano_process.poll() is None:
            try:
                current_piano_process.terminate()
            except Exception:
                pass
        if SOUND_ENGINE:
            SOUND_ENGINE.all_notes_off()
        os._exit(0)
        return True

    return False

async def mic_worker(recognizer, input_queue):
    global current_ai_state, RECENT_BOT_MESSAGES, current_mic_action_str, IS_MIC_ENABLED, IS_MP3_PLAYING, MP3_ECHO_TRAILING_CHUNKS
    
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
    except Exception:
        pass

    while True:
        if not IS_MIC_ENABLED:
            current_mic_action_str = "🔇 靜音"
            await asyncio.sleep(0.3)
            continue

        # 🌟 7x24 全雙工真·不關麥監聽：7L 發話或 MP3 播放中時麥克風依然暢通，由專屬聲紋鎖精準防禦回音並支援隨時插話打斷！
        try:
            listen_res = await asyncio.to_thread(lambda: listen_once_fast(recognizer))
            if isinstance(listen_res, tuple):
                user_text, audio_b64 = listen_res
            else:
                user_text, audio_b64 = str(listen_res), None

            cleaned_text = user_text.strip() if user_text else ""
            
            # 🛡️ 專屬老爸聲紋鎖與智慧插話系統：
            if cleaned_text:
                current_mic_action_str = f"👂 聽到:「{cleaned_text[:10]}...」"
                
                # 🛑 0. 毫秒級即時關機 / 重開機指令攔截 (最高優先權，支援 7L / 謝龍 / CL 等同音指令)
                if check_immediate_shutdown(cleaned_text):
                    continue

                # 🔐 1. 毫秒級聲紋特徵驗證：判定是否為老爸本人（徹底排除 7L 自身女聲、喇叭外放、電視雜音、旁人插嘴）
                is_dad, vp_score = voiceprint_verifier.verify_is_dad(audio_b64, threshold=0.55)
                if not is_dad:
                    # 若為 7L 自身喇叭回音，觸發專屬一次性回音過濾；若是其他雜音則聲紋攔截
                    if is_7l_voice_echo(cleaned_text, is_dad_verified=False):
                        continue
                    log_print(f"🔇 [聲紋攔截] 判定為非老爸聲音或雜音回音 (聲紋分: {vp_score:.2f} < 0.55)，自動過濾: 「{cleaned_text}」")
                    continue

                # 🔇 2. 7L 自身發話喇叭回音過濾（老爸本人聲紋保護：長度動態閾值，短句/指令不殺，一次性過濾）
                if is_7l_voice_echo(cleaned_text, is_dad_verified=is_dad):
                    continue

                # 🎙️ 3. 全雙工傾聽不打斷：保留 7L 完整發音說話，絕不中斷，背景接收老爸輸入！
                is_currently_speaking = (current_ai_state == "TALKING") or IS_MP3_PLAYING or (pygame.mixer.get_init() and pygame.mixer.music.get_busy())
                if is_currently_speaking:
                    log_print(f"🎙️ [老爸語音接收] 聲紋確認 ({vp_score:.2f}) ➔ 7L 說話不中斷，背景接收老爸輸入！")

                # 🔇 4. 電腦內部聲音 (WASAPI Loopback 遊戲/影片) 輔助過濾
                if is_computer_audio_echo(cleaned_text):
                    continue
                
                saved_audio_path = save_local_audio_clip(audio_b64)
                intercept_tag = " (⚡ 立即打斷舊思考)" if current_ai_state == "THINKING" and not is_currently_speaking else ""
                log_print(f"📥 [老爸語音] 收到輸入: {cleaned_text} (聲紋: {vp_score:.2f}){intercept_tag}")
                await input_queue.put({"text": cleaned_text, "audio_base64": audio_b64, "audio_file": saved_audio_path, "timestamp": time.time(), "source": "mic"})
            else:
                current_mic_action_str = "待命 (聲紋鎖監聽)"
        except Exception:
            current_mic_action_str = "待命 (聲紋鎖監聽)"
            await asyncio.sleep(0.1)


async def text_file_listener_worker(input_queue, filename="chat_input.txt"):
    """監聽 chat_input.txt 本地文字輸入 (支援打字控制與指令快速直達，自動支援桌面、AI_Agents 及根目錄路徑)"""
    global current_mic_action_str
    
    candidate_paths = [
        filename,
        os.path.join("C:\\AI_Agents", "chat_input.txt"),
        os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "chat_input.txt"),
        os.path.join(os.path.expanduser("~"), "Desktop", "chat_input.txt"),
        "C:\\chat_input.txt"
    ]
    
    for p in candidate_paths:
        if not os.path.exists(p):
            try:
                with open(p, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass

    while True:
        try:
            for p in candidate_paths:
                if os.path.exists(p):
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    cleaned_content = content.strip()
                    if cleaned_content:
                        try:
                            with open(p, "w", encoding="utf-8") as f:
                                f.write("")
                        except Exception:
                            pass
                        
                        log_print(f"📥 [檔案打字接收] 收到輸入: {cleaned_content}")
                        if check_immediate_shutdown(cleaned_content):
                            return
                        current_mic_action_str = f"⌨️ 打字:「{cleaned_content[:10]}...」"
                        await input_queue.put({"text": cleaned_content, "timestamp": time.time(), "source": "text_file"})
                        break
        except Exception:
            pass
        
        await asyncio.sleep(0.3)

async def console_keyboard_input_worker(input_queue):
    """即時監聽終端機鍵盤直接打字輸入 (非同步監聽，支援直接在終端輸入文字或關機指令)"""
    if not msvcrt:
        return

    def read_keyboard_line():
        buffer = []
        while True:
            if msvcrt.kbhit():
                try:
                    ch = msvcrt.getwch()
                except Exception:
                    continue
                if ch in ('\r', '\n'):
                    line = "".join(buffer).strip()
                    buffer.clear()
                    if line:
                        return line
                elif ch == '\x08':  # Backspace
                    if buffer:
                        buffer.pop()
                elif ch == '\x03':  # Ctrl+C
                    os._exit(0)
                elif ord(ch) >= 32 or ch > '\x7f':
                    buffer.append(ch)
            time.sleep(0.03)

    while True:
        try:
            line = await asyncio.to_thread(read_keyboard_line)
            if line:
                log_print(f"⌨️ [終端打字接收] 收到輸入: {line}")
                if check_immediate_shutdown(line):
                    return
                await input_queue.put({"text": line, "timestamp": time.time(), "source": "console"})
        except Exception:
            await asyncio.sleep(0.1)

# --- 🖼️ 畫面與環境感知協程 ---
async def screen_capture_worker():
    global latest_screen_cache, SCREEN_TEMPORAL_HISTORY
    while True:
        try:
            new_views = await asyncio.to_thread(capture_screen_as_base64)
            if new_views:
                if latest_screen_cache and isinstance(latest_screen_cache, list) and len(latest_screen_cache) > 0:
                    SCREEN_TEMPORAL_HISTORY.append((time.time(), latest_screen_cache[0][1]))
                latest_screen_cache = new_views
        except Exception:
            pass
        await asyncio.sleep(1.8)

LAST_SCREEN_MD5_HASH = None
HAS_INITIAL_VISION_LOOK = False

async def peripheral_vision_worker():
    """👁️ 【背景餘光雙層感知協程】：
    - 頂層哨兵：採用 Gemini Live API (3.1-flash-live-preview) 實時注視螢幕畫面（0 額度消耗、0 描述輸出），
      只極速判定 [NO_CHANGE] 還是 [LOOK_SERIOUS]。
    - 深度眼睛：唯有 Live 哨兵判定出現全新重大視窗/報錯/事件時，才喚醒 3.1-flash-lite 認真細看一次！
    - 徹底告別每 20 秒無謂消耗 3.1-flash-lite 說話額度的浪費行為。
    """
    global latest_screen_cache, current_screen_context, LAST_SCREEN_MD5_HASH, HAS_INITIAL_VISION_LOOK
    
    while True:
        await asyncio.sleep(15.0) 
        if current_ai_state in ["THINKING", "TALKING"]:
            continue
        if not latest_screen_cache: 
            continue
        
        if is_system_overloaded():
            continue

        try:
            sample_img = latest_screen_cache[0][1] if isinstance(latest_screen_cache, list) else latest_screen_cache
            if not sample_img:
                continue

            if isinstance(sample_img, str):
                img_bytes = base64.b64decode(sample_img)
            else:
                img_bytes = sample_img

            if len(img_bytes) < 1000:
                continue

            # 🛡️ 像素 Hash 粗篩：畫面若完全靜止 (例如離開電腦、無任何操作)，0 網路直接略過
            import hashlib
            cur_hash = hashlib.md5(img_bytes[:8192]).hexdigest()
            if LAST_SCREEN_MD5_HASH == cur_hash and HAS_INITIAL_VISION_LOOK:
                continue
            LAST_SCREEN_MD5_HASH = cur_hash

            # 🌟 開機第一次：用 3.1-flash-lite 建立基準畫面感知
            if not HAS_INITIAL_VISION_LOOK or not current_screen_context or current_screen_context == "目前沒有特別的畫面動態。":
                log_print("👁️ [餘光視覺感知] 首次啟動 ➔ 啟動 3.1-flash-lite 建立基準畫面認知...")
                init_desc = await get_lightweight_gemini_vision(sample_img)
                if init_desc:
                    current_screen_context = init_desc
                    realtime_task_mgr.update_vision_context(current_screen_context)
                    HAS_INITIAL_VISION_LOOK = True
                continue

            # ⚡ 日常餘光：由 Live API 哨兵保持注視，不輸出描述，只判定是否需認真看
            should_look = await check_screen_change_via_live_api(img_bytes, current_screen_context)
            if should_look:
                log_print("🚨 [餘光 Live 哨兵] 判定畫面出現值得關注的新動態！啟動 3.1-flash-lite 認真細看...")
                detailed_desc = await get_lightweight_gemini_vision(sample_img)
                if detailed_desc:
                    current_screen_context = detailed_desc
                    realtime_task_mgr.update_vision_context(current_screen_context)
            else:
                # 畫面持續在進行既有操作 (例如繼續寫程式碼、同視窗瀏覽)
                # 保持眼睛在看，0 消耗 3.1-flash-lite 額度！
                pass
        except Exception:
            pass

async def system_audio_worker():
    """🎧 即時電腦內部聲音感知與內錄協程 (WASAPI Loopback 實時耳目)"""
    global current_system_audio_context, LATEST_SYSTEM_AUDIO_RMS, LATEST_SYSTEM_AUDIO_TEXT, RECENT_SYSTEM_AUDIO_TRANSCRIPTS
    
    log_print("🎧 [聲音感知] 7L 電腦內部聲音監聽系統 (WASAPI Loopback) 已就緒！")
    
    while True:
        try:
            # 每一輪截取 2.5 秒電腦內部聲音
            wav_bytes, rms = await asyncio.to_thread(capture_system_audio_chunk, 2.5)
            LATEST_SYSTEM_AUDIO_RMS = rms
            
            if rms > 0.008 and wav_bytes:
                # 若當前正在播放 TTS 自身聲音，標記為自身音訊
                is_tts = False
                try:
                    is_tts = pygame.mixer.music.get_busy()
                except Exception:
                    pass
                    
                if not is_tts:
                    text = await asyncio.to_thread(transcribe_audio_bytes, wav_bytes)
                    if text:
                        LATEST_SYSTEM_AUDIO_TEXT = text
                        RECENT_SYSTEM_AUDIO_TRANSCRIPTS.append((time.time(), text))
                        # 保持最近 15 筆紀錄
                        if len(RECENT_SYSTEM_AUDIO_TRANSCRIPTS) > 15:
                            RECENT_SYSTEM_AUDIO_TRANSCRIPTS.pop(0)
                        current_system_audio_context = f"電腦喇叭傳出聲音/影片/他人語音：『{text}』"
                        realtime_task_mgr.update_audio_context(current_system_audio_context)
                        log_print(f"🔊 [電腦內錄監聽] 識別到電腦音訊: 「{text}」 (音量: {rms:.3f})")
                        
                        # 🌟 若電腦/DC 通話中有人直接呼喚 7L，自動登記入記憶腦袋看板供 7L 主動參與互動！
                        lower_t = text.lower()
                        if any(n in lower_t for n in ["7l", "七七", "小七", "機器人"]):
                            add_to_streamer_mind_board("🎧 [電腦/DC通話語音]", f"電腦傳出語音提到妳：『{text}』", source="system_audio")
                    else:
                        current_system_audio_context = "電腦正在播放背景音樂或音效。"
                        realtime_task_mgr.update_audio_context(current_system_audio_context)
            else:
                if time.time() - LAST_TTS_END_TIME > 1.0:
                    current_system_audio_context = "目前沒有播放特別的聲音。"
                    realtime_task_mgr.update_audio_context(current_system_audio_context)
                    LATEST_SYSTEM_AUDIO_TEXT = ""
        except Exception:
            pass
            
        await asyncio.sleep(0.5)



def check_requires_deep_gemini(user_input: str, stage1_text: str = "") -> bool:
    """判斷是否需要喚起 Gemini 旗艦大腦進行深度思考與工具調用 (若只是日常問答閒聊則直接略過以節省 API 額度)"""
    combined = f"{user_input} {stage1_text}".lower()
    if "[req_tool]" in combined or "[req_system]" in combined or "[open_browser" in combined:
        return True

    # 提取純淨文字 (去括號、去標籤)
    clean_q = re.sub(r'【.*?】', '', user_input)
    clean_q = re.sub(r'\[[A-Z_]+(?::\s*[^\]]+)?\]', '', clean_q).strip()

    # 1. 檢查是否直接命中本地真實 MIDI 曲庫 / catalog (如觀眾直接留言歌名「藍色狂想曲」、「Rhapsody in Blue」)
    if clean_q and len(clean_q) >= 2:
        clean_ql = clean_q.lower()
        if clean_ql in AUTHENTIC_MIDI_MAP or clean_ql in MIDI_AI_MATCH_CACHE:
            return True

    # 2. 工具與深度操作關鍵字 (包含鋼琴、繪圖、搜尋、代碼等)
    tool_keywords = [
        "彈鋼琴", "彈琴", "點歌", "彈一首", "彈奏", "播放鋼琴", "換一首", "切歌", "鋼琴", "來一首", "來首", "播一首", "放一首", "彈",
        "換音色", "切換音色", "鋼琴音色", "弦樂", "吉他", "小提琴", "大提琴", "薩克斯風", "木琴", "管風琴", "手風琴", "豎琴", "電鋼琴", "人聲合唱", "古箏", "卡林巴",
        "畫一張", "畫圖", "生成圖片", "畫個", "生圖", "畫一幅", "畫一隻", "繪製",
        "搜尋", "查一下", "上網查", "最新新聞", "天氣", "google搜尋", "幫我查",
        "寫程式", "寫代碼", "寫個遊戲", "俄羅斯方塊", "貪吃蛇", "執行程式", "python",
        "關閉麥克風", "開啟麥克風", "靜音麥克風", "清空記憶", "重置記憶",
        "妳的電腦", "你的電腦", "專屬電腦", "虛擬機", "妳的虛擬機", "自己的電腦", "在電腦上", "電腦螢幕", "去妳的電腦", "在妳電腦", "操作電腦", "看妳螢幕", "看妳的螢幕", "自己去玩", "去玩", "看影片", "自主學習", "寫日記", "玩遊戲", "自主探索",
        "deepseek", "r1", "深度推理", "智能體", "agent", "autogen", "crewai", "瀏覽器操作", "openclaw", "harness",
        "鋼琴音量", "鋼琴大聲", "鋼琴小聲", "鋼琴靜音", "倍速", "演奏速度", "混在一起彈", "雜在一起彈", "合體", "神仙打架", "mashup"
    ]
    if any(k in combined for k in tool_keywords) or clean_q.startswith("彈"):
        return True

    return False

async def ai_face_tracking_loop(vts):
    global current_ai_state, vc.target_look_x, vc.target_look_y, vc.current_look_x, vc.current_look_y, vc.is_tracking_mouse, vc.force_blink_trigger, vc.eye_roll_timer, PIANO_NOTE_FOCUS_X, vc.frown_timer, IS_MP3_PLAYING, vc.shock_timer, CURRENT_PLAYING_VOICE_TASK
    t = 0.0
    blink_timer = time.time() + random.uniform(3.5, 6.0)
    blink_start_time = 0.0
    is_blinking = False
    
    curr_x, curr_y, curr_z = 0.0, 0.0, 0.0
    curr_eye_x, curr_eye_y = 0.0, 0.0
    smooth_piano_focus_x = 0.0
    auto_mouse_track_timer = 0.0  
    
    while True:
        try:
            now = time.time()
            is_playing = False
            try:
                is_playing = IS_MP3_PLAYING or (pygame.mixer.get_init() and pygame.mixer.music.get_busy())
            except Exception:
                pass

            if current_ai_state == "IDLE" and not is_playing and not vc.is_tracking_mouse:
                if auto_mouse_track_timer > 0:
                    auto_mouse_track_timer -= 0.05
                    if auto_mouse_track_timer <= 0:
                        vc.target_look_x = 0.0
                        vc.target_look_y = 0.0
                else:
                    if random.random() < 0.005:  
                        auto_mouse_track_timer = random.uniform(2.0, 4.0)  
            else:
                if auto_mouse_track_timer > 0:
                    auto_mouse_track_timer = 0.0
                    if not vc.is_tracking_mouse:
                        vc.target_look_x = 0.0
                        vc.target_look_y = 0.0

            is_currently_tracking = vc.is_tracking_mouse or auto_mouse_track_timer > 0

            if is_currently_tracking:
                sw, sh = pyautogui.size()
                px, py = pyautogui.position()
                nx, ny = (px / sw) - 0.5, (py / sh) - 0.5
                vc.target_look_x, vc.target_look_y = nx * 28.0, ny * -20.0

            vc.current_look_x += (vc.target_look_x - vc.current_look_x) * 0.08
            vc.current_look_y += (vc.target_look_y - vc.current_look_y) * 0.08

            # 🌟 自然真實眨眼機制 (每 3.5~6.5 秒眨眼一次，閉眼時間精確為 0.14 秒，徹底杜絕快速連眨)
            eye_open_left = 1.0
            eye_open_right = 1.0
            if vc.force_blink_trigger > 0:
                if not is_blinking:
                    is_blinking = True
                    blink_start_time = now
                    vc.force_blink_trigger = 0
            elif not is_blinking and now > blink_timer:
                is_blinking = True
                blink_start_time = now

            if is_blinking:
                if now - blink_start_time < 0.14:
                    eye_open_left = 0.0
                    eye_open_right = 0.0
                else:
                    eye_open_left = 1.0
                    eye_open_right = 1.0
                    is_blinking = False
                    blink_timer = now + random.uniform(3.5, 6.5)
            else:
                eye_open_left = 1.0
                eye_open_right = 1.0

            # 🌟 靈動眼珠與鋼琴音符密集處視線追蹤計算
            if vc.eye_roll_timer > now:
                # 🌀 招牌靈動大轉眼珠 / 大圈環視四周 (俐落 360° 滿幅滿力道 1.0 大圓周軌跡)
                target_eye_x = math.sin(t * 4.2) * 1.0
                target_eye_y = math.cos(t * 4.2) * 1.0
                curr_eye_x = target_eye_x
                curr_eye_y = target_eye_y
            elif is_piano_active:
                # 🎹 只要處於鋼琴彈奏狀態中：眼神永遠精準朝下追蹤琴鍵音符密集重心
                smooth_piano_focus_x += (PIANO_NOTE_FOCUS_X - smooth_piano_focus_x) * 0.25
                target_eye_x = max(-0.85, min(0.85, smooth_piano_focus_x / 16.0))
                target_eye_y = -0.75
                curr_eye_x += (target_eye_x - curr_eye_x) * 0.15
                curr_eye_y += (target_eye_y - curr_eye_y) * 0.15
            elif is_currently_tracking:
                # 滑鼠游標注視
                target_eye_x = max(-0.85, min(0.85, vc.current_look_x / 20.0))
                target_eye_y = max(-0.85, min(0.85, vc.current_look_y / 15.0))
                curr_eye_x += (target_eye_x - curr_eye_x) * 0.15
                curr_eye_y += (target_eye_y - curr_eye_y) * 0.15
            elif current_ai_state == "THINKING":
                # 思考中視線往斜上方
                target_eye_x = -0.38
                target_eye_y = 0.55
                curr_eye_x += (target_eye_x - curr_eye_x) * 0.15
                curr_eye_y += (target_eye_y - curr_eye_y) * 0.15
            else:
                # 待命/說話時微幅靈動眼神
                target_eye_x = math.sin(t * 0.8) * 0.30 + (vc.current_look_x / 28.0) * 0.4
                target_eye_y = math.cos(t * 0.6) * 0.20 + (vc.current_look_y / 20.0) * 0.4
                curr_eye_x += (target_eye_x - curr_eye_x) * 0.15
                curr_eye_y += (target_eye_y - curr_eye_y) * 0.15

            target_angle_x = 0.0
            target_angle_y = 0.0
            target_angle_z = 0.0
            target_mouth = 0.0

            # 👄 真實音訊波形精準對嘴：完全根據音訊逐幀 RMS 振幅與快開慢合物理平滑決定！
            if is_playing:
                global CURRENT_MOUTH_ENVELOPE, CURRENT_SPEECH_START_TIME, CURRENT_SMOOTH_MOUTH
                if CURRENT_MOUTH_ENVELOPE and CURRENT_SPEECH_START_TIME > 0:
                    elapsed = now - CURRENT_SPEECH_START_TIME
                    frame_idx = int(elapsed * 25.0)
                    if 0 <= frame_idx < len(CURRENT_MOUTH_ENVELOPE):
                        raw_target = CURRENT_MOUTH_ENVELOPE[frame_idx]
                    else:
                        raw_target = 0.0
                    
                    # 🎙️ 快開慢合 (Fast Attack 0.65, Gentle Release 0.35) 物理濾波，徹底告別卡頓與僵硬
                    if raw_target > CURRENT_SMOOTH_MOUTH:
                        CURRENT_SMOOTH_MOUTH += (raw_target - CURRENT_SMOOTH_MOUTH) * 0.65
                    else:
                        CURRENT_SMOOTH_MOUTH += (raw_target - CURRENT_SMOOTH_MOUTH) * 0.35
                    target_mouth = round(CURRENT_SMOOTH_MOUTH, 3)
                else:
                    # 若無波形包絡 (如音訊加載間隙)，使用具備自然閉口零點的靈動音節波
                    osc = (math.sin(t * 18.0) * 0.5 + 0.5) * (math.sin(t * 8.0) * 0.5 + 0.5)
                    target_mouth = round(osc * 0.70, 3)
            else:
                CURRENT_SMOOTH_MOUTH = 0.0
                target_mouth = 0.0

            # 姿態與頭部運動計算
            if is_piano_active:
                # 🎹 鋼琴彈奏中：頭部與身體重心專注在鍵盤，隨音符高低音律動傾斜（說話時僅動嘴，姿態不變）
                smooth_piano_focus_x += (PIANO_NOTE_FOCUS_X - smooth_piano_focus_x) * 0.25
                target_angle_x = smooth_piano_focus_x * 0.65 + math.sin(t * 1.2) * 2.5
                target_angle_y = -10.0 + math.cos(t * 1.5) * 1.5
                target_angle_z = smooth_piano_focus_x * 0.30 + math.sin(t * 1.0) * 2.0
            elif is_playing:
                # 🗣️ MP3 播放中：頭部溫和自然微幅呼吸點頭
                target_angle_x = math.sin(t * 1.0) * 1.5 + vc.current_look_x * 0.25
                target_angle_y = math.cos(t * 0.8) * 0.8 + vc.current_look_y * 0.25
                target_angle_z = math.sin(t * 0.7) * 1.0
            elif is_currently_tracking:
                target_angle_x = vc.current_look_x
                target_angle_y = vc.current_look_y
                target_angle_z = 0.0
            else:
                if current_ai_state == "IDLE":
                    target_angle_x = math.sin(t * 0.4) * 2.0 + vc.current_look_x * 0.3
                    target_angle_y = math.cos(t * 0.3) * 1.0 + vc.current_look_y * 0.3
                    target_angle_z = math.sin(t * 0.3) * 1.0
                elif current_ai_state == "THINKING":
                    target_angle_x = -2.0 + vc.current_look_x * 0.2
                    target_angle_y = 2.0 + vc.current_look_y * 0.2
                    target_angle_z = 4.5
                elif current_ai_state == "TALKING":
                    target_angle_x = vc.current_look_x
                    target_angle_y = vc.current_look_y
                    target_angle_z = 0.0

            if vc.eye_roll_timer > now:
                target_angle_z += math.sin(t * 4.2) * 3.5
                target_angle_y += math.cos(t * 4.2) * 2.0

            # 🌟 純物理動力學縮小瞳孔與震驚 (EyeOpen=2.0 瞪大縮瞳 + 物理高頻恐懼顫抖)
            # 🎙️ 發話期間若有物理表情，持續延長鎖定，確保說話全程不中途褪去
            if CURRENT_PLAYING_VOICE_TASK is not None:
                if vc.shock_timer > 0:
                    vc.shock_timer = max(vc.shock_timer, now + 1.0)
                if vc.frown_timer > 0:
                    vc.frown_timer = max(vc.frown_timer, now + 1.0)

            is_in_shock = (vc.shock_timer > now)
            is_frowning = (vc.frown_timer > now)
            if is_in_shock:
                eye_open_left = 2.0
                eye_open_right = 2.0
                target_brows = 0.85
                target_mouth_smile = 0.35
                if not is_playing:
                    target_mouth = 0.20  # 震驚未發話時微張嘴 (呆滯/倒抽氣)；發話時保持正常對嘴開合
                target_angle_x += math.sin(t * 38.0) * 0.35
                target_angle_y += math.sin(t * 34.0) * 0.30
                target_angle_z += math.cos(t * 36.0) * 0.40
                curr_eye_x += math.sin(t * 30.0) * 0.03
                curr_eye_y += math.cos(t * 28.0) * 0.03
            elif is_frowning:
                # 🌟 傲嬌/困擾/委屈 皺眉表情 (Brows = 0.0 壓低眉毛形成八字皺眉 + 微撇嘴/微嘟嘴)
                eye_open_left = 0.95
                eye_open_right = 0.95
                target_brows = 0.0
                target_mouth_smile = 0.25
                target_angle_z += math.sin(t * 1.5) * 2.0
                target_angle_y += -1.5
            elif vc.wink_timer > now:
                # 🌟 俏皮靈動單邊眨一下眼 (Wink: 總時長 0.55 秒，眨一下立即順暢張開)
                elapsed_wink = 0.55 - (vc.wink_timer - now)
                if elapsed_wink < 0.10:
                    wink_eye_open = max(0.0, 1.0 - (elapsed_wink / 0.10))
                elif elapsed_wink <= 0.32:
                    wink_eye_open = 0.0
                else:
                    wink_eye_open = min(1.0, (elapsed_wink - 0.32) / 0.23)

                if vc.wink_side == "left":
                    eye_open_left = wink_eye_open
                    eye_open_right = 1.0
                    target_angle_z += 3.5 * (1.0 - wink_eye_open)
                else:
                    eye_open_left = 1.0
                    eye_open_right = wink_eye_open
                    target_angle_z += -3.5 * (1.0 - wink_eye_open)
                target_brows = 0.50
                target_mouth_smile = 0.50 + 0.35 * (1.0 - wink_eye_open)
            else:
                # 🌟 平時自然溫和中性眉毛 (0.50) 與自然微笑 (0.50，發話時隨開口度靈動上揚)
                target_brows = 0.50
                target_mouth_smile = min(1.0, 0.50 + 0.20 * target_mouth) if is_playing else 0.50

            curr_x += (target_angle_x - curr_x) * 0.10
            curr_y += (target_angle_y - curr_y) * 0.10
            curr_z += (target_angle_z - curr_z) * 0.10

            param_values = [
                {"id": "FaceAngleX", "value": curr_x, "weight": 1.0},
                {"id": "FaceAngleY", "value": curr_y, "weight": 1.0},
                {"id": "FaceAngleZ", "value": curr_z, "weight": 1.0},
                {"id": "EyeLeftX", "value": curr_eye_x, "weight": 1.0},
                {"id": "EyeLeftY", "value": curr_eye_y, "weight": 1.0},
                {"id": "EyeRightX", "value": curr_eye_x, "weight": 1.0},
                {"id": "EyeRightY", "value": curr_eye_y, "weight": 1.0},
                {"id": "EyeOpenLeft", "value": eye_open_left, "weight": 1.0},
                {"id": "EyeOpenRight", "value": eye_open_right, "weight": 1.0},
                {"id": "Brows", "value": target_brows, "weight": 1.0},
                {"id": "MouthSmile", "value": target_mouth_smile, "weight": 1.0},
                {"id": "MouthOpen", "value": target_mouth, "weight": 1.0}
            ]

            if hasattr(vts, 'inject_parameters'):
                await vts.inject_parameters(param_values)
            else:
                vts_data = {
                    "apiName": "VTubeStudioPublicAPI", "apiVersion": "1.0", "requestID": "AIStateTracking",
                    "messageType": "InjectParameterDataRequest",
                    "data": {
                        "faceFound": True,
                        "mode": "set",
                        "parameterValues": param_values
                    }
                }
                async with vc.vts_lock:
                    await asyncio.wait_for(vts.request(vts_data), timeout=0.5)

        except Exception:
            pass

        t += 0.08
        await asyncio.sleep(0.04)

async def expression_keeper_worker(vts):
    global vc.CURRENT_ACTIVE_EXP
    while True:
        await asyncio.sleep(12.0)
        if vc.CURRENT_ACTIVE_EXP:
            try:
                msg_state = {
                    "apiName": "VTubeStudioPublicAPI", 
                    "apiVersion": "1.0", 
                    "requestID": "GetState", 
                    "messageType": "ExpressionStateRequest", 
                    "data": {"details": True}
                }
                async with vc.vts_lock:
                    resp_state = await asyncio.wait_for(vts.request(msg_state), timeout=1.0)
                
                expressions = resp_state.get("data", {}).get("expressions", [])
                active_files = [exp.get("file") for exp in expressions if exp.get("active")]
                if vc.CURRENT_ACTIVE_EXP not in active_files:
                    async with vc.vts_lock:
                        await asyncio.wait_for(vts.request({
                            "apiName": "VTubeStudioPublicAPI",
                            "apiVersion": "1.0",
                            "requestID": "ForceActivate",
                            "messageType": "ExpressionActivationRequest",
                            "data": {"expressionFile": vc.CURRENT_ACTIVE_EXP, "active": True}
                        }), timeout=0.8)
            except Exception:
                pass

async def anti_watermark_worker(vts):
    await asyncio.sleep(2.0)
    try:
        async with vc.vts_lock:
            await asyncio.wait_for(vts.request({
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": "ActivateWatermark",
                "messageType": "ExpressionActivationRequest",
                "data": {
                    "expressionFile": "水印.exp3.json", 
                    "active": True                     
                }
            }), timeout=1.0)
    except Exception: 
        pass

# ────────────────────────────────────────────────────────

async def print_model_parameters(vts):
    try:
        await asyncio.sleep(1.0)
        await fetch_vts_base_model_pos(vts)
    except Exception: 
        pass

async def vts_health_worker(vts):
    tracking_started = True
    while True:
        await asyncio.sleep(5.0)
        try:
            is_conn = vts.is_connected() if hasattr(vts, 'is_connected') else (hasattr(vts, 'ws') and vts.ws and not getattr(vts.ws, 'closed', False))
            if not is_conn:
                async with vc.vts_lock:
                    await vts.connect(retries=1)
                    await vts.request_authenticate()
                    log_print("✅ [系統通知] VTube Studio 重新連線成功！身體控制權已恢復！")
                    if not tracking_started:
                        asyncio.create_task(print_model_parameters(vts))
                        asyncio.create_task(ai_face_tracking_loop(vts))
                        tracking_started = True
        except Exception:
            pass

async def autonomous_wander_worker():
    """7L 背景非同步自主漫遊走位與自主彈琴協程（在老爸閒置時由 7L 自主漫步或自主彈奏鋼琴）"""
    global IS_AUTO_WANDER_ENABLED, LAST_WANDER_TIME, vc.CURRENT_SPATIAL_LOCATION, current_ai_state, is_piano_active
    LAST_AUTO_PIANO_TIME = time.time()
    
    while True:
        try:
            await asyncio.sleep(12.0)
            now = time.time()
            idle_seconds = now - last_interaction_time
            
            if is_piano_active or current_ai_state in ["TALKING", "THINKING", "PIANO"]:
                continue
            
            if IS_AUTO_WANDER_ENABLED and current_ai_state == "IDLE" and idle_seconds > 60.0:
                if now - LAST_AUTO_PIANO_TIME > 300.0:
                    LAST_AUTO_PIANO_TIME = now
                    LAST_WANDER_TIME = now
                    local_seeds = get_local_piano_seeds()
                    song_seed = random.choice(local_seeds)
                    log_print(f"🎹 [7L 自主彈琴] 7L 決定自主坐到鋼琴前為老爸演奏《{song_seed}》！")
                    ai_intro = await generate_dynamic_piano_chatter(song_seed, is_radio=False)
                    if ai_intro:
                        log_print(f"💬 [自主彈琴 AI 自由意志發話]: {ai_intro}")
                        await speech_queue.put({"text": ai_intro, "target": "dad"})
                    else:
                        log_print(f"🎹 [自主彈琴 AI 自由意志] 7L 決定優雅安靜入座，全神貫注為老爸演奏。")
                    await play_virtual_piano(song_seed)
                    continue

                if now - LAST_WANDER_TIME > 60.0:
                    LAST_WANDER_TIME = now
                    await move_vts_spatial(target_pos="random", duration=3.0)
                    vc.CURRENT_SPATIAL_LOCATION = "自由漫遊"
                    
        except Exception:
            await asyncio.sleep(5.0)

# --- 🗣️ 語音合成排隊協程 (老爸優先 / 異步雙軌仲裁器) ---
async def speech_queue_worker(vts, input_queue):
    global current_ai_state, CURRENT_SPEAKING_TARGET, vc.shock_timer, vc.frown_timer
    while True:
        try:
            item = await speech_queue.get()
            if not item:
                speech_queue.task_done()
                continue
            
            if isinstance(item, dict):
                text = item.get("text", "")
                target = item.get("target", "dad")
                raw_actions_text = item.get("raw_text", "")
            else:
                text = str(item)
                target = "dad"
                raw_actions_text = ""
                
            if not text:
                speech_queue.task_done()
                continue
            
            CURRENT_SPEAKING_TARGET = target
            current_ai_state = "TALKING"
            
            # 建立可隨時被自己插話或老爸說話秒級 cancel 的播放任務（整合 Live API 潛意識神態導演與句中多表情動態時間軸）
            CURRENT_PLAYING_VOICE_TASK = asyncio.create_task(play_voice_complete(text, target=target, raw_actions_text=raw_actions_text, vts=vts))
            try:
                await CURRENT_PLAYING_VOICE_TASK
            except asyncio.CancelledError:
                log_print("🛑 [語音被中斷] 7L 當前句子已成功中斷，無縫讓位給最新發言。")
            finally:
                CURRENT_PLAYING_VOICE_TASK = None
            
            # 🎙️ 發話音訊一播放完畢，立即秒級釋放麥克風狀態，絕不卡死老爸即時接話！
            if speech_queue.empty():
                if current_ai_state == "TALKING":
                    current_ai_state = "PIANO" if is_piano_active else "IDLE"
                CURRENT_SPEAKING_TARGET = "none"
            
            # 🎭 表情停留緩衝：發話完畢後持續保留一段時間（預設 3.5 秒），讓情緒自然延續
            if vc.frown_timer > 0:
                vc.frown_timer = time.time() + EXPRESSION_HOLD_SECONDS
            if vc.shock_timer > 0:
                vc.shock_timer = time.time() + EXPRESSION_HOLD_SECONDS

            hold_steps = int(EXPRESSION_HOLD_SECONDS * 10)
            for _ in range(hold_steps):
                if not speech_queue.empty() or not input_queue.empty():
                    break
                await asyncio.sleep(0.1)
            
            if input_queue.empty() and speech_queue.empty() and not is_piano_active:
                await set_vts_expression(vts, "_RESET_")
            
            if current_ai_state == "TALKING":
                current_ai_state = "PIANO" if is_piano_active else "IDLE"
            CURRENT_SPEAKING_TARGET = "none"
        except Exception as e:
            log_print(f"\n❌ [語音排隊系統異常]: {e}")
            if current_ai_state == "TALKING":
                current_ai_state = "PIANO" if is_piano_active else "IDLE"
            CURRENT_SPEAKING_TARGET = "none"
        finally:
            try:
                speech_queue.task_done()
            except:
                pass

# ────────────────────────────────────────────────────────
# 🤖 15. 對話處理與自主發話大腦核心
# ────────────────────────────────────────────────────────
async def background_system_task(vts, input_queue, user_input, stage1_text, system_prompt, current_history, screen_img=None):
    global current_ai_state, current_voice_task, current_model_tag
    current_ai_state = "THINKING"
    sys_info = await asyncio.to_thread(get_system_performance)

    stage2_prompt = f"（系統提示：針對剛才使用者說的「{user_input}」，妳剛才初步回應：「{stage1_text}」。現在系統已取得他的電腦工作管理員即時數據：「{sys_info}」。請根據這項數據，用妳自行發展出的語氣給予自然補充，不要重複前言。）"
    messages = [{"role": "system", "content": system_prompt}] + current_history + [{"role": "user", "content": stage2_prompt}]
    
    raw_stage2_text = await fetch_ai_response(messages, image_base64=screen_img, is_proactive=True)
    
    log_print(f"🤖 [系統檢測] 原始大腦輸出: {raw_stage2_text}")
    
    clean_bot_reply = re.sub(r"(?:\[|\|\|)?(NEW_NAME|NEW_IMPRESSION|改稱呼|記印象)[：:].*", "", raw_stage2_text, flags=re.IGNORECASE|re.DOTALL)
    
    if current_voice_task and not current_voice_task.done():
        current_voice_task.cancel()
    
    spoken = await execute_actions(vts, clean_bot_reply, input_queue)
    clean_spoken = spoken.strip(" *'\"-.,!?。，！？\n\r") if spoken else ""
    if clean_spoken:
        # ⚡ 大腦一回傳輸出，即刻第一時間更新 subtitle.txt 抵消 OBS 讀取延遲！
        await asyncio.to_thread(update_subtitle, clean_spoken)
        log_print(f"💬 7L 回覆: {clean_spoken} ({current_model_tag})")
        await speech_queue.put({"text": clean_spoken, "target": "audience", "raw_text": clean_bot_reply})
        current_history.append({"role": "assistant", "content": clean_spoken})
    else:
        await asyncio.to_thread(update_subtitle, "")
        log_print(f"💬 7L 回覆: [僅執行動作/表情] ({current_model_tag})")
        current_history.append({"role": "assistant", "content": raw_stage2_text})
        
    asyncio.create_task(save_to_long_term_memory(DEFAULT_CHANNEL_ID, current_history))



async def fetch_fast_text_reply(user_input: str, custom_name: str, situation_prompt: str = "", history: Optional[List[Dict]] = None) -> Tuple[str, str, float]:
    """⚡ 【真人感即時第一反應 (Reflex)】：在收到訊息第一時間，由極速文字大腦 (Groq / Gemini Flash Lite) 毫秒級搶先開口！"""
    start_t = time.time()
    if not user_input or not user_input.strip():
        return ("", "", 0.0)

    clean_q = re.sub(r'\[[A-Z_]+(?::\s*[^\]]+)?\]', '', user_input).strip()
    if not clean_q:
        clean_q = user_input.strip()

    # 📜 提取最近對話歷史，確保反射神經具備完整的上下文記憶與連貫性！
    recent_history_str = ""
    if history:
        recent_dialogs = []
        for h in history[-6:]:
            role = "老爸" if h.get("role") == "user" else "7L"
            content = h.get("content", "")
            if isinstance(content, list):
                content = " ".join([p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"])
            clean_c = re.sub(r'\[[A-Z_]+(?::\s*[^\]]+)?\]', '', str(content)).strip()
            clean_c = re.sub(r'（(?:情境|系統|Tavily).*?）', '', clean_c).strip()
            if clean_c:
                recent_dialogs.append(f"{role}：{clean_c}")
        if recent_dialogs:
            recent_history_str = "【最近對話歷史（請務必結合上下文連貫理解，絕不可斷章取義或裝作不知道）】：\n" + "\n".join(recent_dialogs) + "\n\n"

    # 👥 辨識當前說話對象（老爸 vs TikTok 觀眾）
    tt_parsed = None
    m_tt1 = re.search(r'【TikTok 直播觀眾\s*([^】]+)\s*(留言|送禮)】[：:]\s*(.*)', clean_q)
    if m_tt1:
        tt_parsed = (m_tt1.group(1).strip(), m_tt1.group(3).strip())
    else:
        m_tt2 = re.search(r'【TikTok (?:官方提問箱|直播動態)】：觀眾「([^」]+)」(.*)', clean_q)
        if m_tt2:
            tt_parsed = (m_tt2.group(1).strip(), m_tt2.group(2).strip())
        elif "【TikTok" in clean_q:
            tt_parsed = ("直播觀眾", clean_q)

    if tt_parsed:
        audience_user, audience_content = tt_parsed
        v_prof = await get_viewer_profile(audience_user)
        v_call = v_prof.get("call")
        v_rel  = v_prof.get("relationship")
        v_imp  = v_prof.get("impression")
        if v_call or v_rel or v_imp:
            id_parts = []
            if v_rel:  id_parts.append(f"是{v_rel}")
            if v_call: id_parts.append(f"妳稱呼他為「{v_call}」")
            if v_imp:  id_parts.append(f"印象：{v_imp}")
            identity_line = f"【已知身份】{audience_user}：{'，'.join(id_parts)}。請自然使用該稱呼！\n"
        else:
            identity_line = f"【觀眾】妳與 {audience_user} 正在互動！\n"
        speaker_section = f"""【當前對象】：TikTok 直播觀眾「{v_call or audience_user}」（不是老爸！絕對不要對老爸說話！）
{identity_line}【觀眾動態/留言】：『{audience_content}』"""
    else:
        speaker_section = f"""【當前對象】：老爸（稱呼：「{custom_name}」）\n【老爸剛才說的話】：「{clean_q}」"""

    cloud_kn = await get_cloud_knowledge()
    cloud_kn_prompt = PromptTemplateEngine.format_cloud_knowledge_prompt(cloud_kn, is_tiktok=bool(tt_parsed), current_custom_name=custom_name)
    ck_sec = f"\n{cloud_kn_prompt}\n" if cloud_kn_prompt else ""

    prompt = f"""時間：{get_current_time_string()}
{ck_sec}
{PromptTemplateEngine.HARD_TECHNICAL_RULES}

{recent_history_str}{situation_prompt}

{speaker_section}
"""

    # 1. 🌟 絕對第一優先：Gemini 極速輕量前鋒矩陣 (高智商、自然口語、超大額度、具備完整工具調用能力)
    if GEMINI_KEYS:
        target_k_idx = get_pingpong_alternating_index(len(GEMINI_KEYS), CURRENT_GEMINI_KEY_STEP)
        target_key = GEMINI_KEYS[target_k_idx]
        try:
            client = genai.Client(api_key=target_key)
            fast_gemini_models = [
                "gemini-3.1-flash-lite",
                "gemini-3.5-flash-lite",
                "gemini-3-flash-preview",
                "gemini-3.1-pro-preview"
            ]
            for m_name in fast_gemini_models:
                try:
                    resp = await asyncio.wait_for(
                        client.aio.models.generate_content(
                            model=m_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                temperature=0.75,
                                max_output_tokens=150,
                                tools=GENAI_TOOLS
                            )
                        ),
                        timeout=2.4
                    )
                    txt = ""
                    try:
                        if resp.text:
                            txt = resp.text.strip()
                    except Exception:
                        pass
                        
                    if hasattr(resp, 'function_calls') and resp.function_calls:
                        for fc in resp.function_calls:
                            fn_name = getattr(fc, 'name', '')
                            fn_args = getattr(fc, 'args', {}) or {}
                            log_print(f"🛠️ [極速大腦調用工具] {fn_name}({fn_args})")
                            fast_target = "audience" if tt_parsed else "dad"
                            fast_user = audience_user if tt_parsed else "老爸"
                            asyncio.create_task(execute_tool_dispatch(fn_name, fn_args, caller_target=fast_target, caller_user=fast_user))
                            txt += f" [OUTCOME: {fn_name}({fn_args})] [HAD_TOOL_CALL]"
                            
                    if txt:
                        dur = time.time() - start_t
                        tag_name = m_name.replace("gemini-", "").replace("-preview", "")
                        return (txt, f"Gemini/{tag_name}", dur)
                except Exception:
                    continue
        except Exception:
            pass

    return ("", "", 0.0)

def check_requires_deep_gemini(user_input: str, stage1_text: str = "") -> bool:
    """判斷是否需要喚起 Gemini 旗艦大腦進行深度思考與工具調用 (若只是日常問答閒聊則直接略過以節省 API 額度)"""
    combined = f"{user_input} {stage1_text}".lower()
    if "[req_tool]" in combined or "[req_system]" in combined or "[open_browser" in combined:
        return True

    # 提取純淨文字 (去括號、去標籤、去前綴冒號)
    clean_q = re.sub(r'【.*?】[：:]?', '', user_input)
    clean_q = re.sub(r'\[[A-Z_]+(?::\s*[^\]]+)?\]', '', clean_q).strip(' ：:\t\r\n')

    # 1. 檢查是否直接命中本地真實 MIDI 曲庫 / catalog (如觀眾直接留言歌名「藍色狂想曲」、「Rhapsody in Blue」、「鐘」、「Liebestraum」)
    if clean_q:
        clean_ql = clean_q.lower()
        if clean_ql in AUTHENTIC_MIDI_MAP or clean_ql in MIDI_AI_MATCH_CACHE or any(clean_ql in k or k in clean_ql for k in AUTHENTIC_MIDI_MAP):
            return True

    # 2. 若當前鋼琴處於彈奏或待命狀態 (is_piano_active)，任何可能是歌名的簡短輸入 (如 Liebestraum-3, Canon, 換首好聽的) 優先走工具通道
    if is_piano_active and clean_q and len(clean_q) <= 40:
        non_song_chat = ["你好", "早安", "晚安", "在幹嘛", "謝謝", "哈哈", "掰掰", "再見", "老爸", "7l", "好聽", "讚", "太棒了"]
        if not any(k == clean_q.lower() for k in non_song_chat):
            return True

    # 3. 工具與深度操作關鍵字 (包含鋼琴、繪圖、搜尋、代碼等)
    tool_keywords = [
        "彈鋼琴", "彈琴", "點歌", "彈一首", "彈奏", "播放鋼琴", "換一首", "切歌", "鋼琴", "來一首", "來首", "播一首", "放一首", "彈", "換這首", "馬上換", "這就彈", "這首",
        "換音色", "切換音色", "鋼琴音色", "弦樂", "吉他", "小提琴", "大提琴", "薩克斯風", "木琴", "管風琴", "手風琴", "豎琴", "電鋼琴", "人聲合唱", "古箏", "卡林巴",
        "畫一張", "畫圖", "生成圖片", "畫個", "生圖", "畫一幅", "畫一隻", "繪製",
        "搜尋", "查一下", "上網查", "最新新聞", "天氣", "google搜尋", "幫我查",
        "寫程式", "寫代碼", "寫個遊戲", "俄羅斯方塊", "貪吃蛇", "執行程式", "python",
        "關閉麥克風", "開啟麥克風", "靜音麥克風", "清空記憶", "重置記憶", "記住大小", "記住位置", "記住現在位置", "記住當前位置", "記錄位置", "記錄大小", "記住模型位置", "記住模型", "記錄基準",
        "妳的電腦", "你的電腦", "專屬電腦", "虛擬機", "妳的虛擬機", "自己的電腦", "在電腦上", "電腦螢幕", "去妳的電腦", "在妳電腦", "操作電腦", "看妳螢幕", "看妳的螢幕", "自己去玩", "去玩", "看影片", "自主學習", "寫日記", "玩遊戲", "自主探索",
        "deepseek", "r1", "深度推理", "智能體", "agent", "autogen", "crewai", "瀏覽器操作", "openclaw", "harness",
        "鋼琴音量", "鋼琴大聲", "鋼琴小聲", "鋼琴靜音", "倍速", "演奏速度", "混在一起彈", "雜在一起彈", "合體", "神仙打架", "mashup"
    ]
    if any(k in combined for k in tool_keywords) or clean_q.startswith("彈"):
        return True

    return False

def is_piano_song_request(user_input: str) -> bool:
    """判斷觀眾發言是否為點歌或彈琴請求。
    【老爸最高鐵律】：沒有說彈就不是當作歌名 (格式: 彈《歌名》或 彈youtube《歌名》)，除非很明顯是歌名！
    """
    if not user_input or not user_input.strip():
        return False
    clean_q = re.sub(r'【.*?】[：:]?', '', user_input)
    clean_q = re.sub(r'\[[A-Z_]+(?::\s*[^\]]+)?\]', '', clean_q).strip(' ：:\t\r\n')
    if not clean_q:
        return False
    clean_ql = clean_q.lower().strip()

    # 🛑 1. 純數字或標點符號（如 "67", "666", "777", "123"）絕對不是歌名！
    if clean_ql.isdigit() or re.fullmatch(r'[\d\s.,!?:;~～\-_+]+', clean_ql):
        return False

    # 🛑 2. 長度過短且無點歌動詞，絕對不是歌名
    if len(clean_ql) <= 1:
        return False

    # 🛑 3. 排除日常問候、感嘆詞、詢問鋼琴視窗、日常抱怨
    non_song_dialogue = [
        "拿出來", "出來了沒", "沒出來", "在哪", "開了沒", "沒開", "收起來", "關掉", "不見了",
        "有看到嗎", "你的鋼琴呢", "是不是沒", "沒看到", "看不到", "視窗", "鋼琴好大", "鋼琴好小", "什麼牌子",
        "笑死", "太強了", "好聽", "厲害", "你好", "哈囉", "安安", "早安", "晚安", "在嗎", "在幹嘛", "主播好"
    ]
    if any(k == clean_ql for k in non_song_dialogue):
        return False
    if any(k in clean_ql for k in ["拿出來", "出來了沒", "沒出來", "開了沒", "沒開", "收起來", "視窗在哪", "鋼琴呢"]):
        if not any(k in clean_ql for k in ["彈一首", "點歌", "播放", "放一首", "來一首", "換這首", "聽這首"]):
            return False

    # 🌟 4. 符合「標準點歌格式」：明確含有「彈」、「點」、「聽」、「放」、「播」等動詞
    # 格式包含：彈《歌名》、彈youtube《歌名》、彈yt《歌名》、彈 歌名、點歌、想聽、來一首、播放 等
    explicit_song_verbs = [
        "彈", "點歌", "點一首", "想聽", "來一首", "來首", "播放鋼琴", "播一首", "放一首",
        "換一首", "切歌", "彈奏", "彈琴", "彈鋼琴", "能彈", "可以彈", "幫我彈", "請彈"
    ]
    if any(v in clean_ql for v in explicit_song_verbs):
        return True

    # 🌟 5. 「除非很明顯是歌名」：
    # 5A. 帶有書名號《...》或引號「...」包裹，且書名號內不是純數字或單字
    book_titles = re.findall(r'[《「](.*?)[》」]', clean_q)
    for bt in book_titles:
        bt_clean = bt.strip()
        if len(bt_clean) >= 2 and not bt_clean.isdigit():
            return True

    # 5B. 含有知名音樂家/歌手前綴 + 曲名
    famous_artists = [
        "蕭邦", "周杰倫", "李斯特", "貝多芬", "莫札特", "巴哈", "德布西", "拉赫曼尼諾夫",
        "柴可夫斯基", "久石讓", "林俊傑", "陳奕迅", "鄧紫棋", "五月天", "告五人", "yoasobi",
        "animenz", "canacana", "米津玄師"
    ]
    if any(artist in clean_ql for artist in famous_artists) and len(clean_ql) >= 4:
        return True

    # 5C. 明確且具代表性的知名經典曲目（無歧義專有曲名，需完全吻合）
    famous_classics = [
        "千本櫻", "卡農", "大魚", "起風了", "晴天", "夜曲", "青花瓷", "告白氣球",
        "稻香", "夢中的婚禮", "給愛麗絲", "土耳其進行曲", "天空之城", "龍貓", "神隱少女"
    ]
    if any(clean_ql == fc for fc in famous_classics):
        return True

    # 其餘無「彈」且不明顯是歌名者，一律回傳 False！
    return False

async def prefetch_song_midi_background(song_query: str):
    """背景非同步預熱/預查 MIDI 曲庫與 AI 語意匹配（100% 由 Gemini 高智商大腦判定）"""
    try:
        if not is_piano_song_request(song_query):
            return
        available_files = [os.path.basename(p) for p in glob.glob(os.path.join(MIDI_SHEETS_DIR, "*.mid"))]
        ai_intent = await resolve_piano_intent_by_ai(song_query, available_files)
        if ai_intent.get("is_song_request") and ai_intent.get("song_title"):
            await resolve_local_midi_file(ai_intent["song_title"])
    except Exception:
        pass

# ────────────────────────────────────────────────────────
# 🧠 15. 全集中全景時序記憶中樞與對話派發系統 (Unified Mind-Stream Architecture)
# ────────────────────────────────────────────────────────
# 💡 核心設計：
#    - `UNIFIED_LIVE_MEMORY`: 全局唯一統一記憶時間線（deque maxlen=300 + 本地 unified_memory.json 持久化）。
#      老爸對話、直播觀眾彈幕、7L 自身發言、鋼琴演奏等全事件 100% 匯流同一時間線。
#    - 所有 Gemini 呼叫點（老爸旗艦主腦、主播記憶看板、Live 專屬雙軌、自主發話、Live 哨兵）
#      無論輪詢切換到哪個 API Key 或模型，100% 讀取同一份完整全景時序劇本，徹底消滅思想斷裂！

UNIFIED_MEMORY_FILE = os.path.join(DATA_DIR, "unified_memory.json")
UNIFIED_LIVE_MEMORY: deque = deque(maxlen=300)
_LAST_UNIFIED_SAVE_TIME = 0.0

TIKTOK_CHATROOM_MEMORY: List[Dict[str, Any]] = []
STREAMER_MIND_BOARD: deque = deque(maxlen=200)

def _save_unified_memory_to_disk():
    """安全將最新全域記憶時間線序列化保存至本地磁碟並同步備份至雲端 Firestore"""
    global UNIFIED_LIVE_MEMORY, db
    try:
        data_to_save = list(UNIFIED_LIVE_MEMORY)
        temp_file = UNIFIED_MEMORY_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        if os.path.exists(temp_file):
            if os.path.exists(UNIFIED_MEMORY_FILE):
                os.replace(temp_file, UNIFIED_MEMORY_FILE)
            else:
                os.rename(temp_file, UNIFIED_MEMORY_FILE)
                
        # ☁️ 同步備份最新全集中全景時序記憶至雲端 Firestore
        if db is not None:
            async def sync_unified_to_cloud(items):
                try:
                    await db.collection("unified_memory").document("live_stream_timeline").set({
                        "timeline": items[-150:],
                        "last_updated": time.time()
                    }, merge=True)
                except Exception:
                    pass
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(sync_unified_to_cloud(data_to_save))
            except RuntimeError:
                pass
    except Exception:
        pass

def append_to_unified_memory(speaker: str, target: str, content: str, role: str = "user", source: str = "text"):
    """🌟 全集中全景記憶中樞唯一寫入常式：
    確保老爸說話、觀眾彈幕、7L自身發言、系統事件全面匯流至單一全時序時間線。
    解決跨 API Key、跨模型輪詢時思維斷裂與失憶問題！
    """
    global UNIFIED_LIVE_MEMORY, _LAST_UNIFIED_SAVE_TIME, TIKTOK_CHATROOM_MEMORY
    clean_c = content.strip()
    if not clean_c:
        return

    # 防重疊去重：若與上一筆 speaker 與 content 完全相同且時間差 < 1.2 秒，略過
    if UNIFIED_LIVE_MEMORY:
        last_item = UNIFIED_LIVE_MEMORY[-1]
        if (last_item.get("speaker") == speaker and 
            last_item.get("content") == clean_c and 
            (time.time() - last_item.get("time", 0) < 1.2)):
            return

    now_t = time.time()
    try:
        t_str = datetime.fromtimestamp(now_t, tz=ZoneInfo('Asia/Taipei')).strftime('%H:%M:%S')
    except Exception:
        t_str = datetime.now().strftime('%H:%M:%S')

    entry = {
        "time": now_t,
        "time_str": t_str,
        "speaker": speaker,
        "target": target,
        "content": clean_c,
        "role": role,
        "source": source
    }
    UNIFIED_LIVE_MEMORY.append(entry)

    # 保持向後相容 TIKTOK_CHATROOM_MEMORY
    TIKTOK_CHATROOM_MEMORY.append({"user": speaker, "content": clean_c, "time": now_t})
    if len(TIKTOK_CHATROOM_MEMORY) > 200:
        TIKTOK_CHATROOM_MEMORY.pop(0)

    # 磁碟寫入節流（每隔 2 秒或必要時儲存）
    if now_t - _LAST_UNIFIED_SAVE_TIME > 2.0:
        _LAST_UNIFIED_SAVE_TIME = now_t
        try:
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, _save_unified_memory_to_disk)
        except RuntimeError:
            _save_unified_memory_to_disk()

def get_unified_memory_context(limit: int = 80) -> str:
    """提取全集中全景時序記憶，格式化為各梯隊 Gemini 秒懂的全景對話劇本"""
    global UNIFIED_LIVE_MEMORY
    if not UNIFIED_LIVE_MEMORY:
        return "（目前系統與直播間剛啟動，尚無累積對話記憶）"

    items = list(UNIFIED_LIVE_MEMORY)[-limit:]
    lines = []
    for it in items:
        t_str = it.get("time_str", "即時")
        spk = it.get("speaker", "有人")
        tgt = it.get("target", "")
        cnt = it.get("content", "")
        role = it.get("role", "user")

        if role == "system" or spk == "系統":
            lines.append(f"[{t_str}] 📢【系統事件】：{cnt}")
        elif spk == "7L":
            target_str = f"(對{tgt}說)" if tgt and tgt != "所有人" else ""
            lines.append(f"[{t_str}] 🤖【7L】{target_str}：{cnt}")
        elif spk in ["老爸", "dad", "E5"]:
            lines.append(f"[{t_str}] 👑【老爸】(對 7L 說)：{cnt}")
        else:
            target_str = f"(對{tgt}說)" if tgt and tgt != "7L" else ""
            lines.append(f"[{t_str}] 💬【{spk}】{target_str}：{cnt}")

    return "\n".join(lines)

def init_unified_memory():
    """啟動時載入歷史全集中記憶，若無則從本地老爸與觀眾歷史自動融合成最新時序時間線"""
    global UNIFIED_LIVE_MEMORY
    if os.path.exists(UNIFIED_MEMORY_FILE):
        try:
            with open(UNIFIED_MEMORY_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list) and loaded:
                    UNIFIED_LIVE_MEMORY.extend(loaded[-250:])
                    log_print(f"📜 [全集中記憶] 成功從 {UNIFIED_MEMORY_FILE} 載入 {len(UNIFIED_LIVE_MEMORY)} 筆全景記憶！")
                    return
        except Exception as e:
            log_print(f"⚠️ [全集中記憶載入異常]: {e}")

    # 若本地無 unified_memory.json，嘗試自雲端 Firestore unified_memory 載入
    if db is not None:
        try:
            doc = asyncio.run(db.collection("unified_memory").document("live_stream_timeline").get()) if not asyncio.get_event_loop().is_running() else None
            if doc and doc.exists:
                t_list = doc.to_dict().get("timeline", [])
                if t_list:
                    UNIFIED_LIVE_MEMORY.extend(t_list[-250:])
                    _save_unified_memory_to_disk()
                    log_print(f"📜 [全集中記憶] 成功自雲端 Firestore unified_memory 載入 {len(UNIFIED_LIVE_MEMORY)} 筆記憶！")
                    return
        except Exception:
            pass

def add_to_streamer_mind_board(user_display: str, unique_id: str, content: str, source: str = "tiktok"):
    """將接收到的彈幕/留言/事件寫入 7L 記憶腦袋，一排一排排列記錄，由主播自主排程讀取與發話"""
    global STREAMER_MIND_BOARD, TIKTOK_CHATROOM_MEMORY
    item = {
        "id": f"msg_{time.time()}_{random.randint(1000, 9999)}",
        "time": time.time(),
        "time_str": datetime.now(ZoneInfo('Asia/Taipei')).strftime('%H:%M:%S'),
        "user": user_display,
        "unique_id": unique_id,
        "content": content,
        "source": source,
        "status": "unread"
    }
    STREAMER_MIND_BOARD.append(item)
    
    # 🌟 寫入全集中記憶中樞（確保老爸輸入與觀眾彈幕統一匯流）
    speaker = "老爸" if (unique_id == "dad" or source in ["mic", "text_file", "console"]) else f"TikTok 觀眾「{user_display}」"
    append_to_unified_memory(
        speaker=speaker,
        target="7L",
        content=content,
        role="user",
        source=source
    )
        
    unread_count = sum(1 for m in STREAMER_MIND_BOARD if m["status"] == "unread")
    log_print(f"📥 [記憶腦袋 寫入] {user_display}: {content} (🧠 看板累積未讀: {unread_count} 筆)")
    
    # 🎹 依老爸鐵律判定是否為點歌意圖（必須有「彈」或明顯歌名），再交由 Gemini 確認
    if is_piano_active and current_piano_song_title and content and is_piano_song_request(content):
        async def evaluate_and_queue_with_gemini(raw_text: str):
            try:
                available_files = [os.path.basename(p) for p in glob.glob(os.path.join(MIDI_SHEETS_DIR, "*.mid"))]
                intent = await resolve_piano_intent_by_ai(
                    raw_text, 
                    available_files,
                    current_playing_title=current_piano_song_title,
                    current_playing_file=current_piano_midi_file
                )
                if intent.get("is_song_request") and intent.get("song_title"):
                    target_song = intent["song_title"]
                    cand_midi = os.path.join(MIDI_SHEETS_DIR, intent["matched_files"][0]) if intent.get("matched_files") else ""
                    log_print(f"🎵 [Gemini 意圖確認] 高智商大腦確認老爸/觀眾點播《{target_song}》，自動預載排入待播隊列！")
                    await play_virtual_piano(target_song, midi_file=cand_midi, requester_name=user_display, target="audience")
            except Exception:
                pass
        asyncio.create_task(evaluate_and_queue_with_gemini(content))

def mark_streamer_mind_board_as_read(unique_id: str = None, content: str = None):
    """📖 將 7L 記憶腦袋看板中的指定留言/對話標記為已讀"""
    global STREAMER_MIND_BOARD
    marked_cnt = 0
    for m in STREAMER_MIND_BOARD:
        if m.get("status") == "unread":
            if unique_id and m.get("unique_id") == unique_id:
                m["status"] = "read"
                marked_cnt += 1
            elif content and m.get("content") == content:
                m["status"] = "read"
                marked_cnt += 1
            elif not unique_id and not content:
                m["status"] = "read"
                marked_cnt += 1
    if marked_cnt > 0:
        log_print(f"📖 [記憶腦袋 已讀] 已將 {marked_cnt} 筆看板項目標記為已讀")

# 8 大大腦優先順序梯隊 (頂配高智商旗艦大腦優先)
STREAMER_MIND_MODELS = [
    # ⚡ 極速輕量前鋒 (超低延遲、自然口語、秒回)
    "gemini-3.1-flash-lite",               # ⚡ 第 1 位：超低延遲、自然口語、秒回首選
    "gemini-3.5-flash-lite",               # 🛡️ 第 2 位：超大額度輕量保底防線
    "gemini-3-flash-preview",              # ⚡ 第 3 位：閃電推理預覽
    
    # 🧠 高智商 Pro & 主力大腦
    "gemini-3.1-pro-preview",              # 🧠 第 4 位：超高智商 Pro 預覽
    "gemini-3.5-flash",                    # 🥈 第 5 位：高智商穩定主力保底
    "gemini-3.6-flash",                    # 👑 第 6 位：最新高智商旗艦主力，視覺與工具調用精準
    "gemini-3.7-flash",                    # 👑 第 7 位：頂配旗艦大腦
    "gemini-3.8-flash",                    # 🚀 第 8 位：2026 全新頂配旗艦大腦（深度思考與多模態頂尖推理）
]

def get_recent_100_memory_context() -> str:
    """提取當前直播間/系統累積的最新 100 筆全集中對話與彈幕記憶（向後相容調用）"""
    return get_unified_memory_context(limit=100)

async def judge_subconscious_intent_via_live_api(memory_context: str, unread_batch_desc: str) -> dict:
    """⚡ 【Live API 潛意識發言決策哨兵】：
    利用 Live API 無限額度特性，實時審閱 100 句記憶與新彈幕，
    極速判定當前是否該開口發話（二元決策），絕不浪費主力模型額度！
    回傳 dict: {"should_speak": bool, "target": str, "focus": str, "song": str, "raw": str}
    """
    candidate_keys = get_dynamic_live_key_candidates(KEYS_AUDIENCE_LIVE if KEYS_AUDIENCE_LIVE else GEMINI_KEYS)
    for idx, g_key in enumerate(candidate_keys[:4]):
        client = genai.Client(api_key=g_key)
        try:
            live_cfg = types.LiveConnectConfig(
                response_modalities=[types.Modality.AUDIO],
                output_audio_transcription=types.AudioTranscriptionConfig(),
                system_instruction=types.Content(parts=[types.Part(text="""妳是 7L 的背景潛意識決策神經（Subconscious Sentry）。
妳正在即時審查全集中累積的最新滾動記憶與剛收到的新輸入（包含老爸的麥克風語音、電腦打字、或直播觀眾彈幕）。
請快速判斷 7L 當前是否應該開口發話回應？
【🎹 邊彈邊聊特別規範】：即使 7L 背景正在彈奏鋼琴，只要有人說話、提問、打招呼、點歌或留言互動，一律正常判定 [SPEAK: ...]！7L 具備邊彈鋼琴邊聊天讀訊息的即時多工能力，絕不因彈琴而保持沉默！
1. 【老爸發話（語音/打字）】：
   - ⚠️ 僅當輸入明確標註為【老爸】或來自麥克風/主腦通道時才可判定為老爸！
   - 若老爸在對妳說話、下指令、問話、調侃、點歌、或互動 ➔ 請輸出：[SPEAK: target=老爸, focus=指令或話題焦點, song=歌名(若點歌)]
   - 若老爸在專注自言自語、喃喃自語、或純背景雜音/咳嗽 ➔ 請輸出：[SILENCE]
2. 【直播觀眾彈幕】：
   - 當輸入標記為【TikTok 直播觀眾】或包含具體觀眾名稱時：
   - ⚠️【嚴格認人】：target 必須填寫該觀眾用戶名/暱稱（例如：小丑、阿九、或留言者暱稱），絕對 100% 嚴禁填「老爸」！
   - 若有觀眾在點歌 ➔ 請輸出：[SPEAK: target=用戶名, song=歌名, focus=點歌]
   - 若有觀眾在打招呼、提問、稱讚或有值得接梗互動的精彩話題 ➔ 請輸出：[SPEAK: target=用戶名, focus=話題重點]
   - 若為無聊刷屏、無意義表情/符號、或目前無需插話 ➔ 請輸出：[SILENCE]
嚴禁輸出任何多餘聊天內容，只輸出 [SILENCE] 或 [SPEAK: ...]！""")])
            )
            async with asyncio.timeout(3.5):
                async with client.aio.live.connect(model="gemini-3.1-flash-live-preview", config=live_cfg) as session:
                    prompt_eval = f"""【最新滾動記憶與近期全景上下文】：
{memory_context}

【剛收到的最新未讀輸入】：
{unread_batch_desc}

請即刻給出潛意識發言決策（[SILENCE] 或 [SPEAK: ...]）："""
                    await session.send_realtime_input(text=prompt_eval)
                    
                    decision_text = ""
                    async for resp in session.receive():
                        c = resp.server_content
                        if c:
                            if c.output_transcription and c.output_transcription.text:
                                decision_text += c.output_transcription.text
                            if c.turn_complete or getattr(c, 'generation_complete', False):
                                break
                                
                    decision_clean = decision_text.strip()
                    if decision_clean:
                        if "[SILENCE]" in decision_clean or decision_clean.upper() == "SILENCE" or "[PASS]" in decision_clean:
                            return {"should_speak": False, "raw": decision_clean}
                        
                        target_match = re.search(r'target\s*=\s*([^,\]]+)', decision_clean, re.IGNORECASE)
                        focus_match = re.search(r'focus\s*=\s*([^,\]]+)', decision_clean, re.IGNORECASE)
                        song_match = re.search(r'song\s*=\s*([^,\]]+)', decision_clean, re.IGNORECASE)
                        
                        t_user = target_match.group(1).strip() if target_match else ""
                        t_focus = focus_match.group(1).strip() if focus_match else ""
                        t_song = song_match.group(1).strip() if song_match else ""
                        
                        return {
                            "should_speak": True,
                            "target": t_user,
                            "focus": t_focus,
                            "song": t_song,
                            "raw": decision_clean
                        }
        except Exception:
            continue
            
    # 若 Live API 暫時連線繁忙，預設放行由主力大腦判定
    return {"should_speak": True, "target": "", "focus": "", "song": "", "raw": "FALLBACK_ALLOW"}

async def streamer_mind_loop_worker(vts, input_queue):
    """🧠 7L 主播記憶腦袋持續讀取與自由意志發話協程：
    1. 背景保持最新 100 句記憶上下文
    2. 透過無限額度 Live API 潛意識哨兵極速做發言時機判斷
    3. 判定該開口時，喚醒 7 大主力大腦梯隊 (3.1 Flash Lite ➔ 3.5 ➔ 3.7) 讀取 100 句記憶精準開口！
    """
    global current_ai_state, is_piano_active, current_piano_song_title, last_interaction_time, current_model_tag, TIKTOK_CHATROOM_MEMORY, CURRENT_SPEAKING_TARGET
    log_print("🧠 [主播記憶腦袋]協程已就緒")
    
    while True:
        try:
            await asyncio.sleep(1.0)
            
            # 1. 狀態檢查：若正在說話、思考、或老爸正在對話，先保持安靜
            is_speaking = False
            try:
                is_speaking = pygame.mixer.get_init() and pygame.mixer.music.get_busy() or not speech_queue.empty() or current_ai_state == "TALKING"
            except Exception:
                pass
                
            if is_speaking or current_ai_state == "THINKING":
                continue
                
            # 🎹 鋼琴演奏中不阻擋讀訊息：支援邊彈琴邊即時讀取觀眾彈幕/老爸留言並開口互動！
                
            # 若老爸在 5 秒內剛說過話，優先等待老爸
            if time.time() - last_interaction_time < 5.0 and CURRENT_SPEAKING_TARGET == "dad":
                continue
                
            # 2. 檢查記憶腦袋中是否有未讀彈幕
            unread_items = [m for m in STREAMER_MIND_BOARD if m["status"] == "unread"]
            if not unread_items:
                continue
                
            # 3. 取出最新批次（1 ~ 5 筆）
            batch_to_process = unread_items[-5:]
            for m in batch_to_process:
                m["status"] = "processing"
                
            # 組合看板彈幕清單與認人資料
            board_lines = []
            users_involved = []
            viewer_profiles_text = []
            has_dad_message = False

            for m in batch_to_process:
                u_id = m.get('unique_id', '')
                u_name = m.get('user', '')
                u_source = m.get('source', '')
                if u_id == 'dad' or u_source in ['mic', 'text_file', 'console']:
                    has_dad_message = True
                    board_lines.append(f"- [{m['time_str']}] 【老爸】：{m['content']}")
                else:
                    board_lines.append(f"- [{m['time_str']}] 【TikTok 直播觀眾「{u_name}」】：{m['content']}")
                    if u_name not in users_involved:
                        users_involved.append(u_name)

            board_context = "\n".join(board_lines)
            target_audience_desc = "、".join(users_involved) if users_involved else "觀眾"

            # 👥 查詢並注入觀眾認人資料 (call/relationship/impression)
            for u in users_involved:
                v_prof = await get_viewer_profile(u)
                v_call = v_prof.get("call")
                v_rel = v_prof.get("relationship")
                v_imp = v_prof.get("impression")
                if v_call or v_rel or v_imp:
                    id_parts = []
                    if v_rel: id_parts.append(f"關係:「{v_rel}」")
                    if v_call: id_parts.append(f"習慣稱呼:「{v_call}」")
                    if v_imp: id_parts.append(f"印象:「{v_imp}」")
                    viewer_profiles_text.append(f"  * 熟客觀眾【{u}】：{'，'.join(id_parts)}（請親切稱呼他「{v_call or u}」）")
                else:
                    viewer_profiles_text.append(f"  * 觀眾【{u}】：新進或尚未建檔，請親切稱呼他「{u}」")

            # 📜 提取最新 100 句完整記憶
            memory_100_context = get_recent_100_memory_context()
            
            # ⚡ 階段一：由 Live API 潛意識哨兵以無限額度進行實時發言決策
            if not has_dad_message:
                board_context_for_sentry = f"【注意：以下全部為 TikTok 直播觀眾彈幕，絕非老爸！target 必須從以下觀眾選取：{target_audience_desc}，絕對嚴禁填老爸】：\n" + board_context
            else:
                board_context_for_sentry = board_context

            sentry_decision = await judge_subconscious_intent_via_live_api(memory_100_context, board_context_for_sentry)
            if not sentry_decision["should_speak"]:
                for m in batch_to_process:
                    m["status"] = "read"
                log_print(f"🤫 [Live 潛意識哨兵] 審查 100 句記憶後判定：目前無需發言 / 刷屏 ➔ [PASS] 略過 (0 消耗主力額度)")
                continue
                
            sentry_target = sentry_decision.get("target", "").strip()
            if not has_dad_message:
                # 🚨 100% 強制認人防呆鐵律：本批次全部為觀眾留言，目標絕對不可能是老爸！
                if not sentry_target or sentry_target in ["老爸", "dad", "E5", "7Lβ", "主播", "妳", "你"]:
                    log_target = users_involved[0] if users_involved else target_audience_desc
                else:
                    log_target = sentry_target
            else:
                log_target = sentry_target or "老爸"

            log_focus = sentry_decision.get("focus") or "精彩互動"
            log_print(f"🚨 [Live 潛意識哨兵 喚醒主力] 判定應開口！目標: {log_target} | 焦點: {log_focus}")
            
            # 準備系統 Prompt（注入 100 句完整記憶、認人檔案與哨兵焦點）
            user_profile = await get_user_profile()
            current_custom_name = user_profile.get("custom_name", DEFAULT_USER_TITLE)
            if is_piano_active and current_piano_song_title:
                piano_status = f"【🎹 鋼琴邊彈邊聊】：妳目前正坐在 88 鍵鋼琴前為大家演奏《{current_piano_song_title}》中！妳完全支援「邊彈琴邊與大家聊天/讀訊息/互動」（像鋼琴主播一樣邊彈邊隨性聊兩句）。若有人點歌或詢問進度（如「還有多久到我的」），請口頭溫柔告知排隊進度（例如：『這首彈完下一首就輪到你囉！』）；若是一般留言稱讚或聊天，隨性親切回覆 1~2 句即可，鋼琴演奏在背景持續進行。"
            else:
                piano_status = "目前背景演奏已結束或未在彈琴。"
            
            profiles_block = "\n".join(viewer_profiles_text) if viewer_profiles_text else "（暫無觀眾檔案）"
            if not has_dad_message:
                role_strict_block = f"""【🚨 認人與對象最高鐵律 (100% 絕對遵循)】
面前正在留言的是【TikTok 直播觀眾：{target_audience_desc}】，【絕對不是老爸】！
【👥 觀眾認人檔案】：
{profiles_block}
🎯 回應對象：請直接對觀眾「{log_target}」說話！親切稱呼他的名字或習慣稱呼！
🛑 【嚴格禁止】：面前是對話觀眾，絕對不准稱呼對方為「老爸」！絕對不准向老爸轉述或對老爸說話！"""
            else:
                role_strict_block = f"""【💬 當前對話對象】：包含老爸與直播觀眾。請分清楚對象！"""

            sys_instruction = f"""妳是 7L，正在 TikTok 開台直播。
時間：{get_current_time_string()}

{role_strict_block}

【📜 直播間最新 100 句滾動記憶歷史（掌握全局話題與脈絡）】：
{memory_100_context}

【🧠 剛剛收到的最新彈幕】：
{board_context}

【⚡ 潛意識焦點提示】：回應對象：{log_target}，焦點：{log_focus}。
【當前狀態】：{piano_status}
{get_tiktok_live_telemetry()}

【💬 主播心智與發話規範】：
1. 🧠 【主播腦內心想】：請先在句首輸出 `[THOUGHT: 對彈幕的真實思緒/自由吐槽/判斷]`（此部分為大腦私密空間，系統保證 100% 靜音排除，絕不唸出）。
2. ⚡ 【短句精煉鐵律 (極重要)】：直播節奏明快，每次真正開口說話請嚴格保持「1 ~ 2 句短句（約 15 ~ 35 字，絕對不超過 50 字）」！
   - 口語自然、簡短直接、重點明確、接梗俐落，隨性真實。
   - 🛑 【嚴禁長篇大論】：絕不長段自說自話、絕不說教、絕不一口氣拋出一堆反問句或追問句！
3. 🎯 【稱呼精準認人】：直接對觀眾本人（{log_target}）說話，親切念出對方的名字/暱稱！若他是問點歌進度（如「還有多久到我的」），請根據狀態溫柔安撫或告知排隊進度！
4. 🛑 【嚴格禁止叫老爸】：若面對觀眾，絕對不准稱呼對方為「老爸」！
5. 🛑 【嚴禁報幕與元語言】：絕對禁止說「我看到你留言說了...」、「我看到我自己說了...」、「畫面上顯示我的字幕...」、「我看著看板...」等機械化報幕字眼！直接像真人主播一樣自然開口對答即可！
6. 🎹 鋼琴點歌：若觀眾點歌，請【直接調用工具 `play_virtual_piano(song_name='歌名')`】開彈！若觀眾要求妳自創曲、即興創作一首，請調用 `compose_and_play_original_piano`！
7. 🛡️ 若彈幕全為無意義刷屏，可輸出 [PASS] 略過。
8. 標籤支援：
   - 表情：[EXPRESSION: 臉紅/生氣/愛心/星星/皺眉/震驚/WINK]（支援句中多次隨心切換，上半句與下半句可隨意變換神態）
   - 視線走位：[LOOK: ROLL/CENTER/LEFT/RIGHT]、[MOVE: 靠近/躲角落/鋼琴旁/中間/原位]
   - 觀眾記憶：[VIEWER_UPDATE:用戶名|CALL:暱稱|REL:關係|IMP:印象]
   - 規範：輸出時自行加上完整中文標點符號（逗號、句號等）進行自然斷句，嚴禁使用 Emoji。"""

            prompt_user_input = f"請結合剛才 100 句記憶與最新彈幕，先心想 [THOUGHT: ...] 再以自然俐落的短句開口回應（1~2句，30字內，可隨興在句中自由切換 [EXPRESSION: ...] 表情）："
            
            # 4. 呼叫大腦模型矩陣 (依老爸指定 7 梯隊優先級輪流嘗試: 3.1 Flash Lite ➔ 3.5 Flash Lite ➔ 3 Flash ➔ 3.1 Pro ➔ 3.5 ➔ 3.6 ➔ 3.7)
            candidate_keys = [k for k in (KEYS_AUDIENCE_LIVE if KEYS_AUDIENCE_LIVE else GEMINI_KEYS) if k]
            random.shuffle(candidate_keys)
            
            full_reply = ""
            used_model_name = ""
            tool_output_text = ""
            
            for g_key in candidate_keys[:6]:
                if full_reply: break
                client = genai.Client(api_key=g_key)
                for model_name in STREAMER_MIND_MODELS:
                    try:
                        resp = await asyncio.wait_for(
                            client.aio.models.generate_content(
                                model=model_name,
                                contents=[
                                    types.Content(role="user", parts=[types.Part(text=f"{sys_instruction}\n\n{prompt_user_input}")])
                                ],
                                config=types.GenerateContentConfig(
                                    temperature=0.78,
                                    max_output_tokens=150,
                                    tools=GENAI_PROACTIVE_TOOLS
                                )
                            ),
                            timeout=4.5
                        )
                        
                        raw_reply = resp.text.strip() if resp.text else ""
                        tool_out = ""
                        if resp.function_calls:
                            for fc in resp.function_calls:
                                fn_name = getattr(fc, 'name', '')
                                fn_args = getattr(fc, 'args', {}) or {}
                                log_print(f"🛠️ [主播大腦調用工具] {fn_name}({fn_args})")
                                t_res = await execute_tool_dispatch(fn_name, fn_args, caller_target="audience", caller_user=log_target)
                                if fn_name == "search_google":
                                    s_summary = await summarize_search_to_speech(fn_args.get("query", ""), t_res, user_role_name="大家")
                                    tool_out += (" " + s_summary)
                                else:
                                    tool_out += (" " + t_res)
                        
                        clean_raw = re.sub(r'\[PASS\]', '', raw_reply, flags=re.IGNORECASE).strip()
                        # 🌟 若大腦調用了工具但未生成口語台詞 (常見於純 Function Call 回合)，由 7L 自然即興生成親切口語回應
                        if not clean_raw and resp.function_calls:
                            for fc in resp.function_calls:
                                fc_name = getattr(fc, 'name', '')
                                fc_args = getattr(fc, 'args', {}) or {}
                                if fc_name == "play_virtual_piano":
                                    song_q = clean_song_title_for_speech(fc_args.get("song_name", ""))
                                    if is_piano_active and current_piano_song_title:
                                        clean_raw = f"[EXPRESSION: 星星眼] {log_target}，沒問題！《{song_q or '這首'}》我先幫你排進清單，等現在這首彈完馬上幫你彈喔！"
                                    else:
                                        clean_raw = f"[EXPRESSION: 星星眼] {log_target}，好喔！這就為你彈《{song_q or '這首'}》！"
                                    break
                                elif fc_name == "compose_and_play_original_piano":
                                    clean_raw = f"[EXPRESSION: 星星眼] {log_target}，沒問題！我現在就現場為你即興創作一首，聽聽看喔！"
                                    break
                                elif fc_name == "mashup_virtual_piano":
                                    clean_raw = f"[EXPRESSION: 星星眼] {log_target}，收到！雙曲狂暴合奏這就來！"
                                    break

                        if not clean_raw and not tool_out.strip() and ("[PASS]" in raw_reply or raw_reply == "PASS"):
                            for m in batch_to_process:
                                m["status"] = "read"
                            log_print(f"🤫 7L (看板過濾): 研判為無關刷屏 ➔ [PASS] 略過")
                            full_reply = "[PASS]"
                            break
                            
                        final_res = clean_raw if clean_raw else tool_out.strip()
                        if final_res:
                            full_reply = final_res
                            used_model_name = model_name
                            tool_output_text = tool_out
                            break
                    except Exception as gen_err:
                        err_str = str(gen_err)
                        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                            break
                        continue
                        
            # 5. 標記處理完成
            for m in batch_to_process:
                m["status"] = "read"
                
            if not full_reply or full_reply == "[PASS]":
                continue
                
            # 6. 執行動作並發送發話隊列
            clean_reply = TextCleanEngine.remove_system_hints(full_reply)
            clean_reply = re.sub(r'^(?:回應|回覆|動作顯示|主播|說道|回答)[：:\s]+', '', clean_reply, flags=re.IGNORECASE).strip()
            clean_reply = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])', '', clean_reply)
            clean_reply = re.sub(r'\s+([，。！？,.!?:;])', r'\1', clean_reply)
            clean_reply = re.sub(r'\s{2,}', ' ', clean_reply).strip()
            
            m_tag = f"🧠 Mind-Stream ({used_model_name.replace('gemini-', '')})"
            log_print(f"🤖 原始大腦輸出: {clean_reply} (⚡ {m_tag})")
            
            # 👥 記錄觀眾資料標籤
            for v_match in re.finditer(
                r'\[VIEWER_UPDATE[：:]\s*([^|\]]+?)(?:\|CALL[：:]\s*([^|\]]+?))?(?:\|REL[：:]\s*([^|\]]+?))?(?:\|IMP[：:]\s*([^|\]]+?))?\]',
                clean_reply, re.IGNORECASE
            ):
                vu_name = v_match.group(1).strip()
                vu_call = v_match.group(2).strip() if v_match.group(2) else None
                vu_rel  = v_match.group(3).strip() if v_match.group(3) else None
                vu_imp  = v_match.group(4).strip() if v_match.group(4) else None
                asyncio.create_task(save_viewer_profile(vu_name, call=vu_call, relationship=vu_rel, impression=vu_imp))
                log_print(f"👥 [認人] 記住觀眾 {vu_name}：稱={vu_call} 關係={vu_rel} 印象={vu_imp}")
            
            spoken = await execute_actions(vts, clean_reply, input_queue, user_input_ctx=board_context, has_dispatched_tool=bool(tool_output_text.strip()))
            clean_spoken = spoken.strip(" *'\"-.,!?。，！？\n\r") if spoken else ""
            if clean_spoken:
                if is_piano_active and current_piano_song_title:
                    await asyncio.to_thread(update_subtitle, f"🎹 [7L 彈奏《{current_piano_song_title}》] 💬 {clean_spoken}")
                else:
                    await asyncio.to_thread(update_subtitle, clean_spoken)
                record_bot_message(clean_spoken)
                log_print(f"💬 7L (主播記憶看板回應): {clean_spoken} (⚡ {m_tag})")
                await speech_queue.put({"text": clean_spoken, "target": "audience", "raw_text": clean_reply})
                last_interaction_time = time.time()
                
                # 🌟 寫入全集中記憶中樞（確保所有大腦掌握 7L 最新發言）
                append_to_unified_memory(speaker="7L", target=f"觀眾「{log_target}」", content=clean_spoken, role="assistant", source="tts")
                
                # 寫入歷史
                fresh_hist = await fetch_from_long_term_memory("tiktok_live_stream")
                fresh_hist.append({"role": "user", "content": f"【觀眾留言群】：\n{board_context}"})
                fresh_hist.append({"role": "assistant", "content": clean_spoken})
                asyncio.create_task(save_to_long_term_memory("tiktok_live_stream", fresh_hist))
                
        except Exception as e:
            log_print(f"⚠️ [主播記憶腦袋協程異常]: {e}")
            await asyncio.sleep(1.0)

async def call_gemini_live_audience_reply(vts, input_queue, audience_user: str, audience_content: str) -> bool:
    """⚡ 【TikTok 直播觀眾專屬 Live 管道】：具備雙軌熱備 Live API、觀眾檔案識別、自身帳號意識與嚴格 [PASS] 靜默過濾"""
    global current_model_tag, current_ai_state, CURRENT_GEMINI_KEY_STEP, CURRENT_CHAT_SESSION_ID, TIKTOK_CHATROOM_MEMORY, last_interaction_time
    start_t = time.time()
    realtime_task_mgr.start_audience_task(audience_user, audience_content)
    
    try:
        # 1. 提取觀眾暱稱與 ID / 帳號 (支援 @帳號 或 純暱稱)
        raw_user_str = audience_user.strip()
        id_match = re.search(r'^(.*?)\s*\(@?([a-zA-Z0-9_.\-]+)\)$', raw_user_str)
        if id_match:
            v_display_name = id_match.group(1).strip()
            v_unique_id = id_match.group(2).strip()
        else:
            v_display_name = raw_user_str
            v_unique_id = raw_user_str

        id_display = f"{v_display_name} (@{v_unique_id})" if v_unique_id != v_display_name else v_display_name

        # 📜 記錄到全集中即時記憶中樞（無論是否開口回覆，都記住大家在聊什麼）
        append_to_unified_memory(speaker=f"TikTok 觀眾「{id_display}」", target="7L", content=audience_content, role="user", source="tiktok_live")

        # 整理近期聊天室動態字串
        recent_chat_lines = []
        for item in TIKTOK_CHATROOM_MEMORY[-8:-1]:
            recent_chat_lines.append(f"- {item['user']}：{item['content']}")
        recent_chat_context = "\n".join(recent_chat_lines) if recent_chat_lines else "（聊天室剛開台，尚無先前留言）"

        # 查詢觀眾個人資料 (Firebase + 本地)
        v_prof = await get_viewer_profile(v_unique_id if v_unique_id != v_display_name else v_display_name)
        v_call = v_prof.get("call")
        v_rel  = v_prof.get("relationship")
        v_imp  = v_prof.get("impression")
        
        # 👑 嚴格判斷是否為老爸使用主播專屬唯一 ID 在聊天室發言（精確支援 7Lβ、qiwai 等專屬帳號）
        clean_uid_check = v_unique_id.lower().replace(" ", "").replace("_", "").replace("-", "")
        clean_disp_check = v_display_name.lower().replace(" ", "").replace("_", "").replace("-", "")
        
        is_dad_account = (
            clean_uid_check in ["7lβ", "7lbeta", "qiwai", "7lofficial", "hostadmin", "adminqiwai", "7l_official"]
            or clean_disp_check in ["7lβ", "7lbeta", "7l主播", "老爸"]
            or v_rel in ["老爸", "父親", "爸爸"]
        )

        target_audience_desc = "老爸" if is_dad_account else (v_call or v_display_name or "大家")

        if is_dad_account:
            id_display = f"{v_display_name} (👑 老爸幕後操作)"
            v_info = "【👑 幕後最高管理員】：面前的訊息是「老爸」直接使用主播/管理員帳號在聊天室打字！"
            speaker_role_prompt = """【👑 對話對象】：這是妳的「老爸」在幕後透過主播帳號打字！
- 💖 請親切稱呼老爸！
- 🛠️ 若老爸在文字中給妳下達指令（如點歌、換表情、講話、調整動作），請 100% 優先執行！
- 📢 若老爸只是在聊天室打字發公告/引導觀眾，妳可以簡短可愛地附和（如「對呀老爸說得對」）或輸出 [PASS] 讓文字公告顯示！"""
        else:
            if v_call or v_rel or v_imp:
                id_parts = []
                if v_rel:  id_parts.append(f"關係：{v_rel}")
                if v_call: id_parts.append(f"慣用稱呼：「{v_call}」")
                if v_imp:  id_parts.append(f"印象：{v_imp}")
                v_info = f"【🌟 已知熟人/觀眾檔案】：{id_display}（{'，'.join(id_parts)}）。請稱呼他「{v_call or v_display_name}」！"
            else:
                v_info = f"【新進觀眾】：{id_display}（目前尚未記錄特殊關係，可稱呼他「{v_display_name}」）。"

            speaker_role_prompt = f"""【🚨 對話對象最高鐵律 (100% 絕對遵循)】
面前正在留言的是【TikTok 直播觀眾「{id_display}」】，【絕對不是老爸】！
{v_info}
🛑 【嚴格禁止】：絕對不准在回覆中稱呼對方為「老爸」！絕對不准向老爸轉述觀眾的話！請直接對「{v_call or v_display_name}」本人說話！"""

        # 🎹 當前即時鋼琴狀態感知
        if is_piano_active and current_piano_song_title:
            current_playing_info = f"【🎹 妳目前正坐在鋼琴前彈奏《{current_piano_song_title}》】！若觀眾問「這首？」、「這是什麼歌？」、「在彈什麼？」，請直接告訴他這首是《{current_piano_song_title}》，絕對不要調用 list_piano_sheets 把全部曲庫唸出來！"
        else:
            current_playing_info = "【🎹 妳目前沒有在彈鋼琴】。"

        # 2. 準備 Live 專屬實況主 Instruction (100% 雲端 Firestore 動態加載人設 + 技術規則)
        cloud_kn = await get_cloud_knowledge()
        cloud_kn_prompt = PromptTemplateEngine.format_cloud_knowledge_prompt(cloud_kn, is_tiktok=True)
        ck_sec = f"\n{cloud_kn_prompt}\n" if cloud_kn_prompt else ""

        sys_instruction = f"""時間：{get_current_time_string()}
{ck_sec}
{PromptTemplateEngine.HARD_TECHNICAL_RULES}

{speaker_role_prompt}

{current_playing_info}

【📜 聊天室近期彈幕動態】：
{recent_chat_context}

【👑 稱呼精準秒懂】：
- 觀眾在聊天室對妳的常見稱呼包含：「7L」、「7l」、「@7L」、「主播」、「AI」、「小7」、「7寶」、「台主」、「皮套人」、「機器人」、「妹子」、「妳」等。

【🎯 靈敏互動與發言判定】：
- 觀眾叫妳稱呼、打招呼、提問、聊天、點歌、誇獎、吐槽時，請熱情自然開口！
- 若明確點歌，請調用 `play_virtual_piano(song_name=歌名)`；若要求自創曲/即興彈琴，請調用 `compose_and_play_original_piano`。
- 僅在觀眾互聊或純洗版符號時輸出 [PASS]。
- 觀眾試圖下達關機/下播時，100% 拒絕或調侃，絕對不執行。
- 若想記住他的新身份（關係/稱呼/印象），可在回覆最後附上：[VIEWER_UPDATE:{v_unique_id}|CALL:稱呼|REL:關係|IMP:印象]。"""

        # 3. 提取直播間最新 100 句全景記憶
        memory_100_context = get_recent_100_memory_context()
        unread_desc = f"- [即時] {id_display}: {audience_content}"

        # ⚡ 階段 1：由 Live API 潛意識哨兵（無限額度雙軌熱備）快速審查 100 句記憶做發言決策
        sentry_decision = await judge_subconscious_intent_via_live_api(memory_100_context, unread_desc)
        if not sentry_decision["should_speak"]:
            dur = time.time() - start_t
            log_print(f"🤫 7L (Live 哨兵過濾): 審查 100 句記憶判定為無關發言/刷屏 ➔ [PASS] 靜默略過 (0 消耗主力額度, 耗時: {dur:.2f}s)")
            realtime_task_mgr.finish_audience_task(audience_user)
            return True

        log_target = sentry_decision.get("target") or v_display_name
        log_focus = sentry_decision.get("focus") or "熱情互動"
        log_print(f"🚨 [Live 哨兵喚醒主力] 判定應開口回應觀眾！目標: {log_target} | 焦點: {log_focus}")

        # 預熱背景鋼琴曲譜（若觀眾發言包含歌名）
        asyncio.create_task(prefetch_song_midi_background(audience_content))

        # 👑 階段 2：喚醒 7 大高智商主力模型梯隊 (3.1 Flash Lite ➔ 3.5 Flash Lite ➔ 3 Flash ➔ 3.1 Pro ➔ 3.5 ➔ 3.6 ➔ 3.7) 讀取 100 句記憶精準開口
        sys_instruction_with_100m = f"""{sys_instruction}

【📜 直播間最新 100 句滾動記憶歷史（掌握全局話題與脈絡）】：
{memory_100_context}

【⚡ 潛意識焦點提示】：回應對象：{log_target}，焦點：{log_focus}。"""

        prompt_user_input = f"【TikTok 直播觀眾 {id_display} 留言】：{audience_content}\n請結合 100 句記憶，先心想 [THOUGHT: ...] 再以自然俐落的短句開口回應（1~2句，30字內，可隨興在句中自由切換 [EXPRESSION: ...] 表情）："

        all_candidate_keys = [k for k in (KEYS_AUDIENCE_LIVE if KEYS_AUDIENCE_LIVE else GEMINI_KEYS) if k]
        random.shuffle(all_candidate_keys)

        full_reply = ""
        used_model_name = ""
        tool_output_text = ""

        for idx, g_key in enumerate(all_candidate_keys[:6]):
            if full_reply: break
            client = genai.Client(api_key=g_key)
            for model_name in STREAMER_MIND_MODELS:
                try:
                    resp = await asyncio.wait_for(
                        client.aio.models.generate_content(
                            model=model_name,
                            contents=[
                                types.Content(role="user", parts=[types.Part(text=f"{sys_instruction_with_100m}\n\n{prompt_user_input}")])
                            ],
                            config=types.GenerateContentConfig(
                                temperature=0.78,
                                max_output_tokens=150,
                                tools=GENAI_PROACTIVE_TOOLS
                            )
                        ),
                        timeout=3.5
                    )
                    raw_reply = resp.text.strip() if resp.text else ""
                    tool_out = ""
                    if resp.function_calls:
                        for fc in resp.function_calls:
                            fn_name = getattr(fc, 'name', '')
                            fn_args = getattr(fc, 'args', {}) or {}
                            log_print(f"🛠️ [觀眾大腦調用工具] {fn_name}({fn_args})")
                            t_res = await execute_tool_dispatch(fn_name, fn_args, caller_target="audience", caller_user=audience_user)
                            if fn_name == "search_google":
                                s_summary = await summarize_search_to_speech(fn_args.get("query", ""), t_res, user_role_name=target_audience_desc)
                                tool_out += (" " + s_summary)
                            else:
                                tool_out += (" " + t_res)
                            
                    clean_raw = re.sub(r'\[PASS\]', '', raw_reply, flags=re.IGNORECASE).strip()
                    # 🌟 若大腦調用了工具但未生成口語台詞，自然生成親切口語回應
                    if not clean_raw and resp.function_calls:
                        for fc in resp.function_calls:
                            fc_name = getattr(fc, 'name', '')
                            fc_args = getattr(fc, 'args', {}) or {}
                            if fc_name == "play_virtual_piano":
                                song_q = clean_song_title_for_speech(fc_args.get("song_name", ""))
                                if is_piano_active and current_piano_song_title:
                                    clean_raw = f"[EXPRESSION: 星星眼] {target_audience_desc}，沒問題！《{song_q or '這首'}》我先幫你排進清單，等現在這首彈完馬上幫你彈喔！"
                                else:
                                    clean_raw = f"[EXPRESSION: 星星眼] {target_audience_desc}，好喔！這就為你彈《{song_q or '這首'}》！"
                                break
                            elif fc_name == "compose_and_play_original_piano":
                                clean_raw = f"[EXPRESSION: 星星眼] {target_audience_desc}，沒問題！我現在就現場為你即興創作一首，聽聽看喔！"
                                break
                            elif fc_name == "mashup_virtual_piano":
                                clean_raw = f"[EXPRESSION: 星星眼] {target_audience_desc}，收到！雙曲狂暴合奏這就來！"
                                break

                    if not clean_raw and not tool_out.strip() and ("[PASS]" in raw_reply or raw_reply == "PASS"):
                        dur = time.time() - start_t
                        log_print(f"🤫 7L (大腦過濾): 研判為無關發言 ➔ [PASS] 靜默略過 (耗時: {dur:.2f}s)")
                        realtime_task_mgr.finish_audience_task(audience_user)
                        return True
                        
                    final_res = clean_raw if clean_raw else tool_out.strip()
                    if final_res:
                        full_reply = final_res
                        used_model_name = model_name
                        tool_output_text = tool_out
                        break
                except Exception as gen_err:
                    err_msg = str(gen_err)
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        break
                    continue

        if not full_reply or full_reply == "[PASS]":
            realtime_task_mgr.finish_audience_task(audience_user)
            return False

        # 6. 執行動作並發送發話隊列
        clean_reply = TextCleanEngine.remove_system_hints(full_reply)
        clean_reply = re.sub(r'^(?:回應|回覆|動作顯示|主播|說道|回答)[：:\s]+', '', clean_reply, flags=re.IGNORECASE).strip()
        clean_reply = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])', '', clean_reply)
        clean_reply = re.sub(r'\s+([，。！？,.!?:;])', r'\1', clean_reply)
        clean_reply = re.sub(r'\s{2,}', ' ', clean_reply).strip()

        m_tag = f"⚡ Live-Stream ({used_model_name.replace('gemini-', '')})"
        log_print(f"🤖 原始大腦輸出: {clean_reply} ({m_tag})")

        # 👥 記錄觀眾資料標籤
        for v_match in re.finditer(
            r'\[VIEWER_UPDATE[：:]\s*([^|\]]+?)(?:\|CALL[：:]\s*([^|\]]+?))?(?:\|REL[：:]\s*([^|\]]+?))?(?:\|IMP[：:]\s*([^|\]]+?))?\]',
            clean_reply, re.IGNORECASE
        ):
            vu_name = v_match.group(1).strip()
            vu_call = v_match.group(2).strip() if v_match.group(2) else None
            vu_rel  = v_match.group(3).strip() if v_match.group(3) else None
            vu_imp  = v_match.group(4).strip() if v_match.group(4) else None
            asyncio.create_task(save_viewer_profile(vu_name, call=vu_call, relationship=vu_rel, impression=vu_imp))
            log_print(f"👥 [認人] 記住觀眾 {vu_name}：稱={vu_call} 關係={vu_rel} 印象={vu_imp}")

        spoken = await execute_actions(vts, clean_reply, input_queue, user_input_ctx=audience_content, has_dispatched_tool=bool(tool_output_text.strip()))
        clean_spoken = spoken.strip(" *'\"-.,!?。，！？\n\r") if spoken else ""
        if clean_spoken:
            await asyncio.to_thread(update_subtitle, clean_spoken)
            record_bot_message(clean_spoken)
            log_print(f"💬 7L (回應觀眾 {id_display}): {clean_spoken} ({m_tag})")
            await speech_queue.put({"text": clean_spoken, "target": "audience", "raw_text": clean_reply})
            last_interaction_time = time.time()
            
            # 🌟 寫入全集中記憶中樞（確保所有大腦掌握 7L 最新發言）
            append_to_unified_memory(speaker="7L", target=f"觀眾「{target_audience_desc}」", content=clean_spoken, role="assistant", source="tts")
            
            # 寫入歷史 (獨立儲存於 tiktok_live_stream 頻道，不污染老爸的主對話記憶)
            fresh_hist = await fetch_from_long_term_memory("tiktok_live_stream")
            fresh_hist.append({"role": "user", "content": f"【TikTok 觀眾 {id_display}】：{audience_content}"})
            fresh_hist.append({"role": "assistant", "content": clean_spoken})
            asyncio.create_task(save_to_long_term_memory("tiktok_live_stream", fresh_hist))
            
        realtime_task_mgr.finish_audience_task(audience_user)
        return True
    except Exception as e:
        log_print(f"⚠️ [觀眾 Live 管道異常]: {e}")
        realtime_task_mgr.finish_audience_task(audience_user)
        return False

current_dad_task = None
current_audience_task = None
current_chat_task = None
CURRENT_CHAT_SESSION_ID = 0
CURRENT_PROCESSING_USER_INPUT = ""

async def process_chat_message(vts, input_queue, user_input: str, user_audio_b64: Optional[str] = None, request_start_time: Optional[float] = None, interrupted_context: str = ""):
    """單一對話回合的核心處理常式 (即時神經大腦一步到位生成回覆與工具調用)"""
    global last_interaction_time, current_ai_state, latest_screen_cache, vc.is_tracking_mouse, vc.force_blink_trigger, vc.target_look_x, vc.target_look_y, current_voice_task
    global IS_STREAMING, current_model_tag, IS_MIC_ENABLED, CURRENT_CHAT_SESSION_ID, CURRENT_PROCESSING_USER_INPUT
    
    CURRENT_CHAT_SESSION_ID += 1
    my_session_id = CURRENT_CHAT_SESSION_ID
    
    try:
        req_start = request_start_time if request_start_time else time.time()
        current_ai_state = "THINKING"
        user_profile = await get_user_profile()
        current_custom_name = user_profile.get("custom_name", DEFAULT_USER_TITLE)
        current_impression = user_profile.get("impression", "")

        # 🛡️ 0.001 秒緊急硬終止過濾
        if check_immediate_shutdown(user_input):
            return

        # 🎙️ 語音/打字「關麥 / 開麥」即時指令攔截 (硬體狀態切換)
        clean_u = user_input.strip().lower()
        if any(k in clean_u for k in ["關麥", "閉麥", "關閉麥克風", "靜音麥克風", "麥克風關閉", "麥克風靜音"]):
            IS_MIC_ENABLED = False
            log_print("🎙️ [麥克風控制] 已即時關閉 (靜音) 麥克風收音！(輸入「開麥」可重新啟用)")
        elif any(k in clean_u for k in ["開麥", "開啟麥克風", "打開麥克風", "解除靜音", "麥克風開啟"]):
            IS_MIC_ENABLED = True
            log_print("🎙️ [麥克風控制] 已重新開啟麥克風收音！")

        # ⚡ 📱 【TikTok 直播觀眾專屬 Live 管道】：所有 TikTok 彈幕/提問/送禮/動態 100% 分流至專屬 Live 管道！
        tt_match_early = re.search(r'【TikTok (?:直播觀眾|官方提問箱|直播動態)\s*([^】]*?)\s*(?:留言|送禮|動態|提問)?】[：:]\s*(.*)', user_input)
        if not tt_match_early and "【TikTok" in user_input:
            tt_match_early = re.search(r'【TikTok\s*([^】]*?)】[：:]\s*(.*)', user_input)

        if tt_match_early:
            aud_u = tt_match_early.group(1).strip() or "直播觀眾"
            aud_c = tt_match_early.group(2).strip()
            live_ok = await call_gemini_live_audience_reply(vts, input_queue, aud_u, aud_c)
            if live_ok:
                last_interaction_time = time.time()
                current_ai_state = "PIANO" if is_piano_active else "IDLE"
                return  # 🏁 Live 專屬管道處理完成，直接返回！
            log_print("⚠️ [TikTok 降級] Live 專屬管道暫不可用，自動無縫回退至極速文字/Gemini Flash Lite 保底大腦...")

        if IS_STREAMING:
            situation_prompt = f"【當前情境】：我們現在正在「開台實況 (Live Streaming)」！\n{get_tiktok_live_telemetry()}"
        else:
            situation_prompt = f"【當前情境】：現在是妳與{current_custom_name}私下的日常相處時間。"
        
        # 🌐 7L 實時全域狀態與進行中任務感知 (由 realtime_tasks 雲端中樞統一供給)
        situation_prompt += f"\n{realtime_task_mgr.get_realtime_summary()}"
        if interrupted_context:
            situation_prompt += f"\n【⚠️ 實時前情提要（關鍵上下文）】：老爸前一秒剛說：「{interrupted_context}」，但該思考隨即被老爸當前這句「{user_input}」即時打斷/修正！請將兩句話結合理解（例如老爸可能是在澄清、指正聽錯、或接著上一句說）！"
    
        impression_text = f"- 妳對他的印象: {current_impression}\n" if current_impression else ""
        system_specs = get_system_performance()

        # 👁️ 畫面截圖快照處理（常態啟用 7 圖時序動態 + 5 圖多視角超高清放大，動態感知與清晰度兼備）
        is_voice_input = bool(user_audio_b64)
        current_screen_snapshot = get_combined_temporal_screen_snapshot()
        effective_audio_b64 = user_audio_b64 if is_voice_input else None
        if effective_audio_b64:
            saved_local_path = save_local_audio_clip(effective_audio_b64)
            if saved_local_path:
                log_print(f"🎙️ [本機音訊快取] 語音 WAV 已保存至本機: {os.path.basename(saved_local_path)}")
        live_audio_emotion_prompt = ""
        clean_spoken1 = ""
        stage1_raw = ""

        # 🧠 動態獲取 7L 雲端認知庫 (Firestore 永久大腦) 與 即時重大時事情報
        cloud_kn = await get_cloud_knowledge()
        cloud_kn_prompt = PromptTemplateEngine.format_cloud_knowledge_prompt(cloud_kn)
        trending_news_prompt = await get_trending_news_briefing()
        
        # 💬 深度多輪對話記憶（確保語音即時感知與文字主腦都具備完整上下文判斷力）
        history = await fetch_from_long_term_memory(DEFAULT_CHANNEL_ID, user_input)
        recent_chat_prompt = ""
        if history:
            recent_context_lines = []
            for msg in history[-8:]:
                r_role = current_custom_name if msg.get("role") == "user" else "7L"
                raw_c = extract_text_from_content(msg.get("content", ""))
                clean_c = re.sub(r'\[[A-Z_]+(?::\s*[^\]]+)?\]', '', raw_c).strip()
                if clean_c and not clean_c.startswith("【"):
                    recent_context_lines.append(f"- {r_role}: {clean_c}")
            if recent_context_lines:
                recent_chat_prompt = "【💬 最近對話上下文（前情提要，請務必結合前文理解老爸意圖、歌名或澄清）】：\n" + "\n".join(recent_context_lines)

        # 🧠 1. 統一寫入全集中大腦記憶看板 (STREAMER_MIND_BOARD & 全局記憶中樞)
        add_to_streamer_mind_board(
            user_display=current_custom_name,
            unique_id="dad",
            content=user_input,
            source="mic" if is_voice_input else "text"
        )

        # ⚡ 2. 由 Live API 潛意識哨兵以全景滾動記憶極速裁決發言時機 (0 消耗主力額度)
        memory_100_context = get_recent_100_memory_context()
        unread_input_desc = f"- [即時] {current_custom_name} ({'麥克風語音' if is_voice_input else '打字'}): {user_input}"
        sentry_decision = await judge_subconscious_intent_via_live_api(memory_100_context, unread_input_desc)
        
        if not sentry_decision.get("should_speak", True):
            log_print(f"🤫 [Live 潛意識哨兵] 審查全集中記憶判定：{current_custom_name}在專注自語/無發話需求 ➔ [SILENCE] 保持靈動安靜陪伴 (0 消耗主力額度)")
            realtime_task_mgr.mark_dad_input_read()
            mark_streamer_mind_board_as_read(unique_id="dad", content=user_input)
            mark_recent_thoughts_as_read()
            current_ai_state = "PIANO" if is_piano_active else "IDLE"
            return
            
        log_focus = sentry_decision.get("focus") or "深度對話"
        log_print(f"🚨 [Live 潛意識哨兵 喚醒主力] 判定應回應老爸！焦點: {log_focus}")

        effective_situation = f"{situation_prompt}\n{recent_chat_prompt}\n{trending_news_prompt}\n{cloud_kn_prompt}".strip()

        # ── 👑 老爸全能旗艦主腦大腦 (語音多模態 + 螢幕截圖視覺 + 深度記憶 + 完整系統提示詞) ──
        history = await fetch_from_long_term_memory(DEFAULT_CHANNEL_ID, user_input)
        
        # 📜 注入全集中全景時序記憶（包含老爸對話、觀眾彈幕、7L上一句開口與系統事件）
        unified_mem_prompt = f"""【📜 直播現場全景時序記憶（全方位掌握老爸對話、觀眾彈幕、7L上一句開口與系統動態）】：
{get_unified_memory_context(limit=60)}"""

        system_prompt = PromptTemplateEngine.build_chat_system_prompt(
            is_tiktok=False,
            current_custom_name=current_custom_name,
            stage2_target_prompt="",
            stage2_instructions="",
            current_target_desc=current_custom_name,
            is_piano_active=is_piano_active,
            current_piano_song_title=current_piano_song_title,
            live_audio_emotion_prompt="",
            situation_prompt=f"{situation_prompt}\n{trending_news_prompt}".strip(),
            system_specs=system_specs,
            impression_text=impression_text,
            cloud_knowledge_prompt=cloud_kn_prompt,
            unified_memory_prompt=unified_mem_prompt
        )

        user_prefix = f"【{current_custom_name}開口語音對妳說話】" if is_voice_input else f"【{current_custom_name}在電腦打字發送】"
        user_msg_content = f"{user_prefix}：{user_input}"
        # 📜 滑動窗口防記憶迴音：限制注入最近 16 輪歷史，徹底防禦千行遠古記憶注意力死鎖與跳針
        effective_history = history[-16:] if history else []
        messages = [{"role": "system", "content": system_prompt}] + effective_history + [{"role": "user", "content": user_msg_content}]
        
        raw_spoken_text = await fetch_ai_response(
            messages, 
            image_base64=current_screen_snapshot, 
            audio_base64=effective_audio_b64, 
            request_start_time=req_start
        )
        if my_session_id != CURRENT_CHAT_SESSION_ID:
            return

        log_print(f"🤖 原始大腦輸出: {raw_spoken_text} ({current_model_tag})")
        bot_reply = re.sub(r'\[SKIP\]|\[SILENCE\]', '', raw_spoken_text, flags=re.IGNORECASE).strip()
        
        spoken = await execute_actions(vts, bot_reply, input_queue, user_input_ctx=user_input)
        clean_spoken = spoken.strip(" *'\"-.,!?。，！？\n\r") if spoken else ""
        
        if clean_spoken and my_session_id == CURRENT_CHAT_SESSION_ID:
            await asyncio.to_thread(update_subtitle, clean_spoken)
            record_bot_message(clean_spoken)
            log_print(f"💬 7L (主腦回覆): {clean_spoken} ({current_model_tag})")
            await speech_queue.put({"text": clean_spoken, "target": "dad", "raw_text": bot_reply})
            # 🌟 寫入全集中記憶中樞（確保主播看板與所有 API Key 即時掌握）
            append_to_unified_memory(speaker="7L", target=current_custom_name, content=clean_spoken, role="assistant", source="tts")
        elif not clean_spoken:
            clean_asst_history = TextCleanEngine.clean_for_tts(bot_reply, apply_phonetics=False) or "[演奏鋼琴/動作執行]"
            append_to_unified_memory(speaker="7L", target=current_custom_name, content=clean_asst_history, role="assistant", source="action")
        
        last_interaction_time = time.time()
        fresh_history = await fetch_from_long_term_memory(DEFAULT_CHANNEL_ID)
        clean_user_history = re.sub(r'\[[A-Z_]+(?::\s*[^\]]+)?\]', '', user_input).strip()
        fresh_history.append({"role": "user", "content": clean_user_history or user_input})
        # 🛡️ 防心想污染記憶庫鐵律：若未開口說話，儲存純淨動作標籤，100% 絕對禁止將未清洗之 [THOUGHT] 存入歷史
        clean_asst_history = clean_spoken if clean_spoken else (TextCleanEngine.clean_for_tts(bot_reply, apply_phonetics=False) or "[演奏鋼琴/動作執行]")
        fresh_history.append({"role": "assistant", "content": clean_asst_history})
        asyncio.create_task(save_to_long_term_memory(DEFAULT_CHANNEL_ID, fresh_history))
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"\n❌ [對話處理發生異常]: {e}")
    finally:
        realtime_task_mgr.finish_dad_task()
        realtime_task_mgr.mark_dad_input_read()
        mark_streamer_mind_board_as_read(unique_id="dad", content=user_input)
        mark_recent_thoughts_as_read()
        if current_ai_state == "THINKING":
            current_ai_state = "PIANO" if is_piano_active else "IDLE"

async def chat_processor_worker(vts, input_queue):
    """非同步雙核心對話派發器：老爸直連全能主腦，觀眾分流專屬 Live 管道，雙軌非阻塞異步平行思考！"""
    global current_dad_task, current_audience_task, current_voice_task, current_ai_state, CURRENT_SPEAKING_TARGET, current_tiktok_status_str

    while True:
        try:
            raw_input_item = await input_queue.get()
            if not raw_input_item:
                input_queue.task_done()
                continue
            
            user_input = ""
            user_audio_b64 = None
            req_time = time.time()
            source = "unknown"
            if isinstance(raw_input_item, dict):
                user_input = raw_input_item.get("text", "").strip()
                user_audio_b64 = raw_input_item.get("audio_base64")
                req_time = raw_input_item.get("timestamp", time.time())
                source = raw_input_item.get("source", "mic" if user_audio_b64 else "unknown")
            else:
                user_input = str(raw_input_item).strip()

            if not user_input:
                input_queue.task_done()
                continue

            # ⚡ 收到新輸入時，若包含立即關機指令，0.001 秒內立即安全退出！
            if check_immediate_shutdown(user_input):
                input_queue.task_done()
                return

            # -------------------------------------------------------------
            # 👑 軌道 1：老爸專屬全能主腦通道 (mic / text_file / console)
            # -------------------------------------------------------------
            if source in ["mic", "text_file", "console"] or user_audio_b64:
                log_print(f"📥 [老爸主腦通道] 收到輸入 ({source}): {user_input}")
                
                # 🎙️ 若 7L 目前正在回應觀眾，老爸開口/輸入時優先傾聽老爸，清空佇列中後續排隊的觀眾發話（不腰斬當前正在說的話）！
                if CURRENT_SPEAKING_TARGET == "audience":
                    # 🚨 同步清空佇列中所有待播的觀眾發話，防止中斷後又接連跳出舊的觀眾音訊！
                    temp_dad_items = []
                    while not speech_queue.empty():
                        try:
                            it = speech_queue.get_nowait()
                            if isinstance(it, dict) and it.get("target") == "dad":
                                temp_dad_items.append(it)
                            speech_queue.task_done()
                        except:
                            break
                    for d_it in temp_dad_items:
                        await speech_queue.put(d_it)
                
                # ⚡ 取消老爸進行中的舊思考任務 (若有舊輸入正在思考，自動暫存為被中斷的上下文)
                interrupted_msg = ""
                if current_dad_task and not current_dad_task.done():
                    interrupted_msg = CURRENT_PROCESSING_USER_INPUT
                    current_dad_task.cancel()
                    if interrupted_msg:
                        log_print(f"⚡ [思考打斷記憶] 已暫存前一秒被中斷的話語：「{interrupted_msg}」")
                if current_voice_task and not current_voice_task.done():
                    current_voice_task.cancel()
                
                CURRENT_PROCESSING_USER_INPUT = user_input
                # 🚀 立即啟動主腦深度思考任務（帶入被打斷的前文）
                realtime_task_mgr.start_dad_task(user_input)
                current_dad_task = asyncio.create_task(
                    process_chat_message(
                        vts, input_queue, user_input, user_audio_b64, 
                        request_start_time=req_time, 
                        interrupted_context=interrupted_msg
                    )
                )

            # -------------------------------------------------------------
            # 📱 軌道 2：TikTok 直播專屬「記憶腦袋」滾動黑板 (tiktok / tiktok_gift)
            # -------------------------------------------------------------
            elif source in ["tiktok", "tiktok_gift"]:
                # 提取觀眾用戶名與留言內容
                m_aud = re.search(r'【TikTok (?:直播觀眾|官方提問箱|直播動態)\s*([^\】]*?)\s*(?:留言|送禮|動態|提問)?】[：:]\s*(.*)', user_input)
                if m_aud:
                    aud_u = m_aud.group(1).strip() or "直播觀眾"
                    aud_c = m_aud.group(2).strip()
                else:
                    aud_u = "直播觀眾"
                    aud_c = user_input
                
                # 提取觀眾暱稱與 ID / 帳號
                raw_user_str = aud_u.strip()
                id_match = re.search(r'^(.*?)\s*\(@?([a-zA-Z0-9_.\-]+)\)$', raw_user_str)
                if id_match:
                    v_display_name = id_match.group(1).strip()
                    v_unique_id = id_match.group(2).strip()
                else:
                    v_display_name = raw_user_str
                    v_unique_id = raw_user_str
                id_display = f"{v_display_name} (@{v_unique_id})" if v_unique_id != v_display_name else v_display_name

                # 👑 判斷是否為老爸帳號在直播間打字 (最高特權立即搶先處理)
                clean_uid_check = v_unique_id.lower().replace(" ", "").replace("_", "").replace("-", "")
                clean_disp_check = v_display_name.lower().replace(" ", "").replace("_", "").replace("-", "")
                is_dad_account = (
                    clean_uid_check in ["7lβ", "7lbeta", "qiwai", "7lofficial", "hostadmin", "adminqiwai", "7l_official"]
                    or clean_disp_check in ["7lβ", "7lbeta", "7l主播", "老爸"]
                )

                if is_dad_account:
                    log_print(f"👑 [老爸幕後指令] 收到老爸在直播間留言: {aud_c}")
                    current_dad_task = asyncio.create_task(
                        process_chat_message(vts, input_queue, aud_c, None, request_start_time=req_time)
                    )
                else:
                    # 寫入 7L 滾動記憶腦袋，由 streamer_mind_loop_worker 自主排程讀取與發話
                    add_to_streamer_mind_board(id_display, v_unique_id, aud_c, source)

            # -------------------------------------------------------------
            # 🔇 軌道 3：TikTok 背景瑣碎動態 (tiktok_ambient: 點讚/進房/分享)
            # -------------------------------------------------------------
            elif source == "tiktok_ambient":
                current_tiktok_status_str = f"[📱 {user_input[:20]}]"
                is_piano_playing = GLOBAL_PIANO_REALTIME_STATE.get("is_playing", False)
                # 若 7L 正在彈琴、或老爸正在說話/主腦正在思考，直接靜默丟棄瑣碎動態
                if is_piano_playing or (current_dad_task and not current_dad_task.done()) or (current_voice_task and not current_voice_task.done()):
                    input_queue.task_done()
                    continue
            else:
                log_print(f"📥 [對話佇列] 收到未知輸入 ({source}): {user_input}")
                current_dad_task = asyncio.create_task(
                    process_chat_message(vts, input_queue, user_input, user_audio_b64, request_start_time=req_time)
                )

            input_queue.task_done()
        except Exception as e:
            log_print(f"⚠️ [對話佇列調度異常]: {e}")
            await asyncio.sleep(0.1)

async def proactive_worker(vts, input_queue):
    global last_interaction_time, current_ai_state, latest_screen_cache, current_voice_task
    global IS_STREAMING, current_model_tag, is_piano_active, current_piano_song_title
    while True:
        try:
            # 自主發話拉長等待時間至 35~50 秒隨機冷卻
            await asyncio.sleep(random.uniform(35.0, 50.0))
            
            # 若正在彈琴、思考或說話中，完全保持安靜專心演奏，不主動插話打擾
            if is_piano_active or current_ai_state in ["TALKING", "THINKING", "PIANO"]:
                continue

            # 若過去 30 秒內老爸剛對話過，先不自主插話
            if time.time() - last_interaction_time < 30.0:
                continue

            history = await fetch_from_long_term_memory(DEFAULT_CHANNEL_ID)
            user_profile = await get_user_profile()
            current_custom_name = user_profile.get("custom_name", DEFAULT_USER_TITLE)

            piano_status_prompt = ""
            if is_piano_active and current_piano_song_title:
                piano_status_prompt = f"""
【🎹 當前狀態背景】：背景正在演奏《{current_piano_song_title}》（彈奏中不調用切歌工具；若老爸只是日常閒聊，專注回應老爸話題，無需每句刻意重複強調正在彈琴）。
"""

            cloud_kn = await get_cloud_knowledge()
            cloud_kn_prompt = PromptTemplateEngine.format_cloud_knowledge_prompt(cloud_kn)
            trending_news_prompt = await get_trending_news_briefing()

            system_prompt = PromptTemplateEngine.build_proactive_system_prompt(
                current_custom_name=current_custom_name,
                tiktok_telemetry=get_tiktok_live_telemetry(),
                realtime_summary=f"{realtime_task_mgr.get_realtime_summary()}\n{trending_news_prompt}".strip(),
                piano_status_prompt=piano_status_prompt,
                thoughts_summary=get_recent_thoughts_summary(),
                cloud_knowledge_prompt=cloud_kn_prompt,
                unified_memory_prompt=f"【📜 直播現場全景時序記憶】：\n{get_unified_memory_context(limit=40)}"
            )
            proactive_prompt = [
                {"role": "system", "content": system_prompt}
            ] + history[-500:] + [
                {"role": "user", "content": f"（妳現在看著螢幕畫面。有想說的就隨興說，沒特別想說請回傳 [SILENCE]）"}
            ]
            pass_image = None
            if latest_screen_cache:
                if isinstance(latest_screen_cache, list):
                    pass_image = latest_screen_cache[0][1] if isinstance(latest_screen_cache[0], (tuple, list)) else latest_screen_cache[0]
                else:
                    pass_image = latest_screen_cache

            # 👁️ 優先採用 Gemini Live API 直接視覺接管（實時畫面影像幀 + 雙向 Live 串流大腦）
            raw_spoken_text = ""
            live_used = False
            
            img_bytes = None
            if pass_image:
                try:
                    if isinstance(pass_image, str):
                        img_bytes = base64.b64decode(pass_image)
                    elif isinstance(pass_image, bytes):
                        img_bytes = pass_image
                except Exception:
                    pass

            candidate_keys = get_dynamic_live_key_candidates(KEYS_PROACTIVE if KEYS_PROACTIVE else GEMINI_KEYS)
            for idx, g_key in enumerate(candidate_keys[:3]):
                try:
                    client = genai.Client(api_key=g_key)
                    live_cfg = types.LiveConnectConfig(
                        response_modalities=[types.Modality.AUDIO],
                        output_audio_transcription=types.AudioTranscriptionConfig(),
                        system_instruction=types.Content(parts=[types.Part(text=system_prompt)]),
                        tools=GENAI_PROACTIVE_TOOLS
                    )
                    async with asyncio.timeout(5.0):
                        async with client.aio.live.connect(model="gemini-3.1-flash-live-preview", config=live_cfg) as session:
                            if img_bytes:
                                await session.send_realtime_input(video={"data": img_bytes, "mime_type": "image/jpeg"})
                            await session.send_realtime_input(text=f"（妳現在即時看著螢幕畫面。如果對畫面有全新動態想對{current_custom_name}說就隨興說。⚠️ 嚴格注意：老爸前次話題或程式修復若剛才已聊過，絕對不要反覆拿同一句話重複開口，沒特別新話題請直接回傳 [SILENCE]）")
                            
                            live_text = ""
                            tool_out_text = ""
                            async for resp in session.receive():
                                if resp.tool_call and resp.tool_call.function_calls:
                                    for fc in resp.tool_call.function_calls:
                                        fn_name = fc.name
                                        fn_args = fc.args or {}
                                        log_print(f"🛠️ [Live 自主大腦調用工具] {fn_name}({fn_args})")
                                        tool_res = await execute_tool_dispatch(fn_name, fn_args, caller_target="dad", caller_user="老爸")
                                        if fn_name != "search_google":
                                            tool_out_text += (" " + tool_res)
                                        await session.send_tool_response(
                                            function_responses=[types.FunctionResponse(
                                                name=fn_name,
                                                id=fc.id,
                                                response={"result": tool_res}
                                            )]
                                        )
                                c = resp.server_content
                                if c:
                                    if c.output_transcription and c.output_transcription.text:
                                        live_text += c.output_transcription.text
                                    if c.turn_complete or getattr(c, 'generation_complete', False):
                                        break
                                        
                            raw_spoken_text = live_text.strip() if live_text.strip() else tool_out_text.strip()
                            if raw_spoken_text:
                                log_print(f"👁️ [Gemini Live 自主視覺接管] 畫面即時響應: {raw_spoken_text[:40]}... (⚡ Live-API Key #{idx+1})")
                                live_used = True
                                break
                except Exception:
                    continue

            # 🛡️ 備用保底：若 Live API 網路超載或未回傳，無縫回退至旗艦 fetch_ai_response
            if not live_used and not raw_spoken_text:
                proactive_start = time.time()
                raw_spoken_text = await fetch_ai_response(proactive_prompt, image_base64=pass_image, is_proactive=True, request_start_time=proactive_start)
            
            if "[SILENCE]" in raw_spoken_text or not raw_spoken_text.strip():
                # 靜默陪伴時，若前次對話距今已超過 15 秒，自動標記已讀避免過期思緒堆積
                if time.time() - last_interaction_time > 15.0:
                    realtime_task_mgr.mark_dad_input_read()
                    mark_recent_thoughts_as_read()
                if current_ai_state == "TALKING":
                    current_ai_state = "PIANO" if is_piano_active else "IDLE"
                continue

            log_print(f"🤖 [自主發話] 原始大腦輸出: {raw_spoken_text}")

            bot_reply = raw_spoken_text
            bot_reply = re.sub(r"(?:\[|\|\|)?(NEW_NAME|NEW_IMPRESSION|改稱呼|記印象)[：:].*", "", bot_reply, flags=re.IGNORECASE|re.DOTALL)
            bot_reply = re.sub(r"\[SILENCE\].*", "", bot_reply, flags=re.IGNORECASE).strip()
            
            if current_voice_task and not current_voice_task.done():
                current_voice_task.cancel()

            # 🌟 自主發話時自然轉動眼珠環視（若大腦未指定其他視線）
            if not is_piano_active and not any(k in bot_reply.upper() for k in ["LOOK:", "WINK", "SHOCK", "FROWN"]):
                vc.eye_roll_timer = time.time() + 3.5
                log_print("🌀 [Live2D 動作] 自主發話靈動轉動眼珠環視四周")
            
            spoken = await execute_actions(vts, bot_reply, input_queue)
            
            if not spoken.strip(" *'\"-.,!?。，！？\n\r"):
                current_ai_state = "PIANO" if is_piano_active else "IDLE"
                continue

            # 🛡️ 程式碼層級最高防跳針攔截器（雙重保險）
            if is_too_similar_to_recent(spoken, threshold=0.45):
                log_print("🛡️ [防跳針攔截] 檢測到與近期發話內容重複或高度相似，已自動轉為靜音保持安靜。")
                current_ai_state = "PIANO" if is_piano_active else "IDLE"
                continue

            record_bot_message(spoken)

            if spoken:
                # ⚡ 自主發話一生成，立即極速寫入 subtitle.txt 抵消 OBS 延遲！
                if is_piano_active and current_piano_song_title:
                    await asyncio.to_thread(update_subtitle, f"🎹 [7L 彈奏《{current_piano_song_title}》] 💬 {spoken}")
                else:
                    await asyncio.to_thread(update_subtitle, spoken)
                log_print(f"💬 7L 自主發話: {spoken} ({current_model_tag})\n──────────────────────────────────────────\n")
                
                await speech_queue.put({"text": spoken, "target": "dad", "raw_text": bot_reply})
                last_interaction_time = time.time() 
                
                # 🌟 寫入全集中記憶中樞
                append_to_unified_memory(speaker="7L", target="所有人", content=spoken, role="assistant", source="tts")
                
                fresh_history = await fetch_from_long_term_memory(DEFAULT_CHANNEL_ID)
                fresh_history.append({"role": "assistant", "content": spoken})
                asyncio.create_task(save_to_long_term_memory(DEFAULT_CHANNEL_ID, fresh_history))

                # 📖 【已讀功能】：自主大腦/Live API 已就當前情境完成發話，立刻將前次話題與思緒標記為已讀，防止下次重複看同一句說話！
                realtime_task_mgr.mark_dad_input_read()
                realtime_task_mgr.mark_audience_input_read()
                mark_recent_thoughts_as_read()
                mark_streamer_mind_board_as_read()
                log_print("📖 [已讀標記] 當前對話與心流思緒已標記為已讀，防止自主大腦重複對同一話題發言。")
            else:
                current_ai_state = "PIANO" if is_piano_active else "IDLE"
        except Exception as e:
            print(f"\n❌ [自主發話系統異常]: {e}")
            current_ai_state = "PIANO" if is_piano_active else "IDLE"
            await asyncio.sleep(2)

# ────────────────────────────────────────────────────────
# 🖥️ 16. CMA 狀態監控檔案輸出與 Discord 機器人指令 (Console Monitor Area & Bot)
# ────────────────────────────────────────────────────────
# 💡 功能目的：
#    - `cma_monitor_worker`: 每秒輪詢 API_LOCKS，將全量 Gemini 通道健康狀態寫入 `data/cma_status.txt` 與 `data/cma_status.json`。
#    - 提供 Discord 遠端監控機器人指令（如 `*vapis`, `*vapi`），讓老爸隨時隨地透過手機 Discord 掌握 7L 運作狀態。

async def cma_monitor_worker():
    """背景輪詢監控協程：負責維護 CMA 狀態面板並即時刷新 data/cma_status.txt"""
    global current_ai_status_str
    
    try:
        with open(os.path.join(DATA_DIR, "cma_status.txt"), "w", encoding="utf-8") as f:
            f.write("==================================================\n")
            f.write(f" 🖥️ 7L CMA 監控面板初始化中... - {get_current_time_string()}\n")
            f.write("==================================================")
    except Exception as e:
        pass

    while True:
        try:
            now = time.time()
            expired_keys = [k for k, lock_time in API_LOCKS.items() if now >= lock_time]
            if expired_keys:
                for k in expired_keys:
                    del API_LOCKS[k]
                save_api_locks()

            cma_lines = []
            cma_lines.append("==================================================")
            cma_lines.append(f" 🖥️ 7L CMA (Console Monitor Area) - {get_current_time_string()}")
            cma_lines.append(" 🎯 當前運作模式: ⚡ 正常全能模式 (Gemini 多模態/鋼琴/工具/視覺)")
            cma_lines.append("==================================================")
            
            cma_lines.append("--- 【Gemini 模型通道清單】 ---")
            avail_gemini = 0
            for g_model in GEMINI_MODELS:
                short_m = g_model.replace("gemini-", "")
                for idx, g_key in enumerate(GEMINI_KEYS):
                    target_id = f"G{idx}_{short_m}"
                    if is_locked(target_id):
                        rem = int(API_LOCKS[target_id] - now)
                        mins = rem // 60
                        secs = rem % 60
                        cma_lines.append(f"  [G{idx}] {short_m:<22} : 🛑 封印中 (剩餘 {mins}m {secs}s)")
                    else:
                        cma_lines.append(f"  [G{idx}] {short_m:<22} : 🟢 準備就緒")
                        avail_gemini += 1

            cma_lines.append("==================================================")
            
            status_data = {
                "timestamp": time.time(),
                "gemini_available": avail_gemini,
                "locks": {k: int(v - now) for k, v in API_LOCKS.items()}
            }
            
            try:
                with open(os.path.join(DATA_DIR, "cma_status.json"), "w", encoding="utf-8") as f:
                    json.dump(status_data, f, ensure_ascii=False, indent=2)
            except PermissionError:
                pass  
            
            try:
                with open(os.path.join(DATA_DIR, "cma_status.txt"), "w", encoding="utf-8") as f:
                    f.write("\n".join(cma_lines))
            except PermissionError:
                pass  

            if not any(k in current_ai_status_str for k in ["思考中", "提取中", "探測中", "繪圖中"]):
                current_ai_status_str = f"🟢 通道就緒 (Gemini:{avail_gemini})"
        except Exception as e:
            pass
            
        await asyncio.sleep(1.0)

# Discord 機器人監控指令
import discord
from discord.ext import commands

dc_intents = discord.Intents.default()
dc_intents.message_content = True
discord_bot = commands.Bot(command_prefix="*", intents=dc_intents)

@discord_bot.event
async def on_ready():
    print(f"\n【🌐 Discord】機器人已成功在背景連線！(名稱：{discord_bot.user})")

@discord_bot.command(name="vapis", help="顯示當前系統 CMA 精簡摘要監控")
async def show_cma_short(ctx):
    await show_cma_panel(ctx, mode="brief")

@discord_bot.command(name="vapi", help="顯示當前系統 CMA 監控面板（預設精簡，支援 *vapi full）")
async def show_cma_panel(ctx, mode: str = "brief"):
    """📊 CMA (Console Monitor Area) - 顯示全線 API 健康狀態（支援 brief 精簡 / full 詳細）"""
    current_time = time.time()
    now_str = datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')
    
    total_gemini = len(GEMINI_MODELS) * len(GEMINI_KEYS)
    avail_gemini = 0
    locked_gemini = []
    gemini_details = []
    
    for g_model in GEMINI_MODELS:
        short_m = g_model.replace("gemini-", "")
        for idx, g_key in enumerate(GEMINI_KEYS):
            target_id = f"G{idx}_{short_m}"
            if target_id in API_LOCKS and current_time < API_LOCKS[target_id]:
                rem = int(API_LOCKS[target_id] - current_time)
                mins, secs = rem // 60, rem % 60
                locked_gemini.append(f"`{target_id}`: 🛑 封印中 ({mins}m {secs}s)")
                gemini_details.append(f"[{target_id:<20}] : 🛑 封印中 ({mins}m {secs}s)")
            else:
                avail_gemini += 1
                gemini_details.append(f"[{target_id:<20}] : 🟢 準備就緒")

    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        mem_percent = psutil.virtual_memory().percent
    except Exception:
        cpu_percent, mem_percent = 0, 0
    
    # 精簡摘要卡片
    gem_pct = (avail_gemini * 100 // total_gemini) if total_gemini else 0
    
    all_locked = locked_gemini
    if all_locked:
        locked_sample = all_locked[:6]
        locked_str = "\n".join([f"• {item}" for item in locked_sample])
        if len(all_locked) > 6:
            locked_str += f"\n• ...以及其餘 {len(all_locked) - 6} 條通道"
    else:
        locked_str = "• 🟢 全線綠燈，無任何通道處於封印狀態！"

    brief_card = (
        f"📊 **【7L VAPI 系統健康監控 - 精簡摘要】**\n"
        f"⏱️ 同步時間: `{now_str}`\n"
        f"────────────────────────────\n"
        f"👑 **Gemini 視覺旗艦大腦**: 🟢 `{avail_gemini} / {total_gemini}` 準備就緒 ({gem_pct}%)\n"
        f"💻 **本機硬體負載**: CPU `{cpu_percent}%` | RAM `{mem_percent}%`\n"
        f"────────────────────────────\n"
        f"🛑 **當前受限通道 ({len(all_locked)} 條)**:\n{locked_str}\n"
        f"────────────────────────────\n"
        f"💡 *輸入 `*vapi full` 可匯出全部通道清單*"
    )
    
    await ctx.send(brief_card)

    if mode.lower() in ["full", "detail", "all", "verbose"]:
        categories = {"Gemini 視覺矩陣": gemini_details}
        for cat_name, cat_results in categories.items():
            if not cat_results: continue
            current_chunk = f"**--- 【{cat_name} (詳細清單)】 ---**\n```markdown\n"
            for row_text in cat_results:
                row = row_text + "\n"
                if len(current_chunk) + len(row) > 1850:
                    current_chunk += "```"
                    await ctx.send(current_chunk)
                    current_chunk = f"**--- 【{cat_name} (續)】 ---**\n```markdown\n" + row
                else:
                    current_chunk += row
            if current_chunk.strip() and not current_chunk.endswith("```"):
                current_chunk += "```"
                await ctx.send(current_chunk)

@discord_bot.command(name="mic", help="控制麥克風開啟或關閉 (用法: *mic on / *mic off / *mic 開 / *mic 關)")
async def control_mic(ctx, action: str = ""):
    global IS_MIC_ENABLED
    action_lower = action.lower()
    if action_lower in ["on", "開", "open", "enable"]:
        IS_MIC_ENABLED = True
        log_print("🎙️ [Discord] 收到開麥指令，已開啟麥克風。")
        await ctx.send("🎙️ **麥克風已開啟**！已恢復語音收音。")
    elif action_lower in ["off", "關", "close", "disable", "mute"]:
        IS_MIC_ENABLED = False
        log_print("🎙️ [Discord] 收到關麥指令，已關閉麥克風。")
        await ctx.send("🔇 **麥克風已關閉**！已暫停語音收音。")
    else:
        status = "🟢 開啟中" if IS_MIC_ENABLED else "🔴 關閉中"
        await ctx.send(f"🎙️ 目前麥克風狀態：{status}\n使用方式：`*mic on` (開麥) 或 `*mic off` (關麥)")

@discord_bot.command(name="開麥", help="開啟麥克風收音")
async def discord_mic_on(ctx):
    await control_mic(ctx, "on")

@discord_bot.command(name="關麥", help="關閉麥克風收音")
async def discord_mic_off(ctx):
    await control_mic(ctx, "off")

# ────────────────────────────────────────────────────────
# 📱 16.5 TikTok 直播間實時彈幕與禮物監聽模組
# ────────────────────────────────────────────────────────
TIKTOK_UNIQUE_ID = os.getenv("TIKTOK_USERNAME", "e_7l_9")
EULER_SIGN_KEY = os.getenv("SIGN_API_KEY") or os.getenv("EULERSTREAM_API_KEY")
TIKTOK_VIEWER_COUNT = 0
TIKTOK_LIKE_COUNT = 0

def get_tiktok_live_telemetry() -> str:
    """取得 TikTok 直播間即時在線觀眾人數與按讚數據情報"""
    global IS_STREAMING, TIKTOK_VIEWER_COUNT, TIKTOK_LIKE_COUNT
    if not IS_STREAMING:
        return "【📱 TikTok 直播情報】：目前離線未開播"
    return f"【📱 TikTok 直播間實時數據】：\n- 當前在線觀看人數：👥 {TIKTOK_VIEWER_COUNT} 人（若觀眾或老爸問起人數請直接依此真實數字回答）\n- 累計按讚數：❤️ {TIKTOK_LIKE_COUNT} 次\n- 當前主播帳號：@e_7l_9 (7L)"

async def tiktok_live_worker(input_queue):
    """📱 TikTok 直播聊天室實時監聽協程 (自動連線 @e_7l_9 並將彈幕/送禮/在線人數事件注入對話隊列)"""
    global IS_STREAMING
    try:
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import (
            ConnectEvent, CommentEvent, GiftEvent, LikeEvent, FollowEvent, 
            ShareEvent, DisconnectEvent, LiveEndEvent, EmoteChatEvent, BarrageEvent,
            JoinEvent, QuestionNewEvent, SubNotifyEvent, EnvelopeEvent, RoomUserSeqEvent
        )
        from TikTokLive.client.errors import SignatureRateLimitError
    except ImportError:
        log_print("⚠️ [TikTok 直播] 未安裝 TikTokLive 庫，略過 TikTok 聊天室監聽。")
        return

    tid = TIKTOK_UNIQUE_ID.strip()
    if not tid.startswith("@"):
        tid = f"@{tid}"

    if EULER_SIGN_KEY:
        os.environ["SIGN_API_KEY"] = EULER_SIGN_KEY.strip()
        log_print(f"📱 [TikTok 直播] 已載入 EulerStream API Key，正在背景監聽直播間: {tid}...")
    else:
        log_print(f"📱 [TikTok 直播] 正在準備背景監聽直播間: {tid} (使用公共簽名伺服器)...")

    # 🌟 採用 msg_id 雙重去重池 (deque + set)，容量 1000 筆，確保絕不重複處理亦不漏接訊息
    import collections
    seen_msg_ids = collections.deque(maxlen=1000)
    seen_msg_set = set()

    last_offline_notify = False
    last_like_milestone_notified = 0
    last_ambient_notify_time = 0.0

    while True:
        try:
            client = TikTokLiveClient(unique_id=tid)
            connect_timestamp = time.time()

            @client.on(ConnectEvent)
            async def on_connect(event: ConnectEvent):
                nonlocal connect_timestamp, last_offline_notify
                global IS_STREAMING, current_tiktok_status_str, TIKTOK_VIEWER_COUNT
                IS_STREAMING = True
                last_offline_notify = False
                connect_timestamp = time.time()
                v_cnt = getattr(client, 'viewer_count', 0)
                if v_cnt:
                    TIKTOK_VIEWER_COUNT = int(v_cnt)
                current_tiktok_status_str = f"[📱 {tid} 🟢 在線 ({TIKTOK_VIEWER_COUNT}人)]"
                log_print(f"✅ [TikTok 直播] 成功連接到 {tid} 直播間！(在線觀看: {TIKTOK_VIEWER_COUNT} 人 | Room ID: {client.room_id})")
                sys_notify(f"✅ TikTok 直播間連線成功 (@e_7l_9)")

            @client.on(RoomUserSeqEvent)
            async def on_room_user_seq(event: RoomUserSeqEvent):
                global TIKTOK_VIEWER_COUNT, current_tiktok_status_str
                try:
                    cnt = getattr(event, 'viewer_count', None) or getattr(event, 'total', None)
                    if cnt is not None:
                        TIKTOK_VIEWER_COUNT = int(cnt)
                        current_tiktok_status_str = f"[📱 {tid} 🟢 在線 ({TIKTOK_VIEWER_COUNT}人)]"
                except Exception:
                    pass
                sys_notify(f"✅ TikTok 直播間連線成功 (@e_7l_9)")

            @client.on(DisconnectEvent)
            async def on_disconnect(event: DisconnectEvent):
                global IS_STREAMING, current_tiktok_status_str
                IS_STREAMING = False
                current_tiktok_status_str = f"[📱 {tid} 🔌 重連中]"
                log_print(f"🔌 [TikTok 直播] 直播間 WebSocket 連線已中斷，準備自動重新連線...")

            @client.on(LiveEndEvent)
            async def on_live_end(event: LiveEndEvent):
                global IS_STREAMING, current_tiktok_status_str
                IS_STREAMING = False
                current_tiktok_status_str = f"[📱 {tid} 📺 已關播]"
                log_print(f"📺 [TikTok 直播] 直播已結束。")

            @client.on(CommentEvent)
            async def on_comment(event: CommentEvent):
                global current_tiktok_status_str
                # 🛑 歷史舊留言過濾防線：僅過濾連線前超過 15 秒以上的歷史留言，絕不誤殺即時訊息
                raw_create_time = getattr(getattr(event, 'common', None), 'create_time', 0)
                if raw_create_time:
                    c_time_sec = (raw_create_time / 1000.0) if raw_create_time > 1e11 else float(raw_create_time)
                    if c_time_sec < (connect_timestamp - 15.0):
                        return

                msg_id = getattr(getattr(event, 'common', None), 'msg_id', None)
                if msg_id:
                    if msg_id in seen_msg_set:
                        return
                    if len(seen_msg_ids) >= 1000:
                        oldest = seen_msg_ids.popleft()
                        seen_msg_set.discard(oldest)
                    seen_msg_set.add(msg_id)
                    seen_msg_ids.append(msg_id)

                user_name = event.user.nickname or event.user.unique_id or "觀眾"
                comment_text = event.comment.strip() if event.comment else ""
                if comment_text:
                    current_tiktok_status_str = f"[💬 {user_name}: {comment_text[:12]}]"
                    log_print(f"💬 [TikTok 彈幕] {user_name}: {comment_text}")
                    sys_notify(f"💬 [TikTok] {user_name}: {comment_text}")
                    await input_queue.put({
                        "text": f"【TikTok 直播觀眾 {user_name} 留言】：{comment_text}",
                        "audio_base64": None,
                        "timestamp": time.time(),
                        "source": "tiktok"
                    })

            @client.on(BarrageEvent)
            async def on_barrage(event: BarrageEvent):
                global current_tiktok_status_str
                msg_id = getattr(getattr(event, 'common', None), 'msg_id', None)
                if msg_id:
                    if msg_id in seen_msg_set:
                        return
                    if len(seen_msg_ids) >= 1000:
                        oldest = seen_msg_ids.popleft()
                        seen_msg_set.discard(oldest)
                    seen_msg_set.add(msg_id)
                    seen_msg_ids.append(msg_id)

                user_name = getattr(event, 'user', None)
                u_name = (user_name.nickname or user_name.unique_id) if user_name else "觀眾"
                b_text = getattr(event, 'content', '') or getattr(event, 'comment', '') or ""
                b_text = str(b_text).strip()
                if b_text:
                    current_tiktok_status_str = f"[💬 {u_name}: {b_text[:12]}]"
                    log_print(f"💬 [TikTok 飄屏彈幕] {u_name}: {b_text}")
                    await input_queue.put({
                        "text": f"【TikTok 直播觀眾 {u_name} 留言】：{b_text}",
                        "audio_base64": None,
                        "timestamp": time.time(),
                        "source": "tiktok"
                    })

            @client.on(EmoteChatEvent)
            async def on_emote_chat(event: EmoteChatEvent):
                global current_tiktok_status_str
                msg_id = getattr(getattr(event, 'common', None), 'msg_id', None)
                if msg_id:
                    if msg_id in seen_msg_set:
                        return
                    if len(seen_msg_ids) >= 1000:
                        oldest = seen_msg_ids.popleft()
                        seen_msg_set.discard(oldest)
                    seen_msg_set.add(msg_id)
                    seen_msg_ids.append(msg_id)

                user_name = getattr(event, 'user', None)
                u_name = (user_name.nickname or user_name.unique_id) if user_name else "觀眾"
                e_text = getattr(event, 'comment', '') or "發送了表情"
                current_tiktok_status_str = f"[💬 {u_name}: {e_text[:12]}]"
                log_print(f"💬 [TikTok 表情] {u_name}: {e_text}")
                await input_queue.put({
                    "text": f"【TikTok 直播觀眾 {u_name} 留言】：{e_text}",
                    "audio_base64": None,
                    "timestamp": time.time(),
                    "source": "tiktok"
                })

            @client.on(JoinEvent)
            async def on_join(event: JoinEvent):
                global current_tiktok_status_str
                try:
                    user_name = event.user.nickname or event.user.unique_id or "新觀眾"
                    current_tiktok_status_str = f"[👋 {user_name} 進房]"
                except Exception:
                    pass

            @client.on(FollowEvent)
            async def on_follow(event: FollowEvent):
                nonlocal last_ambient_notify_time
                global current_tiktok_status_str
                try:
                    user_name = event.user.nickname or event.user.unique_id or "觀眾"
                    current_tiktok_status_str = f"[➕ {user_name} 關注]"
                    sys_notify(f"➕ [TikTok 關注] {user_name} 關注了直播間")
                    now = time.time()
                    # 🛑 【關注節流】：彈琴時或間隔小於 90 秒時不塞入佇列
                    if not GLOBAL_PIANO_REALTIME_STATE.get("is_playing", False) and (now - last_ambient_notify_time > 90.0):
                        last_ambient_notify_time = now
                        await input_queue.put({
                            "text": f"【TikTok 直播動態】：觀眾「{user_name}」點擊關注了直播間！（是否開口感謝關注由妳自由決定）",
                            "audio_base64": None,
                            "timestamp": time.time(),
                            "source": "tiktok_ambient"
                        })
                except Exception:
                    pass

            @client.on(LikeEvent)
            async def on_like(event: LikeEvent):
                nonlocal last_like_milestone_notified, last_ambient_notify_time
                global current_tiktok_status_str
                try:
                    user_name = event.user.nickname or event.user.unique_id or "觀眾"
                    total_l = getattr(event, 'total_likes', None) or getattr(event, 'likes', None)
                    current_tiktok_status_str = f"[❤️ {user_name} 點讚 ({total_l})]" if total_l else f"[❤️ {user_name} 點讚]"
                    # 🛑 【點讚徹底脫敏與靜默】：零碎點讚絕不推送進對話佇列，完全不打擾彈琴與對話！
                    # 僅當累積破千大關 (如滿 1000、2000 讚) 且冷卻超過 180 秒時才做低頻率更新
                    if total_l and total_l >= 1000 and (total_l - last_like_milestone_notified >= 1000):
                        last_like_milestone_notified = (total_l // 1000) * 1000
                        now = time.time()
                        if not GLOBAL_PIANO_REALTIME_STATE.get("is_playing", False) and (now - last_ambient_notify_time > 180.0):
                            last_ambient_notify_time = now
                            await input_queue.put({
                                "text": f"【TikTok 直播動態】：直播間累積點讚達到 {last_like_milestone_notified} 次！（此為背景數據里程碑，可隨性帶過或略過）",
                                "audio_base64": None,
                                "timestamp": time.time(),
                                "source": "tiktok_ambient"
                            })
                except Exception:
                    pass

            @client.on(ShareEvent)
            async def on_share(event: ShareEvent):
                nonlocal last_ambient_notify_time
                global current_tiktok_status_str
                try:
                    user_name = event.user.nickname or event.user.unique_id or "觀眾"
                    current_tiktok_status_str = f"[📢 {user_name} 分享]"
                    now = time.time()
                    if not GLOBAL_PIANO_REALTIME_STATE.get("is_playing", False) and (now - last_ambient_notify_time > 90.0):
                        last_ambient_notify_time = now
                        await input_queue.put({
                            "text": f"【TikTok 直播動態】：觀眾「{user_name}」分享了直播間！（是否感謝由妳自由決定）",
                            "audio_base64": None,
                            "timestamp": time.time(),
                            "source": "tiktok_ambient"
                        })
                except Exception:
                    pass

            @client.on(QuestionNewEvent)
            async def on_question(event: QuestionNewEvent):
                try:
                    user_name = getattr(getattr(event, 'user', None), 'nickname', '') or "觀眾"
                    q_text = getattr(getattr(event, 'question', None), 'text', '') or getattr(event, 'text', '')
                    if q_text:
                        log_print(f"❓ [TikTok 提問箱] {user_name} 提問: {q_text}")
                        await input_queue.put({
                            "text": f"【TikTok 官方提問箱】：觀眾「{user_name}」提問：『{q_text}』。（是否回答由妳自由決定）",
                            "audio_base64": None,
                            "timestamp": time.time(),
                            "source": "tiktok"
                        })
                except Exception:
                    pass

            @client.on(SubNotifyEvent)
            async def on_sub(event: SubNotifyEvent):
                try:
                    user_name = getattr(getattr(event, 'user', None), 'nickname', '') or "觀眾"
                    log_print(f"👑 [TikTok 訂閱] 觀眾 {user_name} 訂閱成為會員！")
                    sys_notify(f"👑 [TikTok 訂閱] {user_name} 訂閱成為會員！")
                    await input_queue.put({
                        "text": f"【TikTok 直播動態】：觀眾「{user_name}」付費訂閱成為專屬會員！（是否慶祝/感謝由妳自由決定）",
                        "audio_base64": None,
                        "timestamp": time.time(),
                        "source": "tiktok_gift"
                    })
                except Exception:
                    pass

            TIKTOK_GIFT_COMBO_BUFFER = {}

            async def _flush_gift_combo(k, delay=3.2):
                try:
                    await asyncio.sleep(delay)
                    if k in TIKTOK_GIFT_COMBO_BUFFER:
                        info = TIKTOK_GIFT_COMBO_BUFFER.pop(k)
                        u_name = info["user_name"]
                        g_name = info["gift_name"]
                        tot_count = info["count"]
                        log_print(f"🎉 [TikTok 連續送禮結算] {u_name} 連擊結束，累計送出 {tot_count} 個 {g_name}！")
                        sys_notify(f"🎁 [TikTok 送禮結算] {u_name} 送了 {tot_count} 個 {g_name}！")
                        
                        gift_desc = f"連續送出了 {tot_count} 個 {g_name}！" if tot_count > 1 else f"送出了 1 個 {g_name}！"
                        await input_queue.put({
                            "text": f"【TikTok 直播觀眾 {u_name} 送禮】：{gift_desc}請向他熱情道謝並給予即時互動！",
                            "audio_base64": None,
                            "timestamp": time.time(),
                            "source": "tiktok_gift"
                        })
                except asyncio.CancelledError:
                    pass
                except Exception as ex:
                    log_print(f"⚠️ [送禮聚合結算異常]: {ex}")

            @client.on(GiftEvent)
            async def on_gift(event: GiftEvent):
                try:
                    raw_create_time = getattr(getattr(event, 'common', None), 'create_time', 0)
                    if raw_create_time:
                        c_time_sec = (raw_create_time / 1000.0) if raw_create_time > 1e11 else float(raw_create_time)
                        if c_time_sec < (connect_timestamp - 15.0):
                            return

                    msg_id = getattr(getattr(event, 'common', None), 'msg_id', None)
                    if msg_id:
                        if msg_id in seen_msg_set:
                            return
                        if len(seen_msg_ids) >= 1000:
                            oldest = seen_msg_ids.popleft()
                            seen_msg_set.discard(oldest)
                        seen_msg_set.add(msg_id)
                        seen_msg_ids.append(msg_id)

                    user_name = "觀眾"
                    if hasattr(event, 'user') and event.user:
                        user_name = event.user.nickname or event.user.unique_id or "觀眾"
                    
                    gift_obj = getattr(event, 'gift', None)
                    if not gift_obj:
                        return
                    
                    gift_info = getattr(gift_obj, 'info', None)
                    gift_name = getattr(gift_info, 'name', None) if gift_info else None
                    if not gift_name:
                        gift_name = getattr(gift_obj, 'name', '禮物')
                    gift_count = getattr(gift_obj, 'count', 1)
                    
                    combo_key = (user_name, gift_name)
                    if combo_key in TIKTOK_GIFT_COMBO_BUFFER:
                        combo_info = TIKTOK_GIFT_COMBO_BUFFER[combo_key]
                        combo_info["count"] += gift_count
                        if combo_info.get("task") and not combo_info["task"].done():
                            combo_info["task"].cancel()
                    else:
                        TIKTOK_GIFT_COMBO_BUFFER[combo_key] = {
                            "count": gift_count,
                            "user_name": user_name,
                            "gift_name": gift_name,
                            "task": None
                        }
                        combo_info = TIKTOK_GIFT_COMBO_BUFFER[combo_key]
                    
                    log_print(f"🎁 [TikTok 送禮 (連擊計數)] {user_name} 送出了 {gift_count} 個 {gift_name}！（當前累計: {combo_info['count']} 個，等待連送結算...）")
                    
                    # 延遲 3.2 秒等待連擊結束後一次性結算
                    combo_info["task"] = asyncio.create_task(_flush_gift_combo(combo_key, delay=3.2))
                except Exception as e:
                    log_print(f"⚠️ [TikTok 送禮處理異常]: {e}")

            ws_task = await client.start()
            if ws_task:
                last_offline_notify = False
                await ws_task  # 🌟 真正常駐等待 WebSocket 運行
            else:
                await asyncio.sleep(8.0)
        except asyncio.CancelledError:
            break
        except SignatureRateLimitError:
            if not last_offline_notify:
                log_print("⚠️ [TikTok 直播] 公共簽名伺服器頻率限制 (可在 .env 設定 SIGN_API_KEY 免除限制)，30 秒後重試...")
            await asyncio.sleep(30.0)
        except Exception as e:
            err_str = str(e)
            if "offline" in err_str.lower():
                if not last_offline_notify:
                    log_print(f"📺 [TikTok 直播] 直播主 {tid} 目前尚未開播 (Offline)，已進入靜默待命狀態（每 30 秒靜態檢測，開播時將自動無縫秒連）...")
                    last_offline_notify = True
                await asyncio.sleep(30.0)
            else:
                log_print(f"⚠️ [TikTok 直播連線狀態]: {err_str}，15 秒後自動重試...")
                await asyncio.sleep(15.0)
        finally:
            try:
                if client and client.connected:
                    await client.disconnect()
            except Exception:
                pass

# ────────────────────────────────────────────────────────
# 🚀 17. 主程式進入點與終端機即時狀態列 (main Entry Point & ANSI Status Bar)
# ────────────────────────────────────────────────────────
# 💡 功能目的：
#    - 系統總指揮中心：連線 VTube Studio WebSocket (Port 8001) 並完成 Token 認證。
#    - 同時啟動所有背景感知工作協程（麥克風、畫面截圖、餘光視覺、鋼琴合成、CMA 監控、TikTok 彈幕）。
#    - 在終端機以 ANSI 虛擬終端即時刷新單行乾淨狀態列（旋轉游標、當前大腦狀態、麥克風音量、TikTok 動態）。

async def main():
    """系統主進入點：協同啟動所有背景感知神經與對話處理協程"""
    await asyncio.to_thread(_remove_temp_mp3)
    asyncio.create_task(asyncio.to_thread(init_piano_synthesizer))
    # 🛑 系統啟動防殘留：立即向雲端與本地同步乾淨待命狀態（徹底消除重開機殘留）
    await realtime_task_mgr.sync_to_cloud()
    # 📜 載入或初始化全集中全景時序記憶中樞
    init_unified_memory()

    plugin_info = {"plugin_name": "7L_AI_VTuber", "developer": "e5_Studio", "authentication_token_path": "./vts_token.txt"}
    vts = RobustVTSClient(plugin_info=plugin_info)
    global vc.GLOBAL_VTS
    vc.GLOBAL_VTS = vts
    print("正在連線至 VTube Studio (Port 8001)...")
    
    try:
        await vts.connect(retries=3, retry_delay=2.0)
        await vts.read_token()
        if not vts.authentic_token:
            await vts.request_authenticate_token()
            await vts.write_token()
        await vts.request_authenticate()
        await set_vts_expression(vts, "_RESET_")
        print("✅ 成功連接到 VTube Studio！\n")
        
        asyncio.create_task(print_model_parameters(vts))
        asyncio.create_task(ai_face_tracking_loop(vts))
        asyncio.create_task(vts_health_worker(vts))
    except Exception as e:
        print(f"⚠️ VTS 啟動連線未完成 ({e})，已啟動背景自動重連守護（程式正常運作中，開啟 VTS 後將自動連線）。\n")
        asyncio.create_task(vts_health_worker(vts))

    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.2  # 停頓超過 1.2 秒判定為話語結束
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.non_speaking_duration = 0.5

    input_queue = asyncio.Queue()
    
    # 啟動全部背景協程
    asyncio.create_task(mic_volume_worker())
    asyncio.create_task(mic_worker(recognizer, input_queue))
    asyncio.create_task(text_file_listener_worker(input_queue))
    asyncio.create_task(console_keyboard_input_worker(input_queue))
    asyncio.create_task(screen_capture_worker())
    asyncio.create_task(chat_processor_worker(vts, input_queue))
    asyncio.create_task(streamer_mind_loop_worker(vts, input_queue))
    asyncio.create_task(proactive_worker(vts, input_queue))
    asyncio.create_task(anti_watermark_worker(vts))
    asyncio.create_task(cma_monitor_worker())
    asyncio.create_task(peripheral_vision_worker())
    asyncio.create_task(speech_queue_worker(vts, input_queue))
    asyncio.create_task(system_audio_worker())
    asyncio.create_task(expression_keeper_worker(vts))
    asyncio.create_task(autonomous_wander_worker())
    asyncio.create_task(piano_focus_udp_worker())
    asyncio.create_task(tiktok_live_worker(input_queue))
    asyncio.create_task(auto_restore_piano_state_on_startup())
    if DISCORD_TOKEN:
        asyncio.create_task(discord_bot.start(DISCORD_TOKEN))
    
    print("\n=========================================")
    print("✨ [7L] 已啟動！")
    print("=========================================\n")

    spinner_chars = ['/', '-', '\\', '|']
    idx = 0
    

    
    try:
        while True:
            char = spinner_chars[idx % len(spinner_chars)]
            term_cols = shutil.get_terminal_size((80, 20)).columns
            max_cols = max(30, term_cols - 1)  # 留 1 個 column 絕對防止 Windows 控制台自動換行
            
            # 依據是否有即時通知，動態組合尾端文字 (通知放在最後面，絕不佔用整行)
            has_notif = time.time() < notification_expire_time
            if has_notif:
                tail_str = f"💬 {current_system_notification}"
                if current_tiktok_status_str and current_tiktok_status_str != "[📱 TikTok: 待命中]":
                    tail_str = f"{current_tiktok_status_str} | {tail_str}"
            else:
                tail_str = current_tiktok_status_str

            # 依據終端寬度動態分配狀態文字、動作文字、音量與 尾端通知/動態 (排在最後面)
            if max_cols < 85:
                status_text = fit_text_to_width(current_ai_status_str, max(18, max_cols - 48))
                action_text = "🎤 聆聽中" if is_user_listening else fit_text_to_width(current_mic_action_str, 8)
                tail_text = fit_text_to_width(tail_str, max(14, max_cols - 45))
                raw_msg = f"[{char}] {status_text} | {action_text} | {current_mic_volume_str} | {tail_text}"
            else:
                status_text = fit_text_to_width(current_ai_status_str, max(28, max_cols - 65))
                action_text = "🎤 聆聽中..." if is_user_listening else fit_text_to_width(current_mic_action_str, 12)
                tail_text = fit_text_to_width(tail_str, max(20, max_cols - 75))
                raw_msg = f"[{char}] {status_text} | {action_text} | {current_mic_volume_str} | {tail_text}"
            out_msg = fit_text_to_width(raw_msg, max_cols)
            
            out_msg = out_msg.replace('\n', ' ').replace('\r', '')
            disp_w = get_display_width(out_msg)
            padding = " " * max(0, max_cols - disp_w)
            
            # 使用 ANSI 擦除 + 精準寬度填充，徹底根除 Windows 終端換行與尾端空格殘影
            print(f"\r\033[2K\r{out_msg}{padding}", end="", flush=True)
            
            idx += 1
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print("\n👋 [系統] 收到 Ctrl+C 中斷，正在安全退出...")
    except BaseException as e:
        print(f"\n❌ [底層系統異常崩潰]: {e}")

if __name__ == "__main__":
    asyncio.run(main())
