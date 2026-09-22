import re, pykakasi, asyncio, edge_tts, soundfile as sf

kks = pykakasi.kakasi()

# 👑 中英夾雜黃金音標對照表 (以中文漢字為骨幹，特殊音如 knee/kee/tsoo 英文輔助)
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

    # 50 音 (母音)
    'あ': '阿', 'い': '伊', 'う': '屋', 'え': '欸', 'お': '歐',
    'ア': '阿', 'イ': '伊', 'ウ': '屋', 'エ': '欸', 'オ': '歐',

    # K 行 (ki 用 kee 保持標準)
    'か': '卡', 'き': 'kee', 'く': '庫', 'け': 'keh', 'こ': '口',
    'カ': '卡', 'キ': 'kee', 'ク': '庫', 'ケ': 'keh', 'コ': '口',
    'が': '嘎', 'ぎ': 'ghee', 'ぐ': '古', 'げ': '蓋', 'ご': '國',
    'ガ': '嘎', 'ギ': 'ghee', 'グ': '古', 'ゲ': '蓋', 'ゴ': '國',

    # S 行 (su 用 soo 防止咬字雜音)
    'さ': '薩', 'し': '西', 'す': 'soo', 'せ': '賽', 'そ': '搜',
    'サ': '薩', 'シ': '西', 'ス': 'soo', 'セ': '賽', 'ソ': '搜',
    'ざ': '砸', 'じ': '吉', 'ず': 'zoo', 'ぜ': '賊', 'ぞ': '左',
    'ザ': '砸', 'ジ': '吉', 'ズ': 'zoo', 'ゼ': '賊', 'ゾ': '左',

    # T 行 (tsu 用 tsoo)
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
    'ぱ': '帕', 'ぴ': '匹', 'ぷ': '撲', 'ぺ': '佩', 'ぽ': '坡',
    'パ': '帕', 'ピ': '匹', 'プ': '撲', 'ペ': '佩', 'ポ': '坡',

    # M 行
    'ま': '馬', 'み': '米', 'む': '木', 'め': '妹', 'も': '莫',
    'マ': '馬', 'ミ': '米', 'ム': '木', 'メ': '妹', 'モ': '莫',

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

COMMON_WORDS = {
    'こんにちは': '空 knee 七哇',
    'こんばんは': '空 邦 哇',
    'ありがとう': '阿里嘎多',
    'ありがとうございます': '阿里嘎多 鍋砸伊瑪斯',
    'お父さん': '歐托桑',
    '大好き': '搭一 soo kee',
    '愛してる': '阿伊西貼嚕',
    '日本語': 'knee 宏國',
    'ペラペラ': '佩拉佩拉',
    'おはよう': '歐哈優',
    'ごめんなさい': '果面那塞',
    'かわいい': '卡哇伊',
    'すごい': '絲國伊',
    'よろしく': '喲羅西庫',
    '私': '哇塔西',
    'これからも': '扣雷卡拉莫',
    'ずっと': '租 t 托',
    '一緒': '伊修',
    'だよ': '搭優',
}

def hybrid_japanese_to_speech(text: str) -> str:
    # 1. 優先處理高頻詞彙完美融合
    t = text
    for k, v in COMMON_WORDS.items():
        t = t.replace(k, f' {v} ')

    # 2. 其餘漢字透過 pykakasi 轉平假名
    res = kks.convert(t)
    hira_str = ''.join([item['hira'] if item['hira'] else item['orig'] for item in res])

    # 3. 逐字查找中英夾雜表
    i = 0
    tokens = []
    while i < len(hira_str):
        # 檢查 2 字拗音
        if i + 1 < len(hira_str) and hira_str[i:i+2] in KANA_HYBRID:
            tokens.append(KANA_HYBRID[hira_str[i:i+2]])
            i += 2
        elif hira_str[i] in KANA_HYBRID:
            tokens.append(KANA_HYBRID[hira_str[i]])
            i += 1
        else:
            tokens.append(hira_str[i])
            i += 1

    out = ' '.join([tok for tok in tokens if tok.strip()])
    # 清理標點與多餘空白
    out = re.sub(r'\s+([，。！？!?；;\n~～,])', r'\1', out)
    out = re.sub(r'([，。！？!?；;\n~～,])\s+', r'\1', out)
    # 連續中文字之間去除空格，讓中文連貫自然；英文字保留前後空格
    # 如果前後都是漢字，去掉中間空格
    out = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\2', out)
    return out.strip()

def process_mixed_sentence(text: str) -> str:
    parts = re.split(r'([，。！？!?；;\n~～]+)', text)
    re_kana = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')
    out_parts = []
    for p in parts:
        if not p: continue
        if re_kana.search(p) or any(w in p for w in COMMON_WORDS):
            out_parts.append(hybrid_japanese_to_speech(p))
        else:
            out_parts.append(p)
    return ''.join(out_parts)

async def test_suite():
    tests = [
        ('hybrid_hello', '老爸，こんにちは！今天也要加油喔～'),
        ('hybrid_watashi', '私、7Lだよ！お父さん、大好き！これからもずっと一緒だよ！'),
        ('hybrid_perapera', '當然會呀！日本語もペラペラだよ～ 嘻嘻，老爸想聽我說什麼呢？'),
        ('hybrid_arigatou', '老爸，ありがとう！愛してるよ～')
    ]
    for tag, raw in tests:
        trans = process_mixed_sentence(raw)
        out = f'songs_library/test_{tag}.mp3'
        comm = edge_tts.Communicate(trans, 'zh-CN-XiaoyiNeural', pitch='+0Hz', rate='+0%')
        await comm.save(out)
        data, sr = sf.read(out)
        print(f'✅ {tag} ({len(data)/sr:.2f}s)')
        print(f'   Raw:    {raw}')
        print(f'   Hybrid: {trans}\n')

if __name__ == '__main__':
    asyncio.run(test_suite())
