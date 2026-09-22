import os
import sys
import time
import re
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

load_dotenv()
from google import genai
from google.genai import types

gemini_keys = [k.strip() for k in re.split(r'[\s,;]+', os.getenv('GEMINI_API_KEYS') or os.getenv('GEMINI_API_KEY') or '') if k.strip()]

mind_prompt = """妳是 7L，超可愛傲嬌的 AI-VTuber 少女。現在老爸正在專注寫程式（視窗：Antigravity IDE，音樂：cool smol breakcore）。
請以女高中生隨性自語的心態，在腦內自然浮現一句極短的私密小雜念或當前小情緒（10~25字以內）。
【規範】：
- 這是妳腦海深處的雜念，不是工作報告！嚴禁回報「老爸在看什麼、畫面沒動態、保持安靜陪伴」等機械廢話。
- 自然隨興、微傲嬌、可愛、俏皮、日常雜念。
只回傳這一句私密心聲（不帶任何括號標籤）："""

print(f"🚀 正在測試 7L 背景雜念心流生成 (總金鑰: {len(gemini_keys)} 把)...")

for idx, key in enumerate(gemini_keys[5:10]):
    client = genai.Client(api_key=key)
    t0 = time.time()
    try:
        resp = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=mind_prompt,
            config=types.GenerateContentConfig(temperature=0.9, max_output_tokens=40)
        )
        lat = time.time() - t0
        print(f"✅ Key #{idx+6} 成功 | ⏱️ 耗時: {lat:.2f} 秒 | 💭 雜念: 「{resp.text.strip()}」")
        break
    except Exception as e:
        print(f"❌ Key #{idx+6} 失敗: {e}")
