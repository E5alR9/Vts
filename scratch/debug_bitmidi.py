import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

url = 'https://bitmidi.com/search?q=Clair+de+Lune'
resp = requests.get(url, headers=headers, timeout=6)
print('Status code:', resp.status_code)
print('Length:', len(resp.text))

links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
print(f'Total links found: {len(links)}')
for h, t in links:
    clean_t = re.sub(r'<[^>]+>', '', t).strip()
    if '-mid' in h or 'clair' in h.lower() or 'lune' in h.lower():
        print(f'HREF: {h} | Title: {clean_t}')
