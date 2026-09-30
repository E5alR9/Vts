# -*- coding: utf-8 -*-
"""
🎛️ Live Coding 引擎（零額外軟體：pattern 解析＋SoundFont 渲染＋async 熱更新）。

迷你語言（AI 寫、觀眾看得到）：
    bpm 100
    drums bd:x-x- sn:--x- hh:xxxx oh:---- 
    bass  key=Am  deg=1 . 5 4 | vel=90 90 70 80
    stab  chord=Am7 rhythm=x---x--- prog=41
    lead  notes=69,71,72,74 rhythm=x-x-x-x- prog=81

語法：
- drums 行：`名:格子`，格子字元 x=打 .=休；名可為 bd/sn/hh/oh/tom/clap/crash（鼓組映射）
- euclid(h,k)：歐幾里得節奏，如 hh:euclid(5,8)
- deg：級數（1-7，可負/超八度），key 支援 Am/C/G/D/Em 等大小調
- chord：Am7/G/C/Dm 等常用和弦名；rhythm 同鼓格
- notes：MIDI 直寫；prog：GM 音色號
- 行首 # 為註解；同名 loop 熱更新（重調用同名即換曲不中斷）

執行：async scheduler 按 16 分音符步進；sink 可為即時播放（pygame）或離線 numpy。
"""
import asyncio
import math
import re
import time

STEP = 16  # 16 分音符網格

DRUM_NOTES = {"bd": 36, "sn": 38, "hh": 42, "oh": 46, "tom": 45,
              "clap": 39, "crash": 49, "ride": 51}

KEYS = {
    "C": ([0, 2, 4, 5, 7, 9, 11], 60), "G": ([7, 9, 11, 0, 2, 4, 6], 67),
    "D": ([2, 4, 6, 7, 9, 11, 1], 62), "A": ([9, 11, 1, 2, 4, 6, 8], 69),
    "E": ([4, 6, 8, 9, 11, 1, 3], 64), "F": ([5, 7, 9, 10, 0, 2, 4], 65),
    "Am": ([9, 11, 0, 2, 4, 5, 7], 57), "Em": ([4, 5, 7, 9, 11, 0, 2], 52),
    "Dm": ([2, 3, 5, 7, 9, 10, 0], 50), "Bm": ([11, 0, 2, 4, 6, 7, 9], 59),
}

CHORDS = {
    "C": [60, 64, 67], "G": [55, 59, 62], "D": [54, 57, 62], "A": [57, 61, 64],
    "E": [52, 56, 59], "F": [53, 57, 60], "Am": [57, 60, 64], "Em": [52, 55, 59],
    "Dm": [50, 53, 57], "Bm": [47, 50, 54], "Am7": [57, 60, 64, 67],
    "G7": [55, 59, 62, 65], "Cmaj7": [60, 64, 67, 71], "Fmaj7": [53, 57, 60, 64],
}


def euclid(hits: int, steps: int) -> str:
    """歐幾里得節奏 → 'x..' 字串（Bresenham 均分，euclid(3,8)='x..x..x.'）。"""
    hits, steps = max(0, int(hits)), max(1, int(steps))
    if hits <= 0:
        return "." * steps
    if hits >= steps:
        return "x" * steps
    return "".join("x" if (i * hits) % steps < hits else "." for i in range(steps))


def parse_grid(spec: str):
    """格子規格 → [0/1]（支援 euclid(h,k)）。"""
    spec = spec.strip()
    m = re.fullmatch(r"euclid\((\d+)\s*,\s*(\d+)\)", spec)
    if m:
        spec = euclid(int(m.group(1)), int(m.group(2)))
    return [1 if c in "xX" else 0 for c in spec if c in "xX."]


def deg_to_midi(key: str, deg: int) -> int:
    """級數 → MIDI（1=主音；8=高八度主音；0/負數往下數；步進累加，八度天然正確）。"""
    scale, root = KEYS.get(key, KEYS["Am"])
    acc, pos, s = 0, 0, int(deg) - 1
    while s > 0:
        acc += (scale[(pos + 1) % 7] - scale[pos]) % 12
        pos = (pos + 1) % 7
        s -= 1
    while s < 0:
        prev = (pos - 1) % 7
        acc -= (scale[pos] - scale[prev]) % 12
        pos = prev
        s += 1
    return root + acc


def parse_code(code: str) -> dict:
    """整段 code → {bpm, tracks:[{kind,name,grid,notes,prog,vel,key}]}。"""
    bpm, tracks = 100, []
    for raw in (code or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"bpm\s+(\d+)", line)
        if m:
            bpm = max(40, min(240, int(m.group(1))))
            continue
        parts = line.split(None, 1)
        head = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        if head == "drums":
            for part in rest.split():
                nm, _, spec = part.partition(":")
                nm = nm.strip()
                if nm in DRUM_NOTES and spec:
                    gridstr = "".join("x" if c in "xX" else "-" for c in spec.strip()
                                     if c in "xX.-")
                    tracks.append({"kind": "drum", "name": nm, "grid": parse_grid(spec),
                                   "note": DRUM_NOTES[nm], "vel": 95, "_gridstr": gridstr})
            continue
        if head in ("bass", "lead", "stab"):
            kv = dict(re.findall(r"(\w+)\s*=\s*([^=\s]+(?:\s+[^=\s]+)*?)(?=\s+\w+\s*=|$)", rest))
            grid = parse_grid(kv.get("rhythm", ""))
            prog = int(kv.get("prog", 33 if head == "bass" else (0 if head == "stab" else 81)))
            vel = [int(v) for v in kv.get("vel", "").split()] or [90]
            if head == "bass":
                key = kv.get("key", "Am")
                degs = [int(d) for d in re.findall(r"-?\d+", kv.get("deg", "1"))]
                notes = [deg_to_midi(key, d) for d in degs] or [57]
                tracks.append({"kind": "notes", "name": "bass", "grid": grid, "notes": notes,
                               "prog": prog, "vel": vel, "_degs": degs or [1]})
            elif head == "stab":
                chord = CHORDS.get(kv.get("chord", "Am"), CHORDS["Am"])
                tracks.append({"kind": "chord", "name": "stab", "grid": grid, "notes": chord,
                               "prog": prog, "vel": vel})
            else:
                notes = [int(n) for n in re.findall(r"-?\d+", kv.get("notes", ""))] or [69]
                tracks.append({"kind": "notes", "name": "lead", "grid": grid, "notes": notes,
                               "prog": prog, "vel": vel})
            continue
    return {"bpm": bpm, "tracks": tracks}


def expand(parsed: dict, bars: int = 4):
    """展開成事件 [(sec, kind, payload)]（可測、無副作用；render/play 共用）。"""
    beat = 60.0 / parsed["bpm"]
    step_dur = beat / 4
    total_steps = STEP * bars
    events = []
    CH = {"drum": 9, "bass": 1, "lead": 0, "stab": 2}
    for tr in parsed["tracks"]:
        grid = tr["grid"] or [1]
        cyc = max(1, len(grid))
        seq = tr.get("notes", [tr.get("note", 36)])
        vv = tr.get("vel", [90])
        vv = vv if isinstance(vv, list) else [vv]
        ch = CH.get(tr["name"] if tr["name"] in CH else tr["kind"], 0)
        if tr["kind"] == "drum":
            ch = 9
        for s in range(total_steps):
            if not grid[s % cyc]:
                continue
            t = s * step_dur
            vel = vv[(s // cyc) % len(vv)] if vv else 90
            if tr["kind"] == "drum":
                events.append((t, "drum", (ch, tr["note"], vel)))
            elif tr["kind"] == "chord":
                for nn in seq:
                    events.append((t, "note", (ch, tr["prog"], nn, vel, step_dur * 3)))
                    events.append((t + step_dur * 3, "off", (ch, nn)))
            else:
                nn = seq[(s // cyc) % len(seq)]
                events.append((t, "note", (ch, tr["prog"], nn, vel, step_dur * 1.8)))
                events.append((t + step_dur * 1.8, "off", (ch, nn)))
    events.sort(key=lambda e: e[0])
    return events, total_steps * step_dur


class LiveLoop:
    """一條可熱更新的 loop（同名重調用即換曲不中斷）。"""
    registry = {}

    def __init__(self, name: str, code: str, sink=None, bars: int = 4):
        self.name = name
        self.sink = sink
        self.bars = bars
        self.task = None
        self.update(code)
        LiveLoop.registry[name] = self

    def update(self, code: str):
        self.parsed = parse_code(code)
        self.events, self.loop_dur = expand(self.parsed, self.bars)

    async def run(self):
        t0 = time.monotonic()
        idx = 0
        while True:
            now = time.monotonic() - t0
            while idx < len(self.events) and self.events[idx][0] <= now:
                _, kind, pay = self.events[idx]
                try:
                    if self.sink:
                        self.sink(kind, pay)
                except Exception:
                    pass
                idx += 1
            if idx >= len(self.events):
                # 循環：用最新解析（熱更新生效點）
                t0 = time.monotonic()
                idx = 0
                await asyncio.sleep(0.005)
                continue
            await asyncio.sleep(0.005)

    def start(self):
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self.run())
        return self

    def stop(self):
        if self.task and not self.task.done():
            self.task.cancel()
        LiveLoop.registry.pop(self.name, None)


def live_sink():
    """即時 sink：走鋼琴引擎 MIDI out（Windows 合成器；惰性 import）。"""
    from services import piano_engine as pe
    pe.init_piano_synthesizer()

    def _sink(kind, pay):
        try:
            if pe.SOUND_ENGINE is None or pe.SOUND_ENGINE.midi_out is None:
                return
            if kind == "drum":
                ch, note, vel = pay
                pe.SOUND_ENGINE.note_on(note, vel, channel=ch)
            elif kind == "note":
                ch, prog, nn, vel, dur = pay
                pe.SOUND_ENGINE.note_on(nn, vel, channel=ch, program=prog)
            elif kind == "off":
                ch, nn = pay
                pe.SOUND_ENGINE.note_off(nn, channel=ch)
        except Exception:
            pass

    return _sink


def render_offline(parsed: dict, bars: int = 2, bank=None, sr: int = 44100):
    """離線渲染 → numpy mono（無音訊裝置也可驗聲）。"""
    import numpy as np
    if bank is None:
        import os as _os
        from services.soundfont import SoundFontBank
        sf2 = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                            "soundfonts", "FluidR3_GM_GS.sf2")
        bank = SoundFontBank(sf2)
    events, total = expand(parsed, bars)
    mix = np.zeros(int(sr * (total + 1.0)) + 8, dtype=np.float64)
    for t, kind, pay in events:
        if kind == "drum":
            ch, note, vel = pay
            w = bank.render_note(128, 0, note, vel, 0.4, sr, attack_ms=1.0, release_ms=5.0)
        elif kind == "note":
            ch, prog, nn, vel, dur = pay
            w = bank.render_note(0, prog, nn, vel, min(dur, 2.0), sr)
        else:
            continue
        idx = int(t * sr)
        end = min(len(mix), idx + len(w))
        if idx < len(mix):
            mix[idx:end] += w[:end - idx]
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix /= peak
    return mix.astype(np.float32), total


def midi_to_foxdot(midi: int):
    """MIDI 音高 → FoxDot (oct, degree)（C 大調級數；best-effort）。"""
    midi = max(0, min(127, int(midi)))
    pcs = [0, 2, 4, 5, 7, 9, 11]
    pc = midi % 12
    deg = min(range(7), key=lambda d: abs(pcs[d] - pc))
    octv = midi // 12 - 1
    return octv, deg


def to_foxdot(parsed: dict) -> str:
    """parsed → FoxDot Python 代碼（best-effort，FoxDot 0.8 API；dry-run 可先貼 IDE 驗）。
    度數直通（bass deg 即 FoxDot 級數），主音 MIDI 轉級數＋oct。"""
    lines = [f"Clock.bpm = {parsed.get('bpm', 100)}", 'Scale.default = "minor"']
    for i, tr in enumerate(parsed.get("tracks", [])):
        tag = f"{tr.get('name', 't')}{i}"
        if tr.get("kind") == "drum":
            lines.append(f'p_{tag} >> play("{tr.get("_gridstr") or "x"}")')
        elif tr.get("name") == "bass":
            degs = tr.get("_degs") or [1]
            lines.append(f'b_{tag} >> bass({degs}, dur=1)')
        elif tr.get("name") == "stab":
            _sg = "".join("x" if g else "-" for g in (tr.get("grid") or [1]))
            lines.append(f'k_{tag} >> keys("{_sg}")')
        else:
            from collections import defaultdict as _dd
            groups = _dd(list)
            for n in (tr.get("notes") or [69]):
                o, d = midi_to_foxdot(n)
                groups[o].append(d)
            for oi, (o, ds) in enumerate(sorted(groups.items())):
                lines.append(f'l_{tag}_{oi} >> pluck({ds}, oct={o})')
    return "\n".join(lines) + "\n"


_SONIC_DRUMS = {"bd": "bd_haus", "sn": "sn_dub", "hh": "hat_tap", "oh": "hat_open",
                "tom": "tom_mid", "clap": "perc_snap", "crash": "cym_crash", "ride": "cym_ride"}


def to_sonicpi(parsed: dict, name: str = "seven") -> str:
    """parsed → Sonic Pi Ruby 代碼（16 步直寫，sleep 0.25；Sonic Pi 4.x）。"""
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", name or "seven") or "seven"
    body = [f"live_loop :{safe} do", f"  use_bpm {parsed.get('bpm', 100)}", "  16.times do |i|"]
    for tr in parsed.get("tracks", []):
        grid = tr.get("grid") or [1]
        cyc = max(1, len(grid))
        hits = [s for s in range(16) if grid[s % cyc]]
        if not hits:
            continue
        cond = " or ".join(f"i == {s}" for s in hits)
        if tr.get("kind") == "drum":
            smp = _SONIC_DRUMS.get(tr.get("name", ""), "perc_bell")
            body.append(f"    sample :{smp} if {cond}")
        elif tr.get("name") == "bass":
            notes = tr.get("_midis") or [45]
            seq = ", ".join(str(n) for n in notes)
            body.append(f"    play [ {seq} ][i % {len(notes)}], release: 0.4 if {cond}")
        elif tr.get("name") == "stab":
            notes = tr.get("notes") or [57, 60, 64]
            seq = ", ".join(str(n) for n in notes)
            body.append(f"    play [{seq}] if {cond}")
        else:
            notes = tr.get("notes") or [69]
            seq = ", ".join(str(n) for n in notes)
            body.append(f"    play [{seq}][i % {len(notes)}] if {cond}")
    body += ["    sleep 0.25", "  end", "end"]
    return "\n".join(body) + "\n"


def live(name: str, code: str, sink=None, bars: int = 4) -> LiveLoop:
    """取用或建立 loop（存在即熱更新代碼並沿用）。"""
    if name in LiveLoop.registry:
        LiveLoop.registry[name].update(code)
        return LiveLoop.registry[name].start()
    return LiveLoop(name, code, sink=sink, bars=bars).start()


def stop(name: str):
    if name in LiveLoop.registry:
        LiveLoop.registry[name].stop()


def stop_all():
    for name in list(LiveLoop.registry):
        stop(name)
