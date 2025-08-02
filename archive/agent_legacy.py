# src/agent.py (최종 프롬프트 오류 수정)
import json, datetime, os, sqlite3, sys
from langchain.tools import Tool
from langchain_experimental.tools import PythonREPLTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_tavily import TavilySearch
from langchain.prompts import PromptTemplate # PromptTemplate을 직접 사용합니다.

from tools import list_calendar_events, create_google_calendar_event, update_google_calendar_event
from config import GOOGLE_API_KEY, TAVILY_API_KEY, LLM_MODEL_NAME, DB_PATH
sys.path.append(os.path.join(os.path.dirname(__file__)))
from database_setup import get_db_schema

def run_agent(query: str, context: dict):
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL_NAME, google_api_key=GOOGLE_API_KEY)
    
    tools = [
        Tool.from_function(func=lambda tool_input: list_calendar_events(json.loads(tool_input)), name="List Calendar Events", description="..."),
        Tool.from_function(func=lambda tool_input: create_google_calendar_event(json.loads(tool_input)), name="Create Calendar Event", description="..."),
        Tool.from_function(func=lambda tool_input: update_google_calendar_event(json.loads(tool_input)), name="Update Calendar Event", description="..."),
        TavilySearch(tavily_api_key=TAVILY_API_KEY, name="Web Search", description="..."),
        Tool(name="Python Code Executor", func=PythonREPLTool().run, description="...")
    ]
    
    # --- 프롬프트 생성 및 변수 주입 (핵심 수정 부분) ---

    # 1. 프롬프트 템플릿을 정의합니다. {tools}와 {tool_names}가 변수입니다.
    prompt_template = """
    당신은 유능하고 신중한 AI 비서입니다. 사용자의 복잡한 요청을 해결하기 위해, 반드시 다음의 '행동 원칙'에 따라 단계별로 생각하고 행동해야 합니다.

    **현재 컨텍스트:**
    {context}

    **행동 원칙 (SOP):**
    1.  **목표 분석:** 사용자의 최종 목표가 무엇인지 명확히 이해한다.
    2.  **정보 수집:** 목표 달성에 필요한 정보가 부족하다면(예: 오늘의 빈 시간, 기존 일정의 ID), 가장 먼저 관련 도구를 사용하여 정보를 수집한다. **절대 정보를 추측하거나 가정하지 않는다.**
    3.  **계획 수립:** 수집된 정보를 바탕으로, 목표를 달성하기 위한 구체적인 실행 계획을 세운다.
    4.  **계획 실행:** 세운 계획에 따라 적절한 도구를 **단 하나만** 실행한다.
    5.  **결과 검증 및 자기 성찰:** 실행 결과를 보고, 원래의 목표가 달성되었는지 확인한다.

    **사용 가능한 도구 목록:**
    {tool_names}
    
    **각 도구의 상세 설명:**
    {tools}

    Question: {input}
    {agent_scratchpad}
    """
    
    # 2. PromptTemplate 객체를 생성합니다.
    agent_prompt = PromptTemplate.from_template(prompt_template)

    # 3. .partial() 메소드를 사용하여, 에이전트가 실행되기 전에
    #    프롬프트의 특정 변수({tools}, {tool_names})를 미리 채워넣습니다.
    agent_prompt = agent_prompt.partial(
        tools="\n".join([f"{tool.name}: {tool.description}" for tool in tools]),
        tool_names=", ".join([tool.name for tool in tools]),
    )
    
    # ----------------------------------------------------
    
    agent = create_react_agent(llm, tools, agent_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, max_iterations=10)

    print("--- 최종 에이전트 작동 시작 ---")
    
    context_str = json.dumps(context, ensure_ascii=False, indent=2)
    # .invoke() 호출 시에는 이제 input과 context만 전달하면 됩니다.
    result = agent_executor.invoke({"input": query, "context": context_str})

    print("\n--- 최종 답변 ---")
    print(result['output'])