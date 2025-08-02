# -*- coding: utf-8 -*-
"""
응답 포맷터 테스트 모듈
"""

import unittest
from src.response_formatter import format_response, extract_insights, handle_agent_error

class TestResponseFormatter(unittest.TestCase):
    """응답 포맷터 테스트 클래스"""
    
    def test_format_transactions(self):
        """거래 목록 포맷팅 테스트"""
        # 테스트 데이터
        test_data = {
            'transactions': [
                {
                    'date': '2023-07-01',
                    'amount': 10000,
                    'description': '편의점',
                    'category': '식료품',
                    'payment_method': '신용카드'
                },
                {
                    'date': '2023-07-02',
                    'amount': 30000,
                    'description': '식당',
                    'category': '외식',
                    'payment_method': '체크카드'
                }
            ],
            'total': 40000,
            'count': 2
        }
        
        # 포맷팅 실행
        result = format_response(test_data)
        
        # 검증
        self.assertIn('거래 내역', result)
        self.assertIn('편의점', result)
        self.assertIn('식당', result)
        self.assertIn('10,000', result)
        self.assertIn('30,000', result)
        self.assertIn('40,000', result)
    
    def test_format_analysis(self):
        """분석 결과 포맷팅 테스트"""
        # 테스트 데이터
        test_data = {
            'type': 'expense',
            'analysis': {
                'summary': '7월 지출 분석 결과입니다.',
                'details': [
                    {
                        'name': '식료품',
                        'value': 150000,
                        'percentage': 30.0
                    },
                    {
                        'name': '교통',
                        'value': 100000,
                        'percentage': 20.0
                    },
                    {
                        'name': '주거',
                        'value': 250000,
                        'percentage': 50.0
                    }
                ]
            },
            'period': '2023년 7월'
        }
        
        # 포맷팅 실행
        result = format_response(test_data)
        
        # 검증
        self.assertIn('지출 분석 결과', result)
        self.assertIn('7월 지출 분석 결과입니다', result)
        self.assertIn('식료품', result)
        self.assertIn('150,000', result)
        self.assertIn('30.0%', result)
    
    def test_format_error(self):
        """오류 메시지 포맷팅 테스트"""
        # 테스트 데이터
        test_data = {
            'success': False,
            'error': '데이터베이스 연결 오류',
            'error_code': 'DB_CONNECTION_ERROR'
        }
        
        # 포맷팅 실행
        result = format_response(test_data)
        
        # 검증
        self.assertIn('오류가 발생했습니다', result)
        self.assertIn('데이터베이스 연결 오류', result)
        self.assertIn('DB_CONNECTION_ERROR', result)
    
    def test_extract_insights(self):
        """인사이트 추출 테스트"""
        # 테스트 데이터
        test_data = {
            'type': 'expense',
            'analysis': {
                'details': [
                    {
                        'name': '식료품',
                        'value': 150000,
                        'percentage': 30.0
                    },
                    {
                        'name': '교통',
                        'value': 100000,
                        'percentage': 20.0
                    },
                    {
                        'name': '주거',
                        'value': 250000,
                        'percentage': 50.0
                    }
                ]
            },
            'total': 500000,
            'average': 16666.67,
            'period': '2023년 7월'
        }
        
        # 인사이트 추출 실행
        insights = extract_insights(test_data)
        
        # 검증
        self.assertTrue(len(insights) > 0)
        self.assertTrue(any('주거' in insight for insight in insights))
    
    def test_handle_agent_error(self):
        """에이전트 오류 처리 테스트"""
        # 테스트 데이터
        class TestError(Exception):
            pass
        
        error = TestError("테스트 오류 메시지")
        
        # 오류 처리 실행
        result = handle_agent_error(error)
        
        # 검증
        self.assertIn('오류가 발생했습니다', result)
        self.assertIn('테스트 오류 메시지', result)

if __name__ == '__main__':
    unittest.main()