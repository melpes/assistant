# -*- coding: utf-8 -*-
"""
토스뱅크 계좌 거래내역 수집 스크립트 테스트
"""

import pytest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from decimal import Decimal

from src.ingest_account_transactions import ingest_account_data
from src.ingesters.toss_bank_account_ingester import TossBankAccountIngester
from src.repositories.transaction_repository import TransactionRepository
from src.models import Transaction

class TestIngestAccountTransactions:
    """토스뱅크 계좌 거래내역 수집 스크립트 테스트 클래스"""
    
    @patch('src.ingest_account_transactions.TossBankAccountIngester')
    @patch('src.ingest_account_transactions.TransactionRepository')
    @patch('src.ingest_account_transactions.DatabaseConnection')
    def test_ingest_account_data_basic(self, mock_db_conn, mock_repo, mock_ingester):
        """기본 데이터 수집 테스트"""
        # 모의 객체 설정
        mock_ingester_instance = MagicMock()
        mock_repo_instance = MagicMock()
        
        mock_ingester.return_value = mock_ingester_instance
        mock_repo.return_value = mock_repo_instance
        
        # 정규화된 데이터 설정
        normalized_data = [
            {
                'transaction_id': 'TOSSACC_20230101_10000_12345678',
                'transaction_date': '2023-01-01',
                'description': '테스트 출금',
                'amount': Decimal('10000'),
                'transaction_type': 'expense',
                'category': '기타',
                'payment_method': '계좌출금',
                'source': 'toss_bank_account',
                'account_type': '토스뱅크 계좌',
                'memo': '출금 | 테스트은행 | 잔액: 90,000원',
                'is_excluded': False,
                'metadata': {
                    'institution': '테스트은행',
                    'account_number': '1234-5678',
                    'balance': 90000.0,
                    'original_type': '출금',
                    'transaction_detail': {}
                }
            },
            {
                'transaction_id': 'TOSSACC_20230102_20000_87654321',
                'transaction_date': '2023-01-02',
                'description': '테스트 입금',
                'amount': Decimal('20000'),
                'transaction_type': 'income',
                'category': '기타수입',
                'payment_method': '계좌입금',
                'source': 'toss_bank_account',
                'account_type': '토스뱅크 계좌',
                'memo': '입금 | 테스트은행 | 잔액: 110,000원',
                'is_excluded': False,
                'metadata': {
                    'institution': '테스트은행',
                    'account_number': '1234-5678',
                    'balance': 110000.0,
                    'original_type': '입금',
                    'transaction_detail': {}
                }
            }
        ]
        
        mock_ingester_instance.ingest.return_value = normalized_data
        mock_ingester_instance.validate_file.return_value = True
        
        # Transaction 객체 설정
        transactions = [MagicMock(transaction_id=data['transaction_id']) for data in normalized_data]
        mock_repo_instance._find_existing_transaction_ids.return_value = []
        mock_repo_instance.bulk_create.return_value = transactions
        
        # 함수 실행
        total, created, duplicates = ingest_account_data('test_file.csv', batch_size=100, dry_run=False)
        
        # 검증
        assert total == 2
        assert created == 2
        assert duplicates == 0
        
        # 메서드 호출 검증
        mock_ingester_instance.validate_file.assert_called_once_with('test_file.csv')
        mock_ingester_instance.ingest.assert_called_once_with('test_file.csv')
        mock_repo_instance._find_existing_transaction_ids.assert_called()
        mock_repo_instance.bulk_create.assert_called()
    
    @patch('src.ingest_account_transactions.TossBankAccountIngester')
    @patch('src.ingest_account_transactions.TransactionRepository')
    @patch('src.ingest_account_transactions.DatabaseConnection')
    def test_ingest_account_data_dry_run(self, mock_db_conn, mock_repo, mock_ingester):
        """드라이 런 모드 테스트"""
        # 모의 객체 설정
        mock_ingester_instance = MagicMock()
        mock_repo_instance = MagicMock()
        
        mock_ingester.return_value = mock_ingester_instance
        mock_repo.return_value = mock_repo_instance
        
        # 정규화된 데이터 설정
        normalized_data = [
            {
                'transaction_id': 'TOSSACC_20230101_10000_12345678',
                'transaction_date': '2023-01-01',
                'description': '테스트 출금',
                'amount': Decimal('10000'),
                'transaction_type': 'expense',
                'category': '기타',
                'payment_method': '계좌출금',
                'source': 'toss_bank_account',
                'account_type': '토스뱅크 계좌',
                'memo': '출금 | 테스트은행 | 잔액: 90,000원',
                'is_excluded': False,
                'metadata': {}
            }
        ]
        
        mock_ingester_instance.ingest.return_value = normalized_data
        mock_ingester_instance.validate_file.return_value = True
        
        # Transaction 객체 설정
        mock_repo_instance._find_existing_transaction_ids.return_value = []
        
        # 함수 실행
        total, created, duplicates = ingest_account_data('test_file.csv', batch_size=100, dry_run=True)
        
        # 검증
        assert total == 1
        assert created == 0  # 드라이 런 모드에서는 생성되지 않음
        assert duplicates == 0
        
        # 메서드 호출 검증
        mock_ingester_instance.validate_file.assert_called_once_with('test_file.csv')
        mock_ingester_instance.ingest.assert_called_once_with('test_file.csv')
        mock_repo_instance._find_existing_transaction_ids.assert_called()
        mock_repo_instance.bulk_create.assert_not_called()  # 드라이 런 모드에서는 호출되지 않음
    
    @patch('src.ingest_account_transactions.TossBankAccountIngester')
    @patch('src.ingest_account_transactions.TransactionRepository')
    @patch('src.ingest_account_transactions.DatabaseConnection')
    def test_ingest_account_data_with_duplicates(self, mock_db_conn, mock_repo, mock_ingester):
        """중복 거래 처리 테스트"""
        # 모의 객체 설정
        mock_ingester_instance = MagicMock()
        mock_repo_instance = MagicMock()
        
        mock_ingester.return_value = mock_ingester_instance
        mock_repo.return_value = mock_repo_instance
        
        # 정규화된 데이터 설정
        normalized_data = [
            {
                'transaction_id': 'TOSSACC_20230101_10000_12345678',
                'transaction_date': '2023-01-01',
                'description': '테스트 출금',
                'amount': Decimal('10000'),
                'transaction_type': 'expense',
                'category': '기타',
                'payment_method': '계좌출금',
                'source': 'toss_bank_account',
                'account_type': '토스뱅크 계좌',
                'memo': '출금 | 테스트은행 | 잔액: 90,000원',
                'is_excluded': False,
                'metadata': {}
            },
            {
                'transaction_id': 'TOSSACC_20230102_20000_87654321',
                'transaction_date': '2023-01-02',
                'description': '테스트 입금',
                'amount': Decimal('20000'),
                'transaction_type': 'income',
                'category': '기타수입',
                'payment_method': '계좌입금',
                'source': 'toss_bank_account',
                'account_type': '토스뱅크 계좌',
                'memo': '입금 | 테스트은행 | 잔액: 110,000원',
                'is_excluded': False,
                'metadata': {}
            }
        ]
        
        mock_ingester_instance.ingest.return_value = normalized_data
        mock_ingester_instance.validate_file.return_value = True
        
        # 중복 거래 설정
        mock_repo_instance._find_existing_transaction_ids.return_value = ['TOSSACC_20230101_10000_12345678']
        
        # Transaction 객체 설정
        transactions = [MagicMock(transaction_id=normalized_data[1]['transaction_id'])]
        mock_repo_instance.bulk_create.return_value = transactions
        
        # 함수 실행
        total, created, duplicates = ingest_account_data('test_file.csv', batch_size=100, dry_run=False)
        
        # 검증
        assert total == 2
        assert created == 1  # 중복이 아닌 거래만 생성됨
        assert duplicates == 1  # 중복 거래 수
        
        # 메서드 호출 검증
        mock_ingester_instance.validate_file.assert_called_once_with('test_file.csv')
        mock_ingester_instance.ingest.assert_called_once_with('test_file.csv')
        mock_repo_instance._find_existing_transaction_ids.assert_called()
        mock_repo_instance.bulk_create.assert_called()
    
    @patch('src.ingest_account_transactions.TossBankAccountIngester')
    @patch('src.ingest_account_transactions.TransactionRepository')
    @patch('src.ingest_account_transactions.DatabaseConnection')
    def test_ingest_account_data_with_export(self, mock_db_conn, mock_repo, mock_ingester):
        """데이터 내보내기 테스트"""
        # 모의 객체 설정
        mock_ingester_instance = MagicMock()
        mock_repo_instance = MagicMock()
        
        mock_ingester.return_value = mock_ingester_instance
        mock_repo.return_value = mock_repo_instance
        
        # 정규화된 데이터 설정
        normalized_data = [
            {
                'transaction_id': 'TOSSACC_20230101_10000_12345678',
                'transaction_date': '2023-01-01',
                'description': '테스트 출금',
                'amount': Decimal('10000'),
                'transaction_type': 'expense',
                'category': '기타',
                'payment_method': '계좌출금',
                'source': 'toss_bank_account',
                'account_type': '토스뱅크 계좌',
                'memo': '출금 | 테스트은행 | 잔액: 90,000원',
                'is_excluded': False,
                'metadata': {}
            }
        ]
        
        mock_ingester_instance.ingest.return_value = normalized_data
        mock_ingester_instance.validate_file.return_value = True
        
        # Transaction 객체 설정
        mock_repo_instance._find_existing_transaction_ids.return_value = []
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            export_path = temp_file.name
        
        try:
            # 함수 실행
            total, created, duplicates = ingest_account_data(
                'test_file.csv', batch_size=100, dry_run=True, export_path=export_path
            )
            
            # 검증
            assert total == 1
            assert os.path.exists(export_path)
            
            # 내보낸 파일 내용 확인
            with open(export_path, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
                assert len(exported_data) == 1
                assert exported_data[0]['transaction_id'] == normalized_data[0]['transaction_id']
                assert exported_data[0]['description'] == normalized_data[0]['description']
                assert float(exported_data[0]['amount']) == float(normalized_data[0]['amount'])
        
        finally:
            # 임시 파일 삭제
            if os.path.exists(export_path):
                os.unlink(export_path)
    
    @patch('src.ingest_account_transactions.TossBankAccountIngester')
    @patch('src.ingest_account_transactions.TransactionRepository')
    @patch('src.ingest_account_transactions.DatabaseConnection')
    def test_ingest_account_data_invalid_file(self, mock_db_conn, mock_repo, mock_ingester):
        """유효하지 않은 파일 테스트"""
        # 모의 객체 설정
        mock_ingester_instance = MagicMock()
        mock_repo_instance = MagicMock()
        
        mock_ingester.return_value = mock_ingester_instance
        mock_repo.return_value = mock_repo_instance
        
        # 파일 유효성 검증 실패 설정
        mock_ingester_instance.validate_file.return_value = False
        
        # 함수 실행
        total, created, duplicates = ingest_account_data('invalid_file.csv')
        
        # 검증
        assert total == 0
        assert created == 0
        assert duplicates == 0
        
        # 메서드 호출 검증
        mock_ingester_instance.validate_file.assert_called_once_with('invalid_file.csv')
        mock_ingester_instance.ingest.assert_not_called()  # 유효하지 않은 파일이므로 호출되지 않음