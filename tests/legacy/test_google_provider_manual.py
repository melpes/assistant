"""
GoogleCalendarProvider 수동 테스트 (실제 API 사용)
"""
import sys
import os
import datetime
from datetime import timezone, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.calendar.providers.google import GoogleCalendarProvider
from src.calendar.models import CalendarEvent
from src.calendar.auth import GoogleAuthService

def test_list_events_manual():
    """이벤트 목록 조회 수동 테스트"""
    print("=== GoogleCalendarProvider 수동 테스트 ===")
    
    try:
        # 인증 서비스 생성
        auth_service = GoogleAuthService()
        
        # 프로바이더 생성
        provider = GoogleCalendarProvider(auth_service=auth_service)
        
        # 현재 시간부터 7일 동안의 이벤트 조회
        now = datetime.datetime.now(timezone.utc)
        start_time = now.isoformat()
        end_time = (now + timedelta(days=7)).isoformat()
        
        print(f"이벤트 조회 기간: {start_time} ~ {end_time}")
        
        events = provider.list_events(start_time, end_time)
        
        print(f"조회된 이벤트 수: {len(events)}")
        
        for i, event in enumerate(events[:5], 1):  # 최대 5개만 출력
            print(f"{i}. {event.summary}")
            print(f"   시간: {event.start_time} ~ {event.end_time}")
            if event.location:
                print(f"   위치: {event.location}")
            print()
            
    except Exception as e:
        print(f"오류 발생: {e}")

def test_create_event_manual():
    """이벤트 생성 수동 테스트"""
    print("=== 이벤트 생성 테스트 ===")
    
    try:
        # 인증 서비스 생성
        auth_service = GoogleAuthService()
        
        # 프로바이더 생성
        provider = GoogleCalendarProvider(auth_service=auth_service)
        
        # 테스트 이벤트 생성
        test_event = CalendarEvent(
            summary="테스트 이벤트 (자동 생성)",
            description="캘린더 서비스 테스트로 생성된 이벤트입니다.",
            start_time=(datetime.datetime.now() + timedelta(hours=1)).isoformat(),
            end_time=(datetime.datetime.now() + timedelta(hours=2)).isoformat()
        )
        
        created_event = provider.create_event(test_event)
        print(f"이벤트 생성 성공: {created_event.summary}")
        print(f"이벤트 ID: {created_event.id}")
        
        return created_event.id
        
    except Exception as e:
        print(f"이벤트 생성 오류: {e}")
        return None

if __name__ == "__main__":
    test_list_events_manual()
    event_id = test_create_event_manual()
    
    if event_id:
        print(f"생성된 테스트 이벤트 ID: {event_id}")
        print("수동으로 삭제하거나 나중에 정리해주세요.")