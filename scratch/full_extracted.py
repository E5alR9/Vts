async def execute_actions(vts, text, input_queue, user_input_ctx: str = "", has_dispatched_tool: bool = False, execute_visuals: bool = False, caller_target: str = "", caller_user: str = ""):
-    """集中式系統動作與指令過濾器 (即刻執行底層系統動作/工具，並產出口語純淨文字)"""
-    
-    
-    # 🧠 提取並記錄 7L 大腦私密心想 (Inner Monologue)
-    extracted_thought, text_without_thought = TextCleanEngine.extract_thought(text)
-    if extracted_thought:
-        log_print(f"🧠 [7L 腦內心想] 💭 {extracted_thought}")
-        record_internal_thought(user_input_ctx, extracted_thought)
-        try:
-            web_dash.broadcast_event("ai_thought", {"thought": extracted_thought})
-        except Exception:
-            pass
-        text = text_without_thought
-
-    if bool(re.search(r'\[HAD_TOOL_CALL\]', text, re.IGNORECASE)):
-        has_dispatched_tool = True
-
-    # 🧠 7L 自主雲端大腦演進標籤攔截 [UPDATE_PROMPT: ...] / [ADD_EXAMPLE: ...] / [LEARN_MEME: ...] / [LEARN_FACT: ...] / [UPDATE_RULE: ...]
-    for up in re.finditer(r'\[(?:UPDATE_PROMPT|UPDATE_KNOWLEDGE|SET_PROMPT)[：:]\s*([^|\]]+)\|([^\]]+)\]', text, re.IGNORECASE):
-        f_name = up.group(1).strip()
-        f_val = up.group(2).strip()
-        if f_name and f_val:
-            asyncio.create_task(update_cloud_prompt_field(f_name, f_val))
-            text = text.replace(up.group(0), "")
-
-    for ae in re.finditer(r'\[(?:ADD_EXAMPLE|LEARN_EXAMPLE)[：:]\s*([^|\]]+)\|([^|\]]+)\|([^|\]]+)\|([^\]]+)\]', text, re.IGNORECASE):
-        sc = ae.group(1).strip()
-        ui = ae.group(2).strip()
-        th = ae.group(3).strip()
-        rp = ae.group(4).strip()
-        if sc and rp:
-            asyncio.create_task(add_few_shot_example(sc, ui, th, rp))
-            text = text.replace(ae.group(0), "")
-
-    for lm in re.finditer(r'\[LEARN_MEME[：:]\s*([^\]]+)\]', text, re.IGNORECASE):
-        meme_val = lm.group(1).strip()
-        if meme_val:
-            asyncio.create_task(learn_new_meme(meme_val))
-            text = text.replace(lm.group(0), "")
-
-    for lf in re.finditer(r'\[LEARN_FACT[：:]\s*([^\]]+)\]', text, re.IGNORECASE):
-        fact_val = lf.group(1).strip()
-        if fact_val:
-            asyncio.create_task(learn_new_fact(fact_val))
-            text = text.replace(lf.group(0), "")
-
-    for lr in re.finditer(r'\[(?:UPDATE_RULE|SET_RULE|LEARN_RULE)[：:]\s*([^\]]+)\]', text, re.IGNORECASE):
-        rule_val = lr.group(1).strip()
-        if rule_val:
-            asyncio.create_task(update_custom_rule(rule_val))
-            text = text.replace(lr.group(0), "")
-
-    for tm in re.finditer(r'\[(?:TIMER|SET_TIMER|ALARM|鬧鐘|計時器)[：:]\s*([0-9]+)\s*\|?\s*([^\]]*)\]', text, re.IGNORECASE):
-        t_sec = int(tm.group(1))
-        t_msg = tm.group(2).strip() or "計時時間到"
-        log_print(f"⏱️ [計時器啟動] 設定 {t_sec} 秒後提醒: 「{t_msg}」")
-        asyncio.create_task(set_timer(t_sec, t_msg, input_queue))
-        text = text.replace(tm.group(0), "")
-
-    # ⚡ 檢測 7L 自我插話標籤 [INTERRUPT_SELF] / [CUT_IN] / [插話] / [中斷]
-    if bool(re.search(r'\[(?:INTERRUPT_SELF|CUT_IN|INTERRUPT|SELF_INTERRUPT|插話|中斷|打斷自己)\]', text, re.IGNORECASE)):
-        log_print("⚡ [7L 自我插話] 檢測到 [INTERRUPT_SELF] 標籤，立即秒級打斷當前正在說的話！")
-        asyncio.create_task(interrupt_current_speech(clear_queue=True, reason="7L 自由意志自我插話"))
-
-    # 📐 記住 VTS 模型基準位置與大小 (當老爸說「記住大小」、「記住位置」時即刻執行)
-    if any(k in text or k in user_input_ctx for k in ["記住大小", "記住位置", "記住現在位置", "記住當前位置", "記住現在大小", "記錄位置", "記錄大小", "記住模型位置", "記住模型", "記錄基準大小", "記錄基準位置", "記住當前大小"]):
-        log_print("📐 [VTS 模型記憶] 正在向 VTube Studio 讀取並保存當前模型座標與大小為基準...")
-        asyncio.create_task(vc.fetch_vts_base_model_pos(vc.GLOBAL_VTS))
-
-    # 🛠️ 通用 Python 函數直接調用攔截 (Universal Python Call Interceptor)
-    universal_tool_calls = [
-        (r'(?:\[SPEED:[^\]]+\]\s*)?(?:pe\.)?set_piano_speed\(\s*(?:speed\s*=\s*)?[\'"]?([0-9.]+)x?[\'"]?\s*\)', lambda m: pe.set_piano_speed(speed=float(m.group(1)))),
-        (r'(?:pe\.)?set_piano_volume\(\s*(?:volume\s*=\s*)?[\'"]?([0-9]+)[\'"]?\s*\)', lambda m: pe.set_piano_volume(volume=int(m.group(1)))),
-        (r'(?:pe\.)?set_piano_instrument\(\s*(?:instrument\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: pe.set_piano_instrument(instrument=m.group(1))),
-        (r'(?:pe\.)?open_virtual_piano\(\s*\)', lambda m: pe.open_virtual_piano()),
-        (r'(?:pe\.)?pause_virtual_piano\(\s*\)', lambda m: pe.pause_virtual_piano()),
-        (r'(?:pe\.)?resume_virtual_piano\(\s*\)', lambda m: pe.resume_virtual_piano()),
-        (r'(?:pe\.)?stop_virtual_piano\(\s*\)', lambda m: pe.stop_virtual_piano()),
-        (r'(?:pe\.)?list_piano_sheets\(\s*\)', lambda m: pe.list_piano_sheets()),
-        (r'(?:pe\.)?play_virtual_piano\(\s*(?:song_name\s*=\s*)?[\'"]([^\'"]+)[\'"](?:[^)]*)\)', lambda m: pe.play_virtual_piano(
-            song_name=m.group(1), 
-            force_online=bool(re.search(r'force_online\s*=\s*True', m.group(0), re.I)), 
-            target=(caller_target or ("audience" if CURRENT_SPEAKING_TARGET == "audience" else "dad")),
-            requester_name=(caller_user or ("老爸" if (caller_target == "dad" or CURRENT_SPEAKING_TARGET != "audience") else "大家")),
-            is_direct_song_name=True
-        )),
-        (r'(?:pe\.)?compose_and_play_original_piano\((?:[^)]*)\)', lambda m: pe.compose_and_play_original_piano(
-            theme_or_title=(re.search(r'(?:theme_or_title|theme|title)\s*=\s*[\'"]([^\'"]+)[\'"]', m.group(0)).group(1) if re.search(r'(?:theme_or_title|theme|title)\s*=\s*[\'"]([^\'"]+)[\'"]', m.group(0)) else ""), 
-            mood_or_style=(re.search(r'(?:mood_or_style|mood|style)\s*=\s*[\'"]([^\'"]+)[\'"]', m.group(0)).group(1) if re.search(r'(?:mood_or_style|mood|style)\s*=\s*[\'"]([^\'"]+)[\'"]', m.group(0)) else ""), 
-            target=(caller_target or ("audience" if CURRENT_SPEAKING_TARGET == "audience" else "dad")),
-            requester_name=(caller_user or ("老爸" if (caller_target == "dad" or CURRENT_SPEAKING_TARGET != "audience") else "大家"))
-        )),
-        (r'(?:pe\.)?mashup_virtual_piano\((?:[^)]*)\)', lambda m: pe.mashup_virtual_piano(*(re.findall(r'[\'"]([^\'"]+)[\'"]', m.group(0))))),
-        (r'(?:pe\.)?insert_virtual_piano\(\s*(?:song_name\s*=\s*)?[\'"]([^\'"]+)[\'"](?:[^)]*)\)', lambda m: pe.insert_virtual_piano(song_name=m.group(1))),
-        (r'(?:auto_sing_song|sing_song)\(\s*(?:song_name\s*=\s*)?[\'"]([^\'"]+)[\'"](?:[^)]*)\)', lambda m: produce_and_sing_cover(m.group(1))),
-        (r'(?:generate_ai_image|draw_illustration)\(\s*(?:prompt\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: generate_ai_image(m.group(1))),
-        (r'execute_local_python_code\(\s*(?:code_string\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: execute_local_python_code(m.group(1))),
-        (r'move_spatial_position\(\s*(?:target_position\s*=\s*|position_name\s*=\s*)?[\'"]([^\'"]+)[\'"](?:[^)]*)\)', lambda m: apply_spatial_position(m.group(1))),
-        (r'trigger_vts_expression\(\s*(?:expression_name\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: set_vts_expression(vts, m.group(1))),
-        (r'control_microphone\(\s*(?:is_enabled\s*=\s*)?(True|False)\s*\)', lambda m: control_microphone(m.group(1).lower() == 'true')),
-        (r'clear_all_memories\(\s*\)', lambda m: clear_all_memories()),
-        (r'(?:pe\.)?set_timer\((?:[^)]*)\)', lambda m: set_timer(
-            int(re.search(r'\b(\d+)\b', m.group(0)).group(1)) if re.search(r'\b(\d+)\b', m.group(0)) else 60,
-            (re.findall(r'[\'"]([^\'"]+)[\'"]', m.group(0))[0] if re.findall(r'[\'"]([^\'"]+)[\'"]', m.group(0)) else "鬧鐘時間到"),
-            input_queue
-        )),
-        (r'search_google\(\s*(?:query\s*=\s*)?[\'"]([^\'"]+)[\'"]\s*\)', lambda m: search_google(m.group(1))),
-        (r'update_cloud_knowledge\((?:[^)]*)\)', lambda m: update_cloud_prompt_field(
-            (re.search(r'category\s*=\s*[\'"]([^\'"]+)[\'"]', m.group(0)).group(1) if re.search(r'category\s*=\s*[\'"]([^\'"]+)[\'"]', m.group(0)) else "facts"),
-            (re.search(r'content\s*=\s*[\'"]([^\'"]+)[\'"]', m.group(0)).group(1) if re.search(r'content\s*=\s*[\'"]([^\'"]+)[\'"]', m.group(0)) else (re.findall(r'[\'"]([^\'"]+)[\'"]', m.group(0))[-1] if re.findall(r'[\'"]([^\'"]+)[\'"]', m.group(0)) else ""))
-        ))
-    ]
-    
-    for pattern, func in universal_tool_calls:
-        while True:
-            match = re.search(pattern, text, re.IGNORECASE)
-            if not match:
-                break
-            cmd_name = match.group(0).strip()
-            log_print(f"🛠️ [通用指令攔截] 檢測到 Python 呼叫: {cmd_name}，立即自動執行！")
-            async def _safe_run_intercepted_tool(coro, cmd_s):
-                try:
-                    if asyncio.iscoroutine(coro):
-                        await coro
-                    elif callable(coro):
-                        res = coro()
-                        if asyncio.iscoroutine(res):
-                            await res
-                except Exception as err:
-                    log_print(f"❌ [通用指令執行異常]: {cmd_s} ➔ {err}")
-            asyncio.create_task(_safe_run_intercepted_tool(func(match), cmd_name))
-            has_dispatched_tool = True
-            text = text.replace(match.group(0), "")
-
-    url_match = re.search(r'\[OPEN_BROWSER:\s*([^\]]+)\]', text, re.IGNORECASE)
-    if url_match:
-        url = url_match.group(1).strip()
-        if not url.startswith('http'):
-            url = 'https://' + url
-        try:
-            webbrowser.open(url)
-            log_print(f"🌐 [系統動作] 7L 幫你打開了網頁: {url}")
-        except Exception as e:
-            log_print(f"❌ [開啟網頁失敗]: {e}")
-
-    # 若指定立即執行視覺動作 (例如安靜沉思不發聲時的微眼神/微表情)
-    if execute_visuals:
-        await execute_speech_visual_actions(vts, text)
-
-    clean_text = TextCleanEngine.clean_speech_text(text)
-    return clean_text
-
-# ────────────────────────────────────────────────────────
-# ⚙️ 14. 專屬背景工作協程群 (Workers)
-# ────────────────────────────────────────────────────────
-
-# --- 🎤 語音與收音協程 ---
-is_user_listening = False
-listen_start_time = 0.0
-
-async def mic_volume_worker():
-    global current_mic_volume_str, CURRENT_MIC_VOL_PERCENT
-    
-    stream = None
-    if HAS_PYAUDIO:
-        try:
-            import pyaudio
-            p = pyaudio.PyAudio()
-            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
-        except Exception:
-            pass 
-
-    while True:
-        if not IS_MIC_ENABLED:
-            current_mic_volume_str = "[🔴 麥克風已關閉]"
-            CURRENT_MIC_VOL_PERCENT = 0
-            await asyncio.sleep(0.3)
-            continue
-
-        # 🎙️ 全雙工真·不鎖麥：已有專屬聲紋辨識 (WeSpeaker/Voiceprint)，發話中依然保持全時收音監測與音量跳動
-        if stream:
-            try:
-                frames_avail = stream.get_read_available()
-                if frames_avail > 0:
-                    data = stream.read(frames_avail, exception_on_overflow=False)
-                    audio_data = np.frombuffer(data, dtype=np.int16)
-                    if len(audio_data) > 0:
-                        rms = np.sqrt(np.mean(np.square(audio_data.astype(np.float32))))
-                        vol_percent = min(100, int((rms / 2500) * 100))
-                        CURRENT_MIC_VOL_PERCENT = vol_percent
-                        bars = vol_percent // 10
-                        bar_str = "█" * bars + "_" * (10 - bars)
-                        current_mic_volume_str = f"[🎤 收音: {vol_percent:02d}% |{bar_str}|]"
-                await asyncio.sleep(0.05) 
-            except Exception:
-                current_mic_volume_str = "[🟢 麥克風全時就緒]"
-                CURRENT_MIC_VOL_PERCENT = 0
-                await asyncio.sleep(0.5)
-        else:
-            current_mic_volume_str = "[🟢 麥克風全時就緒]"
-            CURRENT_MIC_VOL_PERCENT = 0
-            await asyncio.sleep(0.5)
-
-