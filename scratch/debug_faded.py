import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

url = 'https://bitmidi.com/search?q=Faded'
resp = requests.get(url, headers=headers, timeout=6)
links = re.findall(r'<a[^>]+href="(/[^"]+-mid)"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
print('Faded results in search:', len(links))
if links:
    page_url = 'https://bitmidi.com' + links[0][0]
    print('Detail page:', page_url)
    p_resp = requests.get(page_url, headers=headers, timeout=6)
    dl_links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', p_resp.text, re.DOTALL)
    for h, t in dl_links:
        if 'mid' in h.lower() or 'upload' in h.lower() or 'download' in h.lower():
            print('Download candidate link:', h, '| text:', t.strip())
