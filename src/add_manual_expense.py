# src/add_manual_expense.py
import sqlite3
import os
from datetime import datetime

DB_FILE_NAME = "personal_data.db"
TABLE_NAME = "expenses"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, DB_FILE_NAME)

def add_manual_expense():
    """현금 지출이나 기타 수동 입력이 필요한 지출을 추가하는 함수"""
    print("=== 수동 지출 내역 추가 ===")
    
    try:
        # 사용자 입력 받기
        date_input = input("거래 날짜 (YYYY-MM-DD 형식, 엔터시 오늘): ").strip()
        if not date_input:
            date_input = datetime.now().strftime('%Y-%m-%d')
        
        description = input("지출 내용: ").strip()
        if not description:
            print("지출 내용은 필수입니다.")
            return
        
        amount_input = input("금액 (원): ").strip()
        try:
            amount = int(amount_input)
            if amount <= 0:
                print("금액은 0보다 큰 값이어야 합니다.")
                return
        except ValueError:
            print("올바른 금액을 입력해주세요.")
            return
        
        # 결제 방식 선택
        print("\n결제 방식을 선택하세요:")
        print("1. 현금")
        print("2. 기타 카드")
        print("3. 기타")
        
        payment_choice = input("선택 (1-3): ").strip()
        payment_methods = {
            '1': '현금',
            '2': '기타카드',
            '3': '기타'
        }
        payment_method = payment_methods.get(payment_choice, '기타')
        
        # 카테고리 선택
        print("\n카테고리를 선택하세요:")
        categories = [
            '식비', '교통비', '생활용품/식료품', '카페/음료', 
            '의료비', '통신비', '공과금', '문화/오락', 
            '의류/패션', '기타'
        ]
        
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")
        
        cat_choice = input("선택 (1-10): ").strip()
        try:
            category = categories[int(cat_choice) - 1]
        except (ValueError, IndexError):
            category = '기타'
        
        memo = input("메모 (선택사항): ").strip()
        
        # 고유 ID 생성
        approval_number = f"MANUAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # DB에 저장
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            
            cur.execute(f"""
                INSERT INTO {TABLE_NAME} 
                (approval_number, transaction_date, description, amount, category, source, payment_method, account_type, memo) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                approval_number,
                date_input,
                description,
                amount,
                category,
                'Manual Entry',
                payment_method,
                '수동입력',
                memo
            ))
            
            con.commit()
        
        print(f"\n✅ 지출 내역이 성공적으로 추가되었습니다!")
        print(f"   날짜: {date_input}")
        print(f"   내용: {description}")
        print(f"   금액: {amount:,}원")
        print(f"   결제방식: {payment_method}")
        print(f"   카테고리: {category}")
        
    except KeyboardInterrupt:
        print("\n\n취소되었습니다.")
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")

def batch_add_expenses():
    """여러 지출을 한번에 추가하는 함수"""
    print("=== 일괄 지출 내역 추가 ===")
    print("형식: 날짜,내용,금액,결제방식,카테고리")
    print("예시: 2024-01-15,점심식사,12000,현금,식비")
    print("입력 완료 후 빈 줄을 입력하세요.\n")
    
    expenses = []
    while True:
        line = input("지출 내역: ").strip()
        if not line:
            break
            
        try:
            parts = line.split(',')
            if len(parts) < 3:
                print("최소 날짜,내용,금액은 입력해야 합니다.")
                continue
                
            date = parts[0].strip()
            description = parts[1].strip()
            amount = int(parts[2].strip())
            payment_method = parts[3].strip() if len(parts) > 3 else '현금'
            category = parts[4].strip() if len(parts) > 4 else '기타'
            
            expenses.append({
                'date': date,
                'description': description,
                'amount': amount,
                'payment_method': payment_method,
                'category': category
            })
            
        except ValueError:
            print("금액은 숫자로 입력해주세요.")
        except Exception as e:
            print(f"입력 오류: {e}")
    
    if not expenses:
        print("추가할 지출이 없습니다.")
        return
    
    # DB에 일괄 저장
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        
        for i, expense in enumerate(expenses):
            approval_number = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
            
            cur.execute(f"""
                INSERT INTO {TABLE_NAME} 
                (approval_number, transaction_date, description, amount, category, source, payment_method, account_type) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                approval_number,
                expense['date'],
                expense['description'],
                expense['amount'],
                expense['category'],
                'Manual Entry',
                expense['payment_method'],
                '수동입력'
            ))
        
        con.commit()
    
    print(f"\n✅ {len(expenses)}개의 지출 내역이 성공적으로 추가되었습니다!")

if __name__ == '__main__':
    print("1. 단일 지출 추가")
    print("2. 일괄 지출 추가")
    choice = input("선택 (1-2): ").strip()
    
    if choice == '2':
        batch_add_expenses()
    else:
        add_manual_expense()