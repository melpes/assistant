"""
캘린더 서비스 단위 테스트
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.calendar.service import CalendarService
from src.calendar.interfaces import CalendarProvider
from src.calendar.models import CalendarEvent
from src.calendar.exceptions import (
    CalendarServiceError,
    EventNotFoundError,
    InvalidEventDataError
)


class TestCalendarService:
    """CalendarService 클래스 테스트"""
    
    @pytest.fixture
    def mock_provider(self):
        """Mock CalendarProvider"""
        provider = Mock(spec=CalendarProvider)
        return provider
    
    @pytest.fixture
    def calendar_service(self, mock_provider):
        """테스트용 CalendarService 인스턴스"""
        return CalendarService(provider=mock_provider)
    
    @pytest.fixture
    def sample_events(self):
        """샘플 이벤트 목록"""
        return [
            CalendarEvent(
                id='event-1',
                summary='첫 번째 이벤트',
                start_time='2024-01-01T10:00:00+09:00',
                end_time='2024-01-01T11:00:00+09:00'
            ),
            CalendarEvent(
                id='event-2',
                summary='두 번째 이벤트',
                start_time='2024-01-01T14:00:00+09:00',
                end_time='2024-01-01T15:00:00+09:00'
            )
        ]
    
    def test_init(self, mock_provider):
        """CalendarService 초기화 테스트"""
        service = CalendarService(provider=mock_provider)
        assert service.provider == mock_provider
    
    def test_get_events_for_period_with_string_dates(self, calendar_service, mock_provider, sample_events):
        """문자열 날짜로 기간별 이벤트 조회 테스트"""
        mock_provider.list_events.return_value = sample_events
        
        events = calendar_service.get_events_for_period(
            start_date='2024-01-01T00:00:00',
            end_date='2024-01-31T23:59:59',
            format_response=False
        )
        
        assert len(events) == 2
        assert all(isinstance(event, CalendarEvent) for event in events)
        mock_provider.list_events.assert_called_once_with(
            '2024-01-01T00:00:00',
            '2024-01-31T23:59:59'
        )
    
    def test_get_events_for_period_with_datetime_objects(self, calendar_service, mock_provider, sample_events):
        """datetime 객체로 기간별 이벤트 조회 테스트"""
        mock_provider.list_events.return_value = sample_events
        
        start_date = datetime(2024, 1, 1, 0, 0, 0)
        end_date = datetime(2024, 1, 31, 23, 59, 59)
        
        events = calendar_service.get_events_for_period(
            start_date=start_date,
            end_date=end_date
        )
        
        assert len(events) == 2
        mock_provider.list_events.assert_called_once()
        
        # datetime이 ISO 형식 문자열로 변환되었는지 확인
        call_args = mock_provider.list_events.call_args[0]
        assert isinstance(call_args[0], str)
        assert isinstance(call_args[1], str)
    
    def test_get_events_for_period_formatted_response(self, calendar_service, mock_provider, sample_events):
        """포맷된 응답으로 기간별 이벤트 조회 테스트"""
        mock_provider.list_events.return_value = sample_events
        
        events = calendar_service.get_events_for_period(
            start_date='2024-01-01T00:00:00',
            end_date='2024-01-31T23:59:59',
            format_response=True
        )
        
        assert len(events) == 2
        assert all(isinstance(event, dict) for event in events)
        
        # 첫 번째 이벤트의 포맷 확인
        first_event = events[0]
        assert 'id' in first_event
        assert '제목' in first_event
        assert '시간' in first_event
        assert first_event['제목'] == '첫 번째 이벤트'
    
    def test_get_events_for_period_no_format(self, calendar_service, mock_provider, sample_events):
        """포맷하지 않은 응답으로 기간별 이벤트 조회 테스트"""
        mock_provider.list_events.return_value = sample_events
        
        events = calendar_service.get_events_for_period(
            start_date='2024-01-01T00:00:00',
            end_date='2024-01-31T23:59:59',
            format_response=False
        )
        
        assert len(events) == 2
        assert all(isinstance(event, CalendarEvent) for event in events)
    
    def test_get_events_for_period_empty_result(self, calendar_service, mock_provider):
        """빈 결과로 기간별 이벤트 조회 테스트"""
        mock_provider.list_events.return_value = []
        
        events = calendar_service.get_events_for_period(
            start_date='2024-01-01T00:00:00',
            end_date='2024-01-31T23:59:59'
        )
        
        assert len(events) == 0
        assert isinstance(events, list)
    
    def test_get_events_for_period_provider_error(self, calendar_service, mock_provider):
        """프로바이더 오류 시 예외 전파 테스트"""
        mock_provider.list_events.side_effect = CalendarServiceError("Provider error")
        
        with pytest.raises(CalendarServiceError):
            calendar_service.get_events_for_period(
                start_date='2024-01-01T00:00:00',
                end_date='2024-01-31T23:59:59'
            )
    
    def test_create_new_event_success(self, calendar_service, mock_provider):
        """새 이벤트 생성 성공 테스트"""
        created_event = CalendarEvent(
            id='new-event-123',
            summary='새 이벤트',
            start_time='2024-01-01T10:00:00+09:00',
            end_time='2024-01-01T11:00:00+09:00'
        )
        mock_provider.create_event.return_value = created_event
        
        result = calendar_service.create_new_event(
            summary='새 이벤트',
            start_time='2024-01-01T10:00:00+09:00',
            end_time='2024-01-01T11:00:00+09:00',
            format_response=False
        )
        
        assert isinstance(result, CalendarEvent)
        assert result.id == 'new-event-123'
        assert result.summary == '새 이벤트'
        
        # 프로바이더 호출 확인
        mock_provider.create_event.assert_called_once()
        call_args = mock_provider.create_event.call_args[0][0]
        assert isinstance(call_args, CalendarEvent)
        assert call_args.summary == '새 이벤트'
    
    def test_create_new_event_with_optional_fields(self, calendar_service, mock_provider):
        """선택적 필드를 포함한 새 이벤트 생성 테스트"""
        created_event = CalendarEvent(
            id='new-event-123',
            summary='상세 이벤트',
            description='이벤트 설명',
            location='서울시 강남구',
            start_time='2024-01-01T10:00:00+09:00',
            end_time='2024-01-01T11:00:00+09:00'
        )
        mock_provider.create_event.return_value = created_event
        
        result = calendar_service.create_new_event(
            summary='상세 이벤트',
            start_time='2024-01-01T10:00:00+09:00',
            end_time='2024-01-01T11:00:00+09:00',
            description='이벤트 설명',
            location='서울시 강남구',
            format_response=False
        )
        
        assert result.description == '이벤트 설명'
        assert result.location == '서울시 강남구'
    
    def test_create_new_event_validation_error(self, calendar_service, mock_provider):
        """잘못된 데이터로 이벤트 생성 시 예외 발생 테스트"""
        with pytest.raises(InvalidEventDataError):
            calendar_service.create_new_event(
                summary='',  # 빈 제목
                start_time='2024-01-01T10:00:00+09:00',
                end_time='2024-01-01T11:00:00+09:00'
            )
    
    def test_create_new_event_provider_error(self, calendar_service, mock_provider):
        """프로바이더 오류 시 예외 전파 테스트"""
        mock_provider.create_event.side_effect = CalendarServiceError("Provider error")
        
        with pytest.raises(CalendarServiceError):
            calendar_service.create_new_event(
                summary='테스트 이벤트',
                start_time='2024-01-01T10:00:00+09:00',
                end_time='2024-01-01T11:00:00+09:00'
            )
    
    def test_update_event_success(self, calendar_service, mock_provider):
        """기존 이벤트 수정 성공 테스트"""
        # 기존 이벤트 (get_event에서 반환)
        existing_event = CalendarEvent(
            id='existing-event-123',
            summary='기존 이벤트',
            start_time='2024-01-01T09:00:00+09:00',
            end_time='2024-01-01T10:00:00+09:00'
        )
        
        # 수정된 이벤트 (update_event에서 반환)
        updated_event = CalendarEvent(
            id='existing-event-123',
            summary='수정된 이벤트',
            start_time='2024-01-01T10:00:00+09:00',
            end_time='2024-01-01T11:00:00+09:00'
        )
        
        mock_provider.get_event.return_value = existing_event
        mock_provider.update_event.return_value = updated_event
        
        result = calendar_service.update_event(
            event_id='existing-event-123',
            summary='수정된 이벤트',
            start_time='2024-01-01T10:00:00+09:00',
            end_time='2024-01-01T11:00:00+09:00',
            format_response=False
        )
        
        assert isinstance(result, CalendarEvent)
        assert result.summary == '수정된 이벤트'
        
        # 프로바이더 호출 확인
        mock_provider.get_event.assert_called_once_with('existing-event-123')
        mock_provider.update_event.assert_called_once()
        call_args = mock_provider.update_event.call_args
        assert call_args[0][0] == 'existing-event-123'
        assert isinstance(call_args[0][1], CalendarEvent)
    
    def test_update_event_not_found(self, calendar_service, mock_provider):
        """존재하지 않는 이벤트 수정 시 예외 발생 테스트"""
        mock_provider.update_event.side_effect = EventNotFoundError('non-existent-id')
        
        with pytest.raises(EventNotFoundError):
            calendar_service.update_event(
                event_id='non-existent-id',
                summary='수정된 이벤트',
                start_time='2024-01-01T10:00:00+09:00',
                end_time='2024-01-01T11:00:00+09:00'
            )
    
    def test_delete_event_success(self, calendar_service, mock_provider):
        """이벤트 삭제 성공 테스트"""
        mock_provider.delete_event.return_value = True
        
        result = calendar_service.delete_event('event-to-delete')
        
        assert result is True
        mock_provider.delete_event.assert_called_once_with('event-to-delete')
    
    def test_delete_event_not_found(self, calendar_service, mock_provider):
        """존재하지 않는 이벤트 삭제 시 예외 발생 테스트"""
        mock_provider.delete_event.side_effect = EventNotFoundError('non-existent-id')
        
        with pytest.raises(EventNotFoundError):
            calendar_service.delete_event('non-existent-id')
    
    def test_get_event_details_success(self, calendar_service, mock_provider):
        """ID로 이벤트 조회 성공 테스트"""
        event = CalendarEvent(
            id='test-event-123',
            summary='테스트 이벤트',
            start_time='2024-01-01T10:00:00+09:00',
            end_time='2024-01-01T11:00:00+09:00'
        )
        mock_provider.get_event.return_value = event
        
        result = calendar_service.get_event_details('test-event-123', format_response=False)
        
        assert isinstance(result, CalendarEvent)
        assert result.id == 'test-event-123'
        mock_provider.get_event.assert_called_once_with('test-event-123')
    
    def test_get_event_details_not_found(self, calendar_service, mock_provider):
        """존재하지 않는 이벤트 조회 시 None 반환 테스트"""
        mock_provider.get_event.return_value = None
        
        result = calendar_service.get_event_details('non-existent-id', format_response=False)
        
        assert result is None
    
    def test_get_today_events(self, calendar_service, mock_provider, sample_events):
        """오늘 이벤트 조회 테스트"""
        mock_provider.list_events.return_value = sample_events
        
        with patch('src.calendar.service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            events = calendar_service.get_today_events()
            
            assert len(events) == 2
            mock_provider.list_events.assert_called_once()
            
            # 오늘 날짜 범위로 호출되었는지 확인
            call_args = mock_provider.list_events.call_args[0]
            assert '2024-01-01T00:00:00' in call_args[0]
            assert '2024-01-02T00:00:00' in call_args[1]  # 다음 날 00:00:00
    
    def test_get_upcoming_events(self, calendar_service, mock_provider, sample_events):
        """향후 이벤트 조회 테스트"""
        mock_provider.list_events.return_value = sample_events
        
        with patch('src.calendar.service.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 3, 12, 0, 0)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            events = calendar_service.get_upcoming_events(days=7, format_response=False)
            
            assert len(events) == 2
            mock_provider.list_events.assert_called_once()
    
    def test_format_event_for_display(self, calendar_service):
        """이벤트 응답 포맷팅 테스트"""
        event = CalendarEvent(
            id='test-event-123',
            summary='테스트 이벤트',
            description='이벤트 설명',
            location='서울시 강남구',
            start_time='2024-01-01T10:00:00+09:00',
            end_time='2024-01-01T11:00:00+09:00',
            all_day=False
        )
        
        formatted = calendar_service._format_event_for_display(event)
        
        assert isinstance(formatted, dict)
        assert formatted['id'] == 'test-event-123'
        assert formatted['제목'] == '테스트 이벤트'
        assert formatted['설명'] == '이벤트 설명'
        assert formatted['위치'] == '서울시 강남구'
        assert '시간' in formatted
        assert formatted['종일 일정'] is False
    
    def test_format_event_for_display_minimal(self, calendar_service):
        """최소한의 이벤트 응답 포맷팅 테스트"""
        event = CalendarEvent(
            summary='최소 이벤트',
            start_time='2024-01-01T10:00:00+09:00',
            end_time='2024-01-01T11:00:00+09:00'
        )
        
        formatted = calendar_service._format_event_for_display(event)
        
        assert formatted['제목'] == '최소 이벤트'
        assert '설명' not in formatted  # 설명이 없으면 키 자체가 없음
        assert '위치' not in formatted  # 위치가 없으면 키 자체가 없음
        assert formatted['id'] is None