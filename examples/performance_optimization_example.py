#!/usr/bin/env python3
"""
캘린더 서비스 성능 최적화 예제

이 스크립트는 캘린더 서비스의 성능 최적화 기능들을 시연합니다.
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.calendar.factory import CalendarServiceFactory
from src.calendar.utils import get_performance_stats, reset_performance_stats


def main():
    """성능 최적화 기능 시연"""
    print("=== 캘린더 서비스 성능 최적화 예제 ===\n")
    
    try:
        # 캘린더 서비스 생성
        print("1. 캘린더 서비스 초기화 중...")
        service = CalendarServiceFactory.create_service()
        print("   ✓ 캘린더 서비스가 성공적으로 초기화되었습니다.\n")
        
        # 성능 통계 초기화
        reset_performance_stats()
        
        # 단일 이벤트 조회 (성능 측정)
        print("2. 단일 이벤트 조회 성능 테스트...")
        start_date = datetime.now().replace(microsecond=0)
        end_date = start_date + timedelta(days=7)
        
        # RFC3339 형식으로 변환
        start_str = start_date.isoformat() + 'Z'
        end_str = end_date.isoformat() + 'Z'
        
        events = service.get_events_for_period(start_str, end_str)
        print(f"   ✓ {len(events)}개 이벤트 조회 완료\n")
        
        # 배치 이벤트 생성 테스트 (실제로는 생성하지 않고 시뮬레이션)
        print("3. 배치 처리 기능 시연...")
        sample_events = [
            {
                'summary': f'테스트 이벤트 {i}',
                'start_time': (datetime.now() + timedelta(days=i)).replace(microsecond=0).isoformat() + 'Z',
                'end_time': (datetime.now() + timedelta(days=i, hours=1)).replace(microsecond=0).isoformat() + 'Z',
                'description': f'배치 처리 테스트용 이벤트 {i}',
                'all_day': False
            }
            for i in range(1, 6)  # 5개 테스트 이벤트
        ]
        
        print(f"   - {len(sample_events)}개 이벤트 배치 생성 준비 완료")
        print("   - 실제 생성은 하지 않습니다 (테스트 목적)\n")
        
        # 성능 보고서 생성
        print("4. 성능 보고서 생성...")
        try:
            performance_report = service.get_performance_report()
            
            print("   성능 통계:")
            for func_name, stats in performance_report['performance_stats'].items():
                if 'avg_time' in stats:
                    print(f"   - {func_name}: 평균 {stats['avg_time']:.4f}초, "
                          f"호출 {stats['call_count']}회, "
                          f"성공률 {stats['success_rate']:.1f}%")
            
            if performance_report['warnings']:
                print("\n   ⚠️ 성능 경고:")
                for warning in performance_report['warnings']:
                    print(f"   - {warning}")
            else:
                print("\n   ✓ 성능 경고 없음")
        except Exception as e:
            print(f"   ❌ 성능 보고서 생성 실패: {e}")
        
        # 최적화 제안
        print("\n5. 성능 최적화 제안...")
        try:
            optimization = service.optimize_performance()
            
            if optimization['suggestions']:
                print("   최적화 제안:")
                for suggestion in optimization['suggestions']:
                    print(f"   - {suggestion}")
            else:
                print("   ✓ 추가 최적화가 필요하지 않습니다.")
        except Exception as e:
            print(f"   ❌ 최적화 제안 생성 실패: {e}")
        
        # 서비스 객체 풀 상태 확인
        print("\n6. 서비스 객체 풀 상태...")
        try:
            if hasattr(service.provider, 'get_service_pool_stats'):
                pool_stats = service.provider.get_service_pool_stats()
                print(f"   - 풀 크기: {pool_stats['pool_size']}/{pool_stats['max_size']}")
                print(f"   - 활성 서비스: {pool_stats['services']}")
            else:
                print("   - 서비스 객체 풀을 사용하지 않습니다.")
        except Exception as e:
            print(f"   ❌ 서비스 객체 풀 상태 확인 실패: {e}")
        
        print("\n=== 성능 최적화 예제 완료 ===")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()