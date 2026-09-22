import os
import sys
import asyncio
import edge_tts
import soundfile as sf
import librosa

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'c:\Users\qiwai')
sys.path.append(os.path.join(r'c:\Users\qiwai', 'services', 'rvc'))
os.environ['rmvpe_root'] = os.path.abspath(r'c:\Users\qiwai\models\rvc')

from services.neural_voice_converter import convert_vocal_to_xiaoyi

out_dir = r"c:\Users\qiwai\scratch"
raw_ja_mp3 = os.path.join(out_dir, "raw_ja_nanami.mp3")
raw_ja_wav = os.path.join(out_dir, "raw_ja_nanami.wav")
xiaoyi_ja_wav = r"c:\Users\qiwai\xiaoyi_japanese_ref.wav"

ja_prompt_text = "お兄ちゃん、今日も一日頑張ろうね！大好きだよ！"

async def step1_make_ref():
    print("1. 生成日語原生語調音訊...")
    comm = edge_tts.Communicate(ja_prompt_text, "ja-JP-NanamiNeural")
    await comm.save(raw_ja_mp3)
    
    # 轉為 WAV 40kHz
    y, sr = librosa.load(raw_ja_mp3, sr=40000)
    sf.write(raw_ja_wav, y, sr)
    
    print("2. 透過 RVC 草莓模型轉換為 100% 曉伊音色...")
    ok = convert_vocal_to_xiaoyi(
        raw_ja_wav,
        xiaoyi_ja_wav,
        key=0.0,
        model_name='caomei',
        index_rate=0.75
    )
    print(f"RVC 轉換結果: ok={ok}, 輸出: {xiaoyi_ja_wav}")

if __name__ == "__main__":
    asyncio.run(step1_make_ref())
