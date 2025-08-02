# src/check_db.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'personal_data.db')

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# expenses 테이블에서 최근 5개의 데이터만 가져오기
cur.execute("SELECT * FROM expenses ORDER BY transaction_date DESC LIMIT 5")
rows = cur.fetchall()

print("DB에 저장된 최근 5개의 지출 내역:")
for row in rows:
    print(row)

# events 테이블은 더 이상 사용하지 않습니다 (캘린더 서비스 리팩토링으로 인해 제거됨)

con.close()