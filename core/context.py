# -*- coding: utf-8 -*-
"""
🧩 ContextManager（Airi systemPromptSupplement 式模組化注入＋層級組裝）。

用法：
    from core import context
    context.register("piano", get_piano_prompt)          # fn(ctx) -> str
    context.register("news", get_news, enabled=lambda ctx: ctx.get("need_news"))
    blocks = context.collect({"need_news": True})        # [(name, text)]，空值自動丟
    prompt = context.assemble(root=..., state=..., sensory_blocks=blocks, task=...)

層級（由重到輕，LLM 注意力顺序）：
    [SYSTEM ROOT]  絕對人格與最高指令（persona.hard_rules）
    [RUNTIME STATE] 時間／演奏狀態／系統狀態
    [SENSORY]      RAG／記憶／視覺等感官補充（providers 來）
    [TASK]         本次對話焦點
空區塊自動省略，分隔符統一，避免一大包 f-string。
"""
from typing import Callable, Dict, List, Tuple

_providers: List[Tuple[str, Callable, Callable]] = []


def register(name: str, fn: Callable, enabled: Callable = None):
    """註冊補充源。fn(ctx)->str；enabled(ctx)->bool 缺省恆開。重名原地覆蓋（順序不變）。"""
    global _providers
    for i, (n, _, _) in enumerate(_providers):
        if n == name:
            _providers[i] = (name, fn, enabled)
            return
    _providers.append((name, fn, enabled))


def unregister(name: str):
    global _providers
    _providers = [(n, f, e) for n, f, e in _providers if n != name]


def providers() -> List[str]:
    return [n for n, _, _ in _providers]


def collect(ctx: dict = None) -> List[Tuple[str, str]]:
    """依註冊顺序收集非空補充（單源異常只跳過該源，絕不炸整條）。"""
    ctx = ctx or {}
    out = []
    for name, fn, enabled in list(_providers):
        try:
            if enabled is not None and not enabled(ctx):
                continue
            text = fn(ctx)
        except Exception:
            continue
        if text and str(text).strip():
            out.append((name, str(text).strip()))
    return out


def assemble(root: str = "", state: str = "", sensory=None, task: str = "") -> str:
    """層級組裝（空區塊省略）。sensory 可為 [(name, text)] 或純字串／字串陣列。"""
    if sensory is None:
        sensory_blocks = []
    elif isinstance(sensory, str):
        sensory_blocks = [sensory] if sensory.strip() else []
    elif isinstance(sensory, (list, tuple)):
        sensory_blocks = []
        for item in sensory:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                _, text = item
            else:
                text = item
            if text and str(text).strip():
                sensory_blocks.append(str(text).strip())
    else:
        sensory_blocks = [str(sensory)] if str(sensory).strip() else []
    parts = []
    if root and root.strip():
        parts.append(f"[SYSTEM ROOT]\n{root.strip()}")
    if state and state.strip():
        parts.append(f"[RUNTIME STATE]\n{state.strip()}")
    if sensory_blocks:
        parts.append("[SENSORY]\n" + "\n\n---\n".join(sensory_blocks))
    if task and task.strip():
        parts.append(f"[TASK]\n{task.strip()}")
    return "\n\n".join(parts)


def clear():
    global _providers
    _providers = []
