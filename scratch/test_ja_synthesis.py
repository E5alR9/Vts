import os
import sys
import numpy as np
import soundfile as sf
import io
import lameenc

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = r"C:\Users\qiwai\GPT-SoVITS"
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
    sys.path.append(os.path.join(BASE_DIR, "GPT_SoVITS"))

prev_cwd = os.getcwd()
os.chdir(BASE_DIR)
from TTS_infer_pack.TTS import TTS, TTS_Config

config = TTS_Config("GPT_SoVITS/configs/tts_infer.yaml")
config.device = "cuda"
config.is_half = True
config.t2s_weights_path = "pretrained_models/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt"
config.vits_weights_path = "pretrained_models/s2G488k.pth"
config.cnhubert_base_path = "pretrained_models/chinese-hubert-base"
config.bert_base_path = "pretrained_models/chinese-roberta-wwm-ext-large"

tts = TTS(config)
os.chdir(prev_cwd)

ref_audio = r"c:\Users\qiwai\xiaoyi_japanese_ref.wav"
ref_text = "お兄ちゃん、今日も一日頑張ろうね！大好きだよ！"
ref_lang = "all_ja"

target_text = "こんにちは〜！今日も一日、一緒にがんばろうね！"

inputs = {
    "text": target_text,
    "text_lang": "all_ja",
    "ref_audio_path": ref_audio,
    "prompt_text": ref_text,
    "prompt_lang": ref_lang,
    "top_k": 5,
    "top_p": 1.0,
    "temperature": 1.0,
    "text_split_method": "cut5",
    "batch_size": 2,
    "speed_factor": 1.0,
}

print("正在進行本地日語合成 (使用曉伊日文原生參考音)...")
gen = tts.run(inputs)
sr, audio = next(gen)

# 轉為 MP3
if audio.dtype != np.int16:
    if audio.dtype == np.float32 or audio.dtype == np.float64:
        audio_clipped = np.clip(audio, -1.0, 1.0)
        pcm_data = (audio_clipped * 32767.0).astype(np.int16)
    else:
        pcm_data = audio.astype(np.int16)
else:
    pcm_data = audio

encoder = lameenc.Encoder()
encoder.set_bit_rate(128)
encoder.set_in_sample_rate(sr)
encoder.set_channels(1)
encoder.set_quality(2)
mp3_data = encoder.encode(pcm_data.tobytes()) + encoder.flush()

out_mp3 = r"c:\Users\qiwai\scratch\test_ja_native.mp3"
with open(out_mp3, "wb") as f:
    f.write(mp3_data)
print(f"✅ 合成完成: {out_mp3} ({len(mp3_data)} bytes)")

# 使用 Gemini 分析
from google import genai
api_key = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
resp = client.models.generate_content(
    model='gemini-3.5-flash-lite',
    contents=[
        genai.types.Part.from_bytes(data=mp3_data, mime_type='audio/mp3'),
        '請詳細評估這段音訊：\n1. 聽起來是否為地道自然的日語母語發音？\n2. 高低重音 (Pitch Accent) 與節奏感 (Mora timing) 是否自然？\n3. 還會不會讓人覺得是「中文腔調在讀日文」？'
    ]
)
print("\n=== Gemini 聽感評估 ===")
print(resp.text)
