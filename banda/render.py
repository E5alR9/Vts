# -*- coding: utf-8 -*-
"""
🔊 banda.render — MIDI → WAV 重演奏（SoundFont）。

對標原曲的混音處方（依 gemini_mix_verdict.txt 教訓）：
  打擊樂 attack 1ms / release 5ms；其他 attack 8ms / release 60ms
  總線 soft limiter -1 dBFS（不靠 peak normalize 撐）
  每軌增益配平 → 立體聲 Haas 5ms → 溫和膠水壓縮
"""
import os
import shutil
import subprocess
import numpy as np

DEFAULT_SF2 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "soundfonts", "FluidR3_GM_GS.sf2")

FSYNTH_EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "tools", "fluidsynth", "fluidsynth-v2.6.1-win10-x64-cpp11",
                          "bin", "fluidsynth.exe")


def fsynth_available() -> bool:
    return os.path.exists(FSYNTH_EXE)


def renderer() -> str:
    """fsynth（真 FluidSynth 2.6，二進位 vendor）優先；缺席退回內建手寫渲染。"""
    want = (os.getenv("BANDA_RENDERER") or "auto").strip().lower()
    if want == "internal":
        return "internal"
    if want == "fsynth" or (want == "auto" and fsynth_available()):
        return "fsynth" if fsynth_available() else "internal"
    return "internal"


def render_midi_fsynth(midi_path: str, out_wav: str, sf2: str = None,
                       sr: int = 44100) -> str:
    """真 FluidSynth 渲染（modulator／濾波／合唱殘響全支援；無頭 CLI）。"""
    if not fsynth_available():
        raise RuntimeError("缺 fluidsynth binary（tools/fluidsynth）")
    os.makedirs(os.path.dirname(os.path.abspath(out_wav)), exist_ok=True)
    cmd = [FSYNTH_EXE, "-ni", "-r", str(sr), "-F", out_wav,
           sf2 or DEFAULT_SF2, midi_path]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if p.returncode != 0 or not os.path.exists(out_wav):
        raise RuntimeError(f"fluidsynth 失敗: {(p.stderr or '')[-200:]}")
    return out_wav


def render_midi(midi_path: str, out_wav: str, bpm: float, sf2: str = None,
                sr: int = 44100) -> str:
    """分派器：fsynth 優先（BANDA_RENDERER=internal 可強制手寫版）。"""
    if renderer() == "fsynth":
        return render_midi_fsynth(midi_path, out_wav, sf2, sr)
    return render_midi_to_wav(midi_path, out_wav, bpm, sf2, sr)

# source_key → (bank, program, gain, pan)
MIX_PLAN = {
    "vocals": (0, 73, 0.85, 0.0),
    "guitar": (0, 30, 0.95, 0.12),
    "piano":  (0, 0, 0.80, -0.10),
    "bass":   (0, 33, 1.00, 0.0),
    "other":  (0, 48, 0.70, -0.15),
    "drums":  (128, 0, 0.90, 0.0),
    "chords": (0, 4, 0.0, 0.0),  # 和弦參考軌：僅供閱譜，渲染靜音（非原曲編制）
}


def render_midi_to_wav(midi_path: str, out_wav: str, bpm: float, sf2: str = None,
                       sr: int = 44100) -> str:
    import numpy as np
    import soundfile as sf
    from services.soundfont import SoundFontBank
    from banda.midi_out import load_track_notes

    bank = SoundFontBank(sf2 or DEFAULT_SF2)
    all_notes = load_track_notes(midi_path)  # tempo map 正確換算秒
    total = 0.0
    for name, notes in all_notes.items():
        if notes:
            total = max(total, max(s + d for s, _, _, d in notes))
    total += 3.0
    L = np.zeros(int(sr * total) + 8, dtype=np.float64)
    R = np.zeros(int(sr * total) + 8, dtype=np.float64)

    for name, notes in all_notes.items():
        key = next((k for k in MIX_PLAN if k.capitalize() == name), None)
        if key is None or not notes:
            continue
        bk, prog, gain, pan = MIX_PLAN[key]
        is_drum = (bk == 128)
        atk, rel = (1.0, 5.0) if is_drum else (8.0, 60.0)
        gl = 0.5 * (1.0 - pan)
        gr = 0.5 * (1.0 + pan)
        for s, midi, vel, dur in notes:
            if s < 0:
                continue
            d = min(dur + 0.12, 4.0)
            w = bank.render_note(bk, prog, midi, vel, d, sr, attack_ms=atk, release_ms=rel)
            i = max(0, int(s * sr))
            end = min(len(L), i + len(w))
            if i < len(L):
                L[i:end] += w[:end - i] * gain * gl
                R[i:end] += w[:end - i] * gain * gr

    mix = np.column_stack((L, R))
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = mix / peak * 0.5  # 留 headroom
    # 軟限制器 -1 dBFS
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix *= 10.0 ** (-1.0 / 20.0)
    os.makedirs(os.path.dirname(os.path.abspath(out_wav)), exist_ok=True)
    sf.write(out_wav, mix.astype(np.float32), sr)
    return out_wav
