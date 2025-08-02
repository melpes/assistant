# -*- coding: utf-8 -*-
"""
학습 엔진 테스트

학습 엔진의 기능을 테스트합니다.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timedelta
from decimal import Decimal
import sqlite3
import os
import tempfile

from src.models import Transaction, ClassificationRule, LearningPattern
from src.repositories.db_connection import DatabaseConnection
from src.repositories.rule_repository import RuleRepository
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.learning_pattern_repository import LearningPatternRepository
from src.learning_engine import LearningEngine


class TestLearningEngine(unittest.TestCase):
    """
    학습 엔진 테스트 클래스
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        # 임시 데이터베이스 생성
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        
        # 데이터베이스 연결
        self.db_connection = DatabaseConnection(self.temp_db.name)
        
        # 저장소 초기화
        self.rule_repository = RuleRepository(self.db_connection)
        self.transaction_repository = TransactionRepository(self.db_connection)
        self.pattern_repository = LearningPatternRepository(self.db_connection)
        
        # 학습 엔진 초기화
        self.learning_engine = LearningEngine(
            pattern_repository=self.pattern_repository,
            rule_repository=self.rule_repository,
            transaction_repository=self.transaction_repository
        )
        
        # 테스트 데이터 생성
        self._create_test_data()
    
    def tearDown(self):
        """
        테스트 정리
        """
        # 데이터베이스 연결 종료
        self.db_connection.close()
        
        # 임시 데이터베이스 파일 삭제
        os.unlink(self.temp_db.name)
    
    def _create_test_data(self):
        """
        테스트 데이터 생성
        """
        # 테스트 거래 생성
        transactions = [
            Transaction(
                transaction_id="test-tx-001",
                transaction_date=date.today() - timedelta(days=10),
                description="스타벅스 강남점 아메리카노",
                amount=Decimal("4500"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category=None,
                payment_method="체크카드결제",
                source="테스트"
            ),
            Transaction(
                transaction_id="test-tx-002",
                transaction_date=date.today() - timedelta(days=5),
                description="스타벅스 홍대점 라떼",
                amount=Decimal("5000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category=None,
                payment_method="체크카드결제",
                source="테스트"
            ),
            Transaction(
                transaction_id="test-tx-003",
                transaction_date=date.today() - timedelta(days=2),
                description="이마트 강남점 생필품",
                amount=Decimal("25000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category=None,
                payment_method="체크카드결제",
                source="테스트"
            )
        ]
        
        # 거래 저장
        for tx in transactions:
            self.transaction_repository.create(tx)
    
    def test_learn_from_correction(self):
        """
        단일 수정사항 학습 테스트
        """
        # 테스트 거래 조회
        transaction = self.transaction_repository.list({'limit': 1})[0]
        
        # 수정사항 학습
        success = self.learning_engine.learn_from_correction(
            transaction=transaction,
            field_name="category",
            previous_value=None,
            corrected_value="식비"
        )
        
        # 검증
        self.assertTrue(success)
        
        # 패턴 조회
        patterns = self.pattern_repository.list({'pattern_type': 'category'})
        
        # 패턴이 생성되었는지 확인
        self.assertGreater(len(patterns), 0)
        
        # 패턴 내용 확인
        pattern = patterns[0]
        self.assertEqual(pattern.pattern_value, "식비")
        self.assertIn("스타벅스", pattern.pattern_key)
    
    def test_learn_from_corrections_batch(self):
        """
        여러 수정사항 일괄 학습 테스트
        """
        # 테스트 거래 조회
        transactions = self.transaction_repository.list({'limit': 3})
        
        # 수정사항 목록
        corrections = [
            {
                'transaction': transactions[0],
                'field_name': 'category',
                'previous_value': None,
                'corrected_value': '식비'
            },
            {
                'transaction': transactions[1],
                'field_name': 'category',
                'previous_value': None,
                'corrected_value': '식비'
            },
            {
                'transaction': transactions[2],
                'field_name': 'category',
                'previous_value': None,
                'corrected_value': '생활용품'
            }
        ]
        
        # 일괄 학습
        results = self.learning_engine.learn_from_corrections_batch(corrections)
        
        # 검증
        self.assertEqual(results['total'], 3)
        self.assertEqual(results['success'], 3)
        self.assertGreater(results['patterns_extracted'], 0)
        
        # 패턴 조회
        patterns = self.pattern_repository.list()
        
        # 패턴이 생성되었는지 확인
        self.assertGreater(len(patterns), 0)
    
    def test_apply_patterns_to_rules(self):
        """
        학습된 패턴을 규칙으로 적용 테스트
        """
        # 테스트 패턴 생성
        pattern = LearningPattern(
            pattern_type='category',
            pattern_name='테스트-패턴',
            pattern_key='스타벅스',
            pattern_value='식비',
            confidence=LearningPattern.CONFIDENCE_HIGH,
            occurrence_count=3,
            status=LearningPattern.STATUS_PENDING
        )
        
        # 패턴 저장
        self.pattern_repository.create(pattern)
        
        # 패턴 적용
        rules_created = self.learning_engine.apply_patterns_to_rules('category')
        
        # 검증
        self.assertEqual(rules_created, 1)
        
        # 규칙 조회
        rules = self.rule_repository.list({'rule_type': ClassificationRule.TYPE_CATEGORY})
        
        # 규칙이 생성되었는지 확인
        self.assertEqual(len(rules), 1)
        
        # 규칙 내용 확인
        rule = rules[0]
        self.assertEqual(rule.condition_value, "스타벅스")
        self.assertEqual(rule.target_value, "식비")
        self.assertEqual(rule.created_by, ClassificationRule.CREATOR_LEARNED)
    
    def test_detect_recurring_patterns(self):
        """
        반복 거래 패턴 감지 테스트
        """
        # 반복 거래 데이터 생성
        today = date.today()
        
        # 매월 1일 통신비 납부
        for i in range(3):
            tx_date = date(today.year, today.month - i, 1) if today.month > i else date(today.year - 1, 12 - (i - today.month), 1)
            tx = Transaction(
                transaction_id=f"recurring-tx-{i+1}",
                transaction_date=tx_date,
                description="SK텔레콤 통신비",
                amount=Decimal("55000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="통신비",
                payment_method="자동이체",
                source="테스트"
            )
            self.transaction_repository.create(tx)
        
        # 반복 패턴 감지
        recurring_patterns = self.learning_engine.detect_recurring_patterns(days=100)
        
        # 검증
        self.assertGreaterEqual(len(recurring_patterns), 1)
        
        # 패턴 내용 확인
        pattern = recurring_patterns[0]
        self.assertEqual(pattern['merchant'], "SK텔레콤")
        self.assertIn('interval_days', pattern)
        self.assertEqual(pattern['category'], "통신비")
    
    def test_generate_dynamic_filters(self):
        """
        동적 필터 생성 테스트
        """
        # 테스트 패턴 생성
        patterns = [
            LearningPattern(
                pattern_type='category',
                pattern_name='테스트-패턴1',
                pattern_key='스타벅스',
                pattern_value='식비',
                confidence=LearningPattern.CONFIDENCE_HIGH,
                occurrence_count=3,
                status=LearningPattern.STATUS_APPLIED
            ),
            LearningPattern(
                pattern_type='category',
                pattern_name='테스트-패턴2',
                pattern_key='이디야',
                pattern_value='식비',
                confidence=LearningPattern.CONFIDENCE_HIGH,
                occurrence_count=3,
                status=LearningPattern.STATUS_APPLIED
            ),
            LearningPattern(
                pattern_type='payment_method',
                pattern_name='테스트-패턴3',
                pattern_key='자동이체',
                pattern_value='계좌이체',
                confidence=LearningPattern.CONFIDENCE_HIGH,
                occurrence_count=3,
                status=LearningPattern.STATUS_APPLIED
            )
        ]
        
        # 패턴 저장
        for pattern in patterns:
            self.pattern_repository.create(pattern)
        
        # 동적 필터 생성
        filters = self.learning_engine.generate_dynamic_filters()
        
        # 검증
        self.assertGreaterEqual(len(filters), 2)
        
        # 필터 내용 확인
        category_filter = next((f for f in filters if '식비' in f['name']), None)
        self.assertIsNotNone(category_filter)
        self.assertIn('conditions', category_filter)
        self.assertGreaterEqual(len(category_filter['conditions']), 1)
    
    def test_detect_pattern_changes(self):
        """
        패턴 변화 감지 테스트
        """
        # 이전 기간 거래 데이터 생성 (31-90일 전)
        today = date.today()
        
        # 이전 기간: 식비 거래 많음
        for i in range(10):
            tx_date = today - timedelta(days=40 + i)
            tx = Transaction(
                transaction_id=f"prev-food-{i+1}",
                transaction_date=tx_date,
                description=f"스타벅스 아메리카노 {i+1}",
                amount=Decimal("4500"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="식비",
                payment_method="체크카드결제",
                source="테스트"
            )
            self.transaction_repository.create(tx)
        
        # 이전 기간: 쇼핑 거래 적음
        for i in range(3):
            tx_date = today - timedelta(days=50 + i)
            tx = Transaction(
                transaction_id=f"prev-shopping-{i+1}",
                transaction_date=tx_date,
                description=f"쿠팡 생필품 {i+1}",
                amount=Decimal("15000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="온라인쇼핑",
                payment_method="체크카드결제",
                source="테스트"
            )
            self.transaction_repository.create(tx)
        
        # 최근 기간 거래 데이터 생성 (0-30일 전)
        
        # 최근 기간: 식비 거래 적음
        for i in range(3):
            tx_date = today - timedelta(days=i + 1)
            tx = Transaction(
                transaction_id=f"recent-food-{i+1}",
                transaction_date=tx_date,
                description=f"스타벅스 아메리카노 {i+1}",
                amount=Decimal("4500"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="식비",
                payment_method="체크카드결제",
                source="테스트"
            )
            self.transaction_repository.create(tx)
        
        # 최근 기간: 쇼핑 거래 많음
        for i in range(10):
            tx_date = today - timedelta(days=i + 5)
            tx = Transaction(
                transaction_id=f"recent-shopping-{i+1}",
                transaction_date=tx_date,
                description=f"쿠팡 생필품 {i+1}",
                amount=Decimal("15000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="온라인쇼핑",
                payment_method="체크카드결제",
                source="테스트"
            )
            self.transaction_repository.create(tx)
        
        # 새로운 상점 추가
        for i in range(5):
            tx_date = today - timedelta(days=i + 3)
            tx = Transaction(
                transaction_id=f"recent-new-{i+1}",
                transaction_date=tx_date,
                description=f"넷플릭스 월정액 {i+1}",
                amount=Decimal("9900"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="문화/오락",
                payment_method="체크카드결제",
                source="테스트"
            )
            self.transaction_repository.create(tx)
        
        # 패턴 변화 감지
        pattern_changes = self.learning_engine.detect_pattern_changes()
        
        # 검증
        self.assertGreater(len(pattern_changes), 0)
        
        # 카테고리 변화 확인
        category_changes = [c for c in pattern_changes if c['type'] == 'category_change']
        self.assertGreater(len(category_changes), 0)
        
        # 새 상점 확인
        new_merchant_changes = [c for c in pattern_changes if c['type'] == 'new_merchant']
        self.assertGreater(len(new_merchant_changes), 0)
        
        # 넷플릭스가 새 상점으로 감지되었는지 확인
        netflix_change = next((c for c in new_merchant_changes if '넷플릭스' in c['value']), None)
        self.assertIsNotNone(netflix_change)
    
    def test_calculate_transaction_similarity(self):
        """
        거래 유사도 계산 테스트
        """
        # 유사한 거래 생성
        tx1 = Transaction(
            transaction_id="sim-tx-1",
            transaction_date=date.today(),
            description="스타벅스 강남점 아메리카노",
            amount=Decimal("4500"),
            transaction_type=Transaction.TYPE_EXPENSE,
            category="식비",
            payment_method="체크카드결제",
            source="테스트"
        )
        
        tx2 = Transaction(
            transaction_id="sim-tx-2",
            transaction_date=date.today(),
            description="스타벅스 홍대점 아메리카노",
            amount=Decimal("4500"),
            transaction_type=Transaction.TYPE_EXPENSE,
            category="식비",
            payment_method="체크카드결제",
            source="테스트"
        )
        
        # 다른 거래 생성
        tx3 = Transaction(
            transaction_id="diff-tx-1",
            transaction_date=date.today(),
            description="이마트 생필품",
            amount=Decimal("25000"),
            transaction_type=Transaction.TYPE_EXPENSE,
            category="생활용품",
            payment_method="체크카드결제",
            source="테스트"
        )
        
        # 유사도 계산
        similarity1 = self.learning_engine._calculate_transaction_similarity(tx1, tx2)
        similarity2 = self.learning_engine._calculate_transaction_similarity(tx1, tx3)
        
        # 검증
        self.assertGreater(similarity1, 0.7)  # 유사한 거래는 높은 유사도
        self.assertLess(similarity2, 0.3)     # 다른 거래는 낮은 유사도
    
    def test_field_to_pattern_type(self):
        """
        필드명을 패턴 유형으로 변환 테스트
        """
        self.assertEqual(self.learning_engine._field_to_pattern_type('category'), 'category')
        self.assertEqual(self.learning_engine._field_to_pattern_type('payment_method'), 'payment_method')
        self.assertEqual(self.learning_engine._field_to_pattern_type('is_excluded'), 'filter')
        self.assertIsNone(self.learning_engine._field_to_pattern_type('unknown_field'))
    
    def test_extract_keywords(self):
        """
        키워드 추출 테스트
        """
        description = "스타벅스 강남점 아메리카노 4500원"
        keywords = self.learning_engine._extract_keywords(description)
        
        self.assertIn("스타벅스", keywords)
        self.assertIn("강남점", keywords)
        self.assertIn("아메리카노", keywords)
        
        # 숫자만 있는 단어는 제외되어야 함
        self.assertNotIn("4500원", keywords)
    
    def test_extract_merchant_name(self):
        """
        상점명 추출 테스트
        """
        description = "스타벅스 강남점 아메리카노"
        merchant = self.learning_engine._extract_merchant_name(description)
        
        self.assertEqual(merchant, "스타벅스")


if __name__ == '__main__':
    unittest.main()