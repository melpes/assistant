# -*- coding: utf-8 -*-
"""
학습 패턴(LearningPattern) 모델

사용자 수정사항으로부터 추출된 패턴을 저장하는 모델입니다.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class LearningPattern:
    """
    학습 패턴 모델
    
    사용자 수정사항으로부터 추출된 패턴을 저장합니다.
    """
    
    # 패턴 유형
    TYPE_CATEGORY = 'category'
    TYPE_PAYMENT_METHOD = 'payment_method'
    TYPE_FILTER = 'filter'
    
    # 패턴 신뢰도 수준
    CONFIDENCE_LOW = 'low'
    CONFIDENCE_MEDIUM = 'medium'
    CONFIDENCE_HIGH = 'high'
    
    # 패턴 상태
    STATUS_PENDING = 'pending'
    STATUS_APPLIED = 'applied'
    STATUS_REJECTED = 'rejected'
    
    id: Optional[int] = None
    pattern_type: str = None  # 패턴 유형 (category, payment_method, filter)
    pattern_name: str = None  # 패턴 이름
    pattern_key: str = None   # 패턴 키 (예: 키워드, 상점명)
    pattern_value: str = None  # 패턴 값 (예: 카테고리, 결제 방식)
    confidence: str = CONFIDENCE_MEDIUM  # 패턴 신뢰도
    occurrence_count: int = 1  # 발생 횟수
    last_seen: datetime = None  # 마지막 발견 시간
    status: str = STATUS_PENDING  # 패턴 상태
    metadata: Dict[str, Any] = None  # 추가 메타데이터
    
    def __post_init__(self):
        """
        초기화 후 처리
        """
        if self.last_seen is None:
            self.last_seen = datetime.now()
        
        if self.metadata is None:
            self.metadata = {}
    
    def increment_occurrence(self) -> None:
        """
        발생 횟수를 증가시킵니다.
        """
        self.occurrence_count += 1
        self.last_seen = datetime.now()
        
        # 신뢰도 업데이트
        if self.occurrence_count >= 5:
            self.confidence = self.CONFIDENCE_HIGH
        elif self.occurrence_count >= 2:
            self.confidence = self.CONFIDENCE_MEDIUM
    
    def to_dict(self) -> Dict[str, Any]:
        """
        객체를 딕셔너리로 변환합니다.
        
        Returns:
            Dict[str, Any]: 딕셔너리 표현
        """
        return {
            'id': self.id,
            'pattern_type': self.pattern_type,
            'pattern_name': self.pattern_name,
            'pattern_key': self.pattern_key,
            'pattern_value': self.pattern_value,
            'confidence': self.confidence,
            'occurrence_count': self.occurrence_count,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'status': self.status,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningPattern':
        """
        딕셔너리로부터 객체를 생성합니다.
        
        Args:
            data: 딕셔너리 데이터
            
        Returns:
            LearningPattern: 생성된 객체
        """
        # last_seen을 datetime으로 변환
        if 'last_seen' in data and data['last_seen']:
            if isinstance(data['last_seen'], str):
                data['last_seen'] = datetime.fromisoformat(data['last_seen'])
        
        return cls(**data)