# -*- coding: utf-8 -*-
"""
IngesterFactory 클래스 정의

플러그인 방식으로 다양한 데이터 수집기를 로드하고 관리하는 팩토리 클래스입니다.
"""

import os
import importlib
import inspect
import logging
from typing import Dict, List, Type, Optional
import pkgutil
from pathlib import Path

from .base_ingester import BaseIngester

# 로깅 설정
logger = logging.getLogger(__name__)

class IngesterFactory:
    """
    데이터 수집기 팩토리 클래스
    
    플러그인 방식으로 다양한 데이터 수집기를 로드하고 관리합니다.
    """
    
    def __init__(self):
        """
        수집기 팩토리 초기화
        """
        self._ingesters: Dict[str, Type[BaseIngester]] = {}
        logger.debug("IngesterFactory 초기화")
    
    def register_ingester(self, ingester_class: Type[BaseIngester]) -> None:
        """
        수집기 클래스를 등록합니다.
        
        Args:
            ingester_class: 등록할 수집기 클래스
            
        Raises:
            ValueError: 이미 같은 이름의 수집기가 등록되어 있는 경우
        """
        # BaseIngester의 하위 클래스인지 확인
        if not issubclass(ingester_class, BaseIngester):
            raise ValueError(f"{ingester_class.__name__}은(는) BaseIngester의 하위 클래스가 아닙니다.")
        
        # 임시 인스턴스를 생성하여 이름 가져오기
        temp_instance = ingester_class("temp", "temp")
        ingester_name = ingester_class.__name__
        
        # 이미 등록된 수집기인지 확인
        if ingester_name in self._ingesters:
            raise ValueError(f"이미 등록된 수집기 이름입니다: {ingester_name}")
        
        # 수집기 등록
        self._ingesters[ingester_name] = ingester_class
        logger.info(f"수집기 등록: {ingester_name}")
    
    def create_ingester(self, ingester_name: str, *args, **kwargs) -> BaseIngester:
        """
        등록된 수집기 클래스로부터 인스턴스를 생성합니다.
        
        Args:
            ingester_name: 생성할 수집기 이름
            *args: 수집기 생성자에 전달할 위치 인자
            **kwargs: 수집기 생성자에 전달할 키워드 인자
            
        Returns:
            BaseIngester: 생성된 수집기 인스턴스
            
        Raises:
            ValueError: 등록되지 않은 수집기 이름인 경우
        """
        if ingester_name not in self._ingesters:
            raise ValueError(f"등록되지 않은 수집기 이름입니다: {ingester_name}")
        
        ingester_class = self._ingesters[ingester_name]
        return ingester_class(*args, **kwargs)
    
    def get_available_ingesters(self) -> List[str]:
        """
        등록된 모든 수집기 이름 목록을 반환합니다.
        
        Returns:
            List[str]: 등록된 수집기 이름 목록
        """
        return list(self._ingesters.keys())
    
    def get_ingester_by_file_extension(self, file_path: str) -> Optional[str]:
        """
        파일 확장자에 맞는 수집기 이름을 찾습니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            Optional[str]: 적합한 수집기 이름, 없으면 None
        """
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        
        for ingester_name, ingester_class in self._ingesters.items():
            # 임시 인스턴스 생성
            temp_instance = ingester_class("temp", "temp")
            if file_ext in temp_instance.get_supported_file_types():
                return ingester_name
        
        return None
    
    def discover_ingesters(self, package_name: str = 'src.ingesters') -> None:
        """
        지정된 패키지에서 모든 수집기 클래스를 자동으로 발견하고 등록합니다.
        
        Args:
            package_name: 수집기 클래스를 검색할 패키지 이름
        """
        logger.info(f"{package_name} 패키지에서 수집기 검색 시작")
        
        try:
            package = importlib.import_module(package_name)
            package_path = os.path.dirname(package.__file__)
            
            for _, module_name, is_pkg in pkgutil.iter_modules([package_path]):
                if is_pkg:
                    continue  # 서브패키지는 건너뜀
                
                # 모듈이 이미 'ingester'로 끝나는 경우에만 처리
                if module_name.endswith('_ingester'):
                    try:
                        module = importlib.import_module(f"{package_name}.{module_name}")
                        
                        # 모듈 내의 모든 클래스 검사
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            # BaseIngester의 직접적인 하위 클래스이고, 추상 클래스가 아닌 경우
                            if (issubclass(obj, BaseIngester) and 
                                obj.__module__ == module.__name__ and 
                                obj != BaseIngester):
                                self.register_ingester(obj)
                    except (ImportError, AttributeError) as e:
                        logger.warning(f"모듈 {module_name} 로드 중 오류 발생: {e}")
            
            logger.info(f"수집기 검색 완료: {len(self._ingesters)}개 발견")
            
        except ImportError as e:
            logger.error(f"패키지 {package_name} 로드 중 오류 발생: {e}")
    
    def clear_ingesters(self) -> None:
        """
        등록된 모든 수집기를 제거합니다.
        """
        self._ingesters.clear()
        logger.debug("모든 수집기 등록 해제")