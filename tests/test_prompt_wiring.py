# -*- coding: utf-8 -*-
"""提示詞接線測試：build_* 走 persona＋層級組裝（簽名不變、舊內容全保留）。"""
import pytest
from conftest import ROOT  # noqa: F401

pte = pytest.importorskip("core.prompts", reason="prompts 依賴重").PromptTemplateEngine


def _chat(**kw):
    args = dict(is_tiktok=False, current_custom_name="測試爸",
                stage2_target_prompt="", stage2_instructions="STAGE2",
                current_target_desc="測試對象", is_piano_active=False,
                current_piano_song_title="", live_audio_emotion_prompt="",
                situation_prompt="SIT", system_specs="", impression_text="IMP",
                cloud_knowledge_prompt="CK", unified_memory_prompt="UM")
    args.update(kw)
    return pte.build_chat_system_prompt(**args)


def test_chat_keeps_legacy_content_and_hierarchy():
    out = _chat()
    for needle in ("STAGE2", "測試對象", "SIT", "IMP", "CK", "UM",
                   "【💬 當前對話環境】", "【潛意識記憶】", "【當前情境與認知】",
                   "pe.play_virtual_piano", "自稱"):
        assert needle in out, needle
    for tag in ("[SYSTEM ROOT]", "[RUNTIME STATE]", "[TASK]"):
        assert tag in out, tag
    assert out.index("[SYSTEM ROOT]") < out.index("[TASK]")


def test_chat_empty_sections_dropped():
    out = _chat(cloud_knowledge_prompt="", unified_memory_prompt="",
                stage2_instructions="", live_audio_emotion_prompt="")
    assert "[SENSORY]" not in out  # UM 空 → 感官塊省略
    assert "[SYSTEM ROOT]" in out and "[TASK]" in out


def test_hard_rules_and_fewshots_from_files():
    assert "受話對象" in pte.hard_rules("vtuber")
    assert "一對一" in pte.hard_rules("companion")
    assert len(pte.few_shot_examples()) == 5


def test_proactive_keeps_content():
    out = pte.build_proactive_system_prompt("測試爸", tiktok_telemetry="TT",
                                            realtime_summary="RT", thoughts_summary="TH",
                                            cloud_knowledge_prompt="CK",
                                            unified_memory_prompt="UM")
    for needle in ("TT", "RT", "TH", "CK", "UM", "SILENCE", "[SYSTEM ROOT]", "[TASK]"):
        assert needle in out, needle
