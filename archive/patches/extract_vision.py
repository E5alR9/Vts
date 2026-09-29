async def ai_face_tracking_loop(vts):
    global current_ai_state, IS_MP3_PLAYING, CURRENT_PLAYING_VOICE_TASK
    t = 0.0
    blink_timer = time.time() + random.uniform(3.5, 6.0)
    blink_start_time = 0.0
    is_blinking = False
    
    curr_x, curr_y, curr_z = 0.0, 0.0, 0.0
    curr_eye_x, curr_eye_y = 0.0, 0.0
    smooth_piano_focus_x = 0.0
    auto_mouse_track_timer = 0.0  
    
    while True:
        try:
            now = time.time()
            is_playing = False
            try:
                is_playing = IS_MP3_PLAYING or (pygame.mixer.get_init() and pygame.mixer.music.get_busy())
            except Exception:
                pass

            if current_ai_state == "IDLE" and not is_playing and not vc.is_tracking_mouse:
                if auto_mouse_track_timer > 0:
                    auto_mouse_track_timer -= 0.05
                    if auto_mouse_track_timer <= 0:
                        vc.target_look_x = 0.0
                        vc.target_look_y = 0.0
                else:
                    if random.random() < 0.005:  
                        auto_mouse_track_timer = random.uniform(2.0, 4.0)  
            else:
                if auto_mouse_track_timer > 0:
                    auto_mouse_track_timer = 0.0
                    if not vc.is_tracking_mouse:
                        vc.target_look_x = 0.0
                        vc.target_look_y = 0.0

            is_currently_tracking = vc.is_tracking_mouse or auto_mouse_track_timer > 0

            if is_currently_tracking:
                sw, sh = pyautogui.size()
                px, py = pyautogui.position()
                nx, ny = (px / sw) - 0.5, (py / sh) - 0.5
                vc.target_look_x, vc.target_look_y = nx * 28.0, ny * -20.0

            vc.current_look_x += (vc.target_look_x - vc.current_look_x) * 0.08
            vc.current_look_y += (vc.target_look_y - vc.current_look_y) * 0.08

            # 🌟 自然真實眨眼機制 (每 3.5~6.5 秒眨眼一次，閉眼時間精確為 0.14 秒，徹底杜絕快速連眨)
            eye_open_left = 1.0
            eye_open_right = 1.0
            if vc.force_blink_trigger > 0:
                if not is_blinking:
                    is_blinking = True
                    blink_start_time = now
                    vc.force_blink_trigger = 0
            elif not is_blinking and now > blink_timer:
                is_blinking = True
                blink_start_time = now

            if is_blinking:
                if now - blink_start_time < 0.14:
                    eye_open_left = 0.0
                    eye_open_right = 0.0
                else:
                    eye_open_left = 1.0
                    eye_open_right = 1.0
                    is_blinking = False
                    blink_timer = now + random.uniform(3.5, 6.5)
            else:
                eye_open_left = 1.0
                eye_open_right = 1.0

            # 🌟 靈動眼珠與鋼琴音符密集處視線追蹤計算
            if vc.eye_roll_timer > now:
                # 🌀 招牌靈動大轉眼珠 / 大圈環視四周 (俐落 360° 滿幅滿力道 1.0 大圓周軌跡)
                target_eye_x = math.sin(t * 4.2) * 1.0
                target_eye_y = math.cos(t * 4.2) * 1.0
                curr_eye_x = target_eye_x
                curr_eye_y = target_eye_y
            elif pe.is_piano_active:
                # 🎹 只要處於鋼琴彈奏狀態中：眼神永遠精準朝下追蹤琴鍵音符密集重心
                smooth_piano_focus_x += (pe.PIANO_NOTE_FOCUS_X - smooth_piano_focus_x) * 0.25
                target_eye_x = max(-0.85, min(0.85, smooth_piano_focus_x / 16.0))
                target_eye_y = -0.75
                curr_eye_x += (target_eye_x - curr_eye_x) * 0.15
                curr_eye_y += (target_eye_y - curr_eye_y) * 0.15
            elif is_currently_tracking:
                # 滑鼠游標注視
                target_eye_x = max(-0.85, min(0.85, vc.current_look_x / 20.0))
                target_eye_y = max(-0.85, min(0.85, vc.current_look_y / 15.0))
                curr_eye_x += (target_eye_x - curr_eye_x) * 0.15
                curr_eye_y += (target_eye_y - curr_eye_y) * 0.15
            elif current_ai_state == "THINKING":
                # 思考中視線往斜上方
                target_eye_x = -0.38
                target_eye_y = 0.55
                curr_eye_x += (target_eye_x - curr_eye_x) * 0.15
                curr_eye_y += (target_eye_y - curr_eye_y) * 0.15
            else:
                # 待命/說話時微幅靈動眼神
                target_eye_x = math.sin(t * 0.8) * 0.30 + (vc.current_look_x / 28.0) * 0.4
                target_eye_y = math.cos(t * 0.6) * 0.20 + (vc.current_look_y / 20.0) * 0.4
                curr_eye_x += (target_eye_x - curr_eye_x) * 0.15
                curr_eye_y += (target_eye_y - curr_eye_y) * 0.15

            target_angle_x = 0.0
            target_angle_y = 0.0
            target_angle_z = 0.0
            target_mouth = 0.0

            # 👄 真實音訊波形精準對嘴：完全根據音訊逐幀 RMS 振幅與快開慢合物理平滑決定！
            if is_playing:
                global CURRENT_MOUTH_ENVELOPE, CURRENT_SPEECH_START_TIME, CURRENT_SMOOTH_MOUTH
                if CURRENT_MOUTH_ENVELOPE and CURRENT_SPEECH_START_TIME > 0:
                    elapsed = now - CURRENT_SPEECH_START_TIME
                    frame_idx = int(elapsed * 25.0)
                    if 0 <= frame_idx < len(CURRENT_MOUTH_ENVELOPE):
                        raw_target = CURRENT_MOUTH_ENVELOPE[frame_idx]
                    else:
                        raw_target = 0.0
                    
                    # 🎙️ 快開慢合 (Fast Attack 0.65, Gentle Release 0.35) 物理濾波，徹底告別卡頓與僵硬
                    if raw_target > CURRENT_SMOOTH_MOUTH:
                        CURRENT_SMOOTH_MOUTH += (raw_target - CURRENT_SMOOTH_MOUTH) * 0.65
                    else:
                        CURRENT_SMOOTH_MOUTH += (raw_target - CURRENT_SMOOTH_MOUTH) * 0.35
                    target_mouth = round(CURRENT_SMOOTH_MOUTH, 3)
                else:
                    # 若無波形包絡 (如音訊加載間隙)，使用具備自然閉口零點的靈動音節波
                    osc = (math.sin(t * 18.0) * 0.5 + 0.5) * (math.sin(t * 8.0) * 0.5 + 0.5)
                    target_mouth = round(osc * 0.70, 3)
            else:
                CURRENT_SMOOTH_MOUTH = 0.0
                target_mouth = 0.0

            # 姿態與頭部運動計算
            if pe.is_piano_active:
                # 🎹 鋼琴彈奏中：頭部與身體重心專注在鍵盤，隨音符高低音律動傾斜（說話時僅動嘴，姿態不變）
                smooth_piano_focus_x += (pe.PIANO_NOTE_FOCUS_X - smooth_piano_focus_x) * 0.25
                target_angle_x = smooth_piano_focus_x * 0.65 + math.sin(t * 1.2) * 2.5
                target_angle_y = -10.0 + math.cos(t * 1.5) * 1.5
                target_angle_z = smooth_piano_focus_x * 0.30 + math.sin(t * 1.0) * 2.0
            elif is_playing:
                # 🗣️ MP3 播放中：頭部溫和自然微幅呼吸點頭
                target_angle_x = math.sin(t * 1.0) * 1.5 + vc.current_look_x * 0.25
                target_angle_y = math.cos(t * 0.8) * 0.8 + vc.current_look_y * 0.25
                target_angle_z = math.sin(t * 0.7) * 1.0
            elif is_currently_tracking:
                target_angle_x = vc.current_look_x
                target_angle_y = vc.current_look_y
                target_angle_z = 0.0
            else:
                if current_ai_state == "IDLE":
                    target_angle_x = math.sin(t * 0.4) * 2.0 + vc.current_look_x * 0.3
                    target_angle_y = math.cos(t * 0.3) * 1.0 + vc.current_look_y * 0.3
                    target_angle_z = math.sin(t * 0.3) * 1.0
                elif current_ai_state == "THINKING":
                    target_angle_x = -2.0 + vc.current_look_x * 0.2
                    target_angle_y = 2.0 + vc.current_look_y * 0.2
                    target_angle_z = 4.5
                elif current_ai_state == "TALKING":
                    target_angle_x = vc.current_look_x
                    target_angle_y = vc.current_look_y
                    target_angle_z = 0.0

            if vc.eye_roll_timer > now:
                target_angle_z += math.sin(t * 4.2) * 3.5
                target_angle_y += math.cos(t * 4.2) * 2.0

            # 🌟 純物理動力學縮小瞳孔與震驚 (EyeOpen=2.0 瞪大縮瞳 + 物理高頻恐懼顫抖)
            # 🎙️ 發話期間若有物理表情，持續延長鎖定，確保說話全程不中途褪去
            if CURRENT_PLAYING_VOICE_TASK is not None:
                if vc.shock_timer > 0:
                    vc.shock_timer = max(vc.shock_timer, now + 1.0)
                if vc.frown_timer > 0:
                    vc.frown_timer = max(vc.frown_timer, now + 1.0)

            is_in_shock = (vc.shock_timer > now)
            is_frowning = (vc.frown_timer > now)
            if is_in_shock:
                eye_open_left = 2.0
                eye_open_right = 2.0
                target_brows = 0.85
                target_mouth_smile = 0.35
                if not is_playing:
                    target_mouth = 0.20  # 震驚未發話時微張嘴 (呆滯/倒抽氣)；發話時保持正常對嘴開合
                target_angle_x += math.sin(t * 38.0) * 0.35
                target_angle_y += math.sin(t * 34.0) * 0.30
                target_angle_z += math.cos(t * 36.0) * 0.40
                curr_eye_x += math.sin(t * 30.0) * 0.03
                curr_eye_y += math.cos(t * 28.0) * 0.03
            elif is_frowning:
                # 🌟 傲嬌/困擾/委屈 皺眉表情 (Brows = 0.0 壓低眉毛形成八字皺眉 + 微撇嘴/微嘟嘴)
                eye_open_left = 0.95
                eye_open_right = 0.95
                target_brows = 0.0
                target_mouth_smile = 0.25
                target_angle_z += math.sin(t * 1.5) * 2.0
                target_angle_y += -1.5
            elif vc.wink_timer > now:
                # 🌟 俏皮靈動單邊眨一下眼 (Wink: 總時長 0.55 秒，眨一下立即順暢張開)
                elapsed_wink = 0.55 - (vc.wink_timer - now)
                if elapsed_wink < 0.10:
                    wink_eye_open = max(0.0, 1.0 - (elapsed_wink / 0.10))
                elif elapsed_wink <= 0.32:
                    wink_eye_open = 0.0
                else:
                    wink_eye_open = min(1.0, (elapsed_wink - 0.32) / 0.23)

                if vc.wink_side == "left":
                    eye_open_left = wink_eye_open
                    eye_open_right = 1.0
                    target_angle_z += 3.5 * (1.0 - wink_eye_open)
                else:
                    eye_open_left = 1.0
                    eye_open_right = wink_eye_open
                    target_angle_z += -3.5 * (1.0 - wink_eye_open)
                target_brows = 0.50
                target_mouth_smile = 0.50 + 0.35 * (1.0 - wink_eye_open)
            else:
                # 🌟 平時自然溫和中性眉毛 (0.50) 與自然微笑 (0.50，發話時隨開口度靈動上揚)
                target_brows = 0.50
                target_mouth_smile = min(1.0, 0.50 + 0.20 * target_mouth) if is_playing else 0.50

            curr_x += (target_angle_x - curr_x) * 0.10
            curr_y += (target_angle_y - curr_y) * 0.10
            curr_z += (target_angle_z - curr_z) * 0.10

            param_values = [
                {"id": "FaceAngleX", "value": curr_x, "weight": 1.0},
                {"id": "FaceAngleY", "value": curr_y, "weight": 1.0},
                {"id": "FaceAngleZ", "value": curr_z, "weight": 1.0},
                {"id": "EyeLeftX", "value": curr_eye_x, "weight": 1.0},
                {"id": "EyeLeftY", "value": curr_eye_y, "weight": 1.0},
                {"id": "EyeRightX", "value": curr_eye_x, "weight": 1.0},
                {"id": "EyeRightY", "value": curr_eye_y, "weight": 1.0},
                {"id": "EyeOpenLeft", "value": eye_open_left, "weight": 1.0},
                {"id": "EyeOpenRight", "value": eye_open_right, "weight": 1.0},
                {"id": "Brows", "value": target_brows, "weight": 1.0},
                {"id": "MouthSmile", "value": target_mouth_smile, "weight": 1.0},
                {"id": "MouthOpen", "value": target_mouth, "weight": 1.0}
            ]

            if hasattr(vts, 'inject_parameters'):
                await vts.inject_parameters(param_values)
            else:
                vts_data = {
                    "apiName": "VTubeStudioPublicAPI", "apiVersion": "1.0", "requestID": "AIStateTracking",
                    "messageType": "InjectParameterDataRequest",
                    "data": {
                        "faceFound": True,
                        "mode": "set",
                        "parameterValues": param_values
                    }
                }
                async with vc.vts_lock:
                    await asyncio.wait_for(vts.request(vts_data), timeout=0.5)

        except Exception:
            pass

        t += 0.08
        await asyncio.sleep(0.04)

def capture_screen_multi_view():
    """
    五方多視角超高清螢幕感知系統 (DXGI GPU 加速 + 硬件級 StretchBlt 極速引擎)：
    1. 🖥️ 全螢幕全景總覽圖 (含原生真實滑鼠游標貼圖)
    2. 🔍 左上象限原生細節放大圖 (Top-Left)
    3. 🔍 右上象限原生細節放大圖 (Top-Right)
    4. 🔍 左下象限原生細節放大圖 (Bottom-Left)
    5. 🔍 右下象限原生細節放大圖 (Bottom-Right)
    """
    global has_printed_vision_error
    try:
        from PIL import ImageDraw, Image
        import io
        
        screenshot = None
        
        # 1. 優先嘗試 DXGI 顯存直出 (若遊戲反作弊未阻擋，僅耗 1~3ms)
        cam = get_dxcam_cam()
        if cam is not None:
            try:
                frame = cam.grab()
                if frame is not None:
                    screenshot = Image.fromarray(frame)
            except Exception:
                pass
                
        # 2. 高效 GDI 硬件級 StretchBlt 備援引擎 (耗時僅 ~10ms，零例外重試，抗遊戲反作弊)
        if screenshot is None:
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            w = user32.GetSystemMetrics(0)
            h = user32.GetSystemMetrics(1)
            target_w = 1920 if w > 1920 else w
            target_h = int(h * (target_w / w))
            
            hdesk = user32.GetDesktopWindow()
            desk_dc = user32.GetWindowDC(hdesk)
            img_dc = gdi32.CreateCompatibleDC(desk_dc)
            mem_bmp = gdi32.CreateCompatibleBitmap(desk_dc, target_w, target_h)
            gdi32.SelectObject(img_dc, mem_bmp)
            
            # 硬件級抗鋸齒縮放 (4K ➔ 1080P 直接在驅動層完成，免 CPU Lanczos 負擔)
            gdi32.SetStretchBltMode(img_dc, 4) # 4 = HALFTONE
            gdi32.StretchBlt(img_dc, 0, 0, target_w, target_h, desk_dc, 0, 0, w, h, 0x00CC0020)
            
            class BITMAPINFOHEADER(ctypes.Structure):
                _fields_ = [
                    ('biSize', ctypes.c_uint32), ('biWidth', ctypes.c_int32), ('biHeight', ctypes.c_int32),
                    ('biPlanes', ctypes.c_uint16), ('biBitCount', ctypes.c_uint16), ('biCompression', ctypes.c_uint32),
                    ('biSizeImage', ctypes.c_uint32), ('biXPelsPerMeter', ctypes.c_int32), ('biYPelsPerMeter', ctypes.c_int32),
                    ('biClrUsed', ctypes.c_uint32), ('biClrImportant', ctypes.c_uint32)
                ]
            bmi = BITMAPINFOHEADER()
            bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bmi.biWidth = target_w
            bmi.biHeight = -target_h
            bmi.biPlanes = 1
            bmi.biBitCount = 32
            bmi.biCompression = 0
            buf = ctypes.create_string_buffer(target_w * target_h * 4)
            gdi32.GetDIBits(img_dc, mem_bmp, 0, target_h, buf, ctypes.byref(bmi), 0)
            screenshot = Image.frombuffer('RGBA', (target_w, target_h), buf, 'raw', 'BGRA', 0, 1).convert('RGB')
            gdi32.DeleteObject(mem_bmp)
            gdi32.DeleteDC(img_dc)
            user32.ReleaseDC(hdesk, desk_dc)

        if screenshot is None:
            return None

        if screenshot.mode != "RGB":
            screenshot = screenshot.convert("RGB")
            
        w, h = screenshot.size
        # 根據實際截圖解析度與系統原始解析度比例調整滑鼠游標座標
        orig_w = ctypes.windll.user32.GetSystemMetrics(0)
        orig_h = ctypes.windll.user32.GetSystemMetrics(1)
        scale_x = w / max(1, orig_w)
        scale_y = h / max(1, orig_h)
        mx_raw, my_raw = pyautogui.position()
        mx = int(mx_raw * scale_x)
        my = int(my_raw * scale_y)
        
        # 🖱️ 自然貼合原生真實滑鼠游標圖標
        cursor_icon = get_realistic_cursor_icon()
        if cursor_icon:
            try:
                screenshot.paste(cursor_icon, (max(0, min(w - 1, mx)), max(0, min(h - 1, my))), cursor_icon)
            except Exception:
                pass
        
        # 1. 全螢幕全景總覽圖
        buf_full = io.BytesIO()
        screenshot.save(buf_full, format="JPEG", quality=75)
        full_b64 = base64.b64encode(buf_full.getvalue()).decode('utf-8')
        
        # 2. 四個象限細節裁切
        mid_x = w // 2
        mid_y = h // 2
        
        # 左上象限
        buf_tl = io.BytesIO()
        screenshot.crop((0, 0, mid_x, mid_y)).save(buf_tl, format="JPEG", quality=80)
        tl_b64 = base64.b64encode(buf_tl.getvalue()).decode('utf-8')
        
        # 右上象限
        buf_tr = io.BytesIO()
        screenshot.crop((mid_x, 0, w, mid_y)).save(buf_tr, format="JPEG", quality=80)
        tr_b64 = base64.b64encode(buf_tr.getvalue()).decode('utf-8')
        
        # 左下象限
        buf_bl = io.BytesIO()
        screenshot.crop((0, mid_y, mid_x, h)).save(buf_bl, format="JPEG", quality=80)
        bl_b64 = base64.b64encode(buf_bl.getvalue()).decode('utf-8')
        
        # 右下象限
        buf_br = io.BytesIO()
        screenshot.crop((mid_x, mid_y, w, h)).save(buf_br, format="JPEG", quality=80)
        br_b64 = base64.b64encode(buf_br.getvalue()).decode('utf-8')
        
        has_printed_vision_error = False
        return [
            ("🖥️【1. 全螢幕全景總覽（含滑鼠游標）】", full_b64),
            ("🔍【2. 左上角細節放大圖】", tl_b64),
            ("🔍【3. 右上角細節放大圖】", tr_b64),
            ("🔍【4. 左下角細節放大圖】", bl_b64),
            ("🔍【5. 右下角細節放大圖】", br_b64)
        ]
    except Exception as e:
        if not has_printed_vision_error:
            print(f"\n❌ [截圖系統報錯]: {e}")
            has_printed_vision_error = True
        return None
