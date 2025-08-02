# src/migrate_database.py
"""
개인 금융 거래 관리 시스템 데이터베이스 마이그레이션
기존 expenses 테이블을 transactions 테이블로 확장하고 새로운 테이블들을 생성합니다.
"""
import sqlite3
import os
import logging
from datetime import datetime
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_FILE_NAME = "personal_data.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, DB_FILE_NAME)

def migrate_database():
    """기존 expenses 테이블을 transactions 테이블로 마이그레이션하고 새로운 테이블들을 생성합니다."""
    logger.info(f"=== 데이터베이스 마이그레이션을 시작합니다: {DB_PATH} ===")
    
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        con.execute("PRAGMA foreign_keys = ON")  # 외래키 제약조건 활성화
        
        # 트랜잭션 시작
        con.execute("BEGIN TRANSACTION")
        
        # 1. 기존 데이터 백업
        backup_table_name = backup_existing_data(cur)
        
        # 2. 새로운 스키마 생성
        create_new_schema(cur)
        
        # 3. 인덱스 생성
        create_indexes(cur)
        
        # 4. 기존 데이터 마이그레이션
        migrate_existing_data(cur)
        
        # 5. 기본 데이터 삽입
        insert_default_data(cur)
        
        # 6. 뷰 생성
        create_views(cur)
        
        # 7. 마이그레이션 검증
        verify_migration(cur)
        
        # 트랜잭션 커밋
        con.commit()
        
        logger.info("=== 데이터베이스 마이그레이션이 완료되었습니다! ===")
        logger.info(f"백업 테이블: {backup_table_name}")
        
    except Exception as e:
        # 오류 발생 시 롤백
        if con:
            con.rollback()
        logger.error(f"마이그레이션 실패: {e}")
        raise
    finally:
        if con:
            con.close()
            logger.info("데이터베이스 연결이 종료되었습니다.")

def backup_existing_data(cur):
    """기존 데이터 백업"""
    try:
        # expenses 테이블 존재 확인
        cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='expenses'
        """)
        
        if not cur.fetchone():
            logger.info("기존 expenses 테이블이 없습니다. 백업을 건너뜁니다.")
            return None
            
        # 백업 테이블 생성
        backup_table_name = f"expenses_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cur.execute(f"""
            CREATE TABLE {backup_table_name} AS 
            SELECT * FROM expenses
        """)
        
        # 백업된 레코드 수 확인
        cur.execute(f"SELECT COUNT(*) FROM {backup_table_name}")
        count = cur.fetchone()[0]
        
        logger.info(f"기존 데이터 백업 완료: {backup_table_name} ({count}개 레코드)")
        return backup_table_name
        
    except sqlite3.Error as e:
        logger.error(f"데이터 백업 실패: {e}")
        raise

def create_new_schema(cur):
    """새로운 스키마 생성"""
    try:
        # 1. transactions 테이블 생성
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                transaction_id TEXT UNIQUE NOT NULL,
                transaction_date DATE NOT NULL,
                description TEXT NOT NULL,
                amount DECIMAL(12,2) NOT NULL,
                transaction_type TEXT NOT NULL CHECK (transaction_type IN ('expense', 'income')),
                category TEXT,
                payment_method TEXT,
                source TEXT NOT NULL,
                account_type TEXT,
                memo TEXT,
                is_excluded BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("transactions 테이블 생성 완료")
        
        # 2. classification_rules 테이블 생성
        cur.execute("""
            CREATE TABLE IF NOT EXISTS classification_rules (
                id INTEGER PRIMARY KEY,
                rule_name TEXT NOT NULL,
                rule_type TEXT NOT NULL CHECK (rule_type IN ('category', 'payment_method', 'filter')),
                condition_type TEXT NOT NULL CHECK (condition_type IN ('contains', 'equals', 'regex', 'amount_range')),
                condition_value TEXT NOT NULL,
                target_value TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_by TEXT DEFAULT 'user' CHECK (created_by IN ('user', 'system', 'learned')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("classification_rules 테이블 생성 완료")
        
        # 3. user_preferences 테이블 생성
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY,
                preference_key TEXT UNIQUE NOT NULL,
                preference_value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("user_preferences 테이블 생성 완료")
        
        # 4. analysis_filters 테이블 생성
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_filters (
                id INTEGER PRIMARY KEY,
                filter_name TEXT NOT NULL,
                filter_config JSON NOT NULL,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("analysis_filters 테이블 생성 완료")
        
    except sqlite3.Error as e:
        logger.error(f"새 스키마 생성 실패: {e}")
        raise

def create_indexes(cur):
    """성능 최적화를 위한 인덱스 생성"""
    try:
        # transactions 테이블 인덱스
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_payment_method ON transactions(payment_method)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_source ON transactions(source)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(amount)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_excluded ON transactions(is_excluded)",
            
            # classification_rules 테이블 인덱스
            "CREATE INDEX IF NOT EXISTS idx_rules_type ON classification_rules(rule_type)",
            "CREATE INDEX IF NOT EXISTS idx_rules_active ON classification_rules(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_rules_priority ON classification_rules(priority)",
            
            # user_preferences 테이블 인덱스
            "CREATE INDEX IF NOT EXISTS idx_preferences_key ON user_preferences(preference_key)",
            
            # analysis_filters 테이블 인덱스
            "CREATE INDEX IF NOT EXISTS idx_filters_default ON analysis_filters(is_default)"
        ]
        
        for index_sql in indexes:
            cur.execute(index_sql)
            
        logger.info("데이터베이스 인덱스 생성 완료")
        
    except sqlite3.Error as e:
        logger.error(f"인덱스 생성 실패: {e}")
        raise

def migrate_existing_data(cur):
    """기존 expenses 데이터를 transactions 테이블로 마이그레이션"""
    try:
        # 기존 expenses 테이블 존재 확인
        cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='expenses'
        """)
        
        if not cur.fetchone():
            logger.info("기존 expenses 테이블이 없습니다. 마이그레이션을 건너뜁니다.")
            return
            
        # 기존 데이터를 transactions 테이블로 복사
        cur.execute("""
            INSERT OR IGNORE INTO transactions (
                transaction_id,
                transaction_date,
                description,
                amount,
                transaction_type,
                category,
                payment_method,
                source,
                account_type,
                memo,
                created_at
            )
            SELECT 
                COALESCE(approval_number, 'MIGRATED_' || id || '_' || CAST(ABS(RANDOM()) AS TEXT)),
                transaction_date,
                COALESCE(description, ''),
                amount / 100.0,  -- 정수를 소수로 변환
                'expense',  -- 기존 데이터는 모두 지출로 처리
                COALESCE(category, '미분류'),
                COALESCE(payment_method, '기타'),
                COALESCE(source, '알 수 없음'),
                account_type,
                memo,
                COALESCE(created_at, CURRENT_TIMESTAMP)
            FROM expenses
        """)
        
        migrated_count = cur.rowcount
        logger.info(f"기존 데이터 마이그레이션 완료: {migrated_count}개 레코드")
        
    except sqlite3.Error as e:
        logger.error(f"데이터 마이그레이션 실패: {e}")
        raise

def insert_default_data(cur):
    """기본 설정 데이터 삽입"""
    try:
        # 기본 분류 규칙 삽입
        default_rules = [
            ('카페 자동분류', 'category', 'contains', '스타벅스', '식비', 10, True, 'system'),
            ('카페 자동분류2', 'category', 'contains', '커피', '식비', 10, True, 'system'),
            ('편의점 자동분류', 'category', 'contains', 'CU', '생활용품', 10, True, 'system'),
            ('편의점 자동분류2', 'category', 'contains', 'GS25', '생활용품', 10, True, 'system'),
            ('지하철 자동분류', 'category', 'contains', '지하철', '교통비', 10, True, 'system'),
            ('버스 자동분류', 'category', 'contains', '버스', '교통비', 10, True, 'system'),
            ('온라인쇼핑 자동분류', 'category', 'contains', '쿠팡', '온라인쇼핑', 10, True, 'system'),
            ('ATM 출금 분류', 'payment_method', 'contains', 'ATM', 'ATM출금', 10, True, 'system'),
            ('체크카드 분류', 'payment_method', 'contains', '체크카드', '체크카드결제', 10, True, 'system'),
        ]
        
        for rule in default_rules:
            cur.execute("""
                INSERT OR IGNORE INTO classification_rules 
                (rule_name, rule_type, condition_type, condition_value, target_value, priority, is_active, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, rule)
            
        # 기본 사용자 설정 삽입
        default_preferences = [
            ('default_currency', 'KRW', '기본 통화'),
            ('date_format', 'YYYY-MM-DD', '날짜 형식'),
            ('default_category', '미분류', '기본 카테고리'),
            ('auto_classify', 'true', '자동 분류 활성화'),
            ('backup_enabled', 'true', '자동 백업 활성화'),
        ]
        
        for pref in default_preferences:
            cur.execute("""
                INSERT OR IGNORE INTO user_preferences 
                (preference_key, preference_value, description)
                VALUES (?, ?, ?)
            """, pref)
            
        # 기본 분석 필터 삽입
        default_filters = [
            ('전체 거래', '{"transaction_type": "all", "exclude_filtered": false}', True),
            ('지출만', '{"transaction_type": "expense", "exclude_filtered": true}', False),
            ('수입만', '{"transaction_type": "income", "exclude_filtered": true}', False),
            ('최근 30일', '{"date_range": "30d", "exclude_filtered": true}', False),
        ]
        
        for filter_data in default_filters:
            cur.execute("""
                INSERT OR IGNORE INTO analysis_filters 
                (filter_name, filter_config, is_default)
                VALUES (?, ?, ?)
            """, filter_data)
            
        logger.info("기본 설정 데이터 삽입 완료")
        
    except sqlite3.Error as e:
        logger.error(f"기본 데이터 삽입 실패: {e}")
        raise

def create_views(cur):
    """분석용 뷰 생성"""
    try:
        # 기존 뷰 삭제
        cur.execute("DROP VIEW IF EXISTS expense_summary")
        
        # 새로운 분석 뷰들 생성
        views = [
            # 거래 요약 뷰
            """
            CREATE VIEW transaction_summary AS
            SELECT 
                transaction_type,
                category,
                payment_method,
                source,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount,
                DATE(transaction_date) as date
            FROM transactions 
            WHERE is_excluded = FALSE
            GROUP BY transaction_type, category, payment_method, source, DATE(transaction_date)
            """,
            
            # 월별 요약 뷰
            """
            CREATE VIEW monthly_summary AS
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                transaction_type,
                category,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount
            FROM transactions 
            WHERE is_excluded = FALSE
            GROUP BY strftime('%Y-%m', transaction_date), transaction_type, category
            """,
            
            # 카테고리별 요약 뷰
            """
            CREATE VIEW category_summary AS
            SELECT 
                category,
                transaction_type,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount,
                MIN(amount) as min_amount,
                MAX(amount) as max_amount
            FROM transactions 
            WHERE is_excluded = FALSE
            GROUP BY category, transaction_type
            """
        ]
        
        for view_sql in views:
            cur.execute(view_sql)
            
        logger.info("분석용 뷰 생성 완료")
        
    except sqlite3.Error as e:
        logger.error(f"뷰 생성 실패: {e}")
        raise

def verify_migration(cur):
    """마이그레이션 결과 검증"""
    try:
        # 테이블 존재 확인
        tables = ['transactions', 'classification_rules', 'user_preferences', 'analysis_filters']
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            logger.info(f"{table} 테이블: {count}개 레코드")
            
        # 인덱스 확인
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = cur.fetchall()
        logger.info(f"생성된 인덱스: {len(indexes)}개")
        
        # 뷰 확인
        cur.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = cur.fetchall()
        logger.info(f"생성된 뷰: {len(views)}개")
        
        logger.info("마이그레이션 검증 완료")
        
    except sqlite3.Error as e:
        logger.error(f"마이그레이션 검증 실패: {e}")
        raise

if __name__ == '__main__':
    migrate_database()