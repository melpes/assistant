# -*- coding: utf-8 -*-
"""
통합 데이터 수집 스크립트

다양한 소스로부터 거래 데이터를 수집하고 데이터베이스에 저장합니다.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.ingesters.ingester_factory import IngesterFactory
from src.repositories.transaction_repository import TransactionRepository
from src.models.transaction import Transaction

def setup_argparse() -> argparse.ArgumentParser:
    """
    명령줄 인자 파서를 설정합니다.
    
    Returns:
        argparse.ArgumentParser: 설정된 인자 파서
    """
    parser = argparse.ArgumentParser(description='통합 데이터 수집 도구')
    
    parser.add_argument('--file', '-f', type=str, help='수집할 파일 경로')
    parser.add_argument('--dir', '-d', type=str, help='수집할 디렉토리 경로')
    parser.add_argument('--type', '-t', type=str, help='수집기 유형 (예: TossBankCardIngester)')
    parser.add_argument('--list', '-l', action='store_true', help='사용 가능한 수집기 목록 표시')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 로깅 활성화')
    
    return parser

def get_data_directory() -> str:
    """
    데이터 디렉토리 경로를 반환합니다.
    
    Returns:
        str: 데이터 디렉토리 경로
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'data')

def collect_from_file(file_path: str, ingester_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    지정된 파일에서 데이터를 수집합니다.
    
    Args:
        file_path: 수집할 파일 경로
        ingester_type: 사용할 수집기 유형 (선택)
        
    Returns:
        List[Dict[str, Any]]: 수집된 거래 데이터 목록
    """
    factory = IngesterFactory()
    factory.discover_ingesters()
    
    # 수집기 유형이 지정되지 않은 경우 파일 확장자로 추론
    if not ingester_type:
        ingester_type = factory.get_ingester_by_file_extension(file_path)
        
        if not ingester_type:
            logger.error(f"파일 유형에 맞는 수집기를 찾을 수 없습니다: {file_path}")
            return []
    
    try:
        # 수집기 생성
        ingester = factory.create_ingester(ingester_type)
        logger.info(f"{ingester_type} 수집기를 사용하여 {file_path} 파일 처리 시작")
        
        # 데이터 수집
        transactions = ingester.ingest(file_path)
        logger.info(f"{len(transactions)}개의 거래 데이터 수집 완료")
        
        return transactions
        
    except Exception as e:
        logger.error(f"데이터 수집 중 오류 발생: {e}")
        return []

def collect_from_directory(dir_path: str) -> List[Dict[str, Any]]:
    """
    지정된 디렉토리의 모든 파일에서 데이터를 수집합니다.
    
    Args:
        dir_path: 수집할 디렉토리 경로
        
    Returns:
        List[Dict[str, Any]]: 수집된 거래 데이터 목록
    """
    all_transactions = []
    
    # 디렉토리 내 모든 파일 처리
    for file_path in Path(dir_path).glob('*'):
        if file_path.is_file():
            transactions = collect_from_file(str(file_path))
            all_transactions.extend(transactions)
    
    logger.info(f"디렉토리 {dir_path}에서 총 {len(all_transactions)}개의 거래 데이터 수집 완료")
    return all_transactions

def save_transactions_to_db(transactions: List[Dict[str, Any]]) -> int:
    """
    수집된 거래 데이터를 데이터베이스에 저장합니다.
    
    Args:
        transactions: 저장할 거래 데이터 목록
        
    Returns:
        int: 저장된 거래 수
    """
    if not transactions:
        logger.warning("저장할 거래 데이터가 없습니다.")
        return 0
    
    try:
        # 트랜잭션 저장소 생성
        repo = TransactionRepository()
        
        # 트랜잭션 객체 생성 및 저장
        saved_count = 0
        for transaction_data in transactions:
            try:
                # Transaction 객체 생성
                transaction = Transaction.from_dict(transaction_data)
                
                # 중복 확인
                existing = repo.find_by_transaction_id(transaction.transaction_id)
                if existing:
                    logger.debug(f"중복 거래 건너뜀: {transaction.transaction_id}")
                    continue
                
                # 저장
                repo.create(transaction)
                saved_count += 1
                
            except Exception as e:
                logger.warning(f"거래 저장 중 오류 발생: {e}, 데이터: {transaction_data}")
        
        logger.info(f"{saved_count}개의 새로운 거래 데이터가 데이터베이스에 저장되었습니다.")
        return saved_count
        
    except Exception as e:
        logger.error(f"데이터베이스 저장 중 오류 발생: {e}")
        return 0

def list_available_ingesters():
    """
    사용 가능한 수집기 목록을 표시합니다.
    """
    factory = IngesterFactory()
    factory.discover_ingesters()
    
    ingesters = factory.get_available_ingesters()
    
    print("\n=== 사용 가능한 데이터 수집기 ===")
    if not ingesters:
        print("사용 가능한 수집기가 없습니다.")
    else:
        for i, ingester_name in enumerate(ingesters, 1):
            try:
                ingester = factory.create_ingester(ingester_name)
                info = ingester.get_info()
                file_types = ", ".join(ingester.get_supported_file_types()) or "없음"
                
                print(f"{i}. {info['name']} ({ingester_name})")
                print(f"   설명: {info['description']}")
                print(f"   지원 파일 형식: {file_types}")
                print()
                
            except Exception as e:
                print(f"{i}. {ingester_name} - 정보 로드 실패: {e}")

def main():
    """
    메인 함수
    """
    parser = setup_argparse()
    args = parser.parse_args()
    
    # 상세 로깅 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 사용 가능한 수집기 목록 표시
    if args.list:
        list_available_ingesters()
        return
    
    # 파일 또는 디렉토리에서 데이터 수집
    transactions = []
    
    if args.file:
        transactions = collect_from_file(args.file, args.type)
    elif args.dir:
        transactions = collect_from_directory(args.dir)
    else:
        # 기본 데이터 디렉토리 사용
        data_dir = get_data_directory()
        logger.info(f"기본 데이터 디렉토리 사용: {data_dir}")
        transactions = collect_from_directory(data_dir)
    
    # 데이터베이스에 저장
    saved_count = save_transactions_to_db(transactions)
    
    print(f"\n작업 완료! {saved_count}개의 새로운 거래 데이터가 추가되었습니다.")

if __name__ == '__main__':
    main()