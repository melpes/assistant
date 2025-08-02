"""
캘린더 모델 레거시 테스트 (수동 실행용)
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.calendar.models import CalendarEvent
from src.calendar.exceptions import CalendarServiceError, EventNotFoundError

def test_calendar_event_creation_manual():
    """CalendarEvent 생성 수동 테스트"""
    print("=== CalendarEvent 생성 테스트 ===")
    
    # 정상적인 이벤트 생성
    event = CalendarEvent(
        summary="테스트 미팅",
        description="테스트용 미팅입니다",
        location="서울시 강남구",
        start_time="2024-01-15T10:00:00+09:00",
        end_time="2024-01-15T11:00:00+09:00"
    )
    
    print(f"이벤트 생성 성공: {event.summary}")
    print(f"시작 시간: {event.start_time}")
    print(f"종료 시간: {event.end_time}")
    print(f"위치: {event.location}")
    print(f"설명: {event.description}")
    
    # Google 이벤트 형식으로 변환 테스트
    google_event = event.to_google_event()
    print(f"Google 이벤트 형식: {google_event}")
    
    # Google 이벤트에서 변환 테스트
    sample_google_event = {
        'id': 'test-123',
        'summary': 'Google에서 가져온 이벤트',
        'start': {'dateTime': '2024-01-20T14:00:00+09:00'},
        'end': {'dateTime': '2024-01-20T15:00:00+09:00'},
        'location': '부산시 해운대구'
    }
    
    converted_event = CalendarEvent.from_google_event(sample_google_event)
    print(f"변환된 이벤트: {converted_event.summary}")

if __name__ == "__main__":
    test_calendar_event_creation_manual()