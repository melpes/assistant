# -*- coding: utf-8 -*-
"""
설정 관리 시스템

사용자 설정, 시스템 설정, 분류 규칙 등의 설정을 관리하는 시스템입니다.
설정 파일 관리, 사용자별 프로파일, 런타임 설정 변경, 백업 및 복원 기능을 제공합니다.
"""

import os
import sys
import json
import yaml
import logging
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import copy

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.repositories.config_repository import ConfigRepository

class ConfigManager:
    """
    설정 관리자 클래스
    
    사용자 설정, 시스템 설정, 분류 규칙 등의 설정을 관리합니다.
    설정 파일 관리, 사용자별 프로파일, 런타임 설정 변경, 백업 및 복원 기능을 제공합니다.
    """
    
    # 기본 설정 디렉토리
    DEFAULT_CONFIG_DIR = os.path.join(parent_dir, 'config')
    
    # 기본 백업 디렉토리
    DEFAULT_BACKUP_DIR = os.path.join(parent_dir, 'backups', 'config')
    
    # 기본 설정 파일명
    DEFAULT_CONFIG_FILE = 'config.yaml'
    
    # 기본 사용자 설정 파일명
    DEFAULT_USER_CONFIG_FILE = 'user_config.yaml'
    
    # 기본 시스템 설정 파일명
    DEFAULT_SYSTEM_CONFIG_FILE = 'system_config.yaml'
    
    # 기본 분류 규칙 파일명
    DEFAULT_RULES_FILE = 'classification_rules.yaml'
    
    # 기본 설정 값
    DEFAULT_CONFIG = {
        'system': {
            'database': {
                'path': os.path.join(parent_dir, 'personal_data.db'),
                'backup_enabled': True,
                'backup_interval_days': 7,
                'max_backups': 5
            },
            'logging': {
                'level': 'INFO',
                'file_path': os.path.join(parent_dir, 'logs', 'financial_system.log'),
                'max_size_mb': 10,
                'backup_count': 3
            },
            'data_sources': {
                'toss_bank_card': {
                    'enabled': True,
                    'file_pattern': '*.xlsx'
                },
                'toss_bank_account': {
                    'enabled': True,
                    'file_pattern': '*.csv'
                },
                'manual_entry': {
                    'enabled': True
                }
            }
        },
        'user': {
            'display': {
                'language': 'ko',
                'date_format': '%Y-%m-%d',
                'currency_format': '{:,}원'
            },
            'analysis': {
                'default_period_days': 30,
                'exclude_transfers': True,
                'default_view': 'category'
            },
            'categories': {
                'expense': [
                    '식비', '교통비', '생활용품/식료품', '카페/음료', 
                    '의료비', '통신비', '공과금', '문화/오락', 
                    '의류/패션', '온라인쇼핑', '현금인출', '해외결제',
                    '간편결제', '기타'
                ],
                'income': [
                    '급여', '용돈', '이자', '환급', '부수입', '임대수입', 
                    '판매수입', '기타수입'
                ]
            },
            'payment_methods': {
                'expense': [
                    '현금', '체크카드결제', '계좌이체', '토스페이', '기타카드', '기타'
                ],
                'income': [
                    '계좌입금', '현금', '급여이체', '이자입금', '기타입금'
                ]
            },
            'templates': {
                'enabled': True,
                'path': os.path.join(parent_dir, 'data', 'templates')
            }
        },
        'rules': {
            'auto_categorization': {
                'enabled': True,
                'min_confidence': 0.7
            },
            'learning': {
                'enabled': True,
                'min_samples': 3
            },
            'exclusions': {
                'enabled': True,
                'patterns': [
                    {'field': 'description', 'pattern': '계좌이체', 'transaction_type': 'expense'},
                    {'field': 'description', 'pattern': '자동이체', 'transaction_type': 'expense'}
                ]
            }
        }
    }
    
    def __init__(self, config_dir: str = None, use_db: bool = True):
        """
        설정 관리자 초기화
        
        Args:
            config_dir: 설정 디렉토리 경로 (기본값: DEFAULT_CONFIG_DIR)
            use_db: 데이터베이스 사용 여부 (기본값: True)
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.backup_dir = self.DEFAULT_BACKUP_DIR
        self.use_db = use_db
        
        # 설정 디렉토리 생성
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 설정 파일 경로
        self.config_file = os.path.join(self.config_dir, self.DEFAULT_CONFIG_FILE)
        self.user_config_file = os.path.join(self.config_dir, self.DEFAULT_USER_CONFIG_FILE)
        self.system_config_file = os.path.join(self.config_dir, self.DEFAULT_SYSTEM_CONFIG_FILE)
        self.rules_file = os.path.join(self.config_dir, self.DEFAULT_RULES_FILE)
        
        # 설정 데이터
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        
        # 데이터베이스 저장소
        self.repository = ConfigRepository() if use_db else None
        
        # 설정 로드
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        설정 파일을 로드합니다.
        
        Returns:
            Dict[str, Any]: 로드된 설정 데이터
        """
        try:
            # 통합 설정 파일 로드
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        self._deep_update(self.config, loaded_config)
                logger.info(f"설정 파일 로드 완료: {self.config_file}")
            
            # 사용자 설정 파일 로드
            if os.path.exists(self.user_config_file):
                with open(self.user_config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    if user_config and 'user' in user_config:
                        self._deep_update(self.config['user'], user_config['user'])
                logger.info(f"사용자 설정 파일 로드 완료: {self.user_config_file}")
            
            # 시스템 설정 파일 로드
            if os.path.exists(self.system_config_file):
                with open(self.system_config_file, 'r', encoding='utf-8') as f:
                    system_config = yaml.safe_load(f)
                    if system_config and 'system' in system_config:
                        self._deep_update(self.config['system'], system_config['system'])
                logger.info(f"시스템 설정 파일 로드 완료: {self.system_config_file}")
            
            # 분류 규칙 파일 로드
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    rules_config = yaml.safe_load(f)
                    if rules_config and 'rules' in rules_config:
                        self._deep_update(self.config['rules'], rules_config['rules'])
                logger.info(f"분류 규칙 파일 로드 완료: {self.rules_file}")
            
            # 데이터베이스에서 설정 로드
            if self.use_db and self.repository:
                db_config = self.repository.get_all_preferences()
                if db_config:
                    for key, value in db_config.items():
                        self.set_config_value(key, value)
                logger.info("데이터베이스에서 설정 로드 완료")
            
            # 기본 설정 파일 저장 (없는 경우)
            if not os.path.exists(self.config_file):
                self.save_config()
            
            return self.config
            
        except Exception as e:
            logger.error(f"설정 로드 중 오류 발생: {e}")
            logger.info("기본 설정을 사용합니다.")
            return self.config
    
    def save_config(self) -> bool:
        """
        설정을 파일에 저장합니다.
        
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 설정 디렉토리 생성
            os.makedirs(self.config_dir, exist_ok=True)
            
            # 통합 설정 파일 저장
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            
            # 사용자 설정 파일 저장
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                yaml.dump({'user': self.config['user']}, f, default_flow_style=False, allow_unicode=True)
            
            # 시스템 설정 파일 저장
            with open(self.system_config_file, 'w', encoding='utf-8') as f:
                yaml.dump({'system': self.config['system']}, f, default_flow_style=False, allow_unicode=True)
            
            # 분류 규칙 파일 저장
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                yaml.dump({'rules': self.config['rules']}, f, default_flow_style=False, allow_unicode=True)
            
            logger.info("설정 파일 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"설정 저장 중 오류 발생: {e}")
            return False
    
    def get_config(self, section: str = None) -> Dict[str, Any]:
        """
        전체 설정 또는 특정 섹션의 설정을 반환합니다.
        
        Args:
            section: 설정 섹션 (system, user, rules)
            
        Returns:
            Dict[str, Any]: 설정 데이터
        """
        if section:
            return self.config.get(section, {})
        return self.config
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        특정 설정 값을 반환합니다.
        
        Args:
            key_path: 설정 키 경로 (예: 'system.database.path')
            default: 기본값
            
        Returns:
            Any: 설정 값
        """
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                if key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"설정 값 조회 중 오류 발생: {e}")
            return default
    
    def set_config_value(self, key_path: str, value: Any) -> bool:
        """
        특정 설정 값을 설정합니다.
        
        Args:
            key_path: 설정 키 경로 (예: 'system.database.path')
            value: 설정 값
            
        Returns:
            bool: 설정 성공 여부
        """
        try:
            keys = key_path.split('.')
            target = self.config
            
            # 마지막 키를 제외한 모든 키에 대해 경로 탐색
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                target = target[key]
            
            # 마지막 키에 값 설정
            target[keys[-1]] = value
            
            # 데이터베이스에 설정 저장
            if self.use_db and self.repository:
                self.repository.set_preference(key_path, str(value))
            
            return True
            
        except Exception as e:
            logger.error(f"설정 값 설정 중 오류 발생: {e}")
            return False
    
    def create_profile(self, profile_name: str) -> bool:
        """
        새 설정 프로파일을 생성합니다.
        
        Args:
            profile_name: 프로파일 이름
            
        Returns:
            bool: 생성 성공 여부
        """
        try:
            profile_dir = os.path.join(self.config_dir, 'profiles', profile_name)
            os.makedirs(profile_dir, exist_ok=True)
            
            # 현재 사용자 설정을 프로파일로 저장
            profile_config_file = os.path.join(profile_dir, self.DEFAULT_USER_CONFIG_FILE)
            with open(profile_config_file, 'w', encoding='utf-8') as f:
                yaml.dump({'user': self.config['user']}, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"설정 프로파일 생성 완료: {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"설정 프로파일 생성 중 오류 발생: {e}")
            return False
    
    def load_profile(self, profile_name: str) -> bool:
        """
        설정 프로파일을 로드합니다.
        
        Args:
            profile_name: 프로파일 이름
            
        Returns:
            bool: 로드 성공 여부
        """
        try:
            profile_dir = os.path.join(self.config_dir, 'profiles', profile_name)
            profile_config_file = os.path.join(profile_dir, self.DEFAULT_USER_CONFIG_FILE)
            
            if not os.path.exists(profile_config_file):
                logger.error(f"프로파일을 찾을 수 없습니다: {profile_name}")
                return False
            
            # 프로파일 설정 로드
            with open(profile_config_file, 'r', encoding='utf-8') as f:
                profile_config = yaml.safe_load(f)
                if profile_config and 'user' in profile_config:
                    # 기존 사용자 설정을 프로파일 설정으로 대체
                    self.config['user'] = profile_config['user']
            
            # 변경된 설정 저장
            self.save_config()
            
            logger.info(f"설정 프로파일 로드 완료: {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"설정 프로파일 로드 중 오류 발생: {e}")
            return False
    
    def list_profiles(self) -> List[str]:
        """
        사용 가능한 설정 프로파일 목록을 반환합니다.
        
        Returns:
            List[str]: 프로파일 이름 목록
        """
        try:
            profiles_dir = os.path.join(self.config_dir, 'profiles')
            
            if not os.path.exists(profiles_dir):
                os.makedirs(profiles_dir, exist_ok=True)
                return []
            
            profiles = []
            for item in os.listdir(profiles_dir):
                profile_dir = os.path.join(profiles_dir, item)
                profile_config_file = os.path.join(profile_dir, self.DEFAULT_USER_CONFIG_FILE)
                
                if os.path.isdir(profile_dir) and os.path.exists(profile_config_file):
                    profiles.append(item)
            
            return profiles
            
        except Exception as e:
            logger.error(f"프로파일 목록 조회 중 오류 발생: {e}")
            return []
    
    def delete_profile(self, profile_name: str) -> bool:
        """
        설정 프로파일을 삭제합니다.
        
        Args:
            profile_name: 프로파일 이름
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            profile_dir = os.path.join(self.config_dir, 'profiles', profile_name)
            
            if not os.path.exists(profile_dir):
                logger.error(f"프로파일을 찾을 수 없습니다: {profile_name}")
                return False
            
            # 프로파일 디렉토리 삭제
            shutil.rmtree(profile_dir)
            
            logger.info(f"설정 프로파일 삭제 완료: {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"설정 프로파일 삭제 중 오류 발생: {e}")
            return False
    
    def backup_config(self) -> str:
        """
        현재 설정을 백업합니다.
        
        Returns:
            str: 백업 파일 경로
        """
        try:
            # 백업 디렉토리 생성
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # 백업 파일명 생성
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f'config_backup_{timestamp}.yaml')
            
            # 설정 백업
            with open(backup_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"설정 백업 완료: {backup_file}")
            
            # 오래된 백업 정리
            self._cleanup_old_backups()
            
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
            if not os.path.exists(backup_file):
                logger.error(f"백업 파일을 찾을 수 없습니다: {backup_file}")
                return False
            
            # 현재 설정 백업
            current_backup = self.backup_config()
            
            # 백업에서 설정 로드
            with open(backup_file, 'r', encoding='utf-8') as f:
                restored_config = yaml.safe_load(f)
                
                if not restored_config:
                    logger.error("백업 파일에서 설정을 로드할 수 없습니다.")
                    return False
                
                # 설정 복원
                self.config = restored_config
            
            # 복원된 설정 저장
            self.save_config()
            
            logger.info(f"설정 복원 완료: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"설정 복원 중 오류 발생: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        사용 가능한 설정 백업 목록을 반환합니다.
        
        Returns:
            List[Dict[str, Any]]: 백업 정보 목록
        """
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir, exist_ok=True)
                return []
            
            backups = []
            for item in os.listdir(self.backup_dir):
                if item.startswith('config_backup_') and item.endswith('.yaml'):
                    backup_file = os.path.join(self.backup_dir, item)
                    file_stat = os.stat(backup_file)
                    
                    # 타임스탬프 추출
                    timestamp_str = item[14:-5]  # 'config_backup_YYYYMMDD_HHMMSS.yaml'
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    except ValueError:
                        timestamp = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    backups.append({
                        'file': backup_file,
                        'filename': item,
                        'timestamp': timestamp,
                        'size': file_stat.st_size
                    })
            
            # 최신 순으로 정렬
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"백업 목록 조회 중 오류 발생: {e}")
            return []
    
    def reset_to_defaults(self, section: str = None) -> bool:
        """
        설정을 기본값으로 초기화합니다.
        
        Args:
            section: 초기화할 섹션 (system, user, rules)
            
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            if section:
                if section in self.DEFAULT_CONFIG:
                    self.config[section] = copy.deepcopy(self.DEFAULT_CONFIG[section])
                else:
                    logger.error(f"유효하지 않은 설정 섹션: {section}")
                    return False
            else:
                self.config = copy.deepcopy(self.DEFAULT_CONFIG)
            
            # 초기화된 설정 저장
            self.save_config()
            
            logger.info(f"설정 초기화 완료: {section if section else '전체'}")
            return True
            
        except Exception as e:
            logger.error(f"설정 초기화 중 오류 발생: {e}")
            return False
    
    def export_config(self, export_file: str, format: str = 'yaml') -> bool:
        """
        설정을 파일로 내보냅니다.
        
        Args:
            export_file: 내보낼 파일 경로
            format: 파일 형식 (yaml/json)
            
        Returns:
            bool: 내보내기 성공 여부
        """
        try:
            # 디렉토리 생성
            os.makedirs(os.path.dirname(os.path.abspath(export_file)), exist_ok=True)
            
            if format.lower() == 'json':
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
            else:
                with open(export_file, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"설정 내보내기 완료: {export_file}")
            return True
            
        except Exception as e:
            logger.error(f"설정 내보내기 중 오류 발생: {e}")
            return False
    
    def import_config(self, import_file: str) -> bool:
        """
        파일에서 설정을 가져옵니다.
        
        Args:
            import_file: 가져올 파일 경로
            
        Returns:
            bool: 가져오기 성공 여부
        """
        try:
            if not os.path.exists(import_file):
                logger.error(f"가져올 파일을 찾을 수 없습니다: {import_file}")
                return False
            
            # 현재 설정 백업
            current_backup = self.backup_config()
            
            # 파일 형식 확인
            if import_file.endswith('.json'):
                with open(import_file, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
            else:
                with open(import_file, 'r', encoding='utf-8') as f:
                    imported_config = yaml.safe_load(f)
            
            if not imported_config:
                logger.error("가져온 파일에서 설정을 로드할 수 없습니다.")
                return False
            
            # 설정 가져오기
            self.config = imported_config
            
            # 가져온 설정 저장
            self.save_config()
            
            logger.info(f"설정 가져오기 완료: {import_file}")
            return True
            
        except Exception as e:
            logger.error(f"설정 가져오기 중 오류 발생: {e}")
            return False
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        딕셔너리를 재귀적으로 업데이트합니다.
        
        Args:
            target: 대상 딕셔너리
            source: 소스 딕셔너리
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def _cleanup_old_backups(self) -> None:
        """
        오래된 백업 파일을 정리합니다.
        """
        try:
            max_backups = self.get_config_value('system.database.max_backups', 5)
            
            backups = self.list_backups()
            if len(backups) > max_backups:
                # 오래된 백업 삭제
                for backup in backups[max_backups:]:
                    try:
                        os.remove(backup['file'])
                        logger.debug(f"오래된 백업 삭제: {backup['filename']}")
                    except Exception as e:
                        logger.error(f"백업 삭제 중 오류 발생: {e}")
                
        except Exception as e:
            logger.error(f"백업 정리 중 오류 발생: {e}")

def main():
    """
    메인 함수
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='설정 관리 도구')
    
    parser.add_argument('--action', '-a', choices=[
        'get', 'set', 'list', 'backup', 'restore', 'reset',
        'create-profile', 'load-profile', 'list-profiles', 'delete-profile',
        'export', 'import'
    ], default='list', help='수행할 작업')
    
    parser.add_argument('--key', '-k', help='설정 키 (예: system.database.path)')
    parser.add_argument('--value', '-v', help='설정 값')
    parser.add_argument('--section', '-s', choices=['system', 'user', 'rules'], help='설정 섹션')
    parser.add_argument('--profile', '-p', help='프로파일 이름')
    parser.add_argument('--file', '-f', help='파일 경로')
    parser.add_argument('--format', choices=['yaml', 'json'], default='yaml', help='파일 형식')
    parser.add_argument('--verbose', action='store_true', help='상세 출력')
    
    args = parser.parse_args()
    
    # 로깅 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 설정 관리자 초기화
    config_manager = ConfigManager()
    
    # 작업 수행
    if args.action == 'get':
        if args.key:
            value = config_manager.get_config_value(args.key)
            print(f"{args.key}: {value}")
        elif args.section:
            section_config = config_manager.get_config(args.section)
            print(f"{args.section} 설정:")
            print(yaml.dump(section_config, default_flow_style=False, allow_unicode=True))
        else:
            all_config = config_manager.get_config()
            print("전체 설정:")
            print(yaml.dump(all_config, default_flow_style=False, allow_unicode=True))
    
    elif args.action == 'set':
        if not args.key or args.value is None:
            print("설정 키와 값을 모두 지정해야 합니다.")
            return
        
        if config_manager.set_config_value(args.key, args.value):
            print(f"설정 값이 업데이트되었습니다: {args.key} = {args.value}")
            config_manager.save_config()
        else:
            print("설정 값 업데이트에 실패했습니다.")
    
    elif args.action == 'list':
        all_config = config_manager.get_config()
        print("현재 설정:")
        print(yaml.dump(all_config, default_flow_style=False, allow_unicode=True))
    
    elif args.action == 'backup':
        backup_file = config_manager.backup_config()
        if backup_file:
            print(f"설정이 백업되었습니다: {backup_file}")
        else:
            print("설정 백업에 실패했습니다.")
    
    elif args.action == 'restore':
        if not args.file:
            backups = config_manager.list_backups()
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
        
        if config_manager.restore_config(backup_file):
            print(f"설정이 복원되었습니다: {backup_file}")
        else:
            print("설정 복원에 실패했습니다.")
    
    elif args.action == 'reset':
        if config_manager.reset_to_defaults(args.section):
            print(f"설정이 초기화되었습니다: {args.section if args.section else '전체'}")
        else:
            print("설정 초기화에 실패했습니다.")
    
    elif args.action == 'create-profile':
        if not args.profile:
            print("프로파일 이름을 지정해야 합니다.")
            return
        
        if config_manager.create_profile(args.profile):
            print(f"프로파일이 생성되었습니다: {args.profile}")
        else:
            print("프로파일 생성에 실패했습니다.")
    
    elif args.action == 'load-profile':
        if not args.profile:
            profiles = config_manager.list_profiles()
            if not profiles:
                print("사용 가능한 프로파일이 없습니다.")
                return
            
            print("사용 가능한 프로파일:")
            for i, profile in enumerate(profiles, 1):
                print(f"{i}. {profile}")
            
            choice = input("로드할 프로파일 번호를 선택하세요: ")
            try:
                index = int(choice) - 1
                if 0 <= index < len(profiles):
                    profile_name = profiles[index]
                else:
                    print("올바른 프로파일 번호를 선택해주세요.")
                    return
            except ValueError:
                print("숫자를 입력해주세요.")
                return
        else:
            profile_name = args.profile
        
        if config_manager.load_profile(profile_name):
            print(f"프로파일이 로드되었습니다: {profile_name}")
        else:
            print("프로파일 로드에 실패했습니다.")
    
    elif args.action == 'list-profiles':
        profiles = config_manager.list_profiles()
        if profiles:
            print("사용 가능한 프로파일:")
            for profile in profiles:
                print(f"- {profile}")
        else:
            print("사용 가능한 프로파일이 없습니다.")
    
    elif args.action == 'delete-profile':
        if not args.profile:
            profiles = config_manager.list_profiles()
            if not profiles:
                print("사용 가능한 프로파일이 없습니다.")
                return
            
            print("사용 가능한 프로파일:")
            for i, profile in enumerate(profiles, 1):
                print(f"{i}. {profile}")
            
            choice = input("삭제할 프로파일 번호를 선택하세요: ")
            try:
                index = int(choice) - 1
                if 0 <= index < len(profiles):
                    profile_name = profiles[index]
                else:
                    print("올바른 프로파일 번호를 선택해주세요.")
                    return
            except ValueError:
                print("숫자를 입력해주세요.")
                return
        else:
            profile_name = args.profile
        
        confirm = input(f"프로파일 '{profile_name}'을(를) 삭제하시겠습니까? (y/n): ")
        if confirm.lower() != 'y':
            print("프로파일 삭제가 취소되었습니다.")
            return
        
        if config_manager.delete_profile(profile_name):
            print(f"프로파일이 삭제되었습니다: {profile_name}")
        else:
            print("프로파일 삭제에 실패했습니다.")
    
    elif args.action == 'export':
        if not args.file:
            print("내보낼 파일 경로를 지정해야 합니다.")
            return
        
        if config_manager.export_config(args.file, args.format):
            print(f"설정이 내보내졌습니다: {args.file}")
        else:
            print("설정 내보내기에 실패했습니다.")
    
    elif args.action == 'import':
        if not args.file:
            print("가져올 파일 경로를 지정해야 합니다.")
            return
        
        if config_manager.import_config(args.file):
            print(f"설정이 가져와졌습니다: {args.file}")
        else:
            print("설정 가져오기에 실패했습니다.")

if __name__ == '__main__':
    main()