# -*- coding: utf-8 -*-
"""
금융 거래 관리 시스템 통합 테스트 모듈

전체 시스템의 통합 테스트를 수행합니다.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import process_query, is_financial_query, update_conversation_history
from src.financial_agent import run_financial_agent
from src.general_agent import run_general_agent

class TestSystemIntegration(unittest.TestCase):
    """시스템 통합 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트 컨텍스트 초기화
        self.test_context = {
            "user_name": "강태희",
            "current_time": "2025-07-23 12:00:00",
            "location": "대한민국 서울",
            "conversation_history": []
        }
    
    @patch('main.run_financial_agent')
    @patch('main.run_general_agent')
    def test_query_routing_financial(self, mock_general_agent, mock_financial_agent):
        """금융 쿼리 라우팅 테스트"""
        # 모의 응답 설정
        mock_financial_agent.return_value = "금융 에이전트 응답"
        mock_general_agent.return_value = "일반 에이전트 응답"
        
        # 금융 관련 쿼리 처리
        query = "지난달 지출 내역을 보여줘"
        response = process_query(query, self.test_context)
        
        # 금융 에이전트가 호출되었는지 확인
        mock_financial_agent.assert_called_once()
        mock_general_agent.assert_not_called()
        
        # 응답이 금융 에이전트에서 왔는지 확인
        self.assertEqual(response, "금융 에이전트 응답")
        
        # 컨텍스트가 올바르게 업데이트되었는지 확인
        self.assertEqual(self.test_context["last_agent_type"], "financial")
    
    @patch('main.run_financial_agent')
    @patch('main.run_general_agent')
    def test_query_routing_general(self, mock_general_agent, mock_financial_agent):
        """일반 쿼리 라우팅 테스트"""
        # 모의 응답 설정
        mock_financial_agent.return_value = "금융 에이전트 응답"
        mock_general_agent.return_value = "일반 에이전트 응답"
        
        # 일반 쿼리 처리
        query = "내일 일정을 알려줘"
        response = process_query(query, self.test_context)
        
        # 일반 에이전트가 호출되었는지 확인
        mock_general_agent.assert_called_once()
        mock_financial_agent.assert_not_called()
        
        # 응답이 일반 에이전트에서 왔는지 확인
        self.assertEqual(response, "일반 에이전트 응답")
        
        # 컨텍스트가 올바르게 업데이트되었는지 확인
        self.assertEqual(self.test_context["last_agent_type"], "general")
    
    @patch('main.run_financial_agent')
    @patch('main.run_general_agent')
    def test_context_based_routing(self, mock_general_agent, mock_financial_agent):
        """컨텍스트 기반 라우팅 테스트"""
        # 모의 응답 설정
        mock_financial_agent.return_value = "금융 에이전트 응답"
        mock_general_agent.return_value = "일반 에이전트 응답"
        
        # 금융 컨텍스트 설정
        self.test_context["last_agent_type"] = "financial"
        self.test_context["conversation_history"] = [{
            "timestamp": "2025-07-23 12:00:00",
            "query": "지난달 지출 내역을 보여줘",
            "response": "지난달 총 지출은 1,234,567원입니다.",
            "agent_type": "financial"
        }]
        
        # 후속 질문 처리 (금융 키워드 없음)
        query = "그 중에서 가장 큰 금액은 얼마야?"
        response = process_query(query, self.test_context)
        
        # 금융 에이전트가 호출되었는지 확인 (컨텍스트 기반)
        mock_financial_agent.assert_called_once()
        mock_general_agent.assert_not_called()
        
        # 응답이 금융 에이전트에서 왔는지 확인
        self.assertEqual(response, "금융 에이전트 응답")
    
    @patch('main.run_financial_agent')
    @patch('main.run_general_agent')
    def test_explicit_context_switch(self, mock_general_agent, mock_financial_agent):
        """명시적 컨텍스트 전환 테스트"""
        # 모의 응답 설정
        mock_financial_agent.return_value = "금융 에이전트 응답"
        mock_general_agent.return_value = "일반 에이전트 응답"
        
        # 금융 컨텍스트 설정
        self.test_context["last_agent_type"] = "financial"
        self.test_context["conversation_history"] = [{
            "timestamp": "2025-07-23 12:00:00",
            "query": "지난달 지출 내역을 보여줘",
            "response": "지난달 총 지출은 1,234,567원입니다.",
            "agent_type": "financial"
        }]
        
        # 명시적인 일반 쿼리 처리
        query = "내일 일정을 알려줘"
        response = process_query(query, self.test_context)
        
        # 일반 에이전트가 호출되었는지 확인 (명시적 키워드 기반)
        mock_general_agent.assert_called_once()
        mock_financial_agent.assert_not_called()
        
        # 응답이 일반 에이전트에서 왔는지 확인
        self.assertEqual(response, "일반 에이전트 응답")
        
        # 컨텍스트가 올바르게 업데이트되었는지 확인
        self.assertEqual(self.test_context["last_agent_type"], "general")
    
    def test_financial_keyword_detection(self):
        """금융 키워드 감지 테스트"""
        # 금융 관련 쿼리 테스트
        financial_queries = [
            "지난달 지출 내역을 보여줘",
            "이번 달 카드 사용 금액은 얼마야?",
            "지난 3개월 동안의 수입을 분석해줘",
            "식비 카테고리에 얼마나 썼는지 알려줘",
            "어제 만원 넘게 쓴 거래 내역 보여줘"
        ]
        
        # 일반 쿼리 테스트
        general_queries = [
            "오늘 날씨 어때?",
            "내일 일정 알려줘",
            "회의 일정 추가해줘",
            "서울에서 맛집 추천해줘",
            "다음 주 월요일에 미팅 잡아줘"
        ]
        
        # 금융 관련 쿼리 테스트
        for query in financial_queries:
            self.assertTrue(is_financial_query(query), f"금융 쿼리로 감지되어야 함: {query}")
        
        # 일반 쿼리 테스트
        for query in general_queries:
            self.assertFalse(is_financial_query(query), f"일반 쿼리로 감지되어야 함: {query}")
    
    def test_conversation_history_management(self):
        """대화 기록 관리 테스트"""
        # 초기 컨텍스트
        context = self.test_context.copy()
        
        # 대화 기록 추가 (최대 10개)
        for i in range(12):
            query = f"테스트 쿼리 {i}"
            response = f"테스트 응답 {i}"
            update_conversation_history(context, query, response, "general")
        
        # 대화 기록이 최대 10개로 제한되었는지 확인
        self.assertEqual(len(context["conversation_history"]), 10)
        
        # 가장 오래된 대화가 제거되었는지 확인
        self.assertEqual(context["conversation_history"][0]["query"], "테스트 쿼리 2")
        
        # 가장 최근 대화가 추가되었는지 확인
        self.assertEqual(context["conversation_history"][-1]["query"], "테스트 쿼리 11")
        
        # 마지막 쿼리와 응답이 올바르게 저장되었는지 확인
        self.assertEqual(context["last_query"], "테스트 쿼리 11")
        self.assertEqual(context["last_response"], "테스트 응답 11")
        self.assertEqual(context["last_agent_type"], "general")


class TestUserScenarios(unittest.TestCase):
    """사용자 시나리오 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트 컨텍스트 초기화
        self.test_context = {
            "user_name": "강태희",
            "current_time": "2025-07-23 12:00:00",
            "location": "대한민국 서울",
            "conversation_history": []
        }
    
    @patch('src.financial_agent.run_financial_agent')
    def test_scenario_expense_analysis(self, mock_financial_agent):
        """지출 분석 시나리오 테스트"""
        # 모의 응답 설정
        mock_financial_agent.side_effect = [
            "7월 총 지출은 1,234,567원입니다. 주요 카테고리는 식비(30%), 교통(20%), 주거(50%)입니다.",
            "식비 카테고리 지출은 370,370원입니다. 주요 항목은 식당(60%), 카페(25%), 마트(15%)입니다.",
            "지난달 대비 식비 지출이 15% 증가했습니다. 주로 식당 지출이 증가했습니다."
        ]
        
        # 시나리오 1: 월별 지출 분석 요청
        query1 = "이번 달 지출 분석해줘"
        with patch('main.run_financial_agent', mock_financial_agent):
            response1 = process_query(query1, self.test_context)
        
        # 시나리오 2: 특정 카테고리 상세 분석 요청
        query2 = "식비 카테고리 상세 내역 보여줘"
        with patch('main.run_financial_agent', mock_financial_agent):
            response2 = process_query(query2, self.test_context)
        
        # 시나리오 3: 이전 달과 비교 분석 요청
        query3 = "지난달과 비교해서 어떤지 알려줘"
        with patch('main.run_financial_agent', mock_financial_agent):
            response3 = process_query(query3, self.test_context)
        
        # 응답 확인
        self.assertIn("7월 총 지출", response1)
        self.assertIn("식비 카테고리 지출", response2)
        self.assertIn("지난달 대비", response3)
        
        # 금융 에이전트가 3번 호출되었는지 확인
        self.assertEqual(mock_financial_agent.call_count, 3)
    
    @patch('src.financial_agent.run_financial_agent')
    def test_scenario_income_tracking(self, mock_financial_agent):
        """수입 추적 시나리오 테스트"""
        # 모의 응답 설정
        mock_financial_agent.side_effect = [
            "7월 총 수입은 3,000,000원입니다. 주요 수입원은 급여(80%), 부수입(20%)입니다.",
            "수입 대비 지출 비율은 41.2%입니다. 순 현금 흐름은 1,765,433원 흑자입니다.",
            "새로운 수입 거래가 추가되었습니다: 2025-07-23 부수입 150,000원 (프리랜서)"
        ]
        
        # 시나리오 1: 월별 수입 조회
        query1 = "이번 달 수입 내역 보여줘"
        with patch('main.run_financial_agent', mock_financial_agent):
            response1 = process_query(query1, self.test_context)
        
        # 시나리오 2: 수입-지출 비교 분석
        query2 = "수입 대비 지출 비율 알려줘"
        with patch('main.run_financial_agent', mock_financial_agent):
            response2 = process_query(query2, self.test_context)
        
        # 시나리오 3: 새 수입 거래 추가
        query3 = "오늘 프리랜서 수입 15만원 추가해줘"
        with patch('main.run_financial_agent', mock_financial_agent):
            response3 = process_query(query3, self.test_context)
        
        # 응답 확인
        self.assertIn("7월 총 수입", response1)
        self.assertIn("수입 대비 지출 비율", response2)
        self.assertIn("새로운 수입 거래가 추가되었습니다", response3)
        
        # 금융 에이전트가 3번 호출되었는지 확인
        self.assertEqual(mock_financial_agent.call_count, 3)
    
    @patch('src.financial_agent.run_financial_agent')
    @patch('src.general_agent.run_general_agent')
    def test_scenario_mixed_queries(self, mock_general_agent, mock_financial_agent):
        """혼합 쿼리 시나리오 테스트"""
        # 모의 응답 설정
        mock_financial_agent.side_effect = [
            "7월 총 지출은 1,234,567원입니다.",
            "식비 카테고리 지출은 370,370원입니다."
        ]
        mock_general_agent.side_effect = [
            "오늘 일정: 14:00 회의, 16:00 미팅",
            "내일 서울 날씨는 맑음, 기온은 25도입니다."
        ]
        
        # 시나리오 1: 금융 쿼리
        query1 = "이번 달 지출 얼마야?"
        with patch('main.run_financial_agent', mock_financial_agent), patch('main.run_general_agent', mock_general_agent):
            response1 = process_query(query1, self.test_context)
        
        # 시나리오 2: 일반 쿼리 (컨텍스트 전환)
        query2 = "오늘 일정 알려줘"
        with patch('main.run_financial_agent', mock_financial_agent), patch('main.run_general_agent', mock_general_agent):
            response2 = process_query(query2, self.test_context)
        
        # 시나리오 3: 금융 쿼리 (명시적)
        query3 = "식비 얼마나 썼어?"
        with patch('main.run_financial_agent', mock_financial_agent), patch('main.run_general_agent', mock_general_agent):
            response3 = process_query(query3, self.test_context)
        
        # 시나리오 4: 일반 쿼리 (명시적)
        query4 = "내일 날씨 어때?"
        with patch('main.run_financial_agent', mock_financial_agent), patch('main.run_general_agent', mock_general_agent):
            response4 = process_query(query4, self.test_context)
        
        # 응답 확인
        self.assertIn("7월 총 지출", response1)
        self.assertIn("오늘 일정", response2)
        self.assertIn("식비 카테고리 지출", response3)
        self.assertIn("내일 서울 날씨", response4)
        
        # 에이전트 호출 횟수 확인
        self.assertEqual(mock_financial_agent.call_count, 2)
        self.assertEqual(mock_general_agent.call_count, 2)
        
        # 컨텍스트 전환이 올바르게 이루어졌는지 확인
        self.assertEqual(self.test_context["last_agent_type"], "general")


if __name__ == '__main__':
    unittest.main()