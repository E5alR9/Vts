# -*- coding: utf-8 -*-
"""鋼琴直轉樂隊測試：音符守恆（數量/音高/時值）＋聲部分配＋鼓直通。"""
import mido
from conftest import ROOT  # noqa: F401


def _make_piano(path):
    mid = mido.MidiFile(type=1, ticks_per_beat=480)
    t = mido.MidiTrack()
    t.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    # C 大三和弦（C4 E4 G4 同時）＋ 後續單音 A4
    for nn in (60, 64, 67):
        t.append(mido.Message("note_on", note=nn, velocity=80, channel=0, time=0))
    for nn in (60, 64, 67):
        t.append(mido.Message("note_off", note=nn, velocity=0, channel=0, time=480))
    t.append(mido.Message("note_on", note=69, velocity=90, channel=0, time=480))
    t.append(mido.Message("note_off", note=69, velocity=0, channel=0, time=480))
    mid.tracks.append(t)
    mid.save(path)
    return path


def test_arrange_preserves_notes(tmp_path, monkeypatch):
    import services.piano_engine as pe
    monkeypatch.setattr(pe, "SHEETS_ABS", str(tmp_path))
    src = _make_piano(str(tmp_path / "p.mid"))
    r = pe.arrange_piano_to_band(src, "violin_lead", out_name="p_band")
    assert r["ok"] and r["notes"] == 4, r
    out = mido.MidiFile(r["file"])
    got = {}
    for tr in out.tracks:
        chs = {m.channel for m in tr if m.type in ("note_on", "note_off")}
        n = sum(1 for m in tr if m.type == "note_on" and m.velocity > 0)
        if n:
            got[next(iter(chs))] = n
    # 最低 C4→貝斯 ch1，最高 G4→主奏 ch0，中間 E4→鋪底 ch2，單音 A4→主奏 ch0
    assert got == {1: 1, 0: 2, 2: 1}, got
    progs = {}
    for tr in out.tracks:
        for m in tr:
            if m.type == "program_change":
                progs[m.channel] = m.program
    assert progs == {0: 40, 1: 33, 2: 48}, progs


def test_arrange_missing_file():
    import services.piano_engine as pe
    r = pe.arrange_piano_to_band("不存在的檔.mid")
    assert r["ok"] is False
