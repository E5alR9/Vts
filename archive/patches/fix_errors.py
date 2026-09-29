import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix pe. attributes
    pe_attrs = [
        'get_local_piano_seeds',
        'AUTHENTIC_MIDI_MAP',
        'MIDI_AI_MATCH_CACHE',
        'MIDI_SHEETS_DIR',
        'resolve_local_midi_file',
        'current_piano_midi_file',
        'current_piano_song_title',
        'clean_song_title_for_speech',
        'GLOBAL_PIANO_REALTIME_STATE',
        'init_piano_synthesizer',
        'piano_focus_udp_worker',
        'auto_restore_piano_state_on_startup'
    ]
    for attr in pe_attrs:
        # Look for the attribute not preceded by pe. or vc. or def or class
        # Just a simple regex replacement is fine if we are careful.
        # Since these are highly specific names, we can just replace them directly,
        # but avoid replacing pe.attr if it already exists.
        content = re.sub(r'(?<!pe\.)(?<!def )\b' + attr + r'\b', f'pe.{attr}', content)

    # Fix vc. attributes
    vc_attrs = ['EXPRESSION_HOLD_SECONDS']
    for attr in vc_attrs:
        content = re.sub(r'(?<!vc\.)(?<!def )\b' + attr + r'\b', f'vc.{attr}', content)

    # Fix the UnboundLocalError by adding global CURRENT_PROCESSING_USER_INPUT in chat_processor_worker
    # Around line 6731, we see: global current_dad_task, current_audience_task, current_voice_task, current_ai_state, CURRENT_SPEAKING_TARGET, current_tiktok_status_str
    content = content.replace(
        'global current_dad_task, current_audience_task, current_voice_task, current_ai_state, CURRENT_SPEAKING_TARGET, current_tiktok_status_str',
        'global current_dad_task, current_audience_task, current_voice_task, current_ai_state, CURRENT_SPEAKING_TARGET, current_tiktok_status_str, CURRENT_PROCESSING_USER_INPUT'
    )

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    fix_file('c:\\Users\\qiwai\\vts_7L_test.py')
