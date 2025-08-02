# -*- coding: utf-8 -*-
"""
비교 분석기 테스트
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.models import Transaction
from src.analyzers import ComparisonAnalyzer
from src.repositories.transaction_repository import TransactionRepository


class TestComparisonAnalyzer(unittest.TestCase):
    """비교 분석기 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.repository = MagicMock(spec=TransactionRepository)
        self.analyzer = ComparisonAnalyzer(self.repository)
        
        # 테스트 데이터 설정
        self.today = datetime.now().date()
        
        # 첫 번째 기간 거래 데이터 (이전 달)
        self.period1_transactions = [
            Transaction(
                transaction_id="exp1_1",
                transaction_date=self.today - timedelta(days=40),
                description="식당 결제",
                amount=Decimal("20000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="식비",
                payment_method="체크카드",
                source="toss_card",
                account_type="일반"
            ),
            Transaction(
                transaction_id="exp1_2",
                transaction_date=self.today - timedelta(days=35),
                description="마트 결제",
                amount=Decimal("30000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="생활용품",
                payment_method="체크카드",
                source="toss_card",
                account_type="일반"
            )
        ]
        
        # 두 번째 기간 거래 데이터 (이번 달)
        self.period2_transactions = [
            Transaction(
                transaction_id="exp2_1",
                transaction_date=self.today - timedelta(days=10),
                description="식당 결제",
                amount=Decimal("25000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="식비",
                payment_method="체크카드",
                source="toss_card",
                account_type="일반"
            ),
            Transaction(
                transaction_id="exp2_2",
                transaction_date=self.today - timedelta(days=5),
                description="마트 결제",
                amount=Decimal("45000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="생활용품",
                payment_method="체크카드",
                source="toss_card",
                account_type="일반"
            ),
            Transaction(
                transaction_id="exp2_3",
                transaction_date=self.today - timedelta(days=2),
                description="교통비",
                amount=Decimal("5000"),
                transaction_type=Transaction.TYPE_EXPENSE,
                category="교통비",
                payment_method="현금",
                source="manual",
                account_type=None
            )
        ]
    
    def test_compare_periods(self):
        """기간 비교 테스트"""
        # 모의 객체 설정
        self.repository.list.side_effect = [
            self.period1_transactions,  # 첫 번째 호출 시 반환
            self.period2_transactions   # 두 번째 호출 시 반환
        ]
        
        # 기간 설정
        period1_start = self.today - timedelta(days=45)
        period1_end = self.today - timedelta(days=31)
        period2_start = self.today - timedelta(days=15)
        period2_end = self.today
        
        # 비교 분석 실행
        result = self.analyzer.compare_periods(
            period1_start, period1_end,
            period2_start, period2_end,
            Transaction.TYPE_EXPENSE
        )
        
        # 검증
        self.assertEqual(self.repository.list.call_count, 2)
        
        # 요약 비교 검증
        summary = result['summary_comparison']
        self.assertEqual(summary['total1'], 50000.0)  # 첫 번째 기간 총액
        self.assertEqual(summary['total2'], 75000.0)  # 두 번째 기간 총액
        self.assertEqual(summary['diff'], 25000.0)    # 차이
        self.assertEqual(summary['diff_percentage'], 50.0)  # 변화율
        
        # 카테고리별 비교 검증
        categories = {item['category']: item for item in result['category_comparison']}
        self.assertEqual(len(categories), 3)
        self.assertEqual(categories['식비']['diff'], 5000.0)
        self.assertEqual(categories['생활용품']['diff'], 15000.0)
        self.assertEqual(categories['교통비']['amount1'], 0.0)
        self.assertEqual(categories['교통비']['amount2'], 5000.0)
        
        # 결제 방식별 비교 검증
        payment_methods = {item['payment_method']: item for item in result['payment_method_comparison']}
        self.assertEqual(len(payment_methods), 2)
        self.assertEqual(payment_methods['체크카드']['diff'], 20000.0)
        self.assertEqual(payment_methods['현금']['amount1'], 0.0)
        self.assertEqual(payment_methods['현금']['amount2'], 5000.0)
    
    def test_compare_months(self):
        """월 비교 테스트"""
        # 모의 객체 설정
        self.repository.list.side_effect = [
            self.period1_transactions,  # 첫 번째 호출 시 반환
            self.period2_transactions   # 두 번째 호출 시 반환
        ]
        
        # 현재 연월 계산
        today = datetime.now().date()
        current_year = today.year
        current_month = today.month
        
        # 이전 월 계산
        if current_month == 1:
            prev_year = current_year - 1
            prev_month = 12
        else:
            prev_year = current_year
            prev_month = current_month - 1
        
        # 비교 분석 실행
        result = self.analyzer.compare_months(
            prev_year, prev_month,
            current_year, current_month,
            Transaction.TYPE_EXPENSE
        )
        
        # 검증
        self.assertEqual(self.repository.list.call_count, 2)
        
        # 기간 정보 검증
        self.assertEqual(result['period1']['year_month'], f"{prev_year}-{prev_month:02d}")
        self.assertEqual(result['period2']['year_month'], f"{current_year}-{current_month:02d}")
        
        # 요약 비교 검증
        summary = result['summary_comparison']
        self.assertEqual(summary['total1'], 50000.0)  # 첫 번째 기간 총액
        self.assertEqual(summary['total2'], 75000.0)  # 두 번째 기간 총액
    
    def test_compare_with_previous_period(self):
        """이전 기간과 비교 테스트"""
        # 모의 객체 설정
        self.repository.list.side_effect = [
            self.period1_transactions,  # 첫 번째 호출 시 반환
            self.period2_transactions   # 두 번째 호출 시 반환
        ]
        
        # 현재 기간 설정
        end_date = self.today
        start_date = end_date - timedelta(days=14)
        
        # 비교 분석 실행
        result = self.analyzer.compare_with_previous_period(
            start_date, end_date,
            Transaction.TYPE_EXPENSE
        )
        
        # 검증
        self.assertEqual(self.repository.list.call_count, 2)
        
        # 기간 정보 검증
        self.assertEqual(result['period1']['days'], 15)  # 이전 기간 일수
        self.assertEqual(result['period2']['days'], 15)  # 현재 기간 일수
        
        # 요약 비교 검증
        summary = result['summary_comparison']
        self.assertEqual(summary['total1'], 50000.0)  # 첫 번째 기간 총액
        self.assertEqual(summary['total2'], 75000.0)  # 두 번째 기간 총액


if __name__ == '__main__':
    unittest.main()