async def execute_actions(vts, text, input_queue):
    global active_timers, target_look_x, target_look_y, is_tracking_mouse, force_blink_trigger
    
    exp_match = re.search(r'\[EXPRESSION:\s*([^\]]+)\]', text, re.IGNORECASE)
    if exp_match:
        exp_tag = exp_match.group(1).strip()
        asyncio.create_task(set_vts_expression(vts, exp_tag))

    move_match = re.search(r'\[(?:MOVE|WINDOW|POSITION):\s*([^\]]+)\]', text, re.IGNORECASE)
    if move_match:
        pos_tag = move_match.group(1).strip()
        if not is_piano_active or any(k in pos_tag for k in ["鋼琴", "原本", "大小", "視窗"]):
            asyncio.create_task(apply_spatial_position(pos_tag))

    url_match = re.search(r'\[OPEN_BROWSER:\s*([^\]]+)\]', text, re.IGNORECASE)
    if url_match:
        url = url_match.group(1).strip()
        if not url.startswith('http'):
            url = 'https://' + url
        try:
            webbrowser.open(url)
            print(f"\n🌐 [系統動作] 7L 幫你打開了網頁: {url}")
        except Exception as e:
            print(f"\n❌ [開啟網頁失敗]: {e}")

    try:
        upper_text = text.upper()
        if "MOUSE" in upper_text and "LOOK" in upper_text: is_tracking_mouse = True
        elif "LEFT" in upper_text and "LOOK" in upper_text: is_tracking_mouse = False; target_look_x, target_look_y = -25.0, 0.0
        elif "RIGHT" in upper_text and "LOOK" in upper_text: is_tracking_mouse = False; target_look_x, target_look_y = 25.0, 0.0
        elif "UP" in upper_text and "LOOK" in upper_text: is_tracking_mouse = False; target_look_x, target_look_y = 0.0, 25.0
        elif "DOWN" in upper_text and "LOOK" in upper_text: is_tracking_mouse = False; target_look_x, target_look_y = 0.0, -25.0
        elif "CENTER" in upper_text and "LOOK" in upper_text: is_tracking_mouse = False; target_look_x, target_look_y = 0.0, 0.0

        if "EARS" in upper_text: force_blink_trigger = 8
    except Exception:
        pass

    clean_text = text
    clean_text = re.sub(r'<think>.*?</think>', '', clean_text, flags=re.DOTALL|re.IGNORECASE)
    clean_text = re.sub(r'\[OPEN_BROWSER:\s*[^\]]+\]', '', clean_text, flags=re.IGNORECASE) 
    clean_text = re.sub(r'\[.*?\]', '', clean_text)  
    clean_text = re.sub(r'\[?(LOOK|EXPRESSION|MOVE|WINDOW|POSITION|TIMER|TYPE|HOTKEY):?\s*[a-zA-Z0-9_\u4e00-\u9fa5]+\]?', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'```.*?```', '', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'`.*?`', '', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'(?:execute_local_python_code|trigger_vts_expression|search_google|generate_ai_image|move_spatial_position)\(.*?\)', '', clean_text, flags=re.IGNORECASE|re.DOTALL)
    clean_text = re.sub(r'^(老爸|玩家|使用者|7L|女兒|溫柔女兒|七[龄靈])[：:]\s*', '', clean_text, flags=re.IGNORECASE)
    clean_text = clean_text.replace('[', '').replace(']', '').replace('*', '').strip()
    
    return clean_text

# ────────────────────────────────────────────────────────
# ⚙️ 14. 專屬背景工作協程群 (Workers)
# ────────────────────────────────────────────────────────

# --- 🎤 語音與收音協程 ---
is_user_listening = False
listen_start_time = 0.0
LISTEN_LIMIT = 5

async def mic_volume_worker():
    global current_mic_volume_str, current_ai_state, IS_MIC_ENABLED
    
    stream = None
    if HAS_PYAUDIO:
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        except Exception:
            pass 

    while True:
        if not IS_MIC_ENABLED:
            current_mic_volume_str = "[🔴 麥克風已關閉]"
            await asyncio.sleep(0.3)
            continue

        if current_ai_state == "TALKING":
            current_mic_volume_str = "[🔇 靜音鎖定 (說話中)]"
            await asyncio.sleep(0.2)
        else:
            if stream:
                try:
                    frames_avail = stream.get_read_available()
                    if frames_avail > 0:
                        data = stream.read(frames_avail, exception_on_overflow=False)
                        audio_data = np.frombuffer(data, dtype=np.int16)
                        if len(audio_data) > 0:
                            rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))
                            vol_percent = min(100, int((rms / 2500) * 100))
                            bars = vol_percent // 10
                            bar_str = "█" * bars + "_" * (10 - bars)
                            current_mic_volume_str = f"[🎤 收音: {vol_percent:02d}% |{bar_str}|]"
                    await asyncio.sleep(0.05) 
                except Exception:
                    current_mic_volume_str = "[🟢 麥克風全時就緒]"
                    await asyncio.sleep(0.5)
            else:
                current_mic_volume_str = "[🟢 麥克風全時就緒]"
                await asyncio.sleep(0.5)

