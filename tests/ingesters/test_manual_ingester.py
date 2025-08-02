# -*- coding: utf-8 -*-
"""
ManualIngester 테스트
"""

import pytest
from datetime import date
from decimal import Decimal

from src.ingesters.manual_ingester import ManualIngester

class TestManualIngester:
    """ManualIngester 테스트 클래스"""
    
    def test_initialization(self):
        """초기화 테스트"""
        ingester = ManualIngester()
        assert ingester.name == "수동 입력"
        assert "수동으로 입력된 거래 데이터" in ingester.description
        
        # 커스텀 이름과 설명으로 초기화
        custom_ingester = ManualIngester("커스텀 이름", "커스텀 설명")
        assert custom_ingester.name == "커스텀 이름"
        assert custom_ingester.description == "커스텀 설명"
    
    def test_get_supported_file_types(self):
        """지원하는 파일 유형 테스트"""
        ingester = ManualIngester()
        file_types = ingester.get_supported_file_types()
        
        assert isinstance(file_types, list)
        assert len(file_types) == 0  # 파일 기반이 아니므로 빈 리스트
    
    def test_get_required_fields(self):
        """필수 필드 목록 테스트"""
        ingester = ManualIngester()
        required_fields = ingester.get_required_fields()
        
        assert isinstance(required_fields, list)
        assert all(field in required_fields for field in [
            'transaction_id', 'transaction_date', 'description', 
            'amount', 'transaction_type', 'source'
        ])
    
    def test_validate_file(self):
        """파일 검증 테스트 (항상 False 반환)"""
        ingester = ManualIngester()
        assert ingester.validate_file("test_file.txt") is False
    
    def test_extract_transactions(self):
        """거래 추출 테스트 (항상 빈 리스트 반환)"""
        ingester = ManualIngester()
        assert ingester.extract_transactions("test_file.txt") == []
    
    def test_normalize_data(self):
        """데이터 정규화 테스트"""
        ingester = ManualIngester()
        
        # 테스트용 원시 데이터
        raw_data = [
            {
                'transaction_date': date(2023, 1, 1),
                'description': '테스트 지출',
                'amount': 10000,
                'transaction_type': 'expense',
                'category': '식비',
                'payment_method': '현금'
            },
            {
                'transaction_date': date(2023, 1, 2),
                'description': '테스트 수입',
                'amount': 50000,
                'transaction_type': 'income',
                'category': '용돈',
                'payment_method': '계좌입금'
            }
        ]
        
        normalized_data = ingester.normalize_data(raw_data)
        
        assert len(normalized_data) == 2
        
        # 지출 거래 확인
        assert normalized_data[0]['transaction_type'] == 'expense'
        assert normalized_data[0]['amount'] == Decimal('10000')
        assert normalized_data[0]['category'] == '식비'
        assert normalized_data[0]['payment_method'] == '현금'
        assert normalized_data[0]['source'] == 'manual_entry'
        assert normalized_data[0]['account_type'] == '수동입력'
        
        # 수입 거래 확인
        assert normalized_data[1]['transaction_type'] == 'income'
        assert normalized_data[1]['amount'] == Decimal('50000')
        assert normalized_data[1]['category'] == '용돈'
        assert normalized_data[1]['payment_method'] == '계좌입금'
    
    def test_normalize_data_missing_fields(self):
        """필수 필드가 누락된 데이터 정규화 테스트"""
        ingester = ManualIngester()
        
        # 필수 필드가 누락된 원시 데이터
        raw_data = [
            {
                'description': '테스트 지출',
                'amount': 10000
                # transaction_date와 transaction_type 누락
            }
        ]
        
        normalized_data = ingester.normalize_data(raw_data)
        assert len(normalized_data) == 0  # 유효하지 않은 데이터는 제외됨
    
    def test_add_expense(self):
        """지출 추가 테스트"""
        ingester = ManualIngester()
        
        expense = ingester.add_expense(
            transaction_date=date(2023, 1, 1),
            description='테스트 지출',
            amount=10000,
            category='식비',
            payment_method='현금',
            memo='테스트 메모'
        )
        
        assert expense['transaction_type'] == 'expense'
        assert expense['description'] == '테스트 지출'
        assert expense['amount'] == Decimal('10000')
        assert expense['category'] == '식비'
        assert expense['payment_method'] == '현금'
        assert expense['memo'] == '테스트 메모'
        assert expense['source'] == 'manual_entry'
        assert expense['account_type'] == '수동입력'
        assert 'transaction_id' in expense
        assert expense['transaction_id'].startswith('MANUAL_')
    
    def test_add_income(self):
        """수입 추가 테스트"""
        ingester = ManualIngester()
        
        income = ingester.add_income(
            transaction_date=date(2023, 1, 1),
            description='테스트 수입',
            amount=50000,
            category='용돈',
            payment_method='계좌입금',
            memo='테스트 메모'
        )
        
        assert income['transaction_type'] == 'income'
        assert income['description'] == '테스트 수입'
        assert income['amount'] == Decimal('50000')
        assert income['category'] == '용돈'
        assert income['payment_method'] == '계좌입금'
        assert income['memo'] == '테스트 메모'
        assert income['source'] == 'manual_entry'
        assert income['account_type'] == '수동입력'
        assert 'transaction_id' in income
        assert income['transaction_id'].startswith('MANUAL_')
    
    def test_batch_add_transactions(self):
        """일괄 거래 추가 테스트"""
        ingester = ManualIngester()
        
        transactions = [
            {
                'transaction_date': date(2023, 1, 1),
                'description': '테스트 지출 1',
                'amount': 10000,
                'transaction_type': 'expense',
                'category': '식비',
                'payment_method': '현금'
            },
            {
                'transaction_date': date(2023, 1, 2),
                'description': '테스트 지출 2',
                'amount': 20000,
                'transaction_type': 'expense',
                'category': '교통비',
                'payment_method': '카드'
            },
            {
                'transaction_date': date(2023, 1, 3),
                'description': '테스트 수입',
                'amount': 50000,
                'transaction_type': 'income',
                'category': '용돈',
                'payment_method': '계좌입금'
            }
        ]
        
        normalized_transactions = ingester.batch_add_transactions(transactions)
        
        assert len(normalized_transactions) == 3
        assert normalized_transactions[0]['description'] == '테스트 지출 1'
        assert normalized_transactions[1]['description'] == '테스트 지출 2'
        assert normalized_transactions[2]['description'] == '테스트 수입'