# -*- coding: utf-8 -*-
"""
로깅 시스템

금융 거래 관리 시스템의 로깅 설정 및 유틸리티를 제공합니다.
구조화된 로깅, 로그 레벨 관리, 로그 포맷팅 등의 기능을 지원합니다.
"""

import os
import sys
import logging
import logging.handlers
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from pathlib import Path

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.config_manager import ConfigManager

# 로그 레벨 매핑
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# 기본 로그 디렉토리
DEFAULT_LOG_DIR = os.path.join(parent_dir, 'logs')

# 기본 로그 파일명
DEFAULT_LOG_FILE = 'financial_system.log'

# 기본 로그 포맷
DEFAULT_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

# 기본 콘솔 로그 포맷
DEFAULT_CONSOLE_FORMAT = '%(levelname)s: %(message)s'

class StructuredLogRecord(logging.LogRecord):
    """
    구조화된 로그 레코드 클래스
    
    추가 컨텍스트 정보를 포함하는 로그 레코드입니다.
    """
    
    def __init__(self, *args, **kwargs):
        """
        로그 레코드 초기화
        """
        super().__init__(*args, **kwargs)
        self.context = {}

class StructuredLogger(logging.Logger):
    """
    구조화된 로거 클래스
    
    컨텍스트 정보를 포함하는 로그 메시지를 생성합니다.
    """
    
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        """
        로그 레코드 생성
        
        Args:
            name: 로거 이름
            level: 로그 레벨
            fn: 파일 이름
            lno: 라인 번호
            msg: 로그 메시지
            args: 메시지 인자
            exc_info: 예외 정보
            func: 함수 이름
            extra: 추가 정보
            sinfo: 스택 정보
            
        Returns:
            StructuredLogRecord: 생성된 로그 레코드
        """
        record = StructuredLogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)
        
        if extra:
            for key, value in extra.items():
                if key == 'context':
                    record.context = value
                else:
                    setattr(record, key, value)
        
        return record
    
    def debug(self, msg, *args, **kwargs):
        """
        DEBUG 레벨 로그 메시지 기록
        
        Args:
            msg: 로그 메시지
            *args: 메시지 인자
            **kwargs: 키워드 인자
        """
        context = kwargs.pop('context', {})
        if context:
            kwargs['extra'] = kwargs.get('extra', {})
            kwargs['extra']['context'] = context
        
        super().debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        """
        INFO 레벨 로그 메시지 기록
        
        Args:
            msg: 로그 메시지
            *args: 메시지 인자
            **kwargs: 키워드 인자
        """
        context = kwargs.pop('context', {})
        if context:
            kwargs['extra'] = kwargs.get('extra', {})
            kwargs['extra']['context'] = context
        
        super().info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        """
        WARNING 레벨 로그 메시지 기록
        
        Args:
            msg: 로그 메시지
            *args: 메시지 인자
            **kwargs: 키워드 인자
        """
        context = kwargs.pop('context', {})
        if context:
            kwargs['extra'] = kwargs.get('extra', {})
            kwargs['extra']['context'] = context
        
        super().warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        """
        ERROR 레벨 로그 메시지 기록
        
        Args:
            msg: 로그 메시지
            *args: 메시지 인자
            **kwargs: 키워드 인자
        """
        context = kwargs.pop('context', {})
        if context:
            kwargs['extra'] = kwargs.get('extra', {})
            kwargs['extra']['context'] = context
        
        # 예외 정보 추가
        if 'exc_info' not in kwargs and sys.exc_info()[0] is not None:
            kwargs['exc_info'] = True
        
        super().error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        """
        CRITICAL 레벨 로그 메시지 기록
        
        Args:
            msg: 로그 메시지
            *args: 메시지 인자
            **kwargs: 키워드 인자
        """
        context = kwargs.pop('context', {})
        if context:
            kwargs['extra'] = kwargs.get('extra', {})
            kwargs['extra']['context'] = context
        
        # 예외 정보 추가
        if 'exc_info' not in kwargs and sys.exc_info()[0] is not None:
            kwargs['exc_info'] = True
        
        super().critical(msg, *args, **kwargs)
    
    def exception(self, msg, *args, **kwargs):
        """
        예외 로그 메시지 기록
        
        Args:
            msg: 로그 메시지
            *args: 메시지 인자
            **kwargs: 키워드 인자
        """
        context = kwargs.pop('context', {})
        if context:
            kwargs['extra'] = kwargs.get('extra', {})
            kwargs['extra']['context'] = context
        
        # 예외 정보 추가
        kwargs['exc_info'] = kwargs.get('exc_info', True)
        
        super().error(msg, *args, **kwargs)

class JsonFormatter(logging.Formatter):
    """
    JSON 로그 포맷터 클래스
    
    로그 메시지를 JSON 형식으로 포맷팅합니다.
    """
    
    def __init__(self, fmt=None, datefmt=None, style='%'):
        """
        포맷터 초기화
        
        Args:
            fmt: 로그 포맷
            datefmt: 날짜 포맷
            style: 포맷 스타일
        """
        super().__init__(fmt, datefmt, style)
    
    def format(self, record):
        """
        로그 레코드 포맷팅
        
        Args:
            record: 로그 레코드
            
        Returns:
            str: 포맷팅된 로그 메시지
        """
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 예외 정보 추가
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # 컨텍스트 정보 추가
        if hasattr(record, 'context') and record.context:
            log_data['context'] = record.context
        
        return json.dumps(log_data, ensure_ascii=False)

class LoggingSystem:
    """
    로깅 시스템 클래스
    
    로깅 설정 및 관리를 담당합니다.
    """
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        로깅 시스템 초기화
        
        Args:
            config_manager: 설정 관리자 (기본값: None, 새로 생성)
        """
        self.config_manager = config_manager or ConfigManager()
        
        # 로깅 설정 로드
        self.log_level = self._get_config('system.logging.level', 'INFO')
        self.log_file = self._get_config('system.logging.file_path', os.path.join(DEFAULT_LOG_DIR, DEFAULT_LOG_FILE))
        self.max_size_mb = self._get_config('system.logging.max_size_mb', 10)
        self.backup_count = self._get_config('system.logging.backup_count', 3)
        self.log_format = self._get_config('system.logging.format', DEFAULT_LOG_FORMAT)
        self.console_format = self._get_config('system.logging.console_format', DEFAULT_CONSOLE_FORMAT)
        self.json_logging = self._get_config('system.logging.json_format', False)
        
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(self.log_file)
        os.makedirs(log_dir, exist_ok=True)
        
        # 로거 팩토리 등록
        logging.setLoggerClass(StructuredLogger)
    
    def _get_config(self, key: str, default: Any) -> Any:
        """
        설정 값 조회
        
        Args:
            key: 설정 키
            default: 기본값
            
        Returns:
            Any: 설정 값
        """
        return self.config_manager.get_config_value(key, default)
    
    def setup_logging(self, verbose: bool = False, log_file: str = None, module_levels: Dict[str, str] = None) -> None:
        """
        로깅 설정
        
        Args:
            verbose: 상세 로깅 활성화 여부
            log_file: 로그 파일 경로
            module_levels: 모듈별 로그 레벨 설정
        """
        # 루트 로거 설정
        root_logger = logging.getLogger()
        
        # 로그 레벨 설정
        log_level = logging.DEBUG if verbose else LOG_LEVELS.get(self.log_level, logging.INFO)
        root_logger.setLevel(log_level)
        
        # 기존 핸들러 제거
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        if self.json_logging:
            console_formatter = JsonFormatter()
        else:
            console_formatter = logging.Formatter(self.console_format)
        
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # 파일 핸들러 추가
        file_path = log_file or self.log_file
        
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=self.max_size_mb * 1024 * 1024,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        if self.json_logging:
            file_formatter = JsonFormatter()
        else:
            file_formatter = logging.Formatter(self.log_format)
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # 모듈별 로그 레벨 설정
        if module_levels:
            for module, level in module_levels.items():
                module_logger = logging.getLogger(module)
                module_logger.setLevel(LOG_LEVELS.get(level, logging.INFO))
        
        # 시스템 로거 설정 완료 로그
        system_logger = logging.getLogger('system')
        system_logger.debug("로깅 시스템 설정 완료", context={
            'log_level': logging.getLevelName(log_level),
            'log_file': file_path,
            'json_logging': self.json_logging
        })
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        로거 가져오기
        
        Args:
            name: 로거 이름
            
        Returns:
            logging.Logger: 로거 인스턴스
        """
        return logging.getLogger(name)
    
    def set_level(self, level: Union[str, int], logger_name: str = None) -> None:
        """
        로그 레벨 설정
        
        Args:
            level: 로그 레벨
            logger_name: 로거 이름 (None: 루트 로거)
        """
        if isinstance(level, str):
            level = LOG_LEVELS.get(level.upper(), logging.INFO)
        
        logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
        logger.setLevel(level)
    
    def add_file_handler(self, file_path: str, level: Union[str, int] = None, logger_name: str = None) -> logging.Handler:
        """
        파일 핸들러 추가
        
        Args:
            file_path: 로그 파일 경로
            level: 로그 레벨
            logger_name: 로거 이름 (None: 루트 로거)
            
        Returns:
            logging.Handler: 추가된 핸들러
        """
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # 로그 레벨 설정
        if isinstance(level, str):
            level = LOG_LEVELS.get(level.upper(), logging.INFO)
        elif level is None:
            level = logging.INFO
        
        # 파일 핸들러 생성
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=self.max_size_mb * 1024 * 1024,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        
        if self.json_logging:
            file_formatter = JsonFormatter()
        else:
            file_formatter = logging.Formatter(self.log_format)
        
        file_handler.setFormatter(file_formatter)
        
        # 로거에 핸들러 추가
        logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
        logger.addHandler(file_handler)
        
        return file_handler
    
    def remove_handler(self, handler: logging.Handler, logger_name: str = None) -> None:
        """
        핸들러 제거
        
        Args:
            handler: 제거할 핸들러
            logger_name: 로거 이름 (None: 루트 로거)
        """
        logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
        logger.removeHandler(handler)
    
    def log_exception(self, exc: Exception, logger_name: str = None, level: str = 'ERROR', context: Dict[str, Any] = None) -> None:
        """
        예외 로깅
        
        Args:
            exc: 예외 객체
            logger_name: 로거 이름 (None: 루트 로거)
            level: 로그 레벨
            context: 컨텍스트 정보
        """
        logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
        
        log_level = LOG_LEVELS.get(level.upper(), logging.ERROR)
        
        # 예외 정보 로깅
        logger.log(log_level, f"{exc.__class__.__name__}: {str(exc)}", exc_info=True, context=context)
    
    def get_log_files(self) -> List[str]:
        """
        로그 파일 목록 조회
        
        Returns:
            List[str]: 로그 파일 경로 목록
        """
        log_dir = os.path.dirname(self.log_file)
        if not os.path.exists(log_dir):
            return []
        
        log_files = []
        base_name = os.path.basename(self.log_file)
        
        for file in os.listdir(log_dir):
            if file == base_name or file.startswith(f"{base_name}."):
                log_files.append(os.path.join(log_dir, file))
        
        return log_files
    
    def clear_logs(self) -> None:
        """
        로그 파일 정리
        """
        log_files = self.get_log_files()
        
        for file in log_files:
            try:
                os.remove(file)
            except Exception as e:
                logging.getLogger('system').error(f"로그 파일 삭제 중 오류 발생: {e}", exc_info=True)

# 전역 로깅 시스템 인스턴스
_logging_system = None

def get_logging_system() -> LoggingSystem:
    """
    로깅 시스템 인스턴스 가져오기
    
    Returns:
        LoggingSystem: 로깅 시스템 인스턴스
    """
    global _logging_system
    
    if _logging_system is None:
        _logging_system = LoggingSystem()
    
    return _logging_system

def setup_logging(verbose: bool = False, log_file: str = None, module_levels: Dict[str, str] = None) -> None:
    """
    로깅 설정
    
    Args:
        verbose: 상세 로깅 활성화 여부
        log_file: 로그 파일 경로
        module_levels: 모듈별 로그 레벨 설정
    """
    logging_system = get_logging_system()
    logging_system.setup_logging(verbose, log_file, module_levels)

def get_logger(name: str) -> logging.Logger:
    """
    로거 가져오기
    
    Args:
        name: 로거 이름
        
    Returns:
        logging.Logger: 로거 인스턴스
    """
    return logging.getLogger(name)

def log_exception(exc: Exception, logger_name: str = None, level: str = 'ERROR', context: Dict[str, Any] = None) -> None:
    """
    예외 로깅
    
    Args:
        exc: 예외 객체
        logger_name: 로거 이름 (None: 루트 로거)
        level: 로그 레벨
        context: 컨텍스트 정보
    """
    logging_system = get_logging_system()
    logging_system.log_exception(exc, logger_name, level, context)

def set_level(level: Union[str, int], logger_name: str = None) -> None:
    """
    로그 레벨 설정
    
    Args:
        level: 로그 레벨
        logger_name: 로거 이름 (None: 루트 로거)
    """
    logging_system = get_logging_system()
    logging_system.set_level(level, logger_name)

def add_file_handler(file_path: str, level: Union[str, int] = None, logger_name: str = None) -> logging.Handler:
    """
    파일 핸들러 추가
    
    Args:
        file_path: 로그 파일 경로
        level: 로그 레벨
        logger_name: 로거 이름 (None: 루트 로거)
        
    Returns:
        logging.Handler: 추가된 핸들러
    """
    logging_system = get_logging_system()
    return logging_system.add_file_handler(file_path, level, logger_name)

def remove_handler(handler: logging.Handler, logger_name: str = None) -> None:
    """
    핸들러 제거
    
    Args:
        handler: 제거할 핸들러
        logger_name: 로거 이름 (None: 루트 로거)
    """
    logging_system = get_logging_system()
    logging_system.remove_handler(handler, logger_name)

def get_log_files() -> List[str]:
    """
    로그 파일 목록 조회
    
    Returns:
        List[str]: 로그 파일 경로 목록
    """
    logging_system = get_logging_system()
    return logging_system.get_log_files()

def clear_logs() -> None:
    """
    로그 파일 정리
    """
    logging_system = get_logging_system()
    logging_system.clear_logs()