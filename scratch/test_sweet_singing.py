import sys, asyncio
sys.path.insert(0, r"c:\Users\qiwai")
sys.stdout.reconfigure(encoding='utf-8')
import singing_engine

async def test_sweet():
    print("=== 🌸 測試溫柔甜美自然音調唱歌（消除尖銳高音） ===")
    notes = await singing_engine.fetch_song_notes_with_ai("千本櫻")
    print("\n【全新自然甜美調音曲譜】：")
    for n in notes:
        print(f"  • {n.get('line')} (音高: {n.get('pitch')}, 語速: {n.get('rate')})")
        
    path = await singing_engine.generate_song_vocal_dynamic("千本櫻")
    print(f"\n✨ 全新歌聲檔案已生成: {path}")

if __name__ == "__main__":
    asyncio.run(test_sweet())
