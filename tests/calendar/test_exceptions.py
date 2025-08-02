"""
캘린더 예외 클래스 단위 테스트
"""
import pytest
from src.calendar.exceptions import (
    CalendarServiceError,
    AuthenticationError,
    TokenExpiredError,
    APIQuotaExceededError,
    NetworkError,
    TimeoutError,
    EventNotFoundError,
    InvalidEventDataError,
    CalendarNotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    InvalidOperationError
)


class TestCalendarServiceError:
    """CalendarServiceError 기본 예외 클래스 테스트"""
    
    def test_basic_creation(self):
        """기본 예외 생성 테스트"""
        error = CalendarServiceError("테스트 오류")
        
        assert str(error) == "테스트 오류"
        assert error.original_error is None
        assert error.get_user_message() == "테스트 오류"
        assert error.get_technical_details() == "테스트 오류"
    
    def test_creation_with_original_error(self):
        """원본 오류와 함께 예외 생성 테스트"""
        original = ValueError("원본 오류")
        error = CalendarServiceError("래핑된 오류", original)
        
        assert str(error) == "래핑된 오류"
        assert error.original_error == original
        assert error.get_user_message() == "래핑된 오류"
        assert "ValueError: 원본 오류" in error.get_technical_details()


class TestAuthenticationError:
    """AuthenticationError 테스트"""
    
    def test_default_message(self):
        """기본 메시지로 인증 오류 생성 테스트"""
        error = AuthenticationError()
        
        assert "인증에 실패했습니다" in str(error)
        assert "구글 계정 인증에 실패했습니다" in error.get_user_message()
    
    def test_custom_message(self):
        """사용자 정의 메시지로 인증 오류 생성 테스트"""
        error = AuthenticationError("사용자 정의 인증 오류")
        
        assert str(error) == "사용자 정의 인증 오류"
        assert "구글 계정 인증에 실패했습니다" in error.get_user_message()
    
    def test_with_original_error(self):
        """원본 오류와 함께 인증 오류 생성 테스트"""
        original = Exception("원본 인증 오류")
        error = AuthenticationError("인증 실패", original)
        
        assert error.original_error == original


class TestTokenExpiredError:
    """TokenExpiredError 테스트"""
    
    def test_default_message(self):
        """기본 메시지로 토큰 만료 오류 생성 테스트"""
        error = TokenExpiredError()
        
        assert "인증 토큰이 만료되었습니다" in str(error)
        assert "인증 세션이 만료되었습니다" in error.get_user_message()
    
    def test_inheritance(self):
        """AuthenticationError 상속 확인 테스트"""
        error = TokenExpiredError()
        
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, CalendarServiceError)


class TestAPIQuotaExceededError:
    """APIQuotaExceededError 테스트"""
    
    def test_default_message(self):
        """기본 메시지로 API 할당량 초과 오류 생성 테스트"""
        error = APIQuotaExceededError()
        
        assert "API 할당량이 초과되었습니다" in str(error)
        assert "Google API 사용량이 한도를 초과했습니다" in error.get_user_message()
        assert error.retry_after is None
    
    def test_with_retry_after(self):
        """재시도 시간과 함께 API 할당량 초과 오류 생성 테스트"""
        error = APIQuotaExceededError(retry_after=60)
        
        assert error.retry_after == 60
        user_message = error.get_user_message()
        assert "60초 후에 다시 시도해주세요" in user_message
    
    def test_custom_message_with_retry_after(self):
        """사용자 정의 메시지와 재시도 시간으로 오류 생성 테스트"""
        error = APIQuotaExceededError("사용자 정의 할당량 오류", retry_after=120)
        
        assert str(error) == "사용자 정의 할당량 오류"
        assert error.retry_after == 120


class TestNetworkError:
    """NetworkError 테스트"""
    
    def test_default_message(self):
        """기본 메시지로 네트워크 오류 생성 테스트"""
        error = NetworkError()
        
        assert "네트워크 연결에 문제가 발생했습니다" in str(error)
        assert "인터넷 연결에 문제가 있습니다" in error.get_user_message()
    
    def test_custom_message(self):
        """사용자 정의 메시지로 네트워크 오류 생성 테스트"""
        error = NetworkError("연결 실패")
        
        assert str(error) == "연결 실패"
        assert "인터넷 연결에 문제가 있습니다" in error.get_user_message()


class TestTimeoutError:
    """TimeoutError 테스트"""
    
    def test_default_message(self):
        """기본 메시지로 타임아웃 오류 생성 테스트"""
        error = TimeoutError()
        
        assert "요청 시간이 초과되었습니다" in str(error)
        assert "서버 응답 시간이 너무 오래 걸립니다" in error.get_user_message()
    
    def test_inheritance(self):
        """NetworkError 상속 확인 테스트"""
        error = TimeoutError()
        
        assert isinstance(error, NetworkError)
        assert isinstance(error, CalendarServiceError)


class TestEventNotFoundError:
    """EventNotFoundError 테스트"""
    
    def test_creation_with_event_id(self):
        """이벤트 ID와 함께 이벤트 없음 오류 생성 테스트"""
        error = EventNotFoundError("test-event-123")
        
        assert "test-event-123" in str(error)
        assert error.event_id == "test-event-123"
        user_message = error.get_user_message()
        assert "test-event-123" in user_message
        assert "요청하신 일정을 찾을 수 없습니다" in user_message
    
    def test_with_original_error(self):
        """원본 오류와 함께 이벤트 없음 오류 생성 테스트"""
        original = Exception("원본 오류")
        error = EventNotFoundError("test-event-123", original)
        
        assert error.event_id == "test-event-123"
        assert error.original_error == original


class TestInvalidEventDataError:
    """InvalidEventDataError 테스트"""
    
    def test_default_message(self):
        """기본 메시지로 잘못된 이벤트 데이터 오류 생성 테스트"""
        error = InvalidEventDataError()
        
        assert "이벤트 데이터가 올바르지 않습니다" in str(error)
        user_message = error.get_user_message()
        assert "일정 정보가 올바르지 않습니다" in user_message
        assert "필수 정보를 모두 입력했는지 확인해주세요" in user_message
    
    def test_custom_message(self):
        """사용자 정의 메시지로 잘못된 이벤트 데이터 오류 생성 테스트"""
        error = InvalidEventDataError("시간 형식이 잘못되었습니다")
        
        assert str(error) == "시간 형식이 잘못되었습니다"


class TestCalendarNotFoundError:
    """CalendarNotFoundError 테스트"""
    
    def test_creation_with_calendar_id(self):
        """캘린더 ID와 함께 캘린더 없음 오류 생성 테스트"""
        error = CalendarNotFoundError("test-calendar-123")
        
        assert "test-calendar-123" in str(error)
        assert error.calendar_id == "test-calendar-123"
        user_message = error.get_user_message()
        assert "test-calendar-123" in user_message
        assert "요청하신 캘린더를 찾을 수 없습니다" in user_message


class TestPermissionDeniedError:
    """PermissionDeniedError 테스트"""
    
    def test_default_message(self):
        """기본 메시지로 권한 부족 오류 생성 테스트"""
        error = PermissionDeniedError()
        
        assert "해당 작업을 수행할 권한이 없습니다" in str(error)
        user_message = error.get_user_message()
        assert "캘린더에 접근할 권한이 없습니다" in user_message
        assert "권한 설정을 확인해주세요" in user_message


class TestRateLimitError:
    """RateLimitError 테스트"""
    
    def test_default_message(self):
        """기본 메시지로 요청 속도 제한 오류 생성 테스트"""
        error = RateLimitError()
        
        assert "요청 속도 제한에 도달했습니다" in str(error)
        assert error.retry_after is None
        user_message = error.get_user_message()
        assert "너무 많은 요청이 발생했습니다" in user_message
        assert "잠시 후 다시 시도해주세요" in user_message
    
    def test_with_retry_after(self):
        """재시도 시간과 함께 요청 속도 제한 오류 생성 테스트"""
        error = RateLimitError(retry_after=30)
        
        assert error.retry_after == 30
        user_message = error.get_user_message()
        assert "30초 후에 다시 시도해주세요" in user_message


class TestServerError:
    """ServerError 테스트"""
    
    def test_default_message(self):
        """기본 메시지로 서버 오류 생성 테스트"""
        error = ServerError()
        
        assert "서버 오류가 발생했습니다" in str(error)
        user_message = error.get_user_message()
        assert "Google 서버에 일시적인 문제가 발생했습니다" in user_message
        assert "잠시 후 다시 시도해주세요" in user_message


class TestInvalidOperationError:
    """InvalidOperationError 테스트"""
    
    def test_default_message(self):
        """기본 메시지로 유효하지 않은 작업 오류 생성 테스트"""
        error = InvalidOperationError()
        
        assert "유효하지 않은 작업입니다" in str(error)
        user_message = error.get_user_message()
        assert "요청하신 작업을 수행할 수 없습니다" in user_message
        assert "입력 정보를 확인해주세요" in user_message


class TestExceptionHierarchy:
    """예외 클래스 계층 구조 테스트"""
    
    def test_all_exceptions_inherit_from_base(self):
        """모든 예외가 CalendarServiceError를 상속하는지 테스트"""
        exceptions = [
            AuthenticationError(),
            TokenExpiredError(),
            APIQuotaExceededError(),
            NetworkError(),
            TimeoutError(),
            EventNotFoundError("test-id"),
            InvalidEventDataError(),
            CalendarNotFoundError("test-calendar"),
            PermissionDeniedError(),
            RateLimitError(),
            ServerError(),
            InvalidOperationError()
        ]
        
        for exception in exceptions:
            assert isinstance(exception, CalendarServiceError)
            assert hasattr(exception, 'get_user_message')
            assert hasattr(exception, 'get_technical_details')
    
    def test_specific_inheritance_relationships(self):
        """특정 상속 관계 테스트"""
        # TokenExpiredError는 AuthenticationError를 상속
        token_error = TokenExpiredError()
        assert isinstance(token_error, AuthenticationError)
        
        # TimeoutError는 NetworkError를 상속
        timeout_error = TimeoutError()
        assert isinstance(timeout_error, NetworkError)