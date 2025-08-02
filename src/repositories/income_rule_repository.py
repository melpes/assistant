# -*- coding: utf-8 -*-
"""
수입 규칙(IncomeRule) Repository 클래스

수입 규칙 데이터의 CRUD 작업을 처리합니다.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.models.income_rule import IncomeRule
from src.repositories.base_repository import BaseRepository
from src.repositories.db_connection import DatabaseConnection

# 로거 설정
logger = logging.getLogger(__name__)


class IncomeRuleRepository(BaseRepository[IncomeRule]):
    """
    수입 규칙 Repository 클래스
    
    수입 규칙 데이터의 CRUD 작업을 처리합니다.
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        수입 규칙 Repository 초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
        """
        self.db = db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """
        수입 규칙 테이블이 존재하는지 확인하고, 없으면 생성합니다.
        """
        # 테이블 생성
        table_schema = """
        CREATE TABLE IF NOT EXISTS income_rules (
            id INTEGER PRIMARY KEY,
            rule_name TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            condition_type TEXT NOT NULL,
            condition_value TEXT NOT NULL,
            target_value TEXT NOT NULL,
            priority INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_by TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute(table_schema)
        
        # 인덱스 생성
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_income_rules_type ON income_rules(rule_type)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_income_rules_active ON income_rules(is_active)")
    
    def create(self, entity: IncomeRule) -> IncomeRule:
        """
        새 수입 규칙을 생성합니다.
        
        Args:
            entity: 생성할 수입 규칙 객체
            
        Returns:
            IncomeRule: 생성된 수입 규칙 (ID가 할당됨)
            
        Raises:
            ValueError: 유효하지 않은 수입 규칙인 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 유효성 검사
        entity.validate()
        
        query = """
        INSERT INTO income_rules (
            rule_name, rule_type, condition_type, condition_value, target_value,
            priority, is_active, created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            entity.created_at.isoformat(),
            entity.updated_at.isoformat()
        )
        
        try:
            with self.db.transaction() as conn:
                conn.execute(query, params)
                entity.id = self.db.get_last_insert_id()
                logger.info(f"수입 규칙 생성 완료: ID={entity.id}, 이름={entity.rule_name}")
                return entity
        except Exception as e:
            logger.error(f"수입 규칙 생성 실패: {e}")
            raise RuntimeError(f"수입 규칙 생성 실패: {e}")
    
    def read(self, id: int) -> Optional[IncomeRule]:
        """
        ID로 수입 규칙을 조회합니다.
        
        Args:
            id: 조회할 수입 규칙의 ID
            
        Returns:
            Optional[IncomeRule]: 조회된 수입 규칙 또는 None (없는 경우)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT * FROM income_rules WHERE id = ?"
        
        try:
            result = self.db.fetch_one(query, (id,))
            if result:
                return self._map_to_entity(result)
            return None
        except Exception as e:
            logger.error(f"수입 규칙 조회 실패 (ID={id}): {e}")
            raise RuntimeError(f"수입 규칙 조회 실패: {e}")
    
    def update(self, entity: IncomeRule) -> IncomeRule:
        """
        수입 규칙을 업데이트합니다.
        
        Args:
            entity: 업데이트할 수입 규칙 객체 (ID 필수)
            
        Returns:
            IncomeRule: 업데이트된 수입 규칙
            
        Raises:
            ValueError: 유효하지 않은 수입 규칙이거나 ID가 없는 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 유효성 검사
        entity.validate()
        
        if entity.id is None:
            raise ValueError("업데이트할 수입 규칙의 ID가 없습니다")
        
        # 존재 여부 확인
        if not self.exists(entity.id):
            raise ValueError(f"존재하지 않는 수입 규칙입니다: ID={entity.id}")
        
        query = """
        UPDATE income_rules SET
            rule_name = ?,
            rule_type = ?,
            condition_type = ?,
            condition_value = ?,
            target_value = ?,
            priority = ?,
            is_active = ?,
            created_by = ?,
            updated_at = ?
        WHERE id = ?
        """
        
        # 업데이트 시간 갱신
        entity.updated_at = datetime.now()
        
        params = (
            entity.rule_name,
            entity.rule_type,
            entity.condition_type,
            entity.condition_value,
            entity.target_value,
            entity.priority,
            entity.is_active,
            entity.created_by,
            entity.updated_at.isoformat(),
            entity.id
        )
        
        try:
            with self.db.transaction() as conn:
                conn.execute(query, params)
                logger.info(f"수입 규칙 업데이트 완료: ID={entity.id}, 이름={entity.rule_name}")
                return entity
        except Exception as e:
            logger.error(f"수입 규칙 업데이트 실패 (ID={entity.id}): {e}")
            raise RuntimeError(f"수입 규칙 업데이트 실패: {e}")
    
    def delete(self, id: int) -> bool:
        """
        ID로 수입 규칙을 삭제합니다.
        
        Args:
            id: 삭제할 수입 규칙의 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "DELETE FROM income_rules WHERE id = ?"
        
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(query, (id,))
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"수입 규칙 삭제 완료: ID={id}")
                else:
                    logger.warning(f"삭제할 수입 규칙을 찾을 수 없음: ID={id}")
                return success
        except Exception as e:
            logger.error(f"수입 규칙 삭제 실패 (ID={id}): {e}")
            raise RuntimeError(f"수입 규칙 삭제 실패: {e}")
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[IncomeRule]:
        """
        필터 조건에 맞는 수입 규칙 목록을 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
                - rule_type: 규칙 유형
                - is_active: 활성화 여부
                - created_by: 생성자
                - search: 이름 검색어
                - limit: 최대 결과 수
                - offset: 결과 오프셋
                - order_by: 정렬 기준 필드
                - order_direction: 정렬 방향 ('asc' 또는 'desc')
            
        Returns:
            List[IncomeRule]: 조회된 수입 규칙 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT * FROM income_rules"
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
        
        if 'search' in filters and filters['search']:
            where_clauses.append("rule_name LIKE ?")
            params.append(f"%{filters['search']}%")
        
        # WHERE 절 구성
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # 정렬
        order_by = filters.get('order_by', 'priority')
        order_direction = filters.get('order_direction', 'desc')
        query += f" ORDER BY {order_by} {order_direction}"
        
        # 페이징
        if 'limit' in filters:
            query += " LIMIT ?"
            params.append(int(filters['limit']))
            
            if 'offset' in filters:
                query += " OFFSET ?"
                params.append(int(filters['offset']))
        
        try:
            results = self.db.fetch_all(query, tuple(params))
            return [self._map_to_entity(row) for row in results]
        except Exception as e:
            logger.error(f"수입 규칙 목록 조회 실패: {e}")
            raise RuntimeError(f"수입 규칙 목록 조회 실패: {e}")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        필터 조건에 맞는 수입 규칙 수를 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
            
        Returns:
            int: 조회된 수입 규칙 수
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT COUNT(*) as count FROM income_rules"
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
        
        if 'search' in filters and filters['search']:
            where_clauses.append("rule_name LIKE ?")
            params.append(f"%{filters['search']}%")
        
        # WHERE 절 구성
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        try:
            result = self.db.fetch_one(query, tuple(params))
            return result['count'] if result else 0
        except Exception as e:
            logger.error(f"수입 규칙 수 조회 실패: {e}")
            raise RuntimeError(f"수입 규칙 수 조회 실패: {e}")
    
    def exists(self, id: int) -> bool:
        """
        ID에 해당하는 수입 규칙이 존재하는지 확인합니다.
        
        Args:
            id: 확인할 수입 규칙의 ID
            
        Returns:
            bool: 존재 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT 1 FROM income_rules WHERE id = ? LIMIT 1"
        
        try:
            result = self.db.fetch_one(query, (id,))
            return result is not None
        except Exception as e:
            logger.error(f"수입 규칙 존재 여부 확인 실패 (ID={id}): {e}")
            raise RuntimeError(f"수입 규칙 존재 여부 확인 실패: {e}")
    
    def get_active_rules(self, rule_type: Optional[str] = None) -> List[IncomeRule]:
        """
        활성화된 수입 규칙 목록을 조회합니다.
        
        Args:
            rule_type: 규칙 유형 (선택)
            
        Returns:
            List[IncomeRule]: 활성화된 수입 규칙 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 기본 쿼리
        query = "SELECT * FROM income_rules WHERE is_active = 1"
        params = []
        
        # 규칙 유형 필터
        if rule_type:
            query += " AND rule_type = ?"
            params.append(rule_type)
        
        # 우선순위 기준 정렬
        query += " ORDER BY priority DESC"
        
        try:
            results = self.db.fetch_all(query, tuple(params))
            return [self._map_to_entity(row) for row in results]
        except Exception as e:
            logger.error(f"활성화된 수입 규칙 목록 조회 실패: {e}")
            raise RuntimeError(f"활성화된 수입 규칙 목록 조회 실패: {e}")
    
    def bulk_create(self, entities: List[IncomeRule]) -> List[IncomeRule]:
        """
        여러 수입 규칙을 일괄 생성합니다.
        
        Args:
            entities: 생성할 수입 규칙 객체 목록
            
        Returns:
            List[IncomeRule]: 생성된 수입 규칙 목록
            
        Raises:
            ValueError: 유효하지 않은 수입 규칙이 있는 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        if not entities:
            return []
        
        # 유효성 검사
        for entity in entities:
            entity.validate()
        
        query = """
        INSERT INTO income_rules (
            rule_name, rule_type, condition_type, condition_value, target_value,
            priority, is_active, created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                entity.created_at.isoformat(),
                entity.updated_at.isoformat()
            )
            params_list.append(params)
        
        try:
            with self.db.transaction() as conn:
                conn.executemany(query, params_list)
                logger.info(f"일괄 수입 규칙 생성 완료: {len(entities)}개")
                
                # 생성된 규칙 조회
                created_rules = self.list(
                    {'order_by': 'id', 'order_direction': 'desc', 'limit': len(entities)}
                )
                
                return created_rules
        except Exception as e:
            logger.error(f"일괄 수입 규칙 생성 실패: {e}")
            raise RuntimeError(f"일괄 수입 규칙 생성 실패: {e}")
    
    def _map_to_entity(self, row: Dict[str, Any]) -> IncomeRule:
        """
        데이터베이스 행을 수입 규칙 엔티티로 변환합니다.
        
        Args:
            row: 데이터베이스 행
            
        Returns:
            IncomeRule: 변환된 수입 규칙 엔티티
        """
        return IncomeRule(
            id=row['id'],
            rule_name=row['rule_name'],
            rule_type=row['rule_type'],
            condition_type=row['condition_type'],
            condition_value=row['condition_value'],
            target_value=row['target_value'],
            priority=row['priority'],
            is_active=bool(row['is_active']),
            created_by=row['created_by'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )