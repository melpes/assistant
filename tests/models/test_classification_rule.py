# -*- coding: utf-8 -*-
"""
ClassificationRule 엔티티 클래스 테스트
"""

import unittest
from datetime import datetime

from src.models.classification_rule import ClassificationRule


class TestClassificationRule(unittest.TestCase):
    """ClassificationRule 클래스 테스트"""

    def setUp(self):
        """테스트 데이터 설정"""
        self.valid_rule_data = {
            'rule_name': '테스트 규칙',
            'rule_type': ClassificationRule.TYPE_CATEGORY,
            'condition_type': ClassificationRule.CONDITION_CONTAINS,
            'condition_value': '스타벅스',
            'target_value': '식비',
            'priority': 10
        }

    def test_create_valid_rule(self):
        """유효한 데이터로 규칙 객체 생성 테스트"""
        rule = ClassificationRule(**self.valid_rule_data)
        
        self.assertEqual(rule.rule_name, '테스트 규칙')
        self.assertEqual(rule.rule_type, ClassificationRule.TYPE_CATEGORY)
        self.assertEqual(rule.condition_type, ClassificationRule.CONDITION_CONTAINS)
        self.assertEqual(rule.condition_value, '스타벅스')
        self.assertEqual(rule.target_value, '식비')
        self.assertEqual(rule.priority, 10)
        self.assertTrue(rule.is_active)
        self.assertEqual(rule.created_by, 'user')
        self.assertIsNotNone(rule.created_at)

    def test_invalid_rule_type(self):
        """유효하지 않은 규칙 유형으로 객체 생성 시 예외 발생 테스트"""
        invalid_data = self.valid_rule_data.copy()
        invalid_data['rule_type'] = 'invalid_type'
        
        with self.assertRaises(ValueError):
            ClassificationRule(**invalid_data)

    def test_invalid_condition_type(self):
        """유효하지 않은 조건 유형으로 객체 생성 시 예외 발생 테스트"""
        invalid_data = self.valid_rule_data.copy()
        invalid_data['condition_type'] = 'invalid_condition'
        
        with self.assertRaises(ValueError):
            ClassificationRule(**invalid_data)

    def test_invalid_creator_type(self):
        """유효하지 않은 생성자 유형으로 객체 생성 시 예외 발생 테스트"""
        invalid_data = self.valid_rule_data.copy()
        invalid_data['created_by'] = 'invalid_creator'
        
        with self.assertRaises(ValueError):
            ClassificationRule(**invalid_data)

    def test_invalid_amount_range_format(self):
        """유효하지 않은 금액 범위 형식으로 객체 생성 시 예외 발생 테스트"""
        invalid_data = self.valid_rule_data.copy()
        invalid_data['condition_type'] = ClassificationRule.CONDITION_AMOUNT_RANGE
        invalid_data['condition_value'] = 'invalid_range'
        
        with self.assertRaises(ValueError):
            ClassificationRule(**invalid_data)

    def test_valid_amount_range_format(self):
        """유효한 금액 범위 형식으로 객체 생성 테스트"""
        valid_data = self.valid_rule_data.copy()
        valid_data['condition_type'] = ClassificationRule.CONDITION_AMOUNT_RANGE
        valid_data['condition_value'] = '1000:5000'
        
        rule = ClassificationRule(**valid_data)
        self.assertEqual(rule.condition_value, '1000:5000')

    def test_activate_deactivate(self):
        """규칙 활성화/비활성화 테스트"""
        rule = ClassificationRule(**self.valid_rule_data)
        
        self.assertTrue(rule.is_active)
        
        rule.deactivate()
        self.assertFalse(rule.is_active)
        
        rule.activate()
        self.assertTrue(rule.is_active)

    def test_update_priority(self):
        """우선순위 업데이트 테스트"""
        rule = ClassificationRule(**self.valid_rule_data)
        
        self.assertEqual(rule.priority, 10)
        
        rule.update_priority(20)
        self.assertEqual(rule.priority, 20)

    def test_matches_contains(self):
        """contains 조건 매칭 테스트"""
        rule = ClassificationRule(**self.valid_rule_data)  # CONDITION_CONTAINS, '스타벅스'
        
        # 일치하는 경우
        transaction_data = {'description': '스타벅스 아메리카노'}
        self.assertTrue(rule.matches(transaction_data))
        
        # 대소문자 무관하게 일치하는 경우
        transaction_data = {'description': '스타벅스 AMERICANO'}
        self.assertTrue(rule.matches(transaction_data))
        
        # 일치하지 않는 경우
        transaction_data = {'description': '커피빈 아메리카노'}
        self.assertFalse(rule.matches(transaction_data))

    def test_matches_equals(self):
        """equals 조건 매칭 테스트"""
        rule_data = self.valid_rule_data.copy()
        rule_data['condition_type'] = ClassificationRule.CONDITION_EQUALS
        rule_data['condition_value'] = '스타벅스'
        rule = ClassificationRule(**rule_data)
        
        # 일치하는 경우
        transaction_data = {'description': '스타벅스'}
        self.assertTrue(rule.matches(transaction_data))
        
        # 대소문자 무관하게 일치하는 경우
        transaction_data = {'description': '스타벅스'}
        self.assertTrue(rule.matches(transaction_data))
        
        # 일치하지 않는 경우
        transaction_data = {'description': '스타벅스 아메리카노'}
        self.assertFalse(rule.matches(transaction_data))

    def test_matches_regex(self):
        """regex 조건 매칭 테스트"""
        rule_data = self.valid_rule_data.copy()
        rule_data['condition_type'] = ClassificationRule.CONDITION_REGEX
        rule_data['condition_value'] = '스타벅스|커피빈'
        rule = ClassificationRule(**rule_data)
        
        # 일치하는 경우 (스타벅스)
        transaction_data = {'description': '스타벅스 아메리카노'}
        self.assertTrue(rule.matches(transaction_data))
        
        # 일치하는 경우 (커피빈)
        transaction_data = {'description': '커피빈 라떼'}
        self.assertTrue(rule.matches(transaction_data))
        
        # 일치하지 않는 경우
        transaction_data = {'description': '이디야 아메리카노'}
        self.assertFalse(rule.matches(transaction_data))

    def test_matches_amount_range(self):
        """amount_range 조건 매칭 테스트"""
        rule_data = self.valid_rule_data.copy()
        rule_data['condition_type'] = ClassificationRule.CONDITION_AMOUNT_RANGE
        rule_data['condition_value'] = '1000:5000'
        rule = ClassificationRule(**rule_data)
        
        # 범위 내 (최소값)
        transaction_data = {'amount': '1000'}
        self.assertTrue(rule.matches(transaction_data))
        
        # 범위 내 (최대값)
        transaction_data = {'amount': '5000'}
        self.assertTrue(rule.matches(transaction_data))
        
        # 범위 내 (중간값)
        transaction_data = {'amount': '3000'}
        self.assertTrue(rule.matches(transaction_data))
        
        # 범위 밖 (최소값 미만)
        transaction_data = {'amount': '999'}
        self.assertFalse(rule.matches(transaction_data))
        
        # 범위 밖 (최대값 초과)
        transaction_data = {'amount': '5001'}
        self.assertFalse(rule.matches(transaction_data))

    def test_to_dict(self):
        """딕셔너리 변환 테스트"""
        rule = ClassificationRule(**self.valid_rule_data)
        rule_dict = rule.to_dict()
        
        self.assertEqual(rule_dict['rule_name'], '테스트 규칙')
        self.assertEqual(rule_dict['rule_type'], ClassificationRule.TYPE_CATEGORY)
        self.assertEqual(rule_dict['condition_type'], ClassificationRule.CONDITION_CONTAINS)
        self.assertEqual(rule_dict['condition_value'], '스타벅스')
        self.assertEqual(rule_dict['target_value'], '식비')
        self.assertEqual(rule_dict['priority'], 10)
        self.assertTrue(rule_dict['is_active'])
        self.assertEqual(rule_dict['created_by'], 'user')
        self.assertIsNotNone(rule_dict['created_at'])

    def test_from_dict(self):
        """딕셔너리에서 객체 생성 테스트"""
        rule_dict = {
            'rule_name': '딕셔너리 규칙',
            'rule_type': ClassificationRule.TYPE_PAYMENT_METHOD,
            'condition_type': ClassificationRule.CONDITION_EQUALS,
            'condition_value': '현대카드',
            'target_value': '신용카드',
            'priority': 5,
            'is_active': False,
            'created_by': ClassificationRule.CREATOR_SYSTEM,
            'created_at': '2025-07-21T12:00:00'
        }
        
        rule = ClassificationRule.from_dict(rule_dict)
        
        self.assertEqual(rule.rule_name, '딕셔너리 규칙')
        self.assertEqual(rule.rule_type, ClassificationRule.TYPE_PAYMENT_METHOD)
        self.assertEqual(rule.condition_type, ClassificationRule.CONDITION_EQUALS)
        self.assertEqual(rule.condition_value, '현대카드')
        self.assertEqual(rule.target_value, '신용카드')
        self.assertEqual(rule.priority, 5)
        self.assertFalse(rule.is_active)
        self.assertEqual(rule.created_by, ClassificationRule.CREATOR_SYSTEM)
        self.assertEqual(rule.created_at, datetime(2025, 7, 21, 12, 0, 0))


if __name__ == '__main__':
    unittest.main()
