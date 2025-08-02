# -*- coding: utf-8 -*-
"""
IncomePatternAnalyzer 테스트

수입 거래의 패턴 분석 및 정기성 식별 기능을 테스트합니다.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import json
from datetime import date, datetime, timedelta
from decimal import Decimal

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ingesters.income_pattern_analyzer import IncomePatternAnalyzer


class TestIncomePatternAnalyzer(unittest.TestCase):
    """
    IncomePatternAnalyzer 클래스 테스트
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        self.analyzer = IncomePatternAnalyzer()
        
        # 임시 파일 생성을 위한 디렉토리
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # 테스트 데이터 생성
        self._create_test_data()
    
    def tearDown(self):
        """
        테스트 정리
        """
        self.temp_dir.cleanup()
    
    def _create_test_data(self):
        """
        테스트 데이터 생성
        """
        # 월급 데이터 (매월 15일)
        for month in range(1, 7):
            transaction_date = date(2024, month, 15)
            self.analyzer.add_transaction({
                'transaction_id': f"INCOME_202401{month}15_2500000_12345678",
                'transaction_date': transaction_date,
                'description': f"{month}월 급여",
                'amount': Decimal('2500000'),
                'category': "급여"
            })
        
        # 이자 데이터 (매월 20일)
        for month in range(1, 7):
            transaction_date = date(2024, month, 20)
            self.analyzer.add_transaction({
                'transaction_id': f"INCOME_202401{month}20_5000_12345678",
                'transaction_date': transaction_date,
                'description': f"{month}월 이자",
                'amount': Decimal('5000'),
                'category': "이자"
            })
        
        # 주급 데이터 (매주 금요일)
        start_date = date(2024, 1, 5)  # 첫 번째 금요일
        for week in range(12):
            transaction_date = start_date + timedelta(days=7 * week)
            self.analyzer.add_transaction({
                'transaction_id': f"INCOME_{transaction_date.strftime('%Y%m%d')}_100000_12345678",
                'transaction_date': transaction_date,
                'description': f"{transaction_date.strftime('%m/%d')} 주급",
                'amount': Decimal('100000'),
                'category': "부수입"
            })
        
        # 비정기 수입
        random_dates = [
            date(2024, 1, 10),
            date(2024, 2, 5),
            date(2024, 3, 22),
            date(2024, 5, 17)
        ]
        
        for i, transaction_date in enumerate(random_dates):
            self.analyzer.add_transaction({
                'transaction_id': f"INCOME_{transaction_date.strftime('%Y%m%d')}_{50000+i*10000}_12345678",
                'transaction_date': transaction_date,
                'description': f"판매 수익 {i+1}",
                'amount': Decimal(f"{50000+i*10000}"),
                'category': "판매수입"
            })
    
    def test_init(self):
        """
        초기화 테스트
        """
        self.assertIsInstance(self.analyzer._income_history, dict)
        self.assertIsInstance(self.analyzer.regular_patterns, dict)
        self.assertIsInstance(self.analyzer.income_trends, dict)
    
    def test_add_transaction(self):
        """
        거래 추가 테스트
        """
        # 거래 추가
        self.analyzer.add_transaction({
            'transaction_id': "TEST_20240101_100000_12345678",
            'transaction_date': "2024-01-01",
            'description': "테스트 거래",
            'amount': 100000,
            'category': "테스트"
        })
        
        # 내역에 추가되었는지 확인
        self.assertIn("테스트", self.analyzer._income_history)
        self.assertEqual(len(self.analyzer._income_history["테스트"]), 1)
        self.assertEqual(self.analyzer._income_history["테스트"][0]['amount'], 100000)
        self.assertEqual(self.analyzer._income_history["테스트"][0]['date'], date(2024, 1, 1))
    
    def test_analyze_patterns(self):
        """
        패턴 분석 테스트
        """
        # 패턴 분석
        result = self.analyzer.analyze_patterns()
        
        # 결과 확인
        self.assertIn('regular_patterns', result)
        self.assertIn('income_trends', result)
        self.assertIn('analysis_date', result)
        
        # 정기 패턴 확인
        patterns = result['regular_patterns']
        self.assertIn('급여', patterns)
        self.assertIn('이자', patterns)
        self.assertIn('부수입', patterns)
        self.assertNotIn('판매수입', patterns)  # 비정기 수입
        
        # 급여 패턴 확인
        self.assertEqual(patterns['급여']['period_type'], 'monthly')
        self.assertAlmostEqual(patterns['급여']['avg_interval'], 30, delta=2)
        self.assertAlmostEqual(patterns['급여']['avg_amount'], 2500000, delta=1)
        
        # 이자 패턴 확인
        self.assertEqual(patterns['이자']['period_type'], 'monthly')
        self.assertAlmostEqual(patterns['이자']['avg_interval'], 30, delta=2)
        self.assertAlmostEqual(patterns['이자']['avg_amount'], 5000, delta=1)
        
        # 주급 패턴 확인
        self.assertEqual(patterns['부수입']['period_type'], 'weekly')
        self.assertAlmostEqual(patterns['부수입']['avg_interval'], 7, delta=1)
        self.assertAlmostEqual(patterns['부수입']['avg_amount'], 100000, delta=1)
        
        # 트렌드 확인
        trends = result['income_trends']
        self.assertIn('monthly_totals', trends)
        self.assertIn('category_series', trends)
        self.assertIn('growth_rates', trends)
    
    def test_determine_period_type(self):
        """
        주기 유형 결정 테스트
        """
        self.assertEqual(self.analyzer._determine_period_type(1), 'daily')
        self.assertEqual(self.analyzer._determine_period_type(7), 'weekly')
        self.assertEqual(self.analyzer._determine_period_type(14), 'biweekly')
        self.assertEqual(self.analyzer._determine_period_type(30), 'monthly')
        self.assertEqual(self.analyzer._determine_period_type(90), 'quarterly')
        self.assertEqual(self.analyzer._determine_period_type(365), 'yearly')
        self.assertEqual(self.analyzer._determine_period_type(45), 'custom_45_days')
    
    def test_calculate_confidence(self):
        """
        신뢰도 계산 테스트
        """
        # 높은 신뢰도 (많은 샘플, 낮은 변동성)
        high_confidence = self.analyzer._calculate_confidence(10, 0.05, 0.02)
        self.assertGreaterEqual(high_confidence, 0.8)
        
        # 중간 신뢰도
        medium_confidence = self.analyzer._calculate_confidence(5, 0.1, 0.05)
        self.assertGreaterEqual(medium_confidence, 0.5)
        self.assertLessEqual(medium_confidence, 0.8)
        
        # 낮은 신뢰도 (적은 샘플, 높은 변동성)
        low_confidence = self.analyzer._calculate_confidence(2, 0.2, 0.1)
        self.assertLessEqual(low_confidence, 0.5)
    
    def test_predict_future_income(self):
        """
        미래 수입 예측 테스트
        """
        # 패턴 분석
        self.analyzer.analyze_patterns()
        
        # 미래 수입 예측
        result = self.analyzer.predict_future_income(months_ahead=3)
        
        # 결과 확인
        self.assertIn('predictions', result)
        self.assertIn('monthly_totals', result)
        
        # 예측 확인
        predictions = result['predictions']
        self.assertGreater(len(predictions), 0)
        
        # 카테고리별 예측 확인
        categories = set(p['category'] for p in predictions)
        self.assertIn('급여', categories)
        self.assertIn('이자', categories)
        self.assertIn('부수입', categories)
        
        # 월별 총액 확인
        monthly_totals = result['monthly_totals']
        self.assertGreater(len(monthly_totals), 0)
    
    def test_get_regular_income_summary(self):
        """
        정기 수입 요약 테스트
        """
        # 패턴 분석
        self.analyzer.analyze_patterns()
        
        # 정기 수입 요약
        result = self.analyzer.get_regular_income_summary()
        
        # 결과 확인
        self.assertIn('total_regular_income', result)
        self.assertIn('monthly_equivalent', result)
        self.assertIn('regular_income_count', result)
        self.assertIn('by_period_type', result)
        
        # 정기 수입 수 확인
        self.assertEqual(result['regular_income_count'], 3)
        
        # 주기별 통계 확인
        by_period_type = result['by_period_type']
        self.assertIn('monthly', by_period_type)
        self.assertIn('weekly', by_period_type)
        
        # 월 환산 금액 확인
        self.assertGreater(result['monthly_equivalent'], 0)
    
    def test_save_and_load_history(self):
        """
        내역 저장 및 로드 테스트
        """
        # 패턴 분석
        self.analyzer.analyze_patterns()
        
        # 내역 저장
        history_file = os.path.join(self.temp_dir.name, 'test_history.json')
        self.analyzer.save_history(history_file)
        
        # 파일이 생성되었는지 확인
        self.assertTrue(os.path.exists(history_file))
        
        # 새 분석기 생성 및 내역 로드
        new_analyzer = IncomePatternAnalyzer(history_file)
        
        # 내역이 로드되었는지 확인
        self.assertGreater(len(new_analyzer._income_history), 0)
        self.assertIn('급여', new_analyzer._income_history)
        self.assertIn('이자', new_analyzer._income_history)
        self.assertIn('부수입', new_analyzer._income_history)
        
        # 정기 패턴이 로드되었는지 확인
        self.assertGreater(len(new_analyzer.regular_patterns), 0)
        
        # 트렌드가 로드되었는지 확인
        self.assertGreater(len(new_analyzer.income_trends), 0)


if __name__ == '__main__':
    unittest.main()