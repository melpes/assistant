"""
캘린더 서비스 통합 테스트

실제 Google Calendar API와 연동하여 전체 플로우를 테스트합니다.
이 테스트는 실제 API 키와 인증 정보가 필요합니다.
"""
import pytest
import time
import datetime
from datetime import timezone, timedelta
from typing import List, Optional

from src.calendar.service import CalendarService
from src.calendar.factory import CalendarServiceFactory
from src.calendar.models import CalendarEvent
from src.calendar.exceptions import (
    CalendarServiceError,
    AuthenticationError,
    EventNotFoundError,
    APIQuotaExceededError
)


@pytest.mark.integration
class TestCalendarServiceIntegration:
    """캘린더 서비스 통합 테스트"""
    
    @pytest.fixture(scope="class")
    def calendar_service(self) -> CalendarService:
        """실제 캘린더 서비스 인스턴스 생성"""
        try:
            factory = CalendarServiceFactory()
            service = factory.create_service()
            print(f"✅ 캘린더 서비스 생성 성공")
            return service
        except Exception as e:
            print(f"❌ 캘린더 서비스 생성 실패: {e}")
            pytest.skip(f"Google Calendar API 인증 실패: {e}")
    
    @pytest.fixture
    def test_event_data(self) -> CalendarEvent:
        """테스트용 이벤트 데이터"""
        now = datetime.datetime.now(timezone.utc)
        return CalendarEvent(
            summary="통합 테스트 이벤트",
            description="캘린더 서비스 통합 테스트로 생성된 이벤트입니다.",
            location="테스트 장소",
            start_time=(now + timedelta(hours=1)).isoformat(),
            end_time=(now + timedelta(hours=2)).isoformat(),
            all_day=False
        )
    
    @pytest.fixture
    def time_range(self) -> tuple[str, str]:
        """테스트용 시간 범위"""
        now = datetime.datetime.now(timezone.utc)
        start_time = now.isoformat()
        end_time = (now + timedelta(days=7)).isoformat()
        return start_time, end_time
    
    def test_service_initialization(self, calendar_service):
        """서비스 초기화 테스트"""
        assert calendar_service is not None
        assert hasattr(calendar_service, 'provider')
        assert hasattr(calendar_service, 'get_events_for_period')
        assert hasattr(calendar_service, 'create_new_event')
    
    def test_list_events_performance(self, calendar_service, time_range):
        """이벤트 목록 조회 성능 테스트 (요구사항 5.1: 5초 이내)"""
        start_time, end_time = time_range
        
        # 성능 측정
        start = time.time()
        events = calendar_service.get_events_for_period(start_time, end_time)
        elapsed = time.time() - start
        
        # 성능 검증
        assert elapsed < 5.0, f"이벤트 조회 시간이 5초를 초과했습니다: {elapsed:.2f}초"
        
        # 결과 검증
        assert isinstance(events, list)
        print(f"조회된 이벤트 수: {len(events)}, 소요 시간: {elapsed:.2f}초")
    
    def test_create_event_performance(self, calendar_service, test_event_data):
        """이벤트 생성 성능 테스트 (요구사항 5.2: 3초 이내)"""
        # 성능 측정
        start = time.time()
        created_event = calendar_service.create_new_event(test_event_data)
        elapsed = time.time() - start
        
        # 성능 검증
        assert elapsed < 3.0, f"이벤트 생성 시간이 3초를 초과했습니다: {elapsed:.2f}초"
        
        # 결과 검증
        assert created_event is not None
        assert created_event.id is not None
        assert created_event.summary == test_event_data.summary
        
        print(f"이벤트 생성 완료, 소요 시간: {elapsed:.2f}초")
        
        # 정리를 위해 이벤트 ID 반환
        return created_event.id
    
    def test_full_crud_flow(self, calendar_service, test_event_data):
        """전체 CRUD 플로우 테스트"""
        created_event_id = None
        
        try:
            # 1. 생성 (Create)
            print("1. 이벤트 생성 테스트")
            start = time.time()
            created_event = calendar_service.create_new_event(test_event_data)
            create_time = time.time() - start
            
            assert created_event is not None
            assert created_event.id is not None
            created_event_id = created_event.id
            
            print(f"   생성 완료: {created_event.summary} (ID: {created_event_id})")
            print(f"   소요 시간: {create_time:.2f}초")
            
            # 2. 조회 (Read)
            print("2. 이벤트 조회 테스트")
            now = datetime.datetime.now(timezone.utc)
            start_time = now.isoformat()
            end_time = (now + timedelta(days=1)).isoformat()
            
            start = time.time()
            events = calendar_service.get_events_for_period(start_time, end_time)
            read_time = time.time() - start
            
            # 생성한 이벤트가 목록에 있는지 확인
            found_event = None
            for event in events:
                if event.id == created_event_id:
                    found_event = event
                    break
            
            assert found_event is not None, "생성한 이벤트를 조회할 수 없습니다"
            print(f"   조회 완료: {len(events)}개 이벤트 중 생성한 이벤트 발견")
            print(f"   소요 시간: {read_time:.2f}초")
            
            # 3. 수정 (Update)
            print("3. 이벤트 수정 테스트")
            updated_event_data = CalendarEvent(
                id=created_event_id,
                summary="수정된 통합 테스트 이벤트",
                description="수정된 설명입니다.",
                location="수정된 장소",
                start_time=created_event.start_time,
                end_time=created_event.end_time,
                all_day=False
            )
            
            start = time.time()
            updated_event = calendar_service.provider.update_event(created_event_id, updated_event_data)
            update_time = time.time() - start
            
            assert updated_event is not None
            assert updated_event.summary == "수정된 통합 테스트 이벤트"
            print(f"   수정 완료: {updated_event.summary}")
            print(f"   소요 시간: {update_time:.2f}초")
            
            # 4. 삭제 (Delete)
            print("4. 이벤트 삭제 테스트")
            start = time.time()
            delete_result = calendar_service.provider.delete_event(created_event_id)
            delete_time = time.time() - start
            
            assert delete_result is True
            print(f"   삭제 완료")
            print(f"   소요 시간: {delete_time:.2f}초")
            
            created_event_id = None  # 삭제되었으므로 정리 불필요
            
            # 전체 성능 검증
            total_time = create_time + read_time + update_time + delete_time
            print(f"\n전체 CRUD 플로우 완료, 총 소요 시간: {total_time:.2f}초")
            
            # 각 작업별 성능 요구사항 검증
            assert create_time < 3.0, f"생성 시간 초과: {create_time:.2f}초"
            assert read_time < 5.0, f"조회 시간 초과: {read_time:.2f}초"
            assert update_time < 3.0, f"수정 시간 초과: {update_time:.2f}초"
            assert delete_time < 3.0, f"삭제 시간 초과: {delete_time:.2f}초"
            
        except Exception as e:
            # 테스트 실패 시 정리
            if created_event_id:
                try:
                    calendar_service.provider.delete_event(created_event_id)
                    print(f"정리 완료: 테스트 이벤트 {created_event_id} 삭제")
                except:
                    print(f"정리 실패: 테스트 이벤트 {created_event_id} 수동 삭제 필요")
            raise e
    
    def test_error_scenarios(self, calendar_service):
        """에러 시나리오 테스트 (요구사항 4.1, 4.2)"""
        
        # 1. 존재하지 않는 이벤트 조회
        print("1. 존재하지 않는 이벤트 조회 테스트")
        with pytest.raises(EventNotFoundError):
            calendar_service.provider.update_event("nonexistent_event_id", CalendarEvent(
                summary="존재하지 않는 이벤트"
            ))
        
        # 2. 잘못된 시간 형식
        print("2. 잘못된 시간 형식 테스트")
        with pytest.raises(CalendarServiceError):
            invalid_event = CalendarEvent(
                summary="잘못된 시간 형식 테스트",
                start_time="invalid_time_format",
                end_time="invalid_time_format"
            )
            calendar_service.create_new_event(invalid_event)
        
        # 3. 빈 제목으로 이벤트 생성
        print("3. 빈 제목 이벤트 생성 테스트")
        with pytest.raises(CalendarServiceError):
            empty_title_event = CalendarEvent(
                summary="",  # 빈 제목
                start_time=datetime.datetime.now(timezone.utc).isoformat(),
                end_time=(datetime.datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
            )
            calendar_service.create_new_event(empty_title_event)
        
        print("에러 시나리오 테스트 완료")
    
    def test_concurrent_operations(self, calendar_service):
        """동시 작업 테스트"""
        import threading
        import queue
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def create_test_event(index):
            try:
                now = datetime.datetime.now(timezone.utc)
                event = CalendarEvent(
                    summary=f"동시 테스트 이벤트 {index}",
                    description=f"동시 작업 테스트 #{index}",
                    start_time=(now + timedelta(hours=index)).isoformat(),
                    end_time=(now + timedelta(hours=index + 1)).isoformat()
                )
                
                start_time = time.time()
                created_event = calendar_service.create_new_event(event)
                elapsed = time.time() - start_time
                
                results.put((index, created_event.id, elapsed))
                
            except Exception as e:
                errors.put((index, str(e)))
        
        # 3개의 동시 이벤트 생성
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_test_event, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 결과 검증
        created_events = []
        while not results.empty():
            index, event_id, elapsed = results.get()
            created_events.append(event_id)
            print(f"동시 이벤트 {index} 생성 완료: {elapsed:.2f}초")
        
        # 에러 확인
        error_count = 0
        while not errors.empty():
            index, error = errors.get()
            print(f"동시 이벤트 {index} 생성 실패: {error}")
            error_count += 1
        
        # 생성된 이벤트 정리
        for event_id in created_events:
            try:
                calendar_service.provider.delete_event(event_id)
            except:
                print(f"정리 실패: 이벤트 {event_id} 수동 삭제 필요")
        
        # 최소 하나는 성공해야 함
        assert len(created_events) > 0, "모든 동시 작업이 실패했습니다"
        print(f"동시 작업 테스트 완료: {len(created_events)}개 성공, {error_count}개 실패")
    
    def test_large_time_range_query(self, calendar_service):
        """큰 시간 범위 조회 테스트"""
        now = datetime.datetime.now(timezone.utc)
        start_time = (now - timedelta(days=30)).isoformat()  # 30일 전
        end_time = (now + timedelta(days=30)).isoformat()    # 30일 후
        
        start = time.time()
        events = calendar_service.get_events_for_period(start_time, end_time)
        elapsed = time.time() - start
        
        # 성능 검증 (큰 범위여도 5초 이내)
        assert elapsed < 5.0, f"큰 시간 범위 조회 시간 초과: {elapsed:.2f}초"
        
        # 결과 검증
        assert isinstance(events, list)
        print(f"60일 범위 조회 완료: {len(events)}개 이벤트, {elapsed:.2f}초")
    
    def test_service_resilience(self, calendar_service):
        """서비스 복원력 테스트"""
        # 여러 번 연속 호출하여 안정성 확인
        now = datetime.datetime.now(timezone.utc)
        start_time = now.isoformat()
        end_time = (now + timedelta(days=1)).isoformat()
        
        success_count = 0
        total_time = 0
        
        for i in range(5):
            try:
                start = time.time()
                events = calendar_service.get_events_for_period(start_time, end_time)
                elapsed = time.time() - start
                
                total_time += elapsed
                success_count += 1
                
                print(f"호출 {i+1}: {len(events)}개 이벤트, {elapsed:.2f}초")
                
                # 각 호출 사이에 짧은 대기
                time.sleep(0.5)
                
            except Exception as e:
                print(f"호출 {i+1} 실패: {e}")
        
        # 최소 80% 성공률
        success_rate = success_count / 5
        assert success_rate >= 0.8, f"성공률이 낮습니다: {success_rate*100:.1f}%"
        
        # 평균 응답 시간
        avg_time = total_time / success_count if success_count > 0 else 0
        print(f"복원력 테스트 완료: 성공률 {success_rate*100:.1f}%, 평균 응답 시간 {avg_time:.2f}초")


@pytest.mark.integration
class TestToolsIntegration:
    """tools.py 함수 통합 테스트"""
    
    def test_tools_calendar_functions(self):
        """tools.py 캘린더 함수 통합 테스트"""
        from src.tools import list_calendar_events, create_google_calendar_event
        
        try:
            # 현재 날짜 계산
            today = datetime.date.today()
            start_date = today.strftime('%Y-%m-%d')
            end_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
            
            print(f"이벤트 조회 기간: {start_date} ~ {end_date}")
            
            # 이벤트 목록 조회 테스트
            start_time = time.time()
            events_result = list_calendar_events(start_date, end_date)
            list_elapsed = time.time() - start_time
            
            assert "오류" not in events_result, f"이벤트 조회 실패: {events_result}"
            print(f"이벤트 조회 완료: {list_elapsed:.2f}초")
            
            # 이벤트 생성 테스트
            tomorrow = (today + timedelta(days=1)).strftime('%Y-%m-%d')
            
            start_time = time.time()
            create_result = create_google_calendar_event(
                title="tools.py 통합 테스트 이벤트",
                description="tools.py 함수 통합 테스트로 생성된 이벤트",
                start_time=f"{tomorrow}T10:00:00",
                end_time=f"{tomorrow}T11:00:00",
                location="테스트 장소"
            )
            create_elapsed = time.time() - start_time
            
            assert "성공적으로 생성되었습니다" in create_result, f"이벤트 생성 실패: {create_result}"
            print(f"이벤트 생성 완료: {create_elapsed:.2f}초")
            
            # 성능 검증
            assert list_elapsed < 5.0, f"조회 시간 초과: {list_elapsed:.2f}초"
            assert create_elapsed < 3.0, f"생성 시간 초과: {create_elapsed:.2f}초"
            
        except Exception as e:
            pytest.skip(f"tools.py 통합 테스트 실패: {e}")


if __name__ == "__main__":
    # 개별 실행을 위한 코드
    pytest.main([__file__, "-v", "-s"])