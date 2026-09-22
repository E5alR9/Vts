import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from google import genai

api_key = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
with open('c:/Users/qiwai/test_ja.mp3', 'rb') as f:
    audio_bytes = f.read()

resp = client.models.generate_content(
    model='gemini-3.5-flash-lite',
    contents=[
        genai.types.Part.from_bytes(data=audio_bytes, mime_type='audio/mp3'),
        '請仔細聽這段音訊的語調、腔調與音色：\n1. 聽感上是否聽起來像中文母語者在生硬讀日語（中文腔/外國人腔）？\n2. 聲調（Pitch Accent）是否不自然？哪幾個詞的聲調或母音聽起來最像中文？\n3. 如果一位只懂中文和基本日語的台灣/華人觀眾聽了，為什麼可能會覺得「聽起來像中文」？'
    ]
)
print('Gemini 聽感分析結果:')
print(resp.text)
