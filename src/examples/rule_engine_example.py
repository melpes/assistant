# -*- coding: utf-8 -*-
"""
규칙 엔진(RuleEngine) 사용 예제
"""

import logging
from datetime import date
from decimal import Decimal

import sys
import os

# 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models import ClassificationRule, Transaction
from src.rule_engine import RuleEngine
from src.repositories.rule_repository import RuleRepository
from src.repositories.db_connection import DatabaseConnection

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """규칙 엔진 사용 예제 메인 함수"""
    # 데이터베이스 연결 생성
    db_connection = DatabaseConnection("personal_data.db")
    
    # 규칙 저장소 생성
    rule_repository = RuleRepository(db_connection)
    
    # 규칙 엔진 생성
    rule_engine = RuleEngine(rule_repository)
    
    # 기본 규칙 생성
    create_default_rules(rule_engine)
    
    # 테스트 거래 생성
    transactions = create_test_transactions()
    
    # 규칙 적용 테스트
    test_rule_application(rule_engine, transactions)
    
    # 규칙 충돌 해결 테스트
    test_conflict_resolution(rule_engine)
    
    # 규칙 통계 테스트
    test_rule_stats(rule_engine)


def create_default_rules(rule_engine):
    """기본 분류 규칙 생성"""
    logger.info("기본 분류 규칙 생성 중...")
    
    # 카테고리 규칙
    category_rules = [
        ClassificationRule(
            rule_name="식당 규칙",
            rule_type="category",
            condition_type="contains",
            condition_value="식당",
            target_value="식비",
            priority=100
        ),
        ClassificationRule(
            rule_name="카페 규칙",
            rule_type="category",
            condition_type="contains",
            condition_value="카페",
            target_value="식비",
            priority=90
        ),
        ClassificationRule(
            rule_name="교통 규칙",
            rule_type="category",
            condition_type="regex",
            condition_value="택시|버스|지하철",
            target_value="교통비",
            priority=80
        ),
        ClassificationRule(
            rule_name="마트 규칙",
            rule_type="category",
            condition_type="contains",
            condition_value="마트",
            target_value="생활용품",
            priority=70
        ),
        ClassificationRule(
            rule_name="의류 규칙",
            rule_type="category",
            condition_type="regex",
            condition_value="의류|패션|옷|신발",
            target_value="의류/패션",
            priority=60
        ),
        ClassificationRule(
            rule_name="고액 지출 규칙",
            rule_type="category",
            condition_type="amount_range",
            condition_value="100000:1000000",
            target_value="고액지출",
            priority=50
        )
    ]
    
    # 결제 방식 규칙
    payment_rules = [
        ClassificationRule(
            rule_name="토스 결제 규칙",
            rule_type="payment_method",
            condition_type="contains",
            condition_value="토스페이",
            target_value="토스페이",
            priority=100
        ),
        ClassificationRule(
            rule_name="체크카드 규칙",
            rule_type="payment_method",
            condition_type="contains",
            condition_value="체크카드",
            target_value="체크카드결제",
            priority=90
        ),
        ClassificationRule(
            rule_name="소액 현금 규칙",
            rule_type="payment_method",
            condition_type="amount_range",
            condition_value="0:10000",
            target_value="현금",
            priority=80
        )
    ]
    
    # 규칙 추가
    for rule in category_rules:
        rule_engine.add_rule(rule)
    
    for rule in payment_rules:
        rule_engine.add_rule(rule)
    
    logger.info(f"기본 규칙 생성 완료: 카테고리 규칙 {len(category_rules)}개, 결제 방식 규칙 {len(payment_rules)}개")


def create_test_transactions():
    """테스트용 거래 생성"""
    return [
        Transaction(
            transaction_id="tx001",
            transaction_date=date(2023, 1, 1),
            description="서울식당 점심",
            amount=Decimal("15000"),
            transaction_type="expense",
            source="toss_card"
        ),
        Transaction(
            transaction_id="tx002",
            transaction_date=date(2023, 1, 2),
            description="스타벅스 카페",
            amount=Decimal("5500"),
            transaction_type="expense",
            source="toss_card"
        ),
        Transaction(
            transaction_id="tx003",
            transaction_date=date(2023, 1, 3),
            description="시내버스 요금",
            amount=Decimal("1200"),
            transaction_type="expense",
            source="toss_card"
        ),
        Transaction(
            transaction_id="tx004",
            transaction_date=date(2023, 1, 4),
            description="홈플러스 마트",
            amount=Decimal("45000"),
            transaction_type="expense",
            source="toss_card"
        ),
        Transaction(
            transaction_id="tx005",
            transaction_date=date(2023, 1, 5),
            description="유니클로 의류 구매",
            amount=Decimal("89000"),
            transaction_type="expense",
            source="toss_card"
        ),
        Transaction(
            transaction_id="tx006",
            transaction_date=date(2023, 1, 6),
            description="가전제품 구매",
            amount=Decimal("250000"),
            transaction_type="expense",
            source="toss_card"
        )
    ]


def test_rule_application(rule_engine, transactions):
    """규칙 적용 테스트"""
    logger.info("규칙 적용 테스트 중...")
    
    # 개별 거래에 규칙 적용
    for transaction in transactions:
        category = rule_engine.apply_rules(transaction, "category")
        payment_method = rule_engine.apply_rules(transaction, "payment_method")
        
        logger.info(f"거래: {transaction.description}, 금액: {transaction.amount}")
        logger.info(f"  - 분류 결과: 카테고리={category or '미분류'}, 결제방식={payment_method or '미분류'}")
    
    # 일괄 규칙 적용
    category_results = rule_engine.apply_rules_batch(transactions, "category")
    payment_results = rule_engine.apply_rules_batch(transactions, "payment_method")
    
    logger.info(f"일괄 분류 결과: 카테고리={len(category_results)}개, 결제방식={len(payment_results)}개")


def test_conflict_resolution(rule_engine):
    """규칙 충돌 해결 테스트"""
    logger.info("규칙 충돌 해결 테스트 중...")
    
    # 충돌하는 규칙 추가
    rule_engine.add_rule(ClassificationRule(
        rule_name="커피 규칙 1",
        rule_type="category",
        condition_type="contains",
        condition_value="커피",
        target_value="식비",
        priority=100
    ))
    
    rule_engine.add_rule(ClassificationRule(
        rule_name="커피 규칙 2",
        rule_type="category",
        condition_type="contains",
        condition_value="커피",
        target_value="카페",
        priority=50
    ))
    
    # 충돌 감지 및 해결
    conflicts = rule_engine.resolve_conflicts("category")
    
    logger.info(f"감지된 충돌: {len(conflicts)}개")
    for high_rule, low_rule in conflicts:
        logger.info(f"  - 충돌: '{high_rule.rule_name}' (우선순위={high_rule.priority}) vs "
                  f"'{low_rule.rule_name}' (우선순위={low_rule.priority})")
        logger.info(f"    조건: {high_rule.condition_type}('{high_rule.condition_value}')")
        logger.info(f"    결과값: '{high_rule.target_value}' vs '{low_rule.target_value}'")


def test_rule_stats(rule_engine):
    """규칙 통계 테스트"""
    logger.info("규칙 통계 테스트 중...")
    
    # 카테고리 규칙 통계
    category_stats = rule_engine.get_rule_stats("category")
    
    logger.info("카테고리 규칙 통계:")
    logger.info(f"  - 총 규칙 수: {category_stats['total_rules']}개")
    logger.info(f"  - 조건 유형별: {category_stats['condition_counts']}")
    logger.info(f"  - 결과값 분포: {category_stats['target_counts']}")
    logger.info(f"  - 우선순위 범위: {category_stats['priority_range']}")
    
    # 결제 방식 규칙 통계
    payment_stats = rule_engine.get_rule_stats("payment_method")
    
    logger.info("결제 방식 규칙 통계:")
    logger.info(f"  - 총 규칙 수: {payment_stats['total_rules']}개")
    logger.info(f"  - 조건 유형별: {payment_stats['condition_counts']}")
    logger.info(f"  - 결과값 분포: {payment_stats['target_counts']}")
    logger.info(f"  - 우선순위 범위: {payment_stats['priority_range']}")


if __name__ == "__main__":
    main()