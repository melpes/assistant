"""
캘린더 서비스 성능 테스트

성능 요구사항 검증을 위한 전용 테스트 모듈입니다.
- 요구사항 5.1: 일정 목록 조회 5초 이내
- 요구사항 5.2: 일정 생성/수정/삭제 3초 이내
"""
import pytest
import time
import datetime
import statistics
from datetime import timezone, timedelta
from typing import List, Dict, Any

from src.calendar.service import CalendarService
from src.calendar.factory import CalendarServiceFactory
from src.calendar.models import CalendarEvent


@pytest.mark.integration
@pytest.mark.performance
class TestCalendarPerformance:
    """캘린더 서비스 성능 테스트"""
    
    @pytest.fixture(scope="class")
    def calendar_service(self) -> CalendarService:
        """실제 캘린더 서비스 인스턴스 생성"""
        try:
            factory = CalendarServiceFactory()
            return factory.create_service()
        except Exception as e:
            pytest.skip(f"Google Calendar API 인증 실패: {e}")
    
    def measure_performance(self, func, *args, **kwargs) -> Dict[str, Any]:
        """성능 측정 헬퍼 함수"""
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        return {
            'result': result,
            'elapsed': elapsed,
            'timestamp': datetime.datetime.now()
        }
    
    def test_list_events_performance_single(self, calendar_service):
        """단일 이벤트 조회 성능 테스트"""
        now = datetime.datetime.now(timezone.utc)
        start_time = now.isoformat()
        end_time = (now + timedelta(days=7)).isoformat()
        
        perf = self.measure_performance(
            calendar_service.get_events_for_period,
            start_time, end_time
        )
        
        # 성능 요구사항 검증 (5초 이내)
        assert perf['elapsed'] < 5.0, f"조회 시간 초과: {perf['elapsed']:.2f}초"
        
        events = perf['result']
        print(f"단일 조회: {len(events)}개 이벤트, {perf['elapsed']:.2f}초")
        
        return perf['elapsed']
    
    def test_list_events_performance_multiple(self, calendar_service):
        """다중 이벤트 조회 성능 테스트"""
        now = datetime.datetime.now(timezone.utc)
        
        # 5번 연속 조회
        times = []
        for i in range(5):
            start_time = (now + timedelta(days=i)).isoformat()
            end_time = (now + timedelta(days=i+1)).isoformat()
            
            perf = self.measure_performance(
                calendar_service.get_events_for_period,
                start_time, end_time
            )
            
            times.append(perf['elapsed'])
            events = perf['result']
            print(f"조회 {i+1}: {len(events)}개 이벤트, {perf['elapsed']:.2f}초")
            
            # 각 조회는 5초 이내
            assert perf['elapsed'] < 5.0, f"조회 {i+1} 시간 초과: {perf['elapsed']:.2f}초"
            
            # API 호출 간격
            time.sleep(0.5)
        
        # 통계 계산
        avg_time = statistics.mean(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"다중 조회 통계: 평균 {avg_time:.2f}초, 최대 {max_time:.2f}초, 최소 {min_time:.2f}초")
        
        # 평균 시간도 5초 이내여야 함
        assert avg_time < 5.0, f"평균 조회 시간 초과: {avg_time:.2f}초"
        
        return times
    
    def test_create_event_performance_single(self, calendar_service):
        """단일 이벤트 생성 성능 테스트"""
        now = datetime.datetime.now(timezone.utc)
        test_event = CalendarEvent(
            summary="성능 테스트 이벤트",
            description="성능 테스트로 생성된 이벤트입니다.",
            start_time=(now + timedelta(hours=1)).isoformat(),
            end_time=(now + timedelta(hours=2)).isoformat()
        )
        
        perf = self.measure_performance(
            calendar_service.create_new_event,
            test_event
        )
        
        # 성능 요구사항 검증 (3초 이내)
        assert perf['elapsed'] < 3.0, f"생성 시간 초과: {perf['elapsed']:.2f}초"
        
        created_event = perf['result']
        print(f"단일 생성: {created_event.summary}, {perf['elapsed']:.2f}초")
        
        # 정리
        try:
            calendar_service.provider.delete_event(created_event.id)
        except:
            print(f"정리 실패: 이벤트 {created_event.id} 수동 삭제 필요")
        
        return perf['elapsed']
    
    def test_create_event_performance_multiple(self, calendar_service):
        """다중 이벤트 생성 성능 테스트"""
        now = datetime.datetime.now(timezone.utc)
        created_events = []
        times = []
        
        try:
            # 3개 이벤트 연속 생성
            for i in range(3):
                test_event = CalendarEvent(
                    summary=f"성능 테스트 이벤트 {i+1}",
                    description=f"성능 테스트로 생성된 이벤트 #{i+1}",
                    start_time=(now + timedelta(hours=i+1)).isoformat(),
                    end_time=(now + timedelta(hours=i+2)).isoformat()
                )
                
                perf = self.measure_performance(
                    calendar_service.create_new_event,
                    test_event
                )
                
                times.append(perf['elapsed'])
                created_events.append(perf['result'])
                
                print(f"생성 {i+1}: {perf['result'].summary}, {perf['elapsed']:.2f}초")
                
                # 각 생성은 3초 이내
                assert perf['elapsed'] < 3.0, f"생성 {i+1} 시간 초과: {perf['elapsed']:.2f}초"
                
                # API 호출 간격
                time.sleep(0.5)
            
            # 통계 계산
            avg_time = statistics.mean(times)
            max_time = max(times)
            min_time = min(times)
            
            print(f"다중 생성 통계: 평균 {avg_time:.2f}초, 최대 {max_time:.2f}초, 최소 {min_time:.2f}초")
            
            # 평균 시간도 3초 이내여야 함
            assert avg_time < 3.0, f"평균 생성 시간 초과: {avg_time:.2f}초"
            
        finally:
            # 정리
            for event in created_events:
                try:
                    calendar_service.provider.delete_event(event.id)
                except:
                    print(f"정리 실패: 이벤트 {event.id} 수동 삭제 필요")
        
        return times
    
    def test_update_event_performance(self, calendar_service):
        """이벤트 수정 성능 테스트"""
        now = datetime.datetime.now(timezone.utc)
        
        # 테스트 이벤트 생성
        test_event = CalendarEvent(
            summary="수정 성능 테스트 이벤트",
            description="수정 성능 테스트용 이벤트",
            start_time=(now + timedelta(hours=1)).isoformat(),
            end_time=(now + timedelta(hours=2)).isoformat()
        )
        
        created_event = calendar_service.create_new_event(test_event)
        
        try:
            # 이벤트 수정
            updated_event_data = CalendarEvent(
                id=created_event.id,
                summary="수정된 성능 테스트 이벤트",
                description="수정된 설명입니다.",
                location="수정된 장소",
                start_time=created_event.start_time,
                end_time=created_event.end_time
            )
            
            perf = self.measure_performance(
                calendar_service.provider.update_event,
                created_event.id, updated_event_data
            )
            
            # 성능 요구사항 검증 (3초 이내)
            assert perf['elapsed'] < 3.0, f"수정 시간 초과: {perf['elapsed']:.2f}초"
            
            updated_event = perf['result']
            print(f"이벤트 수정: {updated_event.summary}, {perf['elapsed']:.2f}초")
            
            return perf['elapsed']
            
        finally:
            # 정리
            try:
                calendar_service.provider.delete_event(created_event.id)
            except:
                print(f"정리 실패: 이벤트 {created_event.id} 수동 삭제 필요")
    
    def test_delete_event_performance(self, calendar_service):
        """이벤트 삭제 성능 테스트"""
        now = datetime.datetime.now(timezone.utc)
        
        # 테스트 이벤트 생성
        test_event = CalendarEvent(
            summary="삭제 성능 테스트 이벤트",
            description="삭제 성능 테스트용 이벤트",
            start_time=(now + timedelta(hours=1)).isoformat(),
            end_time=(now + timedelta(hours=2)).isoformat()
        )
        
        created_event = calendar_service.create_new_event(test_event)
        
        # 이벤트 삭제
        perf = self.measure_performance(
            calendar_service.provider.delete_event,
            created_event.id
        )
        
        # 성능 요구사항 검증 (3초 이내)
        assert perf['elapsed'] < 3.0, f"삭제 시간 초과: {perf['elapsed']:.2f}초"
        
        delete_result = perf['result']
        assert delete_result is True, "삭제 실패"
        
        print(f"이벤트 삭제: {perf['elapsed']:.2f}초")
        
        return perf['elapsed']
    
    def test_large_time_range_performance(self, calendar_service):
        """큰 시간 범위 조회 성능 테스트"""
        now = datetime.datetime.now(timezone.utc)
        
        # 다양한 시간 범위 테스트
        ranges = [
            (7, "1주일"),
            (30, "1개월"),
            (90, "3개월"),
            (365, "1년")
        ]
        
        for days, description in ranges:
            start_time = (now - timedelta(days=days//2)).isoformat()
            end_time = (now + timedelta(days=days//2)).isoformat()
            
            perf = self.measure_performance(
                calendar_service.get_events_for_period,
                start_time, end_time
            )
            
            events = perf['result']
            print(f"{description} 범위 조회: {len(events)}개 이벤트, {perf['elapsed']:.2f}초")
            
            # 큰 범위여도 5초 이내
            assert perf['elapsed'] < 5.0, f"{description} 조회 시간 초과: {perf['elapsed']:.2f}초"
            
            # API 호출 간격
            time.sleep(1)
    
    def test_concurrent_performance(self, calendar_service):
        """동시 작업 성능 테스트"""
        import threading
        import queue
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def concurrent_list_events(thread_id):
            try:
                now = datetime.datetime.now(timezone.utc)
                start_time = (now + timedelta(days=thread_id)).isoformat()
                end_time = (now + timedelta(days=thread_id + 1)).isoformat()
                
                start = time.time()
                events = calendar_service.get_events_for_period(start_time, end_time)
                elapsed = time.time() - start
                
                results.put((thread_id, len(events), elapsed))
                
            except Exception as e:
                errors.put((thread_id, str(e)))
        
        # 3개 스레드로 동시 조회
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_list_events, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 결과 검증
        success_count = 0
        total_time = 0
        
        while not results.empty():
            thread_id, event_count, elapsed = results.get()
            success_count += 1
            total_time += elapsed
            
            print(f"동시 조회 {thread_id}: {event_count}개 이벤트, {elapsed:.2f}초")
            
            # 각 조회는 5초 이내
            assert elapsed < 5.0, f"동시 조회 {thread_id} 시간 초과: {elapsed:.2f}초"
        
        # 에러 확인
        error_count = 0
        while not errors.empty():
            thread_id, error = errors.get()
            print(f"동시 조회 {thread_id} 실패: {error}")
            error_count += 1
        
        # 최소 하나는 성공해야 함
        assert success_count > 0, "모든 동시 작업이 실패했습니다"
        
        avg_time = total_time / success_count if success_count > 0 else 0
        print(f"동시 작업 성능: {success_count}개 성공, 평균 {avg_time:.2f}초")
        
        return success_count, error_count, avg_time


@pytest.mark.integration
@pytest.mark.performance
class TestPerformanceBenchmark:
    """성능 벤치마크 테스트"""
    
    @pytest.fixture(scope="class")
    def calendar_service(self) -> CalendarService:
        """실제 캘린더 서비스 인스턴스 생성"""
        try:
            factory = CalendarServiceFactory()
            return factory.create_service()
        except Exception as e:
            pytest.skip(f"Google Calendar API 인증 실패: {e}")
    
    def test_performance_benchmark(self, calendar_service):
        """전체 성능 벤치마크"""
        print("\n" + "="*60)
        print("캘린더 서비스 성능 벤치마크")
        print("="*60)
        
        benchmark_results = {}
        
        # 1. 조회 성능
        print("\n1. 이벤트 조회 성능 테스트")
        now = datetime.datetime.now(timezone.utc)
        start_time = now.isoformat()
        end_time = (now + timedelta(days=7)).isoformat()
        
        start = time.time()
        events = calendar_service.get_events_for_period(start_time, end_time)
        list_time = time.time() - start
        
        benchmark_results['list_events'] = {
            'time': list_time,
            'count': len(events),
            'requirement': 5.0,
            'passed': list_time < 5.0
        }
        
        print(f"   조회 시간: {list_time:.2f}초 (요구사항: 5초 이내)")
        print(f"   조회 이벤트 수: {len(events)}개")
        print(f"   결과: {'✅ 통과' if list_time < 5.0 else '❌ 실패'}")
        
        # 2. 생성 성능
        print("\n2. 이벤트 생성 성능 테스트")
        test_event = CalendarEvent(
            summary="벤치마크 테스트 이벤트",
            description="성능 벤치마크 테스트용 이벤트",
            start_time=(now + timedelta(hours=1)).isoformat(),
            end_time=(now + timedelta(hours=2)).isoformat()
        )
        
        start = time.time()
        created_event = calendar_service.create_new_event(test_event)
        create_time = time.time() - start
        
        benchmark_results['create_event'] = {
            'time': create_time,
            'requirement': 3.0,
            'passed': create_time < 3.0
        }
        
        print(f"   생성 시간: {create_time:.2f}초 (요구사항: 3초 이내)")
        print(f"   결과: {'✅ 통과' if create_time < 3.0 else '❌ 실패'}")
        
        # 3. 수정 성능
        print("\n3. 이벤트 수정 성능 테스트")
        updated_event_data = CalendarEvent(
            id=created_event.id,
            summary="수정된 벤치마크 테스트 이벤트",
            description="수정된 설명",
            start_time=created_event.start_time,
            end_time=created_event.end_time
        )
        
        start = time.time()
        updated_event = calendar_service.provider.update_event(created_event.id, updated_event_data)
        update_time = time.time() - start
        
        benchmark_results['update_event'] = {
            'time': update_time,
            'requirement': 3.0,
            'passed': update_time < 3.0
        }
        
        print(f"   수정 시간: {update_time:.2f}초 (요구사항: 3초 이내)")
        print(f"   결과: {'✅ 통과' if update_time < 3.0 else '❌ 실패'}")
        
        # 4. 삭제 성능
        print("\n4. 이벤트 삭제 성능 테스트")
        start = time.time()
        delete_result = calendar_service.provider.delete_event(created_event.id)
        delete_time = time.time() - start
        
        benchmark_results['delete_event'] = {
            'time': delete_time,
            'requirement': 3.0,
            'passed': delete_time < 3.0 and delete_result
        }
        
        print(f"   삭제 시간: {delete_time:.2f}초 (요구사항: 3초 이내)")
        print(f"   결과: {'✅ 통과' if delete_time < 3.0 and delete_result else '❌ 실패'}")
        
        # 전체 결과 요약
        print("\n" + "="*60)
        print("성능 벤치마크 결과 요약")
        print("="*60)
        
        total_passed = sum(1 for result in benchmark_results.values() if result['passed'])
        total_tests = len(benchmark_results)
        
        for operation, result in benchmark_results.items():
            status = "✅ 통과" if result['passed'] else "❌ 실패"
            print(f"{operation:15}: {result['time']:6.2f}초 / {result['requirement']:4.1f}초 {status}")
        
        print(f"\n전체 결과: {total_passed}/{total_tests} 통과 ({total_passed/total_tests*100:.1f}%)")
        
        # 모든 테스트가 통과해야 함
        assert total_passed == total_tests, f"성능 요구사항 미달: {total_passed}/{total_tests} 통과"
        
        return benchmark_results


if __name__ == "__main__":
    # 개별 실행을 위한 코드
    pytest.main([__file__, "-v", "-s", "-m", "performance"])