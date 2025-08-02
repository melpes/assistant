# -*- coding: utf-8 -*-
"""
IncomeIngester 테스트

수입 거래 데이터 수집기의 기능을 테스트합니다.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json
import pandas as pd
from datetime import date, datetime, timedelta
from decimal import Decimal

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ingesters.income_ingester import IncomeIngester
from src.models.transaction import Transaction


class TestIncomeIngester(unittest.TestCase):
    """
    IncomeIngester 클래스 테스트
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        self.ingester = IncomeIngester()
        
        # 임시 파일 생성을 위한 디렉토리
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        """
        테스트 정리
        """
        self.temp_dir.cleanup()
    
    def test_init(self):
        """
        초기화 테스트
        """
        self.assertEqual(self.ingester.name, "수입 관리")
        self.assertEqual(self.ingester.description, "수입 거래 데이터 수집 및 관리")
        self.assertIsNotNone(self.ingester.income_type_patterns)
        self.assertIsNotNone(self.ingester.income_exclude_patterns)
        self.assertIsNotNone(self.ingester.regular_income_patterns)
    
    def test_get_supported_file_types(self):
        """
        지원하는 파일 유형 테스트
        """
        file_types = self.ingester.get_supported_file_types()
        self.assertIn('csv', file_types)
        self.assertIn('xlsx', file_types)
        self.assertIn('xls', file_types)
        self.assertIn('json', file_types)
    
    def test_get_required_fields(self):
        """
        필수 필드 테스트
        """
        required_fields = self.ingester.get_required_fields()
        self.assertIn('transaction_id', required_fields)
        self.assertIn('transaction_date', required_fields)
        self.assertIn('description', required_fields)
        self.assertIn('amount', required_fields)
        self.assertIn('transaction_type', required_fields)
    
    def test_categorize_income(self):
        """
        수입 분류 테스트
        """
        # 급여 분류
        self.assertEqual(self.ingester._categorize_income("월급", 2500000), "급여")
        self.assertEqual(self.ingester._categorize_income("급여", 1500000), "급여")
        self.assertEqual(self.ingester._categorize_income("상여금", 1000000), "급여")
        
        # 용돈 분류
        self.assertEqual(self.ingester._categorize_income("용돈", 50000), "용돈")
        self.assertEqual(self.ingester._categorize_income("생일 선물", 30000), "용돈")
        
        # 이자 분류
        self.assertEqual(self.ingester._categorize_income("이자 수익", 5000), "이자")
        self.assertEqual(self.ingester._categorize_income("배당금", 20000), "이자")
        
        # 환급 분류
        self.assertEqual(self.ingester._categorize_income("세금 환급", 150000), "환급")
        self.assertEqual(self.ingester._categorize_income("보험금", 200000), "환급")
        
        # 금액 기반 분류
        self.assertEqual(self.ingester._categorize_income("입금", 2000000), "급여")
        self.assertEqual(self.ingester._categorize_income("입금", 700000), "부수입")
        self.assertEqual(self.ingester._categorize_income("입금", 300000), "부수입")
        self.assertEqual(self.ingester._categorize_income("입금", 50000), "용돈")
        self.assertEqual(self.ingester._categorize_income("입금", 5000), "기타수입")
    
    def test_is_income_excluded(self):
        """
        수입 제외 테스트
        """
        # 제외 대상
        self.assertTrue(self.ingester._is_income_excluded("카드잔액 자동충전"))
        self.assertTrue(self.ingester._is_income_excluded("내계좌 이체"))
        self.assertTrue(self.ingester._is_income_excluded("계좌이체"))
        self.assertTrue(self.ingester._is_income_excluded("강태희 입금"))
        
        # 제외 대상 아님
        self.assertFalse(self.ingester._is_income_excluded("월급"))
        self.assertFalse(self.ingester._is_income_excluded("이자 수익"))
        self.assertFalse(self.ingester._is_income_excluded("용돈"))
        self.assertFalse(self.ingester._is_income_excluded("판매 수익"))
    
    def test_determine_payment_method(self):
        """
        입금 방식 결정 테스트
        """
        self.assertEqual(self.ingester._determine_payment_method("급여", "1월 급여"), "급여이체")
        self.assertEqual(self.ingester._determine_payment_method("이자 수익"), "이자입금")
        self.assertEqual(self.ingester._determine_payment_method("계좌 입금"), "계좌입금")
        self.assertEqual(self.ingester._determine_payment_method("현금 입금"), "현금")
        self.assertEqual(self.ingester._determine_payment_method("기타 입금"), "계좌입금")
    
    def test_is_regular_income(self):
        """
        정기 수입 판단 테스트
        """
        self.assertTrue(self.ingester._is_regular_income("월급", "급여"))
        self.assertTrue(self.ingester._is_regular_income("월세", "임대수입"))
        self.assertTrue(self.ingester._is_regular_income("정기 이자", "이자"))
        
        self.assertFalse(self.ingester._is_regular_income("일회성 수입", "기타수입"))
        self.assertFalse(self.ingester._is_regular_income("판매 수익", "판매수입"))
    
    def test_add_income(self):
        """
        수입 추가 테스트
        """
        # 기본 수입 추가
        transaction_date = date(2024, 1, 15)
        transaction = self.ingester.add_income(
            transaction_date=transaction_date,
            description="1월 급여",
            amount=2500000,
            category="급여",
            payment_method="급여이체",
            memo="1월 정기 급여"
        )
        
        self.assertEqual(transaction['transaction_type'], Transaction.TYPE_INCOME)
        self.assertEqual(transaction['description'], "1월 급여")
        self.assertEqual(float(transaction['amount']), 2500000)
        self.assertEqual(transaction['category'], "급여")
        self.assertEqual(transaction['payment_method'], "급여이체")
        self.assertEqual(transaction['memo'], "1월 정기 급여")
        self.assertEqual(transaction['source'], "manual_income")
        self.assertFalse(transaction['is_excluded'])
        self.assertTrue(transaction['metadata']['is_regular'])
        
        # 자동 분류 테스트
        transaction = self.ingester.add_income(
            transaction_date=date(2024, 1, 20),
            description="이자 수익",
            amount=5000
        )
        
        self.assertEqual(transaction['category'], "이자")
        self.assertEqual(transaction['payment_method'], "이자입금")
        
        # 예외 테스트
        with self.assertRaises(ValueError):
            self.ingester.add_income(
                transaction_date=date(2024, 1, 1),
                description="잘못된 금액",
                amount=0
            )
    
    def test_batch_add_incomes(self):
        """
        일괄 수입 추가 테스트
        """
        transactions = [
            {
                'transaction_date': date(2024, 1, 15),
                'description': "1월 급여",
                'amount': 2500000,
                'category': "급여"
            },
            {
                'transaction_date': date(2024, 1, 20),
                'description': "이자 수익",
                'amount': 5000
            },
            {
                'transaction_date': date(2024, 1, 25),
                'description': "용돈",
                'amount': 50000
            }
        ]
        
        result = self.ingester.batch_add_incomes(transactions)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['category'], "급여")
        self.assertEqual(result[1]['category'], "이자")
        self.assertEqual(result[2]['category'], "용돈")
    
    def test_analyze_income_patterns(self):
        """
        수입 패턴 분석 테스트
        """
        # 정기 수입 패턴이 있는 거래 데이터 생성
        transactions = []
        
        # 급여 (매월 15일)
        for month in range(1, 7):
            transactions.append({
                'transaction_id': f"INCOME_202401{month}15_2500000_12345678",
                'transaction_date': f"2024-{month:02d}-15",
                'description': f"{month}월 급여",
                'amount': Decimal('2500000'),
                'category': "급여",
                'transaction_type': Transaction.TYPE_INCOME
            })
        
        # 이자 (매월 20일)
        for month in range(1, 7):
            transactions.append({
                'transaction_id': f"INCOME_202401{month}20_5000_12345678",
                'transaction_date': f"2024-{month:02d}-20",
                'description': f"{month}월 이자",
                'amount': Decimal('5000'),
                'category': "이자",
                'transaction_type': Transaction.TYPE_INCOME
            })
        
        # 비정기 수입
        transactions.append({
            'transaction_id': f"INCOME_20240110_100000_12345678",
            'transaction_date': f"2024-01-10",
            'description': "판매 수익",
            'amount': Decimal('100000'),
            'category': "판매수입",
            'transaction_type': Transaction.TYPE_INCOME
        })
        
        # 패턴 분석
        result = self.ingester.analyze_income_patterns(transactions)
        
        # 검증
        self.assertEqual(result['total_income'], float(Decimal('15105000')))  # 총 수입
        self.assertEqual(result['category_count'], 3)  # 카테고리 수
        self.assertEqual(result['transaction_count'], 13)  # 거래 수
        
        # 정기 패턴 확인
        self.assertIn('급여', result['regular_patterns'])
        self.assertIn('이자', result['regular_patterns'])
        self.assertNotIn('판매수입', result['regular_patterns'])
        
        # 간격 확인
        self.assertAlmostEqual(result['regular_patterns']['급여']['avg_interval'], 30, delta=2)
        self.assertAlmostEqual(result['regular_patterns']['이자']['avg_interval'], 30, delta=2)
    
    def _create_test_csv(self, filename, data):
        """
        테스트용 CSV 파일 생성
        """
        df = pd.DataFrame(data)
        file_path = os.path.join(self.temp_dir.name, filename)
        df.to_csv(file_path, index=False)
        return file_path
    
    def _create_test_json(self, filename, data):
        """
        테스트용 JSON 파일 생성
        """
        file_path = os.path.join(self.temp_dir.name, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return file_path
    
    def test_validate_file(self):
        """
        파일 유효성 검증 테스트
        """
        # 유효한 CSV 파일
        valid_csv_data = [
            {'날짜': '2024-01-15', '내용': '1월 급여', '금액': 2500000}
        ]
        valid_csv_path = self._create_test_csv('valid.csv', valid_csv_data)
        self.assertTrue(self.ingester.validate_file(valid_csv_path))
        
        # 유효하지 않은 CSV 파일
        invalid_csv_data = [
            {'날짜': '2024-01-15', '설명': '1월 급여'}  # '금액' 열 누락
        ]
        invalid_csv_path = self._create_test_csv('invalid.csv', invalid_csv_data)
        self.assertFalse(self.ingester.validate_file(invalid_csv_path))
        
        # 유효한 JSON 파일
        valid_json_data = [
            {'date': '2024-01-15', 'description': '1월 급여', 'amount': 2500000}
        ]
        valid_json_path = self._create_test_json('valid.json', valid_json_data)
        self.assertTrue(self.ingester.validate_file(valid_json_path))
        
        # 유효하지 않은 JSON 파일
        invalid_json_data = [
            {'date': '2024-01-15', 'description': '1월 급여'}  # 'amount' 필드 누락
        ]
        invalid_json_path = self._create_test_json('invalid.json', invalid_json_data)
        self.assertFalse(self.ingester.validate_file(invalid_json_path))
        
        # 지원하지 않는 파일 형식
        unsupported_path = os.path.join(self.temp_dir.name, 'test.txt')
        with open(unsupported_path, 'w') as f:
            f.write('테스트')
        self.assertFalse(self.ingester.validate_file(unsupported_path))
    
    @patch('pandas.read_csv')
    def test_extract_transactions_csv(self, mock_read_csv):
        """
        CSV 파일에서 거래 추출 테스트
        """
        # 모의 데이터 설정
        mock_df = pd.DataFrame([
            {'날짜': '2024-01-15', '내용': '1월 급여', '금액': 2500000, '유형': '급여', '메모': '1월 정기 급여'},
            {'날짜': '2024-01-20', '내용': '이자 수익', '금액': 5000, '유형': '이자', '메모': ''}
        ])
        mock_read_csv.return_value = mock_df
        
        # 테스트 실행
        transactions = self.ingester.extract_transactions('test.csv')
        
        # 검증
        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0]['description'], '1월 급여')
        self.assertEqual(transactions[0]['amount'], 2500000)
        self.assertEqual(transactions[0]['category'], '급여')
        self.assertEqual(transactions[1]['description'], '이자 수익')
        self.assertEqual(transactions[1]['amount'], 5000)
        self.assertEqual(transactions[1]['category'], '이자')
    
    def test_normalize_data(self):
        """
        데이터 정규화 테스트
        """
        # 테스트 데이터
        raw_data = [
            {
                'transaction_date': date(2024, 1, 15),
                'description': '1월 급여',
                'amount': 2500000,
                'category': '급여',
                'memo': '1월 정기 급여'
            },
            {
                'transaction_date': date(2024, 1, 20),
                'description': '이자 수익',
                'amount': 5000,
                'category': '이자',
                'memo': ''
            },
            {
                'transaction_date': date(2024, 1, 10),
                'description': '내계좌 이체',
                'amount': 1000000,
                'category': '',
                'memo': '자금 이동'
            }
        ]
        
        # 정규화 실행
        normalized = self.ingester.normalize_data(raw_data)
        
        # 검증
        self.assertEqual(len(normalized), 3)
        
        # 급여 검증
        self.assertEqual(normalized[0]['transaction_type'], Transaction.TYPE_INCOME)
        self.assertEqual(normalized[0]['category'], '급여')
        self.assertEqual(float(normalized[0]['amount']), 2500000)
        self.assertEqual(normalized[0]['payment_method'], '급여이체')
        self.assertFalse(normalized[0]['is_excluded'])
        self.assertTrue(normalized[0]['metadata']['is_regular'])
        
        # 이자 검증
        self.assertEqual(normalized[1]['transaction_type'], Transaction.TYPE_INCOME)
        self.assertEqual(normalized[1]['category'], '이자')
        self.assertEqual(float(normalized[1]['amount']), 5000)
        self.assertEqual(normalized[1]['payment_method'], '이자입금')
        self.assertFalse(normalized[1]['is_excluded'])
        
        # 제외 대상 검증
        self.assertEqual(normalized[2]['transaction_type'], Transaction.TYPE_INCOME)
        self.assertTrue(normalized[2]['is_excluded'])


if __name__ == '__main__':
    unittest.main()