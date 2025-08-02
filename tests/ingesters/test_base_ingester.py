# -*- coding: utf-8 -*-
"""
BaseIngester 테스트
"""

import pytest
from abc import ABC
from typing import List, Dict, Any

from src.ingesters.base_ingester import BaseIngester

# 테스트용 구체적인 수집기 클래스
class TestIngester(BaseIngester):
    """테스트용 수집기 구현"""
    
    def __init__(self, name: str = "테스트 수집기", description: str = "테스트용 수집기"):
        super().__init__(name, description)
    
    def validate_file(self, file_path: str) -> bool:
        return file_path.endswith('.test')
    
    def extract_transactions(self, file_path: str) -> List[Dict[str, Any]]:
        return [{'test': 'data'}]
    
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{'transaction_id': 'test_id', 'transaction_date': '2023-01-01', 
                'description': 'Test', 'amount': 100, 'transaction_type': 'expense', 
                'source': 'test'}]
    
    def get_supported_file_types(self) -> List[str]:
        return ['test']
    
    def get_required_fields(self) -> List[str]:
        return ['transaction_id', 'transaction_date', 'description', 'amount', 'transaction_type', 'source']

class TestBaseIngester:
    """BaseIngester 테스트 클래스"""
    
    def test_base_ingester_is_abstract(self):
        """BaseIngester가 추상 클래스인지 확인"""
        assert issubclass(BaseIngester, ABC)
        
        # 추상 메서드 목록 확인
        abstract_methods = [
            'validate_file',
            'extract_transactions',
            'normalize_data',
            'get_supported_file_types',
            'get_required_fields'
        ]
        
        for method in abstract_methods:
            assert method in BaseIngester.__abstractmethods__
    
    def test_concrete_ingester_instantiation(self):
        """구체적인 수집기 인스턴스 생성 테스트"""
        ingester = TestIngester("테스트", "테스트 설명")
        assert ingester.name == "테스트"
        assert ingester.description == "테스트 설명"
    
    def test_get_info(self):
        """get_info 메서드 테스트"""
        ingester = TestIngester()
        info = ingester.get_info()
        
        assert info['name'] == "테스트 수집기"
        assert info['description'] == "테스트용 수집기"
        assert info['class'] == "TestIngester"
    
    def test_validate_data(self):
        """validate_data 메서드 테스트"""
        ingester = TestIngester()
        
        # 유효한 데이터
        valid_data = {
            'transaction_id': 'test_id',
            'transaction_date': '2023-01-01',
            'description': 'Test',
            'amount': 100,
            'transaction_type': 'expense',
            'source': 'test'
        }
        assert ingester.validate_data(valid_data) is True
        
        # 유효하지 않은 데이터 (필수 필드 누락)
        invalid_data = {
            'transaction_id': 'test_id',
            'description': 'Test',
            'amount': 100
        }
        assert ingester.validate_data(invalid_data) is False