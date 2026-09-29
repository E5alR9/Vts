# -*- coding: utf-8 -*-
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from vm_agent.client import VMAgentClient

vm = VMAgentClient(host="172.22.212.232")

groups = [
    (
        "1. 基礎 LLM 與網路工具庫 (Google GenAI, OpenAI, Groq, Anthropic, Tavily)",
        "python -m pip install google-genai google-generativeai openai groq anthropic duckduckgo-search tavily-python python-dotenv requests beautifulsoup4 rich prompt_toolkit"
    ),
    (
        "2. 瀏覽器自主操作智能體 (Browser-Use & Playwright Chromium)",
        "python -m pip install playwright browser-use; python -m playwright install chromium"
    ),
    (
        "3. 微軟 AutoGen 多智能體對話與自動 Debug",
        "python -m pip install pyautogen"
    ),
    (
        "4. LangChain & LangGraph 企業級智能體工作流",
        "python -m pip install langchain langgraph langchain-google-genai langchain-openai langchain-community"
    ),
    (
        "5. HuggingFace Smolagents 輕量代碼智能體",
        "python -m pip install smolagents"
    ),
    (
        "6. Windows 桌面與 UI 深度操控庫 (UIAutomation, PyWinAuto, Selenium)",
        "python -m pip install uiautomation pywinauto selenium webdriver-manager"
    ),
    (
        "7. CrewAI 多角色團隊智能體",
        "python -m pip install crewai crewai-tools"
    )
]

print("==================================================")
print(" [*] 開始在 7L 虛擬機中部署全套頂級 AI 智能體...")
print("==================================================")

for title, cmd in groups:
    print(f"\n[*] 正在安裝: {title}")
    res = vm.exec(cmd, timeout=300)
    success = res.get("success", False)
    if success:
        print(f" [OK] {title} 安裝完成！")
    else:
        print(f" [WARNING] {title} 安裝結果: {res.get('returncode')}")
        err = res.get("stderr", "") or res.get("stdout", "")
        if err:
            lines = err.strip().split("\n")
            print(" 輸出摘要:\n  " + "\n  ".join(lines[-5:]))

print("\n==================================================")
print(" [SUCCESS] 所有智能體模組安裝階段完成！")
print("==================================================")
