# -*- coding: utf-8 -*-
"""
예외 처리 및 로깅 시스템 사용 예제

예외 처리 및 로깅 시스템의 기본 사용법을 보여주는 예제입니다.
"""

import os
import sys
import logging
from datetime import datetime

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.exceptions import (
    FinancialSystemError, DataError, ValidationError, DatabaseError,
    FileError, FileNotFoundError, ConfigError, BackupError
)
from src.logging_system import setup_logging, get_logger, log_exception

def basic_exception_handling():
    """
    기본 예외 처리 예제
    """
    print("=== 기본 예외 처리 예제 ===")
    
    # 로거 가져오기
    logger = get_logger('example')
    
    try:
        # 예외 발생
        raise ValidationError("유효하지 않은 데이터", field="amount")
    except ValidationError as e:
        # 예외 처리
        logger.error(f"검증 오류: {e}")
        print(f"검증 오류가 발생했습니다: {e}")
    except DataError as e:
        # 상위 예외 처리
        logger.error(f"데이터 오류: {e}")
        print(f"데이터 오류가 발생했습니다: {e}")
    except FinancialSystemError as e:
        # 최상위 예외 처리
        logger.error(f"시스템 오류: {e}")
        print(f"시스템 오류가 발생했습니다: {e}")
    except Exception as e:
        # 기타 예외 처리
        logger.error(f"예상치 못한 오류: {e}", exc_info=True)
        print(f"예상치 못한 오류가 발생했습니다: {e}")

def exception_hierarchy_example():
    """
    예외 계층 구조 예제
    """
    print("\n=== 예외 계층 구조 예제 ===")
    
    # 로거 가져오기
    logger = get_logger('example')
    
    # 다양한 예외 생성
    exceptions = [
        ValidationError("유효하지 않은 금액", field="amount"),
        DatabaseError("데이터베이스 연결 실패"),
        FileNotFoundError("설정 파일을 찾을 수 없습니다", file_path="config.yaml"),
        ConfigError("설정 키가 유효하지 않습니다", key="database.path"),
        BackupError("백업 생성 실패", backup_file="backup.zip")
    ]
    
    # 예외 처리
    for exc in exceptions:
        try:
            # 예외 발생
            raise exc
        except FinancialSystemError as e:
            # 예외 유형 확인
            exc_type = e.__class__.__name__
            
            # 예외 처리
            logger.error(f"{exc_type}: {e}")
            print(f"{exc_type}가 발생했습니다: {e}")

def custom_exception_example():
    """
    사용자 정의 예외 예제
    """
    print("\n=== 사용자 정의 예외 예제 ===")
    
    # 로거 가져오기
    logger = get_logger('example')
    
    # 사용자 정의 예외 클래스
    class PaymentError(FinancialSystemError):
        """결제 처리 예외"""
        def __init__(self, message="결제 처리 중 오류가 발생했습니다.", payment_id=None, details=None):
            self.payment_id = payment_id
            payment_info = f" (결제 ID: {payment_id})" if payment_id else ""
            super().__init__(f"{message}{payment_info}", details)
    
    try:
        # 예외 발생
        raise PaymentError("결제 승인 실패", payment_id="PAY123456")
    except PaymentError as e:
        # 예외 처리
        logger.error(f"결제 오류: {e}")
        print(f"결제 오류가 발생했습니다: {e}")

def structured_logging_example():
    """
    구조화된 로깅 예제
    """
    print("\n=== 구조화된 로깅 예제 ===")
    
    # 로거 가져오기
    logger = get_logger('example')
    
    # 컨텍스트 정보
    context = {
        'user_id': 123,
        'transaction_id': 'TX987654',
        'amount': 10000,
        'timestamp': datetime.now().isoformat()
    }
    
    # 구조화된 로그 메시지
    logger.info("거래 처리 시작", context=context)
    logger.debug("거래 세부 정보 검증", context=context)
    logger.info("거래 처리 완료", context=context)
    
    print("구조화된 로그 메시지가 기록되었습니다.")

def exception_logging_example():
    """
    예외 로깅 예제
    """
    print("\n=== 예외 로깅 예제 ===")
    
    # 로거 가져오기
    logger = get_logger('example')
    
    try:
        # 중첩된 예외 발생
        try:
            # 내부 예외
            raise ValueError("잘못된 값")
        except ValueError as inner_exc:
            # 외부 예외
            raise DatabaseError("데이터베이스 쿼리 실패", details=str(inner_exc))
    except DatabaseError as e:
        # 예외 로깅
        logger.exception(f"데이터베이스 오류: {e}")
        
        # 또는 log_exception 함수 사용
        log_exception(e, 'example', 'ERROR', {'query': 'SELECT * FROM users'})
        
        print(f"예외가 로깅되었습니다: {e}")

def error_recovery_example():
    """
    오류 복구 예제
    """
    print("\n=== 오류 복구 예제 ===")
    
    # 로거 가져오기
    logger = get_logger('example')
    
    # 최대 재시도 횟수
    max_retries = 3
    
    # 재시도 함수
    def process_with_retry(func, *args, **kwargs):
        retries = 0
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except FinancialSystemError as e:
                retries += 1
                logger.warning(f"작업 실패 ({retries}/{max_retries}): {e}")
                
                if retries >= max_retries:
                    logger.error(f"최대 재시도 횟수 초과: {e}")
                    raise
                
                print(f"재시도 중... ({retries}/{max_retries})")
    
    # 실패할 수 있는 함수
    def unstable_operation(succeed_after=2):
        nonlocal max_retries
        if max_retries > succeed_after:
            max_retries -= 1
            raise DatabaseError("일시적인 데이터베이스 연결 오류")
        return "작업 성공"
    
    try:
        # 재시도 로직으로 함수 실행
        result = process_with_retry(unstable_operation)
        print(f"결과: {result}")
    except FinancialSystemError as e:
        print(f"최종 오류: {e}")

def user_friendly_errors_example():
    """
    사용자 친화적 오류 메시지 예제
    """
    print("\n=== 사용자 친화적 오류 메시지 예제 ===")
    
    # 로거 가져오기
    logger = get_logger('example')
    
    # 오류 메시지 매핑
    error_messages = {
        ValidationError: "입력한 데이터가 유효하지 않습니다. 다시 확인해주세요.",
        DatabaseError: "데이터베이스 연결에 문제가 있습니다. 잠시 후 다시 시도해주세요.",
        FileNotFoundError: "필요한 파일을 찾을 수 없습니다. 파일이 존재하는지 확인해주세요.",
        ConfigError: "설정에 문제가 있습니다. 관리자에게 문의하세요.",
        BackupError: "백업 처리 중 문제가 발생했습니다. 저장 공간을 확인해주세요."
    }
    
    # 예외 처리
    def get_user_message(exception):
        # 예외 유형에 따른 메시지 반환
        for exc_type, message in error_messages.items():
            if isinstance(exception, exc_type):
                return message
        
        # 기본 메시지
        return "처리 중 오류가 발생했습니다. 다시 시도해주세요."
    
    # 다양한 예외 처리
    exceptions = [
        ValidationError("유효하지 않은 금액", field="amount"),
        DatabaseError("데이터베이스 연결 실패"),
        FileNotFoundError("설정 파일을 찾을 수 없습니다", file_path="config.yaml"),
        ConfigError("설정 키가 유효하지 않습니다", key="database.path"),
        Exception("알 수 없는 오류")
    ]
    
    for exc in exceptions:
        try:
            # 예외 발생
            raise exc
        except Exception as e:
            # 상세 로그 기록 (개발자용)
            logger.error(f"오류 발생: {e}", exc_info=True)
            
            # 사용자 친화적 메시지 표시
            user_message = get_user_message(e)
            print(f"사용자 메시지: {user_message}")
            print(f"기술적 상세 정보: {e}")

def main():
    """
    메인 함수
    """
    # 로깅 설정
    log_file = os.path.join(parent_dir, 'logs', 'example.log')
    setup_logging(verbose=True, log_file=log_file)
    
    # 예제 실행
    basic_exception_handling()
    exception_hierarchy_example()
    custom_exception_example()
    structured_logging_example()
    exception_logging_example()
    error_recovery_example()
    user_friendly_errors_example()
    
    print("\n모든 예제가 완료되었습니다.")
    print(f"로그 파일: {log_file}")

if __name__ == '__main__':
    main()