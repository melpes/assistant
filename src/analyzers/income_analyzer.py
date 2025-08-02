# -*- coding: utf-8 -*-
"""
수입 분석기 클래스

수입 거래를 분석하고 다양한 관점의 리포트를 생성합니다.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple, Union

import pandas as pd

from src.models import Transaction
from src.repositories.transaction_repository import TransactionRepository
from src.analyzers.base_analyzer import BaseAnalyzer

# 로거 설정
logger = logging.getLogger(__name__)


class IncomeAnalyzer(BaseAnalyzer):
    """
    수입 분석기 클래스
    
    수입 거래를 분석하고 다양한 관점의 리포트를 생성합니다.
    """
    
    def __init__(self, transaction_repository: TransactionRepository):
        """
        수입 분석기 초기화
        
        Args:
            transaction_repository: 거래 저장소
        """
        super().__init__(transaction_repository)
    
    def analyze(self, start_date: date, end_date: date, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        지정된 기간의 수입을 분석합니다.
        
        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            filters: 추가 필터 조건 (선택)
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        # 기본 필터 설정
        filters = filters or {}
        filters['start_date'] = start_date
        filters['end_date'] = end_date
        filters['transaction_type'] = Transaction.TYPE_INCOME
        
        # 거래 데이터 조회
        transactions = self.repository.list(filters)
        
        if not transactions:
            logger.info(f"분석 기간 내 수입 데이터가 없습니다: {start_date} ~ {end_date}")
            return {
                'total_income': 0,
                'transaction_count': 0,
                'average_income': 0,
                'daily_average': 0,
                'monthly_estimate': 0,
                'by_category': [],
                'by_source': [],
                'daily_trend': [],
                'period_days': (end_date - start_date).days + 1
            }
        
        # 데이터프레임 변환
        df = self._transactions_to_dataframe(transactions)
        
        # 분석 수행
        total_income = df['amount'].sum()
        transaction_count = len(transactions)
        average_income = total_income / transaction_count if transaction_count > 0 else 0
        period_days = (end_date - start_date).days + 1
        daily_average = total_income / period_days if period_days > 0 else 0
        monthly_estimate = daily_average * 30
        
        # 카테고리별 분석 (수입 유형별)
        by_category = self._analyze_by_category(df, total_income)
        
        # 소스별 분석 (수입 출처별)
        by_source = self._analyze_by_source(df, total_income)
        
        # 일별 트렌드 분석
        daily_trend = self._analyze_daily_trend(df)
        
        # 결과 반환
        return {
            'total_income': float(total_income),
            'transaction_count': transaction_count,
            'average_income': float(average_income),
            'daily_average': float(daily_average),
            'monthly_estimate': float(monthly_estimate),
            'by_category': by_category,
            'by_source': by_source,
            'daily_trend': daily_trend,
            'period_days': period_days
        }
    
    def analyze_by_period(self, days: int = 30, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        최근 N일 동안의 수입을 분석합니다.
        
        Args:
            days: 분석 기간 (일)
            filters: 추가 필터 조건 (선택)
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        start_date, end_date = self.get_date_range(days)
        return self.analyze(start_date, end_date, filters)
    
    def analyze_by_month(self, year: int, month: int, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        특정 연월의 수입을 분석합니다.
        
        Args:
            year: 연도
            month: 월
            filters: 추가 필터 조건 (선택)
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        start_date, end_date = self.get_month_range(year, month)
        return self.analyze(start_date, end_date, filters)
    
    def analyze_by_category(self, category: str, start_date: date, end_date: date, 
                           filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        특정 카테고리(수입 유형)의 수입을 분석합니다.
        
        Args:
            category: 분석할 카테고리
            start_date: 시작 날짜
            end_date: 종료 날짜
            filters: 추가 필터 조건 (선택)
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        filters = filters or {}
        filters['category'] = category
        return self.analyze(start_date, end_date, filters)
    
    def find_regular_income(self, min_frequency: int = 2) -> List[Dict[str, Any]]:
        """
        정기적인 수입 패턴을 찾습니다.
        
        Args:
            min_frequency: 최소 발생 빈도
            
        Returns:
            List[Dict[str, Any]]: 정기 수입 목록
        """
        # 전체 수입 데이터 조회
        filters = {'transaction_type': Transaction.TYPE_INCOME}
        transactions = self.repository.list(filters)
        
        if not transactions:
            return []
        
        # 데이터프레임 변환
        df = self._transactions_to_dataframe(transactions)
        
        # 정기 수입 패턴 분석
        regular_income = []
        
        # 설명과 금액이 동일한 거래 그룹화
        grouped = df.groupby(['description', 'amount'])
        
        for (desc, amount), group in grouped:
            if len(group) >= min_frequency:
                # 날짜 정렬
                dates = sorted(group['transaction_date'].tolist())
                
                # 간격 계산
                intervals = []
                for i in range(1, len(dates)):
                    intervals.append((dates[i] - dates[i-1]).days)
                
                # 평균 간격 및 표준 편차
                avg_interval = sum(intervals) / len(intervals) if intervals else 0
                
                regular_income.append({
                    'description': desc,
                    'amount': float(amount),
                    'frequency': len(group),
                    'first_date': dates[0].isoformat(),
                    'last_date': dates[-1].isoformat(),
                    'avg_interval_days': round(avg_interval, 1),
                    'category': group['category'].iloc[0],
                    'source': group['source'].iloc[0]
                })
        
        # 빈도 기준 정렬
        regular_income.sort(key=lambda x: x['frequency'], reverse=True)
        
        return regular_income
    
    def get_income_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        수입 요약 정보를 반환합니다.
        
        Args:
            days: 분석 기간 (일)
            
        Returns:
            Dict[str, Any]: 수입 요약 정보
        """
        # 분석 수행
        result = self.analyze_by_period(days)
        
        # 요약 정보 구성
        summary = {
            'period': f"최근 {days}일",
            'start_date': (datetime.now().date() - timedelta(days=days)).isoformat(),
            'end_date': datetime.now().date().isoformat(),
            'total_income': self.format_amount(result['total_income']),
            'transaction_count': result['transaction_count'],
            'daily_average': self.format_amount(result['daily_average']),
            'monthly_estimate': self.format_amount(result['monthly_estimate']),
            'top_categories': result['by_category'][:5],
            'top_sources': result['by_source'][:3]
        }
        
        return summary
    
    def print_income_report(self, days: int = 30) -> None:
        """
        수입 리포트를 콘솔에 출력합니다.
        
        Args:
            days: 분석 기간 (일)
        """
        # 분석 수행
        result = self.analyze_by_period(days)
        
        # 리포트 출력
        print(f"\n=== 최근 {days}일 수입 분석 리포트 ===")
        print(f"분석 기간: {(datetime.now().date() - timedelta(days=days)).isoformat()} ~ {datetime.now().date().isoformat()}")
        
        if result['transaction_count'] == 0:
            print("해당 기간에 수입 데이터가 없습니다.")
            return
        
        # 1. 전체 수입 현황
        print("\n[전체 수입 현황]")
        print("-" * 60)
        print(f"총 수입: {self.format_amount(result['total_income'])}")
        print(f"거래 건수: {result['transaction_count']}건")
        print(f"평균 거래 금액: {self.format_amount(result['average_income'])}")
        print(f"일평균 수입: {self.format_amount(result['daily_average'])}")
        print(f"월 예상 수입: {self.format_amount(result['monthly_estimate'])}")
        
        # 2. 수입 유형별 현황
        print("\n[수입 유형별 현황]")
        print("-" * 60)
        for item in result['by_category']:
            print(f"{item['category']:15} | {self.format_amount(item['amount']):>12} ({item['percentage']:5.1f}%) | {item['count']:3}건")
        
        # 3. 수입 출처별 현황
        print("\n[수입 출처별 현황]")
        print("-" * 60)
        for item in result['by_source']:
            print(f"{item['source']:15} | {self.format_amount(item['amount']):>12} ({item['percentage']:5.1f}%) | {item['count']:3}건")
        
        # 4. 최근 5일 일별 수입
        print("\n[최근 5일 일별 수입]")
        print("-" * 40)
        for item in result['daily_trend'][-5:]:
            print(f"{item['date']} | {self.format_amount(item['amount'])}")
    
    def _transactions_to_dataframe(self, transactions: List[Transaction]) -> pd.DataFrame:
        """
        거래 목록을 데이터프레임으로 변환합니다.
        
        Args:
            transactions: 거래 목록
            
        Returns:
            pd.DataFrame: 변환된 데이터프레임
        """
        data = []
        for tx in transactions:
            data.append({
                'id': tx.id,
                'transaction_id': tx.transaction_id,
                'transaction_date': tx.transaction_date,
                'description': tx.description,
                'amount': tx.amount,
                'category': tx.category or '미분류',
                'source': tx.source,
                'account_type': tx.account_type
            })
        
        return pd.DataFrame(data)
    
    def _analyze_by_category(self, df: pd.DataFrame, total_income: Decimal) -> List[Dict[str, Any]]:
        """
        카테고리별(수입 유형별) 분석을 수행합니다.
        
        Args:
            df: 거래 데이터프레임
            total_income: 총 수입액
            
        Returns:
            List[Dict[str, Any]]: 카테고리별 분석 결과
        """
        if df.empty:
            return []
        
        # 카테고리별 그룹화
        grouped = df.groupby('category').agg({
            'amount': ['sum', 'count', 'mean'],
            'id': 'count'
        })
        
        # 결과 포맷팅
        result = []
        for category, data in grouped.iterrows():
            amount = data[('amount', 'sum')]
            percentage = self.calculate_percentage(amount, total_income)
            
            result.append({
                'category': category,
                'amount': float(amount),
                'count': int(data[('id', 'count')]),
                'average': float(data[('amount', 'mean')]),
                'percentage': percentage
            })
        
        # 금액 기준 정렬
        result.sort(key=lambda x: x['amount'], reverse=True)
        
        return result
    
    def _analyze_by_source(self, df: pd.DataFrame, total_income: Decimal) -> List[Dict[str, Any]]:
        """
        소스별(수입 출처별) 분석을 수행합니다.
        
        Args:
            df: 거래 데이터프레임
            total_income: 총 수입액
            
        Returns:
            List[Dict[str, Any]]: 소스별 분석 결과
        """
        if df.empty:
            return []
        
        # 소스별 그룹화
        grouped = df.groupby('source').agg({
            'amount': ['sum', 'count', 'mean'],
            'id': 'count'
        })
        
        # 결과 포맷팅
        result = []
        for source, data in grouped.iterrows():
            amount = data[('amount', 'sum')]
            percentage = self.calculate_percentage(amount, total_income)
            
            result.append({
                'source': source,
                'amount': float(amount),
                'count': int(data[('id', 'count')]),
                'average': float(data[('amount', 'mean')]),
                'percentage': percentage
            })
        
        # 금액 기준 정렬
        result.sort(key=lambda x: x['amount'], reverse=True)
        
        return result
    
    def _analyze_daily_trend(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        일별 트렌드 분석을 수행합니다.
        
        Args:
            df: 거래 데이터프레임
            
        Returns:
            List[Dict[str, Any]]: 일별 트렌드 분석 결과
        """
        if df.empty:
            return []
        
        # 일별 그룹화
        daily = df.groupby('transaction_date').agg({
            'amount': 'sum',
            'id': 'count'
        })
        
        # 결과 포맷팅
        result = []
        for dt, data in daily.iterrows():
            result.append({
                'date': dt.isoformat(),
                'amount': float(data['amount']),
                'count': int(data['id'])
            })
        
        # 날짜 기준 정렬
        result.sort(key=lambda x: x['date'])
        
        return result