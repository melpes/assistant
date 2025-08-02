# -*- coding: utf-8 -*-
"""
IngesterFactory 테스트
"""

import pytest
from typing import List, Dict, Any

from src.ingesters.base_ingester import BaseIngester
from src.ingesters.ingester_factory import IngesterFactory

# 테스트용 수집기 클래스들
class TestIngester1(BaseIngester):
    """테스트용 수집기 1"""
    
    def __init__(self, name: str = "테스트 수집기 1", description: str = "테스트용 수집기 1"):
        super().__init__(name, description)
    
    def validate_file(self, file_path: str) -> bool:
        return file_path.endswith('.test1')
    
    def extract_transactions(self, file_path: str) -> List[Dict[str, Any]]:
        return [{'test': 'data1'}]
    
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{'transaction_id': 'test_id1', 'transaction_date': '2023-01-01', 
                'description': 'Test1', 'amount': 100, 'transaction_type': 'expense', 
                'source': 'test1'}]
    
    def get_supported_file_types(self) -> List[str]:
        return ['test1', 'txt']
    
    def get_required_fields(self) -> List[str]:
        return ['transaction_id', 'transaction_date', 'description', 'amount', 'transaction_type', 'source']

class TestIngester2(BaseIngester):
    """테스트용 수집기 2"""
    
    def __init__(self, name: str = "테스트 수집기 2", description: str = "테스트용 수집기 2"):
        super().__init__(name, description)
    
    def validate_file(self, file_path: str) -> bool:
        return file_path.endswith('.test2')
    
    def extract_transactions(self, file_path: str) -> List[Dict[str, Any]]:
        return [{'test': 'data2'}]
    
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{'transaction_id': 'test_id2', 'transaction_date': '2023-01-01', 
                'description': 'Test2', 'amount': 200, 'transaction_type': 'income', 
                'source': 'test2'}]
    
    def get_supported_file_types(self) -> List[str]:
        return ['test2', 'csv']
    
    def get_required_fields(self) -> List[str]:
        return ['transaction_id', 'transaction_date', 'description', 'amount', 'transaction_type', 'source']

class TestIngesterFactory:
    """IngesterFactory 테스트 클래스"""
    
    def test_factory_initialization(self):
        """팩토리 초기화 테스트"""
        factory = IngesterFactory()
        assert factory._ingesters == {}
    
    def test_register_ingester(self):
        """수집기 등록 테스트"""
        factory = IngesterFactory()
        factory.register_ingester(TestIngester1)
        
        assert "TestIngester1" in factory._ingesters
        assert factory._ingesters["TestIngester1"] == TestIngester1
    
    def test_register_invalid_ingester(self):
        """유효하지 않은 수집기 등록 테스트"""
        factory = IngesterFactory()
        
        # BaseIngester의 하위 클래스가 아닌 경우
        class InvalidIngester:
            pass
        
        with pytest.raises(ValueError):
            factory.register_ingester(InvalidIngester)
    
    def test_register_duplicate_ingester(self):
        """중복 수집기 등록 테스트"""
        factory = IngesterFactory()
        factory.register_ingester(TestIngester1)
        
        with pytest.raises(ValueError):
            factory.register_ingester(TestIngester1)
    
    def test_create_ingester(self):
        """수집기 생성 테스트"""
        factory = IngesterFactory()
        factory.register_ingester(TestIngester1)
        
        ingester = factory.create_ingester("TestIngester1", "커스텀 이름", "커스텀 설명")
        
        assert isinstance(ingester, TestIngester1)
        assert ingester.name == "커스텀 이름"
        assert ingester.description == "커스텀 설명"
    
    def test_create_unregistered_ingester(self):
        """등록되지 않은 수집기 생성 테스트"""
        factory = IngesterFactory()
        
        with pytest.raises(ValueError):
            factory.create_ingester("UnregisteredIngester")
    
    def test_get_available_ingesters(self):
        """사용 가능한 수집기 목록 테스트"""
        factory = IngesterFactory()
        factory.register_ingester(TestIngester1)
        factory.register_ingester(TestIngester2)
        
        ingesters = factory.get_available_ingesters()
        
        assert len(ingesters) == 2
        assert "TestIngester1" in ingesters
        assert "TestIngester2" in ingesters
    
    def test_get_ingester_by_file_extension(self):
        """파일 확장자로 수집기 찾기 테스트"""
        factory = IngesterFactory()
        factory.register_ingester(TestIngester1)
        factory.register_ingester(TestIngester2)
        
        # TestIngester1이 지원하는 확장자
        ingester_name = factory.get_ingester_by_file_extension("file.test1")
        assert ingester_name == "TestIngester1"
        
        # TestIngester2가 지원하는 확장자
        ingester_name = factory.get_ingester_by_file_extension("file.csv")
        assert ingester_name == "TestIngester2"
        
        # 지원하지 않는 확장자
        ingester_name = factory.get_ingester_by_file_extension("file.unknown")
        assert ingester_name is None
    
    def test_clear_ingesters(self):
        """수집기 등록 해제 테스트"""
        factory = IngesterFactory()
        factory.register_ingester(TestIngester1)
        factory.register_ingester(TestIngester2)
        
        assert len(factory._ingesters) == 2
        
        factory.clear_ingesters()
        
        assert len(factory._ingesters) == 0