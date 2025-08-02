# -*- coding: utf-8 -*-
"""
설정(Config) Repository 클래스

사용자 설정 및 분석 필터 데이터의 CRUD 작업을 처리합니다.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from src.models import UserPreference, AnalysisFilter
from src.repositories.base_repository import BaseRepository
from src.repositories.db_connection import DatabaseConnection

# 로거 설정
logger = logging.getLogger(__name__)


class UserPreferenceRepository(BaseRepository[UserPreference]):
    """
    사용자 설정 Repository 클래스
    
    사용자 설정 데이터의 CRUD 작업을 처리합니다.
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        사용자 설정 Repository 초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
        """
        self.db = db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """
        사용자 설정 테이블이 존재하는지 확인하고, 없으면 생성합니다.
        """
        # 테이블 생성 (SQLite는 한 번에 하나의 명령만 실행 가능)
        table_schema = """
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY,
            preference_key TEXT UNIQUE NOT NULL,
            preference_value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute(table_schema)
        
        # 인덱스 생성
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_preferences_key ON user_preferences(preference_key)")
    
    def create(self, entity: UserPreference) -> UserPreference:
        """
        새 사용자 설정을 생성합니다.
        
        Args:
            entity: 생성할 사용자 설정 객체
            
        Returns:
            UserPreference: 생성된 사용자 설정 (ID가 할당됨)
            
        Raises:
            ValueError: 유효하지 않은 사용자 설정인 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 유효성 검사
        entity.validate()
        
        # 중복 키 확인
        if self.exists_by_key(entity.preference_key):
            raise ValueError(f"이미 존재하는 설정 키입니다: {entity.preference_key}")
        
        query = """
        INSERT INTO user_preferences (
            preference_key, preference_value, description, updated_at
        ) VALUES (?, ?, ?, ?)
        """
        
        params = (
            entity.preference_key,
            entity.preference_value,
            entity.description,
            entity.updated_at.isoformat()
        )
        
        try:
            with self.db.transaction() as conn:
                conn.execute(query, params)
                entity.id = self.db.get_last_insert_id()
                logger.info(f"사용자 설정 생성 완료: ID={entity.id}, 키={entity.preference_key}")
                return entity
        except Exception as e:
            logger.error(f"사용자 설정 생성 실패: {e}")
            raise RuntimeError(f"사용자 설정 생성 실패: {e}")
    
    def read(self, id: int) -> Optional[UserPreference]:
        """
        ID로 사용자 설정을 조회합니다.
        
        Args:
            id: 조회할 사용자 설정의 ID
            
        Returns:
            Optional[UserPreference]: 조회된 사용자 설정 또는 None (없는 경우)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT * FROM user_preferences WHERE id = ?"
        
        try:
            result = self.db.fetch_one(query, (id,))
            if result:
                return self._map_to_entity(result)
            return None
        except Exception as e:
            logger.error(f"사용자 설정 조회 실패 (ID={id}): {e}")
            raise RuntimeError(f"사용자 설정 조회 실패: {e}")
    
    def read_by_key(self, key: str) -> Optional[UserPreference]:
        """
        키로 사용자 설정을 조회합니다.
        
        Args:
            key: 조회할 사용자 설정의 키
            
        Returns:
            Optional[UserPreference]: 조회된 사용자 설정 또는 None (없는 경우)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT * FROM user_preferences WHERE preference_key = ?"
        
        try:
            result = self.db.fetch_one(query, (key,))
            if result:
                return self._map_to_entity(result)
            return None
        except Exception as e:
            logger.error(f"사용자 설정 조회 실패 (키={key}): {e}")
            raise RuntimeError(f"사용자 설정 조회 실패: {e}")
    
    def update(self, entity: UserPreference) -> UserPreference:
        """
        사용자 설정을 업데이트합니다.
        
        Args:
            entity: 업데이트할 사용자 설정 객체 (ID 필수)
            
        Returns:
            UserPreference: 업데이트된 사용자 설정
            
        Raises:
            ValueError: 유효하지 않은 사용자 설정이거나 ID가 없는 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 유효성 검사
        entity.validate()
        
        if entity.id is None:
            raise ValueError("업데이트할 사용자 설정의 ID가 없습니다")
        
        # 존재 여부 확인
        if not self.exists(entity.id):
            raise ValueError(f"존재하지 않는 사용자 설정입니다: ID={entity.id}")
        
        # 업데이트 시간 갱신
        entity.updated_at = datetime.now()
        
        query = """
        UPDATE user_preferences SET
            preference_key = ?,
            preference_value = ?,
            description = ?,
            updated_at = ?
        WHERE id = ?
        """
        
        params = (
            entity.preference_key,
            entity.preference_value,
            entity.description,
            entity.updated_at.isoformat(),
            entity.id
        )
        
        try:
            with self.db.transaction() as conn:
                conn.execute(query, params)
                logger.info(f"사용자 설정 업데이트 완료: ID={entity.id}, 키={entity.preference_key}")
                return entity
        except Exception as e:
            logger.error(f"사용자 설정 업데이트 실패 (ID={entity.id}): {e}")
            raise RuntimeError(f"사용자 설정 업데이트 실패: {e}")
    
    def update_by_key(self, key: str, value: str, description: Optional[str] = None) -> Optional[UserPreference]:
        """
        키로 사용자 설정을 업데이트합니다. 없으면 생성합니다.
        
        Args:
            key: 설정 키
            value: 새 설정 값
            description: 설정 설명 (선택)
            
        Returns:
            Optional[UserPreference]: 업데이트된 사용자 설정 또는 None (실패 시)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        try:
            # 기존 설정 조회
            existing = self.read_by_key(key)
            
            if existing:
                # 기존 설정 업데이트
                existing.preference_value = value
                if description is not None:
                    existing.description = description
                return self.update(existing)
            else:
                # 새 설정 생성
                new_pref = UserPreference(
                    preference_key=key,
                    preference_value=value,
                    description=description
                )
                return self.create(new_pref)
        except Exception as e:
            logger.error(f"사용자 설정 업데이트 실패 (키={key}): {e}")
            raise RuntimeError(f"사용자 설정 업데이트 실패: {e}")
    
    def delete(self, id: int) -> bool:
        """
        ID로 사용자 설정을 삭제합니다.
        
        Args:
            id: 삭제할 사용자 설정의 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "DELETE FROM user_preferences WHERE id = ?"
        
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(query, (id,))
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"사용자 설정 삭제 완료: ID={id}")
                else:
                    logger.warning(f"삭제할 사용자 설정을 찾을 수 없음: ID={id}")
                return success
        except Exception as e:
            logger.error(f"사용자 설정 삭제 실패 (ID={id}): {e}")
            raise RuntimeError(f"사용자 설정 삭제 실패: {e}")
    
    def delete_by_key(self, key: str) -> bool:
        """
        키로 사용자 설정을 삭제합니다.
        
        Args:
            key: 삭제할 사용자 설정의 키
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "DELETE FROM user_preferences WHERE preference_key = ?"
        
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(query, (key,))
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"사용자 설정 삭제 완료: 키={key}")
                else:
                    logger.warning(f"삭제할 사용자 설정을 찾을 수 없음: 키={key}")
                return success
        except Exception as e:
            logger.error(f"사용자 설정 삭제 실패 (키={key}): {e}")
            raise RuntimeError(f"사용자 설정 삭제 실패: {e}")
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[UserPreference]:
        """
        필터 조건에 맞는 사용자 설정 목록을 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
                - key_prefix: 키 접두사
                - search_text: 키 또는 값에 포함된 텍스트
                - order_by: 정렬 기준 필드
                - order_direction: 정렬 방향 ('asc' 또는 'desc')
            
        Returns:
            List[UserPreference]: 조회된 사용자 설정 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT * FROM user_preferences"
        where_clauses = []
        params = []
        
        # 필터 조건 적용
        if 'key_prefix' in filters:
            where_clauses.append("preference_key LIKE ?")
            params.append(f"{filters['key_prefix']}%")
        
        if 'search_text' in filters:
            where_clauses.append("(preference_key LIKE ? OR preference_value LIKE ?)")
            search_param = f"%{filters['search_text']}%"
            params.extend([search_param, search_param])
        
        # WHERE 절 구성
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # 정렬
        order_by = filters.get('order_by', 'preference_key')
        order_direction = filters.get('order_direction', 'asc')
        query += f" ORDER BY {order_by} {order_direction}"
        
        try:
            results = self.db.fetch_all(query, tuple(params))
            return [self._map_to_entity(row) for row in results]
        except Exception as e:
            logger.error(f"사용자 설정 목록 조회 실패: {e}")
            raise RuntimeError(f"사용자 설정 목록 조회 실패: {e}")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        필터 조건에 맞는 사용자 설정 수를 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
            
        Returns:
            int: 조회된 사용자 설정 수
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT COUNT(*) as count FROM user_preferences"
        where_clauses = []
        params = []
        
        # 필터 조건 적용 (list 메서드와 동일한 로직)
        if 'key_prefix' in filters:
            where_clauses.append("preference_key LIKE ?")
            params.append(f"{filters['key_prefix']}%")
        
        if 'search_text' in filters:
            where_clauses.append("(preference_key LIKE ? OR preference_value LIKE ?)")
            search_param = f"%{filters['search_text']}%"
            params.extend([search_param, search_param])
        
        # WHERE 절 구성
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        try:
            result = self.db.fetch_one(query, tuple(params))
            return result['count'] if result else 0
        except Exception as e:
            logger.error(f"사용자 설정 수 조회 실패: {e}")
            raise RuntimeError(f"사용자 설정 수 조회 실패: {e}")
    
    def exists(self, id: int) -> bool:
        """
        ID에 해당하는 사용자 설정이 존재하는지 확인합니다.
        
        Args:
            id: 확인할 사용자 설정의 ID
            
        Returns:
            bool: 존재 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT 1 FROM user_preferences WHERE id = ? LIMIT 1"
        
        try:
            result = self.db.fetch_one(query, (id,))
            return result is not None
        except Exception as e:
            logger.error(f"사용자 설정 존재 여부 확인 실패 (ID={id}): {e}")
            raise RuntimeError(f"사용자 설정 존재 여부 확인 실패: {e}")
    
    def exists_by_key(self, key: str) -> bool:
        """
        키에 해당하는 사용자 설정이 존재하는지 확인합니다.
        
        Args:
            key: 확인할 사용자 설정의 키
            
        Returns:
            bool: 존재 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT 1 FROM user_preferences WHERE preference_key = ? LIMIT 1"
        
        try:
            result = self.db.fetch_one(query, (key,))
            return result is not None
        except Exception as e:
            logger.error(f"사용자 설정 존재 여부 확인 실패 (키={key}): {e}")
            raise RuntimeError(f"사용자 설정 존재 여부 확인 실패: {e}")
    
    def get_value(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """
        키에 해당하는 사용자 설정 값을 조회합니다.
        
        Args:
            key: 조회할 사용자 설정의 키
            default_value: 기본값 (설정이 없는 경우)
            
        Returns:
            Optional[str]: 설정 값 또는 기본값
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        try:
            pref = self.read_by_key(key)
            return pref.preference_value if pref else default_value
        except Exception as e:
            logger.error(f"사용자 설정 값 조회 실패 (키={key}): {e}")
            raise RuntimeError(f"사용자 설정 값 조회 실패: {e}")
    
    def get_boolean(self, key: str, default_value: bool = False) -> bool:
        """
        키에 해당하는 사용자 설정 값을 불리언으로 조회합니다.
        
        Args:
            key: 조회할 사용자 설정의 키
            default_value: 기본값 (설정이 없는 경우)
            
        Returns:
            bool: 설정 값 또는 기본값
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        try:
            pref = self.read_by_key(key)
            if pref:
                return UserPreference.get_boolean(pref.preference_value)
            return default_value
        except Exception as e:
            logger.error(f"사용자 설정 불리언 값 조회 실패 (키={key}): {e}")
            raise RuntimeError(f"사용자 설정 불리언 값 조회 실패: {e}")
    
    def get_int(self, key: str, default_value: int = 0) -> int:
        """
        키에 해당하는 사용자 설정 값을 정수로 조회합니다.
        
        Args:
            key: 조회할 사용자 설정의 키
            default_value: 기본값 (설정이 없는 경우)
            
        Returns:
            int: 설정 값 또는 기본값
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        try:
            pref = self.read_by_key(key)
            if pref:
                return UserPreference.get_int(pref.preference_value)
            return default_value
        except Exception as e:
            logger.error(f"사용자 설정 정수 값 조회 실패 (키={key}): {e}")
            raise RuntimeError(f"사용자 설정 정수 값 조회 실패: {e}")
    
    def get_float(self, key: str, default_value: float = 0.0) -> float:
        """
        키에 해당하는 사용자 설정 값을 실수로 조회합니다.
        
        Args:
            key: 조회할 사용자 설정의 키
            default_value: 기본값 (설정이 없는 경우)
            
        Returns:
            float: 설정 값 또는 기본값
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        try:
            pref = self.read_by_key(key)
            if pref:
                return UserPreference.get_float(pref.preference_value)
            return default_value
        except Exception as e:
            logger.error(f"사용자 설정 실수 값 조회 실패 (키={key}): {e}")
            raise RuntimeError(f"사용자 설정 실수 값 조회 실패: {e}")
    
    def get_list(self, key: str, default_value: Optional[List[str]] = None, delimiter: str = ',') -> List[str]:
        """
        키에 해당하는 사용자 설정 값을 리스트로 조회합니다.
        
        Args:
            key: 조회할 사용자 설정의 키
            default_value: 기본값 (설정이 없는 경우)
            delimiter: 구분자 (기본값: ',')
            
        Returns:
            List[str]: 설정 값 또는 기본값
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        if default_value is None:
            default_value = []
            
        try:
            pref = self.read_by_key(key)
            if pref:
                return UserPreference.get_list(pref.preference_value, delimiter)
            return default_value
        except Exception as e:
            logger.error(f"사용자 설정 리스트 값 조회 실패 (키={key}): {e}")
            raise RuntimeError(f"사용자 설정 리스트 값 조회 실패: {e}")
    
    def _map_to_entity(self, row: Dict[str, Any]) -> UserPreference:
        """
        데이터베이스 행을 사용자 설정 엔티티로 변환합니다.
        
        Args:
            row: 데이터베이스 행
            
        Returns:
            UserPreference: 변환된 사용자 설정 엔티티
        """
        return UserPreference(
            id=row['id'],
            preference_key=row['preference_key'],
            preference_value=row['preference_value'],
            description=row['description'],
            updated_at=datetime.fromisoformat(row['updated_at'])
        )


class AnalysisFilterRepository(BaseRepository[AnalysisFilter]):
    """
    분석 필터 Repository 클래스
    
    분석 필터 데이터의 CRUD 작업을 처리합니다.
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        분석 필터 Repository 초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
        """
        self.db = db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """
        분석 필터 테이블이 존재하는지 확인하고, 없으면 생성합니다.
        """
        # 테이블 생성 (SQLite는 한 번에 하나의 명령만 실행 가능)
        table_schema = """
        CREATE TABLE IF NOT EXISTS analysis_filters (
            id INTEGER PRIMARY KEY,
            filter_name TEXT NOT NULL,
            filter_config TEXT NOT NULL,
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute(table_schema)
        
        # 인덱스 생성
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_filters_name ON analysis_filters(filter_name)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_filters_default ON analysis_filters(is_default)")
    
    def create(self, entity: AnalysisFilter) -> AnalysisFilter:
        """
        새 분석 필터를 생성합니다.
        
        Args:
            entity: 생성할 분석 필터 객체
            
        Returns:
            AnalysisFilter: 생성된 분석 필터 (ID가 할당됨)
            
        Raises:
            ValueError: 유효하지 않은 분석 필터인 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 유효성 검사
        entity.validate()
        
        # 기본 필터 설정 시 기존 기본 필터 해제
        if entity.is_default:
            self._unset_all_defaults()
        
        query = """
        INSERT INTO analysis_filters (
            filter_name, filter_config, is_default, created_at
        ) VALUES (?, ?, ?, ?)
        """
        
        # filter_config를 JSON 문자열로 변환
        filter_config_json = json.dumps(entity.filter_config)
        
        params = (
            entity.filter_name,
            filter_config_json,
            entity.is_default,
            entity.created_at.isoformat()
        )
        
        try:
            with self.db.transaction() as conn:
                conn.execute(query, params)
                entity.id = self.db.get_last_insert_id()
                logger.info(f"분석 필터 생성 완료: ID={entity.id}, 이름={entity.filter_name}")
                return entity
        except Exception as e:
            logger.error(f"분석 필터 생성 실패: {e}")
            raise RuntimeError(f"분석 필터 생성 실패: {e}")
    
    def read(self, id: int) -> Optional[AnalysisFilter]:
        """
        ID로 분석 필터를 조회합니다.
        
        Args:
            id: 조회할 분석 필터의 ID
            
        Returns:
            Optional[AnalysisFilter]: 조회된 분석 필터 또는 None (없는 경우)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT * FROM analysis_filters WHERE id = ?"
        
        try:
            result = self.db.fetch_one(query, (id,))
            if result:
                return self._map_to_entity(result)
            return None
        except Exception as e:
            logger.error(f"분석 필터 조회 실패 (ID={id}): {e}")
            raise RuntimeError(f"분석 필터 조회 실패: {e}")
    
    def read_by_name(self, filter_name: str) -> Optional[AnalysisFilter]:
        """
        이름으로 분석 필터를 조회합니다.
        
        Args:
            filter_name: 조회할 분석 필터의 이름
            
        Returns:
            Optional[AnalysisFilter]: 조회된 분석 필터 또는 None (없는 경우)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT * FROM analysis_filters WHERE filter_name = ?"
        
        try:
            result = self.db.fetch_one(query, (filter_name,))
            if result:
                return self._map_to_entity(result)
            return None
        except Exception as e:
            logger.error(f"분석 필터 조회 실패 (이름={filter_name}): {e}")
            raise RuntimeError(f"분석 필터 조회 실패: {e}")
    
    def get_default_filter(self) -> Optional[AnalysisFilter]:
        """
        기본 분석 필터를 조회합니다.
        
        Returns:
            Optional[AnalysisFilter]: 기본 분석 필터 또는 None (없는 경우)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT * FROM analysis_filters WHERE is_default = 1 LIMIT 1"
        
        try:
            result = self.db.fetch_one(query)
            if result:
                return self._map_to_entity(result)
            return None
        except Exception as e:
            logger.error(f"기본 분석 필터 조회 실패: {e}")
            raise RuntimeError(f"기본 분석 필터 조회 실패: {e}")
    
    def update(self, entity: AnalysisFilter) -> AnalysisFilter:
        """
        분석 필터를 업데이트합니다.
        
        Args:
            entity: 업데이트할 분석 필터 객체 (ID 필수)
            
        Returns:
            AnalysisFilter: 업데이트된 분석 필터
            
        Raises:
            ValueError: 유효하지 않은 분석 필터이거나 ID가 없는 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 유효성 검사
        entity.validate()
        
        if entity.id is None:
            raise ValueError("업데이트할 분석 필터의 ID가 없습니다")
        
        # 존재 여부 확인
        if not self.exists(entity.id):
            raise ValueError(f"존재하지 않는 분석 필터입니다: ID={entity.id}")
        
        # 기본 필터 설정 시 기존 기본 필터 해제
        if entity.is_default:
            self._unset_all_defaults()
        
        query = """
        UPDATE analysis_filters SET
            filter_name = ?,
            filter_config = ?,
            is_default = ?
        WHERE id = ?
        """
        
        # filter_config를 JSON 문자열로 변환
        filter_config_json = json.dumps(entity.filter_config)
        
        params = (
            entity.filter_name,
            filter_config_json,
            entity.is_default,
            entity.id
        )
        
        try:
            with self.db.transaction() as conn:
                conn.execute(query, params)
                logger.info(f"분석 필터 업데이트 완료: ID={entity.id}, 이름={entity.filter_name}")
                return entity
        except Exception as e:
            logger.error(f"분석 필터 업데이트 실패 (ID={entity.id}): {e}")
            raise RuntimeError(f"분석 필터 업데이트 실패: {e}")
    
    def delete(self, id: int) -> bool:
        """
        ID로 분석 필터를 삭제합니다.
        
        Args:
            id: 삭제할 분석 필터의 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "DELETE FROM analysis_filters WHERE id = ?"
        
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(query, (id,))
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"분석 필터 삭제 완료: ID={id}")
                else:
                    logger.warning(f"삭제할 분석 필터를 찾을 수 없음: ID={id}")
                return success
        except Exception as e:
            logger.error(f"분석 필터 삭제 실패 (ID={id}): {e}")
            raise RuntimeError(f"분석 필터 삭제 실패: {e}")
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[AnalysisFilter]:
        """
        필터 조건에 맞는 분석 필터 목록을 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
                - name_contains: 이름에 포함된 텍스트
                - is_default: 기본 필터 여부
                - order_by: 정렬 기준 필드
                - order_direction: 정렬 방향 ('asc' 또는 'desc')
            
        Returns:
            List[AnalysisFilter]: 조회된 분석 필터 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT * FROM analysis_filters"
        where_clauses = []
        params = []
        
        # 필터 조건 적용
        if 'name_contains' in filters:
            where_clauses.append("filter_name LIKE ?")
            params.append(f"%{filters['name_contains']}%")
        
        if 'is_default' in filters:
            where_clauses.append("is_default = ?")
            params.append(1 if filters['is_default'] else 0)
        
        # WHERE 절 구성
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # 정렬
        order_by = filters.get('order_by', 'filter_name')
        order_direction = filters.get('order_direction', 'asc')
        query += f" ORDER BY {order_by} {order_direction}"
        
        try:
            results = self.db.fetch_all(query, tuple(params))
            return [self._map_to_entity(row) for row in results]
        except Exception as e:
            logger.error(f"분석 필터 목록 조회 실패: {e}")
            raise RuntimeError(f"분석 필터 목록 조회 실패: {e}")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        필터 조건에 맞는 분석 필터 수를 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
            
        Returns:
            int: 조회된 분석 필터 수
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT COUNT(*) as count FROM analysis_filters"
        where_clauses = []
        params = []
        
        # 필터 조건 적용 (list 메서드와 동일한 로직)
        if 'name_contains' in filters:
            where_clauses.append("filter_name LIKE ?")
            params.append(f"%{filters['name_contains']}%")
        
        if 'is_default' in filters:
            where_clauses.append("is_default = ?")
            params.append(1 if filters['is_default'] else 0)
        
        # WHERE 절 구성
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        try:
            result = self.db.fetch_one(query, tuple(params))
            return result['count'] if result else 0
        except Exception as e:
            logger.error(f"분석 필터 수 조회 실패: {e}")
            raise RuntimeError(f"분석 필터 수 조회 실패: {e}")
    
    def exists(self, id: int) -> bool:
        """
        ID에 해당하는 분석 필터가 존재하는지 확인합니다.
        
        Args:
            id: 확인할 분석 필터의 ID
            
        Returns:
            bool: 존재 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT 1 FROM analysis_filters WHERE id = ? LIMIT 1"
        
        try:
            result = self.db.fetch_one(query, (id,))
            return result is not None
        except Exception as e:
            logger.error(f"분석 필터 존재 여부 확인 실패 (ID={id}): {e}")
            raise RuntimeError(f"분석 필터 존재 여부 확인 실패: {e}")
    
    def exists_by_name(self, filter_name: str) -> bool:
        """
        이름에 해당하는 분석 필터가 존재하는지 확인합니다.
        
        Args:
            filter_name: 확인할 분석 필터의 이름
            
        Returns:
            bool: 존재 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT 1 FROM analysis_filters WHERE filter_name = ? LIMIT 1"
        
        try:
            result = self.db.fetch_one(query, (filter_name,))
            return result is not None
        except Exception as e:
            logger.error(f"분석 필터 존재 여부 확인 실패 (이름={filter_name}): {e}")
            raise RuntimeError(f"분석 필터 존재 여부 확인 실패: {e}")
    
    def set_as_default(self, id: int) -> bool:
        """
        특정 분석 필터를 기본값으로 설정합니다.
        
        Args:
            id: 기본값으로 설정할 분석 필터의 ID
            
        Returns:
            bool: 설정 성공 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        try:
            # 존재 여부 확인
            if not self.exists(id):
                logger.warning(f"기본값으로 설정할 분석 필터를 찾을 수 없음: ID={id}")
                return False
            
            with self.db.transaction() as conn:
                # 모든 필터의 기본값 설정 해제
                conn.execute("UPDATE analysis_filters SET is_default = 0")
                
                # 지정된 필터를 기본값으로 설정
                conn.execute("UPDATE analysis_filters SET is_default = 1 WHERE id = ?", (id,))
                
                logger.info(f"분석 필터를 기본값으로 설정 완료: ID={id}")
                return True
        except Exception as e:
            logger.error(f"분석 필터 기본값 설정 실패 (ID={id}): {e}")
            raise RuntimeError(f"분석 필터 기본값 설정 실패: {e}")
    
    def _unset_all_defaults(self) -> None:
        """
        모든 분석 필터의 기본값 설정을 해제합니다.
        
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        try:
            with self.db.transaction() as conn:
                conn.execute("UPDATE analysis_filters SET is_default = 0")
                logger.info("모든 분석 필터의 기본값 설정 해제 완료")
        except Exception as e:
            logger.error(f"분석 필터 기본값 설정 해제 실패: {e}")
            raise RuntimeError(f"분석 필터 기본값 설정 해제 실패: {e}")
    
    def _map_to_entity(self, row: Dict[str, Any]) -> AnalysisFilter:
        """
        데이터베이스 행을 분석 필터 엔티티로 변환합니다.
        
        Args:
            row: 데이터베이스 행
            
        Returns:
            AnalysisFilter: 변환된 분석 필터 엔티티
        """
        # JSON 문자열을 딕셔너리로 파싱
        filter_config = json.loads(row['filter_config'])
        
        return AnalysisFilter(
            id=row['id'],
            filter_name=row['filter_name'],
            filter_config=filter_config,
            is_default=bool(row['is_default']),
            created_at=datetime.fromisoformat(row['created_at'])
        )