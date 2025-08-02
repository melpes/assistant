# -*- coding: utf-8 -*-
"""
TossBankCardIngester 클래스 정의

토스뱅크 카드 이용내역서(XLSX)를 처리하는 데이터 수집기입니다.
"""

import os
import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import uuid

from .base_ingester import BaseIngester

# 로깅 설정
logger = logging.getLogger(__name__)

class TossBankCardIngester(BaseIngester):
    """
    토스뱅크 카드 이용내역서 데이터 수집기
    
    토스뱅크 카드 이용내역서(XLSX)에서 거래 데이터를 추출하고 정규화합니다.
    취소 거래를 처리하고 중복을 방지합니다.
    """
    
    def __init__(self, name: str = "토스뱅크 카드", description: str = "토스뱅크 카드 이용내역서 데이터 수집기"):
        """
        토스뱅크 카드 수집기 초기화
        
        Args:
            name: 수집기 이름 (기본값: "토스뱅크 카드")
            description: 수집기 설명 (기본값: "토스뱅크 카드 이용내역서 데이터 수집기")
        """
        super().__init__(name, description)
        self.skiprows = 14  # 토스뱅크 카드 이용내역서 헤더 건너뛰기
    
    def validate_file(self, file_path: str) -> bool:
        """
        토스뱅크 카드 이용내역서 파일의 유효성을 검증합니다.
        
        Args:
            file_path: 검증할 파일 경로
            
        Returns:
            bool: 파일이 유효하면 True, 그렇지 않으면 False
        """
        # 파일 확장자 확인
        if not file_path.lower().endswith('.xlsx'):
            logger.warning(f"지원하지 않는 파일 형식입니다: {file_path}")
            return False
        
        try:
            # 파일 내용 확인 (필수 열이 있는지)
            df = pd.read_excel(file_path, skiprows=self.skiprows, nrows=1)
            required_columns = ['매출일자', '가맹점명', '매출금액', '취소금액', '승인번호']
            
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"필수 열이 누락되었습니다: {col}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"파일 검증 중 오류 발생: {str(e)}")
            return False
    
    def extract_transactions(self, file_path: str) -> List[Dict[str, Any]]:
        """
        토스뱅크 카드 이용내역서에서 거래 데이터를 추출합니다.
        
        Args:
            file_path: 거래 데이터가 포함된 파일 경로
            
        Returns:
            List[Dict[str, Any]]: 추출된 거래 데이터 목록
        """
        logger.info(f"토스뱅크 카드 이용내역서에서 데이터 추출 시작: {file_path}")
        
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(file_path, skiprows=self.skiprows)
            
            # 데이터프레임을 딕셔너리 리스트로 변환
            transactions = []
            
            for _, row in df.iterrows():
                try:
                    # 매출금액과 취소금액을 숫자로 변환 (NaN은 0으로 처리)
                    sales_amount = pd.to_numeric(row['매출금액'], errors='coerce')
                    sales_amount = 0 if pd.isna(sales_amount) else sales_amount
                    
                    cancel_amount = pd.to_numeric(row['취소금액'], errors='coerce')
                    cancel_amount = 0 if pd.isna(cancel_amount) else cancel_amount
                    
                    # 최종 금액 계산 (매출금액 - 취소금액)
                    final_amount = sales_amount - cancel_amount
                    
                    # 거래 데이터 생성
                    transaction = {
                        'approval_number': str(row['승인번호']),
                        'transaction_date': row['매출일자'],
                        'description': row['가맹점명'],
                        'sales_amount': sales_amount,
                        'cancel_amount': cancel_amount,
                        'final_amount': final_amount,
                        'card_number': str(row.get('카드번호', '')),
                        'installment': row.get('할부', '일시불'),
                        'approval_time': row.get('승인시간', ''),
                        'category': row.get('이용구분', '')
                    }
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    logger.warning(f"행 처리 중 오류 발생: {str(e)}, 행: {row}")
            
            logger.info(f"{len(transactions)}개의 거래 데이터 추출 완료")
            return transactions
            
        except Exception as e:
            error_msg = f"데이터 추출 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        추출된 원시 데이터를 표준 형식으로 정규화합니다.
        
        Args:
            raw_data: 추출된 원시 거래 데이터
            
        Returns:
            List[Dict[str, Any]]: 정규화된 거래 데이터 목록
        """
        logger.info("토스뱅크 카드 거래 데이터 정규화 시작")
        
        normalized_transactions = []
        
        for transaction in raw_data:
            try:
                # 최종 금액이 0 이하인 거래는 제외 (취소 완료된 거래)
                if transaction['final_amount'] <= 0:
                    logger.debug(f"최종 금액이 0 이하인 거래 제외: {transaction['description']}, {transaction['approval_number']}")
                    continue
                
                # 거래 날짜 처리
                if isinstance(transaction['transaction_date'], str):
                    try:
                        transaction_date = datetime.strptime(transaction['transaction_date'], '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            transaction_date = datetime.strptime(transaction['transaction_date'], '%Y%m%d').date()
                        except ValueError:
                            logger.warning(f"날짜 형식 오류: {transaction['transaction_date']}")
                            continue
                else:
                    try:
                        transaction_date = pd.to_datetime(transaction['transaction_date']).date()
                    except Exception:
                        logger.warning(f"날짜 변환 오류: {transaction['transaction_date']}")
                        continue
                
                # 거래 ID 생성 (승인번호 + 날짜 조합으로 고유성 보장)
                transaction_id = f"TOSSCARD_{transaction['approval_number']}_{transaction_date.strftime('%Y%m%d')}"
                
                # 정규화된 거래 데이터 생성
                normalized_transaction = {
                    'transaction_id': transaction_id,
                    'transaction_date': transaction_date.strftime('%Y-%m-%d'),
                    'description': transaction['description'],
                    'amount': Decimal(str(transaction['final_amount'])),
                    'transaction_type': 'expense',  # 카드 이용내역은 항상 지출
                    'category': self._determine_category(transaction),
                    'payment_method': '카드결제',
                    'source': 'toss_bank_card',
                    'account_type': '토스뱅크 카드',
                    'memo': f"승인번호: {transaction['approval_number']}",
                    'is_excluded': False,
                    'metadata': {
                        'approval_number': transaction['approval_number'],
                        'sales_amount': float(transaction['sales_amount']),
                        'cancel_amount': float(transaction['cancel_amount']),
                        'card_number': transaction.get('card_number', ''),
                        'installment': transaction.get('installment', '일시불'),
                        'approval_time': transaction.get('approval_time', '')
                    }
                }
                
                # 데이터 유효성 검증
                if self.validate_data(normalized_transaction):
                    normalized_transactions.append(normalized_transaction)
                
            except Exception as e:
                logger.warning(f"거래 정규화 중 오류 발생: {e}, 거래: {transaction}")
        
        logger.info(f"{len(normalized_transactions)}개의 거래 데이터 정규화 완료")
        return normalized_transactions
    
    def _determine_category(self, transaction: Dict[str, Any]) -> str:
        """
        거래 정보를 기반으로 카테고리를 결정합니다.
        
        Args:
            transaction: 거래 데이터
            
        Returns:
            str: 결정된 카테고리
        """
        # 기본 카테고리 매핑 (가맹점명 기반)
        description = transaction['description'].lower()
        
        # 간단한 카테고리 매핑 규칙
        if any(keyword in description for keyword in ['마트', '슈퍼', '편의점', 'gs', 'cu', '세븐일레븐']):
            return '생활용품'
        elif any(keyword in description for keyword in ['카페', '스타벅스', '커피', '베이커리', '디저트']):
            return '식비'
        elif any(keyword in description for keyword in ['식당', '레스토랑', '배달', '푸드', '치킨', '피자', '맥도날드', '버거', '김밥', '분식']):
            return '식비'
        elif any(keyword in description for keyword in ['지하철', '버스', '택시', '교통', '철도', '기차']):
            return '교통비'
        elif any(keyword in description for keyword in ['영화', '공연', '티켓', '극장', 'cgv', '메가박스']):
            return '문화/오락'
        elif any(keyword in description for keyword in ['병원', '약국', '의원', '치과', '한의원']):
            return '의료비'
        elif any(keyword in description for keyword in ['통신', '핸드폰', '모바일', 'kt', 'skt', 'lg']):
            return '통신비'
        elif any(keyword in description for keyword in ['전기', '수도', '가스', '관리비', '공과금']):
            return '공과금'
        elif any(keyword in description for keyword in ['옷', '의류', '패션', '신발', '악세사리', '유니클로', '자라', '무신사']):
            return '의류/패션'
        elif any(keyword in description for keyword in ['인출', 'atm', '출금']):
            return '현금인출'
        elif any(keyword in description for keyword in ['해외', '외국', 'global']):
            return '해외결제'
        elif any(keyword in description for keyword in ['토스', '페이', '간편결제', '네이버페이', '카카오페이']):
            return '간편결제'
        else:
            return '기타'
    
    def get_supported_file_types(self) -> List[str]:
        """
        지원하는 파일 유형 목록을 반환합니다.
        
        Returns:
            List[str]: 지원하는 파일 확장자 목록
        """
        return ['xlsx']
    
    def get_required_fields(self) -> List[str]:
        """
        필수 데이터 필드 목록을 반환합니다.
        
        Returns:
            List[str]: 필수 필드 목록
        """
        return [
            'transaction_id',
            'transaction_date',
            'description',
            'amount',
            'transaction_type',
            'source'
        ]