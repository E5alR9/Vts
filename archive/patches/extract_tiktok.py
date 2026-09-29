# 📱 16.5 TikTok 直播間實時彈幕與禮物監聽模組
# ────────────────────────────────────────────────────────
TIKTOK_UNIQUE_ID = os.getenv("TIKTOK_USERNAME", "e_7l_9")
EULER_SIGN_KEY = os.getenv("SIGN_API_KEY") or os.getenv("EULERSTREAM_API_KEY")
TIKTOK_VIEWER_COUNT = 0
TIKTOK_LIKE_COUNT = 0

def get_tiktok_live_telemetry() -> str:
    """取得 TikTok 直播間即時在線觀眾人數與按讚數據情報"""
    global IS_STREAMING, TIKTOK_VIEWER_COUNT, TIKTOK_LIKE_COUNT
    if not IS_STREAMING:
        return "【📱 TikTok 直播情報】：目前離線未開播"
    return f"【📱 TikTok 直播間實時數據】：\n- 當前在線觀看人數：👥 {TIKTOK_VIEWER_COUNT} 人（若觀眾或老爸問起人數請直接依此真實數字回答）\n- 累計按讚數：❤️ {TIKTOK_LIKE_COUNT} 次\n- 當前主播帳號：@e_7l_9 (7L)"

async def tiktok_live_worker(input_queue):
    """📱 TikTok 直播聊天室實時監聽協程 (自動連線 @e_7l_9 並將彈幕/送禮/在線人數事件注入對話隊列)"""
    global IS_STREAMING
    try:
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import (
            ConnectEvent, CommentEvent, GiftEvent, LikeEvent, FollowEvent, 
            ShareEvent, DisconnectEvent, LiveEndEvent, EmoteChatEvent, BarrageEvent,
            JoinEvent, QuestionNewEvent, SubNotifyEvent, EnvelopeEvent, RoomUserSeqEvent
        )
        from TikTokLive.client.errors import SignatureRateLimitError
    except ImportError:
        log_print("⚠️ [TikTok 直播] 未安裝 TikTokLive 庫，略過 TikTok 聊天室監聽。")
        return

    tid = TIKTOK_UNIQUE_ID.strip()
    if not tid.startswith("@"):
        tid = f"@{tid}"

    if EULER_SIGN_KEY:
        os.environ["SIGN_API_KEY"] = EULER_SIGN_KEY.strip()
        log_print(f"📱 [TikTok 直播] 已載入 EulerStream API Key，正在背景監聽直播間: {tid}...")
    else:
        log_print(f"📱 [TikTok 直播] 正在準備背景監聽直播間: {tid} (使用公共簽名伺服器)...")

    # 🌟 採用 msg_id 雙重去重池 (deque + set)，容量 1000 筆，確保絕不重複處理亦不漏接訊息
    import collections
    seen_msg_ids = collections.deque(maxlen=1000)
    seen_msg_set = set()

    last_offline_notify = False
    last_like_milestone_notified = 0
    last_ambient_notify_time = 0.0

    while True:
        try:
            client = TikTokLiveClient(unique_id=tid)
            connect_timestamp = time.time()

            @client.on(ConnectEvent)
            async def on_connect(event: ConnectEvent):
                nonlocal connect_timestamp, last_offline_notify
                global IS_STREAMING, current_tiktok_status_str, TIKTOK_VIEWER_COUNT
                IS_STREAMING = True
                last_offline_notify = False
                connect_timestamp = time.time()
                v_cnt = getattr(client, 'viewer_count', 0)
                if v_cnt:
                    TIKTOK_VIEWER_COUNT = int(v_cnt)
                current_tiktok_status_str = f"[📱 {tid} 🟢 在線 ({TIKTOK_VIEWER_COUNT}人)]"
                log_print(f"✅ [TikTok 直播] 成功連接到 {tid} 直播間！(在線觀看: {TIKTOK_VIEWER_COUNT} 人 | Room ID: {client.room_id})")
                sys_notify(f"✅ TikTok 直播間連線成功 (@e_7l_9)")

            @client.on(RoomUserSeqEvent)
            async def on_room_user_seq(event: RoomUserSeqEvent):
                global TIKTOK_VIEWER_COUNT, current_tiktok_status_str
                try:
                    cnt = getattr(event, 'viewer_count', None) or getattr(event, 'total', None)
                    if cnt is not None:
                        TIKTOK_VIEWER_COUNT = int(cnt)
                        current_tiktok_status_str = f"[📱 {tid} 🟢 在線 ({TIKTOK_VIEWER_COUNT}人)]"
                except Exception:
                    pass
                sys_notify(f"✅ TikTok 直播間連線成功 (@e_7l_9)")

            @client.on(DisconnectEvent)
            async def on_disconnect(event: DisconnectEvent):
                global IS_STREAMING, current_tiktok_status_str
                IS_STREAMING = False
                current_tiktok_status_str = f"[📱 {tid} 🔌 重連中]"
                log_print(f"🔌 [TikTok 直播] 直播間 WebSocket 連線已中斷，準備自動重新連線...")

            @client.on(LiveEndEvent)
            async def on_live_end(event: LiveEndEvent):
                global IS_STREAMING, current_tiktok_status_str
                IS_STREAMING = False
                current_tiktok_status_str = f"[📱 {tid} 📺 已關播]"
                log_print(f"📺 [TikTok 直播] 直播已結束。")

            @client.on(CommentEvent)
            async def on_comment(event: CommentEvent):
                global current_tiktok_status_str
                # 🛑 歷史舊留言過濾防線：僅過濾連線前超過 15 秒以上的歷史留言，絕不誤殺即時訊息
                raw_create_time = getattr(getattr(event, 'common', None), 'create_time', 0)
                if raw_create_time:
                    c_time_sec = (raw_create_time / 1000.0) if raw_create_time > 1e11 else float(raw_create_time)
                    if c_time_sec < (connect_timestamp - 15.0):
                        return

                msg_id = getattr(getattr(event, 'common', None), 'msg_id', None)
                if msg_id:
                    if msg_id in seen_msg_set:
                        return
                    if len(seen_msg_ids) >= 1000:
                        oldest = seen_msg_ids.popleft()
                        seen_msg_set.discard(oldest)
                    seen_msg_set.add(msg_id)
                    seen_msg_ids.append(msg_id)

                user_name = event.user.nickname or event.user.unique_id or "觀眾"
                comment_text = event.comment.strip() if event.comment else ""
                if comment_text:
                    current_tiktok_status_str = f"[💬 {user_name}: {comment_text[:12]}]"
                    log_print(f"💬 [TikTok 彈幕] {user_name}: {comment_text}")
                    sys_notify(f"💬 [TikTok] {user_name}: {comment_text}")
                    await input_queue.put({
                        "text": f"【TikTok 直播觀眾 {user_name} 留言】：{comment_text}",
                        "audio_base64": None,
                        "timestamp": time.time(),
                        "source": "tiktok"
                    })

            @client.on(BarrageEvent)
            async def on_barrage(event: BarrageEvent):
                global current_tiktok_status_str
                msg_id = getattr(getattr(event, 'common', None), 'msg_id', None)
                if msg_id:
                    if msg_id in seen_msg_set:
                        return
                    if len(seen_msg_ids) >= 1000:
                        oldest = seen_msg_ids.popleft()
                        seen_msg_set.discard(oldest)
                    seen_msg_set.add(msg_id)
                    seen_msg_ids.append(msg_id)

                user_name = getattr(event, 'user', None)
                u_name = (user_name.nickname or user_name.unique_id) if user_name else "觀眾"
                b_text = getattr(event, 'content', '') or getattr(event, 'comment', '') or ""
                b_text = str(b_text).strip()
                if b_text:
                    current_tiktok_status_str = f"[💬 {u_name}: {b_text[:12]}]"
                    log_print(f"💬 [TikTok 飄屏彈幕] {u_name}: {b_text}")
                    await input_queue.put({
                        "text": f"【TikTok 直播觀眾 {u_name} 留言】：{b_text}",
                        "audio_base64": None,
                        "timestamp": time.time(),
                        "source": "tiktok"
                    })

            @client.on(EmoteChatEvent)
            async def on_emote_chat(event: EmoteChatEvent):
                global current_tiktok_status_str
                msg_id = getattr(getattr(event, 'common', None), 'msg_id', None)
                if msg_id:
                    if msg_id in seen_msg_set:
                        return
                    if len(seen_msg_ids) >= 1000:
                        oldest = seen_msg_ids.popleft()
                        seen_msg_set.discard(oldest)
                    seen_msg_set.add(msg_id)
                    seen_msg_ids.append(msg_id)

                user_name = getattr(event, 'user', None)
                u_name = (user_name.nickname or user_name.unique_id) if user_name else "觀眾"
                e_text = getattr(event, 'comment', '') or "發送了表情"
                current_tiktok_status_str = f"[💬 {u_name}: {e_text[:12]}]"
                log_print(f"💬 [TikTok 表情] {u_name}: {e_text}")
                await input_queue.put({
                    "text": f"【TikTok 直播觀眾 {u_name} 留言】：{e_text}",
                    "audio_base64": None,
                    "timestamp": time.time(),
                    "source": "tiktok"
                })

            @client.on(JoinEvent)
            async def on_join(event: JoinEvent):
                global current_tiktok_status_str
                try:
                    user_name = event.user.nickname or event.user.unique_id or "新觀眾"
                    current_tiktok_status_str = f"[👋 {user_name} 進房]"
                except Exception:
                    pass

            @client.on(FollowEvent)
            async def on_follow(event: FollowEvent):
                nonlocal last_ambient_notify_time
                global current_tiktok_status_str
                try:
                    user_name = event.user.nickname or event.user.unique_id or "觀眾"
                    current_tiktok_status_str = f"[➕ {user_name} 關注]"
                    sys_notify(f"➕ [TikTok 關注] {user_name} 關注了直播間")
                    now = time.time()
                    # 🛑 【關注節流】：彈琴時或間隔小於 90 秒時不塞入佇列
                    if not pe.GLOBAL_PIANO_REALTIME_STATE.get("is_playing", False) and (now - last_ambient_notify_time > 90.0):
                        last_ambient_notify_time = now
                        await input_queue.put({
                            "text": f"【TikTok 直播動態】：觀眾「{user_name}」點擊關注了直播間！（是否開口感謝關注由妳自由決定）",
                            "audio_base64": None,
                            "timestamp": time.time(),
                            "source": "tiktok_ambient"
                        })
                except Exception:
                    pass

            @client.on(LikeEvent)
            async def on_like(event: LikeEvent):
                nonlocal last_like_milestone_notified, last_ambient_notify_time
                global current_tiktok_status_str
                try:
                    user_name = event.user.nickname or event.user.unique_id or "觀眾"
                    total_l = getattr(event, 'total_likes', None) or getattr(event, 'likes', None)
                    current_tiktok_status_str = f"[❤️ {user_name} 點讚 ({total_l})]" if total_l else f"[❤️ {user_name} 點讚]"
                    # 🛑 【點讚徹底脫敏與靜默】：零碎點讚絕不推送進對話佇列，完全不打擾彈琴與對話！
                    # 僅當累積破千大關 (如滿 1000、2000 讚) 且冷卻超過 180 秒時才做低頻率更新
                    if total_l and total_l >= 1000 and (total_l - last_like_milestone_notified >= 1000):
                        last_like_milestone_notified = (total_l // 1000) * 1000
                        now = time.time()
                        if not pe.GLOBAL_PIANO_REALTIME_STATE.get("is_playing", False) and (now - last_ambient_notify_time > 180.0):
                            last_ambient_notify_time = now
                            await input_queue.put({
                                "text": f"【TikTok 直播動態】：直播間累積點讚達到 {last_like_milestone_notified} 次！（此為背景數據里程碑，可隨性帶過或略過）",
                                "audio_base64": None,
                                "timestamp": time.time(),
                                "source": "tiktok_ambient"
                            })
                except Exception:
                    pass

            @client.on(ShareEvent)
            async def on_share(event: ShareEvent):
                nonlocal last_ambient_notify_time
                global current_tiktok_status_str
                try:
                    user_name = event.user.nickname or event.user.unique_id or "觀眾"
                    current_tiktok_status_str = f"[📢 {user_name} 分享]"
                    now = time.time()
                    if not pe.GLOBAL_PIANO_REALTIME_STATE.get("is_playing", False) and (now - last_ambient_notify_time > 90.0):
                        last_ambient_notify_time = now
                        await input_queue.put({
                            "text": f"【TikTok 直播動態】：觀眾「{user_name}」分享了直播間！（是否感謝由妳自由決定）",
                            "audio_base64": None,
                            "timestamp": time.time(),
                            "source": "tiktok_ambient"
                        })
                except Exception:
                    pass

            @client.on(QuestionNewEvent)
            async def on_question(event: QuestionNewEvent):
                try:
                    user_name = getattr(getattr(event, 'user', None), 'nickname', '') or "觀眾"
                    q_text = getattr(getattr(event, 'question', None), 'text', '') or getattr(event, 'text', '')
                    if q_text:
                        log_print(f"❓ [TikTok 提問箱] {user_name} 提問: {q_text}")
                        await input_queue.put({
                            "text": f"【TikTok 官方提問箱】：觀眾「{user_name}」提問：『{q_text}』。（是否回答由妳自由決定）",
                            "audio_base64": None,
                            "timestamp": time.time(),
                            "source": "tiktok"
                        })
                except Exception:
                    pass

            @client.on(SubNotifyEvent)
            async def on_sub(event: SubNotifyEvent):
                try:
                    user_name = getattr(getattr(event, 'user', None), 'nickname', '') or "觀眾"
                    log_print(f"👑 [TikTok 訂閱] 觀眾 {user_name} 訂閱成為會員！")
                    sys_notify(f"👑 [TikTok 訂閱] {user_name} 訂閱成為會員！")
                    await input_queue.put({
                        "text": f"【TikTok 直播動態】：觀眾「{user_name}」付費訂閱成為專屬會員！（是否慶祝/感謝由妳自由決定）",
                        "audio_base64": None,
                        "timestamp": time.time(),
                        "source": "tiktok_gift"
                    })
                except Exception:
                    pass

            TIKTOK_GIFT_COMBO_BUFFER = {}

            async def _flush_gift_combo(k, delay=3.2):
                try:
                    await asyncio.sleep(delay)
                    if k in TIKTOK_GIFT_COMBO_BUFFER:
                        info = TIKTOK_GIFT_COMBO_BUFFER.pop(k)
                        u_name = info["user_name"]
                        g_name = info["gift_name"]
                        tot_count = info["count"]
                        log_print(f"🎉 [TikTok 連續送禮結算] {u_name} 連擊結束，累計送出 {tot_count} 個 {g_name}！")
                        sys_notify(f"🎁 [TikTok 送禮結算] {u_name} 送了 {tot_count} 個 {g_name}！")
                        
                        gift_desc = f"連續送出了 {tot_count} 個 {g_name}！" if tot_count > 1 else f"送出了 1 個 {g_name}！"
                        await input_queue.put({
                            "text": f"【TikTok 直播觀眾 {u_name} 送禮】：{gift_desc}請向他熱情道謝並給予即時互動！",
                            "audio_base64": None,
                            "timestamp": time.time(),
                            "source": "tiktok_gift"
                        })
                except asyncio.CancelledError:
                    pass
                except Exception as ex:
                    log_print(f"⚠️ [送禮聚合結算異常]: {ex}")

            @client.on(GiftEvent)
            async def on_gift(event: GiftEvent):
                try:
                    raw_create_time = getattr(getattr(event, 'common', None), 'create_time', 0)
                    if raw_create_time:
                        c_time_sec = (raw_create_time / 1000.0) if raw_create_time > 1e11 else float(raw_create_time)
                        if c_time_sec < (connect_timestamp - 15.0):
                            return

                    msg_id = getattr(getattr(event, 'common', None), 'msg_id', None)
                    if msg_id:
                        if msg_id in seen_msg_set:
                            return
                        if len(seen_msg_ids) >= 1000:
                            oldest = seen_msg_ids.popleft()
                            seen_msg_set.discard(oldest)
                        seen_msg_set.add(msg_id)
                        seen_msg_ids.append(msg_id)

                    user_name = "觀眾"
                    if hasattr(event, 'user') and event.user:
                        user_name = event.user.nickname or event.user.unique_id or "觀眾"
                    
                    gift_obj = getattr(event, 'gift', None)
                    if not gift_obj:
                        return
                    
                    gift_info = getattr(gift_obj, 'info', None)
                    gift_name = getattr(gift_info, 'name', None) if gift_info else None
                    if not gift_name:
                        gift_name = getattr(gift_obj, 'name', '禮物')
                    gift_count = getattr(gift_obj, 'count', 1)
                    
                    combo_key = (user_name, gift_name)
                    if combo_key in TIKTOK_GIFT_COMBO_BUFFER:
                        combo_info = TIKTOK_GIFT_COMBO_BUFFER[combo_key]
                        combo_info["count"] += gift_count
                        if combo_info.get("task") and not combo_info["task"].done():
                            combo_info["task"].cancel()
                    else:
                        TIKTOK_GIFT_COMBO_BUFFER[combo_key] = {
                            "count": gift_count,
                            "user_name": user_name,
                            "gift_name": gift_name,
                            "task": None
                        }
                        combo_info = TIKTOK_GIFT_COMBO_BUFFER[combo_key]
                    
                    log_print(f"🎁 [TikTok 送禮 (連擊計數)] {user_name} 送出了 {gift_count} 個 {gift_name}！（當前累計: {combo_info['count']} 個，等待連送結算...）")
                    
                    # 延遲 3.2 秒等待連擊結束後一次性結算
                    combo_info["task"] = asyncio.create_task(_flush_gift_combo(combo_key, delay=3.2))
                except Exception as e:
                    log_print(f"⚠️ [TikTok 送禮處理異常]: {e}")

            ws_task = await client.start()
            if ws_task:
                last_offline_notify = False
                await ws_task  # 🌟 真正常駐等待 WebSocket 運行
            else:
                await asyncio.sleep(8.0)
        except asyncio.CancelledError:
            break
        except SignatureRateLimitError:
            if not last_offline_notify:
                log_print("⚠️ [TikTok 直播] 公共簽名伺服器頻率限制 (可在 .env 設定 SIGN_API_KEY 免除限制)，30 秒後重試...")
            await asyncio.sleep(30.0)
        except Exception as e:
            err_str = str(e)
            if "offline" in err_str.lower():
                if not last_offline_notify:
                    log_print(f"📺 [TikTok 直播] 直播主 {tid} 目前尚未開播 (Offline)，已進入靜默待命狀態（每 30 秒靜態檢測，開播時將自動無縫秒連）...")
                    last_offline_notify = True
                await asyncio.sleep(30.0)
            else:
                log_print(f"⚠️ [TikTok 直播連線狀態]: {err_str}，15 秒後自動重試...")
                await asyncio.sleep(15.0)
        finally:
            try:
                if client and client.connected:
                    await client.disconnect()
            except Exception:
                pass

# ────────────────────────────────────────────────────────
# 🚀 17. 主程式進入點與終端機即時狀態列 (main Entry Point & ANSI Status Bar)
# ────────────────────────────────────────────────────────
# 💡 功能目的：
#    - 系統總指揮中心：連線 VTube Studio WebSocket (Port 8001) 並完成 Token 認證。
#    - 同時啟動所有背景感知工作協程（麥克風、畫面截圖、餘光視覺、鋼琴合成、CMA 監控、TikTok 彈幕）。
#    - 在終端機以 ANSI 虛擬終端即時刷新單行乾淨狀態列（旋轉游標、當前大腦狀態、麥克風音量、TikTok 動態）。

