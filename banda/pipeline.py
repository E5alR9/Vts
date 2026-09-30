# -*- coding: utf-8 -*-
"""
🧵 banda.pipeline — 一鍵扒帶管線。

輸入 YouTube URL/ID 或本地音檔 →
  1. demucs htdemucs_6s 分離（已有 stem 則跳過）
  2. 各軌轉譜（transcribe.py）
  3. 節拍網格量化（quantize.py）
  4. 多軌 MIDI 寫出（midi_out.py）
  5. SoundFont 重演奏 WAV（render.py）
  6. 客觀驗證 + JSON 報告（verify.py）
回傳 dict 全產物路徑與指標。
"""
import os
import json
import numpy as np

from core.utils import log_print

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_DIR = os.path.join(ROOT, "data", "stem_pack")
OUT_DIR = os.path.join(ROOT, "banda", "out")
STEMS_6 = ["vocals", "drums", "bass", "guitar", "piano", "other"]
_AUDIO_EXTS = [".m4a", ".mp3", ".wav", ".flac", ".ogg", ".opus", ".wma", ".aac", ".aiff", ".aif", ".webm"]


def _find_source(pack: str) -> str:
    """找工作區內已複製的 source.<ext>（任意格式）。"""
    for e in _AUDIO_EXTS:
        p = os.path.join(pack, f"source{e}")
        if os.path.exists(p):
            return p
    return ""


def _is_audio_file(p: str) -> bool:
    return os.path.isfile(p) and os.path.splitext(p)[1].lower() in _AUDIO_EXTS


def _resolve_local_path(p: str) -> str:
    """寬鬆解析本地路徑：手打檔名常拿不到 NBSP(\xa0)/全形空白/NFD。
    目錄存在時，掃目錄做正規化比對（NFC＋NBSP/全形空白→普通空白，不分大小寫）。"""
    if os.path.isfile(p):
        return p
    import unicodedata
    d = os.path.dirname(p) or "."
    if not os.path.isdir(d):
        return p
    def norm(s: str) -> str:
        s = unicodedata.normalize("NFC", s)
        for ch in ("\xa0", "\u3000", "\u2007", "\u202f"):
            s = s.replace(ch, " ")
        return s.lower()
    target = norm(os.path.basename(p))
    for f in os.listdir(d):
        if norm(f) == target:
            return os.path.join(d, f)
    return p


def ingest_local(src_path: str, title: str = "") -> str:
    """本地音檔「唯讀複製」進工作區 data/stem_pack/<vid>/source.<ext>。
    原檔（含 playlist-admin 資料夾）絕不寫入/移動/改名。回 vid。"""
    import shutil
    from banda.midi_out import _safe
    src = os.path.abspath(src_path)
    if not os.path.isfile(src):
        raise FileNotFoundError(src)
    stem = (title or os.path.splitext(os.path.basename(src))[0]).strip()
    vid = _safe(stem).rstrip(". ") or "local_song"
    pack = os.path.join(PACK_DIR, vid)
    os.makedirs(pack, exist_ok=True)
    dst = os.path.join(pack, "source" + os.path.splitext(src)[1].lower())
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        log_print(f"📂 [banda] 本地檔唯讀複製 -> data/stem_pack/{vid}/source{os.path.splitext(src)[1].lower()}")
        shutil.copy2(src, dst)
    return vid


def download_audio(vid_or_url: str) -> str:
    """YT → m4a（android/ios 客戶端繞 403）。"""
    from services.video_watch import normalize_video_url
    vid = normalize_video_url(vid_or_url)
    if not vid:
        return ""
    out = os.path.join(PACK_DIR, vid, "source.%(ext)s")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    import subprocess
    import sys
    cmd = [sys.executable, "-m", "yt_dlp", "--extractor-args", "youtube:player_client=android,ios",
           "-x", "--audio-format", "m4a", "--no-playlist", "-o", out,
           f"https://www.youtube.com/watch?v={vid}"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=600)
        d = os.path.dirname(out)
        for f in sorted(os.listdir(d)):
            if f.startswith("source.") and f.endswith((".m4a", ".mp3", ".opus", ".webm")):
                return os.path.join(d, f)
    except Exception as e:
        log_print(f"⚠️ [banda] 下載失敗: {e}")
    return ""


def separate_six(audio_path: str, vid: str, force: bool = False) -> dict:
    """demucs 6 軌 → {stem: wav}。已有成品可跳過。"""
    import subprocess
    import sys
    import shutil
    out = os.path.join(PACK_DIR, vid)
    have = {s: os.path.join(out, f"{s}.wav") for s in STEMS_6}
    if not force and all(os.path.exists(p) for p in have.values()):
        log_print("🎸 [banda] 分軌已存在，跳過分離")
        return have
    cmd = [sys.executable, "-m", "demucs", "-n", "htdemucs_6s", "-o", out, audio_path]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=2400)
    base = os.path.splitext(os.path.basename(audio_path))[0]
    got = {}
    for s in STEMS_6:
        cand = os.path.join(out, "htdemucs_6s", base, f"{s}.wav")
        if os.path.exists(cand):
            shutil.move(cand, have[s])
            got[s] = have[s]
    return got


def dig_song(url_or_id: str, title: str = "", force_separate: bool = False,
             quantize: bool = True) -> dict:
    """一鍵扒帶主入口。回 {ok, vid, midi, wav, report, metrics}。"""
    from services.video_watch import normalize_video_url
    from banda import analyze, transcribe, quantize as qz, midi_out, render, verify

    looks_local = ("/" in url_or_id or "\\" in url_or_id or
                   os.path.splitext(url_or_id)[1].lower() in _AUDIO_EXTS)
    cand = _resolve_local_path(url_or_id) if looks_local else ""
    if _is_audio_file(cand):
        vid = ingest_local(cand, title)  # 本地音檔：複製進工作區，原檔不動
    else:
        vid = normalize_video_url(url_or_id)
    if not vid:
        return {"ok": False, "error": "無效的 YouTube 網址/ID 或本地音檔路徑"}
    pack = os.path.join(PACK_DIR, vid)
    os.makedirs(pack, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1) 音源（已有 stems 就不用重下載）
    stems = {s: os.path.join(pack, f"{s}.wav") for s in STEMS_6}
    if not all(os.path.exists(p) for p in stems.values()):
        audio = _find_source(pack)
        if not audio:
            audio = download_audio(vid)
        if not audio:
            return {"ok": False, "error": "下載失敗／找不到音源"}
        log_print(f"🎸 [banda] {vid} 分離 6 軌中…")
        stems = separate_six(audio, vid, force=force_separate)
        if not stems:
            return {"ok": False, "error": "demucs 分離失敗"}

    # 2) 全曲分析
    # 參考音源：優先「全分軌總和」（與渲染音軌集合完全一致，排除聲效/MV 干擾）；
    # 退而求其次用 source.m4a 原檔。
    import soundfile as _sf
    import librosa as _lr
    ref_audio = os.path.join(pack, "_fullmix_ref_22k.wav")
    if not os.path.exists(ref_audio):
        src = _find_source(pack)
        if not src:
            src = next((p for p in stems.values() if os.path.exists(p)), None)
        if src is None:
            return {"ok": False, "error": "找不到音源"}
        ys, srs = [], set()
        for s in STEMS_6:
            p = stems.get(s)
            if p and os.path.exists(p):
                y, srr = _lr.load(p, sr=22050, mono=True)
                ys.append(y)
                srs.add(srr)
        if not ys:
            return {"ok": False, "error": "分軌不存在"}
        nn = min(len(y) for y in ys)
        fullmix = sum(y[:nn] for y in ys)
        peak = float(np.max(np.abs(fullmix)))
        if peak > 0:
            fullmix = fullmix / peak * 0.9
        _sf.write(ref_audio, fullmix.astype(np.float32), 22050)
    log_print(f"   參考音源: {os.path.basename(ref_audio)}")
    log_print("🎵 [banda] 分析 BPM/拍格/調性/和弦…")
    bpm, beats, downs = analyze.estimate_bpm(ref_audio)
    keyinfo = analyze.estimate_key(ref_audio)
    chords = analyze.detect_chords(ref_audio, seg_sec=2.0)
    log_print(f"   BPM={bpm:.1f}  key={keyinfo['key']} {keyinfo['scale']}  chords={len(chords)}")

    # 3) 轉譜
    log_print("🎼 [banda] 分軌轉譜…")
    raw_tracks = transcribe.transcribe_song(stems)

    # 4) 清洗 + 量化 + 去重（輸出真實秒數，量化吸附）
    from banda import clean as bz
    grid_info = qz.build_grid(beats)
    q_tracks = {}
    for key, notes in raw_tracks.items():
        if key == "drums":
            q_tracks[key] = notes  # 鼓 onset 已是秒，直接用
            continue
        ns = bz.clean_track(qz.dedupe_overlap(notes), key)
        q_tracks[key] = qz.quantize_notes(ns, grid_info,
                                          swing_free=(key == "vocals"))
    chords_q = qz.chords_to_grid(chords, grid_info)

    # 5) MIDI（tempo map 保留 groove）
    safe_title = title or vid
    from banda.midi_out import _safe
    midi_path = os.path.join(OUT_DIR, f"{_safe(safe_title)}.mid")
    midi_out.write_multitrack_midi(midi_path, q_tracks, bpm,
                                   beat_times=beats, chords=chords_q)

    # 6) 重演奏 + 驗證（分軌驗證 + 混音驗證兩層）
    wav_path = os.path.join(OUT_DIR, f"{_safe(safe_title)}_render.wav")
    render.render_midi(midi_path, wav_path, bpm)

    track_metrics = verify.verify_tracks(midi_path, pack)
    mix_metrics = verify.verify_mix(ref_audio, wav_path, ref_has_vocals=False)
    coverage = {k: {"n_notes": len(v),
                    "snapped": sum(1 for n in v if n.get("unit") == "grid"),
                    "snap_rate": round(sum(1 for n in v if n.get("unit") == "grid") / max(1, len(v)), 3)}
                for k, v in q_tracks.items()}
    metrics = mix_metrics
    report = {"vid": vid, "title": safe_title, "bpm": bpm,
              "key": keyinfo, "chords": chords_q,
              "n_notes": {k: len(v) for k, v in raw_tracks.items()},
              "coverage": coverage,
              "track_verification": track_metrics,
              "metrics": metrics,
              "artifacts": {"midi": midi_path, "render_wav": wav_path}}
    rp = os.path.join(OUT_DIR, f"{_safe(safe_title)}_report.json")
    verify.save_report(rp, report)
    log_print(f"🧾 [banda] 報告: {rp}")
    log_print(f"   mix: chroma={metrics['chroma_cosine']} onset_f1={metrics['onset_f1']} "
              f"grade={metrics['grade']}")
    log_print(f"   tracks avg chroma: {track_metrics.get('avg')}")
    report["report_path"] = rp
    report["ok"] = True
    return report


def verify_only(midi_or_wav: str, ref_path: str, bpm: float = None) -> dict:
    """只跑驗證（已扒好的成品 vs 任何參考音源）。"""
    from banda import render, verify
    src = midi_or_wav
    if src.lower().endswith(".mid"):
        bpm = bpm or 100.0
        wav = src.replace(".mid", "_render.wav")
        render.render_midi(src, wav, bpm)
        src = wav
    return verify.verify_render(ref_path, src)
