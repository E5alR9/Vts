import re, pykakasi, asyncio, edge_tts, soundfile as sf

kks = pykakasi.kakasi()

# 👑 中英夾雜黃金音標對照表 (平假名 -> 中英夾雜最佳讀音)
KANA_HYBRID = {
    # 拗音
    'きゃ': 'kyah', 'きゅ': 'kyoo', 'きょ': 'kyoh',
    'しゃ': '夏', 'しゅ': '修', 'しょ': '秀',
    'ちゃ': '恰', 'ちゅ': '秋', 'ちょ': '秋',
    'にゃ': 'nyah', 'にゅ': 'nyoo', 'にょ': 'nyoh',
    'ひゃ': 'hyah', 'ひゅ': 'hyoo', 'ひょ': 'hyoh',
    'みゃ': 'myah', 'みゅ': 'myoo', 'みょ': 'myoh',
    'りゃ': 'ryah', 'りゅ': 'ryoo', 'りょ': 'ryoh',
    'ぎゃ': 'gyah', 'ぎゅ': 'gyoo', 'ぎょ': 'gyoh',
    'じゃ': '夾', 'じゅ': '糾', 'じょ': '舅',
    'びゃ': 'byah', 'びゅ': 'byoo', 'びょ': 'byoh',
    'ぴゃ': 'pyah', 'ぴゅ': 'pyoo', 'ぴょ': 'pyoh',

    # 50 音 (單母音)
    'あ': '阿', 'い': '伊', 'う': '屋', 'え': '欸', 'お': '歐',
    'ア': '阿', 'イ': '伊', 'ウ': '屋', 'エ': '欸', 'オ': '歐',

    # K 行 (ki 鎖定 kee)
    'か': '卡', 'き': 'kee', 'く': '庫', 'け': 'keh', 'こ': '口',
    'カ': '卡', 'キ': 'kee', 'ク': '庫', 'ケ': 'keh', 'コ': '口',
    'が': '嘎', 'ぎ': 'ghee', 'ぐ': '古', 'げ': '蓋', 'ご': '國',
    'ガ': '嘎', 'ギ': 'ghee', 'グ': '古', 'ゲ': '蓋', 'ゴ': '國',

    # S 行 (su 用 soo 防止雜音)
    'さ': '薩', 'し': '西', 'す': 'soo', 'せ': '賽', 'そ': '搜',
    'サ': '薩', 'シ': '西', 'ス': 'soo', 'セ': '賽', 'ソ': '搜',
    'ざ': '砸', 'じ': '吉', 'ず': 'zoo', 'ぜ': '賊', 'ぞ': '左',
    'ザ': '砸', 'ジ': '吉', 'ズ': 'zoo', 'ゼ': '賊', 'ゾ': '左',

    # T 行 (chi 用七，tsu 用 tsoo)
    'た': '塔', 'ち': '七', 'つ': 'tsoo', 'て': '貼', 'と': '托',
    'タ': '塔', 'チ': '七', 'ツ': 'tsoo', 'テ': '貼', 'ト': '托',
    'だ': '搭', 'ぢ': '吉', 'づ': 'zoo', 'で': '爹', 'ど': '豆',
    'ダ': '搭', 'ヂ': '吉', 'ヅ': 'zoo', 'デ': '爹', 'ド': '豆',

    # N 行 (用戶指定：ni 100% 鎖定 knee！)
    'な': '那', 'に': 'knee', 'ぬ': '努', 'ね': '捏', 'の': '諾',
    'ナ': '那', 'ニ': 'knee', 'ヌ': '努', 'ネ': '捏', 'ノ': '諾',

    # H 行
    'は': '哈', 'ひ': '希', 'ふ': '夫', 'へ': '黑', 'ほ': '吼',
    'ハ': '哈', 'ヒ': '希', 'フ': '夫', 'ヘ': '黑', 'ホ': '吼',
    'ば': '巴', 'び': '比', 'ぶ': '布', 'べ': '貝', 'ぼ': '波',
    'バ': '巴', 'ビ': '比', 'ブ': '布', 'ベ': '貝', 'ボ': '波',
    'ぱ': '帕', 'ぴ': 'pee', 'ぷ': 'poo', 'ぺ': '佩', 'ぽ': '坡',
    'パ': '帕', 'ピ': 'pee', 'プ': 'poo', 'ペ': '佩', 'ポ': '坡',

    # M 行
    'ま': '馬', 'み': '米', 'む': '木', 'め': '妹', 'も': '莫',
    'マ': '馬', 'ミ': '米', '姆': '木', 'メ': '妹', 'モ': '莫',

    # Y 行
    'や': '亞', 'ゆ': '優', 'よ': '喲',
    'ヤ': '亞', 'ユ': '優', 'ヨ': '喲',

    # R 行
    'ら': '拉', 'り': '里', 'る': '嚕', 'れ': '雷', 'ろ': '羅',
    'ラ': '拉', 'リ': '里', 'ル': '嚕', 'レ': '雷', 'ロ': '羅',

    # W 行 & 鼻音
    'わ': '哇', 'を': '歐',
    'ワ': '哇', 'ヲ': '歐',
    'ん': '恩', 'ン': '恩',
}

# 詞彙層級優先映射 (口語最自然的融合組合)
HIRA_PHRASE_RULES = [
    (r'こんにち[はわ]', '空 knee 七哇'),
    (r'こんばん[はわ]', '空 邦 哇'),
    (r'ありがとう', '阿里嘎多'),
    (r'おとうさん', '歐托桑'),
    (r'だいすき', '搭一 soo kee'),
    (r'あいしてる', '阿伊西貼嚕'),
    (r'にほんご', 'knee 宏國'),
    (r'ぺらぺら', '佩拉佩拉'),
    (r'お早う|おはよう', '歐哈優'),
    (r'かわいい', '卡哇伊'),
    (r'すごい', '絲國伊'),
    (r'よろしく', '喲羅西庫'),
    (r'わたし', '哇塔西'),
    (r'だよ', '搭優'),
    (r'これからも', '扣雷卡拉莫'),
    (r'ずっと', '租 t 托'),
    (r'いっしょ', '伊修'),
    (r'愛してる', '阿伊西貼嚕'),
]

def japanese_to_hybrid(japanese_clause: str) -> str:
    # 1. 特殊助詞與常見漢字預處理
    t = japanese_clause
    t = t.replace('愛してる', 'あいしてる')
    t = t.replace('大好き', 'だいすき')
    t = t.replace('お父さん', 'おとうさん')
    t = t.replace('私', 'わたし')
    t = t.replace('日本語', 'にほんご')
    
    # 2. pykakasi 將日文漢字全部轉為純平假名 (不污染中英文)
    res = kks.convert(t)
    hira_str = ''.join([item['hira'] if item['hira'] else item['orig'] for item in res])
    
    # 3. 優先套用常用詞彙規則
    for pat, rep in HIRA_PHRASE_RULES:
        hira_str = re.sub(pat, f' {rep} ', hira_str)

    # 4. 對剩下的平假名逐字套用 KANA_HYBRID
    tokens = []
    # 按空格切分成已替換片語與未替換假名
    parts = hira_str.split()
    for p in parts:
        if any(c in p for c in ['空', '阿里', '歐托', '搭一', '佩拉', '卡哇', '哇塔', 'knee']):
            # 已經是合成詞，直接保留
            tokens.append(p)
            continue
            
        i = 0
        while i < len(p):
            # 拗音
            if i + 1 < len(p) and p[i:i+2] in KANA_HYBRID:
                tokens.append(KANA_HYBRID[p[i:i+2]])
                i += 2
            elif p[i] in KANA_HYBRID:
                tokens.append(KANA_HYBRID[p[i]])
                i += 1
            else:
                tokens.append(p[i])
                i += 1
                
    # 5. 排版美化：中文漢字相鄰時合併，英文字詞前後保留空格
    raw_str = ' '.join(tokens)
    raw_str = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', raw_str)
    raw_str = re.sub(r'\s+([，。！？!?；;\n~～,])', r'\1', raw_str)
    return raw_str.strip()

def process_full_reply(text: str) -> str:
    parts = re.split(r'([，。！？!?；;\n~～]+)', text)
    re_kana = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')
    out = []
    for p in parts:
        if not p: continue
        if re_kana.search(p) or any(w in p for w in ['こんにちは', '私', '大好き', 'ありがとう', 'お父さん', '愛してる']):
            out.append(japanese_to_hybrid(p))
        else:
            out.append(p)
    return ''.join(out)

async def test_suite():
    samples = [
        ('hybrid_v2_hello', '老爸，こんにちは！今天也要加油喔～'),
        ('hybrid_v2_watashi', '私、7Lだよ！お父さん、大好き！これからもずっと一緒だよ！'),
        ('hybrid_v2_perapera', '當然會呀！日本語もペラペ拉だよ～ 嘻嘻，老爸想聽我說什麼呢？'),
        ('hybrid_v2_arigatou', '老爸，ありがとう！愛してるよ～')
    ]
    for tag, raw in samples:
        res = process_full_reply(raw)
        out_path = f'songs_library/test_{tag}.mp3'
        comm = edge_tts.Communicate(res, 'zh-CN-XiaoyiNeural', pitch='+0Hz', rate='+0%')
        await comm.save(out_path)
        data, sr = sf.read(out_path)
        print(f'✅ {tag} ({len(data)/sr:.2f}s)')
        print(f'   Raw:    {raw}')
        print(f'   Hybrid: {res}\n')

if __name__ == '__main__':
    asyncio.run(test_suite())
