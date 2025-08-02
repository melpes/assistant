# -*- coding: utf-8 -*-
"""
거래(Transaction) 엔티티 클래스

금융 거래 관리 시스템의 핵심 엔티티로, 모든 수입 및 지출 거래를 표현합니다.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any
import re


class Transaction:
    """
    거래 엔티티 클래스
    
    금융 거래 관리 시스템의 핵심 엔티티로, 모든 수입 및 지출 거래를 표현합니다.
    """
    
    # 거래 유형 상수
    TYPE_EXPENSE = "expense"
    TYPE_INCOME = "income"
    
    # 유효한 거래 유형 목록
    VALID_TRANSACTION_TYPES = [TYPE_EXPENSE, TYPE_INCOME]
    
    def __init__(
        self,
        transaction_id: str,
        transaction_date: date,
        description: str,
        amount: Decimal,
        transaction_type: str,
        source: str,
        category: Optional[str] = None,
        payment_method: Optional[str] = None,
        account_type: Optional[str] = None,
        memo: Optional[str] = None,
        is_excluded: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        id: Optional[int] = None
    ):
        """
        거래 객체 초기화
        
        Args:
            transaction_id: 고유 거래 ID
            transaction_date: 거래 날짜
            description: 거래 설명
            amount: 거래 금액
            transaction_type: 거래 유형 (expense/income)
            source: 데이터 소스 (예: toss_card, toss_account, manual)
            category: 카테고리 (선택)
            payment_method: 결제 방식 (선택)
            account_type: 계좌 유형 (선택)
            memo: 메모 (선택)
            is_excluded: 분석 제외 여부 (기본값: False)
            created_at: 생성 시간 (선택)
            updated_at: 업데이트 시간 (선택)
            id: 데이터베이스 ID (선택)
        """
        self.id = id
        self.transaction_id = transaction_id
        self.transaction_date = transaction_date
        self.description = description
        self.amount = amount
        self.transaction_type = transaction_type
        self.category = category
        self.payment_method = payment_method
        self.source = source
        self.account_type = account_type
        self.memo = memo
        self.is_excluded = is_excluded
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        
        # 객체 생성 시 유효성 검사 수행
        self.validate()
    
    def validate(self) -> None:
        """
        거래 데이터 유효성 검사
        
        Raises:
            ValueError: 유효하지 않은 데이터가 있을 경우
        """
        # 필수 필드 검사
        if not self.transaction_id:
            raise ValueError("거래 ID는 필수 항목입니다")
        
        if not self.transaction_date:
            raise ValueError("거래 날짜는 필수 항목입니다")
        
        if not self.description:
            raise ValueError("거래 설명은 필수 항목입니다")
        
        if self.amount is None:
            raise ValueError("거래 금액은 필수 항목입니다")
        
        if not self.source:
            raise ValueError("데이터 소스는 필수 항목입니다")
        
        # 거래 유형 검사
        if self.transaction_type not in self.VALID_TRANSACTION_TYPES:
            raise ValueError(f"유효하지 않은 거래 유형입니다: {self.transaction_type}. "
                            f"유효한 값: {', '.join(self.VALID_TRANSACTION_TYPES)}")
        
        # 금액 검사
        if not isinstance(self.amount, Decimal):
            try:
                self.amount = Decimal(str(self.amount))
            except (ValueError, TypeError):
                raise ValueError(f"유효하지 않은 금액 형식입니다: {self.amount}")
        
        # 거래 ID 형식 검사 (영숫자, 하이픈, 언더스코어만 허용)
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.transaction_id):
            raise ValueError(f"유효하지 않은 거래 ID 형식입니다: {self.transaction_id}")
    
    def update_category(self, category: str) -> None:
        """
        거래 카테고리 업데이트
        
        Args:
            category: 새 카테고리
        """
        self.category = category
        self.updated_at = datetime.now()
    
    def update_payment_method(self, payment_method: str) -> None:
        """
        결제 방식 업데이트
        
        Args:
            payment_method: 새 결제 방식
        """
        self.payment_method = payment_method
        self.updated_at = datetime.now()
    
    def exclude_from_analysis(self, exclude: bool = True) -> None:
        """
        분석 제외 여부 설정
        
        Args:
            exclude: 제외 여부 (기본값: True)
        """
        self.is_excluded = exclude
        self.updated_at = datetime.now()
    
    def update_memo(self, memo: str) -> None:
        """
        메모 업데이트
        
        Args:
            memo: 새 메모
        """
        self.memo = memo
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        거래 객체를 딕셔너리로 변환
        
        Returns:
            Dict[str, Any]: 거래 정보를 담은 딕셔너리
        """
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'transaction_date': self.transaction_date.isoformat(),
            'description': self.description,
            'amount': str(self.amount),
            'transaction_type': self.transaction_type,
            'category': self.category,
            'payment_method': self.payment_method,
            'source': self.source,
            'account_type': self.account_type,
            'memo': self.memo,
            'is_excluded': self.is_excluded,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """
        딕셔너리에서 거래 객체 생성
        
        Args:
            data: 거래 정보를 담은 딕셔너리
            
        Returns:
            Transaction: 생성된 거래 객체
        """
        # 날짜 문자열을 date 객체로 변환
        if isinstance(data.get('transaction_date'), str):
            data['transaction_date'] = date.fromisoformat(data['transaction_date'])
        
        # 금액을 Decimal로 변환
        if 'amount' in data and not isinstance(data['amount'], Decimal):
            data['amount'] = Decimal(str(data['amount']))
        
        # 생성 시간과 업데이트 시간 처리
        for dt_field in ['created_at', 'updated_at']:
            if dt_field in data and isinstance(data[dt_field], str):
                data[dt_field] = datetime.fromisoformat(data[dt_field])
        
        return cls(**data)
    
    def __str__(self) -> str:
        """
        거래 객체의 문자열 표현
        
        Returns:
            str: 거래 정보 문자열
        """
        return (f"거래: {self.description} | "
                f"날짜: {self.transaction_date} | "
                f"금액: {self.amount} | "
                f"유형: {self.transaction_type} | "
                f"카테고리: {self.category or '미분류'}")
    
    def __repr__(self) -> str:
        """
        거래 객체의 개발자용 표현
        
        Returns:
            str: 개발자용 표현 문자열
        """
        return (f"Transaction(id={self.id}, "
                f"transaction_id='{self.transaction_id}', "
                f"transaction_date={self.transaction_date}, "
                f"amount={self.amount}, "
                f"type={self.transaction_type})")
