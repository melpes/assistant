# -*- coding: utf-8 -*-
"""
로깅 시스템 테스트

로깅 시스템의 기능을 테스트합니다.
"""

import os
import sys
import unittest
import logging
import json
import tempfile
import shutil
from pathlib import Path

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.logging_system import (
    LoggingSystem, StructuredLogger, JsonFormatter,
    setup_logging, get_logger, log_exception, set_level,
    add_file_handler, remove_handler, get_log_files, clear_logs
)
from src.exceptions import FinancialSystemError

class TestLoggingSystem(unittest.TestCase):
    """
    로깅 시스템 테스트 클래스
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, 'test.log')
        
        # 기존 로거 초기화
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    def tearDown(self):
        """
        테스트 정리
        """
        # 임시 디렉토리 삭제
        shutil.rmtree(self.temp_dir)
    
    def test_logging_system_init(self):
        """
        로깅 시스템 초기화 테스트
        """
        # 로깅 시스템 초기화
        logging_system = LoggingSystem()
        
        # 기본 설정 확인
        self.assertIsNotNone(logging_system.log_level)
        self.assertIsNotNone(logging_system.log_file)
        self.assertIsNotNone(logging_system.max_size_mb)
        self.assertIsNotNone(logging_system.backup_count)
        self.assertIsNotNone(logging_system.log_format)
        self.assertIsNotNone(logging_system.console_format)
    
    def test_setup_logging(self):
        """
        로깅 설정 테스트
        """
        # 로깅 시스템 초기화
        logging_system = LoggingSystem()
        
        # 로깅 설정
        logging_system.setup_logging(verbose=True, log_file=self.log_file)
        
        # 루트 로거 확인
        root_logger = logging.getLogger()
        self.assertEqual(root_logger.level, logging.DEBUG)
        self.assertEqual(len(root_logger.handlers), 2)  # 콘솔 + 파일
        
        # 로그 파일 생성 확인
        self.assertTrue(os.path.exists(self.log_file))
    
    def test_get_logger(self):
        """
        로거 가져오기 테스트
        """
        # 로깅 시스템 초기화
        logging_system = LoggingSystem()
        
        # 로깅 설정
        logging_system.setup_logging(log_file=self.log_file)
        
        # 로거 가져오기
        logger = logging_system.get_logger('test')
        
        # 로거 확인
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'test')
        
        # 구조화된 로거 확인
        self.assertIsInstance(logger, StructuredLogger)
    
    def test_log_messages(self):
        """
        로그 메시지 테스트
        """
        # 로깅 시스템 초기화
        logging_system = LoggingSystem()
        
        # 로깅 설정
        logging_system.setup_logging(log_file=self.log_file)
        
        # 로거 가져오기
        logger = logging_system.get_logger('test')
        
        # 로그 메시지 기록
        logger.debug("디버그 메시지")
        logger.info("정보 메시지")
        logger.warning("경고 메시지")
        logger.error("오류 메시지")
        
        # 로그 파일 확인
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 로그 메시지 확인
        self.assertIn("정보 메시지", log_content)
        self.assertIn("경고 메시지", log_content)
        self.assertIn("오류 메시지", log_content)
    
    def test_structured_logging(self):
        """
        구조화된 로깅 테스트
        """
        # 로깅 시스템 초기화
        logging_system = LoggingSystem()
        
        # 로깅 설정
        logging_system.setup_logging(log_file=self.log_file)
        
        # 로거 가져오기
        logger = logging_system.get_logger('test')
        
        # 컨텍스트 정보와 함께 로그 메시지 기록
        context = {'user_id': 123, 'action': 'login'}
        logger.info("사용자 로그인", context=context)
        
        # 로그 파일 확인
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 로그 메시지 확인
        self.assertIn("사용자 로그인", log_content)
    
    def test_json_formatter(self):
        """
        JSON 포맷터 테스트
        """
        # JSON 포맷터 생성
        formatter = JsonFormatter()
        
        # 로그 레코드 생성
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname=__file__,
            lineno=100,
            msg='테스트 메시지',
            args=(),
            exc_info=None
        )
        
        # 로그 레코드 포맷팅
        formatted = formatter.format(record)
        
        # JSON 파싱
        log_data = json.loads(formatted)
        
        # 필드 확인
        self.assertEqual(log_data['level'], 'INFO')
        self.assertEqual(log_data['logger'], 'test')
        self.assertEqual(log_data['message'], '테스트 메시지')
    
    def test_log_exception(self):
        """
        예외 로깅 테스트
        """
        # 로깅 시스템 초기화
        logging_system = LoggingSystem()
        
        # 로깅 설정
        logging_system.setup_logging(log_file=self.log_file)
        
        # 예외 생성
        exc = FinancialSystemError("테스트 예외")
        
        # 예외 로깅
        logging_system.log_exception(exc, 'test')
        
        # 로그 파일 확인
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 로그 메시지 확인
        self.assertIn("FinancialSystemError: 테스트 예외", log_content)
    
    def test_set_level(self):
        """
        로그 레벨 설정 테스트
        """
        # 로깅 시스템 초기화
        logging_system = LoggingSystem()
        
        # 로깅 설정
        logging_system.setup_logging(log_file=self.log_file)
        
        # 로거 가져오기
        logger = logging_system.get_logger('test')
        
        # 로그 레벨 설정
        logging_system.set_level('WARNING', 'test')
        
        # 로그 레벨 확인
        self.assertEqual(logger.level, logging.WARNING)
        
        # 로그 메시지 기록
        logger.debug("디버그 메시지")
        logger.info("정보 메시지")
        logger.warning("경고 메시지")
        
        # 로그 파일 확인
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 로그 메시지 확인
        self.assertNotIn("디버그 메시지", log_content)
        self.assertNotIn("정보 메시지", log_content)
        self.assertIn("경고 메시지", log_content)
    
    def test_add_file_handler(self):
        """
        파일 핸들러 추가 테스트
        """
        # 로깅 시스템 초기화
        logging_system = LoggingSystem()
        
        # 로깅 설정
        logging_system.setup_logging()
        
        # 로거 가져오기
        logger = logging_system.get_logger('test')
        
        # 파일 핸들러 추가
        second_log_file = os.path.join(self.temp_dir, 'second.log')
        handler = logging_system.add_file_handler(second_log_file, 'DEBUG', 'test')
        
        # 로그 메시지 기록
        logger.debug("디버그 메시지")
        
        # 로그 파일 확인
        with open(second_log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 로그 메시지 확인
        self.assertIn("디버그 메시지", log_content)
        
        # 핸들러 제거
        logging_system.remove_handler(handler, 'test')
    
    def test_get_log_files(self):
        """
        로그 파일 목록 조회 테스트
        """
        # 로깅 시스템 초기화
        logging_system = LoggingSystem()
        logging_system.log_file = self.log_file
        
        # 로그 파일 생성
        with open(self.log_file, 'w') as f:
            f.write("테스트 로그")
        
        with open(f"{self.log_file}.1", 'w') as f:
            f.write("테스트 로그 백업 1")
        
        # 로그 파일 목록 조회
        log_files = logging_system.get_log_files()
        
        # 로그 파일 확인
        self.assertEqual(len(log_files), 2)
        self.assertIn(self.log_file, log_files)
        self.assertIn(f"{self.log_file}.1", log_files)
    
    def test_clear_logs(self):
        """
        로그 파일 정리 테스트
        """
        # 로깅 시스템 초기화
        logging_system = LoggingSystem()
        logging_system.log_file = self.log_file
        
        # 로그 파일 생성
        with open(self.log_file, 'w') as f:
            f.write("테스트 로그")
        
        with open(f"{self.log_file}.1", 'w') as f:
            f.write("테스트 로그 백업 1")
        
        # 로그 파일 정리
        logging_system.clear_logs()
        
        # 로그 파일 확인
        self.assertFalse(os.path.exists(self.log_file))
        self.assertFalse(os.path.exists(f"{self.log_file}.1"))
    
    def test_module_functions(self):
        """
        모듈 함수 테스트
        """
        # 로깅 설정
        setup_logging(log_file=self.log_file)
        
        # 로거 가져오기
        logger = get_logger('test')
        
        # 로그 메시지 기록
        logger.info("모듈 함수 테스트")
        
        # 로그 파일 확인
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        # 로그 메시지 확인
        self.assertIn("모듈 함수 테스트", log_content)
        
        # 로그 레벨 설정
        set_level('WARNING', 'test')
        self.assertEqual(logger.level, logging.WARNING)
        
        # 예외 로깅
        exc = FinancialSystemError("모듈 함수 예외")
        log_exception(exc, 'test')
        
        # 로그 파일 목록 조회
        log_files = get_log_files()
        self.assertIn(self.log_file, log_files)
        
        # 파일 핸들러 추가
        second_log_file = os.path.join(self.temp_dir, 'second.log')
        handler = add_file_handler(second_log_file, 'DEBUG', 'test')
        
        # 핸들러 제거
        remove_handler(handler, 'test')
        
        # 로그 파일 정리
        clear_logs()

if __name__ == '__main__':
    unittest.main()