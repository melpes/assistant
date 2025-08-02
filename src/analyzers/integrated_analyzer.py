# -*- coding: utf-8 -*-
"""
통합 분석 엔진 클래스

다양한 분석기를 통합하여 종합적인 분석 결과를 제공합니다.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union

from src.models import Transaction
from src.repositories.transaction_repository import TransactionRepository
from src.analyzers.expense_analyzer import ExpenseAnalyzer
from src.analyzers.income_analyzer import IncomeAnalyzer
from src.analyzers.trend_analyzer import TrendAnalyzer
from src.analyzers.comparison_analyzer import ComparisonAnalyzer

# 로거 설정
logger = logging.getLogger(__name__)


class IntegratedAnalyzer:
    """
    통합 분석 엔진 클래스
    
    다양한 분석기를 통합하여 종합적인 분석 결과를 제공합니다.
    """
    
    def __init__(self, transaction_repository: TransactionRepository):
        """
        통합 분석 엔진 초기화
        
        Args:
            transaction_repository: 거래 저장소
        """
        self.repository = transaction_repository
        self.expense_analyzer = ExpenseAnalyzer(transaction_repository)
        self.income_analyzer = IncomeAnalyzer(transaction_repository)
        self.trend_analyzer = TrendAnalyzer(transaction_repository)
        self.comparison_analyzer = ComparisonAnalyzer(transaction_repository)
    
    def analyze_period(self, start_date: date, end_date: date, 
                     include_expense: bool = True, 
                     include_income: bool = True,
                     include_trends: bool = True) -> Dict[str, Any]:
        """
        지정된 기간의 종합 분석을 수행합니다.
        
        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            include_expense: 지출 분석 포함 여부
            include_income: 수입 분석 포함 여부
            include_trends: 트렌드 분석 포함 여부
            
        Returns:
            Dict[str, Any]: 종합 분석 결과
        """
        result = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days + 1
            }
        }
        
        # 지출 분석
        if include_expense:
            expense_result = self.expense_analyzer.analyze(start_date, end_date)
            result['expense'] = expense_result
        
        # 수입 분석
        if include_income:
            income_result = self.income_analyzer.analyze(start_date, end_date)
            result['income'] = income_result
        
        # 현금 흐름 계산 (수입 - 지출)
        if include_expense and include_income:
            total_expense = expense_result.get('total_expense', 0)
            total_income = income_result.get('total_income', 0)
            net_flow = total_income - total_expense
            
            result['cash_flow'] = {
                'total_income': total_income,
                'total_expense': total_expense,
                'net_flow': net_flow,
                'is_positive': net_flow >= 0,
                'income_expense_ratio': (total_income / total_expense) if total_expense > 0 else None,
                'expense_income_ratio': (total_expense / total_income) if total_income > 0 else None
            }
        
        # 트렌드 분석
        if include_trends:
            trend_result = self.trend_analyzer.analyze(start_date, end_date)
            result['trends'] = trend_result
        
        return result
    
    def analyze_month(self, year: int, month: int,
                    include_expense: bool = True,
                    include_income: bool = True,
                    include_trends: bool = True,
                    compare_with_previous: bool = False) -> Dict[str, Any]:
        """
        특정 월의 종합 분석을 수행합니다.
        
        Args:
            year: 연도
            month: 월
            include_expense: 지출 분석 포함 여부
            include_income: 수입 분석 포함 여부
            include_trends: 트렌드 분석 포함 여부
            compare_with_previous: 이전 월과 비교 여부
            
        Returns:
            Dict[str, Any]: 종합 분석 결과
        """
        # 월 기간 계산
        start_date, end_date = self._get_month_range(year, month)
        
        # 기본 분석 수행
        result = self.analyze_period(
            start_date, end_date,
            include_expense, include_income, include_trends
        )
        
        # 월 정보 추가
        result['period']['year'] = year
        result['period']['month'] = month
        result['period']['year_month'] = f"{year}-{month:02d}"
        
        # 이전 월과 비교
        if compare_with_previous:
            # 이전 월 계산
            if month == 1:
                prev_year = year - 1
                prev_month = 12
            else:
                prev_year = year
                prev_month = month - 1
            
            # 지출 비교
            if include_expense:
                expense_comparison = self.comparison_analyzer.compare_months(
                    prev_year, prev_month, year, month, Transaction.TYPE_EXPENSE
                )
                result['expense_comparison'] = expense_comparison
            
            # 수입 비교
            if include_income:
                income_comparison = self.comparison_analyzer.compare_months(
                    prev_year, prev_month, year, month, Transaction.TYPE_INCOME
                )
                result['income_comparison'] = income_comparison
        
        return result
    
    def analyze_recent_period(self, days: int = 30,
                            include_expense: bool = True,
                            include_income: bool = True,
                            include_trends: bool = True,
                            compare_with_previous: bool = False) -> Dict[str, Any]:
        """
        최근 N일 동안의 종합 분석을 수행합니다.
        
        Args:
            days: 분석 기간 (일)
            include_expense: 지출 분석 포함 여부
            include_income: 수입 분석 포함 여부
            include_trends: 트렌드 분석 포함 여부
            compare_with_previous: 이전 기간과 비교 여부
            
        Returns:
            Dict[str, Any]: 종합 분석 결과
        """
        # 기간 계산
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)
        
        # 기본 분석 수행
        result = self.analyze_period(
            start_date, end_date,
            include_expense, include_income, include_trends
        )
        
        # 기간 정보 추가
        result['period']['description'] = f"최근 {days}일"
        
        # 이전 기간과 비교
        if compare_with_previous:
            prev_end_date = start_date - timedelta(days=1)
            prev_start_date = prev_end_date - timedelta(days=days - 1)
            
            # 지출 비교
            if include_expense:
                expense_comparison = self.comparison_analyzer.compare_periods(
                    prev_start_date, prev_end_date,
                    start_date, end_date,
                    Transaction.TYPE_EXPENSE
                )
                result['expense_comparison'] = expense_comparison
            
            # 수입 비교
            if include_income:
                income_comparison = self.comparison_analyzer.compare_periods(
                    prev_start_date, prev_end_date,
                    start_date, end_date,
                    Transaction.TYPE_INCOME
                )
                result['income_comparison'] = income_comparison
        
        return result
    
    def compare_income_expense(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        수입과 지출을 비교 분석하고 순 현금 흐름을 계산합니다.
        
        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            Dict[str, Any]: 수입-지출 비교 분석 결과
        """
        # 트렌드 분석 수행
        trend_result = self.trend_analyzer.analyze(start_date, end_date)
        
        # 일별 비교 데이터 생성
        daily_comparison = []
        for day_data in trend_result['daily_trend']:
            date_str = day_data['date']
            
            # 해당 날짜의 수입과 지출 찾기
            income_data = next((item for item in trend_result['daily_trend'] 
                              if item['date'] == date_str and item['transaction_type'] == Transaction.TYPE_INCOME), 
                             {'amount': 0, 'count': 0})
            
            expense_data = next((item for item in trend_result['daily_trend'] 
                               if item['date'] == date_str and item['transaction_type'] == Transaction.TYPE_EXPENSE), 
                              {'amount': 0, 'count': 0})
            
            # 일별 비교 데이터 추가
            daily_comparison.append({
                'date': date_str,
                'period': date_str,
                'income': income_data['amount'],
                'expense': expense_data['amount'],
                'income_count': income_data['count'],
                'expense_count': expense_data['count']
            })
        
        # 주별 비교 데이터 생성
        weekly_comparison = []
        for week_data in trend_result['weekly_trend']:
            week_str = week_data['week']
            
            # 해당 주의 수입과 지출 찾기
            income_data = next((item for item in trend_result['weekly_trend'] 
                              if item['week'] == week_str and item['transaction_type'] == Transaction.TYPE_INCOME), 
                             {'total': 0, 'count': 0})
            
            expense_data = next((item for item in trend_result['weekly_trend'] 
                               if item['week'] == week_str and item['transaction_type'] == Transaction.TYPE_EXPENSE), 
                              {'total': 0, 'count': 0})
            
            # 주별 비교 데이터 추가
            weekly_comparison.append({
                'week': week_str,
                'period': week_str,
                'income': income_data['total'],
                'expense': expense_data['total'],
                'income_count': income_data['count'],
                'expense_count': expense_data['count']
            })
        
        # 월별 비교 데이터 생성
        monthly_comparison = []
        for month_data in trend_result['monthly_trend']:
            month_str = month_data['year_month']
            
            # 해당 월의 수입과 지출 찾기
            income_data = next((item for item in trend_result['monthly_trend'] 
                              if item['year_month'] == month_str and item['transaction_type'] == Transaction.TYPE_INCOME), 
                             {'total': 0, 'count': 0})
            
            expense_data = next((item for item in trend_result['monthly_trend'] 
                               if item['year_month'] == month_str and item['transaction_type'] == Transaction.TYPE_EXPENSE), 
                              {'total': 0, 'count': 0})
            
            # 월별 비교 데이터 추가
            monthly_comparison.append({
                'year': month_data['year'],
                'month': month_data['month'],
                'year_month': month_str,
                'period': month_str,
                'income': income_data['total'],
                'expense': expense_data['total'],
                'income_count': income_data['count'],
                'expense_count': expense_data['count']
            })
        
        # 결과 반환
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days + 1
            },
            'daily_comparison': sorted(daily_comparison, key=lambda x: x['date']),
            'weekly_comparison': sorted(weekly_comparison, key=lambda x: x['week']),
            'monthly_comparison': sorted(monthly_comparison, key=lambda x: x['year_month'])
        }
    
    def get_financial_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        최근 N일 동안의 금융 요약 정보를 반환합니다.
        
        Args:
            days: 분석 기간 (일)
            
        Returns:
            Dict[str, Any]: 금융 요약 정보
        """
        # 기간 계산
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)
        
        # 지출 요약
        expense_summary = self.expense_analyzer.get_expense_summary(days)
        
        # 수입 요약
        income_summary = self.income_analyzer.get_income_summary(days)
        
        # 현금 흐름 계산
        total_expense = float(expense_summary['total_expense'].replace(',', '').replace('원', ''))
        total_income = float(income_summary['total_income'].replace(',', '').replace('원', ''))
        net_flow = total_income - total_expense
        
        # 정기 지출 및 수입
        regular_expenses = self.expense_analyzer.find_regular_expenses()
        regular_income = self.income_analyzer.find_regular_income()
        
        # 누락 가능성 있는 지출
        missing_expenses = self.expense_analyzer.find_missing_expenses()
        
        # 요약 정보 구성
        summary = {
            'period': f"최근 {days}일",
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'expense': {
                'total': expense_summary['total_expense'],
                'daily_average': expense_summary['daily_average'],
                'monthly_estimate': expense_summary['monthly_estimate'],
                'transaction_count': expense_summary['transaction_count'],
                'top_categories': expense_summary['top_categories']
            },
            'income': {
                'total': income_summary['total_income'],
                'daily_average': income_summary['daily_average'],
                'monthly_estimate': income_summary['monthly_estimate'],
                'transaction_count': income_summary['transaction_count'],
                'top_categories': income_summary['top_categories']
            },
            'cash_flow': {
                'net_flow': f"{net_flow:,}원",
                'is_positive': net_flow >= 0,
                'status': "흑자" if net_flow >= 0 else "적자",
                'income_expense_ratio': f"{(total_income / total_expense * 100):.1f}%" if total_expense > 0 else "N/A"
            },
            'regular_transactions': {
                'expenses': len(regular_expenses),
                'income': len(regular_income)
            },
            'alerts': {
                'missing_expenses': len(missing_expenses)
            }
        }
        
        return summary
    
    def print_financial_report(self, days: int = 30) -> None:
        """
        종합 금융 리포트를 콘솔에 출력합니다.
        
        Args:
            days: 분석 기간 (일)
        """
        # 종합 분석 수행
        result = self.analyze_recent_period(days, True, True, True, True)
        
        # 리포트 출력
        print(f"\n=== 최근 {days}일 종합 금융 리포트 ===")
        print(f"분석 기간: {result['period']['start_date']} ~ {result['period']['end_date']}")
        
        # 1. 현금 흐름 요약
        if 'cash_flow' in result:
            cf = result['cash_flow']
            print("\n[현금 흐름 요약]")
            print("-" * 60)
            print(f"총 수입: {self._format_amount(cf['total_income'])}")
            print(f"총 지출: {self._format_amount(cf['total_expense'])}")
            print(f"순 흐름: {self._format_amount(cf['net_flow'])} ({'흑자' if cf['is_positive'] else '적자'})")
            
            if cf['income_expense_ratio'] is not None:
                print(f"수입/지출 비율: {cf['income_expense_ratio']:.1f}")
        
        # 2. 지출 요약
        if 'expense' in result:
            exp = result['expense']
            print("\n[지출 요약]")
            print("-" * 60)
            print(f"총 지출: {self._format_amount(exp['total_expense'])}")
            print(f"거래 건수: {exp['transaction_count']}건")
            print(f"일평균 지출: {self._format_amount(exp['daily_average'])}")
            print(f"월 예상 지출: {self._format_amount(exp['monthly_estimate'])}")
            
            print("\n[주요 지출 카테고리 (상위 5개)]")
            for item in exp['by_category'][:5]:
                print(f"{item['category']:15} | {self._format_amount(item['amount']):>12} ({item['percentage']:5.1f}%)")
        
        # 3. 수입 요약
        if 'income' in result:
            inc = result['income']
            print("\n[수입 요약]")
            print("-" * 60)
            print(f"총 수입: {self._format_amount(inc['total_income'])}")
            print(f"거래 건수: {inc['transaction_count']}건")
            print(f"일평균 수입: {self._format_amount(inc['daily_average'])}")
            print(f"월 예상 수입: {self._format_amount(inc['monthly_estimate'])}")
            
            print("\n[주요 수입 유형]")
            for item in inc['by_category']:
                print(f"{item['category']:15} | {self._format_amount(item['amount']):>12} ({item['percentage']:5.1f}%)")
        
        # 4. 이전 기간과 비교
        if 'expense_comparison' in result:
            print("\n[이전 기간 대비 지출 변화]")
            print("-" * 60)
            ec = result['expense_comparison']['summary_comparison']
            print(f"총 지출: {self._format_amount(ec['diff'])} ({ec['diff_percentage']:+.1f}%)")
            print(f"일평균 지출: {self._format_amount(ec['daily_avg_diff'])} ({ec['daily_avg_diff_percentage']:+.1f}%)")
            
            print("\n[주요 변화 카테고리 (상위 3개)]")
            for item in result['expense_comparison']['category_comparison'][:3]:
                if item['diff_percentage'] is not None:
                    print(f"{item['category']:15} | {self._format_amount(item['diff']):>12} ({item['diff_percentage']:+.1f}%)")
        
        if 'income_comparison' in result:
            print("\n[이전 기간 대비 수입 변화]")
            print("-" * 60)
            ic = result['income_comparison']['summary_comparison']
            print(f"총 수입: {self._format_amount(ic['diff'])} ({ic['diff_percentage']:+.1f}%)")
            print(f"일평균 수입: {self._format_amount(ic['daily_avg_diff'])} ({ic['daily_avg_diff_percentage']:+.1f}%)")
    
    def _get_month_range(self, year: int, month: int) -> Tuple[date, date]:
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
    
    def _format_amount(self, amount: Union[int, float, str]) -> str:
        """
        금액을 포맷팅합니다.
        
        Args:
            amount: 금액
            
        Returns:
            str: 포맷팅된 금액 문자열
        """
        if isinstance(amount, str):
            # 이미 포맷팅된 문자열인 경우
            if '원' in amount:
                return amount
            try:
                amount = float(amount.replace(',', ''))
            except ValueError:
                return amount
        
        return f"{amount:,}원"