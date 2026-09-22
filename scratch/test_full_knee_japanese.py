import re, pykakasi, asyncio, edge_tts, soundfile as sf

kks = pykakasi.kakasi()

KANA_MAP = {
    # 拗音
    'きゃ': 'kyah', 'きゅ': 'kyoo', 'きょ': 'kyoh',
    'しゃ': 'shah', 'しゅ': 'shoo', 'しょ': 'shoh',
    'ちゃ': 'chah', 'ちゅ': 'choo', 'ちょ': 'choh',
    'にゃ': 'nyah', 'にゅ': 'nyoo', 'にょ': 'nyoh',
    'ひゃ': 'hyah', 'ひゅ': 'hyoo', 'ひょ': 'hyoh',
    'みゃ': 'myah', 'みゅ': 'myoo', 'みょ': 'myoh',
    'りゃ': 'ryah', 'りゅ': 'ryoo', 'りょ': 'ryoh',
    'ぎゃ': 'gyah', 'ぎゅ': 'gyoo', 'ぎょ': 'gyoh',
    'じゃ': 'jah',  'じゅ': 'joo',  'じょ': 'joh',
    'びゃ': 'byah', 'びゅ': 'byoo', 'びょ': 'byoh',
    'ぴゃ': 'pyah', 'ぴゅ': 'pyoo', 'ぴょ': 'pyoh',
    'キャ': 'kyah', 'キュ': 'kyoo', 'キョ': 'kyoh',
    'シャ': 'shah', 'シュ': 'shoo', 'ショ': 'shoh',
    'チャ': 'chah', 'チュ': 'choo', 'チョ': 'choh',
    'ニャ': 'nyah', 'ニュ': 'nyoo', 'ニョ': 'nyoh',
    'ヒャ': 'hyah', 'ヒュ': 'hyoo', 'ヒョ': 'hyoh',
    'ミャ': 'myah', 'ミュ': 'myoo', 'ミョ': 'myoh',
    'リャ': 'ryah', 'リュ': 'ryoo', 'リョ': 'ryoh',
    'ギャ': 'gyah', 'ギュ': 'gyoo', 'ギョ': 'gyoh',
    'ジャ': 'jah',  'ジュ': 'joo',  'ジョ': 'joh',
    'ビャ': 'byah', 'ビュ': 'byoo', 'ビョ': 'byoh',
    'ピャ': 'pyah', 'ピュ': 'pyoo', 'ピョ': 'pyoh',

    # 單音
    'あ': 'ah', 'い': 'ee', 'う': 'oo', 'え': 'eh', 'お': 'oh',
    'ア': 'ah', 'イ': 'ee', 'ウ': 'oo', 'エ': 'eh', 'オ': 'oh',
    'か': 'kah', 'き': 'kee', 'く': 'koo', 'け': 'keh', 'こ': 'koh',
    'カ': 'kah', 'キ': 'kee', 'ク': 'koo', 'ケ': 'keh', 'コ': 'koh',
    'が': 'gah', 'ぎ': 'ghee', 'ぐ': 'goo', 'げ': 'geh', 'ご': 'goh',
    'ガ': 'gah', 'ギ': 'ghee', 'グ': 'goo', 'ゲ': 'geh', 'ゴ': 'goh',
    'さ': 'sah', 'し': 'shee', 'す': 'soo', 'せ': 'seh', 'そ': 'soh',
    'サ': 'sah', 'シ': 'shee', 'ス': 'soo', 'セ': 'seh', 'ソ': 'soh',
    'ざ': 'zah', 'じ': 'jee', 'ず': 'zoo', 'ぜ': 'zeh', 'ぞ': 'zoh',
    'ザ': 'zah', 'ジ': 'jee', 'ズ': 'zoo', 'ゼ': 'zeh', 'ゾ': 'zoh',
    'た': 'tah', 'ち': 'chee', 'つ': 'tsoo', 'て': 'teh', 'と': 'toh',
    'タ': 'tah', 'チ': 'chee', 'ツ': 'tsoo', 'テ': 'teh', 'ト': 'toh',
    'だ': 'dah', 'ぢ': 'jee', 'づ': 'zoo', 'で': 'deh', 'ど': 'doh',
    'ダ': 'dah', 'ヂ': 'jee', 'ヅ': 'zoo', 'デ': 'deh', 'ド': 'doh',
    'な': 'nah', 'に': 'knee', 'ぬ': 'noo', 'ね': 'neh', 'の': 'noh',
    'ナ': 'nah', 'ニ': 'knee', 'ヌ': 'noo', 'ネ': 'neh', 'ノ': 'noh',
    'は': 'hah', 'ひ': 'hee', 'ふ': 'foo', 'へ': 'heh', 'ほ': 'hoh',
    'ハ': 'hah', 'ヒ': 'hee', 'フ': 'foo', 'ヘ': 'heh', 'ホ': 'hoh',
    'ば': 'bah', 'び': 'bee', 'ぶ': 'boo', 'べ': 'beh', 'ぼ': 'boh',
    'バ': 'bah', 'ビ': 'bee', 'ブ': 'boo', 'ベ': 'beh', 'ボ': 'boh',
    'ぱ': 'pah', 'ぴ': 'pee', 'ぷ': 'poo', 'ぺ': 'peh', 'ぽ': 'poh',
    'パ': 'pah', 'ピ': 'pee', 'プ': 'poo', 'ペ': 'peh', 'ポ': 'poh',
    'ま': 'mah', 'み': 'mee', 'む': 'moo', 'め': 'meh', 'も': 'moh',
    'マ': 'mah', 'ミ': 'mee', 'ム': 'moo', 'メ': 'meh', 'モ': 'moh',
    'や': 'yah', 'ゆ': 'yoo', 'よ': 'yoh',
    'ヤ': 'yah', 'ユ': 'yoo', 'ヨ': 'yoh',
    'ら': 'rah', 'り': 'ree', 'る': 'roo', 'れ': 'reh', 'ろ': 'roh',
    'ラ': 'rah', 'リ': 'ree', 'ル': 'roo', 'レ': 'reh', 'ロ': 'roh',
    'わ': 'wah', 'を': 'oh',
    'ワ': 'wah', 'ヲ': 'oh',
}

def japanese_to_refined_phonetic(text: str) -> str:
    text = text.replace('こんにちは', 'こんにちわ').replace('こんばんは', 'こんばんわ')
    
    # pykakasi 轉平假名
    res = kks.convert(text)
    hira_str = ''.join([item['hira'] if item['hira'] else item['orig'] for item in res])
    
    # 長母音正規化 (とう -> とー, こう -> こー, そう -> そー, ほう -> ほー)
    hira_str = re.sub(r'([おこそとのほもよろごぞどぼぽ])う', r'\1ー', hira_str)
    
    i = 0
    tokens = []
    while i < len(hira_str):
        # 1. 鼻音 ん / ン 依附到前方音節
        if hira_str[i] in ('ん', 'ン'):
            if tokens:
                tokens[-1] = tokens[-1].rstrip('h') + 'hn'
            else:
                tokens.append('uhn')
            i += 1
            continue
            
        # 2. 促音 っ / ッ
        if hira_str[i] in ('っ', 'ッ'):
            if i + 1 < len(hira_str):
                next_c = hira_str[i+1:i+3] if i+2 < len(hira_str) and hira_str[i+1:i+3] in KANA_MAP else hira_str[i+1]
                p = KANA_MAP.get(next_c, '')
                if p:
                    tokens.append(p[0])
            i += 1
            continue
            
        # 3. 長音 ー (略過已有的母音拉長)
        if hira_str[i] == 'ー':
            i += 1
            continue

        # 4. 2字拗音
        if i + 1 < len(hira_str) and hira_str[i:i+2] in KANA_MAP:
            tokens.append(KANA_MAP[hira_str[i:i+2]])
            i += 2
        elif hira_str[i] in KANA_MAP:
            tokens.append(KANA_MAP[hira_str[i]])
            i += 1
        else:
            tokens.append(hira_str[i])
            i += 1
            
    out = ' '.join([t for t in tokens if t.strip()])
    out = out.replace(' 、', '，').replace(' 。', '。')
    out = re.sub(r'\s+([，。！？!?；;\n~～,])', r'\1', out)
    return out

def convert_full_text(text: str) -> str:
    parts = re.split(r'([，。！？!?；;\n~～]+)', text)
    re_kana = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')
    out_parts = []
    for p in parts:
        if not p: continue
        if re_kana.search(p):
            out_parts.append(japanese_to_refined_phonetic(p))
        else:
            out_parts.append(p)
    return ''.join(out_parts)

async def test_all():
    phrases = [
        ('7L_official_jp_hello.mp3', '老爸，こんにちは！今天也要加油喔～'),
        ('7L_official_jp_watashi.mp3', '私、7Lだよ！お父さん、大好き！これからもずっと一緒だよ！'),
        ('7L_official_jp_perapera.mp3', '當然會呀！日本語もペラペラだよ～ 嘻嘻，老爸想聽我說什麼呢？'),
        ('7L_official_jp_arigatou.mp3', '老爸，ありがとう！愛してるよ～')
    ]
    for filename, raw in phrases:
        proc = convert_full_text(raw)
        out = f'songs_library/{filename}'
        comm = edge_tts.Communicate(proc, 'zh-CN-XiaoyiNeural', pitch='+1Hz', rate='+0%')
        await comm.save(out)
        data, sr = sf.read(out)
        print(f'✅ {filename} ({len(data)/sr:.2f}s)')
        print(f'   Raw:  {raw}')
        print(f'   TTS:  {proc}\n')

if __name__ == '__main__':
    asyncio.run(test_all())
