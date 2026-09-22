import asyncio, edge_tts, soundfile as sf

async def test():
    variants = [
        ('nee', 'kohn nee chee wah'),
        ('ni', 'kohn ni chee wah'),
        ('knee', 'kohn knee chee wah'),
        ('nih', 'kohn nih chee wah'),
        ('nii', 'kohn nii chee wah'),
        ('chinese_ni', 'kohn 妮 chee wah'),
        ('chinese_all', '老爸，孔妮七哇！今天也要加油喔～')
    ]
    for tag, text in variants:
        out = f'songs_library/test_ni_{tag}.mp3'
        comm = edge_tts.Communicate(text, 'zh-CN-XiaoyiNeural')
        await comm.save(out)
        data, sr = sf.read(out)
        print(f'✅ {tag}: "{text}" ({len(data)/sr:.2f}s)')

if __name__ == '__main__':
    asyncio.run(test())
