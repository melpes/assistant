# -*- coding: utf-8 -*-
"""
수입 관리 시스템 메인 스크립트

수입 거래 관리, 분석, 예측 기능을 제공하는 통합 CLI 인터페이스입니다.
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
import argparse
import json
from pathlib import Path
import pandas as pd

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
    parser = argparse.ArgumentParser(description='수입 관리 시스템')
    
    # 기본 옵션
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 로깅 활성화')
    parser.add_argument('--rules', '-r', type=str, help='규칙 파일 경로')
    parser.add_argument('--history', type=str, help='수입 내역 기록 파일 경로')
    parser.add_argument('--db', type=str, help='데이터베이스 파일 경로')
    
    # 서브커맨드 설정
    subparsers = parser.add_subparsers(dest='command', help='명령')
    
    # 수입 추가 명령
    add_parser = subparsers.add_parser('add', help='수입 추가')
    add_parser.add_argument('--batch', '-b', action='store_true', help='일괄 입력 모드 활성화')
    add_parser.add_argument('--file', '-f', type=str, help='입력 파일 경로 (CSV, XLSX, JSON)')
    
    # 분석 명령
    analyze_parser = subparsers.add_parser('analyze', help='수입 패턴 분석')
    analyze_parser.add_argument('--months', '-m', type=int, default=6, help='분석할 개월 수 (기본값: 6)')
    
    # 예측 명령
    predict_parser = subparsers.add_parser('predict', help='미래 수입 예측')
    predict_parser.add_argument('--months', '-m', type=int, default=3, help='예측할 개월 수 (기본값: 3)')
    
    # 요약 명령
    summary_parser = subparsers.add_parser('summary', help='정기 수입 요약')
    
    # 규칙 관리 명령
    rule_parser = subparsers.add_parser('rule', help='규칙 관리')
    rule_subparsers = rule_parser.add_subparsers(dest='rule_command', help='규칙 명령')
    
    # 규칙 목록 명령
    rule_list_parser = rule_subparsers.add_parser('list', help='규칙 목록 표시')
    rule_list_parser.add_argument('--type', '-t', choices=['exclude', 'income_type'], default='all', help='규칙 유형')
    
    # 규칙 추가 명령
    rule_add_parser = rule_subparsers.add_parser('add', help='규칙 추가')
    rule_add_parser.add_argument('--type', '-t', choices=['exclude', 'income_type'], required=True, help='규칙 유형')
    rule_add_parser.add_argument('--name', '-n', required=True, help='규칙 이름')
    rule_add_parser.add_argument('--pattern', '-p', required=True, help='정규식 패턴')
    rule_add_parser.add_argument('--target', help='대상 카테고리 (income_type 규칙에만 필요)')
    rule_add_parser.add_argument('--priority', type=int, default=50, help='우선순위 (기본값: 50)')
    
    # 규칙 상태 변경 명령
    rule_status_parser = rule_subparsers.add_parser('status', help='규칙 상태 변경')
    rule_status_parser.add_argument('--type', '-t', choices=['exclude', 'income_type'], required=True, help='규칙 유형')
    rule_status_parser.add_argument('--name', '-n', required=True, help='규칙 이름')
    rule_status_parser.add_argument('--enabled', '-e', choices=['yes', 'no'], required=True, help='활성화 여부')
    
    # 규칙 삭제 명령
    rule_delete_parser = rule_subparsers.add_parser('delete', help='규칙 삭제')
    rule_delete_parser.add_argument('--type', '-t', choices=['exclude', 'income_type'], required=True, help='규칙 유형')
    rule_delete_parser.add_argument('--name', '-n', required=True, help='규칙 이름')
    
    # 조회 명령
    list_parser = subparsers.add_parser('list', help='수입 거래 조회')
    list_parser.add_argument('--start', help='시작 날짜 (YYYY-MM-DD)')
    list_parser.add_argument('--end', help='종료 날짜 (YYYY-MM-DD)')
    list_parser.add_argument('--category', '-c', help='카테고리')
    list_parser.add_argument('--min', type=float, help='최소 금액')
    list_parser.add_argument('--max', type=float, help='최대 금액')
    list_parser.add_argument('--limit', '-l', type=int, default=20, help='최대 결과 수 (기본값: 20)')
    list_parser.add_argument('--excluded', '-e', action='store_true', help='제외 대상 포함')
    list_parser.add_argument('--output', '-o', help='출력 파일 경로 (CSV)')
    
    # 보고서 명령
    report_parser = subparsers.add_parser('report', help='수입 보고서 생성')
    report_parser.add_argument('--type', '-t', choices=['monthly', 'category', 'trend'], required=True, help='보고서 유형')
    report_parser.add_argument('--months', '-m', type=int, default=6, help='보고서 기간 (개월, 기본값: 6)')
    report_parser.add_argument('--output', '-o', required=True, help='출력 파일 경로 (CSV)')
    
    return parser

def add_manual_income(rule_engine, pattern_analyzer):
    """
    수동으로 수입 거래를 입력합니다.
    
    Args:
        rule_engine: 규칙 엔진
        pattern_analyzer: 패턴 분석기
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

def batch_add_incomes(rule_engine, pattern_analyzer, file_path=None):
    """
    여러 수입 거래를 한번에 추가합니다.
    
    Args:
        rule_engine: 규칙 엔진
        pattern_analyzer: 패턴 분석기
        file_path: 입력 파일 경로 (선택)
    """
    if file_path:
        # 파일에서 거래 데이터 로드
        print(f"=== 파일에서 수입 내역 추가: {file_path} ===")
        
        try:
            ingester = IncomeIngester()
            
            # 파일 유효성 검증
            if not ingester.validate_file(file_path):
                print(f"유효하지 않은 파일 형식입니다: {file_path}")
                return
            
            # 거래 데이터 추출
            raw_data = ingester.extract_transactions(file_path)
            
            # 데이터 정규화
            transaction_data_list = ingester.normalize_data(raw_data)
            
            print(f"{len(transaction_data_list)}개의 거래 데이터를 로드했습니다.")
            
        except Exception as e:
            logger.error(f"파일 로드 중 오류 발생: {e}")
            print(f"파일 로드 중 오류가 발생했습니다: {e}")
            return
    else:
        # 수동 입력
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
        
        # 수입 추가
        ingester = IncomeIngester()
        transaction_data_list = ingester.batch_add_incomes(transactions)
    
    try:
        # 규칙 엔진 적용
        if rule_engine:
            for i, transaction_data in enumerate(transaction_data_list):
                transaction_data_list[i] = rule_engine.apply_rules_to_transaction(transaction_data)
        
        # 데이터베이스에 저장
        db_connection = DatabaseConnection()
        repo = TransactionRepository(db_connection)
        saved_count = 0
        excluded_count = 0
        
        for transaction_data in transaction_data_list:
            # 중복 확인
            if repo.exists_by_transaction_id(transaction_data['transaction_id']):
                logger.info(f"중복 거래 건너뜀: {transaction_data['transaction_id']}")
                continue
            
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

def analyze_income_patterns(pattern_analyzer, months=6):
    """
    수입 패턴을 분석합니다.
    
    Args:
        pattern_analyzer: 패턴 분석기
        months: 분석할 개월 수
    """
    print(f"=== 수입 패턴 분석 ({months}개월) ===")
    
    try:
        # 데이터베이스에서 거래 로드
        db_connection = DatabaseConnection()
        repo = TransactionRepository(db_connection)
        
        # 분석 기간 설정
        end_date = date.today()
        start_date = end_date - timedelta(days=30 * months)
        
        # 수입 거래 조회
        transactions = repo.list({
            'transaction_type': Transaction.TYPE_INCOME,
            'start_date': start_date,
            'end_date': end_date,
            'include_excluded': False
        })
        
        print(f"{len(transactions)}개의 수입 거래를 로드했습니다.")
        
        # 패턴 분석기에 거래 추가
        for transaction in transactions:
            pattern_analyzer.add_transaction(transaction.to_dict())
        
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
        # 패턴 분석
        pattern_analyzer.analyze_patterns()
        
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
        # 패턴 분석
        pattern_analyzer.analyze_patterns()
        
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

def list_rules(rule_engine, rule_type='all'):
    """
    규칙 목록을 표시합니다.
    
    Args:
        rule_engine: 규칙 엔진
        rule_type: 규칙 유형 ('exclude', 'income_type', 'all')
    """
    print("=== 규칙 목록 ===")
    
    try:
        if rule_type in ['all', 'exclude']:
            print("\n수입 제외 규칙:")
            exclude_rules = rule_engine.get_rules('exclude')
            if exclude_rules:
                for i, rule in enumerate(exclude_rules, 1):
                    status = "활성" if rule.get('enabled', True) else "비활성"
                    print(f"  {i}. {rule['name']} ({status}, 우선순위: {rule.get('priority', 0)})")
                    print(f"     패턴: {rule['pattern']}")
            else:
                print("  규칙이 없습니다.")
        
        if rule_type in ['all', 'income_type']:
            print("\n수입 유형 규칙:")
            income_type_rules = rule_engine.get_rules('income_type')
            if income_type_rules:
                for i, rule in enumerate(income_type_rules, 1):
                    status = "활성" if rule.get('enabled', True) else "비활성"
                    print(f"  {i}. {rule['name']} ({status}, 우선순위: {rule.get('priority', 0)})")
                    print(f"     패턴: {rule['pattern']} -> {rule['target']}")
            else:
                print("  규칙이 없습니다.")
        
    except Exception as e:
        logger.error(f"규칙 목록 표시 중 오류 발생: {e}")
        print(f"규칙 목록 표시 중 오류가 발생했습니다: {e}")

def add_rule(rule_engine, rule_type, name, pattern, target=None, priority=50):
    """
    규칙을 추가합니다.
    
    Args:
        rule_engine: 규칙 엔진
        rule_type: 규칙 유형 ('exclude', 'income_type')
        name: 규칙 이름
        pattern: 정규식 패턴
        target: 대상 카테고리 (income_type 규칙에만 필요)
        priority: 우선순위
    """
    print(f"=== 규칙 추가: {name} ===")
    
    try:
        if rule_type == 'exclude':
            rule = rule_engine.add_exclude_rule(name, pattern, priority)
            print(f"수입 제외 규칙이 추가되었습니다: {name}")
        elif rule_type == 'income_type':
            if not target:
                print("수입 유형 규칙에는 대상 카테고리가 필요합니다.")
                return
            
            rule = rule_engine.add_income_type_rule(name, pattern, target, priority)
            print(f"수입 유형 규칙이 추가되었습니다: {name} -> {target}")
        
        # 규칙 저장
        rule_engine.save_rules(rule_engine.rules_file)
        
    except ValueError as e:
        logger.error(f"규칙 추가 중 오류 발생: {e}")
        print(f"규칙 추가 중 오류가 발생했습니다: {e}")
    except Exception as e:
        logger.error(f"규칙 추가 중 오류 발생: {e}")
        print(f"규칙 추가 중 오류가 발생했습니다: {e}")

def update_rule_status(rule_engine, rule_type, name, enabled):
    """
    규칙 상태를 변경합니다.
    
    Args:
        rule_engine: 규칙 엔진
        rule_type: 규칙 유형 ('exclude', 'income_type')
        name: 규칙 이름
        enabled: 활성화 여부 ('yes', 'no')
    """
    print(f"=== 규칙 상태 변경: {name} ===")
    
    try:
        enabled_bool = (enabled == 'yes')
        result = rule_engine.update_rule_status(rule_type, name, enabled_bool)
        
        if result:
            status = "활성화" if enabled_bool else "비활성화"
            print(f"규칙 상태가 변경되었습니다: {name} -> {status}")
            
            # 규칙 저장
            rule_engine.save_rules(rule_engine.rules_file)
        else:
            print(f"규칙을 찾을 수 없습니다: {name}")
        
    except Exception as e:
        logger.error(f"규칙 상태 변경 중 오류 발생: {e}")
        print(f"규칙 상태 변경 중 오류가 발생했습니다: {e}")

def delete_rule(rule_engine, rule_type, name):
    """
    규칙을 삭제합니다.
    
    Args:
        rule_engine: 규칙 엔진
        rule_type: 규칙 유형 ('exclude', 'income_type')
        name: 규칙 이름
    """
    print(f"=== 규칙 삭제: {name} ===")
    
    try:
        result = rule_engine.delete_rule(rule_type, name)
        
        if result:
            print(f"규칙이 삭제되었습니다: {name}")
            
            # 규칙 저장
            rule_engine.save_rules(rule_engine.rules_file)
        else:
            print(f"규칙을 찾을 수 없습니다: {name}")
        
    except Exception as e:
        logger.error(f"규칙 삭제 중 오류 발생: {e}")
        print(f"규칙 삭제 중 오류가 발생했습니다: {e}")

def list_transactions(args):
    """
    수입 거래를 조회합니다.
    
    Args:
        args: 명령줄 인자
    """
    print("=== 수입 거래 조회 ===")
    
    try:
        # 필터 설정
        filters = {
            'transaction_type': Transaction.TYPE_INCOME,
            'limit': args.limit,
            'order_by': 'transaction_date',
            'order_direction': 'desc'
        }
        
        if args.start:
            filters['start_date'] = datetime.strptime(args.start, '%Y-%m-%d').date()
        
        if args.end:
            filters['end_date'] = datetime.strptime(args.end, '%Y-%m-%d').date()
        
        if args.category:
            filters['category'] = args.category
        
        if args.min is not None:
            filters['min_amount'] = args.min
        
        if args.max is not None:
            filters['max_amount'] = args.max
        
        if args.excluded:
            filters['include_excluded'] = True
        
        # 데이터베이스에서 거래 조회
        db_connection = DatabaseConnection()
        repo = TransactionRepository(db_connection)
        transactions = repo.list(filters)
        
        # 결과 출력
        if transactions:
            print(f"\n{len(transactions)}개의 거래를 찾았습니다:")
            
            # 테이블 형식으로 출력
            print("\n날짜        | 금액        | 카테고리    | 설명")
            print("-" * 80)
            
            for transaction in transactions:
                date_str = transaction.transaction_date.strftime('%Y-%m-%d')
                amount_str = f"{float(transaction.amount):,.0f}원"
                category = transaction.category or '미분류'
                description = transaction.description
                
                # 긴 설명 자르기
                if len(description) > 30:
                    description = description[:27] + "..."
                
                print(f"{date_str} | {amount_str:12} | {category:10} | {description}")
            
            # 합계 출력
            total = sum(float(t.amount) for t in transactions)
            print("-" * 80)
            print(f"합계: {total:,.0f}원")
            
            # CSV 출력
            if args.output:
                # 데이터프레임 생성
                data = []
                for transaction in transactions:
                    data.append({
                        '날짜': transaction.transaction_date.strftime('%Y-%m-%d'),
                        '금액': float(transaction.amount),
                        '카테고리': transaction.category or '미분류',
                        '설명': transaction.description,
                        '입금방식': transaction.payment_method or '',
                        '메모': transaction.memo or '',
                        '제외여부': '예' if transaction.is_excluded else '아니오'
                    })
                
                df = pd.DataFrame(data)
                df.to_csv(args.output, index=False, encoding='utf-8-sig')
                print(f"\n거래 데이터를 CSV 파일로 저장했습니다: {args.output}")
        else:
            print("조건에 맞는 거래가 없습니다.")
        
    except Exception as e:
        logger.error(f"거래 조회 중 오류 발생: {e}")
        print(f"거래 조회 중 오류가 발생했습니다: {e}")

def generate_report(args):
    """
    수입 보고서를 생성합니다.
    
    Args:
        args: 명령줄 인자
    """
    print(f"=== 수입 보고서 생성: {args.type} ===")
    
    try:
        # 분석 기간 설정
        end_date = date.today()
        start_date = end_date - timedelta(days=30 * args.months)
        
        # 데이터베이스에서 거래 조회
        db_connection = DatabaseConnection()
        repo = TransactionRepository(db_connection)
        transactions = repo.list({
            'transaction_type': Transaction.TYPE_INCOME,
            'start_date': start_date,
            'end_date': end_date,
            'include_excluded': False
        })
        
        if not transactions:
            print("분석할 거래가 없습니다.")
            return
        
        print(f"{len(transactions)}개의 거래를 분석합니다.")
        
        if args.type == 'monthly':
            # 월별 보고서
            monthly_data = {}
            
            for transaction in transactions:
                month_key = transaction.transaction_date.strftime('%Y-%m')
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'count': 0,
                        'total': 0,
                        'by_category': {}
                    }
                
                monthly_data[month_key]['count'] += 1
                monthly_data[month_key]['total'] += float(transaction.amount)
                
                category = transaction.category or '미분류'
                if category not in monthly_data[month_key]['by_category']:
                    monthly_data[month_key]['by_category'][category] = 0
                
                monthly_data[month_key]['by_category'][category] += float(transaction.amount)
            
            # 데이터프레임 생성
            data = []
            for month, stats in sorted(monthly_data.items()):
                row = {
                    '월': month,
                    '거래수': stats['count'],
                    '총액': stats['total']
                }
                
                # 카테고리별 금액 추가
                for category, amount in stats['by_category'].items():
                    row[f'카테고리_{category}'] = amount
                
                data.append(row)
            
            df = pd.DataFrame(data)
            df.to_csv(args.output, index=False, encoding='utf-8-sig')
            print(f"월별 보고서를 저장했습니다: {args.output}")
            
        elif args.type == 'category':
            # 카테고리별 보고서
            category_data = {}
            
            for transaction in transactions:
                category = transaction.category or '미분류'
                
                if category not in category_data:
                    category_data[category] = {
                        'count': 0,
                        'total': 0,
                        'min': float('inf'),
                        'max': 0,
                        'transactions': []
                    }
                
                amount = float(transaction.amount)
                category_data[category]['count'] += 1
                category_data[category]['total'] += amount
                category_data[category]['min'] = min(category_data[category]['min'], amount)
                category_data[category]['max'] = max(category_data[category]['max'], amount)
                category_data[category]['transactions'].append({
                    'date': transaction.transaction_date,
                    'amount': amount,
                    'description': transaction.description
                })
            
            # 데이터프레임 생성
            data = []
            for category, stats in sorted(category_data.items(), key=lambda x: x[1]['total'], reverse=True):
                data.append({
                    '카테고리': category,
                    '거래수': stats['count'],
                    '총액': stats['total'],
                    '평균': stats['total'] / stats['count'],
                    '최소': stats['min'],
                    '최대': stats['max']
                })
            
            df = pd.DataFrame(data)
            df.to_csv(args.output, index=False, encoding='utf-8-sig')
            print(f"카테고리별 보고서를 저장했습니다: {args.output}")
            
        elif args.type == 'trend':
            # 트렌드 보고서
            
            # 패턴 분석기 초기화
            pattern_analyzer = IncomePatternAnalyzer()
            
            # 거래 추가
            for transaction in transactions:
                pattern_analyzer.add_transaction(transaction.to_dict())
            
            # 패턴 분석
            result = pattern_analyzer.analyze_patterns()
            
            # 월별 트렌드 데이터
            monthly_totals = result['income_trends'].get('monthly_totals', [])
            
            if monthly_totals:
                df = pd.DataFrame(monthly_totals)
                df.to_csv(args.output, index=False, encoding='utf-8-sig')
                print(f"트렌드 보고서를 저장했습니다: {args.output}")
            else:
                print("트렌드 데이터가 없습니다.")
        
    except Exception as e:
        logger.error(f"보고서 생성 중 오류 발생: {e}")
        print(f"보고서 생성 중 오류가 발생했습니다: {e}")

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
    
    # 데이터베이스 파일 경로
    db_file = args.db or os.path.join(base_dir, 'personal_data.db')
    
    # 규칙 엔진 초기화
    rule_engine = IncomeRuleEngine(rules_file if os.path.exists(rules_file) else None)
    rule_engine.rules_file = rules_file
    
    # 패턴 분석기 초기화
    pattern_analyzer = IncomePatternAnalyzer(history_file if os.path.exists(history_file) else None)
    pattern_analyzer.history_file = history_file
    
    # 데이터베이스 연결 설정
    os.environ['DB_PATH'] = db_file
    
    # 명령 실행
    if not args.command:
        parser.print_help()
    elif args.command == 'add':
        if args.file:
            batch_add_incomes(rule_engine, pattern_analyzer, args.file)
        elif args.batch:
            batch_add_incomes(rule_engine, pattern_analyzer)
        else:
            add_manual_income(rule_engine, pattern_analyzer)
    elif args.command == 'analyze':
        analyze_income_patterns(pattern_analyzer, args.months)
    elif args.command == 'predict':
        predict_future_income(pattern_analyzer, args.months)
    elif args.command == 'summary':
        show_income_summary(pattern_analyzer)
    elif args.command == 'rule':
        if args.rule_command == 'list':
            list_rules(rule_engine, args.type)
        elif args.rule_command == 'add':
            add_rule(rule_engine, args.type, args.name, args.pattern, args.target, args.priority)
        elif args.rule_command == 'status':
            update_rule_status(rule_engine, args.type, args.name, args.enabled)
        elif args.rule_command == 'delete':
            delete_rule(rule_engine, args.type, args.name)
        else:
            parser.print_help()
    elif args.command == 'list':
        list_transactions(args)
    elif args.command == 'report':
        generate_report(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()