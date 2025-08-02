# -*- coding: utf-8 -*-
"""
ManualIngester 클래스 정의

수동으로 입력된 거래 데이터를 처리하는 데이터 수집기입니다.
지출 및 수입 거래를 모두 지원하며, 자동완성 및 템플릿 기능을 제공합니다.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
import logging
import uuid
import json
import os
from pathlib import Path

from .base_ingester import BaseIngester

# 로깅 설정
logger = logging.getLogger(__name__)

class ManualIngester(BaseIngester):
    """
    수동 입력 데이터 수집기
    
    사용자가 수동으로 입력한 거래 데이터를 처리합니다.
    지출 및 수입 거래를 모두 지원하며, 자동완성 및 템플릿 기능을 제공합니다.
    """
    
    # 기본 카테고리 및 결제 방식 정의
    DEFAULT_EXPENSE_CATEGORIES = [
        '식비', '교통비', '생활용품/식료품', '카페/음료', 
        '의료비', '통신비', '공과금', '문화/오락', 
        '의류/패션', '온라인쇼핑', '현금인출', '해외결제',
        '간편결제', '기타'
    ]
    
    DEFAULT_INCOME_CATEGORIES = [
        '급여', '용돈', '이자', '환급', '부수입', '임대수입', 
        '판매수입', '기타수입'
    ]
    
    DEFAULT_EXPENSE_PAYMENT_METHODS = [
        '현금', '체크카드결제', '계좌이체', '토스페이', '기타카드', '기타'
    ]
    
    DEFAULT_INCOME_PAYMENT_METHODS = [
        '계좌입금', '현금', '급여이체', '이자입금', '기타입금'
    ]
    
    # 템플릿 저장 경로
    TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'templates')
    
    def __init__(self, name: str = "수동 입력", description: str = "수동으로 입력된 거래 데이터 수집기"):
        """
        수동 입력 수집기 초기화
        
        Args:
            name: 수집기 이름 (기본값: "수동 입력")
            description: 수집기 설명 (기본값: "수동으로 입력된 거래 데이터 수집기")
        """
        super().__init__(name, description)
        
        # 자동완성 데이터 저장소
        self.autocomplete_data = {
            'descriptions': {},  # 설명 -> 카테고리, 결제방식 매핑
            'frequent_descriptions': [],  # 자주 사용되는 설명
            'frequent_categories': {
                'expense': [],  # 자주 사용되는 지출 카테고리
                'income': []    # 자주 사용되는 수입 카테고리
            },
            'frequent_payment_methods': {
                'expense': [],  # 자주 사용되는 지출 결제 방식
                'income': []    # 자주 사용되는 수입 결제 방식
            }
        }
        
        # 템플릿 데이터
        self.templates = {
            'expense': {},  # 지출 템플릿
            'income': {}    # 수입 템플릿
        }
        
        # 자동완성 데이터 로드
        self._load_autocomplete_data()
        
        # 템플릿 데이터 로드
        self._load_templates()
        
        # 템플릿 디렉토리 생성
        os.makedirs(self.TEMPLATES_DIR, exist_ok=True)
    
    def validate_file(self, file_path: str) -> bool:
        """
        수동 입력은 파일 기반이 아니므로 항상 False를 반환합니다.
        
        Args:
            file_path: 검증할 파일 경로
            
        Returns:
            bool: 항상 False
        """
        logger.warning("수동 입력 수집기는 파일 기반 검증을 지원하지 않습니다.")
        return False
    
    def extract_transactions(self, file_path: str) -> List[Dict[str, Any]]:
        """
        수동 입력은 파일 기반이 아니므로 빈 리스트를 반환합니다.
        
        Args:
            file_path: 거래 데이터가 포함된 파일 경로
            
        Returns:
            List[Dict[str, Any]]: 빈 리스트
        """
        logger.warning("수동 입력 수집기는 파일 기반 추출을 지원하지 않습니다.")
        return []
    
    def normalize_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        수동 입력 데이터를 표준 형식으로 정규화합니다.
        
        Args:
            raw_data: 수동 입력된 원시 거래 데이터
            
        Returns:
            List[Dict[str, Any]]: 정규화된 거래 데이터 목록
        """
        logger.info("수동 입력 거래 데이터 정규화 시작")
        
        normalized_transactions = []
        
        for transaction in raw_data:
            try:
                # 필수 필드 확인
                if not all(key in transaction for key in ['transaction_date', 'description', 'amount', 'transaction_type']):
                    logger.warning(f"필수 필드가 누락되었습니다: {transaction}")
                    continue
                
                # 거래 ID 생성
                transaction_id = transaction.get('transaction_id') or f"MANUAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                
                # 정규화된 거래 데이터 생성
                normalized_transaction = {
                    'transaction_id': transaction_id,
                    'transaction_date': transaction['transaction_date'],
                    'description': transaction['description'],
                    'amount': Decimal(str(transaction['amount'])),
                    'transaction_type': transaction['transaction_type'],
                    'category': transaction.get('category', '기타' if transaction['transaction_type'] == 'expense' else '기타수입'),
                    'payment_method': transaction.get('payment_method', '기타'),
                    'source': 'manual_entry',
                    'account_type': '수동입력',
                    'memo': transaction.get('memo', ''),
                    'is_excluded': transaction.get('is_excluded', False)
                }
                
                # 데이터 유효성 검증
                if self.validate_data(normalized_transaction):
                    normalized_transactions.append(normalized_transaction)
                    
                    # 자동완성 데이터 업데이트
                    self._update_autocomplete_data(normalized_transaction)
                
            except Exception as e:
                logger.warning(f"거래 정규화 중 오류 발생: {e}, 거래: {transaction}")
        
        logger.info(f"{len(normalized_transactions)}개의 거래 데이터 정규화 완료")
        return normalized_transactions
    
    def add_expense(self, transaction_date: date, description: str, amount: float, 
                   category: str = '기타', payment_method: str = '현금', memo: str = '') -> Dict[str, Any]:
        """
        수동으로 지출 거래를 추가합니다.
        
        Args:
            transaction_date: 거래 날짜
            description: 거래 설명
            amount: 거래 금액
            category: 카테고리 (기본값: '기타')
            payment_method: 결제 방식 (기본값: '현금')
            memo: 메모 (기본값: '')
            
        Returns:
            Dict[str, Any]: 정규화된 거래 데이터
        """
        logger.info(f"수동 지출 추가: {description}, {amount}원")
        
        # 원시 데이터 생성
        raw_data = [{
            'transaction_date': transaction_date,
            'description': description,
            'amount': amount,
            'transaction_type': 'expense',
            'category': category,
            'payment_method': payment_method,
            'memo': memo
        }]
        
        # 데이터 정규화
        normalized_data = self.normalize_data(raw_data)
        
        if normalized_data:
            return normalized_data[0]
        else:
            logger.error("지출 추가 실패")
            return {}
    
    def add_income(self, transaction_date: date, description: str, amount: float, 
                  category: str = '기타수입', payment_method: str = '계좌입금', memo: str = '') -> Dict[str, Any]:
        """
        수동으로 수입 거래를 추가합니다.
        
        Args:
            transaction_date: 거래 날짜
            description: 거래 설명
            amount: 거래 금액
            category: 카테고리 (기본값: '기타수입')
            payment_method: 결제 방식 (기본값: '계좌입금')
            memo: 메모 (기본값: '')
            
        Returns:
            Dict[str, Any]: 정규화된 거래 데이터
        """
        logger.info(f"수동 수입 추가: {description}, {amount}원")
        
        # 원시 데이터 생성
        raw_data = [{
            'transaction_date': transaction_date,
            'description': description,
            'amount': amount,
            'transaction_type': 'income',
            'category': category,
            'payment_method': payment_method,
            'memo': memo
        }]
        
        # 데이터 정규화
        normalized_data = self.normalize_data(raw_data)
        
        if normalized_data:
            return normalized_data[0]
        else:
            logger.error("수입 추가 실패")
            return {}
    
    def batch_add_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        여러 거래를 일괄 추가합니다.
        
        Args:
            transactions: 추가할 거래 데이터 목록
            
        Returns:
            List[Dict[str, Any]]: 정규화된 거래 데이터 목록
        """
        logger.info(f"{len(transactions)}개의 거래 일괄 추가 시작")
        
        # 데이터 정규화
        normalized_data = self.normalize_data(transactions)
        
        logger.info(f"{len(normalized_data)}개의 거래 일괄 추가 완료")
        return normalized_data
    
    def get_autocomplete_suggestions(self, description: str, transaction_type: str = 'expense') -> Dict[str, Any]:
        """
        자동완성 제안을 제공합니다.
        
        Args:
            description: 거래 설명
            transaction_type: 거래 유형 (expense/income)
            
        Returns:
            Dict[str, Any]: 자동완성 제안 (카테고리, 결제 방식 등)
        """
        # 정확히 일치하는 설명이 있는 경우
        if description in self.autocomplete_data['descriptions']:
            data = self.autocomplete_data['descriptions'][description]
            if data['transaction_type'] == transaction_type:
                return {
                    'category': data['category'],
                    'payment_method': data['payment_method'],
                    'exact_match': True
                }
        
        # 부분 일치하는 설명 찾기
        matches = []
        for desc, data in self.autocomplete_data['descriptions'].items():
            if description.lower() in desc.lower() and data['transaction_type'] == transaction_type:
                matches.append((desc, data))
        
        if matches:
            # 가장 많이 사용된 항목 선택
            matches.sort(key=lambda x: x[1].get('count', 0), reverse=True)
            best_match = matches[0][1]
            
            return {
                'category': best_match['category'],
                'payment_method': best_match['payment_method'],
                'exact_match': False,
                'similar_descriptions': [m[0] for m in matches[:5]]  # 최대 5개의 유사 설명 제공
            }
        
        # 기본 제안
        return {
            'category': None,
            'payment_method': None,
            'exact_match': False,
            'similar_descriptions': []
        }
    
    def get_frequent_items(self, item_type: str, transaction_type: str = 'expense', limit: int = 5) -> List[str]:
        """
        자주 사용되는 항목 목록을 반환합니다.
        
        Args:
            item_type: 항목 유형 ('descriptions', 'categories', 'payment_methods')
            transaction_type: 거래 유형 (expense/income)
            limit: 반환할 항목 수
            
        Returns:
            List[str]: 자주 사용되는 항목 목록
        """
        if item_type == 'descriptions':
            return self.autocomplete_data['frequent_descriptions'][:limit]
        elif item_type == 'categories':
            return self.autocomplete_data['frequent_categories'][transaction_type][:limit]
        elif item_type == 'payment_methods':
            return self.autocomplete_data['frequent_payment_methods'][transaction_type][:limit]
        else:
            return []
    
    def get_templates(self, transaction_type: str = 'expense') -> Dict[str, Dict[str, Any]]:
        """
        저장된 템플릿 목록을 반환합니다.
        
        Args:
            transaction_type: 거래 유형 (expense/income)
            
        Returns:
            Dict[str, Dict[str, Any]]: 템플릿 목록
        """
        return self.templates[transaction_type]
    
    def save_template(self, name: str, template_data: Dict[str, Any], transaction_type: str = 'expense') -> bool:
        """
        새 템플릿을 저장합니다.
        
        Args:
            name: 템플릿 이름
            template_data: 템플릿 데이터
            transaction_type: 거래 유형 (expense/income)
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 필수 필드 확인
            required_fields = ['description', 'category', 'payment_method']
            if not all(field in template_data for field in required_fields):
                logger.warning(f"템플릿에 필수 필드가 누락되었습니다: {template_data}")
                return False
            
            # 템플릿 저장
            self.templates[transaction_type][name] = template_data
            
            # 템플릿 파일 저장
            self._save_templates()
            
            logger.info(f"템플릿 저장 완료: {name}")
            return True
            
        except Exception as e:
            logger.error(f"템플릿 저장 중 오류 발생: {e}")
            return False
    
    def delete_template(self, name: str, transaction_type: str = 'expense') -> bool:
        """
        템플릿을 삭제합니다.
        
        Args:
            name: 템플릿 이름
            transaction_type: 거래 유형 (expense/income)
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            if name in self.templates[transaction_type]:
                del self.templates[transaction_type][name]
                
                # 템플릿 파일 저장
                self._save_templates()
                
                logger.info(f"템플릿 삭제 완료: {name}")
                return True
            else:
                logger.warning(f"템플릿을 찾을 수 없습니다: {name}")
                return False
                
        except Exception as e:
            logger.error(f"템플릿 삭제 중 오류 발생: {e}")
            return False
    
    def apply_template(self, template_name: str, transaction_date: date, amount: float, 
                      memo: str = '', transaction_type: str = 'expense') -> Dict[str, Any]:
        """
        템플릿을 적용하여 거래를 생성합니다.
        
        Args:
            template_name: 템플릿 이름
            transaction_date: 거래 날짜
            amount: 거래 금액
            memo: 메모 (기본값: '')
            transaction_type: 거래 유형 (expense/income)
            
        Returns:
            Dict[str, Any]: 생성된 거래 데이터
        """
        try:
            if template_name not in self.templates[transaction_type]:
                logger.warning(f"템플릿을 찾을 수 없습니다: {template_name}")
                return {}
            
            template = self.templates[transaction_type][template_name]
            
            # 템플릿 적용
            if transaction_type == 'expense':
                return self.add_expense(
                    transaction_date=transaction_date,
                    description=template['description'],
                    amount=amount,
                    category=template['category'],
                    payment_method=template['payment_method'],
                    memo=memo or template.get('memo', '')
                )
            else:  # income
                return self.add_income(
                    transaction_date=transaction_date,
                    description=template['description'],
                    amount=amount,
                    category=template['category'],
                    payment_method=template['payment_method'],
                    memo=memo or template.get('memo', '')
                )
                
        except Exception as e:
            logger.error(f"템플릿 적용 중 오류 발생: {e}")
            return {}
    
    def get_supported_file_types(self) -> List[str]:
        """
        지원하는 파일 유형 목록을 반환합니다.
        
        Returns:
            List[str]: 지원하는 파일 확장자 목록
        """
        return []  # 파일 기반이 아니므로 빈 리스트 반환
    
    def get_required_fields(self) -> List[str]:
        """
        필수 데이터 필드 목록을 반환합니다.
        
        Returns:
            List[str]: 필수 필드 목록
        """
        return [
            'transaction_id',
            'transaction_date',
            'description',
            'amount',
            'transaction_type',
            'source'
        ]
    
    def get_categories(self, transaction_type: str = 'expense') -> List[str]:
        """
        사용 가능한 카테고리 목록을 반환합니다.
        
        Args:
            transaction_type: 거래 유형 (expense/income)
            
        Returns:
            List[str]: 카테고리 목록
        """
        if transaction_type == 'expense':
            return self.DEFAULT_EXPENSE_CATEGORIES
        else:  # income
            return self.DEFAULT_INCOME_CATEGORIES
    
    def get_payment_methods(self, transaction_type: str = 'expense') -> List[str]:
        """
        사용 가능한 결제 방식 목록을 반환합니다.
        
        Args:
            transaction_type: 거래 유형 (expense/income)
            
        Returns:
            List[str]: 결제 방식 목록
        """
        if transaction_type == 'expense':
            return self.DEFAULT_EXPENSE_PAYMENT_METHODS
        else:  # income
            return self.DEFAULT_INCOME_PAYMENT_METHODS
    
    def validate_data(self, transaction: Dict[str, Any]) -> bool:
        """
        거래 데이터의 유효성을 검증합니다.
        
        Args:
            transaction: 검증할 거래 데이터
            
        Returns:
            bool: 유효성 여부
        """
        try:
            # 필수 필드 확인
            required_fields = self.get_required_fields()
            for field in required_fields:
                if field not in transaction or transaction[field] is None:
                    logger.warning(f"필수 필드가 누락되었습니다: {field}")
                    return False
            
            # 거래 유형 확인
            if transaction['transaction_type'] not in ['expense', 'income']:
                logger.warning(f"유효하지 않은 거래 유형입니다: {transaction['transaction_type']}")
                return False
            
            # 금액 확인
            if transaction['amount'] <= 0:
                logger.warning(f"금액은 0보다 커야 합니다: {transaction['amount']}")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"데이터 검증 중 오류 발생: {e}")
            return False
    
    def _load_autocomplete_data(self) -> None:
        """
        자동완성 데이터를 로드합니다.
        """
        try:
            autocomplete_file = os.path.join(self.TEMPLATES_DIR, 'autocomplete_data.json')
            
            if os.path.exists(autocomplete_file):
                with open(autocomplete_file, 'r', encoding='utf-8') as f:
                    self.autocomplete_data = json.load(f)
                logger.info("자동완성 데이터 로드 완료")
            else:
                logger.info("자동완성 데이터 파일이 없습니다. 새로 생성합니다.")
                self._save_autocomplete_data()
                
        except Exception as e:
            logger.error(f"자동완성 데이터 로드 중 오류 발생: {e}")
    
    def _save_autocomplete_data(self) -> None:
        """
        자동완성 데이터를 저장합니다.
        """
        try:
            os.makedirs(self.TEMPLATES_DIR, exist_ok=True)
            autocomplete_file = os.path.join(self.TEMPLATES_DIR, 'autocomplete_data.json')
            
            with open(autocomplete_file, 'w', encoding='utf-8') as f:
                json.dump(self.autocomplete_data, f, ensure_ascii=False, indent=2)
            
            logger.info("자동완성 데이터 저장 완료")
            
        except Exception as e:
            logger.error(f"자동완성 데이터 저장 중 오류 발생: {e}")
    
    def _update_autocomplete_data(self, transaction: Dict[str, Any]) -> None:
        """
        거래 데이터를 기반으로 자동완성 데이터를 업데이트합니다.
        
        Args:
            transaction: 거래 데이터
        """
        try:
            description = transaction['description']
            transaction_type = transaction['transaction_type']
            category = transaction['category']
            payment_method = transaction['payment_method']
            
            # 설명 -> 카테고리, 결제방식 매핑 업데이트
            if description in self.autocomplete_data['descriptions']:
                data = self.autocomplete_data['descriptions'][description]
                data['count'] = data.get('count', 0) + 1
                
                # 같은 거래 유형인 경우에만 업데이트
                if data['transaction_type'] == transaction_type:
                    data['category'] = category
                    data['payment_method'] = payment_method
            else:
                self.autocomplete_data['descriptions'][description] = {
                    'transaction_type': transaction_type,
                    'category': category,
                    'payment_method': payment_method,
                    'count': 1
                }
            
            # 자주 사용되는 설명 업데이트
            self._update_frequent_list('descriptions', description)
            
            # 자주 사용되는 카테고리 업데이트
            self._update_frequent_list(f"categories_{transaction_type}", category)
            
            # 자주 사용되는 결제 방식 업데이트
            self._update_frequent_list(f"payment_methods_{transaction_type}", payment_method)
            
            # 자동완성 데이터 저장
            self._save_autocomplete_data()
            
        except Exception as e:
            logger.warning(f"자동완성 데이터 업데이트 중 오류 발생: {e}")
    
    def _update_frequent_list(self, list_type: str, value: str) -> None:
        """
        자주 사용되는 항목 목록을 업데이트합니다.
        
        Args:
            list_type: 목록 유형 ('descriptions', 'categories_expense', 'categories_income', 등)
            value: 추가할 값
        """
        if list_type == 'descriptions':
            target_list = self.autocomplete_data['frequent_descriptions']
        elif list_type == 'categories_expense':
            target_list = self.autocomplete_data['frequent_categories']['expense']
        elif list_type == 'categories_income':
            target_list = self.autocomplete_data['frequent_categories']['income']
        elif list_type == 'payment_methods_expense':
            target_list = self.autocomplete_data['frequent_payment_methods']['expense']
        elif list_type == 'payment_methods_income':
            target_list = self.autocomplete_data['frequent_payment_methods']['income']
        else:
            return
        
        # 이미 목록에 있으면 앞으로 이동
        if value in target_list:
            target_list.remove(value)
        
        # 목록 앞에 추가
        target_list.insert(0, value)
        
        # 최대 20개만 유지
        if len(target_list) > 20:
            target_list.pop()
    
    def _load_templates(self) -> None:
        """
        템플릿 데이터를 로드합니다.
        """
        try:
            templates_file = os.path.join(self.TEMPLATES_DIR, 'transaction_templates.json')
            
            if os.path.exists(templates_file):
                with open(templates_file, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
                logger.info("템플릿 데이터 로드 완료")
            else:
                logger.info("템플릿 데이터 파일이 없습니다. 새로 생성합니다.")
                self._save_templates()
                
        except Exception as e:
            logger.error(f"템플릿 데이터 로드 중 오류 발생: {e}")
    
    def _save_templates(self) -> None:
        """
        템플릿 데이터를 저장합니다.
        """
        try:
            os.makedirs(self.TEMPLATES_DIR, exist_ok=True)
            templates_file = os.path.join(self.TEMPLATES_DIR, 'transaction_templates.json')
            
            with open(templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
            
            logger.info("템플릿 데이터 저장 완료")
            
        except Exception as e:
            logger.error(f"템플릿 데이터 저장 중 오류 발생: {e}")