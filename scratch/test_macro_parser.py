import os
import sys
import re
import time

class MacroParser:
    @staticmethod
    def parse_macro(script_text: str):
        """
        Parses a XMBC-style macro script string into a list of executable action dicts.
        Supported tags:
        - {MOVETO: X, Y} or {MOVE: X, Y}
        - {LOCK} / {UNLOCK}
        - {LMB} / {LMB_HOLD: ms} / {LDOWN} / {LUP}
        - {RMB} / {RMB_HOLD: ms} / {RDOWN} / {RUP}
        - {MMB} / {MMB_HOLD: ms} / {MDOWN} / {MUP}
        - {MB4} / {MB4_HOLD: ms} / {MB4_DOWN} / {MB4_UP} / {X1}
        - {MB5} / {MB5_HOLD: ms} / {MB5_DOWN} / {MB5_UP} / {X2}
        - {WAIT: ms} / {SLEEP: ms} / {DELAY: ms}
        - {KEY: key} / {PRESS: key}
        - {KEYDOWN: key} / {KEYUP: key}
        - {KEY_HOLD: key, ms}
        - {TEXT: content}
        """
        actions = []
        # Remove comments (// or #)
        clean_lines = []
        for line in script_text.splitlines():
            line_str = line.strip()
            if line_str.startswith("//") or line_str.startswith("#"):
                continue
            # Remove inline comments
            line_str = re.sub(r'(//|#).*$', '', line_str).strip()
            if line_str:
                clean_lines.append(line_str)
        
        full_text = " ".join(clean_lines)
        
        # Regex to find all {TAG...} or {TAG: ARG}
        tag_pattern = re.compile(r'\{([A-Za-z0-9_]+)(?:\s*:\s*([^}]+))?\}')
        
        matches = tag_pattern.findall(full_text)
        for tag, arg in matches:
            tag = tag.upper().strip()
            arg = arg.strip() if arg else ""
            
            if tag in ["MOVETO", "MOVE", "POS"]:
                parts = [p.strip() for p in arg.split(",")]
                if len(parts) >= 2:
                    actions.append({"type": "move", "x": int(parts[0]), "y": int(parts[1])})
            elif tag == "LOCK":
                actions.append({"type": "lock"})
            elif tag == "UNLOCK":
                actions.append({"type": "unlock"})
            elif tag in ["LMB", "LCLICK", "LEFT"]:
                actions.append({"type": "click", "button": "left", "hold_ms": 50})
            elif tag in ["LMB_HOLD", "LCLICK_HOLD", "LEFT_HOLD"]:
                ms = int(arg) if arg else 100
                actions.append({"type": "click", "button": "left", "hold_ms": ms})
            elif tag in ["LDOWN", "LEFT_DOWN"]:
                actions.append({"type": "mouse_down", "button": "left"})
            elif tag in ["LUP", "LEFT_UP"]:
                actions.append({"type": "mouse_up", "button": "left"})
            elif tag in ["RMB", "RCLICK", "RIGHT"]:
                actions.append({"type": "click", "button": "right", "hold_ms": 50})
            elif tag in ["RMB_HOLD", "RCLICK_HOLD", "RIGHT_HOLD"]:
                ms = int(arg) if arg else 100
                actions.append({"type": "click", "button": "right", "hold_ms": ms})
            elif tag in ["RDOWN", "RIGHT_DOWN"]:
                actions.append({"type": "mouse_down", "button": "right"})
            elif tag in ["RUP", "RIGHT_UP"]:
                actions.append({"type": "mouse_up", "button": "right"})
            elif tag in ["MMB", "MCLICK", "MIDDLE"]:
                actions.append({"type": "click", "button": "middle", "hold_ms": 50})
            elif tag in ["MMB_HOLD", "MIDDLE_HOLD"]:
                ms = int(arg) if arg else 100
                actions.append({"type": "click", "button": "middle", "hold_ms": ms})
            elif tag in ["MDOWN", "MIDDLE_DOWN"]:
                actions.append({"type": "mouse_down", "button": "middle"})
            elif tag in ["MUP", "MIDDLE_UP"]:
                actions.append({"type": "mouse_up", "button": "middle"})
            elif tag in ["MB4", "X1", "SIDE1"]:
                actions.append({"type": "click", "button": "mouse4", "hold_ms": 50})
            elif tag in ["MB4_HOLD", "X1_HOLD", "SIDE1_HOLD"]:
                ms = int(arg) if arg else 100
                actions.append({"type": "click", "button": "mouse4", "hold_ms": ms})
            elif tag in ["MB4_DOWN", "X1_DOWN"]:
                actions.append({"type": "mouse_down", "button": "mouse4"})
            elif tag in ["MB4_UP", "X1_UP"]:
                actions.append({"type": "mouse_up", "button": "mouse4"})
            elif tag in ["MB5", "X2", "SIDE2"]:
                actions.append({"type": "click", "button": "mouse5", "hold_ms": 50})
            elif tag in ["MB5_HOLD", "X2_HOLD", "SIDE2_HOLD"]:
                ms = int(arg) if arg else 100
                actions.append({"type": "click", "button": "mouse5", "hold_ms": ms})
            elif tag in ["MB5_DOWN", "X2_DOWN"]:
                actions.append({"type": "mouse_down", "button": "mouse5"})
            elif tag in ["MB5_UP", "X2_UP"]:
                actions.append({"type": "mouse_up", "button": "mouse5"})
            elif tag in ["WAIT", "SLEEP", "DELAY", "PAUSE"]:
                ms = int(arg) if arg else 100
                actions.append({"type": "wait", "ms": ms})
            elif tag in ["KEY", "PRESS"]:
                actions.append({"type": "key_press", "key": arg})
            elif tag in ["KEYDOWN", "KEY_DOWN"]:
                actions.append({"type": "key_down", "key": arg})
            elif tag in ["KEYUP", "KEY_UP"]:
                actions.append({"type": "key_up", "key": arg})
            elif tag == "KEY_HOLD":
                parts = [p.strip() for p in arg.split(",")]
                k = parts[0]
                ms = int(parts[1]) if len(parts) > 1 else 100
                actions.append({"type": "key_hold", "key": k, "ms": ms})
            elif tag == "TEXT":
                actions.append({"type": "text", "content": arg})
                
        return actions

if __name__ == "__main__":
    sample = """
    // 測試巨集
    {MOVETO: 960, 540}
    {LOCK}
    {LMB_HOLD: 100}
    {UNLOCK}
    {WAIT: 50}
    {MOVETO: 1000, 600}
    {MB4_HOLD: 150}
    {KEY: space}
    """
    acts = MacroParser.parse_macro(sample)
    print("Parsed actions count:", len(acts))
    for a in acts:
        print(" ->", a)
    assert len(acts) == 8
    print("[OK] Macro Parser Test Passed!")
