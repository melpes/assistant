# -*- coding: utf-8 -*-
"""
TransactionRepository 테스트
"""

import os
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
import tempfile

from src.models import Transaction
from src.repositories.db_connection import DatabaseConnection
from src.repositories.transaction_repository import TransactionRepository


class TestTransactionRepository(unittest.TestCase):
    """TransactionRepository 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 데이터베이스 파일 생성
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False).name
        self.db_connection = DatabaseConnection(self.temp_db_file)
        self.repository = TransactionRepository(self.db_connection)
        
        # 테스트 데이터 생성
        self.test_transaction = Transaction(
            transaction_id="test-transaction-001",
            transaction_date=date.today(),
            description="테스트 거래",
            amount=Decimal("10000.00"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="test",
            category="테스트",
            payment_method="테스트 결제"
        )
    
    def tearDown(self):
        """테스트 정리"""
        self.db_connection.close()
        if os.path.exists(self.temp_db_file):
            os.unlink(self.temp_db_file)
    
    def test_create_transaction(self):
        """거래 생성 테스트"""
        # 거래 생성
        created = self.repository.create(self.test_transaction)
        
        # 검증
        self.assertIsNotNone(created.id)
        self.assertEqual(created.transaction_id, self.test_transaction.transaction_id)
        self.assertEqual(created.description, self.test_transaction.description)
        self.assertEqual(created.amount, self.test_transaction.amount)
    
    def test_read_transaction(self):
        """거래 조회 테스트"""
        # 거래 생성
        created = self.repository.create(self.test_transaction)
        
        # ID로 조회
        read = self.repository.read(created.id)
        
        # 검증
        self.assertIsNotNone(read)
        self.assertEqual(read.id, created.id)
        self.assertEqual(read.transaction_id, created.transaction_id)
        self.assertEqual(read.description, created.description)
    
    def test_read_by_transaction_id(self):
        """거래 ID로 조회 테스트"""
        # 거래 생성
        self.repository.create(self.test_transaction)
        
        # 거래 ID로 조회
        read = self.repository.read_by_transaction_id(self.test_transaction.transaction_id)
        
        # 검증
        self.assertIsNotNone(read)
        self.assertEqual(read.transaction_id, self.test_transaction.transaction_id)
        self.assertEqual(read.description, self.test_transaction.description)
    
    def test_update_transaction(self):
        """거래 업데이트 테스트"""
        # 거래 생성
        created = self.repository.create(self.test_transaction)
        
        # 거래 수정
        created.description = "수정된 거래"
        created.amount = Decimal("20000.00")
        updated = self.repository.update(created)
        
        # 검증
        self.assertEqual(updated.description, "수정된 거래")
        self.assertEqual(updated.amount, Decimal("20000.00"))
        
        # 데이터베이스에서 다시 조회하여 검증
        read = self.repository.read(created.id)
        self.assertEqual(read.description, "수정된 거래")
        self.assertEqual(read.amount, Decimal("20000.00"))
    
    def test_delete_transaction(self):
        """거래 삭제 테스트"""
        # 거래 생성
        created = self.repository.create(self.test_transaction)
        
        # 삭제
        result = self.repository.delete(created.id)
        
        # 검증
        self.assertTrue(result)
        self.assertIsNone(self.repository.read(created.id))
    
    def test_list_transactions(self):
        """거래 목록 조회 테스트"""
        # 여러 거래 생성
        transactions = []
        for i in range(5):
            transaction = Transaction(
                transaction_id=f"test-transaction-{i+1:03d}",
                transaction_date=date.today() - timedelta(days=i),
                description=f"테스트 거래 {i+1}",
                amount=Decimal(f"{(i+1)*10000}.00"),
                transaction_type=Transaction.TYPE_EXPENSE if i % 2 == 0 else Transaction.TYPE_INCOME,
                source="test",
                category="테스트" if i % 2 == 0 else "기타",
                payment_method="테스트 결제"
            )
            created = self.repository.create(transaction)
            transactions.append(created)
        
        # 모든 거래 조회
        all_transactions = self.repository.list()
        self.assertEqual(len(all_transactions), 5)
        
        # 필터링 테스트: 카테고리
        category_transactions = self.repository.list({"category": "테스트"})
        self.assertEqual(len(category_transactions), 3)
        
        # 필터링 테스트: 거래 유형
        type_transactions = self.repository.list({"transaction_type": Transaction.TYPE_INCOME})
        self.assertEqual(len(type_transactions), 2)
        
        # 필터링 테스트: 날짜 범위
        date_transactions = self.repository.list({
            "start_date": date.today() - timedelta(days=3),
            "end_date": date.today() - timedelta(days=1)
        })
        self.assertEqual(len(date_transactions), 3)
        
        # 필터링 테스트: 금액 범위
        amount_transactions = self.repository.list({
            "min_amount": "20000.00",
            "max_amount": "40000.00"
        })
        self.assertEqual(len(amount_transactions), 3)
    
    def test_count_transactions(self):
        """거래 수 조회 테스트"""
        # 여러 거래 생성
        for i in range(5):
            transaction = Transaction(
                transaction_id=f"test-transaction-{i+1:03d}",
                transaction_date=date.today() - timedelta(days=i),
                description=f"테스트 거래 {i+1}",
                amount=Decimal(f"{(i+1)*10000}.00"),
                transaction_type=Transaction.TYPE_EXPENSE if i % 2 == 0 else Transaction.TYPE_INCOME,
                source="test",
                category="테스트" if i % 2 == 0 else "기타",
                payment_method="테스트 결제"
            )
            self.repository.create(transaction)
        
        # 모든 거래 수 조회
        count = self.repository.count()
        self.assertEqual(count, 5)
        
        # 필터링 테스트: 카테고리
        category_count = self.repository.count({"category": "테스트"})
        self.assertEqual(category_count, 3)
        
        # 필터링 테스트: 거래 유형
        type_count = self.repository.count({"transaction_type": Transaction.TYPE_INCOME})
        self.assertEqual(type_count, 2)
    
    def test_exists_transaction(self):
        """거래 존재 여부 테스트"""
        # 거래 생성
        created = self.repository.create(self.test_transaction)
        
        # 존재 여부 확인
        self.assertTrue(self.repository.exists(created.id))
        self.assertFalse(self.repository.exists(999))
    
    def test_exists_by_transaction_id(self):
        """거래 ID로 존재 여부 테스트"""
        # 거래 생성
        self.repository.create(self.test_transaction)
        
        # 존재 여부 확인
        self.assertTrue(self.repository.exists_by_transaction_id(self.test_transaction.transaction_id))
        self.assertFalse(self.repository.exists_by_transaction_id("non-existent-id"))
    
    def test_bulk_create_transactions(self):
        """거래 일괄 생성 테스트"""
        # 여러 거래 생성
        transactions = []
        for i in range(5):
            transaction = Transaction(
                transaction_id=f"bulk-transaction-{i+1:03d}",
                transaction_date=date.today() - timedelta(days=i),
                description=f"일괄 거래 {i+1}",
                amount=Decimal(f"{(i+1)*10000}.00"),
                transaction_type=Transaction.TYPE_EXPENSE,
                source="test",
                category="일괄 테스트",
                payment_method="테스트 결제"
            )
            transactions.append(transaction)
        
        # 일괄 생성
        created = self.repository.bulk_create(transactions)
        
        # 검증
        self.assertEqual(len(created), 5)
        for i, transaction in enumerate(created):
            self.assertIsNotNone(transaction.id)
            self.assertEqual(transaction.transaction_id, f"bulk-transaction-{i+1:03d}")
        
        # 데이터베이스에서 조회하여 검증
        db_transactions = self.repository.list({"category": "일괄 테스트"})
        self.assertEqual(len(db_transactions), 5)
    
    def test_get_categories(self):
        """카테고리 목록 조회 테스트"""
        # 여러 거래 생성
        categories = ["식비", "교통비", "생활용품", "식비", "문화/오락"]
        for i, category in enumerate(categories):
            transaction = Transaction(
                transaction_id=f"category-test-{i+1:03d}",
                transaction_date=date.today(),
                description=f"카테고리 테스트 {i+1}",
                amount=Decimal("10000.00"),
                transaction_type=Transaction.TYPE_EXPENSE,
                source="test",
                category=category,
                payment_method="테스트 결제"
            )
            self.repository.create(transaction)
        
        # 카테고리 목록 조회
        db_categories = self.repository.get_categories()
        
        # 검증 (중복 제거 및 정렬 확인)
        self.assertEqual(len(db_categories), 4)
        self.assertIn("교통비", db_categories)
        self.assertIn("문화/오락", db_categories)
        self.assertIn("생활용품", db_categories)
        self.assertIn("식비", db_categories)
    
    def test_get_payment_methods(self):
        """결제 방식 목록 조회 테스트"""
        # 여러 거래 생성
        payment_methods = ["체크카드", "현금", "계좌이체", "체크카드", "토스페이"]
        for i, payment_method in enumerate(payment_methods):
            transaction = Transaction(
                transaction_id=f"payment-test-{i+1:03d}",
                transaction_date=date.today(),
                description=f"결제 방식 테스트 {i+1}",
                amount=Decimal("10000.00"),
                transaction_type=Transaction.TYPE_EXPENSE,
                source="test",
                category="테스트",
                payment_method=payment_method
            )
            self.repository.create(transaction)
        
        # 결제 방식 목록 조회
        db_payment_methods = self.repository.get_payment_methods()
        
        # 검증 (중복 제거 및 정렬 확인)
        self.assertEqual(len(db_payment_methods), 4)
        self.assertIn("계좌이체", db_payment_methods)
        self.assertIn("토스페이", db_payment_methods)
        self.assertIn("체크카드", db_payment_methods)
        self.assertIn("현금", db_payment_methods)
    
    def test_get_date_range(self):
        """날짜 범위 조회 테스트"""
        # 여러 거래 생성
        start_date = date.today() - timedelta(days=10)
        end_date = date.today()
        
        for i in range(5):
            transaction = Transaction(
                transaction_id=f"date-test-{i+1:03d}",
                transaction_date=start_date + timedelta(days=i*2),
                description=f"날짜 테스트 {i+1}",
                amount=Decimal("10000.00"),
                transaction_type=Transaction.TYPE_EXPENSE,
                source="test",
                category="테스트",
                payment_method="테스트 결제"
            )
            self.repository.create(transaction)
        
        # 날짜 범위 조회
        min_date, max_date = self.repository.get_date_range()
        
        # 검증
        self.assertEqual(min_date, start_date)
        self.assertEqual(max_date, start_date + timedelta(days=8))


if __name__ == "__main__":
    unittest.main()