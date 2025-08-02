# -*- coding: utf-8 -*-
"""
예외 처리 시스템 테스트

예외 클래스 계층 구조 및 기능을 테스트합니다.
"""

import os
import sys
import unittest

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.exceptions import (
    FinancialSystemError, DataError, ValidationError, DuplicateDataError, DataNotFoundError,
    DatabaseError, ConnectionError, QueryError, TransactionError,
    FileError, FileNotFoundError, FileFormatError, FileAccessError,
    ConfigError, ConfigKeyError, ConfigValueError,
    BackupError, BackupCreationError, BackupRestoreError, BackupVerificationError,
    IngestionError, ParsingError, NormalizationError,
    ClassificationError, RuleError,
    AnalysisError, ReportError, FilterError
)

class TestExceptions(unittest.TestCase):
    """
    예외 처리 시스템 테스트 클래스
    """
    
    def test_base_exception(self):
        """
        기본 예외 클래스 테스트
        """
        # 기본 메시지
        exc = FinancialSystemError()
        self.assertEqual(str(exc), "금융 시스템 오류가 발생했습니다.")
        
        # 사용자 정의 메시지
        exc = FinancialSystemError("테스트 오류")
        self.assertEqual(str(exc), "테스트 오류")
        
        # 상세 정보 포함
        exc = FinancialSystemError("테스트 오류", "상세 정보")
        self.assertEqual(str(exc), "테스트 오류 - 상세 정보")
    
    def test_data_exceptions(self):
        """
        데이터 관련 예외 클래스 테스트
        """
        # DataError
        exc = DataError()
        self.assertEqual(str(exc), "데이터 오류가 발생했습니다.")
        self.assertIsInstance(exc, FinancialSystemError)
        
        # ValidationError
        exc = ValidationError(field="username")
        self.assertEqual(str(exc), "데이터 검증 오류가 발생했습니다. (필드: username)")
        self.assertIsInstance(exc, DataError)
        
        # DuplicateDataError
        exc = DuplicateDataError(identifier="123")
        self.assertEqual(str(exc), "중복된 데이터가 발견되었습니다. (ID: 123)")
        self.assertIsInstance(exc, DataError)
        
        # DataNotFoundError
        exc = DataNotFoundError(identifier="456")
        self.assertEqual(str(exc), "요청한 데이터를 찾을 수 없습니다. (ID: 456)")
        self.assertIsInstance(exc, DataError)
    
    def test_database_exceptions(self):
        """
        데이터베이스 관련 예외 클래스 테스트
        """
        # DatabaseError
        exc = DatabaseError()
        self.assertEqual(str(exc), "데이터베이스 오류가 발생했습니다.")
        self.assertIsInstance(exc, FinancialSystemError)
        
        # ConnectionError
        exc = ConnectionError()
        self.assertEqual(str(exc), "데이터베이스 연결에 실패했습니다.")
        self.assertIsInstance(exc, DatabaseError)
        
        # QueryError
        exc = QueryError(query="SELECT * FROM users")
        self.assertEqual(str(exc), "SQL 쿼리 실행에 실패했습니다.")
        self.assertIsInstance(exc, DatabaseError)
        self.assertEqual(exc.query, "SELECT * FROM users")
        
        # TransactionError
        exc = TransactionError()
        self.assertEqual(str(exc), "데이터베이스 트랜잭션에 실패했습니다.")
        self.assertIsInstance(exc, DatabaseError)
    
    def test_file_exceptions(self):
        """
        파일 관련 예외 클래스 테스트
        """
        # FileError
        exc = FileError(file_path="/path/to/file.txt")
        self.assertEqual(str(exc), "파일 처리 오류가 발생했습니다. (파일: /path/to/file.txt)")
        self.assertIsInstance(exc, FinancialSystemError)
        
        # FileNotFoundError
        exc = FileNotFoundError(file_path="/path/to/file.txt")
        self.assertEqual(str(exc), "파일을 찾을 수 없습니다. (파일: /path/to/file.txt)")
        self.assertIsInstance(exc, FileError)
        
        # FileFormatError
        exc = FileFormatError(file_path="/path/to/file.txt", format="CSV")
        self.assertEqual(str(exc), "파일 형식이 유효하지 않습니다. (예상 형식: CSV) (파일: /path/to/file.txt)")
        self.assertIsInstance(exc, FileError)
        
        # FileAccessError
        exc = FileAccessError(file_path="/path/to/file.txt")
        self.assertEqual(str(exc), "파일 접근 권한이 없습니다. (파일: /path/to/file.txt)")
        self.assertIsInstance(exc, FileError)
    
    def test_config_exceptions(self):
        """
        설정 관련 예외 클래스 테스트
        """
        # ConfigError
        exc = ConfigError(key="database.path")
        self.assertEqual(str(exc), "설정 오류가 발생했습니다. (키: database.path)")
        self.assertIsInstance(exc, FinancialSystemError)
        
        # ConfigKeyError
        exc = ConfigKeyError(key="database.path")
        self.assertEqual(str(exc), "설정 키를 찾을 수 없습니다. (키: database.path)")
        self.assertIsInstance(exc, ConfigError)
        
        # ConfigValueError
        exc = ConfigValueError(key="database.path", value="/invalid/path")
        self.assertEqual(str(exc), "설정 값이 유효하지 않습니다. (값: /invalid/path) (키: database.path)")
        self.assertIsInstance(exc, ConfigError)
    
    def test_backup_exceptions(self):
        """
        백업 관련 예외 클래스 테스트
        """
        # BackupError
        exc = BackupError(backup_file="/path/to/backup.zip")
        self.assertEqual(str(exc), "백업 오류가 발생했습니다. (파일: /path/to/backup.zip)")
        self.assertIsInstance(exc, FinancialSystemError)
        
        # BackupCreationError
        exc = BackupCreationError(backup_file="/path/to/backup.zip")
        self.assertEqual(str(exc), "백업 생성에 실패했습니다. (파일: /path/to/backup.zip)")
        self.assertIsInstance(exc, BackupError)
        
        # BackupRestoreError
        exc = BackupRestoreError(backup_file="/path/to/backup.zip")
        self.assertEqual(str(exc), "백업 복원에 실패했습니다. (파일: /path/to/backup.zip)")
        self.assertIsInstance(exc, BackupError)
        
        # BackupVerificationError
        exc = BackupVerificationError(backup_file="/path/to/backup.zip")
        self.assertEqual(str(exc), "백업 검증에 실패했습니다. (파일: /path/to/backup.zip)")
        self.assertIsInstance(exc, BackupError)
    
    def test_ingestion_exceptions(self):
        """
        데이터 수집 관련 예외 클래스 테스트
        """
        # IngestionError
        exc = IngestionError(source="toss_bank_card")
        self.assertEqual(str(exc), "데이터 수집 오류가 발생했습니다. (소스: toss_bank_card)")
        self.assertIsInstance(exc, FinancialSystemError)
        
        # ParsingError
        exc = ParsingError(source="toss_bank_card", line=10)
        self.assertEqual(str(exc), "데이터 파싱에 실패했습니다. (라인: 10) (소스: toss_bank_card)")
        self.assertIsInstance(exc, IngestionError)
        
        # NormalizationError
        exc = NormalizationError(source="toss_bank_card", field="amount")
        self.assertEqual(str(exc), "데이터 정규화에 실패했습니다. (필드: amount) (소스: toss_bank_card)")
        self.assertIsInstance(exc, IngestionError)
    
    def test_classification_exceptions(self):
        """
        분류 관련 예외 클래스 테스트
        """
        # ClassificationError
        exc = ClassificationError(rule_id="rule123")
        self.assertEqual(str(exc), "분류 오류가 발생했습니다. (규칙 ID: rule123)")
        self.assertIsInstance(exc, FinancialSystemError)
        
        # RuleError
        exc = RuleError(rule_id="rule123")
        self.assertEqual(str(exc), "규칙 적용에 실패했습니다. (규칙 ID: rule123)")
        self.assertIsInstance(exc, ClassificationError)
    
    def test_analysis_exceptions(self):
        """
        분석 관련 예외 클래스 테스트
        """
        # AnalysisError
        exc = AnalysisError(analysis_type="expense")
        self.assertEqual(str(exc), "분석 오류가 발생했습니다. (유형: expense)")
        self.assertIsInstance(exc, FinancialSystemError)
        
        # ReportError
        exc = ReportError(report_type="monthly")
        self.assertEqual(str(exc), "리포트 생성에 실패했습니다. (유형: monthly)")
        self.assertIsInstance(exc, AnalysisError)
        
        # FilterError
        exc = FilterError(filter_id="filter123")
        self.assertEqual(str(exc), "필터 적용에 실패했습니다. (필터 ID: filter123)")
        self.assertIsInstance(exc, AnalysisError)

if __name__ == '__main__':
    unittest.main()