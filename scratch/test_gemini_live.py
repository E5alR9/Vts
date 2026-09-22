import asyncio
import os
import re
import sys
import wave
import io
from dotenv import load_dotenv
from google import genai
from google.genai import types

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

raw_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or ""
keys = [k.strip() for k in re.split(r'[\s,;]+', raw_keys) if k.strip()]

if not keys:
    print("❌ 未找到 GEMINI_API_KEY")
    sys.exit(1)

async def test_live_api():
    print("🚀 [Gemini Live API] 正在準備連線測試...")
    
    # 輪詢可用 Key
    for i, key in enumerate(keys[:3]):
        print(f"\n🔑 嘗試使用第 {i+1} 把金鑰連線...")
        client = genai.Client(api_key=key)
        
        # 測試 Live API 模型 (gemini-3.1-flash-live-preview)
        model_name = "gemini-3.1-flash-live-preview"
        
        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            system_instruction=types.Content(
                parts=[types.Part.from_text(text="妳是 7L，一個靈動、可愛又充滿活力的 AI VTuber。請用簡短、熱情的一句話向老爸打招呼！")]
            ),
            output_audio_transcription=types.AudioTranscriptionConfig()
        )
        
        audio_chunks = []
        transcription_text = ""
        
        try:
            print(f"🌐 正在建立 WebSocket 連線至 {model_name}...")
            async with client.aio.live.connect(model=model_name, config=config) as session:
                print("✅ WebSocket 握手成功！連線已建立！")
                
                # 發送即時文字測試指令
                test_prompt = "老爸上線了，跟我打個招呼吧！"
                print(f"📤 發送測試輸入: 『{test_prompt}』")
                await session.send_realtime_input(text=test_prompt)
                
                print("📥 正在接收即時原生語音串流與轉錄文字...")
                
                # 設置超時接收
                async def receive_stream():
                    nonlocal transcription_text
                    async for response in session.receive():
                        server_content = response.server_content
                        if not server_content:
                            continue
                            
                        # 處理文字轉錄
                        if server_content.output_transcription and server_content.output_transcription.text:
                            transcription_text += server_content.output_transcription.text
                            print(f"🗣️ [即時轉錄]: {server_content.output_transcription.text}", end="", flush=True)
                            
                        # 處理原生 PCM 音訊數據
                        if server_content.model_turn:
                            for part in server_content.model_turn.parts:
                                if part.inline_data and part.inline_data.data:
                                    audio_chunks.append(part.inline_data.data)
                                    
                        # 턴 終了判定
                        if server_content.turn_complete:
                            print("\n🏁 [Turn Complete] 回覆串流接收完畢！")
                            break
                            
                await asyncio.wait_for(receive_stream(), timeout=12.0)
                
                total_audio_bytes = sum(len(c) for c in audio_chunks)
                print(f"\n✨ 【測試結果報告】")
                print(f"  - 完整轉錄文字: {transcription_text.strip()}")
                print(f"  - 收到 PCM 音訊區塊: {len(audio_chunks)} 塊 (共 {total_audio_bytes} 位元組)")
                
                # 將 24kHz 16-bit Mono PCM 儲存為 WAV
                if audio_chunks:
                    pcm_data = b"".join(audio_chunks)
                    wav_filename = "gemini_live_test_output.wav"
                    with wave.open(wav_filename, "wb") as wav_file:
                        wav_file.setnchannels(1)        # mono
                        wav_file.setsampwidth(2)        # 16-bit
                        wav_file.setframerate(24000)    # 24kHz
                        wav_file.writeframes(pcm_data)
                    print(f"  - 🎵 原生音訊已儲存至: {wav_filename} (24kHz WAV)")
                    
                print("\n🎉 Gemini 3.1 Flash Live API 測試完全成功！")
                return True
                
        except Exception as e:
            err_str = str(e)
            print(f"⚠️ 連線或接收異常: {err_str}")
            if "429" in err_str or "quota" in err_str.lower():
                print("   ➔ 遭遇配額限制，自動嘗試下一把金鑰...")
                continue
            else:
                break
                
    return False

if __name__ == "__main__":
    asyncio.run(test_live_api())
