"""
Gmail API 연동 및 인증 모듈

이 패키지는 Gmail API를 사용하여 이메일에 접근하기 위한 인증 시스템을 제공합니다.
"""

from .auth import GmailAuthService
from .service import GmailServiceManager
from .processor import EmailProcessor

__all__ = [
    "GmailAuthService",
    "GmailServiceManager", 
    "EmailProcessor"
]