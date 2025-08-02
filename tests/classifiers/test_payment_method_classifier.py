# -*- coding: utf-8 -*-
"""
결제 방식 분류기(PaymentMethodClassifier) 테스트
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import date
from decimal import Decimal

from src.models import Transaction, ClassificationRule
from src.rule_engine import RuleEngine
from src.repositories.rule_repository import RuleRepository
from src.repositories.transaction_repository import TransactionRepository
from src.classifiers.payment_method_classifier import PaymentMethodClassifier


class TestPaymentMethodClassifier(unittest.TestCase):
    """
    결제 방식 분류기 테스트 클래스
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
        self.classifier = PaymentMethodClassifier(
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
    
    def test_classify_with_existing_payment_method(self):
        """
        이미 결제 방식이 있는 거래 분류 테스트
        """
        # 테스트 데이터 설정
        self.test_transaction.payment_method = "체크카드결제"
        
        # 분류 실행
        result = self.classifier.classify(self.test_transaction)
        
        # 검증
        self.assertEqual(result, "체크카드결제")
        self.rule_engine.apply_rules.assert_not_called()
    
    def test_classify_with_rule_match(self):
        """
        규칙 일치 시 분류 테스트
        """
        # 모의 객체 설정
        self.rule_engine.apply_rules.return_value = "체크카드결제"
        
        # 분류 실행
        result = self.classifier.classify(self.test_transaction)
        
        # 검증
        self.assertEqual(result, "체크카드결제")
        self.rule_engine.apply_rules.assert_called_once_with(
            self.test_transaction, ClassificationRule.TYPE_PAYMENT_METHOD
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
        self.assertEqual(result, "체크카드결제")  # toss_card 소스의 기본값
        self.rule_engine.apply_rules.assert_called_once_with(
            self.test_transaction, ClassificationRule.TYPE_PAYMENT_METHOD
        )
    
    def test_classify_with_different_sources(self):
        """
        다양한 소스의 거래 분류 테스트
        """
        # 모의 객체 설정
        self.rule_engine.apply_rules.return_value = None
        
        # 테스트 데이터 설정
        toss_account_transaction = Transaction(
            transaction_id="test456",
            transaction_date=date.today(),
            description="계좌이체",
            amount=Decimal("50000"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="toss_account"
        )
        
        manual_transaction = Transaction(
            transaction_id="test789",
            transaction_date=date.today(),
            description="현금 지출",
            amount=Decimal("10000"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="manual"
        )
        
        unknown_source_transaction = Transaction(
            transaction_id="test000",
            transaction_date=date.today(),
            description="알 수 없는 소스",
            amount=Decimal("20000"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="unknown"
        )
        
        # 분류 실행 및 검증
        self.assertEqual(self.classifier.classify(toss_account_transaction), "계좌이체")
        self.assertEqual(self.classifier.classify(manual_transaction), "현금")
        self.assertEqual(self.classifier.classify(unknown_source_transaction), "기타카드")
    
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
            payment_method="체크카드결제"  # 이미 결제 방식이 있음
        )
        
        transaction3 = Transaction(
            transaction_id="test3",
            transaction_date=date.today(),
            description="마트 장보기",
            amount=Decimal("35000"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="manual"
        )
        
        # 모의 객체 설정
        self.rule_engine.apply_rules_batch.return_value = {
            "test1": "체크카드결제",
            # test3는 규칙 불일치
        }
        
        # 분류 실행
        result = self.classifier.classify_batch([transaction1, transaction2, transaction3])
        
        # 검증
        self.assertEqual(result, {
            "test1": "체크카드결제",
            "test3": "현금"  # manual 소스의 기본값
        })
        self.rule_engine.apply_rules_batch.assert_called_once()
    
    def test_learn_from_correction(self):
        """
        사용자 수정사항 학습 테스트
        """
        # 모의 객체 설정
        self.rule_engine.add_rule.return_value = MagicMock()
        
        # 학습 실행
        result = self.classifier.learn_from_correction(self.test_transaction, "토스페이")
        
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
            'rule_based_classifications': 60,
            'default_classifications': 40,
            'user_corrections': 15,
            'correction_patterns': {"체크카드결제 -> 토스페이": 8, "현금 -> 계좌이체": 4, "기타카드 -> ATM출금": 3}
        }
        
        # 지표 조회
        metrics = self.classifier.get_accuracy_metrics()
        
        # 검증
        self.assertEqual(metrics['total_classified'], 100)
        self.assertEqual(metrics['rule_based_classifications'], 60)
        self.assertEqual(metrics['default_classifications'], 40)
        self.assertEqual(metrics['user_corrections'], 15)
        self.assertEqual(metrics['rule_based_ratio'], 0.6)
        self.assertEqual(metrics['default_ratio'], 0.4)
        self.assertEqual(metrics['correction_ratio'], 0.15)
        self.assertEqual(len(metrics['top_correction_patterns']), 3)
        self.assertEqual(metrics['top_correction_patterns'][0][0], "체크카드결제 -> 토스페이")
        self.assertEqual(metrics['top_correction_patterns'][0][1], 8)
    
    def test_get_available_payment_methods(self):
        """
        사용 가능한 결제 방식 목록 테스트
        """
        # 모의 객체 설정
        rule1 = MagicMock(spec=ClassificationRule)
        rule1.target_value = "체크카드결제"
        
        rule2 = MagicMock(spec=ClassificationRule)
        rule2.target_value = "커스텀결제방식"
        
        self.rule_repository.list.return_value = [rule1, rule2]
        self.transaction_repository.get_payment_methods.return_value = ["체크카드결제", "토스페이", "계좌이체"]
        
        # 결제 방식 목록 조회
        payment_methods = self.classifier.get_available_payment_methods()
        
        # 검증
        self.assertIn("체크카드결제", payment_methods)
        self.assertIn("토스페이", payment_methods)
        self.assertIn("계좌이체", payment_methods)
        self.assertIn("커스텀결제방식", payment_methods)
        for default_method in self.classifier.DEFAULT_PAYMENT_METHODS:
            self.assertIn(default_method, payment_methods)
    
    def test_reset_metrics(self):
        """
        지표 초기화 테스트
        """
        # 테스트 데이터 설정
        self.classifier._accuracy_metrics = {
            'total_classified': 100,
            'rule_based_classifications': 60,
            'default_classifications': 40,
            'user_corrections': 15,
            'correction_patterns': {"체크카드결제 -> 토스페이": 8}
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