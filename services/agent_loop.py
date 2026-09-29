# -*- coding: utf-8 -*-
"""🔁 7L Agent Loop（常駐 Live session 迴路）
階段 1：TikTok 閒聊走常駐 session（已上線）
階段 2：Live function calling → execute_tool_dispatch（點歌/鋼琴/搜尋）
階段 3：轉世前摘要壓縮，前情提要帶入新 session
階段 4：老爸開口即打斷當前語音（barge-in）
開關：環境變數 AGENT_LOOP=1，或改 IS_AGENT_LOOP_ENABLED。失敗一律回退舊鏈。
"""
import asyncio
import os
import re
import sys
import time

import core.websocket_patch  # 🔧 修復 Live API additional_headers 相容性

try:
    import opencc
    _S2T_CONVERTER = opencc.OpenCC('s2t')
    def to_traditional(text: str) -> str:
        if not text:
            return ""
        try:
            return _S2T_CONVERTER.convert(text)
        except Exception:
            return text
except Exception:
    def to_traditional(text: str) -> str:
        return text or ""

IS_AGENT_LOOP_ENABLED = os.getenv("AGENT_LOOP", "1") == "1"
IS_AGENT_LOOP_DAD = os.getenv("AGENT_LOOP_DAD", "1") == "1"  # 爸爸主腦也進迴路（整台 agent 化）

LIVE_MODEL = os.getenv("GEMINI_LIVE_MODEL", "gemini-3.1-flash-live-preview").strip()
# 爸爸迴路優先 3.8 Live（RPD Unlimited，解 HTTP 20/天上限；2026-09-26 實測命中）
_env_live_model = os.getenv("GEMINI_LIVE_MODEL", "").strip()
DAD_LIVE_MODEL_CANDIDATES = list(dict.fromkeys([
    m for m in [
        _env_live_model,
        "gemini-3.8-live",
        "gemini-3.1-flash-live-preview",
        "gemini-3-flash-live-preview",
    ] if m
]))
SUMMARY_MODEL = "gemini-3.5-flash-lite"
MAX_TURNS_PER_SESSION = 30
MAX_TRANSCRIPT_CHARS = 12000
RECEIVE_TIMEOUT = 30.0
DEEP_THINK_TIMEOUT = 150.0

AGENT_DAD_SYSTEM_PROMPT = """妳是 7L，老爸的 AI 女兒，直接跟老爸對話（老爸使用語音或打字）。
- 稱呼固定叫「老爸」，絕不叫老爹/爹地/爸爸以外的稱呼。
- 🗣️ 必須開口說話：只要老爸在跟妳說話、測試麥克風（例如「聽得到嗎」、「在嗎」）、打招呼或提問，妳【必須開口說出 1~3 句繁體中文口語回答】，絕對不可只輸出表情標籤 [EXPRESSION: ...] 而沒有任何實質台詞！
- 👁️ 視覺感知能力：妳隨時擁有眼角餘光視覺，時刻注視老爸當前的電腦螢幕畫面！當老爸問「看得到我現在的畫面嗎」或問螢幕內容時，請直接依據開頭提供的「老爸當前電腦畫面與環境感知」情報親切自然地回答老爸，詳細說出妳看到的視窗、程式碼或內容，絕對不要說看不到！
- 日常閒聊、問候、接梗、看畫面閒談：直接用自然口吻回 1~3 句，可穿插 [EXPRESSION: 微笑/臉紅/星星/WINK/震驚]。
- 寫代碼、除錯、推理計算、深度分析、複雜決策、看螢幕找 bug：【必須調用】deep_think(query=老爸原話) 把難題丟給旗艦大腦，拿到結果後用妳的口吻轉述（1~3 句，不要貼程式碼原文以外的廢話）。
- 需要即時資訊先調用 search_google；要唱歌調用 auto_sing_song；要彈琴調用 pe.play_virtual_piano。
- 老爸專注自語、純咳嗽無須回應時只回 [SILENCE]。
- 嚴禁輸出 thought/結構化草稿。嚴禁 Emoji。
- 🌏 語言鎖定：一律用繁體中文回覆，絕對不輸出其他語言（英語/葡萄牙語/日語）。"""

AGENT_SYSTEM_PROMPT = """妳是 7L，老爸的 AI 女兒，正在 TikTok 直播間跟觀眾閒聊。
- 用自然隨性口吻回 1~2 句短話（20~40 字），句尾帶標點，可穿插 [EXPRESSION: 微笑/臉紅/星星/WINK/震驚]。
- 觀眾明確點歌（唱歌/翻唱）→ 調用 auto_sing_song；想聽鋼琴 → 調用 pe.play_virtual_piano；需要即時資訊 → 調用 search_google。
- 加好友、借帳號等事務：一律回「這個要問我老爸做主喔！」，絕不答應或開條件。
- 工具節制：只有觀眾明確提問（有問號、想知道哪個、怎麼、為何）才調用 search_google；閒聊、附和、表情符號、無意義短句絕不調工具，直接回話或 [PASS]。
- 🌏 語言鎖定：一律用繁體中文回覆，觀眾用外語留言也用繁中回，絕不輸出其他語言。
- 無聊刷屏只回 [PASS]。
- 嚴禁輸出 thought/結構化草稿，直接說台詞。嚴禁 Emoji。"""


def is_enabled() -> bool:
    return bool(IS_AGENT_LOOP_ENABLED)


def is_dad_enabled() -> bool:
    return bool(IS_AGENT_LOOP_DAD)


def get_core():
    """動態拿主核心（仿 auto_cover_pipeline，避循環 import）"""
    return sys.modules.get("vts_7L_test") or sys.modules.get("__main__")


def _get_current_screen_hint(core) -> str:
    """獲取老爸當前螢幕畫面與眼角餘光情報，注入對話上下文讓 7L 具備真實視覺。"""
    try:
        hints = []
        # 1. YouTube 伴讀
        try:
            from services import yt_companion_service as _yt_comp
            if getattr(_yt_comp, "IS_YT_COMPANION_ACTIVE", False) and getattr(_yt_comp, "CURRENT_YT_TITLE", ""):
                hints.append(f"正在觀看 YouTube: 《{_yt_comp.CURRENT_YT_TITLE}》")
        except Exception:
            pass

        # 2. 螢幕視覺感知（餘光/全域）
        screen_ctx = getattr(core, "current_screen_context", "")
        if screen_ctx and screen_ctx != "目前沒有特別的畫面動態。":
            hints.append(f"螢幕畫面: {screen_ctx}")

        # 3. 系統音樂/背景音
        audio_ctx = getattr(core, "current_system_audio_context", "")
        if audio_ctx and audio_ctx != "目前沒有播放特別的聲音。":
            hints.append(f"背景聲音: {audio_ctx}")

        if hints:
            return "（老爸當前電腦畫面與環境感知：" + "；".join(hints) + "）\n"
    except Exception:
        pass
    return ""


def _build_live_tools(core):
    """沿用主腦工具表（觀眾安全版：禁麥克風/清空記憶），轉成 Live function declarations。
    🛡️ 再加一道：雲端認知寫入（update_cloud_knowledge/clear_all_memories）迴路禁用，
    雲端人設只准 HTTP 主腦鏈寫，避免觀眾哄騙 session 竄改世界觀。"""
    try:
        from google.genai import types as _types
    except Exception:
        return None
    try:
        builder = getattr(core, "build_genai_declarations", None)
        if not callable(builder):
            return None
        tools = builder(is_proactive=True) or []
        banned = {"update_cloud_knowledge", "clear_all_memories", "control_microphone"}
        filtered = []
        for tool in tools or []:
            try:
                decls = [d for d in (getattr(tool, "function_declarations", None) or [])
                         if getattr(d, "name", "") not in banned]
                if decls:
                    filtered.append(_types.Tool(function_declarations=decls))
            except Exception:
                continue
        return filtered or None
    except Exception:
        pass
    return None


def _build_deep_think_tool():
    """旗艦大腦外掛工具：難題丟 HTTP 3.8 梯隊，session 負責轉述。"""
    try:
        from google.genai import types as _types
        decl = _types.FunctionDeclaration(
            name="deep_think",
            description="把寫代碼、除錯、推理、深度分析等難題交給旗艦大腦，拿到深度答案後再轉述給老爸。",
            parameters=_types.Schema(
                type="OBJECT",
                properties={"query": _types.Schema(
                    type="STRING", description="老爸的原話或難題描述")},
                required=["query"]))
        return _types.Tool(function_declarations=[decl])
    except Exception:
        return None


class StreamingSentenceDetector:
    """🌊 即時流式分句偵測器：在 Live 3.8 逐 Token 吐字時，按自然標點切出完整子句。"""
    def __init__(self, min_chars: int = 6):
        self.min_chars = min_chars
        self.buffer = ""

    def feed(self, text: str) -> list[str]:
        if not text:
            return []
        self.buffer += text
        ready = []
        while True:
            # 🛡️ 標籤防腰斬：若有未閉合的 [xxx...，先等待閉合，避免在 [EXPRESSION: 內部切斷
            last_open = self.buffer.rfind('[')
            last_close = self.buffer.rfind(']')
            if last_open != -1 and last_open > last_close:
                break

            m = re.search(r'([^。！？!?；;\n]+[。！？!?；;\n]+)', self.buffer)
            if not m:
                # 逗號門檻較高（>= 25字），防長句過長
                m_comma = re.search(r'([^，,]+[，,]+)', self.buffer)
                if m_comma and len(re.sub(r'[^\w\u4e00-\u9fa5]', '', m_comma.group(1))) >= 25:
                    m = m_comma
                else:
                    break

            segment = m.group(1)
            c_len = len(re.sub(r'[^\w\u4e00-\u9fa5]', '', segment))
            if c_len >= self.min_chars:
                ready.append(segment)
                self.buffer = self.buffer[m.end():]
            else:
                break
        return ready

    def flush(self) -> str:
        rem = self.buffer.strip()
        self.buffer = ""
        return rem


async def _presynth_streaming_sentence(core, raw_sentence: str):
    """🌊 串流預合成 Worker：搶先在 Live API 說完前將完整子句送入 RTX 3080 Ti 推理並放入快取。"""
    try:
        if not raw_sentence:
            return
        from core.prompts import TextCleanEngine as _TCE
        clean = _TCE.clean_for_tts(raw_sentence, apply_phonetics=True)
        clean = (clean or "").strip()
        if len(clean) < 4:
            return

        cache = getattr(core, "TTS_PRE_SYNTH_CACHE", None)
        cache_key_fn = getattr(core, "_tts_cache_key", None)
        key = cache_key_fn(clean, None) if callable(cache_key_fn) else f"auto‖{clean}"

        if cache is not None and key in cache:
            return

        import local_xiaoyi_service
        wav = await local_xiaoyi_service.get_xiaoyi_audio_bytes(clean)
        if wav and len(wav) > 100:
            if cache is not None:
                cache[key] = bytes(wav)
                order = getattr(core, "TTS_PRE_SYNTH_ORDER", None)
                if isinstance(order, list):
                    order.append(key)
                    while len(order) > 25:
                        old_k = order.pop(0)
                        cache.pop(old_k, None)
            log = getattr(core, "log_print", print)
            log(f"🌊 [Live 3.8 流式預合成] 子句搶先合成完畢: '{clean[:16]}' ({len(wav)} bytes)")
    except Exception:
        pass


async def _deep_think(query: str) -> str:
    """HTTP 旗艦梯隊代打：記憶＋歷史＋最新螢幕，3.8 深度思考。"""
    core = get_core()
    log = getattr(core, "log_print", print)
    try:
        log(f"🧠 [AgentLoop deep_think] 旗艦代打啟動：{(query or '')[:40]}")
    except Exception:
        pass
    try:
        mem_ctx = ""
        try:
            mem_ctx = core.get_unified_memory_context(limit=30, thought_char_limit=300)
        except Exception:
            pass
        history = []
        try:
            ch = getattr(core, "DEFAULT_CHANNEL_ID", "dad")
            history = await core.fetch_from_long_term_memory(ch, query, limit=10)
        except Exception:
            pass
        screen = None
        try:
            cache = getattr(core, "latest_screen_cache", None)
            if isinstance(cache, list) and cache:
                first = cache[0]
                screen = first[1] if isinstance(first, (tuple, list)) else first
            elif cache:
                screen = cache
        except Exception:
            pass
        messages = [{"role": "system", "content":
                     "你是 7L 的旗艦思考大腦。深入分析以下問題，給出精準、有條理、可執行的答案（程式碼要完整可跑）。"}]
        if mem_ctx:
            messages.append({"role": "system", "content": f"【對話記憶】：\n{mem_ctx}"})
        messages = messages + (history[-8:] if history else []) + [
            {"role": "user", "content": query or ""}]
        answer = await asyncio.wait_for(
            core.fetch_ai_response(
                messages, image_base64=screen,
                target_model="gemini-3.8-flash", need_thinking=True),
            timeout=DEEP_THINK_TIMEOUT)
        answer = (answer or "").strip()
        if not answer:
            return "旗艦大腦這輪沒想出東西，跟老爸說待會再試試。"
        return answer
    except Exception as e:
        return f"旗艦大腦暫時連不上（{e}），跟老爸說待會再試。"


def _search_cache_key(query: str) -> str:
    """搜尋去重鍵：循環剝同義後綴（涵蓋/覆蓋/列表/國家/有哪些/是什麼），eduroam 連刷視為同一題。"""
    import re as _re
    q = (query or "").strip().lower()
    while True:
        nq = _re.sub(r'(涵蓋|覆蓋|列表|国家|國家|有哪些|是什麼|是甚麼|嗎|呢)\s*$', '', q).strip()
        if nq == q:
            break
        q = nq
    q = _re.sub(r'\s+', ' ', q)
    return q


def _search_cache_get(query: str):
    try:
        key = _search_cache_key(query)
        ent = _SEARCH_CACHE.get(key)
        if ent and time.time() - ent[0] < 120.0:
            return ent[1]
        elif ent:
            _SEARCH_CACHE.pop(key, None)
    except Exception:
        pass
    return None


def _search_cache_put(query: str, result: str):
    try:
        _SEARCH_CACHE[_search_cache_key(query)] = (time.time(), result)
        while len(_SEARCH_CACHE) > 30:
            _SEARCH_CACHE.pop(next(iter(_SEARCH_CACHE)))
    except Exception:
        pass


_SEARCH_CACHE: dict = {}


_STREAM_BEAT = 0.0


def note_stream_heartbeat():
    global _STREAM_BEAT
    try:
        import time as _t
        _STREAM_BEAT = _t.time()
    except Exception:
        pass


def is_stream_live(max_age: float = 2.5) -> bool:
    """串流麥是否存活（舊 mic_worker 看到活著就讓路，避免雙重處理）。"""
    try:
        import time as _t
        return (_t.time() - _STREAM_BEAT) < max_age
    except Exception:
        return False


async def push_stream_audio(sess, pcm16k: bytes) -> bool:
    """連續串流块：只送 audio，不掛電話（話筒常開，斷句 server VAD）。"""
    try:
        if sess is None or getattr(sess, "_session", None) is None:
            return False
        blob_cls = getattr(sess, "_blob_cls", None)
        if blob_cls is None:
            try:
                from google.genai import types as _t2
                blob_cls = getattr(_t2, "AudioBlob", None) or getattr(_t2, "Blob", None)
                sess._blob_cls = blob_cls
            except Exception:
                blob_cls = None
        if blob_cls is None:
            return False
        blob = blob_cls(data=pcm16k, mime_type="audio/pcm;rate=16000")
        await sess._session.send_realtime_input(audio=blob)
        note_stream_heartbeat()
        return True
    except Exception:
        return False


class AgentSession:
    """一條常駐 Live session：多輪不斷線、工具直調、轉世帶摘要。"""

    def __init__(self, persona: str = "", extra_tools=None, timeout: float = 30.0,
                 model_candidates=None, owner: str = "audience"):
        self._session = None
        self._connect = None
        self.turns = 0
        self.transcript: list = []          # [(role, text)] 近期原文，轉世時壓縮
        self.context_summary = ""           # 上一世摘要，下一世首輪帶入
        self._persona = persona or AGENT_SYSTEM_PROMPT
        self._extra_tools = extra_tools or []
        self._timeout = timeout
        self._models = model_candidates or [LIVE_MODEL]
        self.live_model_used = ""
        self._owner = owner
        self._chat_lock = asyncio.Lock()    # 同 session 一次只跑一輪，防並發互踩
        self._pump_task = None              # 常駐接收泵（串流麥克風模式用）
        self._pending = None                # 當前等待中的輪次 Future
        self._downstream = None             # (vts, input_queue)：無人等待的輪次往這裡說話

    def set_downstream(self, vts, input_queue):
        self._downstream = (vts, input_queue)

    def _fail_pending(self):
        try:
            p = self._pending
            self._pending = None
            if p and not p.done():
                p.set_result(("", ""))
        except Exception:
            pass

    def _note_turn(self, heard: str, out: str):
        self.turns += 1
        if heard:
            self.transcript.append(("user", heard[:200]))
        if out:
            self.transcript.append(("model", out[:200]))
        if len(self.transcript) > 40:
            self.transcript = self.transcript[-40:]

    async def _ensure_pump(self) -> bool:
        if self._pump_task and not self._pump_task.done():
            return True
        if not await self._ensure():
            return False
        self._pump_task = asyncio.create_task(self._pump_loop())
        return True

    @staticmethod
    def _resp_sort_key(fr) -> tuple:
        """FunctionResponse 照 id 排序用 key（id 缺失才退回 name）。"""
        try:
            fid = str(getattr(fr, "id", "") or "")
        except Exception:
            fid = ""
        try:
            fname = str(getattr(fr, "name", "") or "")
        except Exception:
            fname = ""
        return (fid or fname, fname)

    @staticmethod
    def _sort_responses(fresps: list) -> list:
        try:
            return sorted(list(fresps or []), key=AgentSession._resp_sort_key)
        except Exception:
            return list(fresps or [])

    @staticmethod
    def _err_responses(calls) -> list:
        """dispatch 無回傳/異常時的保底包：每個 call 一個 error response，照 id 排好。"""
        try:
            from google.genai import types as _t
        except Exception:
            return []
        out = []
        for fc in calls or []:
            try:
                out.append(_t.FunctionResponse(
                    id=getattr(fc, "id", "") or getattr(fc, "name", ""),
                    name=getattr(fc, "name", ""),
                    response={"result": "工具執行無回傳"}))
            except Exception:
                continue
        return AgentSession._sort_responses(out)

    @staticmethod
    def _exc_responses(calls, err: Exception) -> list:
        try:
            from google.genai import types as _t
        except Exception:
            return []
        out = []
        for fc in calls or []:
            try:
                out.append(_t.FunctionResponse(
                    id=getattr(fc, "id", "") or getattr(fc, "name", ""),
                    name=getattr(fc, "name", ""),
                    response={"result": f"執行異常：{str(err)[:200]}"}))
            except Exception:
                continue
        return AgentSession._sort_responses(out)

    def _new_bg_dispatch(self, core, calls: list,
                         send_queue: "asyncio.Queue",
                         pending: list):
        """共用 background dispatch：不 await，pump 立刻回去讀下一包。

        dispatch 跑完只做 q.put（絕不直接碰 socket 寫），發送統一由
        pump 每圈 drain 收齊→照 id 排序→去重→一次發出。工具跑 5~15 秒
        也不卡 socket 讀取。
        """
        async def _bg():
            core2 = core
            try:
                fresps = await self._dispatch_tool_calls(core2, calls)
                if fresps:
                    await send_queue.put(self._sort_responses(fresps))
                else:
                    await send_queue.put(self._err_responses(calls))
            except Exception as _e:
                try:
                    await send_queue.put(self._exc_responses(calls, _e))
                except Exception:
                    pass
        try:
            pending.append(asyncio.create_task(_bg()))
        except Exception:
            pass

    def _sorted_unique_responses(self, batches: list) -> list:
        """多 batch 合併→按 id 排序→同 id 去重（只留最後一個），一次送出。"""
        flat: list = []
        for b in batches or []:
            try:
                flat.extend(list(b or []))
            except Exception:
                continue
        try:
            flat = sorted(flat, key=AgentSession._resp_sort_key)
        except Exception:
            pass
        seen: set = set()
        dedup_rev: list = []
        try:
            for fr in reversed(flat):
                try:
                    key = str(getattr(fr, "id", "") or getattr(fr, "name", "") or "")
                except Exception:
                    key = ""
                if key and key in seen:
                    continue
                if key:
                    seen.add(key)
                dedup_rev.append(fr)
            return list(reversed(dedup_rev))
        except Exception:
            return flat

    async def _settle_tools_keep_reading(self, session, pending: list,
                                           send_queue: "asyncio.Queue",
                                           drain, on_tool,
                                           heard_out: list | None = None,
                                           timeout: float = 60.0) -> int:
        """等 dispatch 收齊，但每 0.5s 短讀一次 socket，保持有人讀。

        為何需要：turn_complete 後若直接 gather 死等 5~15 秒，這段沒人讀
        socket，server ping 石沉大海 → 1011。短輪詢保證 receive() 一直被調用，
        ping 由 SDK 正常回應；輪詢讀到的文字併入 heard_out；期間又來的新
        tool_call 經 on_tool 照樣丟 background。全收齊後 drain 會照 id 排序一次發。
        回傳輪詢期間讀到的包數。
        """
        t0 = time.time()
        read_n = 0
        while True:
            try:
                pending[:] = [t for t in pending if not t.done()]
            except Exception:
                break
            if not pending:
                break
            if time.time() - t0 > timeout:
                for t in pending:
                    try:
                        t.cancel()
                    except Exception:
                        pass
                break
            try:
                async with asyncio.timeout(0.5):
                    async for resp in session.receive():
                        read_n += 1
                        try:
                            if heard_out is not None:
                                c = getattr(resp, "server_content", None)
                                if c:
                                    mt = getattr(c, "model_turn", None)
                                    if mt:
                                        for p in getattr(mt, "parts", []) or []:
                                            if getattr(p, "text", ""):
                                                heard_out[1] += p.text
                                    it = getattr(c, "input_transcription", None)
                                    if it and getattr(it, "text", ""):
                                        heard_out[0] += it.text
                            if getattr(resp, "tool_call", None) and on_tool:
                                fcs2 = list(getattr(resp.tool_call, "function_calls", []) or [])
                                if fcs2:
                                    on_tool(fcs2)
                        except Exception:
                            pass
                        break
            except asyncio.TimeoutError:
                pass
            except Exception:
                break
            # 非阻塞推進：只等 0.2s 就回頭短讀，絕不死等
            try:
                await asyncio.wait(list(pending), timeout=0.2)
            except Exception:
                pass
            try:
                await drain()
            except Exception:
                pass
        try:
            await drain()
        except Exception:
            pass
        return read_n

    async def _pump_loop(self):
        """常駐接收泵：整條 session 只有這裡調 receive()；輪次收齊後分派給等待者或下游直說。

        收發分離（治 WebSocket 1011 工具卡住 socket）：
        - tool_call 到手立刻開 background task 跑 dispatch，pump 立刻 continue 繼續讀，
          工具跑 5~15 秒也不卡 socket 讀取，server ping 照常被 SDK 回應。
        - dispatch 跑完只 q.put（不碰 socket 寫），pump 每圈 drain。
        - 同輪多工具順序保證：drain 把 queue 內全部 batch 合併→照 FunctionResponse.id
          排序→去重→一次 send_tool_response。
        - turn_complete 後若還有未完成的 dispatch，用短輪詢邊讀邊等
          （_settle_tools_keep_reading），絕不 gather 死等卡住讀取。
        """
        core = get_core()
        log = getattr(core, "log_print", print)

        # 待發佇列：dispatch background tasks 把結果推入這裡，pump 統一送出
        send_queue: asyncio.Queue = asyncio.Queue()

        async def _drain_send_queue() -> bool:
            """把 send_queue 裡本輪全部 FunctionResponse 按 id 收齊，一次送出。"""
            batches: list = []
            while not send_queue.empty():
                try:
                    fresps = send_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                except Exception:
                    break
                if fresps:
                    batches.append(fresps)
            if not batches:
                return False
            try:
                await self._session.send_tool_response(
                    function_responses=self._sorted_unique_responses(batches))
                return True
            except Exception:
                return False

        try:
            while self._session is not None:
                heard, out = "", ""
                turn_done = False
                got_any = False
                # 本輪所有 dispatch background tasks，收齊才一次發
                pending_dispatches: list[asyncio.Task] = []
                detector = StreamingSentenceDetector(min_chars=6)
                try:
                    async with asyncio.timeout(600):
                        async for resp in self._session.receive():
                            got_any = True

                            # ★ 每圈先把已算好的 FunctionResponse 收齊發出（不 await 新工作）
                            await _drain_send_queue()

                            if getattr(resp, "tool_call", None):
                                fcs = list(getattr(resp.tool_call, "function_calls", []) or [])

                                # ★ 不 await，開 background task；pump 立刻回去讀下一包
                                self._new_bg_dispatch(core, fcs, send_queue,
                                                      pending_dispatches)
                                continue

                            c = getattr(resp, "server_content", None)
                            if c:
                                it = getattr(c, "input_transcription", None)
                                if it and getattr(it, "text", ""):
                                    heard += to_traditional(it.text)
                                new_text = ""
                                ot = getattr(c, "output_transcription", None)
                                if ot and getattr(ot, "text", ""):
                                    out += ot.text
                                    new_text += ot.text
                                mt = getattr(c, "model_turn", None)
                                if mt:
                                    for p in getattr(mt, "parts", []) or []:
                                        if getattr(p, "text", ""):
                                            out += p.text
                                            new_text += p.text

                                # 🌊 流式分句偵測 ➔ 搶先推動顯卡 TTS 推理
                                if new_text:
                                    for seg in detector.feed(new_text):
                                        asyncio.create_task(_presynth_streaming_sentence(core, seg))

                                if getattr(c, "generation_complete", False):
                                    rem = detector.flush()
                                    if rem:
                                        asyncio.create_task(_presynth_streaming_sentence(core, rem))

                                if getattr(c, "turn_complete", False):
                                    rem = detector.flush()
                                    if rem:
                                        asyncio.create_task(_presynth_streaming_sentence(core, rem))
                                    # ★ 還有未完成的 dispatch：短輪詢邊讀邊等，絕不 gather 死等。
                                    # 讀 socket 不中斷 → server ping 照常回 → 不再 1011。
                                    # 輪詢讀到的 heard/out 併回本輪；新 tool_call 照樣丟 background。
                                    pending_live = [t for t in pending_dispatches if not t.done()]
                                    if pending_live:
                                        heard_buf = [heard, out]

                                        def _on_late_tool(fcs2: list):
                                            self._new_bg_dispatch(core, fcs2, send_queue,
                                                                  pending_dispatches)

                                        await self._settle_tools_keep_reading(
                                            self._session, pending_dispatches,
                                            send_queue, _drain_send_queue,
                                            _on_late_tool, heard_buf, timeout=60.0)
                                        heard, out = heard_buf[0], heard_buf[1]
                                        # 工具回覆已照 id 排序一次送出，server 還會再回 post-tool 包
                                        # → 繼續收，不在本包 turn_done
                                        continue
                                    turn_done = True
                                    break
                except TimeoutError:
                    continue  # 閒置，繼續聽
                except Exception as e:
                    try:
                        log(f"🔁 [AgentLoop 收發異常] {type(e).__name__}: {str(e)[:120]}")
                    except Exception:
                        pass
                    # 取消未完成的 dispatch tasks，避免殭屍
                    for t in pending_dispatches:
                        try:
                            t.cancel()
                        except Exception:
                            pass
                    # 清空 send_queue，避免殘留 FunctionResponse 污染下一個 session
                    while not send_queue.empty():
                        try:
                            send_queue.get_nowait()
                        except Exception:
                            break
                    await self.rotate()
                    self._fail_pending()
                    break
                if not got_any:
                    await asyncio.sleep(0.2)
                    continue
                if not turn_done:
                    continue
                heard, out = heard.strip(), out.strip()
                self._note_turn(heard, out)
                total_chars = sum(len(t) for _, t in self.transcript)
                fut = self._pending
                self._pending = None
                if fut and not fut.done():
                    try:
                        fut.set_result((heard, out))
                    except Exception:
                        pass
                elif out or heard:
                    ds = self._downstream
                    if ds:
                        asyncio.create_task(self._speak_stream_turn(ds[0], ds[1], heard, out))
                if self.turns >= MAX_TURNS_PER_SESSION or total_chars > MAX_TRANSCRIPT_CHARS:
                    # 清空 send_queue，避免殘留 FunctionResponse 污染下一個 session
                    while not send_queue.empty():
                        try:
                            send_queue.get_nowait()
                        except Exception:
                            break
                    await self.rotate()
                    self._fail_pending()
                    break
        finally:
            self._fail_pending()

    async def _speak_stream_turn(self, vts, input_queue, heard: str, out: str):
        """串流模式無人等待的輪次：直接下游說話。"""
        core = get_core()
        log = getattr(core, "log_print", print)
        try:
            if not out or "[SILENCE]" in out.upper() or "[SKIP]" in out.upper():
                if heard:
                    try:
                        core.append_to_unified_memory(
                            speaker="老爸", target="7L", content=heard,
                            role="user", source="mic")
                    except Exception:
                        pass
                return
            await _speak_dad_reply(core, log, vts, input_queue, heard or "[語音輸入]", out, heard or "[語音輸入]")
        except Exception as e:
            try:
                log(f"⚠️ [AgentLoop 串流說話異常]: {e}")
            except Exception:
                pass

    async def _ensure(self):
        if self._session is not None:
            return True
        core = get_core()
        try:
            from google.genai import types as _types
            import google.genai as _genai
        except Exception:
            return False
        try:
            keys_fn = getattr(core, "get_dynamic_live_key_candidates", None)
            base_keys = getattr(core, "KEYS_AUDIENCE_LIVE", None) or getattr(core, "GEMINI_KEYS", [])
            if not base_keys:
                try:
                    import core.llm_engine as _le
                    base_keys = _le.KEYS_AUDIENCE_LIVE or _le.GEMINI_KEYS
                except Exception:
                    pass
            candidates = keys_fn(base_keys) if callable(keys_fn) else list(base_keys)
        except Exception:
            return False
        for g_key in (candidates[:4] if candidates else []):
            for live_model in (self._models or [LIVE_MODEL]):
                try:
                    client = _genai.Client(api_key=g_key)
                    tools = _build_live_tools(core) or []
                    if self._extra_tools:
                        tools = list(tools) + list(self._extra_tools)
                    kwargs = dict(
                        response_modalities=[_types.Modality.AUDIO],
                        output_audio_transcription=_types.AudioTranscriptionConfig(),
                        system_instruction=_types.Content(
                            parts=[_types.Part(text=self._persona)]),
                    )
                    if tools:
                        kwargs["tools"] = tools
                    cfg = _types.LiveConnectConfig(**kwargs)
                    mgr = client.aio.live.connect(model=live_model, config=cfg)
                    self._session = await mgr.__aenter__()
                    self._connect = mgr
                    self.turns = 0
                    self.live_model_used = live_model
                    # 🔊 音訊包相容探測（SDK 版本各異：AudioBlob 新名 / Blob 舊名；audio_stream_end 支援度）
                    try:
                        self._blob_cls = getattr(_types, "AudioBlob", None) or getattr(_types, "Blob", None)
                    except Exception:
                        self._blob_cls = None
                    try:
                        import inspect as _insp
                        self._end_kw = "audio_stream_end" in _insp.signature(self._session.send_realtime_input).parameters
                    except Exception:
                        self._end_kw = True
                    try:
                        _blob_name = getattr(self._blob_cls, "__name__", "?")
                        core.log_print(f"🔁 [AgentLoop] Live session 已連線：{live_model}（常駐迴路啟動，音訊包={_blob_name}，掛電話信號={self._end_kw}）")
                    except Exception:
                        pass
                    return True
                except Exception:
                    try:
                        if self._session is None and self._connect is not None:
                            await self._connect.__aexit__(None, None, None)
                    except Exception:
                        pass
                    self._session = None
                    self._connect = None
                    continue
        return False

    async def _summarize_and_reset(self):
        """STAGE3: transcript -> 3-line summary. TEXT CHORE Groq-first, Gemini fallback."""
        core = get_core()
        summary = ""
        if self.transcript:
            convo = "\n".join(
                f"{'AUD' if r == 'user' else '7L'}:{t[:120]}"
                for r, t in self.transcript[-20:])
            try:
                from services import text_chores as _tc
                summary, src = await _tc.summarize_transcript(convo)
                if summary:
                    core.log_print(f"[AgentLoop] summary via {src}: {summary[:60]}")
            except Exception:
                summary = ""
        if summary:
            self.context_summary = summary
            try:
                core.append_to_unified_memory(
                    speaker="7L", target="live", content=f"[prev-life] {summary}",
                    role="assistant", source="agent_loop")
            except Exception:
                pass
        else:
            try:
                tail = self.transcript[-4:] if self.transcript else []
                if tail:
                    self.context_summary = "/".join(
                        f"{'AUD' if r == 'user' else '7L'}:{t[:60]}" for r, t in tail)
                    core.log_print("[AgentLoop] summary failed, keep raw tail")
            except Exception:
                pass
        self.transcript = []
        self.turns = 0
        try:
            if self._connect:
                await self._connect.__aexit__(None, None, None)
        except Exception:
            pass
        self._session = None
        self._connect = None

    async def rotate(self):
        used = self.turns
        try:
            await self._summarize_and_reset()
        except Exception:
            self._session = None
            self._connect = None
        core = get_core()
        try:
            core.log_print(f"🔁 [AgentLoop] session 轉世（已用 {used} 輪）")
        except Exception:
            pass

    async def _dispatch_tool_calls(self, core, function_calls):
        """階段 2：Live 工具調用 → 主腦 execute_tool_dispatch → 回 FunctionResponse。
        search 同 query 120 秒內只查一次（命中回緩存，治 eduroam 連刷）。"""
        try:
            from google.genai import types as _types
        except Exception:
            return []
        responses = []
        dispatcher = getattr(core, "execute_tool_dispatch", None)
        for fc in function_calls or []:
            name = getattr(fc, "name", "") or ""
            args = getattr(fc, "args", {}) or {}
            fid = getattr(fc, "id", "") or name
            try:
                core.log_print(f"🔁 [AgentLoop 調用工具] {name}({args})")
            except Exception:
                pass
            try:
                if name == "deep_think":
                    res = await _deep_think((args or {}).get("query", ""))
                elif name == "search_google":
                    q = str((args or {}).get("query", "")).strip()
                    hit = _search_cache_get(q)
                    if hit is not None:
                        try:
                            core.log_print(f"🔁 [AgentLoop 搜尋命中緩存] {q[:30]}")
                        except Exception:
                            pass
                        res = hit
                    elif callable(dispatcher):
                        audience = getattr(self, "_audience", "audience")
                        res = await dispatcher(name, dict(args),
                                               caller_target=audience,
                                               caller_user=("直播觀眾" if audience == "audience" else "老爸"))
                        try:
                            who = "大家" if audience == "audience" else "老爸"
                            res = await core.summarize_search_to_speech(q, res, user_role_name=who)
                        except Exception:
                            pass
                        _search_cache_put(q, res)
                    else:
                        res = "工具執行器未就緒"
                elif callable(dispatcher):
                    audience = getattr(self, "_audience", "audience")
                    res = await dispatcher(name, dict(args),
                                           caller_target=audience,
                                           caller_user=("直播觀眾" if audience == "audience" else "老爸"))
            except Exception as e:
                res = f"執行異常：{e}"
            try:
                responses.append(_types.FunctionResponse(
                    id=fid, name=name, response={"result": str(res)[:1500]}))
            except Exception:
                pass
        return responses

    async def _exchange(self, core, send_fn, timeout):
        """ONE-ROUND SEND/RECV: send input, multi-round tools, return (heard, spoken).

        RECV-DISPATCH SPLIT (fix WS-1011 tool-stuck socket):
        - tool_call opens background task, async-for keeps reading.
        - dispatch only q.put; drain merges batches, sorts by id, dedups, sends once.
        - after turn_complete with pending dispatches, short-poll read while waiting.
        """
        out, heard = "", ""
        send_queue: asyncio.Queue = asyncio.Queue()

        async def _drain_send_queue() -> bool:
            batches: list = []
            while not send_queue.empty():
                try:
                    fresps = send_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                except Exception:
                    break
                if fresps:
                    batches.append(fresps)
            if not batches:
                return False
            try:
                await self._session.send_tool_response(
                    function_responses=self._sorted_unique_responses(batches))
                return True
            except Exception:
                return False

        pending_dispatches: list[asyncio.Task] = []
        detector = StreamingSentenceDetector(min_chars=6)
        try:
            async with asyncio.timeout(timeout):
                await send_fn(self._session)
                while True:
                    turn_done = False
                    async for resp in self._session.receive():
                        # ★ 每圈先發已算好的 FunctionResponse
                        await _drain_send_queue()

                        if getattr(resp, "tool_call", None):
                            fcs = list(getattr(resp.tool_call, "function_calls", []) or [])

                            # background task; async-for keeps reading, never blocks socket
                            self._new_bg_dispatch(core, fcs, send_queue,
                                                  pending_dispatches)
                            continue

                        c = getattr(resp, "server_content", None)
                        if c:
                            it = getattr(c, "input_transcription", None)
                            if it and getattr(it, "text", ""):
                                heard += to_traditional(it.text)
                            new_text = ""
                            ot = getattr(c, "output_transcription", None)
                            if ot and getattr(ot, "text", ""):
                                out += ot.text
                                new_text += ot.text
                            mt = getattr(c, "model_turn", None)
                            if mt:
                                for p in getattr(mt, "parts", []) or []:
                                    if getattr(p, "text", ""):
                                        out += p.text
                                        new_text += p.text

                            # 🌊 流式分句偵測 ➔ 搶先推動顯卡 TTS 推理
                            if new_text:
                                for seg in detector.feed(new_text):
                                    asyncio.create_task(_presynth_streaming_sentence(core, seg))

                            if getattr(c, "generation_complete", False):
                                rem = detector.flush()
                                if rem:
                                    asyncio.create_task(_presynth_streaming_sentence(core, rem))

                            if getattr(c, "turn_complete", False):
                                rem = detector.flush()
                                if rem:
                                    asyncio.create_task(_presynth_streaming_sentence(core, rem))
                                # pending dispatches: short-poll read while waiting, never gather-block.
                                pending_live = [x for x in pending_dispatches if not x.done()]
                                if pending_live:
                                    heard_buf = [heard, out]
                                    def _on_late_tool(fcs2: list):
                                        self._new_bg_dispatch(core, fcs2, send_queue, pending_dispatches)
                                    await self._settle_tools_keep_reading(
                                        self._session, pending_dispatches,
                                        send_queue, _drain_send_queue,
                                        _on_late_tool, heard_buf, timeout=60.0)
                                    heard, out = heard_buf[0], heard_buf[1]
                                    continue
                                turn_done = True
                                break
                    if turn_done:
                        break
            return heard.strip(), out.strip()
        except Exception as e:
            for t in pending_dispatches:
                try:
                    t.cancel()
                except Exception:
                    pass
            try:
                core = get_core()
                core.log_print(f"🔁 [AgentLoop 收發異常] {type(e).__name__}: {str(e)[:120]}")
            except Exception:
                pass
            await self.rotate()
            return "", ""

    async def _request_turn(self, send_fn, wait):
        """pump 模式送輪次：佔槽位 → 送 → 等 pump 分派結果。"""
        core = get_core()
        t0 = time.time()
        while self._pending and not self._pending.done():
            if time.time() - t0 > min(wait, 30.0):
                return "", ""
            await asyncio.sleep(0.3)
        if self._session is None:
            return "", ""
        try:
            loop = asyncio.get_running_loop()
        except Exception:
            return "", ""
        fut = loop.create_future()
        self._pending = fut
        try:
            await send_fn(self._session)
        except Exception:
            if self._pending is fut:
                self._pending = None
            return "", ""
        try:
            return await asyncio.wait_for(fut, timeout=wait)
        except Exception:
            if self._pending is fut:
                self._pending = None
            return "", ""

    def _pump_alive(self) -> bool:
        try:
            return bool(self._pump_task and not self._pump_task.done())
        except Exception:
            return False

    async def chat(self, text: str, timeout: float = 0) -> str:
        """送一句、收一輪（含工具多回合），回最終口語。空字串=失敗/靜默。
        pump 常駐時走 future 分派，否則走舊 _exchange 直收（觀眾 session 維持舊路）。"""
        if not text or not text.strip():
            return ""
        core = get_core()
        if self.turns >= MAX_TURNS_PER_SESSION:
            await self.rotate()
        if not await self._ensure():
            return ""
        wait = timeout or self._timeout or RECEIVE_TIMEOUT
        payload = text.strip()
        if self.context_summary:
            payload = f"【前情提要】{self.context_summary}\n{text.strip()}"
            self.context_summary = ""

        async def _send_text(sess):
            try:
                await sess.send_client_content(
                    turns=[{"role": "user", "parts": [{"text": payload}]}],
                    turn_complete=True
                )
            except Exception:
                await sess.send_realtime_input(text=payload)

        if self._pump_alive():
            _, out = await self._request_turn(_send_text, wait)
            return out or ""
        async with self._chat_lock:
            _, out = await self._exchange(core, _send_text, wait)
        if not out:
            return ""
        self.turns += 1
        self.transcript.append(("user", text.strip()[:200]))
        self.transcript.append(("model", out[:200]))
        if len(self.transcript) > 40:
            self.transcript = self.transcript[-40:]
        total_chars = sum(len(t) for _, t in self.transcript)
        if total_chars > MAX_TRANSCRIPT_CHARS:
            await self.rotate()
        return to_traditional(out)

    async def chat_audio(self, pcm16k: bytes, timeout: float = 0):
        """麥克風直灌：送 16k PCM，session 原生轉錄＋理解。回 (聽到的, 口語)。"""
        core = get_core()
        if not pcm16k or len(pcm16k) < 3200:
            return "", ""
        if self.turns >= MAX_TURNS_PER_SESSION:
            await self.rotate()
        if not await self._ensure():
            return "", ""
        wait = timeout or self._timeout or RECEIVE_TIMEOUT
        blob_cls = getattr(self, "_blob_cls", None)
        if blob_cls is None:
            try:
                from google.genai import types as _t2
                blob_cls = getattr(_t2, "AudioBlob", None) or getattr(_t2, "Blob", None)
            except Exception:
                blob_cls = None
        if blob_cls is None:
            try:
                core = get_core()
                core.log_print("👂 [AgentLoop 直聽組包失敗] SDK 無 AudioBlob/Blob")
            except Exception:
                pass
            return "", ""
        end_kw = getattr(self, "_end_kw", True)
        try:
            blob = blob_cls(data=pcm16k, mime_type="audio/pcm;rate=16000")
        except Exception as e:
            try:
                core = get_core()
                core.log_print(f"👂 [AgentLoop 直聽組包失敗] {type(e).__name__}: {str(e)[:100]}")
            except Exception:
                pass
            return "", ""

        async def _send_audio(sess):
            screen_hint = _get_current_screen_hint(core)
            if screen_hint:
                try:
                    await sess.send_realtime_input(text=screen_hint)
                except Exception:
                    pass
            await sess.send_realtime_input(audio=blob)
            # 📞 說完掛電話：整段話一次送完，明確告知 server 話筒結束，否則 VAD 空等回空輪
            if end_kw:
                try:
                    await sess.send_realtime_input(audio_stream_end=True)
                except Exception:
                    pass

        if self._pump_alive():
            return await self._request_turn(_send_audio, wait)
        async with self._chat_lock:
            heard, out = await self._exchange(core, _send_audio, wait)
        if not out and not heard:
            return "", ""
        self.turns += 1
        self.transcript.append(("user", (heard or "[語音]")[:200]))
        if out:
            self.transcript.append(("model", out[:200]))
        if len(self.transcript) > 40:
            self.transcript = self.transcript[-40:]
        total_chars = sum(len(t) for _, t in self.transcript)
        if total_chars > MAX_TRANSCRIPT_CHARS:
            await self.rotate()
        return to_traditional(heard), to_traditional(out)


_SESSION: AgentSession | None = None


def get_session() -> AgentSession:
    global _SESSION
    if _SESSION is None:
        _SESSION = AgentSession()
        _SESSION._audience = "audience"
    return _SESSION


_DAD_SESSION: AgentSession | None = None


def get_dad_session() -> AgentSession:
    """爸爸專屬常駐 session：前門快答＋deep_think 旗艦代打。"""
    global _DAD_SESSION
    if _DAD_SESSION is None:
        tools = []
        try:
            dt = _build_deep_think_tool()
            if dt is not None:
                tools.append(dt)
        except Exception:
            pass
        _DAD_SESSION = AgentSession(
            persona=AGENT_DAD_SYSTEM_PROMPT,
            extra_tools=tools, timeout=DEEP_THINK_TIMEOUT,
            model_candidates=DAD_LIVE_MODEL_CANDIDATES)
        _DAD_SESSION._audience = "dad"
    return _DAD_SESSION


def interrupt(reason: str = "dad barge-in"):
    """階段 4：老爸開口 → 秒停當前語音，把麥讓出來（隊列保留，爸爸回覆照常排入）。"""
    core = get_core()
    try:
        task = getattr(core, "CURRENT_PLAYING_VOICE_TASK", None)
        if task and not task.done():
            task.cancel()
            try:
                core.log_print(f"🔁 [AgentLoop 打斷] 已秒停當前語音（{reason}）")
            except Exception:
                pass
            return True
    except Exception:
        pass
    return False


async def handle_tiktok_message(vts, input_queue, id_display: str,
                                unique_id: str, content: str, source: str = "tiktok") -> bool:
    """TikTok 閒聊走常駐 session；回 True=已處理，False=請 dispatcher 走舊看板。"""
    core = get_core()
    log = getattr(core, "log_print", print)
    # 忙時丟棄：上一輪還在想/播，閒聊不排隊（記一筆已讀即可，避免 session 互踩＋回覆大塞車）
    try:
        if get_session()._chat_lock.locked():
            try:
                core.append_to_unified_memory(
                    speaker=f"TikTok 觀眾「{id_display}」", target="老爸/直播間",
                    content=f"{content}（併入上一輪處理中）",
                    role="user", source=source)
            except Exception:
                pass
            log(f"🔁 [AgentLoop 忙碌吸收] 上一輪未完，閒聊併單略過: {content[:30]}")
            return True
    except Exception:
        pass
    try:
        try:
            low = (content or "").lower()
            to_7l = any(tag in low for tag in ["7l", "@7l", "小7", "7寶", "草莓"])
            core.append_to_unified_memory(
                speaker=f"TikTok 觀眾「{id_display}」",
                target="7L" if to_7l else "老爸/直播間",
                content=content, role="user", source=source)
        except Exception:
            pass

        reply = await get_session().chat(f"【{id_display}】：{content}")
        if not reply:
            return False
        if "[PASS]" in reply.upper() or "[SILENCE]" in reply.upper():
            try:
                core.append_to_unified_memory(
                    speaker="7L", target=f"觀眾「{id_display}」",
                    content="[PASS 靜默略過]", role="assistant", source="agent_loop")
            except Exception:
                pass
            return True

        try:
            from core.prompts import TextCleanEngine
            clean_reply = TextCleanEngine.remove_system_hints(reply)
        except Exception:
            clean_reply = reply
        clean_reply = re.sub(r'^(?:回應|回覆|說道|回答)[：:\s]+', '', clean_reply, flags=re.IGNORECASE).strip()

        exec_actions = getattr(core, "execute_actions", None)
        spoken = await exec_actions(vts, clean_reply, input_queue,
                                    user_input_ctx=content,
                                    caller_target="audience",
                                    caller_user=id_display) if callable(exec_actions) else clean_reply
        clean_spoken = (spoken or "").strip(" *'\"-\n\r")
        if clean_spoken and not clean_spoken[-1] in "。！？！.!?~～":
            clean_spoken = clean_spoken.rstrip("，,、；;…") + "！"
        if not clean_spoken:
            return True

        try:
            await asyncio.to_thread(core.update_subtitle, clean_spoken)
        except Exception:
            pass
        try:
            core.record_bot_message(clean_spoken)
        except Exception:
            pass
        log(f"💬 7L (AgentLoop 回應 {id_display}): {clean_spoken} (🔁 session #{get_session().turns})")
        try:
            await core.speech_queue.put({
                "text": clean_spoken, "target": "audience",
                "raw_text": clean_reply, "model": "agent-loop-live"})
        except Exception:
            pass
        try:
            core.append_to_unified_memory(
                speaker="7L", target=f"觀眾「{id_display}」",
                content=clean_spoken, role="assistant",
                source="tts", model="agent-loop-live")
        except Exception:
            pass
        try:
            fresh = await core.fetch_from_long_term_memory("tiktok_live_stream")
            fresh.append({"role": "user", "content": f"【TikTok 觀眾 {id_display}】：{content}"})
            fresh.append({"role": "assistant", "content": clean_spoken})
            asyncio.create_task(core.save_to_long_term_memory("tiktok_live_stream", fresh))
        except Exception:
            pass
        return True
    except Exception as e:
        try:
            log(f"⚠️ [AgentLoop 處理異常，回退看板]: {e}")
        except Exception:
            pass
        return False


async def _speak_dad_reply(core, log, vts, input_queue, user_mem_text: str,
                           reply: str, user_input_ctx: str) -> bool:
    """爸爸下游共用：表情執行 → 字幕 → 語音排隊 → 雙記憶庫。回是否有開口。
    user_mem_text: 寫入記憶的「老爸說了什麼」（session 聽到的為準）。"""
    try:
        from core.prompts import TextCleanEngine
        bot_reply = TextCleanEngine.remove_system_hints(reply)
    except Exception:
        bot_reply = reply
    try:
        prof = await core.get_user_profile()
        custom_name = (prof or {}).get("custom_name", "老爸")
    except Exception:
        custom_name = "老爸"

    exec_actions = getattr(core, "execute_actions", None)
    spoken = await exec_actions(vts, bot_reply, input_queue,
                                user_input_ctx=user_input_ctx,
                                caller_target="dad",
                                caller_user=custom_name) if callable(exec_actions) else bot_reply
    clean_spoken = (spoken or "").strip(" *'\"-.,!?。，！？\n\r")
    if not clean_spoken:
        # 🛡️ 防啞口兜底：若老爸問「聽得到嗎」或打招呼，而大腦只吐出表情標籤無台詞，主動補上親切口語
        low_in = (user_mem_text or "").lower()
        if any(k in low_in for k in ["聽得到", "听得到", "在嗎", "在吗", "哈囉", "hello", "hi", "有聽到"]):
            clean_spoken = "老爸，我聽得到喔！很清楚～"
            bot_reply = f"{clean_spoken} {reply}"
        else:
            return False
    try:
        await asyncio.to_thread(core.update_subtitle, clean_spoken)
    except Exception:
        pass
    try:
        core.record_bot_message(clean_spoken)
    except Exception:
        pass
    try:
        sess = get_dad_session()
        tag = f"{sess.live_model_used or 'live'} #{sess.turns}"
    except Exception:
        tag = "live"
    log(f"💬 7L (AgentLoop 爸爸回覆): {clean_spoken} (🔁 {tag})")
    try:
        await core.speech_queue.put({
            "text": clean_spoken, "target": "dad",
            "raw_text": bot_reply, "model": "agent-loop-dad"})
    except Exception:
        pass
    try:
        if user_mem_text:
            core.append_to_unified_memory(
                speaker="老爸", target="7L", content=user_mem_text,
                role="user", source="mic")
        core.append_to_unified_memory(
            speaker="7L", target=custom_name, content=clean_spoken,
            role="assistant", source="tts", model="agent-loop-dad")
    except Exception:
        pass
    try:
        ch = getattr(core, "DEFAULT_CHANNEL_ID", "dad")
        fresh = await core.fetch_from_long_term_memory(ch)
        fresh.append({"role": "user", "content": user_mem_text or "[語音輸入]"})
        fresh.append({"role": "assistant", "content": clean_spoken})
        asyncio.create_task(core.save_to_long_term_memory(ch, fresh))
    except Exception:
        pass
    try:
        core.last_interaction_time = time.time()
    except Exception:
        pass
    return True


async def handle_dad_message(vts, input_queue, user_input: str, source: str = "mic") -> bool:
    """整台 agent 化：爸爸輸入走專屬常駐 session（快答直回＋deep_think 旗艦代打）。
    回 True=已處理（含靜默），False=請回舊 process_chat_message 全流程。"""
    core = get_core()
    log = getattr(core, "log_print", print)
    my_turn_ok = False
    try:
        try:
            core.current_ai_state = "THINKING"
        except Exception:
            pass
        try:
            core.touch_interaction()
        except Exception:
            pass

        prefix = "【老爸開口語音】" if source == "mic" else "【老爸打字】"
        screen_hint = _get_current_screen_hint(core)
        reply = await get_dad_session().chat(
            f"{screen_hint}{prefix}：{user_input}", timeout=DEEP_THINK_TIMEOUT)
        if not reply:
            return False
        if "[SILENCE]" in reply.upper() or "[SKIP]" in reply.upper():
            my_turn_ok = True
            return True

        await _speak_dad_reply(core, log, vts, input_queue, user_input, reply, user_input)
        try:
            core.last_interaction_time = time.time()
        except Exception:
            pass
        my_turn_ok = True
        return True
    except Exception as e:
        try:
            log(f"⚠️ [AgentLoop 爸爸處理異常，回退舊流程]: {e}")
        except Exception:
            pass
        return False
    finally:
        try:
            rtm = getattr(core, "realtime_task_mgr", None)
            if rtm and my_turn_ok:
                try:
                    rtm.finish_dad_task()
                except Exception:
                    pass
                try:
                    rtm.mark_dad_input_read()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            mark_board = getattr(core, "mark_streamer_mind_board_as_read", None)
            if mark_board and my_turn_ok:
                mark_board(unique_id="dad", content=user_input)
        except Exception:
            pass
        try:
            if getattr(core, "current_ai_state", "") == "THINKING":
                import services.piano_engine as _pe
                core.current_ai_state = "PIANO" if _pe.is_piano_active else "IDLE"
        except Exception:
            try:
                core.current_ai_state = "IDLE"
            except Exception:
                pass


async def handle_dad_audio(vts, input_queue, pcm16k: bytes, source: str = "mic") -> bool:
    """🎙️ 麥克風直灌：PCM 直送爸爸 session（原生轉錄＋理解，對話只跑一遍）。
    STT 只保留作關機安全網。回 True=已處理，False=走舊文字鏈。"""
    core = get_core()
    log = getattr(core, "log_print", print)
    if not pcm16k or len(pcm16k) < 3200:
        log(f"👂 [AgentLoop 直聽跳過] PCM過短({len(pcm16k) if pcm16k else 0}B) → 舊鏈")
        return False
    # ✂️ 靜音修剪＋25 秒封頂：VAD 常因環境音收不了口（整段 30 秒灌過去又慢又暈），
    # 留有人聲段＋尾部，server 轉錄更快更準
    try:
        import numpy as _np
        pcm_arr = _np.frombuffer(pcm16k, dtype=_np.int16).astype(_np.float32)
        frame = 320  # 20ms @16k
        nfr = max(1, len(pcm_arr) // frame)
        rms = _np.sqrt((_np.abs(pcm_arr[:nfr * frame].reshape(nfr, frame).astype(_np.float64) ** 2)).mean(axis=1))
        voiced = rms > 400.0
        if voiced.any():
            first, last = int(_np.argmax(voiced)), nfr - 1 - int(_np.argmax(voiced[::-1]))
            first = max(0, first - 15)   # 前留 0.3s
            last = min(nfr - 1, last + 25)  # 後留 0.5s
            pcm_arr = pcm_arr[first * frame:(last + 1) * frame]
            max_bytes = 16000 * 2 * 25
            if len(pcm_arr) * 2 > max_bytes:
                pcm_arr = pcm_arr[-max_bytes // 2:]
            pcm16k = pcm_arr.astype(_np.int16).tobytes()
            log(f"👂 [AgentLoop 直聽修剪] 靜音切除後 ≈ {len(pcm16k) / 2 / 16000:.1f}s")
        if len(pcm16k) < 3200:
            log("👂 [AgentLoop 直聽跳過] 修剪後過短 → 舊鏈")
            return False
    except Exception as _e_trim:
        log(f"👂 [AgentLoop 直聽修剪失敗，用原音] {_e_trim}")
    # 🧾 自證 PCM：存檔供人耳驗證（16k 單聲道），若檔裡是正常語速人話 yet session 空回 → 轉向查 turn 完成信號
    try:
        import wave as _wv
        import io as _io
        secs = len(pcm16k) / 2 / 16000
        buf = _io.BytesIO()
        with _wv.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(pcm16k)
        dbg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "last_direct_audio.wav")
        with open(os.path.normpath(dbg_path), "wb") as f:
            f.write(buf.getvalue())
        log(f"👂 [AgentLoop 直聽送出] PCM {len(pcm16k)}B ≈ {secs:.1f}s → data/last_direct_audio.wav")
    except Exception as _e_dbg:
        log(f"👂 [AgentLoop 直聽存檔失敗] {_e_dbg}")
    try:
        try:
            core.current_ai_state = "THINKING"
        except Exception:
            pass
        try:
            core.touch_interaction()
        except Exception:
            pass

        heard, reply = await get_dad_session().chat_audio(
            pcm16k, timeout=DEEP_THINK_TIMEOUT)
        if not reply:
            log("👂 [AgentLoop 直聽無回音] session 空回 → 舊鏈接手")
            return False
        heard = to_traditional((heard or "").strip())
        reply = to_traditional((reply or "").strip())
        log(f"👂 [AgentLoop 直聽] session 聽到：{heard[:60] if heard else '(無轉錄)'} | 回覆：{reply[:60] if reply else '(空)'}")
        if "[SILENCE]" in reply.upper() or "[SKIP]" in reply.upper():
            try:
                core.append_to_unified_memory(
                    speaker="老爸", target="7L",
                    content=heard or "[語音]", role="user", source="mic")
            except Exception:
                pass
            try:
                core.last_interaction_time = time.time()
            except Exception:
                pass
            return True

        ok_spoken = await _speak_dad_reply(core, log, vts, input_queue, heard or "[語音輸入]",
                                           reply, heard or "[語音輸入]")
        if not ok_spoken:
            log(f"👂 [AgentLoop 直聽未開口] reply='{reply}' 無發音台詞 → 回退舊鏈處理")
            return False
        try:
            core.last_interaction_time = time.time()
        except Exception:
            pass
        return True
    except Exception as e:
        try:
            log(f"⚠️ [AgentLoop 直聽異常，回退舊鏈]: {e}")
        except Exception:
            pass
        return False
    finally:
        try:
            rtm = getattr(core, "realtime_task_mgr", None)
            if rtm:
                try:
                    rtm.finish_dad_task()
                except Exception:
                    pass
                try:
                    rtm.mark_dad_input_read()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            mark_board = getattr(core, "mark_streamer_mind_board_as_read", None)
            if mark_board:
                mark_board(unique_id="dad", content="")
        except Exception:
            pass
        try:
            if getattr(core, "current_ai_state", "") == "THINKING":
                core.current_ai_state = "IDLE"
        except Exception:
            pass
