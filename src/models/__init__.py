# -*- coding: utf-8 -*-
"""
데이터 모델 패키지

시스템에서 사용하는 데이터 모델 클래스를 정의합니다.
"""

from src.models.classification_rule import ClassificationRule
from src.models.user_preference import UserPreference, AnalysisFilter

# 거래 유형 상수
class Transaction:
    TYPE_EXPENSE = "expense"
    TYPE_INCOME = "income"
    
    def __init__(
        self,
        transaction_id: str,
        date: str,
        amount: float,
        description: str,
        category: str = None,
        payment_method: str = None,
        transaction_type: str = TYPE_EXPENSE,
        memo: str = None
    ):
        """
        거래 초기화
        
        Args:
            transaction_id: 거래 ID
            date: 거래 날짜 (YYYY-MM-DD)
            amount: 거래 금액
            description: 거래 설명
            category: 카테고리
            payment_method: 결제 방식
            transaction_type: 거래 유형 (expense/income)
            memo: 메모
        """
        self.transaction_id = transaction_id
        self.date = date
        self.amount = amount
        self.description = description
        self.category = category
        self.payment_method = payment_method
        self.transaction_type = transaction_type
        self.memo = memo
    
    def to_dict(self) -> dict:
        """
        거래를 딕셔너리로 변환합니다.
        
        Returns:
            dict: 거래 정보 딕셔너리
        """
        return {
            'transaction_id': self.transaction_id,
            'date': self.date,
            'amount': self.amount,
            'description': self.description,
            'category': self.category,
            'payment_method': self.payment_method,
            'transaction_type': self.transaction_type,
            'memo': self.memo
        }