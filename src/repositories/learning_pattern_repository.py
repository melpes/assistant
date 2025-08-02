# -*- coding: utf-8 -*-
"""
학습 패턴 저장소(LearningPatternRepository) 클래스

학습 패턴을 데이터베이스에 저장하고 관리하는 저장소입니다.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from src.models.learning_pattern import LearningPattern
from src.repositories.base_repository import BaseRepository

# 로거 설정
logger = logging.getLogger(__name__)


class LearningPatternRepository(BaseRepository):
    """
    학습 패턴 저장소 클래스
    
    학습 패턴을 데이터베이스에 저장하고 관리합니다.
    """
    
    def __init__(self, db_connection):
        """
        학습 패턴 저장소 초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체
        """
        super().__init__(db_connection)
        self._ensure_table()
    
    def _ensure_table(self) -> None:
        """
        테이블이 존재하는지 확인하고, 없으면 생성합니다.
        """
        query = """
        CREATE TABLE IF NOT EXISTS learning_patterns (
            id INTEGER PRIMARY KEY,
            pattern_type TEXT NOT NULL,
            pattern_name TEXT NOT NULL,
            pattern_key TEXT NOT NULL,
            pattern_value TEXT NOT NULL,
            confidence TEXT NOT NULL,
            occurrence_count INTEGER DEFAULT 1,
            last_seen TIMESTAMP NOT NULL,
            status TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db_connection.execute(query)
        
        # 인덱스 생성
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_learning_patterns_type ON learning_patterns(pattern_type)",
            "CREATE INDEX IF NOT EXISTS idx_learning_patterns_key ON learning_patterns(pattern_key)",
            "CREATE INDEX IF NOT EXISTS idx_learning_patterns_status ON learning_patterns(status)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_learning_patterns_unique ON learning_patterns(pattern_type, pattern_key, pattern_value)"
        ]
        
        for index_query in indexes:
            self.db_connection.execute(index_query)
        
        logger.debug("학습 패턴 테이블 및 인덱스 확인 완료")
    
    def create(self, pattern: LearningPattern) -> LearningPattern:
        """
        새 학습 패턴을 생성합니다.
        
        Args:
            pattern: 생성할 학습 패턴 객체
            
        Returns:
            LearningPattern: 생성된 학습 패턴 (ID 할당됨)
            
        Raises:
            ValueError: 필수 필드가 없는 경우
        """
        # 필수 필드 검증
        if not pattern.pattern_type or not pattern.pattern_key or not pattern.pattern_value:
            raise ValueError("패턴 유형, 키, 값은 필수 필드입니다")
        
        # 중복 확인 및 업데이트
        existing = self.find_by_key_value(
            pattern.pattern_type, pattern.pattern_key, pattern.pattern_value
        )
        
        if existing:
            # 기존 패턴 업데이트
            existing.increment_occurrence()
            return self.update(existing)
        
        # 메타데이터 직렬화
        metadata_json = json.dumps(pattern.metadata) if pattern.metadata else None
        
        query = """
        INSERT INTO learning_patterns (
            pattern_type, pattern_name, pattern_key, pattern_value, 
            confidence, occurrence_count, last_seen, status, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            pattern.pattern_type,
            pattern.pattern_name,
            pattern.pattern_key,
            pattern.pattern_value,
            pattern.confidence,
            pattern.occurrence_count,
            pattern.last_seen.isoformat(),
            pattern.status,
            metadata_json
        )
        
        cursor = self.db_connection.execute(query, params)
        pattern.id = cursor.lastrowid
        
        logger.info(f"학습 패턴 생성됨: {pattern.pattern_name} (ID={pattern.id})")
        return pattern
    
    def read(self, pattern_id: int) -> Optional[LearningPattern]:
        """
        ID로 학습 패턴을 조회합니다.
        
        Args:
            pattern_id: 학습 패턴 ID
            
        Returns:
            Optional[LearningPattern]: 조회된 학습 패턴 또는 None
        """
        query = "SELECT * FROM learning_patterns WHERE id = ?"
        row = self.db_connection.fetch_one(query, (pattern_id,))
        
        if not row:
            return None
        
        return self._row_to_pattern(row)
    
    def update(self, pattern: LearningPattern) -> LearningPattern:
        """
        학습 패턴을 업데이트합니다.
        
        Args:
            pattern: 업데이트할 학습 패턴 객체
            
        Returns:
            LearningPattern: 업데이트된 학습 패턴
            
        Raises:
            ValueError: ID가 없는 경우
        """
        if pattern.id is None:
            raise ValueError("업데이트할 패턴의 ID가 없습니다")
        
        # 메타데이터 직렬화
        metadata_json = json.dumps(pattern.metadata) if pattern.metadata else None
        
        query = """
        UPDATE learning_patterns SET
            pattern_type = ?,
            pattern_name = ?,
            pattern_key = ?,
            pattern_value = ?,
            confidence = ?,
            occurrence_count = ?,
            last_seen = ?,
            status = ?,
            metadata = ?
        WHERE id = ?
        """
        
        params = (
            pattern.pattern_type,
            pattern.pattern_name,
            pattern.pattern_key,
            pattern.pattern_value,
            pattern.confidence,
            pattern.occurrence_count,
            pattern.last_seen.isoformat(),
            pattern.status,
            metadata_json,
            pattern.id
        )
        
        self.db_connection.execute(query, params)
        
        logger.debug(f"학습 패턴 업데이트됨: ID={pattern.id}")
        return pattern
    
    def delete(self, pattern_id: int) -> bool:
        """
        학습 패턴을 삭제합니다.
        
        Args:
            pattern_id: 삭제할 학습 패턴의 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        query = "DELETE FROM learning_patterns WHERE id = ?"
        result = self.db_connection.execute(query, (pattern_id,))
        
        success = result.rowcount > 0
        if success:
            logger.info(f"학습 패턴 삭제됨: ID={pattern_id}")
        
        return success
    
    def list(self, filters: Dict[str, Any] = None) -> List[LearningPattern]:
        """
        필터 조건에 맞는 학습 패턴 목록을 반환합니다.
        
        Args:
            filters: 필터 조건
                - pattern_type: 패턴 유형
                - status: 패턴 상태
                - confidence: 패턴 신뢰도
                - min_occurrence: 최소 발생 횟수
                - limit: 최대 결과 수
                - offset: 결과 오프셋
                
        Returns:
            List[LearningPattern]: 학습 패턴 목록
        """
        filters = filters or {}
        
        # 기본 쿼리
        query = "SELECT * FROM learning_patterns"
        conditions = []
        params = []
        
        # 필터 조건 추가
        if 'pattern_type' in filters:
            conditions.append("pattern_type = ?")
            params.append(filters['pattern_type'])
        
        if 'status' in filters:
            conditions.append("status = ?")
            params.append(filters['status'])
        
        if 'confidence' in filters:
            conditions.append("confidence = ?")
            params.append(filters['confidence'])
        
        if 'min_occurrence' in filters:
            conditions.append("occurrence_count >= ?")
            params.append(filters['min_occurrence'])
        
        if 'pattern_key_contains' in filters:
            conditions.append("pattern_key LIKE ?")
            params.append(f"%{filters['pattern_key_contains']}%")
        
        # WHERE 절 추가
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # 정렬
        query += " ORDER BY occurrence_count DESC, last_seen DESC"
        
        # 페이지네이션
        if 'limit' in filters:
            query += " LIMIT ?"
            params.append(filters['limit'])
            
            if 'offset' in filters:
                query += " OFFSET ?"
                params.append(filters['offset'])
        
        # 쿼리 실행
        rows = self.db_connection.fetch_all(query, tuple(params))
        
        # 결과 변환
        patterns = [self._row_to_pattern(row) for row in rows]
        
        logger.debug(f"학습 패턴 목록 조회: {len(patterns)}개 결과")
        return patterns
    
    def find_by_key_value(
        self, pattern_type: str, pattern_key: str, pattern_value: str
    ) -> Optional[LearningPattern]:
        """
        패턴 유형, 키, 값으로 학습 패턴을 찾습니다.
        
        Args:
            pattern_type: 패턴 유형
            pattern_key: 패턴 키
            pattern_value: 패턴 값
            
        Returns:
            Optional[LearningPattern]: 찾은 학습 패턴 또는 None
        """
        query = """
        SELECT * FROM learning_patterns 
        WHERE pattern_type = ? AND pattern_key = ? AND pattern_value = ?
        """
        
        row = self.db_connection.fetch_one(query, (pattern_type, pattern_key, pattern_value))
        
        if not row:
            return None
        
        return self._row_to_pattern(row)
    
    def find_similar_patterns(
        self, pattern_type: str, pattern_key: str, min_confidence: str = None
    ) -> List[LearningPattern]:
        """
        유사한 패턴을 찾습니다.
        
        Args:
            pattern_type: 패턴 유형
            pattern_key: 패턴 키
            min_confidence: 최소 신뢰도
            
        Returns:
            List[LearningPattern]: 유사한 패턴 목록
        """
        query = """
        SELECT * FROM learning_patterns 
        WHERE pattern_type = ? AND pattern_key LIKE ?
        """
        params = [pattern_type, f"%{pattern_key}%"]
        
        if min_confidence:
            confidence_levels = {
                LearningPattern.CONFIDENCE_LOW: 1,
                LearningPattern.CONFIDENCE_MEDIUM: 2,
                LearningPattern.CONFIDENCE_HIGH: 3
            }
            
            min_level = confidence_levels.get(min_confidence, 1)
            
            # 신뢰도 필터링
            confidence_conditions = []
            confidence_params = []
            
            for conf, level in confidence_levels.items():
                if level >= min_level:
                    confidence_conditions.append("confidence = ?")
                    confidence_params.append(conf)
            
            if confidence_conditions:
                query += " AND (" + " OR ".join(confidence_conditions) + ")"
                params.extend(confidence_params)
        
        # 상태가 적용됨 또는 대기 중인 패턴만 조회
        query += " AND status IN (?, ?)"
        params.extend([LearningPattern.STATUS_APPLIED, LearningPattern.STATUS_PENDING])
        
        # 발생 횟수 및 최근 발견 시간 순으로 정렬
        query += " ORDER BY occurrence_count DESC, last_seen DESC"
        
        # 쿼리 실행
        rows = self.db_connection.fetch_all(query, tuple(params))
        
        # 결과 변환
        patterns = [self._row_to_pattern(row) for row in rows]
        
        logger.debug(f"유사 패턴 조회: {len(patterns)}개 결과")
        return patterns
    
    def get_pattern_stats(self, pattern_type: str = None) -> Dict[str, Any]:
        """
        패턴 통계를 반환합니다.
        
        Args:
            pattern_type: 패턴 유형 (선택)
            
        Returns:
            Dict[str, Any]: 패턴 통계 정보
        """
        # 기본 쿼리
        base_query = "SELECT COUNT(*) as count FROM learning_patterns"
        params = []
        
        # 패턴 유형 필터
        if pattern_type:
            base_query += " WHERE pattern_type = ?"
            params.append(pattern_type)
        
        # 전체 패턴 수
        total_count = self.db_connection.fetch_one(base_query, tuple(params))['count']
        
        # 상태별 패턴 수
        status_query = base_query + (" AND" if pattern_type else " WHERE") + " status = ?"
        
        pending_count = self.db_connection.fetch_one(
            status_query, tuple(params + [LearningPattern.STATUS_PENDING])
        )['count']
        
        applied_count = self.db_connection.fetch_one(
            status_query, tuple(params + [LearningPattern.STATUS_APPLIED])
        )['count']
        
        rejected_count = self.db_connection.fetch_one(
            status_query, tuple(params + [LearningPattern.STATUS_REJECTED])
        )['count']
        
        # 신뢰도별 패턴 수
        confidence_query = base_query + (" AND" if pattern_type else " WHERE") + " confidence = ?"
        
        low_count = self.db_connection.fetch_one(
            confidence_query, tuple(params + [LearningPattern.CONFIDENCE_LOW])
        )['count']
        
        medium_count = self.db_connection.fetch_one(
            confidence_query, tuple(params + [LearningPattern.CONFIDENCE_MEDIUM])
        )['count']
        
        high_count = self.db_connection.fetch_one(
            confidence_query, tuple(params + [LearningPattern.CONFIDENCE_HIGH])
        )['count']
        
        # 최근 패턴
        recent_query = base_query + " ORDER BY last_seen DESC LIMIT 5"
        recent_rows = self.db_connection.fetch_all(recent_query, tuple(params))
        recent_patterns = [self._row_to_pattern(row) for row in recent_rows]
        
        return {
            'total_count': total_count,
            'status_counts': {
                'pending': pending_count,
                'applied': applied_count,
                'rejected': rejected_count
            },
            'confidence_counts': {
                'low': low_count,
                'medium': medium_count,
                'high': high_count
            },
            'recent_patterns': recent_patterns
        }
    
    def update_status(self, pattern_id: int, status: str) -> bool:
        """
        패턴 상태를 업데이트합니다.
        
        Args:
            pattern_id: 패턴 ID
            status: 새 상태
            
        Returns:
            bool: 업데이트 성공 여부
        """
        query = "UPDATE learning_patterns SET status = ? WHERE id = ?"
        result = self.db_connection.execute(query, (status, pattern_id))
        
        success = result.rowcount > 0
        if success:
            logger.debug(f"패턴 상태 업데이트됨: ID={pattern_id}, 상태={status}")
        
        return success
    
    def _row_to_pattern(self, row: Dict[str, Any]) -> LearningPattern:
        """
        데이터베이스 행을 학습 패턴 객체로 변환합니다.
        
        Args:
            row: 데이터베이스 행
            
        Returns:
            LearningPattern: 변환된 학습 패턴 객체
        """
        # 메타데이터 역직렬화
        metadata = json.loads(row['metadata']) if row['metadata'] else {}
        
        # 날짜 변환
        last_seen = datetime.fromisoformat(row['last_seen']) if row['last_seen'] else datetime.now()
        
        return LearningPattern(
            id=row['id'],
            pattern_type=row['pattern_type'],
            pattern_name=row['pattern_name'],
            pattern_key=row['pattern_key'],
            pattern_value=row['pattern_value'],
            confidence=row['confidence'],
            occurrence_count=row['occurrence_count'],
            last_seen=last_seen,
            status=row['status'],
            metadata=metadata
        )