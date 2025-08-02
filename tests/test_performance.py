# -*- coding: utf-8 -*-
"""
금융 거래 관리 시스템 성능 테스트 모듈

시스템의 성능을 테스트하고 최적화 포인트를 식별합니다.
"""

import unittest
import time
import sys
import os
import json
from unittest.mock import patch, MagicMock
import logging

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 테스트할 모듈 가져오기
try:
    from src.financial_tools.transaction_tools import list_transactions, search_transactions
    from src.financial_tools.analysis_tools import analyze_expenses, analyze_income
    from src.financial_tools.comparison_tools import compare_periods
    from src.financial_agent import run_financial_agent
    from src.response_formatter import format_response
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"일부 모듈을 가져올 수 없습니다: {e}")
    MODULES_AVAILABLE = False

@unittest.skipIf(not MODULES_AVAILABLE, "필요한 모듈을 가져올 수 없습니다")
class TestPerformance(unittest.TestCase):
    """성능 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트 컨텍스트 초기화
        self.test_context = {
            "user_name": "강태희",
            "current_time": "2025-07-23 12:00:00",
            "location": "대한민국 서울",
            "conversation_history": []
        }
    
    def measure_execution_time(self, func, *args, **kwargs):
        """함수 실행 시간을 측정합니다."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    
    @patch('src.financial_tools.transaction_tools.list_transactions')
    def test_transaction_query_performance(self, mock_list_transactions):
        """거래 조회 성능 테스트"""
        # 모의 응답 설정 - 다양한 크기의 결과 집합
        def mock_list_with_size(size):
            transactions = []
            for i in range(size):
                transactions.append({
                    'id': f'tx_{i}',
                    'date': '2025-07-23',
                    'amount': 10000,
                    'description': f'테스트 거래 {i}',
                    'category': '식비',
                    'payment_method': '신용카드'
                })
            return {
                'transactions': transactions,
                'total': size * 10000,
                'count': size
            }
        
        # 다양한 크기의 결과 집합에 대한 성능 테스트
        sizes = [10, 100, 500, 1000]
        results = {}
        
        for size in sizes:
            mock_list_transactions.return_value = mock_list_with_size(size)
            
            # 거래 조회 성능 측정
            _, query_time = self.measure_execution_time(
                list_transactions,
                start_date="2025-07-01",
                end_date="2025-07-31"
            )
            
            # 응답 포맷팅 성능 측정
            result = mock_list_with_size(size)
            _, format_time = self.measure_execution_time(format_response, result)
            
            # 결과 저장
            results[size] = {
                'query_time': query_time,
                'format_time': format_time,
                'total_time': query_time + format_time
            }
            
            logger.info(f"거래 {size}개 처리 시간: 쿼리={query_time:.4f}초, 포맷팅={format_time:.4f}초, 총={query_time + format_time:.4f}초")
        
        # 성능 결과 분석
        for size in sizes[1:]:
            # 이전 크기와 비교하여 선형적인 증가인지 확인
            prev_size = sizes[sizes.index(size) - 1]
            ratio = size / prev_size
            time_ratio = results[size]['total_time'] / results[prev_size]['total_time']
            
            # 시간 증가율이 데이터 크기 증가율보다 크게 높으면 경고
            if time_ratio > ratio * 1.5:
                logger.warning(f"성능 경고: 데이터 크기가 {ratio}배 증가했지만, 처리 시간은 {time_ratio:.2f}배 증가했습니다.")
    
    @patch('src.financial_tools.analysis_tools.analyze_expenses')
    def test_analysis_performance(self, mock_analyze_expenses):
        """분석 성능 테스트"""
        # 모의 응답 설정 - 다양한 복잡도의 분석 결과
        def mock_analysis_with_complexity(complexity):
            details = []
            for i in range(complexity):
                details.append({
                    'name': f'카테고리 {i}',
                    'value': 10000 * (complexity - i),
                    'percentage': 100 / complexity
                })
            
            return {
                'type': 'expense',
                'analysis': {
                    'summary': f'{complexity} 카테고리에 대한 분석 결과입니다.',
                    'details': details
                },
                'period': '2025년 7월'
            }
        
        # 다양한 복잡도의 분석에 대한 성능 테스트
        complexities = [5, 20, 50, 100]
        results = {}
        
        for complexity in complexities:
            mock_analyze_expenses.return_value = mock_analysis_with_complexity(complexity)
            
            # 분석 성능 측정
            _, analysis_time = self.measure_execution_time(
                analyze_expenses,
                start_date="2025-07-01",
                end_date="2025-07-31"
            )
            
            # 응답 포맷팅 성능 측정
            result = mock_analysis_with_complexity(complexity)
            _, format_time = self.measure_execution_time(format_response, result)
            
            # 결과 저장
            results[complexity] = {
                'analysis_time': analysis_time,
                'format_time': format_time,
                'total_time': analysis_time + format_time
            }
            
            logger.info(f"복잡도 {complexity}의 분석 처리 시간: 분석={analysis_time:.4f}초, 포맷팅={format_time:.4f}초, 총={analysis_time + format_time:.4f}초")
        
        # 성능 결과 분석
        for complexity in complexities[1:]:
            # 이전 복잡도와 비교하여 선형적인 증가인지 확인
            prev_complexity = complexities[complexities.index(complexity) - 1]
            ratio = complexity / prev_complexity
            time_ratio = results[complexity]['total_time'] / results[prev_complexity]['total_time']
            
            # 시간 증가율이 복잡도 증가율보다 크게 높으면 경고
            if time_ratio > ratio * 1.5:
                logger.warning(f"성능 경고: 복잡도가 {ratio}배 증가했지만, 처리 시간은 {time_ratio:.2f}배 증가했습니다.")
    
    @patch('src.financial_agent.run_financial_agent')
    def test_agent_response_time(self, mock_financial_agent):
        """에이전트 응답 시간 테스트"""
        # 모의 응답 설정
        mock_financial_agent.return_value = "테스트 응답입니다."
        
        # 다양한 복잡도의 쿼리에 대한 성능 테스트
        queries = [
            "이번 달 지출 얼마야?",  # 간단한 쿼리
            "지난 3개월 동안의 식비 지출을 카테고리별로 분석해줘",  # 중간 복잡도 쿼리
            "올해 1월부터 6월까지의 월별 수입과 지출을 비교하고, 카테고리별로 가장 큰 변화가 있는 항목을 알려줘"  # 복잡한 쿼리
        ]
        
        for i, query in enumerate(queries):
            # 에이전트 응답 시간 측정
            _, response_time = self.measure_execution_time(
                run_financial_agent,
                query,
                self.test_context
            )
            
            complexity = ["간단한", "중간 복잡도", "복잡한"][i]
            logger.info(f"{complexity} 쿼리 응답 시간: {response_time:.4f}초")
            
            # 응답 시간이 너무 길면 경고
            if response_time > 5.0:  # 5초 이상이면 경고
                logger.warning(f"성능 경고: {complexity} 쿼리의 응답 시간이 {response_time:.2f}초로 너무 깁니다.")
    
    @patch('src.financial_tools.comparison_tools.compare_periods')
    def test_comparison_performance(self, mock_compare_periods):
        """비교 분석 성능 테스트"""
        # 모의 응답 설정 - 다양한 크기의 비교 결과
        def mock_comparison_with_size(size):
            changes = []
            for i in range(size):
                changes.append({
                    'name': f'카테고리 {i}',
                    'value1': 10000,
                    'value2': 12000,
                    'change': 2000,
                    'change_percentage': 20.0
                })
            
            return {
                'type': 'expense',
                'comparison': {
                    'summary': f'{size} 카테고리에 대한 비교 분석 결과입니다.',
                    'total_change': 2000 * size,
                    'total_change_percentage': 20.0,
                    'changes': changes
                },
                'period1': '2025년 6월',
                'period2': '2025년 7월'
            }
        
        # 다양한 크기의 비교 분석에 대한 성능 테스트
        sizes = [5, 20, 50, 100]
        results = {}
        
        for size in sizes:
            mock_compare_periods.return_value = mock_comparison_with_size(size)
            
            # 비교 분석 성능 측정
            _, comparison_time = self.measure_execution_time(
                compare_periods,
                period1_start="2025-06-01",
                period1_end="2025-06-30",
                period2_start="2025-07-01",
                period2_end="2025-07-31"
            )
            
            # 응답 포맷팅 성능 측정
            result = mock_comparison_with_size(size)
            _, format_time = self.measure_execution_time(format_response, result)
            
            # 결과 저장
            results[size] = {
                'comparison_time': comparison_time,
                'format_time': format_time,
                'total_time': comparison_time + format_time
            }
            
            logger.info(f"{size} 카테고리 비교 처리 시간: 비교={comparison_time:.4f}초, 포맷팅={format_time:.4f}초, 총={comparison_time + format_time:.4f}초")
        
        # 성능 결과 분석
        for size in sizes[1:]:
            # 이전 크기와 비교하여 선형적인 증가인지 확인
            prev_size = sizes[sizes.index(size) - 1]
            ratio = size / prev_size
            time_ratio = results[size]['total_time'] / results[prev_size]['total_time']
            
            # 시간 증가율이 데이터 크기 증가율보다 크게 높으면 경고
            if time_ratio > ratio * 1.5:
                logger.warning(f"성능 경고: 데이터 크기가 {ratio}배 증가했지만, 처리 시간은 {time_ratio:.2f}배 증가했습니다.")


@unittest.skipIf(not MODULES_AVAILABLE, "필요한 모듈을 가져올 수 없습니다")
class TestOptimization(unittest.TestCase):
    """최적화 테스트 클래스"""
    
    def test_response_formatter_optimization(self):
        """응답 포맷터 최적화 테스트"""
        # 대용량 거래 목록 생성
        large_transaction_list = {
            'transactions': [],
            'total': 0,
            'count': 1000
        }
        
        total_amount = 0
        for i in range(1000):
            amount = 10000 + (i % 100) * 100
            total_amount += amount
            large_transaction_list['transactions'].append({
                'id': f'tx_{i}',
                'date': '2025-07-23',
                'amount': amount,
                'description': f'테스트 거래 {i}',
                'category': '식비',
                'payment_method': '신용카드'
            })
        
        large_transaction_list['total'] = total_amount
        
        # 포맷팅 성능 측정
        start_time = time.time()
        formatted_response = format_response(large_transaction_list)
        end_time = time.time()
        
        # 포맷팅 시간 확인
        formatting_time = end_time - start_time
        logger.info(f"1000개 거래 포맷팅 시간: {formatting_time:.4f}초")
        
        # 포맷팅 결과 확인
        self.assertIn("거래 내역", formatted_response)
        self.assertIn("외", formatted_response)  # "외 X건의 거래가 더 있습니다" 문구 확인
        
        # 포맷팅 시간이 너무 길면 경고
        if formatting_time > 1.0:  # 1초 이상이면 경고
            logger.warning(f"성능 경고: 대용량 거래 목록 포맷팅 시간이 {formatting_time:.2f}초로 너무 깁니다.")
    
    def test_insight_extraction_optimization(self):
        """인사이트 추출 최적화 테스트"""
        from src.response_formatter import extract_insights
        
        # 복잡한 분석 결과 생성
        complex_analysis = {
            'type': 'expense',
            'analysis': {
                'details': []
            },
            'total': 1000000,
            'average': 33333.33,
            'period': '2025년 7월'
        }
        
        # 50개의 카테고리 추가
        for i in range(50):
            complex_analysis['analysis']['details'].append({
                'name': f'카테고리 {i}',
                'value': 20000 - i * 300,
                'percentage': (20000 - i * 300) / 10000
            })
        
        # 인사이트 추출 성능 측정
        start_time = time.time()
        insights = extract_insights(complex_analysis)
        end_time = time.time()
        
        # 인사이트 추출 시간 확인
        extraction_time = end_time - start_time
        logger.info(f"50개 카테고리 인사이트 추출 시간: {extraction_time:.4f}초")
        
        # 인사이트가 추출되었는지 확인
        self.assertTrue(len(insights) > 0)
        
        # 추출 시간이 너무 길면 경고
        if extraction_time > 0.5:  # 0.5초 이상이면 경고
            logger.warning(f"성능 경고: 인사이트 추출 시간이 {extraction_time:.2f}초로 너무 깁니다.")


if __name__ == '__main__':
    unittest.main()