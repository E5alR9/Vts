"""Groq-first text chores. Main brain / Live / vision / wav never touch this.

Thin wrapper over core.groq_router (round-robin keys, 429 cooldown,
model ladder auto-filter). Falls back to Gemini Flash-Lite, then local.
"""
import time
import re
import asyncio

try:
    from core.groq_router import groq_chat as _groq_chat
except Exception:
    _groq_chat = None

GROQ_CHORE_BUDGET = 12.0  # 單次雜活 Groq 總預算（含梯隊重試），超時直接降級 Gemini


async def groq_text(system, user, max_tokens=200, temperature=0.5, timeout=None):
    if _groq_chat is None:
        return "", ""
    try:
        resp = await asyncio.wait_for(
            _groq_chat(
                [{"role": "system", "content": system},
                 {"role": "user", "content": user}],
                max_tokens=max_tokens, temperature=temperature,
                timeout=min(timeout or 4.0, 6.0),
            ),
            timeout=timeout or GROQ_CHORE_BUDGET,
        )
    except Exception:
        return "", ""
    if not resp or not getattr(resp, "text", ""):
        return "", ""
    return resp.text.strip(), ("Groq/" + (getattr(resp, "model", "") or "?"))


def groq_key_count():
    try:
        from core import groq_router as _gr
        keys = _gr.GROQ_KEYS or _gr._load_keys()
        return len(keys)
    except Exception:
        return 0


async def gemini_lite_text(prompt, max_tokens=300, temperature=0.5, timeout=None):
    """Gemini 梯隊備援（lifetime 總預算封頂，503 快失敗自動換 key/模型）。回 (text, src)。"""
    import os
    budget = timeout or 10.0
    deadline = time.monotonic() + budget
    try:
        from google import genai
        from google.genai import types
    except Exception:
        return "", ""
    safety = None
    try:
        from core.llm_engine import UNRESTRICTED_SAFETY_SETTINGS as safety
    except Exception:
        safety = None
    raw = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or ""
    keys = []
    for k in re.split(r"[\s,;]+", raw):
        k = (k or "").strip()
        if k and len(k) < 150:
            keys.append(k)
    if not keys:
        return "", ""
    models = [
        "gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3-flash-preview",
        "gemini-3.6-flash", "gemini-3.5-flash",   # lite 全 503 時的保底梯隊
    ]
    for key in keys[:3]:
        try:
            client = genai.Client(api_key=key)
        except Exception:
            continue
        for m in models:
            remain = deadline - time.monotonic()
            if remain <= 1.0:
                return "", ""
            try:
                if safety:
                    cfg = types.GenerateContentConfig(
                        temperature=temperature, max_output_tokens=max_tokens,
                        safety_settings=safety)
                else:
                    cfg = types.GenerateContentConfig(
                        temperature=temperature, max_output_tokens=max_tokens)
                resp = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=m, contents=prompt, config=cfg),
                    timeout=min(4.0, remain))
                txt = (getattr(resp, "text", "") or "").strip()
                if txt:
                    return txt, ("Gemini/" + m.replace("gemini-", ""))
            except Exception:
                continue
    return "", ""


async def chore_text(system, user, max_tokens=300, temperature=0.4, timeout=6.0):
    """通用雜活：Groq 免費層優先 → Gemini Flash-Lite 備援。全失敗回 ("","")。"""
    t0 = time.time()
    ans, src = await groq_text(system, user, max_tokens=max_tokens,
                               temperature=temperature, timeout=timeout)
    ans = (ans or "").strip()
    if ans:
        return ans, ("%s/%.1fs" % (src, time.time() - t0))
    ans2, src2 = await gemini_lite_text((system or "") + "\n\n" + (user or ""),
                                        max_tokens=max_tokens,
                                        temperature=temperature,
                                        timeout=timeout)
    ans2 = (ans2 or "").strip()
    if ans2:
        return ans2, ("%s/%.1fs" % (src2, time.time() - t0))
    return "", ""



def _clean_speech(ans):
    ans = re.sub(r"\[[A-Z_]+(?::\s*[^\]]+)?\]", "", ans or "").strip()
    if not ans or ans.startswith("(") or len(ans) <= 5:
        return ""
    return ans


async def summarize_search_to_speech(query, search_raw, user_role_name="老爸"):
    if not search_raw or "搜尋無結果" in str(search_raw):
        return (f"{user_role_name}，我幫你查了一下，但目前網路上沒有找到相關的資料耶。", "local/empty")
    clean = re.sub(r"https?://\S+", "", search_raw)
    clean = re.sub(r"\s{2,}", " ", clean).strip()[:1500]
    system = ("妳是7L，正在直播中與" + str(user_role_name) +
              "對話。請以親切隨性口吻（1~2句短句，繁體中文）提煉搜尋重點回答，嚴禁照搬原文清單，嚴禁Emoji。")
    user = "查詢問題: " + str(query) + "\n搜尋內容: " + clean[:800]
    t0 = time.time()
    ans, src = await groq_text(system, user, max_tokens=120, temperature=0.7, timeout=6.0)
    ans = _clean_speech(ans)
    if ans:
        return ans, (src + ("/%.1fs" % (time.time() - t0)))
    prompt = ("請以招牌親切口吻，用1~3句短句（40~80字，繁體中文）直接對" + str(user_role_name) +
              "提煉以下情報重點：\n" + clean + "\n嚴禁照抄條列清單、網址或標題，嚴禁Emoji。")
    ans2, src2 = await gemini_lite_text(prompt, max_tokens=500, temperature=0.75, timeout=8.0)
    ans2 = _clean_speech(ans2)
    if ans2:
        return ans2, (src2 + ("/%.1fs" % (time.time() - t0)))
    # 本機提煉器（無 LLM 無金額，純字串截取，絕不傾倒條列與 URL）
    lines = [l.strip() for l in str(search_raw).split("\n") if l.strip()]
    snippets = []
    for l in lines:
        clean_l = re.sub(r"^[-\d.*#\s]+", "", l)
        if ":" in clean_l:
            clean_l = clean_l.split(":", 1)[1].strip()
        clean_l = re.sub(r"https?://\S+", "", clean_l).strip()
        if len(clean_l) > 15:
            snippets.append(clean_l)
        if len(snippets) >= 2:
            break
    if snippets:
        core_txt = "，".join(snippets)
        if len(core_txt) > 90:
            core_txt = core_txt[:85] + "等等"
        return (f"{user_role_name}，我幫你查到囉！大致上來說，{core_txt}。詳細內容我待會再幫你細看喔！",
                "local/extract")
    return (f"{user_role_name}，我剛剛幫你查了，但搜尋到的內容有點繁雜，我待會再仔細整理跟你說！",
            "local/empty")


async def summarize_transcript(convo):
    if not convo or not convo.strip():
        return "", ""
    system = "你是7L直播間的摘要助手（繁體中文）。把閒聊壓成3行以內的重點（誰說了什麼、答應了什麼、未了結什麼），嚴禁超過150字，只輸出摘要正文。"
    t0 = time.time()
    ans, src = await groq_text(system, convo[:3000], max_tokens=200, temperature=0.3)
    ans = (ans or "").strip()
    if ans:
        return ans, (src + ("/%.1fs" % (time.time() - t0)))
    prompt = ("把以下直播閒聊壓成3行以內的重點（誰說了什麼、答應了什麼、未了結什麼），"
              "嚴禁超過150字：\n" + convo[:3000])
    ans2, src2 = await gemini_lite_text(prompt, max_tokens=200, temperature=0.3)
    ans2 = (ans2 or "").strip()
    if ans2:
        return ans2, (src2 + ("/%.1fs" % (time.time() - t0)))
    return "", ""
