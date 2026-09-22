import sys, os, re, json

cat_path = r'c:\Users\qiwai\midi_sheets\midi_catalog.json'
with open(cat_path, 'r', encoding='utf-8') as f:
    cat = json.load(f)

queries = [
    'Ballade No. 1 in G Minor,Op.23',
    'Ballade No. 1 in G Minor, Op. 23',
    'Op. 23'
]

for q in queries:
    clean_q = q.strip().lower()
    norm_q = re.sub(r'[\'\"-_.,!?()（）\s]+', ' ', clean_q).strip()
    print(f"\n=== Query: {q} ===")
    print(f"clean_q: {clean_q}, norm_q: {norm_q}")
    for k_midi, path_midi in cat.items():
        k_norm = re.sub(r'[\'\"-_.,!?()（）\s]+', ' ', k_midi.lower()).strip()
        if k_norm in norm_q:
            print(f"MATCH: k_norm '{k_norm}' in norm_q '{norm_q}' -> {path_midi}")
        if norm_q in k_norm:
            print(f"MATCH: norm_q '{norm_q}' in k_norm '{k_norm}' -> {path_midi}")
        if k_midi.lower() in clean_q:
            print(f"MATCH: k_midi '{k_midi}' in clean_q '{clean_q}' -> {path_midi}")
        if clean_q in k_midi.lower():
            print(f"MATCH: clean_q '{clean_q}' in k_midi '{k_midi}' -> {path_midi}")
