# -*- coding: utf-8 -*-
"""
예외 처리 시스템

금융 거래 관리 시스템의 예외 클래스 계층 구조를 정의합니다.
"""

class FinancialSystemError(Exception):
    """
    금융 시스템 기본 예외 클래스
    
    모든 시스템 예외의 기본 클래스입니다.
    """
    
    def __init__(self, message: str = "금융 시스템 오류가 발생했습니다.", details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            details: 상세 오류 정보
        """
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """
        문자열 표현
        
        Returns:
            str: 오류 메시지 및 상세 정보
        """
        if self.details:
            return f"{self.message} - {self.details}"
        return self.message

class DataError(FinancialSystemError):
    """
    데이터 관련 예외 클래스
    
    데이터 처리, 검증, 저장 등과 관련된 오류에 사용됩니다.
    """
    
    def __init__(self, message: str = "데이터 오류가 발생했습니다.", details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            details: 상세 오류 정보
        """
        super().__init__(message, details)

class ValidationError(DataError):
    """
    데이터 검증 예외 클래스
    
    데이터 유효성 검사 실패 시 발생합니다.
    """
    
    def __init__(self, message: str = "데이터 검증 오류가 발생했습니다.", field: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            field: 오류가 발생한 필드
            details: 상세 오류 정보
        """
        self.field = field
        field_info = f" (필드: {field})" if field else ""
        super().__init__(f"{message}{field_info}", details)

class DuplicateDataError(DataError):
    """
    중복 데이터 예외 클래스
    
    중복된 데이터 발견 시 발생합니다.
    """
    
    def __init__(self, message: str = "중복된 데이터가 발견되었습니다.", identifier: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            identifier: 중복 식별자
            details: 상세 오류 정보
        """
        self.identifier = identifier
        id_info = f" (ID: {identifier})" if identifier else ""
        super().__init__(f"{message}{id_info}", details)

class DataNotFoundError(DataError):
    """
    데이터 미발견 예외 클래스
    
    요청한 데이터를 찾을 수 없을 때 발생합니다.
    """
    
    def __init__(self, message: str = "요청한 데이터를 찾을 수 없습니다.", identifier: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            identifier: 검색 식별자
            details: 상세 오류 정보
        """
        self.identifier = identifier
        id_info = f" (ID: {identifier})" if identifier else ""
        super().__init__(f"{message}{id_info}", details)

class DatabaseError(FinancialSystemError):
    """
    데이터베이스 예외 클래스
    
    데이터베이스 연결, 쿼리, 트랜잭션 등과 관련된 오류에 사용됩니다.
    """
    
    def __init__(self, message: str = "데이터베이스 오류가 발생했습니다.", query: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            query: 실패한 쿼리
            details: 상세 오류 정보
        """
        self.query = query
        super().__init__(message, details)

class ConnectionError(DatabaseError):
    """
    연결 예외 클래스
    
    데이터베이스 연결 실패 시 발생합니다.
    """
    
    def __init__(self, message: str = "데이터베이스 연결에 실패했습니다.", details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            details: 상세 오류 정보
        """
        super().__init__(message, None, details)

class QueryError(DatabaseError):
    """
    쿼리 예외 클래스
    
    SQL 쿼리 실행 실패 시 발생합니다.
    """
    
    def __init__(self, message: str = "SQL 쿼리 실행에 실패했습니다.", query: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            query: 실패한 쿼리
            details: 상세 오류 정보
        """
        super().__init__(message, query, details)

class TransactionError(DatabaseError):
    """
    트랜잭션 예외 클래스
    
    데이터베이스 트랜잭션 실패 시 발생합니다.
    """
    
    def __init__(self, message: str = "데이터베이스 트랜잭션에 실패했습니다.", details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            details: 상세 오류 정보
        """
        super().__init__(message, None, details)

class FileError(FinancialSystemError):
    """
    파일 예외 클래스
    
    파일 읽기, 쓰기, 검증 등과 관련된 오류에 사용됩니다.
    """
    
    def __init__(self, message: str = "파일 처리 오류가 발생했습니다.", file_path: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            file_path: 파일 경로
            details: 상세 오류 정보
        """
        self.file_path = file_path
        path_info = f" (파일: {file_path})" if file_path else ""
        super().__init__(f"{message}{path_info}", details)

class FileNotFoundError(FileError):
    """
    파일 미발견 예외 클래스
    
    파일을 찾을 수 없을 때 발생합니다.
    """
    
    def __init__(self, message: str = "파일을 찾을 수 없습니다.", file_path: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            file_path: 파일 경로
            details: 상세 오류 정보
        """
        super().__init__(message, file_path, details)

class FileFormatError(FileError):
    """
    파일 형식 예외 클래스
    
    파일 형식이 유효하지 않을 때 발생합니다.
    """
    
    def __init__(self, message: str = "파일 형식이 유효하지 않습니다.", file_path: str = None, format: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            file_path: 파일 경로
            format: 예상 파일 형식
            details: 상세 오류 정보
        """
        self.format = format
        format_info = f" (예상 형식: {format})" if format else ""
        super().__init__(f"{message}{format_info}", file_path, details)

class FileAccessError(FileError):
    """
    파일 접근 예외 클래스
    
    파일 접근 권한이 없을 때 발생합니다.
    """
    
    def __init__(self, message: str = "파일 접근 권한이 없습니다.", file_path: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            file_path: 파일 경로
            details: 상세 오류 정보
        """
        super().__init__(message, file_path, details)

class ConfigError(FinancialSystemError):
    """
    설정 예외 클래스
    
    설정 로드, 저장, 검증 등과 관련된 오류에 사용됩니다.
    """
    
    def __init__(self, message: str = "설정 오류가 발생했습니다.", key: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            key: 설정 키
            details: 상세 오류 정보
        """
        self.key = key
        key_info = f" (키: {key})" if key else ""
        super().__init__(f"{message}{key_info}", details)

class ConfigKeyError(ConfigError):
    """
    설정 키 예외 클래스
    
    설정 키를 찾을 수 없을 때 발생합니다.
    """
    
    def __init__(self, message: str = "설정 키를 찾을 수 없습니다.", key: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            key: 설정 키
            details: 상세 오류 정보
        """
        super().__init__(message, key, details)

class ConfigValueError(ConfigError):
    """
    설정 값 예외 클래스
    
    설정 값이 유효하지 않을 때 발생합니다.
    """
    
    def __init__(self, message: str = "설정 값이 유효하지 않습니다.", key: str = None, value: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            key: 설정 키
            value: 설정 값
            details: 상세 오류 정보
        """
        self.value = value
        value_info = f" (값: {value})" if value else ""
        super().__init__(f"{message}{value_info}", key, details)

class BackupError(FinancialSystemError):
    """
    백업 예외 클래스
    
    백업 생성, 복원, 검증 등과 관련된 오류에 사용됩니다.
    """
    
    def __init__(self, message: str = "백업 오류가 발생했습니다.", backup_file: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            backup_file: 백업 파일 경로
            details: 상세 오류 정보
        """
        self.backup_file = backup_file
        file_info = f" (파일: {backup_file})" if backup_file else ""
        super().__init__(f"{message}{file_info}", details)

class BackupCreationError(BackupError):
    """
    백업 생성 예외 클래스
    
    백업 생성 실패 시 발생합니다.
    """
    
    def __init__(self, message: str = "백업 생성에 실패했습니다.", backup_file: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            backup_file: 백업 파일 경로
            details: 상세 오류 정보
        """
        super().__init__(message, backup_file, details)

class BackupRestoreError(BackupError):
    """
    백업 복원 예외 클래스
    
    백업 복원 실패 시 발생합니다.
    """
    
    def __init__(self, message: str = "백업 복원에 실패했습니다.", backup_file: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            backup_file: 백업 파일 경로
            details: 상세 오류 정보
        """
        super().__init__(message, backup_file, details)

class BackupVerificationError(BackupError):
    """
    백업 검증 예외 클래스
    
    백업 검증 실패 시 발생합니다.
    """
    
    def __init__(self, message: str = "백업 검증에 실패했습니다.", backup_file: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            backup_file: 백업 파일 경로
            details: 상세 오류 정보
        """
        super().__init__(message, backup_file, details)

class IngestionError(FinancialSystemError):
    """
    데이터 수집 예외 클래스
    
    데이터 수집, 파싱, 정규화 등과 관련된 오류에 사용됩니다.
    """
    
    def __init__(self, message: str = "데이터 수집 오류가 발생했습니다.", source: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            source: 데이터 소스
            details: 상세 오류 정보
        """
        self.source = source
        source_info = f" (소스: {source})" if source else ""
        super().__init__(f"{message}{source_info}", details)

class ParsingError(IngestionError):
    """
    파싱 예외 클래스
    
    데이터 파싱 실패 시 발생합니다.
    """
    
    def __init__(self, message: str = "데이터 파싱에 실패했습니다.", source: str = None, line: int = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            source: 데이터 소스
            line: 오류 발생 라인
            details: 상세 오류 정보
        """
        self.line = line
        line_info = f" (라인: {line})" if line is not None else ""
        super().__init__(f"{message}{line_info}", source, details)

class NormalizationError(IngestionError):
    """
    정규화 예외 클래스
    
    데이터 정규화 실패 시 발생합니다.
    """
    
    def __init__(self, message: str = "데이터 정규화에 실패했습니다.", source: str = None, field: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            source: 데이터 소스
            field: 오류 발생 필드
            details: 상세 오류 정보
        """
        self.field = field
        field_info = f" (필드: {field})" if field else ""
        super().__init__(f"{message}{field_info}", source, details)

class ClassificationError(FinancialSystemError):
    """
    분류 예외 클래스
    
    거래 분류, 규칙 적용 등과 관련된 오류에 사용됩니다.
    """
    
    def __init__(self, message: str = "분류 오류가 발생했습니다.", rule_id: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            rule_id: 규칙 ID
            details: 상세 오류 정보
        """
        self.rule_id = rule_id
        rule_info = f" (규칙 ID: {rule_id})" if rule_id else ""
        super().__init__(f"{message}{rule_info}", details)

class RuleError(ClassificationError):
    """
    규칙 예외 클래스
    
    규칙 적용 실패 시 발생합니다.
    """
    
    def __init__(self, message: str = "규칙 적용에 실패했습니다.", rule_id: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            rule_id: 규칙 ID
            details: 상세 오류 정보
        """
        super().__init__(message, rule_id, details)

class AnalysisError(FinancialSystemError):
    """
    분석 예외 클래스
    
    거래 분석, 리포트 생성 등과 관련된 오류에 사용됩니다.
    """
    
    def __init__(self, message: str = "분석 오류가 발생했습니다.", analysis_type: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            analysis_type: 분석 유형
            details: 상세 오류 정보
        """
        self.analysis_type = analysis_type
        type_info = f" (유형: {analysis_type})" if analysis_type else ""
        super().__init__(f"{message}{type_info}", details)

class ReportError(AnalysisError):
    """
    리포트 예외 클래스
    
    리포트 생성 실패 시 발생합니다.
    """
    
    def __init__(self, message: str = "리포트 생성에 실패했습니다.", report_type: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            report_type: 리포트 유형
            details: 상세 오류 정보
        """
        super().__init__(message, report_type, details)

class FilterError(AnalysisError):
    """
    필터 예외 클래스
    
    필터 적용 실패 시 발생합니다.
    """
    
    def __init__(self, message: str = "필터 적용에 실패했습니다.", filter_id: str = None, details: str = None):
        """
        예외 초기화
        
        Args:
            message: 오류 메시지
            filter_id: 필터 ID
            details: 상세 오류 정보
        """
        self.filter_id = filter_id
        filter_info = f" (필터 ID: {filter_id})" if filter_id else ""
        super().__init__(f"{message}{filter_info}", details)