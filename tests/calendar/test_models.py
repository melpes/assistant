"""
캘린더 모델 단위 테스트
"""
import pytest
from datetime import datetime
from src.calendar.models import CalendarEvent


class TestCalendarEvent:
    """CalendarEvent 클래스 테스트"""
    
    def test_calendar_event_creation_valid(self):
        """유효한 데이터로 CalendarEvent 생성 테스트"""
        event = CalendarEvent(
            summary="테스트 이벤트",
            start_time="2024-01-01T10:00:00",
            end_time="2024-01-01T11:00:00"
        )
        
        assert event.summary == "테스트 이벤트"
        assert event.start_time == "2024-01-01T10:00:00"
        assert event.end_time == "2024-01-01T11:00:00"
        assert event.all_day is False
        assert event.id is None
        assert event.description is None
        assert event.location is None
    
    def test_calendar_event_creation_with_optional_fields(self):
        """선택적 필드를 포함한 CalendarEvent 생성 테스트"""
        event = CalendarEvent(
            id="test-id-123",
            summary="상세 테스트 이벤트",
            description="이벤트 설명",
            location="서울시 강남구",
            start_time="2024-01-01T10:00:00",
            end_time="2024-01-01T11:00:00",
            all_day=True
        )
        
        assert event.id == "test-id-123"
        assert event.summary == "상세 테스트 이벤트"
        assert event.description == "이벤트 설명"
        assert event.location == "서울시 강남구"
        assert event.all_day is True
    
    def test_calendar_event_validation_empty_summary(self):
        """빈 제목으로 CalendarEvent 생성 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="이벤트 제목\\(summary\\)은 필수입니다"):
            CalendarEvent(
                summary="",
                start_time="2024-01-01T10:00:00",
                end_time="2024-01-01T11:00:00"
            )
    
    def test_calendar_event_validation_empty_start_time(self):
        """빈 시작 시간으로 CalendarEvent 생성 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="시작 시간\\(start_time\\)은 필수입니다"):
            CalendarEvent(
                summary="테스트 이벤트",
                start_time="",
                end_time="2024-01-01T11:00:00"
            )
    
    def test_calendar_event_validation_empty_end_time(self):
        """빈 종료 시간으로 CalendarEvent 생성 시 예외 발생 테스트"""
        with pytest.raises(ValueError, match="종료 시간\\(end_time\\)은 필수입니다"):
            CalendarEvent(
                summary="테스트 이벤트",
                start_time="2024-01-01T10:00:00",
                end_time=""
            )
    
    def test_from_google_event_datetime(self):
        """Google API 응답(datetime)을 CalendarEvent로 변환 테스트"""
        google_event = {
            'id': 'google-event-123',
            'summary': 'Google 이벤트',
            'description': 'Google에서 가져온 이벤트',
            'location': '구글 본사',
            'start': {'dateTime': '2024-01-01T10:00:00+09:00'},
            'end': {'dateTime': '2024-01-01T11:00:00+09:00'}
        }
        
        event = CalendarEvent.from_google_event(google_event)
        
        assert event.id == 'google-event-123'
        assert event.summary == 'Google 이벤트'
        assert event.description == 'Google에서 가져온 이벤트'
        assert event.location == '구글 본사'
        assert event.start_time == '2024-01-01T10:00:00+09:00'
        assert event.end_time == '2024-01-01T11:00:00+09:00'
        assert event.all_day is False
    
    def test_from_google_event_all_day(self):
        """Google API 응답(종일 이벤트)을 CalendarEvent로 변환 테스트"""
        google_event = {
            'id': 'google-allday-123',
            'summary': '종일 이벤트',
            'start': {'date': '2024-01-01'},
            'end': {'date': '2024-01-02'}
        }
        
        event = CalendarEvent.from_google_event(google_event)
        
        assert event.id == 'google-allday-123'
        assert event.summary == '종일 이벤트'
        assert event.start_time == '2024-01-01'
        assert event.end_time == '2024-01-02'
        assert event.all_day is True
        assert event.description is None
        assert event.location is None
    
    def test_from_google_event_minimal(self):
        """최소한의 Google API 응답을 CalendarEvent로 변환 테스트"""
        google_event = {
            'start': {'dateTime': '2024-01-01T10:00:00'},
            'end': {'dateTime': '2024-01-01T11:00:00'}
        }
        
        event = CalendarEvent.from_google_event(google_event)
        
        assert event.summary == '제목 없음'  # 기본값으로 설정됨
        assert event.start_time == '2024-01-01T10:00:00'
        assert event.end_time == '2024-01-01T11:00:00'
        assert event.all_day is False
    
    def test_to_google_event_datetime(self):
        """CalendarEvent를 Google API 형식(datetime)으로 변환 테스트"""
        event = CalendarEvent(
            summary="테스트 이벤트",
            description="설명",
            location="위치",
            start_time="2024-01-01T10:00:00",
            end_time="2024-01-01T11:00:00",
            all_day=False
        )
        
        google_event = event.to_google_event()
        
        expected = {
            'summary': "테스트 이벤트",
            'description': "설명",
            'location': "위치",
            'start': {'dateTime': "2024-01-01T10:00:00"},
            'end': {'dateTime': "2024-01-01T11:00:00"}
        }
        
        assert google_event == expected
    
    def test_to_google_event_all_day(self):
        """CalendarEvent를 Google API 형식(종일)으로 변환 테스트"""
        event = CalendarEvent(
            summary="종일 이벤트",
            start_time="2024-01-01",
            end_time="2024-01-02",
            all_day=True
        )
        
        google_event = event.to_google_event()
        
        expected = {
            'summary': "종일 이벤트",
            'start': {'date': "2024-01-01"},
            'end': {'date': "2024-01-02"}
        }
        
        assert google_event == expected
    
    def test_to_google_event_minimal(self):
        """최소한의 CalendarEvent를 Google API 형식으로 변환 테스트"""
        event = CalendarEvent(
            summary="최소 이벤트",
            start_time="2024-01-01T10:00:00",
            end_time="2024-01-01T11:00:00"
        )
        
        google_event = event.to_google_event()
        
        expected = {
            'summary': "최소 이벤트",
            'start': {'dateTime': "2024-01-01T10:00:00"},
            'end': {'dateTime': "2024-01-01T11:00:00"}
        }
        
        assert google_event == expected