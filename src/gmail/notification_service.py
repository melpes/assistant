"""
알림 서비스

일정 생성 결과 및 사용자 확인 요청에 대한 알림 기능을 제공합니다.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from enum import Enum

from ..calendar.models import CalendarEvent
from .models import ExtractedEventInfo
from .exceptions import NotificationError

# 로깅 설정
logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """알림 유형"""
    EVENT_CREATED = "event_created"
    CONFIRMATION_REQUEST = "confirmation_request"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"


class NotificationService:
    """사용자에게 알림을 보내는 클래스"""
    
    def __init__(self, email_service=None, console_output: bool = True):
        """
        NotificationService 초기화
        
        Args:
            email_service: 이메일 발송 서비스 (선택 사항)
            console_output: 콘솔 출력 여부
        """
        self.email_service = email_service
        self.console_output = console_output
        self.notification_handlers: List[Callable] = []
        self.notification_history: List[Dict[str, Any]] = []
    
    def notify_event_created(
        self,
        event_data: CalendarEvent,
        email_id: str,
        confidence_score: float = 0.0
    ) -> bool:
        """
        일정 생성 알림
        
        Args:
            event_data: 생성된 일정 데이터
            email_id: 원본 이메일 ID
            confidence_score: 신뢰도 점수
            
        Returns:
            알림 성공 여부
        """
        try:
            logger.info(f"일정 생성 알림: 이벤트 ID={event_data.id}")
            
            # 알림 데이터 준비
            notification_data = {
                'type': NotificationType.EVENT_CREATED.value,
                'title': '📅 새 일정이 생성되었습니다',
                'message': self._format_event_created_message(event_data, email_id, confidence_score),
                'event_id': event_data.id,
                'email_id': email_id,
                'confidence_score': confidence_score,
                'event_details': {
                    '제목': event_data.summary,
                    '시작 시간': event_data.start_time,
                    '종료 시간': event_data.end_time,
                    '위치': event_data.location,
                    '설명': event_data.description,
                    '종일 일정': event_data.all_day
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # 알림 발송
            return self._send_notification(notification_data)
            
        except Exception as e:
            error_msg = f"일정 생성 알림 중 오류: {e}"
            logger.error(error_msg)
            self.notify_error(error_msg, email_id)
            return False
    
    def request_confirmation(
        self,
        confirmation_data: Dict[str, Any],
        email_id: str
    ) -> str:
        """
        확인 요청 알림
        
        Args:
            confirmation_data: 확인 요청 데이터
            email_id: 원본 이메일 ID
            
        Returns:
            요청 ID
        """
        try:
            logger.info(f"확인 요청 알림: 이메일 ID={email_id}")
            
            # 요청 ID 생성 (이미 있으면 사용, 없으면 생성)
            request_id = confirmation_data.get('request_id')
            if not request_id:
                import uuid
                request_id = str(uuid.uuid4())
            
            # 알림 데이터 준비
            notification_data = {
                'type': NotificationType.CONFIRMATION_REQUEST.value,
                'title': '❓ 일정 생성 확인이 필요합니다',
                'message': self._format_confirmation_request_message_from_data(confirmation_data),
                'request_id': request_id,
                'email_id': email_id,
                'email_subject': confirmation_data.get('email_subject', ''),
                'confidence_score': confirmation_data.get('confidence_score', 0.0),
                'confidence_breakdown': confirmation_data.get('confidence_breakdown', {}),
                'event_details': confirmation_data.get('event_details', {}),
                'timestamp': datetime.now().isoformat()
            }
            
            # 알림 발송
            self._send_notification(notification_data)
            
            return request_id
            
        except Exception as e:
            error_msg = f"확인 요청 알림 중 오류: {e}"
            logger.error(error_msg)
            raise NotificationError(error_msg, e)
    
    def notify_error(self, error_message: str, email_id: str = "") -> bool:
        """
        오류 알림
        
        Args:
            error_message: 오류 메시지
            email_id: 관련 이메일 ID (선택 사항)
            
        Returns:
            알림 성공 여부
        """
        try:
            logger.error(f"오류 알림: {error_message}")
            
            # 알림 데이터 준비
            notification_data = {
                'type': NotificationType.ERROR.value,
                'title': '❌ 오류가 발생했습니다',
                'message': error_message,
                'email_id': email_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # 알림 발송
            return self._send_notification(notification_data)
            
        except Exception as e:
            logger.error(f"오류 알림 발송 중 오류: {e}")
            return False
    
    def notify_info(self, message: str, title: str = "정보", email_id: str = "") -> bool:
        """
        정보 알림
        
        Args:
            message: 알림 메시지
            title: 알림 제목
            email_id: 관련 이메일 ID (선택 사항)
            
        Returns:
            알림 성공 여부
        """
        try:
            logger.info(f"정보 알림: {message}")
            
            # 알림 데이터 준비
            notification_data = {
                'type': NotificationType.INFO.value,
                'title': f'ℹ️ {title}',
                'message': message,
                'email_id': email_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # 알림 발송
            return self._send_notification(notification_data)
            
        except Exception as e:
            logger.error(f"정보 알림 발송 중 오류: {e}")
            return False
    
    def notify_warning(self, message: str, title: str = "경고", email_id: str = "") -> bool:
        """
        경고 알림
        
        Args:
            message: 경고 메시지
            title: 알림 제목
            email_id: 관련 이메일 ID (선택 사항)
            
        Returns:
            알림 성공 여부
        """
        try:
            logger.warning(f"경고 알림: {message}")
            
            # 알림 데이터 준비
            notification_data = {
                'type': NotificationType.WARNING.value,
                'title': f'⚠️ {title}',
                'message': message,
                'email_id': email_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # 알림 발송
            return self._send_notification(notification_data)
            
        except Exception as e:
            logger.error(f"경고 알림 발송 중 오류: {e}")
            return False
    
    def add_notification_handler(self, handler: Callable[[Dict[str, Any]], bool]) -> None:
        """
        알림 처리 함수 추가
        
        Args:
            handler: 알림 처리 함수 (알림 데이터를 받아 성공 여부를 반환)
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
    
    def get_notification_history(
        self,
        limit: int = 50,
        notification_type: Optional[NotificationType] = None
    ) -> List[Dict[str, Any]]:
        """
        알림 이력 조회
        
        Args:
            limit: 조회할 최대 개수
            notification_type: 필터링할 알림 유형
            
        Returns:
            알림 이력 목록
        """
        history = self.notification_history
        
        # 유형별 필터링
        if notification_type:
            history = [n for n in history if n.get('type') == notification_type.value]
        
        # 최신 순으로 정렬하고 제한
        history = sorted(history, key=lambda x: x.get('timestamp', ''), reverse=True)
        return history[:limit]
    
    def clear_notification_history(self) -> None:
        """알림 이력 삭제"""
        self.notification_history.clear()
        logger.info("알림 이력이 삭제되었습니다.")
    
    def _send_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        알림 발송
        
        Args:
            notification_data: 알림 데이터
            
        Returns:
            발송 성공 여부
        """
        success = True
        
        try:
            # 콘솔 출력
            if self.console_output:
                self._print_console_notification(notification_data)
            
            # 등록된 처리 함수들 실행
            for handler in self.notification_handlers:
                try:
                    handler_success = handler(notification_data)
                    if not handler_success:
                        success = False
                        logger.warning("알림 처리 함수에서 실패를 반환했습니다.")
                except Exception as e:
                    logger.error(f"알림 처리 함수 실행 중 오류: {e}")
                    success = False
            
            # 이메일 발송 (이메일 서비스가 있는 경우)
            if self.email_service:
                try:
                    email_success = self._send_email_notification(notification_data)
                    if not email_success:
                        success = False
                except Exception as e:
                    logger.error(f"이메일 알림 발송 중 오류: {e}")
                    success = False
            
            # 이력에 추가
            self.notification_history.append(notification_data)
            
            # 이력 크기 제한 (최대 1000개)
            if len(self.notification_history) > 1000:
                self.notification_history = self.notification_history[-1000:]
            
            return success
            
        except Exception as e:
            logger.error(f"알림 발송 중 오류: {e}")
            return False
    
    def _print_console_notification(self, notification_data: Dict[str, Any]) -> None:
        """
        콘솔에 알림 출력
        
        Args:
            notification_data: 알림 데이터
        """
        try:
            print("\n" + "=" * 60)
            print(f"🔔 {notification_data.get('title', '알림')}")
            print("=" * 60)
            print(f"메시지: {notification_data.get('message', '')}")
            
            if notification_data.get('email_id'):
                print(f"이메일 ID: {notification_data['email_id']}")
            
            if notification_data.get('confidence_score'):
                print(f"신뢰도: {notification_data['confidence_score']:.2f}")
            
            if notification_data.get('event_details'):
                print("\n📋 일정 세부사항:")
                for key, value in notification_data['event_details'].items():
                    if value:
                        print(f"  • {key}: {value}")
            
            print(f"시간: {notification_data.get('timestamp', '')}")
            print("=" * 60 + "\n")
            
        except Exception as e:
            logger.error(f"콘솔 알림 출력 중 오류: {e}")
    
    def _send_email_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        이메일 알림 발송
        
        Args:
            notification_data: 알림 데이터
            
        Returns:
            발송 성공 여부
        """
        try:
            if not self.email_service:
                return True
            
            # 이메일 제목과 내용 생성
            subject = notification_data.get('title', '알림')
            body = self._format_email_body(notification_data)
            
            # 이메일 발송 (실제 구현은 이메일 서비스에 따라 달라짐)
            # 여기서는 인터페이스만 정의
            return self.email_service.send_notification_email(subject, body)
            
        except Exception as e:
            logger.error(f"이메일 알림 발송 중 오류: {e}")
            return False
    
    def _format_email_body(self, notification_data: Dict[str, Any]) -> str:
        """
        이메일 본문 포맷팅
        
        Args:
            notification_data: 알림 데이터
            
        Returns:
            포맷팅된 이메일 본문
        """
        body_parts = [
            notification_data.get('message', ''),
            ""
        ]
        
        if notification_data.get('email_id'):
            body_parts.append(f"관련 이메일 ID: {notification_data['email_id']}")
        
        if notification_data.get('confidence_score'):
            body_parts.append(f"신뢰도: {notification_data['confidence_score']:.2f}")
        
        if notification_data.get('event_details'):
            body_parts.append("\n일정 세부사항:")
            for key, value in notification_data['event_details'].items():
                if value:
                    body_parts.append(f"  • {key}: {value}")
        
        body_parts.append(f"\n발송 시간: {notification_data.get('timestamp', '')}")
        
        return "\n".join(body_parts)
    
    def _format_event_created_message(
        self,
        event_data: CalendarEvent,
        email_id: str,
        confidence_score: float
    ) -> str:
        """
        일정 생성 알림 메시지 포맷팅
        
        Args:
            event_data: 일정 데이터
            email_id: 이메일 ID
            confidence_score: 신뢰도 점수
            
        Returns:
            포맷팅된 메시지
        """
        message_parts = [
            f"'{event_data.summary}' 일정이 자동으로 생성되었습니다.",
            f"신뢰도: {confidence_score:.2f}",
            f"원본 이메일 ID: {email_id}"
        ]
        
        if event_data.start_time:
            message_parts.append(f"시작 시간: {event_data.start_time}")
        
        if event_data.location:
            message_parts.append(f"위치: {event_data.location}")
        
        return "\n".join(message_parts)
    
    def _format_confirmation_request_message(
        self,
        event_info: ExtractedEventInfo,
        email_id: str,
        email_subject: str
    ) -> str:
        """
        확인 요청 알림 메시지 포맷팅
        
        Args:
            event_info: 일정 정보
            email_id: 이메일 ID
            email_subject: 이메일 제목
            
        Returns:
            포맷팅된 메시지
        """
        message_parts = [
            f"'{event_info.summary}' 일정 생성에 대한 확인이 필요합니다.",
            f"신뢰도가 낮아 사용자 확인을 요청합니다. (신뢰도: {event_info.overall_confidence:.2f})",
            f"원본 이메일: {email_subject}" if email_subject else f"원본 이메일 ID: {email_id}"
        ]
        
        # 신뢰도가 낮은 항목들 표시
        low_confidence_items = [
            key for key, score in event_info.confidence_scores.items()
            if score < 0.7
        ]
        
        if low_confidence_items:
            message_parts.append(f"신뢰도가 낮은 항목: {', '.join(low_confidence_items)}")
        
        return "\n".join(message_parts)
    
    def _format_confirmation_request_message_from_data(
        self,
        confirmation_data: Dict[str, Any]
    ) -> str:
        """
        확인 요청 데이터로부터 알림 메시지 포맷팅
        
        Args:
            confirmation_data: 확인 요청 데이터
            
        Returns:
            포맷팅된 메시지
        """
        event_info = confirmation_data.get('event_info', {})
        email_id = confirmation_data.get('email_id', '')
        email_subject = confirmation_data.get('email_subject', '')
        confidence_score = confirmation_data.get('confidence_score', 0.0)
        confidence_breakdown = confirmation_data.get('confidence_breakdown', {})
        
        summary = event_info.get('summary', '알 수 없는 일정') if isinstance(event_info, dict) else getattr(event_info, 'summary', '알 수 없는 일정')
        
        message_parts = [
            f"'{summary}' 일정 생성에 대한 확인이 필요합니다.",
            f"신뢰도가 낮아 사용자 확인을 요청합니다. (신뢰도: {confidence_score:.2f})",
            f"원본 이메일: {email_subject}" if email_subject else f"원본 이메일 ID: {email_id}"
        ]
        
        # 신뢰도가 낮은 항목들 표시
        if confidence_breakdown:
            low_confidence_items = [
                key for key, score in confidence_breakdown.items()
                if score < 0.7
            ]
            
            if low_confidence_items:
                message_parts.append(f"신뢰도가 낮은 항목: {', '.join(low_confidence_items)}")
        
        return "\n".join(message_parts)