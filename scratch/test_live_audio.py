import asyncio
import os
import re
import sys
import wave
from dotenv import load_dotenv
from google import genai
from google.genai import types

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

raw_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or ""
keys = [k.strip() for k in re.split(r'[\s,;]+', raw_keys) if k.strip()]

async def test_live_audio():
    client = genai.Client(api_key=keys[0])
    model_name = "gemini-3.1-flash-live-preview"
    
    # 設定語音模態與聲音模型
    config = types.LiveConnectConfig(
        response_modalities=[types.Modality.AUDIO],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Aoede"  # 靈動女聲 (可選 Aoede, Kore, Fenrir, Puck 等)
                )
            )
        ),
        system_instruction=types.Content(
            parts=[types.Part.from_text(text="妳是 7L，老爸的 AI 女兒，講話要超級甜、可愛活潑！")]
        ),
        output_audio_transcription=types.AudioTranscriptionConfig()
    )
    
    print(f"🌐 連線至 {model_name} (Voice: Aoede)...")
    audio_data = bytearray()
    full_transcript = ""
    
    async with client.aio.live.connect(model=model_name, config=config) as session:
        print("✅ 連線成功！發送即時語音請求...")
        await session.send_realtime_input(text="老爸今天工作好累喔，給我加個油～")
        
        async for response in session.receive():
            sc = response.server_content
            if not sc:
                continue
                
            if sc.output_transcription and sc.output_transcription.text:
                full_transcript += sc.output_transcription.text
                print(sc.output_transcription.text, end="", flush=True)
                
            if sc.model_turn and sc.model_turn.parts:
                for part in sc.model_turn.parts:
                    if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                        audio_data.extend(part.inline_data.data)
                        
            if sc.turn_complete:
                print("\n🏁 [完成] 即時語音接收完畢！")
                break
                
    print(f"\n✨ 文字: {full_transcript}")
    print(f"🎵 收到原生 PCM 音訊: {len(audio_data)} bytes")
    
    if len(audio_data) > 0:
        wav_path = "live_audio_sample.wav"
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_data)
        print(f"💾 已成功生成 24kHz 高音質 WAV: {wav_path}")

if __name__ == "__main__":
    asyncio.run(test_live_audio())
