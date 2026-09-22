import sys, asyncio
sys.path.insert(0, r"c:\Users\qiwai")
sys.stdout.reconfigure(encoding='utf-8')
import singing_engine

async def test_any_song():
    print("=== 🌐 測試全網任意歌曲歌詞搜尋與旋律生成 ===")
    notes = await singing_engine.fetch_song_notes_with_ai("告白氣球")
    print("\n【全網抓取並調音的《告白氣球》歌詞】：")
    for n in notes:
        print(f"  • {n.get('line')} (音高: {n.get('pitch')}, 語速: {n.get('rate')})")

if __name__ == "__main__":
    asyncio.run(test_any_song())
