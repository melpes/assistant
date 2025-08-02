# -*- coding: utf-8 -*-
"""
토스뱅크 카드 이용내역서 데이터 수집 스크립트

TossBankCardIngester 클래스를 사용하여 토스뱅크 카드 이용내역서를 처리합니다.
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 프로젝트 루트 디렉토리 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.ingesters.toss_bank_card_ingester import TossBankCardIngester

# --- 설정 (토스뱅크 파일 기준) ---
XLSX_FILE_NAME = "토스뱅크카드_이용내역서_강태희님.xlsx"
DB_FILE_NAME = "personal_data.db"
TABLE_NAME = "transactions"  # 확장된 테이블 이름
# --- 설정 끝 ---

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX_PATH = os.path.join(BASE_DIR, 'data', XLSX_FILE_NAME)
DB_PATH = os.path.join(BASE_DIR, DB_FILE_NAME)

def ingest_data():
    """TossBankCardIngester를 사용하여 데이터를 수집하고 DB에 저장하는 함수"""
    logger.info(f"'{XLSX_PATH}' 파일에서 데이터를 읽어옵니다...")
    
    try:
        # TossBankCardIngester 인스턴스 생성
        ingester = TossBankCardIngester()
        
        # 데이터 수집 및 정규화
        transactions = ingester.ingest(XLSX_PATH)
        logger.info(f"{len(transactions)}개의 거래 데이터를 수집했습니다.")
        
        # 데이터베이스에 저장
        logger.info("데이터베이스에 연결하여 데이터를 저장합니다...")
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            
            # 테이블 존재 여부 확인
            cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TABLE_NAME}'")
            if not cur.fetchone():
                logger.error(f"'{TABLE_NAME}' 테이블이 존재하지 않습니다. 데이터베이스 스키마를 확인하세요.")
                return
            
            # 거래 데이터 저장
            inserted_count = 0
            for transaction in transactions:
                try:
                    # 중복 확인
                    cur.execute(
                        f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE transaction_id = ?",
                        (transaction['transaction_id'],)
                    )
                    if cur.fetchone()[0] > 0:
                        logger.debug(f"중복 거래 건너뛰기: {transaction['transaction_id']}")
                        continue
                    
                    # 거래 데이터 삽입
                    cur.execute(
                        f"""
                        INSERT INTO {TABLE_NAME} (
                            transaction_id, transaction_date, description, amount, 
                            transaction_type, category, payment_method, source, 
                            account_type, memo, is_excluded
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            transaction['transaction_id'],
                            transaction['transaction_date'],
                            transaction['description'],
                            float(transaction['amount']),
                            transaction['transaction_type'],
                            transaction['category'],
                            transaction['payment_method'],
                            transaction['source'],
                            transaction['account_type'],
                            transaction['memo'],
                            1 if transaction['is_excluded'] else 0
                        )
                    )
                    inserted_count += 1
                    
                except Exception as e:
                    logger.error(f"거래 저장 중 오류 발생: {str(e)}, 거래: {transaction['transaction_id']}")
            
            con.commit()
            logger.info(f"작업 완료! {inserted_count}개의 새로운 데이터가 추가되었습니다.")
            
    except FileNotFoundError:
        logger.error(f"오류: 파일을 찾을 수 없습니다. '{XLSX_PATH}'")
    except ValueError as e:
        logger.error(f"오류: {str(e)}")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")

if __name__ == '__main__':
    ingest_data()