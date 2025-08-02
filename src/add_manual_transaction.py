# -*- coding: utf-8 -*-
"""
수동 거래 입력 스크립트

사용자가 수동으로 지출 또는 수입 거래를 입력할 수 있는 CLI 인터페이스를 제공합니다.
"""

import os
import sys
import logging
from datetime import datetime
from decimal import Decimal
import argparse

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.ingesters.manual_ingester import ManualIngester
from src.repositories.transaction_repository import TransactionRepository
from src.models.transaction import Transaction

def setup_argparse() -> argparse.ArgumentParser:
    """
    명령줄 인자 파서를 설정합니다.
    
    Returns:
        argparse.ArgumentParser: 설정된 인자 파서
    """
    parser = argparse.ArgumentParser(description='수동 거래 입력 도구')
    
    parser.add_argument('--type', '-t', choices=['expense', 'income', 'batch'], default='expense',
                       help='입력할 거래 유형 (expense: 지출, income: 수입, batch: 일괄 입력)')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 로깅 활성화')
    
    return parser

def add_manual_expense():
    """
    수동으로 지출 거래를 입력합니다.
    """
    print("=== 수동 지출 내역 추가 ===")
    
    try:
        # 사용자 입력 받기
        date_input = input("거래 날짜 (YYYY-MM-DD 형식, 엔터시 오늘): ").strip()
        if not date_input:
            transaction_date = datetime.now().date()
        else:
            transaction_date = datetime.strptime(date_input, '%Y-%m-%d').date()
        
        description = input("지출 내용: ").strip()
        if not description:
            print("지출 내용은 필수입니다.")
            return
        
        amount_input = input("금액 (원): ").strip()
        try:
            amount = float(amount_input)
            if amount <= 0:
                print("금액은 0보다 큰 값이어야 합니다.")
                return
        except ValueError:
            print("올바른 금액을 입력해주세요.")
            return
        
        # 결제 방식 선택
        print("\n결제 방식을 선택하세요:")
        payment_methods = ['현금', '체크카드결제', '계좌이체', '토스페이', '기타카드', '기타']
        
        for i, method in enumerate(payment_methods, 1):
            print(f"{i}. {method}")
        
        payment_choice = input(f"선택 (1-{len(payment_methods)}): ").strip()
        try:
            payment_method = payment_methods[int(payment_choice) - 1]
        except (ValueError, IndexError):
            payment_method = '기타'
        
        # 카테고리 선택
        print("\n카테고리를 선택하세요:")
        categories = [
            '식비', '교통비', '생활용품/식료품', '카페/음료', 
            '의료비', '통신비', '공과금', '문화/오락', 
            '의류/패션', '온라인쇼핑', '현금인출', '해외결제',
            '간편결제', '기타'
        ]
        
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")
        
        cat_choice = input(f"선택 (1-{len(categories)}): ").strip()
        try:
            category = categories[int(cat_choice) - 1]
        except (ValueError, IndexError):
            category = '기타'
        
        memo = input("메모 (선택사항): ").strip()
        
        # ManualIngester를 사용하여 지출 추가
        ingester = ManualIngester()
        transaction_data = ingester.add_expense(
            transaction_date=transaction_date,
            description=description,
            amount=amount,
            category=category,
            payment_method=payment_method,
            memo=memo
        )
        
        # 데이터베이스에 저장
        repo = TransactionRepository()
        transaction = Transaction.from_dict(transaction_data)
        repo.create(transaction)
        
        print(f"\n✅ 지출 내역이 성공적으로 추가되었습니다!")
        print(f"   날짜: {transaction_date}")
        print(f"   내용: {description}")
        print(f"   금액: {amount:,}원")
        print(f"   결제방식: {payment_method}")
        print(f"   카테고리: {category}")
        
    except KeyboardInterrupt:
        print("\n\n취소되었습니다.")
    except Exception as e:
        logger.error(f"오류가 발생했습니다: {e}")
        print(f"오류가 발생했습니다: {e}")

def add_manual_income():
    """
    수동으로 수입 거래를 입력합니다.
    """
    print("=== 수동 수입 내역 추가 ===")
    
    try:
        # 사용자 입력 받기
        date_input = input("거래 날짜 (YYYY-MM-DD 형식, 엔터시 오늘): ").strip()
        if not date_input:
            transaction_date = datetime.now().date()
        else:
            transaction_date = datetime.strptime(date_input, '%Y-%m-%d').date()
        
        description = input("수입 내용: ").strip()
        if not description:
            print("수입 내용은 필수입니다.")
            return
        
        amount_input = input("금액 (원): ").strip()
        try:
            amount = float(amount_input)
            if amount <= 0:
                print("금액은 0보다 큰 값이어야 합니다.")
                return
        except ValueError:
            print("올바른 금액을 입력해주세요.")
            return
        
        # 입금 방식 선택
        print("\n입금 방식을 선택하세요:")
        payment_methods = ['계좌입금', '현금', '기타']
        
        for i, method in enumerate(payment_methods, 1):
            print(f"{i}. {method}")
        
        payment_choice = input(f"선택 (1-{len(payment_methods)}): ").strip()
        try:
            payment_method = payment_methods[int(payment_choice) - 1]
        except (ValueError, IndexError):
            payment_method = '기타'
        
        # 수입 유형 선택
        print("\n수입 유형을 선택하세요:")
        categories = ['급여', '용돈', '이자', '환급', '기타수입']
        
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")
        
        cat_choice = input(f"선택 (1-{len(categories)}): ").strip()
        try:
            category = categories[int(cat_choice) - 1]
        except (ValueError, IndexError):
            category = '기타수입'
        
        memo = input("메모 (선택사항): ").strip()
        
        # ManualIngester를 사용하여 수입 추가
        ingester = ManualIngester()
        transaction_data = ingester.add_income(
            transaction_date=transaction_date,
            description=description,
            amount=amount,
            category=category,
            payment_method=payment_method,
            memo=memo
        )
        
        # 데이터베이스에 저장
        repo = TransactionRepository()
        transaction = Transaction.from_dict(transaction_data)
        repo.create(transaction)
        
        print(f"\n✅ 수입 내역이 성공적으로 추가되었습니다!")
        print(f"   날짜: {transaction_date}")
        print(f"   내용: {description}")
        print(f"   금액: {amount:,}원")
        print(f"   입금방식: {payment_method}")
        print(f"   수입유형: {category}")
        
    except KeyboardInterrupt:
        print("\n\n취소되었습니다.")
    except Exception as e:
        logger.error(f"오류가 발생했습니다: {e}")
        print(f"오류가 발생했습니다: {e}")

def batch_add_transactions():
    """
    여러 거래를 한번에 추가합니다.
    """
    print("=== 일괄 거래 내역 추가 ===")
    print("형식: 날짜,내용,금액,거래유형(expense/income),결제방식,카테고리")
    print("예시: 2024-01-15,점심식사,12000,expense,현금,식비")
    print("입력 완료 후 빈 줄을 입력하세요.\n")
    
    transactions = []
    while True:
        line = input("거래 내역: ").strip()
        if not line:
            break
            
        try:
            parts = line.split(',')
            if len(parts) < 4:
                print("최소 날짜,내용,금액,거래유형은 입력해야 합니다.")
                continue
                
            date_str = parts[0].strip()
            description = parts[1].strip()
            amount = float(parts[2].strip())
            transaction_type = parts[3].strip().lower()
            
            if transaction_type not in ['expense', 'income']:
                print("거래유형은 'expense' 또는 'income'이어야 합니다.")
                continue
            
            payment_method = parts[4].strip() if len(parts) > 4 else ('현금' if transaction_type == 'expense' else '계좌입금')
            category = parts[5].strip() if len(parts) > 5 else ('기타' if transaction_type == 'expense' else '기타수입')
            
            transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            transactions.append({
                'transaction_date': transaction_date,
                'description': description,
                'amount': amount,
                'transaction_type': transaction_type,
                'payment_method': payment_method,
                'category': category
            })
            
        except ValueError as e:
            print(f"입력 오류: {e}")
        except Exception as e:
            print(f"입력 오류: {e}")
    
    if not transactions:
        print("추가할 거래가 없습니다.")
        return
    
    try:
        # ManualIngester를 사용하여 일괄 추가
        ingester = ManualIngester()
        transaction_data_list = ingester.batch_add_transactions(transactions)
        
        # 데이터베이스에 저장
        repo = TransactionRepository()
        saved_count = 0
        
        for transaction_data in transaction_data_list:
            transaction = Transaction.from_dict(transaction_data)
            repo.create(transaction)
            saved_count += 1
        
        print(f"\n✅ {saved_count}개의 거래 내역이 성공적으로 추가되었습니다!")
        
    except Exception as e:
        logger.error(f"오류가 발생했습니다: {e}")
        print(f"오류가 발생했습니다: {e}")

def main():
    """
    메인 함수
    """
    parser = setup_argparse()
    args = parser.parse_args()
    
    # 상세 로깅 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 거래 유형에 따라 적절한 함수 호출
    if args.type == 'income':
        add_manual_income()
    elif args.type == 'batch':
        batch_add_transactions()
    else:  # 기본값: expense
        add_manual_expense()

if __name__ == '__main__':
    main()