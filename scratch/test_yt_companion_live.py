# -*- coding: utf-8 -*-
"""
🎬 YouTube 即時伴看與深度視聽理解測試 (scratch/test_yt_companion_live.py)
--------------------------------------------------------------------------
功能特色：
1. 視窗自動雷達：自動檢測前景或螢幕上的 YouTube 視窗與座標。
2. 視覺高畫質捕獲：自動裁剪 YouTube 視窗 (720p/1024p)，精確讀懂影片畫面與字幕。
3. 系統音訊內錄 (WASAPI Loopback)：直接抓取電腦 YouTube 原始聲音 (16kHz PCM)，無雜音無失真。
4. Gemini Live 雙向即時串流：使用 gemini-3.1-flash-live-preview，音畫同步理解。
5. 隨時互動：終端機隨時可輸入問題（或語音），AI 即刻根據看到的畫面與聽到的聲音回答！
"""

import os
import sys
import warnings

# 徹底過濾 soundcard 與底层音訊緩衝跳幀警告，保持終端機乾淨
warnings.filterwarnings("ignore")
try:
    from soundcard.mediafoundation import SoundcardRuntimeWarning
    warnings.filterwarnings("ignore", category=SoundcardRuntimeWarning)
except Exception:
    pass

# 將專案根目錄加入模組搜尋路徑
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import time
import asyncio
import threading
import io
import queue
import numpy as np
from PIL import Image, ImageGrab
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# WebSocket 相容補丁
import core.websocket_patch
from core.llm_engine import GEMINI_KEYS
from google import genai
from google.genai import types

try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    import soundcard as sc
    HAS_SOUNDCARD = True
except ImportError:
    HAS_SOUNDCARD = False

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

# 顏色輸出
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def find_youtube_window():
    """尋找螢幕上開啟 YouTube 的瀏覽器視窗與座標"""
    if not HAS_WIN32:
        return None, None, "未安裝 pywin32"
    
    yt_hwnd = None
    yt_rect = None
    yt_title = ""

    # 先查前景視窗 (最精準)
    fg_hwnd = win32gui.GetForegroundWindow()
    if fg_hwnd and win32gui.IsWindowVisible(fg_hwnd):
        fg_title = win32gui.GetWindowText(fg_hwnd)
        if "YouTube" in fg_title or "youtube" in fg_title.lower():
            r = win32gui.GetWindowRect(fg_hwnd)
            w, h = r[2] - r[0], r[3] - r[1]
            if w > 300 and h > 200:
                return fg_hwnd, r, fg_title

    # 若前景不是，遍歷所有可見視窗尋找 YouTube
    def enum_cb(hwnd, extra):
        nonlocal yt_hwnd, yt_rect, yt_title
        if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if "YouTube" in title or "- YouTube" in title:
                r = win32gui.GetWindowRect(hwnd)
                w, h = r[2] - r[0], r[3] - r[1]
                if w > 300 and h > 200:
                    yt_hwnd = hwnd
                    yt_rect = r
                    yt_title = title
                    return False  # 停止尋找
        return True

    try:
        win32gui.EnumWindows(enum_cb, None)
    except Exception:
        pass

    return yt_hwnd, yt_rect, yt_title

class AudioLoopbackStreamer:
    """透過 WASAPI Loopback 擷取系統聲音 (YouTube 播放的聲音)"""
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.running = False
        self.audio_queue = queue.Queue(maxsize=100)
        self.thread = None

    def start(self):
        if not HAS_SOUNDCARD:
            print(f"{RED}❌ 未安裝 soundcard 模組，無法啟動系統音訊內錄{RESET}")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._record_worker, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _record_worker(self):
        try:
            default_spk = sc.default_speaker().name
            loopback_mic = None
            for m in sc.all_microphones(include_loopback=True):
                if m.isloopback and (m.name == default_spk or default_spk in m.name):
                    loopback_mic = m
                    break
            
            if not loopback_mic:
                # 備用首個 loopback
                for m in sc.all_microphones(include_loopback=True):
                    if m.isloopback:
                        loopback_mic = m
                        break
            
            if not loopback_mic:
                print(f"{YELLOW}⚠️ 找不到 WASAPI Loopback 錄音裝置，將不傳送系統聲音{RESET}")
                return

            # print(f"{CYAN}🎙️ 系統音訊內錄裝置鎖定: {loopback_mic.name}{RESET}")
            chunk_frames = 3200 # 0.2 秒 (平滑緩衝)
            with loopback_mic.recorder(samplerate=self.sample_rate, channels=1) as mic:
                while self.running:
                    data = mic.record(numframes=chunk_frames) # float32 array
                    pcm_int16 = (data * 32767.0).clip(-32768, 32767).astype(np.int16).tobytes()
                    if not self.audio_queue.full():
                        self.audio_queue.put_nowait(pcm_int16)
        except Exception as e:
            # print(f"{YELLOW}⚠️ 音訊內錄執行緒例外: {e}{RESET}")
            pass

class AudioPlayer:
    """非阻塞背景播放 Gemini Live 傳回的 24kHz PCM 語音"""
    def __init__(self):
        self.p = pyaudio.PyAudio() if HAS_PYAUDIO else None
        self.stream = None
        self.q = queue.Queue()
        self.running = True
        if self.p:
            try:
                self.stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=24000,
                    output=True
                )
                self.t = threading.Thread(target=self._play_loop, daemon=True)
                self.t.start()
            except Exception as e:
                print(f"{YELLOW}⚠️ 無法開啟音訊播放串流: {e}{RESET}")

    def write(self, pcm_bytes):
        self.q.put_nowait(pcm_bytes)

    def _play_loop(self):
        while self.running:
            try:
                data = self.q.get(timeout=0.2)
                if self.stream and data:
                    self.stream.write(data)
            except queue.Empty:
                continue
            except Exception:
                pass

    def close(self):
        self.running = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
        if self.p:
            self.p.terminate()

SYSTEM_INSTRUCTION = """
你是主人的專屬 AI 伴看夥伴。你正在跟主人一起「同步看 YouTube 影片」。
你有極強的多模態理解能力，同時接收：
1. 【畫面串流 (Video)】：正在播放的 YouTube 畫面（包含影片動作、人物表情、內嵌/CC字幕、簡報文字、道具UI）。
2. 【系統音訊 (Audio)】：YouTube 影片正在播放的原始聲音（對話、背景音樂、旁白）。
3. 【主人的輸入】：主人隨時在終端機或語音跟你說話。

【理解與回答原則】：
1. 嚴格看懂聽懂：仔細看畫面中的字幕與文字，聽懂講話者的內容，把畫面動作跟聲音結合在一起。
2. 角色自然生動：像個並肩坐在一起看片的好友，自然口語、簡短有力（1~3句話），不要講官話廢話。
3. 優先回應主人：當主人提問或吐槽時，你必須立刻給出自然語音回答，明確回答你有沒有看到或看到什麼。
"""

async def run_yt_live_session():
    if not GEMINI_KEYS:
        print(f"{RED}❌ 找不到 GEMINI_API_KEY，請檢查 .env 設定！{RESET}")
        return

    api_key = GEMINI_KEYS[0]
    client = genai.Client(api_key=api_key)
    model = "gemini-3.1-flash-live-preview"

    print(f"\n{BOLD}{CYAN}======================================================{RESET}")
    print(f"{BOLD}{GREEN}🎬 YouTube 即時伴看視聽理解系統啟動中...{RESET}")
    print(f"{BOLD}{CYAN}======================================================{RESET}")
    print(f"📡 目標模型: {model}")
    print(f"🔑 API Key: ...{api_key[-6:]}")
    print(f"👀 正在掃描螢幕上的 YouTube 視窗...\n")

    # 啟動系統聲音內錄
    audio_loopback = AudioLoopbackStreamer(sample_rate=16000)
    audio_loopback.start()
    
    # 非阻塞背景音訊播放器
    audio_player = AudioPlayer()

    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        output_audio_transcription=types.AudioTranscriptionConfig(),
        system_instruction=types.Content(
            parts=[types.Part.from_text(text=SYSTEM_INSTRUCTION)]
        )
    )

    async with client.aio.live.connect(model=model, config=config) as session:
        print(f"{GREEN}✅ Gemini Live API 雙向連線成功！{RESET}")
        print(f"{YELLOW}💡 提示：現在請在螢幕上播放任何 YouTube 影片。{RESET}")
        print(f"{YELLOW}💡 你可以直接在終端機打字問它（例如：『這部片在講什麼？』），按 Enter 發送。{RESET}")
        print(f"{YELLOW}💡 輸入 'exit' 或 'q' 結束程式。\n{RESET}")

        is_running = True
        last_ai_speak_time = 0.0
        last_user_question_time = 0.0

        # 任務 1: 畫面截圖串流 (1 FPS)
        async def video_worker():
            nonlocal is_running
            last_title = ""
            while is_running:
                hwnd, rect, title = find_youtube_window()
                
                if rect:
                    if title != last_title:
                        print(f"\n{CYAN}🎯 鎖定 YouTube 視窗: {title[:45]}... (尺寸: {rect[2]-rect[0]}x{rect[3]-rect[1]}){RESET}")
                        last_title = title
                    bbox = (rect[0], rect[1], rect[2], rect[3])
                else:
                    bbox = None # 全螢幕
                
                try:
                    shot = ImageGrab.grab(bbox=bbox)
                    shot.thumbnail((1024, 576))
                    buf = io.BytesIO()
                    shot.save(buf, format="JPEG", quality=75)
                    jpeg_bytes = buf.getvalue()

                    await session.send_realtime_input(
                        video=types.Blob(data=jpeg_bytes, mime_type="image/jpeg")
                    )
                except Exception:
                    pass

                await asyncio.sleep(1.0) # 1 FPS

        # 任務 2: 系統音訊串流 (YouTube 聲音 16kHz)
        async def audio_worker():
            nonlocal is_running, last_ai_speak_time, last_user_question_time
            while is_running:
                try:
                    pcm_chunk = audio_loopback.audio_queue.get_nowait()
                    now = time.time()
                    # 🛡️ 雙重靜音保護：
                    # 1. AI 剛講完話 1.0 秒內不送音訊（防自我打斷）
                    # 2. 主人剛提問 2.0 秒內不送音訊（給伺服器安靜窗口觸發回答）
                    ai_busy = (now - last_ai_speak_time < 1.0)
                    user_asking = (now - last_user_question_time < 2.0)
                    
                    if pcm_chunk and not ai_busy and not user_asking:
                        await session.send_realtime_input(
                            audio=types.Blob(data=pcm_chunk, mime_type="audio/pcm;rate=16000")
                        )
                except queue.Empty:
                    await asyncio.sleep(0.03)
                except Exception:
                    await asyncio.sleep(0.03)

        # 任務 3: 接收 Gemini 回應 (語音播放 + 即時文字印出)
        async def receive_worker():
            nonlocal is_running, last_ai_speak_time
            first_chunk = True
            async for response in session.receive():
                content = response.server_content
                if content is not None:
                    # 語音
                    if content.model_turn is not None:
                        last_ai_speak_time = time.time()
                        for part in content.model_turn.parts:
                            if part.inline_data:
                                audio_player.write(part.inline_data.data)
                            if part.text:
                                if first_chunk:
                                    print(f"\n{BOLD}{GREEN}🤖 AI: {RESET}", end="", flush=True)
                                    first_chunk = False
                                print(f"{GREEN}{part.text}{RESET}", end="", flush=True)

                    # 即時字幕轉錄 (Transcription)
                    if hasattr(content, "output_transcription") and content.output_transcription:
                        if hasattr(content.output_transcription, "text") and content.output_transcription.text:
                            last_ai_speak_time = time.time()
                            if first_chunk:
                                print(f"\n{BOLD}{GREEN}🤖 AI: {RESET}", end="", flush=True)
                                first_chunk = False
                            print(f"{GREEN}{content.output_transcription.text}{RESET}", end="", flush=True)

                    # 打斷處理 (Interruption)
                    if getattr(content, "interrupted", False):
                        first_chunk = True
                        print(f"\n{YELLOW}[⚡ 觸發打斷]{RESET}")

                    # 回合完成
                    if getattr(content, "turn_complete", False):
                        first_chunk = True
                        print() # 換行

        # 任務 4: 終端機使用者文字輸入
        async def user_input_worker():
            nonlocal is_running, last_user_question_time
            loop = asyncio.get_running_loop()
            while is_running:
                try:
                    user_text = await loop.run_in_executor(None, input, f"\n{BOLD}你 (隨時提問): {RESET}")
                    user_text = user_text.strip()
                    if not user_text:
                        continue
                    if user_text.lower() in ["exit", "quit", "q"]:
                        print("👋 正在中斷連線...")
                        is_running = False
                        break
                    
                    print(f"{CYAN}📤 送出問題: {user_text}{RESET}")
                    # 標記主人提問時間，觸發 2 秒音訊靜音窗口
                    last_user_question_time = time.time()
                    
                    # 送出文字，並強制結束活動以觸發模型回應
                    await session.send_realtime_input(text=f"[主人提問]: {user_text}")
                    await session.send_realtime_input(activity_end=types.ActivityEnd())
                except Exception:
                    break

        # 併發執行各個 worker
        tasks = [
            asyncio.create_task(video_worker()),
            asyncio.create_task(audio_worker()),
            asyncio.create_task(receive_worker()),
            asyncio.create_task(user_input_worker()),
        ]

        # 等待退出
        while is_running:
            await asyncio.sleep(0.5)

        for t in tasks:
            t.cancel()

    audio_loopback.stop()
    audio_player.close()
    print(f"{GREEN}✅ 測試工作階段順利結束。{RESET}")

if __name__ == "__main__":
    try:
        asyncio.run(run_yt_live_session())
    except KeyboardInterrupt:
        print("\n使用者中斷")
