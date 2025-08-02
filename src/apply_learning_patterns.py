# -*- coding: utf-8 -*-
"""
학습 패턴 적용 스크립트

학습된 패턴을 규칙으로 변환하여 적용하는 스크립트입니다.
"""

import argparse
import logging
import sys
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# 로거 설정
logger = logging.getLogger(__name__)

# 모듈 경로 추가
sys.path.append('.')

from src.repositories.db_connection import DatabaseConnection
from src.repositories.rule_repository import RuleRepository
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.learning_pattern_repository import LearningPatternRepository
from src.learning_engine import LearningEngine


def main():
    """
    메인 함수
    """
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description='학습된 패턴을 규칙으로 적용합니다.')
    parser.add_argument('--type', choices=['category', 'payment_method', 'filter', 'all'], 
                        default='all', help='적용할 패턴 유형')
    parser.add_argument('--confidence', choices=['low', 'medium', 'high'], 
                        default='medium', help='최소 신뢰도')
    parser.add_argument('--stats', action='store_true', help='패턴 통계 출력')
    parser.add_argument('--filters', action='store_true', help='동적 필터 생성')
    parser.add_argument('--recurring', action='store_true', help='반복 거래 패턴 감지')
    parser.add_argument('--days', type=int, default=90, help='반복 패턴 검색 기간(일)')
    parser.add_argument('--detect-changes', action='store_true', help='패턴 변화 감지')
    
    args = parser.parse_args()
    
    # 데이터베이스 연결
    db_connection = DatabaseConnection('personal_data.db')
    
    try:
        # 저장소 초기화
        rule_repository = RuleRepository(db_connection)
        transaction_repository = TransactionRepository(db_connection)
        pattern_repository = LearningPatternRepository(db_connection)
        
        # 학습 엔진 초기화
        learning_engine = LearningEngine(
            pattern_repository=pattern_repository,
            rule_repository=rule_repository,
            transaction_repository=transaction_repository
        )
        
        # 패턴 통계 출력
        if args.stats:
            print("\n패턴 통계:")
            stats = learning_engine.get_learning_stats()
            print(f"처리된 수정사항: {stats['corrections_processed']}")
            print(f"추출된 패턴: {stats['patterns_extracted']}")
            print(f"적용된 패턴: {stats['patterns_applied']}")
            print(f"생성된 규칙: {stats['rules_generated']}")
            
            # 카테고리 패턴 통계
            category_stats = stats.get('category_patterns', {})
            print(f"\n카테고리 패턴: {category_stats.get('total_count', 0)}개")
            print(f"- 대기 중: {category_stats.get('status_counts', {}).get('pending', 0)}개")
            print(f"- 적용됨: {category_stats.get('status_counts', {}).get('applied', 0)}개")
            
            # 결제 방식 패턴 통계
            payment_stats = stats.get('payment_patterns', {})
            print(f"\n결제 방식 패턴: {payment_stats.get('total_count', 0)}개")
            print(f"- 대기 중: {payment_stats.get('status_counts', {}).get('pending', 0)}개")
            print(f"- 적용됨: {payment_stats.get('status_counts', {}).get('applied', 0)}개")
        
        # 패턴 적용
        if args.type != 'all':
            # 특정 유형의 패턴만 적용
            rules_created = learning_engine.apply_patterns_to_rules(args.type, args.confidence)
            print(f"\n{args.type} 패턴 적용 결과: {rules_created}개 규칙 생성됨")
        else:
            # 모든 유형의 패턴 적용
            category_rules = learning_engine.apply_patterns_to_rules('category', args.confidence)
            payment_rules = learning_engine.apply_patterns_to_rules('payment_method', args.confidence)
            filter_rules = learning_engine.apply_patterns_to_rules('filter', args.confidence)
            
            total_rules = category_rules + payment_rules + filter_rules
            print(f"\n패턴 적용 결과: 총 {total_rules}개 규칙 생성됨")
            print(f"- 카테고리 규칙: {category_rules}개")
            print(f"- 결제 방식 규칙: {payment_rules}개")
            print(f"- 필터 규칙: {filter_rules}개")
        
        # 동적 필터 생성
        if args.filters:
            filters = learning_engine.generate_dynamic_filters()
            print(f"\n동적 필터 생성 결과: {len(filters)}개 필터 생성됨")
            
            for i, filter_config in enumerate(filters[:5], 1):
                print(f"{i}. {filter_config['name']} - {filter_config['description']}")
                if 'conditions' in filter_config and filter_config['conditions']:
                    condition = filter_config['conditions'][0]
                    values = condition.get('values', [])
                    print(f"   조건: {condition.get('field')} {condition.get('operator')} " +
                          f"{', '.join(values[:3])}" + ("..." if len(values) > 3 else ""))
        
        # 반복 거래 패턴 감지
        if args.recurring:
            recurring_patterns = learning_engine.detect_recurring_patterns(days=args.days)
            print(f"\n반복 거래 패턴 감지 결과: {len(recurring_patterns)}개 패턴 발견")
            
            for i, pattern in enumerate(recurring_patterns[:5], 1):
                print(f"{i}. {pattern['merchant']} - {pattern['interval_days']}일 간격, " +
                      f"금액: {pattern['common_amount']}")
                print(f"   카테고리: {pattern['category']}, 결제 방식: {pattern['payment_method']}")
                print(f"   다음 예상일: {pattern['next_expected_date'].strftime('%Y-%m-%d')}")
        
        # 패턴 변화 감지
        pattern_changes = learning_engine.detect_pattern_changes()
        if pattern_changes:
            print(f"\n패턴 변화 감지 결과: {len(pattern_changes)}개 변화 발견")
            
            # 중요 변화만 표시
            significant_changes = [c for c in pattern_changes if c['change_score'] > learning_engine.PATTERN_CHANGE_THRESHOLD]
            print(f"중요 변화: {len(significant_changes)}개")
            
            for i, change in enumerate(significant_changes[:5], 1):
                print(f"{i}. {change['description']}")
        
        print("\n작업이 완료되었습니다.")
        
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        sys.exit(1)
    finally:
        # 데이터베이스 연결 종료
        db_connection.close()


if __name__ == "__main__":
    main()