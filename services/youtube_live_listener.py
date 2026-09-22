# -*- coding: utf-8 -*-
"""
📺 YouTube Live 聊天室監聽（InnerTube get_live_chat 輪詢 · 免 API 金鑰）

流程：抓 live_chat 頁面拿 continuation → 輪詢 get_live_chat → 解析留言 →
     input_queue（source="youtube"），與 TikTok/Twitch 同一條觀眾軌道。

設定 .env：
    YOUTUBE_LIVE_ID=watch?v= 後面那串 ID（直接貼完整網址也行）
⚠️ 非官方端點：YouTube 改版可能失效，失效時本 worker 持續重試並記錄，
   不會影響主程式。
"""
import asyncio
import os
import re
import time

import httpx

from core.utils import log_print

_API = "https://www.youtube.com/youtubei/v1/live_chat/get_live_chat?prettyPrint=false"
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
_CLIENT = {"clientName": "WEB", "clientVersion": "2.20260101.01.00", "hl": "zh-TW", "gl": "TW"}

_CONT_PATTERNS = [
    r'"liveChatRenderer":\{"continuation":"([^"]+)"',
    r'"continuation"\s*:\s*"([A-Za-z0-9_%\-\.]{12,})"',
]


def normalize_video_id(raw: str) -> str:
    """接受完整網址（v= / youtu.be/ / live/）或裸 ID"""
    raw = (raw or "").strip()
    m = re.search(r"(?:v=|youtu\.be/|live/)([A-Za-z0-9_\-]{6,})", raw)
    return m.group(1) if m else raw


def extract_continuation(html: str):
    """從 live_chat 頁面 HTML/JSON 抓第一個 continuation token"""
    for p in _CONT_PATTERNS:
        m = re.search(p, html or "")
        if m:
            return m.group(1)
    return None


def _find_simple(obj, key):
    """深度搜尋 {key: {"simpleText": ...}}（authorName 等），回傳字串或 None"""
    if isinstance(obj, dict):
        if key in obj:
            v = obj[key]
            if isinstance(v, dict) and "simpleText" in v:
                return v["simpleText"]
            if isinstance(v, str):
                return v
        for v in obj.values():
            r = _find_simple(v, key)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_simple(v, key)
            if r:
                return r
    return None


def parse_live_chat_response(data):
    """純函式：InnerTube get_live_chat 回應 → (messages, next_continuation, wait_seconds)

    messages = [{"user": 顯示名, "message": 內容}, ...]
    相容兩種形狀：有包 continuationContents 或直接 liveChatContinuation。
    """
    data = data or {}
    lc = (data.get("continuationContents", {}) or {}).get("liveChatContinuation") \
        or data.get("liveChatContinuation") or data

    messages = []
    for act in (lc.get("actions") or []):
        renderer = None
        text_action = act.get("addLiveChatTextAction")
        if isinstance(text_action, dict):
            item = text_action.get("item") or text_action
            renderer = item.get("liveChatTextActionRenderer")
        if not renderer:
            continue                                   # 送禮/徽章/入場等其他 action 忽略
        runs = (renderer.get("message") or {}).get("runs") or []
        text = "".join(str(r.get("text", "")) for r in runs).strip()
        if not text:
            continue
        author = _find_simple(renderer, "authorName") or "觀眾"
        messages.append({"user": author, "message": text})

    cont = lc.get("continuation")
    timeout_ms = lc.get("timeoutMs") or 8000
    wait = max(5.0, min(15.0, float(timeout_ms) / 1000.0))   # 官方給幾秒就等幾秒（上下限 5~15s）
    return messages, cont, wait


def build_queue_item(user: str, message: str) -> dict:
    """與 TikTok/Twitch 相容的格式（軌道2 正則可解析；無 (@id) 時自動用暱稱當 id）"""
    return {
        "text": f"【YouTube 直播觀眾 {user}】：{message}",
        "audio_base64": None,
        "timestamp": time.time(),
        "source": "youtube",
    }


async def youtube_live_worker(input_queue):
    """背景協程：輪詢 YouTube Live 聊天室（抓頁面 → 輪詢 → 轉發，自動換代 token）"""
    vid = normalize_video_id(os.getenv("YOUTUBE_LIVE_ID") or "")
    if not vid:
        log_print("ℹ️ [YouTube] 未設定 YOUTUBE_LIVE_ID，聊天室監聽未啟動")
        return

    headers = {"User-Agent": _UA, "Content-Type": "application/json"}
    warned_no_cont = False

    async with httpx.AsyncClient(timeout=25, headers={"User-Agent": _UA}) as cli:
        cont = None
        while True:                                   # 外層：取得（或重新取得）continuation
            try:
                if not cont:
                    page = await cli.get(f"https://www.youtube.com/live_chat?v={vid}&is_popout=1")
                    cont = extract_continuation(page.text)
                    if not cont:
                        if not warned_no_cont:
                            log_print(f"⚠️ [YouTube] 取不到 continuation（ID={vid} —— 該影片正在直播嗎？），15 秒後重試")
                            warned_no_cont = True
                        await asyncio.sleep(15)
                        continue
                    warned_no_cont = False
                    log_print(f"📺 [YouTube] 已連線 live_chat：{vid}")

                while True:                           # 內層：輪詢聊天
                    resp = await cli.post(_API, headers=headers,
                                          json={"context": {"client": _CLIENT}, "token": cont})
                    if resp.status_code != 200:
                        log_print(f"⚠️ [YouTube] get_live_chat HTTP {resp.status_code} → 重新抓 continuation")
                        cont = None
                        await asyncio.sleep(10)
                        break

                    msgs, next_cont, wait = parse_live_chat_response(resp.json())
                    for m in msgs:
                        await input_queue.put(build_queue_item(m["user"], m["message"]))
                        try:
                            import services.web_dashboard as wd
                            wd.broadcast_event("youtube_comment", m)
                        except Exception:
                            pass

                    if not next_cont:
                        log_print("ℹ️ [YouTube] continuation 結束（直播可能已結束），20 秒後重抓")
                        cont = None
                        await asyncio.sleep(20)
                        break
                    cont = next_cont
                    await asyncio.sleep(wait)
            except Exception as e:
                log_print(f"⚠️ [YouTube] 輪詢異常：{type(e).__name__}: {e}，10 秒後重試")
                cont = None
                await asyncio.sleep(10)
