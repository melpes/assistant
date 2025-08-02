# src/agent.py (리팩토링)
import os
import sqlite3
import sys
import json
import datetime

from langchain.tools import StructuredTool
from langchain_experimental.tools import PythonREPLTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain_tavily import TavilySearch
from langchain import hub

# 직접 만든 도구와 설정을 가져옵니다.
sys.path.append(os.path.join(os.path.dirname(__file__)))
from database_setup import get_db_schema
from tools import get_daily_summary, create_google_calendar_event, CalendarEventInput
from config import GOOGLE_API_KEY, TAVILY_API_KEY, LLM_MODEL_NAME, DB_PATH


def run_agent(query: str):
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL_NAME, google_api_key=GOOGLE_API_KEY)

    tools = [
        TavilySearch(tavily_api_key=TAVILY_API_KEY, name="Web Search", description="..."),
        # 간단한 Tool과 json.loads를 사용하여 안정성을 확보합니다.
        Tool(
            name="Create Google Calendar Event",
            func=lambda tool_input: create_google_calendar_event(json.loads(tool_input)),
            description="구글 캘린더에 새로운 일정을 등록할 때 사용합니다. 입력은 반드시 JSON 형식이어야 합니다."
        ),
        Tool(name="Daily Summarizer", func=get_daily_summary, description="..."),
        Tool(name="Python Code Executor", func=PythonREPLTool().run, description="...")
    ]
    
    db_schema = get_db_schema(DB_PATH)
    
    agent_prompt = hub.pull("hwchase17/react")
    agent_prompt.template = f"""
    당신은 여러 도구를 사용할 수 있는 만능 AI 비서입니다. 사용자의 질문을 해결하기 위해 최적의 도구를 선택해야 합니다.

    **사용 가능한 도구 목록:**
    {{tools}}

    **규칙:**
    1. 사용자의 모든 요청이 완벽하게 처리되었다고 판단되면, 반드시 'Final Answer'로 최종 응답을 하고 즉시 작업을 종료해야 합니다. 같은 작업을 반복하지 마세요.
    2. 연도가 명시되지 않은 날짜나 '오늘', '내일'과 같은 상대적인 날짜는, 반드시 지금이 **{datetime.date.today().strftime('%Y년 %m월 %d일')}**이라는 사실을 기준으로 가장 가까운 미래 날짜로 해석해야 합니다. 과거 날짜로 해석해서는 안 됩니다.
    3. 도구를 사용할 때, 각 도구의 입력 형식(description)을 반드시 확인하고 정확한 형식으로 Action Input을 제공해야 합니다.

    **Create Google Calendar Event 도구 사용법 예시:**
    Action: Create Google Calendar Event
    Action Input: {{{{"summary": "회의", "start_time": "2025-08-01T10:00:00", "end_time": "2025-08-01T11:00:00"}}}}


    **Python 코드 실행 시 참고 정보:**
    - `Python Code Executor` 도구를 사용할 때만 아래 정보를 참고하세요.
    - 데이터베이스 경로: '{DB_PATH}'
    - 데이터베이스 스키마:
    ```sql
    {db_schema}
    ```
    - `pandas`와 `sqlite3` 라이브러리를 사용할 수 있습니다.

    **작업 흐름:**
    1. 사용자의 질문을 분석하고, 가장 적합한 도구를 하나 선택합니다.
    2. 모든 작업이 끝나면, 최종 답변을 반드시 한글로 제공합니다.

    **출력 형식:**
    Question: 사용자의 질문
    Thought: 내가 해야 할 일에 대한 생각. 어떤 도구를 왜 사용해야 하는지 설명합니다.
    Action: 사용할 도구의 이름.
    Action Input: 도구에 전달할 입력값.
    Observation: 도구 실행 결과.
    ... (이 과정은 여러 번 반복될 수 있습니다)
    Thought: 이제 최종 답변을 알았습니다.
    Final Answer: 최종 답변 (한글)

    자, 시작합니다!

    Question: {query}
    {{agent_scratchpad}}
    """
    
    agent = create_react_agent(llm, tools, agent_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    print("에이전트가 당신의 질문에 대해 생각하고 있습니다...")
    result = agent_executor.invoke({"input": query})
    
    print("\n--- 최종 답변 ---")
    print(result['output'])