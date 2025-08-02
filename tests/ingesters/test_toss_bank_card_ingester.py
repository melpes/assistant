# -*- coding: utf-8 -*-
"""
TossBankCardIngester 테스트
"""

import pytest
import os
import pandas as pd
from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from src.ingesters.toss_bank_card_ingester import TossBankCardIngester

class TestTossBankCardIngester:
    """TossBankCardIngester 테스트 클래스"""
    
    def test_initialization(self):
        """초기화 테스트"""
        ingester = TossBankCardIngester()
        assert ingester.name == "토스뱅크 카드"
        assert "토스뱅크 카드 이용내역서" in ingester.description
        
        # 커스텀 이름과 설명으로 초기화
        custom_ingester = TossBankCardIngester("커스텀 이름", "커스텀 설명")
        assert custom_ingester.name == "커스텀 이름"
        assert custom_ingester.description == "커스텀 설명"
    
    def test_get_supported_file_types(self):
        """지원하는 파일 유형 테스트"""
        ingester = TossBankCardIngester()
        file_types = ingester.get_supported_file_types()
        
        assert isinstance(file_types, list)
        assert "xlsx" in file_types
    
    def test_get_required_fields(self):
        """필수 필드 목록 테스트"""
        ingester = TossBankCardIngester()
        required_fields = ingester.get_required_fields()
        
        assert isinstance(required_fields, list)
        assert all(field in required_fields for field in [
            'transaction_id', 'transaction_date', 'description', 
            'amount', 'transaction_type', 'source'
        ])
    
    def test_validate_file_valid_extension(self):
        """유효한 파일 확장자 검증 테스트"""
        ingester = TossBankCardIngester()
        
        # 유효한 확장자
        with patch('pandas.read_excel') as mock_read_excel:
            # 필요한 컬럼이 있는 DataFrame 모의 객체 생성
            mock_df = pd.DataFrame({
                '매출일자': ['2023-01-01'],
                '가맹점명': ['테스트 가맹점'],
                '매출금액': [10000],
                '취소금액': [0],
                '승인번호': ['1234567890']
            })
            mock_read_excel.return_value = mock_df
            
            assert ingester.validate_file("test_file.xlsx") is True
    
    def test_validate_file_invalid_extension(self):
        """유효하지 않은 파일 확장자 검증 테스트"""
        ingester = TossBankCardIngester()
        
        # 유효하지 않은 확장자
        assert ingester.validate_file("test_file.csv") is False
    
    def test_validate_file_missing_columns(self):
        """필수 컬럼이 없는 파일 검증 테스트"""
        ingester = TossBankCardIngester()
        
        with patch('pandas.read_excel') as mock_read_excel:
            # 필수 컬럼이 없는 DataFrame 모의 객체 생성
            mock_df = pd.DataFrame({
                '날짜': ['2023-01-01'],
                '설명': ['테스트 가맹점'],
                '금액': [10000]
            })
            mock_read_excel.return_value = mock_df
            
            assert ingester.validate_file("test_file.xlsx") is False
    
    def test_extract_transactions(self):
        """거래 데이터 추출 테스트"""
        ingester = TossBankCardIngester()
        
        with patch('pandas.read_excel') as mock_read_excel:
            # 테스트용 DataFrame 모의 객체 생성
            mock_df = pd.DataFrame({
                '매출일자': ['2023-01-01', '2023-01-02'],
                '가맹점명': ['테스트 가맹점1', '테스트 가맹점2'],
                '매출금액': [10000, 20000],
                '취소금액': [0, 5000],
                '승인번호': ['1234567890', '0987654321']
            })
            mock_read_excel.return_value = mock_df
            
            transactions = ingester.extract_transactions("test_file.xlsx")
            
            assert len(transactions) == 2
            assert transactions[0]['approval_number'] == '1234567890'
            assert transactions[0]['description'] == '테스트 가맹점1'
            assert transactions[0]['sales_amount'] == 10000
            assert transactions[0]['final_amount'] == 10000
            
            # 취소금액이 있는 경우 최종 금액 확인
            assert transactions[1]['approval_number'] == '0987654321'
            assert transactions[1]['final_amount'] == 15000  # 20000 - 5000
    
    def test_normalize_data(self):
        """데이터 정규화 테스트"""
        ingester = TossBankCardIngester()
        
        # 테스트용 원시 데이터
        raw_data = [
            {
                'approval_number': '1234567890',
                'transaction_date': date(2023, 1, 1),
                'description': '테스트 가맹점',
                'sales_amount': 10000,
                'cancel_amount': 0,
                'final_amount': 10000,
                'card_number': '1234'
            }
        ]
        
        normalized_data = ingester.normalize_data(raw_data)
        
        assert len(normalized_data) == 1
        assert normalized_data[0]['transaction_id'].startswith('TOSSCARD_1234567890_')
        assert normalized_data[0]['transaction_date'] == '2023-01-01'
        assert normalized_data[0]['description'] == '테스트 가맹점'
        assert normalized_data[0]['amount'] == Decimal('10000')
        assert normalized_data[0]['transaction_type'] == 'expense'
        assert normalized_data[0]['source'] == 'toss_bank_card'
        assert normalized_data[0]['payment_method'] == '카드결제'
        assert normalized_data[0]['account_type'] == '토스뱅크 카드'
        assert '승인번호' in normalized_data[0]['memo']
    
    def test_normalize_data_with_zero_amount(self):
        """금액이 0인 거래 정규화 테스트 (취소된 거래)"""
        ingester = TossBankCardIngester()
        
        # 테스트용 원시 데이터 (취소된 거래)
        raw_data = [
            {
                'approval_number': '1234567890',
                'transaction_date': date(2023, 1, 1),
                'description': '테스트 가맹점',
                'sales_amount': 10000,
                'cancel_amount': 10000,  # 전액 취소
                'final_amount': 0,
                'card_number': '1234'
            }
        ]
        
        normalized_data = ingester.normalize_data(raw_data)
        
        # 최종 금액이 0인 거래는 제외되어야 함
        assert len(normalized_data) == 0
    
    def test_determine_category(self):
        """카테고리 결정 테스트"""
        ingester = TossBankCardIngester()
        
        # 다양한 가맹점명으로 카테고리 테스트
        test_cases = [
            {'description': '이마트', 'expected': '생활용품'},
            {'description': '스타벅스', 'expected': '식비'},
            {'description': '맥도날드', 'expected': '식비'},
            {'description': '지하철', 'expected': '교통비'},
            {'description': 'CGV', 'expected': '문화/오락'},
            {'description': '약국', 'expected': '의료비'},
            {'description': 'KT통신', 'expected': '통신비'},
            {'description': '관리비', 'expected': '공과금'},
            {'description': '유니클로', 'expected': '의류/패션'},
            {'description': 'ATM출금', 'expected': '현금인출'},
            {'description': '해외결제', 'expected': '해외결제'},
            {'description': '토스페이', 'expected': '간편결제'},
            {'description': '알 수 없는 가맹점', 'expected': '기타'}
        ]
        
        for case in test_cases:
            category = ingester._determine_category({'description': case['description']})
            assert category == case['expected'], f"{case['description']} 카테고리 오류"