# -*- coding: utf-8 -*-
"""
수입 규칙(IncomeRule) 엔티티 클래스

수입 거래 분류 및 제외를 위한 규칙을 정의합니다.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
import re


class IncomeRule:
    """
    수입 규칙 엔티티 클래스
    
    수입 거래 분류 및 제외를 위한 규칙을 정의합니다.
    """
    
    # 규칙 유형 상수
    TYPE_CATEGORY = "category"
    TYPE_PAYMENT_METHOD = "payment_method"
    TYPE_EXCLUDE = "exclude"
    
    # 조건 유형 상수
    CONDITION_CONTAINS = "contains"
    CONDITION_EQUALS = "equals"
    CONDITION_REGEX = "regex"
    CONDITION_AMOUNT_RANGE = "amount_range"
    
    # 유효한 규칙 유형 목록
    VALID_RULE_TYPES = [TYPE_CATEGORY, TYPE_PAYMENT_METHOD, TYPE_EXCLUDE]
    
    # 유효한 조건 유형 목록
    VALID_CONDITION_TYPES = [CONDITION_CONTAINS, CONDITION_EQUALS, CONDITION_REGEX, CONDITION_AMOUNT_RANGE]
    
    def __init__(
        self,
        rule_name: str,
        rule_type: str,
        condition_type: str,
        condition_value: str,
        target_value: str,
        priority: int = 0,
        is_active: bool = True,
        created_by: str = "user",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        id: Optional[int] = None
    ):
        """
        수입 규칙 객체 초기화
        
        Args:
            rule_name: 규칙 이름
            rule_type: 규칙 유형 (category/payment_method/exclude)
            condition_type: 조건 유형 (contains/equals/regex/amount_range)
            condition_value: 조건 값
            target_value: 적용할 값
            priority: 우선순위 (기본값: 0)
            is_active: 활성화 여부 (기본값: True)
            created_by: 생성자 (기본값: "user")
            created_at: 생성 시간 (선택)
            updated_at: 업데이트 시간 (선택)
            id: 데이터베이스 ID (선택)
        """
        self.id = id
        self.rule_name = rule_name
        self.rule_type = rule_type
        self.condition_type = condition_type
        self.condition_value = condition_value
        self.target_value = target_value
        self.priority = priority
        self.is_active = is_active
        self.created_by = created_by
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        
        # 객체 생성 시 유효성 검사 수행
        self.validate()
    
    def validate(self) -> None:
        """
        규칙 데이터 유효성 검사
        
        Raises:
            ValueError: 유효하지 않은 데이터가 있을 경우
        """
        # 필수 필드 검사
        if not self.rule_name:
            raise ValueError("규칙 이름은 필수 항목입니다")
        
        if not self.rule_type:
            raise ValueError("규칙 유형은 필수 항목입니다")
        
        if not self.condition_type:
            raise ValueError("조건 유형은 필수 항목입니다")
        
        if self.condition_value is None or self.condition_value == "":
            raise ValueError("조건 값은 필수 항목입니다")
        
        if self.target_value is None or self.target_value == "":
            raise ValueError("적용 값은 필수 항목입니다")
        
        # 규칙 유형 검사
        if self.rule_type not in self.VALID_RULE_TYPES:
            raise ValueError(f"유효하지 않은 규칙 유형입니다: {self.rule_type}. "
                            f"유효한 값: {', '.join(self.VALID_RULE_TYPES)}")
        
        # 조건 유형 검사
        if self.condition_type not in self.VALID_CONDITION_TYPES:
            raise ValueError(f"유효하지 않은 조건 유형입니다: {self.condition_type}. "
                            f"유효한 값: {', '.join(self.VALID_CONDITION_TYPES)}")
        
        # 금액 범위 형식 검사
        if self.condition_type == self.CONDITION_AMOUNT_RANGE:
            try:
                parts = self.condition_value.split('-')
                if len(parts) != 2:
                    raise ValueError("금액 범위는 'min-max' 형식이어야 합니다")
                
                min_amount, max_amount = map(float, parts)
                if min_amount > max_amount:
                    raise ValueError("최소 금액은 최대 금액보다 작아야 합니다")
            except ValueError as e:
                raise ValueError(f"유효하지 않은 금액 범위 형식입니다: {self.condition_value}. {str(e)}")
        
        # 정규식 형식 검사
        if self.condition_type == self.CONDITION_REGEX:
            try:
                re.compile(self.condition_value)
            except re.error:
                raise ValueError(f"유효하지 않은 정규식 형식입니다: {self.condition_value}")
    
    def matches(self, transaction: Dict[str, Any]) -> bool:
        """
        거래가 규칙 조건과 일치하는지 확인합니다.
        
        Args:
            transaction: 확인할 거래 데이터
            
        Returns:
            bool: 조건 일치 여부
        """
        # 비활성화된 규칙은 항상 불일치
        if not self.is_active:
            return False
        
        # 거래 정보 추출
        description = str(transaction.get('description', '')).lower()
        amount = float(transaction.get('amount', 0))
        memo = str(transaction.get('memo', '')).lower()
        
        # 조건 확인
        if self.condition_type == self.CONDITION_CONTAINS:
            return (self.condition_value.lower() in description or 
                    self.condition_value.lower() in memo)
        
        elif self.condition_type == self.CONDITION_EQUALS:
            return (description == self.condition_value.lower() or 
                    memo == self.condition_value.lower())
        
        elif self.condition_type == self.CONDITION_REGEX:
            return (re.search(self.condition_value, description, re.IGNORECASE) is not None or 
                    re.search(self.condition_value, memo, re.IGNORECASE) is not None)
        
        elif self.condition_type == self.CONDITION_AMOUNT_RANGE:
            try:
                min_amount, max_amount = map(float, self.condition_value.split('-'))
                return min_amount <= amount <= max_amount
            except (ValueError, AttributeError):
                return False
        
        return False
    
    def apply(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        거래에 규칙을 적용합니다.
        
        Args:
            transaction: 적용할 거래 데이터
            
        Returns:
            Dict[str, Any]: 규칙이 적용된 거래 데이터
        """
        # 조건 일치 확인
        if not self.matches(transaction):
            return transaction
        
        # 규칙 적용
        if self.rule_type == self.TYPE_CATEGORY:
            transaction['category'] = self.target_value
        
        elif self.rule_type == self.TYPE_PAYMENT_METHOD:
            transaction['payment_method'] = self.target_value
        
        elif self.rule_type == self.TYPE_EXCLUDE:
            transaction['is_excluded'] = self.target_value.lower() == 'true'
        
        return transaction
    
    def to_dict(self) -> Dict[str, Any]:
        """
        규칙 객체를 딕셔너리로 변환
        
        Returns:
            Dict[str, Any]: 규칙 정보를 담은 딕셔너리
        """
        return {
            'id': self.id,
            'rule_name': self.rule_name,
            'rule_type': self.rule_type,
            'condition_type': self.condition_type,
            'condition_value': self.condition_value,
            'target_value': self.target_value,
            'priority': self.priority,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IncomeRule':
        """
        딕셔너리에서 규칙 객체 생성
        
        Args:
            data: 규칙 정보를 담은 딕셔너리
            
        Returns:
            IncomeRule: 생성된 규칙 객체
        """
        # 생성 시간과 업데이트 시간 처리
        for dt_field in ['created_at', 'updated_at']:
            if dt_field in data and isinstance(data[dt_field], str):
                data[dt_field] = datetime.fromisoformat(data[dt_field])
        
        return cls(**data)
    
    def __str__(self) -> str:
        """
        규칙 객체의 문자열 표현
        
        Returns:
            str: 규칙 정보 문자열
        """
        return (f"규칙: {self.rule_name} | "
                f"유형: {self.rule_type} | "
                f"조건: {self.condition_type}({self.condition_value}) | "
                f"적용값: {self.target_value} | "
                f"우선순위: {self.priority}")
    
    def __repr__(self) -> str:
        """
        규칙 객체의 개발자용 표현
        
        Returns:
            str: 개발자용 표현 문자열
        """
        return (f"IncomeRule(id={self.id}, "
                f"rule_name='{self.rule_name}', "
                f"rule_type='{self.rule_type}', "
                f"condition_type='{self.condition_type}', "
                f"priority={self.priority})")