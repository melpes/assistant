# -*- coding: utf-8 -*-
"""
데이터 관리 도구 테스트

management_tools 모듈의 함수들을 테스트합니다.
"""

import os
import unittest
import sys
from unittest.mock import patch, MagicMock
from datetime import datetime

# 외부 모듈 모킹
sys.modules['schedule'] = MagicMock()
sys.modules['yaml'] = MagicMock()

# 내부 모듈 모킹
class MockConfigRepository:
    def get_all_preferences(self):
        return {}
    
    def set_preference(self, key, value):
        return True

sys.modules['src.repositories.config_repository'] = MagicMock()
sys.modules['src.repositories.config_repository'].ConfigRepository = MockConfigRepository

from src.financial_tools.management_tools import (
    add_classification_rule,
    update_classification_rule,
    delete_classification_rule,
    get_classification_rules,
    get_rule_stats,
    backup_data,
    restore_data,
    list_backups,
    export_data,
    get_system_status,
    update_settings,
    get_settings
)
from src.models import ClassificationRule

class TestManagementTools(unittest.TestCase):
    """데이터 관리 도구 테스트 클래스"""
    
    @patch('src.financial_tools.management_tools._get_rule_engine')
    def test_add_classification_rule(self, mock_get_rule_engine):
        """add_classification_rule 함수 테스트"""
        # 모의 객체 설정
        mock_rule_engine = MagicMock()
        mock_get_rule_engine.return_value = mock_rule_engine
        
        # 모의 규칙 객체 생성
        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "테스트 규칙"
        mock_rule.rule_type = "category"
        mock_rule.condition_type = "contains"
        mock_rule.condition_value = "마트"
        mock_rule.target_value = "생활용품/식료품"
        mock_rule.priority = 0
        mock_rule.is_active = True
        mock_rule.created_at = datetime.now()
        mock_rule.created_by = "financial_agent"
        
        # 모의 add_rule 메서드 설정
        mock_rule_engine.add_rule.return_value = mock_rule
        
        # 함수 호출
        result = add_classification_rule(
            rule_name="테스트 규칙",
            rule_type="category",
            condition_type="contains",
            condition_value="마트",
            target_value="생활용품/식료품"
        )
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['rule']['id'], 1)
        self.assertEqual(result['rule']['rule_name'], "테스트 규칙")
        self.assertEqual(result['rule']['rule_type'], "category")
        self.assertEqual(result['rule']['condition_type'], "contains")
        self.assertEqual(result['rule']['condition_value'], "마트")
        self.assertEqual(result['rule']['target_value'], "생활용품/식료품")
        
        # 잘못된 규칙 유형 테스트
        result = add_classification_rule(
            rule_name="테스트 규칙",
            rule_type="invalid_type",
            condition_type="contains",
            condition_value="마트",
            target_value="생활용품/식료품"
        )
        
        self.assertFalse(result['success'])
        self.assertIn("유효하지 않은 규칙 유형", result['error'])
    
    @patch('src.financial_tools.management_tools._get_rule_repository')
    @patch('src.financial_tools.management_tools._get_rule_engine')
    def test_update_classification_rule(self, mock_get_rule_engine, mock_get_rule_repository):
        """update_classification_rule 함수 테스트"""
        # 모의 객체 설정
        mock_rule_engine = MagicMock()
        mock_rule_repository = MagicMock()
        mock_get_rule_engine.return_value = mock_rule_engine
        mock_get_rule_repository.return_value = mock_rule_repository
        
        # 모의 규칙 객체 생성
        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "테스트 규칙"
        mock_rule.rule_type = "category"
        mock_rule.condition_type = "contains"
        mock_rule.condition_value = "마트"
        mock_rule.target_value = "생활용품/식료품"
        mock_rule.priority = 0
        mock_rule.is_active = True
        mock_rule.created_at = datetime.now()
        mock_rule.created_by = "financial_agent"
        
        # 업데이트된 규칙 객체
        updated_mock_rule = MagicMock()
        updated_mock_rule.id = 1
        updated_mock_rule.rule_name = "업데이트된 규칙"
        updated_mock_rule.rule_type = "category"
        updated_mock_rule.condition_type = "contains"
        updated_mock_rule.condition_value = "마트"
        updated_mock_rule.target_value = "식비"
        updated_mock_rule.priority = 0
        updated_mock_rule.is_active = True
        updated_mock_rule.created_at = datetime.now()
        updated_mock_rule.created_by = "financial_agent"
        
        # 모의 메서드 설정
        mock_rule_repository.read.return_value = mock_rule
        mock_rule_engine.update_rule.return_value = updated_mock_rule
        
        # 함수 호출
        result = update_classification_rule(
            rule_id=1,
            rule_name="업데이트된 규칙",
            target_value="식비"
        )
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['rule']['id'], 1)
        self.assertEqual(result['rule']['rule_name'], "업데이트된 규칙")  # 업데이트된 규칙 이름
        self.assertEqual(result['rule']['target_value'], "식비")  # 업데이트된 타겟 값
        
        # 존재하지 않는 규칙 테스트
        mock_rule_repository.read.return_value = None
        
        result = update_classification_rule(
            rule_id=999,
            rule_name="업데이트된 규칙"
        )
        
        self.assertFalse(result['success'])
        self.assertIn("규칙을 찾을 수 없습니다", result['error'])
    
    @patch('src.financial_tools.management_tools._get_rule_engine')
    def test_delete_classification_rule(self, mock_get_rule_engine):
        """delete_classification_rule 함수 테스트"""
        # 모의 객체 설정
        mock_rule_engine = MagicMock()
        mock_get_rule_engine.return_value = mock_rule_engine
        
        # 모의 메서드 설정
        mock_rule_engine.delete_rule.return_value = True
        
        # 함수 호출
        result = delete_classification_rule(rule_id=1)
        
        # 검증
        self.assertTrue(result['success'])
        self.assertIn("규칙이 삭제되었습니다", result['message'])
        
        # 삭제 실패 테스트
        mock_rule_engine.delete_rule.return_value = False
        
        result = delete_classification_rule(rule_id=999)
        
        self.assertFalse(result['success'])
        self.assertIn("규칙 삭제 실패", result['error'])
    
    @patch('src.financial_tools.management_tools._get_rule_repository')
    def test_get_classification_rules(self, mock_get_rule_repository):
        """get_classification_rules 함수 테스트"""
        # 모의 객체 설정
        mock_rule_repository = MagicMock()
        mock_get_rule_repository.return_value = mock_rule_repository
        
        # 모의 규칙 객체 생성
        mock_rule1 = MagicMock()
        mock_rule1.id = 1
        mock_rule1.rule_name = "규칙 1"
        mock_rule1.rule_type = "category"
        mock_rule1.condition_type = "contains"
        mock_rule1.condition_value = "마트"
        mock_rule1.target_value = "생활용품/식료품"
        mock_rule1.priority = 0
        mock_rule1.is_active = True
        mock_rule1.created_at = datetime.now()
        mock_rule1.created_by = "financial_agent"
        
        mock_rule2 = MagicMock()
        mock_rule2.id = 2
        mock_rule2.rule_name = "규칙 2"
        mock_rule2.rule_type = "payment_method"
        mock_rule2.condition_type = "contains"
        mock_rule2.condition_value = "카드"
        mock_rule2.target_value = "체크카드결제"
        mock_rule2.priority = 0
        mock_rule2.is_active = True
        mock_rule2.created_at = datetime.now()
        mock_rule2.created_by = "financial_agent"
        
        # 모의 메서드 설정
        mock_rule_repository.get_active_rules_by_type.return_value = [mock_rule1]
        mock_rule_repository.get_all_rules.return_value = [mock_rule1, mock_rule2]
        
        # 특정 유형 조회 테스트
        result = get_classification_rules(rule_type="category")
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(len(result['rules']), 1)
        self.assertEqual(result['rules'][0]['id'], 1)
        self.assertEqual(result['rules'][0]['rule_type'], "category")
        
        # 전체 조회 테스트
        result = get_classification_rules()
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(len(result['rules']), 2)
        self.assertEqual(result['count'], 2)
    
    @patch('src.financial_tools.management_tools._get_rule_engine')
    def test_get_rule_stats(self, mock_get_rule_engine):
        """get_rule_stats 함수 테스트"""
        # 모의 객체 설정
        mock_rule_engine = MagicMock()
        mock_get_rule_engine.return_value = mock_rule_engine
        
        # 모의 통계 데이터
        mock_stats = {
            'total_rules': 5,
            'condition_counts': {'contains': 3, 'equals': 2},
            'creator_counts': {'financial_agent': 5},
            'priority_range': (0, 10),
            'target_counts': {'생활용품/식료품': 2, '식비': 3}
        }
        
        # 모의 메서드 설정
        mock_rule_engine.get_rule_stats.return_value = mock_stats
        
        # 특정 유형 통계 조회 테스트
        result = get_rule_stats(rule_type="category")
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['stats'], mock_stats)
        self.assertEqual(result['rule_type'], "category")
        
        # 전체 통계 조회 테스트
        result = get_rule_stats()
        
        # 검증
        self.assertTrue(result['success'])
        self.assertIn('category', result['stats'])
        self.assertIn('payment_method', result['stats'])
        self.assertIn('filter', result['stats'])
    
    @patch('src.financial_tools.management_tools._get_backup_manager')
    def test_backup_data(self, mock_get_backup_manager):
        """backup_data 함수 테스트"""
        # 모의 객체 설정
        mock_backup_manager = MagicMock()
        mock_get_backup_manager.return_value = mock_backup_manager
        
        # 모의 메서드 설정
        mock_backup_manager.backup_database.return_value = "/path/to/db_backup.zip"
        mock_backup_manager.backup_config.return_value = "/path/to/config_backup.yaml"
        
        # 데이터베이스만 백업 테스트
        result = backup_data(include_settings=False)
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['database_backup'], "/path/to/db_backup.zip")
        self.assertIsNone(result['settings_backup'])
        
        # 데이터베이스 및 설정 백업 테스트
        result = backup_data(include_settings=True)
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['database_backup'], "/path/to/db_backup.zip")
        self.assertEqual(result['settings_backup'], "/path/to/config_backup.yaml")
        
        # 백업 실패 테스트
        mock_backup_manager.backup_database.return_value = ""
        
        result = backup_data()
        
        # 검증
        self.assertFalse(result['success'])
        self.assertIn("데이터베이스 백업 실패", result['error'])
    
    @patch('os.path.exists')
    @patch('src.financial_tools.management_tools._get_backup_manager')
    def test_restore_data(self, mock_get_backup_manager, mock_exists):
        """restore_data 함수 테스트"""
        # 모의 객체 설정
        mock_backup_manager = MagicMock()
        mock_get_backup_manager.return_value = mock_backup_manager
        mock_exists.return_value = True
        
        # 모의 메서드 설정
        mock_backup_manager.restore_database.return_value = True
        mock_backup_manager.restore_config.return_value = True
        
        # 데이터베이스 복원 테스트
        result = restore_data(backup_path="/path/to/db_backup.zip")
        
        # 검증
        self.assertTrue(result['success'])
        self.assertIn("데이터베이스 복원 완료", result['message'])
        
        # 설정 복원 테스트
        result = restore_data(backup_path="/path/to/config_backup.yaml")
        
        # 검증
        self.assertTrue(result['success'])
        self.assertIn("설정 복원 완료", result['message'])
        
        # 파일이 존재하지 않는 경우 테스트
        mock_exists.return_value = False
        
        result = restore_data(backup_path="/path/to/nonexistent_backup.zip")
        
        # 검증
        self.assertFalse(result['success'])
        self.assertIn("백업 파일을 찾을 수 없습니다", result['error'])
    
    @patch('src.financial_tools.management_tools._get_backup_manager')
    def test_list_backups(self, mock_get_backup_manager):
        """list_backups 함수 테스트"""
        # 모의 객체 설정
        mock_backup_manager = MagicMock()
        mock_get_backup_manager.return_value = mock_backup_manager
        
        # 모의 백업 목록
        mock_db_backups = [
            {
                'file': "/path/to/db_backup1.zip",
                'filename': "db_backup1.zip",
                'timestamp': datetime.now(),
                'size': 1024,
                'type': "full"
            },
            {
                'file': "/path/to/db_backup2.zip",
                'filename': "db_backup2.zip",
                'timestamp': datetime.now(),
                'size': 2048,
                'type': "incremental"
            }
        ]
        
        mock_config_backups = [
            {
                'file': "/path/to/config_backup.yaml",
                'filename': "config_backup.yaml",
                'timestamp': datetime.now(),
                'size': 512
            }
        ]
        
        # 모의 메서드 설정
        mock_backup_manager.list_backups.side_effect = lambda backup_type: mock_db_backups if backup_type == 'database' else mock_config_backups
        
        # 데이터베이스 백업 목록 조회 테스트
        result = list_backups(backup_type="database")
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(len(result['backups']), 2)
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['backup_type'], "database")
        
        # 설정 백업 목록 조회 테스트
        result = list_backups(backup_type="config")
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(len(result['backups']), 1)
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['backup_type'], "config")
    
    @patch('src.financial_tools.management_tools._get_backup_manager')
    def test_export_data(self, mock_get_backup_manager):
        """export_data 함수 테스트"""
        # 모의 객체 설정
        mock_backup_manager = MagicMock()
        mock_get_backup_manager.return_value = mock_backup_manager
        
        # 모의 내보내기 결과
        mock_export_files = {
            'zip': "/path/to/export.zip"
        }
        
        # 모의 메서드 설정
        mock_backup_manager.export_data.return_value = mock_export_files
        
        # CSV 형식 내보내기 테스트
        result = export_data(format="csv")
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['files'], mock_export_files)
        self.assertEqual(result['format'], "csv")
        
        # JSON 형식 내보내기 테스트
        result = export_data(format="json", tables=["expenses", "income"])
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['files'], mock_export_files)
        self.assertEqual(result['format'], "json")
        
        # 내보내기 실패 테스트
        mock_backup_manager.export_data.return_value = {}
        
        result = export_data()
        
        # 검증
        self.assertFalse(result['success'])
        self.assertIn("데이터 내보내기 실패", result['error'])
    
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('src.financial_tools.management_tools._get_config_manager')
    @patch('src.financial_tools.management_tools._get_backup_manager')
    def test_get_system_status(self, mock_get_backup_manager, mock_get_config_manager, mock_getsize, mock_exists):
        """get_system_status 함수 테스트"""
        # 모의 객체 설정
        mock_backup_manager = MagicMock()
        mock_config_manager = MagicMock()
        mock_get_backup_manager.return_value = mock_backup_manager
        mock_get_config_manager.return_value = mock_config_manager
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        
        # 모의 설정 및 백업 정보
        mock_config_manager.get_config.return_value = {'database': {'path': '/path/to/db.sqlite'}}
        mock_config_manager.get_config_value.side_effect = lambda key, default=None: {
            'system.database.path': '/path/to/db.sqlite',
            'system.database.backup_enabled': True,
            'system.database.backup_interval_days': 7
        }.get(key, default)
        mock_config_manager.config_file = '/path/to/config.yaml'
        
        mock_db_backups = [{'timestamp': datetime.now()}]
        mock_config_backups = [{'timestamp': datetime.now()}]
        mock_backup_manager.list_backups.side_effect = lambda backup_type: mock_db_backups if backup_type == 'database' else mock_config_backups
        
        # 함수 호출
        result = get_system_status()
        
        # 검증
        self.assertTrue(result['success'])
        self.assertIn('system', result)
        self.assertIn('database', result['system'])
        self.assertIn('config', result['system'])
        self.assertIn('backups', result['system'])
        self.assertEqual(result['system']['database']['path'], '/path/to/db.sqlite')
        self.assertEqual(result['system']['database']['size'], 1024)
        self.assertTrue(result['system']['database']['backup_enabled'])
        self.assertEqual(result['system']['database']['backup_interval_days'], 7)
        self.assertEqual(result['system']['config']['path'], '/path/to/config.yaml')
        self.assertEqual(result['system']['backups']['database_count'], 1)
        self.assertEqual(result['system']['backups']['config_count'], 1)
    
    @patch('src.financial_tools.management_tools._get_config_manager')
    def test_update_settings(self, mock_get_config_manager):
        """update_settings 함수 테스트"""
        # 모의 객체 설정
        mock_config_manager = MagicMock()
        mock_get_config_manager.return_value = mock_config_manager
        
        # 모의 메서드 설정 - 첫 번째 테스트에서는 'invalid.key'를 제외한 모든 키에 대해 True 반환
        mock_config_manager.set_config_value.side_effect = lambda key, value: key != 'invalid.key'
        
        # 설정 업데이트 테스트
        result = update_settings({
            'system.database.backup_enabled': True,
            'system.database.backup_interval_days': 14,
            'invalid.key': 'value'
        })
        
        # 검증
        self.assertTrue(result['success'])
        self.assertIn('system.database.backup_enabled', result['updated_settings'])
        self.assertIn('system.database.backup_interval_days', result['updated_settings'])
        self.assertIn('invalid.key', result['failed_settings'])
        
        # 모든 설정 업데이트 실패 테스트
        # 새로운 모의 객체 설정
        new_mock_config_manager = MagicMock()
        new_mock_config_manager.set_config_value.return_value = False
        mock_get_config_manager.return_value = new_mock_config_manager
        
        # 함수 호출
        result = update_settings({
            'system.database.backup_enabled': True
        })
        
        # 검증
        self.assertFalse(result['success'])  # 모든 설정이 실패했으므로 success는 False여야 함
        self.assertEqual(len(result['updated_settings']), 0)
        self.assertIn('system.database.backup_enabled', result['failed_settings'])
    
    @patch('src.financial_tools.management_tools._get_config_manager')
    def test_get_settings(self, mock_get_config_manager):
        """get_settings 함수 테스트"""
        # 모의 객체 설정
        mock_config_manager = MagicMock()
        mock_get_config_manager.return_value = mock_config_manager
        
        # 모의 설정 데이터
        mock_system_config = {
            'database': {
                'path': '/path/to/db.sqlite',
                'backup_enabled': True,
                'backup_interval_days': 7
            },
            'logging': {
                'level': 'INFO'
            }
        }
        
        mock_all_config = {
            'system': mock_system_config,
            'user': {
                'display': {
                    'language': 'ko'
                }
            }
        }
        
        # 모의 메서드 설정
        mock_config_manager.get_config.side_effect = lambda section=None: mock_all_config if section is None else mock_system_config if section == 'system' else {}
        
        # 특정 섹션 설정 조회 테스트
        result = get_settings(section="system")
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['settings'], mock_system_config)
        self.assertEqual(result['section'], "system")
        
        # 전체 설정 조회 테스트
        result = get_settings()
        
        # 검증
        self.assertTrue(result['success'])
        self.assertEqual(result['settings'], mock_all_config)

if __name__ == '__main__':
    unittest.main()