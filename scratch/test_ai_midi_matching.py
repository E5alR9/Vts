import sys, os, re, json, asyncio
sys.path.insert(0, r"c:\Users\qiwai")
sys.stdout.reconfigure(encoding='utf-8')
from google import genai
from dotenv import load_dotenv
load_dotenv()

raw_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or ""
keys = [k.strip() for k in re.split(r'[\s,;]+', raw_keys) if k.strip()]

MIDI_DIR = "midi_sheets"
files = [f for f in os.listdir(MIDI_DIR) if f.lower().endswith(('.mid', '.midi'))]

async def match_midi_with_ai(song_query: str, available_files: list) -> str:
    prompt = f"""妳是 7L 的音樂曲庫大腦。請幫忙把使用者的點歌名稱，與資料夾中現有的 MIDI 檔案清單進行【精準語意匹配】。
支援：中英日繁簡轉譯、羅馬拼音、動漫/遊戲譯名、作曲家別名（例如：「千本櫻」➔「Hatsune Miku - Senbonzakura.mid」、「殘酷天使」➔「Evangelion - Cruel Angel's Thesis.mid」、「天空之城」➔「Laputa - Castle in the Sky.mid」、「六兆年與一夜物語」➔「六兆年と一夜物語.mid」）。

【使用者想點播的曲目】：『{song_query}』

【資料夾中現有的 MIDI 檔案清單】：
{json.dumps(available_files, ensure_ascii=False, indent=2)}

【規則】：
1. 若清單中有對應或高度相符的檔案，請【只輸出該檔名】（包含 .mid 副檔名）。
2. 若清單中【確實完全沒有任何相符的檔案】，請輸出 NONE。
3. 嚴禁任何解釋或多餘文字。"""

    client = genai.Client(api_key=keys[0])
    for m in ["gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-3.6-flash"]:
        try:
            resp = await client.aio.models.generate_content(model=m, contents=prompt)
            res_txt = resp.text.strip() if resp.text else "NONE"
            return res_txt
        except Exception:
            continue
    return "NONE"

async def test_ai_matching():
    test_queries = [
        "千本櫻",
        "殘酷天使的行動綱領",
        "天空之城",
        "給愛麗絲",
        "聖誕快樂勞倫斯先生",
        "卡農",
        "六兆年與一夜物語",  # 目前清單中沒有，應該回傳 NONE
    ]
    
    print("=== 🧠 測試 Gemini 智能 MIDI 曲庫語意匹配 ===")
    for q in test_queries:
        matched = await match_midi_with_ai(q, files)
        print(f"🎵 點歌『{q}』 ➔ AI 匹配結果: {matched}")

if __name__ == "__main__":
    asyncio.run(test_ai_matching())
