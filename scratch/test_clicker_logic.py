import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import auto_clicker_tool

def test_macro_parsing_and_execution():
    script = """
    {LOCK}
    {LMB_HOLD: 50}
    {UNLOCK}
    {WAIT: 30}
    {MB4_HOLD: 40}
    """
    actions = auto_clicker_tool.MacroParser.parse(script)
    print("Parsed actions count:", len(actions))
    assert len(actions) == 5
    assert actions[0]["type"] == "lock"
    assert actions[1]["type"] == "click" and actions[1]["button"] == "left" and actions[1]["hold_ms"] == 50
    assert actions[2]["type"] == "unlock"
    assert actions[3]["type"] == "wait" and actions[3]["ms"] == 30
    assert actions[4]["type"] == "click" and actions[4]["button"] == "mouse4" and actions[4]["hold_ms"] == 40
    print("[OK] MacroParser parsing test passed!")

    # Test MacroWorker action execution
    worker = auto_clicker_tool.MacroWorker()
    t0 = time.perf_counter()
    worker._execute_actions(actions)
    t1 = time.perf_counter()
    duration_ms = (t1 - t0) * 1000
    print(f"Executed macro script, elapsed time: {duration_ms:.2f} ms")
    assert duration_ms >= 100
    print("[OK] Macro execution test passed!")

def test_config_persistence():
    cfg = auto_clicker_tool.load_config()
    assert "macro_script" in cfg
    assert "{MOVETO:" in cfg["macro_script"]
    print("[OK] Macro config persistence test passed!")

if __name__ == "__main__":
    test_macro_parsing_and_execution()
    test_config_persistence()
    print("\nALL XMBC MACRO TESTS PASSED SUCCESSFULLY!")
