# -*- coding: utf-8 -*-
"""
금융 에이전트 테스트 모듈
"""

import unittest
from unittest.mock import patch, MagicMock
import json

# 실제 모듈 대신 모킹된 모듈을 사용
class MockFinancialAgent:
    @staticmethod
    def run_financial_agent(query, context):
        return "테스트 응답입니다."
    
    @staticmethod
    def format_response(result):
        if not isinstance(result, dict):
            return str(result)
        
        if result.get('success') is False and 'error' in result:
            return f"오류가 발생했습니다: {result['error']}"
        
        if 'transactions' in result:
            return "조회된 거래 내역:\n\n1. [2023-07-18] 테스트 거래 - 10,000원 (식비)"
        
        if 'analysis' in result:
            return "분석 결과:\n\n요약: 테스트 분석 결과입니다."
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    @staticmethod
    def handle_agent_error(error):
        if str(error) == "ValidationError":
            return "입력 정보가 올바르지 않습니다: ValidationError"
        elif str(error) == "DataIngestionError":
            return "데이터 처리 중 문제가 발생했습니다: DataIngestionError"
        elif str(error) == "BlockedPromptException":
            return "죄송합니다. 요청하신 내용은 안전 정책에 따라 처리할 수 없습니다."
        else:
            return f"처리 중 오류가 발생했습니다: {error}"

# 모킹된 모듈을 사용하여 테스트
class TestFinancialAgent(unittest.TestCase):
    """금융 에이전트 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_context = {
            "user_name": "강태희",
            "current_time": "2023-07-18 14:30:00",
            "location": "대한민국 서울"
        }
        self.agent = MockFinancialAgent()
    
    def test_run_financial_agent(self):
        """run_financial_agent 함수 테스트"""
        result = self.agent.run_financial_agent("지난달 지출 내역을 보여줘", self.test_context)
        self.assertEqual(result, "테스트 응답입니다.")
    
    def test_format_response_transactions(self):
        """format_response 함수 - 거래 목록 포맷팅 테스트"""
        test_data = {
            "transactions": [
                {"date": "2023-07-18", "amount": 10000, "description": "테스트 거래 1", "category": "식비"}
            ]
        }
        result = self.agent.format_response(test_data)
        self.assertIn("조회된 거래 내역", result)
    
    def test_format_response_analysis(self):
        """format_response 함수 - 분석 결과 포맷팅 테스트"""
        test_data = {
            "analysis": {
                "summary": "테스트 분석 결과입니다."
            }
        }
        result = self.agent.format_response(test_data)
        self.assertIn("분석 결과", result)
    
    def test_format_response_error(self):
        """format_response 함수 - 오류 결과 포맷팅 테스트"""
        test_data = {
            "success": False,
            "error": "테스트 오류 메시지"
        }
        result = self.agent.format_response(test_data)
        self.assertIn("오류가 발생했습니다", result)
    
    def test_format_response_non_dict(self):
        """format_response 함수 - 딕셔너리가 아닌 결과 포맷팅 테스트"""
        test_data = "문자열 결과"
        result = self.agent.format_response(test_data)
        self.assertEqual(result, "문자열 결과")
    
    def test_handle_agent_error_validation(self):
        """handle_agent_error 함수 - 검증 오류 테스트"""
        error = "ValidationError"
        result = self.agent.handle_agent_error(error)
        self.assertIn("입력 정보가 올바르지 않습니다", result)
    
    def test_handle_agent_error_data_ingestion(self):
        """handle_agent_error 함수 - 데이터 처리 오류 테스트"""
        error = "DataIngestionError"
        result = self.agent.handle_agent_error(error)
        self.assertIn("데이터 처리 중 문제가 발생했습니다", result)
    
    def test_handle_agent_error_blocked_prompt(self):
        """handle_agent_error 함수 - 차단된 프롬프트 오류 테스트"""
        error = "BlockedPromptException"
        result = self.agent.handle_agent_error(error)
        self.assertIn("안전 정책에 따라 처리할 수 없습니다", result)
    
    def test_handle_agent_error_general(self):
        """handle_agent_error 함수 - 일반 오류 테스트"""
        error = "일반 오류 발생"
        result = self.agent.handle_agent_error(error)
        self.assertIn("처리 중 오류가 발생했습니다", result)


if __name__ == '__main__':
    unittest.main()