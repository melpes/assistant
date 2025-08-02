# -*- coding: utf-8 -*-
"""
성능 모니터링 시스템 사용 예제

성능 모니터링 시스템의 기본 사용법을 보여주는 예제입니다.
"""

import os
import sys
import time
import sqlite3
import logging
from datetime import datetime

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.performance_monitor import (
    QueryProfiler, MemoryProfiler, PerformanceMonitor,
    profile_function, measure_time, profile_query, take_memory_snapshot,
    analyze_performance, optimize_performance, save_performance_stats,
    enable_monitoring, disable_monitoring
)
from src.logging_system import setup_logging, get_logger

# 로거 설정
setup_logging(verbose=True)
logger = get_logger('example')

def query_profiler_example():
    """
    쿼리 프로파일러 예제
    """
    print("=== 쿼리 프로파일러 예제 ===")
    
    # 임시 데이터베이스 생성
    db_path = os.path.join(parent_dir, 'data', 'example.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 테스트 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_table (
        id INTEGER PRIMARY KEY,
        name TEXT,
        value INTEGER
    )
    ''')
    
    # 테스트 데이터 삽입
    cursor.execute("DELETE FROM test_table")
    for i in range(1000):
        cursor.execute('INSERT INTO test_table (name, value) VALUES (?, ?)', (f'item_{i}', i))
    
    conn.commit()
    
    # 쿼리 프로파일러 초기화
    profiler = QueryProfiler(db_path)
    profiler.enable()
    
    # 쿼리 실행 및 프로파일링
    print("쿼리 실행 중...")
    
    with profiler.profile_query('SELECT * FROM test_table'):
        cursor.execute('SELECT * FROM test_table')
        cursor.fetchall()
    
    with profiler.profile_query('SELECT * FROM test_table WHERE value > 500'):
        cursor.execute('SELECT * FROM test_table WHERE value > 500')
        cursor.fetchall()
    
    with profiler.profile_query('SELECT * FROM test_table WHERE name LIKE ?', ('item_%',)):
        cursor.execute('SELECT * FROM test_table WHERE name LIKE ?', ('item_%',))
        cursor.fetchall()
    
    # 통계 확인
    stats = profiler.get_stats()
    print(f"\n쿼리 통계: {len(stats)}개의 쿼리 프로파일링됨")
    
    for query, query_stats in stats.items():
        print(f"쿼리: {query}")
        print(f"  실행 횟수: {query_stats['count']}")
        print(f"  평균 실행 시간: {query_stats['avg_time']:.2f}ms")
        print(f"  최소 실행 시간: {query_stats['min_time']:.2f}ms")
        print(f"  최대 실행 시간: {query_stats['max_time']:.2f}ms")
    
    # 느린 쿼리 확인
    slow_queries = profiler.get_slow_queries(threshold_ms=10)
    print(f"\n느린 쿼리: {len(slow_queries)}개 발견")
    
    for query, query_stats in slow_queries:
        print(f"쿼리: {query}")
        print(f"  평균 실행 시간: {query_stats['avg_time']:.2f}ms")
    
    # 쿼리 분석
    print("\n쿼리 분석:")
    analysis = profiler.analyze_query('SELECT * FROM test_table WHERE value > 500')
    
    print(f"쿼리: {analysis['query']}")
    print(f"인덱스 사용: {'예' if analysis['uses_index'] else '아니오'}")
    print(f"테이블 스캔: {'예' if analysis['table_scan'] else '아니오'}")
    
    if analysis['recommendations']:
        print("권장사항:")
        for rec in analysis['recommendations']:
            print(f"- {rec}")
    
    # 데이터베이스 최적화
    print("\n데이터베이스 최적화 중...")
    profiler.optimize_database()
    
    # 통계 저장
    stats_file = profiler.save_stats()
    print(f"쿼리 통계 저장됨: {stats_file}")
    
    # 연결 종료
    conn.close()
    
    # 프로파일러 비활성화
    profiler.disable()

def memory_profiler_example():
    """
    메모리 프로파일러 예제
    """
    print("\n=== 메모리 프로파일러 예제 ===")
    
    # 메모리 프로파일러 초기화
    profiler = MemoryProfiler()
    profiler.enable()
    
    # 첫 번째 스냅샷 생성
    print("첫 번째 메모리 스냅샷 생성 중...")
    snapshot1 = profiler.take_snapshot('initial')
    
    # 메모리 할당
    print("메모리 할당 중...")
    data = [i for i in range(1000000)]
    
    # 두 번째 스냅샷 생성
    print("두 번째 메모리 스냅샷 생성 중...")
    snapshot2 = profiler.take_snapshot('after_allocation')
    
    # 스냅샷 비교
    print("\n메모리 스냅샷 비교:")
    comparison = profiler.compare_snapshots(snapshot1, snapshot2)
    
    for i, stat in enumerate(comparison[:5], 1):
        print(f"{i}. 파일: {stat['file']}")
        print(f"   라인: {stat['line']}")
        print(f"   크기: {stat['size'] / 1024:.2f} KB")
        print(f"   크기 변화: {stat['size_diff'] / 1024:.2f} KB")
    
    # 메모리 사용량 확인
    memory_usage = profiler.get_memory_usage()
    print(f"\n현재 메모리 사용량:")
    print(f"RSS: {memory_usage['rss_mb']:.2f} MB")
    print(f"VMS: {memory_usage['vms_mb']:.2f} MB")
    print(f"사용률: {memory_usage['percent']:.2f}%")
    
    # 메모리 사용량이 많은 객체 확인
    print("\n메모리 사용량이 많은 객체:")
    top_objects = profiler.get_top_memory_objects(limit=5)
    
    for i, obj in enumerate(top_objects, 1):
        print(f"{i}. 파일: {obj['file']}")
        print(f"   라인: {obj['line']}")
        print(f"   크기: {obj['size_mb']:.2f} MB")
        print(f"   객체 수: {obj['count']}")
    
    # 스냅샷 저장
    snapshot_file = profiler.save_snapshot(snapshot2)
    if snapshot_file:
        print(f"\n메모리 스냅샷 저장됨: {snapshot_file}")
    
    # 스냅샷 초기화
    profiler.clear_snapshots()
    
    # 프로파일러 비활성화
    profiler.disable()

def performance_monitor_example():
    """
    성능 모니터 예제
    """
    print("\n=== 성능 모니터 예제 ===")
    
    # 성능 모니터 초기화
    monitor = PerformanceMonitor()
    monitor.enable()
    
    # 시간 측정
    print("시간 측정 중...")
    
    with monitor.measure_time('operation1'):
        time.sleep(0.1)
    
    with monitor.measure_time('operation2'):
        time.sleep(0.2)
    
    # 함수 프로파일링
    print("\n함수 프로파일링 중...")
    
    @monitor.profile_function
    def slow_function(iterations):
        result = 0
        for i in range(iterations):
            result += i
            time.sleep(0.001)
        return result
    
    slow_function(100)
    slow_function(200)
    
    # 타이머 통계 확인
    timer_stats = monitor.get_timer_stats()
    print("\n타이머 통계:")
    
    for name, stats in timer_stats.items():
        print(f"작업: {name}")
        print(f"  실행 횟수: {stats['count']}")
        print(f"  평균 실행 시간: {stats['avg_time']:.2f}ms")
        print(f"  최소 실행 시간: {stats['min_time']:.2f}ms")
        print(f"  최대 실행 시간: {stats['max_time']:.2f}ms")
    
    # 함수 통계 확인
    function_stats = monitor.get_function_stats()
    print("\n함수 통계:")
    
    for name, stats in function_stats.items():
        print(f"함수: {name}")
        print(f"  호출 횟수: {stats['count']}")
        print(f"  평균 실행 시간: {stats['avg_time']:.2f}ms")
        print(f"  최소 실행 시간: {stats['min_time']:.2f}ms")
        print(f"  최대 실행 시간: {stats['max_time']:.2f}ms")
    
    # 시스템 통계 확인
    system_stats = monitor.get_system_stats()
    print("\n시스템 통계:")
    print(f"CPU 사용률: {system_stats['cpu']['percent']:.2f}%")
    print(f"메모리 사용률: {system_stats['memory']['percent']:.2f}%")
    print(f"디스크 사용률: {system_stats['disk']['percent']:.2f}%")
    
    # 성능 분석
    print("\n성능 분석 중...")
    analysis = monitor.analyze_performance()
    
    if analysis['recommendations']:
        print("권장사항:")
        for rec in analysis['recommendations']:
            print(f"- {rec}")
    
    # 통계 저장
    stats_file = monitor.save_stats()
    print(f"\n성능 통계 저장됨: {stats_file}")
    
    # 모니터 비활성화
    monitor.disable()

def decorator_example():
    """
    데코레이터 및 컨텍스트 매니저 예제
    """
    print("\n=== 데코레이터 및 컨텍스트 매니저 예제 ===")
    
    # 모니터링 활성화
    enable_monitoring()
    
    # 함수 프로파일링 데코레이터
    @profile_function
    def example_function(n):
        result = 0
        for i in range(n):
            result += i
        return result
    
    # 시간 측정 컨텍스트 매니저
    with measure_time('example_operation'):
        example_function(1000000)
    
    # 임시 데이터베이스 생성
    db_path = os.path.join(parent_dir, 'data', 'example.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 쿼리 프로파일링 컨텍스트 매니저
    with profile_query('SELECT COUNT(*) FROM test_table'):
        cursor.execute('SELECT COUNT(*) FROM test_table')
        count = cursor.fetchone()[0]
        print(f"\n테이블 행 수: {count}")
    
    # 메모리 스냅샷 생성
    snapshot_index = take_memory_snapshot('example_snapshot')
    print(f"메모리 스냅샷 생성됨: 인덱스 {snapshot_index}")
    
    # 성능 분석
    analysis = analyze_performance()
    print("\n성능 분석 결과:")
    print(f"CPU 사용률: {analysis['system']['cpu']['percent']:.2f}%")
    print(f"메모리 사용률: {analysis['system']['memory']['percent']:.2f}%")
    
    # 성능 최적화
    optimization = optimize_performance()
    print("\n성능 최적화 결과:")
    for component, result in optimization.items():
        print(f"{component}: {'성공' if result else '실패'}")
    
    # 성능 통계 저장
    stats_file = save_performance_stats()
    print(f"\n성능 통계 저장됨: {stats_file}")
    
    # 연결 종료
    conn.close()
    
    # 모니터링 비활성화
    disable_monitoring()

def main():
    """
    메인 함수
    """
    # 예제 실행
    query_profiler_example()
    memory_profiler_example()
    performance_monitor_example()
    decorator_example()
    
    print("\n모든 예제가 완료되었습니다.")

if __name__ == '__main__':
    main()