import os, sys, re, json
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types

raw = os.getenv('GEMINI_API_KEYS') or os.getenv('GEMINI_API_KEY') or ''
keys = [k.strip() for k in re.split(r'[\s,;]+', raw) if k.strip() and len(k.strip()) < 150]

HIGH_IQ_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite"
]

test_sentences = [
    "你要拿出來了沒啊沒有啊你是不是沒你的鋼琴呢",
    "爸爸的身體音量那你那你把鋼琴拿出來一下好不好你看一下那個東風啊蕭邦的東",
    "沒出來啊",
    "隨便彈一首好聽的",
    "蕭邦 冬風"
]

prompt_tmpl = """妳是 7L 的 AI 鋼琴音樂總監。請深度理解老爸/觀眾的說話意圖，判斷是否為點歌請求。

【使用者輸入】："{sentence}"

【判斷準則】：
1. is_song_request: 使用者是否「真正要聽/點播某首曲目」？
   - 若只是在問「鋼琴拿出來了沒」、「你的鋼琴呢」、「沒出來啊」、「收起來」、「鋼琴在哪」、「視窗開了沒」，這只是詢問鋼琴視窗狀態或抱怨，【絕對不是點歌】，is_song_request 必須填 false！
   - 若明確提到想聽某首曲子（例如「看一下那個東風啊蕭邦的」、「彈冬風」），則是點歌，is_song_request 填 true。
2. song_title: 提取出的乾淨曲名（例如「蕭邦 冬風」）。非點歌時留空字串 ""。
3. is_random: 是否為隨便彈/隨機意圖。

【請輸出純 JSON】：
{{
  "is_song_request": true/false,
  "song_title": "",
  "is_random": true/false,
  "reason": "判斷理由簡述"
}}"""

print("=== 測試倒序階梯 3.8 -> 3.7 -> 3.6 自動降級 ===", flush=True)

for s in test_sentences:
    p = prompt_tmpl.format(sentence=s)
    success = False
    for m in HIGH_IQ_MODELS:
        try:
            client = genai.Client(api_key=keys[13])
            resp = client.models.generate_content(
                model=m,
                contents=p,
                config=types.GenerateContentConfig(temperature=0.1, response_mime_type='application/json')
            )
            print(f'語句: "{s}" [由 {m} 成功判定]:')
            print('  ', resp.text.strip().replace('\n', ' '))
            success = True
            break
        except Exception as e:
            err = str(e).replace('\n', ' ')[:40]
            # 遇到 503 / 429 自動嘗試下一個高智商模型
            continue
    if not success:
        print(f'語句: "{s}" 全部模型失敗')
