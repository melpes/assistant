#!/usr/bin/env python3
"""
전체 이메일-캘린더 자동화 시스템 데모
"""

import sys
sys.path.append('.')

from datetime import datetime
from unittest.mock import Mock
from src.gmail.service import GmailServiceManager
from src.gmail.processor import EmailProcessor
from src.gmail.event_extractor import EventExtractor
from src.gmail.event_creator import EventCreator
from src.gmail.confirmation_service import ConfirmationService
from src.gmail.notification_service import NotificationService
from src.gmail.confidence_evaluator import ConfidenceEvaluator

def demo_full_integration():
    """전체 시스템 통합 데모"""
    print("=== 이메일-캘린더 자동화 시스템 전체 데모 ===\n")
    
    # Mock 서비스들 설정
    mock_gmail_service = Mock()
    mock_calendar_service = Mock()
    
    # Mock 이메일 데이터
    mock_email_data = {
        'id': 'email_demo_123',
        'threadId': 'thread_123',
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': '내일 오후 2시 회의 안내'},
                {'name': 'From', 'value': 'manager@company.com'},
                {'name': 'To', 'value': 'user@company.com'},
                {'name': 'Date', 'value': 'Mon, 25 Jul 2025 10:00:00 +0900'}
            ],
            'body': {
                'data': 'VGVzdCBlbWFpbCBib2R5'  # Base64 encoded
            }
        }
    }
    
    mock_gmail_service.users().messages().get().execute.return_value = mock_email_data
    
    # Mock 캘린더 이벤트
    mock_calendar_event = Mock()
    mock_calendar_event.id = "created_event_456"
    mock_calendar_event.summary = "중요한 회의"
    mock_calendar_event.start_time = "2025-07-26T14:00:00"
    mock_calendar_event.end_time = "2025-07-26T15:00:00"
    
    mock_calendar_service.create_new_event.return_value = mock_calendar_event
    
    print("1. 서비스 초기화")
    print("-" * 30)
    
    # 알림 핸들러 설정
    def demo_notification_handler(data):
        print(f"📧 시스템 알림: {data.get('type', 'unknown')}")
        if data.get('type') == 'confirmation_request':
            print(f"   ❓ 확인 요청 - 신뢰도: {data.get('confidence_score', 0):.2f}")
            print(f"   📝 일정: {data.get('event_details', {}).get('제목', 'N/A')}")
        elif data.get('type') == 'event_created':
            print(f"   ✅ 일정 생성 완료 - ID: {data.get('event_id', 'N/A')}")
        return True
    
    # 서비스들 초기화
    gmail_manager = GmailServiceManager(auth_service=None)
    gmail_manager._service = mock_gmail_service
    
    email_processor = EmailProcessor(mock_gmail_service)
    
    confidence_evaluator = ConfidenceEvaluator()
    event_extractor = EventExtractor()
    
    notification_service = NotificationService(console_output=False)
    notification_service.add_notification_handler(demo_notification_handler)
    
    confirmation_service = ConfirmationService([demo_notification_handler])
    
    event_creator = EventCreator(
        calendar_service=mock_calendar_service,
        notification_service=notification_service,
        confirmation_service=confirmation_service,
        min_confidence_threshold=0.7
    )
    
    print("✅ 모든 서비스 초기화 완료")
    
    print("\n2. 이메일 처리 시뮬레이션")
    print("-" * 30)
    
    # 이메일 내용 시뮬레이션
    email_content = """
    안녕하세요,
    
    내일(7월 26일) 오후 2시에 회의실 A에서 프로젝트 진행 상황 회의가 있습니다.
    참석자: 김팀장, 이과장, 박대리
    
    준비사항:
    - 진행 상황 보고서
    - 다음 단계 계획안
    
    감사합니다.
    """
    
    print(f"📧 처리할 이메일 내용:")
    print(email_content)
    
    print("\n3. 일정 정보 추출")
    print("-" * 30)
    
    # 일정 정보 추출
    extracted_info = event_extractor.extract_event_info(email_content)
    
    print(f"✅ 추출된 일정 정보:")
    print(f"   제목: {extracted_info.summary}")
    print(f"   시작 시간: {extracted_info.start_time}")
    print(f"   종료 시간: {extracted_info.end_time}")
    print(f"   위치: {extracted_info.location}")
    print(f"   참석자: {', '.join(extracted_info.participants)}")
    print(f"   전체 신뢰도: {extracted_info.overall_confidence:.2f}")
    print(f"   신뢰도 세부사항: {extracted_info.confidence_scores}")
    
    print("\n4. 일정 생성 처리")
    print("-" * 30)
    
    # 신뢰도에 따른 처리
    if extracted_info.overall_confidence >= 0.7:
        print("🟢 높은 신뢰도 - 즉시 일정 생성")
        result = event_creator.create_event(
            event_info=extracted_info,
            email_id="email_demo_123",
            email_subject="내일 오후 2시 회의 안내"
        )
        print(f"   결과: {result['status']}")
        if result.get('event_id'):
            print(f"   생성된 이벤트 ID: {result['event_id']}")
    else:
        print("🟡 낮은 신뢰도 - 사용자 확인 요청")
        result = event_creator.create_event(
            event_info=extracted_info,
            email_id="email_demo_123",
            email_subject="내일 오후 2시 회의 안내"
        )
        print(f"   결과: {result['status']}")
        
        if result.get('request_id'):
            request_id = result['request_id']
            print(f"   확인 요청 ID: {request_id}")
            
            print("\n5. 사용자 확인 시뮬레이션")
            print("-" * 30)
            
            # 사용자 확인 상태 조회
            status = confirmation_service.get_confirmation_status(request_id)
            print(f"📋 확인 요청 상태: {status['status']}")
            print(f"   만료 시간: {status['expires_at']}")
            
            # 사용자가 승인하는 시나리오
            print("\n👤 사용자가 일정을 승인...")
            confirmation_result = confirmation_service.process_confirmation_response(
                request_id=request_id,
                confirmed=True,
                user_comment="일정이 정확합니다. 생성해주세요."
            )
            
            print(f"✅ 확인 응답 처리: {confirmation_result['status']}")
            if confirmation_result.get('callback_result'):
                callback_result = confirmation_result['callback_result']
                print(f"   콜백 결과: {callback_result.get('status', 'N/A')}")
                if callback_result.get('event_id'):
                    print(f"   최종 생성된 이벤트 ID: {callback_result['event_id']}")
    
    print("\n6. 시스템 통계")
    print("-" * 30)
    
    # 확인 서비스 통계
    stats = confirmation_service.get_statistics()
    print(f"📊 확인 서비스 통계:")
    print(f"   전체 요청: {stats['total_requests']}")
    print(f"   완료된 요청: {stats['completed_requests']}")
    print(f"   상태별 분포: {stats['completed_by_status']}")
    
    # 알림 서비스 통계
    notification_history = notification_service.get_notification_history(limit=10)
    print(f"\n📨 알림 이력: {len(notification_history)}개")
    for i, notification in enumerate(notification_history, 1):
        print(f"   {i}. {notification.get('type', 'unknown')} - {notification.get('timestamp', 'N/A')}")
    
    print("\n=== 데모 완료 ===")
    print("\n🎉 이메일-캘린더 자동화 시스템이 성공적으로 작동했습니다!")
    print("\n주요 기능:")
    print("✅ 이메일에서 일정 정보 자동 추출")
    print("✅ 신뢰도 기반 자동/수동 처리")
    print("✅ 사용자 확인 요청 시스템")
    print("✅ 실시간 알림 시스템")
    print("✅ 캘린더 일정 자동 생성")

if __name__ == "__main__":
    demo_full_integration()