# -*- coding: utf-8 -*-
"""
비교 분석기 클래스

서로 다른 기간의 거래 데이터를 비교 분석합니다.
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


class ComparisonAnalyzer(BaseAnalyzer):
    """
    비교 분석기 클래스
    
    서로 다른 기간의 거래 데이터를 비교 분석합니다.
    """
    
    def __init__(self, transaction_repository: TransactionRepository):
        """
        비교 분석기 초기화
        
        Args:
            transaction_repository: 거래 저장소
        """
        super().__init__(transaction_repository)
    
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
        # 이 메서드는 비교 분석기에서는 사용하지 않음
        raise NotImplementedError("비교 분석기에서는 analyze 메서드를 직접 사용하지 않습니다. "
                                "compare_periods 또는 다른 비교 메서드를 사용하세요.")
    
    def compare_periods(self, 
                       period1_start: date, period1_end: date, 
                       period2_start: date, period2_end: date,
                       transaction_type: Optional[str] = None,
                       filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        두 기간의 거래 데이터를 비교합니다.
        
        Args:
            period1_start: 첫 번째 기간 시작 날짜
            period1_end: 첫 번째 기간 종료 날짜
            period2_start: 두 번째 기간 시작 날짜
            period2_end: 두 번째 기간 종료 날짜
            transaction_type: 거래 유형 (선택)
            filters: 추가 필터 조건 (선택)
            
        Returns:
            Dict[str, Any]: 비교 분석 결과
        """
        # 기본 필터 설정
        filters = filters or {}
        if transaction_type:
            filters['transaction_type'] = transaction_type
        
        # 첫 번째 기간 데이터 조회
        period1_filters = filters.copy()
        period1_filters['start_date'] = period1_start
        period1_filters['end_date'] = period1_end
        period1_transactions = self.repository.list(period1_filters)
        
        # 두 번째 기간 데이터 조회
        period2_filters = filters.copy()
        period2_filters['start_date'] = period2_start
        period2_filters['end_date'] = period2_end
        period2_transactions = self.repository.list(period2_filters)
        
        # 데이터프레임 변환
        df1 = self._transactions_to_dataframe(period1_transactions) if period1_transactions else pd.DataFrame()
        df2 = self._transactions_to_dataframe(period2_transactions) if period2_transactions else pd.DataFrame()
        
        # 기간 정보
        period1_days = (period1_end - period1_start).days + 1
        period2_days = (period2_end - period2_start).days + 1
        
        # 전체 요약 비교
        summary_comparison = self._compare_summary(df1, df2, period1_days, period2_days)
        
        # 카테고리별 비교
        category_comparison = self._compare_by_category(df1, df2)
        
        # 결제 방식별 비교 (지출인 경우)
        payment_method_comparison = []
        if transaction_type != Transaction.TYPE_INCOME:
            payment_method_comparison = self._compare_by_payment_method(df1, df2)
        
        # 일평균 비교
        daily_avg_comparison = self._compare_daily_average(df1, df2, period1_days, period2_days)
        
        # 결과 반환
        return {
            'period1': {
                'start_date': period1_start.isoformat(),
                'end_date': period1_end.isoformat(),
                'days': period1_days,
                'transaction_count': len(period1_transactions)
            },
            'period2': {
                'start_date': period2_start.isoformat(),
                'end_date': period2_end.isoformat(),
                'days': period2_days,
                'transaction_count': len(period2_transactions)
            },
            'summary_comparison': summary_comparison,
            'category_comparison': category_comparison,
            'payment_method_comparison': payment_method_comparison,
            'daily_avg_comparison': daily_avg_comparison
        }
    
    def compare_months(self, 
                      year1: int, month1: int, 
                      year2: int, month2: int,
                      transaction_type: Optional[str] = None,
                      filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        두 월의 거래 데이터를 비교합니다.
        
        Args:
            year1: 첫 번째 연도
            month1: 첫 번째 월
            year2: 두 번째 연도
            month2: 두 번째 월
            transaction_type: 거래 유형 (선택)
            filters: 추가 필터 조건 (선택)
            
        Returns:
            Dict[str, Any]: 비교 분석 결과
        """
        # 기간 계산
        period1_start, period1_end = self.get_month_range(year1, month1)
        period2_start, period2_end = self.get_month_range(year2, month2)
        
        # 비교 분석 수행
        result = self.compare_periods(
            period1_start, period1_end,
            period2_start, period2_end,
            transaction_type, filters
        )
        
        # 월 정보 추가
        result['period1']['year_month'] = f"{year1}-{month1:02d}"
        result['period2']['year_month'] = f"{year2}-{month2:02d}"
        
        return result
    
    def compare_with_previous_period(self, 
                                   start_date: date, end_date: date,
                                   transaction_type: Optional[str] = None,
                                   filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        지정된 기간과 동일한 길이의 이전 기간을 비교합니다.
        
        Args:
            start_date: 현재 기간 시작 날짜
            end_date: 현재 기간 종료 날짜
            transaction_type: 거래 유형 (선택)
            filters: 추가 필터 조건 (선택)
            
        Returns:
            Dict[str, Any]: 비교 분석 결과
        """
        # 기간 길이 계산
        period_days = (end_date - start_date).days + 1
        
        # 이전 기간 계산
        period2_start = start_date
        period2_end = end_date
        period1_end = start_date - timedelta(days=1)
        period1_start = period1_end - timedelta(days=period_days - 1)
        
        # 비교 분석 수행
        return self.compare_periods(
            period1_start, period1_end,
            period2_start, period2_end,
            transaction_type, filters
        )
    
    def compare_with_previous_month(self, 
                                  year: int, month: int,
                                  transaction_type: Optional[str] = None,
                                  filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        지정된 월과 이전 월을 비교합니다.
        
        Args:
            year: 현재 연도
            month: 현재 월
            transaction_type: 거래 유형 (선택)
            filters: 추가 필터 조건 (선택)
            
        Returns:
            Dict[str, Any]: 비교 분석 결과
        """
        # 이전 월 계산
        if month == 1:
            prev_year = year - 1
            prev_month = 12
        else:
            prev_year = year
            prev_month = month - 1
        
        # 비교 분석 수행
        return self.compare_months(
            prev_year, prev_month,
            year, month,
            transaction_type, filters
        )
    
    def print_comparison_report(self, 
                              year1: int, month1: int, 
                              year2: int, month2: int,
                              transaction_type: Optional[str] = None) -> None:
        """
        두 월의 비교 리포트를 콘솔에 출력합니다.
        
        Args:
            year1: 첫 번째 연도
            month1: 첫 번째 월
            year2: 두 번째 연도
            month2: 두 번째 월
            transaction_type: 거래 유형 (선택)
        """
        # 거래 유형 결정
        tx_type = transaction_type or Transaction.TYPE_EXPENSE
        tx_type_str = "지출" if tx_type == Transaction.TYPE_EXPENSE else "수입"
        
        # 비교 분석 수행
        result = self.compare_months(year1, month1, year2, month2, tx_type)
        
        # 리포트 출력
        print(f"\n=== {year1}년 {month1}월 vs {year2}년 {month2}월 {tx_type_str} 비교 분석 ===")
        
        # 1. 전체 요약 비교
        print("\n[전체 요약 비교]")
        print("-" * 70)
        summary = result['summary_comparison']
        
        print(f"{'항목':15} | {f'{year1}년 {month1}월':>15} | {f'{year2}년 {month2}월':>15} | {'변화':>10} | {'변화율':>6}")
        print("-" * 70)
        print(f"{'총 ' + tx_type_str:15} | {self.format_amount(summary['total1']):>15} | {self.format_amount(summary['total2']):>15} | {self.format_amount(summary['diff']):>10} | {summary['diff_percentage']:>6.1f}%")
        print(f"{'거래 건수':15} | {summary['count1']:>15} | {summary['count2']:>15} | {summary['count_diff']:>10} | {summary['count_diff_percentage']:>6.1f}%")
        print(f"{'평균 금액':15} | {self.format_amount(summary['avg1']):>15} | {self.format_amount(summary['avg2']):>15} | {self.format_amount(summary['avg_diff']):>10} | {summary['avg_diff_percentage']:>6.1f}%")
        print(f"{'일평균':15} | {self.format_amount(summary['daily_avg1']):>15} | {self.format_amount(summary['daily_avg2']):>15} | {self.format_amount(summary['daily_avg_diff']):>10} | {summary['daily_avg_diff_percentage']:>6.1f}%")
        
        # 2. 카테고리별 비교 (상위 5개)
        print(f"\n[카테고리별 {tx_type_str} 비교 (변화율 기준 상위 5개)]")
        print("-" * 70)
        print(f"{'카테고리':15} | {f'{year1}년 {month1}월':>15} | {f'{year2}년 {month2}월':>15} | {'변화':>10} | {'변화율':>6}")
        print("-" * 70)
        
        # 변화율 기준 정렬
        sorted_categories = sorted(result['category_comparison'], 
                                 key=lambda x: abs(x['diff_percentage']) if x['diff_percentage'] is not None else 0, 
                                 reverse=True)
        
        for item in sorted_categories[:5]:
            diff_percentage = f"{item['diff_percentage']:.1f}%" if item['diff_percentage'] is not None else "N/A"
            print(f"{item['category']:15} | {self.format_amount(item['amount1']):>15} | {self.format_amount(item['amount2']):>15} | {self.format_amount(item['diff']):>10} | {diff_percentage:>6}")
        
        # 3. 결제 방식별 비교 (지출인 경우)
        if tx_type == Transaction.TYPE_EXPENSE and result['payment_method_comparison']:
            print(f"\n[결제 방식별 {tx_type_str} 비교]")
            print("-" * 70)
            print(f"{'결제 방식':15} | {f'{year1}년 {month1}월':>15} | {f'{year2}년 {month2}월':>15} | {'변화':>10} | {'변화율':>6}")
            print("-" * 70)
            
            for item in result['payment_method_comparison']:
                diff_percentage = f"{item['diff_percentage']:.1f}%" if item['diff_percentage'] is not None else "N/A"
                print(f"{item['payment_method']:15} | {self.format_amount(item['amount1']):>15} | {self.format_amount(item['amount2']):>15} | {self.format_amount(item['diff']):>10} | {diff_percentage:>6}")
    
    def _transactions_to_dataframe(self, transactions: List[Transaction]) -> pd.DataFrame:
        """
        거래 목록을 데이터프레임으로 변환합니다.
        
        Args:
            transactions: 거래 목록
            
        Returns:
            pd.DataFrame: 변환된 데이터프레임
        """
        if not transactions:
            return pd.DataFrame()
        
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
        
        return pd.DataFrame(data)
    
    def _compare_summary(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                       period1_days: int, period2_days: int) -> Dict[str, Any]:
        """
        두 기간의 전체 요약을 비교합니다.
        
        Args:
            df1: 첫 번째 기간 데이터프레임
            df2: 두 번째 기간 데이터프레임
            period1_days: 첫 번째 기간 일수
            period2_days: 두 번째 기간 일수
            
        Returns:
            Dict[str, Any]: 요약 비교 결과
        """
        # 첫 번째 기간 요약
        total1 = float(df1['amount'].sum()) if not df1.empty else 0
        count1 = len(df1) if not df1.empty else 0
        avg1 = total1 / count1 if count1 > 0 else 0
        daily_avg1 = total1 / period1_days if period1_days > 0 else 0
        
        # 두 번째 기간 요약
        total2 = float(df2['amount'].sum()) if not df2.empty else 0
        count2 = len(df2) if not df2.empty else 0
        avg2 = total2 / count2 if count2 > 0 else 0
        daily_avg2 = total2 / period2_days if period2_days > 0 else 0
        
        # 차이 계산
        diff = total2 - total1
        count_diff = count2 - count1
        avg_diff = avg2 - avg1
        daily_avg_diff = daily_avg2 - daily_avg1
        
        # 변화율 계산
        diff_percentage = (diff / total1) * 100 if total1 > 0 else None
        count_diff_percentage = (count_diff / count1) * 100 if count1 > 0 else None
        avg_diff_percentage = (avg_diff / avg1) * 100 if avg1 > 0 else None
        daily_avg_diff_percentage = (daily_avg_diff / daily_avg1) * 100 if daily_avg1 > 0 else None
        
        return {
            'total1': total1,
            'total2': total2,
            'diff': diff,
            'diff_percentage': diff_percentage,
            'count1': count1,
            'count2': count2,
            'count_diff': count_diff,
            'count_diff_percentage': count_diff_percentage,
            'avg1': avg1,
            'avg2': avg2,
            'avg_diff': avg_diff,
            'avg_diff_percentage': avg_diff_percentage,
            'daily_avg1': daily_avg1,
            'daily_avg2': daily_avg2,
            'daily_avg_diff': daily_avg_diff,
            'daily_avg_diff_percentage': daily_avg_diff_percentage
        }
    
    def _compare_by_category(self, df1: pd.DataFrame, df2: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        두 기간의 카테고리별 데이터를 비교합니다.
        
        Args:
            df1: 첫 번째 기간 데이터프레임
            df2: 두 번째 기간 데이터프레임
            
        Returns:
            List[Dict[str, Any]]: 카테고리별 비교 결과
        """
        # 모든 카테고리 목록
        all_categories = set()
        if not df1.empty:
            all_categories.update(df1['category'].unique())
        if not df2.empty:
            all_categories.update(df2['category'].unique())
        
        # 카테고리별 비교
        result = []
        
        for category in all_categories:
            # 첫 번째 기간 카테고리 금액
            amount1 = float(df1[df1['category'] == category]['amount'].sum()) if not df1.empty and category in df1['category'].values else 0
            count1 = len(df1[df1['category'] == category]) if not df1.empty and category in df1['category'].values else 0
            
            # 두 번째 기간 카테고리 금액
            amount2 = float(df2[df2['category'] == category]['amount'].sum()) if not df2.empty and category in df2['category'].values else 0
            count2 = len(df2[df2['category'] == category]) if not df2.empty and category in df2['category'].values else 0
            
            # 차이 계산
            diff = amount2 - amount1
            count_diff = count2 - count1
            
            # 변화율 계산
            diff_percentage = (diff / amount1) * 100 if amount1 > 0 else None
            count_diff_percentage = (count_diff / count1) * 100 if count1 > 0 else None
            
            result.append({
                'category': category,
                'amount1': amount1,
                'amount2': amount2,
                'diff': diff,
                'diff_percentage': diff_percentage,
                'count1': count1,
                'count2': count2,
                'count_diff': count_diff,
                'count_diff_percentage': count_diff_percentage
            })
        
        # 금액 차이 기준 정렬
        result.sort(key=lambda x: abs(x['diff']) if x['diff'] is not None else 0, reverse=True)
        
        return result
    
    def _compare_by_payment_method(self, df1: pd.DataFrame, df2: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        두 기간의 결제 방식별 데이터를 비교합니다.
        
        Args:
            df1: 첫 번째 기간 데이터프레임
            df2: 두 번째 기간 데이터프레임
            
        Returns:
            List[Dict[str, Any]]: 결제 방식별 비교 결과
        """
        # 모든 결제 방식 목록
        all_payment_methods = set()
        if not df1.empty and 'payment_method' in df1.columns:
            all_payment_methods.update(df1['payment_method'].unique())
        if not df2.empty and 'payment_method' in df2.columns:
            all_payment_methods.update(df2['payment_method'].unique())
        
        # 결제 방식별 비교
        result = []
        
        for payment_method in all_payment_methods:
            # 첫 번째 기간 결제 방식 금액
            amount1 = float(df1[df1['payment_method'] == payment_method]['amount'].sum()) if not df1.empty and 'payment_method' in df1.columns and payment_method in df1['payment_method'].values else 0
            count1 = len(df1[df1['payment_method'] == payment_method]) if not df1.empty and 'payment_method' in df1.columns and payment_method in df1['payment_method'].values else 0
            
            # 두 번째 기간 결제 방식 금액
            amount2 = float(df2[df2['payment_method'] == payment_method]['amount'].sum()) if not df2.empty and 'payment_method' in df2.columns and payment_method in df2['payment_method'].values else 0
            count2 = len(df2[df2['payment_method'] == payment_method]) if not df2.empty and 'payment_method' in df2.columns and payment_method in df2['payment_method'].values else 0
            
            # 차이 계산
            diff = amount2 - amount1
            count_diff = count2 - count1
            
            # 변화율 계산
            diff_percentage = (diff / amount1) * 100 if amount1 > 0 else None
            count_diff_percentage = (count_diff / count1) * 100 if count1 > 0 else None
            
            result.append({
                'payment_method': payment_method,
                'amount1': amount1,
                'amount2': amount2,
                'diff': diff,
                'diff_percentage': diff_percentage,
                'count1': count1,
                'count2': count2,
                'count_diff': count_diff,
                'count_diff_percentage': count_diff_percentage
            })
        
        # 금액 차이 기준 정렬
        result.sort(key=lambda x: abs(x['diff']) if x['diff'] is not None else 0, reverse=True)
        
        return result
    
    def _compare_daily_average(self, df1: pd.DataFrame, df2: pd.DataFrame, 
                             period1_days: int, period2_days: int) -> Dict[str, Any]:
        """
        두 기간의 일평균 데이터를 비교합니다.
        
        Args:
            df1: 첫 번째 기간 데이터프레임
            df2: 두 번째 기간 데이터프레임
            period1_days: 첫 번째 기간 일수
            period2_days: 두 번째 기간 일수
            
        Returns:
            Dict[str, Any]: 일평균 비교 결과
        """
        # 첫 번째 기간 일평균
        total1 = float(df1['amount'].sum()) if not df1.empty else 0
        daily_avg1 = total1 / period1_days if period1_days > 0 else 0
        
        # 두 번째 기간 일평균
        total2 = float(df2['amount'].sum()) if not df2.empty else 0
        daily_avg2 = total2 / period2_days if period2_days > 0 else 0
        
        # 차이 계산
        diff = daily_avg2 - daily_avg1
        
        # 변화율 계산
        diff_percentage = (diff / daily_avg1) * 100 if daily_avg1 > 0 else None
        
        return {
            'daily_avg1': daily_avg1,
            'daily_avg2': daily_avg2,
            'diff': diff,
            'diff_percentage': diff_percentage,
            'period1_days': period1_days,
            'period2_days': period2_days
        }