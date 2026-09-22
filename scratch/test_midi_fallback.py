import sys, os, asyncio
sys.path.insert(0, r"c:\Users\qiwai")
sys.stdout.reconfigure(encoding='utf-8')

import bitmidi_engine
import onlinesequencer_engine

print("=== 🧪 測試 MIDI 雙曲庫下載鏈條 (BitMidi ➔ OnlineSequencer Fallback) ===")

# 測試 1: BitMidi 搜尋
test_song_1 = "Canon in D"
print(f"\n1. 測試 BitMidi 搜尋《{test_song_1}》...")
res_bitmidi = bitmidi_engine.search_bitmidi(test_song_1, max_results=3)
print(f"   BitMidi 搜尋結果數量: {len(res_bitmidi)}")
if res_bitmidi:
    print(f"   第一首: {res_bitmidi[0]['title']} -> {res_bitmidi[0]['url']}")
    dl1 = bitmidi_engine.download_bitmidi_song(res_bitmidi[0], save_dir="test_midi_download")
    print(f"   下載結果: {dl1} (存在: {os.path.exists(dl1) if dl1 else False})")

# 測試 2: OnlineSequencer Fallback 測試
# 挑選一首 BitMidi 可能沒有的冷門/動漫曲目，或直接測試 OnlineSequencer
test_song_2 = "Gurenge"
print(f"\n2. 測試 OnlineSequencer 搜尋與下載《{test_song_2}》...")
try:
    # 測試 onlinesequencer 的 fetch_and_download_first_match
    dl2 = onlinesequencer_engine.fetch_and_download_first_match(test_song_2, save_dir="test_midi_download")
    print(f"   OnlineSequencer 下載結果: {dl2} (存在: {os.path.exists(dl2) if dl2 else False})")
except Exception as e:
    print(f"   OnlineSequencer 測試異常: {e}")

print("\n=== 🏁 測試完成 ===")
