# -*- coding: utf-8 -*-
"""
필터 저장소(FilterRepository) 클래스

분석 필터를 데이터베이스에 저장하고 관리하는 기능을 제공합니다.
"""

from typing import List, Optional, Dict, Any, Union
import json
from datetime import datetime

from src.models.analysis_filter import AnalysisFilter
from src.repositories.base_repository import BaseRepository


class FilterRepository(BaseRepository[AnalysisFilter]):
    """
    필터 저장소 클래스
    
    분석 필터를 데이터베이스에 저장하고 관리하는 기능을 제공합니다.
    """
    
    def __init__(self, db_connection=None):
        """
        필터 저장소 객체 초기화
        
        Args:
            db_connection: 데이터베이스 연결 객체 (선택)
        """
        self.db = db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self) -> None:
        """필터 테이블이 존재하는지 확인하고 없으면 생성"""
        query = """
        CREATE TABLE IF NOT EXISTS analysis_filters (
            id INTEGER PRIMARY KEY,
            filter_name TEXT NOT NULL,
            filter_config TEXT NOT NULL,
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute_query(query)
    
    def create(self, entity: AnalysisFilter) -> AnalysisFilter:
        """
        새 필터를 생성합니다.
        
        Args:
            entity: 생성할 필터 객체
            
        Returns:
            AnalysisFilter: 생성된 필터 객체 (ID가 할당됨)
        """
        if entity.id is not None:
            raise ValueError("새 필터 생성 시 ID가 None이어야 합니다")
        
        self.save(entity)
        return entity
    
    def read(self, id: int) -> Optional[AnalysisFilter]:
        """
        ID로 필터를 조회합니다.
        
        Args:
            id: 조회할 필터의 ID
            
        Returns:
            Optional[AnalysisFilter]: 조회된 필터 객체 또는 None
        """
        return self.get_by_id(id)
    
    def update(self, entity: AnalysisFilter) -> AnalysisFilter:
        """
        필터를 업데이트합니다.
        
        Args:
            entity: 업데이트할 필터 객체 (ID 필수)
            
        Returns:
            AnalysisFilter: 업데이트된 필터 객체
        """
        if entity.id is None:
            raise ValueError("업데이트할 필터의 ID가 필요합니다")
        
        self.save(entity)
        return entity
    
    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[AnalysisFilter]:
        """
        필터 조건에 맞는 필터 목록을 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
            
        Returns:
            List[AnalysisFilter]: 조회된 필터 목록
        """
        if filters is None:
            return self.get_all()
        
        # 필터 조건에 따른 쿼리 구성
        conditions = []
        params = []
        
        if 'filter_name' in filters:
            conditions.append("filter_name LIKE ?")
            params.append(f"%{filters['filter_name']}%")
        
        if 'is_default' in filters:
            conditions.append("is_default = ?")
            params.append(filters['is_default'])
        
        # 조건이 없으면 전체 조회
        if not conditions:
            return self.get_all()
        
        # 쿼리 실행
        query = f"SELECT * FROM analysis_filters WHERE {' AND '.join(conditions)} ORDER BY filter_name"
        results = self.db.execute_query(query, tuple(params)).fetchall()
        
        return [self._row_to_filter(row) for row in results]
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        필터 조건에 맞는 필터 수를 조회합니다.
        
        Args:
            filters: 필터 조건 (선택)
            
        Returns:
            int: 조회된 필터 수
        """
        if filters is None:
            query = "SELECT COUNT(*) FROM analysis_filters"
            result = self.db.execute_query(query).fetchone()
            return result[0] if result else 0
        
        # 필터 조건에 따른 쿼리 구성
        conditions = []
        params = []
        
        if 'filter_name' in filters:
            conditions.append("filter_name LIKE ?")
            params.append(f"%{filters['filter_name']}%")
        
        if 'is_default' in filters:
            conditions.append("is_default = ?")
            params.append(filters['is_default'])
        
        # 조건이 없으면 전체 개수 조회
        if not conditions:
            query = "SELECT COUNT(*) FROM analysis_filters"
            result = self.db.execute_query(query).fetchone()
            return result[0] if result else 0
        
        # 쿼리 실행
        query = f"SELECT COUNT(*) FROM analysis_filters WHERE {' AND '.join(conditions)}"
        result = self.db.execute_query(query, tuple(params)).fetchone()
        
        return result[0] if result else 0
    
    def exists(self, id: int) -> bool:
        """
        ID에 해당하는 필터가 존재하는지 확인합니다.
        
        Args:
            id: 확인할 필터의 ID
            
        Returns:
            bool: 존재 여부
        """
        query = "SELECT 1 FROM analysis_filters WHERE id = ? LIMIT 1"
        result = self.db.execute_query(query, (id,)).fetchone()
        
        return result is not None
    
    def save(self, filter_obj: AnalysisFilter) -> int:
        """
        필터를 데이터베이스에 저장
        
        Args:
            filter_obj: 저장할 필터 객체
            
        Returns:
            int: 저장된 필터의 ID
        """
        # 기본 필터로 설정된 경우 다른 기본 필터 해제
        if filter_obj.is_default:
            self._unset_other_defaults()
        
        # 필터 설정을 JSON 문자열로 변환
        filter_config_json = json.dumps(filter_obj.filter_config, ensure_ascii=False)
        
        if filter_obj.id is None:
            # 새 필터 삽입
            query = """
            INSERT INTO analysis_filters (filter_name, filter_config, is_default, created_at)
            VALUES (?, ?, ?, ?)
            """
            params = (
                filter_obj.filter_name,
                filter_config_json,
                filter_obj.is_default,
                filter_obj.created_at.isoformat()
            )
            cursor = self.db.execute_query(query, params)
            filter_obj.id = cursor.lastrowid
        else:
            # 기존 필터 업데이트
            query = """
            UPDATE analysis_filters
            SET filter_name = ?, filter_config = ?, is_default = ?
            WHERE id = ?
            """
            params = (
                filter_obj.filter_name,
                filter_config_json,
                filter_obj.is_default,
                filter_obj.id
            )
            self.db.execute_query(query, params)
        
        return filter_obj.id
    
    def _unset_other_defaults(self) -> None:
        """다른 모든 기본 필터 설정 해제"""
        query = """
        UPDATE analysis_filters
        SET is_default = FALSE
        WHERE is_default = TRUE
        """
        self.db.execute_query(query)
    
    def get_by_id(self, filter_id: int) -> Optional[AnalysisFilter]:
        """
        ID로 필터 조회
        
        Args:
            filter_id: 조회할 필터 ID
            
        Returns:
            Optional[AnalysisFilter]: 조회된 필터 객체 또는 None
        """
        query = "SELECT * FROM analysis_filters WHERE id = ?"
        result = self.db.execute_query(query, (filter_id,)).fetchone()
        
        if result:
            return self._row_to_filter(result)
        return None
    
    def get_by_name(self, filter_name: str) -> Optional[AnalysisFilter]:
        """
        이름으로 필터 조회
        
        Args:
            filter_name: 조회할 필터 이름
            
        Returns:
            Optional[AnalysisFilter]: 조회된 필터 객체 또는 None
        """
        query = "SELECT * FROM analysis_filters WHERE filter_name = ?"
        result = self.db.execute_query(query, (filter_name,)).fetchone()
        
        if result:
            return self._row_to_filter(result)
        return None
    
    def get_default(self) -> Optional[AnalysisFilter]:
        """
        기본 필터 조회
        
        Returns:
            Optional[AnalysisFilter]: 기본 필터 객체 또는 None
        """
        query = "SELECT * FROM analysis_filters WHERE is_default = TRUE LIMIT 1"
        result = self.db.execute_query(query).fetchone()
        
        if result:
            return self._row_to_filter(result)
        return None
    
    def get_all(self) -> List[AnalysisFilter]:
        """
        모든 필터 조회
        
        Returns:
            List[AnalysisFilter]: 필터 객체 목록
        """
        query = "SELECT * FROM analysis_filters ORDER BY filter_name"
        results = self.db.execute_query(query).fetchall()
        
        return [self._row_to_filter(row) for row in results]
    
    def delete(self, filter_id: int) -> bool:
        """
        필터 삭제
        
        Args:
            filter_id: 삭제할 필터 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        query = "DELETE FROM analysis_filters WHERE id = ?"
        cursor = self.db.execute_query(query, (filter_id,))
        
        return cursor.rowcount > 0
    
    def _row_to_filter(self, row: tuple) -> AnalysisFilter:
        """
        데이터베이스 행을 필터 객체로 변환
        
        Args:
            row: 데이터베이스 조회 결과 행
            
        Returns:
            AnalysisFilter: 변환된 필터 객체
        """
        # JSON 문자열을 딕셔너리로 파싱
        filter_config = json.loads(row[2])
        
        # 생성 시간 처리
        created_at = datetime.fromisoformat(row[4]) if row[4] else datetime.now()
        
        return AnalysisFilter(
            id=row[0],
            filter_name=row[1],
            filter_config=filter_config,
            is_default=bool(row[3]),
            created_at=created_at
        )