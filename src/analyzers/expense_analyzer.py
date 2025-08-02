# -*- coding: utf-8 -*-
"""
지출 분석기 클래스

지출 거래를 분석하고 다양한 관점의 리포트를 생성합니다.
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


class ExpenseAnalyzer(BaseAnalyzer):
    """
    지출 분석기 클래스
    
    지출 거래를 분석하고 다양한 관점의 리포트를 생성합니다.
    """
    
    def __init__(self, transaction_repository: TransactionRepository):
        """
        지출 분석기 초기화
        
        Args:
            transaction_repository: 거래 저장소
        """
        super().__init__(transaction_repository)
    
    def analyze(self, start_date: date, end_date: date, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        지정된 기간의 지출을 분석합니다.
        
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
        filters['transaction_type'] = Transaction.TYPE_EXPENSE
        
        # 거래 데이터 조회
        transactions = self.repository.list(filters)
        
        if not transactions:
            logger.info(f"분석 기간 내 지출 데이터가 없습니다: {start_date} ~ {end_date}")
            return {
                'total_expense': 0,
                'transaction_count': 0,
                'average_expense': 0,
                'daily_average': 0,
                'monthly_estimate': 0,
                'by_payment_method': [],
                'by_category': [],
                'daily_trend': [],
                'period_days': (end_date - start_date).days + 1
            }
        
        # 데이터프레임 변환
        df = self._transactions_to_dataframe(transactions)
        
        # 분석 수행
        total_expense = df['amount'].sum()
        transaction_count = len(transactions)
        average_expense = total_expense / transaction_count if transaction_count > 0 else 0
        period_days = (end_date - start_date).days + 1
        daily_average = total_expense / period_days if period_days > 0 else 0
        monthly_estimate = daily_average * 30
        
        # 결제 방식별 분석
        by_payment_method = self._analyze_by_payment_method(df, total_expense)
        
        # 카테고리별 분석
        by_category = self._analyze_by_category(df, total_expense)
        
        # 일별 트렌드 분석
        daily_trend = self._analyze_daily_trend(df)
        
        # 결과 반환
        return {
            'total_expense': float(total_expense),
            'transaction_count': transaction_count,
            'average_expense': float(average_expense),
            'daily_average': float(daily_average),
            'monthly_estimate': float(monthly_estimate),
            'by_payment_method': by_payment_method,
            'by_category': by_category,
            'daily_trend': daily_trend,
            'period_days': period_days
        }
    
    def analyze_by_period(self, days: int = 30, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        최근 N일 동안의 지출을 분석합니다.
        
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
        특정 연월의 지출을 분석합니다.
        
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
        특정 카테고리의 지출을 분석합니다.
        
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
    
    def analyze_by_payment_method(self, payment_method: str, start_date: date, end_date: date,
                                filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        특정 결제 방식의 지출을 분석합니다.
        
        Args:
            payment_method: 분석할 결제 방식
            start_date: 시작 날짜
            end_date: 종료 날짜
            filters: 추가 필터 조건 (선택)
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        filters = filters or {}
        filters['payment_method'] = payment_method
        return self.analyze(start_date, end_date, filters)
    
    def find_regular_expenses(self, min_frequency: int = 2) -> List[Dict[str, Any]]:
        """
        정기적인 지출 패턴을 찾습니다.
        
        Args:
            min_frequency: 최소 발생 빈도
            
        Returns:
            List[Dict[str, Any]]: 정기 지출 목록
        """
        # 전체 지출 데이터 조회
        filters = {'transaction_type': Transaction.TYPE_EXPENSE}
        transactions = self.repository.list(filters)
        
        if not transactions:
            return []
        
        # 데이터프레임 변환
        df = self._transactions_to_dataframe(transactions)
        
        # 정기 지출 패턴 분석
        regular_expenses = []
        
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
                
                regular_expenses.append({
                    'description': desc,
                    'amount': float(amount),
                    'frequency': len(group),
                    'first_date': dates[0].isoformat(),
                    'last_date': dates[-1].isoformat(),
                    'avg_interval_days': round(avg_interval, 1),
                    'category': group['category'].iloc[0],
                    'payment_method': group['payment_method'].iloc[0]
                })
        
        # 빈도 기준 정렬
        regular_expenses.sort(key=lambda x: x['frequency'], reverse=True)
        
        return regular_expenses
    
    def find_missing_expenses(self) -> List[Dict[str, Any]]:
        """
        누락 가능성이 있는 지출을 찾습니다.
        
        Returns:
            List[Dict[str, Any]]: 누락 가능성 있는 지출 목록
        """
        # 정기 지출 패턴 조회
        regular_expenses = self.find_regular_expenses(min_frequency=2)
        
        # 현재 날짜
        today = datetime.now().date()
        
        # 누락 가능성 있는 지출 필터링
        missing_expenses = []
        
        for expense in regular_expenses:
            last_date = date.fromisoformat(expense['last_date'])
            avg_interval = expense['avg_interval_days']
            
            # 평균 간격의 1.5배 이상 지났으면 누락 가능성 있음
            days_since_last = (today - last_date).days
            if days_since_last > avg_interval * 1.5:
                expense['days_since_last'] = days_since_last
                expense['expected_date'] = (last_date + timedelta(days=int(avg_interval))).isoformat()
                expense['days_overdue'] = days_since_last - int(avg_interval)
                missing_expenses.append(expense)
        
        # 지연일 기준 정렬
        missing_expenses.sort(key=lambda x: x['days_overdue'], reverse=True)
        
        return missing_expenses
    
    def get_expense_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        지출 요약 정보를 반환합니다.
        
        Args:
            days: 분석 기간 (일)
            
        Returns:
            Dict[str, Any]: 지출 요약 정보
        """
        # 분석 수행
        result = self.analyze_by_period(days)
        
        # 요약 정보 구성
        summary = {
            'period': f"최근 {days}일",
            'start_date': (datetime.now().date() - timedelta(days=days)).isoformat(),
            'end_date': datetime.now().date().isoformat(),
            'total_expense': self.format_amount(result['total_expense']),
            'transaction_count': result['transaction_count'],
            'daily_average': self.format_amount(result['daily_average']),
            'monthly_estimate': self.format_amount(result['monthly_estimate']),
            'top_categories': result['by_category'][:5],
            'top_payment_methods': result['by_payment_method'][:3]
        }
        
        return summary
    
    def print_expense_report(self, days: int = 30) -> None:
        """
        지출 리포트를 콘솔에 출력합니다.
        
        Args:
            days: 분석 기간 (일)
        """
        # 분석 수행
        result = self.analyze_by_period(days)
        
        # 리포트 출력
        print(f"\n=== 최근 {days}일 지출 분석 리포트 ===")
        print(f"분석 기간: {(datetime.now().date() - timedelta(days=days)).isoformat()} ~ {datetime.now().date().isoformat()}")
        
        if result['transaction_count'] == 0:
            print("해당 기간에 지출 데이터가 없습니다.")
            return
        
        # 1. 전체 지출 현황
        print("\n[전체 지출 현황]")
        print("-" * 60)
        print(f"총 지출: {self.format_amount(result['total_expense'])}")
        print(f"거래 건수: {result['transaction_count']}건")
        print(f"평균 거래 금액: {self.format_amount(result['average_expense'])}")
        print(f"일평균 지출: {self.format_amount(result['daily_average'])}")
        print(f"월 예상 지출: {self.format_amount(result['monthly_estimate'])}")
        
        # 2. 결제 방식별 지출 현황
        print("\n[결제 방식별 지출 현황]")
        print("-" * 60)
        for item in result['by_payment_method']:
            print(f"{item['payment_method']:15} | {self.format_amount(item['amount']):>12} ({item['percentage']:5.1f}%) | {item['count']:3}건")
        
        # 3. 카테고리별 지출 현황 (상위 10개)
        print("\n[카테고리별 지출 현황 (상위 10개)]")
        print("-" * 60)
        for item in result['by_category'][:10]:
            print(f"{item['category']:15} | {self.format_amount(item['amount']):>12} ({item['percentage']:5.1f}%) | {item['count']:3}건")
        
        # 4. 최근 5일 일별 지출
        print("\n[최근 5일 일별 지출]")
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
                'payment_method': tx.payment_method or '기타',
                'source': tx.source,
                'account_type': tx.account_type
            })
        
        return pd.DataFrame(data)
    
    def _analyze_by_payment_method(self, df: pd.DataFrame, total_expense: Decimal) -> List[Dict[str, Any]]:
        """
        결제 방식별 분석을 수행합니다.
        
        Args:
            df: 거래 데이터프레임
            total_expense: 총 지출액
            
        Returns:
            List[Dict[str, Any]]: 결제 방식별 분석 결과
        """
        if df.empty:
            return []
        
        # 결제 방식별 그룹화
        grouped = df.groupby('payment_method').agg({
            'amount': ['sum', 'count', 'mean'],
            'id': 'count'
        })
        
        # 결과 포맷팅
        result = []
        for payment_method, data in grouped.iterrows():
            amount = data[('amount', 'sum')]
            percentage = self.calculate_percentage(amount, total_expense)
            
            result.append({
                'payment_method': payment_method,
                'amount': float(amount),
                'count': int(data[('id', 'count')]),
                'average': float(data[('amount', 'mean')]),
                'percentage': percentage
            })
        
        # 금액 기준 정렬
        result.sort(key=lambda x: x['amount'], reverse=True)
        
        return result
    
    def _analyze_by_category(self, df: pd.DataFrame, total_expense: Decimal) -> List[Dict[str, Any]]:
        """
        카테고리별 분석을 수행합니다.
        
        Args:
            df: 거래 데이터프레임
            total_expense: 총 지출액
            
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
            percentage = self.calculate_percentage(amount, total_expense)
            
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