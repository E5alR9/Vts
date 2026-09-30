# -*- coding: utf-8 -*-
"""
🎛️ Live Coding 外部橋接（PROVIDER: EXTERNAL；見 docs/AI_SOURCES.md）。

後端（LIVECODE_BACKEND）：
  mini     內建引擎＋SoundFont（零依賴，預設；services/livecode.py）
  foxdot   FoxDot（需 scripts/install_livecoding.ps1；自帶 scsynth）
  sonicpi  Sonic Pi（需開著 Sonic Pi App；本機 OSC 送碼，無需 Ruby）

缺件時一律拋清楚錯（點名安裝腳本），由調用端決定是否退回 mini。
"""
import os
import socket
import struct
import subprocess
import threading

from core.utils import log_print


def backend() -> str:
    return (os.getenv("LIVECODE_BACKEND") or "mini").strip().lower()


def sonic_host() -> str:
    return (os.getenv("SONICPI_HOST") or "127.0.0.1").strip()


def sonic_port() -> int:
    try:
        return int(os.getenv("SONICPI_PORT") or "4557")
    except Exception:
        return 4557


# ── 最小 OSC 編碼器（只夠 /run-code：string args；免 python-osc） ──
def _osc_str(s: str) -> bytes:
    b = s.encode("utf-8") + b"\x00"
    return b + b"\x00" * ((4 - len(b) % 4) % 4)


def osc_message(address: str, args: list) -> bytes:
    """編碼 OSC 封包（目前只支援 string 參數；夠 Sonic Pi 用）。"""
    for a in args:
        if not isinstance(a, str):
            raise TypeError("本編碼器只支援 string 參數")
    return _osc_str(address) + _osc_str("," + "s" * len(args)) + b"".join(_osc_str(a) for a in args)


class SonicPiBridge:
    """Sonic Pi OSC 橋：run(code)/stop_all。需 Sonic Pi 開著並啟用 OSC（預設開）。"""

    def __init__(self, host: str = "", port: int = 0, job_id: str = "SEVEN_LIVE"):
        self.host = host or sonic_host()
        self.port = port or sonic_port()
        self.job_id = job_id

    def _send(self, address: str, args: list):
        data = osc_message(address, args)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.sendto(data, (self.host, self.port))
        finally:
            s.close()

    def run(self, code: str):
        self._send("/run-code", [self.job_id, code])

    def stop_all(self):
        try:
            self._send("/stop-all-jobs", [])
        except Exception:
            pass


class FoxDotBridge:
    """FoxDot 橋：常駐子行程吃 code 行（自帶 scsynth；需 pip FoxDot）。"""

    def __init__(self):
        self.proc = None
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if self.proc and self.proc.poll() is None:
                return
            try:
                __import__("FoxDot")
            except ImportError:
                raise RuntimeError("缺 FoxDot：跑 scripts/install_livecoding.ps1")
            self.proc = subprocess.Popen(
                ["python", "-u", "-c", "from FoxDot import *\n"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                text=True)
            log_print("🦊 [FoxDot] 橋接子行程已啟動（scsynth 由 FoxDot 自帶）")

    def exec_code(self, code: str):
        self.start()
        with self._lock:
            try:
                self.proc.stdin.write(code if code.endswith("\n") else code + "\n")
                self.proc.stdin.flush()
            except Exception as e:
                raise RuntimeError(f"FoxDot 送碼失敗: {e}")

    def stop_all(self):
        with self._lock:
            if self.proc and self.proc.poll() is None:
                try:
                    self.proc.stdin.write("Clock.clear()\n")
                    self.proc.stdin.flush()
                except Exception:
                    pass

    def close(self):
        with self._lock:
            if self.proc and self.proc.poll() is None:
                try:
                    self.proc.terminate()
                except Exception:
                    pass
            self.proc = None


_FOX = FoxDotBridge()


def play_backend(which: str, name: str, code: str, bars: int = 4) -> str:
    """依後端演奏，回說明字串；缺件拋錯（調用端退回 mini）。"""
    from services import livecode as lc
    which = (which or "mini").strip().lower()
    if which == "foxdot":
        _FOX.exec_code(lc.to_foxdot(lc.parse_code(code)))
        return f"FoxDot 演奏中（loop {name}，換曲熱更新）"
    if which == "sonicpi":
        SonicPiBridge().run(lc.to_sonicpi(lc.parse_code(code), name))
        return f"Sonic Pi 演奏中（live_loop {name}；App 需開著）"
    from services.livecode import live, live_sink
    live(name, code, sink=live_sink(), bars=max(1, min(16, int(bars or 4))))
    return f"內建引擎演奏中（loop {name}）"


def stop_backend(which: str, name: str):
    which = (which or "mini").strip().lower()
    if which == "foxdot":
        _FOX.stop_all()
        return
    if which == "sonicpi":
        SonicPiBridge().stop_all()
        return
    from services import livecode as lc
    if name:
        lc.stop(name)
    else:
        lc.stop_all()
