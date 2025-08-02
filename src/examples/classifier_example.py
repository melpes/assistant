# -*- coding: utf-8 -*-
"""
분류기 사용 예제

카테고리 분류기와 결제 방식 분류기를 사용하는 방법을 보여줍니다.
"""

import logging
import sys
from datetime import date
from decimal import Decimal

from src.models import Transaction
from src.rule_engine import RuleEngine
from src.repositories.rule_repository import RuleRepository
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.db_connection import DatabaseConnection
from src.classifiers.category_classifier import CategoryClassifier
from src.classifiers.payment_method_classifier import PaymentMethodClassifier

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def main():
    """
    분류기 사용 예제 메인 함수
    """
    # 데이터베이스 연결
    db_connection = DatabaseConnection("personal_data.db")
    
    # 저장소 생성
    rule_repository = RuleRepository(db_connection)
    transaction_repository = TransactionRepository(db_connection)
    
    # 규칙 엔진 생성
    rule_engine = RuleEngine(rule_repository)
    
    # 분류기 생성
    category_classifier = CategoryClassifier(rule_engine, transaction_repository)
    payment_method_classifier = PaymentMethodClassifier(rule_engine, transaction_repository)
    
    # 테스트 거래 생성
    test_transactions = [
        Transaction(
            transaction_id="example1",
            transaction_date=date.today(),
            description="스타벅스 아메리카노",
            amount=Decimal("4500"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="toss_card"
        ),
        Transaction(
            transaction_id="example2",
            transaction_date=date.today(),
            description="버스 요금",
            amount=Decimal("1250"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="toss_card"
        ),
        Transaction(
            transaction_id="example3",
            transaction_date=date.today(),
            description="마트 장보기",
            amount=Decimal("35000"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="manual"
        ),
        Transaction(
            transaction_id="example4",
            transaction_date=date.today(),
            description="전기요금",
            amount=Decimal("45000"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="toss_account"
        )
    ]
    
    # 개별 분류 예제
    logger.info("=== 개별 분류 예제 ===")
    for transaction in test_transactions:
        # 카테고리 분류
        category = category_classifier.classify(transaction)
        transaction.update_category(category)
        
        # 결제 방식 분류
        payment_method = payment_method_classifier.classify(transaction)
        transaction.update_payment_method(payment_method)
        
        logger.info(f"거래: {transaction.description}")
        logger.info(f"  - 카테고리: {transaction.category}")
        logger.info(f"  - 결제 방식: {transaction.payment_method}")
    
    # 일괄 분류 예제
    logger.info("\n=== 일괄 분류 예제 ===")
    
    # 분류 초기화
    for transaction in test_transactions:
        transaction.category = None
        transaction.payment_method = None
    
    # 카테고리 일괄 분류
    category_results = category_classifier.classify_batch(test_transactions)
    logger.info(f"카테고리 분류 결과: {len(category_results)}개")
    
    # 결제 방식 일괄 분류
    payment_method_results = payment_method_classifier.classify_batch(test_transactions)
    logger.info(f"결제 방식 분류 결과: {len(payment_method_results)}개")
    
    # 결과 적용
    for transaction in test_transactions:
        if transaction.transaction_id in category_results:
            transaction.update_category(category_results[transaction.transaction_id])
        
        if transaction.transaction_id in payment_method_results:
            transaction.update_payment_method(payment_method_results[transaction.transaction_id])
    
    # 결과 출력
    for transaction in test_transactions:
        logger.info(f"거래: {transaction.description}")
        logger.info(f"  - 카테고리: {transaction.category}")
        logger.info(f"  - 결제 방식: {transaction.payment_method}")
    
    # 학습 예제
    logger.info("\n=== 학습 예제 ===")
    
    # 사용자 수정 시뮬레이션
    test_transactions[0].update_category("식비")
    test_transactions[0].update_payment_method("토스페이")
    
    # 학습
    category_classifier.learn_from_correction(test_transactions[0], "식비")
    payment_method_classifier.learn_from_correction(test_transactions[0], "토스페이")
    
    logger.info("사용자 수정사항으로부터 학습 완료")
    
    # 정확도 지표 출력
    logger.info("\n=== 정확도 지표 ===")
    
    category_metrics = category_classifier.get_accuracy_metrics()
    logger.info(f"카테고리 분류 정확도:")
    logger.info(f"  - 총 분류: {category_metrics['total_classified']}개")
    logger.info(f"  - 규칙 기반 분류: {category_metrics['rule_based_classifications']}개 ({category_metrics.get('rule_based_ratio', 0):.2%})")
    logger.info(f"  - 기본값 분류: {category_metrics['default_classifications']}개 ({category_metrics.get('default_ratio', 0):.2%})")
    logger.info(f"  - 사용자 수정: {category_metrics['user_corrections']}개")
    
    payment_metrics = payment_method_classifier.get_accuracy_metrics()
    logger.info(f"결제 방식 분류 정확도:")
    logger.info(f"  - 총 분류: {payment_metrics['total_classified']}개")
    logger.info(f"  - 규칙 기반 분류: {payment_metrics['rule_based_classifications']}개 ({payment_metrics.get('rule_based_ratio', 0):.2%})")
    logger.info(f"  - 기본값 분류: {payment_metrics['default_classifications']}개 ({payment_metrics.get('default_ratio', 0):.2%})")
    logger.info(f"  - 사용자 수정: {payment_metrics['user_corrections']}개")
    
    # 사용 가능한 카테고리 및 결제 방식 목록
    logger.info("\n=== 사용 가능한 분류값 ===")
    
    categories = category_classifier.get_available_categories()
    logger.info(f"카테고리 목록: {', '.join(categories)}")
    
    payment_methods = payment_method_classifier.get_available_payment_methods()
    logger.info(f"결제 방식 목록: {', '.join(payment_methods)}")


if __name__ == "__main__":
    main()