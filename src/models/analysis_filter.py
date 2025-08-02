# -*- coding: utf-8 -*-
"""
분석 필터(AnalysisFilter) 엔티티 클래스

거래 데이터 분석을 위한 필터 조건을 정의합니다.
"""

from datetime import datetime
import json
from typing import Optional, Dict, Any, List, Union


class AnalysisFilter:
    """
    분석 필터 엔티티 클래스
    
    거래 데이터 분석을 위한 필터 조건을 정의합니다.
    """
    
    # 필터 조건 연산자 상수
    OP_AND = "and"
    OP_OR = "or"
    
    # 필터 조건 비교 연산자 상수
    COMP_EQUALS = "equals"
    COMP_NOT_EQUALS = "not_equals"
    COMP_CONTAINS = "contains"
    COMP_NOT_CONTAINS = "not_contains"
    COMP_GREATER_THAN = "greater_than"
    COMP_LESS_THAN = "less_than"
    COMP_BETWEEN = "between"
    COMP_IN_LIST = "in_list"
    
    # 유효한 비교 연산자 목록
    VALID_COMPARISONS = [
        COMP_EQUALS,
        COMP_NOT_EQUALS,
        COMP_CONTAINS,
        COMP_NOT_CONTAINS,
        COMP_GREATER_THAN,
        COMP_LESS_THAN,
        COMP_BETWEEN,
        COMP_IN_LIST
    ]
    
    def __init__(
        self,
        filter_name: str,
        filter_config: Union[Dict[str, Any], str],
        is_default: bool = False,
        created_at: Optional[datetime] = None,
        id: Optional[int] = None
    ):
        """
        분석 필터 객체 초기화
        
        Args:
            filter_name: 필터 이름
            filter_config: 필터 설정 (딕셔너리 또는 JSON 문자열)
            is_default: 기본 필터 여부 (기본값: False)
            created_at: 생성 시간 (선택)
            id: 데이터베이스 ID (선택)
        """
        self.id = id
        self.filter_name = filter_name
        
        # filter_config가 문자열이면 JSON으로 파싱
        if isinstance(filter_config, str):
            try:
                self.filter_config = json.loads(filter_config)
            except json.JSONDecodeError:
                raise ValueError(f"유효하지 않은 JSON 형식입니다: {filter_config}")
        else:
            self.filter_config = filter_config
            
        self.is_default = is_default
        self.created_at = created_at or datetime.now()
        
        # 객체 생성 시 유효성 검사 수행
        self.validate()
    
    def validate(self) -> None:
        """
        분석 필터 데이터 유효성 검사
        
        Raises:
            ValueError: 유효하지 않은 데이터가 있을 경우
        """
        # 필수 필드 검사
        if not self.filter_name:
            raise ValueError("필터 이름은 필수 항목입니다")
        

        
        # 필터 설정 구조 검사
        if not isinstance(self.filter_config, dict):
            raise ValueError("필터 설정은 딕셔너리 형태여야 합니다")
        
        # 필터 조건 검사
        if 'conditions' in self.filter_config:
            self._validate_conditions(self.filter_config['conditions'])
    
    def _validate_conditions(self, conditions: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
        """
        필터 조건 유효성 검사
        
        Args:
            conditions: 검사할 조건 (딕셔너리 또는 조건 목록)
            
        Raises:
            ValueError: 유효하지 않은 조건이 있을 경우
        """
        # 단일 조건인 경우
        if isinstance(conditions, dict):
            # 논리 연산자 조건인 경우
            if 'operator' in conditions:
                if conditions['operator'] not in [self.OP_AND, self.OP_OR]:
                    raise ValueError(f"유효하지 않은 논리 연산자입니다: {conditions['operator']}")
                
                if 'conditions' not in conditions or not isinstance(conditions['conditions'], list):
                    raise ValueError("논리 연산자 조건에는 'conditions' 배열이 필요합니다")
                
                for subcondition in conditions['conditions']:
                    self._validate_conditions(subcondition)
            
            # 비교 연산자 조건인 경우
            elif 'field' in conditions and 'comparison' in conditions:
                if conditions['comparison'] not in self.VALID_COMPARISONS:
                    raise ValueError(f"유효하지 않은 비교 연산자입니다: {conditions['comparison']}")
                
                if 'value' not in conditions and conditions['comparison'] != self.COMP_BETWEEN:
                    raise ValueError("비교 연산자 조건에는 'value' 필드가 필요합니다")
                
                if conditions['comparison'] == self.COMP_BETWEEN:
                    if 'min_value' not in conditions or 'max_value' not in conditions:
                        raise ValueError("between 비교 연산자에는 'min_value'와 'max_value' 필드가 필요합니다")
            
            else:
                raise ValueError("조건에는 'operator'나 'field'와 'comparison'이 필요합니다")
        
        # 조건 목록인 경우
        elif isinstance(conditions, list):
            for condition in conditions:
                self._validate_conditions(condition)
        
        else:
            raise ValueError("조건은 딕셔너리 또는 목록 형태여야 합니다")
    
    def set_as_default(self) -> None:
        """필터를 기본값으로 설정"""
        self.is_default = True
    
    def unset_as_default(self) -> None:
        """필터의 기본값 설정 해제"""
        self.is_default = False
    
    def add_condition(self, field: str, comparison: str, value: Any = None, 
                     min_value: Any = None, max_value: Any = None) -> None:
        """
        필터에 조건 추가
        
        Args:
            field: 필드 이름
            comparison: 비교 연산자
            value: 비교 값 (선택)
            min_value: 최소값 (between 연산자용, 선택)
            max_value: 최대값 (between 연산자용, 선택)
            
        Raises:
            ValueError: 유효하지 않은 비교 연산자인 경우
        """
        if comparison not in self.VALID_COMPARISONS:
            raise ValueError(f"유효하지 않은 비교 연산자입니다: {comparison}")
        
        # 기본 조건 구조 생성
        if 'conditions' not in self.filter_config:
            self.filter_config['conditions'] = {
                'operator': self.OP_AND,
                'conditions': []
            }
        
        # 조건 생성
        condition = {
            'field': field,
            'comparison': comparison
        }
        
        # 비교 연산자에 따라 필요한 값 설정
        if comparison == self.COMP_BETWEEN:
            condition['min_value'] = min_value
            condition['max_value'] = max_value
        else:
            condition['value'] = value
        
        # 조건 추가
        if isinstance(self.filter_config['conditions'], dict):
            self.filter_config['conditions']['conditions'].append(condition)
        else:
            self.filter_config['conditions'].append(condition)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        분석 필터 객체를 딕셔너리로 변환
        
        Returns:
            Dict[str, Any]: 분석 필터 정보를 담은 딕셔너리
        """
        return {
            'id': self.id,
            'filter_name': self.filter_name,
            'filter_config': self.filter_config,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisFilter':
        """
        딕셔너리에서 분석 필터 객체 생성
        
        Args:
            data: 분석 필터 정보를 담은 딕셔너리
            
        Returns:
            AnalysisFilter: 생성된 분석 필터 객체
        """
        # 생성 시간 처리
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)
    
    def matches(self, transaction_data: Dict[str, Any]) -> bool:
        """
        거래 데이터가 이 필터의 조건과 일치하는지 확인
        
        Args:
            transaction_data: 거래 데이터 딕셔너리
            
        Returns:
            bool: 조건 일치 여부
        """
        if 'conditions' not in self.filter_config:
            return True  # 조건이 없으면 모든 거래가 일치
        
        return self._evaluate_condition(self.filter_config['conditions'], transaction_data)
    
    def _evaluate_condition(self, condition: Dict[str, Any], transaction_data: Dict[str, Any]) -> bool:
        """
        조건을 평가하여 거래 데이터가 일치하는지 확인
        
        Args:
            condition: 평가할 조건
            transaction_data: 거래 데이터 딕셔너리
            
        Returns:
            bool: 조건 일치 여부
        """
        # 논리 연산자 조건인 경우
        if 'operator' in condition:
            results = [self._evaluate_condition(subcond, transaction_data) 
                      for subcond in condition['conditions']]
            
            if condition['operator'] == self.OP_AND:
                return all(results)
            elif condition['operator'] == self.OP_OR:
                return any(results)
        
        # 비교 연산자 조건인 경우
        elif 'field' in condition and 'comparison' in condition:
            field = condition['field']
            comparison = condition['comparison']
            field_value = transaction_data.get(field)
            
            # 필드가 없으면 조건 불일치
            if field_value is None:
                return False
            
            # 비교 연산자에 따른 평가
            if comparison == self.COMP_EQUALS:
                return field_value == condition['value']
            
            elif comparison == self.COMP_NOT_EQUALS:
                return field_value != condition['value']
            
            elif comparison == self.COMP_CONTAINS:
                return str(condition['value']).lower() in str(field_value).lower()
            
            elif comparison == self.COMP_NOT_CONTAINS:
                return str(condition['value']).lower() not in str(field_value).lower()
            
            elif comparison == self.COMP_GREATER_THAN:
                try:
                    return float(field_value) > float(condition['value'])
                except (ValueError, TypeError):
                    return False
            
            elif comparison == self.COMP_LESS_THAN:
                try:
                    return float(field_value) < float(condition['value'])
                except (ValueError, TypeError):
                    return False
            
            elif comparison == self.COMP_BETWEEN:
                try:
                    return float(condition['min_value']) <= float(field_value) <= float(condition['max_value'])
                except (ValueError, TypeError):
                    return False
            
            elif comparison == self.COMP_IN_LIST:
                if isinstance(condition['value'], list):
                    return field_value in condition['value']
                else:
                    return False
        
        return False
    
    def __str__(self) -> str:
        """
        분석 필터 객체의 문자열 표현
        
        Returns:
            str: 분석 필터 정보 문자열
        """
        default_mark = " (기본값)" if self.is_default else ""
        return f"필터: {self.filter_name}{default_mark}"
    
    def __repr__(self) -> str:
        """
        분석 필터 객체의 개발자용 표현
        
        Returns:
            str: 개발자용 표현 문자열
        """
        return (f"AnalysisFilter(id={self.id}, "
                f"name='{self.filter_name}', "
                f"is_default={self.is_default})")

