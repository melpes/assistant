"""
캘린더 서비스 인터페이스 정의
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .models import CalendarEvent


class CalendarProvider(ABC):
    """캘린더 제공자 추상 인터페이스"""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass