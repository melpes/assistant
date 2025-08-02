# -*- coding: utf-8 -*-
"""
수동 거래 입력 관리 도구

지출 및 수입 거래를 수동으로 입력하고 관리하는 통합 CLI 인터페이스를 제공합니다.
자동완성, 템플릿, 일괄 입력 등의 기능을 지원합니다.
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
import argparse
import json
from pathlib import Path
import uuid
import re
from typing import List, Dict, Any, Optional, Tuple

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

class ManualTransactionManager:
    """
    수동 거래 관리자 클래스
    
    지출 및 수입 거래를 수동으로 입력하고 관리하는 통합 인터페이스를 제공합니다.
    자동완성, 템플릿, 일괄 입력, 거래 검색 등의 기능을 지원합니다.
    """
    
    def __init__(self):
        """
        수동 거래 관리자 초기화
        """
        self.ingester = ManualIngester()
        self.repository = TransactionRepository()
        
        # 기본 카테고리 및 결제 방식
        self.expense_categories = self.ingester.get_categories('expense')
        self.income_categories = self.ingester.get_categories('income')
        self.expense_payment_methods = self.ingester.get_payment_methods('expense')
        self.income_payment_methods = self.ingester.get_payment_methods('income')
    
    def add_expense(self) -> Dict[str, Any]:
        """
        수동으로 지출 거래를 추가합니다.
        
        Returns:
            Dict[str, Any]: 추가된 거래 데이터
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
                return {}
            
            # 자동완성 제안 확인
            suggestions = self.ingester.get_autocomplete_suggestions(description, 'expense')
            if suggestions['exact_match'] or suggestions['similar_descriptions']:
                print("\n유사한 거래 기록이 있습니다:")
                if suggestions['exact_match']:
                    print(f"  - 카테고리: {suggestions['category']}")
                    print(f"  - 결제방식: {suggestions['payment_method']}")
                    use_suggestion = input("이 정보를 사용하시겠습니까? (y/n): ").strip().lower() == 'y'
                    if use_suggestion:
                        suggested_category = suggestions['category']
                        suggested_payment_method = suggestions['payment_method']
                elif suggestions['similar_descriptions']:
                    print("유사한 설명:")
                    for i, desc in enumerate(suggestions['similar_descriptions'], 1):
                        print(f"  {i}. {desc}")
            
            amount_input = input("금액 (원): ").strip()
            try:
                amount = float(amount_input)
                if amount <= 0:
                    print("금액은 0보다 큰 값이어야 합니다.")
                    return {}
            except ValueError:
                print("올바른 금액을 입력해주세요.")
                return {}
            
            # 결제 방식 선택
            print("\n결제 방식을 선택하세요:")
            for i, method in enumerate(self.expense_payment_methods, 1):
                print(f"{i}. {method}")
            
            payment_choice = input(f"선택 (1-{len(self.expense_payment_methods)}): ").strip()
            try:
                payment_method = self.expense_payment_methods[int(payment_choice) - 1]
            except (ValueError, IndexError):
                payment_method = '기타'
            
            # 카테고리 선택
            print("\n카테고리를 선택하세요:")
            for i, cat in enumerate(self.expense_categories, 1):
                print(f"{i}. {cat}")
            
            cat_choice = input(f"선택 (1-{len(self.expense_categories)}): ").strip()
            try:
                category = self.expense_categories[int(cat_choice) - 1]
            except (ValueError, IndexError):
                category = '기타'
            
            memo = input("메모 (선택사항): ").strip()
            
            # 템플릿으로 저장 여부 확인
            save_as_template = input("\n이 거래를 템플릿으로 저장하시겠습니까? (y/n): ").strip().lower() == 'y'
            if save_as_template:
                template_name = input("템플릿 이름: ").strip()
                if template_name:
                    template_data = {
                        'description': description,
                        'category': category,
                        'payment_method': payment_method,
                        'memo': memo
                    }
                    self.ingester.save_template(template_name, template_data, 'expense')
                    print(f"템플릿 '{template_name}'이(가) 저장되었습니다.")
            
            # 거래 추가
            transaction_data = self.ingester.add_expense(
                transaction_date=transaction_date,
                description=description,
                amount=amount,
                category=category,
                payment_method=payment_method,
                memo=memo
            )
            
            # 데이터베이스에 저장
            transaction = Transaction.from_dict(transaction_data)
            self.repository.create(transaction)
            
            print(f"\n✅ 지출 내역이 성공적으로 추가되었습니다!")
            print(f"   날짜: {transaction_date}")
            print(f"   내용: {description}")
            print(f"   금액: {amount:,}원")
            print(f"   결제방식: {payment_method}")
            print(f"   카테고리: {category}")
            
            return transaction_data
            
        except KeyboardInterrupt:
            print("\n\n취소되었습니다.")
            return {}
        except Exception as e:
            logger.error(f"오류가 발생했습니다: {e}")
            print(f"오류가 발생했습니다: {e}")
            return {}
    
    def add_income(self) -> Dict[str, Any]:
        """
        수동으로 수입 거래를 추가합니다.
        
        Returns:
            Dict[str, Any]: 추가된 거래 데이터
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
                return {}
            
            # 자동완성 제안 확인
            suggestions = self.ingester.get_autocomplete_suggestions(description, 'income')
            if suggestions['exact_match'] or suggestions['similar_descriptions']:
                print("\n유사한 거래 기록이 있습니다:")
                if suggestions['exact_match']:
                    print(f"  - 카테고리: {suggestions['category']}")
                    print(f"  - 입금방식: {suggestions['payment_method']}")
                    use_suggestion = input("이 정보를 사용하시겠습니까? (y/n): ").strip().lower() == 'y'
                    if use_suggestion:
                        suggested_category = suggestions['category']
                        suggested_payment_method = suggestions['payment_method']
                elif suggestions['similar_descriptions']:
                    print("유사한 설명:")
                    for i, desc in enumerate(suggestions['similar_descriptions'], 1):
                        print(f"  {i}. {desc}")
            
            amount_input = input("금액 (원): ").strip()
            try:
                amount = float(amount_input)
                if amount <= 0:
                    print("금액은 0보다 큰 값이어야 합니다.")
                    return {}
            except ValueError:
                print("올바른 금액을 입력해주세요.")
                return {}
            
            # 입금 방식 선택
            print("\n입금 방식을 선택하세요:")
            for i, method in enumerate(self.income_payment_methods, 1):
                print(f"{i}. {method}")
            
            payment_choice = input(f"선택 (1-{len(self.income_payment_methods)}): ").strip()
            try:
                payment_method = self.income_payment_methods[int(payment_choice) - 1]
            except (ValueError, IndexError):
                payment_method = '계좌입금'
            
            # 수입 유형 선택
            print("\n수입 유형을 선택하세요:")
            for i, cat in enumerate(self.income_categories, 1):
                print(f"{i}. {cat}")
            
            cat_choice = input(f"선택 (1-{len(self.income_categories)}): ").strip()
            try:
                category = self.income_categories[int(cat_choice) - 1]
            except (ValueError, IndexError):
                category = '기타수입'
            
            memo = input("메모 (선택사항): ").strip()
            
            # 템플릿으로 저장 여부 확인
            save_as_template = input("\n이 거래를 템플릿으로 저장하시겠습니까? (y/n): ").strip().lower() == 'y'
            if save_as_template:
                template_name = input("템플릿 이름: ").strip()
                if template_name:
                    template_data = {
                        'description': description,
                        'category': category,
                        'payment_method': payment_method,
                        'memo': memo
                    }
                    self.ingester.save_template(template_name, template_data, 'income')
                    print(f"템플릿 '{template_name}'이(가) 저장되었습니다.")
            
            # 거래 추가
            transaction_data = self.ingester.add_income(
                transaction_date=transaction_date,
                description=description,
                amount=amount,
                category=category,
                payment_method=payment_method,
                memo=memo
            )
            
            # 데이터베이스에 저장
            transaction = Transaction.from_dict(transaction_data)
            self.repository.create(transaction)
            
            print(f"\n✅ 수입 내역이 성공적으로 추가되었습니다!")
            print(f"   날짜: {transaction_date}")
            print(f"   내용: {description}")
            print(f"   금액: {amount:,}원")
            print(f"   입금방식: {payment_method}")
            print(f"   수입유형: {category}")
            
            return transaction_data
            
        except KeyboardInterrupt:
            print("\n\n취소되었습니다.")
            return {}
        except Exception as e:
            logger.error(f"오류가 발생했습니다: {e}")
            print(f"오류가 발생했습니다: {e}")
            return {}
    
    def batch_add_transactions(self) -> List[Dict[str, Any]]:
        """
        여러 거래를 한번에 추가합니다.
        
        Returns:
            List[Dict[str, Any]]: 추가된 거래 데이터 목록
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
                memo = parts[6].strip() if len(parts) > 6 else ''
                
                transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                transactions.append({
                    'transaction_date': transaction_date,
                    'description': description,
                    'amount': amount,
                    'transaction_type': transaction_type,
                    'payment_method': payment_method,
                    'category': category,
                    'memo': memo
                })
                
            except ValueError as e:
                print(f"입력 오류: {e}")
            except Exception as e:
                print(f"입력 오류: {e}")
        
        if not transactions:
            print("추가할 거래가 없습니다.")
            return []
        
        try:
            # 일괄 추가
            transaction_data_list = self.ingester.batch_add_transactions(transactions)
            
            # 데이터베이스에 저장
            saved_count = 0
            
            for transaction_data in transaction_data_list:
                transaction = Transaction.from_dict(transaction_data)
                self.repository.create(transaction)
                saved_count += 1
            
            print(f"\n✅ {saved_count}개의 거래 내역이 성공적으로 추가되었습니다!")
            
            return transaction_data_list
            
        except Exception as e:
            logger.error(f"오류가 발생했습니다: {e}")
            print(f"오류가 발생했습니다: {e}")
            return []
    
    def use_template(self) -> Dict[str, Any]:
        """
        템플릿을 사용하여 거래를 추가합니다.
        
        Returns:
            Dict[str, Any]: 추가된 거래 데이터
        """
        print("=== 템플릿으로 거래 추가 ===")
        
        try:
            # 거래 유형 선택
            print("거래 유형을 선택하세요:")
            print("1. 지출")
            print("2. 수입")
            
            type_choice = input("선택 (1-2): ").strip()
            transaction_type = 'expense' if type_choice != '2' else 'income'
            
            # 템플릿 목록 표시
            templates = self.ingester.get_templates(transaction_type)
            
            if not templates:
                print(f"저장된 {transaction_type} 템플릿이 없습니다.")
                return {}
            
            print(f"\n사용 가능한 {transaction_type} 템플릿:")
            template_names = list(templates.keys())
            
            for i, name in enumerate(template_names, 1):
                template = templates[name]
                print(f"{i}. {name}: {template['description']} ({template['category']})")
            
            template_choice = input(f"선택 (1-{len(template_names)}): ").strip()
            try:
                template_name = template_names[int(template_choice) - 1]
            except (ValueError, IndexError):
                print("올바른 템플릿을 선택해주세요.")
                return {}
            
            # 날짜 입력
            date_input = input("거래 날짜 (YYYY-MM-DD 형식, 엔터시 오늘): ").strip()
            if not date_input:
                transaction_date = datetime.now().date()
            else:
                transaction_date = datetime.strptime(date_input, '%Y-%m-%d').date()
            
            # 금액 입력
            amount_input = input("금액 (원): ").strip()
            try:
                amount = float(amount_input)
                if amount <= 0:
                    print("금액은 0보다 큰 값이어야 합니다.")
                    return {}
            except ValueError:
                print("올바른 금액을 입력해주세요.")
                return {}
            
            # 메모 입력
            memo = input("메모 (선택사항): ").strip()
            
            # 템플릿 적용
            transaction_data = self.ingester.apply_template(
                template_name=template_name,
                transaction_date=transaction_date,
                amount=amount,
                memo=memo,
                transaction_type=transaction_type
            )
            
            if not transaction_data:
                print("템플릿 적용 중 오류가 발생했습니다.")
                return {}
            
            # 데이터베이스에 저장
            transaction = Transaction.from_dict(transaction_data)
            self.repository.create(transaction)
            
            print(f"\n✅ 템플릿을 사용하여 거래가 성공적으로 추가되었습니다!")
            print(f"   날짜: {transaction_date}")
            print(f"   내용: {transaction_data['description']}")
            print(f"   금액: {amount:,}원")
            print(f"   카테고리: {transaction_data['category']}")
            
            return transaction_data
            
        except KeyboardInterrupt:
            print("\n\n취소되었습니다.")
            return {}
        except Exception as e:
            logger.error(f"오류가 발생했습니다: {e}")
            print(f"오류가 발생했습니다: {e}")
            return {}
    
    def manage_templates(self) -> None:
        """
        템플릿을 관리합니다.
        """
        print("=== 템플릿 관리 ===")
        
        try:
            while True:
                print("\n1. 템플릿 목록 보기")
                print("2. 템플릿 삭제")
                print("3. 새 템플릿 추가")
                print("4. 돌아가기")
                
                choice = input("선택 (1-4): ").strip()
                
                if choice == '1':
                    self._list_templates()
                elif choice == '2':
                    self._delete_template()
                elif choice == '3':
                    self._add_template()
                elif choice == '4':
                    break
                else:
                    print("올바른 옵션을 선택해주세요.")
            
        except KeyboardInterrupt:
            print("\n\n취소되었습니다.")
        except Exception as e:
            logger.error(f"오류가 발생했습니다: {e}")
            print(f"오류가 발생했습니다: {e}")
    
    def _list_templates(self) -> None:
        """
        템플릿 목록을 표시합니다.
        """
        # 거래 유형 선택
        print("거래 유형을 선택하세요:")
        print("1. 지출")
        print("2. 수입")
        
        type_choice = input("선택 (1-2): ").strip()
        transaction_type = 'expense' if type_choice != '2' else 'income'
        
        # 템플릿 목록 표시
        templates = self.ingester.get_templates(transaction_type)
        
        if not templates:
            print(f"저장된 {transaction_type} 템플릿이 없습니다.")
            return
        
        print(f"\n{transaction_type} 템플릿 목록:")
        for name, template in templates.items():
            print(f"- {name}:")
            print(f"  내용: {template['description']}")
            print(f"  카테고리: {template['category']}")
            print(f"  결제방식: {template['payment_method']}")
            if template.get('memo'):
                print(f"  메모: {template['memo']}")
            print()
    
    def _delete_template(self) -> None:
        """
        템플릿을 삭제합니다.
        """
        # 거래 유형 선택
        print("거래 유형을 선택하세요:")
        print("1. 지출")
        print("2. 수입")
        
        type_choice = input("선택 (1-2): ").strip()
        transaction_type = 'expense' if type_choice != '2' else 'income'
        
        # 템플릿 목록 표시
        templates = self.ingester.get_templates(transaction_type)
        
        if not templates:
            print(f"저장된 {transaction_type} 템플릿이 없습니다.")
            return
        
        print(f"\n{transaction_type} 템플릿 목록:")
        template_names = list(templates.keys())
        
        for i, name in enumerate(template_names, 1):
            template = templates[name]
            print(f"{i}. {name}: {template['description']} ({template['category']})")
        
        template_choice = input(f"삭제할 템플릿 선택 (1-{len(template_names)}): ").strip()
        try:
            template_name = template_names[int(template_choice) - 1]
        except (ValueError, IndexError):
            print("올바른 템플릿을 선택해주세요.")
            return
        
        # 삭제 확인
        confirm = input(f"템플릿 '{template_name}'을(를) 삭제하시겠습니까? (y/n): ").strip().lower() == 'y'
        if confirm:
            if self.ingester.delete_template(template_name, transaction_type):
                print(f"템플릿 '{template_name}'이(가) 삭제되었습니다.")
            else:
                print("템플릿 삭제 중 오류가 발생했습니다.")
    
    def _add_template(self) -> None:
        """
        새 템플릿을 추가합니다.
        """
        # 거래 유형 선택
        print("거래 유형을 선택하세요:")
        print("1. 지출")
        print("2. 수입")
        
        type_choice = input("선택 (1-2): ").strip()
        transaction_type = 'expense' if type_choice != '2' else 'income'
        
        # 템플릿 정보 입력
        template_name = input("템플릿 이름: ").strip()
        if not template_name:
            print("템플릿 이름은 필수입니다.")
            return
        
        description = input("거래 내용: ").strip()
        if not description:
            print("거래 내용은 필수입니다.")
            return
        
        # 카테고리 및 결제 방식 선택
        if transaction_type == 'expense':
            categories = self.expense_categories
            payment_methods = self.expense_payment_methods
        else:
            categories = self.income_categories
            payment_methods = self.income_payment_methods
        
        # 카테고리 선택
        print("\n카테고리를 선택하세요:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")
        
        cat_choice = input(f"선택 (1-{len(categories)}): ").strip()
        try:
            category = categories[int(cat_choice) - 1]
        except (ValueError, IndexError):
            category = '기타' if transaction_type == 'expense' else '기타수입'
        
        # 결제 방식 선택
        print("\n결제 방식을 선택하세요:")
        for i, method in enumerate(payment_methods, 1):
            print(f"{i}. {method}")
        
        payment_choice = input(f"선택 (1-{len(payment_methods)}): ").strip()
        try:
            payment_method = payment_methods[int(payment_choice) - 1]
        except (ValueError, IndexError):
            payment_method = '기타' if transaction_type == 'expense' else '계좌입금'
        
        memo = input("메모 (선택사항): ").strip()
        
        # 템플릿 저장
        template_data = {
            'description': description,
            'category': category,
            'payment_method': payment_method,
            'memo': memo
        }
        
        if self.ingester.save_template(template_name, template_data, transaction_type):
            print(f"템플릿 '{template_name}'이(가) 저장되었습니다.")
        else:
            print("템플릿 저장 중 오류가 발생했습니다.")
    
    def search_transactions(self) -> List[Dict[str, Any]]:
        """
        거래를 검색합니다.
        
        Returns:
            List[Dict[str, Any]]: 검색된 거래 데이터 목록
        """
        print("=== 거래 검색 ===")
        
        try:
            # 검색 조건 입력
            print("\n검색 조건을 입력하세요 (비워두면 모든 조건 무시):")
            
            # 날짜 범위
            start_date_input = input("시작 날짜 (YYYY-MM-DD): ").strip()
            end_date_input = input("종료 날짜 (YYYY-MM-DD): ").strip()
            
            start_date = None
            end_date = None
            
            if start_date_input:
                start_date = datetime.strptime(start_date_input, '%Y-%m-%d').date()
            
            if end_date_input:
                end_date = datetime.strptime(end_date_input, '%Y-%m-%d').date()
            
            # 거래 유형
            print("\n거래 유형을 선택하세요:")
            print("1. 지출")
            print("2. 수입")
            print("3. 모두")
            
            type_choice = input("선택 (1-3): ").strip()
            if type_choice == '1':
                transaction_type = 'expense'
            elif type_choice == '2':
                transaction_type = 'income'
            else:
                transaction_type = None
            
            # 금액 범위
            min_amount_input = input("최소 금액: ").strip()
            max_amount_input = input("최대 금액: ").strip()
            
            min_amount = float(min_amount_input) if min_amount_input else None
            max_amount = float(max_amount_input) if max_amount_input else None
            
            # 설명 검색
            description_search = input("설명 검색어: ").strip()
            
            # 카테고리 검색
            category_search = input("카테고리 검색어: ").strip()
            
            # 검색 실행
            search_params = {}
            
            if start_date:
                search_params['start_date'] = start_date
            
            if end_date:
                search_params['end_date'] = end_date
            
            if transaction_type:
                search_params['transaction_type'] = transaction_type
            
            if min_amount is not None:
                search_params['min_amount'] = min_amount
            
            if max_amount is not None:
                search_params['max_amount'] = max_amount
            
            if description_search:
                search_params['description'] = description_search
            
            if category_search:
                search_params['category'] = category_search
            
            # 검색 결과 가져오기
            transactions = self.repository.search(**search_params)
            
            if not transactions:
                print("검색 결과가 없습니다.")
                return []
            
            # 검색 결과 표시
            print(f"\n검색 결과: {len(transactions)}개의 거래 발견")
            
            for i, transaction in enumerate(transactions, 1):
                transaction_dict = transaction.to_dict()
                print(f"{i}. {transaction_dict['transaction_date']} | "
                      f"{transaction_dict['description']} | "
                      f"{transaction_dict['amount']}원 | "
                      f"{transaction_dict['category']} | "
                      f"{transaction_dict['payment_method']}")
            
            # 상세 정보 보기
            while True:
                detail_input = input("\n상세 정보를 볼 거래 번호 (0: 종료): ").strip()
                if not detail_input or detail_input == '0':
                    break
                
                try:
                    index = int(detail_input) - 1
                    if 0 <= index < len(transactions):
                        transaction_dict = transactions[index].to_dict()
                        print("\n=== 거래 상세 정보 ===")
                        print(f"ID: {transaction_dict['transaction_id']}")
                        print(f"날짜: {transaction_dict['transaction_date']}")
                        print(f"내용: {transaction_dict['description']}")
                        print(f"금액: {transaction_dict['amount']}원")
                        print(f"유형: {transaction_dict['transaction_type']}")
                        print(f"카테고리: {transaction_dict['category']}")
                        print(f"결제방식: {transaction_dict['payment_method']}")
                        print(f"소스: {transaction_dict['source']}")
                        print(f"계좌유형: {transaction_dict['account_type']}")
                        if transaction_dict['memo']:
                            print(f"메모: {transaction_dict['memo']}")
                        print(f"생성일시: {transaction_dict['created_at']}")
                        print(f"수정일시: {transaction_dict['updated_at']}")
                    else:
                        print("올바른 거래 번호를 입력해주세요.")
                except ValueError:
                    print("숫자를 입력해주세요.")
            
            return [t.to_dict() for t in transactions]
            
        except KeyboardInterrupt:
            print("\n\n취소되었습니다.")
            return []
        except Exception as e:
            logger.error(f"오류가 발생했습니다: {e}")
            print(f"오류가 발생했습니다: {e}")
            return []
    
    def edit_transaction(self) -> Dict[str, Any]:
        """
        거래를 편집합니다.
        
        Returns:
            Dict[str, Any]: 편집된 거래 데이터
        """
        print("=== 거래 편집 ===")
        
        try:
            # 거래 ID 입력
            transaction_id = input("편집할 거래 ID: ").strip()
            if not transaction_id:
                print("거래 ID는 필수입니다.")
                return {}
            
            # 거래 조회
            transaction = self.repository.get_by_transaction_id(transaction_id)
            if not transaction:
                print(f"ID가 '{transaction_id}'인 거래를 찾을 수 없습니다.")
                return {}
            
            transaction_dict = transaction.to_dict()
            
            print("\n=== 현재 거래 정보 ===")
            print(f"날짜: {transaction_dict['transaction_date']}")
            print(f"내용: {transaction_dict['description']}")
            print(f"금액: {transaction_dict['amount']}원")
            print(f"유형: {transaction_dict['transaction_type']}")
            print(f"카테고리: {transaction_dict['category']}")
            print(f"결제방식: {transaction_dict['payment_method']}")
            if transaction_dict['memo']:
                print(f"메모: {transaction_dict['memo']}")
            
            print("\n편집할 필드를 선택하세요:")
            print("1. 카테고리")
            print("2. 결제방식")
            print("3. 메모")
            print("4. 분석 제외 여부")
            print("5. 취소")
            
            choice = input("선택 (1-5): ").strip()
            
            if choice == '1':
                # 카테고리 편집
                categories = self.expense_categories if transaction_dict['transaction_type'] == 'expense' else self.income_categories
                
                print("\n카테고리를 선택하세요:")
                for i, cat in enumerate(categories, 1):
                    print(f"{i}. {cat}")
                
                cat_choice = input(f"선택 (1-{len(categories)}): ").strip()
                try:
                    category = categories[int(cat_choice) - 1]
                    transaction.update_category(category)
                    self.repository.update(transaction)
                    print(f"카테고리가 '{category}'(으)로 업데이트되었습니다.")
                except (ValueError, IndexError):
                    print("올바른 카테고리를 선택해주세요.")
                    return {}
                
            elif choice == '2':
                # 결제방식 편집
                payment_methods = self.expense_payment_methods if transaction_dict['transaction_type'] == 'expense' else self.income_payment_methods
                
                print("\n결제방식을 선택하세요:")
                for i, method in enumerate(payment_methods, 1):
                    print(f"{i}. {method}")
                
                payment_choice = input(f"선택 (1-{len(payment_methods)}): ").strip()
                try:
                    payment_method = payment_methods[int(payment_choice) - 1]
                    transaction.update_payment_method(payment_method)
                    self.repository.update(transaction)
                    print(f"결제방식이 '{payment_method}'(으)로 업데이트되었습니다.")
                except (ValueError, IndexError):
                    print("올바른 결제방식을 선택해주세요.")
                    return {}
                
            elif choice == '3':
                # 메모 편집
                current_memo = transaction_dict['memo'] or '(없음)'
                print(f"현재 메모: {current_memo}")
                
                new_memo = input("새 메모: ").strip()
                transaction.update_memo(new_memo)
                self.repository.update(transaction)
                print("메모가 업데이트되었습니다.")
                
            elif choice == '4':
                # 분석 제외 여부 편집
                current_status = "제외됨" if transaction_dict['is_excluded'] else "포함됨"
                print(f"현재 상태: 분석에 {current_status}")
                
                exclude = input("분석에서 제외하시겠습니까? (y/n): ").strip().lower() == 'y'
                transaction.exclude_from_analysis(exclude)
                self.repository.update(transaction)
                
                new_status = "제외됨" if exclude else "포함됨"
                print(f"상태가 업데이트되었습니다: 분석에 {new_status}")
                
            elif choice == '5':
                print("편집이 취소되었습니다.")
                return {}
            
            else:
                print("올바른 옵션을 선택해주세요.")
                return {}
            
            # 업데이트된 거래 반환
            updated_transaction = self.repository.get_by_transaction_id(transaction_id)
            return updated_transaction.to_dict() if updated_transaction else {}
            
        except KeyboardInterrupt:
            print("\n\n취소되었습니다.")
            return {}
        except Exception as e:
            logger.error(f"오류가 발생했습니다: {e}")
            print(f"오류가 발생했습니다: {e}")
            return {}

def setup_argparse() -> argparse.ArgumentParser:
    """
    명령줄 인자 파서를 설정합니다.
    
    Returns:
        argparse.ArgumentParser: 설정된 인자 파서
    """
    parser = argparse.ArgumentParser(description='수동 거래 관리 도구')
    
    parser.add_argument('--action', '-a', choices=['expense', 'income', 'batch', 'template', 'manage-templates', 'search', 'edit'],
                       default='expense', help='수행할 작업 (기본값: expense)')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 로깅 활성화')
    
    return parser

def main():
    """
    메인 함수
    """
    parser = setup_argparse()
    args = parser.parse_args()
    
    # 상세 로깅 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 거래 관리자 초기화
    manager = ManualTransactionManager()
    
    # 작업 수행
    if args.action == 'expense':
        manager.add_expense()
    elif args.action == 'income':
        manager.add_income()
    elif args.action == 'batch':
        manager.batch_add_transactions()
    elif args.action == 'template':
        manager.use_template()
    elif args.action == 'manage-templates':
        manager.manage_templates()
    elif args.action == 'search':
        manager.search_transactions()
    elif args.action == 'edit':
        manager.edit_transaction()
    else:
        print("지원되지 않는 작업입니다.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n프로그램이 중단되었습니다.")
    except Exception as e:
        logger.error(f"예기치 않은 오류가 발생했습니다: {e}")
print(f"예기치 않은 오류가 발생했습니다: {e}")
