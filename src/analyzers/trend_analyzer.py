# -*- coding: utf-8 -*-
"""
트렌드 분석기 클래스

시계열 기반의 거래 트렌드를 분석합니다.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple, Union
from calendar import monthrange

import pandas as pd
import numpy as np

from src.models import Transaction
from src.repositories.transaction_repository import TransactionRepository
from src.analyzers.base_analyzer import BaseAnalyzer

# 로거 설정
logger = logging.getLogger(__name__)


class TrendAnalyzer(BaseAnalyzer):
    """
    트렌드 분석기 클래스
    
    시계열 기반의 거래 트렌드를 분석합니다.
    """
    
    def __init__(self, transaction_repository: TransactionRepository):
        """
        트렌드 분석기 초기화
        
        Args:
            transaction_repository: 거래 저장소
        """
        super().__init__(transaction_repository)
    
    def analyze(self, start_date: date, end_date: date, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        지정된 기간의 트렌드를 분석합니다.
        
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
        
        # 거래 데이터 조회
        transactions = self.repository.list(filters)
        
        if not transactions:
            logger.info(f"분석 기간 내 거래 데이터가 없습니다: {start_date} ~ {end_date}")
            return {
                'daily_trend': [],
                'weekly_trend': [],
                'monthly_trend': [],
                'period_days': (end_date - start_date).days + 1
            }
        
        # 데이터프레임 변환
        df = self._transactions_to_dataframe(transactions)
        
        # 일별 트렌드 분석
        daily_trend = self._analyze_daily_trend(df)
        
        # 주별 트렌드 분석
        weekly_trend = self._analyze_weekly_trend(df)
        
        # 월별 트렌드 분석
        monthly_trend = self._analyze_monthly_trend(df)
        
        # 결과 반환
        return {
            'daily_trend': daily_trend,
            'weekly_trend': weekly_trend,
            'monthly_trend': monthly_trend,
            'period_days': (end_date - start_date).days + 1
        }
    
    def analyze_monthly_trends(self, months: int = 6, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        최근 N개월의 월별 트렌드를 분석합니다.
        
        Args:
            months: 분석할 월 수
            filters: 추가 필터 조건 (선택)
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        # 현재 날짜
        today = datetime.now().date()
        
        # N개월 전 날짜 계산
        start_year = today.year
        start_month = today.month - months
        
        # 연도 조정
        while start_month <= 0:
            start_year -= 1
            start_month += 12
        
        start_date = date(start_year, start_month, 1)
        end_date = today
        
        # 분석 수행
        result = self.analyze(start_date, end_date, filters)
        
        # 월별 트렌드만 반환
        return {
            'monthly_trend': result['monthly_trend'],
            'period_months': months
        }
    
    def analyze_category_trends(self, category: str, months: int = 6) -> Dict[str, Any]:
        """
        특정 카테고리의 월별 트렌드를 분석합니다.
        
        Args:
            category: 분석할 카테고리
            months: 분석할 월 수
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        filters = {'category': category}
        return self.analyze_monthly_trends(months, filters)
    
    def analyze_payment_method_trends(self, payment_method: str, months: int = 6) -> Dict[str, Any]:
        """
        특정 결제 방식의 월별 트렌드를 분석합니다.
        
        Args:
            payment_method: 분석할 결제 방식
            months: 분석할 월 수
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        filters = {'payment_method': payment_method}
        return self.analyze_monthly_trends(months, filters)
    
    def analyze_transaction_type_trends(self, transaction_type: str, months: int = 6) -> Dict[str, Any]:
        """
        특정 거래 유형(수입/지출)의 월별 트렌드를 분석합니다.
        
        Args:
            transaction_type: 분석할 거래 유형
            months: 분석할 월 수
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        filters = {'transaction_type': transaction_type}
        return self.analyze_monthly_trends(months, filters)
    
    def analyze_cash_flow(self, months: int = 6) -> Dict[str, Any]:
        """
        현금 흐름(수입-지출)을 분석합니다.
        
        Args:
            months: 분석할 월 수
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        # 수입 트렌드 분석
        income_trends = self.analyze_transaction_type_trends(Transaction.TYPE_INCOME, months)
        
        # 지출 트렌드 분석
        expense_trends = self.analyze_transaction_type_trends(Transaction.TYPE_EXPENSE, months)
        
        # 현금 흐름 계산
        cash_flow = []
        income_by_month = {item['year_month']: item for item in income_trends['monthly_trend']}
        expense_by_month = {item['year_month']: item for item in expense_trends['monthly_trend']}
        
        # 모든 월 목록 생성
        all_months = sorted(set(list(income_by_month.keys()) + list(expense_by_month.keys())))
        
        for year_month in all_months:
            income = income_by_month.get(year_month, {'total': 0.0})
            expense = expense_by_month.get(year_month, {'total': 0.0})
            
            net_flow = income['total'] - expense['total']
            
            cash_flow.append({
                'year_month': year_month,
                'income': income['total'],
                'expense': expense['total'],
                'net_flow': net_flow,
                'is_positive': net_flow >= 0
            })
        
        return {
            'cash_flow': cash_flow,
            'period_months': months
        }
    
    def print_trend_report(self, months: int = 6) -> None:
        """
        트렌드 리포트를 콘솔에 출력합니다.
        
        Args:
            months: 분석할 월 수
        """
        # 현금 흐름 분석
        result = self.analyze_cash_flow(months)
        
        # 리포트 출력
        print(f"\n=== 최근 {months}개월 트렌드 분석 리포트 ===")
        
        if not result['cash_flow']:
            print("해당 기간에 거래 데이터가 없습니다.")
            return
        
        # 월별 현금 흐름
        print("\n[월별 현금 흐름]")
        print("-" * 70)
        print(f"{'연월':10} | {'수입':>12} | {'지출':>12} | {'순흐름':>12} | {'상태'}")
        print("-" * 70)
        
        for item in result['cash_flow']:
            status = "흑자" if item['is_positive'] else "적자"
            print(f"{item['year_month']:10} | "
                  f"{self.format_amount(item['income']):>12} | "
                  f"{self.format_amount(item['expense']):>12} | "
                  f"{self.format_amount(item['net_flow']):>12} | "
                  f"{status}")
        
        # 평균 계산
        avg_income = sum(item['income'] for item in result['cash_flow']) / len(result['cash_flow'])
        avg_expense = sum(item['expense'] for item in result['cash_flow']) / len(result['cash_flow'])
        avg_net_flow = sum(item['net_flow'] for item in result['cash_flow']) / len(result['cash_flow'])
        
        print("-" * 70)
        print(f"{'평균':10} | "
              f"{self.format_amount(avg_income):>12} | "
              f"{self.format_amount(avg_expense):>12} | "
              f"{self.format_amount(avg_net_flow):>12} | "
              f"{'흑자' if avg_net_flow >= 0 else '적자'}")
    
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
                'transaction_type': tx.transaction_type,
                'category': tx.category or '미분류',
                'payment_method': tx.payment_method or '기타',
                'source': tx.source
            })
        
        df = pd.DataFrame(data)
        
        # 날짜 관련 컬럼 추가
        if not df.empty:
            df['year'] = df['transaction_date'].dt.year if isinstance(df['transaction_date'].iloc[0], pd.Timestamp) else df['transaction_date'].apply(lambda x: x.year)
            df['month'] = df['transaction_date'].dt.month if isinstance(df['transaction_date'].iloc[0], pd.Timestamp) else df['transaction_date'].apply(lambda x: x.month)
            df['week'] = df['transaction_date'].dt.isocalendar().week if isinstance(df['transaction_date'].iloc[0], pd.Timestamp) else df['transaction_date'].apply(lambda x: x.isocalendar()[1])
            df['year_month'] = df.apply(lambda x: f"{x['year']}-{x['month']:02d}", axis=1)
            df['year_week'] = df.apply(lambda x: f"{x['year']}-W{x['week']:02d}", axis=1)
        
        return df
    
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
        
        # 거래 유형별 그룹화
        result = []
        
        for tx_type in [Transaction.TYPE_EXPENSE, Transaction.TYPE_INCOME]:
            type_df = df[df['transaction_type'] == tx_type]
            
            if type_df.empty:
                continue
            
            # 일별 그룹화
            daily = type_df.groupby('transaction_date').agg({
                'amount': 'sum',
                'id': 'count'
            })
            
            # 결과 포맷팅
            for dt, data in daily.iterrows():
                result.append({
                    'date': dt.isoformat() if isinstance(dt, pd.Timestamp) else dt.isoformat(),
                    'transaction_type': tx_type,
                    'amount': float(data['amount']),
                    'count': int(data['id'])
                })
        
        # 날짜 기준 정렬
        result.sort(key=lambda x: x['date'])
        
        return result
    
    def _analyze_weekly_trend(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        주별 트렌드 분석을 수행합니다.
        
        Args:
            df: 거래 데이터프레임
            
        Returns:
            List[Dict[str, Any]]: 주별 트렌드 분석 결과
        """
        if df.empty:
            return []
        
        # 거래 유형별 그룹화
        result = []
        
        for tx_type in [Transaction.TYPE_EXPENSE, Transaction.TYPE_INCOME]:
            type_df = df[df['transaction_type'] == tx_type]
            
            if type_df.empty:
                continue
            
            # 주별 그룹화
            weekly = type_df.groupby('year_week').agg({
                'amount': 'sum',
                'id': 'count',
                'transaction_date': ['min', 'max']
            })
            
            # 결과 포맷팅
            for year_week, data in weekly.iterrows():
                result.append({
                    'year_week': year_week,
                    'transaction_type': tx_type,
                    'start_date': data[('transaction_date', 'min')].isoformat() if isinstance(data[('transaction_date', 'min')], pd.Timestamp) else data[('transaction_date', 'min')].isoformat(),
                    'end_date': data[('transaction_date', 'max')].isoformat() if isinstance(data[('transaction_date', 'max')], pd.Timestamp) else data[('transaction_date', 'max')].isoformat(),
                    'total': float(data[('amount', 'sum')]),
                    'count': int(data[('id', 'count')]),
                    'average': float(data[('amount', 'sum')]) / int(data[('id', 'count')]) if int(data[('id', 'count')]) > 0 else 0
                })
        
        # 연도-주 기준 정렬
        result.sort(key=lambda x: x['year_week'])
        
        return result
    
    def _analyze_monthly_trend(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        월별 트렌드 분석을 수행합니다.
        
        Args:
            df: 거래 데이터프레임
            
        Returns:
            List[Dict[str, Any]]: 월별 트렌드 분석 결과
        """
        if df.empty:
            return []
        
        # 거래 유형별 그룹화
        result = []
        
        for tx_type in [Transaction.TYPE_EXPENSE, Transaction.TYPE_INCOME]:
            type_df = df[df['transaction_type'] == tx_type]
            
            if type_df.empty:
                continue
            
            # 월별 그룹화
            monthly = type_df.groupby(['year', 'month']).agg({
                'amount': 'sum',
                'id': 'count',
                'year_month': 'first'
            })
            
            # 결과 포맷팅
            for (year, month), data in monthly.iterrows():
                # 해당 월의 일수 계산
                _, days_in_month = monthrange(year, month)
                
                result.append({
                    'year': int(year),
                    'month': int(month),
                    'year_month': data['year_month'],
                    'transaction_type': tx_type,
                    'total': float(data['amount']),
                    'count': int(data['id']),
                    'average': float(data['amount']) / int(data['id']) if int(data['id']) > 0 else 0,
                    'daily_average': float(data['amount']) / days_in_month
                })
        
        # 연월 기준 정렬
        result.sort(key=lambda x: f"{x['year']}-{x['month']:02d}")
        
        return result