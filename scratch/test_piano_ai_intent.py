import os, json, asyncio, sys, re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')
raw_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or ""
GEMINI_KEYS = [k.strip() for k in re.split(r'[\s,;]+', raw_keys) if k.strip()]
print('Found keys:', len(GEMINI_KEYS))

async def test_ai_intent(query):
    client = genai.Client(api_key=GEMINI_KEYS[0])
    local_files = ['campanella.mid', 'Hatsune Miku - Senbonzakura.mid', 'Clair-De-Lune-Opus-46-Nr-1.mid', 'Literature (Full ver.).mid']
    prompt = f'''妳是 7L 的 AI 音樂總監。請深度理解點歌語意並進行判斷。
【使用者輸入】："{query}"
【本地曲庫】：{json.dumps(local_files, ensure_ascii=False)}

請輸出 JSON：
{{
  "is_random": true/false, // 是否為隨機/隨便/電台/泛指曲目意圖
  "is_mashup": true/false, // 是否為多曲合奏
  "matched_files": ["matched_local_filename.mid"], // 本地吻合之檔案
  "search_online_query": "" // 僅當點了具體歌名且本地完全沒有時填寫，隨機意圖嚴禁填寫
}}'''
    resp = await client.aio.models.generate_content(
        model='gemini-3.5-flash-lite',
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.1, response_mime_type='application/json')
    )
    print(f'Query: {query} -> Result: {resp.text.strip()}')

async def main():
    for q in ['隨機琴曲', '去彈鋼琴隨便談', '千本櫻跟鐘同時彈', '彈一下月光', '周杰倫 稻香']:
        await test_ai_intent(q)

asyncio.run(main())
