# -*- coding: utf-8 -*-
"""
거래(Transaction) Repository 클래스

거래 데이터의 CRUD 작업을 처리합니다.
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple

from src.models import Transaction
from src.repositories.base_repository import BaseRepository
from src.repositories.db_connection import DatabaseConnection

# 로거 설정
logger = logging.getLogger(__name__)


class TransactionRepository(BaseRepository[Transaction]):
    """
    거래 Repository 클래스
    
    거래 데이터의 CRUD 작업을 처리합니다.
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        거래 Repository 초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
        """
        self.db = db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """
        거래 테이블이 존재하는지 확인하고, 없으면 생성합니다.
        """
        # 테이블 생성 (SQLite는 한 번에 하나의 명령만 실행 가능)
        table_schema = """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            transaction_id TEXT UNIQUE,
            transaction_date DATE NOT NULL,
            description TEXT NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            transaction_type TEXT NOT NULL,
            category TEXT,
            payment_method TEXT,
            source TEXT NOT NULL,
            account_type TEXT,
            memo TEXT,
            is_excluded BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute(table_schema)
        
        # 인덱스 생성
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)")
    
    def create(self, entity: Transaction) -> Transaction:
        """
        새 거래를 생성합니다.
        
        Args:
            entity: 생성할 거래 객체
            
        Returns:
            Transaction: 생성된 거래 (ID가 할당됨)
            
        Raises:
            ValueError: 유효하지 않은 거래인 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 유효성 검사
        entity.validate()
        
        # 중복 거래 확인
        if self.exists_by_transaction_id(entity.transaction_id):
            raise ValueError(f"이미 존재하는 거래 ID입니다: {entity.transaction_id}")
        
        query = """
        INSERT INTO transactions (
            transaction_id, transaction_date, description, amount, transaction_type,
            category, payment_method, source, account_type, memo, is_excluded,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            entity.transaction_id,
            entity.transaction_date.isoformat(),
            entity.description,
            str(entity.amount),
            entity.transaction_type,
            entity.category,
            entity.payment_method,
            entity.source,
            entity.account_type,
            entity.memo,
            entity.is_excluded,
            entity.created_at.isoformat(),
            entity.updated_at.isoformat()
        )
        
        try:
            with self.db.transaction() as conn:
                conn.execute(query, params)
                entity.id = self.db.get_last_insert_id()
                logger.info(f"거래 생성 완료: ID={entity.id}, 거래ID={entity.transaction_id}")
                return entity
        except Exception as e:
            logger.error(f"거래 생성 실패: {e}")
            raise RuntimeError(f"거래 생성 실패: {e}")
    
    def read(self, id: int) -> Optional[Transaction]:
        """
        ID로 거래를 조회합니다.
        
        Args:
            id: 조회할 거래의 ID
            
        Returns:
            Optional[Transaction]: 조회된 거래 또는 None (없는 경우)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT * FROM transactions WHERE id = ?"
        
        try:
            result = self.db.fetch_one(query, (id,))
            if result:
                return self._map_to_entity(result)
            return None
        except Exception as e:
            logger.error(f"거래 조회 실패 (ID={id}): {e}")
            raise RuntimeError(f"거래 조회 실패: {e}")
    
    def read_by_transaction_id(self, transaction_id: str) -> Optional[Transaction]:
        """
        거래 ID로 거래를 조회합니다.
        
        Args:
            transaction_id: 조회할 거래의 거래 ID
            
        Returns:
            Optional[Transaction]: 조회된 거래 또는 None (없는 경우)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT * FROM transactions WHERE transaction_id = ?"
        
        try:
            result = self.db.fetch_one(query, (transaction_id,))
            if result:
                return self._map_to_entity(result)
            return None
        except Exception as e:
            logger.error(f"거래 조회 실패 (거래ID={transaction_id}): {e}")
            raise RuntimeError(f"거래 조회 실패: {e}")
    
    def update(self, entity: Transaction) -> Transaction:
        """
        거래를 업데이트합니다.
        
        Args:
            entity: 업데이트할 거래 객체 (ID 필수)
            
        Returns:
            Transaction: 업데이트된 거래
            
        Raises:
            ValueError: 유효하지 않은 거래이거나 ID가 없는 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        # 유효성 검사
        entity.validate()
        
        if entity.id is None:
            raise ValueError("업데이트할 거래의 ID가 없습니다")
        
        # 존재 여부 확인
        if not self.exists(entity.id):
            raise ValueError(f"존재하지 않는 거래입니다: ID={entity.id}")
        
        query = """
        UPDATE transactions SET
            transaction_id = ?,
            transaction_date = ?,
            description = ?,
            amount = ?,
            transaction_type = ?,
            category = ?,
            payment_method = ?,
            source = ?,
            account_type = ?,
            memo = ?,
            is_excluded = ?,
            updated_at = ?
        WHERE id = ?
        """
        
        # 업데이트 시간 갱신
        entity.updated_at = datetime.now()
        
        params = (
            entity.transaction_id,
            entity.transaction_date.isoformat(),
            entity.description,
            str(entity.amount),
            entity.transaction_type,
            entity.category,
            entity.payment_method,
            entity.source,
            entity.account_type,
            entity.memo,
            entity.is_excluded,
            entity.updated_at.isoformat(),
            entity.id
        )
        
        try:
            with self.db.transaction() as conn:
                conn.execute(query, params)
                logger.info(f"거래 업데이트 완료: ID={entity.id}, 거래ID={entity.transaction_id}")
                return entity
        except Exception as e:
            logger.error(f"거래 업데이트 실패 (ID={entity.id}): {e}")
            raise RuntimeError(f"거래 업데이트 실패: {e}")
    
    def delete(self, id: int) -> bool:
        """
        ID로 거래를 삭제합니다.
        
        Args:
            id: 삭제할 거래의 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "DELETE FROM transactions WHERE id = ?"
        
        try:
            with self.db.transaction() as conn:
                cursor = conn.execute(query, (id,))
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"거래 삭제 완료: ID={id}")
                else:
                    logger.warning(f"삭제할 거래를 찾을 수 없음: ID={id}")
                return success
        except Exception as e:
            logger.error(f"거래 삭제 실패 (ID={id}): {e}")
            raise RuntimeError(f"거래 삭제 실패: {e}")
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[Transaction]:
        """
        필터 조건에 맞는 거래 목록을 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
                - start_date: 시작 날짜
                - end_date: 종료 날짜
                - transaction_type: 거래 유형
                - category: 카테고리
                - payment_method: 결제 방식
                - min_amount: 최소 금액
                - max_amount: 최대 금액
                - source: 데이터 소스
                - description_contains: 설명에 포함된 텍스트
                - include_excluded: 분석 제외 항목 포함 여부 (기본값: False)
                - limit: 최대 결과 수
                - offset: 결과 오프셋
                - order_by: 정렬 기준 필드
                - order_direction: 정렬 방향 ('asc' 또는 'desc')
            
        Returns:
            List[Transaction]: 조회된 거래 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT * FROM transactions"
        where_clauses = []
        params = []
        
        # 필터 조건 적용
        if 'start_date' in filters:
            where_clauses.append("transaction_date >= ?")
            if isinstance(filters['start_date'], date):
                params.append(filters['start_date'].isoformat())
            else:
                params.append(filters['start_date'])
        
        if 'end_date' in filters:
            where_clauses.append("transaction_date <= ?")
            if isinstance(filters['end_date'], date):
                params.append(filters['end_date'].isoformat())
            else:
                params.append(filters['end_date'])
        
        if 'transaction_type' in filters:
            where_clauses.append("transaction_type = ?")
            params.append(filters['transaction_type'])
        
        if 'category' in filters:
            where_clauses.append("category = ?")
            params.append(filters['category'])
        
        if 'payment_method' in filters:
            where_clauses.append("payment_method = ?")
            params.append(filters['payment_method'])
        
        if 'min_amount' in filters:
            where_clauses.append("amount >= ?")
            params.append(str(filters['min_amount']))
        
        if 'max_amount' in filters:
            where_clauses.append("amount <= ?")
            params.append(str(filters['max_amount']))
        
        if 'source' in filters:
            where_clauses.append("source = ?")
            params.append(filters['source'])
        
        if 'description_contains' in filters:
            where_clauses.append("description LIKE ?")
            params.append(f"%{filters['description_contains']}%")
        
        # 기본적으로 분석 제외 항목은 제외
        include_excluded = filters.get('include_excluded', False)
        if not include_excluded:
            where_clauses.append("is_excluded = 0")
        
        # WHERE 절 구성
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # 정렬
        order_by = filters.get('order_by', 'transaction_date')
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
            logger.error(f"거래 목록 조회 실패: {e}")
            raise RuntimeError(f"거래 목록 조회 실패: {e}")
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        필터 조건에 맞는 거래 수를 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
            
        Returns:
            int: 조회된 거래 수
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT COUNT(*) as count FROM transactions"
        where_clauses = []
        params = []
        
        # 필터 조건 적용 (list 메서드와 동일한 로직)
        if 'start_date' in filters:
            where_clauses.append("transaction_date >= ?")
            if isinstance(filters['start_date'], date):
                params.append(filters['start_date'].isoformat())
            else:
                params.append(filters['start_date'])
        
        if 'end_date' in filters:
            where_clauses.append("transaction_date <= ?")
            if isinstance(filters['end_date'], date):
                params.append(filters['end_date'].isoformat())
            else:
                params.append(filters['end_date'])
        
        if 'transaction_type' in filters:
            where_clauses.append("transaction_type = ?")
            params.append(filters['transaction_type'])
        
        if 'category' in filters:
            where_clauses.append("category = ?")
            params.append(filters['category'])
        
        if 'payment_method' in filters:
            where_clauses.append("payment_method = ?")
            params.append(filters['payment_method'])
        
        if 'min_amount' in filters:
            where_clauses.append("amount >= ?")
            params.append(str(filters['min_amount']))
        
        if 'max_amount' in filters:
            where_clauses.append("amount <= ?")
            params.append(str(filters['max_amount']))
        
        if 'source' in filters:
            where_clauses.append("source = ?")
            params.append(filters['source'])
        
        if 'description_contains' in filters:
            where_clauses.append("description LIKE ?")
            params.append(f"%{filters['description_contains']}%")
        
        # 기본적으로 분석 제외 항목은 제외
        include_excluded = filters.get('include_excluded', False)
        if not include_excluded:
            where_clauses.append("is_excluded = 0")
        
        # WHERE 절 구성
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        try:
            result = self.db.fetch_one(query, tuple(params))
            return result['count'] if result else 0
        except Exception as e:
            logger.error(f"거래 수 조회 실패: {e}")
            raise RuntimeError(f"거래 수 조회 실패: {e}")
    
    def exists(self, id: int) -> bool:
        """
        ID에 해당하는 거래가 존재하는지 확인합니다.
        
        Args:
            id: 확인할 거래의 ID
            
        Returns:
            bool: 존재 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT 1 FROM transactions WHERE id = ? LIMIT 1"
        
        try:
            result = self.db.fetch_one(query, (id,))
            return result is not None
        except Exception as e:
            logger.error(f"거래 존재 여부 확인 실패 (ID={id}): {e}")
            raise RuntimeError(f"거래 존재 여부 확인 실패: {e}")
    
    def exists_by_transaction_id(self, transaction_id: str) -> bool:
        """
        거래 ID에 해당하는 거래가 존재하는지 확인합니다.
        
        Args:
            transaction_id: 확인할 거래의 거래 ID
            
        Returns:
            bool: 존재 여부
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = "SELECT 1 FROM transactions WHERE transaction_id = ? LIMIT 1"
        
        try:
            result = self.db.fetch_one(query, (transaction_id,))
            return result is not None
        except Exception as e:
            logger.error(f"거래 존재 여부 확인 실패 (거래ID={transaction_id}): {e}")
            raise RuntimeError(f"거래 존재 여부 확인 실패: {e}")
    
    def get_categories(self) -> List[str]:
        """
        모든 고유 카테고리 목록을 조회합니다.
        
        Returns:
            List[str]: 카테고리 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = """
        SELECT DISTINCT category FROM transactions 
        WHERE category IS NOT NULL AND category != ''
        ORDER BY category
        """
        
        try:
            results = self.db.fetch_all(query)
            return [row['category'] for row in results]
        except Exception as e:
            logger.error(f"카테고리 목록 조회 실패: {e}")
            raise RuntimeError(f"카테고리 목록 조회 실패: {e}")
    
    def get_payment_methods(self) -> List[str]:
        """
        모든 고유 결제 방식 목록을 조회합니다.
        
        Returns:
            List[str]: 결제 방식 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = """
        SELECT DISTINCT payment_method FROM transactions 
        WHERE payment_method IS NOT NULL AND payment_method != ''
        ORDER BY payment_method
        """
        
        try:
            results = self.db.fetch_all(query)
            return [row['payment_method'] for row in results]
        except Exception as e:
            logger.error(f"결제 방식 목록 조회 실패: {e}")
            raise RuntimeError(f"결제 방식 목록 조회 실패: {e}")
    
    def get_date_range(self) -> Tuple[Optional[date], Optional[date]]:
        """
        거래 데이터의 날짜 범위를 조회합니다.
        
        Returns:
            Tuple[Optional[date], Optional[date]]: (최소 날짜, 최대 날짜) 또는 (None, None)
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        query = """
        SELECT 
            MIN(transaction_date) as min_date,
            MAX(transaction_date) as max_date
        FROM transactions
        """
        
        try:
            result = self.db.fetch_one(query)
            if result and result['min_date'] and result['max_date']:
                min_date = date.fromisoformat(result['min_date'])
                max_date = date.fromisoformat(result['max_date'])
                return min_date, max_date
            return None, None
        except Exception as e:
            logger.error(f"날짜 범위 조회 실패: {e}")
            raise RuntimeError(f"날짜 범위 조회 실패: {e}")
    
    def bulk_create(self, entities: List[Transaction]) -> List[Transaction]:
        """
        여러 거래를 일괄 생성합니다.
        
        Args:
            entities: 생성할 거래 객체 목록
            
        Returns:
            List[Transaction]: 생성된 거래 목록
            
        Raises:
            ValueError: 유효하지 않은 거래가 있는 경우
            RuntimeError: 데이터베이스 오류 발생 시
        """
        if not entities:
            return []
        
        # 유효성 검사 및 중복 확인
        transaction_ids = []
        for entity in entities:
            entity.validate()
            transaction_ids.append(entity.transaction_id)
        
        # 중복 거래 확인
        duplicates = self._find_existing_transaction_ids(transaction_ids)
        if duplicates:
            raise ValueError(f"이미 존재하는 거래 ID가 있습니다: {', '.join(duplicates)}")
        
        query = """
        INSERT INTO transactions (
            transaction_id, transaction_date, description, amount, transaction_type,
            category, payment_method, source, account_type, memo, is_excluded,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params_list = []
        for entity in entities:
            params = (
                entity.transaction_id,
                entity.transaction_date.isoformat(),
                entity.description,
                str(entity.amount),
                entity.transaction_type,
                entity.category,
                entity.payment_method,
                entity.source,
                entity.account_type,
                entity.memo,
                entity.is_excluded,
                entity.created_at.isoformat(),
                entity.updated_at.isoformat()
            )
            params_list.append(params)
        
        try:
            with self.db.transaction() as conn:
                conn.executemany(query, params_list)
                logger.info(f"일괄 거래 생성 완료: {len(entities)}개")
                
                # ID 할당을 위해 생성된 거래 조회
                created_transactions = []
                for entity in entities:
                    created = self.read_by_transaction_id(entity.transaction_id)
                    if created:
                        created_transactions.append(created)
                
                return created_transactions
        except Exception as e:
            logger.error(f"일괄 거래 생성 실패: {e}")
            raise RuntimeError(f"일괄 거래 생성 실패: {e}")
    
    def _find_existing_transaction_ids(self, transaction_ids: List[str]) -> List[str]:
        """
        이미 존재하는 거래 ID 목록을 찾습니다.
        
        Args:
            transaction_ids: 확인할 거래 ID 목록
            
        Returns:
            List[str]: 이미 존재하는 거래 ID 목록
            
        Raises:
            RuntimeError: 데이터베이스 오류 발생 시
        """
        if not transaction_ids:
            return []
        
        placeholders = ', '.join(['?'] * len(transaction_ids))
        query = f"SELECT transaction_id FROM transactions WHERE transaction_id IN ({placeholders})"
        
        try:
            results = self.db.fetch_all(query, tuple(transaction_ids))
            return [row['transaction_id'] for row in results]
        except Exception as e:
            logger.error(f"기존 거래 ID 확인 실패: {e}")
            raise RuntimeError(f"기존 거래 ID 확인 실패: {e}")
    
    def _map_to_entity(self, row: Dict[str, Any]) -> Transaction:
        """
        데이터베이스 행을 거래 엔티티로 변환합니다.
        
        Args:
            row: 데이터베이스 행
            
        Returns:
            Transaction: 변환된 거래 엔티티
        """
        return Transaction(
            id=row['id'],
            transaction_id=row['transaction_id'],
            transaction_date=date.fromisoformat(row['transaction_date']),
            description=row['description'],
            amount=Decimal(row['amount']),
            transaction_type=row['transaction_type'],
            category=row['category'],
            payment_method=row['payment_method'],
            source=row['source'],
            account_type=row['account_type'],
            memo=row['memo'],
            is_excluded=bool(row['is_excluded']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )