import sys, os
sys.path.insert(0, r"c:\Users\qiwai")
sys.stdout.reconfigure(encoding='utf-8')

from vts_7L_test import TextCleanEngine, PromptTemplateEngine, strip_all_emojis

def test_text_clean_engine():
    print("=== 🧹 測試 TextCleanEngine 正則清洗引擎 ===")
    
    # 1. 測試 Emoji 去除
    emoji_raw = "老爸好呀！💖✨🎶 今天想聽什麼鋼琴曲？🎹🤖"
    emoji_clean = strip_all_emojis(emoji_raw)
    print(f"1. Emoji 清洗: '{emoji_raw}' ➔ '{emoji_clean}'")
    assert "💖" not in emoji_clean and "🎹" not in emoji_clean
    
    # 2. 測試 TTS 前置清洗
    tts_raw = "[EXPRESSION: 臉紅] [LOOK: ROLL] 老爸 @E5alR9 快看這個！"
    tts_clean = TextCleanEngine.clean_for_tts(tts_raw)
    print(f"2. TTS 清洗: '{tts_raw}' ➔ '{tts_clean}'")
    assert "[EXPRESSION" not in tts_clean and "@" not in tts_clean
    
    # 3. 測試完整口語文字淨化 (剔除思考鏈、系統提示、工具函式殘留)
    full_raw = "<think>這是思考過程</think>（轉頭看向老爸）[LOOK: ROLL] [MOVE: 中間] play_virtual_piano(song_name='愛之夢') 這首超浪漫喔！"
    speech_clean = TextCleanEngine.clean_speech_text(full_raw)
    print(f"3. 口語淨化: '{full_raw}' ➔ '{speech_clean}'")
    assert "<think>" not in speech_clean and "play_virtual_piano" not in speech_clean and "（轉頭" not in speech_clean
    assert speech_clean == "這首超浪漫喔！"

def test_prompt_template_engine():
    print("\n=== 📝 測試 PromptTemplateEngine 範本工廠 ===")
    
    p1 = PromptTemplateEngine.get_piano_status_prompt(True, "愛之夢")
    print(f"1. 彈琴中狀態 Prompt: {p1[:60]}...")
    assert "愛之夢" in p1 and "不插歌" in p1
    
    p2 = PromptTemplateEngine.get_piano_status_prompt(False, "")
    print(f"2. 未彈琴狀態 Prompt: {p2}")
    assert "未彈琴" in p2
    
    chat_prompt = PromptTemplateEngine.build_chat_system_prompt(
        is_tiktok=False,
        current_custom_name="老爸",
        stage2_target_prompt="對象是老爸",
        stage2_instructions="請自然回應",
        current_target_desc="老爸",
        is_piano_active=False,
        current_piano_song_title="",
        live_audio_emotion_prompt="",
        situation_prompt="情境正常",
        system_specs="高階硬體",
        impression_text="好老爸"
    )
    print(f"3. 對話 System Prompt 建構成功，長度: {len(chat_prompt)} 字元")
    assert "7L" in chat_prompt and "trigger_vts_expression" in chat_prompt

if __name__ == "__main__":
    test_text_clean_engine()
    test_prompt_template_engine()
    print("\n✅ 所有文本清洗與 Prompt 工廠單元測試 100% 通過！")
