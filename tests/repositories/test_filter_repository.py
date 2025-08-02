# -*- coding: utf-8 -*-
"""
필터 저장소(FilterRepository) 테스트

필터 저장소의 기능을 테스트합니다.
"""

import unittest
import os
import sqlite3
from datetime import datetime

from src.models.analysis_filter import AnalysisFilter
from src.repositories.filter_repository import FilterRepository
from src.repositories.db_connection import DatabaseConnection


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


class TestFilterRepository(unittest.TestCase):
    """필터 저장소 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트용 데이터베이스 파일 경로
        self.test_db_path = "test_filter_repository.db"
        
        # 기존 테스트 DB 파일이 있으면 삭제
        try:
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
        except PermissionError:
            # 파일이 사용 중인 경우 고유한 파일 이름 생성
            import uuid
            self.test_db_path = f"test_filter_repository_{uuid.uuid4().hex}.db"
        
        # 테스트용 데이터베이스 연결
        self.db_connection = MockDatabaseConnection(self.test_db_path)
        
        # 필터 저장소 생성
        self.repository = FilterRepository(self.db_connection)
    
    def tearDown(self):
        """테스트 정리"""
        # 데이터베이스 연결 닫기
        self.db_connection.close()
        
        # 테스트 DB 파일 삭제
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_save_and_get_by_id(self):
        """필터 저장 및 ID로 조회 테스트"""
        # 필터 객체 생성
        filter_obj = AnalysisFilter(
            filter_name="테스트 필터",
            filter_config={
                'conditions': {
                    'field': 'category',
                    'comparison': 'equals',
                    'value': '식비'
                }
            }
        )
        
        # 필터 저장
        filter_id = self.repository.save(filter_obj)
        
        # ID 검증
        self.assertIsNotNone(filter_id)
        self.assertGreater(filter_id, 0)
        
        # 필터 조회
        retrieved_filter = self.repository.get_by_id(filter_id)
        
        # 조회 결과 검증
        self.assertIsNotNone(retrieved_filter)
        self.assertEqual(retrieved_filter.id, filter_id)
        self.assertEqual(retrieved_filter.filter_name, "테스트 필터")
        self.assertEqual(retrieved_filter.filter_config['conditions']['field'], "category")
        self.assertEqual(retrieved_filter.filter_config['conditions']['comparison'], "equals")
        self.assertEqual(retrieved_filter.filter_config['conditions']['value'], "식비")
    
    def test_get_by_name(self):
        """이름으로 필터 조회 테스트"""
        # 필터 객체 생성
        filter_obj = AnalysisFilter(
            filter_name="이름 테스트",
            filter_config={
                'conditions': {
                    'field': 'amount',
                    'comparison': 'greater_than',
                    'value': 10000
                }
            }
        )
        
        # 필터 저장
        self.repository.save(filter_obj)
        
        # 이름으로 필터 조회
        retrieved_filter = self.repository.get_by_name("이름 테스트")
        
        # 조회 결과 검증
        self.assertIsNotNone(retrieved_filter)
        self.assertEqual(retrieved_filter.filter_name, "이름 테스트")
        self.assertEqual(retrieved_filter.filter_config['conditions']['field'], "amount")
    
    def test_update_filter(self):
        """필터 업데이트 테스트"""
        # 필터 객체 생성
        filter_obj = AnalysisFilter(
            filter_name="업데이트 전",
            filter_config={
                'conditions': {
                    'field': 'category',
                    'comparison': 'equals',
                    'value': '식비'
                }
            }
        )
        
        # 필터 저장
        filter_id = self.repository.save(filter_obj)
        
        # 필터 조회 및 수정
        retrieved_filter = self.repository.get_by_id(filter_id)
        retrieved_filter.filter_name = "업데이트 후"
        retrieved_filter.filter_config['conditions']['value'] = "교통비"
        
        # 수정된 필터 저장
        self.repository.save(retrieved_filter)
        
        # 다시 조회
        updated_filter = self.repository.get_by_id(filter_id)
        
        # 업데이트 결과 검증
        self.assertEqual(updated_filter.filter_name, "업데이트 후")
        self.assertEqual(updated_filter.filter_config['conditions']['value'], "교통비")
    
    def test_get_default(self):
        """기본 필터 조회 테스트"""
        # 일반 필터 객체 생성
        filter1 = AnalysisFilter(
            filter_name="일반 필터",
            filter_config={'conditions': []},
            is_default=False
        )
        
        # 기본 필터 객체 생성
        filter2 = AnalysisFilter(
            filter_name="기본 필터",
            filter_config={'conditions': []},
            is_default=True
        )
        
        # 필터 저장
        self.repository.save(filter1)
        self.repository.save(filter2)
        
        # 기본 필터 조회
        default_filter = self.repository.get_default()
        
        # 조회 결과 검증
        self.assertIsNotNone(default_filter)
        self.assertEqual(default_filter.filter_name, "기본 필터")
        self.assertTrue(default_filter.is_default)
    
    def test_default_filter_exclusivity(self):
        """기본 필터 배타성 테스트"""
        # 기본 필터 객체 생성
        filter1 = AnalysisFilter(
            filter_name="기본 필터 1",
            filter_config={'conditions': []},
            is_default=True
        )
        
        # 다른 기본 필터 객체 생성
        filter2 = AnalysisFilter(
            filter_name="기본 필터 2",
            filter_config={'conditions': []},
            is_default=True
        )
        
        # 필터 저장
        self.repository.save(filter1)
        self.repository.save(filter2)
        
        # 첫 번째 필터 조회
        filter1_updated = self.repository.get_by_name("기본 필터 1")
        
        # 두 번째 필터 조회
        filter2_updated = self.repository.get_by_name("기본 필터 2")
        
        # 결과 검증
        self.assertFalse(filter1_updated.is_default)
        self.assertTrue(filter2_updated.is_default)
    
    def test_get_all(self):
        """모든 필터 조회 테스트"""
        # 필터 객체 생성
        filter1 = AnalysisFilter(
            filter_name="필터 1",
            filter_config={'conditions': []}
        )
        
        filter2 = AnalysisFilter(
            filter_name="필터 2",
            filter_config={'conditions': []}
        )
        
        filter3 = AnalysisFilter(
            filter_name="필터 3",
            filter_config={'conditions': []}
        )
        
        # 필터 저장
        self.repository.save(filter1)
        self.repository.save(filter2)
        self.repository.save(filter3)
        
        # 모든 필터 조회
        all_filters = self.repository.get_all()
        
        # 결과 검증
        self.assertEqual(len(all_filters), 3)
        self.assertEqual(all_filters[0].filter_name, "필터 1")
        self.assertEqual(all_filters[1].filter_name, "필터 2")
        self.assertEqual(all_filters[2].filter_name, "필터 3")
    
    def test_delete(self):
        """필터 삭제 테스트"""
        # 필터 객체 생성
        filter_obj = AnalysisFilter(
            filter_name="삭제 테스트",
            filter_config={'conditions': []}
        )
        
        # 필터 저장
        filter_id = self.repository.save(filter_obj)
        
        # 필터 삭제
        delete_result = self.repository.delete(filter_id)
        
        # 삭제 결과 검증
        self.assertTrue(delete_result)
        
        # 삭제된 필터 조회
        deleted_filter = self.repository.get_by_id(filter_id)
        
        # 조회 결과 검증
        self.assertIsNone(deleted_filter)
    
    def test_complex_filter_config(self):
        """복잡한 필터 설정 테스트"""
        # 복잡한 필터 설정
        complex_config = {
            'conditions': {
                'operator': 'and',
                'conditions': [
                    {
                        'field': 'category',
                        'comparison': 'equals',
                        'value': '식비'
                    },
                    {
                        'operator': 'or',
                        'conditions': [
                            {
                                'field': 'amount',
                                'comparison': 'less_than',
                                'value': 10000
                            },
                            {
                                'field': 'description',
                                'comparison': 'contains',
                                'value': '카페'
                            }
                        ]
                    }
                ]
            }
        }
        
        # 필터 객체 생성
        filter_obj = AnalysisFilter(
            filter_name="복잡한 필터",
            filter_config=complex_config
        )
        
        # 필터 저장
        filter_id = self.repository.save(filter_obj)
        
        # 필터 조회
        retrieved_filter = self.repository.get_by_id(filter_id)
        
        # 조회 결과 검증
        self.assertIsNotNone(retrieved_filter)
        self.assertEqual(retrieved_filter.filter_name, "복잡한 필터")
        
        # 복잡한 설정 검증
        conditions = retrieved_filter.filter_config['conditions']
        self.assertEqual(conditions['operator'], 'and')
        self.assertEqual(len(conditions['conditions']), 2)
        self.assertEqual(conditions['conditions'][0]['field'], 'category')
        self.assertEqual(conditions['conditions'][1]['operator'], 'or')


if __name__ == '__main__':
    unittest.main()