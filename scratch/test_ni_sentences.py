import asyncio, edge_tts, soundfile as sf

async def test():
    variants = [
        ('knee', '老爸，kohn knee chee wah！今天也要加油喔～'),
        ('chinese_ni', '老爸，kohn 妮 chee wah！今天也要加油喔～'),
        ('ni', '老爸，kohn ni chee wah！今天也要加油喔～'),
        ('nih', '老爸，kohn nih chee wah！今天也要加油喔～'),
        ('knee_pure', 'wah tah shee，7L dah yoh！oh toh sahn，dah ee soo kee！koh reh kah rah moh zoo toh ee shoh dah yoh！')
    ]
    for tag, text in variants:
        out = f'songs_library/test_ni_sentence_{tag}.mp3'
        comm = edge_tts.Communicate(text, 'zh-CN-XiaoyiNeural')
        await comm.save(out)
        data, sr = sf.read(out)
        print(f'✅ {tag}: {out} ({len(data)/sr:.2f}s)')

if __name__ == '__main__':
    asyncio.run(test())
