# -*- coding: utf-8 -*-
"""
사용자 설정 모델

사용자 설정 및 분석 필터 모델을 정의합니다.
"""

from datetime import datetime
from typing import Optional, Any

class UserPreference:
    """
    사용자 설정 클래스
    
    사용자별 설정 정보를 저장합니다.
    """
    
    def __init__(
        self,
        key: str,
        value: str,
        user_id: str = "default",
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        사용자 설정 초기화
        
        Args:
            key: 설정 키
            value: 설정 값
            user_id: 사용자 ID
            id: 설정 ID (DB에서 할당)
            created_at: 생성 시간
            updated_at: 업데이트 시간
        """
        self.id = id
        self.key = key
        self.value = value
        self.user_id = user_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def update_value(self, value: str) -> None:
        """
        설정 값을 업데이트합니다.
        
        Args:
            value: 새 설정 값
        """
        self.value = value
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """
        설정을 딕셔너리로 변환합니다.
        
        Returns:
            dict: 설정 정보 딕셔너리
        """
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserPreference':
        """
        딕셔너리에서 설정 객체를 생성합니다.
        
        Args:
            data: 설정 정보 딕셔너리
            
        Returns:
            UserPreference: 생성된 설정 객체
        """
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get('updated_at')
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            id=data.get('id'),
            key=data['key'],
            value=data['value'],
            user_id=data.get('user_id', 'default'),
            created_at=created_at,
            updated_at=updated_at
        )

class AnalysisFilter:
    """
    분석 필터 클래스
    
    분석 조건 필터를 정의합니다.
    """
    
    def __init__(
        self,
        filter_name: str,
        filter_type: str,
        filter_value: Any,
        user_id: str = "default",
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        분석 필터 초기화
        
        Args:
            filter_name: 필터 이름
            filter_type: 필터 유형
            filter_value: 필터 값
            user_id: 사용자 ID
            id: 필터 ID (DB에서 할당)
            created_at: 생성 시간
            updated_at: 업데이트 시간
        """
        self.id = id
        self.filter_name = filter_name
        self.filter_type = filter_type
        self.filter_value = filter_value
        self.user_id = user_id
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def update_value(self, filter_value: Any) -> None:
        """
        필터 값을 업데이트합니다.
        
        Args:
            filter_value: 새 필터 값
        """
        self.filter_value = filter_value
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """
        필터를 딕셔너리로 변환합니다.
        
        Returns:
            dict: 필터 정보 딕셔너리
        """
        return {
            'id': self.id,
            'filter_name': self.filter_name,
            'filter_type': self.filter_type,
            'filter_value': self.filter_value,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AnalysisFilter':
        """
        딕셔너리에서 필터 객체를 생성합니다.
        
        Args:
            data: 필터 정보 딕셔너리
            
        Returns:
            AnalysisFilter: 생성된 필터 객체
        """
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get('updated_at')
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            id=data.get('id'),
            filter_name=data['filter_name'],
            filter_type=data['filter_type'],
            filter_value=data['filter_value'],
            user_id=data.get('user_id', 'default'),
            created_at=created_at,
            updated_at=updated_at
        )