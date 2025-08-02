# -*- coding: utf-8 -*-
"""
필터 엔진(FilterEngine) 통합 테스트

필터 엔진과 저장소의 통합 기능을 테스트합니다.
"""

import unittest
import os
import sqlite3
from datetime import datetime, date, timedelta

from src.filter_engine import FilterEngine
from src.models.analysis_filter import AnalysisFilter
from src.models.transaction import Transaction
from src.repositories.filter_repository import FilterRepository


class MockDatabaseConnection:
    """
    테스트용 데이터베이스 연결 모의 객체
    """
    
    def __init__(self, db_path):
        """
        모의 데이터베이스 연결 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
    
    def execute_query(self, query, params=()):
        """
        SQL 쿼리 실행
        
        Args:
            query: SQL 쿼리 문자열
            params: 쿼리 파라미터 (선택)
            
        Returns:
            sqlite3.Cursor: 쿼리 결과 커서
        """
        return self.connection.execute(query, params)
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.connection:
            self.connection.close()


class TestFilterEngineIntegration(unittest.TestCase):
    """필터 엔진 통합 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트용 데이터베이스 파일 경로
        self.test_db_path = "test_filter_engine_integration.db"
        
        # 기존 테스트 DB 파일이 있으면 삭제
        try:
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
        except PermissionError:
            # 파일이 사용 중인 경우 고유한 파일 이름 생성
            import uuid
            self.test_db_path = f"test_filter_engine_integration_{uuid.uuid4().hex}.db"
        
        # 테스트용 데이터베이스 연결
        self.db_connection = MockDatabaseConnection(self.test_db_path)
        
        # 필터 저장소 생성
        self.repository = FilterRepository(self.db_connection)
        
        # 필터 엔진 생성
        self.filter_engine = FilterEngine(self.repository)
        
        # 테스트용 거래 데이터 생성
        self.transactions = self._create_test_transactions()
    
    def tearDown(self):
        """테스트 정리"""
        # 데이터베이스 연결 닫기
        self.db_connection.close()
        
        # 테스트 DB 파일 삭제
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def _create_test_transactions(self):
        """테스트용 거래 데이터 생성"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)
        
        return [
            Transaction(
                transaction_id="tx1",
                transaction_date=today,
                description="식당 결제",
                amount=15000,
                transaction_type="expense",
                category="식비",
                payment_method="체크카드결제",
                source="토스뱅크카드"
            ),
            Transaction(
                transaction_id="tx2",
                transaction_date=yesterday,
                description="마트 결제",
                amount=30000,
                transaction_type="expense",
                category="생활용품",
                payment_method="체크카드결제",
                source="토스뱅크카드"
            ),
            Transaction(
                transaction_id="tx3",
                transaction_date=last_week,
                description="월급",
                amount=3000000,
                transaction_type="income",
                category="급여",
                payment_method="계좌이체",
                source="토스뱅크계좌"
            ),
            Transaction(
                transaction_id="tx4",
                transaction_date=last_week,
                description="교통비",
                amount=5000,
                transaction_type="expense",
                category="교통비",
                payment_method="체크카드결제",
                source="토스뱅크카드"
            ),
            Transaction(
                transaction_id="tx5",
                transaction_date=last_month,
                description="카페",
                amount=8000,
                transaction_type="expense",
                category="식비",
                payment_method="체크카드결제",
                source="토스뱅크카드"
            ),
            Transaction(
                transaction_id="tx6",
                transaction_date=last_month,
                description="영화관",
                amount=25000,
                transaction_type="expense",
                category="문화/오락",
                payment_method="체크카드결제",
                source="토스뱅크카드"
            ),
            Transaction(
                transaction_id="tx7",
                transaction_date=today,
                description="용돈",
                amount=100000,
                transaction_type="income",
                category="용돈",
                payment_method="계좌이체",
                source="토스뱅크계좌"
            )
        ]
    
    def test_create_save_and_apply_filter(self):
        """필터 생성, 저장 및 적용 통합 테스트"""
        # 필터 생성
        filter_obj = self.filter_engine.create_filter("식비 필터")
        
        # 필터에 조건 추가
        filter_obj.add_condition("category", AnalysisFilter.COMP_EQUALS, "식비")
        
        # 필터 저장
        filter_id = self.filter_engine.save_filter(filter_obj)
        
        # 필터 적용
        filtered_transactions = self.filter_engine.apply_filter_by_id(self.transactions, filter_id)
        
        # 결과 검증
        self.assertEqual(len(filtered_transactions), 2)
        self.assertEqual(filtered_transactions[0].transaction_id, "tx1")
        self.assertEqual(filtered_transactions[1].transaction_id, "tx5")
    
    def test_create_dynamic_filter_and_save(self):
        """동적 필터 생성 및 저장 통합 테스트"""
        # 동적 필터 조건 정의
        conditions = {
            'operator': 'and',
            'conditions': [
                {
                    'field': 'transaction_type',
                    'comparison': 'equals',
                    'value': 'expense'
                },
                {
                    'field': 'amount',
                    'comparison': 'greater_than',
                    'value': 10000
                }
            ]
        }
        
        # 동적 필터 생성 및 저장
        filter_obj = self.filter_engine.create_dynamic_filter(conditions, "고액 지출", True)
        
        # 필터 적용
        filtered_transactions = self.filter_engine.apply_filter(self.transactions, filter_obj)
        
        # 결과 검증
        self.assertEqual(len(filtered_transactions), 3)
        self.assertEqual(filtered_transactions[0].transaction_id, "tx2")
        self.assertEqual(filtered_transactions[1].transaction_id, "tx6")
    
    def test_default_filter(self):
        """기본 필터 통합 테스트"""
        # 일반 필터 생성
        filter1 = AnalysisFilter(
            filter_name="일반 필터",
            filter_config={
                'conditions': {
                    'field': 'category',
                    'comparison': 'equals',
                    'value': '식비'
                }
            }
        )
        
        # 기본 필터 생성
        filter2 = AnalysisFilter(
            filter_name="기본 필터",
            filter_config={
                'conditions': {
                    'field': 'transaction_type',
                    'comparison': 'equals',
                    'value': 'expense'
                }
            },
            is_default=True
        )
        
        # 필터 저장
        self.filter_engine.save_filter(filter1)
        self.filter_engine.save_filter(filter2)
        
        # 기본 필터 적용
        filtered_transactions = self.filter_engine.apply_default_filter(self.transactions)
        
        # 결과 검증
        self.assertEqual(len(filtered_transactions), 5)  # 지출 거래만
    
    def test_combined_filters(self):
        """필터 조합 통합 테스트"""
        # 첫 번째 필터: 최근 거래 (7일 이내)
        filter1 = AnalysisFilter(
            filter_name="최근 거래",
            filter_config={
                'conditions': {
                    'field': 'transaction_date',
                    'comparison': 'greater_than',
                    'value': (date.today() - timedelta(days=7)).isoformat()
                }
            }
        )
        
        # 두 번째 필터: 식비 카테고리
        filter2 = AnalysisFilter(
            filter_name="식비 필터",
            filter_config={
                'conditions': {
                    'field': 'category',
                    'comparison': 'equals',
                    'value': '식비'
                }
            }
        )
        
        # 필터 저장
        filter_id1 = self.filter_engine.save_filter(filter1)
        filter_id2 = self.filter_engine.save_filter(filter2)
        
        # AND 조합 적용
        and_result = self.filter_engine.apply_combined_filters(
            self.transactions, [filter_id1, filter_id2], AnalysisFilter.OP_AND
        )
        
        # AND 결과 검증
        self.assertEqual(len(and_result), 1)  # 최근 7일 내 식비 거래
        self.assertEqual(and_result[0].transaction_id, "tx1")
        
        # OR 조합 적용
        or_result = self.filter_engine.apply_combined_filters(
            self.transactions, [filter_id1, filter_id2], AnalysisFilter.OP_OR
        )
        
        # OR 결과 검증
        self.assertEqual(len(or_result), 5)  # 최근 7일 내 거래 또는 식비 거래
    
    def test_filter_cache(self):
        """필터 캐시 통합 테스트"""
        # 필터 생성 및 저장
        filter_obj = AnalysisFilter(
            filter_name="캐시 테스트",
            filter_config={
                'conditions': {
                    'field': 'category',
                    'comparison': 'equals',
                    'value': '식비'
                }
            }
        )
        
        filter_id = self.filter_engine.save_filter(filter_obj)
        
        # 첫 번째 조회 (저장소에서 로드)
        self.filter_engine.apply_filter_by_id(self.transactions, filter_id)
        
        # 저장소 모의 객체로 교체하여 캐시 확인
        original_repository = self.filter_engine.filter_repository
        mock_repository = unittest.mock.MagicMock(spec=FilterRepository)
        self.filter_engine.filter_repository = mock_repository
        
        # 두 번째 조회 (캐시에서 로드)
        self.filter_engine.apply_filter_by_id(self.transactions, filter_id)
        
        # 저장소 호출 여부 확인
        mock_repository.get_by_id.assert_not_called()
        
        # 원래 저장소 복원
        self.filter_engine.filter_repository = original_repository
    
    def test_filter_deletion(self):
        """필터 삭제 통합 테스트"""
        # 필터 생성 및 저장
        filter_obj = AnalysisFilter(
            filter_name="삭제 테스트",
            filter_config={
                'conditions': {
                    'field': 'category',
                    'comparison': 'equals',
                    'value': '식비'
                }
            }
        )
        
        filter_id = self.filter_engine.save_filter(filter_obj)
        
        # 필터 삭제
        delete_result = self.filter_engine.delete_filter(filter_id)
        
        # 삭제 결과 검증
        self.assertTrue(delete_result)
        
        # 삭제된 필터로 조회 시도
        with self.assertRaises(ValueError):
            self.filter_engine.apply_filter_by_id(self.transactions, filter_id)


if __name__ == '__main__':
    unittest.main()