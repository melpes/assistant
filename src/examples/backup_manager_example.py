# -*- coding: utf-8 -*-
"""
BackupManager 사용 예제

백업 관리 시스템의 기본 사용법을 보여주는 예제입니다.
"""

import os
import sys
import logging
from datetime import datetime

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.backup_manager import BackupManager
from src.config_manager import ConfigManager

def basic_usage_example():
    """
    기본 사용법 예제
    """
    print("=== BackupManager 기본 사용법 ===")
    
    # ConfigManager 초기화
    config_manager = ConfigManager()
    
    # BackupManager 초기화
    backup_manager = BackupManager(config_manager)
    
    # 데이터베이스 경로 확인
    db_path = backup_manager.db_path
    print(f"데이터베이스 경로: {db_path}")
    
    # 백업 설정 확인
    backup_enabled = backup_manager.backup_enabled
    backup_interval = backup_manager.backup_interval_days
    max_backups = backup_manager.max_backups
    
    print(f"자동 백업 활성화: {backup_enabled}")
    print(f"백업 간격: {backup_interval}일")
    print(f"최대 백업 수: {max_backups}")

def backup_restore_example():
    """
    백업 및 복원 예제
    """
    print("\n=== 백업 및 복원 예제 ===")
    
    # ConfigManager 초기화
    config_manager = ConfigManager()
    
    # BackupManager 초기화
    backup_manager = BackupManager(config_manager)
    
    # 데이터베이스 백업
    print("데이터베이스 백업 중...")
    db_backup = backup_manager.backup_database()
    
    if db_backup:
        print(f"데이터베이스 백업 완료: {db_backup}")
        
        # 백업 검증
        if backup_manager.verify_backup(db_backup):
            print("백업 파일 검증 성공")
        else:
            print("백업 파일 검증 실패")
    else:
        print("데이터베이스 백업 실패")
    
    # 설정 백업
    print("\n설정 백업 중...")
    config_backup = backup_manager.backup_config()
    
    if config_backup:
        print(f"설정 백업 완료: {config_backup}")
    else:
        print("설정 백업 실패")
    
    # 백업 목록 조회
    print("\n데이터베이스 백업 목록:")
    db_backups = backup_manager.list_backups()
    
    if db_backups:
        for i, backup in enumerate(db_backups, 1):
            print(f"  {i}. {backup['filename']} ({backup['timestamp']})")
    else:
        print("  사용 가능한 데이터베이스 백업이 없습니다.")
    
    print("\n설정 백업 목록:")
    config_backups = backup_manager.list_backups('config')
    
    if config_backups:
        for i, backup in enumerate(config_backups, 1):
            print(f"  {i}. {backup['filename']} ({backup['timestamp']})")
    else:
        print("  사용 가능한 설정 백업이 없습니다.")
    
    # 복원 예제 (실제로 복원하지는 않음)
    print("\n복원 예제 (실행되지 않음):")
    print("  backup_manager.restore_database(db_backup)")
    print("  backup_manager.restore_config(config_backup)")

def export_import_example():
    """
    내보내기 및 가져오기 예제
    """
    print("\n=== 내보내기 및 가져오기 예제 ===")
    
    # ConfigManager 초기화
    config_manager = ConfigManager()
    
    # BackupManager 초기화
    backup_manager = BackupManager(config_manager)
    
    # CSV 형식으로 내보내기
    print("CSV 형식으로 데이터 내보내기 중...")
    csv_files = backup_manager.export_data('csv')
    
    if csv_files:
        if 'zip' in csv_files:
            print(f"데이터 내보내기 완료: {csv_files['zip']}")
        else:
            print("데이터 내보내기 완료:")
            for table, file_path in csv_files.items():
                print(f"  - {table}: {file_path}")
    else:
        print("데이터 내보내기 실패")
    
    # JSON 형식으로 내보내기
    print("\nJSON 형식으로 데이터 내보내기 중...")
    json_files = backup_manager.export_data('json')
    
    if json_files:
        if 'zip' in json_files:
            print(f"데이터 내보내기 완료: {json_files['zip']}")
        else:
            print("데이터 내보내기 완료:")
            for table, file_path in json_files.items():
                print(f"  - {table}: {file_path}")
    else:
        print("데이터 내보내기 실패")
    
    # 가져오기 예제 (실제로 가져오지는 않음)
    print("\n가져오기 예제 (실행되지 않음):")
    if 'zip' in csv_files:
        print(f"  backup_manager.import_data('{csv_files['zip']}')")
    elif csv_files:
        print(f"  backup_manager.import_data('{list(csv_files.values())[0]}')")

def scheduler_example():
    """
    스케줄러 예제
    """
    print("\n=== 스케줄러 예제 ===")
    
    # ConfigManager 초기화
    config_manager = ConfigManager()
    
    # BackupManager 초기화
    backup_manager = BackupManager(config_manager)
    
    # 스케줄러 시작
    print("자동 백업 스케줄러 시작 중...")
    if backup_manager.start_scheduler():
        print(f"스케줄러 시작됨 (간격: {backup_manager.backup_interval_days}일)")
        
        # 스케줄러 중지 (예제이므로 바로 중지)
        print("자동 백업 스케줄러 중지 중...")
        if backup_manager.stop_scheduler():
            print("스케줄러 중지됨")
        else:
            print("스케줄러 중지 실패")
    else:
        print("스케줄러 시작 실패")

def incremental_backup_example():
    """
    증분 백업 예제
    """
    print("\n=== 증분 백업 예제 ===")
    
    # ConfigManager 초기화
    config_manager = ConfigManager()
    
    # BackupManager 초기화
    backup_manager = BackupManager(config_manager)
    
    # 전체 백업
    print("전체 백업 중...")
    full_backup = backup_manager.backup_database(backup_manager.BACKUP_TYPE_FULL)
    
    if full_backup:
        print(f"전체 백업 완료: {full_backup}")
        
        # 증분 백업
        print("\n증분 백업 중...")
        incremental_backup = backup_manager.backup_database(backup_manager.BACKUP_TYPE_INCREMENTAL)
        
        if incremental_backup:
            print(f"증분 백업 완료: {incremental_backup}")
        else:
            print("증분 백업 실패")
    else:
        print("전체 백업 실패")

def main():
    """
    메인 함수
    """
    # 로깅 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 예제 실행
    basic_usage_example()
    backup_restore_example()
    export_import_example()
    scheduler_example()
    incremental_backup_example()
    
    print("\n모든 예제가 완료되었습니다.")

if __name__ == '__main__':
    main()