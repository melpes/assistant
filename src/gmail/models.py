"""
이메일 캘린더 자동화를 위한 데이터 모델들
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class EmailMetadata:
    """이메일 메타데이터를 나타내는 데이터 클래스"""
    
    id: str = ""
    thread_id: str = ""
    subject: str = ""
    sender: str = ""
    recipients: List[str] = field(default_factory=list)
    cc: List[str] = field(default_factory=list)
    date: Optional[datetime] = None
    labels: List[str] = field(default_factory=list)


@dataclass
class ExtractedEventInfo:
    """이메일에서 추출된 일정 정보를 나타내는 데이터 클래스"""
    
    summary: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None
    participants: List[str] = field(default_factory=list)
    all_day: bool = False
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    overall_confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'summary': self.summary,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'location': self.location,
            'description': self.description,
            'participants': self.participants,
            'all_day': self.all_day,
            'confidence_scores': self.confidence_scores,
            'overall_confidence': self.overall_confidence
        }


@dataclass
class EmailCalendarRule:
    """이메일 캘린더 자동화 규칙을 나타내는 데이터 클래스"""
    
    id: Optional[int] = None
    name: str = ""
    active: bool = True
    min_confidence_score: float = 0.7
    require_confirmation: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class EventHistory:
    """자동 생성된 일정의 이력을 나타내는 데이터 클래스"""
    
    id: Optional[int] = None
    event_id: str = ""
    email_id: str = ""
    rule_id: Optional[int] = None
    confidence_score: float = 0.0
    status: str = "created"  # created, confirmed, modified, deleted
    event_data: dict = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class EmailFilter:
    """이메일 필터를 나타내는 데이터 클래스"""
    
    id: Optional[str] = None
    criteria: Dict[str, str] = field(default_factory=dict)
    actions: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None


@dataclass
class TodoItem:
    """할 일 항목을 나타내는 데이터 클래스"""
    
    id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: int = 0  # 0: 낮음, 1: 보통, 2: 높음
    status: str = "pending"  # pending, completed, canceled
    email_id: Optional[str] = None
    event_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None