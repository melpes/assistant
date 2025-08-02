# -*- coding: utf-8 -*-
"""
데이터베이스 최적화 도구 테스트

데이터베이스 최적화 도구의 기능을 테스트합니다.
"""

import os
import sys
import unittest
import sqlite3
import tempfile
import json
from datetime import datetime

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.db_optimizer import DatabaseOptimizer

class TestDatabaseOptimizer(unittest.TestCase):
    """
    데이터베이스 최적화 도구 테스트 클래스
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        # 임시 데이터베이스 생성
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 테스트 테이블 생성
        self.cursor.execute('''
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY,
            transaction_id TEXT UNIQUE,
            transaction_date DATE NOT NULL,
            description TEXT NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            transaction_type TEXT NOT NULL,
            category TEXT,
            payment_method TEXT,
            source TEXT NOT NULL,
            account_type TEXT,
            memo TEXT,
            is_excluded BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 테스트 데이터 삽입
        for i in range(100):
            self.cursor.execute('''
            INSERT INTO transactions (
                transaction_id, transaction_date, description, amount,
                transaction_type, category, payment_method, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f'TX{i:06d}',
                f'2024-01-{(i % 30) + 1:02d}',
                f'Transaction {i}',
                i * 1000,
                'expense' if i % 2 == 0 else 'income',
                '식비' if i % 5 == 0 else '교통비' if i % 5 == 1 else '생활용품' if i % 5 == 2 else '문화/오락' if i % 5 == 3 else '기타',
                '현금' if i % 3 == 0 else '체크카드결제' if i % 3 == 1 else '계좌이체',
                'manual'
            ))
        
        # 외래 키 테이블 생성
        self.cursor.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )
        ''')
        
        self.conn.commit()
        
        # 데이터베이스 최적화 도구 초기화
        self.optimizer = DatabaseOptimizer(self.db_path)
    
    def tearDown(self):
        """
        테스트 정리
        """
        # 데이터베이스 연결 종료
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_analyze_schema(self):
        """
        스키마 분석 테스트
        """
        # 스키마 분석
        schema_info = self.optimizer.analyze_schema()
        
        # 기본 정보 확인
        self.assertIn('tables', schema_info)
        self.assertIn('indexes', schema_info)
        self.assertIn('total_tables', schema_info)
        self.assertIn('total_rows', schema_info)
        
        # 테이블 정보 확인
        self.assertIn('transactions', schema_info['tables'])
        self.assertIn('categories', schema_info['tables'])
        
        # 트랜잭션 테이블 정보 확인
        transactions_table = schema_info['tables']['transactions']
        self.assertIn('columns', transactions_table)
        self.assertIn('row_count', transactions_table)
        self.assertIn('indexes', transactions_table)
        
        # 행 수 확인
        self.assertEqual(transactions_table['row_count'], 100)
    
    def test_analyze_query(self):
        """
        쿼리 분석 테스트
        """
        # 쿼리 분석
        query = "SELECT * FROM transactions WHERE category = '식비'"
        analysis = self.optimizer.analyze_query(query)
        
        # 기본 정보 확인
        self.assertIn('query', analysis)
        self.assertIn('plan', analysis)
        self.assertIn('uses_index', analysis)
        self.assertIn('table_scan', analysis)
        self.assertIn('recommendations', analysis)
        
        # 테이블 스캔 확인
        self.assertTrue(analysis['table_scan'])
        
        # 인덱스 사용 확인
        self.assertFalse(analysis['uses_index'])
        
        # 권장사항 확인
        self.assertGreater(len(analysis['recommendations']), 0)
    
    def test_recommend_indexes(self):
        """
        인덱스 추천 테스트
        """
        # 인덱스 추천
        recommendations = self.optimizer.recommend_indexes()
        
        # 추천 확인
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # 추천 항목 확인
        for rec in recommendations:
            self.assertIn('table', rec)
            self.assertIn('column', rec)
            self.assertIn('reason', rec)
            self.assertIn('sql', rec)
    
    def test_create_index(self):
        """
        인덱스 생성 테스트
        """
        # 인덱스 생성
        result = self.optimizer.create_index('transactions', ['category'])
        self.assertTrue(result)
        
        # 인덱스 확인
        self.cursor.execute("PRAGMA index_list(transactions)")
        indexes = self.cursor.fetchall()
        self.assertEqual(len(indexes), 1)
        
        # 인덱스 이름 확인
        index_name = indexes[0][1]
        self.assertEqual(index_name, 'idx_transactions_category')
        
        # 인덱스 열 확인
        self.cursor.execute(f"PRAGMA index_info({index_name})")
        columns = self.cursor.fetchall()
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0][2], 'category')
        
        # 고유 인덱스 생성
        result = self.optimizer.create_index('transactions', ['transaction_id'], unique=True)
        self.assertTrue(result)
        
        # 인덱스 확인
        self.cursor.execute("PRAGMA index_list(transactions)")
        indexes = self.cursor.fetchall()
        self.assertEqual(len(indexes), 2)
    
    def test_drop_index(self):
        """
        인덱스 삭제 테스트
        """
        # 인덱스 생성
        self.optimizer.create_index('transactions', ['category'])
        
        # 인덱스 확인
        self.cursor.execute("PRAGMA index_list(transactions)")
        indexes = self.cursor.fetchall()
        self.assertEqual(len(indexes), 1)
        
        # 인덱스 삭제
        result = self.optimizer.drop_index('idx_transactions_category')
        self.assertTrue(result)
        
        # 인덱스 확인
        self.cursor.execute("PRAGMA index_list(transactions)")
        indexes = self.cursor.fetchall()
        self.assertEqual(len(indexes), 0)
    
    def test_optimize_database(self):
        """
        데이터베이스 최적화 테스트
        """
        # 데이터베이스 최적화
        result = self.optimizer.optimize_database()
        self.assertTrue(result)
    
    def test_save_analysis(self):
        """
        분석 결과 저장 테스트
        """
        # 스키마 분석
        schema_info = self.optimizer.analyze_schema()
        
        # 임시 파일 생성
        fd, file_path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        try:
            # 분석 결과 저장
            saved_path = self.optimizer.save_analysis(schema_info, file_path)
            self.assertEqual(saved_path, file_path)
            
            # 저장된 파일 확인
            self.assertTrue(os.path.exists(file_path))
            
            # 파일 내용 확인
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            self.assertIn('tables', loaded_data)
            self.assertIn('indexes', loaded_data)
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(file_path):
                os.unlink(file_path)

if __name__ == '__main__':
    unittest.main()