import ctypes
import time

WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

import ctypes.wintypes

ctypes.windll.user32.WindowFromPoint.argtypes = [POINT]
ctypes.windll.user32.WindowFromPoint.restype = ctypes.wintypes.HWND

def background_click(x: int, y: int, hold_ms: int = 100):
    """Sends mouse down and up messages directly to the window at (x, y) without moving the cursor."""
    # Method A: Get foreground window (the active game window)
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    if not hwnd:
        return False
    
    # Convert screen coords to client coords
    client_pt = POINT(x, y)
    ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(client_pt))
    
    lparam = (client_pt.y << 16) | (client_pt.x & 0xFFFF)
    print(f"Target Foreground HWND: {hwnd}, Client coords: ({client_pt.x}, {client_pt.y})")
    
    ctypes.windll.user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lparam)
    time.sleep(0.005)
    ctypes.windll.user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
    time.sleep(hold_ms / 1000.0)
    ctypes.windll.user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lparam)
    return True

if __name__ == "__main__":
    print("Testing background click at (100, 100)...")
    res = background_click(100, 100, 50)
    print("Result:", res)
