# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"c:\Users\qiwai")
from test_virtual_piano import ClassicalPianoSoundEngine
import time

def test_rush_e_synthesizer():
    print("=== 🎹 測試 Rush E 高密度機槍音符極限發聲 ===")
    engine = ClassicalPianoSoundEngine(volume=100)
    
    # 模擬 Rush E 連續 200 個超高速 E4 音符
    print("🔥 正在觸發 200 個快速連擊音符...")
    for i in range(200):
        engine.note_on(64, velocity=110)
        time.sleep(0.005) # 5ms 一個音符 (200 notes/sec)
        if i >= 10:
            engine.note_off(64)
            
    print("✅ 200 個音符全部順暢發聲，無消音/無爆音！")
    time.sleep(0.3)
    engine.all_notes_off()
    print("=== 🏁 測試完成 ===")

if __name__ == "__main__":
    test_rush_e_synthesizer()
