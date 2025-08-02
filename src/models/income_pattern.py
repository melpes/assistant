# -*- coding: utf-8 -*-
"""
수입 패턴(IncomePattern) 엔티티 클래스

수입 거래의 패턴과 정기성을 분석하고 저장합니다.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List
import json


class IncomePattern:
    """
    수입 패턴 엔티티 클래스
    
    수입 거래의 패턴과 정기성을 분석하고 저장합니다.
    """
    
    # 패턴 유형 상수
    TYPE_REGULAR = "regular"
    TYPE_SEASONAL = "seasonal"
    TYPE_OCCASIONAL = "occasional"
    
    # 주기 유형 상수
    PERIOD_DAILY = "daily"
    PERIOD_WEEKLY = "weekly"
    PERIOD_BIWEEKLY = "biweekly"
    PERIOD_MONTHLY = "monthly"
    PERIOD_QUARTERLY = "quarterly"
    PERIOD_YEARLY = "yearly"
    PERIOD_CUSTOM = "custom"
    
    # 유효한 패턴 유형 목록
    VALID_PATTERN_TYPES = [TYPE_REGULAR, TYPE_SEASONAL, TYPE_OCCASIONAL]
    
    # 유효한 주기 유형 목록
    VALID_PERIOD_TYPES = [PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_BIWEEKLY, 
                         PERIOD_MONTHLY, PERIOD_QUARTERLY, PERIOD_YEARLY, PERIOD_CUSTOM]
    
    def __init__(
        self,
        pattern_name: str,
        pattern_type: str,
        description: str,
        category: str,
        period_type: str,
        period_days: int,
        average_amount: Decimal,
        amount_variance: float,
        occurrence_count: int,
        last_occurrence_date: date,
        next_expected_date: date,
        confidence_score: float,
        transaction_ids: List[str],
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        id: Optional[int] = None
    ):
        """
        수입 패턴 객체 초기화
        
        Args:
            pattern_name: 패턴 이름
            pattern_type: 패턴 유형 (regular/seasonal/occasional)
            description: 패턴 설명
            category: 수입 카테고리
            period_type: 주기 유형 (daily/weekly/biweekly/monthly/quarterly/yearly/custom)
            period_days: 주기 일수
            average_amount: 평균 금액
            amount_variance: 금액 변동성 (표준편차/평균)
            occurrence_count: 발생 횟수
            last_occurrence_date: 마지막 발생 날짜
            next_expected_date: 다음 예상 날짜
            confidence_score: 신뢰도 점수 (0.0 ~ 1.0)
            transaction_ids: 관련 거래 ID 목록
            is_active: 활성화 여부 (기본값: True)
            created_at: 생성 시간 (선택)
            updated_at: 업데이트 시간 (선택)
            id: 데이터베이스 ID (선택)
        """
        self.id = id
        self.pattern_name = pattern_name
        self.pattern_type = pattern_type
        self.description = description
        self.category = category
        self.period_type = period_type
        self.period_days = period_days
        self.average_amount = average_amount
        self.amount_variance = amount_variance
        self.occurrence_count = occurrence_count
        self.last_occurrence_date = last_occurrence_date
        self.next_expected_date = next_expected_date
        self.confidence_score = confidence_score
        self.transaction_ids = transaction_ids
        self.is_active = is_active
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        
        # 객체 생성 시 유효성 검사 수행
        self.validate()
    
    def validate(self) -> None:
        """
        패턴 데이터 유효성 검사
        
        Raises:
            ValueError: 유효하지 않은 데이터가 있을 경우
        """
        # 필수 필드 검사
        if not self.pattern_name:
            raise ValueError("패턴 이름은 필수 항목입니다")
        
        if not self.pattern_type:
            raise ValueError("패턴 유형은 필수 항목입니다")
        
        if not self.period_type:
            raise ValueError("주기 유형은 필수 항목입니다")
        
        if self.period_days < 0:
            raise ValueError("주기 일수는 0 이상이어야 합니다")
        
        if self.occurrence_count < 0:
            raise ValueError("발생 횟수는 0 이상이어야 합니다")
        
        if self.confidence_score < 0 or self.confidence_score > 1:
            raise ValueError("신뢰도 점수는 0.0에서 1.0 사이여야 합니다")
        
        # 패턴 유형 검사
        if self.pattern_type not in self.VALID_PATTERN_TYPES:
            raise ValueError(f"유효하지 않은 패턴 유형입니다: {self.pattern_type}. "
                            f"유효한 값: {', '.join(self.VALID_PATTERN_TYPES)}")
        
        # 주기 유형 검사
        if self.period_type not in self.VALID_PERIOD_TYPES:
            raise ValueError(f"유효하지 않은 주기 유형입니다: {self.period_type}. "
                            f"유효한 값: {', '.join(self.VALID_PERIOD_TYPES)}")
    
    def update_occurrence(self, transaction_date: date, amount: Decimal, transaction_id: str) -> None:
        """
        새로운 거래 발생을 기록하여 패턴을 업데이트합니다.
        
        Args:
            transaction_date: 거래 날짜
            amount: 거래 금액
            transaction_id: 거래 ID
        """
        # 거래 ID 추가
        if transaction_id not in self.transaction_ids:
            self.transaction_ids.append(transaction_id)
        
        # 발생 횟수 증가
        self.occurrence_count += 1
        
        # 마지막 발생 날짜 업데이트
        if transaction_date > self.last_occurrence_date:
            self.last_occurrence_date = transaction_date
        
        # 평균 금액 업데이트
        old_total = self.average_amount * (self.occurrence_count - 1)
        new_total = old_total + amount
        self.average_amount = new_total / self.occurrence_count
        
        # 다음 예상 날짜 업데이트
        self.next_expected_date = self.last_occurrence_date + timedelta(days=self.period_days)
        
        # 업데이트 시간 갱신
        self.updated_at = datetime.now()
    
    def calculate_confidence(self) -> float:
        """
        패턴의 신뢰도 점수를 계산합니다.
        
        Returns:
            float: 신뢰도 점수 (0.0 ~ 1.0)
        """
        # 기본 신뢰도 (발생 횟수 기반)
        base_confidence = min(self.occurrence_count / 10, 0.5)
        
        # 금액 변동성 기반 신뢰도 (변동성이 낮을수록 높은 신뢰도)
        variance_confidence = max(0, 0.3 - self.amount_variance * 3)
        
        # 주기 유형 기반 신뢰도
        period_confidence = 0.0
        if self.period_type in [self.PERIOD_MONTHLY, self.PERIOD_BIWEEKLY]:
            period_confidence = 0.2  # 월간, 격주 주기는 높은 신뢰도
        elif self.period_type in [self.PERIOD_WEEKLY, self.PERIOD_QUARTERLY]:
            period_confidence = 0.15  # 주간, 분기 주기는 중간 신뢰도
        elif self.period_type == self.PERIOD_YEARLY:
            period_confidence = 0.1  # 연간 주기는 낮은 신뢰도
        
        # 총 신뢰도 계산
        confidence = base_confidence + variance_confidence + period_confidence
        
        # 신뢰도 범위 제한
        confidence = max(0.0, min(1.0, confidence))
        
        self.confidence_score = confidence
        return confidence
    
    def is_match(self, transaction: Dict[str, Any], tolerance_days: int = 3) -> bool:
        """
        거래가 이 패턴과 일치하는지 확인합니다.
        
        Args:
            transaction: 확인할 거래 데이터
            tolerance_days: 날짜 허용 오차 (일)
            
        Returns:
            bool: 패턴 일치 여부
        """
        # 카테고리 확인
        if transaction.get('category') != self.category:
            return False
        
        # 금액 확인 (평균의 ±30% 이내)
        amount = Decimal(str(transaction.get('amount', 0)))
        amount_min = self.average_amount * Decimal('0.7')
        amount_max = self.average_amount * Decimal('1.3')
        
        if not (amount_min <= amount <= amount_max):
            return False
        
        # 날짜 확인 (예상 날짜 ±허용 오차 이내)
        transaction_date = transaction.get('transaction_date')
        if isinstance(transaction_date, str):
            transaction_date = date.fromisoformat(transaction_date)
        
        # 다음 예상 날짜와의 차이 계산
        date_diff = abs((transaction_date - self.next_expected_date).days)
        
        return date_diff <= tolerance_days
    
    def to_dict(self) -> Dict[str, Any]:
        """
        패턴 객체를 딕셔너리로 변환
        
        Returns:
            Dict[str, Any]: 패턴 정보를 담은 딕셔너리
        """
        return {
            'id': self.id,
            'pattern_name': self.pattern_name,
            'pattern_type': self.pattern_type,
            'description': self.description,
            'category': self.category,
            'period_type': self.period_type,
            'period_days': self.period_days,
            'average_amount': str(self.average_amount),
            'amount_variance': self.amount_variance,
            'occurrence_count': self.occurrence_count,
            'last_occurrence_date': self.last_occurrence_date.isoformat(),
            'next_expected_date': self.next_expected_date.isoformat(),
            'confidence_score': self.confidence_score,
            'transaction_ids': self.transaction_ids,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IncomePattern':
        """
        딕셔너리에서 패턴 객체 생성
        
        Args:
            data: 패턴 정보를 담은 딕셔너리
            
        Returns:
            IncomePattern: 생성된 패턴 객체
        """
        # 날짜 문자열을 date 객체로 변환
        for date_field in ['last_occurrence_date', 'next_expected_date']:
            if isinstance(data.get(date_field), str):
                data[date_field] = date.fromisoformat(data[date_field])
        
        # 생성 시간과 업데이트 시간 처리
        for dt_field in ['created_at', 'updated_at']:
            if dt_field in data and isinstance(data[dt_field], str):
                data[dt_field] = datetime.fromisoformat(data[dt_field])
        
        # 금액을 Decimal로 변환
        if 'average_amount' in data and not isinstance(data['average_amount'], Decimal):
            data['average_amount'] = Decimal(str(data['average_amount']))
        
        # 거래 ID 목록 처리
        if 'transaction_ids' in data and isinstance(data['transaction_ids'], str):
            data['transaction_ids'] = json.loads(data['transaction_ids'])
        
        return cls(**data)
    
    def __str__(self) -> str:
        """
        패턴 객체의 문자열 표현
        
        Returns:
            str: 패턴 정보 문자열
        """
        return (f"패턴: {self.pattern_name} | "
                f"유형: {self.pattern_type} | "
                f"주기: {self.period_type}({self.period_days}일) | "
                f"평균 금액: {self.average_amount} | "
                f"다음 예상: {self.next_expected_date}")
    
    def __repr__(self) -> str:
        """
        패턴 객체의 개발자용 표현
        
        Returns:
            str: 개발자용 표현 문자열
        """
        return (f"IncomePattern(id={self.id}, "
                f"pattern_name='{self.pattern_name}', "
                f"pattern_type='{self.pattern_type}', "
                f"period_type='{self.period_type}', "
                f"confidence={self.confidence_score:.2f})")