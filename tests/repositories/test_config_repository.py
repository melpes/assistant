# -*- coding: utf-8 -*-
"""
UserPreferenceRepository 및 AnalysisFilterRepository 테스트
"""

import os
import unittest
import json
from datetime import datetime
import tempfile

from src.models import UserPreference, AnalysisFilter
from src.repositories.db_connection import DatabaseConnection
from src.repositories.config_repository import UserPreferenceRepository, AnalysisFilterRepository


class TestUserPreferenceRepository(unittest.TestCase):
    """UserPreferenceRepository 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 데이터베이스 파일 생성
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False).name
        self.db_connection = DatabaseConnection(self.temp_db_file)
        self.repository = UserPreferenceRepository(self.db_connection)
        
        # 테스트 데이터 생성
        self.test_preference = UserPreference(
            preference_key="test.preference.key",
            preference_value="테스트 값",
            description="테스트 설명"
        )
    
    def tearDown(self):
        """테스트 정리"""
        self.db_connection.close()
        if os.path.exists(self.temp_db_file):
            os.unlink(self.temp_db_file)
    
    def test_create_preference(self):
        """설정 생성 테스트"""
        # 설정 생성
        created = self.repository.create(self.test_preference)
        
        # 검증
        self.assertIsNotNone(created.id)
        self.assertEqual(created.preference_key, self.test_preference.preference_key)
        self.assertEqual(created.preference_value, self.test_preference.preference_value)
        self.assertEqual(created.description, self.test_preference.description)
    
    def test_read_preference(self):
        """설정 조회 테스트"""
        # 설정 생성
        created = self.repository.create(self.test_preference)
        
        # ID로 조회
        read = self.repository.read(created.id)
        
        # 검증
        self.assertIsNotNone(read)
        self.assertEqual(read.id, created.id)
        self.assertEqual(read.preference_key, created.preference_key)
        self.assertEqual(read.preference_value, created.preference_value)
        self.assertEqual(read.description, created.description)
    
    def test_read_by_key(self):
        """키로 설정 조회 테스트"""
        # 설정 생성
        self.repository.create(self.test_preference)
        
        # 키로 조회
        read = self.repository.read_by_key(self.test_preference.preference_key)
        
        # 검증
        self.assertIsNotNone(read)
        self.assertEqual(read.preference_key, self.test_preference.preference_key)
        self.assertEqual(read.preference_value, self.test_preference.preference_value)
        self.assertEqual(read.description, self.test_preference.description)
    
    def test_update_preference(self):
        """설정 업데이트 테스트"""
        # 설정 생성
        created = self.repository.create(self.test_preference)
        
        # 설정 수정
        created.preference_value = "수정된 값"
        created.description = "수정된 설명"
        updated = self.repository.update(created)
        
        # 검증
        self.assertEqual(updated.preference_value, "수정된 값")
        self.assertEqual(updated.description, "수정된 설명")
        
        # 데이터베이스에서 다시 조회하여 검증
        read = self.repository.read(created.id)
        self.assertEqual(read.preference_value, "수정된 값")
        self.assertEqual(read.description, "수정된 설명")
    
    def test_update_by_key(self):
        """키로 설정 업데이트 테스트"""
        # 설정 생성
        self.repository.create(self.test_preference)
        
        # 키로 업데이트
        updated = self.repository.update_by_key(
            self.test_preference.preference_key,
            "키로 수정된 값",
            "키로 수정된 설명"
        )
        
        # 검증
        self.assertIsNotNone(updated)
        self.assertEqual(updated.preference_value, "키로 수정된 값")
        self.assertEqual(updated.description, "키로 수정된 설명")
        
        # 데이터베이스에서 다시 조회하여 검증
        read = self.repository.read_by_key(self.test_preference.preference_key)
        self.assertEqual(read.preference_value, "키로 수정된 값")
        self.assertEqual(read.description, "키로 수정된 설명")
    
    def test_update_by_key_create_if_not_exists(self):
        """존재하지 않는 키로 업데이트 시 생성 테스트"""
        # 존재하지 않는 키로 업데이트
        new_key = "new.preference.key"
        created = self.repository.update_by_key(
            new_key,
            "새 값",
            "새 설명"
        )
        
        # 검증
        self.assertIsNotNone(created)
        self.assertEqual(created.preference_key, new_key)
        self.assertEqual(created.preference_value, "새 값")
        self.assertEqual(created.description, "새 설명")
        
        # 데이터베이스에서 조회하여 검증
        read = self.repository.read_by_key(new_key)
        self.assertIsNotNone(read)
        self.assertEqual(read.preference_value, "새 값")
        self.assertEqual(read.description, "새 설명")
    
    def test_delete_preference(self):
        """설정 삭제 테스트"""
        # 설정 생성
        created = self.repository.create(self.test_preference)
        
        # 삭제
        result = self.repository.delete(created.id)
        
        # 검증
        self.assertTrue(result)
        self.assertIsNone(self.repository.read(created.id))
    
    def test_delete_by_key(self):
        """키로 설정 삭제 테스트"""
        # 설정 생성
        self.repository.create(self.test_preference)
        
        # 키로 삭제
        result = self.repository.delete_by_key(self.test_preference.preference_key)
        
        # 검증
        self.assertTrue(result)
        self.assertIsNone(self.repository.read_by_key(self.test_preference.preference_key))
    
    def test_list_preferences(self):
        """설정 목록 조회 테스트"""
        # 여러 설정 생성
        keys = [
            "app.setting.theme",
            "app.setting.language",
            "user.profile.name",
            "user.profile.email",
            "system.version"
        ]
        
        for i, key in enumerate(keys):
            pref = UserPreference(
                preference_key=key,
                preference_value=f"값 {i+1}",
                description=f"설명 {i+1}"
            )
            self.repository.create(pref)
        
        # 모든 설정 조회
        all_prefs = self.repository.list()
        self.assertEqual(len(all_prefs), 5)
        
        # 필터링 테스트: 키 접두사
        app_prefs = self.repository.list({"key_prefix": "app.setting"})
        self.assertEqual(len(app_prefs), 2)
        
        # 필터링 테스트: 검색 텍스트
        user_prefs = self.repository.list({"search_text": "profile"})
        self.assertEqual(len(user_prefs), 2)
    
    def test_count_preferences(self):
        """설정 수 조회 테스트"""
        # 여러 설정 생성
        keys = [
            "app.setting.theme",
            "app.setting.language",
            "user.profile.name",
            "user.profile.email",
            "system.version"
        ]
        
        for i, key in enumerate(keys):
            pref = UserPreference(
                preference_key=key,
                preference_value=f"값 {i+1}",
                description=f"설명 {i+1}"
            )
            self.repository.create(pref)
        
        # 모든 설정 수 조회
        count = self.repository.count()
        self.assertEqual(count, 5)
        
        # 필터링 테스트: 키 접두사
        app_count = self.repository.count({"key_prefix": "app.setting"})
        self.assertEqual(app_count, 2)
        
        # 필터링 테스트: 검색 텍스트
        user_count = self.repository.count({"search_text": "profile"})
        self.assertEqual(user_count, 2)
    
    def test_exists_preference(self):
        """설정 존재 여부 테스트"""
        # 설정 생성
        created = self.repository.create(self.test_preference)
        
        # 존재 여부 확인
        self.assertTrue(self.repository.exists(created.id))
        self.assertFalse(self.repository.exists(999))
    
    def test_exists_by_key(self):
        """키로 설정 존재 여부 테스트"""
        # 설정 생성
        self.repository.create(self.test_preference)
        
        # 존재 여부 확인
        self.assertTrue(self.repository.exists_by_key(self.test_preference.preference_key))
        self.assertFalse(self.repository.exists_by_key("non.existent.key"))
    
    def test_get_value(self):
        """설정 값 조회 테스트"""
        # 설정 생성
        self.repository.create(self.test_preference)
        
        # 값 조회
        value = self.repository.get_value(self.test_preference.preference_key)
        self.assertEqual(value, self.test_preference.preference_value)
        
        # 존재하지 않는 키로 조회
        value = self.repository.get_value("non.existent.key", "기본값")
        self.assertEqual(value, "기본값")
    
    def test_get_typed_values(self):
        """타입별 설정 값 조회 테스트"""
        # 불리언 설정
        self.repository.create(UserPreference(
            preference_key="test.boolean",
            preference_value="true"
        ))
        
        # 정수 설정
        self.repository.create(UserPreference(
            preference_key="test.integer",
            preference_value="42"
        ))
        
        # 실수 설정
        self.repository.create(UserPreference(
            preference_key="test.float",
            preference_value="3.14"
        ))
        
        # 리스트 설정
        self.repository.create(UserPreference(
            preference_key="test.list",
            preference_value="항목1, 항목2, 항목3"
        ))
        
        # 타입별 값 조회
        bool_value = self.repository.get_boolean("test.boolean")
        int_value = self.repository.get_int("test.integer")
        float_value = self.repository.get_float("test.float")
        list_value = self.repository.get_list("test.list")
        
        # 검증
        self.assertTrue(bool_value)
        self.assertEqual(int_value, 42)
        self.assertEqual(float_value, 3.14)
        self.assertEqual(list_value, ["항목1", "항목2", "항목3"])
        
        # 존재하지 않는 키로 조회
        default_bool = self.repository.get_boolean("non.existent.key", True)
        default_int = self.repository.get_int("non.existent.key", 100)
        default_float = self.repository.get_float("non.existent.key", 9.9)
        default_list = self.repository.get_list("non.existent.key", ["기본"])
        
        # 검증
        self.assertTrue(default_bool)
        self.assertEqual(default_int, 100)
        self.assertEqual(default_float, 9.9)
        self.assertEqual(default_list, ["기본"])


class TestAnalysisFilterRepository(unittest.TestCase):
    """AnalysisFilterRepository 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 데이터베이스 파일 생성
        self.temp_db_file = tempfile.NamedTemporaryFile(delete=False).name
        self.db_connection = DatabaseConnection(self.temp_db_file)
        self.repository = AnalysisFilterRepository(self.db_connection)
        
        # 테스트 데이터 생성
        self.test_filter_config = {
            "conditions": {
                "operator": "and",
                "conditions": [
                    {
                        "field": "category",
                        "comparison": "equals",
                        "value": "식비"
                    },
                    {
                        "field": "amount",
                        "comparison": "greater_than",
                        "value": 10000
                    }
                ]
            }
        }
        
        self.test_filter = AnalysisFilter(
            filter_name="테스트 필터",
            filter_config=self.test_filter_config,
            is_default=False
        )
    
    def tearDown(self):
        """테스트 정리"""
        self.db_connection.close()
        if os.path.exists(self.temp_db_file):
            os.unlink(self.temp_db_file)
    
    def test_create_filter(self):
        """필터 생성 테스트"""
        # 필터 생성
        created = self.repository.create(self.test_filter)
        
        # 검증
        self.assertIsNotNone(created.id)
        self.assertEqual(created.filter_name, self.test_filter.filter_name)
        self.assertEqual(created.filter_config, self.test_filter.filter_config)
        self.assertEqual(created.is_default, self.test_filter.is_default)
    
    def test_read_filter(self):
        """필터 조회 테스트"""
        # 필터 생성
        created = self.repository.create(self.test_filter)
        
        # ID로 조회
        read = self.repository.read(created.id)
        
        # 검증
        self.assertIsNotNone(read)
        self.assertEqual(read.id, created.id)
        self.assertEqual(read.filter_name, created.filter_name)
        self.assertEqual(read.filter_config, created.filter_config)
        self.assertEqual(read.is_default, created.is_default)
    
    def test_read_by_name(self):
        """이름으로 필터 조회 테스트"""
        # 필터 생성
        self.repository.create(self.test_filter)
        
        # 이름으로 조회
        read = self.repository.read_by_name(self.test_filter.filter_name)
        
        # 검증
        self.assertIsNotNone(read)
        self.assertEqual(read.filter_name, self.test_filter.filter_name)
        self.assertEqual(read.filter_config, self.test_filter.filter_config)
    
    def test_update_filter(self):
        """필터 업데이트 테스트"""
        # 필터 생성
        created = self.repository.create(self.test_filter)
        
        # 필터 수정
        created.filter_name = "수정된 필터"
        created.filter_config["conditions"]["conditions"].append({
            "field": "description",
            "comparison": "contains",
            "value": "테스트"
        })
        created.is_default = True
        updated = self.repository.update(created)
        
        # 검증
        self.assertEqual(updated.filter_name, "수정된 필터")
        self.assertEqual(len(updated.filter_config["conditions"]["conditions"]), 3)
        self.assertTrue(updated.is_default)
        
        # 데이터베이스에서 다시 조회하여 검증
        read = self.repository.read(created.id)
        self.assertEqual(read.filter_name, "수정된 필터")
        self.assertEqual(len(read.filter_config["conditions"]["conditions"]), 3)
        self.assertTrue(read.is_default)
    
    def test_delete_filter(self):
        """필터 삭제 테스트"""
        # 필터 생성
        created = self.repository.create(self.test_filter)
        
        # 삭제
        result = self.repository.delete(created.id)
        
        # 검증
        self.assertTrue(result)
        self.assertIsNone(self.repository.read(created.id))
    
    def test_list_filters(self):
        """필터 목록 조회 테스트"""
        # 여러 필터 생성
        filter_names = ["식비 필터", "교통비 필터", "생활용품 필터", "문화/오락 필터", "기타 필터"]
        
        for i, name in enumerate(filter_names):
            filter_config = {
                "conditions": {
                    "operator": "and",
                    "conditions": [
                        {
                            "field": "category",
                            "comparison": "equals",
                            "value": name.split()[0]
                        }
                    ]
                }
            }
            
            filter_obj = AnalysisFilter(
                filter_name=name,
                filter_config=filter_config,
                is_default=i == 0  # 첫 번째 필터만 기본값으로 설정
            )
            self.repository.create(filter_obj)
        
        # 모든 필터 조회
        all_filters = self.repository.list()
        self.assertEqual(len(all_filters), 5)
        
        # 필터링 테스트: 이름 포함
        food_filters = self.repository.list({"name_contains": "식비"})
        self.assertEqual(len(food_filters), 1)
        
        # 필터링 테스트: 기본값 필터
        default_filters = self.repository.list({"is_default": True})
        self.assertEqual(len(default_filters), 1)
        self.assertEqual(default_filters[0].filter_name, "식비 필터")
    
    def test_count_filters(self):
        """필터 수 조회 테스트"""
        # 여러 필터 생성
        filter_names = ["식비 필터", "교통비 필터", "생활용품 필터", "문화/오락 필터", "기타 필터"]
        
        for i, name in enumerate(filter_names):
            filter_config = {
                "conditions": {
                    "operator": "and",
                    "conditions": [
                        {
                            "field": "category",
                            "comparison": "equals",
                            "value": name.split()[0]
                        }
                    ]
                }
            }
            
            filter_obj = AnalysisFilter(
                filter_name=name,
                filter_config=filter_config,
                is_default=i == 0  # 첫 번째 필터만 기본값으로 설정
            )
            self.repository.create(filter_obj)
        
        # 모든 필터 수 조회
        count = self.repository.count()
        self.assertEqual(count, 5)
        
        # 필터링 테스트: 이름 포함
        food_count = self.repository.count({"name_contains": "식비"})
        self.assertEqual(food_count, 1)
        
        # 필터링 테스트: 기본값 필터
        default_count = self.repository.count({"is_default": True})
        self.assertEqual(default_count, 1)
    
    def test_exists_filter(self):
        """필터 존재 여부 테스트"""
        # 필터 생성
        created = self.repository.create(self.test_filter)
        
        # 존재 여부 확인
        self.assertTrue(self.repository.exists(created.id))
        self.assertFalse(self.repository.exists(999))
    
    def test_exists_by_name(self):
        """이름으로 필터 존재 여부 테스트"""
        # 필터 생성
        self.repository.create(self.test_filter)
        
        # 존재 여부 확인
        self.assertTrue(self.repository.exists_by_name(self.test_filter.filter_name))
        self.assertFalse(self.repository.exists_by_name("존재하지 않는 필터"))
    
    def test_get_default_filter(self):
        """기본 필터 조회 테스트"""
        # 기본값이 아닌 필터 생성
        self.repository.create(self.test_filter)
        
        # 기본값 필터 조회
        default_filter = self.repository.get_default_filter()
        self.assertIsNone(default_filter)
        
        # 기본값 필터 생성
        default_filter_obj = AnalysisFilter(
            filter_name="기본 필터",
            filter_config={"conditions": {"operator": "and", "conditions": []}},
            is_default=True
        )
        self.repository.create(default_filter_obj)
        
        # 기본값 필터 조회
        default_filter = self.repository.get_default_filter()
        self.assertIsNotNone(default_filter)
        self.assertEqual(default_filter.filter_name, "기본 필터")
        self.assertTrue(default_filter.is_default)
    
    def test_set_as_default(self):
        """필터를 기본값으로 설정 테스트"""
        # 여러 필터 생성
        filter1 = self.repository.create(AnalysisFilter(
            filter_name="필터 1",
            filter_config={"conditions": {"operator": "and", "conditions": []}},
            is_default=False
        ))
        
        filter2 = self.repository.create(AnalysisFilter(
            filter_name="필터 2",
            filter_config={"conditions": {"operator": "and", "conditions": []}},
            is_default=True
        ))
        
        filter3 = self.repository.create(AnalysisFilter(
            filter_name="필터 3",
            filter_config={"conditions": {"operator": "and", "conditions": []}},
            is_default=False
        ))
        
        # 기본값 필터 확인
        default_filter = self.repository.get_default_filter()
        self.assertEqual(default_filter.id, filter2.id)
        
        # 다른 필터를 기본값으로 설정
        result = self.repository.set_as_default(filter3.id)
        self.assertTrue(result)
        
        # 기본값 필터 다시 확인
        default_filter = self.repository.get_default_filter()
        self.assertEqual(default_filter.id, filter3.id)
        
        # 이전 기본값 필터 확인
        filter2 = self.repository.read(filter2.id)
        self.assertFalse(filter2.is_default)


if __name__ == "__main__":
    unittest.main()