# -*- coding: utf-8 -*-
"""
수입 거래 관리 시스템 통합 테스트

수입 거래 관리 시스템의 여러 컴포넌트를 통합하여 테스트합니다.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
import sqlite3

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ingesters.income_ingester import IncomeIngester
from src.ingesters.income_rule_engine import IncomeRuleEngine
from src.ingesters.income_pattern_analyzer import IncomePatternAnalyzer
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.db_connection import DatabaseConnection
from src.models.transaction import Transaction


class TestIncomeManagementIntegration(unittest.TestCase):
    """
    수입 거래 관리 시스템 통합 테스트
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        # 임시 파일 생성을 위한 디렉토리
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # 임시 데이터베이스 생성
        self.db_path = os.path.join(self.temp_dir.name, 'test.db')
        self.db_connection = DatabaseConnection(self.db_path)
        
        # 컴포넌트 초기화
        self.ingester = IncomeIngester()
        self.rule_engine = IncomeRuleEngine()
        self.analyzer = IncomePatternAnalyzer()
        self.repository = TransactionRepository(self.db_connection)
    
    def tearDown(self):
        """
        테스트 정리
        """
        self.temp_dir.cleanup()
    
    def test_end_to_end_income_management(self):
        """
        수입 거래 관리 시스템 종단간 테스트
        """
        # 1. 수입 거래 생성
        transactions = [
            # 급여 (매월 15일)
            {
                'transaction_date': date(2024, 1, 15),
                'description': "1월 급여",
                'amount': 2500000,
                'category': "급여",
                'memo': "1월 정기 급여"
            },
            {
                'transaction_date': date(2024, 2, 15),
                'description': "2월 급여",
                'amount': 2500000,
                'category': "급여",
                'memo': "2월 정기 급여"
            },
            {
                'transaction_date': date(2024, 3, 15),
                'description': "3월 급여",
                'amount': 2500000,
                'category': "급여",
                'memo': "3월 정기 급여"
            },
            
            # 이자 (매월 20일)
            {
                'transaction_date': date(2024, 1, 20),
                'description': "1월 이자",
                'amount': 5000,
                'category': "이자",
                'memo': "1월 정기 이자"
            },
            {
                'transaction_date': date(2024, 2, 20),
                'description': "2월 이자",
                'amount': 5000,
                'category': "이자",
                'memo': "2월 정기 이자"
            },
            {
                'transaction_date': date(2024, 3, 20),
                'description': "3월 이자",
                'amount': 5000,
                'category': "이자",
                'memo': "3월 정기 이자"
            },
            
            # 비정기 수입
            {
                'transaction_date': date(2024, 1, 10),
                'description': "판매 수익",
                'amount': 100000,
                'category': "판매수입",
                'memo': "중고 물품 판매"
            },
            
            # 제외 대상 수입
            {
                'transaction_date': date(2024, 2, 5),
                'description': "내계좌 이체",
                'amount': 1000000,
                'memo': "자금 이동"
            }
        ]
        
        # 2. 수입 거래 일괄 추가
        income_data_list = self.ingester.batch_add_incomes(transactions)
        
        # 3. 규칙 엔진 적용
        for i, income_data in enumerate(income_data_list):
            income_data_list[i] = self.rule_engine.apply_rules_to_transaction(income_data)
        
        # 4. 데이터베이스에 저장
        saved_transactions = []
        for income_data in income_data_list:
            transaction = Transaction.from_dict(income_data)
            saved_transaction = self.repository.create(transaction)
            saved_transactions.append(saved_transaction)
            
            # 패턴 분석기에 추가
            self.analyzer.add_transaction(income_data)
        
        # 5. 패턴 분석
        pattern_result = self.analyzer.analyze_patterns()
        
        # 6. 미래 수입 예측
        prediction_result = self.analyzer.predict_future_income(months_ahead=2)
        
        # 7. 정기 수입 요약
        summary_result = self.analyzer.get_regular_income_summary()
        
        # 검증
        
        # 거래 저장 확인
        self.assertEqual(len(saved_transactions), len(transactions))
        
        # 데이터베이스 조회 확인
        db_transactions = self.repository.list({'transaction_type': 'income'})
        self.assertEqual(len(db_transactions), len(transactions))
        
        # 제외 대상 확인
        excluded_transactions = self.repository.list({
            'transaction_type': 'income',
            'is_excluded': True,
            'include_excluded': True
        })
        self.assertEqual(len(excluded_transactions), 1)
        self.assertIn("내계좌 이체", excluded_transactions[0].description)
        
        # 정기 패턴 확인
        self.assertIn('급여', pattern_result['regular_patterns'])
        self.assertIn('이자', pattern_result['regular_patterns'])
        self.assertNotIn('판매수입', pattern_result['regular_patterns'])
        
        # 예측 확인
        self.assertGreater(len(prediction_result['predictions']), 0)
        
        # 요약 확인
        self.assertEqual(summary_result['regular_income_count'], 2)  # 급여, 이자
        self.assertGreater(summary_result['monthly_equivalent'], 0)
    
    def test_income_rule_engine_integration(self):
        """
        수입 규칙 엔진 통합 테스트
        """
        # 1. 규칙 추가
        self.rule_engine.add_exclude_rule(
            name="테스트 제외 규칙",
            pattern=r"테스트 제외|test exclude",
            priority=75
        )
        
        self.rule_engine.add_income_type_rule(
            name="테스트 수입 유형",
            pattern=r"테스트 수입|test income",
            target="테스트수입",
            priority=75
        )
        
        # 2. 규칙 저장
        rules_file = os.path.join(self.temp_dir.name, 'test_rules.json')
        self.rule_engine.save_rules(rules_file)
        
        # 3. 새 규칙 엔진 생성 및 규칙 로드
        new_rule_engine = IncomeRuleEngine(rules_file)
        
        # 4. 거래 생성
        transactions = [
            {
                'transaction_date': date(2024, 1, 15),
                'description': "테스트 수입",
                'amount': 50000,
                'memo': "테스트 메모"
            },
            {
                'transaction_date': date(2024, 1, 20),
                'description': "테스트 제외",
                'amount': 100000,
                'memo': "제외 대상"
            }
        ]
        
        # 5. 수입 추가
        income_data_list = self.ingester.batch_add_incomes(transactions)
        
        # 6. 규칙 적용
        for i, income_data in enumerate(income_data_list):
            income_data_list[i] = new_rule_engine.apply_rules_to_transaction(income_data)
        
        # 검증
        self.assertEqual(income_data_list[0]['category'], "테스트수입")
        self.assertFalse(income_data_list[0]['is_excluded'])
        
        self.assertTrue(income_data_list[1]['is_excluded'])
    
    def test_income_pattern_analyzer_integration(self):
        """
        수입 패턴 분석기 통합 테스트
        """
        # 1. 정기 수입 데이터 생성
        transactions = []
        
        # 급여 (매월 15일)
        for month in range(1, 7):
            transactions.append({
                'transaction_date': date(2024, month, 15),
                'description': f"{month}월 급여",
                'amount': 2500000,
                'category': "급여",
                'memo': f"{month}월 정기 급여"
            })
        
        # 2. 수입 추가
        income_data_list = self.ingester.batch_add_incomes(transactions)
        
        # 3. 패턴 분석기에 추가
        for income_data in income_data_list:
            self.analyzer.add_transaction(income_data)
        
        # 4. 패턴 분석
        pattern_result = self.analyzer.analyze_patterns()
        
        # 5. 내역 저장
        history_file = os.path.join(self.temp_dir.name, 'test_history.json')
        self.analyzer.save_history(history_file)
        
        # 6. 새 분석기 생성 및 내역 로드
        new_analyzer = IncomePatternAnalyzer(history_file)
        
        # 7. 패턴 분석
        new_pattern_result = new_analyzer.analyze_patterns()
        
        # 검증
        self.assertIn('급여', pattern_result['regular_patterns'])
        self.assertEqual(pattern_result['regular_patterns']['급여']['period_type'], 'monthly')
        
        self.assertIn('급여', new_pattern_result['regular_patterns'])
        self.assertEqual(new_pattern_result['regular_patterns']['급여']['period_type'], 'monthly')
    
    def test_repository_integration(self):
        """
        저장소 통합 테스트
        """
        # 1. 수입 거래 생성
        transactions = [
            {
                'transaction_date': date(2024, 1, 15),
                'description': "1월 급여",
                'amount': 2500000,
                'category': "급여",
                'memo': "1월 정기 급여"
            },
            {
                'transaction_date': date(2024, 2, 15),
                'description': "2월 급여",
                'amount': 2500000,
                'category': "급여",
                'memo': "2월 정기 급여"
            },
            {
                'transaction_date': date(2024, 1, 20),
                'description': "1월 이자",
                'amount': 5000,
                'category': "이자",
                'memo': "1월 정기 이자"
            }
        ]
        
        # 2. 수입 추가
        income_data_list = self.ingester.batch_add_incomes(transactions)
        
        # 3. 데이터베이스에 저장
        saved_transactions = []
        for income_data in income_data_list:
            transaction = Transaction.from_dict(income_data)
            saved_transaction = self.repository.create(transaction)
            saved_transactions.append(saved_transaction)
        
        # 4. 필터링 조회
        # 카테고리별 조회
        category_transactions = self.repository.list({'category': '급여'})
        self.assertEqual(len(category_transactions), 2)
        
        # 날짜 범위 조회
        date_range_transactions = self.repository.list({
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 1, 31)
        })
        self.assertEqual(len(date_range_transactions), 2)
        
        # 금액 범위 조회
        amount_range_transactions = self.repository.list({
            'min_amount': 1000000
        })
        self.assertEqual(len(amount_range_transactions), 2)
        
        # 5. 통계 조회
        # 카테고리 목록
        categories = self.repository.get_categories()
        self.assertIn('급여', categories)
        self.assertIn('이자', categories)
        
        # 날짜 범위
        min_date, max_date = self.repository.get_date_range()
        self.assertEqual(min_date, date(2024, 1, 15))
        self.assertEqual(max_date, date(2024, 2, 15))
        
        # 6. 거래 업데이트
        transaction = category_transactions[0]
        transaction.update_category('수정된급여')
        updated_transaction = self.repository.update(transaction)
        
        # 업데이트 확인
        self.assertEqual(updated_transaction.category, '수정된급여')
        
        # 7. 거래 삭제
        deleted = self.repository.delete(updated_transaction.id)
        self.assertTrue(deleted)
        
        # 삭제 확인
        remaining_transactions = self.repository.list({})
        self.assertEqual(len(remaining_transactions), 2)


if __name__ == '__main__':
    unittest.main()