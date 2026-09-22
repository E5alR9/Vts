import sys, os, asyncio
sys.path.insert(0, r"c:\Users\qiwai")
sys.stdout.reconfigure(encoding='utf-8')

import vts_7L_test

async def test_id_and_pass():
    print("=== 🎭 測試 TikTok 觀眾 ID 識別、自身帳號認知與 [PASS] 靜默過濾 ===")
    input_queue = asyncio.Queue()
    
    # 測試情境 1：觀眾帶 ID 點歌對 7L 說話
    print("\n1. 測試情境 1：觀眾帶 ID 稱呼 7L 並點歌...")
    msg1 = "【TikTok 直播觀眾 小小翼 (@yui_7l) 留言】：7L 可以彈一首卡農嗎？"
    await vts_7L_test.process_chat_message(None, input_queue, msg1)
    
    # 測試情境 2：觀眾之間互相私聊打招呼（非對 7L）
    print("\n2. 測試情境 2：觀眾彼此私聊（非對 7L 說話）...")
    msg2 = "【TikTok 直播觀眾 小明 (@ming99) 留言】：@小華 你下班了沒啊？"
    await vts_7L_test.process_chat_message(None, input_queue, msg2)
    
    # 測試情境 3：純符號灌水洗版
    print("\n3. 測試情境 3：純無意義符號灌水...")
    msg3 = "【TikTok 直播觀眾 路人 (@user_bot) 留言】：..............."
    await vts_7L_test.process_chat_message(None, input_queue, msg3)
    
    print("\n=== 🏁 測試全部完成 ===")

if __name__ == "__main__":
    asyncio.run(test_id_and_pass())
