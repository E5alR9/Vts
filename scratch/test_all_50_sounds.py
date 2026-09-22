import sys, os
sys.path.insert(0, r"c:\Users\qiwai")
import asyncio
import edge_tts
from core.prompts import TextCleanEngine

rows = [
    ("あ行 (母音)", "あ、い、う、え、お"),
    ("か行 (K音)", "か、き、く、け、こ"),
    ("さ行 (S音)", "さ、し、す、せ、そ"),
    ("た行 (T音)", "た、ち、つ、て、と"),
    ("な行 (N音)", "な、に、ぬ、ね、の"),
    ("は行 (H音)", "は、ひ、ふ、へ、ほ"),
    ("ま行 (M音)", "ま、み、む、め、も"),
    ("や行 (Y音)", "や、ゆ、よ"),
    ("ら行 (R音)", "ら、り、る、れ、ろ"),
    ("わ行 (W音/鼻音)", "わ、を、ん"),
    ("が行 (濁音G)", "が、ぎ、ぐ、げ、ご"),
    ("ざ行 (濁音Z)", "ざ、じ、ず、ぜ、ぞ"),
    ("だ行 (濁音D)", "だ、ぢ、づ、で、ど"),
    ("ば行 (濁音B)", "ば、び、ぶ、べ、ぼ"),
    ("ぱ行 (半濁音P)", "ぱ、ぴ、ぷ、ぺ、ぽ"),
]

async def main():
    os.makedirs("songs_library/50on", exist_ok=True)
    full_audio_chunks = []
    
    print("=" * 60)
    print("50音窮舉配對轉換檢測：")
    print("=" * 60)
    
    full_script_lines = []

    for idx, (title, kana_text) in enumerate(rows):
        phonetic = TextCleanEngine.clean_for_tts(kana_text)
        print(f"[{title}]")
        print(f"  原始假名: {kana_text}")
        print(f"  音標轉換: {phonetic}")
        
        # 單行音檔
        single_file = f"songs_library/50on/row_{idx+1:02d}.mp3"
        comm = edge_tts.Communicate(phonetic, "zh-CN-XiaoyiNeural", pitch="+0Hz", rate="+0%")
        await comm.save(single_file)
        
        # 組合大串燒：每一行報幕 + 唸出 50 音
        spoken_line = f"{title}。{phonetic}。"
        full_script_lines.append(spoken_line)

    # 產生完整 50 音總合試聽音檔
    full_text = "老爸，這是我為你唸出的完整 50 音與濁音搭配，請驗收喔！" + " ".join(full_script_lines)
    print("\n產生完整 50 音總合音檔中...")
    master_comm = edge_tts.Communicate(full_text, "zh-CN-XiaoyiNeural", pitch="+0Hz", rate="-5%")
    await master_comm.save("songs_library/50_sounds_full_test.mp3")
    print("✅ 完整總合試聽音檔已生成：songs_library/50_sounds_full_test.mp3")

if __name__ == "__main__":
    asyncio.run(main())
