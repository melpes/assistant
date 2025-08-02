# -*- coding: utf-8 -*-
"""
수입 분석기 테스트
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.models import Transaction
from src.analyzers import IncomeAnalyzer
from src.repositories.transaction_repository import TransactionRepository


class TestIncomeAnalyzer(unittest.TestCase):
    """수입 분석기 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.repository = MagicMock(spec=TransactionRepository)
        self.analyzer = IncomeAnalyzer(self.repository)
        
        # 테스트 데이터 설정
        self.today = datetime.now().date()
        self.start_date = self.today - timedelta(days=30)
        self.end_date = self.today
        
        # 테스트 거래 데이터
        self.test_transactions = [
            Transaction(
                transaction_id="inc1",
                transaction_date=self.today - timedelta(days=25),
                description="급여",
                amount=Decimal("3000000"),
                transaction_type=Transaction.TYPE_INCOME,
                category="급여",
                source="toss_account",
                account_type="일반"
            ),
            Transaction(
                transaction_id="inc2",
                transaction_date=self.today - timedelta(days=15),
                description="이자 수입",
                amount=Decimal("5000"),
                transaction_type=Transaction.TYPE_INCOME,
                category="이자",
                source="toss_account",
                account_type="일반"
            ),
            Transaction(
                transaction_id="inc3",
                transaction_date=self.today - timedelta(days=5),
                description="용돈",
                amount=Decimal("100000"),
                transaction_type=Transaction.TYPE_INCOME,
                category="용돈",
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
        self.assertEqual(result['total_income'], 3105000.0)
        self.assertEqual(result['transaction_count'], 3)
        self.assertEqual(result['average_income'], 1035000.0)
        
        # 카테고리별 분석 검증
        categories = {item['category']: item for item in result['by_category']}
        self.assertEqual(len(categories), 3)
        self.assertEqual(categories['급여']['amount'], 3000000.0)
        self.assertEqual(categories['이자']['amount'], 5000.0)
        self.assertEqual(categories['용돈']['amount'], 100000.0)
        
        # 소스별 분석 검증
        sources = {item['source']: item for item in result['by_source']}
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources['toss_account']['amount'], 3005000.0)
        self.assertEqual(sources['manual']['amount'], 100000.0)
    
    def test_analyze_without_data(self):
        """데이터가 없는 경우 분석 테스트"""
        # 모의 객체 설정
        self.repository.list.return_value = []
        
        # 분석 실행
        result = self.analyzer.analyze(self.start_date, self.end_date)
        
        # 검증
        self.repository.list.assert_called_once()
        self.assertEqual(result['total_income'], 0)
        self.assertEqual(result['transaction_count'], 0)
        self.assertEqual(result['average_income'], 0)
        self.assertEqual(result['by_category'], [])
        self.assertEqual(result['by_source'], [])
    
    def test_analyze_by_period(self):
        """기간별 분석 테스트"""
        # 모의 객체 설정
        self.repository.list.return_value = self.test_transactions
        
        # 분석 실행
        result = self.analyzer.analyze_by_period(days=30)
        
        # 검증
        self.repository.list.assert_called_once()
        self.assertEqual(result['total_income'], 3105000.0)
    
    def test_analyze_by_category(self):
        """카테고리별 분석 테스트"""
        # 모의 객체 설정
        self.repository.list.return_value = [self.test_transactions[0]]  # 급여 카테고리만
        
        # 분석 실행
        result = self.analyzer.analyze_by_category("급여", self.start_date, self.end_date)
        
        # 검증
        self.repository.list.assert_called_once()
        self.assertEqual(result['total_income'], 3000000.0)
        self.assertEqual(result['transaction_count'], 1)
    
    def test_find_regular_income(self):
        """정기 수입 찾기 테스트"""
        # 정기 수입 테스트 데이터
        regular_transactions = [
            Transaction(
                transaction_id=f"sal{i}",
                transaction_date=self.today - timedelta(days=i*30),
                description="월급",
                amount=Decimal("3000000"),
                transaction_type=Transaction.TYPE_INCOME,
                category="급여",
                source="toss_account",
                account_type="일반"
            ) for i in range(1, 4)  # 3개월치 급여
        ]
        
        # 모의 객체 설정
        self.repository.list.return_value = regular_transactions
        
        # 정기 수입 찾기 실행
        result = self.analyzer.find_regular_income()
        
        # 검증
        self.repository.list.assert_called_once()
        self.assertEqual(len(result), 1)  # 하나의 정기 수입 패턴
        self.assertEqual(result[0]['description'], "월급")
        self.assertEqual(result[0]['amount'], 3000000.0)
        self.assertEqual(result[0]['frequency'], 3)


if __name__ == '__main__':
    unittest.main()