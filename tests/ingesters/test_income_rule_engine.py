# -*- coding: utf-8 -*-
"""
IncomeRuleEngine 테스트

수입 거래에 대한 규칙 엔진을 테스트합니다.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json
import re

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ingesters.income_rule_engine import IncomeRuleEngine


class TestIncomeRuleEngine(unittest.TestCase):
    """
    IncomeRuleEngine 클래스 테스트
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        self.rule_engine = IncomeRuleEngine()
        
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
        self.assertIsNotNone(self.rule_engine.exclude_rules)
        self.assertIsNotNone(self.rule_engine.income_type_rules)
        self.assertIsInstance(self.rule_engine._exclude_regex_cache, dict)
        self.assertIsInstance(self.rule_engine._income_type_regex_cache, dict)
    
    def test_is_income_excluded(self):
        """
        수입 제외 규칙 테스트
        """
        # 제외 대상
        self.assertTrue(self.rule_engine.is_income_excluded("카드잔액 자동충전"))
        self.assertTrue(self.rule_engine.is_income_excluded("내계좌 이체"))
        self.assertTrue(self.rule_engine.is_income_excluded("계좌이체"))
        self.assertTrue(self.rule_engine.is_income_excluded("환불"))
        self.assertTrue(self.rule_engine.is_income_excluded("임시 보관"))
        
        # 제외 대상 아님
        self.assertFalse(self.rule_engine.is_income_excluded("월급"))
        self.assertFalse(self.rule_engine.is_income_excluded("이자 수익"))
        self.assertFalse(self.rule_engine.is_income_excluded("용돈"))
        self.assertFalse(self.rule_engine.is_income_excluded("판매 수익"))
    
    def test_categorize_income(self):
        """
        수입 분류 규칙 테스트
        """
        # 급여 분류
        self.assertEqual(self.rule_engine.categorize_income("월급", 2500000), "급여")
        self.assertEqual(self.rule_engine.categorize_income("급여", 1500000), "급여")
        self.assertEqual(self.rule_engine.categorize_income("상여금", 1000000), "급여")
        
        # 용돈 분류
        self.assertEqual(self.rule_engine.categorize_income("용돈", 50000), "용돈")
        self.assertEqual(self.rule_engine.categorize_income("생일 선물", 30000), "용돈")
        
        # 이자 분류
        self.assertEqual(self.rule_engine.categorize_income("이자 수익", 5000), "이자")
        self.assertEqual(self.rule_engine.categorize_income("배당금", 20000), "이자")
        
        # 환급 분류
        self.assertEqual(self.rule_engine.categorize_income("세금 환급", 150000), "환급")
        self.assertEqual(self.rule_engine.categorize_income("보험금", 200000), "환급")
        
        # 부수입 분류
        self.assertEqual(self.rule_engine.categorize_income("알바비", 300000), "부수입")
        self.assertEqual(self.rule_engine.categorize_income("강의료", 400000), "부수입")
        
        # 임대수입 분류
        self.assertEqual(self.rule_engine.categorize_income("월세", 500000), "임대수입")
        self.assertEqual(self.rule_engine.categorize_income("임대료", 600000), "임대수입")
        
        # 판매수입 분류
        self.assertEqual(self.rule_engine.categorize_income("중고 판매", 100000), "판매수입")
        self.assertEqual(self.rule_engine.categorize_income("장터 수익", 50000), "판매수입")
        
        # 금액 기반 분류
        self.assertEqual(self.rule_engine.categorize_income("입금", 2000000), "급여")
        self.assertEqual(self.rule_engine.categorize_income("입금", 700000), "부수입")
        self.assertEqual(self.rule_engine.categorize_income("입금", 300000), "부수입")
        self.assertEqual(self.rule_engine.categorize_income("입금", 50000), "용돈")
        self.assertEqual(self.rule_engine.categorize_income("입금", 5000), "기타수입")
    
    def test_add_exclude_rule(self):
        """
        수입 제외 규칙 추가 테스트
        """
        # 규칙 추가
        rule = self.rule_engine.add_exclude_rule(
            name="테스트 규칙",
            pattern=r"테스트|test",
            priority=75
        )
        
        # 규칙 확인
        self.assertEqual(rule['name'], "테스트 규칙")
        self.assertEqual(rule['pattern'], r"테스트|test")
        self.assertEqual(rule['priority'], 75)
        self.assertTrue(rule['enabled'])
        
        # 규칙 적용 확인
        self.assertTrue(self.rule_engine.is_income_excluded("테스트 입금"))
        self.assertTrue(self.rule_engine.is_income_excluded("test 입금"))
        
        # 잘못된 정규식 패턴
        with self.assertRaises(ValueError):
            self.rule_engine.add_exclude_rule(
                name="잘못된 규칙",
                pattern=r"[잘못된 정규식"
            )
    
    def test_add_income_type_rule(self):
        """
        수입 유형 규칙 추가 테스트
        """
        # 규칙 추가
        rule = self.rule_engine.add_income_type_rule(
            name="테스트 수입",
            pattern=r"테스트 수입|test income",
            target="테스트수입",
            priority=75
        )
        
        # 규칙 확인
        self.assertEqual(rule['name'], "테스트 수입")
        self.assertEqual(rule['pattern'], r"테스트 수입|test income")
        self.assertEqual(rule['target'], "테스트수입")
        self.assertEqual(rule['priority'], 75)
        self.assertTrue(rule['enabled'])
        
        # 규칙 적용 확인
        self.assertEqual(self.rule_engine.categorize_income("테스트 수입", 50000), "테스트수입")
        self.assertEqual(self.rule_engine.categorize_income("test income", 50000), "테스트수입")
        
        # 잘못된 정규식 패턴
        with self.assertRaises(ValueError):
            self.rule_engine.add_income_type_rule(
                name="잘못된 규칙",
                pattern=r"[잘못된 정규식",
                target="테스트"
            )
    
    def test_update_rule_status(self):
        """
        규칙 상태 업데이트 테스트
        """
        # 제외 규칙 상태 업데이트
        rule_name = self.rule_engine.exclude_rules[0]['name']
        result = self.rule_engine.update_rule_status('exclude', rule_name, False)
        self.assertTrue(result)
        
        # 규칙 상태 확인
        for rule in self.rule_engine.exclude_rules:
            if rule['name'] == rule_name:
                self.assertFalse(rule['enabled'])
                break
        
        # 수입 유형 규칙 상태 업데이트
        rule_name = self.rule_engine.income_type_rules[0]['name']
        result = self.rule_engine.update_rule_status('income_type', rule_name, False)
        self.assertTrue(result)
        
        # 규칙 상태 확인
        for rule in self.rule_engine.income_type_rules:
            if rule['name'] == rule_name:
                self.assertFalse(rule['enabled'])
                break
        
        # 존재하지 않는 규칙
        result = self.rule_engine.update_rule_status('exclude', '존재하지 않는 규칙', True)
        self.assertFalse(result)
        
        # 잘못된 규칙 유형
        result = self.rule_engine.update_rule_status('unknown', rule_name, True)
        self.assertFalse(result)
    
    def test_delete_rule(self):
        """
        규칙 삭제 테스트
        """
        # 제외 규칙 추가
        rule = self.rule_engine.add_exclude_rule(
            name="삭제할 규칙",
            pattern=r"삭제 테스트",
            priority=50
        )
        
        # 규칙 삭제
        result = self.rule_engine.delete_rule('exclude', "삭제할 규칙")
        self.assertTrue(result)
        
        # 규칙이 삭제되었는지 확인
        for rule in self.rule_engine.exclude_rules:
            self.assertNotEqual(rule['name'], "삭제할 규칙")
        
        # 수입 유형 규칙 추가
        rule = self.rule_engine.add_income_type_rule(
            name="삭제할 유형 규칙",
            pattern=r"삭제 유형 테스트",
            target="삭제테스트",
            priority=50
        )
        
        # 규칙 삭제
        result = self.rule_engine.delete_rule('income_type', "삭제할 유형 규칙")
        self.assertTrue(result)
        
        # 규칙이 삭제되었는지 확인
        for rule in self.rule_engine.income_type_rules:
            self.assertNotEqual(rule['name'], "삭제할 유형 규칙")
        
        # 존재하지 않는 규칙
        result = self.rule_engine.delete_rule('exclude', '존재하지 않는 규칙')
        self.assertFalse(result)
        
        # 잘못된 규칙 유형
        result = self.rule_engine.delete_rule('unknown', "삭제할 규칙")
        self.assertFalse(result)
    
    def test_get_rules(self):
        """
        규칙 목록 조회 테스트
        """
        # 제외 규칙 목록
        exclude_rules = self.rule_engine.get_rules('exclude')
        self.assertIsInstance(exclude_rules, list)
        self.assertGreater(len(exclude_rules), 0)
        
        # 우선순위 순으로 정렬되었는지 확인
        for i in range(1, len(exclude_rules)):
            self.assertGreaterEqual(exclude_rules[i-1].get('priority', 0), exclude_rules[i].get('priority', 0))
        
        # 수입 유형 규칙 목록
        income_type_rules = self.rule_engine.get_rules('income_type')
        self.assertIsInstance(income_type_rules, list)
        self.assertGreater(len(income_type_rules), 0)
        
        # 우선순위 순으로 정렬되었는지 확인
        for i in range(1, len(income_type_rules)):
            self.assertGreaterEqual(income_type_rules[i-1].get('priority', 0), income_type_rules[i].get('priority', 0))
        
        # 잘못된 규칙 유형
        rules = self.rule_engine.get_rules('unknown')
        self.assertEqual(len(rules), 0)
    
    def test_apply_rules_to_transaction(self):
        """
        거래에 규칙 적용 테스트
        """
        # 제외 대상 거래
        transaction = {
            'description': '내계좌 이체',
            'amount': 1000000,
            'memo': '자금 이동'
        }
        
        result = self.rule_engine.apply_rules_to_transaction(transaction)
        self.assertTrue(result['is_excluded'])
        
        # 카테고리 자동 분류
        transaction = {
            'description': '월급',
            'amount': 2500000,
            'memo': '1월 급여'
        }
        
        result = self.rule_engine.apply_rules_to_transaction(transaction)
        self.assertFalse(result['is_excluded'])
        self.assertEqual(result['category'], '급여')
        
        # 기존 카테고리 유지
        transaction = {
            'description': '월급',
            'amount': 2500000,
            'memo': '1월 급여',
            'category': '사용자정의'
        }
        
        result = self.rule_engine.apply_rules_to_transaction(transaction)
        self.assertFalse(result['is_excluded'])
        self.assertEqual(result['category'], '사용자정의')
    
    def test_save_and_load_rules(self):
        """
        규칙 저장 및 로드 테스트
        """
        # 규칙 추가
        self.rule_engine.add_exclude_rule(
            name="저장 테스트",
            pattern=r"저장|save",
            priority=60
        )
        
        self.rule_engine.add_income_type_rule(
            name="저장 유형 테스트",
            pattern=r"저장 유형|save type",
            target="저장테스트",
            priority=60
        )
        
        # 규칙 저장
        rules_file = os.path.join(self.temp_dir.name, 'test_rules.json')
        self.rule_engine.save_rules(rules_file)
        
        # 파일이 생성되었는지 확인
        self.assertTrue(os.path.exists(rules_file))
        
        # 새 규칙 엔진 생성
        new_engine = IncomeRuleEngine(rules_file)
        
        # 규칙이 로드되었는지 확인
        exclude_rule_names = [rule['name'] for rule in new_engine.exclude_rules]
        income_type_rule_names = [rule['name'] for rule in new_engine.income_type_rules]
        
        self.assertIn("저장 테스트", exclude_rule_names)
        self.assertIn("저장 유형 테스트", income_type_rule_names)
        
        # 규칙 적용 확인
        self.assertTrue(new_engine.is_income_excluded("저장 테스트"))
        self.assertEqual(new_engine.categorize_income("저장 유형 테스트", 50000), "저장테스트")


if __name__ == '__main__':
    unittest.main()