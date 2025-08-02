# -*- coding: utf-8 -*-
"""
필터 엔진(FilterEngine) 클래스

거래 데이터에 대한 다중 조건 필터링 기능을 제공합니다.
"""

from typing import List, Dict, Any, Optional, Union
import json
from datetime import datetime

from src.models.analysis_filter import AnalysisFilter
from src.models.transaction import Transaction
from src.repositories.filter_repository import FilterRepository


class FilterEngine:
    """
    필터 엔진 클래스
    
    거래 데이터에 대한 다중 조건 필터링 기능을 제공합니다.
    """
    
    def __init__(self, filter_repository: Optional[FilterRepository] = None):
        """
        필터 엔진 객체 초기화
        
        Args:
            filter_repository: 필터 저장소 객체 (선택)
        """
        self.filter_repository = filter_repository or FilterRepository()
        self._cached_filters = {}  # 필터 캐싱을 위한 딕셔너리
    
    def apply_filter(self, transactions: List[Transaction], filter_obj: AnalysisFilter) -> List[Transaction]:
        """
        거래 목록에 필터 적용
        
        Args:
            transactions: 필터링할 거래 목록
            filter_obj: 적용할 필터 객체
            
        Returns:
            List[Transaction]: 필터링된 거래 목록
        """
        return [tx for tx in transactions if self._matches_filter(tx, filter_obj)]
    
    def apply_filter_by_id(self, transactions: List[Transaction], filter_id: int) -> List[Transaction]:
        """
        ID로 필터를 조회하여 거래 목록에 적용
        
        Args:
            transactions: 필터링할 거래 목록
            filter_id: 적용할 필터 ID
            
        Returns:
            List[Transaction]: 필터링된 거래 목록
            
        Raises:
            ValueError: 필터를 찾을 수 없는 경우
        """
        filter_obj = self._get_cached_filter(filter_id)
        if not filter_obj:
            raise ValueError(f"ID가 {filter_id}인 필터를 찾을 수 없습니다")
        
        return self.apply_filter(transactions, filter_obj)
    
    def apply_filter_by_name(self, transactions: List[Transaction], filter_name: str) -> List[Transaction]:
        """
        이름으로 필터를 조회하여 거래 목록에 적용
        
        Args:
            transactions: 필터링할 거래 목록
            filter_name: 적용할 필터 이름
            
        Returns:
            List[Transaction]: 필터링된 거래 목록
            
        Raises:
            ValueError: 필터를 찾을 수 없는 경우
        """
        filter_obj = self.filter_repository.get_by_name(filter_name)
        if not filter_obj:
            raise ValueError(f"이름이 '{filter_name}'인 필터를 찾을 수 없습니다")
        
        # 캐시 업데이트
        if filter_obj.id:
            self._cached_filters[filter_obj.id] = filter_obj
        
        return self.apply_filter(transactions, filter_obj)
    
    def apply_default_filter(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        기본 필터를 거래 목록에 적용
        
        Args:
            transactions: 필터링할 거래 목록
            
        Returns:
            List[Transaction]: 필터링된 거래 목록
            
        Raises:
            ValueError: 기본 필터가 없는 경우
        """
        filter_obj = self.filter_repository.get_default()
        if not filter_obj:
            raise ValueError("기본 필터가 설정되어 있지 않습니다")
        
        # 캐시 업데이트
        if filter_obj.id:
            self._cached_filters[filter_obj.id] = filter_obj
        
        return self.apply_filter(transactions, filter_obj)
    
    def apply_combined_filters(self, transactions: List[Transaction], 
                              filter_ids: List[int], 
                              operator: str = AnalysisFilter.OP_AND) -> List[Transaction]:
        """
        여러 필터를 조합하여 거래 목록에 적용
        
        Args:
            transactions: 필터링할 거래 목록
            filter_ids: 적용할 필터 ID 목록
            operator: 필터 조합 연산자 (기본값: AND)
            
        Returns:
            List[Transaction]: 필터링된 거래 목록
            
        Raises:
            ValueError: 유효하지 않은 연산자 또는 필터를 찾을 수 없는 경우
        """
        if operator not in [AnalysisFilter.OP_AND, AnalysisFilter.OP_OR]:
            raise ValueError(f"유효하지 않은 연산자입니다: {operator}")
        
        # 모든 필터 객체 조회
        filters = []
        for filter_id in filter_ids:
            filter_obj = self._get_cached_filter(filter_id)
            if not filter_obj:
                raise ValueError(f"ID가 {filter_id}인 필터를 찾을 수 없습니다")
            filters.append(filter_obj)
        
        # 필터 조합 적용
        if operator == AnalysisFilter.OP_AND:
            result = transactions
            for filter_obj in filters:
                result = self.apply_filter(result, filter_obj)
            return result
        else:  # OR 연산자
            result_set = set()
            for filter_obj in filters:
                filtered = self.apply_filter(transactions, filter_obj)
                result_set.update(filtered)
            # 원래 순서 유지를 위해 원본 목록에서 필터링된 항목만 추출
            return [tx for tx in transactions if tx in result_set]
    
    def create_filter(self, filter_name: str, is_default: bool = False) -> AnalysisFilter:
        """
        새 필터 생성
        
        Args:
            filter_name: 필터 이름
            is_default: 기본 필터 여부 (기본값: False)
            
        Returns:
            AnalysisFilter: 생성된 필터 객체
        """
        filter_obj = AnalysisFilter(
            filter_name=filter_name,
            filter_config={'conditions': []},
            is_default=is_default
        )
        
        # 저장소에 저장
        self.filter_repository.save(filter_obj)
        
        # 캐시 업데이트
        if filter_obj.id:
            self._cached_filters[filter_obj.id] = filter_obj
        
        return filter_obj
    
    def save_filter(self, filter_obj: AnalysisFilter) -> int:
        """
        필터 저장
        
        Args:
            filter_obj: 저장할 필터 객체
            
        Returns:
            int: 저장된 필터의 ID
        """
        filter_id = self.filter_repository.save(filter_obj)
        
        # 캐시 업데이트
        self._cached_filters[filter_id] = filter_obj
        
        return filter_id
    
    def delete_filter(self, filter_id: int) -> bool:
        """
        필터 삭제
        
        Args:
            filter_id: 삭제할 필터 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        # 캐시에서 제거
        if filter_id in self._cached_filters:
            del self._cached_filters[filter_id]
        
        return self.filter_repository.delete(filter_id)
    
    def get_all_filters(self) -> List[AnalysisFilter]:
        """
        모든 필터 조회
        
        Returns:
            List[AnalysisFilter]: 필터 객체 목록
        """
        filters = self.filter_repository.get_all()
        
        # 캐시 업데이트
        for filter_obj in filters:
            if filter_obj.id:
                self._cached_filters[filter_obj.id] = filter_obj
        
        return filters
    
    def _get_cached_filter(self, filter_id: int) -> Optional[AnalysisFilter]:
        """
        캐시된 필터 조회 또는 저장소에서 로드
        
        Args:
            filter_id: 조회할 필터 ID
            
        Returns:
            Optional[AnalysisFilter]: 조회된 필터 객체 또는 None
        """
        # 캐시에 있으면 반환
        if filter_id in self._cached_filters:
            return self._cached_filters[filter_id]
        
        # 저장소에서 로드
        filter_obj = self.filter_repository.get_by_id(filter_id)
        
        # 캐시 업데이트
        if filter_obj:
            self._cached_filters[filter_id] = filter_obj
        
        return filter_obj
    
    def _matches_filter(self, transaction: Transaction, filter_obj: AnalysisFilter) -> bool:
        """
        거래가 필터 조건과 일치하는지 확인
        
        Args:
            transaction: 확인할 거래 객체
            filter_obj: 필터 객체
            
        Returns:
            bool: 조건 일치 여부
        """
        # 거래 객체를 딕셔너리로 변환
        transaction_dict = transaction.to_dict()
        
        # 필터 조건 평가
        return filter_obj.matches(transaction_dict)
    
    def clear_cache(self) -> None:
        """필터 캐시 초기화"""
        self._cached_filters.clear()
    
    def create_dynamic_filter(self, conditions: Dict[str, Any], 
                             filter_name: Optional[str] = None,
                             save: bool = False) -> AnalysisFilter:
        """
        동적 필터 생성
        
        Args:
            conditions: 필터 조건 딕셔너리
            filter_name: 필터 이름 (선택, 저장 시 필수)
            save: 필터 저장 여부 (기본값: False)
            
        Returns:
            AnalysisFilter: 생성된 필터 객체
            
        Raises:
            ValueError: 저장 시 필터 이름이 없는 경우
        """
        # 저장 시 이름 필수
        if save and not filter_name:
            raise ValueError("필터를 저장하려면 이름이 필요합니다")
        
        # 필터 이름 설정
        name = filter_name or f"동적 필터 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 필터 객체 생성
        filter_obj = AnalysisFilter(
            filter_name=name,
            filter_config={'conditions': conditions}
        )
        
        # 필터 저장
        if save:
            self.filter_repository.save(filter_obj)
            
            # 캐시 업데이트
            if filter_obj.id:
                self._cached_filters[filter_obj.id] = filter_obj
        
        return filter_obj