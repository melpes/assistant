# src/general_agent.py
import json
import logging
import google.generativeai as genai

from tools import (
    list_calendar_events, create_google_calendar_event, update_google_calendar_event, 
    delete_google_calendar_event, web_search, create_calendar_events_batch, 
    delete_calendar_events_batch, get_calendar_performance_report, optimize_calendar_performance
)
from config import GOOGLE_API_KEY, LLM_MODEL_NAME
from src.calendar.logging_config import setup_logging
import src.calendar.exceptions

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)

# 도구 이름과 실제 함수를 매핑
AVAILABLE_TOOLS = {
    # 캘린더 관련 도구
    "list_calendar_events": list_calendar_events,
    "create_google_calendar_event": create_google_calendar_event,
    "update_google_calendar_event": update_google_calendar_event,
    "delete_google_calendar_event": delete_google_calendar_event,
    
    # 배치 처리 도구
    "create_calendar_events_batch": create_calendar_events_batch,
    "delete_calendar_events_batch": delete_calendar_events_batch,
    
    # 성능 모니터링 도구
    "get_calendar_performance_report": get_calendar_performance_report,
    "optimize_calendar_performance": optimize_calendar_performance,
    
    # 웹 검색 도구
    "web_search": web_search,
}

def run_general_agent(query: str, context: dict) -> str:
    """네이티브 Tool-Calling으로 일반 작업을 처리합니다."""
    print("--- 일반 업무팀(General Agent) 작동 시작 (네이티브 방식) ---")
    logger.info("일반 업무팀(General Agent) 작동 시작")

    genai.configure(api_key=GOOGLE_API_KEY)
    
    # LLM에게 제공할 도구 명세를 정의합니다. (함수 자체를 전달)
    tools_for_llm = [
        # 캘린더 관련 도구
        list_calendar_events,
        create_google_calendar_event,
        update_google_calendar_event,
        delete_google_calendar_event,
        
        # 배치 처리 도구
        create_calendar_events_batch,
        delete_calendar_events_batch,
        
        # 성능 모니터링 도구
        get_calendar_performance_report,
        optimize_calendar_performance,
        
        # 웹 검색 도구
        web_search,
    ]

    try:
        model = genai.GenerativeModel(model_name=LLM_MODEL_NAME, tools=tools_for_llm)
        chat = model.start_chat(enable_automatic_function_calling=True)

        # 대화 컨텍스트 구성
        conversation_context = ""
        if "conversation_history" in context and len(context["conversation_history"]) > 0:
            # 최근 대화 기록 추가 (최대 3개)
            recent_history = context["conversation_history"][-3:]
            conversation_context = "최근 대화 기록:\n"
            for i, entry in enumerate(recent_history):
                conversation_context += f"[사용자]: {entry['query']}\n"
                conversation_context += f"[비서]: {entry['response']}\n\n"
        
        # 금융 관련 컨텍스트가 있는 경우 안내 추가
        if "last_agent_type" in context and context["last_agent_type"] == "financial":
            conversation_context += "참고: 이전 대화는 금융 에이전트가 처리했습니다. 금융 관련 후속 질문은 금융 에이전트로 라우팅됩니다.\n\n"

        prompt = f"""
        당신은 유능한 비서입니다. 아래 컨텍스트와 사용자 요청을 바탕으로, 필요한 도구를 사용하거나 직접 답변하세요.
        연도가 없는 날짜는 항상 현재 연도 또는 가장 가까운 미래로 해석해야 합니다.
        
        캘린더 관련 작업은 Google Calendar API를 직접 호출하여 처리합니다. 캘린더 일정 조회, 생성, 수정, 삭제 시
        항상 최신 데이터를 사용합니다.
        
        캘린더 일정 시간 형식:
        - 시간 지정 일정: 'YYYY-MM-DDTHH:MM:SS' 형식 (예: '2025-07-18T14:30:00')
        - 종일 일정: 'YYYY-MM-DD' 형식 (예: '2025-07-18')
        
        금융 관련 질문(지출, 수입, 거래 내역 등)은 금융 전문 에이전트가 처리합니다.
        만약 사용자의 질문이 금융과 관련되어 있다면, 금융 에이전트로 라우팅될 것임을 알려주세요.

        {conversation_context}
        [현재 컨텍스트]
        {json.dumps(context, ensure_ascii=False)}

        [사용자 요청]
        {query}
        """
        
        logger.info("LLM에게 계획 및 실행을 요청합니다...")
        print("LLM에게 계획 및 실행을 요청합니다...")
        
        # send_message가 자동으로 도구를 호출하고 결과를 다시 LLM에게 보내 최종 답변을 생성합니다.
        response = chat.send_message(prompt)
        logger.info("LLM 응답 수신 완료")
        return response.text
        
    except genai.types.generation_types.BlockedPromptException as e:
        logger.error(f"차단된 프롬프트 오류: {e}", exc_info=True)
        return "죄송합니다. 요청하신 내용은 안전 정책에 따라 처리할 수 없습니다."
        
    except genai.types.generation_types.StopCandidateException as e:
        logger.error(f"응답 생성 중단 오류: {e}", exc_info=True)
        return "죄송합니다. 응답 생성 중 문제가 발생했습니다. 다른 방식으로 질문해 주세요."
    
    except ImportError as e:
        logger.error(f"모듈 가져오기 오류: {e}", exc_info=True)
        return "필요한 모듈을 불러올 수 없습니다. 필요한 패키지가 설치되어 있는지 확인해주세요."
    
    # 캘린더 서비스 관련 예외 처리
    except src.calendar.exceptions.AuthenticationError as e:
        logger.error(f"인증 오류: {e.get_technical_details()}", exc_info=True)
        return e.get_user_message()
        
    except src.calendar.exceptions.TokenExpiredError as e:
        logger.error(f"토큰 만료 오류: {e.get_technical_details()}", exc_info=True)
        return e.get_user_message()
        
    except src.calendar.exceptions.APIQuotaExceededError as e:
        logger.error(f"API 할당량 초과 오류: {e.get_technical_details()}", exc_info=True)
        return e.get_user_message()
        
    except src.calendar.exceptions.NetworkError as e:
        logger.error(f"네트워크 오류: {e.get_technical_details()}", exc_info=True)
        return e.get_user_message()
        
    except src.calendar.exceptions.EventNotFoundError as e:
        logger.error(f"이벤트 없음 오류: {e.get_technical_details()}", exc_info=True)
        return e.get_user_message()
        
    except src.calendar.exceptions.InvalidEventDataError as e:
        logger.error(f"잘못된 이벤트 데이터 오류: {e.get_technical_details()}", exc_info=True)
        return e.get_user_message()
        
    except src.calendar.exceptions.CalendarServiceError as e:
        logger.error(f"캘린더 서비스 오류: {e.get_technical_details()}", exc_info=True)
        return e.get_user_message()
        
    except Exception as e:
        logger.error(f"에이전트 실행 중 오류 발생: {e}", exc_info=True)
        return f"에이전트 실행 중 오류가 발생했습니다: {e}"