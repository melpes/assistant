# -*- coding: utf-8 -*-
"""
수동 수입 입력 스크립트

사용자가 수동으로 수입 거래를 입력할 수 있는 CLI 인터페이스를 제공합니다.
수입 유형 자동 분류, 수입 제외 규칙 적용, 수입 패턴 인식 기능을 포함합니다.
"""

import os
import sys
import logging
from datetime import datetime
from decimal import Decimal
import argparse
import json
from pathlib import Path

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.ingesters.income_ingester import IncomeIngester
from src.ingesters.income_rule_engine import IncomeRuleEngine
from src.ingesters.income_pattern_analyzer import IncomePatternAnalyzer
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.db_connection import DatabaseConnection
from src.models.transaction import Transaction

def setup_argparse() -> argparse.ArgumentParser:
    """
    명령줄 인자 파서를 설정합니다.
    
    Returns:
        argparse.ArgumentParser: 설정된 인자 파서
    """
    parser = argparse.ArgumentParser(description='수동 수입 입력 도구')
    
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 로깅 활성화')
    parser.add_argument('--batch', '-b', action='store_true', help='일괄 입력 모드 활성화')
    parser.add_argument('--analyze', '-a', action='store_true', help='수입 패턴 분석 실행')
    parser.add_argument('--predict', '-p', action='store_true', help='미래 수입 예측 실행')
    parser.add_argument('--summary', '-s', action='store_true', help='정기 수입 요약 표시')
    parser.add_argument('--months', '-m', type=int, default=3, help='예측할 개월 수 (기본값: 3)')
    parser.add_argument('--rules', '-r', type=str, help='규칙 파일 경로')
    parser.add_argument('--history', type=str, help='수입 내역 기록 파일 경로')
    
    return parser

def add_manual_income(rule_engine=None, pattern_analyzer=None):
    """
    수동으로 수입 거래를 입력합니다.
    
    Args:
        rule_engine: 규칙 엔진 (선택)
        pattern_analyzer: 패턴 분석기 (선택)
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
        payment_methods = ['계좌입금', '현금', '급여이체', '이자입금', '기타입금']
        
        for i, method in enumerate(payment_methods, 1):
            print(f"{i}. {method}")
        
        payment_choice = input(f"선택 (1-{len(payment_methods)}): ").strip()
        try:
            payment_method = payment_methods[int(payment_choice) - 1]
        except (ValueError, IndexError):
            payment_method = '계좌입금'
        
        # 수입 유형 선택
        print("\n수입 유형을 선택하세요:")
        categories = ['급여', '용돈', '이자', '환급', '부수입', '임대수입', '판매수입', '기타수입']
        
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")
        
        cat_choice = input(f"선택 (1-{len(categories)}): ").strip()
        try:
            category = categories[int(cat_choice) - 1]
        except (ValueError, IndexError):
            category = '기타수입'
        
        memo = input("메모 (선택사항): ").strip()
        
        # IncomeIngester를 사용하여 수입 추가
        db_connection = DatabaseConnection()
        ingester = IncomeIngester()
        transaction_data = ingester.add_income(
            transaction_date=transaction_date,
            description=description,
            amount=amount,
            category=category,
            payment_method=payment_method,
            memo=memo
        )
        
        # 규칙 엔진 적용
        if rule_engine:
            transaction_data = rule_engine.apply_rules_to_transaction(transaction_data)
        
        # 데이터베이스에 저장
        repo = TransactionRepository(db_connection)
        transaction = Transaction.from_dict(transaction_data)
        repo.create(transaction)
        
        # 패턴 분석기에 추가
        if pattern_analyzer:
            pattern_analyzer.add_transaction(transaction_data)
            pattern_analyzer.save_history()
        
        print(f"\n✅ 수입 내역이 성공적으로 추가되었습니다!")
        print(f"   날짜: {transaction_date}")
        print(f"   내용: {description}")
        print(f"   금액: {amount:,}원")
        print(f"   입금방식: {payment_method}")
        print(f"   수입유형: {transaction_data['category']}")
        
        if transaction_data.get('is_excluded', False):
            print(f"   ⚠️ 이 거래는 수입 제외 대상으로 분류되었습니다.")
        
    except KeyboardInterrupt:
        print("\n\n취소되었습니다.")
    except Exception as e:
        logger.error(f"오류가 발생했습니다: {e}")
        print(f"오류가 발생했습니다: {e}")

def batch_add_incomes(rule_engine=None, pattern_analyzer=None):
    """
    여러 수입 거래를 한번에 추가합니다.
    
    Args:
        rule_engine: 규칙 엔진 (선택)
        pattern_analyzer: 패턴 분석기 (선택)
    """
    print("=== 일괄 수입 내역 추가 ===")
    print("형식: 날짜,내용,금액,수입유형(선택),입금방식(선택),메모(선택)")
    print("예시: 2024-01-15,월급,2500000,급여,급여이체,1월 급여")
    print("입력 완료 후 빈 줄을 입력하세요.\n")
    
    transactions = []
    while True:
        line = input("수입 내역: ").strip()
        if not line:
            break
            
        try:
            parts = line.split(',')
            if len(parts) < 3:
                print("최소 날짜,내용,금액은 입력해야 합니다.")
                continue
                
            date_str = parts[0].strip()
            description = parts[1].strip()
            amount = float(parts[2].strip())
            
            if amount <= 0:
                print("금액은 0보다 커야 합니다.")
                continue
            
            category = parts[3].strip() if len(parts) > 3 and parts[3].strip() else None
            payment_method = parts[4].strip() if len(parts) > 4 and parts[4].strip() else '계좌입금'
            memo = parts[5].strip() if len(parts) > 5 else ''
            
            transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            transactions.append({
                'transaction_date': transaction_date,
                'description': description,
                'amount': amount,
                'category': category,
                'payment_method': payment_method,
                'memo': memo
            })
            
        except ValueError as e:
            print(f"입력 오류: {e}")
        except Exception as e:
            print(f"입력 오류: {e}")
    
    if not transactions:
        print("추가할 수입 내역이 없습니다.")
        return
    
    try:
        # IncomeIngester를 사용하여 일괄 추가
        db_connection = DatabaseConnection()
        ingester = IncomeIngester()
        transaction_data_list = ingester.batch_add_incomes(transactions)
        
        # 규칙 엔진 적용
        if rule_engine:
            for i, transaction_data in enumerate(transaction_data_list):
                transaction_data_list[i] = rule_engine.apply_rules_to_transaction(transaction_data)
        
        # 데이터베이스에 저장
        repo = TransactionRepository(db_connection)
        saved_count = 0
        excluded_count = 0
        
        for transaction_data in transaction_data_list:
            transaction = Transaction.from_dict(transaction_data)
            repo.create(transaction)
            saved_count += 1
            
            if transaction_data.get('is_excluded', False):
                excluded_count += 1
            
            # 패턴 분석기에 추가
            if pattern_analyzer:
                pattern_analyzer.add_transaction(transaction_data)
        
        # 패턴 분석기 저장
        if pattern_analyzer:
            pattern_analyzer.save_history()
        
        print(f"\n✅ {saved_count}개의 수입 내역이 성공적으로 추가되었습니다!")
        if excluded_count > 0:
            print(f"   ⚠️ {excluded_count}개의 거래가 수입 제외 대상으로 분류되었습니다.")
        
    except Exception as e:
        logger.error(f"오류가 발생했습니다: {e}")
        print(f"오류가 발생했습니다: {e}")

def analyze_income_patterns(pattern_analyzer):
    """
    수입 패턴을 분석합니다.
    
    Args:
        pattern_analyzer: 패턴 분석기
    """
    print("=== 수입 패턴 분석 ===")
    
    try:
        # 패턴 분석
        result = pattern_analyzer.analyze_patterns()
        
        # 정기 패턴 출력
        print("\n정기 수입 패턴:")
        if result['regular_patterns']:
            for category, pattern in result['regular_patterns'].items():
                confidence = pattern.get('confidence', 0) * 100
                print(f"  - {category}: {pattern['period_type']} 주기, 평균 {pattern['avg_amount']:,.0f}원, 신뢰도 {confidence:.1f}%")
                print(f"    다음 예상일: {pattern['next_expected_date']}")
        else:
            print("  정기 수입 패턴이 발견되지 않았습니다.")
        
        # 월별 트렌드 출력
        print("\n월별 수입 트렌드:")
        monthly_totals = result['income_trends'].get('monthly_totals', [])
        if monthly_totals:
            for month_data in monthly_totals:
                print(f"  - {month_data['month']}: {month_data['total']:,.0f}원")
        else:
            print("  월별 트렌드 데이터가 없습니다.")
        
        # 패턴 분석기 저장
        pattern_analyzer.save_history()
        
    except Exception as e:
        logger.error(f"패턴 분석 중 오류 발생: {e}")
        print(f"패턴 분석 중 오류가 발생했습니다: {e}")

def predict_future_income(pattern_analyzer, months_ahead=3):
    """
    미래 수입을 예측합니다.
    
    Args:
        pattern_analyzer: 패턴 분석기
        months_ahead: 예측할 개월 수
    """
    print(f"=== 미래 수입 예측 ({months_ahead}개월) ===")
    
    try:
        # 미래 수입 예측
        result = pattern_analyzer.predict_future_income(months_ahead)
        
        # 예측 결과 출력
        print("\n예상 수입:")
        predictions = result['predictions']
        if predictions:
            # 날짜별로 그룹화
            by_date = {}
            for prediction in predictions:
                date_str = prediction['date']
                if date_str not in by_date:
                    by_date[date_str] = []
                by_date[date_str].append(prediction)
            
            # 날짜순으로 출력
            for date_str in sorted(by_date.keys()):
                date_predictions = by_date[date_str]
                total = sum(p['amount'] for p in date_predictions)
                print(f"  - {date_str}: 총 {total:,.0f}원")
                for prediction in date_predictions:
                    confidence = prediction['confidence'] * 100
                    print(f"    • {prediction['category']}: {prediction['amount']:,.0f}원 (신뢰도 {confidence:.1f}%)")
        else:
            print("  예측 가능한 수입이 없습니다.")
        
        # 월별 예상 총액 출력
        print("\n월별 예상 총액:")
        monthly_totals = result['monthly_totals']
        if monthly_totals:
            for month_data in monthly_totals:
                print(f"  - {month_data['month']}: {month_data['total']:,.0f}원")
        else:
            print("  월별 예상 데이터가 없습니다.")
        
    except Exception as e:
        logger.error(f"수입 예측 중 오류 발생: {e}")
        print(f"수입 예측 중 오류가 발생했습니다: {e}")

def show_income_summary(pattern_analyzer):
    """
    정기 수입 요약을 표시합니다.
    
    Args:
        pattern_analyzer: 패턴 분석기
    """
    print("=== 정기 수입 요약 ===")
    
    try:
        # 정기 수입 요약
        result = pattern_analyzer.get_regular_income_summary()
        
        # 요약 정보 출력
        print(f"\n월 환산 정기 수입: {result['monthly_equivalent']:,.0f}원")
        print(f"정기 수입 항목 수: {result['regular_income_count']}개")
        print(f"높은 신뢰도 항목 수: {result['high_confidence_count']}개")
        
        # 주기별 통계 출력
        print("\n주기별 통계:")
        by_period_type = result['by_period_type']
        if by_period_type:
            for period_type, stats in by_period_type.items():
                print(f"  - {period_type}: {stats['count']}개 항목, 총 {stats['total']:,.0f}원")
        else:
            print("  주기별 통계 데이터가 없습니다.")
        
    except Exception as e:
        logger.error(f"수입 요약 중 오류 발생: {e}")
        print(f"수입 요약 중 오류가 발생했습니다: {e}")

def main():
    """
    메인 함수
    """
    parser = setup_argparse()
    args = parser.parse_args()
    
    # 상세 로깅 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 기본 파일 경로 설정
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    
    # 디렉토리가 없으면 생성
    os.makedirs(data_dir, exist_ok=True)
    
    # 규칙 파일 경로
    rules_file = args.rules or os.path.join(data_dir, 'income_rules.json')
    
    # 수입 내역 기록 파일 경로
    history_file = args.history or os.path.join(data_dir, 'income_history.json')
    
    # 규칙 엔진 초기화
    rule_engine = IncomeRuleEngine(rules_file if os.path.exists(rules_file) else None)
    
    # 패턴 분석기 초기화
    pattern_analyzer = IncomePatternAnalyzer(history_file if os.path.exists(history_file) else None)
    pattern_analyzer.history_file = history_file
    
    # 명령 실행
    if args.analyze:
        analyze_income_patterns(pattern_analyzer)
    elif args.predict:
        predict_future_income(pattern_analyzer, args.months)
    elif args.summary:
        show_income_summary(pattern_analyzer)
    elif args.batch:
        batch_add_incomes(rule_engine, pattern_analyzer)
    else:
        add_manual_income(rule_engine, pattern_analyzer)

if __name__ == '__main__':
    main()