#!/usr/bin/env python3
"""
낮은 신뢰도 일정에 대한 사용자 확인 요청 데모
"""

import sys
sys.path.append('.')

from datetime import datetime
from unittest.mock import Mock
from src.gmail.event_extractor import EventExtractor
from src.gmail.event_creator import EventCreator
from src.gmail.confirmation_service import ConfirmationService
from src.gmail.notification_service import NotificationService
from src.gmail.models import ExtractedEventInfo

def demo_low_confidence_scenario():
    """낮은 신뢰도 시나리오 데모"""
    print("=== 낮은 신뢰도 일정 확인 요청 데모 ===\n")
    
    # Mock 캘린더 서비스
    mock_calendar_service = Mock()
    mock_calendar_event = Mock()
    mock_calendar_event.id = "confirmed_event_789"
    mock_calendar_event.summary = "수정된 회의"
    mock_calendar_event.start_time = "2025-07-26T15:00:00"
    mock_calendar_event.end_time = "2025-07-26T16:00:00"
    mock_calendar_service.create_new_event.return_value = mock_calendar_event
    
    # 알림 핸들러
    def demo_notification_handler(data):
        print(f"🔔 알림: {data.get('type', 'unknown')}")
        if data.get('type') == 'confirmation_request':
            print(f"   ❓ 사용자 확인 필요")
            print(f"   📧 이메일: {data.get('email_subject', 'N/A')}")
            print(f"   📊 신뢰도: {data.get('confidence_score', 0):.2f}")
            print(f"   📅 일정: {data.get('event_details', {}).get('제목', 'N/A')}")
            
            # 신뢰도가 낮은 항목들 표시
            confidence_breakdown = data.get('confidence_breakdown', {})
            low_confidence_items = [key for key, score in confidence_breakdown.items() if score < 0.7]
            if low_confidence_items:
                print(f"   ⚠️ 신뢰도가 낮은 항목: {', '.join(low_confidence_items)}")
                
        elif data.get('type') == 'event_created':
            print(f"   ✅ 일정 생성 완료")
            print(f"   🆔 이벤트 ID: {data.get('event_id', 'N/A')}")
        return True
    
    # 서비스 초기화
    notification_service = NotificationService(console_output=False)
    notification_service.add_notification_handler(demo_notification_handler)
    
    confirmation_service = ConfirmationService([demo_notification_handler])
    
    event_creator = EventCreator(
        calendar_service=mock_calendar_service,
        notification_service=notification_service,
        confirmation_service=confirmation_service,
        min_confidence_threshold=0.7
    )
    
    print("1. 낮은 신뢰도 일정 정보 생성")
    print("-" * 40)
    
    # 낮은 신뢰도 일정 정보 (애매한 내용)
    low_confidence_event = ExtractedEventInfo(
        summary="회의",  # 너무 일반적
        start_time=datetime(2025, 7, 26, 14, 0),  # 시간은 명확
        end_time=None,  # 종료 시간 없음
        location="어딘가",  # 애매한 위치
        description="뭔가 중요한 내용",  # 애매한 설명
        participants=["누군가"],  # 애매한 참석자
        all_day=False,
        confidence_scores={
            "summary": 0.4,      # 매우 낮음
            "datetime": 0.8,     # 높음
            "location": 0.3,     # 매우 낮음
            "participants": 0.2, # 매우 낮음
            "description": 0.3   # 매우 낮음
        },
        overall_confidence=0.4  # 임계값 이하
    )
    
    print(f"📋 일정 정보:")
    print(f"   제목: {low_confidence_event.summary}")
    print(f"   시작 시간: {low_confidence_event.start_time}")
    print(f"   종료 시간: {low_confidence_event.end_time}")
    print(f"   위치: {low_confidence_event.location}")
    print(f"   참석자: {', '.join(low_confidence_event.participants)}")
    print(f"   전체 신뢰도: {low_confidence_event.overall_confidence:.2f}")
    
    print("\n2. 일정 생성 시도 (확인 요청 발생)")
    print("-" * 40)
    
    result = event_creator.create_event(
        event_info=low_confidence_event,
        email_id="low_confidence_email_123",
        email_subject="애매한 회의 관련 이메일"
    )
    
    print(f"📤 처리 결과: {result['status']}")
    
    if result.get('request_id'):
        request_id = result['request_id']
        print(f"🆔 확인 요청 ID: {request_id}")
        
        print("\n3. 확인 요청 상태 조회")
        print("-" * 40)
        
        status = confirmation_service.get_confirmation_status(request_id)
        print(f"📊 요청 상태: {status['status']}")
        print(f"⏰ 만료 시간: {status['expires_at']}")
        print(f"📧 관련 이메일: {status['email_subject']}")
        
        print("\n4. 사용자 응답 시나리오 1: 수정 후 승인")
        print("-" * 40)
        
        # 사용자가 정보를 수정하여 승인
        user_modifications = {
            "summary": "프로젝트 진행 상황 회의",
            "location": "회의실 B",
            "participants": ["김팀장", "이과장", "박대리"],
            "description": "분기별 프로젝트 진행 상황 점검 및 다음 단계 논의"
        }
        
        print("👤 사용자가 다음과 같이 수정하여 승인:")
        for key, value in user_modifications.items():
            print(f"   • {key}: {value}")
        
        confirmation_result = confirmation_service.process_confirmation_response(
            request_id=request_id,
            confirmed=True,
            modified_data=user_modifications,
            user_comment="정보를 수정했습니다. 이제 정확합니다."
        )
        
        print(f"\n✅ 확인 응답 처리: {confirmation_result['status']}")
        print(f"💬 사용자 코멘트: {confirmation_result.get('user_comment', 'N/A')}")
        
        if confirmation_result.get('callback_result'):
            callback_result = confirmation_result['callback_result']
            print(f"🔄 콜백 결과: {callback_result.get('status', 'N/A')}")
            if callback_result.get('event_id'):
                print(f"🆔 최종 생성된 이벤트 ID: {callback_result['event_id']}")
    
    print("\n5. 또 다른 낮은 신뢰도 시나리오: 거부")
    print("-" * 40)
    
    # 또 다른 낮은 신뢰도 일정
    another_low_confidence_event = ExtractedEventInfo(
        summary="미팅",
        start_time=datetime(2025, 7, 27, 10, 0),
        end_time=None,
        location="",
        description="",
        participants=[],
        all_day=False,
        confidence_scores={
            "summary": 0.3,
            "datetime": 0.6,
            "location": 0.1,
            "participants": 0.1
        },
        overall_confidence=0.25
    )
    
    result2 = event_creator.create_event(
        event_info=another_low_confidence_event,
        email_id="another_email_456",
        email_subject="미팅 관련"
    )
    
    if result2.get('request_id'):
        request_id2 = result2['request_id']
        
        print("👤 사용자가 일정 생성을 거부...")
        rejection_result = confirmation_service.process_confirmation_response(
            request_id=request_id2,
            confirmed=False,
            user_comment="이 미팅은 취소되었습니다."
        )
        
        print(f"❌ 거부 응답 처리: {rejection_result['status']}")
        print(f"💬 사용자 코멘트: {rejection_result.get('user_comment', 'N/A')}")
        
        if rejection_result.get('callback_result'):
            callback_result = rejection_result['callback_result']
            print(f"🔄 콜백 결과: {callback_result.get('status', 'N/A')}")
    
    print("\n6. 최종 통계")
    print("-" * 40)
    
    stats = confirmation_service.get_statistics()
    print(f"📊 확인 서비스 통계:")
    print(f"   전체 요청: {stats['total_requests']}")
    print(f"   완료된 요청: {stats['completed_requests']}")
    print(f"   상태별 분포: {stats['completed_by_status']}")
    
    notification_history = notification_service.get_notification_history()
    print(f"\n📨 알림 이력: {len(notification_history)}개")
    for i, notification in enumerate(notification_history, 1):
        print(f"   {i}. {notification.get('type', 'unknown')} - {notification.get('timestamp', 'N/A')}")
    
    print(f"\n🔍 캘린더 서비스 호출:")
    print(f"   create_new_event 호출 횟수: {mock_calendar_service.create_new_event.call_count}회")
    
    print("\n=== 낮은 신뢰도 시나리오 데모 완료 ===")
    print("\n🎯 주요 확인 사항:")
    print("✅ 낮은 신뢰도 일정에 대한 자동 확인 요청")
    print("✅ 사용자 수정사항 적용 및 승인 처리")
    print("✅ 사용자 거부 처리")
    print("✅ 실시간 알림 및 상태 추적")
    print("✅ 콜백 기반 비동기 처리")

if __name__ == "__main__":
    demo_low_confidence_scenario()