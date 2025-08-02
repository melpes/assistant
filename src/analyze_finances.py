# -*- coding: utf-8 -*-
"""
금융 분석 도구

통합 분석 엔진을 사용하여 다양한 관점에서 금융 데이터를 분석합니다.
"""

import sys
import os
import argparse
from datetime import datetime, date, timedelta

from src.repositories.db_connection import DatabaseConnection
from src.repositories.transaction_repository import TransactionRepository
from src.analyzers import (
    ExpenseAnalyzer, 
    IncomeAnalyzer, 
    TrendAnalyzer, 
    ComparisonAnalyzer, 
    IntegratedAnalyzer
)

# 데이터베이스 파일 경로
DB_FILE_NAME = "personal_data.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, DB_FILE_NAME)


def parse_args():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(description="금융 분석 도구")
    
    # 분석 유형 선택
    parser.add_argument("--type", choices=["expense", "income", "trend", "comparison", "summary"],
                      default="summary", help="분석 유형 (기본값: summary)")
    
    # 기간 설정
    parser.add_argument("--days", type=int, default=30, help="분석 기간 (일) (기본값: 30)")
    parser.add_argument("--start-date", help="시작 날짜 (YYYY-MM-DD 형식)")
    parser.add_argument("--end-date", help="종료 날짜 (YYYY-MM-DD 형식)")
    parser.add_argument("--month", help="분석할 월 (YYYY-MM 형식)")
    
    # 비교 분석 옵션
    parser.add_argument("--compare", action="store_true", help="이전 기간과 비교")
    parser.add_argument("--compare-month", help="비교할 월 (YYYY-MM 형식)")
    
    # 필터 옵션
    parser.add_argument("--category", help="특정 카테고리만 분석")
    parser.add_argument("--payment-method", help="특정 결제 방식만 분석")
    
    # 출력 옵션
    parser.add_argument("--output", choices=["console", "json", "csv"],
                      default="console", help="출력 형식 (기본값: console)")
    parser.add_argument("--output-file", help="출력 파일 경로")
    
    return parser.parse_args()


def get_date_range(args):
    """인수에서 날짜 범위 계산"""
    today = datetime.now().date()
    
    if args.month:
        # 월 지정 시
        year, month = map(int, args.month.split("-"))
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
    elif args.start_date and args.end_date:
        # 시작일과 종료일 지정 시
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    else:
        # 기본값: 최근 N일
        end_date = today
        start_date = end_date - timedelta(days=args.days - 1)
    
    return start_date, end_date


def analyze_expenses(analyzer, args):
    """지출 분석 실행"""
    start_date, end_date = get_date_range(args)
    
    filters = {}
    if args.category:
        filters['category'] = args.category
    if args.payment_method:
        filters['payment_method'] = args.payment_method
    
    if args.month:
        year, month = map(int, args.month.split("-"))
        result = analyzer.analyze_by_month(year, month, filters)
    else:
        result = analyzer.analyze(start_date, end_date, filters)
    
    if args.output == "console":
        analyzer.print_expense_report(args.days)
    
    return result


def analyze_income(analyzer, args):
    """수입 분석 실행"""
    start_date, end_date = get_date_range(args)
    
    filters = {}
    if args.category:
        filters['category'] = args.category
    
    if args.month:
        year, month = map(int, args.month.split("-"))
        result = analyzer.analyze_by_month(year, month, filters)
    else:
        result = analyzer.analyze(start_date, end_date, filters)
    
    if args.output == "console":
        analyzer.print_income_report(args.days)
    
    return result


def analyze_trends(analyzer, args):
    """트렌드 분석 실행"""
    if args.month:
        # 월 지정 시 최근 6개월 분석
        year, month = map(int, args.month.split("-"))
        result = analyzer.analyze_monthly_trends(6)
    else:
        # 기본: 최근 90일 분석
        days = args.days if args.days > 30 else 90
        start_date = datetime.now().date() - timedelta(days=days - 1)
        end_date = datetime.now().date()
        result = analyzer.analyze(start_date, end_date)
    
    if args.output == "console":
        analyzer.print_trend_report(6)
    
    return result


def analyze_comparison(analyzer, args):
    """비교 분석 실행"""
    if args.month and args.compare_month:
        # 두 월 비교
        year1, month1 = map(int, args.compare_month.split("-"))
        year2, month2 = map(int, args.month.split("-"))
        result = analyzer.compare_months(year1, month1, year2, month2)
        
        if args.output == "console":
            analyzer.print_comparison_report(year1, month1, year2, month2)
    elif args.month:
        # 이전 월과 비교
        year, month = map(int, args.month.split("-"))
        result = analyzer.compare_with_previous_month(year, month)
        
        if args.output == "console":
            # 이전 월 계산
            if month == 1:
                prev_year = year - 1
                prev_month = 12
            else:
                prev_year = year
                prev_month = month - 1
            
            analyzer.print_comparison_report(prev_year, prev_month, year, month)
    else:
        # 두 기간 비교
        start_date, end_date = get_date_range(args)
        period_days = (end_date - start_date).days + 1
        
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=period_days - 1)
        
        result = analyzer.compare_periods(
            prev_start_date, prev_end_date,
            start_date, end_date
        )
    
    return result


def analyze_summary(analyzer, args):
    """종합 분석 실행"""
    if args.month:
        # 월 분석
        year, month = map(int, args.month.split("-"))
        result = analyzer.analyze_month(
            year, month,
            include_expense=True,
            include_income=True,
            include_trends=True,
            compare_with_previous=args.compare
        )
    else:
        # 기간 분석
        days = args.days
        result = analyzer.analyze_recent_period(
            days,
            include_expense=True,
            include_income=True,
            include_trends=True,
            compare_with_previous=args.compare
        )
    
    if args.output == "console":
        analyzer.print_financial_report(days)
    
    return result


def main():
    """메인 함수"""
    args = parse_args()
    
    # 데이터베이스 연결
    db_connection = DatabaseConnection(DB_PATH)
    transaction_repository = TransactionRepository(db_connection)
    
    # 분석기 초기화
    expense_analyzer = ExpenseAnalyzer(transaction_repository)
    income_analyzer = IncomeAnalyzer(transaction_repository)
    trend_analyzer = TrendAnalyzer(transaction_repository)
    comparison_analyzer = ComparisonAnalyzer(transaction_repository)
    integrated_analyzer = IntegratedAnalyzer(transaction_repository)
    
    # 분석 유형에 따라 실행
    if args.type == "expense":
        result = analyze_expenses(expense_analyzer, args)
    elif args.type == "income":
        result = analyze_income(income_analyzer, args)
    elif args.type == "trend":
        result = analyze_trends(trend_analyzer, args)
    elif args.type == "comparison":
        result = analyze_comparison(comparison_analyzer, args)
    else:  # summary
        result = analyze_summary(integrated_analyzer, args)
    
    # JSON 또는 CSV 출력
    if args.output == "json":
        import json
        output = json.dumps(result, indent=2, ensure_ascii=False)
        
        if args.output_file:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(output)
        else:
            print(output)
    
    elif args.output == "csv":
        import csv
        import json
        
        # JSON을 평탄화하여 CSV로 변환
        def flatten_json(nested_json, prefix=''):
            flat_json = {}
            for key, value in nested_json.items():
                if isinstance(value, dict):
                    flat_json.update(flatten_json(value, prefix + key + '_'))
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            flat_json.update(flatten_json(item, prefix + key + f'_{i}_'))
                        else:
                            flat_json[prefix + key + f'_{i}'] = item
                else:
                    flat_json[prefix + key] = value
            return flat_json
        
        flat_result = flatten_json(result)
        
        if args.output_file:
            with open(args.output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(flat_result.keys())
                writer.writerow(flat_result.values())
        else:
            writer = csv.writer(sys.stdout)
            writer.writerow(flat_result.keys())
            writer.writerow(flat_result.values())


if __name__ == "__main__":
    main()