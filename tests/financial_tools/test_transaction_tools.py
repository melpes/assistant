# -*- coding: utf-8 -*-
"""
거래 조회 도구 테스트 모듈
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timedelta
from decimal import Decimal

from src.financial_tools.transaction_tools import (
    list_transactions, get_transaction_details, search_transactions,
    get_available_categories, get_available_payment_methods, get_transaction_date_range
)
from src.models.transaction import Transaction


class TestTransactionTools(unittest.TestCase):
    """거래 조회 도구 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트용 거래 객체 생성
        self.test_transactions = [
            Transaction(
                id=1,
                transaction_id="test-tx-1",
                transaction_date=date.today() - timedelta(days=5),
                description="테스트 거래 1",
                amount=Decimal("50000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="식비",
                payment_method="체크카드",
                source="test",
                account_type=None,
                memo="테스트 메모 1"
            ),
            Transaction(
                id=2,
                transaction_id="test-tx-2",
                transaction_date=date.today() - timedelta(days=3),
                description="테스트 거래 2",
                amount=Decimal("100000"),
                transaction_type=Transaction.TYPE_INCOME,
                category="급여",
                payment_method=None,
                source="test",
                account_type="입출금계좌",
                memo="테스트 메모 2"
            )
        ]
    
    @patch('src.financial_tools.transaction_tools._get_transaction_repository')
    def test_list_transactions(self, mock_get_repo):
        """list_transactions 함수 테스트"""
        # Mock 설정
        mock_repo = MagicMock()
        mock_repo.list.return_value = self.test_transactions
        mock_repo.count.return_value = len(self.test_transactions)
        mock_get_repo.return_value = mock_repo
        
        # 함수 호출
        result = list_transactions(
            start_date=date.today().isoformat(),
            end_date=(date.today() + timedelta(days=1)).isoformat(),
            category="식비",
            limit=10
        )
        
        # 검증
        self.assertIn("transactions", result)
        self.assertIn("summary", result)
        self.assertIn("pagination", result)
        self.assertEqual(len(result["transactions"]), 2)
        self.assertEqual(result["pagination"]["total"], 2)
        self.assertEqual(result["pagination"]["limit"], 10)
        self.assertFalse(result["pagination"]["has_more"])
        
        # Mock 호출 검증
        mock_repo.list.assert_called_once()
        mock_repo.count.assert_called_once()
    
    @patch('src.financial_tools.transaction_tools._get_transaction_repository')
    def test_list_transactions_with_invalid_date(self, mock_get_repo):
        """list_transactions 함수 - 유효하지 않은 날짜 테스트"""
        # 함수 호출
        result = list_transactions(start_date="invalid-date")
        
        # 검증
        self.assertIn("error", result)
        self.assertEqual(len(result["transactions"]), 0)
        
        # Mock 호출 검증
        mock_get_repo.assert_not_called()
    
    @patch('src.financial_tools.transaction_tools._get_transaction_repository')
    def test_get_transaction_details(self, mock_get_repo):
        """get_transaction_details 함수 테스트"""
        # Mock 설정
        mock_repo = MagicMock()
        mock_repo.read_by_transaction_id.return_value = self.test_transactions[0]
        mock_get_repo.return_value = mock_repo
        
        # 함수 호출
        result = get_transaction_details("test-tx-1")
        
        # 검증
        self.assertIn("transaction", result)
        self.assertEqual(result["transaction"]["transaction_id"], "test-tx-1")
        self.assertEqual(result["transaction"]["description"], "테스트 거래 1")
        
        # Mock 호출 검증
        mock_repo.read_by_transaction_id.assert_called_once_with("test-tx-1")
    
    @patch('src.financial_tools.transaction_tools._get_transaction_repository')
    def test_get_transaction_details_not_found(self, mock_get_repo):
        """get_transaction_details 함수 - 거래 없음 테스트"""
        # Mock 설정
        mock_repo = MagicMock()
        mock_repo.read_by_transaction_id.return_value = None
        mock_get_repo.return_value = mock_repo
        
        # 함수 호출
        result = get_transaction_details("non-existent")
        
        # 검증
        self.assertIn("error", result)
        self.assertIsNone(result["transaction"])
        
        # Mock 호출 검증
        mock_repo.read_by_transaction_id.assert_called_once_with("non-existent")
    
    @patch('src.financial_tools.transaction_tools._get_transaction_repository')
    def test_search_transactions(self, mock_get_repo):
        """search_transactions 함수 테스트"""
        # Mock 설정
        mock_repo = MagicMock()
        mock_repo.list.return_value = self.test_transactions
        mock_repo.count.return_value = len(self.test_transactions)
        mock_get_repo.return_value = mock_repo
        
        # 함수 호출
        result = search_transactions("테스트", limit=10)
        
        # 검증
        self.assertIn("transactions", result)
        self.assertIn("summary", result)
        self.assertIn("pagination", result)
        self.assertEqual(len(result["transactions"]), 2)
        self.assertEqual(result["pagination"]["total"], 2)
        
        # Mock 호출 검증
        mock_repo.list.assert_called_once()
        mock_repo.count.assert_called_once()
    
    @patch('src.financial_tools.transaction_tools._get_transaction_repository')
    def test_search_transactions_short_query(self, mock_get_repo):
        """search_transactions 함수 - 짧은 검색어 테스트"""
        # 함수 호출
        result = search_transactions("a")
        
        # 검증
        self.assertIn("error", result)
        self.assertEqual(len(result["transactions"]), 0)
        
        # Mock 호출 검증
        mock_get_repo.assert_not_called()
    
    @patch('src.financial_tools.transaction_tools._get_transaction_repository')
    def test_get_available_categories(self, mock_get_repo):
        """get_available_categories 함수 테스트"""
        # Mock 설정
        mock_repo = MagicMock()
        mock_repo.get_categories.return_value = ["식비", "교통비", "생활용품", "급여"]
        mock_get_repo.return_value = mock_repo
        
        # 함수 호출
        result = get_available_categories()
        
        # 검증
        self.assertIn("categories", result)
        self.assertEqual(len(result["categories"]), 4)
        self.assertEqual(result["count"], 4)
        
        # Mock 호출 검증
        mock_repo.get_categories.assert_called_once()
    
    @patch('src.financial_tools.transaction_tools._get_transaction_repository')
    def test_get_available_payment_methods(self, mock_get_repo):
        """get_available_payment_methods 함수 테스트"""
        # Mock 설정
        mock_repo = MagicMock()
        mock_repo.get_payment_methods.return_value = ["체크카드", "신용카드", "계좌이체", "현금"]
        mock_get_repo.return_value = mock_repo
        
        # 함수 호출
        result = get_available_payment_methods()
        
        # 검증
        self.assertIn("payment_methods", result)
        self.assertEqual(len(result["payment_methods"]), 4)
        self.assertEqual(result["count"], 4)
        
        # Mock 호출 검증
        mock_repo.get_payment_methods.assert_called_once()
    
    @patch('src.financial_tools.transaction_tools._get_transaction_repository')
    def test_get_transaction_date_range(self, mock_get_repo):
        """get_transaction_date_range 함수 테스트"""
        # Mock 설정
        mock_repo = MagicMock()
        min_date = date(2023, 1, 1)
        max_date = date(2023, 12, 31)
        mock_repo.get_date_range.return_value = (min_date, max_date)
        mock_get_repo.return_value = mock_repo
        
        # 함수 호출
        result = get_transaction_date_range()
        
        # 검증
        self.assertIn("date_range", result)
        self.assertEqual(result["date_range"]["start"], "2023-01-01")
        self.assertEqual(result["date_range"]["end"], "2023-12-31")
        self.assertTrue(result["has_data"])
        
        # Mock 호출 검증
        mock_repo.get_date_range.assert_called_once()
    
    @patch('src.financial_tools.transaction_tools._get_transaction_repository')
    def test_get_transaction_date_range_no_data(self, mock_get_repo):
        """get_transaction_date_range 함수 - 데이터 없음 테스트"""
        # Mock 설정
        mock_repo = MagicMock()
        mock_repo.get_date_range.return_value = (None, None)
        mock_get_repo.return_value = mock_repo
        
        # 함수 호출
        result = get_transaction_date_range()
        
        # 검증
        self.assertIn("date_range", result)
        self.assertIsNone(result["date_range"]["start"])
        self.assertIsNone(result["date_range"]["end"])
        self.assertFalse(result["has_data"])
        
        # Mock 호출 검증
        mock_repo.get_date_range.assert_called_once()


if __name__ == '__main__':
    unittest.main()