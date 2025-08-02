# -*- coding: utf-8 -*-
"""
지출 분석기 테스트
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.models import Transaction
from src.analyzers import ExpenseAnalyzer
from src.repositories.transaction_repository import TransactionRepository


class TestExpenseAnalyzer(unittest.TestCase):
    """지출 분석기 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.repository = MagicMock(spec=TransactionRepository)
        self.analyzer = ExpenseAnalyzer(self.repository)
        
        # 테스트 데이터 설정
        self.today = datetime.now().date()
        self.start_date = self.today - timedelta(days=30)
        self.end_date = self.today
        
        # 테스트 거래 데이터
        self.test_transactions = [
            Transaction(
                transaction_id="exp1",
                transaction_date=self.today - timedelta(days=5),
                description="식당 결제",
                amount=Decimal("25000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="식비",
                payment_method="체크카드",
                source="toss_card",
                account_type="일반"
            ),
            Transaction(
                transaction_id="exp2",
                transaction_date=self.today - timedelta(days=3),
                description="마트 결제",
                amount=Decimal("45000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="생활용품",
                payment_method="체크카드",
                source="toss_card",
                account_type="일반"
            ),
            Transaction(
                transaction_id="exp3",
                transaction_date=self.today - timedelta(days=1),
                description="교통비",
                amount=Decimal("5000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="교통비",
                payment_method="현금",
                source="manual",
                account_type=None
            )
        ]
    
    def test_analyze_with_data(self):
        """데이터가 있는 경우 분석 테스트"""
        # 모의 객체 설정
        self.repository.list.return_value = self.test_transactions
        
        # 분석 실행
        result = self.analyzer.analyze(self.start_date, self.end_date)
        
        # 검증
        self.repository.list.assert_called_once()
        self.assertEqual(result['total_expense'], 75000.0)
        self.assertEqual(result['transaction_count'], 3)
        self.assertEqual(result['average_expense'], 25000.0)
        
        # 카테고리별 분석 검증
        categories = {item['category']: item for item in result['by_category']}
        self.assertEqual(len(categories), 3)
        self.assertEqual(categories['생활용품']['amount'], 45000.0)
        self.assertEqual(categories['식비']['amount'], 25000.0)
        self.assertEqual(categories['교통비']['amount'], 5000.0)
        
        # 결제 방식별 분석 검증
        payment_methods = {item['payment_method']: item for item in result['by_payment_method']}
        self.assertEqual(len(payment_methods), 2)
        self.assertEqual(payment_methods['체크카드']['amount'], 70000.0)
        self.assertEqual(payment_methods['현금']['amount'], 5000.0)
    
    def test_analyze_without_data(self):
        """데이터가 없는 경우 분석 테스트"""
        # 모의 객체 설정
        self.repository.list.return_value = []
        
        # 분석 실행
        result = self.analyzer.analyze(self.start_date, self.end_date)
        
        # 검증
        self.repository.list.assert_called_once()
        self.assertEqual(result['total_expense'], 0)
        self.assertEqual(result['transaction_count'], 0)
        self.assertEqual(result['average_expense'], 0)
        self.assertEqual(result['by_category'], [])
        self.assertEqual(result['by_payment_method'], [])
    
    def test_analyze_by_period(self):
        """기간별 분석 테스트"""
        # 모의 객체 설정
        self.repository.list.return_value = self.test_transactions
        
        # 분석 실행
        result = self.analyzer.analyze_by_period(days=7)
        
        # 검증
        self.repository.list.assert_called_once()
        self.assertEqual(result['total_expense'], 75000.0)
    
    def test_analyze_by_category(self):
        """카테고리별 분석 테스트"""
        # 모의 객체 설정
        self.repository.list.return_value = [self.test_transactions[0]]  # 식비 카테고리만
        
        # 분석 실행
        result = self.analyzer.analyze_by_category("식비", self.start_date, self.end_date)
        
        # 검증
        self.repository.list.assert_called_once()
        self.assertEqual(result['total_expense'], 25000.0)
        self.assertEqual(result['transaction_count'], 1)
    
    def test_find_regular_expenses(self):
        """정기 지출 찾기 테스트"""
        # 정기 지출 테스트 데이터
        regular_transactions = [
            Transaction(
                transaction_id=f"reg{i}",
                transaction_date=self.today - timedelta(days=i*30),
                description="월세",
                amount=Decimal("500000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="주거비",
                payment_method="계좌이체",
                source="toss_account",
                account_type="일반"
            ) for i in range(1, 4)  # 3개월치 월세
        ]
        
        # 모의 객체 설정
        self.repository.list.return_value = regular_transactions
        
        # 정기 지출 찾기 실행
        result = self.analyzer.find_regular_expenses()
        
        # 검증
        self.repository.list.assert_called_once()
        self.assertEqual(len(result), 1)  # 하나의 정기 지출 패턴
        self.assertEqual(result[0]['description'], "월세")
        self.assertEqual(result[0]['amount'], 500000.0)
        self.assertEqual(result[0]['frequency'], 3)


if __name__ == '__main__':
    unittest.main()