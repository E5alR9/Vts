with open('vts_7L_test.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('pe.current_piano_song_title=pe.current_piano_song_title',
                          'current_piano_song_title=pe.current_piano_song_title')
with open('vts_7L_test.py', 'w', encoding='utf-8') as f:
    f.write(content)
