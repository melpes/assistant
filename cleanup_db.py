import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'personal_data.db')

def cleanup_database():
    """마이그레이션 후 불필요한 테이블을 정리합니다."""
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        
        # 기존 테이블 삭제
        tables_to_drop = ['expenses', 'expenses_new']
        
        for table in tables_to_drop:
            try:
                cur.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"'{table}' 테이블이 삭제되었습니다.")
            except sqlite3.Error as e:
                print(f"'{table}' 테이블 삭제 중 오류 발생: {e}")
        
        # 기존 뷰 삭제
        cur.execute("DROP VIEW IF EXISTS expense_summary")
        print("'expense_summary' 뷰가 삭제되었습니다.")
        
        con.commit()
        print("데이터베이스 정리가 완료되었습니다.")
        
    except sqlite3.Error as e:
        print(f"데이터베이스 정리 중 오류 발생: {e}")
    finally:
        if con:
            con.close()

if __name__ == '__main__':
    cleanup_database()