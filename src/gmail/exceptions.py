"""
Gmail 이메일 캘린더 자동화 관련 예외 클래스들
"""


class EmailCalendarError(Exception):
    """이메일 캘린더 자동화 관련 기본 예외 클래스"""
    
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.original_error = original_error


class GmailApiError(EmailCalendarError):
    """Gmail API 관련 오류"""
    pass


class EmailProcessingError(EmailCalendarError):
    """이메일 처리 중 발생한 오류"""
    pass


class EventExtractionError(EmailCalendarError):
    """일정 정보 추출 중 발생한 오류"""
    pass


class EventCreationError(EmailCalendarError):
    """일정 생성 중 발생한 오류"""
    pass


class RuleEngineError(EmailCalendarError):
    """규칙 엔진 관련 오류"""
    pass


class NotificationError(EmailCalendarError):
    """알림 관련 오류"""
    pass


class RepositoryError(EmailCalendarError):
    """저장소 관련 오류"""
    pass


class AuthenticationError(EmailCalendarError):
    """인증 관련 오류"""
    pass


class ConfidenceEvaluationError(EmailCalendarError):
    """신뢰도 평가 관련 오류"""
    pass