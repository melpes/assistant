# -*- coding: utf-8 -*-
"""
Transaction 엔티티 클래스 테스트
"""

import unittest
from datetime import date, datetime
from decimal import Decimal

from src.models.transaction import Transaction


class TestTransaction(unittest.TestCase):
    """Transaction 클래스 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.valid_transaction_data = {
            'transaction_id': 'test-123',
            'transaction_date': date(2025, 7, 21),
            'description': '테스트 거래',
            'amount': Decimal('10000.00'),
            'transaction_type': Transaction.TYPE_EXPENSE,
            'source': 'test',
            'category': '식비',
            'payment_method': '체크카드'
        }

    def test_create_valid_transaction(self):
        """유효한 데이터로 거래 객체 생성 테스트"""
        transaction = Transaction(**self.valid_transaction_data)
        
        self.assertEqual(transaction.transaction_id, 'test-123')
        self.assertEqual(transaction.transaction_date, date(2025, 7, 21))
        self.assertEqual(transaction.description, '테스트 거래')
        self.assertEqual(transaction.amount, Decimal('10000.00'))
        self.assertEqual(transaction.transaction_type, Transaction.TYPE_EXPENSE)
        self.assertEqual(transaction.source, 'test')
        self.assertEqual(transaction.category, '식비')
        self.assertEqual(transaction.payment_method, '체크카드')
        self.assertFalse(transaction.is_excluded)
        self.assertIsNotNone(transaction.created_at)
        self.assertIsNotNone(transaction.updated_at)

    def test_invalid_transaction_id(self):
        """유효하지 않은 거래 ID로 객체 생성 시 예외 발생 테스트"""
        invalid_data = self.valid_transaction_data.copy()
        invalid_data['transaction_id'] = 'invalid id with spaces'
        
        with self.assertRaises(ValueError):
            Transaction(**invalid_data)

    def test_missing_required_fields(self):
        """필수 필드 누락 시 예외 발생 테스트"""
        required_fields = ['transaction_id', 'transaction_date', 'description', 'amount', 'transaction_type', 'source']
        
        for field in required_fields:
            invalid_data = self.valid_transaction_data.copy()
            invalid_data[field] = None
            
            with self.assertRaises(ValueError):
                Transaction(**invalid_data)

    def test_invalid_transaction_type(self):
        """유효하지 않은 거래 유형으로 객체 생성 시 예외 발생 테스트"""
        invalid_data = self.valid_transaction_data.copy()
        invalid_data['transaction_type'] = 'invalid_type'
        
        with self.assertRaises(ValueError):
            Transaction(**invalid_data)

    def test_update_category(self):
        """카테고리 업데이트 테스트"""
        transaction = Transaction(**self.valid_transaction_data)
        original_updated_at = transaction.updated_at
        
        # 잠시 대기하여 업데이트 시간 차이 보장
        import time
        time.sleep(0.001)
        
        transaction.update_category('생활용품')
        
        self.assertEqual(transaction.category, '생활용품')
        self.assertGreater(transaction.updated_at, original_updated_at)

    def test_update_payment_method(self):
        """결제 방식 업데이트 테스트"""
        transaction = Transaction(**self.valid_transaction_data)
        original_updated_at = transaction.updated_at
        
        # 잠시 대기하여 업데이트 시간 차이 보장
        import time
        time.sleep(0.001)
        
        transaction.update_payment_method('신용카드')
        
        self.assertEqual(transaction.payment_method, '신용카드')
        self.assertGreater(transaction.updated_at, original_updated_at)

    def test_exclude_from_analysis(self):
        """분석 제외 설정 테스트"""
        transaction = Transaction(**self.valid_transaction_data)
        
        self.assertFalse(transaction.is_excluded)
        
        transaction.exclude_from_analysis()
        self.assertTrue(transaction.is_excluded)
        
        transaction.exclude_from_analysis(False)
        self.assertFalse(transaction.is_excluded)

    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        transaction = Transaction(**self.valid_transaction_data)
        transaction_dict = transaction.to_dict()
        
        self.assertEqual(transaction_dict['transaction_id'], 'test-123')
        self.assertEqual(transaction_dict['transaction_date'], date(2025, 7, 21).isoformat())
        self.assertEqual(transaction_dict['description'], '테스트 거래')
        self.assertEqual(transaction_dict['amount'], str(Decimal('10000.00')))
        self.assertEqual(transaction_dict['transaction_type'], Transaction.TYPE_EXPENSE)
        self.assertEqual(transaction_dict['category'], '식비')
        self.assertEqual(transaction_dict['payment_method'], '체크카드')

    def test_from_dict(self):
        """딕셔너리에서 객체 생성 테스트"""
        transaction_dict = {
            'transaction_id': 'dict-123',
            'transaction_date': '2025-07-21',
            'description': '딕셔너리 테스트',
            'amount': '5000.50',
            'transaction_type': Transaction.TYPE_INCOME,
            'source': 'dict_test',
            'created_at': '2025-07-21T12:00:00',
            'updated_at': '2025-07-21T12:00:00'
        }
        
        transaction = Transaction.from_dict(transaction_dict)
        
        self.assertEqual(transaction.transaction_id, 'dict-123')
        self.assertEqual(transaction.transaction_date, date(2025, 7, 21))
        self.assertEqual(transaction.description, '딕셔너리 테스트')
        self.assertEqual(transaction.amount, Decimal('5000.50'))
        self.assertEqual(transaction.transaction_type, Transaction.TYPE_INCOME)
        self.assertEqual(transaction.source, 'dict_test')
        self.assertEqual(transaction.created_at, datetime(2025, 7, 21, 12, 0, 0))
        self.assertEqual(transaction.updated_at, datetime(2025, 7, 21, 12, 0, 0))


if __name__ == '__main__':
    unittest.main()
