"""
캘린더 서비스 팩토리 사용 예제

이 예제는 CalendarServiceFactory를 사용하여 캘린더 서비스를 생성하고 사용하는 방법을 보여줍니다.
"""
import sys
import os
import logging
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.calendar.factory import CalendarServiceFactory
from src.calendar.logging_config import setup_logging

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)


def main():
    """
    캘린더 서비스 팩토리 사용 예제 실행
    """
    try:
        print("캘린더 서비스 팩토리 예제 시작...")
        
        # 기본 설정으로 캘린더 서비스 생성
        print("기본 설정으로 캘린더 서비스 생성 중...")
        calendar_service = CalendarServiceFactory.create_service()
        
        # 오늘 날짜와 일주일 후 날짜 계산
        today = datetime.now().replace(microsecond=0).isoformat() + 'Z'
        next_week = (datetime.now() + timedelta(days=7)).replace(microsecond=0).isoformat() + 'Z'
        
        # 일정 조회
        print(f"다음 7일간의 일정 조회 중...")
        events = calendar_service.get_events_for_period(today, next_week)
        
        # 결과 출력
        print(f"\n다음 7일간의 일정 ({len(events)}개):")
        for event in events:
            print(f"- {event['제목']} ({event['시간']})")
        
        print("\n특정 프로바이더 지정 예제:")
        # 특정 프로바이더 지정하여 서비스 생성
        google_service = CalendarServiceFactory.create_service("google")
        print("Google 캘린더 서비스 생성 완료")
        
        # 특정 캘린더 ID 지정 예제
        print("\n특정 캘린더 ID 지정 예제:")
        calendar_id = "primary"  # 기본 캘린더
        custom_service = CalendarServiceFactory.create_service(calendar_id=calendar_id)
        print(f"캘린더 ID '{calendar_id}'로 서비스 생성 완료")
        
        print("\n캘린더 서비스 팩토리 예제 완료")
        
    except Exception as e:
        logger.error(f"예제 실행 중 오류 발생: {e}", exc_info=True)
        print(f"오류 발생: {e}")


if __name__ == "__main__":
    main()