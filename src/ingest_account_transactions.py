# -*- coding: utf-8 -*-
"""
토스뱅크 계좌 거래내역 수집 스크립트

토스뱅크 계좌 거래내역 CSV 파일을 처리하여 데이터베이스에 저장합니다.
수입/지출 구분 로직 개선 및 필터링 규칙을 적용합니다.
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import time
import json
from decimal import Decimal

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                         'logs', 'account_transactions.log'), 'a')
    ]
)
logger = logging.getLogger(__name__)

# 현재 디렉토리 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# calendar 폴더와의 충돌을 피하기 위해 경로 조정
if current_dir in sys.path:
    sys.path.remove(current_dir)

from src.ingesters.toss_bank_account_ingester import TossBankAccountIngester
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.db_connection import DatabaseConnection
from src.models import Transaction
from src.ingesters.ingester_factory import IngesterFactory

# --- 설정 ---
DEFAULT_ACCOUNT_CSV_FILE_NAME = "토스뱅크_거래내역(토스뱅크 거래내역).csv"  # 토스뱅크에서 다운로드한 계좌 내역 파일
DB_FILE_NAME = "personal_data.db"
# --- 설정 끝 ---

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CSV_PATH = os.path.join(BASE_DIR, 'data', DEFAULT_ACCOUNT_CSV_FILE_NAME)
DB_PATH = os.path.join(BASE_DIR, DB_FILE_NAME)

# 로그 디렉토리 생성
log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)

def ingest_account_data(file_path: Optional[str] = None, batch_size: int = 1000, 
                        dry_run: bool = False, verbose: bool = False,
                        export_path: Optional[str] = None) -> Tuple[int, int, int]:
    """
    토스뱅크 계좌 입출금 내역을 DB에 저장하는 함수
    
    Args:
        file_path: CSV 파일 경로 (기본값: None, 기본 경로 사용)
        batch_size: 일괄 처리 크기 (기본값: 1000)
        dry_run: 실제 저장하지 않고 테스트만 수행 (기본값: False)
        verbose: 상세 로그 출력 여부 (기본값: False)
        export_path: 정규화된 데이터 내보내기 경로 (기본값: None)
        
    Returns:
        Tuple[int, int, int]: (총 거래 수, 새로 추가된 거래 수, 중복 거래 수)
    """
    # 로그 레벨 설정
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    # 파일 경로 설정
    csv_path = file_path if file_path else DEFAULT_CSV_PATH
    
    logger.info(f"'{csv_path}' 파일에서 계좌 데이터를 읽어옵니다...")
    
    try:
        # 시작 시간 기록
        start_time = time.time()
        
        # 데이터베이스 연결 설정
        db_connection = DatabaseConnection(DB_PATH)
        transaction_repo = TransactionRepository(db_connection)
        
        # 토스뱅크 계좌 수집기 생성 (팩토리 패턴 사용)
        factory = IngesterFactory()
        factory.register_ingester(TossBankAccountIngester)
        ingester = factory.create_ingester('TossBankAccountIngester')
        
        # 파일 유효성 검증
        if not ingester.validate_file(csv_path):
            logger.error(f"유효하지 않은 파일 형식입니다: {csv_path}")
            return 0, 0, 0
        
        # 데이터 수집 및 정규화
        logger.info("데이터 추출 및 정규화 시작...")
        normalized_data = ingester.ingest(csv_path)
        logger.info(f"총 {len(normalized_data)}개의 거래 내역을 정규화했습니다.")
        
        # 정규화된 데이터 내보내기 (요청 시)
        if export_path:
            export_dir = os.path.dirname(export_path)
            if export_dir:
                os.makedirs(export_dir, exist_ok=True)
            
            # Decimal 객체를 JSON으로 직렬화하기 위한 사용자 정의 인코더
            class DecimalEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, Decimal):
                        return float(obj)
                    return super(DecimalEncoder, self).default(obj)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(normalized_data, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
            logger.info(f"정규화된 데이터를 '{export_path}'에 저장했습니다.")
        
        # Transaction 객체 생성
        logger.info("Transaction 객체 생성 중...")
        transactions = []
        error_count = 0
        
        # 배치 처리로 Transaction 객체 생성
        for i in range(0, len(normalized_data), batch_size):
            batch_data = normalized_data[i:i+batch_size]
            batch_transactions = []
            
            for data in batch_data:
                try:
                    transaction = Transaction.from_dict(data)
                    batch_transactions.append(transaction)
                except Exception as e:
                    error_count += 1
                    if error_count <= 5 or verbose:  # 처음 5개 오류만 상세 로깅
                        logger.error(f"Transaction 객체 생성 오류: {e}, 데이터: {data}")
                    elif error_count == 6:
                        logger.error("추가 오류는 verbose 모드에서만 표시됩니다.")
            
            transactions.extend(batch_transactions)
            
            # 진행 상황 로깅
            if (i // batch_size) % 5 == 0 or i + batch_size >= len(normalized_data):
                logger.info(f"Transaction 객체 생성 진행 중: {min(i + batch_size, len(normalized_data))}/{len(normalized_data)}")
        
        if error_count > 0:
            logger.warning(f"총 {error_count}개의 Transaction 객체 생성 오류가 발생했습니다.")
        
        logger.info(f"{len(transactions)}개의 Transaction 객체를 생성했습니다.")
        
        # 일괄 저장
        total_created = 0
        if transactions and not dry_run:
            try:
                # 중복 거래 필터링 (최적화된 방식)
                logger.info("중복 거래 확인 중...")
                
                # 트랜잭션 ID 목록 생성
                transaction_ids = [t.transaction_id for t in transactions]
                
                # 배치 처리로 중복 확인
                existing_ids = []
                for i in range(0, len(transaction_ids), batch_size):
                    batch_ids = transaction_ids[i:i+batch_size]
                    batch_existing_ids = transaction_repo._find_existing_transaction_ids(batch_ids)
                    existing_ids.extend(batch_existing_ids)
                    
                    # 진행 상황 로깅
                    if (i // batch_size) % 5 == 0 or i + batch_size >= len(transaction_ids):
                        logger.info(f"중복 확인 진행 중: {min(i + batch_size, len(transaction_ids))}/{len(transaction_ids)}")
                
                # 새로운 거래만 필터링
                new_transactions = [t for t in transactions if t.transaction_id not in existing_ids]
                
                if existing_ids:
                    logger.info(f"{len(existing_ids)}개의 중복 거래를 건너뜁니다.")
                
                if new_transactions:
                    logger.info(f"{len(new_transactions)}개의 새로운 거래를 저장합니다...")
                    
                    # 배치 단위로 저장
                    for i in range(0, len(new_transactions), batch_size):
                        batch = new_transactions[i:i+batch_size]
                        
                        try:
                            created_transactions = transaction_repo.bulk_create(batch)
                            total_created += len(created_transactions)
                            
                            # 진행 상황 로깅
                            logger.info(f"배치 저장 진행 중: {min(i + batch_size, len(new_transactions))}/{len(new_transactions)}, "
                                       f"총 {total_created}개 저장")
                        except Exception as e:
                            logger.error(f"배치 저장 오류: {e}")
                            # 개별 저장 시도 (배치 저장 실패 시)
                            for j, transaction in enumerate(batch):
                                try:
                                    transaction_repo.create(transaction)
                                    total_created += 1
                                except Exception as inner_e:
                                    logger.error(f"개별 저장 오류 ({j+1}/{len(batch)}): {inner_e}")
                    
                    logger.info(f"총 {total_created}개의 새로운 거래 내역이 추가되었습니다.")
                else:
                    logger.info("추가할 새로운 거래 내역이 없습니다.")
                
            except Exception as e:
                logger.error(f"거래 저장 오류: {e}")
        elif dry_run:
            logger.info("드라이 런 모드: 데이터베이스에 저장하지 않습니다.")
            # 중복 거래 확인 (드라이 런 모드에서도)
            transaction_ids = [t.transaction_id for t in transactions]
            existing_ids = transaction_repo._find_existing_transaction_ids(transaction_ids)
            logger.info(f"드라이 런 결과: 총 {len(transactions)}개 중 {len(existing_ids)}개 중복, "
                       f"{len(transactions) - len(existing_ids)}개 새로운 거래")
        else:
            logger.info("저장할 거래 내역이 없습니다.")
        
        # 처리 시간 계산
        elapsed_time = time.time() - start_time
        logger.info(f"처리 완료! 소요 시간: {elapsed_time:.2f}초")
        
        return len(transactions), total_created, len(existing_ids) if 'existing_ids' in locals() else 0
        
    except FileNotFoundError:
        logger.error(f"오류: 파일을 찾을 수 없습니다. '{csv_path}'")
        logger.info("토스뱅크 앱에서 '전체 > 입출금내역 > CSV 다운로드'로 파일을 다운로드해주세요.")
        return 0, 0, 0
    except Exception as e:
        logger.error(f"처리 오류: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0, 0, 0

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='토스뱅크 계좌 거래내역 수집')
    parser.add_argument('--file', '-f', help='CSV 파일 경로')
    parser.add_argument('--batch-size', '-b', type=int, default=1000, help='일괄 처리 크기')
    parser.add_argument('--dry-run', '-d', action='store_true', help='실제 저장하지 않고 테스트만 수행')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 로그 출력')
    parser.add_argument('--export', '-e', help='정규화된 데이터를 JSON 파일로 내보내기')
    
    args = parser.parse_args()
    
    # 시작 메시지
    logger.info("=" * 80)
    logger.info("토스뱅크 계좌 거래내역 수집 시작")
    logger.info(f"파일: {args.file if args.file else DEFAULT_CSV_PATH}")
    logger.info(f"배치 크기: {args.batch_size}")
    logger.info(f"드라이 런: {args.dry_run}")
    logger.info(f"상세 로그: {args.verbose}")
    logger.info(f"내보내기: {args.export if args.export else '사용 안 함'}")
    logger.info("=" * 80)
    
    # 데이터 수집 실행
    total, created, duplicates = ingest_account_data(
        args.file, args.batch_size, args.dry_run, args.verbose, args.export
    )
    
    # 결과 요약
    logger.info("=" * 80)
    logger.info("토스뱅크 계좌 거래내역 수집 결과")
    logger.info(f"총 거래 수: {total}")
    logger.info(f"새로 추가된 거래 수: {created}")
    logger.info(f"중복 거래 수: {duplicates}")
    logger.info("=" * 80)

if __name__ == '__main__':
    main()