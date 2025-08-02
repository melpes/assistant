# -*- coding: utf-8 -*-
"""
학습 엔진 사용 예제

학습 엔진을 사용하여 사용자 수정사항으로부터 패턴을 추출하고 학습하는 예제입니다.
"""

import logging
import sys
from datetime import datetime, date
from decimal import Decimal

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# 모듈 경로 추가
sys.path.append('.')

from src.models import Transaction, ClassificationRule, LearningPattern
from src.repositories.db_connection import DatabaseConnection
from src.repositories.rule_repository import RuleRepository
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.learning_pattern_repository import LearningPatternRepository
from src.learning_engine import LearningEngine


def main():
    """
    학습 엔진 예제 실행
    """
    print("학습 엔진 예제 시작")
    
    # 데이터베이스 연결
    db_connection = DatabaseConnection('personal_data.db')
    
    # 저장소 초기화
    rule_repository = RuleRepository(db_connection)
    transaction_repository = TransactionRepository(db_connection)
    pattern_repository = LearningPatternRepository(db_connection)
    
    # 학습 엔진 초기화
    learning_engine = LearningEngine(
        pattern_repository=pattern_repository,
        rule_repository=rule_repository,
        transaction_repository=transaction_repository
    )
    
    # 예제 1: 단일 수정사항 학습
    print("\n예제 1: 단일 수정사항 학습")
    
    # 예제 거래 생성
    transaction = Transaction(
        id=1,
        transaction_id="example-tx-001",
        transaction_date=date.today(),
        description="스타벅스 강남점 아메리카노",
        amount=Decimal("4500"),
        transaction_type=Transaction.TYPE_EXPENSE,
        category="미분류",  # 원래 분류
        payment_method="체크카드결제",
        source="예제"
    )
    
    # 수정사항 학습
    success = learning_engine.learn_from_correction(
        transaction=transaction,
        field_name="category",
        previous_value="미분류",
        corrected_value="식비"
    )
    
    print(f"학습 성공 여부: {success}")
    
    # 예제 2: 여러 수정사항 일괄 학습
    print("\n예제 2: 여러 수정사항 일괄 학습")
    
    # 예제 거래 목록
    transactions = [
        Transaction(
            id=2,
            transaction_id="example-tx-002",
            transaction_date=date.today(),
            description="이마트 강남점 생필품",
            amount=Decimal("25000"),
            transaction_type=Transaction.TYPE_EXPENSE,
            category="미분류",
            payment_method="체크카드결제",
            source="예제"
        ),
        Transaction(
            id=3,
            transaction_id="example-tx-003",
            transaction_date=date.today(),
            description="CGV 영화티켓",
            amount=Decimal("12000"),
            transaction_type=Transaction.TYPE_EXPENSE,
            category="미분류",
            payment_method="체크카드결제",
            source="예제"
        )
    ]
    
    # 수정사항 목록
    corrections = [
        {
            'transaction': transactions[0],
            'field_name': 'category',
            'previous_value': '미분류',
            'corrected_value': '생활용품'
        },
        {
            'transaction': transactions[1],
            'field_name': 'category',
            'previous_value': '미분류',
            'corrected_value': '문화/오락'
        }
    ]
    
    # 일괄 학습
    results = learning_engine.learn_from_corrections_batch(corrections)
    print(f"일괄 학습 결과: {results}")
    
    # 예제 3: 학습된 패턴을 규칙으로 적용
    print("\n예제 3: 학습된 패턴을 규칙으로 적용")
    
    # 패턴 적용
    rules_created = learning_engine.apply_patterns_to_rules('category')
    print(f"생성된 규칙 수: {rules_created}")
    
    # 예제 4: 반복 거래 패턴 감지
    print("\n예제 4: 반복 거래 패턴 감지")
    
    # 반복 패턴 감지
    recurring_patterns = learning_engine.detect_recurring_patterns(days=90)
    print(f"감지된 반복 패턴 수: {len(recurring_patterns)}")
    
    for i, pattern in enumerate(recurring_patterns[:3], 1):
        print(f"패턴 {i}: {pattern['merchant']} - {pattern['interval_days']}일 간격, "
              f"금액: {pattern['common_amount']}")
    
    # 예제 5: 동적 필터 생성
    print("\n예제 5: 동적 필터 생성")
    
    # 필터 생성
    filters = learning_engine.generate_dynamic_filters()
    print(f"생성된 필터 수: {len(filters)}")
    
    for i, filter_config in enumerate(filters[:3], 1):
        print(f"필터 {i}: {filter_config['name']} - {filter_config['description']}")
    
    # 예제 6: 패턴 변화 감지
    print("\n예제 6: 패턴 변화 감지")
    
    # 패턴 변화 감지
    pattern_changes = learning_engine.detect_pattern_changes()
    print(f"감지된 패턴 변화 수: {len(pattern_changes)}")
    
    for i, change in enumerate(pattern_changes[:3], 1):
        print(f"변화 {i}: {change['description']} (변화 점수: {change['change_score']:.2f})")
    
    # 학습 통계 출력
    print("\n학습 통계:")
    stats = learning_engine.get_learning_stats()
    print(f"처리된 수정사항: {stats['corrections_processed']}")
    print(f"추출된 패턴: {stats['patterns_extracted']}")
    print(f"적용된 패턴: {stats['patterns_applied']}")
    print(f"생성된 규칙: {stats['rules_generated']}")
    
    # 패턴 변화 통계
    if 'pattern_changes' in stats:
        print(f"\n패턴 변화 통계:")
        print(f"총 변화 수: {stats['pattern_changes']['total']}")
        print(f"중요 변화 수: {stats['pattern_changes']['significant_changes']}")
        
        if stats['pattern_changes']['top_changes']:
            print("\n주요 패턴 변화:")
            for i, change in enumerate(stats['pattern_changes']['top_changes'], 1):
                print(f"{i}. {change['description']}")
    
    print("\n학습 엔진 예제 완료")


if __name__ == "__main__":
    main()