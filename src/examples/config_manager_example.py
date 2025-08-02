# -*- coding: utf-8 -*-
"""
ConfigManager 사용 예제

설정 관리 시스템의 기본 사용법을 보여주는 예제입니다.
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

from src.config_manager import ConfigManager

def basic_usage_example():
    """
    기본 사용법 예제
    """
    print("=== ConfigManager 기본 사용법 ===")
    
    # ConfigManager 초기화
    config_manager = ConfigManager()
    
    # 설정 로드
    config = config_manager.load_config()
    print(f"설정 로드 완료: {len(config)} 섹션")
    
    # 설정 값 조회
    db_path = config_manager.get_config_value('system.database.path')
    print(f"데이터베이스 경로: {db_path}")
    
    language = config_manager.get_config_value('user.display.language')
    print(f"언어 설정: {language}")
    
    # 설정 값 변경
    config_manager.set_config_value('user.display.date_format', '%Y/%m/%d')
    print("날짜 형식 변경됨")
    
    # 변경된 설정 값 확인
    date_format = config_manager.get_config_value('user.display.date_format')
    print(f"변경된 날짜 형식: {date_format}")
    
    # 설정 저장
    config_manager.save_config()
    print("설정 저장 완료")

def profile_management_example():
    """
    프로파일 관리 예제
    """
    print("\n=== 프로파일 관리 예제 ===")
    
    # ConfigManager 초기화
    config_manager = ConfigManager()
    
    # 현재 프로파일 목록 조회
    profiles = config_manager.list_profiles()
    print(f"현재 프로파일 목록: {profiles}")
    
    # 새 프로파일 생성
    profile_name = f"example_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    config_manager.create_profile(profile_name)
    print(f"새 프로파일 생성됨: {profile_name}")
    
    # 설정 값 변경
    original_language = config_manager.get_config_value('user.display.language')
    config_manager.set_config_value('user.display.language', 'en')
    print(f"언어 설정 변경됨: {original_language} -> en")
    
    # 프로파일 로드
    config_manager.load_profile(profile_name)
    print(f"프로파일 로드됨: {profile_name}")
    
    # 설정 값 확인
    current_language = config_manager.get_config_value('user.display.language')
    print(f"현재 언어 설정: {current_language}")
    
    # 프로파일 삭제
    config_manager.delete_profile(profile_name)
    print(f"프로파일 삭제됨: {profile_name}")
    
    # 설정 초기화
    config_manager.set_config_value('user.display.language', original_language)
    print(f"언어 설정 복원됨: {original_language}")

def backup_restore_example():
    """
    백업 및 복원 예제
    """
    print("\n=== 백업 및 복원 예제 ===")
    
    # ConfigManager 초기화
    config_manager = ConfigManager()
    
    # 현재 백업 목록 조회
    backups = config_manager.list_backups()
    print(f"현재 백업 목록: {len(backups)}개")
    
    # 설정 값 변경
    original_value = config_manager.get_config_value('user.analysis.default_period_days')
    config_manager.set_config_value('user.analysis.default_period_days', 60)
    print(f"기본 분석 기간 변경됨: {original_value} -> 60")
    
    # 백업 생성
    backup_file = config_manager.backup_config()
    print(f"백업 생성됨: {backup_file}")
    
    # 설정 값 다시 변경
    config_manager.set_config_value('user.analysis.default_period_days', 90)
    print(f"기본 분석 기간 다시 변경됨: 60 -> 90")
    
    # 백업에서 복원
    config_manager.restore_config(backup_file)
    print(f"백업에서 복원됨: {backup_file}")
    
    # 설정 값 확인
    current_value = config_manager.get_config_value('user.analysis.default_period_days')
    print(f"현재 기본 분석 기간: {current_value}")
    
    # 설정 초기화
    config_manager.set_config_value('user.analysis.default_period_days', original_value)
    print(f"기본 분석 기간 복원됨: {original_value}")

def export_import_example():
    """
    내보내기 및 가져오기 예제
    """
    print("\n=== 내보내기 및 가져오기 예제 ===")
    
    # ConfigManager 초기화
    config_manager = ConfigManager()
    
    # 임시 디렉토리 생성
    import tempfile
    temp_dir = tempfile.mkdtemp()
    print(f"임시 디렉토리 생성됨: {temp_dir}")
    
    # YAML 형식으로 내보내기
    yaml_file = os.path.join(temp_dir, 'config_export.yaml')
    config_manager.export_config(yaml_file, 'yaml')
    print(f"YAML 형식으로 내보내기 완료: {yaml_file}")
    
    # JSON 형식으로 내보내기
    json_file = os.path.join(temp_dir, 'config_export.json')
    config_manager.export_config(json_file, 'json')
    print(f"JSON 형식으로 내보내기 완료: {json_file}")
    
    # 설정 값 변경
    original_value = config_manager.get_config_value('user.display.currency_format')
    config_manager.set_config_value('user.display.currency_format', '${:,.2f}')
    print(f"통화 형식 변경됨: {original_value} -> ${{:,.2f}}")
    
    # YAML 파일에서 가져오기
    config_manager.import_config(yaml_file)
    print(f"YAML 파일에서 가져오기 완료: {yaml_file}")
    
    # 설정 값 확인
    current_value = config_manager.get_config_value('user.display.currency_format')
    print(f"현재 통화 형식: {current_value}")
    
    # 임시 디렉토리 정리
    import shutil
    shutil.rmtree(temp_dir)
    print(f"임시 디렉토리 삭제됨: {temp_dir}")

def main():
    """
    메인 함수
    """
    # 로깅 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 예제 실행
    basic_usage_example()
    profile_management_example()
    backup_restore_example()
    export_import_example()
    
    print("\n모든 예제가 완료되었습니다.")

if __name__ == '__main__':
    main()