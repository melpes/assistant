# -*- coding: utf-8 -*-
"""
캐싱 시스템 테스트

캐싱 시스템의 기능을 테스트합니다.
"""

import os
import sys
import unittest
import tempfile
import shutil
import time
from datetime import datetime

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.cache_manager import (
    CacheEntry, MemoryCache, DiskCache, CacheManager,
    cached, invalidate_cache, get_cache_manager
)

class TestCacheManager(unittest.TestCase):
    """
    캐싱 시스템 테스트 클래스
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        
        # 메모리 캐시 초기화
        self.memory_cache = MemoryCache(max_size=100, default_ttl=60)
        
        # 디스크 캐시 초기화
        self.disk_cache = DiskCache(cache_dir=self.temp_dir, default_ttl=60)
        
        # 캐시 관리자 초기화
        self.cache_manager = CacheManager()
        self.cache_manager.memory_cache = self.memory_cache
        self.cache_manager.disk_cache = self.disk_cache
    
    def tearDown(self):
        """
        테스트 정리
        """
        # 임시 디렉토리 삭제
        shutil.rmtree(self.temp_dir)
    
    def test_cache_entry(self):
        """
        캐시 항목 테스트
        """
        # 캐시 항목 생성
        entry = CacheEntry('test_key', 'test_value', ttl=1)
        
        # 속성 확인
        self.assertEqual(entry.key, 'test_key')
        self.assertEqual(entry.value, 'test_value')
        self.assertEqual(entry.ttl, 1)
        self.assertEqual(entry.access_count, 0)
        
        # 접근 기록 업데이트
        entry.access()
        self.assertEqual(entry.access_count, 1)
        
        # 만료 확인
        self.assertFalse(entry.is_expired())
        
        # 만료 대기
        time.sleep(1.1)
        self.assertTrue(entry.is_expired())
        
        # 딕셔너리 변환
        entry_dict = entry.to_dict()
        self.assertEqual(entry_dict['key'], 'test_key')
        self.assertEqual(entry_dict['access_count'], 1)
        self.assertTrue(entry_dict['is_expired'])
    
    def test_memory_cache(self):
        """
        메모리 캐시 테스트
        """
        # 캐시 값 설정
        self.memory_cache.set('test_key', 'test_value')
        
        # 캐시 값 조회
        value = self.memory_cache.get('test_key')
        self.assertEqual(value, 'test_value')
        
        # 기본값 테스트
        value = self.memory_cache.get('non_existent_key', 'default_value')
        self.assertEqual(value, 'default_value')
        
        # TTL 테스트
        self.memory_cache.set('ttl_key', 'ttl_value', ttl=1)
        self.assertEqual(self.memory_cache.get('ttl_key'), 'ttl_value')
        time.sleep(1.1)
        self.assertIsNone(self.memory_cache.get('ttl_key'))
        
        # 캐시 삭제
        self.memory_cache.set('delete_key', 'delete_value')
        self.assertEqual(self.memory_cache.get('delete_key'), 'delete_value')
        self.assertTrue(self.memory_cache.delete('delete_key'))
        self.assertIsNone(self.memory_cache.get('delete_key'))
        
        # 캐시 통계
        stats = self.memory_cache.get_stats()
        self.assertIn('total_items', stats)
        self.assertIn('hit_rate', stats)
        self.assertIn('utilization', stats)
        
        # 캐시 초기화
        self.memory_cache.clear()
        self.assertIsNone(self.memory_cache.get('test_key'))
    
    def test_disk_cache(self):
        """
        디스크 캐시 테스트
        """
        # 캐시 값 설정
        self.disk_cache.set('test_key', 'test_value')
        
        # 캐시 값 조회
        value = self.disk_cache.get('test_key')
        self.assertEqual(value, 'test_value')
        
        # 기본값 테스트
        value = self.disk_cache.get('non_existent_key', 'default_value')
        self.assertEqual(value, 'default_value')
        
        # TTL 테스트
        self.disk_cache.set('ttl_key', 'ttl_value', ttl=1)
        self.assertEqual(self.disk_cache.get('ttl_key'), 'ttl_value')
        time.sleep(1.1)
        self.assertIsNone(self.disk_cache.get('ttl_key'))
        
        # 캐시 삭제
        self.disk_cache.set('delete_key', 'delete_value')
        self.assertEqual(self.disk_cache.get('delete_key'), 'delete_value')
        self.assertTrue(self.disk_cache.delete('delete_key'))
        self.assertIsNone(self.disk_cache.get('delete_key'))
        
        # 캐시 통계
        stats = self.disk_cache.get_stats()
        self.assertIn('total_items', stats)
        self.assertIn('total_size_bytes', stats)
        
        # 캐시 초기화
        self.disk_cache.clear()
        self.assertIsNone(self.disk_cache.get('test_key'))
    
    def test_cache_manager(self):
        """
        캐시 관리자 테스트
        """
        # 캐시 값 설정
        self.cache_manager.set('test_key', 'test_value')
        
        # 캐시 값 조회
        value = self.cache_manager.get('test_key')
        self.assertEqual(value, 'test_value')
        
        # 기본값 테스트
        value = self.cache_manager.get('non_existent_key', 'default_value')
        self.assertEqual(value, 'default_value')
        
        # 캐시 삭제
        self.cache_manager.set('delete_key', 'delete_value')
        self.assertEqual(self.cache_manager.get('delete_key'), 'delete_value')
        self.assertTrue(self.cache_manager.delete('delete_key'))
        self.assertIsNone(self.cache_manager.get('delete_key'))
        
        # 캐시 통계
        stats = self.cache_manager.get_stats()
        self.assertIn('memory', stats)
        self.assertIn('disk', stats)
        
        # 캐시 초기화
        self.cache_manager.clear()
        self.assertIsNone(self.cache_manager.get('test_key'))
    
    def test_cache_decorator(self):
        """
        캐시 데코레이터 테스트
        """
        # 전역 캐시 관리자 설정
        global _cache_manager
        _cache_manager = self.cache_manager
        
        # 캐시 데코레이터 테스트
        call_count = 0
        
        @cached(ttl=60)
        def test_function(arg1, arg2=None):
            nonlocal call_count
            call_count += 1
            return f"{arg1}_{arg2}"
        
        # 첫 번째 호출 (캐시 미스)
        result1 = test_function("test", arg2="value")
        self.assertEqual(result1, "test_value")
        self.assertEqual(call_count, 1)
        
        # 두 번째 호출 (캐시 히트)
        result2 = test_function("test", arg2="value")
        self.assertEqual(result2, "test_value")
        self.assertEqual(call_count, 1)  # 함수가 다시 호출되지 않음
        
        # 다른 인자로 호출 (캐시 미스)
        result3 = test_function("test", arg2="other")
        self.assertEqual(result3, "test_other")
        self.assertEqual(call_count, 2)
        
        # 캐시 무효화 테스트
        @invalidate_cache()
        def invalidate_function():
            return "invalidated"
        
        invalidate_function()
        
        # 캐시가 무효화되어 함수가 다시 호출됨
        result4 = test_function("test", arg2="value")
        self.assertEqual(result4, "test_value")
        self.assertEqual(call_count, 3)
    
    def test_global_cache_manager(self):
        """
        전역 캐시 관리자 테스트
        """
        # 전역 캐시 관리자 초기화
        global _cache_manager
        _cache_manager = None
        
        # 전역 캐시 관리자 가져오기
        cache_manager = get_cache_manager()
        self.assertIsNotNone(cache_manager)
        
        # 동일한 인스턴스 확인
        cache_manager2 = get_cache_manager()
        self.assertIs(cache_manager, cache_manager2)

if __name__ == '__main__':
    unittest.main()