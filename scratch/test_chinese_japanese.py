import asyncio, edge_tts, soundfile as sf

# 測試用中文字音（配合少數英文輔助）合成日文，讓小依發出最自然的語音
test_cases = [
    # こんにちは 測試
    ('hello_cn1', '老爸，空妮七哇！今天也要加油喔～'),
    ('hello_cn2', '老爸，孔妮七哇！今天也要加油喔～'),
    ('hello_cn3', '老爸，扣恩妮七哇！今天也要加油喔～'),
    
    # 私、7Lだよ！お父さん、大好き！ 測試
    ('pure_cn1', '哇塔西，7L搭優！歐托桑，搭一絲琪！'),
    ('pure_cn2', '瓦塔西，7L大優！歐偷桑，代斯琪！'),
    ('pure_cn3', '哇塔西，7L搭優！歐豆桑，大伊絲琪！'),
    
    # ありがとう 測試
    ('arigatou_cn1', '老爸，阿里嘎多！愛一西貼路優～'),
    ('arigatou_cn2', '老爸，阿莉嘎多！阿伊西貼嚕喲～'),
    
    # 日本語もペラペラだよ～ 測試
    ('perapera_cn1', '當然會呀！妮宏國莫佩拉佩拉搭優～ 嘻嘻，老爸想聽我說什麼呢？'),
    ('perapera_cn2', '當然會呀！尼烘果摸配拉配拉大優～ 嘻嘻，老爸想聽我說什麼呢？')
]

async def run_tests():
    for tag, text in test_cases:
        out = f'songs_library/test_chinese_{tag}.mp3'
        comm = edge_tts.Communicate(text, 'zh-CN-XiaoyiNeural', pitch='+0Hz', rate='+0%')
        await comm.save(out)
        data, sr = sf.read(out)
        print(f'✅ {tag}: {text} ({len(data)/sr:.2f}s)')

if __name__ == '__main__':
    asyncio.run(run_tests())
