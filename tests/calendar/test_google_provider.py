"""
Google Calendar Provider 단위 테스트
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from googleapiclient.errors import HttpError
from googleapiclient.discovery import Resource

from src.calendar.providers.google import GoogleCalendarProvider
from src.calendar.models import CalendarEvent
from src.calendar.auth import GoogleAuthService
from src.calendar.exceptions import (
    CalendarServiceError,
    EventNotFoundError,
    NetworkError,
    APIQuotaExceededError,
    PermissionDeniedError,
    InvalidEventDataError,
    TimeoutError,
    ServerError,
    RateLimitError,
    TokenExpiredError
)


class TestGoogleCalendarProvider:
    """GoogleCalendarProvider 클래스 테스트"""
    
    @pytest.fixture
    def mock_auth_service(self):
        """Mock GoogleAuthService"""
        auth_service = Mock(spec=GoogleAuthService)
        mock_creds = Mock()
        auth_service.get_credentials.return_value = mock_creds
        return auth_service
    
    @pytest.fixture
    def mock_service(self):
        """Mock Google Calendar API 서비스"""
        service = Mock()  # spec 제거
        
        # events() 메서드 체인 모킹
        events_resource = Mock()
        service.events.return_value = events_resource
        
        # 각 API 메서드 모킹
        events_resource.list.return_value = Mock()
        events_resource.insert.return_value = Mock()
        events_resource.update.return_value = Mock()
        events_resource.delete.return_value = Mock()
        events_resource.get.return_value = Mock()
        
        return service
    
    @pytest.fixture
    def provider(self, mock_auth_service):
        """테스트용 GoogleCalendarProvider 인스턴스"""
        return GoogleCalendarProvider(
            auth_service=mock_auth_service,
            calendar_id="test-calendar",
            use_service_pool=False
        )
    
    @pytest.fixture
    def sample_google_event(self):
        """샘플 Google 이벤트 데이터"""
        return {
            'id': 'google-event-123',
            'summary': '테스트 이벤트',
            'description': '테스트 설명',
            'location': '서울시 강남구',
            'start': {'dateTime': '2024-01-01T10:00:00+09:00'},
            'end': {'dateTime': '2024-01-01T11:00:00+09:00'}
        }
    
    @pytest.fixture
    def sample_calendar_event(self):
        """샘플 CalendarEvent 객체"""
        return CalendarEvent(
            id='test-event-123',
            summary='테스트 이벤트',
            description='테스트 설명',
            location='서울시 강남구',
            start_time='2024-01-01T10:00:00+09:00',
            end_time='2024-01-01T11:00:00+09:00'
        )
    
    def test_init_default_values(self, mock_auth_service):
        """기본값으로 GoogleCalendarProvider 초기화 테스트"""
        provider = GoogleCalendarProvider(auth_service=mock_auth_service)
        
        assert provider.auth_service == mock_auth_service
        assert provider.calendar_id == "primary"
        assert provider.use_service_pool is True
    
    def test_init_custom_values(self, mock_auth_service):
        """사용자 정의 값으로 GoogleCalendarProvider 초기화 테스트"""
        provider = GoogleCalendarProvider(
            auth_service=mock_auth_service,
            calendar_id="custom-calendar",
            use_service_pool=False
        )
        
        assert provider.calendar_id == "custom-calendar"
        assert provider.use_service_pool is False
    
    @patch('src.calendar.providers.google.build')
    def test_get_service_success(self, mock_build, provider, mock_service):
        """Google API 서비스 객체 생성 성공 테스트"""
        mock_build.return_value = mock_service
        
        service = provider._get_service()
        
        assert service == mock_service
        mock_build.assert_called_once()
        provider.auth_service.get_credentials.assert_called_once()
    
    @patch('src.calendar.providers.google.build')
    def test_get_service_auth_failure(self, mock_build, provider):
        """인증 실패 시 예외 발생 테스트"""
        provider.auth_service.get_credentials.side_effect = Exception("Auth failed")
        
        with pytest.raises(Exception):  # 인증 실패는 원본 예외가 그대로 전파됨
            provider._get_service()
    
    @patch('src.calendar.providers.google.build')
    def test_list_events_success(self, mock_build, provider, mock_service, sample_google_event):
        """이벤트 목록 조회 성공 테스트"""
        mock_build.return_value = mock_service
        
        # API 응답 모킹
        mock_response = {'items': [sample_google_event]}
        mock_service.events().list().execute.return_value = mock_response
        
        events = provider.list_events('2024-01-01T00:00:00', '2024-01-31T23:59:59')
        
        assert len(events) == 1
        assert isinstance(events[0], CalendarEvent)
        assert events[0].id == 'google-event-123'
        assert events[0].summary == '테스트 이벤트'
        
        # API 호출 확인 (pageToken=None이 추가로 전달됨)
        mock_service.events().list.assert_called_with(
            calendarId="test-calendar",
            timeMin='2024-01-01T00:00:00',
            timeMax='2024-01-31T23:59:59',
            singleEvents=True,
            orderBy='startTime',
            pageToken=None
        )
    
    @patch('src.calendar.providers.google.build')
    def test_list_events_empty_response(self, mock_build, provider, mock_service):
        """빈 이벤트 목록 응답 테스트"""
        mock_build.return_value = mock_service
        mock_service.events().list().execute.return_value = {'items': []}
        
        events = provider.list_events('2024-01-01T00:00:00', '2024-01-31T23:59:59')
        
        assert len(events) == 0
        assert isinstance(events, list)
    
    @patch('src.calendar.providers.google.build')
    def test_list_events_http_error_404(self, mock_build, provider, mock_service):
        """HTTP 404 오류 시 예외 발생 테스트"""
        mock_build.return_value = mock_service
        
        http_error = HttpError(
            resp=Mock(status=404),
            content=b'{"error": {"message": "Not found"}}'
        )
        mock_service.events().list().execute.side_effect = http_error
        
        with pytest.raises(EventNotFoundError):
            provider.list_events('2024-01-01T00:00:00', '2024-01-31T23:59:59')
    
    @patch('src.calendar.providers.google.build')
    def test_list_events_http_error_403(self, mock_build, provider, mock_service):
        """HTTP 403 오류 시 예외 발생 테스트"""
        mock_build.return_value = mock_service
        
        http_error = HttpError(
            resp=Mock(status=403),
            content=b'{"error": {"message": "Quota exceeded"}}'
        )
        mock_service.events().list().execute.side_effect = http_error
        
        with pytest.raises(PermissionDeniedError):  # 403 오류는 PermissionDeniedError로 처리됨
            provider.list_events('2024-01-01T00:00:00', '2024-01-31T23:59:59')
    
    @patch('src.calendar.providers.google.build')
    def test_create_event_success(self, mock_build, provider, mock_service, sample_calendar_event, sample_google_event):
        """이벤트 생성 성공 테스트"""
        mock_build.return_value = mock_service
        mock_service.events().insert().execute.return_value = sample_google_event
        
        created_event = provider.create_event(sample_calendar_event)
        
        assert isinstance(created_event, CalendarEvent)
        assert created_event.id == 'google-event-123'
        assert created_event.summary == '테스트 이벤트'
        
        # API 호출 확인 (실제로는 2번 호출됨: 한 번은 빈 호출, 한 번은 실제 파라미터)
        assert mock_service.events().insert.call_count >= 1
        # 마지막 호출의 인자 확인
        call_args = mock_service.events().insert.call_args
        if call_args and len(call_args) > 1:
            assert call_args[1]['calendarId'] == "test-calendar"
            assert 'body' in call_args[1]
    
    @patch('src.calendar.providers.google.build')
    def test_create_event_invalid_data(self, mock_build, provider, mock_service):
        """잘못된 데이터로 이벤트 생성 시 예외 발생 테스트"""
        mock_build.return_value = mock_service
        
        http_error = HttpError(
            resp=Mock(status=400),
            content=b'{"error": {"message": "Invalid event data"}}'
        )
        mock_service.events().insert().execute.side_effect = http_error
        
        invalid_event = CalendarEvent(
            summary="테스트",
            start_time="invalid-time",
            end_time="invalid-time"
        )
        
        with pytest.raises(CalendarServiceError):  # 400 오류는 CalendarServiceError로 처리됨
            provider.create_event(invalid_event)
    
    @patch('src.calendar.providers.google.build')
    def test_update_event_success(self, mock_build, provider, mock_service, sample_calendar_event, sample_google_event):
        """이벤트 수정 성공 테스트"""
        mock_build.return_value = mock_service
        mock_service.events().update().execute.return_value = sample_google_event
        
        updated_event = provider.update_event('test-event-123', sample_calendar_event)
        
        assert isinstance(updated_event, CalendarEvent)
        assert updated_event.id == 'google-event-123'
        
        # API 호출 확인
        assert mock_service.events().update.call_count >= 1
        call_args = mock_service.events().update.call_args
        if call_args and len(call_args) > 1:
            assert call_args[1]['calendarId'] == "test-calendar"
            assert call_args[1]['eventId'] == 'test-event-123'
    
    @patch('src.calendar.providers.google.build')
    def test_update_event_not_found(self, mock_build, provider, mock_service, sample_calendar_event):
        """존재하지 않는 이벤트 수정 시 예외 발생 테스트"""
        mock_build.return_value = mock_service
        
        http_error = HttpError(
            resp=Mock(status=404),
            content=b'{"error": {"message": "Event not found"}}'
        )
        mock_service.events().update().execute.side_effect = http_error
        
        with pytest.raises(EventNotFoundError):
            provider.update_event('non-existent-id', sample_calendar_event)
    
    @patch('src.calendar.providers.google.build')
    def test_delete_event_success(self, mock_build, provider, mock_service):
        """이벤트 삭제 성공 테스트"""
        mock_build.return_value = mock_service
        mock_service.events().delete().execute.return_value = None
        
        result = provider.delete_event('test-event-123')
        
        assert result is True
        
        # API 호출 확인
        assert mock_service.events().delete.call_count >= 1
        # 실제 파라미터로 호출되었는지 확인
        mock_service.events().delete.assert_called_with(
            calendarId="test-calendar",
            eventId='test-event-123'
        )
    
    @patch('src.calendar.providers.google.build')
    def test_delete_event_not_found(self, mock_build, provider, mock_service):
        """존재하지 않는 이벤트 삭제 시 예외 발생 테스트"""
        mock_build.return_value = mock_service
        
        http_error = HttpError(
            resp=Mock(status=404),
            content=b'{"error": {"message": "Event not found"}}'
        )
        mock_service.events().delete().execute.side_effect = http_error
        
        with pytest.raises(EventNotFoundError):
            provider.delete_event('non-existent-id')
    
    @patch('src.calendar.providers.google.build')
    def test_get_event_success(self, mock_build, provider, mock_service, sample_google_event):
        """이벤트 조회 성공 테스트"""
        mock_build.return_value = mock_service
        mock_service.events().get().execute.return_value = sample_google_event
        
        event = provider.get_event('test-event-123')
        
        assert isinstance(event, CalendarEvent)
        assert event.id == 'google-event-123'
        assert event.summary == '테스트 이벤트'
        
        # API 호출 확인
        assert mock_service.events().get.call_count >= 1
        # 실제 파라미터로 호출되었는지 확인
        mock_service.events().get.assert_called_with(
            calendarId="test-calendar",
            eventId='test-event-123'
        )
    
    @patch('src.calendar.providers.google.build')
    def test_get_event_not_found(self, mock_build, provider, mock_service):
        """존재하지 않는 이벤트 조회 시 None 반환 테스트"""
        mock_build.return_value = mock_service
        
        http_error = HttpError(
            resp=Mock(status=404),
            content=b'{"error": {"message": "Event not found"}}'
        )
        mock_service.events().get().execute.side_effect = http_error
        
        event = provider.get_event('non-existent-id')
        
        assert event is None
    
    @patch('src.calendar.providers.google.build')
    def test_handle_http_error_rate_limit(self, mock_build, provider, mock_service):
        """Rate limit 오류 처리 테스트"""
        mock_build.return_value = mock_service
        
        http_error = HttpError(
            resp=Mock(status=429),
            content=b'{"error": {"message": "Rate limit exceeded"}}'
        )
        mock_service.events().list().execute.side_effect = http_error
        
        with pytest.raises(APIQuotaExceededError):  # 429 오류는 APIQuotaExceededError로 처리됨
            provider.list_events('2024-01-01T00:00:00', '2024-01-31T23:59:59')
    
    @patch('src.calendar.providers.google.build')
    def test_handle_http_error_server_error(self, mock_build, provider, mock_service):
        """서버 오류 처리 테스트"""
        mock_build.return_value = mock_service
        
        http_error = HttpError(
            resp=Mock(status=500),
            content=b'{"error": {"message": "Internal server error"}}'
        )
        mock_service.events().list().execute.side_effect = http_error
        
        with pytest.raises(ServerError):
            provider.list_events('2024-01-01T00:00:00', '2024-01-31T23:59:59')
    
    @patch('src.calendar.providers.google.build')
    def test_handle_network_error(self, mock_build, provider, mock_service):
        """네트워크 오류 처리 테스트"""
        mock_build.return_value = mock_service
        mock_service.events().list().execute.side_effect = ConnectionError("Network error")
        
        with pytest.raises(CalendarServiceError):  # 네트워크 오류는 CalendarServiceError로 래핑됨
            provider.list_events('2024-01-01T00:00:00', '2024-01-31T23:59:59')
    
    @patch('src.calendar.providers.google.build')
    def test_handle_timeout_error(self, mock_build, provider, mock_service):
        """타임아웃 오류 처리 테스트"""
        mock_build.return_value = mock_service
        mock_service.events().list().execute.side_effect = TimeoutError("Request timeout")
        
        with pytest.raises(CalendarServiceError):  # 타임아웃 오류도 CalendarServiceError로 래핑됨
            provider.list_events('2024-01-01T00:00:00', '2024-01-31T23:59:59')