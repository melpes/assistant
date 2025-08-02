# -*- coding: utf-8 -*-
"""
수입 패턴(IncomePattern) Repository 클래스

수입 패턴 데이터의 CRUD 작업을 처리합니다.
"""

import logging
import json
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional

from src.models.income_pattern import IncomePattern
from src.repositories.base_repository import BaseRepository
from src.repositories.db_connection import DatabaseConnection

# 로거 설정
logger = logging.getLogger(__name__)


class IncomePatternRepository(BaseRepository[IncomePattern]):
    """
    수입 패턴 Repository 클래스
    
    수입 패턴 데이터의 CRUD 작업을 처리합니다.
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        수입 패턴 Repository 초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
        """
        self.db = db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """
        수입 패턴 테이블이 존재하는지 확인하고, 없으면 생성합니다.
        """
        # 테이블 생성
        table_schema = """
        CREATE TABLE IF NOT EXISTS income_patterns (
            id INTEGER PRIMARY KEY,
            pattern_name TEXT NOT NULL,
            pattern_type TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            period_type TEXT NOT NULL,
            period_days INTEGER NOT NULL,
            average_amount DECIMAL(12,2) NOT NULL,
            amount_variance REAL NOT NULL,
            occurrence_count INTEGER NOT NULL,
            last_occurrence_date DATE NOT NULL,
            next_expected_date DATE NOT NULL,
            confidence_score REAL NOT NULL,
            transaction_ids TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute(table_schema)
        
        # 인덱스 생성
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_income_patterns_type ON income_patterns(pattern_type)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_income_patterns_category ON income_patterns(category)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_income_patterns_next_date ON income_patterns(next_expected_date)")
    
    def create(self, entity: IncomePattern) -> IncomePattern:
        """
        새 수입 패턴을 생성합니다.
        
        Args:
            entity: 생성할 수입 패턴 객체
            
        Returns:
            IncomePattern: 생성된 수입 패턴 (ID가 할당됨)
            
        Raises:
            ValueError: 유효하지 않은 수입 패턴인 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 유효성 검사
        entity.validate()
        
        query = """
        INSERT INTO income_patterns (
            pattern_name, pattern_type, description, category, period_type,
            period_days, average_amount, amount_variance, occurrence_count,
            last_occurrence_date, next_expected_date, confidence_score,
            transaction_ids, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # 거래 ID 목록을 JSON 문자열로 변환
        transaction_ids_json = json.dumps(entity.transaction_ids)
        
        params = (
            entity.pattern_name,
            entity.pattern_type,
            entity.description,
            entity.category,
            entity.period_type,
            entity.period_days,
            str(entity.average_amount),
            entity.amount_variance,
            entity.occurrence_count,
            entity.last_occurrence_date.isoformat(),
            entity.next_expected_date.isoformat(),
            entity.confidence_score,
            transaction_ids_json,
            entity.is_active,
            entity.created_at.isoformat(),
            entity.updated_at.isoformat()
        )
        
        try:
            with self.db.transaction() as conn:
                conn.execute(query, params)
                entity.id = self.db.get_last_insert_id()
                logger.info(f"수입 패턴 생성 완료: ID={entity.id}, 이름={entity.pattern_name}")
                return entity
        except Exception as e:
            logger.error(f"수입 패턴 생성 실패: {e}")
            raise RuntimeError(f"수입 패턴 생성 실패: {e}")
    
    def read(self, id: int) -> Optional[IncomePattern]:
        """
        ID로 수입 패턴을 조회합니다.
        
        Args:
            id: 조회할 수입 패턴의 ID
            
        Returns:
            Optional[IncomePattern]: 조회된 수입 패턴 또는 None (없는 경우)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT * FROM income_patterns WHERE id = ?"
        
        try:
            result = self.db.fetch_one(query, (id,))
            if result:
                return self._map_to_entity(result)
            return None
        except Exception as e:
            logger.error(f"수입 패턴 조회 실패 (ID={id}): {e}")
            raise RuntimeError(f"수입 패턴 조회 실패: {e}")
    
    def update(self, entity: IncomePattern) -> IncomePattern:
        """
        수입 패턴을 업데이트합니다.
        
        Args:
            entity: 업데이트할 수입 패턴 객체 (ID 필수)
            
        Returns:
            IncomePattern: 업데이트된 수입 패턴
            
        Raises:
            ValueError: 유효하지 않은 수입 패턴이거나 ID가 없는 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 유효성 검사
        entity.validate()
        
        if entity.id is None:
            raise ValueError("업데이트할 수입 패턴의 ID가 없습니다")
        
        # 존재 여부 확인
        if not self.exists(entity.id):
            raise ValueError(f"존재하지 않는 수입 패턴입니다: ID={entity.id}")
        
        query = """
        UPDATE income_patterns SET
            pattern_name = ?,
            pattern_type = ?,
            description = ?,
            category = ?,
            period_type = ?,
            period_days = ?,
            average_amount = ?,
            amount_variance = ?,
            occurrence_count = ?,
            last_occurrence_date = ?,
            next_expected_date = ?,
            confidence_score = ?,
            transaction_ids = ?,
            is_active = ?,
            updated_at = ?
        WHERE id = ?
        """
        
        # 업데이트 시간 갱신
        entity.updated_at = datetime.now()
        
        # 거래 ID 목록을 JSON 문자열로 변환
        transaction_ids_json = json.dumps(entity.transaction_ids)
        
        params = (
            entity.pattern_name,
            entity.pattern_type,
            entity.description,
            entity.category,
            entity.period_type,
            entity.period_days,
            str(entity.average_amount),
            entity.amount_variance,
            entity.occurrence_count,
            entity.last_occurrence_date.isoformat(),
            entity.next_expected_date.isoformat(),
            entity.confidence_score,
            transaction_ids_json,
            entity.is_active,
            entity.updated_at.isoformat(),
            entity.id
        )
        
        try:
            with self.db.transaction() as conn:
                conn.execute(query, params)
                logger.info(f"수입 패턴 업데이트 완료: ID={entity.id}, 이름={entity.pattern_name}")
                return entity
        except Exception as e:
            logger.error(f"수입 패턴 업데이트 실패 (ID={entity.id}): {e}")
            raise RuntimeError(f"수입 패턴 업데이트 실패: {e}")
    
    def delete(self, id: int) -> bool:
        """
        ID로 수입 패턴을 삭제합니다.
        
        Args:
            id: 삭제할 수입 패턴의 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "DELETE FROM income_patterns WHERE id = ?"
        
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(query, (id,))
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"수입 패턴 삭제 완료: ID={id}")
                else:
                    logger.warning(f"삭제할 수입 패턴을 찾을 수 없음: ID={id}")
                return success
        except Exception as e:
            logger.error(f"수입 패턴 삭제 실패 (ID={id}): {e}")
            raise RuntimeError(f"수입 패턴 삭제 실패: {e}")
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[IncomePattern]:
        """
        필터 조건에 맞는 수입 패턴 목록을 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
                - pattern_type: 패턴 유형
                - category: 카테고리
                - period_type: 주기 유형
                - min_confidence: 최소 신뢰도
                - is_active: 활성화 여부
                - upcoming_days: 향후 n일 이내 예상 패턴
                - search: 이름 검색어
                - limit: 최대 결과 수
                - offset: 결과 오프셋
                - order_by: 정렬 기준 필드
                - order_direction: 정렬 방향 ('asc' 또는 'desc')
            
        Returns:
            List[IncomePattern]: 조회된 수입 패턴 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT * FROM income_patterns"
        where_clauses = []
        params = []
        
        # 필터 조건 적용
        if 'pattern_type' in filters:
            where_clauses.append("pattern_type = ?")
            params.append(filters['pattern_type'])
        
        if 'category' in filters:
            where_clauses.append("category = ?")
            params.append(filters['category'])
        
        if 'period_type' in filters:
            where_clauses.append("period_type = ?")
            params.append(filters['period_type'])
        
        if 'min_confidence' in filters:
            where_clauses.append("confidence_score >= ?")
            params.append(float(filters['min_confidence']))
        
        if 'is_active' in filters:
            where_clauses.append("is_active = ?")
            params.append(1 if filters['is_active'] else 0)
        
        if 'upcoming_days' in filters:
            today = date.today()
            target_date = today + datetime.timedelta(days=int(filters['upcoming_days']))
            where_clauses.append("next_expected_date BETWEEN ? AND ?")
            params.append(today.isoformat())
            params.append(target_date.isoformat())
        
        if 'search' in filters and filters['search']:
            where_clauses.append("pattern_name LIKE ? OR description LIKE ?")
            search_param = f"%{filters['search']}%"
            params.append(search_param)
            params.append(search_param)
        
        # WHERE 절 구성
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # 정렬
        order_by = filters.get('order_by', 'next_expected_date')
        order_direction = filters.get('order_direction', 'asc')
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
            logger.error(f"수입 패턴 목록 조회 실패: {e}")
            raise RuntimeError(f"수입 패턴 목록 조회 실패: {e}")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        필터 조건에 맞는 수입 패턴 수를 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
            
        Returns:
            int: 조회된 수입 패턴 수
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT COUNT(*) as count FROM income_patterns"
        where_clauses = []
        params = []
        
        # 필터 조건 적용 (list 메서드와 동일한 로직)
        if 'pattern_type' in filters:
            where_clauses.append("pattern_type = ?")
            params.append(filters['pattern_type'])
        
        if 'category' in filters:
            where_clauses.append("category = ?")
            params.append(filters['category'])
        
        if 'period_type' in filters:
            where_clauses.append("period_type = ?")
            params.append(filters['period_type'])
        
        if 'min_confidence' in filters:
            where_clauses.append("confidence_score >= ?")
            params.append(float(filters['min_confidence']))
        
        if 'is_active' in filters:
            where_clauses.append("is_active = ?")
            params.append(1 if filters['is_active'] else 0)
        
        if 'upcoming_days' in filters:
            today = date.today()
            target_date = today + datetime.timedelta(days=int(filters['upcoming_days']))
            where_clauses.append("next_expected_date BETWEEN ? AND ?")
            params.append(today.isoformat())
            params.append(target_date.isoformat())
        
        if 'search' in filters and filters['search']:
            where_clauses.append("pattern_name LIKE ? OR description LIKE ?")
            search_param = f"%{filters['search']}%"
            params.append(search_param)
            params.append(search_param)
        
        # WHERE 절 구성
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        try:
            result = self.db.fetch_one(query, tuple(params))
            return result['count'] if result else 0
        except Exception as e:
            logger.error(f"수입 패턴 수 조회 실패: {e}")
            raise RuntimeError(f"수입 패턴 수 조회 실패: {e}")
    
    def exists(self, id: int) -> bool:
        """
        ID에 해당하는 수입 패턴이 존재하는지 확인합니다.
        
        Args:
            id: 확인할 수입 패턴의 ID
            
        Returns:
            bool: 존재 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT 1 FROM income_patterns WHERE id = ? LIMIT 1"
        
        try:
            result = self.db.fetch_one(query, (id,))
            return result is not None
        except Exception as e:
            logger.error(f"수입 패턴 존재 여부 확인 실패 (ID={id}): {e}")
            raise RuntimeError(f"수입 패턴 존재 여부 확인 실패: {e}")
    
    def get_upcoming_patterns(self, days: int = 7) -> List[IncomePattern]:
        """
        향후 n일 이내에 예상되는 수입 패턴 목록을 조회합니다.
        
        Args:
            days: 향후 일수 (기본값: 7)
            
        Returns:
            List[IncomePattern]: 예상 수입 패턴 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        today = date.today()
        target_date = today + datetime.timedelta(days=days)
        
        query = """
        SELECT * FROM income_patterns 
        WHERE is_active = 1 
        AND next_expected_date BETWEEN ? AND ? 
        ORDER BY next_expected_date ASC, confidence_score DESC
        """
        
        try:
            results = self.db.fetch_all(query, (today.isoformat(), target_date.isoformat()))
            return [self._map_to_entity(row) for row in results]
        except Exception as e:
            logger.error(f"예상 수입 패턴 조회 실패: {e}")
            raise RuntimeError(f"예상 수입 패턴 조회 실패: {e}")
    
    def find_matching_pattern(self, transaction: Dict[str, Any], tolerance_days: int = 3) -> Optional[IncomePattern]:
        """
        거래와 일치하는 수입 패턴을 찾습니다.
        
        Args:
            transaction: 확인할 거래 데이터
            tolerance_days: 날짜 허용 오차 (일)
            
        Returns:
            Optional[IncomePattern]: 일치하는 패턴 또는 None
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 카테고리 확인
        category = transaction.get('category')
        if not category:
            return None
        
        # 활성화된 패턴 목록 조회
        patterns = self.list({'category': category, 'is_active': True})
        
        # 각 패턴에 대해 일치 여부 확인
        for pattern in patterns:
            if pattern.is_match(transaction, tolerance_days):
                return pattern
        
        return None
    
    def _map_to_entity(self, row: Dict[str, Any]) -> IncomePattern:
        """
        데이터베이스 행을 수입 패턴 엔티티로 변환합니다.
        
        Args:
            row: 데이터베이스 행
            
        Returns:
            IncomePattern: 변환된 수입 패턴 엔티티
        """
        # 거래 ID 목록을 JSON에서 파싱
        transaction_ids = json.loads(row['transaction_ids'])
        
        return IncomePattern(
            id=row['id'],
            pattern_name=row['pattern_name'],
            pattern_type=row['pattern_type'],
            description=row['description'],
            category=row['category'],
            period_type=row['period_type'],
            period_days=row['period_days'],
            average_amount=Decimal(row['average_amount']),
            amount_variance=row['amount_variance'],
            occurrence_count=row['occurrence_count'],
            last_occurrence_date=date.fromisoformat(row['last_occurrence_date']),
            next_expected_date=date.fromisoformat(row['next_expected_date']),
            confidence_score=row['confidence_score'],
            transaction_ids=transaction_ids,
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )