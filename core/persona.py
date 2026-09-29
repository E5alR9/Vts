# -*- coding: utf-8 -*-
"""
🪪 Persona 角色卡載入器（Airi CCv3 式解耦的輕量版）：人格住 `personas/*.md`，
程式碼只管解析＋渲染，不再寫死「妳是……」。

檔案：
    personas/7l_base.md       雙模式共用（身分／關係／越權鐵律）
    personas/7l_vtuber.md     MODE=vtuber 疊加（受話對象／只對觀眾）
    personas/7l_companion.md  MODE=companion 疊加（一對一）
    personas/7l_behavior.md   雙模式共用（對話／靜默／工具語法／節奏／輸出規範）
    personas/7l_fewshots.md   few-shot 示範（### 情境／> 輸入／~ 心想／正文）

佔位符：{{owner}} {{character}} {{mode}}（identity.py；非法回退）。
"""
import os
import re

PERSONA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "personas")

_FILES = {
    "base": "7l_base.md",
    "vtuber": "7l_vtuber.md",
    "companion": "7l_companion.md",
    "behavior": "7l_behavior.md",
    "fewshots": "7l_fewshots.md",
}

_cache = {}


def _read(name: str) -> str:
    if name not in _cache:
        path = os.path.join(PERSONA_DIR, _FILES[name])
        with open(path, "r", encoding="utf-8") as f:
            _cache[name] = f.read()
    return _cache[name]


def render(text: str, mode: str = "") -> str:
    """替換佔位符（缺 identity 時回退預設名，絕不炸）。"""
    try:
        from core.identity import get_owner_name, get_character_name, get_mode
        owner, char = get_owner_name(), get_character_name()
        mode = mode or get_mode()
    except Exception:
        owner, char, mode = "老爸", "7L", mode or "vtuber"
    return (text.replace("{{owner}}", owner)
                 .replace("{{character}}", char)
                 .replace("{{mode}}", mode))


def load_persona(mode: str = "") -> dict:
    """回傳 {base, overlay, behavior, fewshots_raw}（已渲染）。"""
    try:
        from core.identity import get_mode
        mode = (mode or get_mode()).strip().lower()
    except Exception:
        mode = (mode or "vtuber").strip().lower()
    if mode not in ("companion", "vtuber"):
        mode = "vtuber"
    overlay_name = "companion" if mode == "companion" else "vtuber"
    return {
        "mode": mode,
        "base": render(_read("base"), mode),
        "overlay": render(_read(overlay_name), mode),
        "behavior": render(_read("behavior"), mode),
        "fewshots_raw": render(_read("fewshots"), mode),
    }


def parse_fewshots(raw: str) -> list:
    """解析 fewshots.md → [{scenario, input, thought, reply}]（寬容解析，壞塊跳過）。"""
    out = []
    for chunk in re.split(r"(?m)^###\s*", raw or ""):
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.splitlines()
        scenario = lines[0].strip()
        inp, thought, reply_lines = "", "", []
        for ln in lines[1:]:
            s = ln.strip()
            if s.startswith(">") and not inp:
                inp = s[1:].strip()
            elif s.startswith("~") and not thought:
                thought = s[1:].strip()
            elif s:
                reply_lines.append(ln.rstrip())
        reply = "\n".join(reply_lines).strip()
        if inp and reply:
            out.append({"scenario": scenario, "input": inp, "thought": thought, "reply": reply})
    return out


def get_fewshot_examples(mode: str = "") -> list:
    return parse_fewshots(load_persona(mode)["fewshots_raw"])


def hard_rules(mode: str = "") -> str:
    """HARD_TECHNICAL_RULES 的真相源：base＋overlay＋behavior 組裝。
    prompts.py 的舊常數僅為相容快照，新碼一律調用此函式。"""
    p = load_persona(mode)
    return f"{p['base']}\n\n{p['overlay']}\n\n{p['behavior']}"


def clear_cache():
    _cache.clear()
