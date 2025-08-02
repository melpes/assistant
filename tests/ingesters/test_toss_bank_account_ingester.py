# -*- coding: utf-8 -*-
"""
TossBankAccountIngester 테스트
"""

import pytest
import os
import pandas as pd
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from src.ingesters.toss_bank_account_ingester import TossBankAccountIngester

class TestTossBankAccountIngester:
    """TossBankAccountIngester 테스트 클래스"""
    
    def test_initialization(self):
        """초기화 테스트"""
        ingester = TossBankAccountIngester()
        assert ingester.name == "토스뱅크 계좌"
        assert "토스뱅크 계좌 거래내역" in ingester.description
        
        # 커스텀 이름과 설명으로 초기화
        custom_ingester = TossBankAccountIngester("커스텀 이름", "커스텀 설명")
        assert custom_ingester.name == "커스텀 이름"
        assert custom_ingester.description == "커스텀 설명"
    
    def test_get_supported_file_types(self):
        """지원하는 파일 유형 테스트"""
        ingester = TossBankAccountIngester()
        file_types = ingester.get_supported_file_types()
        
        assert isinstance(file_types, list)
        assert "csv" in file_types
    
    def test_get_required_fields(self):
        """필수 필드 목록 테스트"""
        ingester = TossBankAccountIngester()
        required_fields = ingester.get_required_fields()
        
        assert isinstance(required_fields, list)
        assert all(field in required_fields for field in [
            'transaction_id', 'transaction_date', 'description', 
            'amount', 'transaction_type', 'source'
        ])
    
    def test_validate_file_valid_extension(self):
        """유효한 파일 확장자 검증 테스트"""
        ingester = TossBankAccountIngester()
        
        # 유효한 확장자
        with patch('pandas.read_csv') as mock_read_csv:
            # 필요한 컬럼이 있는 DataFrame 모의 객체 생성
            mock_df = pd.DataFrame({
                '거래 일시': ['2023-01-01 12:34:56'],
                '적요': ['테스트 거래'],
                '거래 유형': ['출금'],
                '거래 금액': [10000],
                '거래 후 잔액': [90000]
            })
            mock_read_csv.return_value = mock_df
            
            assert ingester.validate_file("test_file.csv") is True
    
    def test_validate_file_invalid_extension(self):
        """유효하지 않은 파일 확장자 검증 테스트"""
        ingester = TossBankAccountIngester()
        
        # 유효하지 않은 확장자
        assert ingester.validate_file("test_file.xlsx") is False
    
    def test_validate_file_missing_columns(self):
        """필수 컬럼이 없는 파일 검증 테스트"""
        ingester = TossBankAccountIngester()
        
        with patch('pandas.read_csv') as mock_read_csv:
            # 필수 컬럼이 없는 DataFrame 모의 객체 생성
            mock_df = pd.DataFrame({
                '날짜': ['2023-01-01'],
                '설명': ['테스트 거래'],
                '금액': [10000]
            })
            mock_read_csv.return_value = mock_df
            
            assert ingester.validate_file("test_file.csv") is False
    
    def test_extract_transactions(self):
        """거래 데이터 추출 테스트"""
        ingester = TossBankAccountIngester()
        
        with patch('pandas.read_csv') as mock_read_csv, \
             patch('pandas.to_datetime') as mock_to_datetime:
            # 테스트용 DataFrame 모의 객체 생성
            mock_df = pd.DataFrame({
                '거래 일시': ['2023-01-01 12:34:56', '2023-01-02 12:34:56', '2023-01-03 12:34:56'],
                '적요': ['테스트 출금', '테스트 입금', '카드 캐시백'],
                '거래 유형': ['출금', '입금', '프로모션입금'],
                '거래 금액': [-10000, 20000, 500],
                '거래 후 잔액': [90000, 110000, 110500],
                '거래 기관': ['테스트은행', '테스트은행', '토스'],
                '계좌번호': ['1234-5678', '1234-5678', '1234-5678'],
                '메모': ['테스트 메모1', '테스트 메모2', '캐시백']
            })
            
            # 날짜 모의 객체 설정
            mock_dates = [date(2023, 1, 1), date(2023, 1, 2), date(2023, 1, 3)]
            mock_to_datetime.return_value.dt.date = pd.Series(mock_dates)
            
            # read_csv가 DataFrame을 반환하도록 설정
            mock_read_csv.return_value = mock_df
            
            transactions = ingester.extract_transactions("test_file.csv")
            
            assert len(transactions) == 3
            
            # 출금 거래 확인
            assert transactions[0]['description'] == '테스트 출금'
            assert transactions[0]['transaction_type'] == '출금'
            assert transactions[0]['amount'] == 10000  # 절대값으로 저장
            assert transactions[0]['is_expense'] is True
            assert transactions[0]['balance'] == 90000
            assert transactions[0]['memo'] == '테스트 메모1'
            assert 'raw_data' in transactions[0]
            
            # 입금 거래 확인
            assert transactions[1]['description'] == '테스트 입금'
            assert transactions[1]['transaction_type'] == '입금'
            assert transactions[1]['amount'] == 20000
            assert transactions[1]['is_expense'] is False
            assert transactions[1]['balance'] == 110000
            
            # 캐시백 거래 확인
            assert transactions[2]['description'] == '카드 캐시백'
            assert transactions[2]['transaction_type'] == '프로모션입금'
            assert transactions[2]['amount'] == 500
            assert transactions[2]['is_expense'] is False
            assert transactions[2]['is_cashback'] is True  # 캐시백으로 인식
    
    def test_normalize_data(self):
        """데이터 정규화 테스트"""
        ingester = TossBankAccountIngester()
        
        # 테스트용 원시 데이터
        raw_data = [
            {
                'transaction_date': date(2023, 1, 1),
                'description': '테스트 출금',
                'transaction_type': '출금',
                'amount': 10000,
                'is_expense': True,
                'is_cashback': False,
                'institution': '테스트은행',
                'account_number': '1234-5678',
                'balance': 90000,
                'memo': '테스트 메모',
                'raw_data': {}
            },
            {
                'transaction_date': date(2023, 1, 2),
                'description': '테스트 입금',
                'transaction_type': '입금',
                'amount': 20000,
                'is_expense': False,
                'is_cashback': False,
                'institution': '테스트은행',
                'account_number': '1234-5678',
                'balance': 110000,
                'memo': '테스트 메모',
                'raw_data': {}
            },
            {
                'transaction_date': date(2023, 1, 3),
                'description': '캐시백',
                'transaction_type': '입금',
                'amount': 1000,
                'is_expense': False,
                'is_cashback': True,
                'institution': '토스',
                'account_number': '1234-5678',
                'balance': 111000,
                'memo': '캐시백',
                'raw_data': {}
            }
        ]
        
        normalized_data = ingester.normalize_data(raw_data)
        
        assert len(normalized_data) == 3
        
        # 출금 거래 확인
        assert normalized_data[0]['transaction_type'] == 'expense'
        assert normalized_data[0]['amount'] == Decimal('10000')
        assert normalized_data[0]['source'] == 'toss_bank_account'
        assert normalized_data[0]['is_excluded'] is False
        assert 'metadata' in normalized_data[0]
        assert 'transaction_detail' in normalized_data[0]['metadata']
        
        # 입금 거래 확인
        assert normalized_data[1]['transaction_type'] == 'income'
        assert normalized_data[1]['amount'] == Decimal('20000')
        assert 'metadata' in normalized_data[1]
        
        # 캐시백 거래 확인 (제외 대상)
        assert normalized_data[2]['transaction_type'] == 'income'
        assert normalized_data[2]['is_excluded'] is True
        assert 'metadata' in normalized_data[2]
        assert 'transaction_detail' in normalized_data[2]['metadata']
        
        # 거래 ID 형식 확인
        for data in normalized_data:
            assert data['transaction_id'].startswith('TOSSACC_')
            assert len(data['transaction_id']) > 20  # 충분히 긴 ID
        
        # 중복 ID 없음 확인
        ids = [data['transaction_id'] for data in normalized_data]
        assert len(ids) == len(set(ids))  # 중복 없음
    
    def test_determine_payment_method(self):
        """결제 방식 결정 테스트"""
        ingester = TossBankAccountIngester()
        
        # 기본 결제 방식 테스트
        assert ingester._determine_payment_method('테스트', '체크카드결제') == '체크카드결제'
        assert ingester._determine_payment_method('atm현금', '출금') == 'ATM출금'
        assert ingester._determine_payment_method('자동환전', '출금') == '해외결제'
        assert ingester._determine_payment_method('토스페이', '출금') == '토스페이'
        assert ingester._determine_payment_method('자동이체', '출금') == '자동이체'
        assert ingester._determine_payment_method('테스트', '이체') == '계좌이체'
        assert ingester._determine_payment_method('테스트', '출금') == '계좌출금'
        assert ingester._determine_payment_method('결제', '출금') == '계좌결제'
        
        # 추가 결제 방식 테스트
        assert ingester._determine_payment_method('네이버페이', '출금') == '네이버페이'
        assert ingester._determine_payment_method('카카오페이', '출금') == '카카오페이'
        assert ingester._determine_payment_method('간편페이 결제', '출금') == '간편결제'
        assert ingester._determine_payment_method('오픈뱅킹', '이체') == '오픈뱅킹'
        assert ingester._determine_payment_method('펌뱅킹', '이체') == '펌뱅킹'
        assert ingester._determine_payment_method('테스트', '프로모션입금') == '프로모션입금'
        assert ingester._determine_payment_method('테스트', '이자입금') == '이자입금'
    
    def test_categorize_transaction(self):
        """카테고리 분류 테스트"""
        ingester = TossBankAccountIngester()
        
        # 지출 카테고리 테스트
        assert ingester._categorize_transaction('이마트', 10000, 'expense', '출금') == '생활용품/식료품'
        assert ingester._categorize_transaction('스타벅스', 5000, 'expense', '체크카드결제') == '카페/음료'
        assert ingester._categorize_transaction('맥도날드', 8000, 'expense', '체크카드결제') == '식비'
        assert ingester._categorize_transaction('택시', 12000, 'expense', '체크카드결제') == '교통비'
        assert ingester._categorize_transaction('병원', 30000, 'expense', '체크카드결제') == '의료비'
        assert ingester._categorize_transaction('kt', 50000, 'expense', '자동이체') == '통신비'
        assert ingester._categorize_transaction('전기요금', 20000, 'expense', '자동이체') == '공과금'
        assert ingester._categorize_transaction('cgv', 15000, 'expense', '체크카드결제') == '문화/오락'
        assert ingester._categorize_transaction('맨즈코리아', 50000, 'expense', '체크카드결제') == '의류/패션'
        assert ingester._categorize_transaction('쿠팡', 25000, 'expense', '체크카드결제') == '온라인쇼핑'
        assert ingester._categorize_transaction('atm출금', 100000, 'expense', 'ATM출금') == '현금인출'
        assert ingester._categorize_transaction('자동환전', 100000, 'expense', '출금') == '해외결제'
        assert ingester._categorize_transaction('토스페이', 10000, 'expense', '출금') == '간편결제'
        
        # 메모 기반 분류 테스트
        assert ingester._categorize_transaction('강태희', 10000, 'expense', '출금', '유튜브 뮤직') == '구독서비스'
        
        # 수입 카테고리 테스트
        assert ingester._categorize_transaction('급여', 1000000, 'income', '입금') == '급여'
        assert ingester._categorize_transaction('용돈', 50000, 'income', '입금') == '용돈'
        assert ingester._categorize_transaction('이자입금', 1000, 'income', '이자입금') == '이자수입'
        assert ingester._categorize_transaction('캐시백', 500, 'income', '프로모션입금') == '프로모션/캐시백'
        
        # 금액 기반 추정 테스트
        assert ingester._categorize_transaction('알 수 없음', 10000, 'expense', '출금') in ['소형결제', '기타']
        assert ingester._categorize_transaction('알 수 없음', 60000, 'expense', '출금') in ['중형결제', '기타']
        assert ingester._categorize_transaction('알 수 없음', 150000, 'expense', '출금') in ['대형결제', '기타']  
  def test_is_income_excluded(self):
        """수입 제외 여부 결정 테스트"""
        ingester = TossBankAccountIngester()
        
        # 기본 제외 패턴 테스트
        assert ingester._is_income_excluded('카드잔액 자동충전', '입금') is True
        assert ingester._is_income_excluded('내계좌 이체', '입금') is True
        assert ingester._is_income_excluded('계좌이체', '입금') is True
        assert ingester._is_income_excluded('일반 입금', '입금') is False
        
        # 특정 거래 유형 테스트
        assert ingester._is_income_excluded('캐시백', '프로모션입금') is True
        assert ingester._is_income_excluded('포인트', '카드 캐시백') is True
        
        # 메모 기반 테스트
        assert ingester._is_income_excluded('테스트', '입금', '카드잔액 자동충전') is True
        assert ingester._is_income_excluded('테스트', '입금', '일반 메모') is False
        
        # 내 계좌 간 이체 테스트
        assert ingester._is_income_excluded('강태희', '입금') is True
    
    def test_categorize_income(self):
        """수입 카테고리 분류 테스트"""
        ingester = TossBankAccountIngester()
        
        # 기본 수입 유형 테스트
        assert ingester._categorize_income('급여', 1000000) == '급여'
        assert ingester._categorize_income('월급', 2000000) == '급여'
        assert ingester._categorize_income('용돈', 50000) == '용돈'
        assert ingester._categorize_income('이자', 1000) == '이자수입'
        assert ingester._categorize_income('이자입금', 1000) == '이자수입'
        assert ingester._categorize_income('통장 이자', 500) == '이자수입'
        assert ingester._categorize_income('환급', 30000) == '환급'
        
        # 메모 기반 테스트
        assert ingester._categorize_income('강태희', 50000, '대회 뒷풀이') == '용돈'
        
        # 프로모션/캐시백 테스트
        assert ingester._categorize_income('프로모션입금', 1000) == '프로모션/캐시백'
        assert ingester._categorize_income('카드 캐시백', 500) == '프로모션/캐시백'
        
        # 금액 기반 추정 테스트
        assert ingester._categorize_income('알 수 없음', 1500000) == '급여'
        assert ingester._categorize_income('알 수 없음', 600000) == '대형수입'
        assert ingester._categorize_income('알 수 없음', 200000) == '중형수입'
        assert ingester._categorize_income('알 수 없음', 50000) == '소형수입'
        assert ingester._categorize_income('알 수 없음', 5000) == '소액수입'
    
    def test_determine_transaction_subtype(self):
        """거래 하위 유형 결정 테스트"""
        ingester = TossBankAccountIngester()
        
        # 카드 관련
        assert ingester._determine_transaction_subtype('테스트', '체크카드결제') == '체크카드결제'
        assert ingester._determine_transaction_subtype('테스트', '카드결제') == '신용카드결제'
        assert ingester._determine_transaction_subtype('카드 캐시백', '프로모션입금') == '카드캐시백'
        
        # 현금 인출
        assert ingester._determine_transaction_subtype('ATM현금', 'ATM출금') == '현금인출'
        
        # 해외 결제
        assert ingester._determine_transaction_subtype('자동환전', '출금') == '해외결제'
        
        # 간편결제
        assert ingester._determine_transaction_subtype('토스페이 오픈뱅킹', '출금') == '토스페이_오픈뱅킹'
        assert ingester._determine_transaction_subtype('토스페이 펌뱅킹', '출금') == '토스페이_펌뱅킹'
        assert ingester._determine_transaction_subtype('토스페이', '출금') == '토스페이'
        
        # 이체 관련
        assert ingester._determine_transaction_subtype('오픈뱅킹', '이체') == '오픈뱅킹이체'
        assert ingester._determine_transaction_subtype('펌뱅킹', '이체') == '펌뱅킹이체'
        assert ingester._determine_transaction_subtype('일반이체', '이체') == '일반이체'
        
        # 입출금
        assert ingester._determine_transaction_subtype('테스트', '출금') == '계좌출금'
        assert ingester._determine_transaction_subtype('테스트', '입금') == '계좌입금'
        assert ingester._determine_transaction_subtype('테스트', '프로모션입금') == '프로모션입금'
        assert ingester._determine_transaction_subtype('테스트', '이자입금') == '이자입금'
    
    def test_get_transaction_detail(self):
        """거래 상세 정보 추출 테스트"""
        ingester = TossBankAccountIngester()
        
        # 이체 관련 정보
        transfer_transaction = {
            'description': '강태희 → 홍길동',
            'transaction_type': '이체',
            'amount': 50000,
            'memo': '생활비'
        }
        detail = ingester._get_transaction_detail(transfer_transaction)
        assert 'sender' in detail
        assert 'receiver' in detail
        assert detail['sender'] == '강태희'
        assert detail['receiver'] == '홍길동'
        
        # 카드 결제 정보
        card_transaction = {
            'description': '맥도날드(1234-5678-9012-3456)',
            'transaction_type': '체크카드결제',
            'amount': 8000,
            'memo': ''
        }
        detail = ingester._get_transaction_detail(card_transaction)
        assert 'card_number' in detail
        assert detail['card_number'] == '1234-5678-9012-3456'
        
        # 해외 결제 정보
        foreign_transaction = {
            'description': '부족한돈 자동환전 (USD) DISCORD',
            'transaction_type': '출금',
            'amount': 10000,
            'memo': ''
        }
        detail = ingester._get_transaction_detail(foreign_transaction)
        assert 'currency' in detail
        assert detail['currency'] == 'USD'
        
        # 금액 범주화 테스트
        assert ingester._get_transaction_detail({'amount': 5000})['amount_category'] == '소액'
        assert ingester._get_transaction_detail({'amount': 50000})['amount_category'] == '중액'
        assert ingester._get_transaction_detail({'amount': 500000})['amount_category'] == '고액'
        assert ingester._get_transaction_detail({'amount': 1500000})['amount_category'] == '대액'