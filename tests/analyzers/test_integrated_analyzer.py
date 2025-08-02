# -*- coding: utf-8 -*-
"""
통합 분석 엔진 테스트
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.models import Transaction
from src.analyzers import IntegratedAnalyzer, ExpenseAnalyzer, IncomeAnalyzer, TrendAnalyzer, ComparisonAnalyzer
from src.repositories.transaction_repository import TransactionRepository


class TestIntegratedAnalyzer(unittest.TestCase):
    """통합 분석 엔진 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.repository = MagicMock(spec=TransactionRepository)
        
        # 개별 분석기 모의 객체
        self.expense_analyzer = MagicMock(spec=ExpenseAnalyzer)
        self.income_analyzer = MagicMock(spec=IncomeAnalyzer)
        self.trend_analyzer = MagicMock(spec=TrendAnalyzer)
        self.comparison_analyzer = MagicMock(spec=ComparisonAnalyzer)
        
        # 통합 분석 엔진 생성
        self.analyzer = IntegratedAnalyzer(self.repository)
        
        # 개별 분석기 교체
        self.analyzer.expense_analyzer = self.expense_analyzer
        self.analyzer.income_analyzer = self.income_analyzer
        self.analyzer.trend_analyzer = self.trend_analyzer
        self.analyzer.comparison_analyzer = self.comparison_analyzer
        
        # 테스트 데이터 설정
        self.today = datetime.now().date()
        self.start_date = self.today - timedelta(days=30)
        self.end_date = self.today
    
    def test_analyze_period(self):
        """기간 분석 테스트"""
        # 모의 객체 설정
        self.expense_analyzer.analyze.return_value = {
            'total_expense': 100000.0,
            'transaction_count': 10,
            'by_category': [{'category': '식비', 'amount': 50000.0}]
        }
        
        self.income_analyzer.analyze.return_value = {
            'total_income': 300000.0,
            'transaction_count': 2,
            'by_category': [{'category': '급여', 'amount': 300000.0}]
        }
        
        self.trend_analyzer.analyze.return_value = {
            'daily_trend': [{'date': '2023-01-01', 'amount': 10000.0}],
            'monthly_trend': [{'year_month': '2023-01', 'amount': 100000.0}]
        }
        
        # 분석 실행
        result = self.analyzer.analyze_period(
            self.start_date, self.end_date,
            include_expense=True,
            include_income=True,
            include_trends=True
        )
        
        # 검증
        self.expense_analyzer.analyze.assert_called_once_with(self.start_date, self.end_date)
        self.income_analyzer.analyze.assert_called_once_with(self.start_date, self.end_date)
        self.trend_analyzer.analyze.assert_called_once_with(self.start_date, self.end_date)
        
        # 결과 검증
        self.assertEqual(result['period']['start_date'], self.start_date.isoformat())
        self.assertEqual(result['period']['end_date'], self.end_date.isoformat())
        self.assertEqual(result['expense']['total_expense'], 100000.0)
        self.assertEqual(result['income']['total_income'], 300000.0)
        self.assertEqual(result['cash_flow']['net_flow'], 200000.0)
        self.assertTrue(result['cash_flow']['is_positive'])
        self.assertEqual(result['trends']['daily_trend'], [{'date': '2023-01-01', 'amount': 10000.0}])
    
    def test_analyze_month(self):
        """월 분석 테스트"""
        # 모의 객체 설정
        self.expense_analyzer.analyze.return_value = {
            'total_expense': 100000.0,
            'transaction_count': 10
        }
        
        self.income_analyzer.analyze.return_value = {
            'total_income': 300000.0,
            'transaction_count': 2
        }
        
        self.trend_analyzer.analyze.return_value = {
            'daily_trend': [],
            'monthly_trend': []
        }
        
        # 현재 연월
        year = 2023
        month = 1
        
        # 분석 실행
        result = self.analyzer.analyze_month(
            year, month,
            include_expense=True,
            include_income=True,
            include_trends=False,
            compare_with_previous=False
        )
        
        # 검증
        self.expense_analyzer.analyze.assert_called_once()
        self.income_analyzer.analyze.assert_called_once()
        self.trend_analyzer.analyze.assert_not_called()
        
        # 결과 검증
        self.assertEqual(result['period']['year'], year)
        self.assertEqual(result['period']['month'], month)
        self.assertEqual(result['period']['year_month'], f"{year}-{month:02d}")
        self.assertEqual(result['expense']['total_expense'], 100000.0)
        self.assertEqual(result['income']['total_income'], 300000.0)
    
    def test_analyze_month_with_comparison(self):
        """비교 포함 월 분석 테스트"""
        # 모의 객체 설정
        self.expense_analyzer.analyze.return_value = {
            'total_expense': 100000.0,
            'transaction_count': 10
        }
        
        self.income_analyzer.analyze.return_value = {
            'total_income': 300000.0,
            'transaction_count': 2
        }
        
        self.comparison_analyzer.compare_months.return_value = {
            'summary_comparison': {
                'total1': 90000.0,
                'total2': 100000.0,
                'diff': 10000.0,
                'diff_percentage': 11.1
            }
        }
        
        # 현재 연월
        year = 2023
        month = 1
        
        # 분석 실행
        result = self.analyzer.analyze_month(
            year, month,
            include_expense=True,
            include_income=True,
            include_trends=False,
            compare_with_previous=True
        )
        
        # 검증
        self.expense_analyzer.analyze.assert_called_once()
        self.income_analyzer.analyze.assert_called_once()
        self.comparison_analyzer.compare_months.assert_called()
        
        # 결과 검증
        self.assertTrue('expense_comparison' in result)
        self.assertTrue('income_comparison' in result)
        self.assertEqual(result['expense_comparison']['summary_comparison']['diff'], 10000.0)
    
    def test_get_financial_summary(self):
        """금융 요약 테스트"""
        # 모의 객체 설정
        self.expense_analyzer.get_expense_summary.return_value = {
            'total_expense': '100,000원',
            'daily_average': '3,333원',
            'monthly_estimate': '100,000원',
            'transaction_count': 10,
            'top_categories': []
        }
        
        self.income_analyzer.get_income_summary.return_value = {
            'total_income': '300,000원',
            'daily_average': '10,000원',
            'monthly_estimate': '300,000원',
            'transaction_count': 2,
            'top_categories': []
        }
        
        self.expense_analyzer.find_regular_expenses.return_value = [{'description': '월세'}]
        self.income_analyzer.find_regular_income.return_value = [{'description': '급여'}]
        self.expense_analyzer.find_missing_expenses.return_value = []
        
        # 요약 실행
        result = self.analyzer.get_financial_summary(days=30)
        
        # 검증
        self.expense_analyzer.get_expense_summary.assert_called_once_with(30)
        self.income_analyzer.get_income_summary.assert_called_once_with(30)
        self.expense_analyzer.find_regular_expenses.assert_called_once()
        self.income_analyzer.find_regular_income.assert_called_once()
        self.expense_analyzer.find_missing_expenses.assert_called_once()
        
        # 결과 검증
        self.assertEqual(result['period'], '최근 30일')
        self.assertEqual(result['expense']['total'], '100,000원')
        self.assertEqual(result['income']['total'], '300,000원')
        self.assertEqual(result['cash_flow']['status'], '흑자')
        self.assertEqual(result['regular_transactions']['expenses'], 1)
        self.assertEqual(result['regular_transactions']['income'], 1)
        self.assertEqual(result['alerts']['missing_expenses'], 0)


if __name__ == '__main__':
    unittest.main()