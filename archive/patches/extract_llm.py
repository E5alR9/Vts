async def fetch_ai_response(messages, image_base64=None, audio_base64=None, is_proactive=False, request_start_time: Optional[float] = None):
    """
    🧠 多模態大腦推理總入口 (文字 + 視覺 + 音訊 + 工具調用)
    
    Args:
        messages: 對話歷史紀錄陣列
        image_base64: 五方多視角螢幕截圖 Base64 列表或單張圖片
        audio_base64: 麥克風音訊資料 Base64
        is_proactive: 是否為主動巡邏/主動找話題發話
        request_start_time: 請求發起的時間戳記（計算精確總延遲）
    """
    global current_ai_status_str, current_model_tag, CURRENT_GEMINI_KEY_STEP
    used_eye = "無"
    overall_start_time = request_start_time if request_start_time else time.time()

    # 防卡死機制：讓渡運算權，確保皮套滑順
    await asyncio.sleep(0.05)

    # 提取最新的使用者指令以供智能任務分流
    user_query = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            c = msg.get("content", "")
            if isinstance(c, str):
                user_query = c
            elif isinstance(c, list):
                user_query = " ".join([p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text"])
            break

    # ── 1. 建構通用多模態輸入 Payload (共用給所有併發通道) ──
    chat_contents = []
    system_text = ""
    for msg in messages:
        if msg["role"] == "system":
            system_text += msg["content"] + "\n\n"
            
    for msg in messages:
        if msg["role"] == "system": continue
        raw_content = msg["content"]
        if isinstance(raw_content, list):
            text = " ".join([p["text"] for p in raw_content if p.get("type") == "text"])
        else:
            text = raw_content
            
        if not chat_contents and system_text:
            text = system_text + text
            
        role = "user" if msg["role"] == "user" else "model"
        chat_contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))

    if image_base64:
        user_parts = []
        if isinstance(image_base64, list):
            for item in image_base64:
                if isinstance(item, tuple):
                    label, img_b64 = item
                    img_bytes = base64.b64decode(img_b64)
                    user_parts.append(types.Part.from_text(text=f"\n{label}："))
                    user_parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
                else:
                    user_parts.append(types.Part.from_bytes(data=base64.b64decode(item), mime_type="image/jpeg"))
        else:
            image_bytes = base64.b64decode(image_base64)
            user_parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

        if user_parts:
            if chat_contents and chat_contents[-1].role == "user":
                chat_contents[-1].parts.extend(user_parts)
            else:
                chat_contents.append(types.Content(role="user", parts=user_parts))

    if audio_base64:
        try:
            if isinstance(audio_base64, str):
                raw_audio_bytes = base64.b64decode(audio_base64)
            else:
                raw_audio_bytes = audio_base64
            
            audio_part = types.Part.from_bytes(data=raw_audio_bytes, mime_type="audio/wav")
            if chat_contents and chat_contents[-1].role == "user":
                chat_contents[-1].parts.append(audio_part)
            else:
                chat_contents.append(types.Content(role="user", parts=[audio_part]))
        except Exception as e_aud:
            log_print(f"⚠️ [音訊多模態封裝異常]: {e_aud}")

    # 構建 Interactions API 專用輸入 Payload
    interaction_input = []
    full_user_text = f"{system_text}\n\n{text}" if system_text else text
    interaction_input.append({"type": "text", "text": full_user_text})

    if image_base64:
        if isinstance(image_base64, list):
            for item in image_base64:
                if isinstance(item, tuple):
                    label, img_b64 = item
                    interaction_input.append({"type": "text", "text": f"\n{label}："})
                    interaction_input.append({"type": "image", "data": img_b64, "mime_type": "image/jpeg"})
                else:
                    interaction_input.append({"type": "image", "data": item, "mime_type": "image/jpeg"})
        else:
            interaction_input.append({"type": "image", "data": image_base64, "mime_type": "image/jpeg"})

    if audio_base64:
        aud_b64_str = audio_base64 if isinstance(audio_base64, str) else base64.b64encode(audio_base64).decode('utf-8')
        interaction_input.append({"type": "audio", "data": aud_b64_str, "mime_type": "audio/wav"})

    # ── 單一 Gemini 通道執行器 ──
    async def _call_single_gemini(g_key, g_model, target_id):
        temp_google_client = genai.Client(api_key=g_key)
        api_call_start = time.time()
        extracted_text = ""
        used_engine_tag = "一體化"

        try:
            active_tools = GENAI_PROACTIVE_TOOLS if is_proactive else GENAI_TOOLS
            config_kwargs = {"temperature": 0.85, "tools": active_tools}
            
            # 🧠 為 Gemini 3.8 / 3.7 / 2.5 等旗艦模型開啟原生深度思考 (Thinking)，其內在推理直接作為 7L 私密心聲
            if any(k in g_model for k in ["3.8", "3.7", "2.5", "3-flash", "3.1-pro"]):
                try:
                    config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=-1)
                except Exception:
                    pass

            gen_config = types.GenerateContentConfig(**config_kwargs)

            # 👑 放寬單通道等待時間至 120 秒，讓 3.8 / 3.7-flash 深度思考、多模態與工具調用在背景充裕完成，絕不 premature timeout！
            response = await asyncio.wait_for(
                temp_google_client.aio.models.generate_content(
                    model=g_model,
                    contents=chat_contents,
                    config=gen_config
                ),
                timeout=120.0
            )

            had_tool_calls = False
            tool_results_map = {}
            if hasattr(response, 'function_calls') and response.function_calls:
                had_tool_calls = True
                call_names = [getattr(fc, 'name', '') for fc in response.function_calls]
                for fc in response.function_calls:
                    fn_name = getattr(fc, 'name', '')
                    fn_args = getattr(fc, 'args', {}) or {}
                    if fn_name == "pe.stop_virtual_piano" and "open_virtual_piano" in call_names:
                        log_print(f"🛡️ [工具衝突過濾] 同回合同時包含 open_virtual_piano 與 pe.stop_virtual_piano，已自動過濾 pe.stop_virtual_piano！")
                        continue
                    log_print(f"🛠️ [大腦調用工具] {fn_name}({fn_args})")
                    tool_out = await execute_tool_dispatch(fn_name, fn_args, caller_target="dad", caller_user="老爸")
                    tool_results_map[fn_name] = tool_out
                    # ⚠️ 資訊查詢與系統提示類資料僅供大腦吸收，嚴禁拼入 extracted_text 作為口語！
                    if fn_name not in ["search_google"] and tool_out and "[EXPRESSION:" in tool_out:
                        extracted_text += f" {tool_out}"

            model_speech = ""
            thought_text = ""
            try:
                if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                    for p in response.candidates[0].content.parts:
                        if getattr(p, 'thought', False) and getattr(p, 'text', ''):
                            thought_text += p.text + " "
                        elif getattr(p, 'text', '') and not getattr(p, 'thought', False):
                            model_speech += p.text + " "
                if not model_speech.strip() and response.text:
                    model_speech = response.text.strip()
            except Exception:
                try:
                    if response.text:
                        model_speech = response.text.strip()
                except Exception:
                    pass

            if thought_text.strip() and "[THOUGHT:" not in model_speech and "[THINK:" not in model_speech:
                model_speech = f"[THOUGHT: {thought_text.strip()}] {model_speech}".strip()

            # 🌟 當調用了資訊類工具 (如 search_google) 或第一輪未輸出台詞時：
            # 立即發起第二輪 Function Response 請求，將搜尋結果反饋給大腦進行深度思考、消化整理並輸出自然口語！
            if had_tool_calls:
                needs_stage2 = any(getattr(fc, 'name', '') == 'search_google' for fc in response.function_calls) or not model_speech.strip()
                if needs_stage2:
                    stage2_done = False
                    try:
                        followup_contents = list(chat_contents)
                        if response.candidates and response.candidates[0].content:
                            followup_contents.append(response.candidates[0].content)
                        else:
                            call_parts = [types.Part.from_function_call(name=getattr(fc, 'name', ''), args=getattr(fc, 'args', {}) or {}) for fc in response.function_calls]
                            followup_contents.append(types.Content(role="model", parts=call_parts))

                        fn_resp_parts = []
                        for fc in response.function_calls:
                            f_name = getattr(fc, 'name', '')
                            f_res = tool_results_map.get(f_name, "執行成功")
                            fn_resp_parts.append(types.Part.from_function_response(
                                name=f_name,
                                response={
                                    "result": str(f_res),
                                    "instruction": "請根據以上查詢結果，以 7L 招牌自然隨性口吻（1~3句短句，40~80字以內）直接對老爸提煉並說明重點，嚴禁照抄條列清單、網址或網頁標題！"
                                }
                            ))
                        followup_contents.append(types.Content(role="user", parts=fn_resp_parts))

                        stage2_resp = await asyncio.wait_for(
                            temp_google_client.aio.models.generate_content(
                                model=g_model,
                                contents=followup_contents,
                                config=types.GenerateContentConfig(temperature=0.85)
                            ),
                            timeout=25.0
                        )
                        s2_speech = ""
                        s2_thought = ""
                        if stage2_resp and stage2_resp.candidates and stage2_resp.candidates[0].content and stage2_resp.candidates[0].content.parts:
                            for p in stage2_resp.candidates[0].content.parts:
                                if getattr(p, 'thought', False) and getattr(p, 'text', ''):
                                    s2_thought += p.text + " "
                                elif getattr(p, 'text', '') and not getattr(p, 'thought', False):
                                    s2_speech += p.text + " "
                        if not s2_speech.strip() and stage2_resp and stage2_resp.text:
                            s2_speech = stage2_resp.text.strip()

                        if s2_speech.strip():
                            model_speech = s2_speech.strip()
                            if s2_thought.strip() and "[THOUGHT:" not in model_speech and "[THINK:" not in model_speech:
                                model_speech = f"[THOUGHT: {s2_thought.strip()}] {model_speech}".strip()
                            stage2_done = True
                    except Exception as e_s2:
                        log_print(f"⚠️ [搜尋情報第二輪主通道整合異常]: {e_s2} ➔ 即刻切換極速備份模型整理")

                    # 若第二輪主通道因 503 等原因失敗，且調用了 search_google，立即啟動極速提煉器整理成自然口語
                    if not stage2_done and any(getattr(fc, 'name', '') == 'search_google' for fc in response.function_calls):
                        s_query = next((getattr(fc, 'args', {}).get('query', '') for fc in response.function_calls if getattr(fc, 'name', '') == 'search_google'), user_query)
                        s_raw = tool_results_map.get("search_google", "")
                        model_speech = await summarize_search_to_speech(s_query, s_raw, user_role_name="老爸")

            # 🌟 採用 Gemini 生成的口語回覆；若調用工具帶有標籤則一併保留
            if model_speech:
                tags_in_tool = " ".join(re.findall(r'\[[A-Z_]+(?::\s*[^\]]+)?\]', extracted_text))
                valid_tags = [t for t in tags_in_tool.split() if not any(x in t for x in ["HAD_TOOL_CALL", "SEARCH", "GOOGLE"])]
                clean_tags_str = " ".join(valid_tags)
                extracted_text = f"{model_speech} {clean_tags_str}".strip()
            else:
                if any(getattr(fc, 'name', '') == 'search_google' for fc in response.function_calls):
                    s_query = next((getattr(fc, 'args', {}).get('query', '') for fc in response.function_calls if getattr(fc, 'name', '') == 'search_google'), user_query)
                    s_raw = tool_results_map.get("search_google", "")
                    extracted_text = await summarize_search_to_speech(s_query, s_raw, user_role_name="老爸")
                elif "pe.play_virtual_piano" in tool_results_map:
                    piano_fc = next((fc for fc in response.function_calls if getattr(fc, 'name', '') == 'pe.play_virtual_piano'), None)
                    p_name = pe.clean_song_title_for_speech(getattr(piano_fc, 'args', {}).get('song_name', '')) if piano_fc else ''
                    if pe.is_piano_active and pe.current_piano_song_title:
                        extracted_text = f"[EXPRESSION: 星星眼] 老爸，沒問題！《{p_name or '這首'}》我先幫你排進清單，等現在這首彈完馬上幫你彈喔！"
                    else:
                        extracted_text = f"[EXPRESSION: 星星眼] 老爸，這就來為你彈《{p_name or '這首'}》！"
                elif "pe.compose_and_play_original_piano" in tool_results_map:
                    extracted_text = f"[EXPRESSION: 星星眼] 老爸，收到！我現在就現場為你創作一首原創鋼琴曲，聽聽看喔！"
                elif "pe.mashup_virtual_piano" in tool_results_map:
                    extracted_text = f"[EXPRESSION: 星星眼] 老爸，收到！雙曲狂暴合奏這就來！"
                else:
                    extracted_text = TextCleanEngine.remove_system_hints(extracted_text).strip()

            if extracted_text.strip() or had_tool_calls:
                api_duration = time.time() - api_call_start
                return (extracted_text.strip(), used_engine_tag, api_duration, g_model, target_id)
            raise ValueError(f"通道 {target_id} 未回傳有效文字內容")

        except asyncio.CancelledError:
            return None
        except (asyncio.TimeoutError, TimeoutError):
            # ⏳ 屬於背景深度思考或已由其他競速通道搶答，不視為大腦異常，絕不鎖定金鑰通道！
            return None
        except Exception as e:
            if isinstance(e, (asyncio.TimeoutError, TimeoutError)) or "timeout" in type(e).__name__.lower():
                return None
            err_str = str(e).lower()
            record_model_failure(g_model, err_str)
            if "503" in err_str or "unavailable" in err_str or "high demand" in err_str:
                lock_target(target_id, "503 high demand")
            elif "404" in err_str or "not_found" in err_str or "no longer available" in err_str:
                if 'DEAD_GEMINI_MODELS' in globals():
                    DEAD_GEMINI_MODELS.add(g_model)
                lock_entire_model(g_model, duration=get_seconds_until_pt_midnight(), reason="404 下架/未開通")
                lock_target(target_id, "404 not found")
            elif "429" in err_str or "rate limit" in err_str or "resource" in err_str or "quota" in err_str:
                lock_target(target_id, str(e))
            elif "timeouterror" in err_str or "timeout" in err_str:
                pass
            else:
                clean_err = str(e).replace('\n', ' ').strip()[:50]
                display_err = clean_err if clean_err else type(e).__name__
                log_print(f"⚠️ [大腦異常] 通道 {target_id}: {display_err}")
                lock_target(target_id, "wait 30s")
            return None

    # 🌟 第一防線：主力 Gemini 旗艦大腦（5 秒階梯式併發競速：5秒未回覆時原請求不中斷，加開新通道雙軌/多軌搶答！）
    max_gemini_attempts = 45 
    active_gemini_tasks = {}  # task -> (target_id, g_model, start_time)
    launched_gemini_targets = set()

    while len(launched_gemini_targets) < max_gemini_attempts:
        await asyncio.sleep(0.01)
        
        # 嚴格限制同時進行的通道數最多為 2 個，杜絕同時爆發 20 個併發把所有金鑰配額瞬間打滿
        if len(active_gemini_tasks) < 2:
            channels = get_available_gemini_channels(limit=5, user_query=user_query, has_image=bool(image_base64), is_proactive=is_proactive)
            candidate = None
            for ch in channels:
                if ch[2] not in launched_gemini_targets:
                    candidate = ch
                    break

            if candidate:
                g_key, g_model, target_id = candidate
                launched_gemini_targets.add(target_id)
                
                # 每次依序派發一個通道，立即推進交替序輪指針至下一回步數
                CURRENT_GEMINI_KEY_STEP += 1

                task = asyncio.create_task(_call_single_gemini(g_key, g_model, target_id))
                active_gemini_tasks[task] = (target_id, g_model, time.time())
                
                status_prefix = "👁️🧠" if image_base64 else "🧠"
                concurrent_count = len(active_gemini_tasks)
                concur_tag = f" [雙軌搶答: {concurrent_count}]" if concurrent_count > 1 else ""
                current_ai_status_str = f"{status_prefix} {g_model} [{target_id}]{concur_tag} 思考中..."
                if concurrent_count > 1:
                    log_print(f"🚀 [雙軌競速] 依序輪流加開新通道 {target_id} 搶答 (目前共 2 個通道併發)")

        if not active_gemini_tasks:
            break

        # 等待深度思考模型完成（充裕等待，不 premature timeout 搶截深度推理）
        done, _ = await asyncio.wait(
            active_gemini_tasks.keys(),
            timeout=12.0,
            return_when=asyncio.FIRST_COMPLETED
        )

        if done:
            for finished_task in done:
                t_id, m_name, t_start = active_gemini_tasks.pop(finished_task)
                try:
                    res = finished_task.result()
                    if res:
                        extracted_text, used_engine_tag, api_duration, win_model, win_tid = res
                        # 🏁 率先成功奪冠！取消其他所有背景併發中的任務
                        for rem_task in list(active_gemini_tasks.keys()):
                            rem_task.cancel()
                        active_gemini_tasks.clear()

                        total_duration = time.time() - overall_start_time
                        time_stat = f" [總耗時: {total_duration:.2f}s | 深度思考: {api_duration:.2f}s]"
                        MODEL_FAIL_COUNT[win_model] = 0
                        if image_base64 and audio_base64:
                            current_model_tag = f"🧠🎙️👁️ {win_model} ({used_engine_tag} 全模態){time_stat}"
                        elif audio_base64:
                            current_model_tag = f"🧠🎙️ {win_model} ({used_engine_tag} 音訊直連){time_stat}"
                        elif image_base64:
                            current_model_tag = f"🧠👁️ {win_model} ({used_engine_tag} 視覺){time_stat}"
                        else:
                            current_model_tag = f"🧠 {win_model} ({used_engine_tag}){time_stat}"
                        return extracted_text.strip()
                except Exception:
                    pass
        else:
            # 12 秒到期：日誌提示，原任務不中斷繼續跑，依序輪流加開雙軌！
            running_names = [active_gemini_tasks[t][0] for t in active_gemini_tasks]
            log_print(f"⏱️ [深度思考中] 通道 {', '.join(running_names)} 推理中 ➔ 原請求不中斷繼續跑，依序加開下一把金鑰熱備！")

    # 若所有通道均已啟動，等待仍在運行的任務
    if active_gemini_tasks:
        try:
            done, _ = await asyncio.wait(
                active_gemini_tasks.keys(),
                timeout=10.0,
                return_when=asyncio.FIRST_COMPLETED
            )
            for finished_task in done:
                t_id, m_name, t_start = active_gemini_tasks.pop(finished_task)
                try:
                    res = finished_task.result()
                    if res:
                        extracted_text, used_engine_tag, api_duration, win_model, win_tid = res
                        for rem_task in list(active_gemini_tasks.keys()):
                            rem_task.cancel()
                        active_gemini_tasks.clear()
                        total_duration = time.time() - overall_start_time
                        time_stat = f" [總耗時: {total_duration:.2f}s | 思考: {api_duration:.2f}s]"
                        MODEL_FAIL_COUNT[win_model] = 0
                        if image_base64 and audio_base64:
                            current_model_tag = f"🧠🎙️👁️ {win_model} ({used_engine_tag} 全模態){time_stat}"
                        elif audio_base64:
                            current_model_tag = f"🧠🎙️ {win_model} ({used_engine_tag} 音訊直連){time_stat}"
                        elif image_base64:
                            current_model_tag = f"🧠👁️ {win_model} ({used_engine_tag} 視覺){time_stat}"
                        else:
                            current_model_tag = f"🧠 {win_model} ({used_engine_tag}){time_stat}"
                        return extracted_text.strip()
                except Exception:
                    pass
        except Exception:
            pass
        for rem_task in list(active_gemini_tasks.keys()):
            rem_task.cancel()
        active_gemini_tasks.clear()

    # 🌟 第二防線：若 Gemini 旗艦大腦全部不可用且有畫面，嘗試輕量雲端餘光
    if image_base64:
        current_ai_status_str = "👁️ 備用視覺提取中 (雲端輕量版)..."
        local_desc = ""
        if not is_system_overloaded():
            try: 
                local_desc = await get_lightweight_gemini_vision(image_base64)
            except Exception: 
                pass
                
        if local_desc:
            used_eye = "gemini-lite"
            if messages and messages[-1]["role"] == "user": 
                inject_text = f"\n\n【備用視覺情報】：畫面描述: {local_desc}\n【鐵律】：畫面上的白色箭頭代表老爸當前的滑鼠游標。請注意：【除非滑鼠正指著某個你覺得很有趣、或特別值得注意的東西，否則請自然看待，不需要刻意強調滑鼠位置】。自然流暢表達，不限制說話長度！"
                
                if isinstance(messages[-1]["content"], list):
                    messages[-1]["content"].append({"type": "text", "text": inject_text})
                else:
                    messages[-1]["content"] += inject_text

    log_print("⚠️ [大腦提示] 本輪所有 Gemini 通道皆繁忙/超時，為維持純淨發話，本輪靜默略過。")
