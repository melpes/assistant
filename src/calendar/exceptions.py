"""
캘린더 서비스 예외 클래스들

이 모듈은 캘린더 서비스에서 발생할 수 있는 다양한 예외 클래스들을 정의합니다.
각 예외는 사용자 친화적인 한국어 메시지를 포함합니다.
"""
from typing import Optional


class CalendarServiceError(Exception):
    """캘린더 서비스 기본 예외 클래스"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error
        
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        return str(self)
    
    def get_technical_details(self) -> str:
        """기술적인 오류 세부 정보를 반환합니다."""
        if self.original_error:
            return f"{self}: {type(self.original_error).__name__}: {self.original_error}"
        return str(self)


class AuthenticationError(CalendarServiceError):
    """인증 관련 오류"""
    
    def __init__(self, message: str = "인증에 실패했습니다", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
    
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        return "구글 계정 인증에 실패했습니다. 다시 로그인해주세요."


class TokenExpiredError(AuthenticationError):
    """토큰 만료 오류"""
    
    def __init__(self, message: str = "인증 토큰이 만료되었습니다", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
    
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        return "인증 세션이 만료되었습니다. 다시 로그인해주세요."


class APIQuotaExceededError(CalendarServiceError):
    """API 할당량 초과 오류"""
    
    def __init__(
        self,
        message: str = "API 할당량이 초과되었습니다",
        original_error: Optional[Exception] = None,
        retry_after: Optional[int] = None
    ):
        super().__init__(message, original_error)
        self.retry_after = retry_after
    
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        base_msg = "Google API 사용량이 한도를 초과했습니다."
        if self.retry_after:
            return f"{base_msg} {self.retry_after}초 후에 다시 시도해주세요."
        return f"{base_msg} 잠시 후 다시 시도해주세요."


class NetworkError(CalendarServiceError):
    """네트워크 관련 오류"""
    
    def __init__(self, message: str = "네트워크 연결에 문제가 발생했습니다", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
    
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        return "인터넷 연결에 문제가 있습니다. 네트워크 상태를 확인하고 다시 시도해주세요."


class TimeoutError(NetworkError):
    """요청 시간 초과 오류"""
    
    def __init__(self, message: str = "요청 시간이 초과되었습니다", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
    
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        return "서버 응답 시간이 너무 오래 걸립니다. 잠시 후 다시 시도해주세요."


class EventNotFoundError(CalendarServiceError):
    """이벤트를 찾을 수 없는 경우"""
    
    def __init__(self, event_id: str, original_error: Optional[Exception] = None):
        message = f"이벤트를 찾을 수 없습니다: {event_id}"
        super().__init__(message, original_error)
        self.event_id = event_id
    
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        return f"요청하신 일정을 찾을 수 없습니다. ID: {self.event_id}"


class InvalidEventDataError(CalendarServiceError):
    """잘못된 이벤트 데이터"""
    
    def __init__(self, message: str = "이벤트 데이터가 올바르지 않습니다", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
    
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        return "일정 정보가 올바르지 않습니다. 필수 정보를 모두 입력했는지 확인해주세요."


class CalendarNotFoundError(CalendarServiceError):
    """캘린더를 찾을 수 없는 경우"""
    
    def __init__(self, calendar_id: str, original_error: Optional[Exception] = None):
        message = f"캘린더를 찾을 수 없습니다: {calendar_id}"
        super().__init__(message, original_error)
        self.calendar_id = calendar_id
    
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        return f"요청하신 캘린더를 찾을 수 없습니다. ID: {self.calendar_id}"


class PermissionDeniedError(CalendarServiceError):
    """권한 부족 오류"""
    
    def __init__(self, message: str = "해당 작업을 수행할 권한이 없습니다", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
    
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        return "캘린더에 접근할 권한이 없습니다. 권한 설정을 확인해주세요."


class RateLimitError(CalendarServiceError):
    """요청 속도 제한 오류"""
    
    def __init__(
        self,
        message: str = "요청 속도 제한에 도달했습니다",
        original_error: Optional[Exception] = None,
        retry_after: Optional[int] = None
    ):
        super().__init__(message, original_error)
        self.retry_after = retry_after
    
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        if self.retry_after:
            return f"너무 많은 요청이 발생했습니다. {self.retry_after}초 후에 다시 시도해주세요."
        return "너무 많은 요청이 발생했습니다. 잠시 후 다시 시도해주세요."


class ServerError(CalendarServiceError):
    """서버 오류"""
    
    def __init__(self, message: str = "서버 오류가 발생했습니다", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
    
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        return "Google 서버에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요."


class InvalidOperationError(CalendarServiceError):
    """유효하지 않은 작업 오류"""
    
    def __init__(self, message: str = "유효하지 않은 작업입니다", original_error: Optional[Exception] = None):
        super().__init__(message, original_error)
    
    def get_user_message(self) -> str:
        """사용자에게 표시할 메시지를 반환합니다."""
        return "요청하신 작업을 수행할 수 없습니다. 입력 정보를 확인해주세요."