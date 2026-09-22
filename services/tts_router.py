r"""
🎙️ TTS 路由器 (TTS Router)

🎯 目的：
   把直播主迴圈的語音合成，從「寫死 C:\Users\qiwai\GPT-SoVITS 的單一引擎」
   改成可插拔的引擎鏈，預設走本地小模型 Kokoro-82M (ONNX，約 310MB)。

⚙️ 引擎優先序（可用環境變數覆寫）：
   TTS_ENGINE=kokoro          預設：本地離線、RTX 3060 Ti 或 CPU 都跑得動
        ↓ 失敗才降級
   TTS_FALLBACK=edge          微軟雲端（台灣腔 zh-TW 聲線），音質優良、零 GPU
        ↓
   TTS_FALLBACK=xiaoyi        原 GPT-SoVITS 曉伊（需本機存在 GPT-SoVITS 安裝）

🌍 語言自動判定：沿用原 local_xiaoyi_service 的假名/漢字啟發式，
   中文夾日文梗（バカ → 八嘎）會先做音譯，再交給對應聲線。

📦 介面：
   await get_tts_audio_bytes(text)  ->  WAV/MP3 bytes（與原 get_xiaoyi_audio_bytes 相容）
   get_active_engine()              ->  目前生效的引擎名稱（供儀表板/日誌）
"""

import os
import re
import io
import time
import asyncio
import threading
from typing import Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KOKORO_DIR = os.path.join(BASE_DIR, "models", "kokoro")

# ── 設定 ─────────────────────────────────────────────────────────────────────
ENGINE_ORDER = [e.strip().lower() for e in (os.getenv("TTS_ENGINE") or "kokoro").split(",") if e.strip()]
_FALLBACK = [e.strip().lower() for e in (os.getenv("TTS_FALLBACK") or "edge,xiaoyi").split(",") if e.strip()]

# 依序嘗試的完整引擎鏈（去重、保序）
_seen = set()
ENGINE_CHAIN = []
for _e in ENGINE_ORDER + _FALLBACK:
    if _e not in _seen:
        _seen.add(_e)
        ENGINE_CHAIN.append(_e)
if not ENGINE_CHAIN:
    ENGINE_CHAIN = ["kokoro", "edge", "xiaoyi"]

ZH_VOICE = os.getenv("TTS_ZH_VOICE") or "zf_001"      # v1.1-zh 聲線檔為匿名 ID（zf_001~zf_099）
JA_VOICE = os.getenv("TTS_JA_VOICE") or "edge"         # 此 voices 檔無日文聲線 -> 走 edge-tts
EN_VOICE = os.getenv("TTS_EN_VOICE") or "af_sol"
TTS_SPEED = float(os.getenv("TTS_SPEED") or "1.0")
KOKORO_MODEL = os.getenv("TTS_KOKORO_MODEL") or "kokoro-v1.1-zh.onnx"
KOKORO_VOICES = os.getenv("TTS_KOKORO_VOICES") or "voices-v1.1-zh.bin"

_active_engine: Optional[str] = None
_engine_errors: dict = {}


def _log(msg: str) -> None:
    """安全輸出：Windows cp950 主控台印不出 emoji 時自動降級，绝不讓 log 打斷合成流程"""
    try:
        print(msg)
    except Exception:
        try:
            print(msg.encode("utf-8", "replace").decode("ascii", "replace"))
        except Exception:
            pass

# ── Kokoro 懶載入（模型 310MB，只在第一次合成時載入）─────────────────────────
_kokoro = None
_kokoro_lock = threading.Lock()


def _resolve_kokoro_paths() -> Tuple[Optional[str], Optional[str]]:
    model = os.path.join(KOKORO_DIR, KOKORO_MODEL)
    voices = os.path.join(KOKORO_DIR, KOKORO_VOICES)
    # 目錄裡若只有另一版檔案就自動抓現有的
    if not os.path.exists(model):
        cands = sorted([f for f in os.listdir(KOKORO_DIR) if f.endswith(".onnx")]) if os.path.isdir(KOKORO_DIR) else []
        if cands:
            model = os.path.join(KOKORO_DIR, cands[0])
    if not os.path.exists(voices):
        cands = sorted([f for f in os.listdir(KOKORO_DIR) if f.endswith(".bin")]) if os.path.isdir(KOKORO_DIR) else []
        if cands:
            voices = os.path.join(KOKORO_DIR, cands[0])
    if os.path.exists(model) and os.path.exists(voices):
        return model, voices
    return None, None


def _get_kokoro():
    global _kokoro
    if _kokoro is not None:
        return _kokoro
    model, voices = _resolve_kokoro_paths()
    if not model:
        raise RuntimeError(f"Kokoro 模型檔缺失（{KOKORO_DIR}）")
    # Windows 下 phonemizer 需要 espeak-ng 資料；espeakng_loader 內建一份
    try:
        import espeakng_loader
        os.environ.setdefault("ESPEAK_DATA_PATH", espeakng_loader.get_data_path())
        os.environ.setdefault("ESPEAKNG_DLL_PATH", espeakng_loader.get_library_path())
    except Exception:
        pass
    from kokoro_onnx import Kokoro
    _kokoro = Kokoro(model, voices)
    return _kokoro


# ── 文字前處理（沿用原曉伊服務的防卡頓規則）──────────────────────────────────
_LOANWORDS = {
    'バカ': '八嘎', 'ばか': '八嘎',
    'かわいい': '卡哇伊', 'カワイイ': '卡哇伊',
    'すごい': '斯國一', 'スゴイ': '斯國一',
    'すげえ': '斯國一', 'スゲエ': '斯國一',
    'やばい': '呀拜', 'ヤバイ': '呀拜',
    'おはよ': '歐嗨喲', 'オハヨ': '歐嗨喲',
    'ありがと': '阿里嘎多', 'アリガト': '阿里嘎多',
}
RE_TAG = re.compile(r'\[[A-Z_]+(?::[^\]]*)?\]')


def detect_language(text: str) -> str:
    """回傳 'ja' 或 'zh'（沿用原假名/漢字啟發式，中文語境優先）"""
    num_kana = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF]', text))
    num_hanzi = len(re.findall(r'[\u4E00-\u9FFF]', text))
    has_chinese_markers = bool(re.search(r'[的了嗎吧呢這那是在說妳你我他們著啦喔呀嘛欸咦啥誰怎麼盧搞弄為什麼]', text))
    if num_kana > 0:
        if num_hanzi == 0:
            return "ja"
        if not has_chinese_markers and (num_kana / (num_kana + num_hanzi) >= 0.35):
            return "ja"
        if has_chinese_markers and (num_kana / (num_kana + num_hanzi) >= 0.65):
            return "ja"
    return "zh"


def _clean_text(text: str, lang: str) -> str:
    text = RE_TAG.sub('', text or "")
    text = re.sub(r'[\(（][^\)）]*[\)）]', '', text)          # 括號表情 (∠・ω<)
    text = re.sub(r'[⌒☆★♪♡♥✧✦๑•̀ㅂ•́و✧~～]+', '！', text)
    text = text.replace("7L", "小七").replace("7l", "小七")
    text = re.sub(r'[，,]{2,}', '，', text)
    text = re.sub(r'[！!]{2,}', '！', text).strip(' ，,')
    if lang != "ja":
        for k, v in _LOANWORDS.items():
            text = text.replace(k, v)
    return text


# ── 各引擎實作 ───────────────────────────────────────────────────────────────
def _synth_kokoro_sync(text: str) -> bytes:
    """阻塞式合成（Kokoro ONNX），回傳 WAV bytes"""
    k = _get_kokoro()
    lang = detect_language(text)
    text = _clean_text(text, lang)
    if not text:
        return b""

    if lang == "ja":
        # v1.1-zh 聲線檔不含日文聲線：直接拋錯，讓引擎鏈降級到 edge-tts 日文聲線
        if JA_VOICE == "edge" or not _voice_exists(k, JA_VOICE):
            raise RuntimeError("Kokoro voices 檔無日文聲線，日文交給 edge-tts")
        voice = JA_VOICE
    elif lang == "en":
        voice = EN_VOICE if _voice_exists(k, EN_VOICE) else _pick_voice(k, "af_")
    else:
        voice = ZH_VOICE if _voice_exists(k, ZH_VOICE) else _pick_voice(k, "zf_")
    if not voice:
        raise RuntimeError("voices 檔內沒有可用聲線")

    # espeak 語系代碼：中文是 cmn（普通話）不是 zh
    espeak_lang = {"zh": "cmn", "ja": "ja", "en": "en-us"}.get(lang, "cmn")
    samples, sr = k.create(text, voice=voice, speed=TTS_SPEED, lang=espeak_lang)
    import numpy as np
    import soundfile as sf
    buf = io.BytesIO()
    sf.write(buf, np.asarray(samples, dtype=np.float32), sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def _voice_exists(k, name: str) -> bool:
    try:
        voices = k.get_voices() if hasattr(k, "get_voices") else list(getattr(k, "voices", {}).keys())
        return bool(name) and name in set(voices)
    except Exception:
        return True   # 無法列舉時不設限，交給 create() 自己報錯


def _pick_voice(k, prefix: str) -> str:
    """挑第一個符合前綴的可用聲線（zf_ / zm_ / af_ …）"""
    try:
        voices = sorted(k.get_voices() if hasattr(k, "get_voices") else getattr(k, "voices", {}).keys())
        for v in voices:
            if v.startswith(prefix):
                return v
    except Exception:
        pass
    return ""


async def _synth_kokoro(text: str) -> bytes:
    # ONNX 推論是 CPU 密集，丟到執行緒避免卡住直播事件迴圈
    async with _AioLock(_kokoro_lock):
        return await asyncio.to_thread(_synth_kokoro_sync, text)


class _AioLock:
    """把 threading.Lock 包成 async context（to_thread 內仍需序列化同一模型）"""
    def __init__(self, lock: threading.Lock):
        self._lock = lock

    async def __aenter__(self):
        await asyncio.to_thread(self._lock.acquire)
        return self

    async def __aexit__(self, *exc):
        self._lock.release()
        return False


async def _synth_edge(text: str) -> bytes:
    """微軟 Edge-TTS 雲端合成（台灣腔女聲 / 日文聲線），回傳 MP3 bytes"""
    import edge_tts
    lang = detect_language(text)
    voice = "ja-JP-NanamiNeural" if lang == "ja" else "zh-TW-HsiaoChenNeural"
    text = _clean_text(text, lang)
    if not text:
        return b""
    comm = edge_tts.Communicate(text, voice=voice, rate="+0%")
    buf = io.BytesIO()
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


async def _synth_xiaoyi(text: str) -> bytes:
    """原 GPT-SoVITS 曉伊（需本機有 GPT-SoVITS 安裝，否則拋錯讓鏈降級）"""
    svc_path = os.getenv("GPT_SOVITS_DIR") or r"C:\Users\qiwai\GPT-SoVITS"
    if not os.path.isdir(svc_path):
        raise RuntimeError(f"GPT-SoVITS 不存在: {svc_path}")
    import local_xiaoyi_service
    return await local_xiaoyi_service.get_xiaoyi_audio_bytes(text)


_ENGINES = {
    "kokoro": _synth_kokoro,
    "edge": _synth_edge,
    "xiaoyi": _synth_xiaoyi,
}


def get_active_engine() -> Optional[str]:
    return _active_engine


def get_engine_errors() -> dict:
    return dict(_engine_errors)


def file_extension(engine: str) -> str:
    """回傳該引擎產出的副檔名（供播放端正確命名暫存檔）"""
    return ".mp3" if engine == "edge" else ".wav"


async def get_tts_audio_bytes(text: str) -> bytes:
    """
    依引擎鏈合成語音。全部失敗回傳 b""（呼叫端會記錄警告，不會中斷直播）。
    """
    global _active_engine
    if not text or not text.strip():
        return b""

    # 第一次成功後固定走該引擎（避免每次合成都重試失敗引擎）
    chain = ([_active_engine] if _active_engine in _ENGINES else []) + \
            [e for e in ENGINE_CHAIN if e != _active_engine]

    for engine in chain:
        fn = _ENGINES.get(engine)
        if fn is None:
            continue
        try:
            t0 = time.time()
            data = await fn(text)
            if data and len(data) > 100:
                if _active_engine != engine:
                    _log(f"[TTS Router] 切換引擎 -> {engine}")
                    _active_engine = engine
                _engine_errors.pop(engine, None)
                return data
            raise RuntimeError("回傳音訊為空")
        except Exception as e:
            _engine_errors[engine] = str(e)[:200]
            if _active_engine == engine:
                _active_engine = None  # 生效中的引擎壞了，重新走整條鏈
            _log(f"[TTS Router] {engine} 失敗，降級下一個: {str(e)[:120]}")
            continue
    return b""


# 向後相容：舊程式碼呼叫 get_xiaoyi_audio_bytes 也能運作
async def get_xiaoyi_audio_bytes(text: str) -> bytes:
    return await get_tts_audio_bytes(text)
