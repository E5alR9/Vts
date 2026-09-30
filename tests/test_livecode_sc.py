# -*- coding: utf-8 -*-
"""外部橋接測試（OSC 編碼＋缺件提示；不需裝 SuperCollider/FoxDot/Sonic Pi）。"""
from conftest import ROOT  # noqa: F401
from services import livecode_sc as sc


def test_osc_message_encoding():
    pkt = sc.osc_message("/run-code", ["JOB", "play 60"])
    assert pkt.startswith(b"/run-code\x00")
    assert b"play 60" in pkt
    assert len(pkt) % 4 == 0
    try:
        sc.osc_message("/x", [123])
        assert False, "非 string 應拋錯"
    except TypeError:
        pass


def test_backend_defaults_and_switch():
    import os
    os.environ.pop("LIVECODE_BACKEND", None)
    assert sc.backend() == "mini"
    os.environ["LIVECODE_BACKEND"] = "sonicpi"
    assert sc.backend() == "sonicpi"
    os.environ.pop("LIVECODE_BACKEND", None)


def test_foxdot_missing_hint():
    import pytest
    try:
        __import__("FoxDot")
        pytest.skip("本機有 FoxDot，跳過缺件測試")
    except ImportError:
        pass
    b = sc.FoxDotBridge()
    try:
        b.start()
        assert False, "應提示安裝腳本"
    except RuntimeError as e:
        assert "install_livecoding" in str(e)
