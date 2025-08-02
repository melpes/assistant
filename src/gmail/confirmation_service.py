"""
사용자 확인 요청 서비스

신뢰도가 낮은 일정 정보에 대한 사용자 확인 요청 및 응답 처리 기능을 제공합니다.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field

from .models import ExtractedEventInfo
from .exceptions import NotificationError

# 로깅 설정
logger = logging.getLogger(__name__)


@dataclass
class ConfirmationRequest:
    """사용자 확인 요청을 나타내는 데이터 클래스"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email_id: str = ""
    email_subject: str = ""
    event_info: ExtractedEventInfo = field(default_factory=ExtractedEventInfo)
    confidence_score: float = 0.0
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    status: str = "pending"  # pending, confirmed, rejected, expired
    response_data: Optional[Dict[str, Any]] = None
    callback_function: Optional[Callable] = None


class ConfirmationService:
    """사용자 확인 요청 서비스 클래스"""
    
    def __init__(self, notification_handlers: Optional[List[Callable]] = None):
        """
        ConfirmationService 초기화
        
        Args:
            notification_handlers: 알림 처리 함수들의 리스트
        """
        self.notification_handlers = notification_handlers or []
        self.pending_requests: Dict[str, ConfirmationRequest] = {}
        self.completed_requests: Dict[str, ConfirmationRequest] = {}
    
    def request_confirmation(
        self,
        event_info: ExtractedEventInfo,
        email_id: str,
        email_subject: str = "",
        callback_function: Optional[Callable] = None,
        expiry_hours: int = 24
    ) -> str:
        """
        사용자 확인 요청 생성
        
        Args:
            event_info: 확인이 필요한 일정 정보
            email_id: 원본 이메일 ID
            email_subject: 이메일 제목
            callback_function: 확인 완료 시 호출할 콜백 함수
            expiry_hours: 요청 만료 시간 (시간)
            
        Returns:
            생성된 확인 요청 ID
            
        Raises:
            NotificationError: 확인 요청 생성 실패 시
        """
        try:
            logger.info(f"사용자 확인 요청 생성: 이메일 ID={email_id}")
            
            # 확인 요청 객체 생성
            request = ConfirmationRequest(
                email_id=email_id,
                email_subject=email_subject,
                event_info=event_info,
                confidence_score=event_info.overall_confidence,
                confidence_breakdown=event_info.confidence_scores,
                expires_at=datetime.now() + timedelta(hours=expiry_hours),
                callback_function=callback_function
            )
            
            # 요청 저장
            self.pending_requests[request.id] = request
            
            # 알림 발송
            self._send_confirmation_notification(request)
            
            logger.info(f"사용자 확인 요청 생성 완료: 요청 ID={request.id}")
            return request.id
            
        except Exception as e:
            error_msg = f"사용자 확인 요청 생성 중 오류: {e}"
            logger.error(error_msg)
            raise NotificationError(error_msg, e)
    
    def process_confirmation_response(
        self,
        request_id: str,
        confirmed: bool,
        modified_data: Optional[Dict[str, Any]] = None,
        user_comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        사용자 확인 응답 처리
        
        Args:
            request_id: 확인 요청 ID
            confirmed: 확인 여부 (True: 승인, False: 거부)
            modified_data: 사용자가 수정한 데이터 (선택 사항)
            user_comment: 사용자 코멘트 (선택 사항)
            
        Returns:
            처리 결과
            
        Raises:
            NotificationError: 응답 처리 실패 시
        """
        try:
            logger.info(f"사용자 확인 응답 처리: 요청 ID={request_id}, 확인={confirmed}")
            
            # 요청 조회
            request = self.pending_requests.get(request_id)
            if not request:
                raise NotificationError(f"확인 요청을 찾을 수 없습니다: {request_id}")
            
            # 만료 확인
            if datetime.now() > request.expires_at:
                request.status = "expired"
                self._move_to_completed(request_id)
                return {
                    'success': False,
                    'status': 'expired',
                    'message': '확인 요청이 만료되었습니다.'
                }
            
            # 응답 데이터 설정
            response_data = {
                'confirmed': confirmed,
                'modified_data': modified_data,
                'user_comment': user_comment,
                'response_time': datetime.now().isoformat()
            }
            
            request.response_data = response_data
            request.status = "confirmed" if confirmed else "rejected"
            
            # 콜백 함수 실행
            callback_result = None
            if request.callback_function:
                try:
                    callback_result = request.callback_function(request_id, confirmed, modified_data)
                    logger.info(f"콜백 함수 실행 완료: 요청 ID={request_id}")
                except Exception as e:
                    logger.error(f"콜백 함수 실행 중 오류: {e}")
                    callback_result = {'error': str(e)}
            
            # 완료된 요청으로 이동
            self._move_to_completed(request_id)
            
            result = {
                'success': True,
                'request_id': request_id,
                'status': request.status,
                'confirmed': confirmed,
                'callback_result': callback_result,
                'message': '확인 응답이 성공적으로 처리되었습니다.'
            }
            
            if modified_data:
                result['modified_data'] = modified_data
            
            if user_comment:
                result['user_comment'] = user_comment
            
            logger.info(f"사용자 확인 응답 처리 완료: 요청 ID={request_id}")
            return result
            
        except Exception as e:
            error_msg = f"사용자 확인 응답 처리 중 오류: {e}"
            logger.error(error_msg)
            raise NotificationError(error_msg, e)
    
    def get_confirmation_request(self, request_id: str) -> Optional[ConfirmationRequest]:
        """
        확인 요청 조회
        
        Args:
            request_id: 확인 요청 ID
            
        Returns:
            확인 요청 객체 또는 None
        """
        # 대기 중인 요청에서 먼저 찾기
        request = self.pending_requests.get(request_id)
        if request:
            return request
        
        # 완료된 요청에서 찾기
        return self.completed_requests.get(request_id)
    
    def get_pending_requests(self, email_id: Optional[str] = None) -> List[ConfirmationRequest]:
        """
        대기 중인 확인 요청 목록 조회
        
        Args:
            email_id: 특정 이메일 ID로 필터링 (선택 사항)
            
        Returns:
            대기 중인 확인 요청 목록
        """
        requests = list(self.pending_requests.values())
        
        if email_id:
            requests = [req for req in requests if req.email_id == email_id]
        
        # 만료된 요청 정리
        self._cleanup_expired_requests()
        
        return requests
    
    def get_confirmation_status(self, request_id: str) -> Dict[str, Any]:
        """
        확인 요청 상태 조회
        
        Args:
            request_id: 확인 요청 ID
            
        Returns:
            확인 요청 상태 정보
        """
        request = self.get_confirmation_request(request_id)
        if not request:
            return {
                'found': False,
                'message': '확인 요청을 찾을 수 없습니다.'
            }
        
        # 만료 확인
        is_expired = datetime.now() > request.expires_at
        if is_expired and request.status == "pending":
            request.status = "expired"
            if request_id in self.pending_requests:
                self._move_to_completed(request_id)
        
        return {
            'found': True,
            'request_id': request_id,
            'status': request.status,
            'email_id': request.email_id,
            'email_subject': request.email_subject,
            'confidence_score': request.confidence_score,
            'created_at': request.created_at.isoformat(),
            'expires_at': request.expires_at.isoformat(),
            'is_expired': is_expired,
            'response_data': request.response_data
        }
    
    def cancel_confirmation_request(self, request_id: str) -> Dict[str, Any]:
        """
        확인 요청 취소
        
        Args:
            request_id: 취소할 확인 요청 ID
            
        Returns:
            취소 결과
        """
        try:
            request = self.pending_requests.get(request_id)
            if not request:
                return {
                    'success': False,
                    'message': '취소할 확인 요청을 찾을 수 없습니다.'
                }
            
            request.status = "cancelled"
            self._move_to_completed(request_id)
            
            logger.info(f"확인 요청 취소 완료: 요청 ID={request_id}")
            return {
                'success': True,
                'request_id': request_id,
                'status': 'cancelled',
                'message': '확인 요청이 취소되었습니다.'
            }
            
        except Exception as e:
            error_msg = f"확인 요청 취소 중 오류: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }
    
    def add_notification_handler(self, handler: Callable) -> None:
        """
        알림 처리 함수 추가
        
        Args:
            handler: 알림 처리 함수
        """
        if handler not in self.notification_handlers:
            self.notification_handlers.append(handler)
            logger.info("알림 처리 함수가 추가되었습니다.")
    
    def remove_notification_handler(self, handler: Callable) -> None:
        """
        알림 처리 함수 제거
        
        Args:
            handler: 제거할 알림 처리 함수
        """
        if handler in self.notification_handlers:
            self.notification_handlers.remove(handler)
            logger.info("알림 처리 함수가 제거되었습니다.")
    
    def _send_confirmation_notification(self, request: ConfirmationRequest) -> None:
        """
        확인 요청 알림 발송
        
        Args:
            request: 확인 요청 객체
        """
        try:
            # 알림 데이터 준비
            notification_data = {
                'type': 'confirmation_request',
                'request_id': request.id,
                'email_id': request.email_id,
                'email_subject': request.email_subject,
                'event_summary': request.event_info.summary,
                'confidence_score': request.confidence_score,
                'confidence_breakdown': request.confidence_breakdown,
                'event_details': self._format_event_for_notification(request.event_info),
                'expires_at': request.expires_at.isoformat(),
                'created_at': request.created_at.isoformat()
            }
            
            # 등록된 알림 처리 함수들 실행
            for handler in self.notification_handlers:
                try:
                    handler(notification_data)
                    logger.info(f"알림 처리 함수 실행 완료: 요청 ID={request.id}")
                except Exception as e:
                    logger.error(f"알림 처리 함수 실행 중 오류: {e}")
            
        except Exception as e:
            logger.error(f"확인 요청 알림 발송 중 오류: {e}")
    
    def _format_event_for_notification(self, event_info: ExtractedEventInfo) -> Dict[str, Any]:
        """
        알림용 일정 정보 포맷팅
        
        Args:
            event_info: 일정 정보
            
        Returns:
            포맷팅된 일정 정보
        """
        return {
            '제목': event_info.summary,
            '시작 시간': event_info.start_time.strftime('%Y년 %m월 %d일 %H:%M') if event_info.start_time else '미정',
            '종료 시간': event_info.end_time.strftime('%Y년 %m월 %d일 %H:%M') if event_info.end_time else '미정',
            '종일 일정': '예' if event_info.all_day else '아니오',
            '위치': event_info.location or '미정',
            '설명': event_info.description or '',
            '참석자': ', '.join(event_info.participants) if event_info.participants else '없음'
        }
    
    def _move_to_completed(self, request_id: str) -> None:
        """
        요청을 완료된 요청으로 이동
        
        Args:
            request_id: 이동할 요청 ID
        """
        if request_id in self.pending_requests:
            request = self.pending_requests.pop(request_id)
            self.completed_requests[request_id] = request
            logger.info(f"요청을 완료된 요청으로 이동: 요청 ID={request_id}")
    
    def _cleanup_expired_requests(self) -> None:
        """만료된 요청들을 정리"""
        current_time = datetime.now()
        expired_request_ids = []
        
        for request_id, request in self.pending_requests.items():
            if current_time > request.expires_at:
                request.status = "expired"
                expired_request_ids.append(request_id)
        
        # 만료된 요청들을 완료된 요청으로 이동
        for request_id in expired_request_ids:
            self._move_to_completed(request_id)
        
        if expired_request_ids:
            logger.info(f"만료된 요청 {len(expired_request_ids)}개를 정리했습니다.")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        확인 요청 통계 조회
        
        Returns:
            통계 정보
        """
        # 만료된 요청 정리
        self._cleanup_expired_requests()
        
        # 완료된 요청들의 상태별 통계
        completed_stats = {}
        for request in self.completed_requests.values():
            status = request.status
            completed_stats[status] = completed_stats.get(status, 0) + 1
        
        return {
            'pending_requests': len(self.pending_requests),
            'completed_requests': len(self.completed_requests),
            'completed_by_status': completed_stats,
            'total_requests': len(self.pending_requests) + len(self.completed_requests),
            'statistics_time': datetime.now().isoformat()
        }