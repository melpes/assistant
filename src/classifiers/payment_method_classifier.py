# -*- coding: utf-8 -*-
"""
결제 방식 분류기(PaymentMethodClassifier) 클래스

거래 내역을 결제 방식으로 자동 분류하는 분류기입니다.
"""

import logging
from typing import Dict, Any, Optional, List
from collections import defaultdict, Counter

from src.models import Transaction, ClassificationRule
from src.repositories.rule_repository import RuleRepository
from src.repositories.transaction_repository import TransactionRepository
from src.rule_engine import RuleEngine
from src.classifiers.base_classifier import BaseClassifier

# 로거 설정
logger = logging.getLogger(__name__)


class PaymentMethodClassifier(BaseClassifier):
    """
    결제 방식 분류기 클래스
    
    거래 내역을 결제 방식으로 자동 분류하는 분류기입니다.
    """
    
    # 기본 결제 방식 목록
    DEFAULT_PAYMENT_METHODS = [
        "체크카드결제", "ATM출금", "토스페이", "자동환전", 
        "계좌이체", "현금", "기타카드"
    ]
    
    # 규칙 유형
    RULE_TYPE = ClassificationRule.TYPE_PAYMENT_METHOD
    
    def __init__(
        self, 
        rule_engine: RuleEngine, 
        transaction_repository: Optional[TransactionRepository] = None
    ):
        """
        결제 방식 분류기 초기화
        
        Args:
            rule_engine: 규칙 엔진
            transaction_repository: 거래 저장소 (선택, 학습 기능에 사용)
        """
        self.rule_engine = rule_engine
        self.transaction_repository = transaction_repository
        self._accuracy_metrics = {
            'total_classified': 0,
            'rule_based_classifications': 0,
            'default_classifications': 0,
            'user_corrections': 0,
            'correction_patterns': defaultdict(int)
        }
        
        # 기본 결제 방식 규칙 초기화
        self._ensure_default_rules()
    
    def classify(self, transaction: Transaction) -> Optional[str]:
        """
        거래를 결제 방식으로 분류합니다.
        
        분류 우선순위:
        1. 사용자 정의 규칙
        2. 학습된 규칙
        3. 기본 규칙
        4. 소스 기반 기본값
        
        Args:
            transaction: 분류할 거래 객체
            
        Returns:
            str: 분류된 결제 방식
        """
        # 이미 결제 방식이 있으면 반환
        if transaction.payment_method:
            return transaction.payment_method
        
        # 규칙 엔진으로 분류 시도
        payment_method = self.rule_engine.apply_rules(transaction, self.RULE_TYPE)
        
        # 분류 결과 기록
        self._accuracy_metrics['total_classified'] += 1
        
        if payment_method:
            self._accuracy_metrics['rule_based_classifications'] += 1
            logger.debug(f"규칙 기반 분류: {transaction.description} -> {payment_method}")
            return payment_method
        
        # 소스 기반 기본값 할당
        self._accuracy_metrics['default_classifications'] += 1
        default_method = self._get_default_by_source(transaction.source)
        logger.debug(f"기본 결제 방식 할당: {transaction.description} -> {default_method}")
        return default_method
    
    def classify_batch(self, transactions: List[Transaction]) -> Dict[str, str]:
        """
        여러 거래를 일괄 분류합니다.
        
        Args:
            transactions: 분류할 거래 객체 목록
            
        Returns:
            Dict[str, str]: 거래 ID를 키로, 결제 방식을 값으로 하는 딕셔너리
        """
        # 이미 결제 방식이 있는 거래 필터링
        unclassified = [t for t in transactions if not t.payment_method]
        
        if not unclassified:
            return {}
        
        # 규칙 엔진으로 일괄 분류
        rule_results = self.rule_engine.apply_rules_batch(unclassified, self.RULE_TYPE)
        
        # 결과 통합
        results = {}
        for transaction in unclassified:
            # 규칙 기반 결과가 있으면 사용
            if transaction.transaction_id in rule_results:
                payment_method = rule_results[transaction.transaction_id]
                self._accuracy_metrics['rule_based_classifications'] += 1
            else:
                # 소스 기반 기본값 할당
                payment_method = self._get_default_by_source(transaction.source)
                self._accuracy_metrics['default_classifications'] += 1
            
            results[transaction.transaction_id] = payment_method
            self._accuracy_metrics['total_classified'] += 1
        
        logger.info(f"일괄 결제 방식 분류 완료: {len(results)}/{len(transactions)} 거래 분류됨")
        return results
    
    def learn_from_correction(self, transaction: Transaction, correct_payment_method: str) -> bool:
        """
        사용자 수정사항으로부터 학습합니다.
        
        Args:
            transaction: 수정된 거래 객체
            correct_payment_method: 올바른 결제 방식
            
        Returns:
            bool: 학습 성공 여부
        """
        if not correct_payment_method:
            logger.warning("학습 실패: 올바른 결제 방식이 제공되지 않았습니다")
            return False
        
        # 수정 패턴 기록
        prev_method = transaction.payment_method or "미분류"
        pattern = f"{prev_method} -> {correct_payment_method}"
        self._accuracy_metrics['user_corrections'] += 1
        self._accuracy_metrics['correction_patterns'][pattern] += 1
        
        # 유사한 거래 패턴 찾기
        if not self.transaction_repository:
            logger.warning("학습 제한: 거래 저장소가 제공되지 않았습니다")
            return self._create_simple_rule(transaction, correct_payment_method)
        
        # 소스 기반 규칙 생성
        if transaction.source:
            return self._create_source_based_rule(transaction, correct_payment_method)
        else:
            return self._create_simple_rule(transaction, correct_payment_method)
    
    def get_accuracy_metrics(self) -> Dict[str, Any]:
        """
        분류 정확도 지표를 반환합니다.
        
        Returns:
            Dict[str, Any]: 정확도 지표 정보
        """
        metrics = dict(self._accuracy_metrics)
        
        # 비율 계산
        total = metrics['total_classified']
        if total > 0:
            metrics['rule_based_ratio'] = metrics['rule_based_classifications'] / total
            metrics['default_ratio'] = metrics['default_classifications'] / total
            metrics['correction_ratio'] = metrics['user_corrections'] / total if metrics['user_corrections'] > 0 else 0
        
        # 가장 많은 수정 패턴
        correction_patterns = dict(metrics['correction_patterns'])
        metrics['top_correction_patterns'] = sorted(
            correction_patterns.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return metrics
    
    def get_available_payment_methods(self) -> List[str]:
        """
        사용 가능한 모든 결제 방식 목록을 반환합니다.
        
        Returns:
            List[str]: 결제 방식 목록
        """
        payment_methods = set(self.DEFAULT_PAYMENT_METHODS)
        
        # 규칙에서 사용 중인 결제 방식 추가
        rule_repo = self.rule_engine.rule_repository
        rules = rule_repo.list({'rule_type': self.RULE_TYPE})
        for rule in rules:
            payment_methods.add(rule.target_value)
        
        # 거래에서 사용 중인 결제 방식 추가
        if self.transaction_repository:
            db_methods = self.transaction_repository.get_payment_methods()
            payment_methods.update(db_methods)
        
        return sorted(list(payment_methods))
    
    def reset_metrics(self) -> None:
        """
        정확도 지표를 초기화합니다.
        """
        self._accuracy_metrics = {
            'total_classified': 0,
            'rule_based_classifications': 0,
            'default_classifications': 0,
            'user_corrections': 0,
            'correction_patterns': defaultdict(int)
        }
    
    def _ensure_default_rules(self) -> None:
        """
        기본 결제 방식 규칙을 초기화합니다.
        """
        rule_repo = self.rule_engine.rule_repository
        
        # 기본 규칙 정의
        default_rules = [
            # 토스뱅크 카드 관련 규칙
            {
                'rule_name': '체크카드-토스뱅크',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '토스뱅크카드',
                'target_value': '체크카드결제',
                'priority': 10
            },
            {
                'rule_name': '체크카드-일반',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '체크카드',
                'target_value': '체크카드결제',
                'priority': 10
            },
            
            # ATM 관련 규칙
            {
                'rule_name': 'ATM-출금',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': 'ATM',
                'target_value': 'ATM출금',
                'priority': 10
            },
            {
                'rule_name': 'ATM-현금인출',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '현금인출',
                'target_value': 'ATM출금',
                'priority': 10
            },
            
            # 토스페이 관련 규칙
            {
                'rule_name': '토스페이-결제',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '토스페이',
                'target_value': '토스페이',
                'priority': 10
            },
            
            # 계좌이체 관련 규칙
            {
                'rule_name': '계좌이체-일반',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '이체',
                'target_value': '계좌이체',
                'priority': 10
            },
            {
                'rule_name': '계좌이체-송금',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '송금',
                'target_value': '계좌이체',
                'priority': 10
            }
        ]
        
        # 기존 시스템 규칙 조회
        existing_rules = rule_repo.list({
            'rule_type': self.RULE_TYPE,
            'created_by': ClassificationRule.CREATOR_SYSTEM
        })
        existing_rule_names = {rule.rule_name for rule in existing_rules}
        
        # 없는 규칙만 추가
        rules_to_add = []
        for rule_data in default_rules:
            if rule_data['rule_name'] not in existing_rule_names:
                rule = ClassificationRule(
                    rule_type=self.RULE_TYPE,
                    created_by=ClassificationRule.CREATOR_SYSTEM,
                    **rule_data
                )
                rules_to_add.append(rule)
        
        # 일괄 추가
        if rules_to_add:
            rule_repo.bulk_create(rules_to_add)
            logger.info(f"기본 결제 방식 규칙 {len(rules_to_add)}개 추가됨")
    
    def _get_default_by_source(self, source: str) -> str:
        """
        데이터 소스에 따른 기본 결제 방식을 반환합니다.
        
        Args:
            source: 데이터 소스
            
        Returns:
            str: 기본 결제 방식
        """
        source_defaults = {
            'toss_card': '체크카드결제',
            'toss_account': '계좌이체',
            'manual': '현금'
        }
        
        return source_defaults.get(source, '기타카드')
    
    def _create_simple_rule(self, transaction: Transaction, payment_method: str) -> bool:
        """
        단순 규칙을 생성합니다.
        
        Args:
            transaction: 거래 객체
            payment_method: 결제 방식
            
        Returns:
            bool: 규칙 생성 성공 여부
        """
        try:
            # 키워드 추출
            keywords = self._extract_keywords(transaction.description)
            if not keywords:
                return False
            
            # 가장 긴 키워드 선택
            best_keyword = max(keywords, key=len)
            
            # 규칙 생성
            rule = ClassificationRule(
                rule_name=f"학습-{payment_method}-{best_keyword[:20]}",
                rule_type=self.RULE_TYPE,
                condition_type=ClassificationRule.CONDITION_CONTAINS,
                condition_value=best_keyword,
                target_value=payment_method,
                priority=20,  # 기본 규칙보다 높은 우선순위
                created_by=ClassificationRule.CREATOR_LEARNED
            )
            
            self.rule_engine.add_rule(rule)
            logger.info(f"단순 규칙 생성됨: {rule.rule_name}")
            return True
        
        except Exception as e:
            logger.error(f"규칙 생성 실패: {e}")
            return False
    
    def _create_source_based_rule(self, transaction: Transaction, payment_method: str) -> bool:
        """
        소스 기반 규칙을 생성합니다.
        
        Args:
            transaction: 거래 객체
            payment_method: 결제 방식
            
        Returns:
            bool: 규칙 생성 성공 여부
        """
        try:
            # 유사한 거래 찾기
            similar_transactions = []
            if self.transaction_repository:
                similar_transactions = self.transaction_repository.list({
                    'source': transaction.source,
                    'limit': 20
                })
            
            # 패턴 분석
            patterns = self._analyze_patterns(transaction, similar_transactions)
            if not patterns:
                return self._create_simple_rule(transaction, payment_method)
            
            # 가장 좋은 패턴 선택
            best_pattern = patterns[0]
            
            # 규칙 생성
            rule = ClassificationRule(
                rule_name=f"소스-{payment_method}-{transaction.source}-{best_pattern[:20]}",
                rule_type=self.RULE_TYPE,
                condition_type=ClassificationRule.CONDITION_CONTAINS,
                condition_value=best_pattern,
                target_value=payment_method,
                priority=30,  # 단순 규칙보다 높은 우선순위
                created_by=ClassificationRule.CREATOR_LEARNED
            )
            
            self.rule_engine.add_rule(rule)
            logger.info(f"소스 기반 규칙 생성됨: {rule.rule_name}")
            return True
        
        except Exception as e:
            logger.error(f"소스 기반 규칙 생성 실패: {e}")
            return self._create_simple_rule(transaction, payment_method)
    
    def _extract_keywords(self, description: str) -> List[str]:
        """
        설명에서 키워드를 추출합니다.
        
        Args:
            description: 거래 설명
            
        Returns:
            List[str]: 추출된 키워드 목록
        """
        # 간단한 키워드 추출 (공백으로 분리)
        words = description.split()
        
        # 숫자와 특수문자만 있는 단어 제외
        keywords = [word for word in words if any(c.isalpha() for c in word)]
        
        # 너무 짧은 단어 제외 (2글자 이상)
        keywords = [word for word in keywords if len(word) >= 2]
        
        return keywords
    
    def _analyze_patterns(
        self, 
        transaction: Transaction, 
        similar_transactions: List[Transaction]
    ) -> List[str]:
        """
        거래 패턴을 분석합니다.
        
        Args:
            transaction: 거래 객체
            similar_transactions: 유사한 거래 목록
            
        Returns:
            List[str]: 패턴 목록 (중요도 순)
        """
        # 키워드 빈도 분석
        keyword_counts = Counter()
        
        # 현재 거래의 키워드
        current_keywords = self._extract_keywords(transaction.description)
        for keyword in current_keywords:
            keyword_counts[keyword] += 3  # 현재 거래의 키워드에 가중치 부여
        
        # 유사 거래의 키워드
        for t in similar_transactions:
            keywords = self._extract_keywords(t.description)
            for keyword in keywords:
                keyword_counts[keyword] += 1
        
        # 중요도 순으로 정렬
        patterns = [k for k, v in keyword_counts.most_common() if len(k) >= 2]
        
        return patterns