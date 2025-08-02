"""
캘린더 서비스 팩토리

이 모듈은 설정에 기반하여 적절한 캘린더 제공자와 서비스를 생성하는 팩토리 클래스를 제공합니다.
"""
import logging
from typing import Dict, Any, Optional, Type

from .interfaces import CalendarProvider
from .service import CalendarService
from .auth import GoogleAuthService
from .providers.google import GoogleCalendarProvider
from ..config import CALENDAR_CONFIG

# 로깅 설정
logger = logging.getLogger(__name__)


class CalendarServiceFactory:
    """
    캘린더 서비스 팩토리 클래스
    
    설정에 기반하여 적절한 캘린더 제공자와 서비스를 생성합니다.
    """
    
    # 사용 가능한 프로바이더 매핑
    _providers = {
        "google": GoogleCalendarProvider
    }
    
    @classmethod
    def create_provider(cls, provider_type: str = None, **kwargs) -> CalendarProvider:
        """
        설정에 기반하여 캘린더 제공자를 생성합니다.
        
        Args:
            provider_type: 프로바이더 유형 (기본값: 설정에서 가져옴)
            **kwargs: 프로바이더 생성자에 전달할 추가 인자
            
        Returns:
            CalendarProvider 인스턴스
            
        Raises:
            ValueError: 지원하지 않는 프로바이더 유형인 경우
        """
        # 프로바이더 유형이 지정되지 않은 경우 설정에서 가져옴
        if provider_type is None:
            provider_type = CALENDAR_CONFIG.get("provider", "google")
        
        # 프로바이더 클래스 가져오기
        provider_class = cls._providers.get(provider_type.lower())
        if not provider_class:
            supported = ", ".join(cls._providers.keys())
            raise ValueError(
                f"지원하지 않는 캘린더 프로바이더 유형입니다: {provider_type}. "
                f"지원되는 유형: {supported}"
            )
        
        logger.info(f"캘린더 프로바이더 생성: {provider_type}")
        
        # 프로바이더 유형별 초기화 로직
        if provider_type.lower() == "google":
            # Google 프로바이더의 경우 인증 서비스 생성
            auth_service = kwargs.get("auth_service")
            if not auth_service:
                auth_kwargs = {}
                
                # 설정에서 인증 관련 옵션 가져오기
                if "auth" in CALENDAR_CONFIG:
                    auth_config = CALENDAR_CONFIG["auth"]
                    if "token_path" in auth_config:
                        auth_kwargs["token_path"] = auth_config["token_path"]
                    if "credentials_path" in auth_config:
                        auth_kwargs["credentials_path"] = auth_config["credentials_path"]
                    if "scopes" in auth_config:
                        auth_kwargs["scopes"] = auth_config["scopes"]
                
                auth_service = GoogleAuthService(**auth_kwargs)
                kwargs["auth_service"] = auth_service
            
            # 캘린더 ID 설정
            if "calendar_id" not in kwargs and "calendar_id" in CALENDAR_CONFIG:
                kwargs["calendar_id"] = CALENDAR_CONFIG["calendar_id"]
        
        # 프로바이더 인스턴스 생성 및 반환
        return provider_class(**kwargs)
    
    @classmethod
    def create_service(cls, provider_type: str = None, **kwargs) -> CalendarService:
        """
        설정에 기반하여 캘린더 서비스를 생성합니다.
        
        Args:
            provider_type: 프로바이더 유형 (기본값: 설정에서 가져옴)
            **kwargs: 프로바이더 생성자에 전달할 추가 인자
            
        Returns:
            CalendarService 인스턴스
        """
        # 프로바이더 생성
        provider = kwargs.pop("provider", None)
        if not provider:
            provider = cls.create_provider(provider_type, **kwargs)
        
        logger.info("캘린더 서비스 생성")
        
        # 서비스 인스턴스 생성 및 반환
        return CalendarService(provider)
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[CalendarProvider]) -> None:
        """
        새로운 프로바이더 유형을 등록합니다.
        
        Args:
            name: 프로바이더 이름
            provider_class: CalendarProvider 구현 클래스
        """
        cls._providers[name.lower()] = provider_class
        logger.info(f"새로운 캘린더 프로바이더 등록됨: {name}")