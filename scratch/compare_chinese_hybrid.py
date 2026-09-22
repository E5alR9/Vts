import asyncio, edge_tts, soundfile as sf

# 對比測試：
# 方案 A: 100% 純中文漢字聲韻融合
# 方案 B: 中文漢字為主 (90%) + 特殊音節英文輔助 (如 ki/tsu/ke)
test_pairs = [
    # 1. こんにちは (Konnichiwa)
    ('hello_pure_chinese', '老爸，空妮七哇！今天也要加油喔～'),
    ('hello_hybrid', '老爸，空 knee 七哇！今天也要加油喔～'),
    
    # 2. 私、7Lだよ！お父さん、大好き！ (Watashi, 7L dayo! Otousan, daisuki!)
    ('pure_sentence_chinese', '哇塔西，7L搭優！歐托桑，搭一絲琪！'),
    ('pure_sentence_hybrid', '哇塔西，7L搭優！歐托桑，dah ee soo kee！'),
    
    # 3. ありがとう！愛してるよ～ (Arigatou! Aishiteru yo~)
    ('arigatou_pure_chinese', '老爸，阿里嘎多！阿伊西貼嚕喲～'),
    ('arigatou_hybrid', '老爸，阿里嘎多！ah ee shee teh roo yoh～'),
    
    # 4. 日本語もペラペラだよ～ (Nihongo mo perapera dayo~)
    ('perapera_pure_chinese', '當然會呀！妮宏國莫佩拉佩拉搭優～ 嘻嘻，老爸想聽我說什麼呢？'),
    ('perapera_hybrid', '當然會呀！knee 宏國莫佩拉佩拉搭優～ 嘻嘻，老爸想聽我說什麼呢？')
]

async def run():
    for tag, text in test_pairs:
        out = f'songs_library/test_{tag}.mp3'
        comm = edge_tts.Communicate(text, 'zh-CN-XiaoyiNeural')
        await comm.save(out)
        data, sr = sf.read(out)
        print(f'✅ {tag}: {text} ({len(data)/sr:.2f}s)')

if __name__ == '__main__':
    asyncio.run(run())
