import os
import re

file_path = r"c:\Users\qiwai\core\prompts.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Marker start:
marker_start = "# 46. 校 (jiào vs xiào) - 校對/校正一律讀 jiào\n        t = re.sub(r'校(對|準|正|驗)', r'叫\\1', t)\n        \n"
idx_start = content.find(marker_start)
if idx_start == -1:
    print("ERROR: marker_start not found!")
    exit(1)

pos_after_marker_start = idx_start + len(marker_start)

# Marker end:
marker_end = "\nclass PromptTemplateEngine:"
idx_end = content.find(marker_end)
if idx_end == -1:
    print("ERROR: marker_end not found!")
    exit(1)

clean_middle = '''        # 47. 漂 (piāo vs piǎo vs piào)
        t = re.sub(r'漂(浮|流|移)', r'飄\\1', t)
        t = t.replace('漂白', '殍白').replace('漂亮', '票亮')
        
        # 48. 打 (dá vs dǎ)
        t = t.replace('一打', '一達')
        
        # 49. 和 (hè vs huó vs huò)
        t = re.sub(r'(一唱一|附|應)和', r'\\1賀', t)
        t = t.replace('曲高和寡', '曲高賀寡')
        t = re.sub(r'和(面|麵)', r'活\\1', t)
        t = t.replace('和藥', '惑藥')
        
        # 50. 係 (jì vs xì) - 繫帶一律讀 jì
        t = re.sub(r'繫(好)?(鞋帶|安全帶|領帶|上)', r'記\\1\\2', t)
        
        # 51. 咽 (yàn vs yè vs yān)
        t = re.sub(r'(吞|狼吞虎)咽', r'\\1驗', t)
        t = re.sub(r'(嗚|哽)咽', r'\\1夜', t)
        
        # 52. 載 (zǎi vs zài)
        t = re.sub(r'(登|刊|記)載', r'\\1仔', t)
        t = re.sub(r'(三年五|千)載', r'\\1仔', t)
        t = re.sub(r'(下|加|轉|上傳)載', r'\\1在', t)
        t = re.sub(r'載(入|重|滿|客|運|歌載舞)', r'在\\1', t)
        
        # 53. 提 (dī vs tí)
        t = t.replace('提防', '低防')
        
        # 54. 冠 (guàn vs guān)
        t = re.sub(r'(奪|衛冕|勇奪)冠', r'\\1慣', t)
        t = t.replace('冠軍', '慣軍')
        t = re.sub(r'(皇|衣|桂)冠', r'\\1官', t)
        
        # 55. 龜 (jūn vs guī)
        t = t.replace('龜裂', '軍裂')
        
        # 56. 匙 (shi vs chí)
        t = t.replace('鑰匙', '要石')
        t = re.sub(r'(湯|茶)匙', r'\\1池', t)
        
        # 57. 露 (lòu vs lù)
        t = re.sub(r'露(面|頭|臉|餡|馬腳)', r'漏\\1', t)
        
        # 58. 泊 (pō vs bó)
        t = re.sub(r'(湖|血)泊', r'\\1坡', t)
        t = re.sub(r'(停|漂)泊', r'\\1博', t)
        
        # 59. 圈 (juàn vs quān)
        t = re.sub(r'(豬|羊|牛)圈', r'\\1倦', t)
        
        # 60. 荷 (hè vs hé)
        t = re.sub(r'(負|重)荷', r'\\1賀', t)
        
        # 61. 爪 (zhuǎ vs zhǎo)
        t = t.replace('爪子', '准子')
        t = re.sub(r'(鷹|魔|利)爪', r'\\1沼', t)
        
        # 62. 殼 (qiào vs ké)
        t = re.sub(r'(地|甲)殼', r'\\1俏', t)
        t = re.sub(r'(蛋|貝|腦|外)殼', r'\\1咳', t)
        
        # 63. 強 (qiǎng vs jiàng vs qiáng)
        t = re.sub(r'(強迫|勉強)', lambda m: '搶迫' if m.group(0)=='強迫' else '免搶', t)
        t = t.replace('倔強', '倔降')

        # 64. 沒 (méi vs mò) - 口語「有的沒的」徹底校正為 méi 發音（防 Edge-TTS 誤讀古典詞「沒的 mò de」）
        t = re.sub(r'有的(沒|没)的', r'有的梅的', t)
        t = re.sub(r'有的(沒|没)', r'有的梅', t)
        t = re.sub(r'(那些|這些|那種|這種|很多|搞|聊|扯|說|講)沒的', r'\\1梅的', t)

        # 65. 樂 (yuè vs lè) - 音樂相關詞彙 100% 精準校正為 yuè (月) 發音，絕不誤讀成 lè (ㄌㄜˋ)
        t = re.sub(r'(古典|音樂|交響|管弦|弦|國|民|聲|爵士|流行|搖滾|純音|輕音|背景|鋼琴|配|奏)樂', r'\\1月', t)
        t = re.sub(r'樂(曲|取|譜|器|團|隊|章|理|壇|手|迷|界|評)', r'月\\1', t)
        t = t.replace('音樂會', '音月會')

        # 66. 幾 (jǐ vs jī) - 數量、人稱、時間、疑問一律讀 jǐ (ㄐㄧˇ，以「己」替換，防 Edge-TTS 誤讀成 jī ㄐㄧ)
        ji_jī_words = ['幾乎', '茶几', '窗几', '几案', '几桌', '幾希', '幾率', '几椅']
        ji_placeholders = {}
        for idx, w in enumerate(ji_jī_words):
            if w in t:
                ph = f'__JI_JI_{idx}__'
                ji_placeholders[ph] = w
                t = t.replace(w, ph)
        
        t = t.replace('幾個人', '己個人')
        t = t.replace('幾個', '己個')
        t = re.sub(r'幾(位|人|天|次|點|分|秒|隻|只|把|張|條|根|件|本|首|種|樣|回|遍|套|門|杯|瓶|碗|口|步|筆|串|棟|家|輛|架|歲|輪|代|款|段|篇|名|排|隊|句|台|部|十|百|千|萬|億|何|時|許|塊|顆|串|組|倍)', r'己\\1', t)
        t = re.sub(r'(好|十|這|那|有|沒|前|後|第)幾', r'\\1己', t)
        t = t.replace('所剩無幾', '所剩無己').replace('寥寥無幾', '寥寥無己').replace('相差無幾', '相差無己')
        t = t.replace('幾', '己')

        for ph, w in ji_placeholders.items():
            t = t.replace(ph, w)

        # 67. 載入自訂字典 (data/tts_heteronym_dictionary.json)
        dict_file = os.path.join(DATA_DIR, "tts_heteronym_dictionary.json")
        if os.path.exists(dict_file):
            try:
                with open(dict_file, "r", encoding="utf-8") as f:
                    custom_dict = json.load(f)
                custom_repls = custom_dict.get("自訂單詞發音置換", {})
                for k, v in custom_repls.items():
                    if k in t:
                        t = t.replace(k, v)
            except Exception:
                pass
                
        return t

    @classmethod
    def clean_for_tts(cls, text: str, apply_phonetics: bool = True) -> str:
        """語音合成 (TTS) 前置專用清洗（徹底保證 100% 不唸出大腦心想與系統標籤，並精準校正破音字發音）"""
        if not text:
            return ""
        t = cls.RE_THOUGHT_TAG.sub('', text)
        t = cls.RE_THINK_BLOCK.sub('', t)
        t = cls.RE_THINKING_PROC.sub('', t)
        t = cls.RE_PAREN_THINK.sub('', t)
        t = cls.RE_TAG_BRACKETS.sub('', t)
        t = cls.RE_SPEAKER_PREFIX.sub('', t)
        t = re.sub(r'^(?:回應|回覆|動作顯示|主播|說道|回答)[：:\\s]+', '', t, flags=re.IGNORECASE)
        t = cls.RE_AT_MENTION.sub(lambda m: m.group(0)[1:], t)
        t = t.replace('@', '').replace('*', '').strip()
        t = cls.strip_emojis(t)
        t = cls.natural_clause_segmentation(t)
        if apply_phonetics:
            t = cls.fix_heteronyms_for_tts(t)
        if re.search(r'[\\u3040-\\u309F\\u30A0-\\u30FF]', t) or any(w in t for w in ['こんにちは', '私', '大好き', 'ありがとう', 'お父さん', '愛してる']):
            t = cls.japanese_to_xiaoyi_phonetic(t)
        return t

    _KAKASI_INST = None
    _KANA_MAP = {
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

        # 50 音 (中文漢字為主，特殊音如 knee/kee/tsoo/say/kay/tay/nay/doh 等英文輔助)
        'あ': '阿', 'い': '伊', 'う': '屋', 'え': '欸', 'お': '歐',
        'ア': '阿', 'イ': '伊', 'ウ': '屋', 'エ': '欸', 'オ': '歐',
        'か': '卡', 'き': 'kee', 'く': '庫', 'け': 'kay', 'こ': '摳',
        'カ': '卡', 'キ': 'kee', 'ク': '庫', 'ケ': 'kay', 'コ': '摳',
        'が': '嘎', 'ぎ': 'ghee', 'ぐ': 'goo', 'げ': 'gay', 'ご': 'goh',
        'ガ': '嘎', 'ギ': 'ghee', 'グ': 'goo', 'ゲ': 'gay', 'ゴ': 'goh',
        'さ': '薩', 'し': '西', 'す': 'soo', 'せ': 'say', 'そ': '搜',
        'サ': '薩', 'シ': '西', 'ス': 'soo', 'セ': 'say', 'ソ': '搜',
        'ざ': '砸', 'じ': '吉', 'ず': 'zoo', 'ぜ': 'zay', 'ぞ': 'zoh',
        'ザ': '砸', 'ジ': '吉', 'ズ': 'zoo', 'ゼ': 'zay', 'ゾ': 'zoh',
        'た': '塔', 'ち': '七', 'つ': 'tsoo', 'て': 'tay', 'と': 'toh',
        'タ': '塔', 'チ': '七', 'ツ': 'tsoo', 'テ': 'tay', 'ト': 'toh',
        'だ': '搭', 'ぢ': '吉', 'づ': 'zoo', 'で': 'day', 'ど': 'doh',
        'ダ': '搭', 'ヂ': '吉', 'ヅ': 'zoo', 'デ': 'day', 'ド': 'doh',
        'な': '那', 'に': 'knee', 'ぬ': '奴', 'ね': 'nay', 'の': 'know',
        'ナ': '那', 'ニ': 'knee', 'ヌ': '奴', 'ネ': 'nay', 'ノ': 'know',
        'は': '哈', 'ひ': 'hee', 'ふ': '呼', 'へ': 'hay', 'ほ': 'hoe',
        'ハ': '哈', 'ヒ': 'hee', 'フ': '呼', 'ヘ': 'hay', 'ホ': 'hoe',
        'ば': '巴', 'び': '比', 'ぶ': '布', 'べ': 'bay', 'ぼ': '波',
        'バ': '巴', 'ビ': '比', 'ブ': '布', 'ベ': 'bay', 'ボ': '波',
        'ぱ': '帕', 'ぴ': 'pee', 'ぷ': '鋪', 'ぺ': 'pay', 'ぽ': '坡',
        'パ': '帕', 'ピ': 'pee', 'プ': '鋪', 'ペ': 'pay', 'ポ': '坡',
        'ま': '馬', 'み': '米', 'む': '木', 'め': 'may', 'も': '莫',
        'マ': '馬', 'ミ': '米', 'ム': '木', 'メ': 'may', 'モ': '莫',
        'や': '亞', 'ゆ': 'yoo', 'よ': '喲',
        'ヤ': '亞', 'ユ': 'yoo', 'ヨ': '喲',
        'ら': '拉', 'り': '里', 'る': '嚕', 'れ': '雷', 'ろ': '羅',
        'ラ': '拉', 'リ': '里', 'ル': '嚕', 'レ': '雷', 'ロ': '羅',
        'わ': '哇', 'を': '歐',
        'ワ': '哇', 'ヲ': '歐',
        'ん': '恩', 'ン': '恩',
    }

    _HIRA_PHRASE_RULES = [
        (r'こんにち[はわ]', '空 knee 七哇'),
        (r'こんばん[はわ]', '空 邦 哇'),
        (r'ありがとう', '阿里嘎多'),
        (r'おとうさん', '歐托桑'),
        (r'だいすき', '搭一 soo kee'),
        (r'あいしてる', '阿伊西貼嚕'),
        (r'にほんご', 'knee 宏國'),
        (r'ぺらぺら', '佩拉佩拉'),
        (r'お早う|おはよう', '歐哈優'),
        (r'ごめんなさい', '果面那塞'),
        (r'かわいい', '卡哇伊'),
        (r'すごい', '絲國伊'),
        (r'よろしく', '喲羅西庫'),
        (r'わたし', '哇塔西'),
        (r'だよ', '搭優'),
        (r'これからも', '扣雷卡拉莫'),
        (r'ずっと', '租 t 托'),
        (r'いっしょ', '伊修'),
    ]

    @classmethod
    def japanese_to_xiaoyi_phonetic(cls, text: str) -> str:
        """🎙️ 將日文字句轉為微軟 Xiaoyi 中英夾雜黃金音標 (以中文為骨幹，特殊音 knee/kee/tsoo 英文輔助)"""
        if not text:
            return ""
        if not re.search(r'[\\u3040-\\u309F\\u30A0-\\u30FF]', text) and not any(w in text for w in ['こんにちは', '私', '大好き', 'ありがとう', 'お父さん', '愛してる']):
            return text
            
        try:
            if cls._KAKASI_INST is None:
                import pykakasi
                cls._KAKASI_INST = pykakasi.kakasi()
        except Exception:
            return text

        parts = re.split(r'([，。！？!?；;\\n~～]+)', text)
        re_kana = re.compile(r'[\\u3040-\\u309F\\u30A0-\\u30FF]')
        out_parts = []
        for p in parts:
            if not p:
                continue
            if not re_kana.search(p) and not any(w in p for w in ['こんにちは', '私', '大好き', 'ありがとう', 'お父さん', '愛してる']):
                out_parts.append(p)
                continue

            seg = p
            seg = seg.replace('、', '，')
            seg = seg.replace('愛してる', 'あいしてる')
            seg = seg.replace('大好き', 'だいすき')
            seg = seg.replace('お父さん', 'おとうさん')
            seg = seg.replace('私', 'わたし')
            seg = seg.replace('日本語', 'にほんご')

            res = cls._KAKASI_INST.convert(seg)
            hira_str = ''.join([item['hira'] if item['hira'] else item['orig'] for item in res])

            for pat, rep in cls._HIRA_PHRASE_RULES:
                hira_str = re.sub(pat, f' {rep} ', hira_str)

            tokens = []
            raw_parts = hira_str.split()
            for rp in raw_parts:
                if re.search(r'[\\u4e00-\\u9fa5]', rp) or re.match(r'^[a-zA-Z0-9]+$', rp):
                    tokens.append(rp)
                    continue

                i = 0
                while i < len(rp):
                    if i + 1 < len(rp) and rp[i:i+2] in cls._KANA_MAP:
                        tokens.append(cls._KANA_MAP[rp[i:i+2]])
                        i += 2
                    elif rp[i] in cls._KANA_MAP:
                        tokens.append(cls._KANA_MAP[rp[i]])
                        i += 1
                    else:
                        tokens.append(rp[i])
                        i += 1

            raw_str = ' '.join(tokens)
            raw_str = re.sub(r'([\\u4e00-\\u9fa5])\\s+([\\u4e00-\\u9fa5])', r'\\1\\2', raw_str)
            raw_str = re.sub(r'\\s+([，。！？!?；;\\n~～,、])', r'\\1', raw_str)
            raw_str = re.sub(r'([，。！？!?；;\\n~～,、])\\s+', r'\\1', raw_str)
            out_parts.append(raw_str.strip())

        return ''.join(out_parts)
'''

new_content = content[:pos_after_marker_start] + clean_middle + content[idx_end:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("SUCCESS: core/prompts.py updated cleanly with V2 fixes!")
