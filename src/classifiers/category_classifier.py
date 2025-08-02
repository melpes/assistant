# -*- coding: utf-8 -*-
"""
카테고리 분류기(CategoryClassifier) 클래스

거래 내역을 카테고리로 자동 분류하는 분류기입니다.
"""

import logging
from typing import Dict, Any, Optional, List, Set
from collections import defaultdict, Counter

from src.models import Transaction, ClassificationRule
from src.repositories.rule_repository import RuleRepository
from src.repositories.transaction_repository import TransactionRepository
from src.rule_engine import RuleEngine
from src.classifiers.base_classifier import BaseClassifier

# 로거 설정
logger = logging.getLogger(__name__)


class CategoryClassifier(BaseClassifier):
    """
    카테고리 분류기 클래스
    
    거래 내역을 카테고리로 자동 분류하는 분류기입니다.
    """
    
    # 기본 카테고리 목록
    DEFAULT_CATEGORIES = [
        "식비", "생활용품", "교통비", "온라인쇼핑", "문화/오락", 
        "의료비", "통신비", "공과금", "의류/패션", "현금인출", 
        "해외결제", "간편결제", "기타"
    ]
    
    # 규칙 유형
    RULE_TYPE = ClassificationRule.TYPE_CATEGORY
    
    def __init__(
        self, 
        rule_engine: RuleEngine, 
        transaction_repository: Optional[TransactionRepository] = None
    ):
        """
        카테고리 분류기 초기화
        
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
        
        # 기본 카테고리 규칙 초기화
        self._ensure_default_rules()
    
    def classify(self, transaction: Transaction) -> Optional[str]:
        """
        거래를 카테고리로 분류합니다.
        
        분류 우선순위:
        1. 사용자 정의 규칙
        2. 학습된 규칙
        3. 기본 규칙
        4. 기본값 ('기타')
        
        Args:
            transaction: 분류할 거래 객체
            
        Returns:
            str: 분류된 카테고리
        """
        # 이미 카테고리가 있으면 반환
        if transaction.category:
            return transaction.category
        
        # 규칙 엔진으로 분류 시도
        category = self.rule_engine.apply_rules(transaction, self.RULE_TYPE)
        
        # 분류 결과 기록
        self._accuracy_metrics['total_classified'] += 1
        
        if category:
            self._accuracy_metrics['rule_based_classifications'] += 1
            logger.debug(f"규칙 기반 분류: {transaction.description} -> {category}")
            return category
        
        # 기본 카테고리 할당
        self._accuracy_metrics['default_classifications'] += 1
        default_category = "기타"
        logger.debug(f"기본 카테고리 할당: {transaction.description} -> {default_category}")
        return default_category
    
    def classify_batch(self, transactions: List[Transaction]) -> Dict[str, str]:
        """
        여러 거래를 일괄 분류합니다.
        
        Args:
            transactions: 분류할 거래 객체 목록
            
        Returns:
            Dict[str, str]: 거래 ID를 키로, 카테고리를 값으로 하는 딕셔너리
        """
        # 이미 카테고리가 있는 거래 필터링
        uncategorized = [t for t in transactions if not t.category]
        
        if not uncategorized:
            return {}
        
        # 규칙 엔진으로 일괄 분류
        rule_results = self.rule_engine.apply_rules_batch(uncategorized, self.RULE_TYPE)
        
        # 결과 통합
        results = {}
        for transaction in uncategorized:
            # 규칙 기반 결과가 있으면 사용
            if transaction.transaction_id in rule_results:
                category = rule_results[transaction.transaction_id]
                self._accuracy_metrics['rule_based_classifications'] += 1
            else:
                # 기본 카테고리 할당
                category = "기타"
                self._accuracy_metrics['default_classifications'] += 1
            
            results[transaction.transaction_id] = category
            self._accuracy_metrics['total_classified'] += 1
        
        logger.info(f"일괄 카테고리 분류 완료: {len(results)}/{len(transactions)} 거래 분류됨")
        return results
    
    def learn_from_correction(self, transaction: Transaction, correct_category: str) -> bool:
        """
        사용자 수정사항으로부터 학습합니다.
        
        Args:
            transaction: 수정된 거래 객체
            correct_category: 올바른 카테고리
            
        Returns:
            bool: 학습 성공 여부
        """
        if not correct_category:
            logger.warning("학습 실패: 올바른 카테고리가 제공되지 않았습니다")
            return False
        
        # 수정 패턴 기록
        prev_category = transaction.category or "미분류"
        pattern = f"{prev_category} -> {correct_category}"
        self._accuracy_metrics['user_corrections'] += 1
        self._accuracy_metrics['correction_patterns'][pattern] += 1
        
        # 유사한 거래 패턴 찾기
        if not self.transaction_repository:
            logger.warning("학습 제한: 거래 저장소가 제공되지 않았습니다")
            return self._create_simple_rule(transaction, correct_category)
        
        # 설명에서 키워드 추출
        keywords = self._extract_keywords(transaction.description)
        if not keywords:
            logger.warning(f"학습 제한: 키워드를 추출할 수 없습니다: {transaction.description}")
            return self._create_simple_rule(transaction, correct_category)
        
        # 유사한 거래 찾기
        similar_transactions = self._find_similar_transactions(keywords)
        
        # 패턴 분석 및 규칙 생성
        if similar_transactions:
            return self._create_pattern_based_rule(transaction, correct_category, similar_transactions)
        else:
            return self._create_simple_rule(transaction, correct_category)
    
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
    
    def get_available_categories(self) -> List[str]:
        """
        사용 가능한 모든 카테고리 목록을 반환합니다.
        
        Returns:
            List[str]: 카테고리 목록
        """
        categories = set(self.DEFAULT_CATEGORIES)
        
        # 규칙에서 사용 중인 카테고리 추가
        rule_repo = self.rule_engine.rule_repository
        rules = rule_repo.list({'rule_type': self.RULE_TYPE})
        for rule in rules:
            categories.add(rule.target_value)
        
        # 거래에서 사용 중인 카테고리 추가
        if self.transaction_repository:
            db_categories = self.transaction_repository.get_categories()
            categories.update(db_categories)
        
        return sorted(list(categories))
    
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
        기본 카테고리 규칙을 초기화합니다.
        """
        rule_repo = self.rule_engine.rule_repository
        
        # 기본 규칙 정의
        default_rules = [
            # 식비 관련 규칙
            {
                'rule_name': '식비-음식점',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '식당',
                'target_value': '식비',
                'priority': 10
            },
            {
                'rule_name': '식비-카페',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '카페',
                'target_value': '식비',
                'priority': 10
            },
            {
                'rule_name': '식비-배달',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '배달',
                'target_value': '식비',
                'priority': 10
            },
            
            # 교통비 관련 규칙
            {
                'rule_name': '교통비-택시',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '택시',
                'target_value': '교통비',
                'priority': 10
            },
            {
                'rule_name': '교통비-대중교통',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '교통',
                'target_value': '교통비',
                'priority': 10
            },
            
            # 공과금 관련 규칙
            {
                'rule_name': '공과금-전기',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '전기요금',
                'target_value': '공과금',
                'priority': 10
            },
            {
                'rule_name': '공과금-수도',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '수도요금',
                'target_value': '공과금',
                'priority': 10
            },
            {
                'rule_name': '공과금-가스',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '가스요금',
                'target_value': '공과금',
                'priority': 10
            },
            
            # 쇼핑 관련 규칙
            {
                'rule_name': '온라인쇼핑-쿠팡',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '쿠팡',
                'target_value': '온라인쇼핑',
                'priority': 10
            },
            {
                'rule_name': '온라인쇼핑-마켓컬리',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '마켓컬리',
                'target_value': '온라인쇼핑',
                'priority': 10
            },
            {
                'rule_name': '온라인쇼핑-11번가',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '11번가',
                'target_value': '온라인쇼핑',
                'priority': 10
            },
            
            # 의료비 관련 규칙
            {
                'rule_name': '의료비-병원',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '병원',
                'target_value': '의료비',
                'priority': 10
            },
            {
                'rule_name': '의료비-약국',
                'condition_type': ClassificationRule.CONDITION_CONTAINS,
                'condition_value': '약국',
                'target_value': '의료비',
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
            logger.info(f"기본 카테고리 규칙 {len(rules_to_add)}개 추가됨")
    
    def _create_simple_rule(self, transaction: Transaction, category: str) -> bool:
        """
        단순 규칙을 생성합니다.
        
        Args:
            transaction: 거래 객체
            category: 카테고리
            
        Returns:
            bool: 규칙 생성 성공 여부
        """
        try:
            # 상점명 추출
            merchant = self._extract_merchant_name(transaction.description)
            condition_value = merchant if merchant else transaction.description
            
            # 규칙 생성
            rule = ClassificationRule(
                rule_name=f"학습-{category}-{condition_value[:20]}",
                rule_type=self.RULE_TYPE,
                condition_type=ClassificationRule.CONDITION_CONTAINS,
                condition_value=condition_value,
                target_value=category,
                priority=20,  # 기본 규칙보다 높은 우선순위
                created_by=ClassificationRule.CREATOR_LEARNED
            )
            
            self.rule_engine.add_rule(rule)
            logger.info(f"단순 규칙 생성됨: {rule.rule_name}")
            return True
        
        except Exception as e:
            logger.error(f"규칙 생성 실패: {e}")
            return False
    
    def _create_pattern_based_rule(
        self, 
        transaction: Transaction, 
        category: str, 
        similar_transactions: List[Transaction]
    ) -> bool:
        """
        패턴 기반 규칙을 생성합니다.
        
        Args:
            transaction: 거래 객체
            category: 카테고리
            similar_transactions: 유사한 거래 목록
            
        Returns:
            bool: 규칙 생성 성공 여부
        """
        try:
            # 공통 키워드 추출
            descriptions = [t.description for t in similar_transactions]
            descriptions.append(transaction.description)
            common_keywords = self._extract_common_keywords(descriptions)
            
            if not common_keywords:
                return self._create_simple_rule(transaction, category)
            
            # 가장 좋은 키워드 선택
            best_keyword = max(common_keywords, key=len)
            
            # 규칙 생성
            rule = ClassificationRule(
                rule_name=f"패턴-{category}-{best_keyword[:20]}",
                rule_type=self.RULE_TYPE,
                condition_type=ClassificationRule.CONDITION_CONTAINS,
                condition_value=best_keyword,
                target_value=category,
                priority=30,  # 단순 규칙보다 높은 우선순위
                created_by=ClassificationRule.CREATOR_LEARNED
            )
            
            self.rule_engine.add_rule(rule)
            logger.info(f"패턴 기반 규칙 생성됨: {rule.rule_name}")
            return True
        
        except Exception as e:
            logger.error(f"패턴 기반 규칙 생성 실패: {e}")
            return self._create_simple_rule(transaction, category)
    
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
    
    def _extract_merchant_name(self, description: str) -> Optional[str]:
        """
        설명에서 상점명을 추출합니다.
        
        Args:
            description: 거래 설명
            
        Returns:
            Optional[str]: 추출된 상점명 또는 None
        """
        # 간단한 상점명 추출 (첫 번째 단어)
        words = description.split()
        if words:
            return words[0]
        return None
    
    def _find_similar_transactions(self, keywords: List[str]) -> List[Transaction]:
        """
        키워드와 유사한 거래를 찾습니다.
        
        Args:
            keywords: 키워드 목록
            
        Returns:
            List[Transaction]: 유사한 거래 목록
        """
        if not self.transaction_repository:
            return []
        
        similar_transactions = []
        
        # 각 키워드로 검색
        for keyword in keywords:
            if len(keyword) < 2:
                continue
                
            transactions = self.transaction_repository.list({
                'description_contains': keyword,
                'limit': 10
            })
            
            similar_transactions.extend(transactions)
        
        # 중복 제거
        unique_transactions = {}
        for transaction in similar_transactions:
            if transaction.id not in unique_transactions:
                unique_transactions[transaction.id] = transaction
        
        return list(unique_transactions.values())
    
    def _extract_common_keywords(self, descriptions: List[str]) -> List[str]:
        """
        여러 설명에서 공통 키워드를 추출합니다.
        
        Args:
            descriptions: 설명 목록
            
        Returns:
            List[str]: 공통 키워드 목록
        """
        if not descriptions:
            return []
        
        # 각 설명에서 키워드 추출
        all_keywords = []
        for description in descriptions:
            keywords = self._extract_keywords(description)
            all_keywords.append(set(keywords))
        
        # 공통 키워드 찾기
        common_keywords = set.intersection(*all_keywords) if all_keywords else set()
        
        return list(common_keywords)