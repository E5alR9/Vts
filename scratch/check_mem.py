import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
with urllib.request.urlopen('http://127.0.0.1:7860/api/memory') as res:
    data = json.loads(res.read().decode('utf-8'))
    for item in data.get('memories', []):
        if item.get('role') != 'thought':
            print(f"{item.get('time_str')} [{item.get('speaker')} -> {item.get('target')}]: {item.get('content')}")
