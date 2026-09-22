import asyncio
import os
import sys

# 將工作目錄加入路徑
sys.path.insert(0, r"c:\Users\qiwai")
from vts_7L_test import (
    add_to_streamer_mind_board,
    get_recent_100_memory_context,
    judge_subconscious_intent_via_live_api,
    STREAMER_MIND_BOARD,
    TIKTOK_CHATROOM_MEMORY
)

async def run_test():
    print("=== ⚡ 測試 Live API 潛意識哨兵 + 100 句記憶機制 ===")
    
    # 1. 注入 5 條歷史記憶
    for i in range(5):
        add_to_streamer_mind_board(f"觀眾_{i+1}", f"id_{i+1}", f"這是一條歷史彈幕第 {i+1} 則")
        
    print("\n📜 當前累積記憶條數:", len(TIKTOK_CHATROOM_MEMORY))
    ctx = get_recent_100_memory_context()
    print("📜 100 句記憶上下文前 3 行:\n", "\n".join(ctx.splitlines()[:3]))
    
    # 2. 測試場景 A：無意義刷屏 (應被 Live 哨兵靜默過濾 [SILENCE])
    print("\n🧪 [測試 A] 模擬觀眾發送無意義刷屏: 『1111111111111111111』")
    res_a = await judge_subconscious_intent_via_live_api(ctx, "- [18:00:00] 刷屏路人: 1111111111111111111")
    print(f"👉 哨兵判定結果 A: should_speak={res_a['should_speak']}, raw={res_a.get('raw')}")
    
    # 3. 測試場景 B：明確問候與點歌 (應被 Live 哨兵即刻喚醒 [SPEAK])
    print("\n🧪 [測試 B] 模擬觀眾發送精彩互動: 『7L 鋼琴好棒喔！想聽起風了～』")
    res_b = await judge_subconscious_intent_via_live_api(ctx, "- [18:00:05] 小小翼: 7L 鋼琴好棒喔！想聽起風了～")
    print(f"👉 哨兵判定結果 B: should_speak={res_b['should_speak']}, target={res_b.get('target')}, focus={res_b.get('focus')}, raw={res_b.get('raw')}")
    
    print("\n=== 🏁 測試完成 ===")

if __name__ == "__main__":
    asyncio.run(run_test())
