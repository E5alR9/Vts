import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

url = 'https://bitmidi.com/debussy-clair-de-lune-mid'
resp = requests.get(url, headers=headers, timeout=6)
print('Status code:', resp.status_code)

links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
for h, t in links:
    if 'download' in h or '.mid' in h or 'download' in t.lower() or 'upload' in h:
        print(f'Download Link candidate: {h} | Text: {t.strip()[:40]}')
