# -*- coding: utf-8 -*-
"""
필터 엔진(FilterEngine) 사용 예제

필터 엔진을 사용하여 거래 데이터를 필터링하는 방법을 보여줍니다.
"""

import sys
import os
from datetime import datetime, date, timedelta
import random

# 상위 디렉토리를 모듈 검색 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.filter_engine import FilterEngine
from src.models.analysis_filter import AnalysisFilter
from src.models.transaction import Transaction
from src.repositories.filter_repository import FilterRepository


def create_sample_transactions(count=20):
    """
    샘플 거래 데이터 생성
    
    Args:
        count: 생성할 거래 수 (기본값: 20)
        
    Returns:
        List[Transaction]: 샘플 거래 목록
    """
    categories = ['식비', '생활용품', '교통비', '문화/오락', '의료비', '통신비', '공과금', '의류/패션', '기타']
    payment_methods = ['체크카드결제', 'ATM출금', '토스페이', '계좌이체', '현금']
    sources = ['토스뱅크카드', '토스뱅크계좌', '수동입력']
    descriptions = [
        '식당 결제', '마트 결제', '카페', '편의점', '대중교통', '택시', '영화관', '병원', '약국',
        '통신요금', '전기요금', '수도요금', '가스요금', '의류 구매', '신발 구매', '도서 구매',
        '온라인 쇼핑', '배달음식', '주유소', '문화센터'
    ]
    
    transactions = []
    today = date.today()
    
    for i in range(count):
        # 거래 유형 결정 (80% 지출, 20% 수입)
        transaction_type = 'expense' if random.random() < 0.8 else 'income'
        
        # 거래 날짜 (최근 30일 내)
        days_ago = random.randint(0, 30)
        transaction_date = today - timedelta(days=days_ago)
        
        # 거래 금액
        if transaction_type == 'expense':
            amount = random.randint(1000, 100000)
            category = random.choice(categories)
            payment_method = random.choice(payment_methods)
            description = random.choice(descriptions)
        else:
            amount = random.randint(100000, 3000000)
            category = random.choice(['급여', '용돈', '이자', '환급', '기타수입'])
            payment_method = '계좌이체'
            description = f"{category} 입금"
        
        # 거래 객체 생성
        transaction = Transaction(
            transaction_id=f"tx{i+1}",
            transaction_date=transaction_date,
            description=description,
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            payment_method=payment_method,
            source=random.choice(sources)
        )
        
        transactions.append(transaction)
    
    return transactions


def print_transactions(transactions, title=None):
    """
    거래 목록 출력
    
    Args:
        transactions: 출력할 거래 목록
        title: 출력 제목 (선택)
    """
    if title:
        print(f"\n=== {title} ===")
    
    if not transactions:
        print("거래 내역이 없습니다.")
        return
    
    # 헤더 출력
    print(f"{'ID':<5} {'날짜':<12} {'유형':<8} {'금액':<10} {'카테고리':<12} {'결제방식':<15} {'설명':<20}")
    print("-" * 80)
    
    # 거래 내역 출력
    for tx in transactions:
        print(f"{tx.transaction_id:<5} "
              f"{tx.transaction_date.strftime('%Y-%m-%d'):<12} "
              f"{'지출' if tx.transaction_type == 'expense' else '수입':<8} "
              f"{tx.amount:>9,d} "
              f"{tx.category:<12} "
              f"{tx.payment_method:<15} "
              f"{tx.description[:20]:<20}")


def main():
    """필터 엔진 사용 예제 메인 함수"""
    print("=== 필터 엔진 사용 예제 ===")
    
    # 데이터베이스 연결 및 필터 저장소 생성
    from src.repositories.db_connection import DatabaseConnection
    db_connection = DatabaseConnection("filter_engine_example.db")
    filter_repository = FilterRepository(db_connection)
    
    # 필터 엔진 생성
    filter_engine = FilterEngine(filter_repository)
    
    # 샘플 거래 데이터 생성
    transactions = create_sample_transactions(30)
    
    # 전체 거래 목록 출력
    print_transactions(transactions, "전체 거래 목록")
    
    # 예제 1: 카테고리 필터
    print("\n\n예제 1: 카테고리 필터 적용")
    category_filter = AnalysisFilter(
        filter_name="식비 필터",
        filter_config={
            'conditions': {
                'field': 'category',
                'comparison': 'equals',
                'value': '식비'
            }
        }
    )
    
    filtered_transactions = filter_engine.apply_filter(transactions, category_filter)
    print_transactions(filtered_transactions, "식비 카테고리 거래")
    
    # 예제 2: 금액 범위 필터
    print("\n\n예제 2: 금액 범위 필터 적용")
    amount_filter = AnalysisFilter(
        filter_name="고액 지출",
        filter_config={
            'conditions': {
                'field': 'amount',
                'comparison': 'between',
                'min_value': 50000,
                'max_value': 100000
            }
        }
    )
    
    filtered_transactions = filter_engine.apply_filter(transactions, amount_filter)
    print_transactions(filtered_transactions, "5만원 ~ 10만원 거래")
    
    # 예제 3: 복합 필터 (AND 조건)
    print("\n\n예제 3: 복합 필터 적용 (AND 조건)")
    complex_filter = AnalysisFilter(
        filter_name="카드 고액 지출",
        filter_config={
            'conditions': {
                'operator': 'and',
                'conditions': [
                    {
                        'field': 'payment_method',
                        'comparison': 'equals',
                        'value': '체크카드결제'
                    },
                    {
                        'field': 'amount',
                        'comparison': 'greater_than',
                        'value': 30000
                    },
                    {
                        'field': 'transaction_type',
                        'comparison': 'equals',
                        'value': 'expense'
                    }
                ]
            }
        }
    )
    
    filtered_transactions = filter_engine.apply_filter(transactions, complex_filter)
    print_transactions(filtered_transactions, "3만원 이상 체크카드 지출")
    
    # 예제 4: 복합 필터 (OR 조건)
    print("\n\n예제 4: 복합 필터 적용 (OR 조건)")
    or_filter = AnalysisFilter(
        filter_name="식비 또는 문화/오락",
        filter_config={
            'conditions': {
                'operator': 'or',
                'conditions': [
                    {
                        'field': 'category',
                        'comparison': 'equals',
                        'value': '식비'
                    },
                    {
                        'field': 'category',
                        'comparison': 'equals',
                        'value': '문화/오락'
                    }
                ]
            }
        }
    )
    
    filtered_transactions = filter_engine.apply_filter(transactions, or_filter)
    print_transactions(filtered_transactions, "식비 또는 문화/오락 카테고리")
    
    # 예제 5: 설명 포함 필터
    print("\n\n예제 5: 설명 포함 필터 적용")
    contains_filter = AnalysisFilter(
        filter_name="카페 포함",
        filter_config={
            'conditions': {
                'field': 'description',
                'comparison': 'contains',
                'value': '카페'
            }
        }
    )
    
    filtered_transactions = filter_engine.apply_filter(transactions, contains_filter)
    print_transactions(filtered_transactions, "설명에 '카페' 포함")
    
    # 예제 6: 동적 필터 생성
    print("\n\n예제 6: 동적 필터 생성 및 적용")
    conditions = {
        'operator': 'and',
        'conditions': [
            {
                'field': 'transaction_type',
                'comparison': 'equals',
                'value': 'income'
            },
            {
                'field': 'amount',
                'comparison': 'greater_than',
                'value': 1000000
            }
        ]
    }
    
    dynamic_filter = filter_engine.create_dynamic_filter(conditions, "고액 수입")
    filtered_transactions = filter_engine.apply_filter(transactions, dynamic_filter)
    print_transactions(filtered_transactions, "100만원 이상 수입")
    
    # 예제 7: 필터 저장 및 조회
    print("\n\n예제 7: 필터 저장 및 조회")
    
    # 필터 저장
    filter_id = filter_engine.save_filter(dynamic_filter)
    print(f"필터 저장 완료 (ID: {filter_id})")
    
    # 저장된 필터 조회
    saved_filters = filter_engine.get_all_filters()
    print("\n저장된 필터 목록:")
    for f in saved_filters:
        print(f"- {f.filter_name} (ID: {f.id})")
    
    # 예제 8: 필터 조합
    print("\n\n예제 8: 필터 조합 적용")
    
    # 두 개의 필터 생성 및 저장
    filter1 = AnalysisFilter(
        filter_name="최근 거래",
        filter_config={
            'conditions': {
                'field': 'transaction_date',
                'comparison': 'greater_than',
                'value': (date.today() - timedelta(days=15)).isoformat()
            }
        }
    )
    
    filter2 = AnalysisFilter(
        filter_name="지출만",
        filter_config={
            'conditions': {
                'field': 'transaction_type',
                'comparison': 'equals',
                'value': 'expense'
            }
        }
    )
    
    filter_id1 = filter_engine.save_filter(filter1)
    filter_id2 = filter_engine.save_filter(filter2)
    
    # AND 조합 적용
    combined_and = filter_engine.apply_combined_filters(
        transactions, [filter_id1, filter_id2], AnalysisFilter.OP_AND
    )
    print_transactions(combined_and, "최근 15일 지출 (AND 조합)")
    
    # OR 조합 적용
    combined_or = filter_engine.apply_combined_filters(
        transactions, [filter_id1, filter_id2], AnalysisFilter.OP_OR
    )
    print_transactions(combined_or, "최근 15일 또는 지출 (OR 조합)")


if __name__ == "__main__":
    main()