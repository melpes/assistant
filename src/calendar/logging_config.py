"""
캘린더 서비스 로깅 설정

이 모듈은 캘린더 서비스의 로깅 설정을 제공합니다.
"""
import os
import logging
from logging.handlers import RotatingFileHandler

from ..config import BASE_DIR


def setup_logging(log_level=logging.INFO):
    """
    캘린더 서비스의 로깅을 설정합니다.
    
    Args:
        log_level: 로그 레벨 (기본값: logging.INFO)
    """
    # 로그 디렉토리 생성
    log_dir = os.path.join(BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 로그 파일 경로
    log_file = os.path.join(log_dir, 'calendar_service.log')
    
    # 로거 설정
    logger = logging.getLogger('src.calendar')
    logger.setLevel(log_level)
    
    # 이미 핸들러가 설정되어 있으면 중복 설정 방지
    if not logger.handlers:
        # 파일 핸들러 설정
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 핸들러 추가
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger