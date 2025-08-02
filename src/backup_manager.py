# -*- coding: utf-8 -*-
"""
백업 관리 시스템

데이터베이스 및 설정 파일의 백업 및 복원을 관리하는 시스템입니다.
자동 백업 스케줄링, 데이터 내보내기/가져오기, 증분 백업, 무결성 검증 기능을 제공합니다.
"""

import os
import sys
import logging
import shutil
import sqlite3
import json
import csv
import zipfile
import hashlib
import time
import threading
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.config_manager import ConfigManager
from src.repositories.db_connection import DatabaseConnection

class BackupManager:
    """
    백업 관리자 클래스
    
    데이터베이스 및 설정 파일의 백업 및 복원을 관리합니다.
    자동 백업 스케줄링, 데이터 내보내기/가져오기, 증분 백업, 무결성 검증 기능을 제공합니다.
    """
    
    # 기본 백업 디렉토리
    DEFAULT_BACKUP_DIR = os.path.join(parent_dir, 'backups')
    
    # 기본 데이터베이스 백업 디렉토리
    DEFAULT_DB_BACKUP_DIR = os.path.join(DEFAULT_BACKUP_DIR, 'database')
    
    # 기본 설정 백업 디렉토리
    DEFAULT_CONFIG_BACKUP_DIR = os.path.join(DEFAULT_BACKUP_DIR, 'config')
    
    # 기본 내보내기 디렉토리
    DEFAULT_EXPORT_DIR = os.path.join(parent_dir, 'exports')
    
    # 백업 유형
    BACKUP_TYPE_FULL = 'full'
    BACKUP_TYPE_INCREMENTAL = 'incremental'
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        백업 관리자 초기화
        
        Args:
            config_manager: 설정 관리자 (기본값: None, 새로 생성)
        """
        self.config_manager = config_manager or ConfigManager()
        
        # 백업 디렉토리 설정
        self.backup_dir = self.DEFAULT_BACKUP_DIR
        self.db_backup_dir = self.DEFAULT_DB_BACKUP_DIR
        self.config_backup_dir = self.DEFAULT_CONFIG_BACKUP_DIR
        self.export_dir = self.DEFAULT_EXPORT_DIR
        
        # 디렉토리 생성
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.db_backup_dir, exist_ok=True)
        os.makedirs(self.config_backup_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)
        
        # 데이터베이스 경로
        self.db_path = self.config_manager.get_config_value('system.database.path')
        
        # 백업 설정
        self.backup_enabled = self.config_manager.get_config_value('system.database.backup_enabled', True)
        self.backup_interval_days = self.config_manager.get_config_value('system.database.backup_interval_days', 7)
        self.max_backups = self.config_manager.get_config_value('system.database.max_backups', 5)
        
        # 스케줄러 스레드
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # 마지막 백업 정보
        self.last_backup_info = self._load_last_backup_info()
    
    def backup_database(self, backup_type: str = BACKUP_TYPE_FULL) -> str:
        """
        데이터베이스를 백업합니다.
        
        Args:
            backup_type: 백업 유형 (full/incremental)
            
        Returns:
            str: 백업 파일 경로
        """
        try:
            if not os.path.exists(self.db_path):
                logger.error(f"데이터베이스 파일을 찾을 수 없습니다: {self.db_path}")
                return ""
            
            # 백업 파일명 생성
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"db_backup_{backup_type}_{timestamp}.db"
            backup_file = os.path.join(self.db_backup_dir, backup_filename)
            
            # 데이터베이스 백업
            if backup_type == self.BACKUP_TYPE_FULL:
                # 전체 백업
                shutil.copy2(self.db_path, backup_file)
                logger.info(f"데이터베이스 전체 백업 완료: {backup_file}")
            else:
                # 증분 백업 (변경된 테이블만)
                self._create_incremental_backup(backup_file)
                logger.info(f"데이터베이스 증분 백업 완료: {backup_file}")
            
            # 백업 파일 압축
            zip_file = self._compress_backup(backup_file)
            
            # 원본 백업 파일 삭제
            if os.path.exists(zip_file):
                os.remove(backup_file)
                backup_file = zip_file
            
            # 백업 체크섬 생성
            checksum = self._create_checksum(backup_file)
            
            # 백업 정보 저장
            backup_info = {
                'file': backup_file,
                'type': backup_type,
                'timestamp': datetime.now().isoformat(),
                'checksum': checksum,
                'size': os.path.getsize(backup_file)
            }
            
            self.last_backup_info = backup_info
            self._save_last_backup_info()
            
            # 오래된 백업 정리
            self._cleanup_old_backups()
            
            return backup_file
            
        except Exception as e:
            logger.error(f"데이터베이스 백업 중 오류 발생: {e}")
            return ""
    
    def restore_database(self, backup_file: str) -> bool:
        """
        백업에서 데이터베이스를 복원합니다.
        
        Args:
            backup_file: 백업 파일 경로
            
        Returns:
            bool: 복원 성공 여부
        """
        try:
            if not os.path.exists(backup_file):
                logger.error(f"백업 파일을 찾을 수 없습니다: {backup_file}")
                return False
            
            # 현재 데이터베이스 백업
            current_backup = self.backup_database()
            
            # 압축 파일 확인
            if backup_file.endswith('.zip'):
                # 압축 해제
                extracted_file = self._extract_backup(backup_file)
                if not extracted_file:
                    logger.error("백업 파일 압축 해제 실패")
                    return False
                
                backup_file = extracted_file
            
            # 체크섬 검증
            if not self._verify_checksum(backup_file):
                logger.error("백업 파일 체크섬 검증 실패")
                return False
            
            # 데이터베이스 복원
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            
            shutil.copy2(backup_file, self.db_path)
            
            # 임시 파일 정리
            if backup_file != self.db_path and backup_file.startswith(os.path.join(self.backup_dir, 'temp')):
                os.remove(backup_file)
            
            logger.info(f"데이터베이스 복원 완료: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"데이터베이스 복원 중 오류 발생: {e}")
            return False
    
    def backup_config(self) -> str:
        """
        설정 파일을 백업합니다.
        
        Returns:
            str: 백업 파일 경로
        """
        try:
            # 설정 관리자를 통해 백업
            backup_file = self.config_manager.backup_config()
            
            if not backup_file:
                logger.error("설정 백업 실패")
                return ""
            
            logger.info(f"설정 백업 완료: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"설정 백업 중 오류 발생: {e}")
            return ""
    
    def restore_config(self, backup_file: str) -> bool:
        """
        백업에서 설정을 복원합니다.
        
        Args:
            backup_file: 백업 파일 경로
            
        Returns:
            bool: 복원 성공 여부
        """
        try:
            # 설정 관리자를 통해 복원
            result = self.config_manager.restore_config(backup_file)
            
            if result:
                logger.info(f"설정 복원 완료: {backup_file}")
            else:
                logger.error(f"설정 복원 실패: {backup_file}")
            
            return result
            
        except Exception as e:
            logger.error(f"설정 복원 중 오류 발생: {e}")
            return False
    
    def export_data(self, format: str = 'csv', tables: List[str] = None) -> Dict[str, str]:
        """
        데이터를 내보냅니다.
        
        Args:
            format: 내보내기 형식 (csv/json)
            tables: 내보낼 테이블 목록 (None: 모든 테이블)
            
        Returns:
            Dict[str, str]: 테이블별 내보내기 파일 경로
        """
        try:
            # 내보내기 디렉토리 생성
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_subdir = os.path.join(self.export_dir, f"export_{timestamp}")
            os.makedirs(export_subdir, exist_ok=True)
            
            # 데이터베이스 연결
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 테이블 목록 조회
            if not tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
            
            export_files = {}
            
            for table in tables:
                try:
                    # 테이블 데이터 조회
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    
                    if not rows:
                        logger.info(f"테이블 '{table}'에 데이터가 없습니다.")
                        continue
                    
                    # 열 이름 가져오기
                    columns = [column[0] for column in cursor.description]
                    
                    # 내보내기 파일 경로
                    if format.lower() == 'json':
                        export_file = os.path.join(export_subdir, f"{table}.json")
                        
                        # JSON 형식으로 내보내기
                        data = []
                        for row in rows:
                            data.append({columns[i]: row[i] for i in range(len(columns))})
                        
                        with open(export_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                    else:
                        export_file = os.path.join(export_subdir, f"{table}.csv")
                        
                        # CSV 형식으로 내보내기
                        with open(export_file, 'w', encoding='utf-8', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow(columns)
                            writer.writerows(rows)
                    
                    export_files[table] = export_file
                    logger.info(f"테이블 '{table}' 내보내기 완료: {export_file}")
                    
                except Exception as e:
                    logger.error(f"테이블 '{table}' 내보내기 중 오류 발생: {e}")
            
            conn.close()
            
            # 내보내기 파일 압축
            if export_files:
                zip_file = os.path.join(self.export_dir, f"export_{timestamp}.zip")
                with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for table, file_path in export_files.items():
                        zipf.write(file_path, os.path.basename(file_path))
                
                logger.info(f"내보내기 파일 압축 완료: {zip_file}")
                
                # 임시 디렉토리 정리
                shutil.rmtree(export_subdir)
                
                return {'zip': zip_file}
            
            return export_files
            
        except Exception as e:
            logger.error(f"데이터 내보내기 중 오류 발생: {e}")
            return {}
    
    def import_data(self, import_file: str, table: str = None) -> bool:
        """
        데이터를 가져옵니다.
        
        Args:
            import_file: 가져올 파일 경로
            table: 가져올 테이블 이름 (None: 파일명에서 추론)
            
        Returns:
            bool: 가져오기 성공 여부
        """
        try:
            if not os.path.exists(import_file):
                logger.error(f"가져올 파일을 찾을 수 없습니다: {import_file}")
                return False
            
            # 현재 데이터베이스 백업
            current_backup = self.backup_database()
            
            # 압축 파일 확인
            if import_file.endswith('.zip'):
                # 임시 디렉토리 생성
                temp_dir = os.path.join(self.backup_dir, 'temp', f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                os.makedirs(temp_dir, exist_ok=True)
                
                # 압축 해제
                with zipfile.ZipFile(import_file, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # 가져오기 결과
                import_results = []
                
                # 각 파일 가져오기
                for file_name in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file_name)
                    table_name = os.path.splitext(file_name)[0]
                    result = self._import_single_file(file_path, table_name)
                    import_results.append(result)
                
                # 임시 디렉토리 정리
                shutil.rmtree(temp_dir)
                
                return all(import_results)
            else:
                # 테이블 이름 추론
                if not table:
                    table = os.path.splitext(os.path.basename(import_file))[0]
                
                # 단일 파일 가져오기
                return self._import_single_file(import_file, table)
            
        except Exception as e:
            logger.error(f"데이터 가져오기 중 오류 발생: {e}")
            return False
    
    def _import_single_file(self, file_path: str, table: str) -> bool:
        """
        단일 파일에서 데이터를 가져옵니다.
        
        Args:
            file_path: 가져올 파일 경로
            table: 가져올 테이블 이름
            
        Returns:
            bool: 가져오기 성공 여부
        """
        try:
            # 파일 형식 확인
            if file_path.endswith('.json'):
                # JSON 파일 읽기
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not data or not isinstance(data, list):
                    logger.error(f"유효하지 않은 JSON 데이터: {file_path}")
                    return False
                
                # 열 이름 가져오기
                columns = list(data[0].keys())
                
                # 데이터베이스 연결
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 테이블 존재 여부 확인
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    logger.error(f"테이블이 존재하지 않습니다: {table}")
                    conn.close()
                    return False
                
                # 테이블 스키마 확인
                cursor.execute(f"PRAGMA table_info({table})")
                table_columns = [row[1] for row in cursor.fetchall()]
                
                # 공통 열만 사용
                common_columns = [col for col in columns if col in table_columns]
                
                if not common_columns:
                    logger.error(f"테이블 '{table}'과 일치하는 열이 없습니다.")
                    conn.close()
                    return False
                
                # 데이터 삽입
                placeholders = ', '.join(['?' for _ in common_columns])
                columns_str = ', '.join(common_columns)
                
                for row in data:
                    values = [row.get(col) for col in common_columns]
                    cursor.execute(f"INSERT OR REPLACE INTO {table} ({columns_str}) VALUES ({placeholders})", values)
                
                conn.commit()
                conn.close()
                
                logger.info(f"JSON 데이터 가져오기 완료: {file_path} -> {table}")
                return True
                
            elif file_path.endswith('.csv'):
                # CSV 파일 읽기
                with open(file_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.reader(f)
                    columns = next(reader)  # 헤더 행
                    rows = list(reader)
                
                # 데이터베이스 연결
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 테이블 존재 여부 확인
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    logger.error(f"테이블이 존재하지 않습니다: {table}")
                    conn.close()
                    return False
                
                # 테이블 스키마 확인
                cursor.execute(f"PRAGMA table_info({table})")
                table_columns = [row[1] for row in cursor.fetchall()]
                
                # 공통 열만 사용
                common_columns = [col for col in columns if col in table_columns]
                common_indices = [columns.index(col) for col in common_columns]
                
                if not common_columns:
                    logger.error(f"테이블 '{table}'과 일치하는 열이 없습니다.")
                    conn.close()
                    return False
                
                # 데이터 삽입
                placeholders = ', '.join(['?' for _ in common_columns])
                columns_str = ', '.join(common_columns)
                
                for row in rows:
                    values = [row[i] for i in common_indices]
                    cursor.execute(f"INSERT OR REPLACE INTO {table} ({columns_str}) VALUES ({placeholders})", values)
                
                conn.commit()
                conn.close()
                
                logger.info(f"CSV 데이터 가져오기 완료: {file_path} -> {table}")
                return True
                
            else:
                logger.error(f"지원하지 않는 파일 형식: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"파일 '{file_path}' 가져오기 중 오류 발생: {e}")
            return False
    
    def start_scheduler(self) -> bool:
        """
        자동 백업 스케줄러를 시작합니다.
        
        Returns:
            bool: 시작 성공 여부
        """
        try:
            if self.scheduler_running:
                logger.warning("스케줄러가 이미 실행 중입니다.")
                return True
            
            if not self.backup_enabled:
                logger.info("자동 백업이 비활성화되어 있습니다.")
                return False
            
            # 백업 스케줄 설정
            schedule.every(self.backup_interval_days).days.do(self._scheduled_backup)
            
            # 스케줄러 스레드 시작
            self.scheduler_running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info(f"자동 백업 스케줄러 시작됨 (간격: {self.backup_interval_days}일)")
            return True
            
        except Exception as e:
            logger.error(f"스케줄러 시작 중 오류 발생: {e}")
            return False
    
    def stop_scheduler(self) -> bool:
        """
        자동 백업 스케줄러를 중지합니다.
        
        Returns:
            bool: 중지 성공 여부
        """
        try:
            if not self.scheduler_running:
                logger.warning("스케줄러가 실행 중이 아닙니다.")
                return True
            
            # 스케줄러 중지
            self.scheduler_running = False
            schedule.clear()
            
            # 스레드 종료 대기
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=1.0)
            
            logger.info("자동 백업 스케줄러 중지됨")
            return True
            
        except Exception as e:
            logger.error(f"스케줄러 중지 중 오류 발생: {e}")
            return False
    
    def list_backups(self, backup_type: str = 'database') -> List[Dict[str, Any]]:
        """
        백업 목록을 반환합니다.
        
        Args:
            backup_type: 백업 유형 (database/config)
            
        Returns:
            List[Dict[str, Any]]: 백업 정보 목록
        """
        try:
            if backup_type == 'config':
                # 설정 백업 목록
                return self.config_manager.list_backups()
            else:
                # 데이터베이스 백업 목록
                backups = []
                
                if not os.path.exists(self.db_backup_dir):
                    return []
                
                for item in os.listdir(self.db_backup_dir):
                    if item.startswith('db_backup_') and (item.endswith('.db') or item.endswith('.zip')):
                        backup_file = os.path.join(self.db_backup_dir, item)
                        file_stat = os.stat(backup_file)
                        
                        # 백업 유형 및 타임스탬프 추출
                        parts = item.split('_')
                        if len(parts) >= 4:
                            backup_type = parts[2]
                            timestamp_str = parts[3].split('.')[0]
                            try:
                                timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                            except ValueError:
                                timestamp = datetime.fromtimestamp(file_stat.st_mtime)
                        else:
                            backup_type = 'unknown'
                            timestamp = datetime.fromtimestamp(file_stat.st_mtime)
                        
                        # 체크섬 파일 확인
                        checksum_file = f"{backup_file}.checksum"
                        checksum = None
                        if os.path.exists(checksum_file):
                            with open(checksum_file, 'r') as f:
                                checksum = f.read().strip()
                        
                        backups.append({
                            'file': backup_file,
                            'filename': item,
                            'type': backup_type,
                            'timestamp': timestamp,
                            'size': file_stat.st_size,
                            'checksum': checksum
                        })
                
                # 최신 순으로 정렬
                backups.sort(key=lambda x: x['timestamp'], reverse=True)
                
                return backups
                
        except Exception as e:
            logger.error(f"백업 목록 조회 중 오류 발생: {e}")
            return []
    
    def verify_backup(self, backup_file: str) -> bool:
        """
        백업 파일의 무결성을 검증합니다.
        
        Args:
            backup_file: 백업 파일 경로
            
        Returns:
            bool: 검증 성공 여부
        """
        try:
            if not os.path.exists(backup_file):
                logger.error(f"백업 파일을 찾을 수 없습니다: {backup_file}")
                return False
            
            # 체크섬 검증
            return self._verify_checksum(backup_file)
            
        except Exception as e:
            logger.error(f"백업 검증 중 오류 발생: {e}")
            return False
    
    def _create_incremental_backup(self, backup_file: str) -> bool:
        """
        증분 백업을 생성합니다.
        
        Args:
            backup_file: 백업 파일 경로
            
        Returns:
            bool: 생성 성공 여부
        """
        try:
            # 마지막 백업 이후 변경된 테이블만 백업
            if not self.last_backup_info:
                # 마지막 백업 정보가 없으면 전체 백업
                shutil.copy2(self.db_path, backup_file)
                return True
            
            # 소스 데이터베이스 연결
            src_conn = sqlite3.connect(self.db_path)
            src_cursor = src_conn.cursor()
            
            # 대상 데이터베이스 생성
            dst_conn = sqlite3.connect(backup_file)
            dst_cursor = dst_conn.cursor()
            
            # 테이블 목록 조회
            src_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in src_cursor.fetchall()]
            
            # 마지막 백업 시간
            last_backup_time = datetime.fromisoformat(self.last_backup_info['timestamp'])
            
            for table in tables:
                try:
                    # 테이블 스키마 복사
                    src_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                    schema = src_cursor.fetchone()[0]
                    dst_cursor.execute(schema)
                    
                    # 변경된 데이터 확인
                    if 'updated_at' in schema:
                        # updated_at 열이 있는 경우
                        src_cursor.execute(f"SELECT * FROM {table} WHERE updated_at >= ?", 
                                          (last_backup_time.strftime('%Y-%m-%d %H:%M:%S'),))
                    else:
                        # 모든 데이터 복사
                        src_cursor.execute(f"SELECT * FROM {table}")
                    
                    rows = src_cursor.fetchall()
                    
                    if rows:
                        # 열 이름 가져오기
                        columns = [column[0] for column in src_cursor.description]
                        placeholders = ', '.join(['?' for _ in columns])
                        columns_str = ', '.join(columns)
                        
                        # 데이터 삽입
                        dst_cursor.executemany(
                            f"INSERT OR REPLACE INTO {table} ({columns_str}) VALUES ({placeholders})",
                            rows
                        )
                        
                        logger.debug(f"테이블 '{table}' 증분 백업 완료: {len(rows)}행")
                    
                except Exception as e:
                    logger.error(f"테이블 '{table}' 증분 백업 중 오류 발생: {e}")
            
            # 변경사항 저장
            dst_conn.commit()
            
            # 연결 종료
            src_conn.close()
            dst_conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"증분 백업 생성 중 오류 발생: {e}")
            return False
    
    def _compress_backup(self, backup_file: str) -> str:
        """
        백업 파일을 압축합니다.
        
        Args:
            backup_file: 백업 파일 경로
            
        Returns:
            str: 압축 파일 경로
        """
        try:
            zip_file = f"{backup_file}.zip"
            
            with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_file, os.path.basename(backup_file))
            
            logger.debug(f"백업 파일 압축 완료: {zip_file}")
            return zip_file
            
        except Exception as e:
            logger.error(f"백업 파일 압축 중 오류 발생: {e}")
            return ""
    
    def _extract_backup(self, zip_file: str) -> str:
        """
        압축된 백업 파일을 추출합니다.
        
        Args:
            zip_file: 압축 파일 경로
            
        Returns:
            str: 추출된 파일 경로
        """
        try:
            # 임시 디렉토리 생성
            temp_dir = os.path.join(self.backup_dir, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # 압축 해제
            with zipfile.ZipFile(zip_file, 'r') as zipf:
                file_list = zipf.namelist()
                if not file_list:
                    logger.error("압축 파일이 비어 있습니다.")
                    return ""
                
                # 첫 번째 파일 추출
                file_name = file_list[0]
                extracted_file = os.path.join(temp_dir, file_name)
                zipf.extract(file_name, temp_dir)
            
            logger.debug(f"백업 파일 압축 해제 완료: {extracted_file}")
            return extracted_file
            
        except Exception as e:
            logger.error(f"백업 파일 압축 해제 중 오류 발생: {e}")
            return ""
    
    def _create_checksum(self, file_path: str) -> str:
        """
        파일의 체크섬을 생성합니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            str: 체크섬 문자열
        """
        try:
            hasher = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                # 청크 단위로 읽어서 해시 계산
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            
            checksum = hasher.hexdigest()
            
            # 체크섬 파일 저장
            checksum_file = f"{file_path}.checksum"
            with open(checksum_file, 'w') as f:
                f.write(checksum)
            
            logger.debug(f"체크섬 생성 완료: {checksum}")
            return checksum
            
        except Exception as e:
            logger.error(f"체크섬 생성 중 오류 발생: {e}")
            return ""
    
    def _verify_checksum(self, file_path: str) -> bool:
        """
        파일의 체크섬을 검증합니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            bool: 검증 성공 여부
        """
        try:
            # 체크섬 파일 확인
            checksum_file = f"{file_path}.checksum"
            
            if not os.path.exists(checksum_file):
                # 체크섬 파일이 없으면 새로 생성
                self._create_checksum(file_path)
                return True
            
            # 저장된 체크섬 읽기
            with open(checksum_file, 'r') as f:
                stored_checksum = f.read().strip()
            
            # 현재 체크섬 계산
            hasher = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            
            current_checksum = hasher.hexdigest()
            
            # 체크섬 비교
            if stored_checksum == current_checksum:
                logger.debug(f"체크섬 검증 성공: {file_path}")
                return True
            else:
                logger.error(f"체크섬 검증 실패: {file_path}")
                return False
            
        except Exception as e:
            logger.error(f"체크섬 검증 중 오류 발생: {e}")
            return False
    
    def _load_last_backup_info(self) -> Dict[str, Any]:
        """
        마지막 백업 정보를 로드합니다.
        
        Returns:
            Dict[str, Any]: 백업 정보
        """
        try:
            info_file = os.path.join(self.db_backup_dir, 'last_backup_info.json')
            
            if not os.path.exists(info_file):
                return {}
            
            with open(info_file, 'r', encoding='utf-8') as f:
                info = json.load(f)
            
            return info
            
        except Exception as e:
            logger.error(f"마지막 백업 정보 로드 중 오류 발생: {e}")
            return {}
    
    def _save_last_backup_info(self) -> bool:
        """
        마지막 백업 정보를 저장합니다.
        
        Returns:
            bool: 저장 성공 여부
        """
        try:
            info_file = os.path.join(self.db_backup_dir, 'last_backup_info.json')
            
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(self.last_backup_info, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"마지막 백업 정보 저장 중 오류 발생: {e}")
            return False
    
    def _cleanup_old_backups(self) -> None:
        """
        오래된 백업 파일을 정리합니다.
        """
        try:
            backups = self.list_backups()
            
            if len(backups) > self.max_backups:
                # 오래된 백업 삭제
                for backup in backups[self.max_backups:]:
                    try:
                        os.remove(backup['file'])
                        logger.debug(f"오래된 백업 삭제: {backup['filename']}")
                        
                        # 체크섬 파일 삭제
                        checksum_file = f"{backup['file']}.checksum"
                        if os.path.exists(checksum_file):
                            os.remove(checksum_file)
                    except Exception as e:
                        logger.error(f"백업 삭제 중 오류 발생: {e}")
                
        except Exception as e:
            logger.error(f"백업 정리 중 오류 발생: {e}")
    
    def _run_scheduler(self) -> None:
        """
        스케줄러 스레드 실행 함수
        """
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 스케줄 확인
    
    def _scheduled_backup(self) -> None:
        """
        예약된 백업 실행 함수
        """
        try:
            logger.info("예약된 백업 시작")
            
            # 데이터베이스 백업
            db_backup = self.backup_database()
            
            # 설정 백업
            config_backup = self.backup_config()
            
            logger.info("예약된 백업 완료")
            
        except Exception as e:
            logger.error(f"예약된 백업 중 오류 발생: {e}")

def main():
    """
    메인 함수
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='백업 관리 도구')
    
    parser.add_argument('--action', '-a', choices=[
        'backup-db', 'restore-db', 'backup-config', 'restore-config',
        'export', 'import', 'list', 'verify', 'start-scheduler', 'stop-scheduler'
    ], default='list', help='수행할 작업')
    
    parser.add_argument('--type', '-t', choices=['full', 'incremental'], default='full',
                       help='백업 유형 (기본값: full)')
    parser.add_argument('--file', '-f', help='파일 경로')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='내보내기/가져오기 형식')
    parser.add_argument('--table', help='테이블 이름')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 출력')
    
    args = parser.parse_args()
    
    # 로깅 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 설정 관리자 초기화
    config_manager = ConfigManager()
    
    # 백업 관리자 초기화
    backup_manager = BackupManager(config_manager)
    
    # 작업 수행
    if args.action == 'backup-db':
        backup_file = backup_manager.backup_database(args.type)
        if backup_file:
            print(f"데이터베이스 백업 완료: {backup_file}")
        else:
            print("데이터베이스 백업 실패")
    
    elif args.action == 'restore-db':
        if not args.file:
            backups = backup_manager.list_backups()
            if not backups:
                print("사용 가능한 백업이 없습니다.")
                return
            
            print("사용 가능한 백업:")
            for i, backup in enumerate(backups, 1):
                print(f"{i}. {backup['filename']} ({backup['timestamp']})")
            
            choice = input("복원할 백업 번호를 선택하세요: ")
            try:
                index = int(choice) - 1
                if 0 <= index < len(backups):
                    backup_file = backups[index]['file']
                else:
                    print("올바른 백업 번호를 선택해주세요.")
                    return
            except ValueError:
                print("숫자를 입력해주세요.")
                return
        else:
            backup_file = args.file
        
        if backup_manager.restore_database(backup_file):
            print(f"데이터베이스 복원 완료: {backup_file}")
        else:
            print("데이터베이스 복원 실패")
    
    elif args.action == 'backup-config':
        backup_file = backup_manager.backup_config()
        if backup_file:
            print(f"설정 백업 완료: {backup_file}")
        else:
            print("설정 백업 실패")
    
    elif args.action == 'restore-config':
        if not args.file:
            backups = backup_manager.list_backups('config')
            if not backups:
                print("사용 가능한 설정 백업이 없습니다.")
                return
            
            print("사용 가능한 설정 백업:")
            for i, backup in enumerate(backups, 1):
                print(f"{i}. {backup['filename']} ({backup['timestamp']})")
            
            choice = input("복원할 설정 백업 번호를 선택하세요: ")
            try:
                index = int(choice) - 1
                if 0 <= index < len(backups):
                    backup_file = backups[index]['file']
                else:
                    print("올바른 백업 번호를 선택해주세요.")
                    return
            except ValueError:
                print("숫자를 입력해주세요.")
                return
        else:
            backup_file = args.file
        
        if backup_manager.restore_config(backup_file):
            print(f"설정 복원 완료: {backup_file}")
        else:
            print("설정 복원 실패")
    
    elif args.action == 'export':
        tables = [args.table] if args.table else None
        export_files = backup_manager.export_data(args.format, tables)
        
        if export_files:
            if 'zip' in export_files:
                print(f"데이터 내보내기 완료: {export_files['zip']}")
            else:
                print("데이터 내보내기 완료:")
                for table, file_path in export_files.items():
                    print(f"  - {table}: {file_path}")
        else:
            print("데이터 내보내기 실패")
    
    elif args.action == 'import':
        if not args.file:
            print("가져올 파일 경로를 지정해야 합니다.")
            return
        
        if backup_manager.import_data(args.file, args.table):
            print(f"데이터 가져오기 완료: {args.file}")
        else:
            print("데이터 가져오기 실패")
    
    elif args.action == 'list':
        print("데이터베이스 백업 목록:")
        db_backups = backup_manager.list_backups()
        
        if db_backups:
            for i, backup in enumerate(db_backups, 1):
                print(f"{i}. {backup['filename']} ({backup['timestamp']}, {backup['type']})")
        else:
            print("  사용 가능한 데이터베이스 백업이 없습니다.")
        
        print("\n설정 백업 목록:")
        config_backups = backup_manager.list_backups('config')
        
        if config_backups:
            for i, backup in enumerate(config_backups, 1):
                print(f"{i}. {backup['filename']} ({backup['timestamp']})")
        else:
            print("  사용 가능한 설정 백업이 없습니다.")
    
    elif args.action == 'verify':
        if not args.file:
            print("검증할 백업 파일 경로를 지정해야 합니다.")
            return
        
        if backup_manager.verify_backup(args.file):
            print(f"백업 파일 검증 성공: {args.file}")
        else:
            print(f"백업 파일 검증 실패: {args.file}")
    
    elif args.action == 'start-scheduler':
        if backup_manager.start_scheduler():
            print("자동 백업 스케줄러 시작됨")
        else:
            print("자동 백업 스케줄러 시작 실패")
    
    elif args.action == 'stop-scheduler':
        if backup_manager.stop_scheduler():
            print("자동 백업 스케줄러 중지됨")
        else:
            print("자동 백업 스케줄러 중지 실패")

if __name__ == '__main__':
    main()