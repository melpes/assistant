# -*- coding: utf-8 -*-
"""
ConfigManager 테스트

설정 관리 시스템의 기능을 테스트합니다.
"""

import os
import sys
import unittest
import tempfile
import shutil
import yaml
import json
from datetime import datetime
from pathlib import Path

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    """
    ConfigManager 테스트 클래스
    """
    
    def setUp(self):
        """
        테스트 설정
        """
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, 'config')
        self.backup_dir = os.path.join(self.temp_dir, 'backups')
        
        # ConfigManager 초기화 (데이터베이스 사용 안 함)
        self.config_manager = ConfigManager(config_dir=self.config_dir, use_db=False)
        self.config_manager.backup_dir = self.backup_dir
    
    def tearDown(self):
        """
        테스트 정리
        """
        # 임시 디렉토리 삭제
        shutil.rmtree(self.temp_dir)
    
    def test_load_save_config(self):
        """
        설정 로드 및 저장 테스트
        """
        # 기본 설정 로드
        config = self.config_manager.load_config()
        self.assertIsNotNone(config)
        self.assertIn('system', config)
        self.assertIn('user', config)
        self.assertIn('rules', config)
        
        # 설정 저장
        result = self.config_manager.save_config()
        self.assertTrue(result)
        
        # 설정 파일 확인
        config_file = os.path.join(self.config_dir, self.config_manager.DEFAULT_CONFIG_FILE)
        self.assertTrue(os.path.exists(config_file))
        
        # 사용자 설정 파일 확인
        user_config_file = os.path.join(self.config_dir, self.config_manager.DEFAULT_USER_CONFIG_FILE)
        self.assertTrue(os.path.exists(user_config_file))
        
        # 시스템 설정 파일 확인
        system_config_file = os.path.join(self.config_dir, self.config_manager.DEFAULT_SYSTEM_CONFIG_FILE)
        self.assertTrue(os.path.exists(system_config_file))
        
        # 규칙 파일 확인
        rules_file = os.path.join(self.config_dir, self.config_manager.DEFAULT_RULES_FILE)
        self.assertTrue(os.path.exists(rules_file))
    
    def test_get_set_config_value(self):
        """
        설정 값 조회 및 설정 테스트
        """
        # 설정 값 조회
        db_path = self.config_manager.get_config_value('system.database.path')
        self.assertIsNotNone(db_path)
        
        # 설정 값 설정
        new_path = os.path.join(self.temp_dir, 'test.db')
        result = self.config_manager.set_config_value('system.database.path', new_path)
        self.assertTrue(result)
        
        # 설정 값 확인
        updated_path = self.config_manager.get_config_value('system.database.path')
        self.assertEqual(updated_path, new_path)
        
        # 존재하지 않는 키에 대한 기본값 테스트
        default_value = 'default'
        value = self.config_manager.get_config_value('non.existent.key', default_value)
        self.assertEqual(value, default_value)
        
        # 중첩 키 생성 테스트
        result = self.config_manager.set_config_value('new.nested.key', 'test_value')
        self.assertTrue(result)
        
        # 중첩 키 확인
        value = self.config_manager.get_config_value('new.nested.key')
        self.assertEqual(value, 'test_value')
    
    def test_profile_management(self):
        """
        프로파일 관리 테스트
        """
        # 프로파일 생성
        profile_name = 'test_profile'
        result = self.config_manager.create_profile(profile_name)
        self.assertTrue(result)
        
        # 프로파일 목록 확인
        profiles = self.config_manager.list_profiles()
        self.assertIn(profile_name, profiles)
        
        # 설정 값 변경
        self.config_manager.set_config_value('user.display.language', 'en')
        
        # 프로파일 로드
        result = self.config_manager.load_profile(profile_name)
        self.assertTrue(result)
        
        # 설정 값 확인 (프로파일 로드 전 값으로 복원되어야 함)
        language = self.config_manager.get_config_value('user.display.language')
        self.assertEqual(language, 'ko')  # 기본값
        
        # 프로파일 삭제
        result = self.config_manager.delete_profile(profile_name)
        self.assertTrue(result)
        
        # 프로파일 목록 확인
        profiles = self.config_manager.list_profiles()
        self.assertNotIn(profile_name, profiles)
    
    def test_backup_restore(self):
        """
        백업 및 복원 테스트
        """
        # 설정 값 변경
        test_value = 'test_backup_value'
        self.config_manager.set_config_value('system.test_key', test_value)
        
        # 백업 생성
        backup_file = self.config_manager.backup_config()
        self.assertTrue(os.path.exists(backup_file))
        
        # 설정 값 변경
        new_value = 'new_value'
        self.config_manager.set_config_value('system.test_key', new_value)
        
        # 백업에서 복원
        result = self.config_manager.restore_config(backup_file)
        self.assertTrue(result)
        
        # 설정 값 확인
        restored_value = self.config_manager.get_config_value('system.test_key')
        self.assertEqual(restored_value, test_value)
        
        # 백업 목록 확인
        backups = self.config_manager.list_backups()
        self.assertGreaterEqual(len(backups), 1)
    
    def test_reset_to_defaults(self):
        """
        기본값 초기화 테스트
        """
        # 설정 값 변경
        self.config_manager.set_config_value('system.test_key', 'test_value')
        self.config_manager.set_config_value('user.test_key', 'test_value')
        
        # 시스템 섹션만 초기화
        result = self.config_manager.reset_to_defaults('system')
        self.assertTrue(result)
        
        # 시스템 설정 확인
        system_test_key = self.config_manager.get_config_value('system.test_key', None)
        self.assertIsNone(system_test_key)
        
        # 사용자 설정 확인 (변경되지 않아야 함)
        user_test_key = self.config_manager.get_config_value('user.test_key')
        self.assertEqual(user_test_key, 'test_value')
        
        # 전체 초기화
        result = self.config_manager.reset_to_defaults()
        self.assertTrue(result)
        
        # 사용자 설정 확인 (초기화되어야 함)
        user_test_key = self.config_manager.get_config_value('user.test_key', None)
        self.assertIsNone(user_test_key)
    
    def test_export_import(self):
        """
        내보내기 및 가져오기 테스트
        """
        # 설정 값 변경
        test_value = 'test_export_value'
        self.config_manager.set_config_value('system.export_test', test_value)
        
        # YAML 형식으로 내보내기
        yaml_file = os.path.join(self.temp_dir, 'export_test.yaml')
        result = self.config_manager.export_config(yaml_file, 'yaml')
        self.assertTrue(result)
        self.assertTrue(os.path.exists(yaml_file))
        
        # JSON 형식으로 내보내기
        json_file = os.path.join(self.temp_dir, 'export_test.json')
        result = self.config_manager.export_config(json_file, 'json')
        self.assertTrue(result)
        self.assertTrue(os.path.exists(json_file))
        
        # 설정 값 변경
        self.config_manager.set_config_value('system.export_test', 'changed_value')
        
        # YAML 파일에서 가져오기
        result = self.config_manager.import_config(yaml_file)
        self.assertTrue(result)
        
        # 설정 값 확인
        imported_value = self.config_manager.get_config_value('system.export_test')
        self.assertEqual(imported_value, test_value)
        
        # 설정 값 변경
        self.config_manager.set_config_value('system.export_test', 'changed_again')
        
        # JSON 파일에서 가져오기
        result = self.config_manager.import_config(json_file)
        self.assertTrue(result)
        
        # 설정 값 확인
        imported_value = self.config_manager.get_config_value('system.export_test')
        self.assertEqual(imported_value, test_value)

if __name__ == '__main__':
    unittest.main()