import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auto_clicker_tool

def test_user_exact_script():
    user_script = """
    {TAB}
    {MOVETO: 1244, 722}
    {LOCK}
    {LMB_HOLD: 300}
    {UNLOCK}
    {TAB}
    """
    actions = auto_clicker_tool.MacroParser.parse(user_script)
    print("Parsed user actions:")
    for idx, act in enumerate(actions, 1):
        print(f"  Step {idx}: {act}")
    
    assert len(actions) == 6
    assert actions[0] == {"type": "key_press", "key": "tab"}
    assert actions[1] == {"type": "move", "x": 1244, "y": 722}
    assert actions[2] == {"type": "lock"}
    assert actions[3] == {"type": "click", "button": "left", "hold_ms": 300}
    assert actions[4] == {"type": "unlock"}
    assert actions[5] == {"type": "key_press", "key": "tab"}
    print("\n[OK] User macro parsed 100% perfectly!")

if __name__ == "__main__":
    test_user_exact_script()
