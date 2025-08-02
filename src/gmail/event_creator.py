"""
일정 생성기 모듈

이메일에서 추출된 정보를 기반으로 캘린더 일정을 생성하는 기능을 제공합니다.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

from ..calendar.service import CalendarService
from ..calendar.models import CalendarEvent
from ..calendar.exceptions import CalendarServiceError, InvalidEventDataError
from .models import ExtractedEventInfo, EventHistory
from .exceptions import EventCreationError
from .confirmation_service import ConfirmationService
from .notification_service import NotificationService

# 로깅 설정
logger = logging.getLogger(__name__)


class EventCreator:
    """추출된 정보를 기반으로 캘린더 일정을 생성하는 클래스"""
    
    def __init__(
        self,
        calendar_service: CalendarService,
        event_history_repository=None,
        notification_service: Optional[NotificationService] = None,
        confirmation_service: Optional[ConfirmationService] = None,
        min_confidence_threshold: float = 0.7
    ):
        """
        EventCreator 초기화
        
        Args:
            calendar_service: 캘린더 서비스 인스턴스
            event_history_repository: 일정 이력 저장소 (선택 사항)
            notification_service: 알림 서비스 (선택 사항)
            confirmation_service: 확인 요청 서비스 (선택 사항)
            min_confidence_threshold: 최소 신뢰도 임계값
        """
        self.calendar_service = calendar_service
        self.event_history_repository = event_history_repository
        self.notification_service = notification_service or NotificationService()
        self.confirmation_service = confirmation_service or ConfirmationService()
        self.min_confidence_threshold = min_confidence_threshold
    
    def create_event(
        self,
        event_info: ExtractedEventInfo,
        email_id: str,
        email_subject: str = "",
        rule_id: Optional[int] = None,
        require_confirmation: bool = True
    ) -> Dict[str, Any]:
        """
        일정 생성
        
        Args:
            event_info: 추출된 일정 정보
            email_id: 원본 이메일 ID
            email_subject: 이메일 제목 (선택 사항)
            rule_id: 적용된 규칙 ID (선택 사항)
            require_confirmation: 사용자 확인 요청 여부
            
        Returns:
            생성 결과 정보
            
        Raises:
            EventCreationError: 일정 생성 실패 시
        """
        try:
            logger.info(f"일정 생성 시작: 이메일 ID={email_id}, 신뢰도={event_info.overall_confidence}")
            
            # 신뢰도 확인
            if event_info.overall_confidence < self.min_confidence_threshold and require_confirmation:
                logger.info(f"신뢰도가 낮아 사용자 확인 요청: {event_info.overall_confidence}")
                return self._request_user_confirmation_via_service(event_info, email_id, email_subject, rule_id)
            
            # 일정 데이터 검증
            self._validate_event_info(event_info)
            
            # CalendarEvent 객체 생성
            calendar_event = self._create_calendar_event(event_info, email_id, email_subject)
            
            # 캘린더에 일정 생성
            created_event = self.calendar_service.create_new_event(
                summary=calendar_event.summary,
                start_time=calendar_event.start_time,
                end_time=calendar_event.end_time,
                description=calendar_event.description,
                location=calendar_event.location,
                all_day=calendar_event.all_day,
                format_response=False
            )
            
            logger.info(f"일정 생성 완료: 이벤트 ID={created_event.id}")
            
            # 일정 이력 저장
            if self.event_history_repository:
                self._save_event_history(
                    created_event.id,
                    email_id,
                    rule_id,
                    event_info.overall_confidence,
                    event_info.to_dict(),
                    "created"
                )
            
            # 알림 발송
            if self.notification_service:
                self.notification_service.notify_event_created(created_event, email_id)
            
            return {
                'success': True,
                'event_id': created_event.id,
                'event_data': created_event,
                'confidence_score': event_info.overall_confidence,
                'status': 'created',
                'message': '일정이 성공적으로 생성되었습니다.'
            }
            
        except CalendarServiceError as e:
            error_msg = f"캘린더 서비스 오류: {e}"
            logger.error(f"일정 생성 실패: {error_msg}")
            raise EventCreationError(error_msg, e)
        except Exception as e:
            error_msg = f"일정 생성 중 예상치 못한 오류: {e}"
            logger.error(f"일정 생성 실패: {error_msg}")
            raise EventCreationError(error_msg, e)
    
    def request_user_confirmation(
        self,
        event_info: ExtractedEventInfo,
        email_id: str,
        email_subject: str = ""
    ) -> Dict[str, Any]:
        """
        사용자 확인 요청
        
        Args:
            event_info: 일정 정보
            email_subject: 이메일 제목
            email_id: 이메일 ID
            
        Returns:
            확인 요청 결과
        """
        try:
            logger.info(f"사용자 확인 요청: 이메일 ID={email_id}")
            
            confirmation_data = {
                'event_info': event_info.to_dict(),
                'email_id': email_id,
                'email_subject': email_subject,
                'confidence_score': event_info.overall_confidence,
                'confidence_breakdown': event_info.confidence_scores,
                'requires_confirmation': True
            }
            
            # 알림 서비스를 통해 확인 요청
            if self.notification_service:
                request_id = self.notification_service.request_confirmation(
                    confirmation_data,
                    email_id
                )
                confirmation_data['request_id'] = request_id
            
            return {
                'success': True,
                'status': 'pending_confirmation',
                'confirmation_data': confirmation_data,
                'message': f'신뢰도가 낮아 사용자 확인이 필요합니다. (신뢰도: {event_info.overall_confidence:.2f})'
            }
            
        except Exception as e:
            error_msg = f"사용자 확인 요청 중 오류: {e}"
            logger.error(error_msg)
            raise EventCreationError(error_msg, e)
    
    def process_user_confirmation(
        self,
        request_id: str,
        confirmed: bool,
        modified_event_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        사용자 확인 응답 처리
        
        Args:
            request_id: 확인 요청 ID
            confirmed: 확인 여부
            modified_event_info: 수정된 일정 정보 (선택 사항)
            
        Returns:
            처리 결과
        """
        try:
            logger.info(f"사용자 확인 응답 처리: 요청 ID={request_id}, 확인={confirmed}")
            
            if not confirmed:
                return {
                    'success': True,
                    'status': 'cancelled',
                    'message': '사용자가 일정 생성을 취소했습니다.'
                }
            
            # 수정된 정보가 있으면 적용
            if modified_event_info:
                # 수정된 정보로 일정 생성
                # 여기서는 간단히 구현하고, 실제로는 더 복잡한 로직이 필요할 수 있습니다
                logger.info("수정된 정보로 일정 생성")
                # TODO: 수정된 정보를 ExtractedEventInfo로 변환하여 create_event 호출
            
            return {
                'success': True,
                'status': 'confirmed',
                'message': '사용자 확인이 완료되었습니다.'
            }
            
        except Exception as e:
            error_msg = f"사용자 확인 응답 처리 중 오류: {e}"
            logger.error(error_msg)
            raise EventCreationError(error_msg, e)
    
    def update_event(
        self,
        event_id: str,
        event_info: ExtractedEventInfo,
        email_id: str,
        email_subject: str = ""
    ) -> Dict[str, Any]:
        """
        기존 일정 수정
        
        Args:
            event_id: 수정할 일정 ID
            event_info: 새로운 일정 정보
            email_id: 원본 이메일 ID
            email_subject: 이메일 제목
            
        Returns:
            수정 결과
        """
        try:
            logger.info(f"일정 수정: 이벤트 ID={event_id}")
            
            # 일정 데이터 검증
            self._validate_event_info(event_info)
            
            # 기존 일정 조회
            existing_event = self.calendar_service.get_event_details(event_id, format_response=False)
            if not existing_event:
                raise EventCreationError(f"수정할 일정을 찾을 수 없습니다: {event_id}")
            
            # 설명에 원본 이메일 참조 추가
            description = self._create_event_description(event_info.description, email_id, email_subject)
            
            # 일정 수정
            updated_event = self.calendar_service.update_event(
                event_id=event_id,
                summary=event_info.summary,
                start_time=event_info.start_time,
                end_time=event_info.end_time,
                description=description,
                location=event_info.location,
                all_day=event_info.all_day,
                format_response=False
            )
            
            logger.info(f"일정 수정 완료: 이벤트 ID={event_id}")
            
            # 일정 이력 업데이트
            if self.event_history_repository:
                self._save_event_history(
                    event_id,
                    email_id,
                    None,
                    event_info.overall_confidence,
                    event_info.to_dict(),
                    "modified"
                )
            
            return {
                'success': True,
                'event_id': event_id,
                'event_data': updated_event,
                'confidence_score': event_info.overall_confidence,
                'status': 'modified',
                'message': '일정이 성공적으로 수정되었습니다.'
            }
            
        except Exception as e:
            error_msg = f"일정 수정 중 오류: {e}"
            logger.error(error_msg)
            raise EventCreationError(error_msg, e)
    
    def delete_event(self, event_id: str, email_id: str) -> Dict[str, Any]:
        """
        일정 삭제
        
        Args:
            event_id: 삭제할 일정 ID
            email_id: 원본 이메일 ID
            
        Returns:
            삭제 결과
        """
        try:
            logger.info(f"일정 삭제: 이벤트 ID={event_id}")
            
            # 일정 삭제
            success = self.calendar_service.delete_event(event_id)
            
            if success:
                logger.info(f"일정 삭제 완료: 이벤트 ID={event_id}")
                
                # 일정 이력 업데이트
                if self.event_history_repository:
                    self._save_event_history(
                        event_id,
                        email_id,
                        None,
                        0.0,
                        {},
                        "deleted"
                    )
                
                return {
                    'success': True,
                    'event_id': event_id,
                    'status': 'deleted',
                    'message': '일정이 성공적으로 삭제되었습니다.'
                }
            else:
                return {
                    'success': False,
                    'event_id': event_id,
                    'status': 'failed',
                    'message': '일정 삭제에 실패했습니다.'
                }
                
        except Exception as e:
            error_msg = f"일정 삭제 중 오류: {e}"
            logger.error(error_msg)
            raise EventCreationError(error_msg, e)
    
    def format_event_data(self, event_info: ExtractedEventInfo) -> Dict[str, Any]:
        """
        일정 정보 포맷팅
        
        Args:
            event_info: 일정 정보
            
        Returns:
            포맷팅된 일정 데이터
        """
        try:
            formatted_data = {
                '제목': event_info.summary,
                '시작 시간': event_info.start_time.strftime('%Y년 %m월 %d일 %H:%M') if event_info.start_time else '미정',
                '종료 시간': event_info.end_time.strftime('%Y년 %m월 %d일 %H:%M') if event_info.end_time else '미정',
                '종일 일정': '예' if event_info.all_day else '아니오',
                '위치': event_info.location or '미정',
                '설명': event_info.description or '',
                '참석자': ', '.join(event_info.participants) if event_info.participants else '없음',
                '전체 신뢰도': f"{event_info.overall_confidence:.2f}",
                '신뢰도 세부사항': event_info.confidence_scores
            }
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"일정 데이터 포맷팅 중 오류: {e}")
            return {'오류': str(e)}
    
    def _validate_event_info(self, event_info: ExtractedEventInfo) -> None:
        """
        일정 정보 검증 및 자동 보정
        
        Args:
            event_info: 검증할 일정 정보
            
        Raises:
            InvalidEventDataError: 일정 데이터가 올바르지 않은 경우
        """
        if not event_info.summary:
            raise InvalidEventDataError("일정 제목이 없습니다")
        
        if not event_info.start_time:
            raise InvalidEventDataError("시작 시간이 없습니다")
        
        # 종료 시간이 없는 경우 자동으로 1시간 후로 설정
        if not event_info.end_time:
            event_info.end_time = event_info.start_time + timedelta(hours=1)
            logger.info(f"종료 시간이 없어 자동으로 1시간 후로 설정: {event_info.end_time}")
        
        if event_info.start_time >= event_info.end_time:
            # 시작 시간이 종료 시간보다 늦은 경우 종료 시간을 1시간 후로 조정
            event_info.end_time = event_info.start_time + timedelta(hours=1)
            logger.warning(f"시작 시간이 종료 시간보다 늦어 종료 시간을 조정: {event_info.end_time}")
    
    def _create_calendar_event(
        self,
        event_info: ExtractedEventInfo,
        email_id: str,
        email_subject: str = ""
    ) -> CalendarEvent:
        """
        CalendarEvent 객체 생성
        
        Args:
            event_info: 추출된 일정 정보
            email_id: 원본 이메일 ID
            email_subject: 이메일 제목
            
        Returns:
            CalendarEvent 객체
        """
        # 설명에 원본 이메일 참조 추가
        description = self._create_event_description(event_info.description, email_id, email_subject)
        
        return CalendarEvent(
            summary=event_info.summary,
            start_time=event_info.start_time.isoformat() if event_info.start_time else "",
            end_time=event_info.end_time.isoformat() if event_info.end_time else "",
            description=description,
            location=event_info.location,
            all_day=event_info.all_day
        )
    
    def _create_event_description(
        self,
        original_description: Optional[str],
        email_id: str,
        email_subject: str = ""
    ) -> str:
        """
        원본 이메일 참조를 포함한 일정 설명 생성
        
        Args:
            original_description: 원본 설명
            email_id: 이메일 ID
            email_subject: 이메일 제목
            
        Returns:
            참조 링크가 포함된 설명
        """
        description_parts = []
        
        # 원본 설명 추가
        if original_description:
            description_parts.append(original_description)
        
        # 구분선 추가
        if description_parts:
            description_parts.append("\n" + "-" * 50)
        
        # 원본 이메일 참조 정보 추가
        reference_info = [
            "\n📧 원본 이메일 정보:",
            f"• 이메일 ID: {email_id}"
        ]
        
        if email_subject:
            reference_info.append(f"• 제목: {email_subject}")
        
        # Gmail 링크 추가 (웹에서 이메일을 열 수 있는 링크)
        gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{email_id}"
        reference_info.append(f"• Gmail에서 보기: {gmail_link}")
        
        # 생성 시간 추가
        reference_info.append(f"• 일정 생성 시간: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}")
        
        description_parts.extend(reference_info)
        
        return "\n".join(description_parts)
    
    def _save_event_history(
        self,
        event_id: str,
        email_id: str,
        rule_id: Optional[int],
        confidence_score: float,
        event_data: Dict[str, Any],
        status: str
    ) -> None:
        """
        일정 이력 저장
        
        Args:
            event_id: 일정 ID
            email_id: 이메일 ID
            rule_id: 규칙 ID
            confidence_score: 신뢰도 점수
            event_data: 일정 데이터
            status: 상태
        """
        try:
            if self.event_history_repository:
                self.event_history_repository.add_event_history(
                    event_id=event_id,
                    email_id=email_id,
                    rule_id=rule_id,
                    confidence_score=confidence_score,
                    event_data=event_data
                )
                logger.info(f"일정 이력 저장 완료: 이벤트 ID={event_id}, 상태={status}")
        except Exception as e:
            logger.error(f"일정 이력 저장 중 오류: {e}")
            # 이력 저장 실패는 전체 프로세스를 중단시키지 않음
    
    def _request_user_confirmation_via_service(
        self,
        event_info: ExtractedEventInfo,
        email_id: str,
        email_subject: str = "",
        rule_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        확인 서비스를 통한 사용자 확인 요청
        
        Args:
            event_info: 일정 정보
            email_id: 이메일 ID
            email_subject: 이메일 제목
            rule_id: 규칙 ID
            
        Returns:
            확인 요청 결과
        """
        try:
            logger.info(f"확인 서비스를 통한 사용자 확인 요청: 이메일 ID={email_id}")
            
            # 콜백 함수 정의 (확인 완료 시 실제 일정 생성)
            def confirmation_callback(request_id: str, confirmed: bool, modified_data: Optional[Dict[str, Any]] = None):
                if confirmed:
                    # 수정된 데이터가 있으면 적용
                    final_event_info = event_info
                    if modified_data:
                        final_event_info = self._apply_user_modifications(event_info, modified_data)
                    
                    # 실제 일정 생성 (확인 요구 없이)
                    return self.create_event(
                        final_event_info,
                        email_id,
                        email_subject,
                        rule_id,
                        require_confirmation=False
                    )
                else:
                    return {
                        'success': True,
                        'status': 'cancelled_by_user',
                        'message': '사용자가 일정 생성을 취소했습니다.'
                    }
            
            # 확인 서비스를 통해 확인 요청
            request_id = self.confirmation_service.request_confirmation(
                event_info=event_info,
                email_id=email_id,
                email_subject=email_subject,
                callback_function=confirmation_callback
            )
            
            return {
                'success': True,
                'status': 'pending_confirmation',
                'request_id': request_id,
                'confidence_score': event_info.overall_confidence,
                'message': f'신뢰도가 낮아 사용자 확인이 필요합니다. (신뢰도: {event_info.overall_confidence:.2f})',
                'event_details': self.format_event_data(event_info)
            }
            
        except Exception as e:
            error_msg = f"확인 서비스를 통한 사용자 확인 요청 중 오류: {e}"
            logger.error(error_msg)
            raise EventCreationError(error_msg, e)
    
    def _apply_user_modifications(
        self,
        original_event_info: ExtractedEventInfo,
        modifications: Dict[str, Any]
    ) -> ExtractedEventInfo:
        """
        사용자 수정사항을 원본 일정 정보에 적용
        
        Args:
            original_event_info: 원본 일정 정보
            modifications: 사용자 수정사항
            
        Returns:
            수정된 일정 정보
        """
        try:
            # 원본 정보 복사
            modified_info = ExtractedEventInfo(
                summary=original_event_info.summary,
                start_time=original_event_info.start_time,
                end_time=original_event_info.end_time,
                location=original_event_info.location,
                description=original_event_info.description,
                participants=original_event_info.participants.copy(),
                all_day=original_event_info.all_day,
                confidence_scores=original_event_info.confidence_scores.copy(),
                overall_confidence=original_event_info.overall_confidence
            )
            
            # 수정사항 적용
            if 'summary' in modifications:
                modified_info.summary = modifications['summary']
            
            if 'start_time' in modifications:
                if isinstance(modifications['start_time'], str):
                    modified_info.start_time = datetime.fromisoformat(modifications['start_time'])
                else:
                    modified_info.start_time = modifications['start_time']
            
            if 'end_time' in modifications:
                if isinstance(modifications['end_time'], str):
                    modified_info.end_time = datetime.fromisoformat(modifications['end_time'])
                else:
                    modified_info.end_time = modifications['end_time']
            
            # 종료 시간이 명시적으로 수정되지 않았고 시작 시간이 수정된 경우
            # 원본 일정의 지속 시간을 유지하여 종료 시간 자동 조정
            if 'start_time' in modifications and 'end_time' not in modifications:
                if original_event_info.start_time and original_event_info.end_time:
                    duration = original_event_info.end_time - original_event_info.start_time
                    modified_info.end_time = modified_info.start_time + duration
                    logger.info(f"종료 시간 자동 조정: {modified_info.end_time}")
            
            if 'location' in modifications:
                modified_info.location = modifications['location']
            
            if 'description' in modifications:
                modified_info.description = modifications['description']
            
            if 'participants' in modifications:
                modified_info.participants = modifications['participants']
            
            if 'all_day' in modifications:
                modified_info.all_day = modifications['all_day']
            
            # 시간 검증
            if modified_info.start_time and modified_info.end_time:
                if modified_info.start_time >= modified_info.end_time:
                    logger.warning("시작 시간이 종료 시간보다 늦음. 종료 시간을 1시간 후로 조정")
                    modified_info.end_time = modified_info.start_time + timedelta(hours=1)
            
            # 사용자가 수정했으므로 신뢰도를 높임
            modified_info.overall_confidence = 1.0
            
            logger.info(f"사용자 수정사항 적용 완료")
            return modified_info
            
        except Exception as e:
            logger.error(f"사용자 수정사항 적용 중 오류: {e}")
            # 오류 발생 시 원본 정보 반환
            return original_event_info