# -*- coding: utf-8 -*-
"""
필터 엔진(FilterEngine) 테스트

필터 엔진의 기능을 테스트합니다.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date

from src.filter_engine import FilterEngine
from src.models.analysis_filter import AnalysisFilter
from src.models.transaction import Transaction
from src.repositories.filter_repository import FilterRepository


class TestFilterEngine(unittest.TestCase):
    """필터 엔진 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 필터 저장소 모의 객체 생성
        self.mock_repository = MagicMock(spec=FilterRepository)
        
        # 필터 엔진 생성
        self.filter_engine = FilterEngine(self.mock_repository)
        
        # 테스트용 거래 데이터 생성
        self.transactions = [
            Transaction(
                transaction_id="tx1",
                transaction_date=date(2023, 1, 1),
                description="식당 결제",
                amount=15000,
                transaction_type="expense",
                category="식비",
                payment_method="체크카드결제",
                source="토스뱅크카드"
            ),
            Transaction(
                transaction_id="tx2",
                transaction_date=date(2023, 1, 2),
                description="마트 결제",
                amount=30000,
                transaction_type="expense",
                category="생활용품",
                payment_method="체크카드결제",
                source="토스뱅크카드"
            ),
            Transaction(
                transaction_id="tx3",
                transaction_date=date(2023, 1, 3),
                description="월급",
                amount=3000000,
                transaction_type="income",
                category="급여",
                payment_method="계좌이체",
                source="토스뱅크계좌"
            ),
            Transaction(
                transaction_id="tx4",
                transaction_date=date(2023, 1, 4),
                description="교통비",
                amount=5000,
                transaction_type="expense",
                category="교통비",
                payment_method="체크카드결제",
                source="토스뱅크카드"
            )
        ]
    
    def test_apply_filter_category(self):
        """카테고리 필터 적용 테스트"""
        # 카테고리 필터 생성
        filter_obj = AnalysisFilter(
            filter_name="식비 필터",
            filter_config={
                'conditions': {
                    'field': 'category',
                    'comparison': 'equals',
                    'value': '식비'
                }
            }
        )
        
        # 필터 적용
        result = self.filter_engine.apply_filter(self.transactions, filter_obj)
        
        # 결과 검증
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].transaction_id, "tx1")
        self.assertEqual(result[0].category, "식비")
    
    def test_apply_filter_amount_range(self):
        """금액 범위 필터 적용 테스트"""
        # 금액 범위 필터 생성
        filter_obj = AnalysisFilter(
            filter_name="소액 지출",
            filter_config={
                'conditions': {
                    'field': 'amount',
                    'comparison': 'between',
                    'min_value': 5000,
                    'max_value': 20000
                }
            }
        )
        
        # 필터 적용
        result = self.filter_engine.apply_filter(self.transactions, filter_obj)
        
        # 결과 검증
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].transaction_id, "tx1")
        self.assertEqual(result[1].transaction_id, "tx4")
    
    def test_apply_filter_transaction_type(self):
        """거래 유형 필터 적용 테스트"""
        # 거래 유형 필터 생성
        filter_obj = AnalysisFilter(
            filter_name="수입만",
            filter_config={
                'conditions': {
                    'field': 'transaction_type',
                    'comparison': 'equals',
                    'value': 'income'
                }
            }
        )
        
        # 필터 적용
        result = self.filter_engine.apply_filter(self.transactions, filter_obj)
        
        # 결과 검증
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].transaction_id, "tx3")
        self.assertEqual(result[0].transaction_type, "income")
    
    def test_apply_filter_description_contains(self):
        """설명 포함 필터 적용 테스트"""
        # 설명 포함 필터 생성
        filter_obj = AnalysisFilter(
            filter_name="결제 포함",
            filter_config={
                'conditions': {
                    'field': 'description',
                    'comparison': 'contains',
                    'value': '결제'
                }
            }
        )
        
        # 필터 적용
        result = self.filter_engine.apply_filter(self.transactions, filter_obj)
        
        # 결과 검증
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].transaction_id, "tx1")
        self.assertEqual(result[1].transaction_id, "tx2")
    
    def test_apply_complex_filter(self):
        """복합 필터 적용 테스트"""
        # 복합 필터 생성 (카드 결제 + 10000원 이상)
        filter_obj = AnalysisFilter(
            filter_name="카드 고액 결제",
            filter_config={
                'conditions': {
                    'operator': 'and',
                    'conditions': [
                        {
                            'field': 'payment_method',
                            'comparison': 'equals',
                            'value': '체크카드결제'
                        },
                        {
                            'field': 'amount',
                            'comparison': 'greater_than',
                            'value': 10000
                        }
                    ]
                }
            }
        )
        
        # 필터 적용
        result = self.filter_engine.apply_filter(self.transactions, filter_obj)
        
        # 결과 검증
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].transaction_id, "tx1")
        self.assertEqual(result[1].transaction_id, "tx2")
    
    def test_apply_filter_by_id(self):
        """ID로 필터 적용 테스트"""
        # 모의 필터 객체 생성
        mock_filter = AnalysisFilter(
            id=1,
            filter_name="테스트 필터",
            filter_config={
                'conditions': {
                    'field': 'category',
                    'comparison': 'equals',
                    'value': '식비'
                }
            }
        )
        
        # 저장소 모의 동작 설정
        self.mock_repository.get_by_id.return_value = mock_filter
        
        # 필터 적용
        result = self.filter_engine.apply_filter_by_id(self.transactions, 1)
        
        # 저장소 호출 검증
        self.mock_repository.get_by_id.assert_called_once_with(1)
        
        # 결과 검증
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].transaction_id, "tx1")
    
    def test_apply_filter_by_name(self):
        """이름으로 필터 적용 테스트"""
        # 모의 필터 객체 생성
        mock_filter = AnalysisFilter(
            id=1,
            filter_name="식비 필터",
            filter_config={
                'conditions': {
                    'field': 'category',
                    'comparison': 'equals',
                    'value': '식비'
                }
            }
        )
        
        # 저장소 모의 동작 설정
        self.mock_repository.get_by_name.return_value = mock_filter
        
        # 필터 적용
        result = self.filter_engine.apply_filter_by_name(self.transactions, "식비 필터")
        
        # 저장소 호출 검증
        self.mock_repository.get_by_name.assert_called_once_with("식비 필터")
        
        # 결과 검증
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].transaction_id, "tx1")
    
    def test_apply_default_filter(self):
        """기본 필터 적용 테스트"""
        # 모의 필터 객체 생성
        mock_filter = AnalysisFilter(
            id=1,
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
        
        # 저장소 모의 동작 설정
        self.mock_repository.get_default.return_value = mock_filter
        
        # 필터 적용
        result = self.filter_engine.apply_default_filter(self.transactions)
        
        # 저장소 호출 검증
        self.mock_repository.get_default.assert_called_once()
        
        # 결과 검증
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].transaction_id, "tx1")
        self.assertEqual(result[1].transaction_id, "tx2")
        self.assertEqual(result[2].transaction_id, "tx4")
    
    def test_apply_combined_filters_and(self):
        """AND 연산자로 필터 조합 적용 테스트"""
        # 모의 필터 객체 생성
        mock_filter1 = AnalysisFilter(
            id=1,
            filter_name="체크카드 필터",
            filter_config={
                'conditions': {
                    'field': 'payment_method',
                    'comparison': 'equals',
                    'value': '체크카드결제'
                }
            }
        )
        
        mock_filter2 = AnalysisFilter(
            id=2,
            filter_name="소액 필터",
            filter_config={
                'conditions': {
                    'field': 'amount',
                    'comparison': 'less_than',
                    'value': 10000
                }
            }
        )
        
        # 저장소 모의 동작 설정
        self.mock_repository.get_by_id.side_effect = lambda id: mock_filter1 if id == 1 else mock_filter2
        
        # 필터 조합 적용
        result = self.filter_engine.apply_combined_filters(
            self.transactions, [1, 2], AnalysisFilter.OP_AND
        )
        
        # 저장소 호출 검증
        self.mock_repository.get_by_id.assert_any_call(1)
        self.mock_repository.get_by_id.assert_any_call(2)
        
        # 결과 검증
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].transaction_id, "tx4")
    
    def test_apply_combined_filters_or(self):
        """OR 연산자로 필터 조합 적용 테스트"""
        # 모의 필터 객체 생성
        mock_filter1 = AnalysisFilter(
            id=1,
            filter_name="식비 필터",
            filter_config={
                'conditions': {
                    'field': 'category',
                    'comparison': 'equals',
                    'value': '식비'
                }
            }
        )
        
        mock_filter2 = AnalysisFilter(
            id=2,
            filter_name="수입 필터",
            filter_config={
                'conditions': {
                    'field': 'transaction_type',
                    'comparison': 'equals',
                    'value': 'income'
                }
            }
        )
        
        # 저장소 모의 동작 설정
        self.mock_repository.get_by_id.side_effect = lambda id: mock_filter1 if id == 1 else mock_filter2
        
        # 필터 조합 적용
        result = self.filter_engine.apply_combined_filters(
            self.transactions, [1, 2], AnalysisFilter.OP_OR
        )
        
        # 저장소 호출 검증
        self.mock_repository.get_by_id.assert_any_call(1)
        self.mock_repository.get_by_id.assert_any_call(2)
        
        # 결과 검증
        self.assertEqual(len(result), 2)
        # 원본 순서가 유지되므로 tx1이 먼저 나와야 함
        self.assertEqual(result[0].transaction_id, "tx1")
        self.assertEqual(result[1].transaction_id, "tx3")
    
    def test_create_filter(self):
        """필터 생성 테스트"""
        # 필터 생성
        self.filter_engine.create_filter("테스트 필터")
        
        # 저장소 호출 검증
        self.mock_repository.save.assert_called_once()
        
        # 저장된 필터 검증
        saved_filter = self.mock_repository.save.call_args[0][0]
        self.assertEqual(saved_filter.filter_name, "테스트 필터")
        self.assertEqual(saved_filter.is_default, False)
    
    def test_save_filter(self):
        """필터 저장 테스트"""
        # 필터 객체 생성
        filter_obj = AnalysisFilter(
            filter_name="저장 테스트",
            filter_config={'conditions': []}
        )
        
        # 저장소 모의 동작 설정
        self.mock_repository.save.return_value = 1
        
        # 필터 저장
        filter_id = self.filter_engine.save_filter(filter_obj)
        
        # 저장소 호출 검증
        self.mock_repository.save.assert_called_once_with(filter_obj)
        
        # 결과 검증
        self.assertEqual(filter_id, 1)
    
    def test_delete_filter(self):
        """필터 삭제 테스트"""
        # 저장소 모의 동작 설정
        self.mock_repository.delete.return_value = True
        
        # 필터 삭제
        result = self.filter_engine.delete_filter(1)
        
        # 저장소 호출 검증
        self.mock_repository.delete.assert_called_once_with(1)
        
        # 결과 검증
        self.assertTrue(result)
    
    def test_get_all_filters(self):
        """모든 필터 조회 테스트"""
        # 모의 필터 객체 생성
        mock_filters = [
            AnalysisFilter(id=1, filter_name="필터1", filter_config={'conditions': []}),
            AnalysisFilter(id=2, filter_name="필터2", filter_config={'conditions': []})
        ]
        
        # 저장소 모의 동작 설정
        self.mock_repository.get_all.return_value = mock_filters
        
        # 모든 필터 조회
        result = self.filter_engine.get_all_filters()
        
        # 저장소 호출 검증
        self.mock_repository.get_all.assert_called_once()
        
        # 결과 검증
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 2)
    
    def test_create_dynamic_filter(self):
        """동적 필터 생성 테스트"""
        # 조건 정의
        conditions = {
            'operator': 'and',
            'conditions': [
                {
                    'field': 'category',
                    'comparison': 'equals',
                    'value': '식비'
                },
                {
                    'field': 'amount',
                    'comparison': 'less_than',
                    'value': 20000
                }
            ]
        }
        
        # 동적 필터 생성 (저장 안 함)
        filter_obj = self.filter_engine.create_dynamic_filter(conditions, "동적 필터", False)
        
        # 저장소 호출 검증
        self.mock_repository.save.assert_not_called()
        
        # 필터 검증
        self.assertEqual(filter_obj.filter_name, "동적 필터")
        self.assertEqual(filter_obj.filter_config['conditions'], conditions)
        
        # 동적 필터 생성 (저장)
        filter_obj = self.filter_engine.create_dynamic_filter(conditions, "저장 필터", True)
        
        # 저장소 호출 검증
        self.mock_repository.save.assert_called_once_with(filter_obj)


if __name__ == '__main__':
    unittest.main()