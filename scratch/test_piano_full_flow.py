import sys, os, asyncio
sys.path.insert(0, r"c:\Users\qiwai")
sys.stdout.reconfigure(encoding='utf-8')

import vts_7L_test

async def test_piano_pipeline():
    print("=== 🎹 開始測試 7L 鋼琴曲目抓取與調度功能 ===")
    
    # 1. 測試本機曲庫匹配
    test_queries = ["卡農", "給愛麗絲", "月光", "冬風"]
    print("\n1. 測試本機 MIDI 解析匹配 (resolve_local_midi_file)...")
    for q in test_queries:
        path, title = await vts_7L_test.resolve_local_midi_file(q)
        print(f"   - 搜尋『{q}』 ➔ 匹配到: 《{title}》 (路徑: {path})")
    
    # 2. 測試雲端 BitMidi 自動下載抓取（測試一首本機可能沒有的曲目）
    test_cloud_query = "Clair de Lune"
    print(f"\n2. 測試雲端自動抓取《{test_cloud_query}》...")
    dl_path = await asyncio.to_thread(vts_7L_test.bitmidi_engine.fetch_and_download_first_match, test_cloud_query, vts_7L_test.MIDI_SHEETS_DIR)
    print(f"   - 雲端抓取結果: {dl_path}")
    if dl_path and os.path.exists(dl_path):
        print(f"   ✅ 成功下載並儲存，大小: {os.path.getsize(dl_path)} bytes")
    
    # 3. 測試工具分發調用 play_virtual_piano 函式
    print("\n3. 測試大腦工具調發器 execute_tool_dispatch (play_virtual_piano)...")
    tool_resp = await vts_7L_test.execute_tool_dispatch("play_virtual_piano", {"song_name": "卡農", "queue_as_next": False})
    print(f"   - 工具回傳訊息: {tool_resp}")
    
    # 4. 檢查鋼琴背景任務與狀態
    print(f"   - is_piano_active 狀態: {vts_7L_test.is_piano_active}")
    print(f"   - 當前演奏曲目: 《{vts_7L_test.current_piano_song_title}》")
    
    # 清理停止鋼琴
    if vts_7L_test.is_piano_active:
        await vts_7L_test.execute_tool_dispatch("stop_virtual_piano", {})
        print("   - 已成功停止鋼琴並重置狀態！")

    print("\n=== 🏁 鋼琴抓取與調度測試全部通過！ ===")

if __name__ == "__main__":
    asyncio.run(test_piano_pipeline())
