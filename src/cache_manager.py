# -*- coding: utf-8 -*-
"""
캐싱 시스템

자주 사용되는 데이터를 캐싱하여 성능을 향상시키는 시스템입니다.
메모리 캐시, 디스크 캐시, 캐시 무효화 등의 기능을 제공합니다.
"""

import os
import sys
import time
import json
import pickle
import hashlib
import logging
import functools
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from pathlib import Path

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.logging_system import get_logger
from src.config_manager import ConfigManager
from src.performance_monitor import profile_function, measure_time

# 로거 설정
logger = get_logger('cache')

class CacheEntry:
    """
    캐시 항목 클래스
    
    캐시된 데이터와 메타데이터를 저장합니다.
    """
    
    def __init__(self, key: str, value: Any, ttl: int = None):
        """
        캐시 항목 초기화
        
        Args:
            key: 캐시 키
            value: 캐시 값
            ttl: 유효 시간 (초)
        """
        self.key = key
        self.value = value
        self.created_at = datetime.now()
        self.last_accessed = self.created_at
        self.access_count = 0
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """
        만료 여부 확인
        
        Returns:
            bool: 만료 여부
        """
        if self.ttl is None:
            return False
        
        return (datetime.now() - self.created_at).total_seconds() > self.ttl
    
    def access(self) -> None:
        """
        접근 기록 업데이트
        """
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """
        딕셔너리 변환
        
        Returns:
            Dict[str, Any]: 딕셔너리 표현
        """
        return {
            'key': self.key,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'ttl': self.ttl,
            'is_expired': self.is_expired()
        }

class MemoryCache:
    """
    메모리 캐시 클래스
    
    메모리에 데이터를 캐싱합니다.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = None):
        """
        메모리 캐시 초기화
        
        Args:
            max_size: 최대 항목 수
            default_ttl: 기본 유효 시간 (초)
        """
        self.cache = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.lock = threading.RLock()
    
    @profile_function
    def get(self, key: str, default: Any = None) -> Any:
        """
        캐시 값 조회
        
        Args:
            key: 캐시 키
            default: 기본값
            
        Returns:
            Any: 캐시 값 또는 기본값
        """
        with self.lock:
            if key not in self.cache:
                return default
            
            entry = self.cache[key]
            
            # 만료 확인
            if entry.is_expired():
                del self.cache[key]
                return default
            
            # 접근 기록 업데이트
            entry.access()
            
            return entry.value
    
    @profile_function
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """
        캐시 값 설정
        
        Args:
            key: 캐시 키
            value: 캐시 값
            ttl: 유효 시간 (초)
        """
        with self.lock:
            # 캐시 크기 확인
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict()
            
            # TTL 설정
            if ttl is None:
                ttl = self.default_ttl
            
            # 캐시 항목 생성
            entry = CacheEntry(key, value, ttl)
            self.cache[key] = entry
    
    @profile_function
    def delete(self, key: str) -> bool:
        """
        캐시 항목 삭제
        
        Args:
            key: 캐시 키
            
        Returns:
            bool: 삭제 성공 여부
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    @profile_function
    def clear(self) -> None:
        """
        캐시 전체 삭제
        """
        with self.lock:
            self.cache.clear()
    
    @profile_function
    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 조회
        
        Returns:
            Dict[str, Any]: 캐시 통계
        """
        with self.lock:
            # 만료된 항목 제거
            self._remove_expired()
            
            # 통계 계산
            total_items = len(self.cache)
            
            if total_items == 0:
                return {
                    'total_items': 0,
                    'hit_rate': 0,
                    'miss_rate': 0,
                    'utilization': 0,
                    'avg_access_count': 0,
                    'oldest_item_age': 0,
                    'newest_item_age': 0
                }
            
            total_access = sum(entry.access_count for entry in self.cache.values())
            
            # 항목 나이 계산
            now = datetime.now()
            oldest = min(self.cache.values(), key=lambda e: e.created_at)
            newest = max(self.cache.values(), key=lambda e: e.created_at)
            oldest_age = (now - oldest.created_at).total_seconds()
            newest_age = (now - newest.created_at).total_seconds()
            
            return {
                'total_items': total_items,
                'hit_rate': total_access / (total_access + 1) * 100,  # 히트율 (%)
                'miss_rate': 100 - (total_access / (total_access + 1) * 100),  # 미스율 (%)
                'utilization': total_items / self.max_size * 100,  # 사용률 (%)
                'avg_access_count': total_access / total_items,  # 평균 접근 횟수
                'oldest_item_age': oldest_age,  # 가장 오래된 항목 나이 (초)
                'newest_item_age': newest_age  # 가장 최근 항목 나이 (초)
            }
    
    def _evict(self) -> None:
        """
        캐시 항목 제거
        """
        # 만료된 항목 제거
        if self._remove_expired() > 0:
            return
        
        # LRU 정책: 가장 오래 접근하지 않은 항목 제거
        if self.cache:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_accessed)
            del self.cache[oldest_key]
    
    def _remove_expired(self) -> int:
        """
        만료된 항목 제거
        
        Returns:
            int: 제거된 항목 수
        """
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)

class DiskCache:
    """
    디스크 캐시 클래스
    
    파일 시스템에 데이터를 캐싱합니다.
    """
    
    def __init__(self, cache_dir: str = None, default_ttl: int = None, config_manager: ConfigManager = None):
        """
        디스크 캐시 초기화
        
        Args:
            cache_dir: 캐시 디렉토리
            default_ttl: 기본 유효 시간 (초)
            config_manager: 설정 관리자
        """
        self.config_manager = config_manager or ConfigManager()
        
        # 캐시 디렉토리 설정
        if cache_dir is None:
            cache_dir = self.config_manager.get_config_value('system.cache.disk_cache_dir')
            
            if cache_dir is None:
                cache_dir = os.path.join(parent_dir, 'cache')
        
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.lock = threading.RLock()
        
        # 캐시 디렉토리 생성
        os.makedirs(self.cache_dir, exist_ok=True)
    
    @profile_function
    def get(self, key: str, default: Any = None) -> Any:
        """
        캐시 값 조회
        
        Args:
            key: 캐시 키
            default: 기본값
            
        Returns:
            Any: 캐시 값 또는 기본값
        """
        with self.lock:
            cache_file = self._get_cache_file(key)
            
            if not os.path.exists(cache_file):
                return default
            
            try:
                with open(cache_file, 'rb') as f:
                    entry_data = pickle.load(f)
                
                # 만료 확인
                if self._is_expired(entry_data):
                    os.remove(cache_file)
                    return default
                
                # 접근 기록 업데이트
                entry_data['last_accessed'] = datetime.now()
                entry_data['access_count'] += 1
                
                with open(cache_file, 'wb') as f:
                    pickle.dump(entry_data, f)
                
                return entry_data['value']
                
            except Exception as e:
                logger.error(f"캐시 파일 읽기 오류: {e}")
                return default
    
    @profile_function
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """
        캐시 값 설정
        
        Args:
            key: 캐시 키
            value: 캐시 값
            ttl: 유효 시간 (초)
        """
        with self.lock:
            cache_file = self._get_cache_file(key)
            
            # TTL 설정
            if ttl is None:
                ttl = self.default_ttl
            
            # 캐시 항목 생성
            entry_data = {
                'key': key,
                'value': value,
                'created_at': datetime.now(),
                'last_accessed': datetime.now(),
                'access_count': 0,
                'ttl': ttl
            }
            
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(entry_data, f)
            except Exception as e:
                logger.error(f"캐시 파일 쓰기 오류: {e}")
    
    @profile_function
    def delete(self, key: str) -> bool:
        """
        캐시 항목 삭제
        
        Args:
            key: 캐시 키
            
        Returns:
            bool: 삭제 성공 여부
        """
        with self.lock:
            cache_file = self._get_cache_file(key)
            
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    return True
                except Exception as e:
                    logger.error(f"캐시 파일 삭제 오류: {e}")
            
            return False
    
    @profile_function
    def clear(self) -> None:
        """
        캐시 전체 삭제
        """
        with self.lock:
            try:
                for file in os.listdir(self.cache_dir):
                    file_path = os.path.join(self.cache_dir, file)
                    if os.path.isfile(file_path) and file.endswith('.cache'):
                        os.remove(file_path)
            except Exception as e:
                logger.error(f"캐시 디렉토리 정리 오류: {e}")
    
    @profile_function
    def get_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 조회
        
        Returns:
            Dict[str, Any]: 캐시 통계
        """
        with self.lock:
            # 만료된 항목 제거
            self._remove_expired()
            
            # 캐시 파일 목록
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.cache')]
            total_items = len(cache_files)
            
            if total_items == 0:
                return {
                    'total_items': 0,
                    'total_size_bytes': 0,
                    'avg_item_size_bytes': 0,
                    'oldest_item_age': 0,
                    'newest_item_age': 0
                }
            
            # 통계 계산
            total_size = 0
            access_counts = []
            created_times = []
            
            for file in cache_files:
                file_path = os.path.join(self.cache_dir, file)
                total_size += os.path.getsize(file_path)
                
                try:
                    with open(file_path, 'rb') as f:
                        entry_data = pickle.load(f)
                        access_counts.append(entry_data.get('access_count', 0))
                        created_times.append(entry_data.get('created_at', datetime.now()))
                except Exception:
                    pass
            
            # 항목 나이 계산
            now = datetime.now()
            oldest_age = (now - min(created_times)).total_seconds() if created_times else 0
            newest_age = (now - max(created_times)).total_seconds() if created_times else 0
            
            return {
                'total_items': total_items,
                'total_size_bytes': total_size,
                'avg_item_size_bytes': total_size / total_items if total_items > 0 else 0,
                'avg_access_count': sum(access_counts) / len(access_counts) if access_counts else 0,
                'oldest_item_age': oldest_age,
                'newest_item_age': newest_age
            }
    
    def _get_cache_file(self, key: str) -> str:
        """
        캐시 파일 경로 조회
        
        Args:
            key: 캐시 키
            
        Returns:
            str: 캐시 파일 경로
        """
        # 키 해시 생성
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")
    
    def _is_expired(self, entry_data: Dict[str, Any]) -> bool:
        """
        만료 여부 확인
        
        Args:
            entry_data: 캐시 항목 데이터
            
        Returns:
            bool: 만료 여부
        """
        ttl = entry_data.get('ttl')
        created_at = entry_data.get('created_at')
        
        if ttl is None or created_at is None:
            return False
        
        return (datetime.now() - created_at).total_seconds() > ttl
    
    def _remove_expired(self) -> int:
        """
        만료된 항목 제거
        
        Returns:
            int: 제거된 항목 수
        """
        removed_count = 0
        
        for file in os.listdir(self.cache_dir):
            if not file.endswith('.cache'):
                continue
            
            file_path = os.path.join(self.cache_dir, file)
            
            try:
                with open(file_path, 'rb') as f:
                    entry_data = pickle.load(f)
                
                if self._is_expired(entry_data):
                    os.remove(file_path)
                    removed_count += 1
            except Exception:
                # 손상된 캐시 파일 제거
                try:
                    os.remove(file_path)
                    removed_count += 1
                except Exception:
                    pass
        
        return removed_countclass Cac
heManager:
    """
    캐시 관리자 클래스
    
    메모리 캐시와 디스크 캐시를 통합 관리합니다.
    """
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        캐시 관리자 초기화
        
        Args:
            config_manager: 설정 관리자
        """
        self.config_manager = config_manager or ConfigManager()
        
        # 캐시 설정 로드
        self.memory_cache_enabled = self.config_manager.get_config_value('system.cache.memory_cache_enabled', True)
        self.disk_cache_enabled = self.config_manager.get_config_value('system.cache.disk_cache_enabled', True)
        self.memory_cache_size = self.config_manager.get_config_value('system.cache.memory_cache_size', 1000)
        self.default_ttl = self.config_manager.get_config_value('system.cache.default_ttl', 3600)  # 1시간
        self.disk_cache_dir = self.config_manager.get_config_value('system.cache.disk_cache_dir')
        
        # 캐시 초기화
        self.memory_cache = MemoryCache(self.memory_cache_size, self.default_ttl) if self.memory_cache_enabled else None
        self.disk_cache = DiskCache(self.disk_cache_dir, self.default_ttl, self.config_manager) if self.disk_cache_enabled else None
        
        logger.info(f"캐시 관리자 초기화 완료 (메모리 캐시: {'활성화' if self.memory_cache_enabled else '비활성화'}, "
                   f"디스크 캐시: {'활성화' if self.disk_cache_enabled else '비활성화'})")
    
    @profile_function
    def get(self, key: str, default: Any = None) -> Any:
        """
        캐시 값 조회
        
        Args:
            key: 캐시 키
            default: 기본값
            
        Returns:
            Any: 캐시 값 또는 기본값
        """
        # 메모리 캐시 조회
        if self.memory_cache_enabled:
            value = self.memory_cache.get(key)
            if value is not None:
                return value
        
        # 디스크 캐시 조회
        if self.disk_cache_enabled:
            value = self.disk_cache.get(key)
            if value is not None:
                # 메모리 캐시에 저장
                if self.memory_cache_enabled:
                    self.memory_cache.set(key, value)
                return value
        
        return default
    
    @profile_function
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """
        캐시 값 설정
        
        Args:
            key: 캐시 키
            value: 캐시 값
            ttl: 유효 시간 (초)
        """
        # 메모리 캐시 저장
        if self.memory_cache_enabled:
            self.memory_cache.set(key, value, ttl)
        
        # 디스크 캐시 저장
        if self.disk_cache_enabled:
            self.disk_cache.set(key, value, ttl)
    
    @profile_function
    def delete(self, key: str) -> bool:
        """
        캐시 항목 삭제
        
        Args:
            key: 캐시 키
            
        Returns:
            bool: 삭제 성공 여부
        """
        result = False
        
        # 메모리 캐시 삭제
        if self.memory_cache_enabled:
            result = self.memory_cache.delete(key) or result
        
        # 디스크 캐시 삭제
        if self.disk_cache_enabled:
            result = self.disk_cache.delete(key) or result
        
        return result
    
    @profile_function
    def clear(self) -> None:
        """
        캐시 전체 삭제
        """
        # 메모리 캐시 삭제
        if self.memory_cache_enabled:
            self.memory_cache.clear()
        
        # 디스크 캐시 삭제
        if self.disk_cache_enabled:
            self.disk_cache.clear()
        
        logger.info("캐시가 초기화되었습니다.")
    
    @profile_function
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        캐시 통계 조회
        
        Returns:
            Dict[str, Dict[str, Any]]: 캐시 통계
        """
        stats = {}
        
        # 메모리 캐시 통계
        if self.memory_cache_enabled:
            stats['memory'] = self.memory_cache.get_stats()
        
        # 디스크 캐시 통계
        if self.disk_cache_enabled:
            stats['disk'] = self.disk_cache.get_stats()
        
        return stats

def cached(ttl: int = None, key_prefix: str = None):
    """
    캐시 데코레이터
    
    함수 결과를 캐싱합니다.
    
    Args:
        ttl: 유효 시간 (초)
        key_prefix: 캐시 키 접두사
        
    Returns:
        Callable: 데코레이터 함수
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 관리자 가져오기
            cache_manager = get_cache_manager()
            
            # 캐시 키 생성
            cache_key = _generate_cache_key(func, key_prefix, args, kwargs)
            
            # 캐시 조회
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"캐시 히트: {cache_key}")
                return cached_result
            
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 캐시 저장
            cache_manager.set(cache_key, result, ttl)
            logger.debug(f"캐시 미스: {cache_key}")
            
            return result
        return wrapper
    return decorator

def invalidate_cache(key_pattern: str = None):
    """
    캐시 무효화 데코레이터
    
    함수 실행 후 캐시를 무효화합니다.
    
    Args:
        key_pattern: 캐시 키 패턴
        
    Returns:
        Callable: 데코레이터 함수
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 캐시 무효화
            if key_pattern:
                invalidate_cache_by_pattern(key_pattern)
            
            return result
        return wrapper
    return decorator

def _generate_cache_key(func: Callable, prefix: str = None, args: tuple = None, kwargs: dict = None) -> str:
    """
    캐시 키 생성
    
    Args:
        func: 함수
        prefix: 접두사
        args: 위치 인자
        kwargs: 키워드 인자
        
    Returns:
        str: 캐시 키
    """
    # 기본 키 생성
    key_parts = [func.__module__, func.__qualname__]
    
    # 접두사 추가
    if prefix:
        key_parts.insert(0, prefix)
    
    # 인자 추가
    if args:
        key_parts.append(str(args))
    
    if kwargs:
        key_parts.append(str(sorted(kwargs.items())))
    
    # 키 결합
    return ":".join(str(p) for p in key_parts)

def invalidate_cache_by_pattern(pattern: str) -> int:
    """
    패턴으로 캐시 무효화
    
    Args:
        pattern: 캐시 키 패턴
        
    Returns:
        int: 무효화된 항목 수
    """
    # 캐시 관리자 가져오기
    cache_manager = get_cache_manager()
    
    # TODO: 패턴 기반 캐시 무효화 구현
    # 현재는 전체 캐시 삭제
    cache_manager.clear()
    
    return 0

# 전역 캐시 관리자 인스턴스
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """
    캐시 관리자 인스턴스 가져오기
    
    Returns:
        CacheManager: 캐시 관리자 인스턴스
    """
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager()
    
    return _cache_manager

def main():
    """
    메인 함수
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='캐시 관리 도구')
    
    parser.add_argument('--action', '-a', choices=[
        'stats', 'clear', 'get', 'set', 'delete'
    ], default='stats', help='수행할 작업')
    
    parser.add_argument('--key', '-k', help='캐시 키')
    parser.add_argument('--value', '-v', help='캐시 값')
    parser.add_argument('--ttl', '-t', type=int, help='유효 시간 (초)')
    parser.add_argument('--verbose', action='store_true', help='상세 출력')
    
    args = parser.parse_args()
    
    # 로깅 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 캐시 관리자 초기화
    cache_manager = get_cache_manager()
    
    # 작업 수행
    if args.action == 'stats':
        # 캐시 통계 조회
        stats = cache_manager.get_stats()
        
        print("캐시 통계:")
        
        if 'memory' in stats:
            memory_stats = stats['memory']
            print("\n메모리 캐시:")
            print(f"  총 항목 수: {memory_stats['total_items']}")
            print(f"  히트율: {memory_stats['hit_rate']:.2f}%")
            print(f"  사용률: {memory_stats['utilization']:.2f}%")
            print(f"  평균 접근 횟수: {memory_stats['avg_access_count']:.2f}")
        
        if 'disk' in stats:
            disk_stats = stats['disk']
            print("\n디스크 캐시:")
            print(f"  총 항목 수: {disk_stats['total_items']}")
            print(f"  총 크기: {disk_stats['total_size_bytes'] / 1024:.2f} KB")
            print(f"  평균 항목 크기: {disk_stats['avg_item_size_bytes'] / 1024:.2f} KB")
            print(f"  평균 접근 횟수: {disk_stats['avg_access_count']:.2f}")
    
    elif args.action == 'clear':
        # 캐시 초기화
        cache_manager.clear()
        print("캐시가 초기화되었습니다.")
    
    elif args.action == 'get':
        # 캐시 값 조회
        if not args.key:
            print("캐시 키를 지정해야 합니다.")
            return
        
        value = cache_manager.get(args.key)
        if value is not None:
            print(f"캐시 값: {value}")
        else:
            print("캐시 항목을 찾을 수 없습니다.")
    
    elif args.action == 'set':
        # 캐시 값 설정
        if not args.key or args.value is None:
            print("캐시 키와 값을 모두 지정해야 합니다.")
            return
        
        cache_manager.set(args.key, args.value, args.ttl)
        print(f"캐시 값이 설정되었습니다: {args.key} = {args.value}")
    
    elif args.action == 'delete':
        # 캐시 항목 삭제
        if not args.key:
            print("캐시 키를 지정해야 합니다.")
            return
        
        result = cache_manager.delete(args.key)
        if result:
            print("캐시 항목이 삭제되었습니다.")
        else:
            print("캐시 항목을 찾을 수 없습니다.")

if __name__ == '__main__':
    main()