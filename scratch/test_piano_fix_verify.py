# -*- coding: utf-8 -*-
import os
import sys
import asyncio
import re

sys.path.insert(0, r"c:\Users\qiwai")
import vts_7L_test

async def test():
    print("1. Testing resolve_local_midi_file with '花之塔'...")
    p, t = await vts_7L_test.resolve_local_midi_file("花之塔")
    print(f"Result: path={p}, title={t}")
    assert p is not None and os.path.exists(p), "Failed to resolve 花之塔"

    print("\n2. Testing execute_actions with tag [PLAY_VIRTUAL_PIANO: song_name=花之塔]...")
    class MockQueue:
        async def put(self, val): pass
    
    clean = await vts_7L_test.execute_actions(None, "[EXPRESSION: 臉紅] [MOVE: 鋼琴旁] [PLAY_VIRTUAL_PIANO: song_name=花之塔] 好喔我彈給你聽！", MockQueue())
    print("Clean text:", clean)
    assert "[PLAY_VIRTUAL_PIANO" not in clean
    assert "好喔我彈給你聽" in clean

    print("\n3. Testing play_virtual_piano instant non-blocking return for online/local song...")
    res = await vts_7L_test.play_virtual_piano("花之塔")
    print("play_virtual_piano returned:", res)
    assert "[EXPRESSION:" in res

    print("\n🎉 ALL TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(test())
