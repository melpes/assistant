# -*- coding: utf-8 -*-
"""
IncomeRuleEngine 클래스 정의

수입 거래에 대한 규칙 엔진을 구현합니다.
수입 제외 규칙 적용 및 관리 기능을 제공합니다.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Pattern
import json
from pathlib import Path

# 로깅 설정
logger = logging.getLogger(__name__)

class IncomeRuleEngine:
    """
    수입 규칙 엔진
    
    수입 거래에 대한 규칙을 적용하고 관리하는 기능을 제공합니다.
    수입 제외 규칙, 수입 유형 분류 규칙 등을 처리합니다.
    """
    
    def __init__(self, rules_file: Optional[str] = None):
        """
        수입 규칙 엔진 초기화
        
        Args:
            rules_file: 규칙 파일 경로 (선택)
        """
        # 기본 규칙 설정
        self.exclude_rules = [
            {
                'name': '자금 이동',
                'pattern': r'카드잔액\s*자동충전|내계좌\s*이체|계좌이체|이체|충전|본인계좌|자기계좌|내 계좌',
                'enabled': True,
                'priority': 100
            },
            {
                'name': '환불 및 반환',
                'pattern': r'환불|반환|취소',
                'enabled': True,
                'priority': 90
            },
            {
                'name': '카드 관련',
                'pattern': r'카드잔액|자동충전',
                'enabled': True,
                'priority': 80
            },
            {
                'name': '임시 보관',
                'pattern': r'임시 보관|임시보관|보관금',
                'enabled': True,
                'priority': 70
            }
        ]
        
        self.income_type_rules = [
            {
                'name': '급여',
                'pattern': r'급여|월급|상여금|연봉|인건비|수당|주급|보너스|성과급',
                'target': '급여',
                'enabled': True,
                'priority': 100
            },
            {
                'name': '용돈',
                'pattern': r'용돈|선물|축하금|생일|대회|뒷풀이|간식|지원금',
                'target': '용돈',
                'enabled': True,
                'priority': 90
            },
            {
                'name': '이자',
                'pattern': r'이자|배당|수익|예금이자|통장 이자|이자입금|적금|펀드',
                'target': '이자',
                'enabled': True,
                'priority': 80
            },
            {
                'name': '환급',
                'pattern': r'환급|세금|공제|환급금|보험금|취소|반환|환불',
                'target': '환급',
                'enabled': True,
                'priority': 70
            },
            {
                'name': '부수입',
                'pattern': r'부수입|알바|아르바이트|프리랜서|외주|수당|강의|강연',
                'target': '부수입',
                'enabled': True,
                'priority': 60
            },
            {
                'name': '임대수입',
                'pattern': r'임대|월세|전세|임차|부동산|집세|관리비',
                'target': '임대수입',
                'enabled': True,
                'priority': 50
            },
            {
                'name': '판매수입',
                'pattern': r'판매|중고|장터|마켓|거래|양도|매출|수익',
                'target': '판매수입',
                'enabled': True,
                'priority': 40
            }
        ]
        
        # 컴파일된 정규식 캐시
        self._exclude_regex_cache = {}
        self._income_type_regex_cache = {}
        
        # 사용자 정의 규칙 로드
        if rules_file:
            self.load_rules(rules_file)
    
    def load_rules(self, rules_file: str) -> None:
        """
        규칙 파일에서 규칙을 로드합니다.
        
        Args:
            rules_file: 규칙 파일 경로
        """
        try:
            path = Path(rules_file)
            if not path.exists():
                logger.warning(f"규칙 파일이 존재하지 않습니다: {rules_file}")
                return
            
            with open(rules_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            if 'exclude_rules' in rules:
                self.exclude_rules = rules['exclude_rules']
                logger.info(f"{len(self.exclude_rules)}개의 수입 제외 규칙을 로드했습니다.")
            
            if 'income_type_rules' in rules:
                self.income_type_rules = rules['income_type_rules']
                logger.info(f"{len(self.income_type_rules)}개의 수입 유형 규칙을 로드했습니다.")
            
            # 캐시 초기화
            self._exclude_regex_cache = {}
            self._income_type_regex_cache = {}
            
        except Exception as e:
            logger.error(f"규칙 파일 로드 중 오류 발생: {e}")
    
    def save_rules(self, rules_file: str) -> None:
        """
        규칙을 파일에 저장합니다.
        
        Args:
            rules_file: 규칙 파일 경로
        """
        try:
            rules = {
                'exclude_rules': self.exclude_rules,
                'income_type_rules': self.income_type_rules
            }
            
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            
            logger.info(f"규칙을 파일에 저장했습니다: {rules_file}")
            
        except Exception as e:
            logger.error(f"규칙 파일 저장 중 오류 발생: {e}")
    
    def is_income_excluded(self, description: str, memo: str = '') -> bool:
        """
        수입 거래가 제외 대상인지 확인합니다.
        
        Args:
            description: 거래 설명
            memo: 메모 (선택)
            
        Returns:
            bool: 제외 대상이면 True, 그렇지 않으면 False
        """
        description = str(description).lower()
        memo = str(memo).lower()
        
        # 우선순위 순으로 규칙 정렬
        sorted_rules = sorted(self.exclude_rules, key=lambda x: x.get('priority', 0), reverse=True)
        
        for rule in sorted_rules:
            if not rule.get('enabled', True):
                continue
            
            pattern = rule['pattern']
            
            # 정규식 캐시 확인
            if pattern not in self._exclude_regex_cache:
                try:
                    self._exclude_regex_cache[pattern] = re.compile(pattern, re.IGNORECASE)
                except re.error:
                    logger.warning(f"잘못된 정규식 패턴: {pattern}")
                    continue
            
            regex = self._exclude_regex_cache[pattern]
            
            # 설명과 메모에서 패턴 검색
            if regex.search(description) or (memo and regex.search(memo)):
                logger.debug(f"수입 제외 규칙 적용: {rule['name']}, 설명: {description}")
                return True
        
        return False
    
    def categorize_income(self, description: str, amount: float, memo: str = '') -> str:
        """
        수입 거래를 카테고리로 분류합니다.
        
        Args:
            description: 거래 설명
            amount: 거래 금액
            memo: 메모 (선택)
            
        Returns:
            str: 수입 카테고리
        """
        description = str(description).lower()
        memo = str(memo).lower()
        
        # 우선순위 순으로 규칙 정렬
        sorted_rules = sorted(self.income_type_rules, key=lambda x: x.get('priority', 0), reverse=True)
        
        for rule in sorted_rules:
            if not rule.get('enabled', True):
                continue
            
            pattern = rule['pattern']
            
            # 정규식 캐시 확인
            if pattern not in self._income_type_regex_cache:
                try:
                    self._income_type_regex_cache[pattern] = re.compile(pattern, re.IGNORECASE)
                except re.error:
                    logger.warning(f"잘못된 정규식 패턴: {pattern}")
                    continue
            
            regex = self._income_type_regex_cache[pattern]
            
            # 설명과 메모에서 패턴 검색
            if regex.search(description) or (memo and regex.search(memo)):
                logger.debug(f"수입 유형 규칙 적용: {rule['name']}, 설명: {description}, 유형: {rule['target']}")
                return rule['target']
        
        # 금액 기반 추정 (규칙에 매칭되지 않은 경우)
        if amount >= 1000000:  # 100만원 이상
            return '급여'
        elif 500000 <= amount < 1000000:  # 50만원 ~ 100만원
            return '부수입'
        elif 100000 <= amount < 500000:  # 10만원 ~ 50만원
            return '부수입'
        elif 10000 <= amount < 100000:  # 1만원 ~ 10만원
            return '용돈'
        else:  # 1만원 미만
            return '기타수입'
    
    def add_exclude_rule(self, name: str, pattern: str, priority: int = 50) -> Dict[str, Any]:
        """
        수입 제외 규칙을 추가합니다.
        
        Args:
            name: 규칙 이름
            pattern: 정규식 패턴
            priority: 우선순위 (기본값: 50)
            
        Returns:
            Dict[str, Any]: 추가된 규칙
            
        Raises:
            ValueError: 유효하지 않은 정규식 패턴인 경우
        """
        # 정규식 유효성 검사
        try:
            re.compile(pattern)
        except re.error as e:
            raise ValueError(f"유효하지 않은 정규식 패턴입니다: {e}")
        
        # 규칙 추가
        rule = {
            'name': name,
            'pattern': pattern,
            'enabled': True,
            'priority': priority
        }
        
        self.exclude_rules.append(rule)
        logger.info(f"수입 제외 규칙 추가: {name}")
        
        # 캐시 초기화
        self._exclude_regex_cache = {}
        
        return rule
    
    def add_income_type_rule(self, name: str, pattern: str, target: str, priority: int = 50) -> Dict[str, Any]:
        """
        수입 유형 규칙을 추가합니다.
        
        Args:
            name: 규칙 이름
            pattern: 정규식 패턴
            target: 대상 카테고리
            priority: 우선순위 (기본값: 50)
            
        Returns:
            Dict[str, Any]: 추가된 규칙
            
        Raises:
            ValueError: 유효하지 않은 정규식 패턴인 경우
        """
        # 정규식 유효성 검사
        try:
            re.compile(pattern)
        except re.error as e:
            raise ValueError(f"유효하지 않은 정규식 패턴입니다: {e}")
        
        # 규칙 추가
        rule = {
            'name': name,
            'pattern': pattern,
            'target': target,
            'enabled': True,
            'priority': priority
        }
        
        self.income_type_rules.append(rule)
        logger.info(f"수입 유형 규칙 추가: {name} -> {target}")
        
        # 캐시 초기화
        self._income_type_regex_cache = {}
        
        return rule
    
    def update_rule_status(self, rule_type: str, rule_name: str, enabled: bool) -> bool:
        """
        규칙의 활성화 상태를 업데이트합니다.
        
        Args:
            rule_type: 규칙 유형 ('exclude' 또는 'income_type')
            rule_name: 규칙 이름
            enabled: 활성화 여부
            
        Returns:
            bool: 업데이트 성공 여부
        """
        if rule_type == 'exclude':
            rules = self.exclude_rules
        elif rule_type == 'income_type':
            rules = self.income_type_rules
        else:
            logger.warning(f"알 수 없는 규칙 유형: {rule_type}")
            return False
        
        for rule in rules:
            if rule['name'] == rule_name:
                rule['enabled'] = enabled
                logger.info(f"규칙 상태 업데이트: {rule_name}, 활성화={enabled}")
                return True
        
        logger.warning(f"규칙을 찾을 수 없음: {rule_name}")
        return False
    
    def delete_rule(self, rule_type: str, rule_name: str) -> bool:
        """
        규칙을 삭제합니다.
        
        Args:
            rule_type: 규칙 유형 ('exclude' 또는 'income_type')
            rule_name: 규칙 이름
            
        Returns:
            bool: 삭제 성공 여부
        """
        if rule_type == 'exclude':
            rules = self.exclude_rules
            cache = self._exclude_regex_cache
        elif rule_type == 'income_type':
            rules = self.income_type_rules
            cache = self._income_type_regex_cache
        else:
            logger.warning(f"알 수 없는 규칙 유형: {rule_type}")
            return False
        
        for i, rule in enumerate(rules):
            if rule['name'] == rule_name:
                del rules[i]
                logger.info(f"규칙 삭제: {rule_name}")
                
                # 캐시 초기화
                cache.clear()
                
                return True
        
        logger.warning(f"규칙을 찾을 수 없음: {rule_name}")
        return False
    
    def get_rules(self, rule_type: str) -> List[Dict[str, Any]]:
        """
        규칙 목록을 반환합니다.
        
        Args:
            rule_type: 규칙 유형 ('exclude' 또는 'income_type')
            
        Returns:
            List[Dict[str, Any]]: 규칙 목록
        """
        if rule_type == 'exclude':
            return sorted(self.exclude_rules, key=lambda x: x.get('priority', 0), reverse=True)
        elif rule_type == 'income_type':
            return sorted(self.income_type_rules, key=lambda x: x.get('priority', 0), reverse=True)
        else:
            logger.warning(f"알 수 없는 규칙 유형: {rule_type}")
            return []
    
    def apply_rules_to_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        거래에 모든 규칙을 적용합니다.
        
        Args:
            transaction: 거래 데이터
            
        Returns:
            Dict[str, Any]: 규칙이 적용된 거래 데이터
        """
        description = transaction.get('description', '')
        memo = transaction.get('memo', '')
        amount = float(transaction.get('amount', 0))
        
        # 수입 제외 여부 결정
        is_excluded = self.is_income_excluded(description, memo)
        transaction['is_excluded'] = is_excluded
        
        # 카테고리가 없거나 '기타수입'인 경우에만 자동 분류
        if not transaction.get('category') or transaction.get('category') == '기타수입':
            category = self.categorize_income(description, amount, memo)
            transaction['category'] = category
        
        return transaction