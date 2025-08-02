# src/clean_account_data.py
import sqlite3
import os

DB_FILE_NAME = "personal_data.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, DB_FILE_NAME)

def clean_account_data():
    """토스뱅크 계좌 데이터만 삭제하고 다시 수집할 수 있도록 정리"""
    print("토스뱅크 계좌 데이터를 정리합니다...")
    
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        
        # 토스뱅크 계좌 데이터만 삭제
        cur.execute("DELETE FROM expenses WHERE source = 'Toss Bank Account'")
        deleted_count = cur.rowcount
        
        con.commit()
        print(f"✅ {deleted_count}개의 토스뱅크 계좌 데이터가 삭제되었습니다.")

if __name__ == '__main__':
    clean_account_data()