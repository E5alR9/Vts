# -*- coding: utf-8 -*-
"""ContextManager 測試（註冊／收集／容錯／層級組裝）。"""
from conftest import ROOT  # noqa: F401
from core import context as C


def setup_function(_):
    C.clear()


def test_register_collect_order_and_filter():
    C.register("b", lambda ctx: "B")
    C.register("a", lambda ctx: "A")
    C.register("gated", lambda ctx: "G", enabled=lambda ctx: ctx.get("on"))
    assert C.providers() == ["b", "a", "gated"]
    assert [n for n, _ in C.collect({})] == ["b", "a"]
    assert [n for n, _ in C.collect({"on": True})] == ["b", "a", "gated"]
    C.register("b", lambda ctx: "B2")  # 重名覆蓋
    assert C.collect({})[0] == ("b", "B2")
    C.unregister("a")
    assert "a" not in C.providers()


def test_collect_isolates_failures_and_empties():
    C.register("boom", lambda ctx: 1 / 0)
    C.register("empty", lambda ctx: "   ")
    C.register("none", lambda ctx: None)
    C.register("ok", lambda ctx: "OK")
    assert C.collect({}) == [("ok", "OK")]


def test_assemble_hierarchy_and_drop_empty():
    out = C.assemble(root="R", state="", sensory=[("s1", "S1"), ("s2", "  ")], task="T")
    assert "[SYSTEM ROOT]" in out and "[SENSORY]" in out and "[TASK]" in out
    assert "[RUNTIME STATE]" not in out  # 空區塊省略
    assert out.index("[SYSTEM ROOT]") < out.index("[SENSORY]") < out.index("[TASK]")
    assert C.assemble(sensory="solo") == "[SENSORY]\nsolo"
    assert C.assemble() == ""
