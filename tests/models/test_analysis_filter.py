# -*- coding: utf-8 -*-
"""
AnalysisFilter 엔티티 클래스 테스트
"""

import unittest
from datetime import datetime
import json

from src.models.analysis_filter import AnalysisFilter


class TestAnalysisFilter(unittest.TestCase):
    """AnalysisFilter 클래스 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.valid_filter_data = {
            'filter_name': '테스트 필터',
            'filter_config': {
                'conditions': {
                    'operator': AnalysisFilter.OP_AND,
                    'conditions': [
                        {
                            'field': 'category',
                            'comparison': AnalysisFilter.COMP_EQUALS,
                            'value': '식비'
                        },
                        {
                            'field': 'amount',
                            'comparison': AnalysisFilter.COMP_GREATER_THAN,
                            'value': '10000'
                        }
                    ]
                }
            },
            'is_default': False
        }

    def test_create_valid_filter(self):
        """유효한 데이터로 필터 객체 생성 테스트"""
        filter_obj = AnalysisFilter(**self.valid_filter_data)
        
        self.assertEqual(filter_obj.filter_name, '테스트 필터')
        self.assertEqual(filter_obj.filter_config['conditions']['operator'], AnalysisFilter.OP_AND)
        self.assertEqual(len(filter_obj.filter_config['conditions']['conditions']), 2)
        self.assertFalse(filter_obj.is_default)
        self.assertIsNotNone(filter_obj.created_at)

    def test_create_filter_with_json_string(self):
        """JSON 문자열로 필터 객체 생성 테스트"""
        filter_data = self.valid_filter_data.copy()
        filter_data['filter_config'] = json.dumps(filter_data['filter_config'])
        
        filter_obj = AnalysisFilter(**filter_data)
        
        self.assertEqual(filter_obj.filter_name, '테스트 필터')
        self.assertEqual(filter_obj.filter_config['conditions']['operator'], AnalysisFilter.OP_AND)
        self.assertEqual(len(filter_obj.filter_config['conditions']['conditions']), 2)

    def test_invalid_json_string(self):
        """유효하지 않은 JSON 문자열로 객체 생성 시 예외 발생 테스트"""
        filter_data = self.valid_filter_data.copy()
        filter_data['filter_config'] = '{invalid json}'
        
        with self.assertRaises(ValueError):
            AnalysisFilter(**filter_data)

    def test_missing_required_fields(self):
        """필수 필드 누락 시 예외 발생 테스트"""
        # filter_name 누락
        invalid_data = self.valid_filter_data.copy()
        invalid_data['filter_name'] = None
        
        with self.assertRaises(ValueError):
            AnalysisFilter(**invalid_data)
        
        # filter_config 누락
        invalid_data = self.valid_filter_data.copy()
        invalid_data['filter_config'] = None
        
        with self.assertRaises(ValueError):
            AnalysisFilter(**invalid_data)

    def test_invalid_filter_config_structure(self):
        """유효하지 않은 필터 설정 구조로 객체 생성 시 예외 발생 테스트"""
        invalid_data = self.valid_filter_data.copy()
        invalid_data['filter_config'] = 'not_a_dict'
        
        with self.assertRaises(ValueError):
            AnalysisFilter(**invalid_data)

    def test_invalid_operator(self):
        """유효하지 않은 연산자로 조건 검증 시 예외 발생 테스트"""
        invalid_data = self.valid_filter_data.copy()
        invalid_data['filter_config']['conditions']['operator'] = 'invalid_operator'
        
        with self.assertRaises(ValueError):
            AnalysisFilter(**invalid_data)

    def test_invalid_comparison(self):
        """유효하지 않은 비교 연산자로 조건 검증 시 예외 발생 테스트"""
        invalid_data = self.valid_filter_data.copy()
        invalid_data['filter_config']['conditions']['conditions'][0]['comparison'] = 'invalid_comparison'
        
        with self.assertRaises(ValueError):
            AnalysisFilter(**invalid_data)

    def test_missing_value_in_condition(self):
        """비교 조건에서 value 누락 시 예외 발생 테스트"""
        invalid_data = self.valid_filter_data.copy()
        del invalid_data['filter_config']['conditions']['conditions'][0]['value']
        
        with self.assertRaises(ValueError):
            AnalysisFilter(**invalid_data)

    def test_between_comparison_missing_values(self):
        """between 비교에서 min_value/max_value 누락 시 예외 발생 테스트"""
        invalid_data = self.valid_filter_data.copy()
        invalid_data['filter_config']['conditions']['conditions'][0]['comparison'] = AnalysisFilter.COMP_BETWEEN
        del invalid_data['filter_config']['conditions']['conditions'][0]['value']
        
        with self.assertRaises(ValueError):
            AnalysisFilter(**invalid_data)

    def test_set_as_default(self):
        """기본값 설정 테스트"""
        filter_obj = AnalysisFilter(**self.valid_filter_data)
        
        self.assertFalse(filter_obj.is_default)
        
        filter_obj.set_as_default()
        self.assertTrue(filter_obj.is_default)
        
        filter_obj.unset_as_default()
        self.assertFalse(filter_obj.is_default)

    def test_add_condition(self):
        """조건 추가 테스트"""
        # 빈 필터 생성
        filter_obj = AnalysisFilter(
            filter_name='빈 필터',
            filter_config={}
        )
        
        # 조건 추가
        filter_obj.add_condition(
            field='category',
            comparison=AnalysisFilter.COMP_EQUALS,
            value='식비'
        )
        
        # 조건 구조 확인
        self.assertIn('conditions', filter_obj.filter_config)
        self.assertEqual(filter_obj.filter_config['conditions']['operator'], AnalysisFilter.OP_AND)
        self.assertEqual(len(filter_obj.filter_config['conditions']['conditions']), 1)
        
        # 조건 내용 확인
        condition = filter_obj.filter_config['conditions']['conditions'][0]
        self.assertEqual(condition['field'], 'category')
        self.assertEqual(condition['comparison'], AnalysisFilter.COMP_EQUALS)
        self.assertEqual(condition['value'], '식비')
        
        # between 조건 추가
        filter_obj.add_condition(
            field='amount',
            comparison=AnalysisFilter.COMP_BETWEEN,
            min_value=1000,
            max_value=5000
        )
        
        # between 조건 확인
        condition = filter_obj.filter_config['conditions']['conditions'][1]
        self.assertEqual(condition['field'], 'amount')
        self.assertEqual(condition['comparison'], AnalysisFilter.COMP_BETWEEN)
        self.assertEqual(condition['min_value'], 1000)
        self.assertEqual(condition['max_value'], 5000)

    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        filter_obj = AnalysisFilter(**self.valid_filter_data)
        filter_dict = filter_obj.to_dict()
        
        self.assertEqual(filter_dict['filter_name'], '테스트 필터')
        self.assertEqual(filter_dict['filter_config'], self.valid_filter_data['filter_config'])
        self.assertFalse(filter_dict['is_default'])
        self.assertIsNotNone(filter_dict['created_at'])

    def test_from_dict(self):
        """딕셔너리에서 객체 생성 테스트"""
        filter_dict = {
            'filter_name': '딕셔너리 필터',
            'filter_config': {
                'conditions': {
                    'operator': AnalysisFilter.OP_OR,
                    'conditions': [
                        {
                            'field': 'payment_method',
                            'comparison': AnalysisFilter.COMP_EQUALS,
                            'value': '신용카드'
                        }
                    ]
                }
            },
            'is_default': True,
            'created_at': '2025-07-21T12:00:00'
        }
        
        filter_obj = AnalysisFilter.from_dict(filter_dict)
        
        self.assertEqual(filter_obj.filter_name, '딕셔너리 필터')
        self.assertEqual(filter_obj.filter_config['conditions']['operator'], AnalysisFilter.OP_OR)
        self.assertTrue(filter_obj.is_default)
        self.assertEqual(filter_obj.created_at, datetime(2025, 7, 21, 12, 0, 0))

    def test_matches_and_condition(self):
        """AND 조건 매칭 테스트"""
        filter_obj = AnalysisFilter(**self.valid_filter_data)  # category='식비' AND amount>'10000'
        
        # 두 조건 모두 일치
        transaction_data = {'category': '식비', 'amount': '15000'}
        self.assertTrue(filter_obj.matches(transaction_data))
        
        # 첫 번째 조건만 일치
        transaction_data = {'category': '식비', 'amount': '5000'}
        self.assertFalse(filter_obj.matches(transaction_data))
        
        # 두 번째 조건만 일치
        transaction_data = {'category': '교통비', 'amount': '15000'}
        self.assertFalse(filter_obj.matches(transaction_data))
        
        # 두 조건 모두 불일치
        transaction_data = {'category': '교통비', 'amount': '5000'}
        self.assertFalse(filter_obj.matches(transaction_data))

    def test_matches_or_condition(self):
        """OR 조건 매칭 테스트"""
        filter_data = self.valid_filter_data.copy()
        filter_data['filter_config']['conditions']['operator'] = AnalysisFilter.OP_OR
        filter_obj = AnalysisFilter(**filter_data)  # category='식비' OR amount>'10000'
        
        # 두 조건 모두 일치
        transaction_data = {'category': '식비', 'amount': '15000'}
        self.assertTrue(filter_obj.matches(transaction_data))
        
        # 첫 번째 조건만 일치
        transaction_data = {'category': '식비', 'amount': '5000'}
        self.assertTrue(filter_obj.matches(transaction_data))
        
        # 두 번째 조건만 일치
        transaction_data = {'category': '교통비', 'amount': '15000'}
        self.assertTrue(filter_obj.matches(transaction_data))
        
        # 두 조건 모두 불일치
        transaction_data = {'category': '교통비', 'amount': '5000'}
        self.assertFalse(filter_obj.matches(transaction_data))

    def test_matches_contains_condition(self):
        """contains 조건 매칭 테스트"""
        filter_data = {
            'filter_name': 'Contains 테스트',
            'filter_config': {
                'conditions': {
                    'field': 'description',
                    'comparison': AnalysisFilter.COMP_CONTAINS,
                    'value': '스타벅스'
                }
            }
        }
        filter_obj = AnalysisFilter(**filter_data)
        
        # 일치하는 경우
        transaction_data = {'description': '스타벅스 아메리카노'}
        self.assertTrue(filter_obj.matches(transaction_data))
        
        # 일치하지 않는 경우
        transaction_data = {'description': '커피빈 아메리카노'}
        self.assertFalse(filter_obj.matches(transaction_data))

    def test_matches_not_contains_condition(self):
        """not_contains 조건 매칭 테스트"""
        filter_data = {
            'filter_name': 'Not Contains 테스트',
            'filter_config': {
                'conditions': {
                    'field': 'description',
                    'comparison': AnalysisFilter.COMP_NOT_CONTAINS,
                    'value': '스타벅스'
                }
            }
        }
        filter_obj = AnalysisFilter(**filter_data)
        
        # 일치하는 경우 (포함하지 않음)
        transaction_data = {'description': '커피빈 아메리카노'}
        self.assertTrue(filter_obj.matches(transaction_data))
        
        # 일치하지 않는 경우 (포함함)
        transaction_data = {'description': '스타벅스 아메리카노'}
        self.assertFalse(filter_obj.matches(transaction_data))

    def test_matches_in_list_condition(self):
        """in_list 조건 매칭 테스트"""
        filter_data = {
            'filter_name': 'In List 테스트',
            'filter_config': {
                'conditions': {
                    'field': 'category',
                    'comparison': AnalysisFilter.COMP_IN_LIST,
                    'value': ['식비', '교통비', '생활용품']
                }
            }
        }
        filter_obj = AnalysisFilter(**filter_data)
        
        # 목록에 있는 경우
        transaction_data = {'category': '식비'}
        self.assertTrue(filter_obj.matches(transaction_data))
        
        transaction_data = {'category': '교통비'}
        self.assertTrue(filter_obj.matches(transaction_data))
        
        # 목록에 없는 경우
        transaction_data = {'category': '의료비'}
        self.assertFalse(filter_obj.matches(transaction_data))


if __name__ == '__main__':
    unittest.main()
