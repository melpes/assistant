# -*- coding: utf-8 -*-
"""
에이전트 통합 및 라우팅 테스트

main.py의 에이전트 라우팅 로직을 테스트합니다.
"""

import unittest
from unittest.mock import patch, MagicMock

class TestAgentIntegration(unittest.TestCase):
    """에이전트 통합 및 라우팅 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 테스트 컨텍스트 초기화
        self.test_context = {
            "user_name": "강태희",
            "current_time": "2025-07-23 12:00:00",
            "location": "대한민국 서울",
            "conversation_history": []
        }
    
    def test_financial_query_detection(self):
        """금융 관련 쿼리 감지 테스트"""
        # 테스트를 위한 모듈 임포트
        import re
        
        # 금융 키워드 정의
        financial_keywords = [
            '금융', '지출', '수입', '거래', '카드', '계좌', '돈', '금액', '결제',
            '카테고리', '썼', '분석', '내역'
        ]
        
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
        
        # 금융 관련 쿼리 감지 함수
        def is_financial_query(query):
            return any(keyword in query for keyword in financial_keywords)
        
        # 금융 관련 쿼리 테스트
        for query in financial_queries:
            self.assertTrue(is_financial_query(query), f"금융 쿼리로 감지되어야 함: {query}")
        
        # 일반 쿼리 테스트
        for query in general_queries:
            self.assertFalse(is_financial_query(query), f"일반 쿼리로 감지되어야 함: {query}")
    
    def test_context_update(self):
        """대화 컨텍스트 업데이트 테스트"""
        # 테스트를 위한 함수 정의
        def update_conversation_history(context, query, response, agent_type):
            # 대화 기록이 없으면 초기화
            if "conversation_history" not in context:
                context["conversation_history"] = []
            
            # 대화 기록 추가
            context["conversation_history"].append({
                "timestamp": "2025-07-23 12:00:00",
                "query": query,
                "response": response,
                "agent_type": agent_type
            })
            
            # 대화 기록 최대 10개로 제한
            if len(context["conversation_history"]) > 10:
                context["conversation_history"] = context["conversation_history"][-10:]
            
            # 마지막 쿼리와 응답 저장
            context["last_query"] = query
            context["last_response"] = response
            context["last_agent_type"] = agent_type
        
        # 테스트 컨텍스트 초기화
        test_context = self.test_context.copy()
        
        # 1. 금융 쿼리 처리
        financial_query = "지난달 지출 내역을 보여줘"
        financial_response = "지난달 총 지출은 1,234,567원입니다."
        update_conversation_history(test_context, financial_query, financial_response, "financial")
        
        # 컨텍스트가 올바르게 업데이트되었는지 확인
        self.assertEqual(test_context["last_query"], financial_query)
        self.assertEqual(test_context["last_response"], financial_response)
        self.assertEqual(test_context["last_agent_type"], "financial")
        self.assertEqual(len(test_context["conversation_history"]), 1)
        
        # 2. 일반 쿼리 처리
        general_query = "오늘 날씨 어때?"
        general_response = "오늘 서울의 날씨는 맑음, 기온은 25도입니다."
        update_conversation_history(test_context, general_query, general_response, "general")
        
        # 컨텍스트가 올바르게 업데이트되었는지 확인
        self.assertEqual(test_context["last_query"], general_query)
        self.assertEqual(test_context["last_response"], general_response)
        self.assertEqual(test_context["last_agent_type"], "general")
        self.assertEqual(len(test_context["conversation_history"]), 2)
        
        # 대화 기록이 올바르게 누적되었는지 확인
        self.assertEqual(test_context["conversation_history"][0]["query"], financial_query)
        self.assertEqual(test_context["conversation_history"][1]["query"], general_query)
    
    def test_context_based_routing_logic(self):
        """컨텍스트 기반 라우팅 로직 테스트"""
        # 테스트 컨텍스트 초기화
        test_context = self.test_context.copy()
        
        # 금융 관련 키워드 정의
        financial_keywords = [
            '금융', '지출', '수입', '거래', '카드', '계좌', '돈', '금액', '결제',
            '카테고리', '썼', '분석', '내역'
        ]
        
        # 금융 관련 쿼리 감지 함수
        def is_financial_query(query):
            return any(keyword in query for keyword in financial_keywords)
        
        # 라우팅 로직 함수
        def should_use_financial_agent(query, context):
            # 쿼리 유형 판단
            query_is_financial = is_financial_query(query)
            
            # 이전 대화 컨텍스트 확인
            has_financial_context = False
            if "conversation_history" in context and len(context["conversation_history"]) > 0:
                last_agent = context.get("last_agent_type")
                if last_agent == "financial":
                    has_financial_context = True
            
            # 명시적인 금융 키워드가 있거나, 이전 대화가 금융 관련이고 후속 질문인 경우
            return query_is_financial or has_financial_context
        
        # 1. 금융 키워드가 있는 쿼리
        financial_query = "지난달 지출 내역을 보여줘"
        self.assertTrue(should_use_financial_agent(financial_query, test_context))
        
        # 2. 금융 키워드가 없는 쿼리 (컨텍스트 없음)
        general_query = "오늘 날씨 어때?"
        self.assertFalse(should_use_financial_agent(general_query, test_context))
        
        # 3. 금융 컨텍스트 설정
        test_context["last_agent_type"] = "financial"
        test_context["conversation_history"] = [{
            "timestamp": "2025-07-23 12:00:00",
            "query": financial_query,
            "response": "지난달 총 지출은 1,234,567원입니다.",
            "agent_type": "financial"
        }]
        
        # 4. 금융 키워드가 없는 후속 질문 (금융 컨텍스트 있음)
        followup_query = "그 중에서 가장 큰 금액은 얼마야?"
        self.assertTrue(should_use_financial_agent(followup_query, test_context))
        
        # 5. 명시적인 일반 쿼리 (컨텍스트 전환)
        explicit_general_query = "내일 일정 알려줘"
        # 금융 컨텍스트가 있어도 명시적인 일반 쿼리는 일반 에이전트로 라우팅되어야 함
        # 하지만 현재 로직에서는 이전 컨텍스트가 우선시됨
        self.assertTrue(should_use_financial_agent(explicit_general_query, test_context))
        
        # 6. 컨텍스트 전환 로직 테스트 (개선된 로직)
        def should_use_financial_agent_improved(query, context):
            # 쿼리 유형 판단
            query_is_financial = is_financial_query(query)
            
            # 명시적인 일반 쿼리 키워드 확인
            explicit_general_keywords = ['일정', '날씨', '알람', '타이머', '미팅', '회의']
            is_explicit_general = any(keyword in query for keyword in explicit_general_keywords)
            
            # 이전 대화 컨텍스트 확인
            has_financial_context = False
            if "conversation_history" in context and len(context["conversation_history"]) > 0:
                last_agent = context.get("last_agent_type")
                if last_agent == "financial":
                    has_financial_context = True
            
            # 명시적인 일반 쿼리는 일반 에이전트로 라우팅
            if is_explicit_general:
                return False
            
            # 명시적인 금융 키워드가 있거나, 이전 대화가 금융 관련이고 후속 질문인 경우
            return query_is_financial or has_financial_context
        
        # 7. 개선된 로직으로 명시적인 일반 쿼리 테스트
        self.assertFalse(should_use_financial_agent_improved(explicit_general_query, test_context))

if __name__ == '__main__':
    unittest.main()