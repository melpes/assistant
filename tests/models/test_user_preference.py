# -*- coding: utf-8 -*-
"""
UserPreference 엔티티 클래스 테스트
"""

import unittest
from datetime import datetime

from src.models.user_preference import UserPreference


class TestUserPreference(unittest.TestCase):
    """UserPreference 클래스 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.valid_preference_data = {
            'preference_key': 'default_category',
            'preference_value': '기타',
            'description': '기본 카테고리 설정'
        }

    def test_create_valid_preference(self):
        """유효한 데이터로 설정 객체 생성 테스트"""
        preference = UserPreference(**self.valid_preference_data)
        
        self.assertEqual(preference.preference_key, 'default_category')
        self.assertEqual(preference.preference_value, '기타')
        self.assertEqual(preference.description, '기본 카테고리 설정')
        self.assertIsNotNone(preference.updated_at)

    def test_invalid_preference_key(self):
        """유효하지 않은 설정 키로 객체 생성 시 예외 발생 테스트"""
        invalid_data = self.valid_preference_data.copy()
        invalid_data['preference_key'] = 'invalid key with spaces'
        
        with self.assertRaises(ValueError):
            UserPreference(**invalid_data)

    def test_missing_required_fields(self):
        """필수 필드 누락 시 예외 발생 테스트"""
        # preference_key 누락
        invalid_data = self.valid_preference_data.copy()
        invalid_data['preference_key'] = None
        
        with self.assertRaises(ValueError):
            UserPreference(**invalid_data)
        
        # preference_value 누락
        invalid_data = self.valid_preference_data.copy()
        invalid_data['preference_value'] = None
        
        with self.assertRaises(ValueError):
            UserPreference(**invalid_data)

    def test_update_value(self):
        """설정 값 업데이트 테스트"""
        preference = UserPreference(**self.valid_preference_data)
        original_updated_at = preference.updated_at
        
        # 잠시 대기하여 업데이트 시간 차이 보장
        import time
        time.sleep(0.001)
        
        preference.update_value('식비')
        
        self.assertEqual(preference.preference_value, '식비')
        self.assertGreater(preference.updated_at, original_updated_at)

    def test_update_description(self):
        """설정 설명 업데이트 테스트"""
        preference = UserPreference(**self.valid_preference_data)
        original_updated_at = preference.updated_at
        
        # 잠시 대기하여 업데이트 시간 차이 보장
        import time
        time.sleep(0.001)
        
        preference.update_description('새로운 설명')
        
        self.assertEqual(preference.description, '새로운 설명')
        self.assertGreater(preference.updated_at, original_updated_at)

    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        preference = UserPreference(**self.valid_preference_data)
        preference_dict = preference.to_dict()
        
        self.assertEqual(preference_dict['preference_key'], 'default_category')
        self.assertEqual(preference_dict['preference_value'], '기타')
        self.assertEqual(preference_dict['description'], '기본 카테고리 설정')
        self.assertIsNotNone(preference_dict['updated_at'])

    def test_from_dict(self):
        """딕셔너리에서 객체 생성 테스트"""
        preference_dict = {
            'preference_key': 'default_payment_method',
            'preference_value': '체크카드',
            'description': '기본 결제 방식 설정',
            'updated_at': '2025-07-21T12:00:00'
        }
        
        preference = UserPreference.from_dict(preference_dict)
        
        self.assertEqual(preference.preference_key, 'default_payment_method')
        self.assertEqual(preference.preference_value, '체크카드')
        self.assertEqual(preference.description, '기본 결제 방식 설정')
        self.assertEqual(preference.updated_at, datetime(2025, 7, 21, 12, 0, 0))

    def test_get_boolean(self):
        """불리언 값 변환 테스트"""
        # True 값 테스트
        for value in ['true', 'yes', '1', 'on', 'y']:
            self.assertTrue(UserPreference.get_boolean(value))
            self.assertTrue(UserPreference.get_boolean(value.upper()))
        
        # False 값 테스트
        for value in ['false', 'no', '0', 'off', 'n', 'anything_else']:
            self.assertFalse(UserPreference.get_boolean(value))

    def test_get_int(self):
        """정수 값 변환 테스트"""
        self.assertEqual(UserPreference.get_int('123'), 123)
        self.assertEqual(UserPreference.get_int('-456'), -456)
        
        with self.assertRaises(ValueError):
            UserPreference.get_int('not_a_number')

    def test_get_float(self):
        """실수 값 변환 테스트"""
        self.assertEqual(UserPreference.get_float('123.45'), 123.45)
        self.assertEqual(UserPreference.get_float('-456.78'), -456.78)
        
        with self.assertRaises(ValueError):
            UserPreference.get_float('not_a_number')

    def test_get_list(self):
        """리스트 값 변환 테스트"""
        # 기본 구분자(,) 테스트
        self.assertEqual(
            UserPreference.get_list('item1,item2,item3'),
            ['item1', 'item2', 'item3']
        )
        
        # 공백 처리 테스트
        self.assertEqual(
            UserPreference.get_list('item1, item2,  item3'),
            ['item1', 'item2', 'item3']
        )
        
        # 빈 항목 제외 테스트
        self.assertEqual(
            UserPreference.get_list('item1,,item2,'),
            ['item1', 'item2']
        )
        
        # 사용자 정의 구분자 테스트
        self.assertEqual(
            UserPreference.get_list('item1;item2;item3', delimiter=';'),
            ['item1', 'item2', 'item3']
        )

    def test_get_value_as(self):
        """값 타입 변환 테스트"""
        # 문자열 설정
        preference = UserPreference(
            preference_key='test_key',
            preference_value='test_value'
        )
        self.assertEqual(preference.get_value_as('str'), 'test_value')
        
        # 불리언 설정
        preference = UserPreference(
            preference_key='test_bool',
            preference_value='yes'
        )
        self.assertTrue(preference.get_value_as('bool'))
        
        # 정수 설정
        preference = UserPreference(
            preference_key='test_int',
            preference_value='123'
        )
        self.assertEqual(preference.get_value_as('int'), 123)
        
        # 실수 설정
        preference = UserPreference(
            preference_key='test_float',
            preference_value='123.45'
        )
        self.assertEqual(preference.get_value_as('float'), 123.45)
        
        # 리스트 설정
        preference = UserPreference(
            preference_key='test_list',
            preference_value='item1,item2,item3'
        )
        self.assertEqual(preference.get_value_as('list'), ['item1', 'item2', 'item3'])
        
        # 지원하지 않는 타입
        with self.assertRaises(ValueError):
            preference.get_value_as('unsupported_type')


if __name__ == '__main__':
    unittest.main()
