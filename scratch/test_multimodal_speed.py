import os
import sys
import time
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
import io

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

load_dotenv()

gemini_keys = [k.strip() for k in re.split(r'[\s,;]+', os.getenv('GEMINI_API_KEYS') or os.getenv('GEMINI_API_KEY') or '') if k.strip()]
client = genai.Client(api_key=gemini_keys[0])

img = Image.new('RGB', (640, 360), color=(40, 50, 60))
buf = io.BytesIO()
img.save(buf, format='JPEG', quality=85)
img_bytes = buf.getvalue()

models = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.6-flash"
]

print("=" * 80)
print("🖼️ 【多模態 (螢幕截圖 + 聊天文字) 回應速度實測】")
print("=" * 80)

for m in models:
    t0 = time.time()
    try:
        r = client.models.generate_content(
            model=m,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'),
                "老爸問：妳看得到我現在畫面嗎？（請 1 句話簡短親切回答）"
            ]
        )
        print(f"✅ {m:<25} | ⏱️ {time.time()-t0:.2f}s | {r.text.strip()[:60]}")
    except Exception as e:
        print(f"❌ {m:<25} | ⏱️ {time.time()-t0:.2f}s | 錯誤: {e}")
