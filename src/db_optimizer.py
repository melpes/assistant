# -*- coding: utf-8 -*-
"""
데이터베이스 최적화 도구

SQLite 데이터베이스의 성능을 최적화하는 도구입니다.
인덱스 관리, 쿼리 최적화, 스키마 분석 등의 기능을 제공합니다.
"""

import os
import sys
import sqlite3
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.logging_system import get_logger
from src.config_manager import ConfigManager
from src.performance_monitor import profile_function, measure_time

# 로거 설정
logger = get_logger('db_optimizer')

class DatabaseOptimizer:
    """
    데이터베이스 최적화 클래스
    
    SQLite 데이터베이스의 성능을 최적화합니다.
    """
    
    def __init__(self, db_path: str = None, config_manager: ConfigManager = None):
        """
        데이터베이스 최적화 도구 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
            config_manager: 설정 관리자
        """
        self.config_manager = config_manager or ConfigManager()
        self.db_path = db_path or self.config_manager.get_config_value('system.database.path')
        
        # 최적화 결과 저장 경로
        self.output_dir = os.path.join(parent_dir, 'profiles')
        os.makedirs(self.output_dir, exist_ok=True)
    
    @profile_function
    def analyze_schema(self) -> Dict[str, Any]:
        """
        데이터베이스 스키마 분석
        
        Returns:
            Dict[str, Any]: 스키마 분석 결과
        """
        try:
            with measure_time('analyze_schema'):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 테이블 목록 조회
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                schema_info = {
                    'tables': {},
                    'indexes': {},
                    'total_tables': len(tables),
                    'total_indexes': 0,
                    'total_rows': 0,
                    'total_size_bytes': os.path.getsize(self.db_path)
                }
                
                # 테이블별 정보 수집
                for table in tables:
                    # 테이블 스키마 조회
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [
                        {
                            'name': row[1],
                            'type': row[2],
                            'notnull': bool(row[3]),
                            'default': row[4],
                            'pk': bool(row[5])
                        }
                        for row in cursor.fetchall()
                    ]
                    
                    # 테이블 행 수 조회
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]
                    
                    # 인덱스 조회
                    cursor.execute(f"PRAGMA index_list({table})")
                    indexes = [
                        {
                            'name': row[1],
                            'unique': bool(row[2]),
                            'columns': self._get_index_columns(cursor, row[1])
                        }
                        for row in cursor.fetchall()
                    ]
                    
                    schema_info['tables'][table] = {
                        'columns': columns,
                        'row_count': row_count,
                        'indexes': indexes
                    }
                    
                    schema_info['total_rows'] += row_count
                    schema_info['total_indexes'] += len(indexes)
                    
                    # 인덱스 정보 저장
                    for index in indexes:
                        schema_info['indexes'][index['name']] = {
                            'table': table,
                            'columns': index['columns'],
                            'unique': index['unique']
                        }
                
                conn.close()
                
                return schema_info
                
        except Exception as e:
            logger.error(f"스키마 분석 중 오류 발생: {e}")
            return {'error': str(e)}
    
    @profile_function
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        쿼리 실행 계획 분석
        
        Args:
            query: SQL 쿼리
            
        Returns:
            Dict[str, Any]: 실행 계획 분석 결과
        """
        try:
            with measure_time('analyze_query'):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # EXPLAIN QUERY PLAN 실행
                cursor.execute(f"EXPLAIN QUERY PLAN {query}")
                plan_rows = cursor.fetchall()
                
                # 실행 계획 파싱
                plan = []
                for row in plan_rows:
                    plan.append({
                        'id': row[0],
                        'parent': row[1],
                        'detail': row[3]
                    })
                
                # 실행 계획 분석
                analysis = {
                    'query': query,
                    'plan': plan,
                    'uses_index': any('USING INDEX' in row['detail'] for row in plan),
                    'table_scan': any('SCAN TABLE' in row['detail'] for row in plan),
                    'recommendations': []
                }
                
                # 테이블 스캔 감지
                if analysis['table_scan'] and not analysis['uses_index']:
                    # 테이블 이름 추출
                    table_names = []
                    for row in plan:
                        if 'SCAN TABLE' in row['detail']:
                            parts = row['detail'].split()
                            table_idx = parts.index('TABLE') + 1
                            if table_idx < len(parts):
                                table_names.append(parts[table_idx])
                    
                    # WHERE 절 조건 추출
                    where_columns = self._extract_where_columns(query)
                    
                    # 인덱스 추천
                    for table in table_names:
                        for column in where_columns:
                            analysis['recommendations'].append(
                                f"테이블 '{table}'의 '{column}' 열에 인덱스 추가를 고려하세요."
                            )
                
                conn.close()
                
                return analysis
                
        except Exception as e:
            logger.error(f"쿼리 분석 중 오류 발생: {e}")
            return {'query': query, 'error': str(e)}
    
    @profile_function
    def recommend_indexes(self) -> List[Dict[str, Any]]:
        """
        인덱스 추천
        
        Returns:
            List[Dict[str, Any]]: 추천 인덱스 목록
        """
        try:
            with measure_time('recommend_indexes'):
                # 스키마 분석
                schema_info = self.analyze_schema()
                
                # 추천 인덱스 목록
                recommendations = []
                
                # 테이블별 분석
                for table_name, table_info in schema_info['tables'].items():
                    # 기존 인덱스 열
                    existing_index_columns = set()
                    for index in table_info['indexes']:
                        for column in index['columns']:
                            existing_index_columns.add(column)
                    
                    # 외래 키 열 확인
                    cursor = sqlite3.connect(self.db_path).cursor()
                    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                    foreign_keys = cursor.fetchall()
                    
                    # 외래 키 열에 인덱스 추천
                    for fk in foreign_keys:
                        column = fk[3]  # 외래 키 열 이름
                        if column not in existing_index_columns:
                            recommendations.append({
                                'table': table_name,
                                'column': column,
                                'reason': '외래 키',
                                'sql': f"CREATE INDEX idx_{table_name}_{column} ON {table_name}({column});"
                            })
                    
                    # 기본 키가 아닌 열 중 인덱스 추천
                    for column in table_info['columns']:
                        column_name = column['name']
                        
                        # 이미 인덱스가 있는 열은 제외
                        if column_name in existing_index_columns:
                            continue
                        
                        # 기본 키는 제외
                        if column['pk']:
                            continue
                        
                        # 특정 패턴의 열에 인덱스 추천
                        if (
                            column_name.endswith('_id') or
                            column_name.endswith('_date') or
                            column_name in ('category', 'payment_method', 'transaction_type')
                        ):
                            recommendations.append({
                                'table': table_name,
                                'column': column_name,
                                'reason': '일반적인 조회 패턴',
                                'sql': f"CREATE INDEX idx_{table_name}_{column_name} ON {table_name}({column_name});"
                            })
                
                return recommendations
                
        except Exception as e:
            logger.error(f"인덱스 추천 중 오류 발생: {e}")
            return []
    
    @profile_function
    def create_index(self, table: str, columns: List[str], unique: bool = False) -> bool:
        """
        인덱스 생성
        
        Args:
            table: 테이블 이름
            columns: 열 이름 목록
            unique: 고유 인덱스 여부
            
        Returns:
            bool: 생성 성공 여부
        """
        try:
            with measure_time('create_index'):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 인덱스 이름 생성
                index_name = f"idx_{table}_{'_'.join(columns)}"
                
                # 인덱스 생성 SQL
                unique_str = "UNIQUE " if unique else ""
                columns_str = ", ".join(columns)
                sql = f"CREATE {unique_str}INDEX IF NOT EXISTS {index_name} ON {table}({columns_str})"
                
                # 인덱스 생성
                cursor.execute(sql)
                conn.commit()
                conn.close()
                
                logger.info(f"인덱스가 생성되었습니다: {index_name}")
                return True
                
        except Exception as e:
            logger.error(f"인덱스 생성 중 오류 발생: {e}")
            return False
    
    @profile_function
    def drop_index(self, index_name: str) -> bool:
        """
        인덱스 삭제
        
        Args:
            index_name: 인덱스 이름
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            with measure_time('drop_index'):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 인덱스 삭제 SQL
                sql = f"DROP INDEX IF EXISTS {index_name}"
                
                # 인덱스 삭제
                cursor.execute(sql)
                conn.commit()
                conn.close()
                
                logger.info(f"인덱스가 삭제되었습니다: {index_name}")
                return True
                
        except Exception as e:
            logger.error(f"인덱스 삭제 중 오류 발생: {e}")
            return False
    
    @profile_function
    def optimize_database(self) -> bool:
        """
        데이터베이스 최적화
        
        Returns:
            bool: 최적화 성공 여부
        """
        try:
            with measure_time('optimize_database'):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # VACUUM 실행
                cursor.execute("VACUUM")
                
                # ANALYZE 실행
                cursor.execute("ANALYZE")
                
                # PRAGMA 최적화 설정
                cursor.execute("PRAGMA optimize")
                
                conn.commit()
                conn.close()
                
                logger.info("데이터베이스 최적화가 완료되었습니다.")
                return True
                
        except Exception as e:
            logger.error(f"데이터베이스 최적화 중 오류 발생: {e}")
            return False
    
    @profile_function
    def analyze_queries_from_log(self, log_file: str) -> List[Dict[str, Any]]:
        """
        로그 파일에서 쿼리 분석
        
        Args:
            log_file: 로그 파일 경로
            
        Returns:
            List[Dict[str, Any]]: 쿼리 분석 결과
        """
        try:
            with measure_time('analyze_queries_from_log'):
                if not os.path.exists(log_file):
                    logger.error(f"로그 파일을 찾을 수 없습니다: {log_file}")
                    return []
                
                # 로그 파일에서 SQL 쿼리 추출
                queries = []
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if 'SQL:' in line:
                            query_start = line.find('SQL:') + 4
                            query = line[query_start:].strip()
                            queries.append(query)
                
                # 쿼리 분석
                results = []
                for query in queries:
                    analysis = self.analyze_query(query)
                    results.append(analysis)
                
                return results
                
        except Exception as e:
            logger.error(f"로그 파일 분석 중 오류 발생: {e}")
            return []
    
    @profile_function
    def save_analysis(self, analysis: Dict[str, Any], file_path: str = None) -> str:
        """
        분석 결과 저장
        
        Args:
            analysis: 분석 결과
            file_path: 저장할 파일 경로
            
        Returns:
            str: 저장된 파일 경로
        """
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(self.output_dir, f"db_analysis_{timestamp}.json")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            
            logger.info(f"분석 결과가 저장되었습니다: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"분석 결과 저장 중 오류 발생: {e}")
            return ""
    
    def _get_index_columns(self, cursor: sqlite3.Cursor, index_name: str) -> List[str]:
        """
        인덱스 열 목록 조회
        
        Args:
            cursor: 데이터베이스 커서
            index_name: 인덱스 이름
            
        Returns:
            List[str]: 인덱스 열 목록
        """
        cursor.execute(f"PRAGMA index_info({index_name})")
        return [row[2] for row in cursor.fetchall()]
    
    def _extract_where_columns(self, query: str) -> List[str]:
        """
        WHERE 절 조건 열 추출
        
        Args:
            query: SQL 쿼리
            
        Returns:
            List[str]: WHERE 절 조건 열 목록
        """
        # 간단한 WHERE 절 파싱
        query = query.upper()
        where_idx = query.find('WHERE')
        
        if where_idx == -1:
            return []
        
        where_clause = query[where_idx + 5:]
        
        # ORDER BY, GROUP BY, LIMIT 등 제거
        for keyword in ['ORDER BY', 'GROUP BY', 'LIMIT', 'HAVING']:
            keyword_idx = where_clause.find(keyword)
            if keyword_idx != -1:
                where_clause = where_clause[:keyword_idx]
        
        # 조건 분리
        conditions = []
        
        # AND, OR로 분리
        for operator in ['AND', 'OR']:
            if operator in where_clause:
                parts = where_clause.split(operator)
                conditions.extend(parts)
                where_clause = ""
        
        if where_clause:
            conditions.append(where_clause)
        
        # 열 이름 추출
        columns = []
        for condition in conditions:
            # 비교 연산자로 분리
            for operator in ['=', '>', '<', '>=', '<=', '<>', 'LIKE', 'IN', 'BETWEEN']:
                if operator in condition:
                    column = condition.split(operator)[0].strip()
                    # 테이블 이름 제거
                    if '.' in column:
                        column = column.split('.')[1]
                    columns.append(column)
                    break
        
        return columns

def main():
    """
    메인 함수
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='데이터베이스 최적화 도구')
    
    parser.add_argument('--action', '-a', choices=[
        'analyze', 'optimize', 'recommend-indexes', 'create-index', 'drop-index', 'analyze-query'
    ], default='analyze', help='수행할 작업')
    
    parser.add_argument('--db-path', help='데이터베이스 파일 경로')
    parser.add_argument('--table', help='테이블 이름')
    parser.add_argument('--columns', help='열 이름 (쉼표로 구분)')
    parser.add_argument('--index', help='인덱스 이름')
    parser.add_argument('--unique', action='store_true', help='고유 인덱스 생성')
    parser.add_argument('--query', help='SQL 쿼리')
    parser.add_argument('--log-file', help='로그 파일 경로')
    parser.add_argument('--output', '-o', help='출력 파일 경로')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 출력')
    
    args = parser.parse_args()
    
    # 로깅 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 데이터베이스 최적화 도구 초기화
    optimizer = DatabaseOptimizer(args.db_path)
    
    # 작업 수행
    if args.action == 'analyze':
        # 데이터베이스 스키마 분석
        analysis = optimizer.analyze_schema()
        
        if args.output:
            optimizer.save_analysis(analysis, args.output)
        else:
            print(json.dumps(analysis, indent=2))
    
    elif args.action == 'optimize':
        # 데이터베이스 최적화
        result = optimizer.optimize_database()
        print(f"데이터베이스 최적화 결과: {'성공' if result else '실패'}")
    
    elif args.action == 'recommend-indexes':
        # 인덱스 추천
        recommendations = optimizer.recommend_indexes()
        
        if recommendations:
            print("추천 인덱스:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. 테이블: {rec['table']}, 열: {rec['column']}, 이유: {rec['reason']}")
                print(f"   SQL: {rec['sql']}")
        else:
            print("추천할 인덱스가 없습니다.")
        
        if args.output:
            optimizer.save_analysis({'recommendations': recommendations}, args.output)
    
    elif args.action == 'create-index':
        # 인덱스 생성
        if not args.table or not args.columns:
            print("테이블 이름과 열 이름을 지정해야 합니다.")
            return
        
        columns = [col.strip() for col in args.columns.split(',')]
        result = optimizer.create_index(args.table, columns, args.unique)
        print(f"인덱스 생성 결과: {'성공' if result else '실패'}")
    
    elif args.action == 'drop-index':
        # 인덱스 삭제
        if not args.index:
            print("인덱스 이름을 지정해야 합니다.")
            return
        
        result = optimizer.drop_index(args.index)
        print(f"인덱스 삭제 결과: {'성공' if result else '실패'}")
    
    elif args.action == 'analyze-query':
        # 쿼리 분석
        if args.query:
            # 단일 쿼리 분석
            analysis = optimizer.analyze_query(args.query)
            
            if 'error' in analysis:
                print(f"쿼리 분석 오류: {analysis['error']}")
            else:
                print(f"쿼리: {analysis['query']}")
                print(f"인덱스 사용: {'예' if analysis['uses_index'] else '아니오'}")
                print(f"테이블 스캔: {'예' if analysis['table_scan'] else '아니오'}")
                
                if analysis['recommendations']:
                    print("권장사항:")
                    for rec in analysis['recommendations']:
                        print(f"- {rec}")
            
            if args.output:
                optimizer.save_analysis(analysis, args.output)
        
        elif args.log_file:
            # 로그 파일에서 쿼리 분석
            results = optimizer.analyze_queries_from_log(args.log_file)
            
            if results:
                print(f"{len(results)}개의 쿼리가 분석되었습니다.")
                
                # 문제가 있는 쿼리만 표시
                problem_queries = [r for r in results if r.get('table_scan') and not r.get('uses_index')]
                
                if problem_queries:
                    print(f"{len(problem_queries)}개의 문제 쿼리가 발견되었습니다:")
                    for i, query in enumerate(problem_queries, 1):
                        print(f"{i}. 쿼리: {query['query']}")
                        if query.get('recommendations'):
                            for rec in query['recommendations']:
                                print(f"   - {rec}")
                else:
                    print("모든 쿼리가 최적화되어 있습니다.")
            
            if args.output:
                optimizer.save_analysis({'queries': results}, args.output)
        
        else:
            print("쿼리 또는 로그 파일을 지정해야 합니다.")

if __name__ == '__main__':
    main()