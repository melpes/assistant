"""
Google Calendar Provider 구현

이 모듈은 Google Calendar API를 사용하여 캘린더 이벤트를 관리하는 제공자 클래스를 제공합니다.
"""
from typing import List, Optional
import datetime
import logging
from datetime import timezone

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..interfaces import CalendarProvider
from ..models import CalendarEvent
from ..auth import GoogleAuthService
from ..utils import retry, measure_performance, format_error_message, batch_execute, _service_pool
from ..exceptions import (
    CalendarServiceError,
    EventNotFoundError,
    NetworkError,
    APIQuotaExceededError,
    PermissionDeniedError,
    InvalidEventDataError,
    TimeoutError,
    ServerError,
    RateLimitError,
    TokenExpiredError
)

# 로깅 설정
logger = logging.getLogger(__name__)


class GoogleCalendarProvider(CalendarProvider):
    """Google Calendar API를 사용하는 캘린더 제공자 구현"""
    
    def __init__(
        self,
        auth_service: GoogleAuthService = None,
        calendar_id: str = "primary",
        use_service_pool: bool = True
    ):
        """
        GoogleCalendarProvider 초기화
        
        Args:
            auth_service: Google 인증 서비스 인스턴스
            calendar_id: 사용할 캘린더 ID (기본값: "primary")
            use_service_pool: 서비스 객체 풀 사용 여부 (기본값: True)
        """
        self.auth_service = auth_service or GoogleAuthService()
        self.calendar_id = calendar_id
        self.use_service_pool = use_service_pool
        self._service = None
        self._service_key = f"google_calendar_{calendar_id}"
    
    def _get_service(self):
        """
        Google Calendar API 서비스 객체를 가져옵니다.
        서비스 객체 풀을 사용하여 재사용성을 높입니다.
        
        Returns:
            Google Calendar API 서비스 객체
            
        Raises:
            AuthenticationError: 인증 실패 시
        """
        if self.use_service_pool:
            # 서비스 객체 풀 사용
            def create_service():
                creds = self.auth_service.get_credentials()
                return build("calendar", "v3", credentials=creds)
            
            return _service_pool.get_service(self._service_key, create_service)
        else:
            # 기존 방식 (인스턴스별 캐싱)
            if not self._service:
                creds = self.auth_service.get_credentials()
                self._service = build("calendar", "v3", credentials=creds)
            return self._service
    
    @retry(max_tries=3, delay=1.0, backoff_factor=2.0)
    @measure_performance
    def list_events(self, start_time: str, end_time: str) -> List[CalendarEvent]:
        """
        지정된 기간의 이벤트 목록을 조회합니다.
        
        Args:
            start_time: 조회 시작 시간 (ISO 8601 형식)
            end_time: 조회 종료 시간 (ISO 8601 형식)
            
        Returns:
            CalendarEvent 객체들의 리스트
            
        Raises:
            CalendarServiceError: 조회 실패 시
        """
        try:
            service = self._get_service()
            
            # 페이지네이션을 위한 변수들
            all_events = []
            page_token = None
            
            logger.info(f"캘린더 이벤트 조회 시작: {start_time} ~ {end_time}")
            
            while True:
                events_result = service.events().list(
                    calendarId=self.calendar_id,
                    timeMin=start_time,
                    timeMax=end_time,
                    singleEvents=True,
                    orderBy="startTime",
                    pageToken=page_token
                ).execute()
                
                items = events_result.get("items", [])
                
                # Google API 응답을 CalendarEvent 객체로 변환
                for item in items:
                    try:
                        event = CalendarEvent.from_google_event(item)
                        all_events.append(event)
                    except ValueError as e:
                        # 개별 이벤트 변환 오류는 건너뛰고 계속 진행
                        logger.warning(f"이벤트 변환 중 오류 발생: {e}")
                
                # 다음 페이지가 있는지 확인
                page_token = events_result.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"캘린더 이벤트 조회 완료: {len(all_events)}개 이벤트 로드됨")
            return all_events
            
        except HttpError as e:
            self._handle_http_error(e, "이벤트 목록 조회 중 오류가 발생했습니다")
        except Exception as e:
            error_msg = format_error_message(e, "이벤트 목록 조회 중 예상치 못한 오류가 발생했습니다")
            logger.error(f"이벤트 목록 조회 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
    @retry(max_tries=3, delay=1.0, backoff_factor=2.0)
    @measure_performance
    def create_event(self, event: CalendarEvent) -> CalendarEvent:
        """
        새로운 이벤트를 생성합니다.
        
        Args:
            event: 생성할 이벤트 정보
            
        Returns:
            생성된 이벤트 정보 (ID 포함)
            
        Raises:
            CalendarServiceError: 생성 실패 시
        """
        try:
            service = self._get_service()
            
            # CalendarEvent를 Google API 형식으로 변환
            google_event = event.to_google_event()
            
            logger.info(f"새 캘린더 이벤트 생성 시작: {event.summary}")
            
            # API 호출로 이벤트 생성
            created_event = service.events().insert(
                calendarId=self.calendar_id,
                body=google_event
            ).execute()
            
            # 생성된 이벤트 정보를 CalendarEvent로 변환하여 반환
            result = CalendarEvent.from_google_event(created_event)
            logger.info(f"캘린더 이벤트 생성 완료: ID={result.id}")
            return result
            
        except HttpError as e:
            self._handle_http_error(e, "이벤트 생성 중 오류가 발생했습니다")
        except ValueError as e:
            error_msg = f"이벤트 데이터가 올바르지 않습니다: {e}"
            logger.error(f"이벤트 생성 실패: {error_msg}")
            raise InvalidEventDataError(error_msg, e)
        except Exception as e:
            error_msg = format_error_message(e, "이벤트 생성 중 예상치 못한 오류가 발생했습니다")
            logger.error(f"이벤트 생성 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
    @retry(max_tries=3, delay=1.0, backoff_factor=2.0)
    @measure_performance
    def update_event(self, event_id: str, event: CalendarEvent) -> CalendarEvent:
        """
        기존 이벤트를 수정합니다.
        
        Args:
            event_id: 수정할 이벤트 ID
            event: 수정할 이벤트 정보
            
        Returns:
            수정된 이벤트 정보
            
        Raises:
            EventNotFoundError: 이벤트를 찾을 수 없는 경우
            CalendarServiceError: 수정 실패 시
        """
        try:
            service = self._get_service()
            
            logger.info(f"캘린더 이벤트 수정 시작: ID={event_id}")
            
            # 이벤트 존재 여부 확인
            try:
                service.events().get(
                    calendarId=self.calendar_id,
                    eventId=event_id
                ).execute()
            except HttpError as e:
                if e.status_code == 404:
                    logger.warning(f"이벤트를 찾을 수 없음: ID={event_id}")
                    raise EventNotFoundError(event_id, e)
                self._handle_http_error(e, "이벤트 조회 중 오류가 발생했습니다")
            
            # CalendarEvent를 Google API 형식으로 변환
            google_event = event.to_google_event()
            
            # API 호출로 이벤트 수정
            updated_event = service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=google_event
            ).execute()
            
            # 수정된 이벤트 정보를 CalendarEvent로 변환하여 반환
            result = CalendarEvent.from_google_event(updated_event)
            logger.info(f"캘린더 이벤트 수정 완료: ID={event_id}")
            return result
            
        except EventNotFoundError:
            raise
        except HttpError as e:
            self._handle_http_error(e, "이벤트 수정 중 오류가 발생했습니다")
        except ValueError as e:
            error_msg = f"이벤트 데이터가 올바르지 않습니다: {e}"
            logger.error(f"이벤트 수정 실패: {error_msg}")
            raise InvalidEventDataError(error_msg, e)
        except Exception as e:
            error_msg = format_error_message(e, "이벤트 수정 중 예상치 못한 오류가 발생했습니다")
            logger.error(f"이벤트 수정 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
    @retry(max_tries=3, delay=1.0, backoff_factor=2.0)
    @measure_performance
    def delete_event(self, event_id: str) -> bool:
        """
        이벤트를 삭제합니다.
        
        Args:
            event_id: 삭제할 이벤트 ID
            
        Returns:
            삭제 성공 여부
            
        Raises:
            EventNotFoundError: 이벤트를 찾을 수 없는 경우
            CalendarServiceError: 삭제 실패 시
        """
        try:
            service = self._get_service()
            
            logger.info(f"캘린더 이벤트 삭제 시작: ID={event_id}")
            
            # 이벤트 존재 여부 확인
            try:
                service.events().get(
                    calendarId=self.calendar_id,
                    eventId=event_id
                ).execute()
            except HttpError as e:
                if e.status_code == 404:
                    logger.warning(f"이벤트를 찾을 수 없음: ID={event_id}")
                    raise EventNotFoundError(event_id, e)
                self._handle_http_error(e, "이벤트 조회 중 오류가 발생했습니다")
            
            # API 호출로 이벤트 삭제
            service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"캘린더 이벤트 삭제 완료: ID={event_id}")
            return True
            
        except EventNotFoundError:
            raise
        except HttpError as e:
            self._handle_http_error(e, "이벤트 삭제 중 오류가 발생했습니다")
        except Exception as e:
            error_msg = format_error_message(e, "이벤트 삭제 중 예상치 못한 오류가 발생했습니다")
            logger.error(f"이벤트 삭제 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
    @retry(max_tries=3, delay=1.0, backoff_factor=2.0)
    @measure_performance
    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """
        특정 이벤트를 조회합니다.
        
        Args:
            event_id: 조회할 이벤트 ID
            
        Returns:
            이벤트 정보 또는 None (존재하지 않는 경우)
            
        Raises:
            CalendarServiceError: 조회 실패 시
        """
        try:
            service = self._get_service()
            
            logger.info(f"캘린더 이벤트 조회 시작: ID={event_id}")
            
            # API 호출로 이벤트 조회
            event = service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Google API 응답을 CalendarEvent로 변환하여 반환
            result = CalendarEvent.from_google_event(event)
            logger.info(f"캘린더 이벤트 조회 완료: ID={event_id}")
            return result
            
        except HttpError as e:
            if e.status_code == 404:
                logger.info(f"이벤트를 찾을 수 없음: ID={event_id}")
                return None
            self._handle_http_error(e, "이벤트 조회 중 오류가 발생했습니다")
        except Exception as e:
            error_msg = format_error_message(e, "이벤트 조회 중 예상치 못한 오류가 발생했습니다")
            logger.error(f"이벤트 조회 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
    def _handle_http_error(self, error: HttpError, message: str):
        """
        HttpError를 적절한 예외로 변환합니다.
        
        Args:
            error: 발생한 HttpError
            message: 기본 오류 메시지
            
        Raises:
            EventNotFoundError: 이벤트를 찾을 수 없는 경우 (404)
            PermissionDeniedError: 권한 부족 시 (403)
            APIQuotaExceededError: API 할당량 초과 시 (429)
            RateLimitError: 요청 속도 제한 시 (429 with Retry-After)
            TokenExpiredError: 토큰 만료 시 (401)
            ServerError: 서버 오류 시 (5xx)
            NetworkError: 네트워크 오류 시
            TimeoutError: 요청 시간 초과 시
            CalendarServiceError: 기타 오류
        """
        # 응답 헤더에서 Retry-After 값 추출
        retry_after = None
        if hasattr(error, 'resp') and hasattr(error.resp, 'headers'):
            retry_after_header = error.resp.headers.get('Retry-After')
            if retry_after_header:
                try:
                    retry_after = int(retry_after_header)
                except (ValueError, TypeError):
                    pass
        
        error_reason = None
        if hasattr(error, 'reason'):
            error_reason = error.reason
        
        # 오류 코드에 따른 예외 처리
        if error.status_code == 404:
            raise EventNotFoundError("요청한 이벤트를 찾을 수 없습니다", error)
        elif error.status_code == 403:
            raise PermissionDeniedError("캘린더에 접근할 권한이 없습니다", error)
        elif error.status_code == 401:
            raise TokenExpiredError("인증 토큰이 만료되었습니다", error)
        elif error.status_code == 429:
            if retry_after:
                raise RateLimitError(
                    f"요청 속도 제한에 도달했습니다. {retry_after}초 후에 다시 시도하세요.",
                    error,
                    retry_after
                )
            else:
                raise APIQuotaExceededError("Google Calendar API 할당량이 초과되었습니다", error)
        elif 500 <= error.status_code < 600:
            raise ServerError(f"Google 서버 오류 (코드: {error.status_code})", error)
        elif "timeout" in str(error).lower():
            raise TimeoutError("요청 시간이 초과되었습니다", error)
        else:
            # 기타 오류에 대한 상세 로깅
            logger.error(
                f"Google Calendar API 오류: {error.status_code} - {error_reason or '알 수 없는 오류'}"
            )
            raise CalendarServiceError(f"{message}: {error}", error)
    
    @measure_performance
    def create_events_batch(
        self,
        events: List[CalendarEvent],
        batch_size: int = 10
    ) -> List[Optional[CalendarEvent]]:
        """
        여러 이벤트를 배치로 생성합니다.
        
        Args:
            events: 생성할 이벤트들의 리스트
            batch_size: 배치 크기 (기본값: 10)
            
        Returns:
            생성된 이벤트들의 리스트 (실패한 경우 None)
        """
        logger.info(f"배치 이벤트 생성 시작: {len(events)}개 이벤트")
        
        def create_single_event(event: CalendarEvent) -> Optional[CalendarEvent]:
            try:
                return self.create_event(event)
            except Exception as e:
                logger.error(f"배치 이벤트 생성 실패: {e}")
                return None
        
        results = batch_execute(
            create_single_event,
            events,
            batch_size=batch_size,
            delay_between_batches=0.2  # API 속도 제한 방지
        )
        
        success_count = sum(1 for r in results if r is not None)
        logger.info(f"배치 이벤트 생성 완료: {success_count}/{len(events)}개 성공")
        
        return results
    
    @measure_performance
    def update_events_batch(
        self,
        event_updates: List[tuple],  # (event_id, CalendarEvent) 튜플들
        batch_size: int = 10
    ) -> List[Optional[CalendarEvent]]:
        """
        여러 이벤트를 배치로 수정합니다.
        
        Args:
            event_updates: (event_id, CalendarEvent) 튜플들의 리스트
            batch_size: 배치 크기 (기본값: 10)
            
        Returns:
            수정된 이벤트들의 리스트 (실패한 경우 None)
        """
        logger.info(f"배치 이벤트 수정 시작: {len(event_updates)}개 이벤트")
        
        def update_single_event(update_tuple: tuple) -> Optional[CalendarEvent]:
            try:
                event_id, event = update_tuple
                return self.update_event(event_id, event)
            except Exception as e:
                logger.error(f"배치 이벤트 수정 실패: {e}")
                return None
        
        results = batch_execute(
            update_single_event,
            event_updates,
            batch_size=batch_size,
            delay_between_batches=0.2
        )
        
        success_count = sum(1 for r in results if r is not None)
        logger.info(f"배치 이벤트 수정 완료: {success_count}/{len(event_updates)}개 성공")
        
        return results
    
    @measure_performance
    def delete_events_batch(
        self,
        event_ids: List[str],
        batch_size: int = 10
    ) -> List[bool]:
        """
        여러 이벤트를 배치로 삭제합니다.
        
        Args:
            event_ids: 삭제할 이벤트 ID들의 리스트
            batch_size: 배치 크기 (기본값: 10)
            
        Returns:
            각 이벤트의 삭제 성공 여부 리스트
        """
        logger.info(f"배치 이벤트 삭제 시작: {len(event_ids)}개 이벤트")
        
        def delete_single_event(event_id: str) -> bool:
            try:
                return self.delete_event(event_id)
            except Exception as e:
                logger.error(f"배치 이벤트 삭제 실패: {e}")
                return False
        
        results = batch_execute(
            delete_single_event,
            event_ids,
            batch_size=batch_size,
            delay_between_batches=0.2
        )
        
        success_count = sum(1 for r in results if r)
        logger.info(f"배치 이벤트 삭제 완료: {success_count}/{len(event_ids)}개 성공")
        
        return results
    
    @measure_performance
    def get_events_batch(
        self,
        event_ids: List[str],
        batch_size: int = 10
    ) -> List[Optional[CalendarEvent]]:
        """
        여러 이벤트를 배치로 조회합니다.
        
        Args:
            event_ids: 조회할 이벤트 ID들의 리스트
            batch_size: 배치 크기 (기본값: 10)
            
        Returns:
            조회된 이벤트들의 리스트 (실패한 경우 None)
        """
        logger.info(f"배치 이벤트 조회 시작: {len(event_ids)}개 이벤트")
        
        def get_single_event(event_id: str) -> Optional[CalendarEvent]:
            try:
                return self.get_event(event_id)
            except Exception as e:
                logger.error(f"배치 이벤트 조회 실패: {e}")
                return None
        
        results = batch_execute(
            get_single_event,
            event_ids,
            batch_size=batch_size,
            delay_between_batches=0.1  # 조회는 더 빠르게
        )
        
        success_count = sum(1 for r in results if r is not None)
        logger.info(f"배치 이벤트 조회 완료: {success_count}/{len(event_ids)}개 성공")
        
        return results
    
    def get_service_pool_stats(self) -> dict:
        """
        서비스 객체 풀의 현재 상태를 반환합니다.
        
        Returns:
            풀 상태 정보
        """
        return _service_pool.get_stats()
    
    def clear_service_pool(self) -> None:
        """
        서비스 객체 풀을 초기화합니다.
        """
        _service_pool.clear()
        logger.info("Google Calendar 서비스 객체 풀이 초기화되었습니다.")