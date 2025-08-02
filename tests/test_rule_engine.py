# -*- coding: utf-8 -*-
"""
규칙 엔진(RuleEngine) 테스트
"""

import unittest
from unittest.mock import Mock, patch
from datetime import date, datetime
from decimal import Decimal

from src.models import ClassificationRule, Transaction
from src.rule_engine import RuleEngine


class TestRuleEngine(unittest.TestCase):
    """규칙 엔진 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 규칙 저장소 Mock 생성
        self.rule_repository = Mock()
        
        # 규칙 엔진 생성
        self.rule_engine = RuleEngine(self.rule_repository)
        
        # 테스트용 규칙 생성
        self.rules = [
            ClassificationRule(
                id=1,
                rule_name="식비 규칙",
                rule_type="category",
                condition_type="contains",
                condition_value="식당",
                target_value="식비",
                priority=100,
                is_active=True
            ),
            ClassificationRule(
                id=2,
                rule_name="카페 규칙",
                rule_type="category",
                condition_type="contains",
                condition_value="카페",
                target_value="식비",
                priority=90,
                is_active=True
            ),
            ClassificationRule(
                id=3,
                rule_name="교통비 규칙",
                rule_type="category",
                condition_type="regex",
                condition_value="택시|버스|지하철",
                target_value="교통비",
                priority=80,
                is_active=True
            ),
            ClassificationRule(
                id=4,
                rule_name="소액 현금 규칙",
                rule_type="payment_method",
                condition_type="amount_range",
                condition_value="0:10000",
                target_value="현금",
                priority=70,
                is_active=True
            ),
            ClassificationRule(
                id=5,
                rule_name="비활성 규칙",
                rule_type="category",
                condition_type="contains",
                condition_value="마트",
                target_value="생활용품",
                priority=60,
                is_active=False
            )
        ]
        
        # 테스트용 거래 생성
        self.transactions = [
            Transaction(
                id=1,
                transaction_id="tx001",
                transaction_date=date(2023, 1, 1),
                description="서울식당 점심",
                amount=Decimal("15000"),
                transaction_type="expense",
                source="toss_card"
            ),
            Transaction(
                id=2,
                transaction_id="tx002",
                transaction_date=date(2023, 1, 2),
                description="스타벅스 카페",
                amount=Decimal("5500"),
                transaction_type="expense",
                source="toss_card"
            ),
            Transaction(
                id=3,
                transaction_id="tx003",
                transaction_date=date(2023, 1, 3),
                description="시내버스 요금",
                amount=Decimal("1200"),
                transaction_type="expense",
                source="toss_card"
            ),
            Transaction(
                id=4,
                transaction_id="tx004",
                transaction_date=date(2023, 1, 4),
                description="홈플러스 마트",
                amount=Decimal("45000"),
                transaction_type="expense",
                source="toss_card"
            )
        ]
    
    def test_apply_rules_with_contains_condition(self):
        """contains 조건 규칙 적용 테스트"""
        # Mock 설정
        self.rule_repository.get_active_rules_by_type.return_value = [
            rule for rule in self.rules if rule.rule_type == "category" and rule.is_active
        ]
        
        # 규칙 적용
        result = self.rule_engine.apply_rules(self.transactions[0], "category")
        
        # 검증
        self.assertEqual(result, "식비")
        self.rule_repository.get_active_rules_by_type.assert_called_once_with("category")
    
    def test_apply_rules_with_regex_condition(self):
        """regex 조건 규칙 적용 테스트"""
        # Mock 설정
        self.rule_repository.get_active_rules_by_type.return_value = [
            rule for rule in self.rules if rule.rule_type == "category" and rule.is_active
        ]
        
        # 규칙 적용
        result = self.rule_engine.apply_rules(self.transactions[2], "category")
        
        # 검증
        self.assertEqual(result, "교통비")
    
    def test_apply_rules_with_amount_range_condition(self):
        """amount_range 조건 규칙 적용 테스트"""
        # Mock 설정
        self.rule_repository.get_active_rules_by_type.return_value = [
            rule for rule in self.rules if rule.rule_type == "payment_method" and rule.is_active
        ]
        
        # 규칙 적용
        result = self.rule_engine.apply_rules(self.transactions[2], "payment_method")
        
        # 검증
        self.assertEqual(result, "현금")
    
    def test_apply_rules_no_match(self):
        """일치하는 규칙이 없는 경우 테스트"""
        # Mock 설정
        self.rule_repository.get_active_rules_by_type.return_value = [
            rule for rule in self.rules if rule.rule_type == "category" and rule.is_active
        ]
        
        # 규칙 적용 (마트는 비활성 규칙이므로 매칭되지 않음)
        result = self.rule_engine.apply_rules(self.transactions[3], "category")
        
        # 검증
        self.assertIsNone(result)
    
    def test_apply_rules_batch(self):
        """일괄 규칙 적용 테스트"""
        # Mock 설정
        self.rule_repository.get_active_rules_by_type.return_value = [
            rule for rule in self.rules if rule.rule_type == "category" and rule.is_active
        ]
        
        # 일괄 규칙 적용
        results = self.rule_engine.apply_rules_batch(self.transactions, "category")
        
        # 검증
        self.assertEqual(len(results), 3)  # 마트는 비활성 규칙이므로 매칭되지 않음
        self.assertEqual(results["tx001"], "식비")
        self.assertEqual(results["tx002"], "식비")
        self.assertEqual(results["tx003"], "교통비")
        self.assertNotIn("tx004", results)
    
    def test_add_rule(self):
        """규칙 추가 테스트"""
        # 새 규칙 생성
        new_rule = ClassificationRule(
            rule_name="새 규칙",
            rule_type="category",
            condition_type="contains",
            condition_value="편의점",
            target_value="식비",
            priority=50
        )
        
        # Mock 설정
        self.rule_repository.create.return_value = ClassificationRule(
            id=6,
            rule_name="새 규칙",
            rule_type="category",
            condition_type="contains",
            condition_value="편의점",
            target_value="식비",
            priority=50
        )
        
        # 규칙 추가
        result = self.rule_engine.add_rule(new_rule)
        
        # 검증
        self.assertEqual(result.id, 6)
        self.rule_repository.create.assert_called_once_with(new_rule)
    
    def test_update_rule(self):
        """규칙 업데이트 테스트"""
        # 업데이트할 규칙
        rule = ClassificationRule(
            id=1,
            rule_name="식비 규칙 수정",
            rule_type="category",
            condition_type="contains",
            condition_value="식당",
            target_value="식비",
            priority=200
        )
        
        # Mock 설정
        self.rule_repository.update.return_value = rule
        
        # 규칙 업데이트
        result = self.rule_engine.update_rule(rule)
        
        # 검증
        self.assertEqual(result.priority, 200)
        self.rule_repository.update.assert_called_once_with(rule)
    
    def test_update_rule_without_id(self):
        """ID 없는 규칙 업데이트 시 예외 발생 테스트"""
        # ID가 없는 규칙
        rule = ClassificationRule(
            rule_name="ID 없는 규칙",
            rule_type="category",
            condition_type="contains",
            condition_value="테스트",
            target_value="테스트"
        )
        
        # 예외 발생 확인
        with self.assertRaises(ValueError):
            self.rule_engine.update_rule(rule)
    
    def test_delete_rule(self):
        """규칙 삭제 테스트"""
        # Mock 설정
        self.rule_repository.read.return_value = self.rules[0]
        self.rule_repository.delete.return_value = True
        
        # 규칙 삭제
        result = self.rule_engine.delete_rule(1)
        
        # 검증
        self.assertTrue(result)
        self.rule_repository.read.assert_called_once_with(1)
        self.rule_repository.delete.assert_called_once_with(1)
    
    def test_delete_nonexistent_rule(self):
        """존재하지 않는 규칙 삭제 테스트"""
        # Mock 설정
        self.rule_repository.read.return_value = None
        
        # 존재하지 않는 규칙 삭제
        result = self.rule_engine.delete_rule(999)
        
        # 검증
        self.assertFalse(result)
        self.rule_repository.read.assert_called_once_with(999)
        self.rule_repository.delete.assert_not_called()
    
    def test_update_rule_priority(self):
        """규칙 우선순위 업데이트 테스트"""
        # Mock 설정
        self.rule_repository.read.return_value = self.rules[0]
        
        # 우선순위 업데이트
        result = self.rule_engine.update_rule_priority(1, 300)
        
        # 검증
        self.assertTrue(result)
        self.rule_repository.read.assert_called_once_with(1)
        self.rule_repository.update.assert_called_once()
        self.assertEqual(self.rule_repository.update.call_args[0][0].priority, 300)
    
    def test_resolve_conflicts(self):
        """규칙 충돌 해결 테스트"""
        # 충돌하는 규칙 생성
        conflicting_rules = [
            ClassificationRule(
                id=1,
                rule_name="규칙 1",
                rule_type="category",
                condition_type="contains",
                condition_value="테스트",
                target_value="카테고리1",
                priority=100,
                is_active=True
            ),
            ClassificationRule(
                id=2,
                rule_name="규칙 2",
                rule_type="category",
                condition_type="contains",
                condition_value="테스트",
                target_value="카테고리2",
                priority=50,
                is_active=True
            )
        ]
        
        # Mock 설정
        self.rule_repository.get_active_rules_by_type.return_value = conflicting_rules
        
        # 충돌 해결
        conflicts = self.rule_engine.resolve_conflicts("category")
        
        # 검증
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0][0].id, 1)  # 우선순위 높은 규칙
        self.assertEqual(conflicts[0][1].id, 2)  # 우선순위 낮은 규칙
    
    def test_get_rule_stats(self):
        """규칙 통계 테스트"""
        # Mock 설정
        self.rule_repository.get_active_rules_by_type.return_value = [
            rule for rule in self.rules if rule.rule_type == "category" and rule.is_active
        ]
        
        # 통계 조회
        stats = self.rule_engine.get_rule_stats("category")
        
        # 검증
        self.assertEqual(stats['total_rules'], 3)
        self.assertEqual(stats['condition_counts']['contains'], 2)
        self.assertEqual(stats['condition_counts']['regex'], 1)
        self.assertEqual(stats['target_counts']['식비'], 2)
        self.assertEqual(stats['target_counts']['교통비'], 1)
    
    def test_cache_invalidation(self):
        """캐시 무효화 테스트"""
        # 캐시 설정
        self.rule_engine._rule_cache = {
            "category": self.rules[:3],
            "payment_method": [self.rules[3]]
        }
        
        # 캐시 무효화
        self.rule_engine._invalidate_cache("category")
        
        # 검증
        self.assertNotIn("category", self.rule_engine._rule_cache)
        self.assertIn("payment_method", self.rule_engine._rule_cache)
    
    def test_clear_cache(self):
        """캐시 초기화 테스트"""
        # 캐시 설정
        self.rule_engine._rule_cache = {
            "category": self.rules[:3],
            "payment_method": [self.rules[3]]
        }
        self.rule_engine._cache_timestamp = {
            "category": datetime.now(),
            "payment_method": datetime.now()
        }
        
        # 캐시 초기화
        self.rule_engine.clear_cache()
        
        # 검증
        self.assertEqual(len(self.rule_engine._rule_cache), 0)
        self.assertEqual(len(self.rule_engine._cache_timestamp), 0)


if __name__ == '__main__':
    unittest.main()