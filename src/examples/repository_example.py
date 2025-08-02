# -*- coding: utf-8 -*-
"""
Repository 패턴 사용 예제

이 모듈은 Repository 패턴을 사용하여 금융 거래 데이터를 관리하는 방법을 보여줍니다.
"""

import os
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

from src.models import Transaction, ClassificationRule, UserPreference, AnalysisFilter
from src.repositories.db_connection import DatabaseConnection
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.rule_repository import RuleRepository
from src.repositories.config_repository import UserPreferenceRepository, AnalysisFilterRepository

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinancialDataManager:
    """
    금융 데이터 관리 클래스
    
    Repository 패턴을 사용하여 금융 거래 데이터를 관리합니다.
    """
    
    def __init__(self, db_path: str):
        """
        금융 데이터 관리자 초기화
        
        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_connection = DatabaseConnection(db_path)
        self.transaction_repo = TransactionRepository(self.db_connection)
        self.rule_repo = RuleRepository(self.db_connection)
        self.preference_repo = UserPreferenceRepository(self.db_connection)
        self.filter_repo = AnalysisFilterRepository(self.db_connection)
        
        logger.info(f"금융 데이터 관리자 초기화 완료 (DB: {db_path})")
    
    def close(self):
        """데이터베이스 연결 종료"""
        self.db_connection.close()
        logger.info("데이터베이스 연결 종료")
    
    def add_transaction(self, transaction: Transaction) -> Transaction:
        """
        거래 추가
        
        Args:
            transaction: 추가할 거래 객체
            
        Returns:
            Transaction: 추가된 거래 객체
        """
        # 거래 추가
        created = self.transaction_repo.create(transaction)
        logger.info(f"거래 추가 완료: {created.description} ({created.amount})")
        
        # 자동 분류 규칙 적용
        self._apply_classification_rules(created)
        
        return created
    
    def add_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        여러 거래 일괄 추가
        
        Args:
            transactions: 추가할 거래 객체 목록
            
        Returns:
            List[Transaction]: 추가된 거래 객체 목록
        """
        # 거래 일괄 추가
        created = self.transaction_repo.bulk_create(transactions)
        logger.info(f"거래 {len(created)}개 일괄 추가 완료")
        
        # 자동 분류 규칙 적용
        for transaction in created:
            self._apply_classification_rules(transaction)
        
        return created
    
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """
        거래 ID로 거래 조회
        
        Args:
            transaction_id: 조회할 거래 ID
            
        Returns:
            Optional[Transaction]: 조회된 거래 또는 None
        """
        return self.transaction_repo.read_by_transaction_id(transaction_id)
    
    def update_transaction(self, transaction: Transaction) -> Transaction:
        """
        거래 업데이트
        
        Args:
            transaction: 업데이트할 거래 객체
            
        Returns:
            Transaction: 업데이트된 거래 객체
        """
        return self.transaction_repo.update(transaction)
    
    def delete_transaction(self, transaction_id: str) -> bool:
        """
        거래 ID로 거래 삭제
        
        Args:
            transaction_id: 삭제할 거래 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        transaction = self.transaction_repo.read_by_transaction_id(transaction_id)
        if transaction:
            return self.transaction_repo.delete(transaction.id)
        return False
    
    def get_transactions(self, filters: Optional[Dict[str, Any]] = None) -> List[Transaction]:
        """
        필터 조건에 맞는 거래 목록 조회
        
        Args:
            filters: 필터 조건 (선택)
            
        Returns:
            List[Transaction]: 조회된 거래 목록
        """
        return self.transaction_repo.list(filters)
    
    def add_classification_rule(self, rule: ClassificationRule) -> ClassificationRule:
        """
        분류 규칙 추가
        
        Args:
            rule: 추가할 분류 규칙 객체
            
        Returns:
            ClassificationRule: 추가된 분류 규칙 객체
        """
        return self.rule_repo.create(rule)
    
    def get_classification_rules(self, rule_type: Optional[str] = None) -> List[ClassificationRule]:
        """
        분류 규칙 목록 조회
        
        Args:
            rule_type: 규칙 유형 (선택)
            
        Returns:
            List[ClassificationRule]: 조회된 분류 규칙 목록
        """
        filters = {"is_active": True}
        if rule_type:
            filters["rule_type"] = rule_type
        
        return self.rule_repo.list(filters)
    
    def set_preference(self, key: str, value: str, description: Optional[str] = None) -> UserPreference:
        """
        사용자 설정 저장
        
        Args:
            key: 설정 키
            value: 설정 값
            description: 설정 설명 (선택)
            
        Returns:
            UserPreference: 저장된 사용자 설정 객체
        """
        return self.preference_repo.update_by_key(key, value, description)
    
    def get_preference(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        """
        사용자 설정 조회
        
        Args:
            key: 설정 키
            default_value: 기본값 (설정이 없는 경우)
            
        Returns:
            Optional[str]: 설정 값 또는 기본값
        """
        return self.preference_repo.get_value(key, default_value)
    
    def add_analysis_filter(self, filter_obj: AnalysisFilter) -> AnalysisFilter:
        """
        분석 필터 추가
        
        Args:
            filter_obj: 추가할 분석 필터 객체
            
        Returns:
            AnalysisFilter: 추가된 분석 필터 객체
        """
        return self.filter_repo.create(filter_obj)
    
    def get_analysis_filters(self) -> List[AnalysisFilter]:
        """
        분석 필터 목록 조회
        
        Returns:
            List[AnalysisFilter]: 조회된 분석 필터 목록
        """
        return self.filter_repo.list()
    
    def get_default_analysis_filter(self) -> Optional[AnalysisFilter]:
        """
        기본 분석 필터 조회
        
        Returns:
            Optional[AnalysisFilter]: 기본 분석 필터 또는 None
        """
        return self.filter_repo.get_default_filter()
    
    def _apply_classification_rules(self, transaction: Transaction) -> None:
        """
        거래에 분류 규칙 적용
        
        Args:
            transaction: 분류 규칙을 적용할 거래 객체
        """
        # 카테고리 규칙 적용
        if not transaction.category:
            category_rules = self.rule_repo.get_active_rules_by_type(ClassificationRule.TYPE_CATEGORY)
            for rule in category_rules:
                if rule.matches(transaction.to_dict()):
                    transaction.update_category(rule.target_value)
                    logger.info(f"카테고리 규칙 '{rule.rule_name}' 적용: {transaction.description} -> {rule.target_value}")
                    break
        
        # 결제 방식 규칙 적용
        if not transaction.payment_method:
            payment_rules = self.rule_repo.get_active_rules_by_type(ClassificationRule.TYPE_PAYMENT_METHOD)
            for rule in payment_rules:
                if rule.matches(transaction.to_dict()):
                    transaction.update_payment_method(rule.target_value)
                    logger.info(f"결제 방식 규칙 '{rule.rule_name}' 적용: {transaction.description} -> {rule.target_value}")
                    break
        
        # 변경된 거래 저장
        self.transaction_repo.update(transaction)


def main():
    """메인 함수"""
    # 데이터베이스 파일 경로
    db_path = "personal_data.db"
    
    # 금융 데이터 관리자 생성
    manager = FinancialDataManager(db_path)
    
    try:
        # 1. 분류 규칙 추가
        category_rule = ClassificationRule(
            rule_name="식비 규칙",
            rule_type=ClassificationRule.TYPE_CATEGORY,
            condition_type=ClassificationRule.CONDITION_CONTAINS,
            condition_value="식당",
            target_value="식비",
            priority=100
        )
        manager.add_classification_rule(category_rule)
        
        payment_rule = ClassificationRule(
            rule_name="신용카드 규칙",
            rule_type=ClassificationRule.TYPE_PAYMENT_METHOD,
            condition_type=ClassificationRule.CONDITION_CONTAINS,
            condition_value="카드",
            target_value="신용카드",
            priority=100
        )
        manager.add_classification_rule(payment_rule)
        
        # 2. 거래 추가
        transaction = Transaction(
            transaction_id="test-transaction-001",
            transaction_date=date.today(),
            description="맛있는 식당",
            amount=Decimal("25000"),
            transaction_type=Transaction.TYPE_EXPENSE,
            source="manual"
        )
        created_transaction = manager.add_transaction(transaction)
        
        # 3. 거래 조회
        retrieved_transaction = manager.get_transaction(created_transaction.transaction_id)
        if retrieved_transaction:
            print(f"조회된 거래: {retrieved_transaction}")
            print(f"카테고리: {retrieved_transaction.category}")
            print(f"결제 방식: {retrieved_transaction.payment_method}")
        
        # 4. 사용자 설정 저장
        manager.set_preference("display.currency", "KRW", "표시 통화")
        manager.set_preference("display.date_format", "YYYY-MM-DD", "날짜 표시 형식")
        
        # 5. 사용자 설정 조회
        currency = manager.get_preference("display.currency")
        date_format = manager.get_preference("display.date_format")
        print(f"표시 통화: {currency}")
        print(f"날짜 표시 형식: {date_format}")
        
        # 6. 분석 필터 추가
        filter_config = {
            "conditions": {
                "operator": "and",
                "conditions": [
                    {
                        "field": "category",
                        "comparison": "equals",
                        "value": "식비"
                    },
                    {
                        "field": "transaction_date",
                        "comparison": "greater_than",
                        "value": date.today().replace(day=1).isoformat()
                    }
                ]
            }
        }
        
        analysis_filter = AnalysisFilter(
            filter_name="이번 달 식비",
            filter_config=filter_config,
            is_default=True
        )
        manager.add_analysis_filter(analysis_filter)
        
        # 7. 기본 분석 필터 조회
        default_filter = manager.get_default_analysis_filter()
        if default_filter:
            print(f"기본 분석 필터: {default_filter.filter_name}")
        
    finally:
        # 데이터베이스 연결 종료
        manager.close()


if __name__ == "__main__":
    main()