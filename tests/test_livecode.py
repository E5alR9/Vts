# -*- coding: utf-8 -*-
"""Live Coding 引擎測試（解析／節奏／級數／展開時序；不碰音訊裝置）。"""
import asyncio
from conftest import ROOT  # noqa: F401
from services import livecode as lc


def test_euclid_known():
    assert lc.euclid(3, 8) == "x..x..x."
    assert lc.euclid(0, 4) == "...."
    assert lc.euclid(4, 4) == "xxxx"
    assert sum(lc.parse_grid("euclid(5,8)")) == 5


def test_deg_to_midi():
    assert lc.deg_to_midi("Am", 1) == 57
    assert lc.deg_to_midi("Am", 8) == 69
    assert lc.deg_to_midi("Am", 0) == 55
    assert lc.deg_to_midi("C", 5) == 67
    assert lc.deg_to_midi("Am", -6) == 45


def test_parse_code():
    p = lc.parse_code("""
bpm 120
# 註解行
drums bd:x-x- sn:--x-
bass key=Am deg=1 5 4 4
stab chord=Am7 rhythm=x---x---
lead notes=69,72 prog=81
""")
    assert p["bpm"] == 120
    kinds = [t["kind"] for t in p["tracks"]]
    assert kinds.count("drum") == 2
    assert "notes" in kinds and "chord" in kinds
    bass = next(t for t in p["tracks"] if t["name"] == "bass")
    assert bass["notes"][0] == 57


def test_expand_timing():
    p = lc.parse_code("bpm 120\ndrums bd:x---")
    events, dur = lc.expand(p, bars=1)
    assert dur == 2.0
    assert events[0][0] == 0.0
    assert all(e[0] < dur for e in events)


def test_live_hot_update():
    got = []
    loop = lc.LiveLoop("t1", "bpm 120\ndrums bd:x---", sink=lambda k, p: got.append((k, p)), bars=1)
    loop.update("bpm 120\ndrums bd:x--- sn:--x-")
    assert len(loop.events) > 1
    lc.stop("t1")
    assert "t1" not in lc.LiveLoop.registry


def test_foxdot_codegen():
    p = lc.parse_code("bpm 100\ndrums bd:x-x-\nbass key=Am deg=1 5\nlead notes=69,72 prog=81")
    code = lc.to_foxdot(p)
    assert "Clock.bpm = 100" in code
    assert 'play("x-x-")' in code
    assert "bass([1, 5]" in code
    assert "pluck(" in code and "oct=" in code
    assert lc.midi_to_foxdot(69) == (4, 5)
    assert lc.midi_to_foxdot(60) == (4, 0)


def test_sonicpi_codegen():
    p = lc.parse_code("bpm 100\ndrums bd:x-x- sn:--x-\nbass key=Am deg=1 5")
    code = lc.to_sonicpi(p, "seven")
    assert "live_loop :seven" in code
    assert "sample :bd_haus" in code and "sample :sn_dub" in code
    assert "sleep 0.25" in code
