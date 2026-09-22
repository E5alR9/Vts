import os
import sys
import time
import re
import asyncio
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

sys.path.insert(0, os.getcwd())
load_dotenv()
from google import genai
from google.genai import types
from core.memory import get_cloud_knowledge

gemini_keys = [k.strip() for k in re.split(r'[\s,;]+', os.getenv('GEMINI_API_KEYS') or os.getenv('GEMINI_API_KEY') or '') if k.strip()]

async def main():
    print("🚀 正在測試乾淨人設（100% 依循雲端知識庫）的 7L 雜念心流...")
    cloud_kn = await get_cloud_knowledge()
    persona_desc = ""
    if cloud_kn:
        persona_desc = cloud_kn.get("persona_core") or cloud_kn.get("conversation_style") or ""
        if persona_desc:
            persona_desc = persona_desc.strip()[:100]

    persona_ctx = f"【7L 性格人設】：{persona_desc}\n" if persona_desc else ""
    curr_app = "Antigravity IDE"
    curr_music = "cool smol breakcore"

    mind_prompt = (
        f"妳是 7L。\n"
        f"{persona_ctx}"
        f"情境：老爸正在專注（當前視窗：{curr_app[:30]}，背景音樂：{curr_music[:30]}）。\n"
        f"請完全依循妳的人設與心情，在腦海深處自然浮現一句極短的私密小雜念或隨性心聲（10~25字以內）。\n"
        f"【規範】：\n"
        f"- 純粹為內心深處自然產生的碎片雜念，嚴禁回報「老爸在看什麼、畫面無動態、保持陪伴」等機械式打卡工作報告。\n"
        f"只回傳這一句私密心聲（不帶任何標籤括號）："
    )

    for idx, key in enumerate(gemini_keys[12:15]):
        client = genai.Client(api_key=key)
        t0 = time.time()
        try:
            resp = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model='gemini-3.5-flash-lite',
                    contents=mind_prompt,
                    config=types.GenerateContentConfig(temperature=0.9, max_output_tokens=40)
                ),
                timeout=4.0
            )
            lat = time.time() - t0
            txt = resp.text.strip() if resp and resp.text else ""
            print(f"✅ Key #{idx+13} | ⏱️ 耗時: {lat:.2f}s | 💭 雜念: 「{txt}」")
            break
        except Exception as e:
            print(f"❌ Key #{idx+13} 異常: {e}")

if __name__ == "__main__":
    asyncio.run(main())
