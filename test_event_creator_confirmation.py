#!/usr/bin/env python3
"""
EventCreator와 사용자 확인 요청 시스템 통합 테스트
"""

import sys
sys.path.append('.')

from datetime import datetime
from unittest.mock import Mock
from src.gmail.event_creator import EventCreator
from src.gmail.confirmation_service import ConfirmationService
from src.gmail.notification_service import NotificationService
from src.gmail.models import ExtractedEventInfo

def test_event_creator_with_confirmation():
    """EventCreator와 확인 시스템 통합 테스트"""
    print("=== EventCreator 확인 시스템 통합 테스트 시작 ===\n")
    
    # Mock 서비스들 설정
    mock_calendar_service = Mock()
    mock_calendar_service.create_new_event.return_value = Mock(
        id="event_123",
        summary="테스트 회의",
        start_time="2024-01-15T14:00:00",
        end_time="2024-01-15T15:00:00"
    )
    
    # 알림 핸들러 설정
    def notification_handler(data):
        print(f"📧 알림: {data.get('type', 'unknown')}")
        if data.get('type') == 'confirmation_request':
            print(f"   확인 요청 ID: {data.get('request_id', 'N/A')}")
            print(f"   이메일 ID: {data.get('email_id', 'N/A')}")
            print(f"   신뢰도: {data.get('confidence_score', 0):.2f}")
        return True
    
    # 서비스들 초기화
    notification_service = NotificationService(console_output=False)
    notification_service.add_notification_handler(notification_handler)
    
    confirmation_service = ConfirmationService([notification_handler])
    
    event_creator = EventCreator(
        calendar_service=mock_calendar_service,
        notification_service=notification_service,
        confirmation_service=confirmation_service,
        min_confidence_threshold=0.7
    )
    
    print("1. 높은 신뢰도 일정 생성 테스트 (확인 요청 없음)")
    print("-" * 50)
    
    # 높은 신뢰도 일정 정보
    high_confidence_event = ExtractedEventInfo(
        summary="확실한 회의",
        start_time=datetime(2024, 1, 15, 14, 0),
        end_time=datetime(2024, 1, 15, 15, 0),
        location="회의실 A",
        description="명확한 일정",
        participants=["colleague@example.com"],
        all_day=False,
        confidence_scores={
            "summary": 0.9,
            "start_time": 0.9,
            "location": 0.8,
            "participants": 0.8
        },
        overall_confidence=0.85  # 임계값 이상
    )
    
    result1 = event_creator.create_event(
        event_info=high_confidence_event,
        email_id="email_123",
        email_subject="명확한 회의 안내"
    )
    
    print(f"✅ 높은 신뢰도 일정 생성: {result1['status']}")
    print(f"   이벤트 ID: {result1.get('event_id', 'N/A')}")
    print(f"   신뢰도: {result1.get('confidence_score', 0):.2f}")
    
    print("\n2. 낮은 신뢰도 일정 생성 테스트 (확인 요청 발생)")
    print("-" * 50)
    
    # 낮은 신뢰도 일정 정보
    low_confidence_event = ExtractedEventInfo(
        summary="애매한 회의",
        start_time=datetime(2024, 1, 15, 14, 0),
        end_time=datetime(2024, 1, 15, 15, 0),
        location="어딘가",
        description="불분명한 내용",
        participants=[],
        all_day=False,
        confidence_scores={
            "summary": 0.6,
            "start_time": 0.5,  # 낮은 신뢰도
            "location": 0.4,    # 매우 낮은 신뢰도
            "participants": 0.3
        },
        overall_confidence=0.45  # 임계값 이하
    )
    
    result2 = event_creator.create_event(
        event_info=low_confidence_event,
        email_id="email_456",
        email_subject="애매한 회의 관련"
    )
    
    print(f"✅ 낮은 신뢰도 일정 처리: {result2['status']}")
    print(f"   요청 ID: {result2.get('request_id', 'N/A')}")
    print(f"   신뢰도: {result2.get('confidence_score', 0):.2f}")
    
    # 확인 요청 상태 확인
    if result2.get('request_id'):
        request_id = result2['request_id']
        status = confirmation_service.get_confirmation_status(request_id)
        print(f"   확인 요청 상태: {status['status']}")
        print(f"   만료 시간: {status['expires_at']}")
    
    print("\n3. 사용자 확인 응답 시뮬레이션")
    print("-" * 50)
    
    if result2.get('request_id'):
        request_id = result2['request_id']
        
        # 사용자가 수정사항과 함께 승인
        modified_data = {
            "start_time": "2024-01-15T15:00:00",
            "location": "회의실 B",
            "summary": "수정된 회의 제목"
        }
        
        print("사용자가 수정사항과 함께 승인...")
        confirmation_result = confirmation_service.process_confirmation_response(
            request_id=request_id,
            confirmed=True,
            modified_data=modified_data,
            user_comment="시간과 장소를 수정했습니다"
        )
        
        print(f"✅ 확인 응답 처리: {confirmation_result['status']}")
        print(f"   콜백 결과: {confirmation_result.get('callback_result', {}).get('status', 'N/A')}")
        
        if confirmation_result.get('callback_result'):
            callback_result = confirmation_result['callback_result']
            if callback_result.get('event_id'):
                print(f"   생성된 이벤트 ID: {callback_result['event_id']}")
    
    print("\n4. 확인 서비스 통계")
    print("-" * 50)
    
    stats = confirmation_service.get_statistics()
    print(f"✅ 확인 서비스 통계:")
    print(f"   대기 중인 요청: {stats['pending_requests']}")
    print(f"   완료된 요청: {stats['completed_requests']}")
    print(f"   전체 요청: {stats['total_requests']}")
    print(f"   상태별 분포: {stats['completed_by_status']}")
    
    print("\n5. 확인 요청 거부 테스트")
    print("-" * 50)
    
    # 또 다른 낮은 신뢰도 일정
    another_low_confidence_event = ExtractedEventInfo(
        summary="취소될 회의",
        start_time=datetime(2024, 1, 16, 10, 0),
        end_time=datetime(2024, 1, 16, 11, 0),
        location="미정",
        description="",
        participants=[],
        all_day=False,
        confidence_scores={
            "summary": 0.5,
            "start_time": 0.4,
            "location": 0.2
        },
        overall_confidence=0.35
    )
    
    result3 = event_creator.create_event(
        event_info=another_low_confidence_event,
        email_id="email_789",
        email_subject="취소될 회의"
    )
    
    if result3.get('request_id'):
        request_id3 = result3['request_id']
        
        # 사용자가 거부
        print("사용자가 일정 생성을 거부...")
        rejection_result = confirmation_service.process_confirmation_response(
            request_id=request_id3,
            confirmed=False,
            user_comment="이 회의는 취소되었습니다"
        )
        
        print(f"✅ 거부 응답 처리: {rejection_result['status']}")
        print(f"   사용자 코멘트: {rejection_result.get('user_comment', 'N/A')}")
        
        if rejection_result.get('callback_result'):
            callback_result = rejection_result['callback_result']
            print(f"   콜백 결과: {callback_result.get('status', 'N/A')}")
    
    print("\n=== 통합 테스트 완료 ===")
    
    # 최종 통계
    final_stats = confirmation_service.get_statistics()
    print(f"\n📊 최종 통계:")
    print(f"   전체 요청: {final_stats['total_requests']}")
    print(f"   완료된 요청: {final_stats['completed_requests']}")
    print(f"   상태별 분포: {final_stats['completed_by_status']}")
    
    # Mock 호출 확인
    print(f"\n🔍 Calendar Service 호출 횟수:")
    print(f"   create_new_event 호출: {mock_calendar_service.create_new_event.call_count}회")

if __name__ == "__main__":
    test_event_creator_with_confirmation()