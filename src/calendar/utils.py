"""
캘린더 서비스 유틸리티 함수들

이 모듈은 캘린더 서비스에서 사용하는 유틸리티 함수들을 제공합니다.
"""
import time
import random
import functools
import logging
import threading
from collections import defaultdict, deque
from typing import Type, Callable, Any, List, Union, Optional, Dict
from datetime import datetime, timedelta

from .exceptions import (
    CalendarServiceError,
    NetworkError,
    APIQuotaExceededError
)

# 로깅 설정
logger = logging.getLogger(__name__)

# 성능 모니터링을 위한 전역 변수들
_performance_stats = defaultdict(list)
_performance_lock = threading.Lock()
_performance_history = defaultdict(lambda: deque(maxlen=100))  # 최근 100개 기록만 유지


def retry(
    max_tries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1,
    exceptions_to_retry: List[Type[Exception]] = None
) -> Callable:
    """
    네트워크 오류나 API 오류 발생 시 자동으로 재시도하는 데코레이터

    Args:
        max_tries: 최대 시도 횟수 (기본값: 3)
        delay: 초기 대기 시간(초) (기본값: 1.0)
        backoff_factor: 대기 시간 증가 계수 (기본값: 2.0)
        jitter: 무작위성 추가 계수 (기본값: 0.1)
        exceptions_to_retry: 재시도할 예외 클래스 목록 (기본값: NetworkError, APIQuotaExceededError)

    Returns:
        데코레이터 함수
    """
    if exceptions_to_retry is None:
        exceptions_to_retry = [NetworkError, APIQuotaExceededError]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tries = 0
            current_delay = delay
            last_exception = None

            while tries < max_tries:
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions_to_retry) as e:
                    tries += 1
                    last_exception = e

                    if tries >= max_tries:
                        break

                    # API 할당량 초과 시 더 긴 대기 시간 적용
                    if isinstance(e, APIQuotaExceededError):
                        wait_time = min(current_delay * 2, 60)  # 최대 60초
                    else:
                        wait_time = current_delay

                    # 무작위성 추가
                    if jitter > 0:
                        wait_time = wait_time * (1 + random.uniform(-jitter, jitter))

                    # 로그 메시지
                    logger.warning(
                        f"{func.__name__} 실행 중 오류 발생: {e}. "
                        f"{tries}/{max_tries}번째 시도, {wait_time:.2f}초 후 재시도합니다."
                    )

                    # 대기
                    time.sleep(wait_time)

                    # 다음 시도를 위한 대기 시간 증가
                    current_delay *= backoff_factor

            # 모든 재시도 실패 시 마지막 예외 발생
            if last_exception:
                logger.error(f"{func.__name__} 함수 {max_tries}회 시도 후 실패: {last_exception}")
                raise last_exception
            return None

        return wrapper

    return decorator


def format_error_message(error: Exception, default_message: str = "오류가 발생했습니다") -> str:
    """
    사용자 친화적인 한국어 오류 메시지를 생성합니다.

    Args:
        error: 발생한 예외
        default_message: 기본 오류 메시지

    Returns:
        사용자 친화적인 오류 메시지
    """
    if isinstance(error, CalendarServiceError):
        return str(error)
    
    # 일반적인 네트워크 오류
    if isinstance(error, ConnectionError):
        return "네트워크 연결에 문제가 발생했습니다. 인터넷 연결을 확인해주세요."
    
    # 타임아웃 오류
    if "timeout" in str(error).lower():
        return "요청 시간이 초과되었습니다. 나중에 다시 시도해주세요."
    
    # 기본 메시지 반환
    return f"{default_message}: {str(error)}"


def measure_performance(func: Callable) -> Callable:
    """
    함수 실행 시간을 측정하고 성능 통계를 수집하는 데코레이터

    Args:
        func: 측정할 함수

    Returns:
        데코레이터 함수
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 성능 통계 수집
            with _performance_lock:
                func_name = func.__name__
                _performance_stats[func_name].append({
                    'timestamp': datetime.now(),
                    'execution_time': execution_time,
                    'success': success,
                    'error': error
                })
                _performance_history[func_name].append(execution_time)
            
            # 로그 기록
            status = "성공" if success else "실패"
            logger.info(f"{func_name} 실행 시간: {execution_time:.4f}초 ({status})")
            
            # 성능 경고 (5초 이상 소요 시)
            if execution_time > 5.0:
                logger.warning(f"{func_name} 실행 시간이 {execution_time:.4f}초로 예상보다 오래 걸렸습니다.")
        
        return result
    
    return wrapper


def get_performance_stats(func_name: Optional[str] = None) -> Dict[str, Any]:
    """
    성능 통계를 조회합니다.
    
    Args:
        func_name: 특정 함수의 통계만 조회할 경우 함수명 (None이면 전체)
        
    Returns:
        성능 통계 딕셔너리
    """
    with _performance_lock:
        if func_name:
            if func_name not in _performance_stats:
                return {}
            
            stats = _performance_stats[func_name]
            history = list(_performance_history[func_name])
            
            if not history:
                return {'function': func_name, 'call_count': 0}
            
            return {
                'function': func_name,
                'call_count': len(stats),
                'avg_time': sum(history) / len(history),
                'min_time': min(history),
                'max_time': max(history),
                'success_rate': sum(1 for s in stats if s['success']) / len(stats) * 100,
                'recent_calls': stats[-10:]  # 최근 10개 호출
            }
        else:
            # 전체 통계
            result = {}
            for func_name_key in _performance_stats:
                stats = _performance_stats[func_name_key]
                history = list(_performance_history[func_name_key])
                
                if not history:
                    result[func_name_key] = {'function': func_name_key, 'call_count': 0}
                else:
                    result[func_name_key] = {
                        'function': func_name_key,
                        'call_count': len(stats),
                        'avg_time': sum(history) / len(history),
                        'min_time': min(history),
                        'max_time': max(history),
                        'success_rate': sum(1 for s in stats if s['success']) / len(stats) * 100,
                        'recent_calls': stats[-10:]  # 최근 10개 호출
                    }
            return result


def reset_performance_stats(func_name: Optional[str] = None) -> None:
    """
    성능 통계를 초기화합니다.
    
    Args:
        func_name: 특정 함수의 통계만 초기화할 경우 함수명 (None이면 전체)
    """
    with _performance_lock:
        if func_name:
            if func_name in _performance_stats:
                _performance_stats[func_name].clear()
                _performance_history[func_name].clear()
        else:
            _performance_stats.clear()
            _performance_history.clear()


def check_performance_threshold(func_name: str, threshold: float = 3.0) -> bool:
    """
    특정 함수의 평균 실행 시간이 임계값을 초과하는지 확인합니다.
    
    Args:
        func_name: 확인할 함수명
        threshold: 임계값 (초)
        
    Returns:
        임계값 초과 여부
    """
    stats = get_performance_stats(func_name)
    if not stats or 'avg_time' not in stats:
        return False
    
    return stats['avg_time'] > threshold


def safe_execute(
    func: Callable,
    *args: Any,
    default_return: Any = None,
    error_message: str = "작업 실행 중 오류가 발생했습니다",
    **kwargs: Any
) -> Any:
    """
    안전하게 함수를 실행하고 예외 처리하는 유틸리티 함수

    Args:
        func: 실행할 함수
        *args: 함수에 전달할 위치 인자
        default_return: 오류 발생 시 반환할 기본값
        error_message: 오류 발생 시 로그에 기록할 메시지
        **kwargs: 함수에 전달할 키워드 인자

    Returns:
        함수 실행 결과 또는 오류 발생 시 default_return
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"{error_message}: {e}")
        return default_return


def batch_execute(
    func: Callable,
    items: List[Any],
    batch_size: int = 10,
    delay_between_batches: float = 0.1
) -> List[Any]:
    """
    항목들을 배치로 나누어 함수를 실행합니다.
    
    Args:
        func: 각 항목에 대해 실행할 함수
        items: 처리할 항목들의 리스트
        batch_size: 배치 크기 (기본값: 10)
        delay_between_batches: 배치 간 대기 시간(초) (기본값: 0.1)
        
    Returns:
        각 항목에 대한 함수 실행 결과 리스트
    """
    results = []
    total_batches = (len(items) + batch_size - 1) // batch_size
    
    logger.info(f"배치 처리 시작: {len(items)}개 항목을 {total_batches}개 배치로 처리")
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        logger.info(f"배치 {batch_num}/{total_batches} 처리 중 ({len(batch)}개 항목)")
        
        batch_results = []
        for item in batch:
            try:
                result = func(item)
                batch_results.append(result)
            except Exception as e:
                logger.error(f"배치 처리 중 오류 발생: {e}")
                batch_results.append(None)
        
        results.extend(batch_results)
        
        # 배치 간 대기 (API 속도 제한 방지)
        if i + batch_size < len(items) and delay_between_batches > 0:
            time.sleep(delay_between_batches)
    
    logger.info(f"배치 처리 완료: {len(results)}개 결과 반환")
    return results


class ServiceObjectPool:
    """
    서비스 객체를 재사용하기 위한 풀 클래스
    """
    
    def __init__(self, max_size: int = 5):
        """
        ServiceObjectPool 초기화
        
        Args:
            max_size: 풀의 최대 크기
        """
        self.max_size = max_size
        self._pool = {}
        self._lock = threading.Lock()
        self._last_used = {}
        self._cleanup_interval = 300  # 5분
        self._last_cleanup = time.time()
    
    def get_service(self, service_key: str, factory_func: Callable) -> Any:
        """
        서비스 객체를 가져옵니다. 없으면 새로 생성합니다.
        
        Args:
            service_key: 서비스 식별 키
            factory_func: 서비스 객체 생성 함수
            
        Returns:
            서비스 객체
        """
        with self._lock:
            # 정기적인 정리 작업
            current_time = time.time()
            if current_time - self._last_cleanup > self._cleanup_interval:
                self._cleanup_old_services()
                self._last_cleanup = current_time
            
            # 기존 서비스 객체가 있으면 반환
            if service_key in self._pool:
                self._last_used[service_key] = current_time
                logger.debug(f"서비스 객체 재사용: {service_key}")
                return self._pool[service_key]
            
            # 풀이 가득 찬 경우 가장 오래된 객체 제거
            if len(self._pool) >= self.max_size:
                oldest_key = min(self._last_used.keys(), key=lambda k: self._last_used[k])
                del self._pool[oldest_key]
                del self._last_used[oldest_key]
                logger.debug(f"풀 용량 초과로 오래된 서비스 객체 제거: {oldest_key}")
            
            # 새 서비스 객체 생성
            try:
                service = factory_func()
                self._pool[service_key] = service
                self._last_used[service_key] = current_time
                logger.debug(f"새 서비스 객체 생성: {service_key}")
                return service
            except Exception as e:
                logger.error(f"서비스 객체 생성 실패: {service_key}, {e}")
                raise
    
    def _cleanup_old_services(self) -> None:
        """
        오래된 서비스 객체들을 정리합니다.
        """
        current_time = time.time()
        timeout = 1800  # 30분
        
        keys_to_remove = []
        for key, last_used in self._last_used.items():
            if current_time - last_used > timeout:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._pool[key]
            del self._last_used[key]
            logger.debug(f"오래된 서비스 객체 정리: {key}")
    
    def clear(self) -> None:
        """
        풀의 모든 서비스 객체를 제거합니다.
        """
        with self._lock:
            self._pool.clear()
            self._last_used.clear()
            logger.info("서비스 객체 풀 초기화 완료")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        풀의 현재 상태를 반환합니다.
        
        Returns:
            풀 상태 정보
        """
        with self._lock:
            return {
                'pool_size': len(self._pool),
                'max_size': self.max_size,
                'services': list(self._pool.keys()),
                'last_cleanup': self._last_cleanup
            }


# 전역 서비스 객체 풀
_service_pool = ServiceObjectPool()