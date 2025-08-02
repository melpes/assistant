# main.py
import sys
import os
import datetime
import re
import json
import logging

# src 폴더를 파이썬 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config import GOOGLE_API_KEY, TAVILY_API_KEY
# supervisor 또는 테스트를 위해 general_agent를 직접 호출
from general_agent import run_general_agent

# 로그 디렉토리 확인 및 생성
if not os.path.exists("logs"):
    os.makedirs("logs")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/main.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 금융 에이전트 모듈 가져오기 시도
try:
    from financial_agent import run_financial_agent
    FINANCIAL_AGENT_AVAILABLE = True
    logger.info("금융 에이전트 모듈 로드 성공")
except ImportError as e:
    logger.warning(f"금융 에이전트 모듈을 불러올 수 없습니다: {e}")
    print(f"경고: 금융 에이전트 모듈을 불러올 수 없습니다: {e}")
    print("금융 관련 쿼리는 일반 에이전트로 처리됩니다.")
    FINANCIAL_AGENT_AVAILABLE = False

# 금융 관련 키워드 목록
FINANCIAL_KEYWORDS = [
    '금융', '지출', '수입', '거래', '카드', '계좌', '돈', '금액', '결제',
    '통장', '송금', '이체', '입금', '출금', '잔액', '카테고리', '분석',
    '리포트', '보고서', '통계', '내역', '사용내역', '사용 내역', '소비',
    '지출 내역', '수입 내역', '월별', '일별', '주별', '기간별', '예산',
    '저축', '투자', '대출', '이자', '적금', '펀드', '주식', '배당금',
    '세금', '공과금', '청구서', '할부', '환불', '정산', '가계부', '썼'
]

# 컨텍스트 파일 경로
CONTEXT_FILE = "user_context.json"

def load_context():
    """사용자 컨텍스트를 로드합니다."""
    try:
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"컨텍스트 로드 중 오류 발생: {e}")
    
    # 기본 컨텍스트 반환
    return {
        "user_name": "강태희",
        "current_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "location": "대한민국 서울",
        "conversation_history": []
    }

def save_context(context):
    """사용자 컨텍스트를 저장합니다."""
    try:
        with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
            json.dump(context, ensure_ascii=False, indent=2, fp=f)
    except Exception as e:
        logger.error(f"컨텍스트 저장 중 오류 발생: {e}")

def is_financial_query(query):
    """쿼리가 금융 관련인지 확인합니다."""
    # 금융 관련 키워드가 있는지 확인
    return any(keyword in query for keyword in FINANCIAL_KEYWORDS)

def update_conversation_history(context, query, response, agent_type):
    """대화 기록을 업데이트합니다."""
    # 대화 기록이 없으면 초기화
    if "conversation_history" not in context:
        context["conversation_history"] = []
    
    # 대화 기록 추가
    context["conversation_history"].append({
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "query": query,
        "response": response,
        "agent_type": agent_type
    })
    
    # 대화 기록 최대 10개로 제한
    if len(context["conversation_history"]) > 10:
        context["conversation_history"] = context["conversation_history"][-10:]
    
    # 마지막 쿼리와 응답 저장
    context["last_query"] = query
    context["last_response"] = response
    context["last_agent_type"] = agent_type

def process_query(query, context):
    """쿼리를 처리하고 적절한 에이전트로 라우팅합니다."""
    # 현재 시간 업데이트
    context["current_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 쿼리 유형 판단
    query_is_financial = is_financial_query(query)
    
    # 명시적인 일반 쿼리 키워드 확인
    explicit_general_keywords = ['일정', '날씨', '알람', '타이머', '미팅', '회의', '캘린더', '메일', '이메일']
    is_explicit_general = any(keyword in query for keyword in explicit_general_keywords)
    
    # 이전 대화 컨텍스트 확인
    has_financial_context = False
    if "conversation_history" in context and len(context["conversation_history"]) > 0:
        last_agent = context.get("last_agent_type")
        if last_agent == "financial":
            has_financial_context = True
    
    # 에이전트 선택 로직
    use_financial_agent = False
    
    # 명시적인 일반 쿼리는 일반 에이전트로 라우팅
    if is_explicit_general:
        use_financial_agent = False
    # 명시적인 금융 키워드가 있거나, 이전 대화가 금융 관련이고 후속 질문인 경우
    elif (query_is_financial or has_financial_context) and FINANCIAL_AGENT_AVAILABLE:
        use_financial_agent = True
    
    # 에이전트 실행
    if use_financial_agent:
        logger.info(f"금융 에이전트로 쿼리 라우팅: '{query}'")
        if query_is_financial:
            print("금융 관련 쿼리로 판단하여 금융 에이전트를 실행합니다.")
        else:
            print("이전 대화 컨텍스트에 따라 금융 에이전트를 실행합니다.")
        
        response = run_financial_agent(query, context)
        update_conversation_history(context, query, response, "financial")
    else:
        if query_is_financial and not FINANCIAL_AGENT_AVAILABLE:
            logger.warning("금융 관련 쿼리이지만 금융 에이전트를 사용할 수 없어 일반 에이전트로 라우팅합니다.")
            print("금융 관련 쿼리이지만 금융 에이전트를 사용할 수 없어 일반 에이전트를 실행합니다.")
        elif is_explicit_general and has_financial_context:
            logger.info(f"명시적인 일반 쿼리로 판단하여 일반 에이전트로 라우팅: '{query}'")
            print("명시적인 일반 쿼리로 판단하여 일반 에이전트를 실행합니다.")
        else:
            logger.info(f"일반 에이전트로 쿼리 라우팅: '{query}'")
            print("일반 쿼리로 판단하여 일반 에이전트를 실행합니다.")
        
        response = run_general_agent(query, context)
        update_conversation_history(context, query, response, "general")
    
    return response

def main():
    """메인 함수"""
    # 환경변수 및 인증 파일 확인
    from src.auth_config import ensure_credentials_file
    
    # API 키 확인
    if not GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY가 설정되지 않았습니다.")
        print("오류: .env 파일에 GOOGLE_API_KEY를 설정해주세요.")
        print("예시: GOOGLE_API_KEY=your_api_key_here")
        return
    
    if not TAVILY_API_KEY:
        logger.error("TAVILY_API_KEY가 설정되지 않았습니다.")
        print("오류: .env 파일에 TAVILY_API_KEY를 설정해주세요.")
        print("예시: TAVILY_API_KEY=your_api_key_here")
        return
    
    # credentials.json 파일 확인 및 생성
    if not ensure_credentials_file():
        print("오류: Google OAuth 인증 정보를 설정할 수 없습니다.")
        print(".env 파일에 다음 변수들을 설정해주세요:")
        print("- GOOGLE_CLIENT_ID")
        print("- GOOGLE_CLIENT_SECRET") 
        print("- GOOGLE_PROJECT_ID")
        return

    # 쿼리 파일 읽기
    try:
        with open("query.txt", "r", encoding="utf-8") as f:
            query = f.read().strip()
        if not query:
            logger.error("query.txt 파일이 비어있습니다.")
            print("오류: query.txt 파일이 비어있습니다.")
            return
        logger.info(f"사용자 요청: {query}")
        print(f"사용자 요청: {query}")
    except FileNotFoundError:
        logger.error("query.txt 파일을 찾을 수 없습니다.")
        print("오류: query.txt 파일을 찾을 수 없습니다.")
        return

    # 컨텍스트 로드
    user_context = load_context()
    
    # 쿼리 처리
    final_response = process_query(query, user_context)
    
    # 컨텍스트 저장
    save_context(user_context)
    
    # 응답 출력
    print("\n--- 최종 답변 ---")
    print(final_response)


if __name__ == "__main__":
    main()