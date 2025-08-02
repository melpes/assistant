# src/expense_analyzer.py
import sys
import os

# calendar 폴더와의 충돌을 피하기 위해 경로 조정
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# calendar 폴더를 sys.path에서 제거
if current_dir in sys.path:
    sys.path.remove(current_dir)

import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_FILE_NAME = "personal_data.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, DB_FILE_NAME)

def get_expense_summary(days=30):
    """지정된 기간의 지출 요약을 반환"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    with sqlite3.connect(DB_PATH) as con:
        # 전체 지출 현황
        total_query = """
        SELECT 
            payment_method,
            COUNT(*) as count,
            SUM(amount) as total,
            AVG(amount) as average
        FROM expenses 
        WHERE transaction_date >= ? AND transaction_date <= ?
        GROUP BY payment_method
        ORDER BY total DESC
        """
        
        df_total = pd.read_sql_query(total_query, con, params=[
            start_date.strftime('%Y-%m-%d'), 
            end_date.strftime('%Y-%m-%d')
        ])
        
        # 카테고리별 지출
        category_query = """
        SELECT 
            category,
            payment_method,
            COUNT(*) as count,
            SUM(amount) as total
        FROM expenses 
        WHERE transaction_date >= ? AND transaction_date <= ?
        GROUP BY category, payment_method
        ORDER BY total DESC
        """
        
        df_category = pd.read_sql_query(category_query, con, params=[
            start_date.strftime('%Y-%m-%d'), 
            end_date.strftime('%Y-%m-%d')
        ])
        
        # 일별 지출 트렌드
        daily_query = """
        SELECT 
            transaction_date,
            payment_method,
            SUM(amount) as daily_total
        FROM expenses 
        WHERE transaction_date >= ? AND transaction_date <= ?
        GROUP BY transaction_date, payment_method
        ORDER BY transaction_date DESC
        """
        
        df_daily = pd.read_sql_query(daily_query, con, params=[
            start_date.strftime('%Y-%m-%d'), 
            end_date.strftime('%Y-%m-%d')
        ])
    
    return df_total, df_category, df_daily

def print_expense_report(days=30):
    """지출 리포트를 콘솔에 출력"""
    print(f"\n=== 최근 {days}일 지출 분석 리포트 ===")
    print(f"분석 기간: {(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')} ~ {datetime.now().strftime('%Y-%m-%d')}")
    
    df_total, df_category, df_daily = get_expense_summary(days)
    
    if df_total.empty:
        print("해당 기간에 지출 데이터가 없습니다.")
        return
    
    # 1. 결제 방식별 지출 현황
    print("\n[결제 방식별 지출 현황]")
    print("-" * 60)
    total_amount = df_total['total'].sum()
    
    for _, row in df_total.iterrows():
        percentage = (row['total'] / total_amount) * 100
        print(f"{row['payment_method']:15} | {row['total']:>10,}원 ({percentage:5.1f}%) | {row['count']:3}건 | 평균 {row['average']:>7,.0f}원")
    
    print(f"{'전체 합계':15} | {total_amount:>10,}원 (100.0%) | {df_total['count'].sum():3}건")
    
    # 2. 카테고리별 지출 현황 (상위 10개)
    print("\n[카테고리별 지출 현황 (상위 10개)]")
    print("-" * 60)
    
    category_summary = df_category.groupby('category').agg({
        'total': 'sum',
        'count': 'sum'
    }).sort_values('total', ascending=False).head(10)
    
    for category, row in category_summary.iterrows():
        percentage = (row['total'] / total_amount) * 100
        print(f"{category:15} | {row['total']:>10,}원 ({percentage:5.1f}%) | {row['count']:3}건")
    
    # 3. 최근 5일 일별 지출
    print("\n[최근 5일 일별 지출]")
    print("-" * 40)
    
    recent_daily = df_daily.groupby('transaction_date')['daily_total'].sum().head(5)
    for date, amount in recent_daily.items():
        print(f"{date} | {amount:>10,}원")
    
    # 4. 일평균 지출
    avg_daily = total_amount / days
    print(f"\n[일평균 지출]: {avg_daily:,.0f}원")
    print(f"[월 예상 지출]: {avg_daily * 30:,.0f}원")

def get_payment_method_breakdown():
    """결제 방식별 상세 분석"""
    with sqlite3.connect(DB_PATH) as con:
        query = """
        SELECT 
            payment_method,
            source,
            account_type,
            COUNT(*) as transaction_count,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount,
            MIN(transaction_date) as first_transaction,
            MAX(transaction_date) as last_transaction
        FROM expenses 
        GROUP BY payment_method, source, account_type
        ORDER BY total_amount DESC
        """
        
        df = pd.read_sql_query(query, con)
        
        print("\n[결제 방식별 상세 분석]")
        print("=" * 80)
        
        for _, row in df.iterrows():
            print(f"\n결제방식: {row['payment_method']} ({row['source']})")
            print(f"  계좌유형: {row['account_type']}")
            print(f"  총 지출: {row['total_amount']:,}원")
            print(f"  거래 횟수: {row['transaction_count']}건")
            print(f"  평균 금액: {row['avg_amount']:,.0f}원")
            print(f"  기간: {row['first_transaction']} ~ {row['last_transaction']}")

def find_missing_expenses():
    """누락될 수 있는 지출 패턴 분석"""
    print("\n[지출 패턴 분석 및 누락 가능성 체크]")
    print("=" * 50)
    
    with sqlite3.connect(DB_PATH) as con:
        # 정기적인 지출이 누락되었는지 체크
        regular_query = """
        SELECT 
            description,
            COUNT(*) as frequency,
            AVG(amount) as avg_amount,
            MAX(transaction_date) as last_date
        FROM expenses 
        WHERE description LIKE '%자동이체%' OR description LIKE '%정기%'
        GROUP BY description
        HAVING frequency > 1
        ORDER BY last_date DESC
        """
        
        df_regular = pd.read_sql_query(regular_query, con)
        
        if not df_regular.empty:
            print("정기 지출 내역:")
            for _, row in df_regular.iterrows():
                days_ago = (datetime.now() - pd.to_datetime(row['last_date'])).days
                print(f"  {row['description']} | 마지막: {row['last_date']} ({days_ago}일 전) | 평균: {row['avg_amount']:,.0f}원")
        
        # 현금 사용 비율 체크
        cash_query = """
        SELECT 
            payment_method,
            SUM(amount) as total
        FROM expenses 
        WHERE transaction_date >= date('now', '-30 days')
        GROUP BY payment_method
        """
        
        df_cash = pd.read_sql_query(cash_query, con)
        total_expense = df_cash['total'].sum()
        cash_expense = df_cash[df_cash['payment_method'] == '현금']['total'].sum() if '현금' in df_cash['payment_method'].values else 0
        
        cash_ratio = (cash_expense / total_expense * 100) if total_expense > 0 else 0
        
        print(f"\n현금 사용 비율: {cash_ratio:.1f}%")
        if cash_ratio < 10:
            print("[TIP] 현금 사용 내역이 적습니다. 현금 지출을 수동으로 추가해보세요.")

if __name__ == '__main__':
    print("지출 분석 도구")
    print("1. 30일 지출 리포트")
    print("2. 7일 지출 리포트")
    print("3. 결제 방식별 상세 분석")
    print("4. 누락 지출 패턴 분석")
    
    choice = input("선택 (1-4): ").strip()
    
    if choice == '1':
        print_expense_report(30)
    elif choice == '2':
        print_expense_report(7)
    elif choice == '3':
        get_payment_method_breakdown()
    elif choice == '4':
        find_missing_expenses()
    else:
        print_expense_report(30)