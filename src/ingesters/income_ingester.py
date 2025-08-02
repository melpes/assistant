# -*- coding: utf-8 -*-
"""
IncomeIngester 클래스 정의

수입 거래 데이터 수집 및 관리를 위한 수집기입니다.
수입 유형 자동 분류, 수입 제외 규칙 적용, 수입 패턴 인식 기능을 제공합니다.
"""

import os
import re
import uuid
import hashlib
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Set, Tuple
import json
import pandas as pd
from pathlib import Path

from .base_ingester import BaseIngester
from src.models.transaction import Transaction

# 로깅 설정
logger = logging.getLogger(__name__)

class IncomeIngester(BaseIngester):
    """
    수입 거래 데이터 수집기
    
    수입 거래 데이터를 수집하고 관리하는 기능을 제공합니다.
    수입 유형 자동 분류, 수입 제외 규칙 적용, 수입 패턴 인식 기능을 구현합니다.
    """
    
    def __init__(self, name: str = "수입 관리", description: str = "수입 거래 데이터 수집 및 관리"):
        """
        수입 수집기 초기화
        
        Args:
            name: 수집기 이름 (기본값: "수입 관리")
            description: 수집기 설명 (기본값: "수입 거래 데이터 수집 및 관리")
        """
        super().__init__(name, description)
        
        # 수입 유형 패턴
        self.income_type_patterns = {
            '급여': [r'급여', r'월급', r'상여금', r'연봉', r'인건비', r'수당', r'주급', r'보너스', r'성과급'],
            '용돈': [r'용돈', r'선물', r'축하금', r'생일', r'대회', r'뒷풀이', r'간식', r'지원금'],
            '이자': [r'이자', r'배당', r'수익', r'예금이자', r'통장 이자', r'이자입금', r'적금', r'펀드'],
            '환급': [r'환급', r'세금', r'공제', r'환급금', r'보험금', r'취소', r'반환', r'환불'],
            '부수입': [r'부수입', r'알바', r'아르바이트', r'프리랜서', r'외주', r'수당', r'강의', r'강연'],
            '임대수입': [r'임대', r'월세', r'전세', r'임차', r'부동산', r'집세', r'관리비'],
            '판매수입': [r'판매', r'중고', r'장터', r'마켓', r'거래', r'양도', r'매출', r'수익'],
            '기타수입': []  # 기본값
        }
        
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
            r'자동충전',
            r'본인계좌',
            r'자기계좌',
            r'내 계좌',
            r'계좌 이동',
            r'자금 이동',
            r'임시 보관'
        ]
        
        # 정기 수입 패턴 (주기성 분석용)
        self.regular_income_patterns = {
            '월급': {
                'patterns': [r'급여', r'월급', r'봉급', r'salary'],
                'period': 30,  # 약 한 달
                'variance': 5   # 허용 오차 (일)
            },
            '주급': {
                'patterns': [r'주급', r'weekly', r'알바비', r'아르바이트'],
                'period': 7,   # 일주일
                'variance': 2   # 허용 오차 (일)
            },
            '이자': {
                'patterns': [r'이자', r'배당', r'이자수익', r'예금이자'],
                'period': 30,  # 약 한 달
                'variance': 5   # 허용 오차 (일)
            },
            '임대수입': {
                'patterns': [r'임대', r'월세', r'임차료', r'관리비'],
                'period': 30,  # 약 한 달
                'variance': 5   # 허용 오차 (일)
            }
        }
        
        # 성능 최적화를 위한 캐시
        self._category_cache = {}
        self._exclude_cache = {}
        
        # 정기 수입 패턴 분석을 위한 내부 상태
        self._income_history = {}  # 수입 유형별 거래 내역 기록
    
    def validate_file(self, file_path: str) -> bool:
        """
        입력 파일의 유효성을 검증합니다.
        
        Args:
            file_path: 검증할 파일 경로
            
        Returns:
            bool: 파일이 유효하면 True, 그렇지 않으면 False
        """
        # 파일 확장자 확인
        ext = Path(file_path).suffix.lower()
        
        if ext == '.csv':
            try:
                # CSV 파일 검증
                df = pd.read_csv(file_path, nrows=1)
                required_columns = ['날짜', '내용', '금액']
                for col in required_columns:
                    if col not in df.columns:
                        logger.warning(f"필수 열이 누락되었습니다: {col}")
                        return False
                return True
            except Exception as e:
                logger.error(f"CSV 파일 검증 중 오류 발생: {str(e)}")
                return False
                
        elif ext == '.xlsx' or ext == '.xls':
            try:
                # Excel 파일 검증
                df = pd.read_excel(file_path, nrows=1)
                required_columns = ['날짜', '내용', '금액']
                for col in required_columns:
                    if col not in df.columns:
                        logger.warning(f"필수 열이 누락되었습니다: {col}")
                        return False
                return True
            except Exception as e:
                logger.error(f"Excel 파일 검증 중 오류 발생: {str(e)}")
                return False
                
        elif ext == '.json':
            try:
                # JSON 파일 검증
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, list):
                    logger.warning("JSON 파일은 배열 형식이어야 합니다.")
                    return False
                    
                if len(data) == 0:
                    logger.warning("JSON 파일에 데이터가 없습니다.")
                    return False
                    
                required_fields = ['date', 'description', 'amount']
                for field in required_fields:
                    if field not in data[0]:
                        logger.warning(f"필수 필드가 누락되었습니다: {field}")
                        return False
                        
                return True
            except Exception as e:
                logger.error(f"JSON 파일 검증 중 오류 발생: {str(e)}")
                return False
        
        # 지원하지 않는 파일 형식
        logger.warning(f"지원하지 않는 파일 형식입니다: {ext}")
        return False
    
    def extract_transactions(self, file_path: str) -> List[Dict[str, Any]]:
        """
        파일에서 거래 데이터를 추출합니다.
        
        Args:
            file_path: 거래 데이터가 포함된 파일 경로
            
        Returns:
            List[Dict[str, Any]]: 추출된 거래 데이터 목록
        """
        logger.info(f"수입 거래 데이터 추출 시작: {file_path}")
        
        ext = Path(file_path).suffix.lower()
        transactions = []
        
        try:
            if ext == '.csv':
                # CSV 파일 처리
                df = pd.read_csv(file_path)
                for _, row in df.iterrows():
                    try:
                        transaction_date = pd.to_datetime(row['날짜']).date()
                        description = str(row['내용'])
                        amount = float(row['금액'])
                        
                        category = str(row.get('유형', '')) if pd.notna(row.get('유형', '')) else ''
                        memo = str(row.get('메모', '')) if pd.notna(row.get('메모', '')) else ''
                        
                        transaction = {
                            'transaction_date': transaction_date,
                            'description': description,
                            'amount': amount,
                            'category': category,
                            'memo': memo,
                            'raw_data': row.to_dict()
                        }
                        
                        transactions.append(transaction)
                    except Exception as e:
                        logger.warning(f"CSV 행 처리 중 오류 발생: {str(e)}, 행: {row}")
                
            elif ext == '.xlsx' or ext == '.xls':
                # Excel 파일 처리
                df = pd.read_excel(file_path)
                for _, row in df.iterrows():
                    try:
                        transaction_date = pd.to_datetime(row['날짜']).date()
                        description = str(row['내용'])
                        amount = float(row['금액'])
                        
                        category = str(row.get('유형', '')) if pd.notna(row.get('유형', '')) else ''
                        memo = str(row.get('메모', '')) if pd.notna(row.get('메모', '')) else ''
                        
                        transaction = {
                            'transaction_date': transaction_date,
                            'description': description,
                            'amount': amount,
                            'category': category,
                            'memo': memo,
                            'raw_data': row.to_dict()
                        }
                        
                        transactions.append(transaction)
                    except Exception as e:
                        logger.warning(f"Excel 행 처리 중 오류 발생: {str(e)}, 행: {row}")
                
            elif ext == '.json':
                # JSON 파일 처리
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data:
                    try:
                        transaction_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
                        description = str(item['description'])
                        amount = float(item['amount'])
                        
                        category = str(item.get('category', ''))
                        memo = str(item.get('memo', ''))
                        
                        transaction = {
                            'transaction_date': transaction_date,
                            'description': description,
                            'amount': amount,
                            'category': category,
                            'memo': memo,
                            'raw_data': item
                        }
                        
                        transactions.append(transaction)
                    except Exception as e:
                        logger.warning(f"JSON 항목 처리 중 오류 발생: {str(e)}, 항목: {item}")
            
            logger.info(f"{len(transactions)}개의 수입 거래 데이터 추출 완료")
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
        logger.info("수입 거래 데이터 정규화 시작")
        
        normalized_transactions = []
        transaction_ids = set()
        
        for transaction in raw_data:
            try:
                # 거래 날짜
                transaction_date = transaction['transaction_date']
                
                # 거래 ID 생성 (날짜 + 금액 + 설명 해시로 고유성 보장)
                hash_input = f"{transaction_date.strftime('%Y%m%d')}_{transaction['amount']:.2f}_{transaction['description']}"
                hash_value = hashlib.md5(hash_input.encode('utf-8')).hexdigest()[:8]
                transaction_id = f"INCOME_{transaction_date.strftime('%Y%m%d')}_{int(transaction['amount'])}_{hash_value}"
                
                # 중복 ID 확인 및 처리
                if transaction_id in transaction_ids:
                    # 중복 ID가 있으면 해시에 추가 정보 포함
                    hash_input = f"{hash_input}_{len(transaction_ids)}"
                    hash_value = hashlib.md5(hash_input.encode('utf-8')).hexdigest()[:8]
                    transaction_id = f"INCOME_{transaction_date.strftime('%Y%m%d')}_{int(transaction['amount'])}_{hash_value}"
                
                transaction_ids.add(transaction_id)
                
                # 수입 유형 결정
                description = transaction['description']
                memo = transaction.get('memo', '')
                
                # 카테고리가 이미 있으면 사용, 없으면 자동 분류
                if transaction.get('category') and transaction['category'].strip():
                    category = transaction['category'].strip()
                else:
                    category = self._categorize_income(description, transaction['amount'], memo)
                
                # 수입 제외 여부 결정 (자금 이동, 임시 보관 등)
                is_excluded = self._is_income_excluded(description, memo)
                
                # 정규화된 거래 데이터 생성
                normalized_transaction = {
                    'transaction_id': transaction_id,
                    'transaction_date': transaction_date.strftime('%Y-%m-%d'),
                    'description': description,
                    'amount': Decimal(str(transaction['amount'])),
                    'transaction_type': Transaction.TYPE_INCOME,
                    'category': category,
                    'payment_method': self._determine_payment_method(description, memo),
                    'source': 'income_ingester',
                    'account_type': '수입',
                    'memo': memo,
                    'is_excluded': is_excluded,
                    'metadata': {
                        'income_type': category,
                        'is_regular': self._is_regular_income(description, category),
                        'original_data': transaction.get('raw_data', {})
                    }
                }
                
                # 데이터 유효성 검증
                if self.validate_data(normalized_transaction):
                    normalized_transactions.append(normalized_transaction)
                    
                    # 정기 수입 패턴 분석을 위해 내부 상태 업데이트
                    self._update_income_history(normalized_transaction)
                
            except Exception as e:
                logger.warning(f"거래 정규화 중 오류 발생: {e}, 거래: {transaction}")
        
        # 정기 수입 패턴 분석
        self._analyze_income_patterns(normalized_transactions)
        
        logger.info(f"{len(normalized_transactions)}개의 수입 거래 데이터 정규화 완료")
        return normalized_transactions
    
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
        
        # 캐시 확인
        cache_key = f"{description}_{memo}_{amount}"
        if cache_key in self._category_cache:
            return self._category_cache[cache_key]
        
        # 수입 유형 패턴 매칭 (설명 기준)
        for category, patterns in self.income_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE) or re.search(pattern, memo, re.IGNORECASE):
                    self._category_cache[cache_key] = category
                    return category
        
        # 금액 기반 추정 (예: 큰 금액은 급여일 가능성이 높음)
        if amount >= 1000000:  # 100만원 이상
            category = '급여'
        elif 500000 <= amount < 1000000:  # 50만원 ~ 100만원
            category = '부수입'
        elif 100000 <= amount < 500000:  # 10만원 ~ 50만원
            category = '부수입'
        elif 10000 <= amount < 100000:  # 1만원 ~ 10만원
            category = '용돈'
        else:  # 1만원 미만
            category = '기타수입'
        
        # 캐시에 저장
        self._category_cache[cache_key] = category
        return category
    
    def _is_income_excluded(self, description: str, memo: str = '') -> bool:
        """
        수입 거래가 제외 대상인지 확인합니다.
        
        Args:
            description: 거래 설명
            memo: 메모 (선택)
            
        Returns:
            bool: 제외 대상이면 True, 그렇지 않으면 False
        """
        description = str(description).lower()
        memo = str(memo).lower()
        
        # 캐시 확인
        cache_key = f"{description}_{memo}"
        if cache_key in self._exclude_cache:
            return self._exclude_cache[cache_key]
        
        # 자금 이동, 임시 보관 등은 수입에서 제외
        for pattern in self.income_exclude_patterns:
            if (re.search(pattern, description, re.IGNORECASE) or 
                (memo and re.search(pattern, memo, re.IGNORECASE))):
                self._exclude_cache[cache_key] = True
                return True
        
        # 특정 키워드가 포함된 경우 제외
        exclude_keywords = ['자동충전', '카드잔액', '취소', '환불', '반환', '카드 캐시백']
        for keyword in exclude_keywords:
            if (keyword in description.lower() or 
                (memo and keyword in memo.lower())):
                self._exclude_cache[cache_key] = True
                return True
        
        # 같은 계좌 간 이체는 제외 (내 계좌 간 이동)
        if '강태희' in description and ('입금' in description or '이체' in description):
            self._exclude_cache[cache_key] = True
            return True
        
        self._exclude_cache[cache_key] = False
        return False
    
    def _determine_payment_method(self, description: str, memo: str = '') -> str:
        """
        거래 설명과 메모를 기반으로 입금 방식을 결정합니다.
        
        Args:
            description: 거래 설명
            memo: 메모 (선택)
            
        Returns:
            str: 결정된 입금 방식
        """
        description = str(description).lower()
        memo = str(memo).lower()
        
        # 급여 관련
        if any(keyword in description or keyword in memo for keyword in ['급여', '월급', '봉급', '상여금']):
            return '급여이체'
        
        # 이자 관련
        elif any(keyword in description or keyword in memo for keyword in ['이자', '배당', '수익']):
            return '이자입금'
        
        # 계좌 이체 관련
        elif any(keyword in description or keyword in memo for keyword in ['이체', '송금', '입금', '계좌']):
            return '계좌입금'
        
        # 현금 관련
        elif any(keyword in description or keyword in memo for keyword in ['현금', '직접', '수기']):
            return '현금'
        
        # 기본값
        return '계좌입금'
    
    def _is_regular_income(self, description: str, category: str) -> bool:
        """
        수입이 정기적인지 판단합니다.
        
        Args:
            description: 거래 설명
            category: 수입 카테고리
            
        Returns:
            bool: 정기 수입이면 True, 그렇지 않으면 False
        """
        description = str(description).lower()
        
        # 카테고리 기반 판단
        if category in ['급여', '월급', '임대수입']:
            return True
        
        # 설명 기반 판단
        regular_keywords = ['월급', '급여', '봉급', '월세', '임대료', '정기', '월 이자', '월별', '주급']
        for keyword in regular_keywords:
            if keyword in description:
                return True
        
        return False
    
    def _update_income_history(self, transaction: Dict[str, Any]) -> None:
        """
        수입 내역 기록을 업데이트합니다.
        
        Args:
            transaction: 정규화된 거래 데이터
        """
        category = transaction['category']
        transaction_date = datetime.strptime(transaction['transaction_date'], '%Y-%m-%d').date()
        
        if category not in self._income_history:
            self._income_history[category] = []
        
        self._income_history[category].append({
            'date': transaction_date,
            'amount': float(transaction['amount']),
            'description': transaction['description']
        })
    
    def _analyze_income_patterns(self, transactions: List[Dict[str, Any]]) -> None:
        """
        수입 패턴을 분석하고 정기성을 식별합니다.
        
        Args:
            transactions: 정규화된 거래 데이터 목록
        """
        # 카테고리별로 그룹화
        category_groups = {}
        for transaction in transactions:
            category = transaction['category']
            if category not in category_groups:
                category_groups[category] = []
            
            category_groups[category].append({
                'date': datetime.strptime(transaction['transaction_date'], '%Y-%m-%d').date(),
                'amount': float(transaction['amount']),
                'transaction_id': transaction['transaction_id']
            })
        
        # 각 카테고리별 패턴 분석
        for category, transactions in category_groups.items():
            if len(transactions) < 2:
                continue
            
            # 날짜순 정렬
            sorted_transactions = sorted(transactions, key=lambda x: x['date'])
            
            # 날짜 간격 계산
            intervals = []
            for i in range(1, len(sorted_transactions)):
                interval = (sorted_transactions[i]['date'] - sorted_transactions[i-1]['date']).days
                intervals.append(interval)
            
            # 간격이 일정한지 확인 (표준편차 사용)
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
                std_dev = variance ** 0.5
                
                # 표준편차가 작으면 정기 수입으로 판단
                is_regular = std_dev < 5 and avg_interval > 0
                
                if is_regular:
                    logger.info(f"정기 수입 패턴 발견: 카테고리={category}, 평균 간격={avg_interval:.1f}일, 표준편차={std_dev:.1f}")
                    
                    # 거래 메타데이터 업데이트
                    for transaction in transactions:
                        transaction_id = transaction['transaction_id']
                        for t in transactions:
                            if t['transaction_id'] == transaction_id:
                                if 'metadata' not in t:
                                    t['metadata'] = {}
                                t['metadata']['is_regular'] = True
                                t['metadata']['interval_days'] = avg_interval
                                t['metadata']['next_expected'] = (transaction['date'] + timedelta(days=int(avg_interval))).strftime('%Y-%m-%d')
    
    def get_supported_file_types(self) -> List[str]:
        """
        지원하는 파일 유형 목록을 반환합니다.
        
        Returns:
            List[str]: 지원하는 파일 확장자 목록
        """
        return ['csv', 'xlsx', 'xls', 'json']
    
    def get_required_fields(self) -> List[str]:
        """
        필수 데이터 필드 목록을 반환합니다.
        
        Returns:
            List[str]: 필수 필드 목록
        """
        return ['transaction_id', 'transaction_date', 'description', 'amount', 'transaction_type']
    
    def add_income(self, transaction_date: date, description: str, amount: float, 
                  category: Optional[str] = None, payment_method: Optional[str] = None, 
                  memo: Optional[str] = None) -> Dict[str, Any]:
        """
        수동으로 수입 거래를 추가합니다.
        
        Args:
            transaction_date: 거래 날짜
            description: 거래 설명
            amount: 거래 금액
            category: 수입 유형 (선택)
            payment_method: 입금 방식 (선택)
            memo: 메모 (선택)
            
        Returns:
            Dict[str, Any]: 생성된 거래 데이터
        """
        # 금액 검증
        if amount <= 0:
            raise ValueError("수입 금액은 0보다 커야 합니다")
        
        # 거래 ID 생성
        hash_input = f"{transaction_date.strftime('%Y%m%d')}_{amount:.2f}_{description}"
        hash_value = hashlib.md5(hash_input.encode('utf-8')).hexdigest()[:8]
        transaction_id = f"INCOME_MANUAL_{transaction_date.strftime('%Y%m%d')}_{int(amount)}_{hash_value}"
        
        # 카테고리가 없으면 자동 분류
        if not category:
            category = self._categorize_income(description, amount, memo or '')
        
        # 입금 방식이 없으면 자동 결정
        if not payment_method:
            payment_method = self._determine_payment_method(description, memo or '')
        
        # 정기 수입 여부 판단
        is_regular = self._is_regular_income(description, category)
        
        # 거래 데이터 생성
        transaction = {
            'transaction_id': transaction_id,
            'transaction_date': transaction_date.strftime('%Y-%m-%d'),
            'description': description,
            'amount': Decimal(str(amount)),
            'transaction_type': Transaction.TYPE_INCOME,
            'category': category,
            'payment_method': payment_method,
            'source': 'manual_income',
            'account_type': '수입',
            'memo': memo or '',
            'is_excluded': False,
            'metadata': {
                'income_type': category,
                'is_regular': is_regular,
                'manual_entry': True
            }
        }
        
        logger.info(f"수동 수입 추가: {description}, {amount}원, {category}")
        return transaction
    
    def batch_add_incomes(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        여러 수입 거래를 일괄 추가합니다.
        
        Args:
            transactions: 추가할 거래 데이터 목록
            
        Returns:
            List[Dict[str, Any]]: 생성된 거래 데이터 목록
        """
        result = []
        
        for transaction in transactions:
            try:
                # 필수 필드 확인
                if 'transaction_date' not in transaction or 'description' not in transaction or 'amount' not in transaction:
                    logger.warning(f"필수 필드가 누락된 거래: {transaction}")
                    continue
                
                # 수입 추가
                income_data = self.add_income(
                    transaction_date=transaction['transaction_date'],
                    description=transaction['description'],
                    amount=float(transaction['amount']),
                    category=transaction.get('category'),
                    payment_method=transaction.get('payment_method'),
                    memo=transaction.get('memo', '')
                )
                
                result.append(income_data)
                
            except Exception as e:
                logger.warning(f"거래 추가 중 오류 발생: {e}, 거래: {transaction}")
        
        logger.info(f"{len(result)}개의 수입 거래 일괄 추가 완료")
        return result
    
    def analyze_income_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        수입 패턴을 분석하고 결과를 반환합니다.
        
        Args:
            transactions: 분석할 거래 데이터 목록
            
        Returns:
            Dict[str, Any]: 분석 결과
        """
        # 카테고리별 통계
        category_stats = {}
        total_amount = Decimal('0')
        
        for transaction in transactions:
            category = transaction['category']
            amount = Decimal(str(transaction['amount']))
            
            if category not in category_stats:
                category_stats[category] = {
                    'count': 0,
                    'total': Decimal('0'),
                    'min': amount,
                    'max': amount,
                    'transactions': []
                }
            
            stats = category_stats[category]
            stats['count'] += 1
            stats['total'] += amount
            stats['min'] = min(stats['min'], amount)
            stats['max'] = max(stats['max'], amount)
            stats['transactions'].append({
                'date': transaction['transaction_date'],
                'amount': float(amount),
                'description': transaction['description']
            })
            
            total_amount += amount
        
        # 정기 수입 패턴 분석
        regular_patterns = {}
        
        for category, stats in category_stats.items():
            if stats['count'] < 2:
                continue
                
            # 날짜순 정렬
            sorted_transactions = sorted(stats['transactions'], key=lambda x: x['date'])
            
            # 날짜 간격 계산
            intervals = []
            for i in range(1, len(sorted_transactions)):
                date1 = datetime.strptime(sorted_transactions[i-1]['date'], '%Y-%m-%d').date()
                date2 = datetime.strptime(sorted_transactions[i]['date'], '%Y-%m-%d').date()
                interval = (date2 - date1).days
                intervals.append(interval)
            
            # 간격이 일정한지 확인
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
                std_dev = variance ** 0.5
                
                # 표준편차가 작으면 정기 수입으로 판단
                if std_dev < 5 and avg_interval > 0:
                    # 다음 예상 날짜 계산
                    last_date = datetime.strptime(sorted_transactions[-1]['date'], '%Y-%m-%d').date()
                    next_date = last_date + timedelta(days=int(avg_interval))
                    
                    regular_patterns[category] = {
                        'avg_interval': avg_interval,
                        'std_dev': std_dev,
                        'avg_amount': float(stats['total'] / stats['count']),
                        'next_expected_date': next_date.strftime('%Y-%m-%d')
                    }
        
        # 결과 생성
        result = {
            'total_income': float(total_amount),
            'category_count': len(category_stats),
            'transaction_count': sum(stats['count'] for stats in category_stats.values()),
            'categories': {
                category: {
                    'count': stats['count'],
                    'total': float(stats['total']),
                    'average': float(stats['total'] / stats['count']),
                    'min': float(stats['min']),
                    'max': float(stats['max']),
                    'percentage': float(stats['total'] / total_amount * 100) if total_amount > 0 else 0
                }
                for category, stats in category_stats.items()
            },
            'regular_patterns': regular_patterns
        }
        
        return result