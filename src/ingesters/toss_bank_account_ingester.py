# -*- coding: utf-8 -*-
"""
TossBankAccountIngester 클래스 정의

토스뱅크 계좌 거래내역(CSV)을 처리하는 데이터 수집기입니다.
수입/지출 구분 로직 개선 및 필터링 규칙을 적용합니다.
"""

import os
import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Set, Tuple
import logging
from pathlib import Path
import uuid
import re
import hashlib
import json
import time

from .base_ingester import BaseIngester

# 로깅 설정
logger = logging.getLogger(__name__)

class TossBankAccountIngester(BaseIngester):
    """
    토스뱅크 계좌 거래내역 데이터 수집기
    
    토스뱅크 계좌 거래내역(CSV)에서 거래 데이터를 추출하고 정규화합니다.
    수입/지출 구분 및 필터링 규칙을 적용합니다.
    """
    
    def __init__(self, name: str = "토스뱅크 계좌", description: str = "토스뱅크 계좌 거래내역 데이터 수집기"):
        """
        토스뱅크 계좌 수집기 초기화
        
        Args:
            name: 수집기 이름 (기본값: "토스뱅크 계좌")
            description: 수집기 설명 (기본값: "토스뱅크 계좌 거래내역 데이터 수집기")
        """
        super().__init__(name, description)
        self.skiprows = 8  # 토스뱅크 계좌 거래내역 CSV 헤더 건너뛰기
        
        # 수입 제외 패턴 (자금 이동, 임시 보관 등)
        self.income_exclude_patterns = [
            r'카드잔액\s*자동충전',
            r'내계좌\s*이체',
            r'계좌이체',
            r'이체',
            r'충전',
            r'환불',
            r'반환',
            r'카드잔액',
            r'자동충전'
        ]
        
        # 캐시백, 이자, 프로모션 패턴 (실제 지출에서 제외)
        self.cashback_patterns = [
            r'캐시백',
            r'이자',
            r'프로모션',
            r'적립',
            r'리워드',
            r'보너스',
            r'프로모션입금'
        ]
        
        # 수입 유형 패턴
        self.income_type_patterns = {
            '급여': [r'급여', r'월급', r'상여금', r'연봉', r'인건비', r'수당', r'주급'],
            '용돈': [r'용돈', r'선물', r'축하금', r'생일', r'대회', r'뒷풀이', r'간식'],
            '이자': [r'이자', r'배당', r'수익', r'예금이자', r'통장 이자', r'이자입금'],
            '환급': [r'환급', r'세금', r'공제', r'환급금', r'보험금', r'취소'],
            '기타수입': []  # 기본값
        }
        
        # 거래 유형별 카테고리 매핑
        self.transaction_type_categories = {
            '체크카드결제': '체크카드결제',
            'ATM출금': 'ATM출금',
            '자동이체': '자동이체',
            '계좌이체': '계좌이체',
            '토스페이': '간편결제',
            '자동환전': '해외결제',
            '카드결제': '카드결제',
            '계좌결제': '계좌결제',
            '계좌출금': '계좌출금',
            '입금': '입금',
            '출금': '출금',
            '프로모션입금': '프로모션입금'
        }
        
        # 지출 카테고리 패턴
        self.expense_category_patterns = {
            '식비': [
                r'맥도날드', r'버거킹', r'롯데리아', r'써브웨이', r'한솥', r'밥버거', r'맘스터치', 
                r'식당', r'치킨', r'피자', r'배달', r'음식', r'버거', r'떡볶이', r'파스타', 
                r'중국집', r'우동', r'갈비', r'기린', r'푸드', r'밥은', r'유부', r'쪼매매운떡볶이',
                r'봉구스', r'정직유부', r'모두의 유부'
            ],
            '카페/음료': [
                r'카페', r'스타벅스', r'커피', r'음료', r'빽다방', r'베이커리', r'디저트',
                r'떼루와', r'유니온커피'
            ],
            '생활용품/식료품': [
                r'마트', r'슈퍼', r'편의점', r'이마트', r'롯데마트', r'cu', r'gs25', r'세븐일레븐',
                r'구시아푸드마켓', r'지에스25'
            ],
            '교통비': [
                r'택시', r'교통카드', r'버스', r'지하철', r'주유', r'카카오T', r'철도', r'기차',
                r'서울시설공단'
            ],
            '문화/오락': [
                r'영화', r'게임', r'오락', r'문화', r'cgv', r'pc', r'보드게임', r'디스코드', 
                r'discord', r'메가박스', r'런PC', r'여기PC', r'시스포유', r'정글비'
            ],
            '의료비': [
                r'병원', r'약국', r'의료', r'치료', r'의원', r'치과', r'한의원', r'수암약국'
            ],
            '통신비': [
                r'통신', r'휴대폰', r'kt', r'skt', r'lg', r'유튜브', r'모바일'
            ],
            '공과금': [
                r'전기', r'가스', r'수도', r'관리비'
            ],
            '의류/패션': [
                r'옷', r'의류', r'신발', r'패션', r'맨즈코리아', r'유니클로', r'자라', r'무신사'
            ],
            '온라인쇼핑': [
                r'쿠팡', r'온라인쇼핑', r'네이버페이', r'구글페이먼트', r'쿠페이'
            ],
            '현금인출': [
                r'atm현금', r'atm출금', r'인출', r'출금'
            ],
            '해외결제': [
                r'자동환전', r'환전', r'해외', r'외국', r'global', r'dlsite', r'discord', r'cursor'
            ],
            '간편결제': [
                r'카카오', r'토스페이', r'네이버페이', r'카카오페이', r'간편결제'
            ],
            '구독서비스': [
                r'유튜브', r'넷플릭스', r'왓챠', r'디즈니', r'애플', r'구글', r'멤버십', r'구독',
                r'유튜브 뮤직', r'제미나이', r'레진'
            ]
        }
        
        # 배치 처리 크기
        self.batch_size = 1000
        
        # 성능 최적화를 위한 캐시
        self._category_cache = {}
        self._payment_method_cache = {}
    
    def validate_file(self, file_path: str) -> bool:
        """
        토스뱅크 계좌 거래내역 파일의 유효성을 검증합니다.
        
        Args:
            file_path: 검증할 파일 경로
            
        Returns:
            bool: 파일이 유효하면 True, 그렇지 않으면 False
        """
        # 파일 확장자 확인
        if not file_path.lower().endswith('.csv'):
            logger.warning(f"지원하지 않는 파일 형식입니다: {file_path}")
            return False
        
        try:
            # 파일 내용 확인 (필수 열이 있는지)
            df = pd.read_csv(file_path, skiprows=self.skiprows, encoding='utf-8', nrows=1)
            required_columns = ['거래 일시', '적요', '거래 유형', '거래 금액', '거래 후 잔액']
            
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
        토스뱅크 계좌 거래내역에서 거래 데이터를 추출합니다.
        
        Args:
            file_path: 거래 데이터가 포함된 파일 경로
            
        Returns:
            List[Dict[str, Any]]: 추출된 거래 데이터 목록
        """
        logger.info(f"토스뱅크 계좌 거래내역에서 데이터 추출 시작: {file_path}")
        
        try:
            start_time = time.time()
            
            # CSV 파일 읽기 (청크 단위로 처리)
            transactions = []
            
            # 전체 행 수 확인 (성능 최적화를 위해 샘플링)
            with open(file_path, 'r', encoding='utf-8') as f:
                # 첫 100줄만 읽어서 헤더 크기 확인
                for i, _ in enumerate(f):
                    if i >= 100:
                        break
            
            # 청크 단위로 데이터 처리
            chunks = pd.read_csv(file_path, skiprows=self.skiprows, encoding='utf-8', chunksize=self.batch_size)
            
            total_chunks = 0
            processed_rows = 0
            
            for chunk_idx, chunk in enumerate(chunks):
                total_chunks += 1
                chunk = chunk.dropna(subset=['거래 일시'])  # 빈 행 제거
                processed_rows += len(chunk)
                
                # 벡터화된 연산으로 성능 개선
                # 거래 일시 처리
                dates = pd.to_datetime(chunk['거래 일시']).dt.date
                
                # 거래 금액 처리
                amounts = chunk['거래 금액'].astype(str).str.replace(',', '').str.replace('"', '')
                amounts = pd.to_numeric(amounts, errors='coerce')
                
                # 잔액 처리
                balances = chunk['거래 후 잔액'].astype(str).str.replace(',', '').str.replace('"', '')
                balances = pd.to_numeric(balances, errors='coerce').fillna(0)
                
                # 지출/수입 구분
                is_expenses = amounts < 0
                
                # 금액 절대값
                abs_amounts = amounts.abs()
                
                # 각 행별로 처리
                for i, row in chunk.iterrows():
                    try:
                        idx = chunk.index.get_loc(i)
                        
                        # 거래 일시
                        transaction_date = dates.iloc[idx]
                        
                        # 금액
                        amount = abs_amounts.iloc[idx]
                        if pd.isna(amount):
                            logger.warning(f"금액 변환 오류: {row['거래 금액']}")
                            continue
                        
                        # 잔액
                        balance = balances.iloc[idx]
                        
                        # 거래 유형 및 설명
                        description = str(row['적요'])
                        transaction_type = str(row['거래 유형'])
                        
                        # 거래 기관 및 계좌번호
                        institution = str(row.get('거래 기관', '')) if pd.notna(row.get('거래 기관', '')) else ''
                        account_number = str(row.get('계좌번호', '')) if pd.notna(row.get('계좌번호', '')) else ''
                        
                        # 메모
                        memo = str(row.get('메모', '')) if pd.notna(row.get('메모', '')) else ''
                        
                        # 지출/수입 구분
                        is_expense = is_expenses.iloc[idx]
                        
                        # 캐시백, 이자 등 여부 확인 (캐싱 적용)
                        cache_key = f"{description}_{transaction_type}_{memo}"
                        if cache_key in self._category_cache:
                            is_cashback = self._category_cache[cache_key]['is_cashback']
                        else:
                            is_cashback = (
                                any(re.search(pattern, description, re.IGNORECASE) for pattern in self.cashback_patterns) or
                                any(re.search(pattern, transaction_type, re.IGNORECASE) for pattern in self.cashback_patterns) or
                                any(re.search(pattern, memo, re.IGNORECASE) for pattern in self.cashback_patterns) or
                                transaction_type == '프로모션입금'
                            )
                            self._category_cache[cache_key] = {'is_cashback': is_cashback}
                        
                        # 거래 데이터 생성
                        transaction = {
                            'transaction_date': transaction_date,
                            'description': description,
                            'transaction_type': transaction_type,
                            'amount': float(amount),
                            'is_expense': is_expense,
                            'is_cashback': is_cashback,
                            'institution': institution,
                            'account_number': account_number,
                            'balance': float(balance),
                            'memo': memo,
                            'raw_data': {
                                '거래 일시': str(row['거래 일시']),
                                '적요': description,
                                '거래 유형': transaction_type,
                                '거래 금액': str(row['거래 금액']),
                                '거래 후 잔액': str(row['거래 후 잔액']),
                                '거래 기관': institution,
                                '계좌번호': account_number,
                                '메모': memo
                            }
                        }
                        
                        transactions.append(transaction)
                        
                    except Exception as e:
                        logger.warning(f"행 처리 중 오류 발생: {str(e)}, 행: {row}")
                
                # 메모리 최적화를 위해 주기적으로 GC 호출
                if chunk_idx % 10 == 0 and chunk_idx > 0:
                    import gc
                    gc.collect()
                
                # 진행 상황 로깅
                if chunk_idx % 5 == 0 or chunk_idx == total_chunks - 1:
                    elapsed = time.time() - start_time
                    logger.info(f"청크 {chunk_idx+1} 처리 완료: {processed_rows}개 행 처리 (경과 시간: {elapsed:.2f}초)")
            
            elapsed_time = time.time() - start_time
            logger.info(f"{len(transactions)}개의 거래 데이터 추출 완료 (총 소요 시간: {elapsed_time:.2f}초)")
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
        logger.info("토스뱅크 계좌 거래 데이터 정규화 시작")
        start_time = time.time()
        
        normalized_transactions = []
        
        # 중복 거래 ID 방지를 위한 집합
        transaction_ids = set()
        
        # 성능 최적화를 위한 배치 처리
        batch_size = 1000
        total_batches = (len(raw_data) + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(raw_data))
            batch_data = raw_data[start_idx:end_idx]
            
            batch_normalized = []
            
            for transaction in batch_data:
                try:
                    # 거래 날짜
                    transaction_date = transaction['transaction_date']
                    
                    # 거래 ID 생성 (날짜 + 금액 + 설명 + 잔액 해시로 고유성 보장)
                    hash_input = f"{transaction_date.strftime('%Y%m%d')}_{transaction['amount']:.2f}_{transaction['description']}_{transaction['balance']:.2f}"
                    hash_value = hashlib.md5(hash_input.encode('utf-8')).hexdigest()[:8]
                    transaction_id = f"TOSSACC_{transaction_date.strftime('%Y%m%d')}_{int(transaction['amount'])}_{hash_value}"
                    
                    # 중복 ID 확인 및 처리
                    if transaction_id in transaction_ids:
                        # 중복 ID가 있으면 해시에 추가 정보 포함
                        hash_input = f"{hash_input}_{len(transaction_ids)}"
                        hash_value = hashlib.md5(hash_input.encode('utf-8')).hexdigest()[:8]
                        transaction_id = f"TOSSACC_{transaction_date.strftime('%Y%m%d')}_{int(transaction['amount'])}_{hash_value}"
                    
                    transaction_ids.add(transaction_id)
                    
                    # 거래 유형 결정 (expense 또는 income)
                    transaction_type = 'expense' if transaction['is_expense'] else 'income'
                    
                    # 결제 방식 결정 (캐싱 적용)
                    cache_key = f"{transaction['description']}_{transaction['transaction_type']}"
                    if cache_key in self._payment_method_cache:
                        payment_method = self._payment_method_cache[cache_key]
                    else:
                        payment_method = self._determine_payment_method(transaction['description'], transaction['transaction_type'])
                        self._payment_method_cache[cache_key] = payment_method
                    
                    # 카테고리 결정 (캐싱 적용)
                    if cache_key in self._category_cache and 'category' in self._category_cache[cache_key]:
                        category = self._category_cache[cache_key]['category']
                    else:
                        category = self._categorize_transaction(
                            transaction['description'], 
                            transaction['amount'], 
                            transaction_type,
                            transaction['transaction_type'],
                            transaction.get('memo', '')
                        )
                        if cache_key not in self._category_cache:
                            self._category_cache[cache_key] = {}
                        self._category_cache[cache_key]['category'] = category
                    
                    # 수입 제외 여부 결정 (자금 이동, 임시 보관 등)
                    is_excluded = False
                    
                    # 캐시백, 이자 등은 분석에서 제외
                    if transaction['is_cashback']:
                        is_excluded = True
                    
                    # 수입인 경우 제외 패턴 확인
                    if transaction_type == 'income':
                        if cache_key in self._category_cache and 'is_excluded' in self._category_cache[cache_key]:
                            is_excluded = self._category_cache[cache_key]['is_excluded']
                        else:
                            is_excluded_income = self._is_income_excluded(transaction['description'], transaction['transaction_type'])
                            is_excluded = is_excluded or is_excluded_income
                            if cache_key not in self._category_cache:
                                self._category_cache[cache_key] = {}
                            self._category_cache[cache_key]['is_excluded'] = is_excluded
                    
                    # 메모 생성
                    memo_parts = []
                    if transaction['transaction_type']:
                        memo_parts.append(transaction['transaction_type'])
                    if transaction['institution']:
                        memo_parts.append(transaction['institution'])
                    if transaction['balance'] > 0:
                        memo_parts.append(f"잔액: {int(transaction['balance']):,}원")
                    if transaction.get('memo'):
                        memo_parts.append(transaction['memo'])
                    
                    memo = ' | '.join(memo_parts)
                    
                    # 거래 상세 정보 추출
                    transaction_detail = self._get_transaction_detail(transaction)
                    
                    # 메타데이터 생성
                    metadata = {
                        'institution': transaction['institution'],
                        'account_number': transaction['account_number'],
                        'balance': float(transaction['balance']),
                        'original_type': transaction['transaction_type'],
                        'transaction_detail': transaction_detail
                    }
                    
                    # 정규화된 거래 데이터 생성
                    normalized_transaction = {
                        'transaction_id': transaction_id,
                        'transaction_date': transaction_date.strftime('%Y-%m-%d'),
                        'description': transaction['description'],
                        'amount': Decimal(str(transaction['amount'])),
                        'transaction_type': transaction_type,
                        'category': category,
                        'payment_method': payment_method,
                        'source': 'toss_bank_account',
                        'account_type': '토스뱅크 계좌',
                        'memo': memo,
                        'is_excluded': is_excluded,
                        'metadata': metadata
                    }
                    
                    # 데이터 유효성 검증
                    if self.validate_data(normalized_transaction):
                        batch_normalized.append(normalized_transaction)
                    
                except Exception as e:
                    logger.warning(f"거래 정규화 중 오류 발생: {e}, 거래: {transaction}")
            
            # 배치 처리 결과 추가
            normalized_transactions.extend(batch_normalized)
            
            # 진행 상황 로깅
            if batch_idx % 5 == 0 or batch_idx == total_batches - 1:
                elapsed = time.time() - start_time
                logger.info(f"배치 {batch_idx+1}/{total_batches} 정규화 완료: "
                           f"{len(normalized_transactions)}/{len(raw_data)} 처리 (경과 시간: {elapsed:.2f}초)")
            
            # 메모리 최적화
            if batch_idx % 10 == 0 and batch_idx > 0:
                import gc
                gc.collect()
        
        # 통계 정보 로깅
        income_count = sum(1 for t in normalized_transactions if t['transaction_type'] == 'income')
        expense_count = sum(1 for t in normalized_transactions if t['transaction_type'] == 'expense')
        excluded_count = sum(1 for t in normalized_transactions if t['is_excluded'])
        
        logger.info(f"정규화 완료: 수입 {income_count}건, 지출 {expense_count}건, 분석 제외 {excluded_count}건")
        
        # 카테고리별 통계
        categories = {}
        for t in normalized_transactions:
            cat = t['category']
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        logger.info("카테고리별 거래 수:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  - {category}: {count}개")
        
        elapsed_time = time.time() - start_time
        logger.info(f"{len(normalized_transactions)}개의 거래 데이터 정규화 완료 (총 소요 시간: {elapsed_time:.2f}초)")
        return normalized_transactions
    
    def _determine_payment_method(self, description: str, transaction_type: str) -> str:
        """
        거래 설명과 거래 유형을 기반으로 결제 방식을 결정합니다.
        
        Args:
            description: 거래 설명
            transaction_type: 거래 유형
            
        Returns:
            str: 결정된 결제 방식
        """
        description = str(description).lower()
        transaction_type = str(transaction_type).lower()
        
        # 거래 유형별 결제 방식 매핑 (우선순위 순)
        
        # 카드 관련
        if '체크카드결제' in transaction_type:
            return '체크카드결제'
        elif '카드결제' in transaction_type:
            return '카드결제'
        
        # ATM 관련
        elif 'atm출금' in transaction_type or 'atm현금' in description:
            return 'ATM출금'
        
        # 해외 결제
        elif '자동환전' in description or '자동환전' in transaction_type:
            return '해외결제'
        
        # 간편결제
        elif '토스페이' in description:
            return '토스페이'
        elif '네이버페이' in description:
            return '네이버페이'
        elif '카카오페이' in description:
            return '카카오페이'
        elif '페이' in description and ('간편' in description or '결제' in description):
            return '간편결제'
        
        # 자동이체
        elif '자동이체' in description or '자동이체' in transaction_type or '정기이체' in description:
            return '자동이체'
        
        # 이체 관련
        elif '이체' in transaction_type or '이체' in description:
            if '오픈뱅킹' in description:
                return '오픈뱅킹'
            elif '펌뱅킹' in description:
                return '펌뱅킹'
            else:
                return '계좌이체'
        
        # 결제 관련
        elif '결제' in description:
            return '계좌결제'
        
        # 입출금
        elif '출금' in transaction_type:
            return '계좌출금'
        elif '입금' in transaction_type:
            if '프로모션' in transaction_type:
                return '프로모션입금'
            elif '이자' in transaction_type:
                return '이자입금'
            else:
                return '계좌입금'
        
        # 기타 거래 유형
        else:
            return transaction_type
    
    def _categorize_transaction(self, description: str, amount: float, transaction_type: str, original_type: str, memo: str = '') -> str:
        """
        거래 내역을 기반으로 카테고리를 자동 분류합니다.
        
        Args:
            description: 거래 설명
            amount: 거래 금액
            transaction_type: 거래 유형 (expense/income)
            original_type: 원본 거래 유형
            memo: 메모 (선택)
            
        Returns:
            str: 결정된 카테고리
        """
        description = str(description).lower()
        original_type = str(original_type).lower()
        memo = str(memo).lower()
        
        # 수입 거래인 경우 수입 유형 분류
        if transaction_type == 'income':
            return self._categorize_income(description, amount, memo)
        
        # 지출 카테고리 매핑 (패턴 기반)
        for category, patterns in self.expense_category_patterns.items():
            for pattern in patterns:
                if (re.search(pattern, description, re.IGNORECASE) or 
                    re.search(pattern, memo, re.IGNORECASE)):
                    return category
        
        # 거래 유형 기반 카테고리
        if original_type in ['체크카드결제', '카드결제']:
            return '카드결제'
        elif original_type in ['자동이체', '정기이체']:
            return '자동이체'
        elif original_type in ['계좌이체', '이체']:
            return '계좌이체'
        elif original_type in ['출금']:
            return '계좌출금'
        elif original_type in ['입금']:
            return '입금'
        elif original_type in ['프로모션입금']:
            return '프로모션입금'
        
        # 금액 기반 추정
        if amount >= 100000:  # 10만원 이상
            return '대형결제'
        elif amount >= 50000:  # 5만원 이상
            return '중형결제'
        elif amount >= 10000:  # 1만원 이상
            return '소형결제'
        
        return '기타'
    
    def _categorize_income(self, description: str, amount: float, memo: str = '') -> str:
        """
        수입 거래를 카테고리로 분류합니다.
        
        Args:
            description: 거래 설명
            amount: 거래 금액
            memo: 메모 (선택)
            
        Returns:
            str: 수입 카테고리
        """
        description = str(description).lower()
        memo = str(memo).lower()
        
        # 특수 케이스 처리
        if '프로모션입금' in description or '캐시백' in description:
            return '프로모션/캐시백'
        
        if '이자' in description or '이자입금' in description:
            return '이자수입'
        
        # 수입 유형 패턴 매칭 (설명 기준)
        for category, patterns in self.income_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    return category
        
        # 수입 유형 패턴 매칭 (메모 기준)
        if memo:
            for category, patterns in self.income_type_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, memo, re.IGNORECASE):
                        return category
        
        # 금액 기반 추정 (예: 큰 금액은 급여일 가능성이 높음)
        if amount >= 1000000:  # 100만원 이상
            return '급여'
        elif 500000 <= amount < 1000000:  # 50만원 ~ 100만원
            return '대형수입'
        elif 100000 <= amount < 500000:  # 10만원 ~ 50만원
            return '중형수입'
        elif 10000 <= amount < 100000:  # 1만원 ~ 10만원
            return '소형수입'
        else:  # 1만원 미만
            return '소액수입'
    
    def _is_income_excluded(self, description: str, transaction_type: str, memo: str = '') -> bool:
        """
        수입 거래가 제외 대상인지 확인합니다.
        
        Args:
            description: 거래 설명
            transaction_type: 거래 유형
            memo: 메모 (선택)
            
        Returns:
            bool: 제외 대상이면 True, 그렇지 않으면 False
        """
        # 자금 이동, 임시 보관 등은 수입에서 제외
        for pattern in self.income_exclude_patterns:
            if (re.search(pattern, description, re.IGNORECASE) or 
                re.search(pattern, transaction_type, re.IGNORECASE) or 
                (memo and re.search(pattern, memo, re.IGNORECASE))):
                return True
        
        # 특정 거래 유형은 항상 제외
        if transaction_type in ['프로모션입금', '카드 캐시백']:
            return True
        
        # 특정 키워드가 포함된 경우 제외
        exclude_keywords = ['자동충전', '카드잔액', '취소', '환불', '반환', '카드 캐시백']
        for keyword in exclude_keywords:
            if (keyword in description.lower() or 
                keyword in transaction_type.lower() or 
                (memo and keyword in memo.lower())):
                return True
        
        # 같은 계좌 간 이체는 제외 (내 계좌 간 이동)
        if '강태희' in description and ('입금' in transaction_type or '이체' in description):
            return True
        
        return False
    
    def _get_transaction_detail(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        거래의 상세 정보를 추출합니다.
        
        Args:
            transaction: 거래 데이터
            
        Returns:
            Dict[str, Any]: 거래 상세 정보
        """
        # 거래 유형별 상세 정보 추출
        detail = {}
        
        # 거래 유형 분석
        transaction_type = transaction['transaction_type'].lower()
        description = transaction['description'].lower()
        memo = transaction.get('memo', '').lower()
        
        # 거래 하위 유형 결정
        detail['transaction_subtype'] = self._determine_transaction_subtype(description, transaction_type)
        
        # 이체 관련 정보
        if '이체' in transaction_type or '이체' in description:
            # 송금인/수취인 추출 시도
            if '→' in description:
                parts = description.split('→')
                if len(parts) >= 2:
                    detail['sender'] = parts[0].strip()
                    detail['receiver'] = parts[1].strip()
            elif '받은' in description:
                detail['direction'] = '입금'
            elif '보낸' in description:
                detail['direction'] = '출금'
            
            # 이체 목적 추출 (메모에서)
            if memo and memo != '':
                detail['transfer_purpose'] = memo
        
        # 카드 결제 정보
        elif '카드' in transaction_type or '카드' in description:
            # 카드번호 추출 시도
            card_number_match = re.search(r'\d{4}-\d{4}-\d{4}-\d{4}', description)
            if card_number_match:
                detail['card_number'] = card_number_match.group(0)
            
            # 결제 가맹점 정보
            if '(' in description and ')' in description:
                start = description.find('(') + 1
                end = description.find(')', start)
                if start < end:
                    detail['merchant'] = description[start:end]
        
        # 자동이체 정보
        elif '자동이체' in transaction_type or '자동이체' in description:
            # 자동이체 대상 추출 시도
            if '(' in description and ')' in description:
                start = description.find('(') + 1
                end = description.find(')', start)
                if start < end:
                    detail['auto_payment_target'] = description[start:end]
            
            # 정기성 여부
            detail['is_recurring'] = True
        
        # 현금 인출 정보
        elif 'atm' in transaction_type or 'atm' in description:
            # ATM 위치 추출 시도
            if 'atm' in description and '(' in description:
                start = description.find('(') + 1
                end = description.find(')', start)
                if start < end:
                    detail['atm_location'] = description[start:end]
        
        # 해외 결제 정보
        elif '자동환전' in description or '환전' in transaction_type:
            # 통화 및 가맹점 추출
            currency_match = re.search(r'\((.*?)\)', description)
            if currency_match:
                detail['currency'] = currency_match.group(1)
            
            # 가맹점 추출
            merchant_match = re.search(r'자동환전.*?\((.*?)\)(.*)', description)
            if merchant_match and len(merchant_match.groups()) > 1:
                detail['merchant'] = merchant_match.group(2).strip()
        
        # 프로모션/캐시백 정보
        elif '프로모션' in transaction_type or '캐시백' in description:
            detail['promotion_type'] = '캐시백' if '캐시백' in description else '프로모션'
        
        # 금액 범주화
        amount = transaction['amount']
        if amount >= 1000000:  # 100만원 이상
            detail['amount_category'] = '대액'
        elif amount >= 100000:  # 10만원 이상
            detail['amount_category'] = '고액'
        elif amount >= 10000:  # 1만원 이상
            detail['amount_category'] = '중액'
        else:
            detail['amount_category'] = '소액'
        
        return detail
    
    def _determine_transaction_subtype(self, description: str, transaction_type: str) -> str:
        """
        거래 설명과 거래 유형을 기반으로 거래 하위 유형을 결정합니다.
        
        Args:
            description: 거래 설명
            transaction_type: 거래 유형
            
        Returns:
            str: 결정된 거래 하위 유형
        """
        # 카드 관련
        if '체크카드결제' in transaction_type:
            return '체크카드결제'
        elif '카드결제' in transaction_type:
            return '신용카드결제'
        elif '카드 캐시백' in description or '카드 캐시백' in transaction_type:
            return '카드캐시백'
        
        # 현금 인출
        elif 'atm출금' in transaction_type or 'atm현금' in description:
            return '현금인출'
        
        # 해외 결제
        elif '자동환전' in description:
            return '해외결제'
        
        # 간편결제
        elif '토스페이' in description:
            if '오픈뱅킹' in description:
                return '토스페이_오픈뱅킹'
            elif '펌뱅킹' in description:
                return '토스페이_펌뱅킹'
            else:
                return '토스페이'
        
        # 자동이체
        elif '자동이체' in transaction_type or '자동이체' in description:
            return '자동이체'
        
        # 이체 관련
        elif '이체' in transaction_type or '이체' in description:
            if '오픈뱅킹' in description:
                return '오픈뱅킹이체'
            elif '펌뱅킹' in description:
                return '펌뱅킹이체'
            else:
                return '일반이체'
        
        # 입출금
        elif '출금' in transaction_type:
            return '계좌출금'
        elif '입금' in transaction_type:
            if '프로모션' in transaction_type:
                return '프로모션입금'
            elif '이자' in transaction_type:
                return '이자입금'
            else:
                return '계좌입금'
        
        # 기본값
        return transaction_type
    
    def get_supported_file_types(self) -> List[str]:
        """
        지원하는 파일 유형 목록을 반환합니다.
        
        Returns:
            List[str]: 지원하는 파일 확장자 목록
        """
        return ['csv']
    
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