# -*- coding: utf-8 -*-
"""
분석 도구 모듈 테스트

지출/수입 분석 및 리포트 관련 도구 함수들을 테스트합니다.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from decimal import Decimal

from src.financial_tools.analysis_tools import (
    analyze_expenses,
    analyze_income,
    compare_periods,
    analyze_trends,
    get_financial_summary,
    _prepare_chart_data
)
from src.models import Transaction


class TestAnalysisTools(unittest.TestCase):
    """분석 도구 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트용 날짜
        self.today = date.today()
        self.start_date = self.today - timedelta(days=30)
        self.end_date = self.today
        
        # 테스트용 거래 데이터
        self.test_transactions = [
            self._create_mock_transaction(1, "식비", "카드", 10000, "expense"),
            self._create_mock_transaction(2, "식비", "카드", 15000, "expense"),
            self._create_mock_transaction(3, "교통비", "카드", 5000, "expense"),
            self._create_mock_transaction(4, "월급", None, 1000000, "income"),
            self._create_mock_transaction(5, "부수입", None, 50000, "income")
        ]
    
    def _create_mock_transaction(self, id, category, payment_method, amount, tx_type):
        """테스트용 거래 객체 생성"""
        tx = MagicMock(spec=Transaction)
        tx.id = id
        tx.transaction_id = f"TX{id}"
        tx.transaction_date = self.today - timedelta(days=id)
        tx.description = f"테스트 거래 {id}"
        tx.amount = Decimal(str(amount))
        tx.transaction_type = tx_type
        tx.category = category
        tx.payment_method = payment_method
        tx.source = "테스트"
        tx.account_type = "테스트"
        tx.memo = None
        tx.is_excluded = False
        return tx
    
    @patch('src.financial_tools.analysis_tools._get_transaction_repository')
    @patch('src.analyzers.expense_analyzer.ExpenseAnalyzer.analyze')
    @patch('src.analyzers.trend_analyzer.TrendAnalyzer.analyze')
    def test_analyze_expenses(self, mock_trend_analyze, mock_expense_analyze, mock_get_repo):
        """지출 분석 함수 테스트"""
        # 모의 객체 설정
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        
        # ExpenseAnalyzer.analyze 모의 응답 설정
        mock_expense_analyze.return_value = {
            'total_expense': 30000,
            'transaction_count': 3,
            'average_expense': 10000,
            'daily_average': 1000,
            'monthly_estimate': 30000,
            'by_payment_method': [
                {'payment_method': '카드', 'amount': 30000, 'count': 3, 'average': 10000, 'percentage': 100}
            ],
            'by_category': [
                {'category': '식비', 'amount': 25000, 'count': 2, 'average': 12500, 'percentage': 83.33},
                {'category': '교통비', 'amount': 5000, 'count': 1, 'average': 5000, 'percentage': 16.67}
            ],
            'daily_trend': [],
            'period_days': 30
        }
        
        # TrendAnalyzer.analyze 모의 응답 설정
        mock_trend_analyze.return_value = {
            'daily_trend': [
                {'date': '2023-01-01', 'transaction_type': 'expense', 'amount': 10000, 'count': 1},
                {'date': '2023-01-02', 'transaction_type': 'expense', 'amount': 15000, 'count': 1},
                {'date': '2023-01-03', 'transaction_type': 'expense', 'amount': 5000, 'count': 1}
            ],
            'weekly_trend': [],
            'monthly_trend': [],
            'period_days': 30
        }
        
        # 함수 호출
        result = analyze_expenses(
            start_date=self.start_date.isoformat(),
            end_date=self.end_date.isoformat(),
            category=None,
            payment_method=None,
            group_by="category"
        )
        
        # 검증
        self.assertIn('summary', result)
        self.assertIn('data', result)
        self.assertIn('chart', result)
        self.assertEqual(result['summary']['total_expense'], 30000)
        self.assertEqual(result['summary']['transaction_count'], 3)
        self.assertEqual(result['group_by'], "category")
        self.assertEqual(len(result['data']), 2)  # 2개 카테고리
        
        # 차트 데이터 검증
        self.assertEqual(result['chart']['type'], "pie")
        self.assertEqual(len(result['chart']['labels']), 2)
        self.assertEqual(len(result['chart']['values']), 2)
    
    @patch('src.financial_tools.analysis_tools._get_transaction_repository')
    @patch('src.analyzers.income_analyzer.IncomeAnalyzer.analyze')
    @patch('src.analyzers.trend_analyzer.TrendAnalyzer.analyze')
    def test_analyze_income(self, mock_trend_analyze, mock_income_analyze, mock_get_repo):
        """수입 분석 함수 테스트"""
        # 모의 객체 설정
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        
        # IncomeAnalyzer.analyze 모의 응답 설정
        mock_income_analyze.return_value = {
            'total_income': 1050000,
            'transaction_count': 2,
            'average_income': 525000,
            'daily_average': 35000,
            'monthly_estimate': 1050000,
            'by_income_type': [
                {'income_type': '월급', 'amount': 1000000, 'count': 1, 'average': 1000000, 'percentage': 95.24},
                {'income_type': '부수입', 'amount': 50000, 'count': 1, 'average': 50000, 'percentage': 4.76}
            ],
            'period_days': 30
        }
        
        # TrendAnalyzer.analyze 모의 응답 설정
        mock_trend_analyze.return_value = {
            'daily_trend': [
                {'date': '2023-01-04', 'transaction_type': 'income', 'amount': 1000000, 'count': 1},
                {'date': '2023-01-05', 'transaction_type': 'income', 'amount': 50000, 'count': 1}
            ],
            'weekly_trend': [],
            'monthly_trend': [],
            'period_days': 30
        }
        
        # 함수 호출
        result = analyze_income(
            start_date=self.start_date.isoformat(),
            end_date=self.end_date.isoformat(),
            income_type=None,
            group_by="income_type"
        )
        
        # 검증
        self.assertIn('summary', result)
        self.assertIn('data', result)
        self.assertIn('chart', result)
        self.assertEqual(result['summary']['total_income'], 1050000)
        self.assertEqual(result['summary']['transaction_count'], 2)
        self.assertEqual(result['group_by'], "income_type")
        self.assertEqual(len(result['data']), 2)  # 2개 수입 유형
        
        # 차트 데이터 검증
        self.assertEqual(result['chart']['type'], "pie")
        self.assertEqual(len(result['chart']['labels']), 2)
        self.assertEqual(len(result['chart']['values']), 2)
    
    @patch('src.financial_tools.analysis_tools._get_transaction_repository')
    @patch('src.analyzers.comparison_analyzer.ComparisonAnalyzer.compare_periods')
    def test_compare_periods(self, mock_compare_periods, mock_get_repo):
        """기간 비교 분석 함수 테스트"""
        # 모의 객체 설정
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        
        # ComparisonAnalyzer.compare_periods 모의 응답 설정
        mock_compare_periods.return_value = {
            'period1_total': 30000,
            'period2_total': 45000,
            'period1_days': 30,
            'period2_days': 30,
            'absolute_change': 15000,
            'percentage_change': 50,
            'daily_average_change': 500,
            'comparison': [
                {
                    'name': '식비',
                    'period1_amount': 25000,
                    'period2_amount': 35000,
                    'absolute_change': 10000,
                    'percentage_change': 40,
                    'is_increase': True
                },
                {
                    'name': '교통비',
                    'period1_amount': 5000,
                    'period2_amount': 10000,
                    'absolute_change': 5000,
                    'percentage_change': 100,
                    'is_increase': True
                }
            ]
        }
        
        # 함수 호출
        period1_start = (self.today - timedelta(days=60)).isoformat()
        period1_end = (self.today - timedelta(days=31)).isoformat()
        period2_start = self.start_date.isoformat()
        period2_end = self.end_date.isoformat()
        
        result = compare_periods(
            period1_start=period1_start,
            period1_end=period1_end,
            period2_start=period2_start,
            period2_end=period2_end,
            transaction_type="expense",
            group_by="category"
        )
        
        # 검증
        self.assertIn('summary', result)
        self.assertIn('comparison', result)
        self.assertIn('chart', result)
        self.assertEqual(result['summary']['period1']['total'], 30000)
        self.assertEqual(result['summary']['period2']['total'], 45000)
        self.assertEqual(result['summary']['change']['absolute'], 15000)
        self.assertEqual(result['summary']['change']['percentage'], 50)
        self.assertEqual(result['transaction_type'], "expense")
        self.assertEqual(result['group_by'], "category")
        self.assertEqual(len(result['comparison']), 2)  # 2개 카테고리
        
        # 차트 데이터 검증
        self.assertEqual(result['chart']['type'], "comparison")
        self.assertEqual(len(result['chart']['labels']), 2)
        self.assertEqual(len(result['chart']['period1_values']), 2)
        self.assertEqual(len(result['chart']['period2_values']), 2)
    
    @patch('src.financial_tools.analysis_tools._get_transaction_repository')
    @patch('src.analyzers.trend_analyzer.TrendAnalyzer.analyze_monthly_trends')
    def test_analyze_trends(self, mock_analyze_monthly_trends, mock_get_repo):
        """트렌드 분석 함수 테스트"""
        # 모의 객체 설정
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        
        # TrendAnalyzer.analyze_monthly_trends 모의 응답 설정
        mock_analyze_monthly_trends.return_value = {
            'monthly_trend': [
                {
                    'year': 2023,
                    'month': 1,
                    'year_month': '2023-01',
                    'transaction_type': 'expense',
                    'total': 30000,
                    'count': 3,
                    'average': 10000,
                    'daily_average': 1000
                },
                {
                    'year': 2023,
                    'month': 2,
                    'year_month': '2023-02',
                    'transaction_type': 'expense',
                    'total': 35000,
                    'count': 4,
                    'average': 8750,
                    'daily_average': 1250
                },
                {
                    'year': 2023,
                    'month': 3,
                    'year_month': '2023-03',
                    'transaction_type': 'expense',
                    'total': 40000,
                    'count': 5,
                    'average': 8000,
                    'daily_average': 1333
                }
            ],
            'period_months': 3
        }
        
        # 함수 호출
        result = analyze_trends(
            months=3,
            transaction_type="expense",
            category=None
        )
        
        # 검증
        self.assertIn('summary', result)
        self.assertIn('monthly_data', result)
        self.assertIn('chart', result)
        self.assertEqual(result['summary']['months_analyzed'], 3)
        self.assertEqual(result['summary']['transaction_type'], "expense")
        self.assertEqual(result['summary']['trend']['direction'], "증가")
        self.assertEqual(result['summary']['trend']['change'], 10000)  # 40000 - 30000
        self.assertEqual(len(result['monthly_data']), 3)  # 3개월
        
        # 차트 데이터 검증
        self.assertEqual(result['chart']['type'], "line")
        self.assertEqual(len(result['chart']['labels']), 3)
        self.assertEqual(len(result['chart']['values']), 3)
        self.assertEqual(result['chart']['min_value'], 30000)
        self.assertEqual(result['chart']['max_value'], 40000)
    
    @patch('src.financial_tools.analysis_tools._get_transaction_repository')
    @patch('src.analyzers.expense_analyzer.ExpenseAnalyzer.analyze')
    @patch('src.analyzers.income_analyzer.IncomeAnalyzer.analyze')
    def test_get_financial_summary(self, mock_income_analyze, mock_expense_analyze, mock_get_repo):
        """재정 요약 정보 함수 테스트"""
        # 모의 객체 설정
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        
        # ExpenseAnalyzer.analyze 모의 응답 설정
        mock_expense_analyze.return_value = {
            'total_expense': 30000,
            'transaction_count': 3,
            'average_expense': 10000,
            'daily_average': 1000,
            'monthly_estimate': 30000,
            'by_payment_method': [
                {'payment_method': '카드', 'amount': 30000, 'count': 3, 'average': 10000, 'percentage': 100}
            ],
            'by_category': [
                {'category': '식비', 'amount': 25000, 'count': 2, 'average': 12500, 'percentage': 83.33},
                {'category': '교통비', 'amount': 5000, 'count': 1, 'average': 5000, 'percentage': 16.67}
            ],
            'daily_trend': [],
            'period_days': 30
        }
        
        # IncomeAnalyzer.analyze 모의 응답 설정
        mock_income_analyze.return_value = {
            'total_income': 1050000,
            'transaction_count': 2,
            'average_income': 525000,
            'daily_average': 35000,
            'monthly_estimate': 1050000,
            'by_income_type': [
                {'income_type': '월급', 'amount': 1000000, 'count': 1, 'average': 1000000, 'percentage': 95.24},
                {'income_type': '부수입', 'amount': 50000, 'count': 1, 'average': 50000, 'percentage': 4.76}
            ],
            'period_days': 30
        }
        
        # 함수 호출
        result = get_financial_summary(
            start_date=self.start_date.isoformat(),
            end_date=self.end_date.isoformat()
        )
        
        # 검증
        self.assertIn('period', result)
        self.assertIn('income', result)
        self.assertIn('expense', result)
        self.assertIn('balance', result)
        self.assertEqual(result['period']['days'], 30)
        self.assertEqual(result['income']['total'], 1050000)
        self.assertEqual(result['expense']['total'], 30000)
        self.assertEqual(result['balance']['net_cash_flow'], 1020000)  # 1050000 - 30000
        self.assertEqual(result['balance']['is_positive'], True)
        
        # 저축률 검증 (순현금흐름 / 총수입)
        expected_savings_rate = 1020000 / 1050000 * 100  # 약 97.14%
        self.assertAlmostEqual(result['balance']['savings_rate'], expected_savings_rate, places=2)
    
    def test_prepare_chart_data(self):
        """차트 데이터 변환 함수 테스트"""
        # 테스트 데이터
        pie_data = [
            {'category': '식비', 'amount': 25000, 'count': 2},
            {'category': '교통비', 'amount': 5000, 'count': 1}
        ]
        
        bar_data = [
            {'year_month': '2023-01', 'total': 30000},
            {'year_month': '2023-02', 'total': 35000},
            {'year_month': '2023-03', 'total': 40000}
        ]
        
        line_data = [
            {'date': '2023-01-01', 'amount': 10000},
            {'date': '2023-01-02', 'amount': 15000},
            {'date': '2023-01-03', 'amount': 5000}
        ]
        
        # 파이 차트 테스트
        pie_chart = _prepare_chart_data(pie_data, "pie")
        self.assertEqual(pie_chart['type'], "pie")
        self.assertEqual(len(pie_chart['labels']), 2)
        self.assertEqual(len(pie_chart['values']), 2)
        self.assertEqual(pie_chart['total'], 30000)
        
        # 막대 차트 테스트
        bar_chart = _prepare_chart_data(bar_data, "bar")
        self.assertEqual(bar_chart['type'], "bar")
        self.assertEqual(len(bar_chart['labels']), 3)
        self.assertEqual(len(bar_chart['values']), 3)
        self.assertEqual(bar_chart['max_value'], 40000)
        
        # 라인 차트 테스트
        line_chart = _prepare_chart_data(line_data, "line")
        self.assertEqual(line_chart['type'], "line")
        self.assertEqual(len(line_chart['labels']), 3)
        self.assertEqual(len(line_chart['values']), 3)
        self.assertEqual(line_chart['min_value'], 5000)
        self.assertEqual(line_chart['max_value'], 15000)
        
        # 기본 데이터 형식 테스트
        raw_chart = _prepare_chart_data(line_data, "unknown")
        self.assertEqual(raw_chart['type'], "raw")
        self.assertEqual(raw_chart['data'], line_data)


if __name__ == '__main__':
    unittest.main()