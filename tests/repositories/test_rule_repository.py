# -*- coding: utf-8 -*-
"""
RuleRepository 테스트
"""

import os
import unittest
from datetime import datetime
import tempfile

from src.models import ClassificationRule
from src.repositories.db_connection import DatabaseConnection
from src.repositories.rule_repository import RuleRepository


class TestRuleRepository(unittest.TestCase):
    """RuleRepository 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 데이터베이스 파일 생성
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False).name
        self.db_connection = DatabaseConnection(self.temp_db_file)
        self.repository = RuleRepository(self.db_connection)
        
        # 테스트 데이터 생성
        self.test_rule = ClassificationRule(
            rule_name="테스트 규칙",
            rule_type=ClassificationRule.TYPE_CATEGORY,
            condition_type=ClassificationRule.CONDITION_CONTAINS,
            condition_value="테스트",
            target_value="테스트 카테고리",
            priority=10,
            is_active=True,
            created_by=ClassificationRule.CREATOR_USER
        )
    
    def tearDown(self):
        """테스트 정리"""
        self.db_connection.close()
        if os.path.exists(self.temp_db_file):
            os.unlink(self.temp_db_file)
    
    def test_create_rule(self):
        """규칙 생성 테스트"""
        # 규칙 생성
        created = self.repository.create(self.test_rule)
        
        # 검증
        self.assertIsNotNone(created.id)
        self.assertEqual(created.rule_name, self.test_rule.rule_name)
        self.assertEqual(created.rule_type, self.test_rule.rule_type)
        self.assertEqual(created.condition_type, self.test_rule.condition_type)
        self.assertEqual(created.condition_value, self.test_rule.condition_value)
        self.assertEqual(created.target_value, self.test_rule.target_value)
        self.assertEqual(created.priority, self.test_rule.priority)
        self.assertEqual(created.is_active, self.test_rule.is_active)
        self.assertEqual(created.created_by, self.test_rule.created_by)
    
    def test_read_rule(self):
        """규칙 조회 테스트"""
        # 규칙 생성
        created = self.repository.create(self.test_rule)
        
        # ID로 조회
        read = self.repository.read(created.id)
        
        # 검증
        self.assertIsNotNone(read)
        self.assertEqual(read.id, created.id)
        self.assertEqual(read.rule_name, created.rule_name)
        self.assertEqual(read.rule_type, created.rule_type)
        self.assertEqual(read.condition_type, created.condition_type)
        self.assertEqual(read.condition_value, created.condition_value)
        self.assertEqual(read.target_value, created.target_value)
    
    def test_update_rule(self):
        """규칙 업데이트 테스트"""
        # 규칙 생성
        created = self.repository.create(self.test_rule)
        
        # 규칙 수정
        created.rule_name = "수정된 규칙"
        created.target_value = "수정된 카테고리"
        created.priority = 20
        created.is_active = False
        updated = self.repository.update(created)
        
        # 검증
        self.assertEqual(updated.rule_name, "수정된 규칙")
        self.assertEqual(updated.target_value, "수정된 카테고리")
        self.assertEqual(updated.priority, 20)
        self.assertEqual(updated.is_active, False)
        
        # 데이터베이스에서 다시 조회하여 검증
        read = self.repository.read(created.id)
        self.assertEqual(read.rule_name, "수정된 규칙")
        self.assertEqual(read.target_value, "수정된 카테고리")
        self.assertEqual(read.priority, 20)
        self.assertEqual(read.is_active, False)
    
    def test_delete_rule(self):
        """규칙 삭제 테스트"""
        # 규칙 생성
        created = self.repository.create(self.test_rule)
        
        # 삭제
        result = self.repository.delete(created.id)
        
        # 검증
        self.assertTrue(result)
        self.assertIsNone(self.repository.read(created.id))
    
    def test_list_rules(self):
        """규칙 목록 조회 테스트"""
        # 여러 규칙 생성
        rules = []
        rule_types = [
            ClassificationRule.TYPE_CATEGORY,
            ClassificationRule.TYPE_PAYMENT_METHOD,
            ClassificationRule.TYPE_CATEGORY,
            ClassificationRule.TYPE_FILTER,
            ClassificationRule.TYPE_PAYMENT_METHOD
        ]
        
        for i, rule_type in enumerate(rule_types):
            rule = ClassificationRule(
                rule_name=f"테스트 규칙 {i+1}",
                rule_type=rule_type,
                condition_type=ClassificationRule.CONDITION_CONTAINS,
                condition_value=f"테스트 {i+1}",
                target_value=f"테스트 결과 {i+1}",
                priority=i*10,
                is_active=i % 2 == 0,
                created_by=ClassificationRule.CREATOR_USER if i % 2 == 0 else ClassificationRule.CREATOR_SYSTEM
            )
            created = self.repository.create(rule)
            rules.append(created)
        
        # 모든 규칙 조회
        all_rules = self.repository.list()
        self.assertEqual(len(all_rules), 5)
        
        # 필터링 테스트: 규칙 유형
        category_rules = self.repository.list({"rule_type": ClassificationRule.TYPE_CATEGORY})
        self.assertEqual(len(category_rules), 2)
        
        # 필터링 테스트: 활성화 여부
        active_rules = self.repository.list({"is_active": True})
        self.assertEqual(len(active_rules), 3)
        
        # 필터링 테스트: 생성자
        user_rules = self.repository.list({"created_by": ClassificationRule.CREATOR_USER})
        self.assertEqual(len(user_rules), 3)
        
        # 필터링 테스트: 우선순위 범위
        priority_rules = self.repository.list({
            "min_priority": 10,
            "max_priority": 30
        })
        self.assertEqual(len(priority_rules), 3)
    
    def test_count_rules(self):
        """규칙 수 조회 테스트"""
        # 여러 규칙 생성
        rule_types = [
            ClassificationRule.TYPE_CATEGORY,
            ClassificationRule.TYPE_PAYMENT_METHOD,
            ClassificationRule.TYPE_CATEGORY,
            ClassificationRule.TYPE_FILTER,
            ClassificationRule.TYPE_PAYMENT_METHOD
        ]
        
        for i, rule_type in enumerate(rule_types):
            rule = ClassificationRule(
                rule_name=f"테스트 규칙 {i+1}",
                rule_type=rule_type,
                condition_type=ClassificationRule.CONDITION_CONTAINS,
                condition_value=f"테스트 {i+1}",
                target_value=f"테스트 결과 {i+1}",
                priority=i*10,
                is_active=i % 2 == 0,
                created_by=ClassificationRule.CREATOR_USER if i % 2 == 0 else ClassificationRule.CREATOR_SYSTEM
            )
            self.repository.create(rule)
        
        # 모든 규칙 수 조회
        count = self.repository.count()
        self.assertEqual(count, 5)
        
        # 필터링 테스트: 규칙 유형
        category_count = self.repository.count({"rule_type": ClassificationRule.TYPE_CATEGORY})
        self.assertEqual(category_count, 2)
        
        # 필터링 테스트: 활성화 여부
        active_count = self.repository.count({"is_active": True})
        self.assertEqual(active_count, 3)
    
    def test_exists_rule(self):
        """규칙 존재 여부 테스트"""
        # 규칙 생성
        created = self.repository.create(self.test_rule)
        
        # 존재 여부 확인
        self.assertTrue(self.repository.exists(created.id))
        self.assertFalse(self.repository.exists(999))
    
    def test_get_active_rules_by_type(self):
        """유형별 활성화된 규칙 목록 조회 테스트"""
        # 여러 규칙 생성
        for i in range(5):
            rule = ClassificationRule(
                rule_name=f"카테고리 규칙 {i+1}",
                rule_type=ClassificationRule.TYPE_CATEGORY,
                condition_type=ClassificationRule.CONDITION_CONTAINS,
                condition_value=f"테스트 {i+1}",
                target_value=f"테스트 카테고리 {i+1}",
                priority=i*10,
                is_active=i % 2 == 0  # 0, 2, 4번 인덱스만 활성화
            )
            self.repository.create(rule)
        
        # 다른 유형의 규칙도 생성
        payment_rule = ClassificationRule(
            rule_name="결제 방식 규칙",
            rule_type=ClassificationRule.TYPE_PAYMENT_METHOD,
            condition_type=ClassificationRule.CONDITION_CONTAINS,
            condition_value="카드",
            target_value="신용카드",
            is_active=True
        )
        self.repository.create(payment_rule)
        
        # 카테고리 유형의 활성화된 규칙 조회
        active_category_rules = self.repository.get_active_rules_by_type(ClassificationRule.TYPE_CATEGORY)
        
        # 검증
        self.assertEqual(len(active_category_rules), 3)  # 0, 2, 4번 인덱스
        
        # 우선순위 순으로 정렬되었는지 확인
        self.assertEqual(active_category_rules[0].priority, 40)  # 가장 높은 우선순위
        self.assertEqual(active_category_rules[1].priority, 20)
        self.assertEqual(active_category_rules[2].priority, 0)   # 가장 낮은 우선순위
    
    def test_bulk_create_rules(self):
        """규칙 일괄 생성 테스트"""
        # 여러 규칙 생성
        rules = []
        for i in range(5):
            rule = ClassificationRule(
                rule_name=f"일괄 규칙 {i+1}",
                rule_type=ClassificationRule.TYPE_CATEGORY,
                condition_type=ClassificationRule.CONDITION_CONTAINS,
                condition_value=f"일괄 {i+1}",
                target_value=f"일괄 카테고리 {i+1}",
                priority=i*10,
                is_active=True
            )
            rules.append(rule)
        
        # 일괄 생성
        created = self.repository.bulk_create(rules)
        
        # 검증
        self.assertEqual(len(created), 5)
        for i, rule in enumerate(created):
            self.assertIsNotNone(rule.id)
            self.assertEqual(rule.rule_name, f"일괄 규칙 {i+1}")
            self.assertEqual(rule.condition_value, f"일괄 {i+1}")
        
        # 데이터베이스에서 조회하여 검증
        db_rules = self.repository.list()
        self.assertEqual(len(db_rules), 5)


if __name__ == "__main__":
    unittest.main()