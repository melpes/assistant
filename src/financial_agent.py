# -*- coding: utf-8 -*-
"""
금융 에이전트 모듈

LLM을 활용하여 금융 관련 쿼리를 처리하는 에이전트를 구현합니다.
"""

import json
import logging
import traceback
import google.generativeai as genai

from src.financial_tools.transaction_tools import (
    list_transactions, get_transaction_details, search_transactions,
    get_available_categories, get_available_payment_methods, get_transaction_date_range
)
from src.financial_tools.analysis_tools import (
    analyze_expenses, analyze_income, analyze_income_patterns,
    compare_income_expense, analyze_trends, get_financial_summary
)
from src.financial_tools.comparison_tools import (
    compare_periods, compare_months, compare_with_previous_period, 
    compare_with_previous_month, find_significant_changes
)
from src.financial_tools.input_tools import (
    add_expense, add_income, update_transaction, batch_add_transactions,
    get_transaction_templates, apply_transaction_template,
    save_transaction_template, delete_transaction_template,
    get_autocomplete_suggestions
)
from src.financial_tools.management_tools import (
    add_classification_rule, update_classification_rule, delete_classification_rule,
    get_classification_rules, get_rule_stats, backup_data, restore_data,
    list_backups, export_data, get_system_status, update_settings, get_settings
)
from src.exceptions import (
    ValidationError, DataIngestionError, ClassificationError, AnalysisError,
    DatabaseError, ConfigError, BackupError
)
from src.response_formatter import format_response, handle_agent_error, extract_insights
from config import GOOGLE_API_KEY, LLM_MODEL_NAME

# 로거 설정
logger = logging.getLogger(__name__)

# 이 함수들은 src/response_formatter.py로 이동되었습니다.

# 도구 이름과 실제 함수를 매핑
FINANCIAL_TOOLS = {
    # 거래 조회 도구
    "list_transactions": list_transactions,
    "get_transaction_details": get_transaction_details,
    "search_transactions": search_transactions,
    "get_available_categories": get_available_categories,
    "get_available_payment_methods": get_available_payment_methods,
    "get_transaction_date_range": get_transaction_date_range,
    
    # 분석 도구
    "analyze_expenses": analyze_expenses,
    "analyze_income": analyze_income,
    "analyze_income_patterns": analyze_income_patterns,
    "compare_income_expense": compare_income_expense,
    "analyze_trends": analyze_trends,
    "get_financial_summary": get_financial_summary,
    
    # 비교 분석 도구
    "compare_periods": compare_periods,
    "compare_months": compare_months,
    "compare_with_previous_period": compare_with_previous_period,
    "compare_with_previous_month": compare_with_previous_month,
    "find_significant_changes": find_significant_changes,
    
    # 수동 거래 입력 도구
    "add_expense": add_expense,
    "add_income": add_income,
    "update_transaction": update_transaction,
    "batch_add_transactions": batch_add_transactions,
    "get_transaction_templates": get_transaction_templates,
    "apply_transaction_template": apply_transaction_template,
    "save_transaction_template": save_transaction_template,
    "delete_transaction_template": delete_transaction_template,
    "get_autocomplete_suggestions": get_autocomplete_suggestions,
    
    # 데이터 관리 도구
    "add_classification_rule": add_classification_rule,
    "update_classification_rule": update_classification_rule,
    "delete_classification_rule": delete_classification_rule,
    "get_classification_rules": get_classification_rules,
    "get_rule_stats": get_rule_stats,
    "backup_data": backup_data,
    "restore_data": restore_data,
    "list_backups": list_backups,
    "export_data": export_data,
    "get_system_status": get_system_status,
    "update_settings": update_settings,
    "get_settings": get_settings,
}

def run_financial_agent(query: str, context: dict) -> str:
    """
    금융 관련 쿼리를 처리하는 에이전트를 실행합니다.
    
    Args:
        query: 사용자 쿼리
        context: 사용자 컨텍스트
        
    Returns:
        str: 에이전트 응답
        
    Raises:
        RuntimeError: 에이전트 실행 중 오류 발생 시
    """
    print("--- 금융 에이전트(Financial Agent) 작동 시작 ---")
    logger.info("금융 에이전트(Financial Agent) 작동 시작")

    genai.configure(api_key=GOOGLE_API_KEY)
    
    # LLM에게 제공할 도구 명세를 정의합니다.
    tools_for_llm = [
        # 거래 조회 도구
        list_transactions,
        get_transaction_details,
        search_transactions,
        get_available_categories,
        get_available_payment_methods,
        get_transaction_date_range,
        
        # 분석 도구
        analyze_expenses,
        analyze_income,
        analyze_income_patterns,
        compare_income_expense,
        analyze_trends,
        get_financial_summary,
        
        # 비교 분석 도구
        compare_periods,
        compare_months,
        compare_with_previous_period,
        compare_with_previous_month,
        find_significant_changes,
        
        # 수동 거래 입력 도구
        add_expense,
        add_income,
        update_transaction,
        batch_add_transactions,
        get_transaction_templates,
        apply_transaction_template,
        save_transaction_template,
        delete_transaction_template,
        get_autocomplete_suggestions,
        
        # 데이터 관리 도구
        add_classification_rule,
        update_classification_rule,
        delete_classification_rule,
        get_classification_rules,
        get_rule_stats,
        backup_data,
        restore_data,
        list_backups,
        export_data,
        get_system_status,
        update_settings,
        get_settings,
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
        
        prompt = f"""
        당신은 개인 금융 관리 전문가입니다. 아래 컨텍스트와 사용자 요청을 바탕으로, 필요한 도구를 사용하거나 직접 답변하세요.
        
        금융 거래 관리 시스템에 접근하여 거래 내역을 조회하고 분석할 수 있습니다. 사용자의 요청에 따라 적절한 도구를 선택하여
        정확한 정보를 제공하세요.
        
        거래 유형:
        - 지출(expense): 사용자가 지출한 금액
        - 수입(income): 사용자가 받은 금액
        
        날짜 형식:
        - 'YYYY-MM-DD' 형식 (예: '2023-07-18')
        
        분석 도구:
        - analyze_expenses: 지출 분석 리포트 생성
        - analyze_income: 수입 분석 리포트 생성
        - analyze_income_patterns: 정기적인 수입 패턴 분석
        - analyze_trends: 지출 또는 수입 트렌드 분석
        - get_financial_summary: 지정된 기간의 재정 요약 정보 제공
        - compare_income_expense: 수입과 지출을 비교 분석하고 순 현금 흐름 계산
        
        비교 분석 도구:
        - compare_periods: 두 기간의 지출 또는 수입을 비교 분석
        - compare_months: 두 월의 지출 또는 수입을 비교 분석
        - compare_with_previous_period: 지정된 기간과 동일한 길이의 이전 기간을 비교
        - compare_with_previous_month: 지정된 월과 이전 월을 비교
        - find_significant_changes: 두 기간 사이의 주요 변동 사항을 찾아 분석
        
        수동 거래 입력 도구:
        - add_expense: 새로운 지출 거래 추가
        - add_income: 새로운 수입 거래 추가
        - update_transaction: 기존 거래 정보 업데이트
        - batch_add_transactions: 여러 거래 일괄 추가
        - get_transaction_templates: 저장된 거래 템플릿 목록 조회
        - apply_transaction_template: 템플릿을 사용하여 거래 추가
        - save_transaction_template: 새 거래 템플릿 저장
        - delete_transaction_template: 거래 템플릿 삭제
        - get_autocomplete_suggestions: 거래 설명에 대한 자동완성 제안 조회
        
        데이터 관리 도구:
        - add_classification_rule: 새로운 분류 규칙 추가
        - update_classification_rule: 기존 분류 규칙 업데이트
        - delete_classification_rule: 분류 규칙 삭제
        - get_classification_rules: 분류 규칙 목록 조회
        - get_rule_stats: 분류 규칙 통계 조회
        - backup_data: 데이터 백업
        - restore_data: 백업에서 데이터 복원
        - list_backups: 백업 목록 조회
        - export_data: 데이터 내보내기
        - get_system_status: 시스템 상태 정보 조회
        - update_settings: 시스템 설정 업데이트
        - get_settings: 시스템 설정 조회
        
        응답 형식 가이드라인:
        1. 사용자에게 친근하고 도움이 되는 톤으로 응답하세요.
        2. 복잡한 금융 정보를 이해하기 쉽게 설명하세요.
        3. 분석 결과에서 핵심 인사이트를 강조하세요.
        4. 필요한 경우 이모지를 적절히 사용하여 가독성을 높이세요.
        5. 오류가 발생한 경우 문제 해결 방법을 제안하세요.
        6. 사용자가 후속 질문을 할 수 있도록 관련 정보를 제공하세요.
        
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
    
    except ValidationError as e:
        logger.error(f"입력 검증 오류: {e}", exc_info=True)
        return f"입력 정보가 올바르지 않습니다: {e}"
    
    except DataIngestionError as e:
        logger.error(f"데이터 처리 오류: {e}", exc_info=True)
        return f"데이터 처리 중 문제가 발생했습니다: {e}"
    
    except ClassificationError as e:
        logger.error(f"거래 분류 오류: {e}", exc_info=True)
        return f"거래 분류 중 문제가 발생했습니다: {e}"
    
    except AnalysisError as e:
        logger.error(f"데이터 분석 오류: {e}", exc_info=True)
        return f"데이터 분석 중 문제가 발생했습니다: {e}"
    
    except DatabaseError as e:
        logger.error(f"데이터베이스 오류: {e}", exc_info=True)
        return f"데이터베이스 작업 중 문제가 발생했습니다: {e}"
    
    except ConfigError as e:
        logger.error(f"설정 오류: {e}", exc_info=True)
        return f"시스템 설정 관련 문제가 발생했습니다: {e}"
    
    except BackupError as e:
        logger.error(f"백업 오류: {e}", exc_info=True)
        return f"데이터 백업 또는 복원 중 문제가 발생했습니다: {e}"
    
    except ImportError as e:
        logger.error(f"모듈 가져오기 오류: {e}", exc_info=True)
        return "필요한 모듈을 불러올 수 없습니다. 필요한 패키지가 설치되어 있는지 확인해주세요."
    
    except Exception as e:
        logger.error(f"에이전트 실행 중 오류 발생: {e}", exc_info=True)
        error_trace = traceback.format_exc()
        logger.debug(f"상세 오류 정보: {error_trace}")
        return f"에이전트 실행 중 오류가 발생했습니다: {e}"