# -*- coding: utf-8 -*-
"""
학습 엔진(LearningEngine) 클래스

사용자 수정사항으로부터 패턴을 추출하고 학습하는 엔진입니다.
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import Counter

from src.models import Transaction, ClassificationRule, LearningPattern
from src.repositories.learning_pattern_repository import LearningPatternRepository
from src.repositories.rule_repository import RuleRepository
from src.repositories.transaction_repository import TransactionRepository

# 로거 설정
logger = logging.getLogger(__name__)


class LearningEngine:
    """
    학습 엔진 클래스
    
    사용자 수정사항으로부터 패턴을 추출하고 학습하는 엔진입니다.
    """
    
    # 키워드 추출 설정
    MIN_KEYWORD_LENGTH = 2
    MAX_KEYWORDS_PER_TRANSACTION = 5
    
    # 유사도 임계값
    SIMILARITY_THRESHOLD = 0.6
    
    # 패턴 변화 감지 설정
    PATTERN_CHANGE_THRESHOLD = 0.3
    MIN_PATTERN_SAMPLES = 5
    
    # 패턴 적용 설정
    MIN_PATTERN_CONFIDENCE = LearningPattern.CONFIDENCE_MEDIUM
    MIN_PATTERN_OCCURRENCES = 2
    
    def __init__(
        self,
        pattern_repository: LearningPatternRepository,
        rule_repository: RuleRepository,
        transaction_repository: Optional[TransactionRepository] = None
    ):
        """
        학습 엔진 초기화
        
        Args:
            pattern_repository: 학습 패턴 저장소
            rule_repository: 규칙 저장소
            transaction_repository: 거래 저장소 (선택, 유사 거래 검색에 사용)
        """
        self.pattern_repository = pattern_repository
        self.rule_repository = rule_repository
        self.transaction_repository = transaction_repository
        
        # 학습 통계
        self._learning_stats = {
            'patterns_extracted': 0,
            'patterns_applied': 0,
            'rules_generated': 0,
            'corrections_processed': 0
        }
    
    def learn_from_correction(
        self, 
        transaction: Transaction, 
        field_name: str, 
        previous_value: str, 
        corrected_value: str
    ) -> bool:
        """
        사용자 수정사항으로부터 학습합니다.
        
        Args:
            transaction: 수정된 거래 객체
            field_name: 수정된 필드명 (category, payment_method 등)
            previous_value: 이전 값
            corrected_value: 수정된 값
            
        Returns:
            bool: 학습 성공 여부
        """
        if not transaction or not field_name or not corrected_value:
            logger.warning("학습 실패: 필수 정보가 누락되었습니다")
            return False
        
        # 통계 업데이트
        self._learning_stats['corrections_processed'] += 1
        
        try:
            # 패턴 유형 결정
            pattern_type = self._field_to_pattern_type(field_name)
            if not pattern_type:
                logger.warning(f"학습 실패: 지원되지 않는 필드 - {field_name}")
                return False
            
            # 키워드 추출
            keywords = self._extract_keywords(transaction.description)
            if not keywords:
                logger.warning(f"학습 실패: 키워드를 추출할 수 없습니다 - {transaction.description}")
                return False
            
            # 유사 거래 검색
            similar_transactions = self._find_similar_transactions(transaction)
            
            # 패턴 추출 및 저장
            patterns = self._extract_patterns(
                transaction, pattern_type, keywords, corrected_value, similar_transactions
            )
            
            if not patterns:
                logger.warning("학습 실패: 패턴을 추출할 수 없습니다")
                return False
            
            # 패턴 저장
            for pattern in patterns:
                self.pattern_repository.create(pattern)
                self._learning_stats['patterns_extracted'] += 1
            
            # 고신뢰도 패턴 자동 적용
            self._apply_high_confidence_patterns(pattern_type)
            
            logger.info(f"학습 성공: {len(patterns)}개 패턴 추출됨")
            return True
            
        except Exception as e:
            logger.error(f"학습 중 오류 발생: {e}")
            return False
    
    def learn_from_corrections_batch(
        self, 
        corrections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        여러 수정사항을 일괄 학습합니다.
        
        Args:
            corrections: 수정사항 목록
                각 항목은 다음 키를 포함해야 함:
                - transaction: 거래 객체
                - field_name: 수정된 필드명
                - previous_value: 이전 값
                - corrected_value: 수정된 값
                
        Returns:
            Dict[str, Any]: 학습 결과 통계
        """
        results = {
            'total': len(corrections),
            'success': 0,
            'failure': 0,
            'patterns_extracted': 0,
            'rules_generated': 0
        }
        
        # 초기 통계 저장
        initial_patterns = self._learning_stats['patterns_extracted']
        initial_rules = self._learning_stats['rules_generated']
        
        # 각 수정사항 처리
        for correction in corrections:
            success = self.learn_from_correction(
                correction.get('transaction'),
                correction.get('field_name'),
                correction.get('previous_value'),
                correction.get('corrected_value')
            )
            
            if success:
                results['success'] += 1
            else:
                results['failure'] += 1
        
        # 결과 통계 업데이트
        results['patterns_extracted'] = self._learning_stats['patterns_extracted'] - initial_patterns
        results['rules_generated'] = self._learning_stats['rules_generated'] - initial_rules
        
        logger.info(f"일괄 학습 완료: {results['success']}/{results['total']} 성공")
        return results
    
    def apply_patterns_to_rules(self, pattern_type: str, min_confidence: str = None) -> int:
        """
        학습된 패턴을 규칙으로 변환하여 적용합니다.
        
        Args:
            pattern_type: 패턴 유형
            min_confidence: 최소 신뢰도 (기본값: MIN_PATTERN_CONFIDENCE)
            
        Returns:
            int: 적용된 규칙 수
        """
        min_confidence = min_confidence or self.MIN_PATTERN_CONFIDENCE
        
        # 적용 가능한 패턴 조회
        patterns = self.pattern_repository.list({
            'pattern_type': pattern_type,
            'status': LearningPattern.STATUS_PENDING,
            'min_occurrence': self.MIN_PATTERN_OCCURRENCES
        })
        
        # 신뢰도 필터링
        confidence_levels = {
            LearningPattern.CONFIDENCE_LOW: 1,
            LearningPattern.CONFIDENCE_MEDIUM: 2,
            LearningPattern.CONFIDENCE_HIGH: 3
        }
        
        min_level = confidence_levels.get(min_confidence, 2)
        patterns = [p for p in patterns if confidence_levels.get(p.confidence, 0) >= min_level]
        
        if not patterns:
            logger.info(f"적용할 패턴이 없습니다: 유형={pattern_type}")
            return 0
        
        # 규칙 유형 결정
        rule_type = self._pattern_type_to_rule_type(pattern_type)
        if not rule_type:
            logger.warning(f"규칙 변환 실패: 지원되지 않는 패턴 유형 - {pattern_type}")
            return 0
        
        # 패턴 우선순위 계산
        prioritized_patterns = self._calculate_pattern_priorities(patterns)
        
        # 패턴을 규칙으로 변환
        rules_created = 0
        for pattern, priority in prioritized_patterns:
            # 이미 적용된 패턴 건너뛰기
            if pattern.status == LearningPattern.STATUS_APPLIED:
                continue
                
            # 규칙 생성
            rule = ClassificationRule(
                rule_name=f"학습-{pattern.pattern_value}-{pattern.pattern_key[:20]}",
                rule_type=rule_type,
                condition_type=ClassificationRule.CONDITION_CONTAINS,
                condition_value=pattern.pattern_key,
                target_value=pattern.pattern_value,
                priority=priority,  # 계산된 우선순위 사용
                created_by=ClassificationRule.CREATOR_LEARNED
            )
            
            # 중복 규칙 확인
            existing_rules = self.rule_repository.list({
                'rule_type': rule_type,
                'condition_type': rule.condition_type,
                'condition_value': rule.condition_value,
                'target_value': rule.target_value
            })
            
            if existing_rules:
                logger.debug(f"중복 규칙 건너뛰기: {rule.rule_name}")
                continue
            
            # 규칙 저장
            self.rule_repository.create(rule)
            rules_created += 1
            
            # 패턴 상태 업데이트
            pattern.status = LearningPattern.STATUS_APPLIED
            self.pattern_repository.update(pattern)
            
            self._learning_stats['patterns_applied'] += 1
            self._learning_stats['rules_generated'] += 1
            
            logger.info(f"패턴을 규칙으로 변환: {pattern.pattern_name} -> {rule.rule_name} (우선순위: {priority})")
        
        logger.info(f"패턴 적용 완료: {rules_created}개 규칙 생성됨")
        return rules_created
    
    def _calculate_pattern_priorities(self, patterns: List[LearningPattern]) -> List[Tuple[LearningPattern, int]]:
        """
        패턴의 우선순위를 계산합니다.
        
        Args:
            patterns: 패턴 목록
            
        Returns:
            List[Tuple[LearningPattern, int]]: (패턴, 우선순위) 튜플 목록
        """
        # 기본 우선순위 설정
        base_priorities = {
            LearningPattern.CONFIDENCE_LOW: 15,
            LearningPattern.CONFIDENCE_MEDIUM: 20,
            LearningPattern.CONFIDENCE_HIGH: 25
        }
        
        # 패턴 특성에 따른 우선순위 조정
        prioritized_patterns = []
        
        for pattern in patterns:
            # 기본 우선순위
            priority = base_priorities.get(pattern.confidence, 20)
            
            # 발생 횟수에 따른 보정
            if pattern.occurrence_count >= 10:
                priority += 5
            elif pattern.occurrence_count >= 5:
                priority += 3
            
            # 패턴 키 길이에 따른 보정 (더 구체적인 패턴이 우선)
            if len(pattern.pattern_key) >= 10:
                priority += 2
            
            # 상점명 패턴은 우선순위 높임
            if pattern.pattern_name and pattern.pattern_name.startswith('상점-'):
                priority += 3
            
            # 공통 키워드 패턴은 우선순위 높임
            if pattern.pattern_name and pattern.pattern_name.startswith('공통-'):
                priority += 4
            
            # 최근 패턴은 우선순위 높임
            if pattern.last_seen:
                days_ago = (datetime.now() - pattern.last_seen).days
                if days_ago <= 7:
                    priority += 2
            
            # 우선순위 범위 제한 (10-50)
            priority = max(10, min(priority, 50))
            
            prioritized_patterns.append((pattern, priority))
        
        # 우선순위 순으로 정렬
        prioritized_patterns.sort(key=lambda x: x[1], reverse=True)
        
        return prioritized_patterns
    
    def detect_recurring_patterns(self, days: int = 90) -> List[Dict[str, Any]]:
        """
        반복 거래 패턴을 감지합니다.
        
        Args:
            days: 검색할 과거 일수
            
        Returns:
            List[Dict[str, Any]]: 감지된 반복 패턴 목록
        """
        if not self.transaction_repository:
            logger.warning("반복 패턴 감지 실패: 거래 저장소가 제공되지 않았습니다")
            return []
        
        # 과거 거래 조회
        transactions = self.transaction_repository.list({
            'days': days,
            'order_by': 'transaction_date'
        })
        
        if not transactions:
            logger.info(f"반복 패턴 감지: 거래가 없습니다 (최근 {days}일)")
            return []
        
        # 상점별 거래 그룹화
        merchant_transactions = {}
        for transaction in transactions:
            merchant = self._extract_merchant_name(transaction.description)
            if not merchant:
                continue
                
            if merchant not in merchant_transactions:
                merchant_transactions[merchant] = []
            
            merchant_transactions[merchant].append(transaction)
        
        # 반복 패턴 감지
        recurring_patterns = []
        
        for merchant, merchant_txs in merchant_transactions.items():
            # 최소 3회 이상 거래가 있는 상점만 분석
            if len(merchant_txs) < 3:
                continue
            
            # 거래 간격 분석
            intervals = []
            for i in range(1, len(merchant_txs)):
                prev_date = merchant_txs[i-1].transaction_date
                curr_date = merchant_txs[i].transaction_date
                interval = (curr_date - prev_date).days
                intervals.append(interval)
            
            # 간격 빈도 분석
            interval_counter = Counter(intervals)
            most_common = interval_counter.most_common(1)
            
            if not most_common:
                continue
                
            common_interval, count = most_common[0]
            
            # 최소 2회 이상 동일한 간격으로 발생한 경우
            if count >= 2 and 1 <= common_interval <= 60:  # 1일~60일 간격
                # 금액 패턴 분석
                amounts = [tx.amount for tx in merchant_txs]
                amount_counter = Counter(amounts)
                most_common_amount = amount_counter.most_common(1)
                
                if most_common_amount:
                    common_amount, amount_count = most_common_amount[0]
                    
                    # 패턴 정보 저장
                    pattern = {
                        'merchant': merchant,
                        'interval_days': common_interval,
                        'common_amount': common_amount,
                        'transaction_count': len(merchant_txs),
                        'interval_consistency': count / (len(merchant_txs) - 1),
                        'amount_consistency': amount_count / len(merchant_txs),
                        'last_transaction': merchant_txs[-1],
                        'next_expected_date': merchant_txs[-1].transaction_date.replace(
                            day=merchant_txs[-1].transaction_date.day + common_interval
                        ),
                        'category': merchant_txs[-1].category,
                        'payment_method': merchant_txs[-1].payment_method
                    }
                    
                    recurring_patterns.append(pattern)
        
        # 일관성 점수로 정렬
        recurring_patterns.sort(
            key=lambda p: (p['interval_consistency'] + p['amount_consistency']) / 2,
            reverse=True
        )
        
        logger.info(f"반복 패턴 감지: {len(recurring_patterns)}개 패턴 발견")
        return recurring_patterns
    
    def generate_dynamic_filters(self) -> List[Dict[str, Any]]:
        """
        학습된 패턴을 기반으로 동적 필터를 생성합니다.
        
        Returns:
            List[Dict[str, Any]]: 생성된 필터 목록
        """
        filters = []
        
        # 카테고리 패턴 기반 필터
        category_patterns = self.pattern_repository.list({
            'pattern_type': 'category',
            'status': LearningPattern.STATUS_APPLIED,
            'min_occurrence': 3
        })
        
        # 카테고리별 키워드 그룹화
        category_keywords = {}
        for pattern in category_patterns:
            category = pattern.pattern_value
            if category not in category_keywords:
                category_keywords[category] = []
            
            category_keywords[category].append(pattern.pattern_key)
        
        # 카테고리별 필터 생성
        for category, keywords in category_keywords.items():
            # 상위 5개 키워드만 사용
            top_keywords = keywords[:5]
            
            if top_keywords:
                filter_config = {
                    'name': f"자동-{category}",
                    'description': f"{category} 관련 거래 (자동 생성)",
                    'conditions': [
                        {
                            'field': 'description',
                            'operator': 'contains_any',
                            'values': top_keywords
                        }
                    ]
                }
                
                filters.append(filter_config)
        
        # 결제 방식 패턴 기반 필터
        payment_patterns = self.pattern_repository.list({
            'pattern_type': 'payment_method',
            'status': LearningPattern.STATUS_APPLIED,
            'min_occurrence': 3
        })
        
        # 결제 방식별 키워드 그룹화
        payment_keywords = {}
        for pattern in payment_patterns:
            payment = pattern.pattern_value
            if payment not in payment_keywords:
                payment_keywords[payment] = []
            
            payment_keywords[payment].append(pattern.pattern_key)
        
        # 결제 방식별 필터 생성
        for payment, keywords in payment_keywords.items():
            # 상위 5개 키워드만 사용
            top_keywords = keywords[:5]
            
            if top_keywords:
                filter_config = {
                    'name': f"자동-{payment}",
                    'description': f"{payment} 결제 방식 거래 (자동 생성)",
                    'conditions': [
                        {
                            'field': 'description',
                            'operator': 'contains_any',
                            'values': top_keywords
                        }
                    ]
                }
                
                filters.append(filter_config)
        
        logger.info(f"동적 필터 생성: {len(filters)}개 필터 생성됨")
        return filters
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """
        학습 통계를 반환합니다.
        
        Returns:
            Dict[str, Any]: 학습 통계 정보
        """
        stats = dict(self._learning_stats)
        
        # 패턴 저장소 통계 추가
        category_stats = self.pattern_repository.get_pattern_stats('category')
        payment_stats = self.pattern_repository.get_pattern_stats('payment_method')
        filter_stats = self.pattern_repository.get_pattern_stats('filter')
        
        stats['category_patterns'] = category_stats
        stats['payment_patterns'] = payment_stats
        stats['filter_patterns'] = filter_stats
        
        # 패턴 변화 감지 통계 추가
        if self.transaction_repository:
            pattern_changes = self.detect_pattern_changes()
            stats['pattern_changes'] = {
                'total': len(pattern_changes),
                'significant_changes': len([p for p in pattern_changes if p['change_score'] > self.PATTERN_CHANGE_THRESHOLD]),
                'top_changes': pattern_changes[:3] if pattern_changes else []
            }
        
        return stats
    
    def detect_pattern_changes(self) -> List[Dict[str, Any]]:
        """
        거래 패턴의 변화를 감지합니다.
        
        Returns:
            List[Dict[str, Any]]: 감지된 패턴 변화 목록
        """
        if not self.transaction_repository:
            logger.warning("패턴 변화 감지 실패: 거래 저장소가 제공되지 않았습니다")
            return []
        
        # 최근 거래 조회 (최근 30일)
        recent_transactions = self.transaction_repository.list({
            'days': 30,
            'order_by': 'transaction_date'
        })
        
        # 이전 거래 조회 (31-90일)
        previous_transactions = self.transaction_repository.list({
            'start_days': 31,
            'end_days': 90,
            'order_by': 'transaction_date'
        })
        
        if not recent_transactions or not previous_transactions:
            logger.info("패턴 변화 감지: 충분한 거래 데이터가 없습니다")
            return []
        
        # 카테고리별 거래 그룹화
        recent_by_category = self._group_transactions_by_field(recent_transactions, 'category')
        previous_by_category = self._group_transactions_by_field(previous_transactions, 'category')
        
        # 결제 방식별 거래 그룹화
        recent_by_payment = self._group_transactions_by_field(recent_transactions, 'payment_method')
        previous_by_payment = self._group_transactions_by_field(previous_transactions, 'payment_method')
        
        # 상점별 거래 그룹화
        recent_by_merchant = {}
        previous_by_merchant = {}
        
        for tx in recent_transactions:
            merchant = self._extract_merchant_name(tx.description)
            if merchant:
                if merchant not in recent_by_merchant:
                    recent_by_merchant[merchant] = []
                recent_by_merchant[merchant].append(tx)
        
        for tx in previous_transactions:
            merchant = self._extract_merchant_name(tx.description)
            if merchant:
                if merchant not in previous_by_merchant:
                    previous_by_merchant[merchant] = []
                previous_by_merchant[merchant].append(tx)
        
        # 패턴 변화 감지
        pattern_changes = []
        
        # 카테고리 패턴 변화
        for category, recent_txs in recent_by_category.items():
            # 최소 샘플 수 확인
            if len(recent_txs) < self.MIN_PATTERN_SAMPLES:
                continue
                
            # 이전 기간에 없는 새로운 카테고리
            if category not in previous_by_category:
                pattern_changes.append({
                    'type': 'new_category',
                    'value': category,
                    'count': len(recent_txs),
                    'change_score': 1.0,
                    'description': f"새로운 카테고리: {category} ({len(recent_txs)}건)"
                })
                continue
            
            # 카테고리 비율 변화
            recent_ratio = len(recent_txs) / len(recent_transactions)
            previous_ratio = len(previous_by_category[category]) / len(previous_transactions)
            
            change_ratio = abs(recent_ratio - previous_ratio) / max(previous_ratio, 0.01)
            
            if change_ratio > self.PATTERN_CHANGE_THRESHOLD:
                change_direction = "증가" if recent_ratio > previous_ratio else "감소"
                
                pattern_changes.append({
                    'type': 'category_change',
                    'value': category,
                    'recent_ratio': recent_ratio,
                    'previous_ratio': previous_ratio,
                    'change_score': change_ratio,
                    'direction': change_direction,
                    'description': f"카테고리 비율 변화: {category} ({change_direction}, {change_ratio:.2f})"
                })
        
        # 결제 방식 패턴 변화
        for payment, recent_txs in recent_by_payment.items():
            # 최소 샘플 수 확인
            if len(recent_txs) < self.MIN_PATTERN_SAMPLES:
                continue
                
            # 이전 기간에 없는 새로운 결제 방식
            if payment not in previous_by_payment:
                pattern_changes.append({
                    'type': 'new_payment_method',
                    'value': payment,
                    'count': len(recent_txs),
                    'change_score': 1.0,
                    'description': f"새로운 결제 방식: {payment} ({len(recent_txs)}건)"
                })
                continue
            
            # 결제 방식 비율 변화
            recent_ratio = len(recent_txs) / len(recent_transactions)
            previous_ratio = len(previous_by_payment[payment]) / len(previous_transactions)
            
            change_ratio = abs(recent_ratio - previous_ratio) / max(previous_ratio, 0.01)
            
            if change_ratio > self.PATTERN_CHANGE_THRESHOLD:
                change_direction = "증가" if recent_ratio > previous_ratio else "감소"
                
                pattern_changes.append({
                    'type': 'payment_method_change',
                    'value': payment,
                    'recent_ratio': recent_ratio,
                    'previous_ratio': previous_ratio,
                    'change_score': change_ratio,
                    'direction': change_direction,
                    'description': f"결제 방식 비율 변화: {payment} ({change_direction}, {change_ratio:.2f})"
                })
        
        # 상점 패턴 변화
        for merchant, recent_txs in recent_by_merchant.items():
            # 최소 샘플 수 확인
            if len(recent_txs) < 3:  # 상점은 더 적은 샘플로도 의미가 있을 수 있음
                continue
                
            # 이전 기간에 없는 새로운 상점
            if merchant not in previous_by_merchant:
                pattern_changes.append({
                    'type': 'new_merchant',
                    'value': merchant,
                    'count': len(recent_txs),
                    'change_score': 0.8,  # 새 상점은 중요하지만 카테고리보다는 낮은 점수
                    'description': f"새로운 상점: {merchant} ({len(recent_txs)}건)"
                })
                continue
            
            # 상점 방문 빈도 변화
            recent_freq = len(recent_txs) / 30  # 일평균 방문 횟수
            previous_freq = len(previous_by_merchant[merchant]) / 60  # 일평균 방문 횟수
            
            change_ratio = abs(recent_freq - previous_freq) / max(previous_freq, 0.01)
            
            if change_ratio > self.PATTERN_CHANGE_THRESHOLD:
                change_direction = "증가" if recent_freq > previous_freq else "감소"
                
                pattern_changes.append({
                    'type': 'merchant_frequency_change',
                    'value': merchant,
                    'recent_frequency': recent_freq,
                    'previous_frequency': previous_freq,
                    'change_score': change_ratio * 0.7,  # 상점 빈도 변화는 약간 낮은 점수
                    'direction': change_direction,
                    'description': f"상점 방문 빈도 변화: {merchant} ({change_direction}, {change_ratio:.2f})"
                })
        
        # 변화 점수로 정렬
        pattern_changes.sort(key=lambda x: x['change_score'], reverse=True)
        
        logger.info(f"패턴 변화 감지: {len(pattern_changes)}개 변화 발견")
        return pattern_changes
    
    def _group_transactions_by_field(self, transactions: List[Transaction], field: str) -> Dict[str, List[Transaction]]:
        """
        거래를 특정 필드 값으로 그룹화합니다.
        
        Args:
            transactions: 거래 목록
            field: 그룹화할 필드명
            
        Returns:
            Dict[str, List[Transaction]]: 그룹화된 거래
        """
        grouped = {}
        
        for tx in transactions:
            value = getattr(tx, field, None)
            if value:
                if value not in grouped:
                    grouped[value] = []
                grouped[value].append(tx)
        
        return grouped
    
    def reset_stats(self) -> None:
        """
        학습 통계를 초기화합니다.
        """
        self._learning_stats = {
            'patterns_extracted': 0,
            'patterns_applied': 0,
            'rules_generated': 0,
            'corrections_processed': 0
        }
    
    def _field_to_pattern_type(self, field_name: str) -> Optional[str]:
        """
        필드명을 패턴 유형으로 변환합니다.
        
        Args:
            field_name: 필드명
            
        Returns:
            Optional[str]: 패턴 유형 또는 None
        """
        mapping = {
            'category': 'category',
            'payment_method': 'payment_method',
            'is_excluded': 'filter'
        }
        
        return mapping.get(field_name.lower())
    
    def _pattern_type_to_rule_type(self, pattern_type: str) -> Optional[str]:
        """
        패턴 유형을 규칙 유형으로 변환합니다.
        
        Args:
            pattern_type: 패턴 유형
            
        Returns:
            Optional[str]: 규칙 유형 또는 None
        """
        mapping = {
            'category': ClassificationRule.TYPE_CATEGORY,
            'payment_method': ClassificationRule.TYPE_PAYMENT_METHOD,
            'filter': ClassificationRule.TYPE_FILTER
        }
        
        return mapping.get(pattern_type)
    
    def _extract_keywords(self, description: str) -> List[str]:
        """
        설명에서 키워드를 추출합니다.
        
        Args:
            description: 거래 설명
            
        Returns:
            List[str]: 추출된 키워드 목록
        """
        if not description:
            return []
        
        # 간단한 키워드 추출 (공백으로 분리)
        words = description.split()
        
        # 숫자와 특수문자만 있는 단어 제외
        keywords = [word for word in words if any(c.isalpha() for c in word)]
        
        # 너무 짧은 단어 제외
        keywords = [word for word in keywords if len(word) >= self.MIN_KEYWORD_LENGTH]
        
        # 중복 제거 및 최대 개수 제한
        unique_keywords = list(dict.fromkeys(keywords))
        return unique_keywords[:self.MAX_KEYWORDS_PER_TRANSACTION]
    
    def _extract_merchant_name(self, description: str) -> Optional[str]:
        """
        설명에서 상점명을 추출합니다.
        
        Args:
            description: 거래 설명
            
        Returns:
            Optional[str]: 추출된 상점명 또는 None
        """
        if not description:
            return None
        
        # 간단한 상점명 추출 (첫 번째 단어)
        words = description.split()
        if words:
            return words[0]
        return None
    
    def _find_similar_transactions(self, transaction: Transaction) -> List[Transaction]:
        """
        유사한 거래를 찾습니다.
        
        Args:
            transaction: 거래 객체
            
        Returns:
            List[Transaction]: 유사한 거래 목록
        """
        if not self.transaction_repository:
            return []
        
        # 상점명 추출
        merchant = self._extract_merchant_name(transaction.description)
        if not merchant:
            return []
        
        # 상점명으로 검색
        similar_transactions = self.transaction_repository.list({
            'description_contains': merchant,
            'limit': 20  # 더 많은 후보 검색
        })
        
        # 자기 자신 제외
        similar_transactions = [t for t in similar_transactions if t.id != transaction.id]
        
        # 유사도 계산 및 정렬
        scored_transactions = []
        for tx in similar_transactions:
            similarity = self._calculate_transaction_similarity(transaction, tx)
            if similarity >= self.SIMILARITY_THRESHOLD:
                scored_transactions.append((tx, similarity))
        
        # 유사도 순으로 정렬
        scored_transactions.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 10개만 반환
        return [tx for tx, _ in scored_transactions[:10]]
    
    def _calculate_transaction_similarity(self, tx1: Transaction, tx2: Transaction) -> float:
        """
        두 거래 간의 유사도를 계산합니다.
        
        Args:
            tx1: 첫 번째 거래
            tx2: 두 번째 거래
            
        Returns:
            float: 유사도 (0.0 ~ 1.0)
        """
        # 기본 점수
        score = 0.0
        
        # 상점명 유사도
        merchant1 = self._extract_merchant_name(tx1.description)
        merchant2 = self._extract_merchant_name(tx2.description)
        
        if merchant1 and merchant2 and merchant1 == merchant2:
            score += 0.5  # 상점명이 같으면 기본 0.5점
        
        # 설명 유사도
        keywords1 = set(self._extract_keywords(tx1.description))
        keywords2 = set(self._extract_keywords(tx2.description))
        
        if keywords1 and keywords2:
            common_keywords = keywords1.intersection(keywords2)
            keyword_similarity = len(common_keywords) / max(len(keywords1), len(keywords2))
            score += keyword_similarity * 0.3  # 키워드 유사도는 최대 0.3점
        
        # 금액 유사도
        if tx1.amount and tx2.amount:
            # 금액이 비슷하면 추가 점수
            amount_ratio = min(tx1.amount, tx2.amount) / max(tx1.amount, tx2.amount)
            if amount_ratio > 0.9:  # 금액이 90% 이상 비슷하면
                score += 0.1
        
        # 카테고리 유사도
        if tx1.category and tx2.category and tx1.category == tx2.category:
            score += 0.05
        
        # 결제 방식 유사도
        if tx1.payment_method and tx2.payment_method and tx1.payment_method == tx2.payment_method:
            score += 0.05
        
        return min(score, 1.0)  # 최대 1.0으로 제한
    
    def _extract_patterns(
        self,
        transaction: Transaction,
        pattern_type: str,
        keywords: List[str],
        target_value: str,
        similar_transactions: List[Transaction] = None
    ) -> List[LearningPattern]:
        """
        패턴을 추출합니다.
        
        Args:
            transaction: 거래 객체
            pattern_type: 패턴 유형
            keywords: 키워드 목록
            target_value: 대상 값
            similar_transactions: 유사한 거래 목록
            
        Returns:
            List[LearningPattern]: 추출된 패턴 목록
        """
        patterns = []
        
        # 상점명 패턴
        merchant = self._extract_merchant_name(transaction.description)
        if merchant:
            pattern = LearningPattern(
                pattern_type=pattern_type,
                pattern_name=f"상점-{merchant}-{target_value}",
                pattern_key=merchant,
                pattern_value=target_value,
                confidence=LearningPattern.CONFIDENCE_MEDIUM,
                metadata={
                    'source_transaction_id': transaction.transaction_id,
                    'source_description': transaction.description
                }
            )
            patterns.append(pattern)
        
        # 키워드 패턴
        for keyword in keywords:
            # 너무 짧은 키워드 제외
            if len(keyword) < self.MIN_KEYWORD_LENGTH:
                continue
                
            pattern = LearningPattern(
                pattern_type=pattern_type,
                pattern_name=f"키워드-{keyword}-{target_value}",
                pattern_key=keyword,
                pattern_value=target_value,
                confidence=LearningPattern.CONFIDENCE_LOW,
                metadata={
                    'source_transaction_id': transaction.transaction_id,
                    'source_description': transaction.description
                }
            )
            patterns.append(pattern)
        
        # 유사 거래 분석
        if similar_transactions:
            # 공통 키워드 추출
            all_descriptions = [t.description for t in similar_transactions]
            all_descriptions.append(transaction.description)
            
            common_keywords = self._extract_common_keywords(all_descriptions)
            
            for keyword in common_keywords:
                if len(keyword) < self.MIN_KEYWORD_LENGTH:
                    continue
                    
                pattern = LearningPattern(
                    pattern_type=pattern_type,
                    pattern_name=f"공통-{keyword}-{target_value}",
                    pattern_key=keyword,
                    pattern_value=target_value,
                    confidence=LearningPattern.CONFIDENCE_HIGH,
                    metadata={
                        'source_transaction_id': transaction.transaction_id,
                        'source_description': transaction.description,
                        'similar_count': len(similar_transactions)
                    }
                )
                patterns.append(pattern)
        
        return patterns
    
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
    
    def _apply_high_confidence_patterns(self, pattern_type: str) -> int:
        """
        고신뢰도 패턴을 자동으로 적용합니다.
        
        Args:
            pattern_type: 패턴 유형
            
        Returns:
            int: 적용된 패턴 수
        """
        # 고신뢰도 패턴 조회
        patterns = self.pattern_repository.list({
            'pattern_type': pattern_type,
            'confidence': LearningPattern.CONFIDENCE_HIGH,
            'status': LearningPattern.STATUS_PENDING,
            'min_occurrence': 3  # 최소 3회 이상 발생한 패턴
        })
        
        if not patterns:
            return 0
        
        # 규칙 유형 결정
        rule_type = self._pattern_type_to_rule_type(pattern_type)
        if not rule_type:
            return 0
        
        # 패턴을 규칙으로 변환
        rules_created = 0
        for pattern in patterns:
            # 규칙 생성
            rule = ClassificationRule(
                rule_name=f"자동-{pattern.pattern_value}-{pattern.pattern_key[:20]}",
                rule_type=rule_type,
                condition_type=ClassificationRule.CONDITION_CONTAINS,
                condition_value=pattern.pattern_key,
                target_value=pattern.pattern_value,
                priority=25,  # 학습된 규칙보다 높은 우선순위
                created_by=ClassificationRule.CREATOR_LEARNED
            )
            
            # 중복 규칙 확인
            existing_rules = self.rule_repository.list({
                'rule_type': rule_type,
                'condition_type': rule.condition_type,
                'condition_value': rule.condition_value,
                'target_value': rule.target_value
            })
            
            if existing_rules:
                continue
            
            # 규칙 저장
            self.rule_repository.create(rule)
            rules_created += 1
            
            # 패턴 상태 업데이트
            pattern.status = LearningPattern.STATUS_APPLIED
            self.pattern_repository.update(pattern)
            
            self._learning_stats['patterns_applied'] += 1
            self._learning_stats['rules_generated'] += 1
            
            logger.debug(f"고신뢰도 패턴 자동 적용: {pattern.pattern_name} -> {rule.rule_name}")
        
        if rules_created > 0:
            logger.info(f"고신뢰도 패턴 자동 적용: {rules_created}개 규칙 생성됨")
        
        return rules_created