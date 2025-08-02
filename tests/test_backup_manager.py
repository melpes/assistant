# -*- coding: utf-8 -*-
"""
BackupManager 테스트

백업 관리 시스템의 기능을 테스트합니다.
"""

import os
import sys
import unittest
import tempfile
import shutil
import sqlite3
import json
import zipfile
from datetime import datetime
from pathlib import Path

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.backup_manager import BackupManager
from src.config_manager import ConfigManager

class TestBackupManager(unittest.TestCase):
    """
    BackupManager 테스트 클래스
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, 'config')
        self.backup_dir = os.path.join(self.temp_dir, 'backups')
        self.db_backup_dir = os.path.join(self.backup_dir, 'database')
        self.config_backup_dir = os.path.join(self.backup_dir, 'config')
        self.export_dir = os.path.join(self.temp_dir, 'exports')
        
        # 디렉토리 생성
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.db_backup_dir, exist_ok=True)
        os.makedirs(self.config_backup_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)
        
        # 테스트 데이터베이스 생성
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self._create_test_database()
        
        # ConfigManager 초기화 (데이터베이스 사용 안 함)
        self.config_manager = ConfigManager(config_dir=self.config_dir, use_db=False)
        self.config_manager.set_config_value('system.database.path', self.db_path)
        
        # BackupManager 초기화
        self.backup_manager = BackupManager(self.config_manager)
        self.backup_manager.backup_dir = self.backup_dir
        self.backup_manager.db_backup_dir = self.db_backup_dir
        self.backup_manager.config_backup_dir = self.config_backup_dir
        self.backup_manager.export_dir = self.export_dir
    
    def tearDown(self):
        """
        테스트 정리
        """
        # 임시 디렉토리 삭제
        shutil.rmtree(self.temp_dir)
    
    def _create_test_database(self):
        """
        테스트용 데이터베이스 생성
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 테스트 테이블 생성
        cursor.execute('''
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
        cursor.execute('''
        INSERT INTO transactions (
            transaction_id, transaction_date, description, amount,
            transaction_type, category, payment_method, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'TEST001', '2024-01-01', '테스트 거래 1', 10000,
            'expense', '식비', '현금', 'manual'
        ))
        
        cursor.execute('''
        INSERT INTO transactions (
            transaction_id, transaction_date, description, amount,
            transaction_type, category, payment_method, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'TEST002', '2024-01-02', '테스트 거래 2', 20000,
            'expense', '교통비', '체크카드결제', 'manual'
        ))
        
        conn.commit()
        conn.close()
    
    def test_backup_restore_database(self):
        """
        데이터베이스 백업 및 복원 테스트
        """
        # 데이터베이스 백업
        backup_file = self.backup_manager.backup_database()
        self.assertTrue(backup_file)
        self.assertTrue(os.path.exists(backup_file))
        
        # 체크섬 파일 확인
        checksum_file = f"{backup_file}.checksum"
        self.assertTrue(os.path.exists(checksum_file))
        
        # 원본 데이터베이스 수정
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions")
        conn.commit()
        conn.close()
        
        # 데이터베이스 복원
        result = self.backup_manager.restore_database(backup_file)
        self.assertTrue(result)
        
        # 복원된 데이터 확인
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 2)
    
    def test_backup_restore_config(self):
        """
        설정 백업 및 복원 테스트
        """
        # 설정 값 변경
        self.config_manager.set_config_value('user.display.language', 'en')
        
        # 설정 백업
        backup_file = self.backup_manager.backup_config()
        self.assertTrue(backup_file)
        self.assertTrue(os.path.exists(backup_file))
        
        # 설정 값 변경
        self.config_manager.set_config_value('user.display.language', 'fr')
        
        # 설정 복원
        result = self.backup_manager.restore_config(backup_file)
        self.assertTrue(result)
        
        # 복원된 설정 확인
        language = self.config_manager.get_config_value('user.display.language')
        self.assertEqual(language, 'en')
    
    def test_export_import_data(self):
        """
        데이터 내보내기 및 가져오기 테스트
        """
        # CSV 형식으로 내보내기
        export_files = self.backup_manager.export_data('csv')
        self.assertTrue(export_files)
        
        # 원본 데이터베이스 수정
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions")
        conn.commit()
        conn.close()
        
        # 데이터 가져오기
        if 'zip' in export_files:
            result = self.backup_manager.import_data(export_files['zip'])
        else:
            result = self.backup_manager.import_data(list(export_files.values())[0])
        
        self.assertTrue(result)
        
        # 가져온 데이터 확인
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 2)
    
    def test_verify_backup(self):
        """
        백업 검증 테스트
        """
        # 데이터베이스 백업
        backup_file = self.backup_manager.backup_database()
        self.assertTrue(backup_file)
        
        # 백업 검증
        result = self.backup_manager.verify_backup(backup_file)
        self.assertTrue(result)
        
        # 백업 파일 수정
        with open(backup_file, 'a') as f:
            f.write('corrupted')
        
        # 수정된 백업 검증
        result = self.backup_manager.verify_backup(backup_file)
        self.assertFalse(result)
    
    def test_list_backups(self):
        """
        백업 목록 조회 테스트
        """
        # 데이터베이스 백업 생성
        backup_file1 = self.backup_manager.backup_database()
        backup_file2 = self.backup_manager.backup_database()
        
        # 백업 목록 조회
        backups = self.backup_manager.list_backups()
        self.assertEqual(len(backups), 2)
        
        # 설정 백업 생성
        config_backup = self.backup_manager.backup_config()
        
        # 설정 백업 목록 조회
        config_backups = self.backup_manager.list_backups('config')
        self.assertGreaterEqual(len(config_backups), 1)
    
    def test_incremental_backup(self):
        """
        증분 백업 테스트
        """
        # 전체 백업
        full_backup = self.backup_manager.backup_database(self.backup_manager.BACKUP_TYPE_FULL)
        self.assertTrue(full_backup)
        
        # 데이터베이스 수정
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO transactions (
            transaction_id, transaction_date, description, amount,
            transaction_type, category, payment_method, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'TEST003', '2024-01-03', '테스트 거래 3', 30000,
            'expense', '식비', '현금', 'manual'
        ))
        conn.commit()
        conn.close()
        
        # 증분 백업
        incremental_backup = self.backup_manager.backup_database(self.backup_manager.BACKUP_TYPE_INCREMENTAL)
        self.assertTrue(incremental_backup)
        
        # 원본 데이터베이스 수정
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions")
        conn.commit()
        conn.close()
        
        # 증분 백업 복원
        result = self.backup_manager.restore_database(incremental_backup)
        self.assertTrue(result)
        
        # 복원된 데이터 확인
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 3)

if __name__ == '__main__':
    unittest.main()