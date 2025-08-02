# -*- coding: utf-8 -*-
"""
분류 규칙(ClassificationRule) Repository 클래스

분류 규칙 데이터의 CRUD 작업을 처리합니다.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.models import ClassificationRule
from src.repositories.base_repository import BaseRepository
from src.repositories.db_connection import DatabaseConnection

# 로거 설정
logger = logging.getLogger(__name__)


class RuleRepository(BaseRepository[ClassificationRule]):
    """
    분류 규칙 Repository 클래스
    
    분류 규칙 데이터의 CRUD 작업을 처리합니다.
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        분류 규칙 Repository 초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
        """
        self.db = db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """
        분류 규칙 테이블이 존재하는지 확인하고, 없으면 생성합니다.
        """
        # 테이블 생성 (SQLite는 한 번에 하나의 명령만 실행 가능)
        table_schema = """
        CREATE TABLE IF NOT EXISTS classification_rules (
            id INTEGER PRIMARY KEY,
            rule_name TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            condition_type TEXT NOT NULL,
            condition_value TEXT NOT NULL,
            target_value TEXT NOT NULL,
            priority INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_by TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute(table_schema)
        
        # 인덱스 생성
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_rules_type ON classification_rules(rule_type)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_rules_active ON classification_rules(is_active)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_rules_priority ON classification_rules(priority)")
    
    def create(self, entity: ClassificationRule) -> ClassificationRule:
        """
        새 분류 규칙을 생성합니다.
        
        Args:
            entity: 생성할 분류 규칙 객체
            
        Returns:
            ClassificationRule: 생성된 분류 규칙 (ID가 할당됨)
            
        Raises:
            ValueError: 유효하지 않은 분류 규칙인 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 유효성 검사
        entity.validate()
        
        query = """
        INSERT INTO classification_rules (
            rule_name, rule_type, condition_type, condition_value,
            target_value, priority, is_active, created_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            entity.rule_name,
            entity.rule_type,
            entity.condition_type,
            entity.condition_value,
            entity.target_value,
            entity.priority,
            entity.is_active,
            entity.created_by,
            entity.created_at.isoformat()
        )
        
        try:
            with self.db.transaction() as conn:
                conn.execute(query, params)
                entity.id = self.db.get_last_insert_id()
                logger.info(f"분류 규칙 생성 완료: ID={entity.id}, 이름={entity.rule_name}")
                return entity
        except Exception as e:
            logger.error(f"분류 규칙 생성 실패: {e}")
            raise RuntimeError(f"분류 규칙 생성 실패: {e}")
    
    def read(self, id: int) -> Optional[ClassificationRule]:
        """
        ID로 분류 규칙을 조회합니다.
        
        Args:
            id: 조회할 분류 규칙의 ID
            
        Returns:
            Optional[ClassificationRule]: 조회된 분류 규칙 또는 None (없는 경우)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT * FROM classification_rules WHERE id = ?"
        
        try:
            result = self.db.fetch_one(query, (id,))
            if result:
                return self._map_to_entity(result)
            return None
        except Exception as e:
            logger.error(f"분류 규칙 조회 실패 (ID={id}): {e}")
            raise RuntimeError(f"분류 규칙 조회 실패: {e}")
    
    def update(self, entity: ClassificationRule) -> ClassificationRule:
        """
        분류 규칙을 업데이트합니다.
        
        Args:
            entity: 업데이트할 분류 규칙 객체 (ID 필수)
            
        Returns:
            ClassificationRule: 업데이트된 분류 규칙
            
        Raises:
            ValueError: 유효하지 않은 분류 규칙이거나 ID가 없는 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 유효성 검사
        entity.validate()
        
        if entity.id is None:
            raise ValueError("업데이트할 분류 규칙의 ID가 없습니다")
        
        # 존재 여부 확인
        if not self.exists(entity.id):
            raise ValueError(f"존재하지 않는 분류 규칙입니다: ID={entity.id}")
        
        query = """
        UPDATE classification_rules SET
            rule_name = ?,
            rule_type = ?,
            condition_type = ?,
            condition_value = ?,
            target_value = ?,
            priority = ?,
            is_active = ?,
            created_by = ?
        WHERE id = ?
        """
        
        params = (
            entity.rule_name,
            entity.rule_type,
            entity.condition_type,
            entity.condition_value,
            entity.target_value,
            entity.priority,
            entity.is_active,
            entity.created_by,
            entity.id
        )
        
        try:
            with self.db.transaction() as conn:
                conn.execute(query, params)
                logger.info(f"분류 규칙 업데이트 완료: ID={entity.id}, 이름={entity.rule_name}")
                return entity
        except Exception as e:
            logger.error(f"분류 규칙 업데이트 실패 (ID={entity.id}): {e}")
            raise RuntimeError(f"분류 규칙 업데이트 실패: {e}")
    
    def delete(self, id: int) -> bool:
        """
        ID로 분류 규칙을 삭제합니다.
        
        Args:
            id: 삭제할 분류 규칙의 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "DELETE FROM classification_rules WHERE id = ?"
        
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(query, (id,))
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"분류 규칙 삭제 완료: ID={id}")
                else:
                    logger.warning(f"삭제할 분류 규칙을 찾을 수 없음: ID={id}")
                return success
        except Exception as e:
            logger.error(f"분류 규칙 삭제 실패 (ID={id}): {e}")
            raise RuntimeError(f"분류 규칙 삭제 실패: {e}")
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[ClassificationRule]:
        """
        필터 조건에 맞는 분류 규칙 목록을 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
                - rule_type: 규칙 유형
                - is_active: 활성화 여부
                - created_by: 생성자
                - min_priority: 최소 우선순위
                - max_priority: 최대 우선순위
                - order_by: 정렬 기준 필드
                - order_direction: 정렬 방향 ('asc' 또는 'desc')
            
        Returns:
            List[ClassificationRule]: 조회된 분류 규칙 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT * FROM classification_rules"
        where_clauses = []
        params = []
        
        # 필터 조건 적용
        if 'rule_type' in filters:
            where_clauses.append("rule_type = ?")
            params.append(filters['rule_type'])
        
        if 'is_active' in filters:
            where_clauses.append("is_active = ?")
            params.append(1 if filters['is_active'] else 0)
        
        if 'created_by' in filters:
            where_clauses.append("created_by = ?")
            params.append(filters['created_by'])
        
        if 'min_priority' in filters:
            where_clauses.append("priority >= ?")
            params.append(int(filters['min_priority']))
        
        if 'max_priority' in filters:
            where_clauses.append("priority <= ?")
            params.append(int(filters['max_priority']))
        
        # WHERE 절 구성
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # 정렬
        order_by = filters.get('order_by', 'priority')
        order_direction = filters.get('order_direction', 'desc')
        query += f" ORDER BY {order_by} {order_direction}"
        
        try:
            results = self.db.fetch_all(query, tuple(params))
            return [self._map_to_entity(row) for row in results]
        except Exception as e:
            logger.error(f"분류 규칙 목록 조회 실패: {e}")
            raise RuntimeError(f"분류 규칙 목록 조회 실패: {e}")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        필터 조건에 맞는 분류 규칙 수를 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
            
        Returns:
            int: 조회된 분류 규칙 수
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT COUNT(*) as count FROM classification_rules"
        where_clauses = []
        params = []
        
        # 필터 조건 적용 (list 메서드와 동일한 로직)
        if 'rule_type' in filters:
            where_clauses.append("rule_type = ?")
            params.append(filters['rule_type'])
        
        if 'is_active' in filters:
            where_clauses.append("is_active = ?")
            params.append(1 if filters['is_active'] else 0)
        
        if 'created_by' in filters:
            where_clauses.append("created_by = ?")
            params.append(filters['created_by'])
        
        if 'min_priority' in filters:
            where_clauses.append("priority >= ?")
            params.append(int(filters['min_priority']))
        
        if 'max_priority' in filters:
            where_clauses.append("priority <= ?")
            params.append(int(filters['max_priority']))
        
        # WHERE 절 구성
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        try:
            result = self.db.fetch_one(query, tuple(params))
            return result['count'] if result else 0
        except Exception as e:
            logger.error(f"분류 규칙 수 조회 실패: {e}")
            raise RuntimeError(f"분류 규칙 수 조회 실패: {e}")
    
    def exists(self, id: int) -> bool:
        """
        ID에 해당하는 분류 규칙이 존재하는지 확인합니다.
        
        Args:
            id: 확인할 분류 규칙의 ID
            
        Returns:
            bool: 존재 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT 1 FROM classification_rules WHERE id = ? LIMIT 1"
        
        try:
            result = self.db.fetch_one(query, (id,))
            return result is not None
        except Exception as e:
            logger.error(f"분류 규칙 존재 여부 확인 실패 (ID={id}): {e}")
            raise RuntimeError(f"분류 규칙 존재 여부 확인 실패: {e}")
    
    def get_active_rules_by_type(self, rule_type: str) -> List[ClassificationRule]:
        """
        특정 유형의 활성화된 규칙 목록을 우선순위 순으로 조회합니다.
        
        Args:
            rule_type: 규칙 유형
            
        Returns:
            List[ClassificationRule]: 활성화된 규칙 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = """
        SELECT * FROM classification_rules 
        WHERE rule_type = ? AND is_active = 1
        ORDER BY priority DESC
        """
        
        try:
            results = self.db.fetch_all(query, (rule_type,))
            return [self._map_to_entity(row) for row in results]
        except Exception as e:
            logger.error(f"활성화된 규칙 목록 조회 실패 (유형={rule_type}): {e}")
            raise RuntimeError(f"활성화된 규칙 목록 조회 실패: {e}")
    
    def bulk_create(self, entities: List[ClassificationRule]) -> List[ClassificationRule]:
        """
        여러 분류 규칙을 일괄 생성합니다.
        
        Args:
            entities: 생성할 분류 규칙 객체 목록
            
        Returns:
            List[ClassificationRule]: 생성된 분류 규칙 목록
            
        Raises:
            ValueError: 유효하지 않은 분류 규칙이 있는 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        if not entities:
            return []
        
        # 유효성 검사
        for entity in entities:
            entity.validate()
        
        query = """
        INSERT INTO classification_rules (
            rule_name, rule_type, condition_type, condition_value,
            target_value, priority, is_active, created_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params_list = []
        for entity in entities:
            params = (
                entity.rule_name,
                entity.rule_type,
                entity.condition_type,
                entity.condition_value,
                entity.target_value,
                entity.priority,
                entity.is_active,
                entity.created_by,
                entity.created_at.isoformat()
            )
            params_list.append(params)
        
        try:
            with self.db.transaction() as conn:
                conn.executemany(query, params_list)
                logger.info(f"일괄 분류 규칙 생성 완료: {len(entities)}개")
                
                # 생성된 규칙 조회
                created_rules = []
                for entity in entities:
                    # 규칙 이름과 조건으로 조회
                    query = """
                    SELECT * FROM classification_rules 
                    WHERE rule_name = ? AND condition_value = ? AND target_value = ?
                    ORDER BY id DESC LIMIT 1
                    """
                    result = self.db.fetch_one(query, (entity.rule_name, entity.condition_value, entity.target_value))
                    if result:
                        created_rules.append(self._map_to_entity(result))
                
                return created_rules
        except Exception as e:
            logger.error(f"일괄 분류 규칙 생성 실패: {e}")
            raise RuntimeError(f"일괄 분류 규칙 생성 실패: {e}")
    
    def _map_to_entity(self, row: Dict[str, Any]) -> ClassificationRule:
        """
        데이터베이스 행을 분류 규칙 엔티티로 변환합니다.
        
        Args:
            row: 데이터베이스 행
            
        Returns:
            ClassificationRule: 변환된 분류 규칙 엔티티
        """
        return ClassificationRule(
            id=row['id'],
            rule_name=row['rule_name'],
            rule_type=row['rule_type'],
            condition_type=row['condition_type'],
            condition_value=row['condition_value'],
            target_value=row['target_value'],
            priority=row['priority'],
            is_active=bool(row['is_active']),
            created_by=row['created_by'],
            created_at=datetime.fromisoformat(row['created_at'])
        )