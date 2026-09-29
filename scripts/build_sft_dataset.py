# -*- coding: utf-8 -*-
"""7L SFT 語料匯出：統一記憶＋對話庫 → 微調用 jsonl（messages 格式，Axolotl/LLaMA-Factory 通吃）。
跑法：py -3.12 scripts/build_sft_dataset.py
輸出：finetune_data/7l_sft.jsonl ＋ 统计行數。語料會隨開播自動長大，三不五時重跑即可。
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT_DIR = os.path.join(BASE, "finetune_data")
OUT_PATH = os.path.join(OUT_DIR, "7l_sft.jsonl")

SYSTEM_SHORT = (
    "妳是 7L，老爸的 AI 女兒，TikTok 副播。說話自然隨性，1~2 句短話，"
    "熟人稱呼要叫對，遊戲事務一律推給老爸做主。"
)

TAG_RE = re.compile(r'\[[A-Z_\u4e00-\u9fa5]+(?:[：:]\s*[^\]]*)?\]')
URL_RE = re.compile(r'https?://\S+')
NOISE_RE = re.compile(r'^(?:\[|【|http|\(|系統|schw|ubs_|番茄鐘|計時|鋼琴.*(?:開始|結束|演奏中)|字幕|TTS|API|GPU|CUDA|Error|Traceback)', re.IGNORECASE)


def clean(s: str) -> str:
    s = TAG_RE.sub('', s or '')
    s = URL_RE.sub('', s)
    s = re.sub(r'\s+', ' ', s).strip(' ，,')
    return s


def usable(s: str) -> bool:
    return 4 <= len(s) <= 140 and not NOISE_RE.search(s)


def load_json_list(path: str):
    try:
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
        if isinstance(d, list):
            return d
        if isinstance(d, dict):
            for v in d.values():
                if isinstance(v, list):
                    return v
    except Exception:
        pass
    return []


def main():
    items = []
    for fn in ("unified_memory.json", "dialogue_memory.json"):
        items.extend(load_json_list(os.path.join(DATA, fn)))
    # 按時間排序，相鄰 user→assistant 配對
    items.sort(key=lambda x: x.get("time", 0.0) if isinstance(x, dict) else 0)
    pairs = []
    seen = set()
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            continue
        role = it.get("role", "")
        spk = it.get("speaker", "")
        content = clean(str(it.get("content", "")))
        is_user = role == "user" or ("觀眾" in spk or "老爸" in spk)
        if not (is_user and usable(content)):
            continue
        # 找下一則 7L 回覆
        for nxt in items[i + 1:i + 4]:
            if not isinstance(nxt, dict):
                continue
            nrole, nspk = nxt.get("role", ""), nxt.get("speaker", "")
            if nrole == "assistant" or nspk == "7L":
                out = clean(str(nxt.get("content", "")))
                if usable(out) and (content, out) not in seen:
                    seen.add((content, out))
                    who = "觀眾說" if "觀眾" in spk else "老爸說"
                    pairs.append({"messages": [
                        {"role": "system", "content": SYSTEM_SHORT},
                        {"role": "user", "content": f"{who}：「{content}」"},
                        {"role": "assistant", "content": out},
                    ]})
                break
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"✅ 匯出 {len(pairs)} 對 → {OUT_PATH}")
    print("   不夠訓就多開幾天台再跑一次，檔案會自己長大。")


if __name__ == "__main__":
    sys.exit(main())
