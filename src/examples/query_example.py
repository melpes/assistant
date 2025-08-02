# -*- coding: utf-8 -*-
"""
거래 및 분류 규칙 조회 예제

이 스크립트는 Repository 패턴을 사용하여 거래 및 분류 규칙을 조회하는 방법을 보여줍니다.
"""

import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models import Transaction, ClassificationRule
from src.repositories.db_connection import DatabaseConnection
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.rule_repository import RuleRepository


def print_separator(title: str = None):
    """구분선 출력"""
    width = 60
    if title:
        print("\n" + "=" * width)
        print(f"{title:^{width}}")
        print("=" * width)
    else:
        print("\n" + "-" * width)


def print_transaction(transaction: Transaction):
    """거래 정보 출력"""
    print(f"ID: {transaction.id}")
    print(f"거래 ID: {transaction.transaction_id}")
    print(f"날짜: {transaction.transaction_date}")
    print(f"설명: {transaction.description}")
    print(f"금액: {transaction.amount:,.0f}원")
    print(f"유형: {transaction.transaction_type}")
    print(f"카테고리: {transaction.category or '미분류'}")
    print(f"결제 방식: {transaction.payment_method or '미지정'}")
    print(f"소스: {transaction.source}")
    if transaction.memo:
        print(f"메모: {transaction.memo}")


def print_rule(rule: ClassificationRule):
    """분류 규칙 정보 출력"""
    print(f"ID: {rule.id}")
    print(f"이름: {rule.rule_name}")
    print(f"유형: {rule.rule_type}")
    print(f"조건: {rule.condition_type}({rule.condition_value})")
    print(f"결과값: {rule.target_value}")
    print(f"우선순위: {rule.priority}")
    print(f"활성화: {'예' if rule.is_active else '아니오'}")
    print(f"생성자: {rule.created_by}")
    print(f"생성일: {rule.created_at.strftime('%Y-%m-%d %H:%M:%S')}")


def query_transactions(db_path: str):
    """거래 조회 예제"""
    # 데이터베이스 연결 및 Repository 생성
    db_connection = DatabaseConnection(db_path)
    transaction_repo = TransactionRepository(db_connection)
    
    try:
        # 1. 모든 거래 조회
        print_separator("모든 거래 목록")
        transactions = transaction_repo.list()
        print(f"총 {len(transactions)}개의 거래가 있습니다.")
        
        if transactions:
            # 첫 번째 거래 상세 정보 출력
            print_separator("첫 번째 거래 상세 정보")
            print_transaction(transactions[0])
        
        # 2. 지출 거래만 조회
        print_separator("지출 거래 목록")
        expense_transactions = transaction_repo.list({"transaction_type": Transaction.TYPE_EXPENSE})
        print(f"총 {len(expense_transactions)}개의 지출 거래가 있습니다.")
        
        # 3. 수입 거래만 조회
        print_separator("수입 거래 목록")
        income_transactions = transaction_repo.list({"transaction_type": Transaction.TYPE_INCOME})
        print(f"총 {len(income_transactions)}개의 수입 거래가 있습니다.")
        
        # 4. 특정 카테고리 거래 조회
        print_separator("카테고리별 거래 목록")
        categories = transaction_repo.get_categories()
        print(f"사용 중인 카테고리: {', '.join(categories)}")
        
        for category in categories:
            category_transactions = transaction_repo.list({"category": category})
            print(f"- {category}: {len(category_transactions)}개 거래")
        
        # 5. 특정 기간 거래 조회
        print_separator("기간별 거래 목록")
        today = date.today()
        start_date = today - timedelta(days=30)  # 최근 30일
        
        recent_transactions = transaction_repo.list({
            "start_date": start_date,
            "end_date": today
        })
        print(f"{start_date} ~ {today} 기간 동안 {len(recent_transactions)}개의 거래가 있습니다.")
        
        # 6. 금액 범위로 거래 조회
        print_separator("금액별 거래 목록")
        high_amount_transactions = transaction_repo.list({
            "min_amount": "50000"
        })
        print(f"50,000원 이상 거래: {len(high_amount_transactions)}개")
        
        medium_amount_transactions = transaction_repo.list({
            "min_amount": "10000",
            "max_amount": "50000"
        })
        print(f"10,000원 ~ 50,000원 거래: {len(medium_amount_transactions)}개")
        
        low_amount_transactions = transaction_repo.list({
            "max_amount": "10000"
        })
        print(f"10,000원 이하 거래: {len(low_amount_transactions)}개")
        
        # 7. 결제 방식별 거래 조회
        print_separator("결제 방식별 거래 목록")
        payment_methods = transaction_repo.get_payment_methods()
        print(f"사용 중인 결제 방식: {', '.join(payment_methods)}")
        
        for payment_method in payment_methods:
            payment_transactions = transaction_repo.list({"payment_method": payment_method})
            print(f"- {payment_method}: {len(payment_transactions)}개 거래")
        
        # 8. 거래 날짜 범위 조회
        print_separator("거래 날짜 범위")
        min_date, max_date = transaction_repo.get_date_range()
        if min_date and max_date:
            print(f"가장 오래된 거래 날짜: {min_date}")
            print(f"가장 최근 거래 날짜: {max_date}")
            print(f"데이터 기간: {(max_date - min_date).days + 1}일")
        else:
            print("거래 데이터가 없습니다.")
    
    finally:
        # 데이터베이스 연결 종료
        db_connection.close()


def query_rules(db_path: str):
    """분류 규칙 조회 예제"""
    # 데이터베이스 연결 및 Repository 생성
    db_connection = DatabaseConnection(db_path)
    rule_repo = RuleRepository(db_connection)
    
    try:
        # 1. 모든 분류 규칙 조회
        print_separator("모든 분류 규칙 목록")
        rules = rule_repo.list()
        print(f"총 {len(rules)}개의 분류 규칙이 있습니다.")
        
        if rules:
            # 첫 번째 규칙 상세 정보 출력
            print_separator("첫 번째 규칙 상세 정보")
            print_rule(rules[0])
        
        # 2. 활성화된 규칙만 조회
        print_separator("활성화된 규칙 목록")
        active_rules = rule_repo.list({"is_active": True})
        print(f"총 {len(active_rules)}개의 활성화된 규칙이 있습니다.")
        
        # 3. 비활성화된 규칙만 조회
        print_separator("비활성화된 규칙 목록")
        inactive_rules = rule_repo.list({"is_active": False})
        print(f"총 {len(inactive_rules)}개의 비활성화된 규칙이 있습니다.")
        
        # 4. 규칙 유형별 조회
        print_separator("규칙 유형별 목록")
        
        # 카테고리 규칙
        category_rules = rule_repo.list({"rule_type": ClassificationRule.TYPE_CATEGORY})
        print(f"카테고리 규칙: {len(category_rules)}개")
        
        # 결제 방식 규칙
        payment_rules = rule_repo.list({"rule_type": ClassificationRule.TYPE_PAYMENT_METHOD})
        print(f"결제 방식 규칙: {len(payment_rules)}개")
        
        # 필터 규칙
        filter_rules = rule_repo.list({"rule_type": ClassificationRule.TYPE_FILTER})
        print(f"필터 규칙: {len(filter_rules)}개")
        
        # 5. 우선순위별 규칙 조회
        print_separator("우선순위별 규칙 목록")
        
        # 높은 우선순위 규칙
        high_priority_rules = rule_repo.list({
            "min_priority": 50,
            "order_by": "priority",
            "order_direction": "desc"
        })
        print(f"높은 우선순위(50 이상) 규칙: {len(high_priority_rules)}개")
        
        # 중간 우선순위 규칙
        medium_priority_rules = rule_repo.list({
            "min_priority": 10,
            "max_priority": 50,
            "order_by": "priority",
            "order_direction": "desc"
        })
        print(f"중간 우선순위(10-50) 규칙: {len(medium_priority_rules)}개")
        
        # 낮은 우선순위 규칙
        low_priority_rules = rule_repo.list({
            "max_priority": 10,
            "order_by": "priority",
            "order_direction": "desc"
        })
        print(f"낮은 우선순위(10 이하) 규칙: {len(low_priority_rules)}개")
        
        # 6. 생성자별 규칙 조회
        print_separator("생성자별 규칙 목록")
        
        # 사용자 생성 규칙
        user_rules = rule_repo.list({"created_by": ClassificationRule.CREATOR_USER})
        print(f"사용자 생성 규칙: {len(user_rules)}개")
        
        # 시스템 생성 규칙
        system_rules = rule_repo.list({"created_by": ClassificationRule.CREATOR_SYSTEM})
        print(f"시스템 생성 규칙: {len(system_rules)}개")
        
        # 학습된 규칙
        learned_rules = rule_repo.list({"created_by": ClassificationRule.CREATOR_LEARNED})
        print(f"학습된 규칙: {len(learned_rules)}개")
        
        # 7. 활성화된 카테고리 규칙 조회
        print_separator("활성화된 카테고리 규칙")
        active_category_rules = rule_repo.get_active_rules_by_type(ClassificationRule.TYPE_CATEGORY)
        print(f"총 {len(active_category_rules)}개의 활성화된 카테고리 규칙이 있습니다.")
        
        for i, rule in enumerate(active_category_rules):
            print(f"\n{i+1}. {rule.rule_name} (우선순위: {rule.priority})")
            print(f"   조건: {rule.condition_type}({rule.condition_value})")
            print(f"   결과값: {rule.target_value}")
    
    finally:
        # 데이터베이스 연결 종료
        db_connection.close()


def main():
    """메인 함수"""
    # 데이터베이스 파일 경로
    db_path = "personal_data.db"
    
    # 데이터베이스 파일 존재 여부 확인
    if not os.path.exists(db_path):
        print(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
        print("먼저 repository_example.py를 실행하여 샘플 데이터를 생성해주세요.")
        return
    
    # 거래 조회
    query_transactions(db_path)
    
    # 분류 규칙 조회
    query_rules(db_path)


if __name__ == "__main__":
    main()