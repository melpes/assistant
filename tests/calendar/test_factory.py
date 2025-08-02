"""
캘린더 서비스 팩토리 단위 테스트 (정리된 버전)
"""
import pytest
from unittest.mock import Mock, patch

from src.calendar.factory import CalendarServiceFactory
from src.calendar.service import CalendarService
from src.calendar.providers.google import GoogleCalendarProvider
from src.calendar.auth import GoogleAuthService
from src.calendar.interfaces import CalendarProvider


class TestCalendarServiceFactory:
    """CalendarServiceFactory 클래스 테스트 (실제 구현에 맞춤)"""
    
    def test_providers_mapping_exists(self):
        """프로바이더 매핑이 존재하는지 테스트"""
        assert hasattr(CalendarServiceFactory, '_providers')
        assert 'google' in CalendarServiceFactory._providers
        assert CalendarServiceFactory._providers['google'] == GoogleCalendarProvider
    
    @patch('src.calendar.factory.CALENDAR_CONFIG', {'provider': 'google'})
    @patch('src.calendar.factory.GoogleAuthService')
    def test_create_provider_default_google(self, mock_auth_service):
        """기본 Google 프로바이더 생성 테스트"""
        mock_auth_instance = Mock(spec=GoogleAuthService)
        mock_auth_service.return_value = mock_auth_instance
        
        provider = CalendarServiceFactory.create_provider()
        
        assert isinstance(provider, GoogleCalendarProvider)
        assert provider.auth_service == mock_auth_instance
    
    @patch('src.calendar.factory.GoogleAuthService')
    def test_create_provider_explicit_google(self, mock_auth_service):
        """명시적 Google 프로바이더 생성 테스트"""
        mock_auth_instance = Mock(spec=GoogleAuthService)
        mock_auth_service.return_value = mock_auth_instance
        
        provider = CalendarServiceFactory.create_provider(provider_type='google')
        
        assert isinstance(provider, GoogleCalendarProvider)
    
    @patch('src.calendar.factory.GoogleAuthService')
    def test_create_provider_with_custom_kwargs(self, mock_auth_service):
        """사용자 정의 인자로 프로바이더 생성 테스트"""
        mock_auth_instance = Mock(spec=GoogleAuthService)
        mock_auth_service.return_value = mock_auth_instance
        
        provider = CalendarServiceFactory.create_provider(
            provider_type='google',
            calendar_id='custom-calendar'
        )
        
        assert isinstance(provider, GoogleCalendarProvider)
        assert provider.calendar_id == 'custom-calendar'
    
    def test_create_provider_invalid_type(self):
        """지원하지 않는 프로바이더 유형으로 생성 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="지원하지 않는 캘린더 프로바이더 유형입니다"):
            CalendarServiceFactory.create_provider(provider_type='invalid')
    
    @patch('src.calendar.factory.CALENDAR_CONFIG', {'provider': 'invalid'})
    def test_create_provider_invalid_config(self):
        """설정에 잘못된 프로바이더 유형이 있을 때 예외 발생 테스트"""
        with pytest.raises(ValueError, match="지원하지 않는 캘린더 프로바이더 유형입니다"):
            CalendarServiceFactory.create_provider()
    
    @patch('src.calendar.factory.GoogleAuthService')
    def test_create_service_default(self, mock_auth_service):
        """기본 캘린더 서비스 생성 테스트"""
        mock_auth_instance = Mock(spec=GoogleAuthService)
        mock_auth_service.return_value = mock_auth_instance
        
        service = CalendarServiceFactory.create_service()
        
        assert isinstance(service, CalendarService)
        assert isinstance(service.provider, GoogleCalendarProvider)
    
    @patch('src.calendar.factory.GoogleAuthService')
    def test_create_service_with_provider_type(self, mock_auth_service):
        """특정 프로바이더 유형으로 캘린더 서비스 생성 테스트"""
        mock_auth_instance = Mock(spec=GoogleAuthService)
        mock_auth_service.return_value = mock_auth_instance
        
        service = CalendarServiceFactory.create_service(provider_type='google')
        
        assert isinstance(service, CalendarService)
        assert isinstance(service.provider, GoogleCalendarProvider)
    
    @patch('src.calendar.factory.GoogleAuthService')
    def test_create_service_with_provider_kwargs(self, mock_auth_service):
        """프로바이더 인자와 함께 캘린더 서비스 생성 테스트"""
        mock_auth_instance = Mock(spec=GoogleAuthService)
        mock_auth_service.return_value = mock_auth_instance
        
        service = CalendarServiceFactory.create_service(
            provider_type='google',
            calendar_id='test-calendar'
        )
        
        assert isinstance(service, CalendarService)
        assert service.provider.calendar_id == 'test-calendar'
    
    def test_create_service_invalid_provider_type(self):
        """잘못된 프로바이더 유형으로 서비스 생성 시 예외 발생 테스트"""
        with pytest.raises(ValueError):
            CalendarServiceFactory.create_service(provider_type='invalid')
    
    def test_register_provider(self):
        """새로운 프로바이더 등록 테스트"""
        # 커스텀 프로바이더 클래스 생성
        class CustomProvider(CalendarProvider):
            def list_events(self, start_time, end_time):
                return []
            
            def create_event(self, event):
                return event
            
            def update_event(self, event_id, event):
                return event
            
            def delete_event(self, event_id):
                return True
            
            def get_event(self, event_id):
                return None
        
        # 프로바이더 등록
        CalendarServiceFactory.register_provider('custom', CustomProvider)
        
        # 등록된 프로바이더로 생성 테스트
        provider = CalendarServiceFactory.create_provider(provider_type='custom')
        assert isinstance(provider, CustomProvider)
        
        # 정리
        del CalendarServiceFactory._providers['custom']
    
    @patch('src.calendar.factory.GoogleAuthService')
    def test_create_provider_auth_service_injection(self, mock_auth_service):
        """인증 서비스 주입으로 프로바이더 생성 테스트"""
        custom_auth = Mock(spec=GoogleAuthService)
        
        provider = CalendarServiceFactory.create_provider(
            provider_type='google',
            auth_service=custom_auth
        )
        
        assert isinstance(provider, GoogleCalendarProvider)
        assert provider.auth_service == custom_auth
        # 팩토리에서 새로운 인증 서비스를 생성하지 않았는지 확인
        mock_auth_service.assert_not_called()
    
    @patch('src.calendar.factory.logger')
    @patch('src.calendar.factory.GoogleAuthService')
    def test_logging_on_provider_creation(self, mock_auth_service, mock_logger):
        """프로바이더 생성 시 로깅 테스트"""
        mock_auth_instance = Mock(spec=GoogleAuthService)
        mock_auth_service.return_value = mock_auth_instance
        
        CalendarServiceFactory.create_provider(provider_type='google')
        
        # 로깅이 호출되었는지 확인
        mock_logger.info.assert_called_with("캘린더 프로바이더 생성: google")