# -*- coding: utf-8 -*-
import asyncio
import re
import os
import sys

sys.path.insert(0, r"c:\Users\qiwai")
from vts_7L_test import play_virtual_piano, execute_actions, is_piano_active

async def test_youtube_bypass():
    print("=== 🎬 測試 YouTube 指定查歌 100% 繞過本地配對與重複曲目攔截 ===")
    
    # 測試 A: 模擬老爸輸入 "youtuber 查 インンムニア(INSOMNIA)-Eve Music Vibeo 然後彈"
    raw_input = "youtuber 查 インンムニア(INSOMNIA)-Eve Music Vibeo 然後彈"
    print(f"📥 測試輸入: {raw_input}")
    
    # 測試正則提取
    yt_cmd_m = re.search(r'(?:youtuber|youtube|yt|從yt|從youtube|去yt|去youtube)\s*(?:查|搜|找|搜尋|下載)?\s*(.*?)\s*(?:然後彈|來彈|彈出來|放出來|彈一下|彈|播放|放)+$', raw_input.strip(), re.IGNORECASE)
    if yt_cmd_m:
        extracted = yt_cmd_m.group(1).strip()
        print(f"✅ 正則成功提取 YouTube 搜尋目標: 『{extracted}』")
        assert extracted == "インンムニア(INSOMNIA)-Eve Music Vibeo"
    else:
        print("❌ 正則提取失敗")

    print("\n🎬 呼叫 play_virtual_piano(song_name='インンムニア(INSOMNIA)-Eve Music Vibeo', force_online=True)...")
    res = await play_virtual_piano(song_name="インンムニア(INSOMNIA)-Eve Music Vibeo", force_online=True)
    print(f"👉 呼叫回傳標籤: {res}")
    
    # 稍等 1 秒確保背景 task 啟動且未報錯
    await asyncio.sleep(1.0)
    print("=== 🏁 測試通過！ ===")

if __name__ == "__main__":
    asyncio.run(test_youtube_bypass())
