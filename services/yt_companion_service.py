# -*- coding: utf-8 -*-
"""
🎬 YouTube 專屬「眼與耳」即時感官與時序記憶中樞 (services/yt_companion_service.py)
--------------------------------------------------------------------------
🎯 核心設計：
1. 【只當眼與耳，不發出聲音】：
   - 持續接收 1 FPS 視窗裁切畫面 + 16kHz WASAPI 數位原聲音訊。
   - 完全靜音（不佔用喇叭、不發出 TTS 音訊），純粹充當 7L 的視覺與聽覺受體。
2. 【播到哪，記憶沉澱到哪】：
   - 每 15~20 秒或偵測到精彩轉折時，自動將剛才看到的畫面動作、字幕與對白
     提煉為客觀生動的「視聽劇情筆記」，沉澱進 `YT_PERCEPTION_LOG`。
3. 【無縫注入 7L 主腦】：
   - 提供 `get_yt_memory_context()`。
   - 當主人在麥克風或文字中對 7L 說話時，7L 主腦（8大 Gemini 模型 + 傲嬌個性 + RVC 口型）
     自動調用這份影片記憶，用她自己的聲音自然回答主人！
"""

import os
import sys
import time
import asyncio
import io
import queue
import warnings
from collections import deque
from datetime import datetime
import numpy as np
from PIL import Image, ImageGrab

# 徹底過濾底層音訊警告
warnings.filterwarnings("ignore")
try:
    from soundcard.mediafoundation import SoundcardRuntimeWarning
    warnings.filterwarnings("ignore", category=SoundcardRuntimeWarning)
except Exception:
    pass

# WebSocket 握手補丁
import core.websocket_patch
from core.llm_engine import GEMINI_KEYS
from core.utils import log_print, sys_notify
from google import genai
from google.genai import types

try:
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    import soundcard as sc
    HAS_SOUNDCARD = True
except ImportError:
    HAS_SOUNDCARD = False

# 全域狀態
IS_YT_WATCHER_ENABLED = True     # 全域功能總開關
IS_YT_COMPANION_ACTIVE = False   # 當前是否鎖定 YouTube 視窗並在感官串流中
CURRENT_YT_TITLE = ""            # 當前鎖定的 YouTube 影片標題
LATEST_YT_FRAME_BYTES = None     # 最新一幀裁剪後的 YouTube 截圖 (供 Web 儀表板相框顯示)
ON_VISION_RECORD_CB = None       # 外部視覺紀錄回呼: cb(text, scene)

# 🧠 影片劇情時序感知記憶池（保留最新 15 筆劇情記憶紀錄）
YT_PERCEPTION_LOG = deque(maxlen=15)
_LAST_MEMORY_TICK_TIME = 0.0

# 內部控制
_live_session = None
_loopback_streamer = None
_service_task = None

def find_youtube_window():
    """
    🎯 嚴格前景判定 (Strict Focus Detection)：
    只鎖定「當前操作中的前景焦點視窗 (GetForegroundWindow)」或「置頂浮動子母畫面 (PiP Topmost)」。
    若使用者切換至 VS Code、遊戲或桌面在背景播放音樂，一律返回 None，徹底杜絕 Token 浪費。
    """
    if not HAS_WIN32:
        return None, None, ""

    # 1. 檢測當前前景焦點視窗 (最重要核心判斷)
    try:
        fg_hwnd = win32gui.GetForegroundWindow()
        if fg_hwnd and win32gui.IsWindowVisible(fg_hwnd) and not win32gui.IsIconic(fg_hwnd):
            fg_title = win32gui.GetWindowText(fg_hwnd)
            # 排除純 YouTube Music (music.youtube.com) 標籤，專注影片
            if ("YouTube" in fg_title or "- YouTube" in fg_title) and "YouTube Music" not in fg_title:
                r = win32gui.GetWindowRect(fg_hwnd)
                w, h = r[2] - r[0], r[3] - r[1]
                if w > 300 and h > 200:
                    return fg_hwnd, r, fg_title
    except Exception:
        pass

    # 2. 檢測置頂浮動子母畫面 (PiP / Topmost 視窗，例如 Chrome 懸浮看片)
    pip_hwnd, pip_rect, pip_title = None, None, ""
    def _enum_topmost_cb(hwnd, _):
        nonlocal pip_hwnd, pip_rect, pip_title
        if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
            # 檢查是否有 WS_EX_TOPMOST 置頂屬性
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            if ex_style & win32con.WS_EX_TOPMOST:
                title = win32gui.GetWindowText(hwnd)
                if ("YouTube" in title or "- YouTube" in title or "Picture-in-Picture" in title or "子母畫面" in title) and "YouTube Music" not in title:
                    r = win32gui.GetWindowRect(hwnd)
                    w, h = r[2] - r[0], r[3] - r[1]
                    if w > 200 and h > 150:
                        pip_hwnd = hwnd
                        pip_rect = r
                        pip_title = title
                        return False
        return True

    try:
        import win32con
        win32gui.EnumWindows(_enum_topmost_cb, None)
    except Exception:
        pass

    return pip_hwnd, pip_rect, pip_title

class AudioLoopbackStreamer:
    """WASAPI Loopback 系統音訊採集 (YouTube 聲音 16kHz PCM)"""
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.running = False
        self.audio_queue = queue.Queue(maxsize=120)
        self.thread = None

    def start(self):
        if not HAS_SOUNDCARD:
            return
        self.running = True
        import threading
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None

    def _worker(self):
        try:
            default_spk = sc.default_speaker().name
            loopback_mic = None
            for m in sc.all_microphones(include_loopback=True):
                if m.isloopback and (m.name == default_spk or default_spk in m.name):
                    loopback_mic = m
                    break
            if not loopback_mic:
                for m in sc.all_microphones(include_loopback=True):
                    if m.isloopback:
                        loopback_mic = m
                        break
            if not loopback_mic:
                return

            chunk_frames = 3200 # 0.2 秒採集
            with loopback_mic.recorder(samplerate=self.sample_rate, channels=1) as mic:
                while self.running:
                    data = mic.record(numframes=chunk_frames)
                    pcm_int16 = (data * 32767.0).clip(-32768, 32767).astype(np.int16).tobytes()
                    if not self.audio_queue.full():
                        self.audio_queue.put_nowait(pcm_int16)
        except Exception:
            pass

EYE_EAR_SYSTEM_INSTRUCTION = """
你是 7L 的「眼與耳感官神經中樞 (Visual & Auditory Sensory Nerve)」。
你正在充當 7L 的眼睛與耳朵，透過即時畫面串流與系統原聲音訊，觀看主人電腦上的 YouTube 影片。

【核心規則】：
1. 【絕對靜音】：你不是對話助手，不要對主人說話，保持安靜。
2. 【記憶沉澱記錄員】：你的職責是將影片內容提煉為「劇情與情境筆記」，存入 7L 的記憶庫。
3. 【記錄格式】：每當收到記錄信號或劇情發生關鍵轉折，用繁體中文記錄 1~2 句話：
   - 畫面動作、字幕與文字重點
   - 角色說了什麼關鍵台詞、笑點或情節進展
   - 保持生動、具體、客觀（例如：「灰檸檬在電車難題選了撞 4 公斤，說比較不會痛...」）。
"""

def add_perception_memory(text: str):
    """將一段感官記憶加入時序隊列，並同步推送至 Web 後台視覺串流"""
    global YT_PERCEPTION_LOG
    clean = text.strip()
    if not clean:
        return
    # 避免重複刷同一句
    if YT_PERCEPTION_LOG and clean == YT_PERCEPTION_LOG[-1].get("content"):
        return
    time_str = datetime.now().strftime("%H:%M:%S")
    item = {"time": time_str, "content": clean}
    YT_PERCEPTION_LOG.append(item)
    log_print(f"👁️👂 [YT 眼耳感知沉澱] ({time_str}): {clean}")

    # 🌐 同步推播至 Web 儀表板 VISION 視覺時序歷史串流
    if ON_VISION_RECORD_CB:
        try:
            video_note = f"《{CURRENT_YT_TITLE[:22]}》: {clean}" if CURRENT_YT_TITLE else clean
            ON_VISION_RECORD_CB(video_note, scene="觀賞影片")
        except Exception:
            pass

def get_yt_memory_context() -> str:
    """供 7L 主腦 fetch_ai_response 調用的時序影片記憶字串"""
    if not IS_YT_COMPANION_ACTIVE and not YT_PERCEPTION_LOG:
        return ""

    title = CURRENT_YT_TITLE if CURRENT_YT_TITLE else "剛才觀看的影片"
    lines = [
        f"【🎬 7L 雙眼與雙耳感知的 YouTube 影片即時記憶】",
        f"影片標題：《{title}》",
        "（妳的眼耳感知神經正在/剛才同步觀看這部影片，以下是妳親眼看到和聽到的劇情進展筆記）："
    ]
    if YT_PERCEPTION_LOG:
        for it in list(YT_PERCEPTION_LOG)[-8:]: # 取最新 8 筆
            lines.append(f"- [{it['time']}] {it['content']}")
    else:
        lines.append("- (目前畫面正在加載或剛進入影片中)")
    lines.append("👉 當老爸問妳影片內容、剛才那個人在幹嘛、或聊到這部片時，請直接以妳親眼看到和親耳聽到的記憶，用 7L 本人的口氣自然回答！")
    return "\n".join(lines)

async def _yt_companion_session_loop(target_hwnd, initial_rect, initial_title):
    """單次 YouTube 伴看感官連線"""
    global _live_session, _loopback_streamer
    global IS_YT_COMPANION_ACTIVE, CURRENT_YT_TITLE

    if not GEMINI_KEYS:
        log_print("❌ [YT 眼耳] 無可用 GEMINI_KEYS，無法啟動感官串流")
        return

    api_key = GEMINI_KEYS[0]
    client = genai.Client(api_key=api_key)
    model = "gemini-3.1-flash-live-preview"

    CURRENT_YT_TITLE = initial_title
    IS_YT_COMPANION_ACTIVE = True
    sys_notify(f"👀 啟動眼耳感知: {initial_title[:25]}...")
    log_print(f"🎬 [YT 眼耳] 正在為視窗啟動感官串流: {initial_title[:40]}...")

    if not _loopback_streamer:
        _loopback_streamer = AudioLoopbackStreamer(sample_rate=16000)
        _loopback_streamer.start()

    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        output_audio_transcription=types.AudioTranscriptionConfig(),
        system_instruction=types.Content(
            parts=[types.Part.from_text(text=EYE_EAR_SYSTEM_INSTRUCTION)]
        )
    )

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            _live_session = session
            log_print(f"✅ [YT 眼耳] 感官神經連線就緒！開始默默吸收畫面與聲音。")

            session_running = True
            last_seen_time = time.time()
            current_rect = initial_rect

            # 啟動時沉澱第一筆認知
            add_perception_memory(f"開始陪伴老爸觀看 YouTube 影片《{initial_title[:30]}》")

            # 任務 1: 畫面採集 (1 FPS)
            async def _video_worker():
                global LATEST_YT_FRAME_BYTES
                nonlocal session_running, current_rect
                while session_running and IS_YT_WATCHER_ENABLED:
                    try:
                        bbox = (current_rect[0], current_rect[1], current_rect[2], current_rect[3]) if current_rect else None
                        shot = ImageGrab.grab(bbox=bbox)
                        shot.thumbnail((1024, 576))
                        buf = io.BytesIO()
                        shot.save(buf, format="JPEG", quality=70)
                        jpeg_bytes = buf.getvalue()
                        LATEST_YT_FRAME_BYTES = jpeg_bytes

                        await session.send_realtime_input(
                            video=types.Blob(data=jpeg_bytes, mime_type="image/jpeg")
                        )
                    except Exception:
                        pass
                    await asyncio.sleep(1.0)

            # 任務 2: 系統音訊採集
            async def _audio_worker():
                nonlocal session_running
                while session_running and IS_YT_WATCHER_ENABLED:
                    try:
                        pcm_chunk = _loopback_streamer.audio_queue.get_nowait()
                        if pcm_chunk:
                            await session.send_realtime_input(
                                audio=types.Blob(data=pcm_chunk, mime_type="audio/pcm;rate=16000")
                            )
                    except queue.Empty:
                        await asyncio.sleep(0.04)
                    except Exception:
                        await asyncio.sleep(0.04)

            # 任務 3: 定期促使大腦沉澱當前進度記憶 (每 15 秒觸發一次記錄刷新)
            async def _memory_tick_worker():
                nonlocal session_running
                await asyncio.sleep(6.0) # 給連線初期幾秒積累
                while session_running and IS_YT_WATCHER_ENABLED:
                    try:
                        # 促使模型將最近這段的視聽內容做一個 1~2 句的感官沉澱筆記
                        await session.send_realtime_input(text="請用繁體中文，用一句話記錄剛剛畫面中發生的動作或人物台詞：")
                        await session.send_realtime_input(activity_end=types.ActivityEnd())
                    except Exception:
                        pass
                    await asyncio.sleep(18.0) # 每 18 秒沉澱一次記憶

            # 任務 4: 接收字幕筆記 (純文字沉澱，不播放任何聲音！)
            async def _receive_worker():
                nonlocal session_running
                full_turn_text = []
                async for response in session.receive():
                    if not session_running:
                        break
                    content = response.server_content
                    if content is not None:
                        # 🔇 關鍵：完全不播放 part.inline_data，保持安靜！
                        if hasattr(content, "output_transcription") and content.output_transcription:
                            if hasattr(content.output_transcription, "text") and content.output_transcription.text:
                                full_turn_text.append(content.output_transcription.text)

                        if getattr(content, "interrupted", False):
                            full_turn_text.clear()

                        if getattr(content, "turn_complete", False):
                            if full_turn_text:
                                complete_text = "".join(full_turn_text).strip()
                                # 濾除非筆記的客套話
                                if complete_text and len(complete_text) > 3:
                                    add_perception_memory(complete_text)
                                full_turn_text.clear()

            # 併發啟動
            v_task = asyncio.create_task(_video_worker())
            a_task = asyncio.create_task(_audio_worker())
            m_task = asyncio.create_task(_memory_tick_worker())
            r_task = asyncio.create_task(_receive_worker())

            # 視窗持續存在性檢查
            while session_running and IS_YT_WATCHER_ENABLED:
                hwnd, rect, title = find_youtube_window()
                now = time.time()
                if hwnd:
                    last_seen_time = now
                    current_rect = rect
                    CURRENT_YT_TITLE = title
                else:
                    if now - last_seen_time > 4.0:
                        log_print("💤 [YT 嚴格前景] YouTube 視窗已離開焦點 (判定為背景聽音樂/工作)，4 秒內已自動休眠斷線，0 API 消耗。")
                        session_running = False
                        break

                await asyncio.sleep(1.0)

            v_task.cancel()
            a_task.cancel()
            m_task.cancel()
            r_task.cancel()

    except Exception as e:
        log_print(f"⚠️ [YT 眼耳] 感官連線中斷: {e}")
    finally:
        _live_session = None
        IS_YT_COMPANION_ACTIVE = False
        LATEST_YT_FRAME_BYTES = None

# ── 🎬 伴看授權閘門（網站通知確認）────────────────────────────────────────────
#   YT_COMPANION_APPROVAL=0            關閉詢問，回到純自動啟動
#   YT_COMPANION_APPROVAL_TIMEOUT=60   等待老爸在後台回應的秒數（與前端進度條同步）
#   YT_COMPANION_ON_TIMEOUT=allow|deny 超時未回應：allow=照常啟動／deny=本次不啟動
#   YT_COMPANION_APPROVAL_COOLDOWN=180 被拒絕後，多少秒內不再詢問
YT_REQUIRE_APPROVAL = (os.getenv("YT_COMPANION_APPROVAL", "1") or "1").strip() == "1"
YT_APPROVAL_TIMEOUT = float(os.getenv("YT_COMPANION_APPROVAL_TIMEOUT", "60") or 60)
YT_APPROVAL_ON_TIMEOUT = (os.getenv("YT_COMPANION_ON_TIMEOUT", "allow") or "allow").strip().lower()
YT_APPROVAL_COOLDOWN = float(os.getenv("YT_COMPANION_APPROVAL_COOLDOWN", "180") or 180)

_pending_approval = None
_reject_until = 0.0


def _broadcast_yt(event_type: str, payload: dict):
    try:
        import services.web_dashboard as _wd
        _wd.broadcast_event(event_type, payload)
    except Exception:
        pass


def resolve_yt_approval(approved: bool, title: str = "") -> bool:
    """由網站後台（WS action 或 /api/yt_companion/*）呼叫：回應當前待審批的伴看請求。"""
    global _pending_approval
    if _pending_approval:
        _pending_approval["approved"] = bool(approved)
        try:
            _pending_approval["event"].set()
        except Exception:
            pass
        return True
    return False


async def request_yt_approval(title: str) -> bool:
    """回 True=允許啟動伴看感官串流；False=拒絕／超時未授權／視窗已離開。"""
    global _pending_approval, _reject_until
    if not YT_REQUIRE_APPROVAL:
        return True
    now = time.time()
    if now < _reject_until:
        return False
    short_title = (title or "")[:30]
    ev = asyncio.Event()
    _pending_approval = {"event": ev, "approved": False, "title": title}
    _broadcast_yt("yt_companion_request", {"title": title, "short_title": short_title})
    log_print(f"🔔 [YT 眼耳] 偵測到影片視窗《{short_title}》，等待老爸在網站後台授權伴看...")

    deadline = time.time() + YT_APPROVAL_TIMEOUT
    window_gone = False
    while not ev.is_set():
        remain = deadline - time.time()
        if remain <= 0:
            break
        try:
            await asyncio.wait_for(ev.wait(), timeout=min(1.0, max(remain, 0.1)))
        except asyncio.TimeoutError:
            pass
        except Exception:
            break
        hwnd, _, _ = find_youtube_window()
        if not hwnd:
            window_gone = True
            break

    approved = bool(_pending_approval and _pending_approval.get("approved"))
    decided = ev.is_set()
    _pending_approval = None

    if decided and approved:
        _broadcast_yt("yt_companion_approved", {"title": title})
        log_print("✅ [YT 眼耳] 老爸已授權，啟動伴看感官串流。")
        return True
    if decided and not approved:
        _broadcast_yt("yt_companion_rejected", {"title": title, "reason": "rejected"})
        _reject_until = time.time() + YT_APPROVAL_COOLDOWN
        log_print(f"❌ [YT 眼耳] 老爸拒絕伴看，{int(YT_APPROVAL_COOLDOWN)} 秒內不再詢問。")
        return False

    _broadcast_yt("yt_companion_rejected", {"title": title, "reason": "timeout"})
    if window_gone:
        log_print("💤 [YT 眼耳] 等待授權期間視窗已離開焦點，取消本次伴看。")
        return False
    if YT_APPROVAL_ON_TIMEOUT == "deny":
        _reject_until = time.time() + YT_APPROVAL_COOLDOWN
        log_print(f"⌛ [YT 眼耳] {int(YT_APPROVAL_TIMEOUT)} 秒未授權，本次不啟動（冷卻 {int(YT_APPROVAL_COOLDOWN)} 秒）。")
        return False
    log_print(f"⌛ [YT 眼耳] {int(YT_APPROVAL_TIMEOUT)} 秒未回應，依設定放行啟動伴看。")
    return True


async def start_yt_auto_watcher():
    """背景守護協程：偵測 YouTube 出現，經網站授權後自動連線眼耳感官"""
    log_print("👀 [YT 眼耳雷達] 背景視窗偵測守護已啟動")
    while True:
        try:
            if IS_YT_WATCHER_ENABLED and not IS_YT_COMPANION_ACTIVE:
                hwnd, rect, title = find_youtube_window()
                if hwnd:
                    if not await request_yt_approval(title):
                        await asyncio.sleep(1.5)
                        continue
                    hwnd, rect, title = find_youtube_window()
                    if not hwnd:
                        await asyncio.sleep(1.5)
                        continue
                    await _yt_companion_session_loop(hwnd, rect, title)
            await asyncio.sleep(1.5)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(2.0)

def init_yt_companion():
    """在系統啟動時初始化：掛上網站授權回呼並啟動背景任務"""
    global _service_task
    try:
        import services.web_dashboard as _wd
        _wd.APPROVE_YT_COMPANION_CALLBACK = lambda title="": resolve_yt_approval(True, title)
        _wd.REJECT_YT_COMPANION_CALLBACK = lambda title="": resolve_yt_approval(False, title)
    except Exception:
        pass
    if _service_task is None:
        _service_task = asyncio.create_task(start_yt_auto_watcher())
    return _service_task
