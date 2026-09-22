import re

test_inputs = [
    "[PLAY_VIRTUAL_PIANO: song_name='蕭邦 冬風', auto_radio_mode=True]",
    "[PLAY_VIRTUAL_PIANO: 花之塔]",
    '[PLAY_VIRTUAL_PIANO: song_name="卡農"]',
    "[PLAY_PIANO: 少女的祈禱, auto_radio_mode=True]"
]

for text in test_inputs:
    piano_tag_m = re.search(r'\[(?:PLAY_VIRTUAL_PIANO|PLAY_PIANO|PLAY_SONG)[：:]\s*([^\]]+)\]', text, re.IGNORECASE)
    if piano_tag_m:
        tag_args_raw = piano_tag_m.group(1).strip()
        parsed_song_name = ''
        parsed_auto_radio = False
        s_name_m = re.search(r'(?:song_name|title)\s*=\s*[\'"]?([^\'",\]]+)[\'"]?', tag_args_raw, re.IGNORECASE)
        if s_name_m:
            parsed_song_name = s_name_m.group(1).strip()
        else:
            parsed_song_name = tag_args_raw.split(',')[0].strip().strip('\'"')
            
        if re.search(r'auto_radio_mode\s*=\s*(?:True|1)', tag_args_raw, re.IGNORECASE):
            parsed_auto_radio = True
            
        print(f"Input: {text} => Name: '{parsed_song_name}', Radio: {parsed_auto_radio}")
