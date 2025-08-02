# -*- coding: utf-8 -*-
"""
분류 규칙 모델

거래 내역 자동 분류를 위한 규칙 모델을 정의합니다.
"""

from datetime import datetime
from typing import Optional

class ClassificationRule:
    """
    분류 규칙 클래스
    
    거래 내역 자동 분류를 위한 규칙을 정의합니다.
    """
    
    # 규칙 유형 상수
    RULE_TYPE_CATEGORY = "category"
    RULE_TYPE_PAYMENT_METHOD = "payment_method"
    RULE_TYPE_FILTER = "filter"
    
    # 조건 유형 상수
    CONDITION_CONTAINS = "contains"
    CONDITION_EQUALS = "equals"
    CONDITION_REGEX = "regex"
    CONDITION_AMOUNT_RANGE = "amount_range"
    
    def __init__(
        self,
        rule_name: str,
        rule_type: str,
        condition_type: str,
        condition_value: str,
        target_value: str,
        priority: int = 0,
        is_active: bool = True,
        created_by: str = "system",
        id: Optional[int] = None,
        created_at: Optional[datetime] = None
    ):
        """
        분류 규칙 초기화
        
        Args:
            rule_name: 규칙 이름
            rule_type: 규칙 유형 (category/payment_method/filter)
            condition_type: 조건 유형 (contains/equals/regex/amount_range)
            condition_value: 조건 값
            target_value: 분류 결과 값
            priority: 우선순위 (높을수록 먼저 적용)
            is_active: 활성화 여부
            created_by: 생성자
            id: 규칙 ID (DB에서 할당)
            created_at: 생성 시간
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
    
    def update_priority(self, priority: int) -> None:
        """
        우선순위를 업데이트합니다.
        
        Args:
            priority: 새 우선순위
        """
        self.priority = priority
    
    def activate(self) -> None:
        """규칙을 활성화합니다."""
        self.is_active = True
    
    def deactivate(self) -> None:
        """규칙을 비활성화합니다."""
        self.is_active = False
    
    def to_dict(self) -> dict:
        """
        규칙을 딕셔너리로 변환합니다.
        
        Returns:
            dict: 규칙 정보 딕셔너리
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
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ClassificationRule':
        """
        딕셔너리에서 규칙 객체를 생성합니다.
        
        Args:
            data: 규칙 정보 딕셔너리
            
        Returns:
            ClassificationRule: 생성된 규칙 객체
        """
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return cls(
            id=data.get('id'),
            rule_name=data['rule_name'],
            rule_type=data['rule_type'],
            condition_type=data['condition_type'],
            condition_value=data['condition_value'],
            target_value=data['target_value'],
            priority=data.get('priority', 0),
            is_active=data.get('is_active', True),
            created_by=data.get('created_by', 'system'),
            created_at=created_at
        )
    
    def __str__(self) -> str:
        """
        규칙의 문자열 표현을 반환합니다.
        
        Returns:
            str: 규칙 문자열
        """
        return f"Rule({self.id}): {self.rule_name} - {self.condition_type}({self.condition_value}) -> {self.target_value}"
    
    def __repr__(self) -> str:
        """
        규칙의 개발자용 문자열 표현을 반환합니다.
        
        Returns:
            str: 규칙 표현 문자열
        """
        return (f"ClassificationRule(id={self.id}, rule_name='{self.rule_name}', "
                f"rule_type='{self.rule_type}', condition_type='{self.condition_type}', "
                f"condition_value='{self.condition_value}', target_value='{self.target_value}', "
                f"priority={self.priority}, is_active={self.is_active})")