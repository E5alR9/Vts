import os
import sys
import time
import re
import json
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
        sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
    except Exception:
        pass

load_dotenv()

from google import genai
from google.genai import types

# 取得金鑰池
GEMINI_KEYS = [k.strip() for k in re.split(r'[\s,;]+', os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or "") if k.strip() and len(k.strip()) < 150]

print("=" * 105)
print("🚀 【7L 大腦全模型正常聊天思考速度基準測試 (Chat Speed Benchmark)】")
print(f"🔑 偵測到可用 Gemini 金鑰數量: {len(GEMINI_KEYS)} 把")
print("=" * 105)

MODELS_TO_TEST = [
    # 7L 核心 8 階梯模型
    ("gemini-3.1-flash-lite", "⚡ 第 1 梯隊 (極速輕量)"),
    ("gemini-3.5-flash-lite", "🛡️ 第 2 梯隊 (輕量保底)"),
    ("gemini-3-flash-preview", "⚡ 第 3 梯隊 (閃電預覽)"),
    ("gemini-3.1-pro-preview", "🧠 第 4 梯隊 (Pro 預覽)"),
    ("gemini-3.5-flash", "🥈 第 5 梯隊 (主力保底)"),
    ("gemini-3.6-flash", "👑 第 6 梯隊 (高智商主力)"),
    ("gemini-3.7-flash", "👑 第 7 梯隊 (頂配旗艦)"),
    ("gemini-3.8-flash", "🚀 第 8 梯隊 (2026 旗艦)"),
    # 常見相容/備用模型
    ("gemini-2.5-flash", "🌟 常規備用 (2.5 Flash)"),
    ("gemini-2.0-flash", "🌟 常規備用 (2.0 Flash)"),
]

PROMPT = "老爸：今天寫程式有點累，妳在做什麼呢？（請以 7L 親切隨性口吻 1~2 句自然簡短回覆）"

def is_current_thinking_model(m_name: str) -> bool:
    return any(k in m_name for k in ["3.8", "3.7", "2.5", "3-flash", "3.1-pro"])

def test_model_call(model_name: str, thinking_budget, key_idx=0):
    """測試單一模型呼叫並測量耗時與思考表現"""
    last_error = ""
    for k_i in range(min(5, len(GEMINI_KEYS))):
        key = GEMINI_KEYS[(key_idx + k_i) % len(GEMINI_KEYS)]
        client = genai.Client(api_key=key)
        
        cfg_kwargs = {"temperature": 0.85}
        if thinking_budget is not None:
            cfg_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=thinking_budget)
            
        gen_config = types.GenerateContentConfig(**cfg_kwargs)
        
        t0 = time.time()
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=PROMPT,
                config=gen_config
            )
            lat = time.time() - t0
            
            # 解析文字與思考
            text = ""
            thought = ""
            if resp.candidates and resp.candidates[0].content and resp.candidates[0].content.parts:
                for p in resp.candidates[0].content.parts:
                    if getattr(p, 'thought', False) and getattr(p, 'text', ''):
                        thought += p.text + " "
                    elif getattr(p, 'text', '') and not getattr(p, 'thought', False):
                        text += p.text + " "
            if not text.strip() and resp.text:
                text = resp.text.strip()
                
            usage = getattr(resp, 'usage_metadata', None)
            c_tokens = getattr(usage, 'candidates_token_count', 0) if usage else 0
            
            return {
                "status": "SUCCESS",
                "latency": round(lat, 2),
                "text": text.strip().replace("\n", " ")[:60],
                "thought": thought.strip().replace("\n", " ")[:60] if thought else "(無)",
                "tokens": c_tokens,
                "error": None
            }
        except Exception as e:
            err_msg = str(e)
            last_error = err_msg
            if any(x in err_msg for x in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]):
                continue
            elif "404" in err_msg or "NOT_FOUND" in err_msg:
                return {"status": "NOT_FOUND", "latency": round(time.time() - t0, 2), "text": "", "thought": "", "tokens": 0, "error": "404 Model Not Found"}
            else:
                break
                
    return {
        "status": "FAILED",
        "latency": 0.0,
        "text": "",
        "thought": "",
        "tokens": 0,
        "error": last_error[:80] if last_error else "All attempts failed"
    }

print("\n【測試 1】：現行配置模式 (依 vts_7L_test.py 邏輯：指定模型預設 thinking_budget = -1 無限思考)")
print(f"{'模型名稱':<25} | {'模型定位':<20} | {'Thinking設定':<18} | {'耗時(秒)':<9} | {'狀態':<10} | {'回覆摘要'}")
print("-" * 115)

results_current = []
for idx, (m_name, m_tag) in enumerate(MODELS_TO_TEST):
    budget = -1 if is_current_thinking_model(m_name) else None
    b_desc = "Budget = -1 (無限思考)" if budget == -1 else "Default (未限制)"
    res = test_model_call(m_name, budget, key_idx=idx)
    results_current.append({"model": m_name, "tag": m_tag, "budget": b_desc, **res})
    
    st_icon = "✅" if res["status"] == "SUCCESS" else ("⚠️" if res["status"] == "NOT_FOUND" else "❌")
    lat_str = f"{res['latency']}s" if res['latency'] > 0 else "-"
    summary = res["text"] if res["status"] == "SUCCESS" else res["error"]
    print(f"{m_name:<25} | {m_tag:<20} | {b_desc:<18} | ⏱️ {lat_str:<7} | {st_icon} {res['status']:<7} | {summary}")
    time.sleep(0.3)

print("\n" + "=" * 105)
print("【測試 2】：極速聊天模式 (設定 thinking_budget = 0 完全關閉深度思考)")
print(f"{'模型名稱':<25} | {'模型定位':<20} | {'Thinking設定':<18} | {'耗時(秒)':<9} | {'狀態':<10} | {'回覆摘要'}")
print("-" * 115)

results_zero = []
for idx, (m_name, m_tag) in enumerate(MODELS_TO_TEST):
    budget = 0
    b_desc = "Budget = 0 (關閉思考⚡)"
    res = test_model_call(m_name, budget, key_idx=idx+2)
    results_zero.append({"model": m_name, "tag": m_tag, "budget": b_desc, **res})
    
    st_icon = "✅" if res["status"] == "SUCCESS" else ("⚠️" if res["status"] == "NOT_FOUND" else "❌")
    lat_str = f"{res['latency']}s" if res['latency'] > 0 else "-"
    summary = res["text"] if res["status"] == "SUCCESS" else res["error"]
    print(f"{m_name:<25} | {m_tag:<20} | {b_desc:<18} | ⏱️ {lat_str:<7} | {st_icon} {res['status']:<7} | {summary}")
    time.sleep(0.3)

# 儲存結果
summary_data = {
    "current_config_results": results_current,
    "budget_zero_results": results_zero
}
with open("scratch/models_speed_benchmark.json", "w", encoding="utf-8") as f:
    json.dump(summary_data, f, ensure_ascii=False, indent=2)

print("\n🎉 測試完成！數據已輸出至 scratch/models_speed_benchmark.json")
