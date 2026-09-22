import os
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
from core.utils import log_print, sys_notify, get_current_time_string, get_unified_time_prompt, record_interaction_tick
from core.llm_engine import UNRESTRICTED_SAFETY_SETTINGS
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
                            config=types.GenerateContentConfig(
                                temperature=0.75,
                                max_output_tokens=500,
                                safety_settings=UNRESTRICTED_SAFETY_SETTINGS
                            )
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
                            config=types.GenerateContentConfig(
                                temperature=0.2,
                                safety_settings=UNRESTRICTED_SAFETY_SETTINGS
                            )
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
            config_kwargs = {
                "temperature": 0.85,
                "tools": active_tools,
                "safety_settings": UNRESTRICTED_SAFETY_SETTINGS
            }
            
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
                    if fn_name == "pe.stop_virtual_piano" and "open_virtual_piano" in call_names:
                        log_print(f"🛡️ [工具衝突過濾] 同回合同時包含 open_virtual_piano 與 pe.stop_virtual_piano，已自動過濾 pe.stop_virtual_piano！")
                        continue
                    log_print(f"🛠️ [大腦調用工具] {fn_name}({fn_args})")
                    tool_out = await tool_dispatcher(fn_name, fn_args, caller_target="dad", caller_user="老爸")
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

            # 7L 已有獨立背景即時心流協程，對話回覆不再包裹 [THOUGHT: ...]

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
                                config=types.GenerateContentConfig(
                                    temperature=0.85,
                                    safety_settings=UNRESTRICTED_SAFETY_SETTINGS
                                )
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
                elif "pe.play_virtual_piano" in tool_results_map:
                    piano_fc = next((fc for fc in response.function_calls if getattr(fc, 'name', '') == 'pe.play_virtual_piano'), None)
                    p_name = pe.clean_song_title_for_speech(getattr(piano_fc, 'args', {}).get('song_name', '')) if piano_fc else ''
                    if pe.is_piano_active and pe.current_piano_song_title:
                        extracted_text = f"[EXPRESSION: 星星眼] 老爸，沒問題！《{p_name or '這首'}》我先幫你排進清單，等現在這首彈完馬上幫你彈喔！"
                    else:
                        extracted_text = f"[EXPRESSION: 星星眼] 老爸，這就來為你彈《{p_name or '這首'}》！"
                elif "pe.compose_and_play_original_piano" in tool_results_map:
                    extracted_text = f"[EXPRESSION: 星星眼] 老爸，收到！我現在就現場為你創作一首原創鋼琴曲，聽聽看喔！"
                elif "pe.mashup_virtual_piano" in tool_results_map:
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
            # ⏳ 單通道內部超時
            log_print(f"⌛ [通道無回應] 通道 {target_id} ({g_model}) 超時未回傳 ➔ 釋放通道轉交備用金鑰")
            return None
        except Exception as e:
            if isinstance(e, (asyncio.TimeoutError, TimeoutError)) or "timeout" in type(e).__name__.lower():
                log_print(f"⌛ [通道無回應] 通道 {target_id} ({g_model}) 超時無回應 ➔ 釋放通道")
                return None
            err_str = str(e).lower()
            record_model_failure(g_model, err_str)
            if "503" in err_str or "unavailable" in err_str or "high demand" in err_str:
                log_print(f"⚠️ [伺服器超載 503] 通道 {target_id} ({g_model}): 官方模型高負載/忙碌中 ➔ 暫時冷卻 180s")
                lock_target(target_id, "503 high demand")
            elif "404" in err_str or "not_found" in err_str or "no longer available" in err_str:
                if 'DEAD_GEMINI_MODELS' in globals():
                    DEAD_GEMINI_MODELS.add(g_model)
                log_print(f"❌ [模型下架 404] 通道 {target_id} ({g_model}): 模型未開通或已下架 ➔ 封印至午夜")
                lock_entire_model(g_model, duration=get_seconds_until_pt_midnight(), reason="404 下架/未開通")
                lock_target(target_id, "404 not found")
            elif any(k in err_str for k in ["per day", "requests per day", "daily requests", "rpd", "tokens per day", "tpd"]):
                log_print(f"🛑 [今日額度用盡] 通道 {target_id} ({g_model}): 此 API Key 今日免費額度已滿 (RPD) ➔ 封印至 PT 午夜，自動切換下一把金鑰")
                lock_target(target_id, str(e))
            elif "429" in err_str or "rate limit" in err_str or "resource" in err_str or "quota" in err_str:
                log_print(f"⚠️ [頻率超限 429] 通道 {target_id} ({g_model}): 呼叫過於頻繁 (RPM/TPM) ➔ 短暫冷卻 60s")
                lock_target(target_id, str(e))
            elif "timeouterror" in err_str or "timeout" in err_str:
                log_print(f"⌛ [通道連線逾時] 通道 {target_id} ({g_model}) 連線中斷或逾時")
            else:
                clean_err = str(e).replace('\n', ' ').strip()[:70]
                display_err = clean_err if clean_err else type(e).__name__
                log_print(f"⚠️ [大腦異常/無回應] 通道 {target_id} ({g_model}): {display_err} ➔ 自動切換下一把金鑰")
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
            # 12 秒到期：日誌提示，原任務未逾時未報錯、仍在背景深度思考，依序輪流加開雙軌熱備搶答！
            running_names = [active_gemini_tasks[t][0] for t in active_gemini_tasks]
            log_print(f"⏱️ [思考中/尚未回應] 通道 {', '.join(running_names)} 仍在深度推理中 (未報錯無異常) ➔ 原請求不中斷繼續跑，加開新金鑰通道搶答！")

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

    time_prompt = get_unified_time_prompt()
    prompt = f"""{time_prompt}
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
                                max_output_tokens=500,
                                tools=GENAI_TOOLS,
                                safety_settings=UNRESTRICTED_SAFETY_SETTINGS
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
                            asyncio.create_task(tool_dispatcher(fn_name, fn_args, caller_target=fast_target, caller_user=fast_user))
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
        if pe.is_piano_active and pe.current_piano_song_title:
            current_playing_info = f"【🎹 妳目前正坐在鋼琴前彈奏《{pe.current_piano_song_title}》】！若觀眾問「這首？」、「這是什麼歌？」、「在彈什麼？」，請直接告訴他這首是《{pe.current_piano_song_title}》，絕對不要調用 list_piano_sheets 把全部曲庫唸出來！"
        else:
            current_playing_info = "【🎹 妳目前沒有在彈鋼琴】。"

        # 2. 準備 Live 專屬實況主 Instruction (100% 雲端 Firestore 動態加載人設 + 技術規則)
        cloud_kn = await get_cloud_knowledge()
        cloud_kn_prompt = PromptTemplateEngine.format_cloud_knowledge_prompt(cloud_kn, is_tiktok=True)
        ck_sec = f"\n{cloud_kn_prompt}\n" if cloud_kn_prompt else ""

        time_prompt = get_unified_time_prompt()
        sys_instruction = f"""{time_prompt}
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
- 若明確點歌，請調用 `pe.play_virtual_piano(song_name=歌名)`；若要求自創曲/即興彈琴，請調用 `pe.compose_and_play_original_piano`。
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

        prompt_user_input = f"【TikTok 直播觀眾 {id_display} 留言】：{audience_content}\n請結合 100 句記憶，以自然俐落的短句開口回應（1~2句，30字內，可隨興在句中自由切換 [EXPRESSION: ...] 表情）："

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
                                max_output_tokens=500,
                                tools=GENAI_PROACTIVE_TOOLS,
                                safety_settings=UNRESTRICTED_SAFETY_SETTINGS
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
                            t_res = await tool_dispatcher(fn_name, fn_args, caller_target="audience", caller_user=audience_user)
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
                            if fc_name == "pe.play_virtual_piano":
                                song_q = pe.clean_song_title_for_speech(fc_args.get("song_name", ""))
                                if pe.is_piano_active and pe.current_piano_song_title:
                                    clean_raw = f"[EXPRESSION: 星星眼] {target_audience_desc}，沒問題！《{song_q or '這首'}》我先幫你排進清單，等現在這首彈完馬上幫你彈喔！"
                                else:
                                    clean_raw = f"[EXPRESSION: 星星眼] {target_audience_desc}，好喔！這就為你彈《{song_q or '這首'}》！"
                                break
                            elif fc_name == "pe.compose_and_play_original_piano":
                                clean_raw = f"[EXPRESSION: 星星眼] {target_audience_desc}，沒問題！我現在就現場為你即興創作一首，聽聽看喔！"
                                break
                            elif fc_name == "pe.mashup_virtual_piano":
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
            record_interaction_tick()
            
            # 🌟 寫入全集中記憶中樞（確保所有大腦掌握 7L 最新發言）
            append_to_unified_memory(speaker="7L", target=f"觀眾「{target_audience_desc}」", content=clean_spoken, role="assistant", source="tts")
            
            # 寫入歷史 (獨立儲存於 tiktok_live_stream 頻道，不污染老爸的主對話記憶)
            fresh_hist = await fetch_from_long_term_memory_hook("tiktok_live_stream")
            fresh_hist.append({"role": "user", "content": f"【TikTok 觀眾 {id_display}】：{audience_content}"})
            fresh_hist.append({"role": "assistant", "content": clean_spoken})
            asyncio.create_task(save_to_long_term_memory("tiktok_live_stream", fresh_hist))
            
        realtime_task_mgr.finish_audience_task(audience_user)
        return True
    except Exception as e:
        log_print(f"⚠️ [觀眾 Live 管道異常]: {e}")
        realtime_task_mgr.finish_audience_task(audience_user)
        return False