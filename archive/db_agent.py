# src/db_agent.py
import os, sys, sqlite3
from langchain.tools import Tool
from langchain_experimental.tools import PythonREPLTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
# from tools import get_daily_summary
from config import GOOGLE_API_KEY, LLM_MODEL_NAME, DB_PATH

sys.path.append(os.path.join(os.path.dirname(__file__)))
from database_setup import get_db_schema

def run_db_agent(query: str, context: dict) -> str:
    """데이터베이스 관련 작업을 처리하는 에이전트를 실행합니다."""
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL_NAME, google_api_key=GOOGLE_API_KEY)
    
    tools = [
        # Tool(name="Daily Summarizer", func=get_daily_summary, description="로컬 DB에서 특정 날짜의 일정과 지출을 요약합니다."),
        Tool(name="Python Code Executor", func=PythonREPLTool().run, description="DB 데이터 분석 등 복잡한 작업을 위해 Python 코드를 실행합니다.")
    ]
    
    db_schema = get_db_schema(DB_PATH)
    agent_prompt = hub.pull("hwchase17/react")
    agent_prompt.template = f"""
    당신은 Python 데이터 분석 전문가입니다. 주어진 질문을 해결하기 위해 도구를 사용하세요.

    **사용 가능한 도구:** {{tools}}
    **데이터베이스 정보:**
    - 경로: '{DB_PATH}'
    - 스키마: {db_schema}
    
    ... (이하 프롬프트 내용은 기존 agent.py와 동일) ...

    Question: {query}
    {{agent_scratchpad}}
    """
    
    agent = create_react_agent(llm, tools, agent_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    print("--- 데이터 분석팀(DB Agent) 작동 시작 ---")
    result = agent_executor.invoke({"input": query})
    return result['output']