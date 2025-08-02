# -*- coding: utf-8 -*-
"""
트렌드 분석기 테스트
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.models import Transaction
from src.analyzers import TrendAnalyzer
from src.repositories.transaction_repository import TransactionRepository


class TestTrendAnalyzer(unittest.TestCase):
    """트렌드 분석기 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.repository = MagicMock(spec=TransactionRepository)
        self.analyzer = TrendAnalyzer(self.repository)
        
        # 테스트 데이터 설정
        self.today = datetime.now().date()
        
        # 테스트 거래 데이터 - 3개월치 데이터
        self.test_transactions = []
        
        # 지출 데이터
        for i in range(90):
            self.test_transactions.append(
                Transaction(
                    transaction_id=f"exp{i}",
                    transaction_date=self.today - timedelta(days=i),
                    description=f"지출 {i}",
                    amount=Decimal(str(1000 + i * 100)),
                    transaction_type=Transaction.TYPE_EXPENSE,
                    category="식비" if i % 3 == 0 else "생활용품" if i % 3 == 1 else "교통비",
                    payment_method="체크카드" if i % 2 == 0 else "현금",
                    source="toss_card" if i % 2 == 0 else "manual",
                    account_type="일반"
                )
            )
        
        # 수입 데이터
        for i in range(3):
            self.test_transactions.append(
                Transaction(
                    transaction_id=f"inc{i}",
                    transaction_date=self.today - timedelta(days=i*30),
                    description="급여",
                    amount=Decimal("3000000"),
                    transaction_type=Transaction.TYPE_INCOME,
                    category="급여",
                    source="toss_account",
                    account_type="일반"
                )
            )
    
    def test_analyze_with_data(self):
        """데이터가 있는 경우 분석 테스트"""
        # 모의 객체 설정
        self.repository.list.return_value = self.test_transactions
        
        # 분석 실행
        start_date = self.today - timedelta(days=90)
        end_date = self.today
        result = self.analyzer.analyze(start_date, end_date)
        
        # 검증
        self.repository.list.assert_called_once()
        
        # 일별 트렌드 검증
        self.assertTrue(len(result['daily_trend']) > 0)
        
        # 주별 트렌드 검증
        self.assertTrue(len(result['weekly_trend']) > 0)
        
        # 월별 트렌드 검증
        self.assertTrue(len(result['monthly_trend']) > 0)
    
    def test_analyze_without_data(self):
        """데이터가 없는 경우 분석 테스트"""
        # 모의 객체 설정
        self.repository.list.return_value = []
        
        # 분석 실행
        start_date = self.today - timedelta(days=90)
        end_date = self.today
        result = self.analyzer.analyze(start_date, end_date)
        
        # 검증
        self.repository.list.assert_called_once()
        self.assertEqual(result['daily_trend'], [])
        self.assertEqual(result['weekly_trend'], [])
        self.assertEqual(result['monthly_trend'], [])
    
    def test_analyze_monthly_trends(self):
        """월별 트렌드 분석 테스트"""
        # 모의 객체 설정
        self.repository.list.return_value = self.test_transactions
        
        # 분석 실행
        result = self.analyzer.analyze_monthly_trends(months=3)
        
        # 검증
        self.repository.list.assert_called_once()
        self.assertTrue(len(result['monthly_trend']) > 0)
    
    def test_analyze_cash_flow(self):
        """현금 흐름 분석 테스트"""
        # 모의 객체 설정
        self.repository.list.side_effect = [
            # 수입 데이터 반환
            [tx for tx in self.test_transactions if tx.transaction_type == Transaction.TYPE_INCOME],
            # 지출 데이터 반환
            [tx for tx in self.test_transactions if tx.transaction_type == Transaction.TYPE_EXPENSE]
        ]
        
        # 분석 실행
        result = self.analyzer.analyze_cash_flow(months=3)
        
        # 검증
        self.assertEqual(self.repository.list.call_count, 2)
        self.assertTrue(len(result['cash_flow']) > 0)
        
        # 현금 흐름 검증
        for item in result['cash_flow']:
            self.assertTrue('income' in item)
            self.assertTrue('expense' in item)
            self.assertTrue('net_flow' in item)
            self.assertTrue('is_positive' in item)


if __name__ == '__main__':
    unittest.main()