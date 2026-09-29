dc_intents = discord.Intents.default()
dc_intents.message_content = True
discord_bot = commands.Bot(command_prefix="*", intents=dc_intents)

@discord_bot.event
async def on_ready():
    print(f"\n【🌐 Discord】機器人已成功在背景連線！(名稱：{discord_bot.user})")

@discord_bot.command(name="vapis", help="顯示當前系統 CMA 精簡摘要監控")
async def show_cma_short(ctx):
    await show_cma_panel(ctx, mode="brief")

@discord_bot.command(name="vapi", help="顯示當前系統 CMA 監控面板（預設精簡，支援 *vapi full）")
async def show_cma_panel(ctx, mode: str = "brief"):
    """📊 CMA (Console Monitor Area) - 顯示全線 API 健康狀態（支援 brief 精簡 / full 詳細）"""
    current_time = time.time()
    now_str = datetime.now(ZoneInfo('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')
    
    total_gemini = len(GEMINI_MODELS) * len(GEMINI_KEYS)
    avail_gemini = 0
    locked_gemini = []
    gemini_details = []
    
    for g_model in GEMINI_MODELS:
        short_m = g_model.replace("gemini-", "")
        for idx, g_key in enumerate(GEMINI_KEYS):
            target_id = f"G{idx}_{short_m}"
            if target_id in API_LOCKS and current_time < API_LOCKS[target_id]:
                rem = int(API_LOCKS[target_id] - current_time)
                mins, secs = rem // 60, rem % 60
                locked_gemini.append(f"`{target_id}`: 🛑 封印中 ({mins}m {secs}s)")
                gemini_details.append(f"[{target_id:<20}] : 🛑 封印中 ({mins}m {secs}s)")
            else:
                avail_gemini += 1
                gemini_details.append(f"[{target_id:<20}] : 🟢 準備就緒")

    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        mem_percent = psutil.virtual_memory().percent
    except Exception:
        cpu_percent, mem_percent = 0, 0
    
    # 精簡摘要卡片
    gem_pct = (avail_gemini * 100 // total_gemini) if total_gemini else 0
    
    all_locked = locked_gemini
    if all_locked:
        locked_sample = all_locked[:6]
        locked_str = "\n".join([f"• {item}" for item in locked_sample])
        if len(all_locked) > 6:
            locked_str += f"\n• ...以及其餘 {len(all_locked) - 6} 條通道"
    else:
        locked_str = "• 🟢 全線綠燈，無任何通道處於封印狀態！"

    brief_card = (
        f"📊 **【7L VAPI 系統健康監控 - 精簡摘要】**\n"
        f"⏱️ 同步時間: `{now_str}`\n"
        f"────────────────────────────\n"
        f"👑 **Gemini 視覺旗艦大腦**: 🟢 `{avail_gemini} / {total_gemini}` 準備就緒 ({gem_pct}%)\n"
        f"💻 **本機硬體負載**: CPU `{cpu_percent}%` | RAM `{mem_percent}%`\n"
        f"────────────────────────────\n"
        f"🛑 **當前受限通道 ({len(all_locked)} 條)**:\n{locked_str}\n"
        f"────────────────────────────\n"
        f"💡 *輸入 `*vapi full` 可匯出全部通道清單*"
    )
    
    await ctx.send(brief_card)

    if mode.lower() in ["full", "detail", "all", "verbose"]:
        categories = {"Gemini 視覺矩陣": gemini_details}
        for cat_name, cat_results in categories.items():
            if not cat_results: continue
            current_chunk = f"**--- 【{cat_name} (詳細清單)】 ---**\n```markdown\n"
            for row_text in cat_results:
                row = row_text + "\n"
                if len(current_chunk) + len(row) > 1850:
                    current_chunk += "```"
                    await ctx.send(current_chunk)
                    current_chunk = f"**--- 【{cat_name} (續)】 ---**\n```markdown\n" + row
                else:
                    current_chunk += row
            if current_chunk.strip() and not current_chunk.endswith("```"):
                current_chunk += "```"
                await ctx.send(current_chunk)

@discord_bot.command(name="mic", help="控制麥克風開啟或關閉 (用法: *mic on / *mic off / *mic 開 / *mic 關)")
async def control_mic(ctx, action: str = ""):
    global IS_MIC_ENABLED
    action_lower = action.lower()
    if action_lower in ["on", "開", "open", "enable"]:
        IS_MIC_ENABLED = True
        log_print("🎙️ [Discord] 收到開麥指令，已開啟麥克風。")
        await ctx.send("🎙️ **麥克風已開啟**！已恢復語音收音。")
    elif action_lower in ["off", "關", "close", "disable", "mute"]:
        IS_MIC_ENABLED = False
        log_print("🎙️ [Discord] 收到關麥指令，已關閉麥克風。")
        await ctx.send("🔇 **麥克風已關閉**！已暫停語音收音。")
    else:
        status = "🟢 開啟中" if IS_MIC_ENABLED else "🔴 關閉中"
        await ctx.send(f"🎙️ 目前麥克風狀態：{status}\n使用方式：`*mic on` (開麥) 或 `*mic off` (關麥)")

@discord_bot.command(name="開麥", help="開啟麥克風收音")
async def discord_mic_on(ctx):
    await control_mic(ctx, "on")

@discord_bot.command(name="關麥", help="關閉麥克風收音")
async def discord_mic_off(ctx):
    await control_mic(ctx, "off")

# ────────────────────────────────────────────────────────
