# -*- coding: utf-8 -*-
"""
기본 Repository 추상 클래스

모든 Repository 클래스의 기본이 되는 추상 클래스로, CRUD 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TypeVar, Generic

# 제네릭 타입 변수 정의
T = TypeVar('T')


class BaseRepository(Generic[T], ABC):
    """
    기본 Repository 추상 클래스
    
    모든 Repository 클래스의 기본이 되는 추상 클래스로, CRUD 인터페이스를 정의합니다.
    제네릭 타입 T를 사용하여 다양한 엔티티 타입을 지원합니다.
    """
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """
        새 엔티티를 생성합니다.
        
        Args:
            entity: 생성할 엔티티 객체
            
        Returns:
            T: 생성된 엔티티 (ID가 할당됨)
            
        Raises:
            ValueError: 유효하지 않은 엔티티인 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        pass
    
    @abstractmethod
    def read(self, id: int) -> Optional[T]:
        """
        ID로 엔티티를 조회합니다.
        
        Args:
            id: 조회할 엔티티의 ID
            
        Returns:
            Optional[T]: 조회된 엔티티 또는 None (없는 경우)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """
        엔티티를 업데이트합니다.
        
        Args:
            entity: 업데이트할 엔티티 객체 (ID 필수)
            
        Returns:
            T: 업데이트된 엔티티
            
        Raises:
            ValueError: 유효하지 않은 엔티티이거나 ID가 없는 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """
        ID로 엔티티를 삭제합니다.
        
        Args:
            id: 삭제할 엔티티의 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        pass
    
    @abstractmethod
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """
        필터 조건에 맞는 엔티티 목록을 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
            
        Returns:
            List[T]: 조회된 엔티티 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        pass
    
    @abstractmethod
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        필터 조건에 맞는 엔티티 수를 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
            
        Returns:
            int: 조회된 엔티티 수
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        pass
    
    @abstractmethod
    def exists(self, id: int) -> bool:
        """
        ID에 해당하는 엔티티가 존재하는지 확인합니다.
        
        Args:
            id: 확인할 엔티티의 ID
            
        Returns:
            bool: 존재 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        pass