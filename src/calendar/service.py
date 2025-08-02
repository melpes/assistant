"""
캘린더 서비스 계층

이 모듈은 캘린더 제공자를 추상화하고 사용자 친화적인 인터페이스를 제공하는 서비스 클래스를 제공합니다.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union

from .interfaces import CalendarProvider
from .models import CalendarEvent
from .utils import measure_performance, retry, format_error_message, get_performance_stats, check_performance_threshold
from .exceptions import (
    CalendarServiceError,
    EventNotFoundError,
    InvalidEventDataError
)

# 로깅 설정
logger = logging.getLogger(__name__)


class CalendarService:
    """
    캘린더 서비스 클래스
    
    이 클래스는 캘린더 제공자를 추상화하고 사용자 친화적인 인터페이스를 제공합니다.
    """
    
    def __init__(self, provider: CalendarProvider):
        """
        CalendarService 초기화
        
        Args:
            provider: 사용할 캘린더 제공자 인스턴스
        """
        self.provider = provider
    
    @measure_performance
    def get_events_for_period(
        self,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        format_response: bool = True
    ) -> Union[List[CalendarEvent], List[Dict[str, Any]]]:
        """
        특정 기간의 이벤트를 조회합니다.
        
        Args:
            start_date: 조회 시작 날짜 (ISO 8601 문자열 또는 datetime 객체)
            end_date: 조회 종료 날짜 (ISO 8601 문자열 또는 datetime 객체)
            format_response: 응답을 사용자 친화적인 형식으로 변환할지 여부
            
        Returns:
            CalendarEvent 객체 리스트 또는 사용자 친화적인 형식의 딕셔너리 리스트
            
        Raises:
            CalendarServiceError: 조회 실패 시
        """
        try:
            # datetime 객체를 ISO 8601 문자열로 변환
            start_time = self._format_datetime(start_date)
            end_time = self._format_datetime(end_date)
            
            logger.info(f"기간 내 이벤트 조회: {start_time} ~ {end_time}")
            
            events = self.provider.list_events(start_time, end_time)
            
            if format_response:
                return [self._format_event_for_display(event) for event in events]
            return events
            
        except Exception as e:
            error_msg = format_error_message(e, "이벤트 조회 중 오류가 발생했습니다")
            logger.error(f"이벤트 조회 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
    @measure_performance
    def get_today_events(self, format_response: bool = True) -> Union[List[CalendarEvent], List[Dict[str, Any]]]:
        """
        오늘의 이벤트를 조회합니다.
        
        Args:
            format_response: 응답을 사용자 친화적인 형식으로 변환할지 여부
            
        Returns:
            CalendarEvent 객체 리스트 또는 사용자 친화적인 형식의 딕셔너리 리스트
            
        Raises:
            CalendarServiceError: 조회 실패 시
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        return self.get_events_for_period(today, tomorrow, format_response)
    
    @measure_performance
    def get_upcoming_events(
        self,
        days: int = 7,
        format_response: bool = True
    ) -> Union[List[CalendarEvent], List[Dict[str, Any]]]:
        """
        향후 일정 기간의 이벤트를 조회합니다.
        
        Args:
            days: 조회할 일수 (기본값: 7)
            format_response: 응답을 사용자 친화적인 형식으로 변환할지 여부
            
        Returns:
            CalendarEvent 객체 리스트 또는 사용자 친화적인 형식의 딕셔너리 리스트
            
        Raises:
            CalendarServiceError: 조회 실패 시
        """
        now = datetime.now()
        end_date = now + timedelta(days=days)
        
        return self.get_events_for_period(now, end_date, format_response)
    
    @measure_performance
    def create_new_event(
        self,
        summary: str,
        start_time: Union[str, datetime],
        end_time: Union[str, datetime],
        description: Optional[str] = None,
        location: Optional[str] = None,
        all_day: bool = False,
        format_response: bool = True
    ) -> Union[CalendarEvent, Dict[str, Any]]:
        """
        새로운 이벤트를 생성합니다.
        
        Args:
            summary: 이벤트 제목
            start_time: 시작 시간 (ISO 8601 문자열 또는 datetime 객체)
            end_time: 종료 시간 (ISO 8601 문자열 또는 datetime 객체)
            description: 이벤트 설명 (선택 사항)
            location: 이벤트 위치 (선택 사항)
            all_day: 종일 이벤트 여부
            format_response: 응답을 사용자 친화적인 형식으로 변환할지 여부
            
        Returns:
            생성된 CalendarEvent 객체 또는 사용자 친화적인 형식의 딕셔너리
            
        Raises:
            InvalidEventDataError: 이벤트 데이터가 올바르지 않은 경우
            CalendarServiceError: 생성 실패 시
        """
        try:
            # datetime 객체를 ISO 8601 문자열로 변환
            start_str = self._format_datetime(start_time)
            end_str = self._format_datetime(end_time)
            
            # 종일 이벤트인 경우 시간 정보 제거
            if all_day:
                start_str = start_str.split('T')[0]
                end_str = end_str.split('T')[0]
            
            # 이벤트 객체 생성
            event = CalendarEvent(
                summary=summary,
                start_time=start_str,
                end_time=end_str,
                description=description,
                location=location,
                all_day=all_day
            )
            
            logger.info(f"새 이벤트 생성: {summary}")
            
            # 제공자를 통해 이벤트 생성
            created_event = self.provider.create_event(event)
            
            if format_response:
                return self._format_event_for_display(created_event)
            return created_event
            
        except ValueError as e:
            error_msg = f"이벤트 데이터가 올바르지 않습니다: {e}"
            logger.error(f"이벤트 생성 실패: {error_msg}")
            raise InvalidEventDataError(error_msg, e)
        except Exception as e:
            error_msg = format_error_message(e, "이벤트 생성 중 오류가 발생했습니다")
            logger.error(f"이벤트 생성 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
    @measure_performance
    def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[Union[str, datetime]] = None,
        end_time: Optional[Union[str, datetime]] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        all_day: Optional[bool] = None,
        format_response: bool = True
    ) -> Union[CalendarEvent, Dict[str, Any]]:
        """
        기존 이벤트를 수정합니다.
        
        Args:
            event_id: 수정할 이벤트 ID
            summary: 이벤트 제목 (선택 사항)
            start_time: 시작 시간 (ISO 8601 문자열 또는 datetime 객체, 선택 사항)
            end_time: 종료 시간 (ISO 8601 문자열 또는 datetime 객체, 선택 사항)
            description: 이벤트 설명 (선택 사항)
            location: 이벤트 위치 (선택 사항)
            all_day: 종일 이벤트 여부 (선택 사항)
            format_response: 응답을 사용자 친화적인 형식으로 변환할지 여부
            
        Returns:
            수정된 CalendarEvent 객체 또는 사용자 친화적인 형식의 딕셔너리
            
        Raises:
            EventNotFoundError: 이벤트를 찾을 수 없는 경우
            InvalidEventDataError: 이벤트 데이터가 올바르지 않은 경우
            CalendarServiceError: 수정 실패 시
        """
        try:
            # 기존 이벤트 조회
            existing_event = self.provider.get_event(event_id)
            if not existing_event:
                raise EventNotFoundError(event_id)
            
            # 수정할 필드만 업데이트
            if summary is not None:
                existing_event.summary = summary
            
            if start_time is not None:
                start_str = self._format_datetime(start_time)
                if all_day:
                    start_str = start_str.split('T')[0]
                existing_event.start_time = start_str
            
            if end_time is not None:
                end_str = self._format_datetime(end_time)
                if all_day:
                    end_str = end_str.split('T')[0]
                existing_event.end_time = end_str
            
            if description is not None:
                existing_event.description = description
            
            if location is not None:
                existing_event.location = location
            
            if all_day is not None:
                existing_event.all_day = all_day
            
            logger.info(f"이벤트 수정: ID={event_id}")
            
            # 제공자를 통해 이벤트 수정
            updated_event = self.provider.update_event(event_id, existing_event)
            
            if format_response:
                return self._format_event_for_display(updated_event)
            return updated_event
            
        except EventNotFoundError:
            raise
        except ValueError as e:
            error_msg = f"이벤트 데이터가 올바르지 않습니다: {e}"
            logger.error(f"이벤트 수정 실패: {error_msg}")
            raise InvalidEventDataError(error_msg, e)
        except Exception as e:
            error_msg = format_error_message(e, "이벤트 수정 중 오류가 발생했습니다")
            logger.error(f"이벤트 수정 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
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
            logger.info(f"이벤트 삭제: ID={event_id}")
            return self.provider.delete_event(event_id)
        except EventNotFoundError:
            raise
        except Exception as e:
            error_msg = format_error_message(e, "이벤트 삭제 중 오류가 발생했습니다")
            logger.error(f"이벤트 삭제 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
    @measure_performance
    def get_event_details(
        self,
        event_id: str,
        format_response: bool = True
    ) -> Union[Optional[CalendarEvent], Optional[Dict[str, Any]]]:
        """
        특정 이벤트의 상세 정보를 조회합니다.
        
        Args:
            event_id: 조회할 이벤트 ID
            format_response: 응답을 사용자 친화적인 형식으로 변환할지 여부
            
        Returns:
            CalendarEvent 객체 또는 사용자 친화적인 형식의 딕셔너리, 이벤트가 없으면 None
            
        Raises:
            CalendarServiceError: 조회 실패 시
        """
        try:
            logger.info(f"이벤트 상세 조회: ID={event_id}")
            
            event = self.provider.get_event(event_id)
            
            if not event:
                return None
            
            if format_response:
                return self._format_event_for_display(event)
            return event
            
        except Exception as e:
            error_msg = format_error_message(e, "이벤트 상세 조회 중 오류가 발생했습니다")
            logger.error(f"이벤트 상세 조회 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
    def _format_datetime(self, dt: Union[str, datetime]) -> str:
        """
        datetime 객체를 ISO 8601 문자열로 변환합니다.
        
        Args:
            dt: 변환할 datetime 객체 또는 ISO 8601 문자열
            
        Returns:
            ISO 8601 형식의 문자열
        """
        if isinstance(dt, str):
            return dt
        
        # datetime 객체를 ISO 8601 문자열로 변환
        return dt.isoformat()
    
    def _format_event_for_display(self, event: CalendarEvent) -> Dict[str, Any]:
        """
        CalendarEvent 객체를 사용자 친화적인 형식으로 변환합니다.
        
        Args:
            event: 변환할 CalendarEvent 객체
            
        Returns:
            사용자 친화적인 형식의 딕셔너리
        """
        # 시작 시간과 종료 시간 파싱
        try:
            if event.all_day:
                # 종일 이벤트인 경우 날짜만 파싱
                start_dt = datetime.fromisoformat(event.start_time).date()
                end_dt = datetime.fromisoformat(event.end_time).date()
                
                start_formatted = start_dt.strftime("%Y년 %m월 %d일")
                end_formatted = end_dt.strftime("%Y년 %m월 %d일")
                
                # 종일 이벤트 표시
                time_str = f"{start_formatted} (종일)"
                if start_dt != end_dt:
                    time_str = f"{start_formatted} ~ {end_formatted} (종일)"
            else:
                # 일반 이벤트인 경우 날짜와 시간 모두 파싱
                start_dt = datetime.fromisoformat(event.start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(event.end_time.replace('Z', '+00:00'))
                
                # 한국 시간으로 변환 (UTC+9)
                from datetime import timezone
                kr_tz = timezone(timedelta(hours=9))
                start_dt = start_dt.astimezone(kr_tz)
                end_dt = end_dt.astimezone(kr_tz)
                
                # 날짜와 시간 포맷팅
                start_date = start_dt.strftime("%Y년 %m월 %d일")
                start_time = start_dt.strftime("%H:%M")
                end_date = end_dt.strftime("%Y년 %m월 %d일")
                end_time = end_dt.strftime("%H:%M")
                
                # 같은 날짜인 경우 날짜는 한 번만 표시
                if start_date == end_date:
                    time_str = f"{start_date} {start_time} ~ {end_time}"
                else:
                    time_str = f"{start_date} {start_time} ~ {end_date} {end_time}"
        except (ValueError, TypeError):
            # 시간 파싱 오류 시 원본 값 사용
            time_str = f"{event.start_time} ~ {event.end_time}"
        
        # 사용자 친화적인 형식으로 변환
        formatted = {
            "id": event.id,
            "제목": event.summary,
            "시간": time_str,
            "종일 일정": event.all_day
        }
        
        if event.description:
            formatted["설명"] = event.description
        
        if event.location:
            formatted["위치"] = event.location
        
        return formatted
    
    # 배치 처리 메서드들
    @measure_performance
    def create_events_batch(
        self,
        events_data: List[Dict[str, Any]],
        batch_size: int = 10,
        format_response: bool = True
    ) -> List[Optional[Union[CalendarEvent, Dict[str, Any]]]]:
        """
        여러 이벤트를 배치로 생성합니다.
        
        Args:
            events_data: 생성할 이벤트 데이터들의 리스트
            batch_size: 배치 크기 (기본값: 10)
            format_response: 응답을 사용자 친화적인 형식으로 변환할지 여부
            
        Returns:
            생성된 이벤트들의 리스트 (실패한 경우 None)
            
        Raises:
            CalendarServiceError: 배치 생성 실패 시
        """
        try:
            logger.info(f"배치 이벤트 생성 시작: {len(events_data)}개 이벤트")
            
            # 이벤트 데이터를 CalendarEvent 객체로 변환
            events = []
            for data in events_data:
                try:
                    event = CalendarEvent(
                        summary=data.get('summary', ''),
                        start_time=self._format_datetime(data.get('start_time', '')),
                        end_time=self._format_datetime(data.get('end_time', '')),
                        description=data.get('description'),
                        location=data.get('location'),
                        all_day=data.get('all_day', False)
                    )
                    events.append(event)
                except Exception as e:
                    logger.error(f"이벤트 데이터 변환 실패: {e}")
                    events.append(None)
            
            # 유효한 이벤트만 필터링
            valid_events = [e for e in events if e is not None]
            
            if hasattr(self.provider, 'create_events_batch'):
                # 제공자가 배치 처리를 지원하는 경우
                results = self.provider.create_events_batch(valid_events, batch_size)
            else:
                # 제공자가 배치 처리를 지원하지 않는 경우 순차 처리
                results = []
                for event in valid_events:
                    try:
                        result = self.provider.create_event(event)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"개별 이벤트 생성 실패: {e}")
                        results.append(None)
            
            # 응답 포맷팅
            if format_response:
                formatted_results = []
                for result in results:
                    if result:
                        formatted_results.append(self._format_event_for_display(result))
                    else:
                        formatted_results.append(None)
                return formatted_results
            
            return results
            
        except Exception as e:
            error_msg = format_error_message(e, "배치 이벤트 생성 중 오류가 발생했습니다")
            logger.error(f"배치 이벤트 생성 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
    @measure_performance
    def update_events_batch(
        self,
        event_updates: List[Dict[str, Any]],
        batch_size: int = 10,
        format_response: bool = True
    ) -> List[Optional[Union[CalendarEvent, Dict[str, Any]]]]:
        """
        여러 이벤트를 배치로 수정합니다.
        
        Args:
            event_updates: 수정할 이벤트 정보들의 리스트 (각각 'id' 키 포함)
            batch_size: 배치 크기 (기본값: 10)
            format_response: 응답을 사용자 친화적인 형식으로 변환할지 여부
            
        Returns:
            수정된 이벤트들의 리스트 (실패한 경우 None)
            
        Raises:
            CalendarServiceError: 배치 수정 실패 시
        """
        try:
            logger.info(f"배치 이벤트 수정 시작: {len(event_updates)}개 이벤트")
            
            # 수정 데이터를 (event_id, CalendarEvent) 튜플로 변환
            update_tuples = []
            for data in event_updates:
                try:
                    event_id = data.get('id')
                    if not event_id:
                        logger.error("이벤트 ID가 없습니다")
                        continue
                    
                    # 기존 이벤트 조회
                    existing_event = self.provider.get_event(event_id)
                    if not existing_event:
                        logger.error(f"이벤트를 찾을 수 없습니다: {event_id}")
                        continue
                    
                    # 수정할 필드만 업데이트
                    if 'summary' in data:
                        existing_event.summary = data['summary']
                    if 'start_time' in data:
                        existing_event.start_time = self._format_datetime(data['start_time'])
                    if 'end_time' in data:
                        existing_event.end_time = self._format_datetime(data['end_time'])
                    if 'description' in data:
                        existing_event.description = data['description']
                    if 'location' in data:
                        existing_event.location = data['location']
                    if 'all_day' in data:
                        existing_event.all_day = data['all_day']
                    
                    update_tuples.append((event_id, existing_event))
                    
                except Exception as e:
                    logger.error(f"이벤트 수정 데이터 준비 실패: {e}")
                    continue
            
            if hasattr(self.provider, 'update_events_batch'):
                # 제공자가 배치 처리를 지원하는 경우
                results = self.provider.update_events_batch(update_tuples, batch_size)
            else:
                # 제공자가 배치 처리를 지원하지 않는 경우 순차 처리
                results = []
                for event_id, event in update_tuples:
                    try:
                        result = self.provider.update_event(event_id, event)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"개별 이벤트 수정 실패: {e}")
                        results.append(None)
            
            # 응답 포맷팅
            if format_response:
                formatted_results = []
                for result in results:
                    if result:
                        formatted_results.append(self._format_event_for_display(result))
                    else:
                        formatted_results.append(None)
                return formatted_results
            
            return results
            
        except Exception as e:
            error_msg = format_error_message(e, "배치 이벤트 수정 중 오류가 발생했습니다")
            logger.error(f"배치 이벤트 수정 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
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
            
        Raises:
            CalendarServiceError: 배치 삭제 실패 시
        """
        try:
            logger.info(f"배치 이벤트 삭제 시작: {len(event_ids)}개 이벤트")
            
            if hasattr(self.provider, 'delete_events_batch'):
                # 제공자가 배치 처리를 지원하는 경우
                results = self.provider.delete_events_batch(event_ids, batch_size)
            else:
                # 제공자가 배치 처리를 지원하지 않는 경우 순차 처리
                results = []
                for event_id in event_ids:
                    try:
                        result = self.provider.delete_event(event_id)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"개별 이벤트 삭제 실패: {e}")
                        results.append(False)
            
            return results
            
        except Exception as e:
            error_msg = format_error_message(e, "배치 이벤트 삭제 중 오류가 발생했습니다")
            logger.error(f"배치 이벤트 삭제 실패: {error_msg}")
            raise CalendarServiceError(error_msg, e)
    
    # 성능 모니터링 메서드들
    def get_performance_report(self) -> Dict[str, Any]:
        """
        캘린더 서비스의 성능 보고서를 생성합니다.
        
        Returns:
            성능 통계 보고서
        """
        stats = get_performance_stats()
        
        # 캘린더 관련 함수들만 필터링
        calendar_stats = {}
        for func_name, func_stats in stats.items():
            if any(keyword in func_name.lower() for keyword in ['event', 'calendar', 'list', 'create', 'update', 'delete']):
                calendar_stats[func_name] = func_stats
        
        # 성능 경고 확인
        warnings = []
        for func_name in calendar_stats:
            if check_performance_threshold(func_name, 3.0):
                warnings.append(f"{func_name} 함수의 평균 실행 시간이 3초를 초과합니다.")
        
        return {
            'performance_stats': calendar_stats,
            'warnings': warnings,
            'total_functions': len(calendar_stats),
            'report_time': datetime.now().isoformat()
        }
    
    def optimize_performance(self) -> Dict[str, Any]:
        """
        성능 최적화 제안을 생성합니다.
        
        Returns:
            최적화 제안 딕셔너리
        """
        report = self.get_performance_report()
        suggestions = []
        
        # 성능 통계 분석
        for func_name, stats in report['performance_stats'].items():
            if 'avg_time' in stats:
                avg_time = stats['avg_time']
                success_rate = stats.get('success_rate', 100)
                
                if avg_time > 5.0:
                    suggestions.append(f"{func_name}: 평균 실행 시간이 {avg_time:.2f}초로 매우 느립니다. 배치 처리 사용을 고려하세요.")
                elif avg_time > 3.0:
                    suggestions.append(f"{func_name}: 평균 실행 시간이 {avg_time:.2f}초입니다. 최적화가 필요할 수 있습니다.")
                
                if success_rate < 90:
                    suggestions.append(f"{func_name}: 성공률이 {success_rate:.1f}%로 낮습니다. 에러 처리를 확인하세요.")
        
        # 서비스 객체 풀 상태 확인
        if hasattr(self.provider, 'get_service_pool_stats'):
            pool_stats = self.provider.get_service_pool_stats()
            if pool_stats['pool_size'] == 0:
                suggestions.append("서비스 객체 풀이 비어있습니다. 서비스 객체 재사용을 활성화하세요.")
        
        return {
            'suggestions': suggestions,
            'performance_report': report,
            'optimization_time': datetime.now().isoformat()
        }