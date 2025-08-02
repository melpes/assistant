"""
tools.py 캘린더 함수 통합 테스트 (실제 API 사용)
"""
import os
import sys
import datetime
from datetime import timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.tools import list_calendar_events, create_google_calendar_event

def test_tools_calendar_integration():
    """tools.py 캘린더 함수 통합 테스트"""
    print("=== tools.py 캘린더 함수 통합 테스트 ===")
    
    try:
        # 현재 날짜 계산
        today = datetime.date.today()
        start_date = today.strftime('%Y-%m-%d')
        end_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
        
        print(f"이벤트 조회 기간: {start_date} ~ {end_date}")
        
        # 이벤트 목록 조회 테스트
        print("\n1. 이벤트 목록 조회 테스트")
        events_result = list_calendar_events(start_date, end_date)
        print(f"조회 결과: {events_result}")
        
        # 이벤트 생성 테스트
        print("\n2. 이벤트 생성 테스트")
        tomorrow = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        
        create_result = create_google_calendar_event(
            title="테스트 이벤트 (tools.py)",
            description="tools.py 함수 테스트로 생성된 이벤트",
            start_time=f"{tomorrow}T10:00:00",
            end_time=f"{tomorrow}T11:00:00",
            location="테스트 장소"
        )
        print(f"생성 결과: {create_result}")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tools_calendar_integration()