# -*- coding: utf-8 -*-
"""
성능 모니터링 시스템 테스트

성능 모니터링 시스템의 기능을 테스트합니다.
"""

import os
import sys
import unittest
import sqlite3
import tempfile
import time
from datetime import datetime

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.performance_monitor import (
    QueryProfiler, MemoryProfiler, PerformanceMonitor,
    profile_function, measure_time, profile_query, take_memory_snapshot,
    analyze_performance, optimize_performance
)

class TestPerformanceMonitor(unittest.TestCase):
    """
    성능 모니터링 시스템 테스트 클래스
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        # 임시 데이터베이스 생성
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 테스트 테이블 생성
        self.cursor.execute('''
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT,
            value INTEGER
        )
        ''')
        
        # 테스트 데이터 삽입
        for i in range(100):
            self.cursor.execute('INSERT INTO test_table (name, value) VALUES (?, ?)', (f'item_{i}', i))
        
        self.conn.commit()
        
        # 쿼리 프로파일러 초기화
        self.query_profiler = QueryProfiler(self.db_path)
        
        # 메모리 프로파일러 초기화
        self.memory_profiler = MemoryProfiler()
        
        # 성능 모니터 초기화
        self.performance_monitor = PerformanceMonitor()
    
    def tearDown(self):
        """
        테스트 정리
        """
        # 데이터베이스 연결 종료
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_query_profiler(self):
        """
        쿼리 프로파일러 테스트
        """
        # 프로파일링 활성화
        self.query_profiler.enable()
        
        # 쿼리 실행 및 프로파일링
        with self.query_profiler.profile_query('SELECT * FROM test_table'):
            self.cursor.execute('SELECT * FROM test_table')
            self.cursor.fetchall()
        
        # 느린 쿼리 실행 및 프로파일링
        with self.query_profiler.profile_query('SELECT * FROM test_table WHERE value > 50'):
            self.cursor.execute('SELECT * FROM test_table WHERE value > 50')
            self.cursor.fetchall()
        
        # 통계 확인
        stats = self.query_profiler.get_stats()
        self.assertGreaterEqual(len(stats), 2)
        
        # 느린 쿼리 확인
        slow_queries = self.query_profiler.get_slow_queries(0)  # 모든 쿼리
        self.assertGreaterEqual(len(slow_queries), 2)
        
        # 쿼리 분석
        analysis = self.query_profiler.analyze_query('SELECT * FROM test_table WHERE value > 50')
        self.assertEqual(analysis['query'], 'SELECT * FROM test_table WHERE value > 50')
        self.assertIn('table_scan', analysis)
        
        # 통계 초기화
        self.query_profiler.reset_stats()
        stats = self.query_profiler.get_stats()
        self.assertEqual(len(stats), 0)
        
        # 프로파일링 비활성화
        self.query_profiler.disable()
    
    def test_memory_profiler(self):
        """
        메모리 프로파일러 테스트
        """
        # 프로파일링 활성화
        self.memory_profiler.enable()
        
        # 스냅샷 생성
        snapshot_index = self.memory_profiler.take_snapshot('test_snapshot')
        self.assertGreaterEqual(snapshot_index, 0)
        
        # 메모리 할당
        data = [i for i in range(1000000)]
        
        # 두 번째 스냅샷 생성
        snapshot_index2 = self.memory_profiler.take_snapshot('test_snapshot2')
        self.assertGreaterEqual(snapshot_index2, 1)
        
        # 스냅샷 비교
        comparison = self.memory_profiler.compare_snapshots(snapshot_index, snapshot_index2)
        self.assertIsInstance(comparison, list)
        
        # 메모리 사용량 확인
        memory_usage = self.memory_profiler.get_memory_usage()
        self.assertIn('rss', memory_usage)
        self.assertIn('vms', memory_usage)
        
        # 메모리 사용량이 많은 객체 확인
        top_objects = self.memory_profiler.get_top_memory_objects()
        self.assertIsInstance(top_objects, list)
        
        # 스냅샷 초기화
        self.memory_profiler.clear_snapshots()
        
        # 프로파일링 비활성화
        self.memory_profiler.disable()
    
    def test_performance_monitor(self):
        """
        성능 모니터 테스트
        """
        # 모니터링 활성화
        self.performance_monitor.enable()
        
        # 시간 측정
        with self.performance_monitor.measure_time('test_operation'):
            time.sleep(0.1)
        
        # 함수 프로파일링
        @self.performance_monitor.profile_function
        def test_function():
            time.sleep(0.1)
            return 'test'
        
        result = test_function()
        self.assertEqual(result, 'test')
        
        # 타이머 통계 확인
        timer_stats = self.performance_monitor.get_timer_stats()
        self.assertIn('test_operation', timer_stats)
        
        # 함수 통계 확인
        function_stats = self.performance_monitor.get_function_stats()
        self.assertIn('test_function', function_stats)
        
        # 시스템 통계 확인
        system_stats = self.performance_monitor.get_system_stats()
        self.assertIn('cpu', system_stats)
        self.assertIn('memory', system_stats)
        self.assertIn('disk', system_stats)
        
        # 성능 분석
        analysis = self.performance_monitor.analyze_performance()
        self.assertIn('system', analysis)
        self.assertIn('recommendations', analysis)
        
        # 통계 초기화
        self.performance_monitor.reset_stats()
        timer_stats = self.performance_monitor.get_timer_stats()
        self.assertEqual(len(timer_stats), 0)
        
        # 모니터링 비활성화
        self.performance_monitor.disable()
    
    def test_decorators_and_context_managers(self):
        """
        데코레이터 및 컨텍스트 매니저 테스트
        """
        # 함수 프로파일링 데코레이터
        @profile_function
        def test_function():
            time.sleep(0.1)
            return 'test'
        
        result = test_function()
        self.assertEqual(result, 'test')
        
        # 시간 측정 컨텍스트 매니저
        with measure_time('test_operation'):
            time.sleep(0.1)
        
        # 쿼리 프로파일링 컨텍스트 매니저
        with profile_query('SELECT * FROM test_table'):
            self.cursor.execute('SELECT * FROM test_table')
            self.cursor.fetchall()
        
        # 메모리 스냅샷 생성
        snapshot_index = take_memory_snapshot('test_snapshot')
        self.assertGreaterEqual(snapshot_index, -1)  # -1은 비활성화된 경우
        
        # 성능 분석
        analysis = analyze_performance()
        self.assertIsInstance(analysis, dict)
        
        # 성능 최적화
        optimization = optimize_performance()
        self.assertIsInstance(optimization, dict)

if __name__ == '__main__':
    unittest.main()