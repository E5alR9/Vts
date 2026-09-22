import requests, re

url = 'https://bitmidi.com/search?q=rhapsody+in+blue'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
try:
    resp = requests.get(url, headers=headers, timeout=6)
    print('status:', resp.status_code, 'len:', len(resp.text))
    matches = re.findall(r'href="(/[^\"]+-mid)"', resp.text)
    print('matches:', matches[:10])
except Exception as e:
    print('err:', e)
