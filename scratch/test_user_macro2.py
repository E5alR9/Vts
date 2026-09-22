import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auto_clicker_tool

def test_script():
    script = """
    {lock}
    {CLICK_POS: 1244, 722, 300}
    {MOVETO: 2474, 1598}
    {LMB}
    {LMB}
    {unlock}
    """
    actions = auto_clicker_tool.MacroParser.parse(script)
    print("Parsed actions count:", len(actions))
    for idx, a in enumerate(actions, 1):
        print(f"Step {idx}: {a}")
    
    assert len(actions) == 6
    assert actions[0]["type"] == "lock"
    assert actions[1]["type"] == "click_pos" and actions[1]["x"] == 1244 and actions[1]["y"] == 722 and actions[1]["hold_ms"] == 300
    assert actions[2]["type"] == "move" and actions[2]["x"] == 2474 and actions[2]["y"] == 1598
    assert actions[3]["type"] == "click" and actions[3]["button"] == "left"
    assert actions[4]["type"] == "click" and actions[4]["button"] == "left"
    assert actions[5]["type"] == "unlock"
    print("\n[OK] Script parsed 100% perfectly!")

if __name__ == "__main__":
    test_script()
