#!/usr/bin/env python3
"""
사용자 확인 요청 시스템 수동 테스트
"""

import sys
sys.path.append('.')

from datetime import datetime, timedelta
from src.gmail.confirmation_service import ConfirmationService
from src.gmail.models import ExtractedEventInfo

def test_confirmation_service():
    """확인 서비스 기본 기능 테스트"""
    print("=== 사용자 확인 요청 시스템 테스트 시작 ===\n")
    
    # 서비스 초기화
    def mock_notification_handler(data):
        print(f"📧 알림 발송: {data['type']}")
        print(f"   제목: {data.get('title', 'N/A')}")
        print(f"   요청 ID: {data.get('request_id', 'N/A')}")
        return True
    
    service = ConfirmationService([mock_notification_handler])
    
    # 테스트용 일정 정보
    event_info = ExtractedEventInfo(
        summary="중요한 회의",
        start_time=datetime(2024, 1, 15, 14, 0),
        end_time=datetime(2024, 1, 15, 15, 0),
        location="회의실 A",
        description="프로젝트 진행 상황 논의",
        participants=["colleague@example.com"],
        all_day=False,
        confidence_scores={
            "summary": 0.9,
            "start_time": 0.5,  # 낮은 신뢰도
            "location": 0.8,
            "participants": 0.7
        },
        overall_confidence=0.6  # 임계값 이하
    )
    
    print("1. 확인 요청 생성 테스트")
    print("-" * 40)
    
    # 확인 요청 생성
    request_id = service.request_confirmation(
        event_info=event_info,
        email_id="test_email_123",
        email_subject="회의 일정 안내",
        expiry_hours=24
    )
    
    print(f"✅ 확인 요청 생성 완료: {request_id}")
    print(f"   대기 중인 요청 수: {len(service.pending_requests)}")
    
    print("\n2. 확인 요청 상태 조회 테스트")
    print("-" * 40)
    
    status = service.get_confirmation_status(request_id)
    print(f"✅ 요청 상태: {status['status']}")
    print(f"   신뢰도: {status['confidence_score']}")
    print(f"   만료 시간: {status['expires_at']}")
    
    print("\n3. 사용자 응답 처리 테스트 (승인)")
    print("-" * 40)
    
    # 콜백 함수 정의
    def test_callback(req_id, confirmed, modified_data):
        print(f"🔄 콜백 함수 실행: 요청 ID={req_id}, 확인={confirmed}")
        if modified_data:
            print(f"   수정된 데이터: {modified_data}")
        return {"event_id": "created_event_456", "status": "success"}
    
    # 콜백 함수 설정
    service.pending_requests[request_id].callback_function = test_callback
    
    # 사용자 응답 처리
    modified_data = {
        "start_time": "2024-01-15T15:00:00",
        "location": "회의실 B"
    }
    
    result = service.process_confirmation_response(
        request_id=request_id,
        confirmed=True,
        modified_data=modified_data,
        user_comment="시간과 장소를 조정했습니다"
    )
    
    print(f"✅ 응답 처리 완료: {result['status']}")
    print(f"   콜백 결과: {result.get('callback_result', 'N/A')}")
    print(f"   완료된 요청 수: {len(service.completed_requests)}")
    
    print("\n4. 통계 조회 테스트")
    print("-" * 40)
    
    stats = service.get_statistics()
    print(f"✅ 통계 정보:")
    print(f"   대기 중인 요청: {stats['pending_requests']}")
    print(f"   완료된 요청: {stats['completed_requests']}")
    print(f"   전체 요청: {stats['total_requests']}")
    print(f"   상태별 완료 요청: {stats['completed_by_status']}")
    
    print("\n5. 거부 응답 테스트")
    print("-" * 40)
    
    # 새로운 요청 생성
    request_id2 = service.request_confirmation(
        event_info=event_info,
        email_id="test_email_456",
        email_subject="또 다른 회의"
    )
    
    # 거부 응답
    result2 = service.process_confirmation_response(
        request_id=request_id2,
        confirmed=False,
        user_comment="일정이 취소되었습니다"
    )
    
    print(f"✅ 거부 응답 처리 완료: {result2['status']}")
    print(f"   사용자 코멘트: {result2.get('user_comment', 'N/A')}")
    
    print("\n=== 테스트 완료 ===")
    
    # 최종 통계
    final_stats = service.get_statistics()
    print(f"\n📊 최종 통계:")
    print(f"   전체 요청: {final_stats['total_requests']}")
    print(f"   완료된 요청: {final_stats['completed_requests']}")
    print(f"   상태별 분포: {final_stats['completed_by_status']}")

if __name__ == "__main__":
    test_confirmation_service()