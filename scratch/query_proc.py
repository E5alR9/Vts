import urllib.request, json
payload = {
    'tool': 'execute_local_python_code',
    'args': {'code_string': 'import os\nRESULT = f"CWD: {os.getcwd()} | data_exists: {os.path.exists(\'data/sounds_7L_clean\')}"'}
}
req = urllib.request.Request('http://127.0.0.1:7860/api/tools/execute', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(req, timeout=5) as res:
    print(res.read().decode('utf-8'))
