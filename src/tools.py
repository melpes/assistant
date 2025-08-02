# src/tools.py
import datetime
import json
import os
from typing import Optional, Union

# tavily 모듈이 설치되어 있지 않은 경우를 위한 임시 처리
try:
    from tavily import TavilyClient
except ImportError:
    print("경고: tavily 모듈을 찾을 수 없습니다. web_search 함수는 사용할 수 없습니다.")
    TavilyClient = None

# config.py는 supervisor, db_agent 등 다른 파일에서 필요할 수 있으므로 유지합니다.
# 하지만 이 파일 자체는 TAVILY_API_KEY만 직접 사용합니다.
from src.config import TAVILY_API_KEY
from src.calendar.factory import CalendarServiceFactory

# 캘린더 서비스 인스턴스 생성 (모듈 레벨에서 재사용)
_calendar_service = CalendarServiceFactory.create_service()


def web_search(query: str) -> str:
    """주어진 쿼리에 대해 웹 검색을 수행하고 검색된 내용을 요약하여 반환합니다."""
    print(f"Tool 'web_search' 실행: {query}")
    if TavilyClient is None:
        return "tavily 모듈이 설치되어 있지 않아 웹 검색을 수행할 수 없습니다."
    
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
        # qna_search는 질문에 대한 직접적인 답변을 찾아주므로 더 유용합니다.
        response = tavily.qna_search(query=query, search_depth="advanced")
        return response
    except Exception as e:
        return f"웹 검색 중 오류 발생: {e}"


def list_calendar_events(start_time: str, end_time: str) -> str:
    """지정된 기간의 구글 캘린더 일정을 조회합니다. 시간은 'YYYY-MM-DDTHH:MM:SS' 형식이어야 합니다."""
    print(f"Tool 'list_calendar_events' 실행: {start_time} ~ {end_time}")
    try:
        # 새로운 캘린더 서비스를 사용하여 일정 조회
        events = _calendar_service.get_events_for_period(start_time, end_time)
        
        if not events:
            return "해당 기간에 예정된 일정이 없습니다."

        event_list = []
        for event in events:
            event_list.append(f"- 제목: {event['제목']}, 시간: {event['시간']}, ID: {event['id']}")
        return "\n".join(event_list)
    except Exception as e:
        return f"캘린더 일정 조회 중 오류 발생: {e}"


def create_google_calendar_event(summary: str, start_time: str, end_time: str, location: Optional[str] = None, description: Optional[str] = None) -> str:
    """
    구글 캘린더에 새 일정을 생성합니다.

    Args:
        summary (str): 일정의 제목.
        start_time (str): 일정 시작 시간. 시간 지정 시 'YYYY-MM-DDTHH:MM:SS', 온종일 일정 시 'YYYY-MM-DD' 형식.
        end_time (str): 일정 종료 시간. 시간 지정 시 'YYYY-MM-DDTHH:MM:SS', 온종일 일정 시 'YYYY-MM-DD' 형식.
        location (Optional[str]): 일정 장소.
        description (Optional[str]): 일정 상세 설명.
    """
    print(f"Tool 'create_google_calendar_event' 실행: {summary}")
    try:
        # 'T' 포함 여부로 온종일/시간 지정 일정 구분
        all_day = 'T' not in start_time
        
        # 새로운 캘린더 서비스를 사용하여 일정 생성
        created_event = _calendar_service.create_new_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            location=location,
            description=description,
            all_day=all_day
        )
        
        return f"구글 캘린더에 '{summary}' 일정을 성공적으로 추가했습니다."
    except Exception as e:
        return f"캘린더 일정 생성 중 오류 발생: {e}"

# 추가 캘린더 함수들
def update_google_calendar_event(event_id: str, summary: Optional[str] = None, start_time: Optional[str] = None, 
                                end_time: Optional[str] = None, location: Optional[str] = None, 
                                description: Optional[str] = None) -> str:
    """
    구글 캘린더의 기존 일정을 수정합니다.
    
    Args:
        event_id (str): 수정할 일정의 ID.
        summary (Optional[str]): 일정의 새 제목.
        start_time (Optional[str]): 일정의 새 시작 시간.
        end_time (Optional[str]): 일정의 새 종료 시간.
        location (Optional[str]): 일정의 새 장소.
        description (Optional[str]): 일정의 새 상세 설명.
    """
    print(f"Tool 'update_google_calendar_event' 실행: ID={event_id}")
    try:
        # 'T' 포함 여부로 온종일/시간 지정 일정 구분 (start_time이 제공된 경우에만)
        all_day = None
        if start_time is not None:
            all_day = 'T' not in start_time
        
        # 새로운 캘린더 서비스를 사용하여 일정 수정
        updated_event = _calendar_service.update_event(
            event_id=event_id,
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            location=location,
            description=description,
            all_day=all_day
        )
        
        return f"구글 캘린더의 '{updated_event['제목']}' 일정을 성공적으로 수정했습니다."
    except Exception as e:
        return f"캘린더 일정 수정 중 오류 발생: {e}"

def delete_google_calendar_event(event_id: str) -> str:
    """
    구글 캘린더의 일정을 삭제합니다.
    
    Args:
        event_id (str): 삭제할 일정의 ID.
    """
    print(f"Tool 'delete_google_calendar_event' 실행: ID={event_id}")
    try:
        # 새로운 캘린더 서비스를 사용하여 일정 삭제
        success = _calendar_service.delete_event(event_id)
        
        if success:
            return f"구글 캘린더에서 일정(ID: {event_id})을 성공적으로 삭제했습니다."
        else:
            return f"구글 캘린더에서 일정(ID: {event_id}) 삭제에 실패했습니다."
    except Exception as e:
        return f"캘린더 일정 삭제 중 오류 발생: {e}"


# 성능 최적화 관련 함수들
def create_calendar_events_batch(events_json: str) -> str:
    """
    여러 구글 캘린더 일정을 배치로 생성합니다.
    
    Args:
        events_json (str): 생성할 일정들의 JSON 문자열. 각 일정은 summary, start_time, end_time 등을 포함해야 합니다.
    """
    print(f"Tool 'create_calendar_events_batch' 실행")
    try:
        # JSON 문자열을 파싱
        events_data = json.loads(events_json)
        
        if not isinstance(events_data, list):
            return "이벤트 데이터는 리스트 형태여야 합니다."
        
        # 배치 생성 실행
        results = _calendar_service.create_events_batch(events_data, batch_size=10)
        
        # 결과 집계
        success_count = sum(1 for r in results if r is not None)
        total_count = len(results)
        
        return f"배치 일정 생성 완료: {success_count}/{total_count}개 성공"
        
    except json.JSONDecodeError as e:
        return f"JSON 파싱 오류: {e}"
    except Exception as e:
        return f"배치 일정 생성 중 오류 발생: {e}"


def delete_calendar_events_batch(event_ids_json: str) -> str:
    """
    여러 구글 캘린더 일정을 배치로 삭제합니다.
    
    Args:
        event_ids_json (str): 삭제할 일정 ID들의 JSON 배열 문자열.
    """
    print(f"Tool 'delete_calendar_events_batch' 실행")
    try:
        # JSON 문자열을 파싱
        event_ids = json.loads(event_ids_json)
        
        if not isinstance(event_ids, list):
            return "이벤트 ID 데이터는 리스트 형태여야 합니다."
        
        # 배치 삭제 실행
        results = _calendar_service.delete_events_batch(event_ids, batch_size=10)
        
        # 결과 집계
        success_count = sum(1 for r in results if r)
        total_count = len(results)
        
        return f"배치 일정 삭제 완료: {success_count}/{total_count}개 성공"
        
    except json.JSONDecodeError as e:
        return f"JSON 파싱 오류: {e}"
    except Exception as e:
        return f"배치 일정 삭제 중 오류 발생: {e}"


def get_calendar_performance_report() -> str:
    """
    캘린더 서비스의 성능 보고서를 생성합니다.
    """
    print(f"Tool 'get_calendar_performance_report' 실행")
    try:
        report = _calendar_service.get_performance_report()
        
        # 보고서를 문자열로 포맷팅
        result_lines = ["=== 캘린더 서비스 성능 보고서 ===\n"]
        
        if report['performance_stats']:
            result_lines.append("성능 통계:")
            for func_name, stats in report['performance_stats'].items():
                if 'avg_time' in stats:
                    result_lines.append(
                        f"- {func_name}: 평균 {stats['avg_time']:.4f}초, "
                        f"호출 {stats['call_count']}회, "
                        f"성공률 {stats['success_rate']:.1f}%"
                    )
        else:
            result_lines.append("성능 통계가 없습니다.")
        
        if report['warnings']:
            result_lines.append("\n⚠️ 성능 경고:")
            for warning in report['warnings']:
                result_lines.append(f"- {warning}")
        else:
            result_lines.append("\n✓ 성능 경고 없음")
        
        result_lines.append(f"\n보고서 생성 시간: {report['report_time']}")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"성능 보고서 생성 중 오류 발생: {e}"


def optimize_calendar_performance() -> str:
    """
    캘린더 서비스의 성능 최적화 제안을 생성합니다.
    """
    print(f"Tool 'optimize_calendar_performance' 실행")
    try:
        optimization = _calendar_service.optimize_performance()
        
        # 최적화 제안을 문자열로 포맷팅
        result_lines = ["=== 캘린더 서비스 성능 최적화 제안 ===\n"]
        
        if optimization['suggestions']:
            result_lines.append("최적화 제안:")
            for suggestion in optimization['suggestions']:
                result_lines.append(f"- {suggestion}")
        else:
            result_lines.append("✓ 추가 최적화가 필요하지 않습니다.")
        
        # 서비스 객체 풀 상태 추가
        if hasattr(_calendar_service.provider, 'get_service_pool_stats'):
            pool_stats = _calendar_service.provider.get_service_pool_stats()
            result_lines.append(f"\n서비스 객체 풀 상태:")
            result_lines.append(f"- 풀 크기: {pool_stats['pool_size']}/{pool_stats['max_size']}")
            result_lines.append(f"- 활성 서비스: {len(pool_stats['services'])}개")
        
        result_lines.append(f"\n최적화 분석 시간: {optimization['optimization_time']}")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"성능 최적화 분석 중 오류 발생: {e}"