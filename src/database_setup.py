# src/database_setup.py (수정)
import sqlite3
import os
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'personal_data.db')

def create_database():
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        con.execute("PRAGMA foreign_keys = ON")  # 외래키 제약조건 활성화
        logger.info(f"데이터베이스에 성공적으로 연결되었습니다: {DB_PATH}")

        # 1. transactions 테이블 (expenses 테이블을 대체)
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
        logger.info("'transactions' 테이블이 성공적으로 생성되었거나 이미 존재합니다.")

        # 2. classification_rules 테이블
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
        logger.info("'classification_rules' 테이블이 성공적으로 생성되었거나 이미 존재합니다.")

        # 3. user_preferences 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY,
                preference_key TEXT UNIQUE NOT NULL,
                preference_value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("'user_preferences' 테이블이 성공적으로 생성되었거나 이미 존재합니다.")

        # 4. analysis_filters 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_filters (
                id INTEGER PRIMARY KEY,
                filter_name TEXT NOT NULL,
                filter_config JSON NOT NULL,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("'analysis_filters' 테이블이 성공적으로 생성되었거나 이미 존재합니다.")

        # 인덱스 생성
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_payment_method ON transactions(payment_method)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_source ON transactions(source)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(amount)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_excluded ON transactions(is_excluded)",
            
            "CREATE INDEX IF NOT EXISTS idx_rules_type ON classification_rules(rule_type)",
            "CREATE INDEX IF NOT EXISTS idx_rules_active ON classification_rules(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_rules_priority ON classification_rules(priority)",
            
            "CREATE INDEX IF NOT EXISTS idx_preferences_key ON user_preferences(preference_key)",
            
            "CREATE INDEX IF NOT EXISTS idx_filters_default ON analysis_filters(is_default)"
        ]
        
        for index_sql in indexes:
            cur.execute(index_sql)
        logger.info("데이터베이스 인덱스가 성공적으로 생성되었습니다.")

        # 분석용 뷰 생성
        cur.execute("DROP VIEW IF EXISTS expense_summary")
        
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
        logger.info("분석용 뷰가 성공적으로 생성되었습니다.")



        # 기본 설정 데이터 삽입
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
        
        con.commit()
        logger.info("변경사항이 성공적으로 저장되었습니다.")
    except sqlite3.Error as e:
        logger.error(f"데이터베이스 작업 중 오류가 발생했습니다: {e}")
    finally:
        if con:
            con.close()
            logger.info("데이터베이스 연결이 종료되었습니다.")

def get_db_schema(db_path: str) -> str:
    """DB 스키마를 동적으로 읽어와 문자열로 반환합니다."""
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cur.fetchall()]
        schema_str = ""
        for table in tables:
            cur.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
            schema = cur.fetchone()[0]
            schema_str += schema + "\n\n"
        con.close()
        return schema_str.strip()
    except Exception as e:
        print(f"DB 스키마 조회 중 오류 발생: {e}")
        return ""

if __name__ == '__main__':
    create_database()