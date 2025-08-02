# -*- coding: utf-8 -*-
"""
BaseIngester 추상 클래스 정의

모든 데이터 수집기(Ingester)의 기본 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

class BaseIngester(ABC):
    """
    데이터 수집기 추상 기본 클래스
    
    모든 데이터 수집기는 이 클래스를 상속받아 구현해야 합니다.
    """
    
    def __init__(self, name: str, description: str):
        """
        데이터 수집기 초기화
        
        Args:
            name: 수집기 이름
            description: 수집기 설명
        """
        self.name = name
        self.description = description
        logger.debug(f"수집기 초기화: {name}")
    
    @abstractmethod
    def validate_file(self, file_path: str) -> bool:
        """
        입력 파일의 유효성을 검증합니다.
        
        Args:
            file_path: 검증할 파일 경로
            
        Returns:
            bool: 파일이 유효하면 True, 그렇지 않으면 False
        """
        pass
    
    @abstractmethod
    def extract_transactions(self, file_path: str) -> List[Dict[str, Any]]:
        """
        파일에서 거래 데이터를 추출합니다.
        
        Args:
            file_path: 거래 데이터가 포함된 파일 경로
            
        Returns:
            List[Dict[str, Any]]: 추출된 거래 데이터 목록
        """
        pass
    
    @abstractmethod
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        추출된 원시 데이터를 표준 형식으로 정규화합니다.
        
        Args:
            raw_data: 추출된 원시 거래 데이터
            
        Returns:
            List[Dict[str, Any]]: 정규화된 거래 데이터 목록
        """
        pass
    
    def ingest(self, file_path: str) -> List[Dict[str, Any]]:
        """
        파일에서 데이터를 수집하고 정규화합니다.
        
        Args:
            file_path: 거래 데이터가 포함된 파일 경로
            
        Returns:
            List[Dict[str, Any]]: 정규화된 거래 데이터 목록
            
        Raises:
            ValueError: 파일이 유효하지 않거나 처리 중 오류가 발생한 경우
        """
        logger.info(f"{self.name} 수집기로 데이터 수집 시작: {file_path}")
        
        # 파일 존재 확인
        path = Path(file_path)
        if not path.exists():
            error_msg = f"파일을 찾을 수 없습니다: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # 파일 유효성 검증
        if not self.validate_file(file_path):
            error_msg = f"유효하지 않은 파일 형식입니다: {file_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # 데이터 추출
            raw_data = self.extract_transactions(file_path)
            logger.info(f"{len(raw_data)}개의 거래 데이터를 추출했습니다.")
            
            # 데이터 정규화
            normalized_data = self.normalize_data(raw_data)
            logger.info(f"{len(normalized_data)}개의 거래 데이터를 정규화했습니다.")
            
            return normalized_data
            
        except Exception as e:
            error_msg = f"데이터 수집 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def get_info(self) -> Dict[str, str]:
        """
        수집기 정보를 반환합니다.
        
        Returns:
            Dict[str, str]: 수집기 정보
        """
        return {
            "name": self.name,
            "description": self.description,
            "class": self.__class__.__name__
        }
    
    @abstractmethod
    def get_supported_file_types(self) -> List[str]:
        """
        지원하는 파일 유형 목록을 반환합니다.
        
        Returns:
            List[str]: 지원하는 파일 확장자 목록 (예: ['xlsx', 'csv'])
        """
        pass
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        필수 데이터 필드 목록을 반환합니다.
        
        Returns:
            List[str]: 필수 필드 목록
        """
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        단일 거래 데이터의 유효성을 검증합니다.
        
        Args:
            data: 검증할 거래 데이터
            
        Returns:
            bool: 데이터가 유효하면 True, 그렇지 않으면 False
        """
        required_fields = self.get_required_fields()
        
        # 필수 필드 존재 여부 확인
        for field in required_fields:
            if field not in data or data[field] is None:
                logger.warning(f"필수 필드가 누락되었습니다: {field}")
                return False
        
        return True