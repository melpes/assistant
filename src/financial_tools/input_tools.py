# -*- coding: utf-8 -*-
"""
수동 거래 입력 도구 모듈

LLM 에이전트가 사용할 수 있는 수동 거래 입력 도구 함수들을 제공합니다.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.ingesters.manual_ingester import ManualIngester
from src.repositories.transaction_repository import TransactionRepository
from src.models.transaction import Transaction

# 로거 설정
logger = logging.getLogger(__name__)

def add_expense(
    date: str,
    amount: float,
    description: str,
    category: str = None,
    payment_method: str = None,
    memo: str = None
) -> Dict[str, Any]:
    """
    새로운 지출 거래를 추가합니다.
    
    Args:
        date: 거래 날짜 (YYYY-MM-DD)
        amount: 거래 금액
        description: 거래 설명
        category: 카테고리 (기본값: 자동 분류)
        payment_method: 결제 방식 (기본값: 자동 분류)
        memo: 메모
        
    Returns:
        Dict[str, Any]: 추가된 거래 정보
    """
    logger.info(f"지출 거래 추가: {description}, {amount}원")
    
    try:
        # 날짜 문자열을 datetime.date 객체로 변환
        transaction_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # 금액 검증
        if amount <= 0:
            return {
                "success": False,
                "error": "금액은 0보다 커야 합니다.",
                "transaction": None
            }
        
        # ManualIngester 인스턴스 생성
        ingester = ManualIngester()
        
        # 카테고리가 제공되지 않은 경우 자동 제안 사용
        if category is None:
            suggestions = ingester.get_autocomplete_suggestions(description, 'expense')
            if suggestions['exact_match'] or suggestions['category']:
                category = suggestions['category']
            else:
                category = '기타'
        
        # 결제 방식이 제공되지 않은 경우 자동 제안 사용
        if payment_method is None:
            suggestions = ingester.get_autocomplete_suggestions(description, 'expense')
            if suggestions['exact_match'] or suggestions['payment_method']:
                payment_method = suggestions['payment_method']
            else:
                payment_method = '현금'
        
        # 거래 추가
        transaction_data = ingester.add_expense(
            transaction_date=transaction_date,
            description=description,
            amount=amount,
            category=category,
            payment_method=payment_method,
            memo=memo or ''
        )
        
        # 데이터베이스에 저장
        repo = TransactionRepository()
        transaction = Transaction.from_dict(transaction_data)
        repo.create(transaction)
        
        return {
            "success": True,
            "transaction": transaction_data,
            "message": "지출 거래가 성공적으로 추가되었습니다."
        }
        
    except ValueError as e:
        logger.error(f"입력값 오류: {e}")
        return {
            "success": False,
            "error": f"입력값 오류: {e}",
            "transaction": None
        }
    except Exception as e:
        logger.error(f"지출 거래 추가 중 오류 발생: {e}")
        return {
            "success": False,
            "error": f"지출 거래 추가 중 오류 발생: {e}",
            "transaction": None
        }

def add_income(
    date: str,
    amount: float,
    description: str,
    category: str = None,
    payment_method: str = None,
    memo: str = None
) -> Dict[str, Any]:
    """
    새로운 수입 거래를 추가합니다.
    
    Args:
        date: 거래 날짜 (YYYY-MM-DD)
        amount: 거래 금액
        description: 거래 설명
        category: 수입 유형 (기본값: 자동 분류)
        payment_method: 입금 방식 (기본값: 자동 분류)
        memo: 메모
        
    Returns:
        Dict[str, Any]: 추가된 거래 정보
    """
    logger.info(f"수입 거래 추가: {description}, {amount}원")
    
    try:
        # 날짜 문자열을 datetime.date 객체로 변환
        transaction_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # 금액 검증
        if amount <= 0:
            return {
                "success": False,
                "error": "금액은 0보다 커야 합니다.",
                "transaction": None
            }
        
        # ManualIngester 인스턴스 생성
        ingester = ManualIngester()
        
        # 카테고리가 제공되지 않은 경우 자동 제안 사용
        if category is None:
            suggestions = ingester.get_autocomplete_suggestions(description, 'income')
            if suggestions['exact_match'] or suggestions['category']:
                category = suggestions['category']
            else:
                category = '기타수입'
        
        # 결제 방식이 제공되지 않은 경우 자동 제안 사용
        if payment_method is None:
            suggestions = ingester.get_autocomplete_suggestions(description, 'income')
            if suggestions['exact_match'] or suggestions['payment_method']:
                payment_method = suggestions['payment_method']
            else:
                payment_method = '계좌입금'
        
        # 거래 추가
        transaction_data = ingester.add_income(
            transaction_date=transaction_date,
            description=description,
            amount=amount,
            category=category,
            payment_method=payment_method,
            memo=memo or ''
        )
        
        # 데이터베이스에 저장
        repo = TransactionRepository()
        transaction = Transaction.from_dict(transaction_data)
        repo.create(transaction)
        
        return {
            "success": True,
            "transaction": transaction_data,
            "message": "수입 거래가 성공적으로 추가되었습니다."
        }
        
    except ValueError as e:
        logger.error(f"입력값 오류: {e}")
        return {
            "success": False,
            "error": f"입력값 오류: {e}",
            "transaction": None
        }
    except Exception as e:
        logger.error(f"수입 거래 추가 중 오류 발생: {e}")
        return {
            "success": False,
            "error": f"수입 거래 추가 중 오류 발생: {e}",
            "transaction": None
        }

def update_transaction(
    transaction_id: str,
    category: str = None,
    payment_method: str = None,
    memo: str = None,
    is_excluded: bool = None
) -> Dict[str, Any]:
    """
    기존 거래 정보를 업데이트합니다.
    
    Args:
        transaction_id: 거래 ID
        category: 새 카테고리
        payment_method: 새 결제 방식
        memo: 새 메모
        is_excluded: 분석 제외 여부
        
    Returns:
        Dict[str, Any]: 업데이트된 거래 정보
    """
    logger.info(f"거래 업데이트: {transaction_id}")
    
    try:
        # 거래 조회
        repo = TransactionRepository()
        transaction = repo.get_by_transaction_id(transaction_id)
        
        if not transaction:
            return {
                "success": False,
                "error": f"거래 ID '{transaction_id}'를 찾을 수 없습니다.",
                "transaction": None
            }
        
        # 업데이트할 필드 설정
        if category is not None:
            transaction.category = category
        
        if payment_method is not None:
            transaction.payment_method = payment_method
        
        if memo is not None:
            transaction.memo = memo
        
        if is_excluded is not None:
            transaction.is_excluded = is_excluded
        
        # 데이터베이스에 저장
        repo.update(transaction)
        
        return {
            "success": True,
            "transaction": transaction.to_dict(),
            "message": "거래 정보가 성공적으로 업데이트되었습니다."
        }
        
    except Exception as e:
        logger.error(f"거래 업데이트 중 오류 발생: {e}")
        return {
            "success": False,
            "error": f"거래 업데이트 중 오류 발생: {e}",
            "transaction": None
        }

def batch_add_transactions(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    여러 거래를 일괄 추가합니다.
    
    Args:
        transactions: 추가할 거래 데이터 목록
            각 거래는 다음 필드를 포함해야 함:
            - date: 거래 날짜 (YYYY-MM-DD)
            - amount: 거래 금액
            - description: 거래 설명
            - transaction_type: 거래 유형 (expense/income)
            - category: 카테고리 (선택)
            - payment_method: 결제 방식 (선택)
            - memo: 메모 (선택)
        
    Returns:
        Dict[str, Any]: 일괄 추가 결과
    """
    logger.info(f"{len(transactions)}개의 거래 일괄 추가 시작")
    
    try:
        # 입력 데이터 검증
        if not transactions:
            return {
                "success": False,
                "error": "추가할 거래가 없습니다.",
                "transactions": []
            }
        
        # 데이터 변환
        normalized_transactions = []
        
        for tx in transactions:
            # 필수 필드 확인
            if not all(key in tx for key in ['date', 'amount', 'description', 'transaction_type']):
                continue
                
            # 날짜 변환
            try:
                transaction_date = datetime.strptime(tx['date'], '%Y-%m-%d').date()
            except ValueError:
                continue
                
            # 금액 확인
            if tx['amount'] <= 0:
                continue
                
            # 거래 유형 확인
            if tx['transaction_type'] not in ['expense', 'income']:
                continue
                
            # 정규화된 거래 데이터 생성
            normalized_tx = {
                'transaction_date': transaction_date,
                'description': tx['description'],
                'amount': tx['amount'],
                'transaction_type': tx['transaction_type'],
                'category': tx.get('category'),
                'payment_method': tx.get('payment_method'),
                'memo': tx.get('memo', '')
            }
            
            normalized_transactions.append(normalized_tx)
        
        if not normalized_transactions:
            return {
                "success": False,
                "error": "유효한 거래 데이터가 없습니다.",
                "transactions": []
            }
        
        # ManualIngester를 사용하여 일괄 추가
        ingester = ManualIngester()
        transaction_data_list = ingester.batch_add_transactions(normalized_transactions)
        
        # 데이터베이스에 저장
        repo = TransactionRepository()
        saved_transactions = []
        
        for transaction_data in transaction_data_list:
            transaction = Transaction.from_dict(transaction_data)
            repo.create(transaction)
            saved_transactions.append(transaction_data)
        
        return {
            "success": True,
            "transactions": saved_transactions,
            "count": len(saved_transactions),
            "message": f"{len(saved_transactions)}개의 거래가 성공적으로 추가되었습니다."
        }
        
    except Exception as e:
        logger.error(f"일괄 거래 추가 중 오류 발생: {e}")
        return {
            "success": False,
            "error": f"일괄 거래 추가 중 오류 발생: {e}",
            "transactions": []
        }

def get_transaction_templates(transaction_type: str = 'expense') -> Dict[str, Any]:
    """
    저장된 거래 템플릿 목록을 반환합니다.
    
    Args:
        transaction_type: 거래 유형 (expense/income)
        
    Returns:
        Dict[str, Any]: 템플릿 목록
    """
    logger.info(f"{transaction_type} 템플릿 목록 조회")
    
    try:
        # ManualIngester 인스턴스 생성
        ingester = ManualIngester()
        
        # 템플릿 목록 조회
        templates = ingester.get_templates(transaction_type)
        
        return {
            "success": True,
            "templates": templates,
            "count": len(templates)
        }
        
    except Exception as e:
        logger.error(f"템플릿 목록 조회 중 오류 발생: {e}")
        return {
            "success": False,
            "error": f"템플릿 목록 조회 중 오류 발생: {e}",
            "templates": {}
        }

def apply_transaction_template(
    template_name: str,
    date: str,
    amount: float,
    memo: str = None,
    transaction_type: str = 'expense'
) -> Dict[str, Any]:
    """
    템플릿을 적용하여 거래를 생성합니다.
    
    Args:
        template_name: 템플릿 이름
        date: 거래 날짜 (YYYY-MM-DD)
        amount: 거래 금액
        memo: 메모 (기본값: 템플릿의 메모)
        transaction_type: 거래 유형 (expense/income)
        
    Returns:
        Dict[str, Any]: 생성된 거래 정보
    """
    logger.info(f"템플릿 적용: {template_name}, {amount}원")
    
    try:
        # 날짜 문자열을 datetime.date 객체로 변환
        transaction_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # 금액 검증
        if amount <= 0:
            return {
                "success": False,
                "error": "금액은 0보다 커야 합니다.",
                "transaction": None
            }
        
        # ManualIngester 인스턴스 생성
        ingester = ManualIngester()
        
        # 템플릿 존재 여부 확인
        templates = ingester.get_templates(transaction_type)
        if template_name not in templates:
            return {
                "success": False,
                "error": f"템플릿 '{template_name}'을(를) 찾을 수 없습니다.",
                "transaction": None
            }
        
        # 템플릿 적용
        transaction_data = ingester.apply_template(
            template_name=template_name,
            transaction_date=transaction_date,
            amount=amount,
            memo=memo,
            transaction_type=transaction_type
        )
        
        if not transaction_data:
            return {
                "success": False,
                "error": "템플릿 적용 중 오류가 발생했습니다.",
                "transaction": None
            }
        
        # 데이터베이스에 저장
        repo = TransactionRepository()
        transaction = Transaction.from_dict(transaction_data)
        repo.create(transaction)
        
        return {
            "success": True,
            "transaction": transaction_data,
            "message": "템플릿을 사용하여 거래가 성공적으로 추가되었습니다."
        }
        
    except ValueError as e:
        logger.error(f"입력값 오류: {e}")
        return {
            "success": False,
            "error": f"입력값 오류: {e}",
            "transaction": None
        }
    except Exception as e:
        logger.error(f"템플릿 적용 중 오류 발생: {e}")
        return {
            "success": False,
            "error": f"템플릿 적용 중 오류 발생: {e}",
            "transaction": None
        }

def save_transaction_template(
    name: str,
    description: str,
    category: str,
    payment_method: str,
    memo: str = None,
    transaction_type: str = 'expense'
) -> Dict[str, Any]:
    """
    새 거래 템플릿을 저장합니다.
    
    Args:
        name: 템플릿 이름
        description: 거래 설명
        category: 카테고리
        payment_method: 결제 방식
        memo: 메모
        transaction_type: 거래 유형 (expense/income)
        
    Returns:
        Dict[str, Any]: 저장 결과
    """
    logger.info(f"템플릿 저장: {name}")
    
    try:
        # 필수 필드 확인
        if not name or not description or not category or not payment_method:
            return {
                "success": False,
                "error": "템플릿 이름, 설명, 카테고리, 결제 방식은 필수입니다.",
                "template": None
            }
        
        # ManualIngester 인스턴스 생성
        ingester = ManualIngester()
        
        # 템플릿 데이터 생성
        template_data = {
            'description': description,
            'category': category,
            'payment_method': payment_method,
            'memo': memo or ''
        }
        
        # 템플릿 저장
        success = ingester.save_template(name, template_data, transaction_type)
        
        if not success:
            return {
                "success": False,
                "error": "템플릿 저장 중 오류가 발생했습니다.",
                "template": None
            }
        
        return {
            "success": True,
            "template": {
                "name": name,
                **template_data
            },
            "message": f"템플릿 '{name}'이(가) 성공적으로 저장되었습니다."
        }
        
    except Exception as e:
        logger.error(f"템플릿 저장 중 오류 발생: {e}")
        return {
            "success": False,
            "error": f"템플릿 저장 중 오류 발생: {e}",
            "template": None
        }

def delete_transaction_template(
    name: str,
    transaction_type: str = 'expense'
) -> Dict[str, Any]:
    """
    거래 템플릿을 삭제합니다.
    
    Args:
        name: 템플릿 이름
        transaction_type: 거래 유형 (expense/income)
        
    Returns:
        Dict[str, Any]: 삭제 결과
    """
    logger.info(f"템플릿 삭제: {name}")
    
    try:
        # ManualIngester 인스턴스 생성
        ingester = ManualIngester()
        
        # 템플릿 존재 여부 확인
        templates = ingester.get_templates(transaction_type)
        if name not in templates:
            return {
                "success": False,
                "error": f"템플릿 '{name}'을(를) 찾을 수 없습니다."
            }
        
        # 템플릿 삭제
        success = ingester.delete_template(name, transaction_type)
        
        if not success:
            return {
                "success": False,
                "error": "템플릿 삭제 중 오류가 발생했습니다."
            }
        
        return {
            "success": True,
            "message": f"템플릿 '{name}'이(가) 성공적으로 삭제되었습니다."
        }
        
    except Exception as e:
        logger.error(f"템플릿 삭제 중 오류 발생: {e}")
        return {
            "success": False,
            "error": f"템플릿 삭제 중 오류 발생: {e}"
        }

def get_autocomplete_suggestions(
    description: str,
    transaction_type: str = 'expense'
) -> Dict[str, Any]:
    """
    거래 설명에 대한 자동완성 제안을 제공합니다.
    
    Args:
        description: 거래 설명
        transaction_type: 거래 유형 (expense/income)
        
    Returns:
        Dict[str, Any]: 자동완성 제안
    """
    logger.info(f"자동완성 제안 조회: {description}")
    
    try:
        # ManualIngester 인스턴스 생성
        ingester = ManualIngester()
        
        # 자동완성 제안 조회
        suggestions = ingester.get_autocomplete_suggestions(description, transaction_type)
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"자동완성 제안 조회 중 오류 발생: {e}")
        return {
            "success": False,
            "error": f"자동완성 제안 조회 중 오류 발생: {e}",
            "suggestions": {}
        }