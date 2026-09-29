# -*- coding: utf-8 -*-
"""Persona 角色卡測試（檔案即真相源；ck 下的 commit 必須同步更新 md）。"""
from conftest import ROOT  # noqa: F401
from core import persona as P


def test_persona_files_render_both_modes():
    for mode in ("vtuber", "companion"):
        p = P.load_persona(mode)
        assert p["mode"] == mode
        for key in ("base", "overlay", "behavior", "fewshots_raw"):
            assert p[key] and p[key].strip(), key
            assert "{{owner}}" not in p[key] and "{{character}}" not in p[key], key
    v = P.load_persona("vtuber")["overlay"]
    c = P.load_persona("companion")["overlay"]
    assert v != c
    assert "觀眾" in v and "一對一" in c


def test_persona_invalid_mode_falls_back():
    assert P.load_persona("亂填")["mode"] == "vtuber"


def test_fewshots_parse():
    exs = P.get_fewshot_examples("vtuber")
    assert len(exs) == 5
    for ex in exs:
        assert ex["scenario"] and ex["input"] and ex["reply"]
    assert P.parse_fewshots("### 壞塊\n沒有分隔符\n") == []


def test_hard_rules_assembles():
    rules = P.hard_rules("vtuber")
    assert "自稱" in rules and "pe.play_virtual_piano" in rules
    assert "受話對象" in rules  # vtuber 疊加有進來
    comp = P.hard_rules("companion")
    assert "一對一" in comp and "絕不自作多情" not in comp
