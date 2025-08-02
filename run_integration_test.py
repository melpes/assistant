# -*- coding: utf-8 -*-
"""
금융 거래 관리 시스템 통합 테스트 실행 스크립트

전체 시스템의 통합 테스트를 실행합니다.
"""

import unittest
import sys
import os
import logging
from datetime import datetime

# 로그 디렉토리 확인 및 생성
if not os.path.exists("logs"):
    os.makedirs("logs")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_integration_tests():
    """통합 테스트를 실행합니다."""
    logger.info("금융 거래 관리 시스템 통합 테스트 시작")
    
    # 테스트 스위트 생성
    test_suite = unittest.TestSuite()
    
    # 통합 테스트 모듈 추가
    test_loader = unittest.TestLoader()
    
    # 시스템 통합 테스트
    try:
        from tests.test_integration import TestSystemIntegration, TestUserScenarios
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestSystemIntegration))
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestUserScenarios))
        logger.info("시스템 통합 테스트 추가됨")
    except ImportError as e:
        logger.error(f"시스템 통합 테스트 모듈을 가져올 수 없습니다: {e}")
    
    # 성능 테스트
    try:
        from tests.test_performance import TestPerformance, TestOptimization
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestPerformance))
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestOptimization))
        logger.info("성능 테스트 추가됨")
    except ImportError as e:
        logger.error(f"성능 테스트 모듈을 가져올 수 없습니다: {e}")
    
    # 금융 에이전트 테스트
    try:
        from tests.test_financial_agent import TestFinancialAgent
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestFinancialAgent))
        logger.info("금융 에이전트 테스트 추가됨")
    except ImportError as e:
        logger.error(f"금융 에이전트 테스트 모듈을 가져올 수 없습니다: {e}")
    
    # 응답 포맷터 테스트
    try:
        from tests.test_response_formatter import TestResponseFormatter
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestResponseFormatter))
        logger.info("응답 포맷터 테스트 추가됨")
    except ImportError as e:
        logger.error(f"응답 포맷터 테스트 모듈을 가져올 수 없습니다: {e}")
    
    # 에이전트 통합 테스트
    try:
        from tests.test_agent_integration import TestAgentIntegration
        test_suite.addTest(test_loader.loadTestsFromTestCase(TestAgentIntegration))
        logger.info("에이전트 통합 테스트 추가됨")
    except ImportError as e:
        logger.error(f"에이전트 통합 테스트 모듈을 가져올 수 없습니다: {e}")
    
    # 테스트 실행
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)
    
    # 테스트 결과 요약
    logger.info(f"테스트 실행 완료: 총 {test_result.testsRun}개 테스트 실행")
    logger.info(f"성공: {test_result.testsRun - len(test_result.errors) - len(test_result.failures)}개")
    logger.info(f"실패: {len(test_result.failures)}개")
    logger.info(f"오류: {len(test_result.errors)}개")
    
    # 실패한 테스트 목록
    if test_result.failures:
        logger.error("실패한 테스트:")
        for test, error in test_result.failures:
            logger.error(f"- {test}")
    
    # 오류가 발생한 테스트 목록
    if test_result.errors:
        logger.error("오류가 발생한 테스트:")
        for test, error in test_result.errors:
            logger.error(f"- {test}")
    
    # 종료 코드 반환 (실패 또는 오류가 있으면 1, 없으면 0)
    return 1 if test_result.failures or test_result.errors else 0

if __name__ == "__main__":
    exit_code = run_integration_tests()
    sys.exit(exit_code)