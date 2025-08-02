"""
캘린더 이벤트 데이터 모델
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class CalendarEvent:
    """캘린더 이벤트를 나타내는 데이터 클래스"""
    
    id: Optional[str] = None
    summary: str = ""
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: str = ""
    end_time: str = ""
    all_day: bool = False
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.summary:
            raise ValueError("이벤트 제목(summary)은 필수입니다")
        
        if not self.start_time:
            raise ValueError("시작 시간(start_time)은 필수입니다")
        
        if not self.end_time:
            raise ValueError("종료 시간(end_time)은 필수입니다")
    
    @classmethod
    def from_google_event(cls, google_event: dict) -> 'CalendarEvent':
        """Google Calendar API 응답을 CalendarEvent로 변환"""
        start = google_event.get('start', {})
        end = google_event.get('end', {})
        
        # 종일 이벤트 확인
        all_day = 'date' in start
        
        # 시간 정보 추출
        start_time = start.get('date') or start.get('dateTime', '')
        end_time = end.get('date') or end.get('dateTime', '')
        
        # summary가 없는 경우 기본값 제공
        summary = google_event.get('summary', '') or '제목 없음'
        
        return cls(
            id=google_event.get('id'),
            summary=summary,
            description=google_event.get('description'),
            location=google_event.get('location'),
            start_time=start_time,
            end_time=end_time,
            all_day=all_day
        )
    
    def to_google_event(self) -> dict:
        """CalendarEvent를 Google Calendar API 형식으로 변환"""
        event = {
            'summary': self.summary,
        }
        
        if self.description:
            event['description'] = self.description
        
        if self.location:
            event['location'] = self.location
        
        # 시간 정보 설정
        if self.all_day:
            event['start'] = {'date': self.start_time}
            event['end'] = {'date': self.end_time}
        else:
            # 시간 지정 일정의 경우 타임존 정보도 함께 제공
            event['start'] = {
                'dateTime': self.start_time,
                'timeZone': 'Asia/Seoul'  # 한국 시간대
            }
            event['end'] = {
                'dateTime': self.end_time,
                'timeZone': 'Asia/Seoul'  # 한국 시간대
            }
        
        return event