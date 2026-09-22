import psutil
import datetime

for p in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
    try:
        cmd = ' '.join(p.info['cmdline'] or [])
        if 'vts_7L' in cmd or 'python' in p.info['name'].lower():
            t = datetime.datetime.fromtimestamp(p.info['create_time']).strftime('%H:%M:%S')
            print(f"PID: {p.info['pid']} | Started: {t} | Cmd: {cmd[:100]}")
    except Exception:
        pass
