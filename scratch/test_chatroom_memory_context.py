import sys, os, asyncio
sys.path.insert(0, r"c:\Users\qiwai")
sys.stdout.reconfigure(encoding='utf-8')

import vts_7L_test

async def test_memory_context():
    print("=== 🧠 測試 TikTok 聊天室動態滾動記憶 + 嚴格叫名字才回覆 ===")
    input_queue = asyncio.Queue()
    
    # 1. 觀眾們自言自語聊火鍋 (非對 7L 說話)
    print("\n1. 模擬觀眾 A 自言自語...")
    msg1 = "【TikTok 直播觀眾 小明 (@ming99) 留言】：今天天氣好冷喔"
    await vts_7L_test.process_chat_message(None, input_queue, msg1)
    
    print("\n2. 模擬觀眾 B 接著聊宵夜...")
    msg2 = "【TikTok 直播觀眾 小華 (@hua88) 留言】：@小明 超冷！我想吃麻辣火鍋"
    await vts_7L_test.process_chat_message(None, input_queue, msg2)
    
    # 2. 觀眾 C 明確指名問 7L 剛才大家聊的話題
    print("\n3. 模擬觀眾 C 明確叫 7L 提問...")
    msg3 = "【TikTok 直播觀眾 小美 (@mei_cute) 留言】：7L 妳有看到大家在聊火鍋嗎？妳喜歡吃火鍋嗎？"
    await vts_7L_test.process_chat_message(None, input_queue, msg3)
    
    print("\n=== 🏁 測試全部完成 ===")

if __name__ == "__main__":
    asyncio.run(test_memory_context())
