"""
사용자 확인 요청 서비스 테스트
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.gmail.confirmation_service import ConfirmationService, ConfirmationRequest
from src.gmail.models import ExtractedEventInfo
from src.gmail.exceptions import NotificationError


class TestConfirmationService:
    """ConfirmationService 테스트 클래스"""
    
    def setup_method(self):
        """테스트 설정"""
        self.mock_notification_handler = Mock()
        self.service = ConfirmationService([self.mock_notification_handler])
        
        # 테스트용 일정 정보
        self.test_event_info = ExtractedEventInfo(
            summary="테스트 회의",
            start_time=datetime(2024, 1, 15, 14, 0),
            end_time=datetime(2024, 1, 15, 15, 0),
            location="회의실 A",
            description="중요한 회의입니다",
            participants=["test@example.com"],
            all_day=False,
            confidence_scores={
                "summary": 0.9,
                "start_time": 0.6,  # 낮은 신뢰도
                "location": 0.8
            },
            overall_confidence=0.7
        )
    
    def test_request_confirmation_success(self):
        """확인 요청 생성 성공 테스트"""
        # Given
        email_id = "test_email_123"
        email_subject = "회의 일정 안내"
        
        # When
        request_id = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id=email_id,
            email_subject=email_subject
        )
        
        # Then
        assert request_id is not None
        assert len(request_id) > 0
        assert request_id in self.service.pending_requests
        
        # 요청 내용 확인
        request = self.service.pending_requests[request_id]
        assert request.email_id == email_id
        assert request.email_subject == email_subject
        assert request.event_info == self.test_event_info
        assert request.status == "pending"
        
        # 알림 핸들러 호출 확인
        self.mock_notification_handler.assert_called_once()
    
    def test_request_confirmation_with_callback(self):
        """콜백 함수와 함께 확인 요청 생성 테스트"""
        # Given
        callback_mock = Mock()
        email_id = "test_email_123"
        
        # When
        request_id = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id=email_id,
            callback_function=callback_mock
        )
        
        # Then
        request = self.service.pending_requests[request_id]
        assert request.callback_function == callback_mock
    
    def test_process_confirmation_response_confirmed(self):
        """확인 응답 처리 - 승인 테스트"""
        # Given
        request_id = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="test_email_123"
        )
        
        modified_data = {
            "start_time": "2024-01-15T15:00:00",
            "location": "회의실 B"
        }
        user_comment = "시간과 장소를 수정했습니다"
        
        # When
        result = self.service.process_confirmation_response(
            request_id=request_id,
            confirmed=True,
            modified_data=modified_data,
            user_comment=user_comment
        )
        
        # Then
        assert result['success'] is True
        assert result['confirmed'] is True
        assert result['status'] == "confirmed"
        assert result['modified_data'] == modified_data
        assert result['user_comment'] == user_comment
        
        # 요청이 완료된 요청으로 이동했는지 확인
        assert request_id not in self.service.pending_requests
        assert request_id in self.service.completed_requests
    
    def test_process_confirmation_response_rejected(self):
        """확인 응답 처리 - 거부 테스트"""
        # Given
        request_id = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="test_email_123"
        )
        
        # When
        result = self.service.process_confirmation_response(
            request_id=request_id,
            confirmed=False,
            user_comment="일정이 취소되었습니다"
        )
        
        # Then
        assert result['success'] is True
        assert result['confirmed'] is False
        assert result['status'] == "rejected"
        assert result['user_comment'] == "일정이 취소되었습니다"
    
    def test_process_confirmation_response_with_callback(self):
        """콜백 함수와 함께 확인 응답 처리 테스트"""
        # Given
        callback_mock = Mock(return_value={"event_id": "created_event_123"})
        request_id = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="test_email_123",
            callback_function=callback_mock
        )
        
        # When
        result = self.service.process_confirmation_response(
            request_id=request_id,
            confirmed=True
        )
        
        # Then
        callback_mock.assert_called_once_with(request_id, True, None)
        assert result['callback_result'] == {"event_id": "created_event_123"}
    
    def test_process_confirmation_response_callback_error(self):
        """콜백 함수 오류 처리 테스트"""
        # Given
        callback_mock = Mock(side_effect=Exception("콜백 오류"))
        request_id = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="test_email_123",
            callback_function=callback_mock
        )
        
        # When
        result = self.service.process_confirmation_response(
            request_id=request_id,
            confirmed=True
        )
        
        # Then
        assert result['success'] is True  # 콜백 오류가 있어도 응답 처리는 성공
        assert 'error' in result['callback_result']
    
    def test_process_confirmation_response_not_found(self):
        """존재하지 않는 요청에 대한 응답 처리 테스트"""
        # Given
        non_existent_id = "non_existent_request"
        
        # When & Then
        with pytest.raises(NotificationError, match="확인 요청을 찾을 수 없습니다"):
            self.service.process_confirmation_response(
                request_id=non_existent_id,
                confirmed=True
            )
    
    def test_process_confirmation_response_expired(self):
        """만료된 요청에 대한 응답 처리 테스트"""
        # Given
        with patch('src.gmail.confirmation_service.datetime') as mock_datetime:
            # 과거 시간으로 설정하여 즉시 만료되도록 함
            past_time = datetime.now() - timedelta(hours=25)
            mock_datetime.now.return_value = past_time
            
            request_id = self.service.request_confirmation(
                event_info=self.test_event_info,
                email_id="test_email_123",
                expiry_hours=24
            )
            
            # 현재 시간으로 복원
            mock_datetime.now.return_value = datetime.now()
            
            # When
            result = self.service.process_confirmation_response(
                request_id=request_id,
                confirmed=True
            )
            
            # Then
            assert result['success'] is False
            assert result['status'] == 'expired'
    
    def test_get_confirmation_request(self):
        """확인 요청 조회 테스트"""
        # Given
        request_id = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="test_email_123"
        )
        
        # When
        request = self.service.get_confirmation_request(request_id)
        
        # Then
        assert request is not None
        assert request.id == request_id
        assert request.email_id == "test_email_123"
    
    def test_get_confirmation_request_not_found(self):
        """존재하지 않는 확인 요청 조회 테스트"""
        # Given
        non_existent_id = "non_existent_request"
        
        # When
        request = self.service.get_confirmation_request(non_existent_id)
        
        # Then
        assert request is None
    
    def test_get_pending_requests(self):
        """대기 중인 확인 요청 목록 조회 테스트"""
        # Given
        request_id1 = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="email_1"
        )
        request_id2 = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="email_2"
        )
        
        # When
        pending_requests = self.service.get_pending_requests()
        
        # Then
        assert len(pending_requests) == 2
        request_ids = [req.id for req in pending_requests]
        assert request_id1 in request_ids
        assert request_id2 in request_ids
    
    def test_get_pending_requests_filtered_by_email(self):
        """이메일 ID로 필터링된 대기 중인 확인 요청 조회 테스트"""
        # Given
        self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="email_1"
        )
        request_id2 = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="email_2"
        )
        
        # When
        filtered_requests = self.service.get_pending_requests(email_id="email_2")
        
        # Then
        assert len(filtered_requests) == 1
        assert filtered_requests[0].id == request_id2
        assert filtered_requests[0].email_id == "email_2"
    
    def test_get_confirmation_status(self):
        """확인 요청 상태 조회 테스트"""
        # Given
        request_id = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="test_email_123",
            email_subject="테스트 이메일"
        )
        
        # When
        status = self.service.get_confirmation_status(request_id)
        
        # Then
        assert status['found'] is True
        assert status['request_id'] == request_id
        assert status['status'] == "pending"
        assert status['email_id'] == "test_email_123"
        assert status['email_subject'] == "테스트 이메일"
        assert status['confidence_score'] == 0.7
        assert 'created_at' in status
        assert 'expires_at' in status
        assert status['is_expired'] is False
    
    def test_get_confirmation_status_not_found(self):
        """존재하지 않는 확인 요청 상태 조회 테스트"""
        # Given
        non_existent_id = "non_existent_request"
        
        # When
        status = self.service.get_confirmation_status(non_existent_id)
        
        # Then
        assert status['found'] is False
        assert '확인 요청을 찾을 수 없습니다' in status['message']
    
    def test_cancel_confirmation_request(self):
        """확인 요청 취소 테스트"""
        # Given
        request_id = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="test_email_123"
        )
        
        # When
        result = self.service.cancel_confirmation_request(request_id)
        
        # Then
        assert result['success'] is True
        assert result['status'] == 'cancelled'
        assert request_id not in self.service.pending_requests
        assert request_id in self.service.completed_requests
    
    def test_cancel_confirmation_request_not_found(self):
        """존재하지 않는 확인 요청 취소 테스트"""
        # Given
        non_existent_id = "non_existent_request"
        
        # When
        result = self.service.cancel_confirmation_request(non_existent_id)
        
        # Then
        assert result['success'] is False
        assert '취소할 확인 요청을 찾을 수 없습니다' in result['message']
    
    def test_add_remove_notification_handler(self):
        """알림 처리 함수 추가/제거 테스트"""
        # Given
        new_handler = Mock()
        
        # When - 추가
        self.service.add_notification_handler(new_handler)
        
        # Then
        assert new_handler in self.service.notification_handlers
        
        # When - 제거
        self.service.remove_notification_handler(new_handler)
        
        # Then
        assert new_handler not in self.service.notification_handlers
    
    def test_cleanup_expired_requests(self):
        """만료된 요청 정리 테스트"""
        # Given
        with patch('src.gmail.confirmation_service.datetime') as mock_datetime:
            # 과거 시간으로 요청 생성
            past_time = datetime.now() - timedelta(hours=25)
            mock_datetime.now.return_value = past_time
            
            request_id = self.service.request_confirmation(
                event_info=self.test_event_info,
                email_id="test_email_123",
                expiry_hours=24
            )
            
            # 현재 시간으로 복원
            mock_datetime.now.return_value = datetime.now()
            
            # When
            self.service._cleanup_expired_requests()
            
            # Then
            assert request_id not in self.service.pending_requests
            assert request_id in self.service.completed_requests
            assert self.service.completed_requests[request_id].status == "expired"
    
    def test_get_statistics(self):
        """통계 조회 테스트"""
        # Given
        # 대기 중인 요청 생성
        self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="email_1"
        )
        
        # 완료된 요청 생성
        request_id2 = self.service.request_confirmation(
            event_info=self.test_event_info,
            email_id="email_2"
        )
        self.service.process_confirmation_response(request_id2, confirmed=True)
        
        # When
        stats = self.service.get_statistics()
        
        # Then
        assert stats['pending_requests'] == 1
        assert stats['completed_requests'] == 1
        assert stats['total_requests'] == 2
        assert 'confirmed' in stats['completed_by_status']
        assert stats['completed_by_status']['confirmed'] == 1
        assert 'statistics_time' in stats
    
    def test_notification_handler_exception(self):
        """알림 핸들러 예외 처리 테스트"""
        # Given
        failing_handler = Mock(side_effect=Exception("핸들러 오류"))
        service = ConfirmationService([failing_handler])
        
        # When & Then - 예외가 발생해도 요청 생성은 성공해야 함
        request_id = service.request_confirmation(
            event_info=self.test_event_info,
            email_id="test_email_123"
        )
        
        assert request_id is not None
        assert request_id in service.pending_requests
     