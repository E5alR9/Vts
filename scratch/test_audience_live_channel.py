import sys, os, asyncio
sys.path.insert(0, r"c:\Users\qiwai")
sys.stdout.reconfigure(encoding='utf-8')

import vts_7L_test

async def test_audience_live_flow():
    print("=== ⚡ 測試 TikTok 觀眾專屬 Gemini Live 管道 ===")
    
    input_queue = asyncio.Queue()
    test_msg = "【TikTok 直播觀眾 小小翼 留言】：7L 鋼琴彈得好棒喔！"
    
    print(f"📥 模擬收到觀眾彈幕: 『{test_msg}』")
    await vts_7L_test.process_chat_message(None, input_queue, test_msg)
    
    print("=== 🏁 測試完成 ===")

if __name__ == "__main__":
    asyncio.run(test_audience_live_flow())
