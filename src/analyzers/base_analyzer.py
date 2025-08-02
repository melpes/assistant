# -*- coding: utf-8 -*-
"""
기본 분석기 추상 클래스

모든 분석기 클래스의 기본 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union

from src.repositories.transaction_repository import TransactionRepository


class BaseAnalyzer(ABC):
    """
    기본 분석기 추상 클래스
    
    모든 분석기 클래스의 기본 인터페이스를 정의합니다.
    """
    
    def __init__(self, transaction_repository: TransactionRepository):
        """
        분석기 초기화
        
        Args:
            transaction_repository: 거래 저장소
        """
        self.repository = transaction_repository
    
    @abstractmethod
    def analyze(self, start_date: date, end_date: date, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        지정된 기간의 데이터를 분석합니다.
        
        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            filters: 추가 필터 조건 (선택)
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        pass
    
    def get_date_range(self, period_days: int = 30) -> Tuple[date, date]:
        """
        현재 날짜를 기준으로 기간을 계산합니다.
        
        Args:
            period_days: 기간 (일)
            
        Returns:
            Tuple[date, date]: (시작 날짜, 종료 날짜)
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period_days)
        return start_date, end_date
    
    def get_month_range(self, year: int, month: int) -> Tuple[date, date]:
        """
        특정 연월의 시작일과 종료일을 계산합니다.
        
        Args:
            year: 연도
            month: 월
            
        Returns:
            Tuple[date, date]: (시작 날짜, 종료 날짜)
        """
        start_date = date(year, month, 1)
        
        # 다음 달의 첫날에서 하루를 빼서 이번 달의 마지막 날을 구함
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
            
        return start_date, end_date
    
    def format_amount(self, amount: Union[int, float]) -> str:
        """
        금액을 포맷팅합니다.
        
        Args:
            amount: 금액
            
        Returns:
            str: 포맷팅된 금액 문자열
        """
        return f"{amount:,}원"
    
    def calculate_percentage(self, part: Union[int, float], total: Union[int, float]) -> float:
        """
        백분율을 계산합니다.
        
        Args:
            part: 부분 값
            total: 전체 값
            
        Returns:
            float: 백분율 (0-100)
        """
        if total == 0:
            return 0.0
        return (part / total) * 100