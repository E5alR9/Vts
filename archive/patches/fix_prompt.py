import re

with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_string = """        current_history.append({"role": "assistant", "content": raw_stage2_text})
                    asyncio.create_task(save_to_long_term_memory(DEFAULT_CHANNEL_ID, current_history))



async def fetch_fast_text_reply(user_input: str, custom_name: str, situation_prompt: str = "", history: Optional[List[Dict]] = None) -> Tuple[str, str, float]:
    \"\"\"⚡ 【真人感即時第一反應 (Reflex)】：在收到訊息第一時間，由極速文字大腦 (Groq / Gemini Flash Lite) 毫秒級搶先開口！
    6. 🛠️ 【系統直接指令調用 (極重要)】：若要執行動作，請直接在對話中輸出對應的 Python 指令碼（系統會自動攔截執行，不會唸出來）：
       - 🎹 點歌/彈琴：`pe.play_virtual_piano(song_name='歌名')`
       - 🎹 即興創作：`pe.compose_and_play_original_piano()`
       - 🎹 停止彈琴：`pe.stop_virtual_piano()`
       - 🚶 移動走位：`move_spatial_position('左側/右側/靠近/原位')`
       - 🎨 畫圖：`draw_illustration('畫面描述')`
       - 💻 執行代碼：`execute_local_python_code('Python程式碼')`\"\"\""""

good_string = """        current_history.append({"role": "assistant", "content": raw_stage2_text})
        
    asyncio.create_task(save_to_long_term_memory(DEFAULT_CHANNEL_ID, current_history))



async def fetch_fast_text_reply(user_input: str, custom_name: str, situation_prompt: str = "", history: Optional[List[Dict]] = None) -> Tuple[str, str, float]:
    \"\"\"⚡ 【真人感即時第一反應 (Reflex)】：在收到訊息第一時間，由極速文字大腦 (Groq / Gemini Flash Lite) 毫秒級搶先開口！\"\"\""""

content = content.replace(bad_string, good_string)

target_1 = "6. 🎹 鋼琴點歌：若觀眾點歌，請【直接調用工具 `pe.play_virtual_piano(song_name='歌名')`】開彈！若觀眾要求妳自創曲、即興創作一首，請調用 `pe.compose_and_play_original_piano`！"
replacement_1 = """6. 🛠️ 【系統直接指令調用 (極重要)】：若要執行動作，請直接在對話中輸出對應的 Python 指令碼（系統會自動攔截執行，不會唸出來）：
   - 🎹 點歌/彈琴：`pe.play_virtual_piano(song_name='歌名')`
   - 🎹 即興創作：`pe.compose_and_play_original_piano()`
   - 🎹 停止彈琴：`pe.stop_virtual_piano()`
   - 🚶 移動走位：`move_spatial_position('左側/右側/靠近/原位')`
   - 🎨 畫圖：`draw_illustration('畫面描述')`
   - 💻 執行代碼：`execute_local_python_code('Python程式碼')`"""

target_2 = "3. 🎹 鋼琴才藝：老爸若點歌，務必【直接調用 `pe.play_virtual_piano` 工具】開彈！若老爸要求妳自創曲、即興創作，請調用 `pe.compose_and_play_original_piano`！"
replacement_2 = replacement_1.replace("6. ", "3. ")

content = content.replace(target_1, replacement_1)
content = content.replace(target_2, replacement_2)

with open('vts_7L_test.py', 'w', encoding='utf-8') as f:
    f.write(content)
