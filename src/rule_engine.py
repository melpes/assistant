# -*- coding: utf-8 -*-
"""
규칙 엔진(RuleEngine) 클래스

거래 내역에 분류 규칙을 적용하여 자동 분류하는 엔진입니다.
"""

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from functools import lru_cache

from src.models import ClassificationRule, Transaction
from src.repositories.rule_repository import RuleRepository

# 로거 설정
logger = logging.getLogger(__name__)


class RuleEngine:
    """
    규칙 엔진 클래스
    
    거래 내역에 분류 규칙을 적용하여 자동 분류하는 엔진입니다.
    """
    
    # 규칙 캐시 크기
    CACHE_SIZE = 100
    
    def __init__(self, rule_repository: RuleRepository):
        """
        규칙 엔진 초기화
        
        Args:
            rule_repository: 규칙 저장소
        """
        self.rule_repository = rule_repository
        self._rule_cache = {}  # 규칙 유형별 캐시
        self._cache_timestamp = {}  # 캐시 타임스탬프
    
    def apply_rules(self, transaction: Transaction, rule_type: str) -> Optional[str]:
        """
        거래에 특정 유형의 규칙을 적용하여 결과값을 반환합니다.
        
        Args:
            transaction: 거래 객체
            rule_type: 규칙 유형 (category, payment_method, filter)
            
        Returns:
            Optional[str]: 규칙 적용 결과값 또는 None (일치하는 규칙이 없는 경우)
        """
        # 거래 데이터를 딕셔너리로 변환
        transaction_data = transaction.to_dict()
        
        # 규칙 목록 가져오기 (캐시 활용)
        rules = self._get_active_rules_by_type(rule_type)
        
        # 우선순위 순으로 규칙 적용
        for rule in rules:
            if self._match_rule(rule, transaction_data):
                logger.debug(f"규칙 일치: {rule.rule_name} (ID={rule.id}), "
                           f"거래: {transaction.description}, 결과값: {rule.target_value}")
                return rule.target_value
        
        logger.debug(f"일치하는 규칙 없음: 거래={transaction.description}, 규칙 유형={rule_type}")
        return None
    
    def apply_rules_batch(self, transactions: List[Transaction], rule_type: str) -> Dict[str, str]:
        """
        여러 거래에 특정 유형의 규칙을 일괄 적용합니다.
        
        Args:
            transactions: 거래 객체 목록
            rule_type: 규칙 유형 (category, payment_method, filter)
            
        Returns:
            Dict[str, str]: 거래 ID를 키로, 규칙 적용 결과값을 값으로 하는 딕셔너리
        """
        results = {}
        rules = self._get_active_rules_by_type(rule_type)
        
        for transaction in transactions:
            transaction_data = transaction.to_dict()
            
            # 우선순위 순으로 규칙 적용
            for rule in rules:
                if self._match_rule(rule, transaction_data):
                    results[transaction.transaction_id] = rule.target_value
                    break
        
        logger.info(f"일괄 규칙 적용 완료: {len(results)}/{len(transactions)} 거래에 적용됨")
        return results
    
    def add_rule(self, rule: ClassificationRule) -> ClassificationRule:
        """
        새 규칙을 추가합니다.
        
        Args:
            rule: 추가할 규칙 객체
            
        Returns:
            ClassificationRule: 추가된 규칙 (ID가 할당됨)
        """
        # 규칙 저장
        created_rule = self.rule_repository.create(rule)
        
        # 캐시 무효화
        self._invalidate_cache(rule.rule_type)
        
        logger.info(f"규칙 추가됨: {created_rule.rule_name} (ID={created_rule.id})")
        return created_rule
    
    def update_rule(self, rule: ClassificationRule) -> ClassificationRule:
        """
        기존 규칙을 업데이트합니다.
        
        Args:
            rule: 업데이트할 규칙 객체 (ID 필수)
            
        Returns:
            ClassificationRule: 업데이트된 규칙
            
        Raises:
            ValueError: ID가 없는 경우
        """
        if rule.id is None:
            raise ValueError("업데이트할 규칙의 ID가 없습니다")
        
        # 규칙 업데이트
        updated_rule = self.rule_repository.update(rule)
        
        # 캐시 무효화
        self._invalidate_cache(rule.rule_type)
        
        logger.info(f"규칙 업데이트됨: {updated_rule.rule_name} (ID={updated_rule.id})")
        return updated_rule
    
    def delete_rule(self, rule_id: int) -> bool:
        """
        규칙을 삭제합니다.
        
        Args:
            rule_id: 삭제할 규칙의 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        # 규칙 조회 (캐시 무효화를 위해 유형 확인)
        rule = self.rule_repository.read(rule_id)
        if not rule:
            logger.warning(f"삭제할 규칙을 찾을 수 없음: ID={rule_id}")
            return False
        
        # 규칙 삭제
        success = self.rule_repository.delete(rule_id)
        
        # 캐시 무효화
        if success:
            self._invalidate_cache(rule.rule_type)
            logger.info(f"규칙 삭제됨: ID={rule_id}")
        
        return success
    
    def update_rule_priority(self, rule_id: int, priority: int) -> bool:
        """
        규칙의 우선순위를 업데이트합니다.
        
        Args:
            rule_id: 규칙 ID
            priority: 새 우선순위
            
        Returns:
            bool: 업데이트 성공 여부
        """
        # 규칙 조회
        rule = self.rule_repository.read(rule_id)
        if not rule:
            logger.warning(f"우선순위를 업데이트할 규칙을 찾을 수 없음: ID={rule_id}")
            return False
        
        # 우선순위 업데이트
        rule.update_priority(priority)
        self.rule_repository.update(rule)
        
        # 캐시 무효화
        self._invalidate_cache(rule.rule_type)
        
        logger.info(f"규칙 우선순위 업데이트됨: ID={rule_id}, 우선순위={priority}")
        return True
    
    def resolve_conflicts(self, rule_type: str) -> List[Tuple[ClassificationRule, ClassificationRule]]:
        """
        특정 유형의 규칙 간 충돌을 감지하고 해결합니다.
        
        충돌은 동일한 조건을 가진 규칙들이 서로 다른 결과값을 가질 때 발생합니다.
        우선순위가 높은 규칙이 우선적으로 적용됩니다.
        
        Args:
            rule_type: 규칙 유형
            
        Returns:
            List[Tuple[ClassificationRule, ClassificationRule]]: 충돌하는 규칙 쌍 목록
        """
        # 활성화된 규칙 목록 가져오기
        rules = self.rule_repository.get_active_rules_by_type(rule_type)
        
        # 조건 유형과 값으로 그룹화
        condition_groups = {}
        for rule in rules:
            key = (rule.condition_type, rule.condition_value)
            if key not in condition_groups:
                condition_groups[key] = []
            condition_groups[key].append(rule)
        
        # 충돌 감지 (동일 조건, 다른 결과값)
        conflicts = []
        for group in condition_groups.values():
            if len(group) > 1:
                # 결과값으로 그룹화
                result_groups = {}
                for rule in group:
                    if rule.target_value not in result_groups:
                        result_groups[rule.target_value] = []
                    result_groups[rule.target_value].append(rule)
                
                # 서로 다른 결과값이 있으면 충돌
                if len(result_groups) > 1:
                    # 우선순위 순으로 정렬
                    sorted_rules = sorted(group, key=lambda r: r.priority, reverse=True)
                    
                    # 최고 우선순위 규칙과 나머지 규칙들 간의 충돌 쌍 생성
                    highest_rule = sorted_rules[0]
                    for rule in sorted_rules[1:]:
                        if rule.target_value != highest_rule.target_value:
                            conflicts.append((highest_rule, rule))
        
        if conflicts:
            logger.warning(f"규칙 충돌 감지됨: {len(conflicts)}개 충돌, 규칙 유형={rule_type}")
        
        return conflicts
    
    def get_rule_stats(self, rule_type: str) -> Dict[str, Any]:
        """
        특정 유형의 규칙 통계를 반환합니다.
        
        Args:
            rule_type: 규칙 유형
            
        Returns:
            Dict[str, Any]: 규칙 통계 정보
        """
        # 활성화된 규칙 목록 가져오기
        rules = self.rule_repository.get_active_rules_by_type(rule_type)
        
        # 조건 유형별 개수
        condition_counts = {}
        for rule in rules:
            if rule.condition_type not in condition_counts:
                condition_counts[rule.condition_type] = 0
            condition_counts[rule.condition_type] += 1
        
        # 생성자별 개수
        creator_counts = {}
        for rule in rules:
            if rule.created_by not in creator_counts:
                creator_counts[rule.created_by] = 0
            creator_counts[rule.created_by] += 1
        
        # 우선순위 범위
        priorities = [rule.priority for rule in rules]
        min_priority = min(priorities) if priorities else 0
        max_priority = max(priorities) if priorities else 0
        
        # 결과값 분포
        target_counts = {}
        for rule in rules:
            if rule.target_value not in target_counts:
                target_counts[rule.target_value] = 0
            target_counts[rule.target_value] += 1
        
        return {
            'total_rules': len(rules),
            'condition_counts': condition_counts,
            'creator_counts': creator_counts,
            'priority_range': (min_priority, max_priority),
            'target_counts': target_counts
        }
    
    def clear_cache(self) -> None:
        """
        모든 규칙 캐시를 초기화합니다.
        """
        self._rule_cache.clear()
        self._cache_timestamp.clear()
        logger.debug("규칙 캐시 초기화됨")
    
    def _invalidate_cache(self, rule_type: str) -> None:
        """
        특정 유형의 규칙 캐시를 무효화합니다.
        
        Args:
            rule_type: 규칙 유형
        """
        if rule_type in self._rule_cache:
            del self._rule_cache[rule_type]
        if rule_type in self._cache_timestamp:
            del self._cache_timestamp[rule_type]
        logger.debug(f"규칙 캐시 무효화됨: 유형={rule_type}")
    
    def _get_active_rules_by_type(self, rule_type: str) -> List[ClassificationRule]:
        """
        특정 유형의 활성화된 규칙 목록을 가져옵니다 (캐시 활용).
        
        Args:
            rule_type: 규칙 유형
            
        Returns:
            List[ClassificationRule]: 활성화된 규칙 목록
        """
        # 캐시 확인
        if rule_type in self._rule_cache:
            logger.debug(f"규칙 캐시 사용: 유형={rule_type}")
            return self._rule_cache[rule_type]
        
        # 규칙 조회
        rules = self.rule_repository.get_active_rules_by_type(rule_type)
        
        # 캐시 저장
        self._rule_cache[rule_type] = rules
        logger.debug(f"규칙 캐시 갱신: 유형={rule_type}, 규칙 수={len(rules)}")
        
        return rules
    
    def _match_rule(self, rule: ClassificationRule, transaction_data: Dict[str, Any]) -> bool:
        """
        규칙이 거래 데이터와 일치하는지 확인합니다.
        
        Args:
            rule: 규칙 객체
            transaction_data: 거래 데이터 딕셔너리
            
        Returns:
            bool: 일치 여부
        """
        if not rule.is_active:
            return False
        
        # 조건 유형에 따른 매칭 로직
        if rule.condition_type == ClassificationRule.CONDITION_CONTAINS:
            # 설명에 특정 문자열이 포함되어 있는지 확인
            return rule.condition_value.lower() in transaction_data.get('description', '').lower()
        
        elif rule.condition_type == ClassificationRule.CONDITION_EQUALS:
            # 설명이 특정 문자열과 정확히 일치하는지 확인
            return rule.condition_value.lower() == transaction_data.get('description', '').lower()
        
        elif rule.condition_type == ClassificationRule.CONDITION_REGEX:
            # 정규식 패턴과 일치하는지 확인
            try:
                pattern = re.compile(rule.condition_value, re.IGNORECASE)
                return bool(pattern.search(transaction_data.get('description', '')))
            except re.error:
                logger.error(f"잘못된 정규식 패턴: {rule.condition_value}")
                return False
        
        elif rule.condition_type == ClassificationRule.CONDITION_AMOUNT_RANGE:
            # 금액이 특정 범위 내에 있는지 확인
            try:
                amount = Decimal(transaction_data.get('amount', '0'))
                min_val, max_val = map(lambda x: Decimal(x.strip()), rule.condition_value.split(':'))
                return min_val <= amount <= max_val
            except (ValueError, TypeError, InvalidOperation):
                logger.error(f"금액 범위 비교 오류: {rule.condition_value}, 금액={transaction_data.get('amount')}")
                return False
        
        return False