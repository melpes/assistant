"""
캘린더 서비스 사용 예제

이 스크립트는 CalendarService 클래스의 사용 방법을 보여줍니다.
"""
import os
import sys
import datetime
from datetime import timedelta

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.calendar import (
    CalendarService,
    GoogleCalendarProvider,
    GoogleAuthService
)


def main():
    """캘린더 서비스 사용 예제 실행"""
    try:
        # Google 인증 서비스 생성
        auth_service = GoogleAuthService()
        
        # Google Calendar Provider 생성
        provider = GoogleCalendarProvider(auth_service)
        
        # Calendar Service 생성
        service = CalendarService(provider)
        
        # 오늘 날짜 계산
        today = datetime.datetime.now()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        
        print("\n===== 오늘의 일정 =====")
        today_events = service.get_today_events()
        if today_events:
            for event in today_events:
                print(f"- {event['제목']} ({event['시간']})")
        else:
            print("오늘 예정된 일정이 없습니다.")
        
        print("\n===== 다음 주 일정 =====")
        upcoming_events = service.get_events_for_period(today, next_week)
        if upcoming_events:
            for event in upcoming_events:
                print(f"- {event['제목']} ({event['시간']})")
        else:
            print("다음 주 예정된 일정이 없습니다.")
        
        # 새 일정 생성 예제 (주석 처리)
        """
        print("\n===== 새 일정 생성 =====")
        new_event = service.create_new_event(
            summary="테스트 일정",
            start_time=tomorrow.replace(hour=10, minute=0),
            end_time=tomorrow.replace(hour=11, minute=0),
            description="CalendarService 테스트",
            location="온라인"
        )
        print(f"새 일정이 생성되었습니다: {new_event['제목']} ({new_event['시간']})")
        
        # 생성된 일정 ID 저장
        event_id = new_event['id']
        
        # 일정 수정 예제
        print("\n===== 일정 수정 =====")
        updated_event = service.update_event(
            event_id=event_id,
            summary="수정된 테스트 일정",
            description="CalendarService 수정 테스트"
        )
        print(f"일정이 수정되었습니다: {updated_event['제목']} ({updated_event['시간']})")
        
        # 일정 삭제 예제
        print("\n===== 일정 삭제 =====")
        deleted = service.delete_event(event_id)
        if deleted:
            print(f"일정이 삭제되었습니다: {event_id}")
        else:
            print(f"일정 삭제에 실패했습니다: {event_id}")
        """
        
    except Exception as e:
        print(f"오류 발생: {e}")


if __name__ == "__main__":
    main()