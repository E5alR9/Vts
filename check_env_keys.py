# -*- coding: utf-8 -*-
with open("c:/Users/qiwai/.env", "r", encoding="utf-8") as f:
    for line in f:
        line_s = line.strip()
        if line_s and not line_s.startswith("#") and "=" in line_s:
            k, v = line_s.split("=", 1)
            v = v.strip().strip('"').strip("'")
            print(f"{k}: len={len(v)}")
            if "," in v:
                sub = [s.strip().strip('"').strip("'") for s in v.split(",") if s.strip()]
                for i, s in enumerate(sub):
                    print(f"  [{i}] prefix={s[:10]} len={len(s)}")
            else:
                print(f"  prefix={v[:10]}")
