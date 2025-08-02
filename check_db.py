import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'personal_data.db')

def check_database_structure():
    """데이터베이스 구조를 확인합니다."""
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        
        # 테이블 및 뷰 확인
        cur.execute("SELECT name, type FROM sqlite_master WHERE type='table' OR type='view'")
        print("=== 테이블 및 뷰 ===")
        for row in cur.fetchall():
            print(f"- {row[0]} ({row[1]})")
        
        # 인덱스 확인
        cur.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        print("\n=== 인덱스 ===")
        for row in cur.fetchall():
            print(f"- {row[0]}")
        
        # 테이블별 레코드 수 확인
        tables = ['transactions', 'classification_rules', 'user_preferences', 'analysis_filters']
        print("\n=== 테이블별 레코드 수 ===")
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"- {table}: {count}개 레코드")
        
        # transactions 테이블 스키마 확인
        cur.execute("PRAGMA table_info(transactions)")
        print("\n=== transactions 테이블 스키마 ===")
        for col in cur.fetchall():
            print(f"- {col[1]} ({col[2]}) {' PRIMARY KEY' if col[5] == 1 else ''}")
        
    except sqlite3.Error as e:
        print(f"데이터베이스 확인 중 오류 발생: {e}")
    finally:
        if con:
            con.close()

if __name__ == '__main__':
    check_database_structure()