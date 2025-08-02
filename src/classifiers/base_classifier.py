# -*- coding: utf-8 -*-
"""
기본 분류기(BaseClassifier) 추상 클래스

모든 분류기의 기본 인터페이스를 정의합니다.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from src.models import Transaction

# 로거 설정
logger = logging.getLogger(__name__)


class BaseClassifier(ABC):
    """
    기본 분류기 추상 클래스
    
    모든 분류기의 기본 인터페이스를 정의합니다.
    """
    
    @abstractmethod
    def classify(self, transaction: Transaction) -> Optional[str]:
        """
        거래를 분류하여 결과값을 반환합니다.
        
        Args:
            transaction: 분류할 거래 객체
            
        Returns:
            Optional[str]: 분류 결과값 또는 None (분류 불가능한 경우)
        """
        pass
    
    @abstractmethod
    def classify_batch(self, transactions: List[Transaction]) -> Dict[str, str]:
        """
        여러 거래를 일괄 분류합니다.
        
        Args:
            transactions: 분류할 거래 객체 목록
            
        Returns:
            Dict[str, str]: 거래 ID를 키로, 분류 결과값을 값으로 하는 딕셔너리
        """
        pass
    
    @abstractmethod
    def learn_from_correction(self, transaction: Transaction, correct_value: str) -> bool:
        """
        사용자 수정사항으로부터 학습합니다.
        
        Args:
            transaction: 수정된 거래 객체
            correct_value: 올바른 분류 결과값
            
        Returns:
            bool: 학습 성공 여부
        """
        pass
    
    @abstractmethod
    def get_accuracy_metrics(self) -> Dict[str, Any]:
        """
        분류 정확도 지표를 반환합니다.
        
        Returns:
            Dict[str, Any]: 정확도 지표 정보
        """
        pass