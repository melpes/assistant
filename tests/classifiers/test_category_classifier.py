# -*- coding: utf-8 -*-
"""
카테고리 분류기(CategoryClassifier) 테스트
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import date
from decimal import Decimal

from src.models import Transaction, ClassificationRule
from src.rule_engine import RuleEngine
from src.repositories.rule_repository import RuleRepository
from src.repositories.transaction_repository import TransactionRepository
from src.classifiers.category_classifier import CategoryClassifier


class TestCategoryClassifier(unittest.TestCase):
    """
    카테고리 분류기 테스트 클래스
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        # 모의 객체 생성
        self.rule_repository = MagicMock(spec=RuleRepository)
        self.transaction_repository = MagicMock(spec=TransactionRepository)
        self.rule_engine = MagicMock(spec=RuleEngine)
        self.rule_engine.rule_repository = self.rule_repository
        
        # 분류기 생성
        self.classifier = CategoryClassifier(
            rule_engine=self.rule_engine,
            transaction_repository=self.transaction_repository
        )
        
        # 테스트 거래 생성
        self.test_transaction = Transaction(
            transaction_id="test123",
            transaction_date=date.today(),
            description="스타벅스 아메리카노",
            amount=Decimal("4500"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="toss_card"
        )
    
    def test_classify_with_existing_category(self):
        """
        이미 카테고리가 있는 거래 분류 테스트
        """
        # 테스트 데이터 설정
        self.test_transaction.category = "식비"
        
        # 분류 실행
        result = self.classifier.classify(self.test_transaction)
        
        # 검증
        self.assertEqual(result, "식비")
        self.rule_engine.apply_rules.assert_not_called()
    
    def test_classify_with_rule_match(self):
        """
        규칙 일치 시 분류 테스트
        """
        # 모의 객체 설정
        self.rule_engine.apply_rules.return_value = "식비"
        
        # 분류 실행
        result = self.classifier.classify(self.test_transaction)
        
        # 검증
        self.assertEqual(result, "식비")
        self.rule_engine.apply_rules.assert_called_once_with(
            self.test_transaction, ClassificationRule.TYPE_CATEGORY
        )
    
    def test_classify_with_no_rule_match(self):
        """
        규칙 불일치 시 분류 테스트
        """
        # 모의 객체 설정
        self.rule_engine.apply_rules.return_value = None
        
        # 분류 실행
        result = self.classifier.classify(self.test_transaction)
        
        # 검증
        self.assertEqual(result, "기타")
        self.rule_engine.apply_rules.assert_called_once_with(
            self.test_transaction, ClassificationRule.TYPE_CATEGORY
        )
    
    def test_classify_batch(self):
        """
        일괄 분류 테스트
        """
        # 테스트 데이터 설정
        transaction1 = Transaction(
            transaction_id="test1",
            transaction_date=date.today(),
            description="스타벅스 아메리카노",
            amount=Decimal("4500"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="toss_card"
        )
        
        transaction2 = Transaction(
            transaction_id="test2",
            transaction_date=date.today(),
            description="버스 요금",
            amount=Decimal("1250"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="toss_card",
            category="교통비"  # 이미 카테고리가 있음
        )
        
        transaction3 = Transaction(
            transaction_id="test3",
            transaction_date=date.today(),
            description="마트 장보기",
            amount=Decimal("35000"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="toss_card"
        )
        
        # 모의 객체 설정
        self.rule_engine.apply_rules_batch.return_value = {
            "test1": "식비",
            # test3는 규칙 불일치
        }
        
        # 분류 실행
        result = self.classifier.classify_batch([transaction1, transaction2, transaction3])
        
        # 검증
        self.assertEqual(result, {
            "test1": "식비",
            "test3": "기타"
        })
        self.rule_engine.apply_rules_batch.assert_called_once()
    
    def test_learn_from_correction(self):
        """
        사용자 수정사항 학습 테스트
        """
        # 모의 객체 설정
        self.rule_engine.add_rule.return_value = MagicMock()
        
        # 학습 실행
        result = self.classifier.learn_from_correction(self.test_transaction, "식비")
        
        # 검증
        self.assertTrue(result)
        self.rule_engine.add_rule.assert_called_once()
    
    def test_get_accuracy_metrics(self):
        """
        정확도 지표 테스트
        """
        # 테스트 데이터 설정
        self.classifier._accuracy_metrics = {
            'total_classified': 100,
            'rule_based_classifications': 70,
            'default_classifications': 30,
            'user_corrections': 10,
            'correction_patterns': {"미분류 -> 식비": 5, "기타 -> 교통비": 3, "식비 -> 문화/오락": 2}
        }
        
        # 지표 조회
        metrics = self.classifier.get_accuracy_metrics()
        
        # 검증
        self.assertEqual(metrics['total_classified'], 100)
        self.assertEqual(metrics['rule_based_classifications'], 70)
        self.assertEqual(metrics['default_classifications'], 30)
        self.assertEqual(metrics['user_corrections'], 10)
        self.assertEqual(metrics['rule_based_ratio'], 0.7)
        self.assertEqual(metrics['default_ratio'], 0.3)
        self.assertEqual(metrics['correction_ratio'], 0.1)
        self.assertEqual(len(metrics['top_correction_patterns']), 3)
        self.assertEqual(metrics['top_correction_patterns'][0][0], "미분류 -> 식비")
        self.assertEqual(metrics['top_correction_patterns'][0][1], 5)
    
    def test_get_available_categories(self):
        """
        사용 가능한 카테고리 목록 테스트
        """
        # 모의 객체 설정
        rule1 = MagicMock(spec=ClassificationRule)
        rule1.target_value = "식비"
        
        rule2 = MagicMock(spec=ClassificationRule)
        rule2.target_value = "커스텀카테고리"
        
        self.rule_repository.list.return_value = [rule1, rule2]
        self.transaction_repository.get_categories.return_value = ["식비", "교통비", "문화/오락"]
        
        # 카테고리 목록 조회
        categories = self.classifier.get_available_categories()
        
        # 검증
        self.assertIn("식비", categories)
        self.assertIn("교통비", categories)
        self.assertIn("문화/오락", categories)
        self.assertIn("커스텀카테고리", categories)
        for default_category in self.classifier.DEFAULT_CATEGORIES:
            self.assertIn(default_category, categories)
    
    def test_reset_metrics(self):
        """
        지표 초기화 테스트
        """
        # 테스트 데이터 설정
        self.classifier._accuracy_metrics = {
            'total_classified': 100,
            'rule_based_classifications': 70,
            'default_classifications': 30,
            'user_corrections': 10,
            'correction_patterns': {"미분류 -> 식비": 5}
        }
        
        # 초기화 실행
        self.classifier.reset_metrics()
        
        # 검증
        metrics = self.classifier.get_accuracy_metrics()
        self.assertEqual(metrics['total_classified'], 0)
        self.assertEqual(metrics['rule_based_classifications'], 0)
        self.assertEqual(metrics['default_classifications'], 0)
        self.assertEqual(metrics['user_corrections'], 0)
        self.assertEqual(len(metrics['correction_patterns']), 0)


if __name__ == '__main__':
    unittest.main()