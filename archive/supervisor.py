# src/supervisor.py (tool_names 변수 추가)
import json
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from config import GOOGLE_API_KEY, LLM_MODEL_NAME

from general_agent import run_general_agent
from db_agent import run_db_agent

def run_supervisor(query: str, context: dict):
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL_NAME, google_api_key=GOOGLE_API_KEY)
    
    tools = [
        Tool(
            name="General Agent",
            func=lambda q: run_general_agent(query=q, context=context),
            description="웹 검색, 구글 캘린더 일정 관리 등 일반적인 작업을 처리합니다."
        ),
        Tool(
            name="Database Agent",
            func=lambda q: run_db_agent(query=q, context=context),
            description="지출 내역 분석, 데이터베이스 조회 등 데이터 관련 작업을 처리합니다."
        )
    ]
    
    # 1. 도구 이름 목록을 문자열로 만듭니다. (이 부분이 추가되었습니다)
    tool_names = ", ".join([t.name for t in tools])

    # 2. 프롬프트 템플릿에 {tool_names} 변수를 추가합니다.
    prompt_template = """
    당신은 유능한 비서실장입니다. 사용자의 요청을 분석하여, 가장 적합한 전문팀(Agent)에게 작업을 위임해야 합니다.

    **사용자 컨텍스트 정보:**
    {context}

    **사용 가능한 전문팀 목록:**
    {tool_names}

    **각 전문팀의 상세 설명:**
    {tools}
    
    Question: {input}
    {agent_scratchpad}
    """
    
    agent_prompt = PromptTemplate.from_template(prompt_template)
    
    # 3. .partial()을 사용하여 프롬프트에 tool_names 변수를 미리 채워넣습니다.
    agent_prompt = agent_prompt.partial(tool_names=tool_names)

    agent = create_react_agent(llm, tools, agent_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    context_str = json.dumps(context, ensure_ascii=False, indent=2)

    print("--- 비서실장(Supervisor) 작동 시작 ---")
    
    result = agent_executor.invoke({
        "input": query,
        "context": context_str
    })
    
    print("\n--- 최종 답변 ---")
    print(result['output'])