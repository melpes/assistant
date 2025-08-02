# -*- coding: utf-8 -*-
"""
수입 분석 도구 테스트

수입 분석 및 수입-지출 비교 관련 도구 함수들을 테스트합니다.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from decimal import Decimal

from src.financial_tools.analysis_tools import (
    analyze_income,
    analyze_income_patterns,
    compare_income_expense
)
from src.models import Transaction


class TestIncomeAnalysisTools(unittest.TestCase):
    """수입 분석 도구 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트용 날짜
        self.today = date.today()
        self.start_date = self.today - timedelta(days=180)  # 6개월
        self.end_date = self.today
        
        # 테스트용 거래 데이터
        self.test_transactions = [
            self._create_mock_transaction(1, "월급", None, 3000000, "income"),
            self._create_mock_transaction(2, "이자수입", None, 50000, "income"),
            self._create_mock_transaction(3, "부수입", None, 100000, "income"),
            self._create_mock_transaction(4, "식비", "카드", 50000, "expense"),
            self._create_mock_transaction(5, "교통비", "카드", 30000, "expense")
        ]
    
    def _create_mock_transaction(self, id, category, payment_method, amount, tx_type):
        """테스트용 거래 객체 생성"""
        tx = MagicMock(spec=Transaction)
        tx.id = id
        tx.transaction_id = f"TX{id}"
        tx.transaction_date = self.today - timedelta(days=id * 30)
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
    @patch('src.analyzers.income_analyzer.IncomeAnalyzer.find_regular_income')
    def test_analyze_income_patterns(self, mock_find_regular_income, mock_get_repo):
        """수입 패턴 분석 함수 테스트"""
        # 모의 객체 설정
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        
        # IncomeAnalyzer.find_regular_income 모의 응답 설정
        mock_find_regular_income.return_value = [
            {
                'description': '월급',
                'amount': 3000000.0,
                'frequency': 6,
                'first_date': '2023-01-01',
                'last_date': '2023-06-01',
                'avg_interval_days': 30.0,
                'category': '월급',
                'source': '회사'
            },
            {
                'description': '이자수입',
                'amount': 50000.0,
                'frequency': 3,
                'first_date': '2023-01-15',
                'last_date': '2023-03-15',
                'avg_interval_days': 30.0,
                'category': '이자수입',
                'source': '은행'
            }
        ]
        
        # 함수 호출
        result = analyze_income_patterns(
            min_frequency=2,
            min_amount=10000,
            max_months=12
        )
        
        # 검증
        self.assertIn('summary', result)
        self.assertIn('regular_patterns', result)
        self.assertIn('monthly_estimates', result)
        self.assertIn('chart', result)
        self.assertEqual(result['summary']['total_patterns_found'], 2)
        self.assertEqual(result['summary']['total_regular_income'], 3050000.0)
        self.assertEqual(len(result['regular_patterns']), 2)
        self.assertEqual(len(result['monthly_estimates']), 2)
        
        # 월간 예상 수입 검증
        monthly_estimates = {item['description']: item for item in result['monthly_estimates']}
        self.assertEqual(monthly_estimates['월급']['monthly_amount'], 3000000.0)
        self.assertEqual(monthly_estimates['이자수입']['monthly_amount'], 50000.0)
        
        # 차트 데이터 검증
        self.assertEqual(result['chart']['type'], "bar")
        self.assertEqual(len(result['chart']['labels']), 2)
        self.assertEqual(len(result['chart']['values']), 2)
    
    @patch('src.financial_tools.analysis_tools._get_transaction_repository')
    @patch('src.analyzers.integrated_analyzer.IntegratedAnalyzer.compare_income_expense')
    def test_compare_income_expense(self, mock_compare_income_expense, mock_get_repo):
        """수입-지출 비교 함수 테스트"""
        # 모의 객체 설정
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        
        # IntegratedAnalyzer.compare_income_expense 모의 응답 설정
        mock_compare_income_expense.return_value = {
            'monthly_comparison': [
                {
                    'year': 2023,
                    'month': 1,
                    'period': '2023-01',
                    'income': 3050000.0,
                    'expense': 80000.0,
                    'income_count': 2,
                    'expense_count': 2
                },
                {
                    'year': 2023,
                    'month': 2,
                    'period': '2023-02',
                    'income': 3000000.0,
                    'expense': 85000.0,
                    'income_count': 1,
                    'expense_count': 2
                },
                {
                    'year': 2023,
                    'month': 3,
                    'period': '2023-03',
                    'income': 3050000.0,
                    'expense': 75000.0,
                    'income_count': 2,
                    'expense_count': 2
                }
            ],
            'weekly_comparison': [],
            'daily_comparison': []
        }
        
        # 함수 호출
        result = compare_income_expense(
            start_date=self.start_date.isoformat(),
            end_date=self.end_date.isoformat(),
            group_by="monthly"
        )
        
        # 검증
        self.assertIn('summary', result)
        self.assertIn('time_series', result)
        self.assertIn('chart', result)
        self.assertEqual(result['group_by'], "monthly")
        self.assertEqual(result['time_unit'], "월별")
        self.assertEqual(len(result['time_series']), 3)
        
        # 순 현금 흐름 계산 검증
        time_series = result['time_series']
        self.assertEqual(time_series[0]['net_cash_flow'], 2970000.0)  # 3050000 - 80000
        self.assertEqual(time_series[0]['is_positive'], True)
        self.assertAlmostEqual(time_series[0]['savings_rate'], 97.38, places=2)  # (3050000 - 80000) / 3050000 * 100
        
        # 전체 요약 검증
        self.assertEqual(result['summary']['total_income'], 9100000.0)
        self.assertEqual(result['summary']['total_expense'], 240000.0)
        self.assertEqual(result['summary']['net_cash_flow'], 8860000.0)
        self.assertAlmostEqual(result['summary']['savings_rate'], 97.36, places=2)
        self.assertEqual(result['summary']['is_positive'], True)
        
        # 차트 데이터 검증
        self.assertEqual(result['chart']['type'], "cash_flow")
        self.assertEqual(len(result['chart']['labels']), 3)
        self.assertEqual(len(result['chart']['income_values']), 3)
        self.assertEqual(len(result['chart']['expense_values']), 3)
        self.assertEqual(len(result['chart']['net_values']), 3)


if __name__ == '__main__':
    unittest.main()