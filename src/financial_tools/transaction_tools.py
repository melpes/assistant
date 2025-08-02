# -*- coding: utf-8 -*-
"""
거래 조회 도구 모듈

LLM 에이전트가 호출할 수 있는 거래 조회 및 필터링 관련 도구 함수들을 제공합니다.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union

from src.repositories.transaction_repository import TransactionRepository
from src.repositories.db_connection import DatabaseConnection
from src.models.transaction import Transaction

# 로거 설정
logger = logging.getLogger(__name__)

# 데이터베이스 연결 및 저장소 초기화
def _get_transaction_repository() -> TransactionRepository:
    """
    TransactionRepository 인스턴스를 반환합니다.
    
    Returns:
        TransactionRepository: 거래 저장소 인스턴스
    """
    db_connection = DatabaseConnection()
    return TransactionRepository(db_connection)

def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """
    문자열을 날짜 객체로 변환합니다.
    
    Args:
        date_str: 날짜 문자열 (YYYY-MM-DD)
        
    Returns:
        Optional[date]: 변환된 날짜 객체 또는 None
        
    Raises:
        ValueError: 유효하지 않은 날짜 형식인 경우
    """
    if not date_str:
        return None
    
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise ValueError(f"유효하지 않은 날짜 형식입니다: {date_str}. YYYY-MM-DD 형식을 사용하세요.")

def _format_transaction(transaction: Transaction) -> Dict[str, Any]:
    """
    거래 객체를 API 응답용 딕셔너리로 변환합니다.
    
    Args:
        transaction: 거래 객체
        
    Returns:
        Dict[str, Any]: 포맷된 거래 정보
    """
    return {
        "id": transaction.id,
        "transaction_id": transaction.transaction_id,
        "date": transaction.transaction_date.isoformat(),
        "description": transaction.description,
        "amount": float(transaction.amount),
        "type": transaction.transaction_type,
        "category": transaction.category or "미분류",
        "payment_method": transaction.payment_method or "미분류",
        "source": transaction.source,
        "account_type": transaction.account_type,
        "memo": transaction.memo,
        "is_excluded": transaction.is_excluded
    }

def _calculate_summary(transactions: List[Transaction]) -> Dict[str, Any]:
    """
    거래 목록의 요약 정보를 계산합니다.
    
    Args:
        transactions: 거래 객체 목록
        
    Returns:
        Dict[str, Any]: 요약 정보
    """
    if not transactions:
        return {
            "total_count": 0,
            "total_amount": 0,
            "expense_count": 0,
            "expense_amount": 0,
            "income_count": 0,
            "income_amount": 0,
            "date_range": {
                "start": None,
                "end": None
            }
        }
    
    # 초기값 설정
    expense_count = 0
    expense_amount = Decimal('0')
    income_count = 0
    income_amount = Decimal('0')
    min_date = transactions[0].transaction_date
    max_date = transactions[0].transaction_date
    
    # 거래 집계
    for tx in transactions:
        if tx.transaction_type == Transaction.TYPE_EXPENSE:
            expense_count += 1
            expense_amount += tx.amount
        elif tx.transaction_type == Transaction.TYPE_INCOME:
            income_count += 1
            income_amount += tx.amount
        
        # 날짜 범위 업데이트
        if tx.transaction_date < min_date:
            min_date = tx.transaction_date
        if tx.transaction_date > max_date:
            max_date = tx.transaction_date
    
    return {
        "total_count": len(transactions),
        "total_amount": float(expense_amount + income_amount),
        "expense_count": expense_count,
        "expense_amount": float(expense_amount),
        "income_count": income_count,
        "income_amount": float(income_amount),
        "date_range": {
            "start": min_date.isoformat(),
            "end": max_date.isoformat()
        }
    }

def list_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    payment_method: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    transaction_type: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    특정 조건에 맞는 거래 내역을 조회합니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        category: 카테고리 필터
        payment_method: 결제 방식 필터
        min_amount: 최소 금액
        max_amount: 최대 금액
        transaction_type: 거래 유형 (expense/income)
        limit: 반환할 최대 거래 수
        
    Returns:
        dict: 거래 목록과 요약 정보
        
    Raises:
        ValueError: 유효하지 않은 입력 값이 있는 경우
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        # 날짜 파싱
        parsed_start_date = _parse_date(start_date)
        parsed_end_date = _parse_date(end_date)
        
        # 기본 날짜 범위 설정 (지정되지 않은 경우 최근 30일)
        if not parsed_start_date and not parsed_end_date:
            parsed_end_date = date.today()
            parsed_start_date = parsed_end_date - timedelta(days=30)
        elif not parsed_start_date:
            parsed_start_date = parsed_end_date - timedelta(days=30)
        elif not parsed_end_date:
            parsed_end_date = parsed_start_date + timedelta(days=30)
        
        # 거래 유형 검증
        if transaction_type and transaction_type not in [Transaction.TYPE_EXPENSE, Transaction.TYPE_INCOME]:
            raise ValueError(f"유효하지 않은 거래 유형입니다: {transaction_type}. 'expense' 또는 'income'을 사용하세요.")
        
        # 필터 구성
        filters = {
            'start_date': parsed_start_date,
            'end_date': parsed_end_date,
            'limit': limit,
            'order_by': 'transaction_date',
            'order_direction': 'desc'
        }
        
        if category:
            filters['category'] = category
        
        if payment_method:
            filters['payment_method'] = payment_method
        
        if min_amount is not None:
            filters['min_amount'] = min_amount
        
        if max_amount is not None:
            filters['max_amount'] = max_amount
        
        if transaction_type:
            filters['transaction_type'] = transaction_type
        
        # 거래 조회
        repo = _get_transaction_repository()
        transactions = repo.list(filters)
        
        # 전체 개수 조회 (페이징을 위해)
        total_count = repo.count(filters)
        
        # 응답 구성
        formatted_transactions = [_format_transaction(tx) for tx in transactions]
        summary = _calculate_summary(transactions)
        
        return {
            "transactions": formatted_transactions,
            "summary": summary,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "has_more": total_count > limit
            },
            "filters": {
                "start_date": parsed_start_date.isoformat() if parsed_start_date else None,
                "end_date": parsed_end_date.isoformat() if parsed_end_date else None,
                "category": category,
                "payment_method": payment_method,
                "min_amount": min_amount,
                "max_amount": max_amount,
                "transaction_type": transaction_type
            }
        }
    
    except ValueError as e:
        logger.error(f"입력 값 오류: {e}")
        return {
            "error": str(e),
            "transactions": [],
            "summary": _calculate_summary([]),
            "pagination": {"total": 0, "limit": limit, "has_more": False}
        }
    
    except Exception as e:
        logger.error(f"거래 조회 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"거래 조회 중 오류가 발생했습니다: {e}",
            "transactions": [],
            "summary": _calculate_summary([]),
            "pagination": {"total": 0, "limit": limit, "has_more": False}
        }

def get_transaction_details(transaction_id: str) -> Dict[str, Any]:
    """
    특정 거래의 상세 정보를 조회합니다.
    
    Args:
        transaction_id: 거래 ID
        
    Returns:
        dict: 거래 상세 정보
        
    Raises:
        ValueError: 거래 ID가 유효하지 않은 경우
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        if not transaction_id:
            raise ValueError("거래 ID는 필수 항목입니다.")
        
        repo = _get_transaction_repository()
        transaction = repo.read_by_transaction_id(transaction_id)
        
        if not transaction:
            return {
                "error": f"거래 ID '{transaction_id}'에 해당하는 거래를 찾을 수 없습니다.",
                "transaction": None
            }
        
        return {
            "transaction": _format_transaction(transaction)
        }
    
    except ValueError as e:
        logger.error(f"입력 값 오류: {e}")
        return {
            "error": str(e),
            "transaction": None
        }
    
    except Exception as e:
        logger.error(f"거래 상세 조회 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"거래 상세 조회 중 오류가 발생했습니다: {e}",
            "transaction": None
        }

def search_transactions(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    키워드로 거래를 검색합니다.
    
    Args:
        query: 검색 키워드
        limit: 반환할 최대 거래 수
        
    Returns:
        dict: 검색 결과 거래 목록
        
    Raises:
        ValueError: 검색어가 유효하지 않은 경우
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        if not query or len(query.strip()) < 2:
            raise ValueError("검색어는 2글자 이상이어야 합니다.")
        
        # 필터 구성
        filters = {
            'description_contains': query,
            'limit': limit,
            'order_by': 'transaction_date',
            'order_direction': 'desc'
        }
        
        # 거래 조회
        repo = _get_transaction_repository()
        transactions = repo.list(filters)
        
        # 전체 개수 조회
        total_count = repo.count(filters)
        
        # 응답 구성
        formatted_transactions = [_format_transaction(tx) for tx in transactions]
        summary = _calculate_summary(transactions)
        
        return {
            "query": query,
            "transactions": formatted_transactions,
            "summary": summary,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "has_more": total_count > limit
            }
        }
    
    except ValueError as e:
        logger.error(f"입력 값 오류: {e}")
        return {
            "error": str(e),
            "query": query,
            "transactions": [],
            "summary": _calculate_summary([]),
            "pagination": {"total": 0, "limit": limit, "has_more": False}
        }
    
    except Exception as e:
        logger.error(f"거래 검색 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"거래 검색 중 오류가 발생했습니다: {e}",
            "query": query,
            "transactions": [],
            "summary": _calculate_summary([]),
            "pagination": {"total": 0, "limit": limit, "has_more": False}
        }

def get_available_categories() -> Dict[str, Any]:
    """
    사용 가능한 모든 카테고리 목록을 조회합니다.
    
    Returns:
        dict: 카테고리 목록
        
    Raises:
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        repo = _get_transaction_repository()
        categories = repo.get_categories()
        
        return {
            "categories": categories,
            "count": len(categories)
        }
    
    except Exception as e:
        logger.error(f"카테고리 목록 조회 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"카테고리 목록 조회 중 오류가 발생했습니다: {e}",
            "categories": [],
            "count": 0
        }

def get_available_payment_methods() -> Dict[str, Any]:
    """
    사용 가능한 모든 결제 방식 목록을 조회합니다.
    
    Returns:
        dict: 결제 방식 목록
        
    Raises:
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        repo = _get_transaction_repository()
        payment_methods = repo.get_payment_methods()
        
        return {
            "payment_methods": payment_methods,
            "count": len(payment_methods)
        }
    
    except Exception as e:
        logger.error(f"결제 방식 목록 조회 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"결제 방식 목록 조회 중 오류가 발생했습니다: {e}",
            "payment_methods": [],
            "count": 0
        }

def get_transaction_date_range() -> Dict[str, Any]:
    """
    거래 데이터의 전체 날짜 범위를 조회합니다.
    
    Returns:
        dict: 날짜 범위 정보
        
    Raises:
        RuntimeError: 데이터베이스 오류 발생 시
    """
    try:
        repo = _get_transaction_repository()
        min_date, max_date = repo.get_date_range()
        
        return {
            "date_range": {
                "start": min_date.isoformat() if min_date else None,
                "end": max_date.isoformat() if max_date else None
            },
            "has_data": min_date is not None and max_date is not None
        }
    
    except Exception as e:
        logger.error(f"날짜 범위 조회 중 오류 발생: {e}", exc_info=True)
        return {
            "error": f"날짜 범위 조회 중 오류가 발생했습니다: {e}",
            "date_range": {"start": None, "end": None},
            "has_data": False
        }