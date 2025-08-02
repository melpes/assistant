# -*- coding: utf-8 -*-
"""
데이터베이스 연결 관리 모듈

SQLite 데이터베이스 연결을 관리하고 트랜잭션 처리를 지원합니다.
"""

import sqlite3
import logging
from typing import Optional, Any, List, Dict, Tuple
from contextlib import contextmanager
import os

# 로거 설정
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    데이터베이스 연결 관리 클래스
    
    SQLite 데이터베이스 연결을 관리하고 트랜잭션 처리를 지원합니다.
    """
    
    def __init__(self, db_path: str):
        """
        데이터베이스 연결 객체 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self._connection = None
        
        # 데이터베이스 파일 존재 여부 확인
        if not os.path.exists(db_path):
            logger.warning(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
    
    def connect(self) -> sqlite3.Connection:
        """
        데이터베이스에 연결
        
        Returns:
            sqlite3.Connection: 데이터베이스 연결 객체
            
        Raises:
            RuntimeError: 데이터베이스 연결 실패 시
        """
        try:
            if self._connection is None:
                self._connection = sqlite3.connect(self.db_path)
                # Row 객체를 딕셔너리처럼 접근할 수 있도록 설정
                self._connection.row_factory = sqlite3.Row
                # 외래 키 제약 조건 활성화
                self._connection.execute("PRAGMA foreign_keys = ON")
            return self._connection
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            raise RuntimeError(f"데이터베이스 연결 실패: {e}")
    
    def close(self) -> None:
        """
        데이터베이스 연결 종료
        """
        if self._connection:
            self._connection.close()
            self._connection = None
    
    @contextmanager
    def transaction(self):
        """
        트랜잭션 컨텍스트 매니저
        
        트랜잭션 내에서 예외가 발생하면 롤백하고, 정상 종료 시 커밋합니다.
        
        Yields:
            sqlite3.Connection: 데이터베이스 연결 객체
            
        Raises:
            Exception: 트랜잭션 내에서 발생한 예외
        """
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception as e:
            connection.rollback()
            logger.error(f"트랜잭션 실패, 롤백 수행: {e}")
            raise
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        SQL 쿼리 실행
        
        Args:
            query: SQL 쿼리 문자열
            params: 쿼리 파라미터 (선택)
            
        Returns:
            sqlite3.Cursor: 쿼리 결과 커서
            
        Raises:
            RuntimeError: 쿼리 실행 실패 시
        """
        try:
            connection = self.connect()
            return connection.execute(query, params)
        except sqlite3.Error as e:
            logger.error(f"쿼리 실행 실패: {e}, 쿼리: {query}, 파라미터: {params}")
            raise RuntimeError(f"쿼리 실행 실패: {e}")
    
    def execute_many(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """
        여러 파라미터로 SQL 쿼리 실행
        
        Args:
            query: SQL 쿼리 문자열
            params_list: 쿼리 파라미터 목록
            
        Returns:
            sqlite3.Cursor: 쿼리 결과 커서
            
        Raises:
            RuntimeError: 쿼리 실행 실패 시
        """
        try:
            connection = self.connect()
            return connection.executemany(query, params_list)
        except sqlite3.Error as e:
            logger.error(f"대량 쿼리 실행 실패: {e}, 쿼리: {query}")
            raise RuntimeError(f"대량 쿼리 실행 실패: {e}")
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        단일 레코드 조회
        
        Args:
            query: SQL 쿼리 문자열
            params: 쿼리 파라미터 (선택)
            
        Returns:
            Optional[Dict[str, Any]]: 조회된 레코드 또는 None
            
        Raises:
            RuntimeError: 쿼리 실행 실패 시
        """
        try:
            cursor = self.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"단일 레코드 조회 실패: {e}, 쿼리: {query}, 파라미터: {params}")
            raise RuntimeError(f"단일 레코드 조회 실패: {e}")
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        여러 레코드 조회
        
        Args:
            query: SQL 쿼리 문자열
            params: 쿼리 파라미터 (선택)
            
        Returns:
            List[Dict[str, Any]]: 조회된 레코드 목록
            
        Raises:
            RuntimeError: 쿼리 실행 실패 시
        """
        try:
            cursor = self.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"다중 레코드 조회 실패: {e}, 쿼리: {query}, 파라미터: {params}")
            raise RuntimeError(f"다중 레코드 조회 실패: {e}")
    
    def get_last_insert_id(self) -> int:
        """
        마지막으로 삽입된 행의 ID 조회
        
        Returns:
            int: 마지막으로 삽입된 행의 ID
        """
        return self.fetch_one("SELECT last_insert_rowid() as id")["id"]
    
    def table_exists(self, table_name: str) -> bool:
        """
        테이블 존재 여부 확인
        
        Args:
            table_name: 테이블 이름
            
        Returns:
            bool: 테이블 존재 여부
        """
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        result = self.fetch_one(query, (table_name,))
        return result is not None
    
    def create_table_if_not_exists(self, table_name: str, schema: str) -> None:
        """
        테이블이 없으면 생성
        
        Args:
            table_name: 테이블 이름
            schema: 테이블 스키마 SQL
            
        Raises:
            RuntimeError: 테이블 생성 실패 시
            
        Note:
            이 메서드는 단일 SQL 문만 실행할 수 있습니다.
            여러 문장(CREATE TABLE + CREATE INDEX)을 실행하려면 각각 execute()를 호출하세요.
        """
        if not self.table_exists(table_name):
            try:
                self.execute(schema)
                logger.info(f"테이블 생성 완료: {table_name}")
            except sqlite3.Error as e:
                logger.error(f"테이블 생성 실패: {e}, 테이블: {table_name}")
                raise RuntimeError(f"테이블 생성 실패: {e}")