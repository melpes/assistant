# -*- coding: utf-8 -*-
"""
TossBankCardIngester 통합 테스트

실제 파일을 사용하여 전체 수집 과정을 테스트합니다.
"""

import pytest
import os
import pandas as pd
from datetime import date
from decimal import Decimal
import tempfile
import shutil

from src.ingesters.toss_bank_card_ingester import TossBankCardIngester

class TestTossBankCardIntegration:
    """TossBankCardIngester 통합 테스트 클래스"""
    
    @pytest.fixture
    def sample_xlsx_file(self):
        """테스트용 샘플 XLSX 파일 생성"""
        # 임시 디렉토리 생성
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, "test_toss_card.xlsx")
        
        # 테스트 데이터 생성
        df = pd.DataFrame({
            '매출일자': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-03'],
            '가맹점명': ['테스트 마트', '테스트 카페', '테스트 식당', '테스트 식당'],
            '매출금액': [10000, 5000, 15000, 20000],
            '취소금액': [0, 0, 0, 20000],  # 마지막 거래는 전액 취소
            '승인번호': ['1234567890', '2345678901', '3456789012', '4567890123'],
            '카드번호': ['1234', '1234', '1234', '1234'],
            '할부': ['일시불', '일시불', '일시불', '일시불'],
            '승인시간': ['12:34:56', '13:45:67', '18:23:45', '19:12:34'],
            '이용구분': ['일반', '일반', '일반', '취소']
        })
        
        # 헤더 행 추가 (토스뱅크 카드 이용내역서 형식)
        header_df = pd.DataFrame({
            '토스뱅크 카드 이용내역서': [''] * 14
        })
        
        # 파일 저장 (헤더 포함)
        with pd.ExcelWriter(file_path) as writer:
            header_df.to_excel(writer, index=False, header=False)
            df.to_excel(writer, index=False, startrow=14)
        
        yield file_path
        
        # 테스트 후 임시 디렉토리 삭제
        shutil.rmtree(temp_dir)
    
    def test_full_ingestion_process(self, sample_xlsx_file):
        """전체 수집 과정 통합 테스트"""
        ingester = TossBankCardIngester()
        
        # 1. 파일 유효성 검증
        assert ingester.validate_file(sample_xlsx_file) is True
        
        # 2. 거래 데이터 추출
        raw_data = ingester.extract_transactions(sample_xlsx_file)
        assert len(raw_data) == 4
        
        # 3. 데이터 정규화
        normalized_data = ingester.normalize_data(raw_data)
        
        # 취소된 거래는 제외되어야 함
        assert len(normalized_data) == 3
        
        # 정규화된 데이터 검증
        categories = [transaction['category'] for transaction in normalized_data]
        assert '생활용품' in categories  # '테스트 마트'
        assert '식비' in categories  # '테스트 카페', '테스트 식당'
        
        # 거래 ID 고유성 검증
        transaction_ids = [transaction['transaction_id'] for transaction in normalized_data]
        assert len(transaction_ids) == len(set(transaction_ids))
        
        # 메타데이터 검증
        for transaction in normalized_data:
            assert 'metadata' in transaction
            assert 'approval_number' in transaction['metadata']
            assert 'sales_amount' in transaction['metadata']
            assert 'cancel_amount' in transaction['metadata']
    
    def test_ingest_method(self, sample_xlsx_file):
        """ingest 메서드 통합 테스트"""
        ingester = TossBankCardIngester()
        
        # ingest 메서드 호출
        normalized_data = ingester.ingest(sample_xlsx_file)
        
        # 결과 검증
        assert len(normalized_data) == 3  # 취소된 거래 제외
        
        # 모든 거래가 expense 타입인지 확인
        for transaction in normalized_data:
            assert transaction['transaction_type'] == 'expense'
            assert transaction['source'] == 'toss_bank_card'
            assert transaction['payment_method'] == '카드결제'
    
    def test_duplicate_prevention(self, sample_xlsx_file):
        """중복 방지 기능 테스트"""
        ingester = TossBankCardIngester()
        
        # 첫 번째 수집
        first_data = ingester.ingest(sample_xlsx_file)
        
        # 동일한 파일로 두 번째 수집
        second_data = ingester.ingest(sample_xlsx_file)
        
        # 거래 ID 비교
        first_ids = set(item['transaction_id'] for item in first_data)
        second_ids = set(item['transaction_id'] for item in second_data)
        
        # 동일한 거래는 동일한 ID를 가져야 함
        assert first_ids == second_ids
        
        # 각 수집에서 거래 ID는 고유해야 함
        assert len(first_ids) == len(first_data)
        assert len(second_ids) == len(second_data)