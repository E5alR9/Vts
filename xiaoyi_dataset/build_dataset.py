import os
import asyncio
import edge_tts
import librosa
import soundfile as sf
from corpus import CORPUS

VOICE = "zh-CN-XiaoyiNeural"
OUTPUT_DIR = "wavs"
LIST_FILE = "train.list"

os.makedirs(OUTPUT_DIR, exist_ok=True)

async def build_dataset():
    print(f"=== 開始自動生成 Xiaoyi 訓練資料集 (共 {len(CORPUS)} 句) ===")
    lines = []
    
    for i, text in enumerate(CORPUS):
        name = f"xiaoyi_{i:04d}"
        mp3_path = os.path.join(OUTPUT_DIR, f"{name}.mp3")
        wav_path = os.path.join(OUTPUT_DIR, f"{name}.wav")
        
        # 活潑靈動微調參數 (微調 rate 和 pitch)
        communicate = edge_tts.Communicate(text, VOICE, rate="+5%", pitch="+5Hz")
        await communicate.save(mp3_path)
        
        # 轉為標準 24kHz 單聲道高品質 WAV
        y, sr = librosa.load(mp3_path, sr=24000, mono=True)
        sf.write(wav_path, y, sr)
        
        # 清理暫存 mp3
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
            
        # 記錄標準格式: [音檔路徑]|[文本]
        rel_wav_path = f"wavs/{name}.wav"
        lines.append(f"{rel_wav_path}|{text}")
        print(f"[{i+1}/{len(CORPUS)}] 成功生成: {text[:25]}...")
        
    with open(LIST_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    print(f"\n🎉 資料集構建完成！清單已儲存至: {LIST_FILE}")
    print(f"音檔目錄: {OUTPUT_DIR}/ (共 {len(CORPUS)} 個 24kHz WAV)")

if __name__ == "__main__":
    asyncio.run(build_dataset())
