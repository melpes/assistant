# -*- coding: utf-8 -*-
"""
성능 모니터링 시스템

금융 거래 관리 시스템의 성능을 모니터링하고 최적화하는 도구입니다.
데이터베이스 쿼리 프로파일링, 메모리 사용량 추적, 실행 시간 측정 등의 기능을 제공합니다.
"""

import os
import sys
import time
import logging
import sqlite3
import psutil
import tracemalloc
import functools
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from contextlib import contextmanager

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.logging_system import get_logger
from src.config_manager import ConfigManager

# 로거 설정
logger = get_logger('performance')

class QueryProfiler:
    """
    SQL 쿼리 프로파일링 클래스
    
    데이터베이스 쿼리의 실행 시간과 성능을 측정합니다.
    """
    
    def __init__(self, db_path: str = None, config_manager: ConfigManager = None):
        """
        쿼리 프로파일러 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
            config_manager: 설정 관리자
        """
        self.config_manager = config_manager or ConfigManager()
        self.db_path = db_path or self.config_manager.get_config_value('system.database.path')
        self.query_stats = {}
        self.enabled = self.config_manager.get_config_value('system.performance.query_profiling_enabled', False)
        self.log_slow_queries = self.config_manager.get_config_value('system.performance.log_slow_queries', True)
        self.slow_query_threshold = self.config_manager.get_config_value('system.performance.slow_query_threshold_ms', 100)
        
        # 프로파일링 결과 저장 경로
        self.profile_dir = os.path.join(parent_dir, 'profiles')
        os.makedirs(self.profile_dir, exist_ok=True)
    
    def enable(self) -> None:
        """
        프로파일링 활성화
        """
        self.enabled = True
        logger.info("쿼리 프로파일링이 활성화되었습니다.")
    
    def disable(self) -> None:
        """
        프로파일링 비활성화
        """
        self.enabled = False
        logger.info("쿼리 프로파일링이 비활성화되었습니다.")
    
    @contextmanager
    def profile_query(self, query: str, params: tuple = None) -> None:
        """
        쿼리 프로파일링 컨텍스트 매니저
        
        Args:
            query: SQL 쿼리
            params: 쿼리 파라미터
        """
        if not self.enabled:
            yield
            return
        
        # 쿼리 정규화 (파라미터 제거)
        normalized_query = self._normalize_query(query)
        
        # 시작 시간 기록
        start_time = time.time()
        
        try:
            # 쿼리 실행
            yield
        finally:
            # 종료 시간 기록
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # 밀리초 단위
            
            # 쿼리 통계 업데이트
            if normalized_query not in self.query_stats:
                self.query_stats[normalized_query] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'avg_time': 0
                }
            
            stats = self.query_stats[normalized_query]
            stats['count'] += 1
            stats['total_time'] += execution_time
            stats['min_time'] = min(stats['min_time'], execution_time)
            stats['max_time'] = max(stats['max_time'], execution_time)
            stats['avg_time'] = stats['total_time'] / stats['count']
            
            # 느린 쿼리 로깅
            if self.log_slow_queries and execution_time > self.slow_query_threshold:
                logger.warning(f"느린 쿼리 감지: {execution_time:.2f}ms, 쿼리: {query}")
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        쿼리 실행 계획 분석
        
        Args:
            query: SQL 쿼리
            
        Returns:
            Dict[str, Any]: 실행 계획 분석 결과
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # EXPLAIN QUERY PLAN 실행
            cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            plan = cursor.fetchall()
            
            # 실행 계획 분석
            analysis = {
                'query': query,
                'plan': plan,
                'uses_index': any('USING INDEX' in str(row) for row in plan),
                'table_scan': any('SCAN TABLE' in str(row) for row in plan),
                'recommendations': []
            }
            
            # 테이블 스캔 감지
            if analysis['table_scan'] and not analysis['uses_index']:
                analysis['recommendations'].append("인덱스 추가를 고려하세요.")
            
            conn.close()
            return analysis
            
        except Exception as e:
            logger.error(f"쿼리 분석 중 오류 발생: {e}")
            return {'query': query, 'error': str(e)}
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        쿼리 통계 조회
        
        Returns:
            Dict[str, Dict[str, Any]]: 쿼리별 통계
        """
        return self.query_stats
    
    def get_slow_queries(self, threshold_ms: float = None) -> List[Tuple[str, Dict[str, Any]]]:
        """
        느린 쿼리 목록 조회
        
        Args:
            threshold_ms: 임계값 (밀리초)
            
        Returns:
            List[Tuple[str, Dict[str, Any]]]: 느린 쿼리 목록
        """
        threshold = threshold_ms or self.slow_query_threshold
        
        slow_queries = [
            (query, stats) for query, stats in self.query_stats.items()
            if stats['avg_time'] > threshold
        ]
        
        # 평균 실행 시간 기준으로 정렬
        slow_queries.sort(key=lambda x: x[1]['avg_time'], reverse=True)
        
        return slow_queries
    
    def reset_stats(self) -> None:
        """
        통계 초기화
        """
        self.query_stats = {}
        logger.info("쿼리 통계가 초기화되었습니다.")
    
    def save_stats(self, file_path: str = None) -> str:
        """
        통계 저장
        
        Args:
            file_path: 저장할 파일 경로
            
        Returns:
            str: 저장된 파일 경로
        """
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(self.profile_dir, f"query_stats_{timestamp}.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.query_stats, f, ensure_ascii=False, indent=2)
            
            logger.info(f"쿼리 통계가 저장되었습니다: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"쿼리 통계 저장 중 오류 발생: {e}")
            return ""
    
    def load_stats(self, file_path: str) -> bool:
        """
        통계 로드
        
        Args:
            file_path: 로드할 파일 경로
            
        Returns:
            bool: 로드 성공 여부
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.query_stats = json.load(f)
            
            logger.info(f"쿼리 통계가 로드되었습니다: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"쿼리 통계 로드 중 오류 발생: {e}")
            return False
    
    def optimize_database(self) -> bool:
        """
        데이터베이스 최적화
        
        Returns:
            bool: 최적화 성공 여부
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # VACUUM 실행
            cursor.execute("VACUUM")
            
            # ANALYZE 실행
            cursor.execute("ANALYZE")
            
            conn.commit()
            conn.close()
            
            logger.info("데이터베이스 최적화가 완료되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"데이터베이스 최적화 중 오류 발생: {e}")
            return False
    
    def _normalize_query(self, query: str) -> str:
        """
        쿼리 정규화
        
        Args:
            query: SQL 쿼리
            
        Returns:
            str: 정규화된 쿼리
        """
        # 공백 정규화
        query = ' '.join(query.split())
        
        # 대소문자 통일
        query = query.upper()
        
        return query

class MemoryProfiler:
    """
    메모리 프로파일링 클래스
    
    메모리 사용량을 추적하고 분석합니다.
    """
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        메모리 프로파일러 초기화
        
        Args:
            config_manager: 설정 관리자
        """
        self.config_manager = config_manager or ConfigManager()
        self.enabled = self.config_manager.get_config_value('system.performance.memory_profiling_enabled', False)
        self.snapshots = []
        
        # 프로파일링 결과 저장 경로
        self.profile_dir = os.path.join(parent_dir, 'profiles')
        os.makedirs(self.profile_dir, exist_ok=True)
    
    def enable(self) -> None:
        """
        프로파일링 활성화
        """
        if not self.enabled:
            tracemalloc.start()
            self.enabled = True
            logger.info("메모리 프로파일링이 활성화되었습니다.")
    
    def disable(self) -> None:
        """
        프로파일링 비활성화
        """
        if self.enabled:
            tracemalloc.stop()
            self.enabled = False
            logger.info("메모리 프로파일링이 비활성화되었습니다.")
    
    def take_snapshot(self, name: str = None) -> int:
        """
        메모리 스냅샷 생성
        
        Args:
            name: 스냅샷 이름
            
        Returns:
            int: 스냅샷 인덱스
        """
        if not self.enabled:
            logger.warning("메모리 프로파일링이 비활성화되어 있습니다.")
            return -1
        
        snapshot = tracemalloc.take_snapshot()
        timestamp = datetime.now()
        
        snapshot_info = {
            'index': len(self.snapshots),
            'name': name or f"snapshot_{len(self.snapshots)}",
            'timestamp': timestamp,
            'snapshot': snapshot
        }
        
        self.snapshots.append(snapshot_info)
        logger.info(f"메모리 스냅샷 생성: {snapshot_info['name']}")
        
        return snapshot_info['index']
    
    def compare_snapshots(self, start_index: int, end_index: int) -> List[Dict[str, Any]]:
        """
        스냅샷 비교
        
        Args:
            start_index: 시작 스냅샷 인덱스
            end_index: 종료 스냅샷 인덱스
            
        Returns:
            List[Dict[str, Any]]: 비교 결과
        """
        if not self.enabled:
            logger.warning("메모리 프로파일링이 비활성화되어 있습니다.")
            return []
        
        if start_index < 0 or start_index >= len(self.snapshots) or end_index < 0 or end_index >= len(self.snapshots):
            logger.error("유효하지 않은 스냅샷 인덱스입니다.")
            return []
        
        start_snapshot = self.snapshots[start_index]['snapshot']
        end_snapshot = self.snapshots[end_index]['snapshot']
        
        # 스냅샷 비교
        stats = end_snapshot.compare_to(start_snapshot, 'lineno')
        
        # 결과 변환
        result = []
        for stat in stats[:10]:  # 상위 10개만 반환
            result.append({
                'file': stat.traceback[0].filename,
                'line': stat.traceback[0].lineno,
                'size': stat.size,
                'size_diff': stat.size_diff,
                'count': stat.count,
                'count_diff': stat.count_diff
            })
        
        return result
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        현재 메모리 사용량 조회
        
        Returns:
            Dict[str, Any]: 메모리 사용량 정보
        """
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss,  # Resident Set Size
            'vms': memory_info.vms,  # Virtual Memory Size
            'rss_mb': memory_info.rss / (1024 * 1024),  # MB 단위
            'vms_mb': memory_info.vms / (1024 * 1024),  # MB 단위
            'percent': process.memory_percent()
        }
    
    def get_top_memory_objects(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        메모리 사용량이 많은 객체 조회
        
        Args:
            limit: 반환할 객체 수
            
        Returns:
            List[Dict[str, Any]]: 메모리 사용량이 많은 객체 목록
        """
        if not self.enabled or not self.snapshots:
            logger.warning("메모리 프로파일링이 비활성화되어 있거나 스냅샷이 없습니다.")
            return []
        
        # 최신 스냅샷 사용
        latest_snapshot = self.snapshots[-1]['snapshot']
        stats = latest_snapshot.statistics('lineno')
        
        # 결과 변환
        result = []
        for stat in stats[:limit]:
            result.append({
                'file': stat.traceback[0].filename,
                'line': stat.traceback[0].lineno,
                'size': stat.size,
                'size_mb': stat.size / (1024 * 1024),
                'count': stat.count
            })
        
        return result
    
    def save_snapshot(self, index: int, file_path: str = None) -> str:
        """
        스냅샷 저장
        
        Args:
            index: 스냅샷 인덱스
            file_path: 저장할 파일 경로
            
        Returns:
            str: 저장된 파일 경로
        """
        if not self.enabled or index < 0 or index >= len(self.snapshots):
            logger.error("유효하지 않은 스냅샷 인덱스입니다.")
            return ""
        
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            snapshot_name = self.snapshots[index]['name']
            file_path = os.path.join(self.profile_dir, f"memory_{snapshot_name}_{timestamp}.trace")
        
        try:
            self.snapshots[index]['snapshot'].dump(file_path)
            logger.info(f"메모리 스냅샷이 저장되었습니다: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"메모리 스냅샷 저장 중 오류 발생: {e}")
            return ""
    
    def clear_snapshots(self) -> None:
        """
        스냅샷 초기화
        """
        self.snapshots = []
        logger.info("메모리 스냅샷이 초기화되었습니다.")

class PerformanceMonitor:
    """
    성능 모니터링 클래스
    
    시스템 전반의 성능을 모니터링하고 최적화합니다.
    """
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        성능 모니터링 초기화
        
        Args:
            config_manager: 설정 관리자
        """
        self.config_manager = config_manager or ConfigManager()
        self.query_profiler = QueryProfiler(config_manager=self.config_manager)
        self.memory_profiler = MemoryProfiler(config_manager=self.config_manager)
        self.enabled = self.config_manager.get_config_value('system.performance.monitoring_enabled', False)
        self.timers = {}
        self.function_stats = {}
        
        # 프로파일링 결과 저장 경로
        self.profile_dir = os.path.join(parent_dir, 'profiles')
        os.makedirs(self.profile_dir, exist_ok=True)
    
    def enable(self) -> None:
        """
        모니터링 활성화
        """
        self.enabled = True
        
        # 쿼리 프로파일링 활성화
        if self.config_manager.get_config_value('system.performance.query_profiling_enabled', False):
            self.query_profiler.enable()
        
        # 메모리 프로파일링 활성화
        if self.config_manager.get_config_value('system.performance.memory_profiling_enabled', False):
            self.memory_profiler.enable()
        
        logger.info("성능 모니터링이 활성화되었습니다.")
    
    def disable(self) -> None:
        """
        모니터링 비활성화
        """
        self.enabled = False
        self.query_profiler.disable()
        self.memory_profiler.disable()
        logger.info("성능 모니터링이 비활성화되었습니다.")
    
    @contextmanager
    def measure_time(self, name: str) -> None:
        """
        실행 시간 측정 컨텍스트 매니저
        
        Args:
            name: 측정 이름
        """
        if not self.enabled:
            yield
            return
        
        # 시작 시간 기록
        start_time = time.time()
        
        try:
            # 코드 실행
            yield
        finally:
            # 종료 시간 기록
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # 밀리초 단위
            
            # 타이머 통계 업데이트
            if name not in self.timers:
                self.timers[name] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'avg_time': 0
                }
            
            stats = self.timers[name]
            stats['count'] += 1
            stats['total_time'] += execution_time
            stats['min_time'] = min(stats['min_time'], execution_time)
            stats['max_time'] = max(stats['max_time'], execution_time)
            stats['avg_time'] = stats['total_time'] / stats['count']
            
            logger.debug(f"시간 측정 [{name}]: {execution_time:.2f}ms")
    
    def profile_function(self, func: Callable = None, name: str = None) -> Callable:
        """
        함수 프로파일링 데코레이터
        
        Args:
            func: 프로파일링할 함수
            name: 프로파일링 이름
            
        Returns:
            Callable: 래핑된 함수
        """
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return f(*args, **kwargs)
                
                profile_name = name or f.__qualname__
                
                # 시작 시간 기록
                start_time = time.time()
                
                try:
                    # 함수 실행
                    result = f(*args, **kwargs)
                    return result
                finally:
                    # 종료 시간 기록
                    end_time = time.time()
                    execution_time = (end_time - start_time) * 1000  # 밀리초 단위
                    
                    # 함수 통계 업데이트
                    if profile_name not in self.function_stats:
                        self.function_stats[profile_name] = {
                            'count': 0,
                            'total_time': 0,
                            'min_time': float('inf'),
                            'max_time': 0,
                            'avg_time': 0
                        }
                    
                    stats = self.function_stats[profile_name]
                    stats['count'] += 1
                    stats['total_time'] += execution_time
                    stats['min_time'] = min(stats['min_time'], execution_time)
                    stats['max_time'] = max(stats['max_time'], execution_time)
                    stats['avg_time'] = stats['total_time'] / stats['count']
                    
                    logger.debug(f"함수 프로파일링 [{profile_name}]: {execution_time:.2f}ms")
            
            return wrapper
        
        if func is None:
            return decorator
        return decorator(func)
    
    def get_timer_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        타이머 통계 조회
        
        Returns:
            Dict[str, Dict[str, Any]]: 타이머별 통계
        """
        return self.timers
    
    def get_function_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        함수 통계 조회
        
        Returns:
            Dict[str, Dict[str, Any]]: 함수별 통계
        """
        return self.function_stats
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        시스템 통계 조회
        
        Returns:
            Dict[str, Any]: 시스템 통계
        """
        # CPU 사용량
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # 메모리 사용량
        memory = self.memory_profiler.get_memory_usage()
        
        # 디스크 사용량
        disk = psutil.disk_usage(parent_dir)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count()
            },
            'memory': memory,
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
        }
    
    def reset_stats(self) -> None:
        """
        통계 초기화
        """
        self.timers = {}
        self.function_stats = {}
        self.query_profiler.reset_stats()
        self.memory_profiler.clear_snapshots()
        logger.info("성능 통계가 초기화되었습니다.")
    
    def save_stats(self, file_path: str = None) -> str:
        """
        통계 저장
        
        Args:
            file_path: 저장할 파일 경로
            
        Returns:
            str: 저장된 파일 경로
        """
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(self.profile_dir, f"performance_stats_{timestamp}.json")
        
        try:
            # 통계 데이터 수집
            stats = {
                'timestamp': datetime.now().isoformat(),
                'timers': self.timers,
                'functions': self.function_stats,
                'queries': self.query_profiler.get_stats(),
                'system': self.get_system_stats()
            }
            
            # JSON 파일로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            logger.info(f"성능 통계가 저장되었습니다: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"성능 통계 저장 중 오류 발생: {e}")
            return ""
    
    def load_stats(self, file_path: str) -> bool:
        """
        통계 로드
        
        Args:
            file_path: 로드할 파일 경로
            
        Returns:
            bool: 로드 성공 여부
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            # 통계 데이터 복원
            if 'timers' in stats:
                self.timers = stats['timers']
            
            if 'functions' in stats:
                self.function_stats = stats['functions']
            
            # 쿼리 통계 복원
            if 'queries' in stats:
                self.query_profiler.query_stats = stats['queries']
            
            logger.info(f"성능 통계가 로드되었습니다: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"성능 통계 로드 중 오류 발생: {e}")
            return False
    
    def analyze_performance(self) -> Dict[str, Any]:
        """
        성능 분석
        
        Returns:
            Dict[str, Any]: 성능 분석 결과
        """
        # 시스템 통계
        system_stats = self.get_system_stats()
        
        # 느린 쿼리
        slow_queries = self.query_profiler.get_slow_queries()
        
        # 메모리 사용량이 많은 객체
        top_memory_objects = self.memory_profiler.get_top_memory_objects()
        
        # 실행 시간이 긴 함수
        slow_functions = sorted(
            [(name, stats) for name, stats in self.function_stats.items()],
            key=lambda x: x[1]['avg_time'],
            reverse=True
        )[:10]
        
        # 분석 결과
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'system': system_stats,
            'slow_queries': slow_queries,
            'top_memory_objects': top_memory_objects,
            'slow_functions': slow_functions,
            'recommendations': []
        }
        
        # 권장사항 생성
        if system_stats['memory']['percent'] > 80:
            analysis['recommendations'].append("메모리 사용량이 높습니다. 메모리 누수를 확인하세요.")
        
        if system_stats['disk']['percent'] > 80:
            analysis['recommendations'].append("디스크 공간이 부족합니다. 불필요한 파일을 정리하세요.")
        
        if slow_queries:
            analysis['recommendations'].append("느린 쿼리가 있습니다. 인덱스 추가를 고려하세요.")
        
        return analysis
    
    def optimize_performance(self) -> Dict[str, bool]:
        """
        성능 최적화
        
        Returns:
            Dict[str, bool]: 최적화 결과
        """
        results = {}
        
        # 데이터베이스 최적화
        results['database'] = self.query_profiler.optimize_database()
        
        # 캐시 정리
        results['cache'] = self._clear_cache()
        
        return results
    
    def _clear_cache(self) -> bool:
        """
        캐시 정리
        
        Returns:
            bool: 정리 성공 여부
        """
        try:
            # 캐시 디렉토리 경로
            cache_dir = os.path.join(parent_dir, 'cache')
            
            # 캐시 디렉토리가 있으면 정리
            if os.path.exists(cache_dir):
                for file in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            
            logger.info("캐시가 정리되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"캐시 정리 중 오류 발생: {e}")
            return False

# 전역 성능 모니터링 인스턴스
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """
    성능 모니터링 인스턴스 가져오기
    
    Returns:
        PerformanceMonitor: 성능 모니터링 인스턴스
    """
    global _performance_monitor
    
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    
    return _performance_monitor

def profile_function(func: Callable = None, name: str = None) -> Callable:
    """
    함수 프로파일링 데코레이터
    
    Args:
        func: 프로파일링할 함수
        name: 프로파일링 이름
        
    Returns:
        Callable: 래핑된 함수
    """
    monitor = get_performance_monitor()
    return monitor.profile_function(func, name)

@contextmanager
def measure_time(name: str) -> None:
    """
    실행 시간 측정 컨텍스트 매니저
    
    Args:
        name: 측정 이름
    """
    monitor = get_performance_monitor()
    with monitor.measure_time(name):
        yield

@contextmanager
def profile_query(query: str, params: tuple = None) -> None:
    """
    쿼리 프로파일링 컨텍스트 매니저
    
    Args:
        query: SQL 쿼리
        params: 쿼리 파라미터
    """
    monitor = get_performance_monitor()
    with monitor.query_profiler.profile_query(query, params):
        yield

def take_memory_snapshot(name: str = None) -> int:
    """
    메모리 스냅샷 생성
    
    Args:
        name: 스냅샷 이름
        
    Returns:
        int: 스냅샷 인덱스
    """
    monitor = get_performance_monitor()
    return monitor.memory_profiler.take_snapshot(name)

def analyze_performance() -> Dict[str, Any]:
    """
    성능 분석
    
    Returns:
        Dict[str, Any]: 성능 분석 결과
    """
    monitor = get_performance_monitor()
    return monitor.analyze_performance()

def optimize_performance() -> Dict[str, bool]:
    """
    성능 최적화
    
    Returns:
        Dict[str, bool]: 최적화 결과
    """
    monitor = get_performance_monitor()
    return monitor.optimize_performance()

def save_performance_stats(file_path: str = None) -> str:
    """
    성능 통계 저장
    
    Args:
        file_path: 저장할 파일 경로
        
    Returns:
        str: 저장된 파일 경로
    """
    monitor = get_performance_monitor()
    return monitor.save_stats(file_path)

def enable_monitoring() -> None:
    """
    모니터링 활성화
    """
    monitor = get_performance_monitor()
    monitor.enable()

def disable_monitoring() -> None:
    """
    모니터링 비활성화
    """
    monitor = get_performance_monitor()
    monitor.disable()