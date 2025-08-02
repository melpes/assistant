# -*- coding: utf-8 -*-
"""
리포트 생성 CLI 도구

다양한 형식의 재무 리포트를 생성합니다.
"""

import os
import sys
import argparse
import json
import logging
from datetime import datetime, date, timedelta

from src.repositories.db_connection import DatabaseConnection
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.config_repository import ConfigRepository
from src.analyzers.integrated_analyzer import IntegratedAnalyzer
from src.reports.report_generator import ReportGenerator

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 데이터베이스 파일 경로
DB_FILE_NAME = "personal_data.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, DB_FILE_NAME)


def parse_args():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(description="재무 리포트 생성 도구")
    
    # 명령 선택
    subparsers = parser.add_subparsers(dest="command", help="명령")
    
    # 리포트 생성 명령
    create_parser = subparsers.add_parser("create", help="리포트 생성")
    create_parser.add_argument("--type", choices=["summary", "detail", "template"],
                             default="summary", help="리포트 유형 (기본값: summary)")
    create_parser.add_argument("--template", help="템플릿 이름 (템플릿 리포트인 경우)")
    
    # 기간 설정
    create_parser.add_argument("--days", type=int, default=30, help="분석 기간 (일) (기본값: 30)")
    create_parser.add_argument("--start-date", help="시작 날짜 (YYYY-MM-DD 형식)")
    create_parser.add_argument("--end-date", help="종료 날짜 (YYYY-MM-DD 형식)")
    create_parser.add_argument("--month", help="분석할 월 (YYYY-MM 형식)")
    
    # 비교 분석 옵션
    create_parser.add_argument("--compare", action="store_true", help="이전 기간과 비교")
    
    # 필터 옵션
    create_parser.add_argument("--category", help="특정 카테고리만 분석")
    create_parser.add_argument("--payment-method", help="특정 결제 방식만 분석")
    create_parser.add_argument("--transaction-type", choices=["expense", "income", "all"],
                             default="all", help="거래 유형 (기본값: all)")
    
    # 출력 옵션
    create_parser.add_argument("--output", choices=["console", "json", "csv"],
                             default="console", help="출력 형식 (기본값: console)")
    create_parser.add_argument("--output-file", help="출력 파일 경로")
    
    # 템플릿 관리 명령
    template_parser = subparsers.add_parser("template", help="템플릿 관리")
    template_subparsers = template_parser.add_subparsers(dest="template_command", help="템플릿 명령")
    
    # 템플릿 목록 조회
    template_list_parser = template_subparsers.add_parser("list", help="템플릿 목록 조회")
    
    # 템플릿 추가
    template_add_parser = template_subparsers.add_parser("add", help="템플릿 추가")
    template_add_parser.add_argument("--name", required=True, help="템플릿 이름")
    template_add_parser.add_argument("--file", required=True, help="템플릿 파일 경로")
    
    # 템플릿 제거
    template_remove_parser = template_subparsers.add_parser("remove", help="템플릿 제거")
    template_remove_parser.add_argument("--name", required=True, help="템플릿 이름")
    
    # 스케줄 관리 명령
    schedule_parser = subparsers.add_parser("schedule", help="스케줄 관리")
    schedule_subparsers = schedule_parser.add_subparsers(dest="schedule_command", help="스케줄 명령")
    
    # 스케줄 목록 조회
    schedule_list_parser = schedule_subparsers.add_parser("list", help="스케줄 목록 조회")
    
    # 스케줄 추가
    schedule_add_parser = schedule_subparsers.add_parser("add", help="스케줄 추가")
    schedule_add_parser.add_argument("--id", required=True, help="리포트 ID")
    schedule_add_parser.add_argument("--type", choices=["summary", "detail", "template"],
                                   required=True, help="리포트 유형")
    schedule_add_parser.add_argument("--template", help="템플릿 이름 (템플릿 리포트인 경우)")
    schedule_add_parser.add_argument("--schedule-type", choices=["daily", "weekly", "monthly"],
                                   required=True, help="스케줄 유형")
    schedule_add_parser.add_argument("--time", default="00:00", help="실행 시간 (HH:MM 형식)")
    schedule_add_parser.add_argument("--day", help="실행 요일 또는 날짜 (weekly: monday-sunday, monthly: 1-31)")
    schedule_add_parser.add_argument("--days", type=int, default=30, help="분석 기간 (일) (기본값: 30)")
    schedule_add_parser.add_argument("--output", choices=["json", "csv"],
                                   default="json", help="출력 형식 (기본값: json)")
    schedule_add_parser.add_argument("--output-dir", help="출력 디렉토리")
    
    # 스케줄 제거
    schedule_remove_parser = schedule_subparsers.add_parser("remove", help="스케줄 제거")
    schedule_remove_parser.add_argument("--id", required=True, help="리포트 ID")
    
    # 스케줄 실행
    schedule_run_parser = schedule_subparsers.add_parser("run", help="스케줄 즉시 실행")
    schedule_run_parser.add_argument("--id", required=True, help="리포트 ID")
    
    # 스케줄러 시작/중지
    schedule_start_parser = schedule_subparsers.add_parser("start", help="스케줄러 시작")
    schedule_stop_parser = schedule_subparsers.add_parser("stop", help="스케줄러 중지")
    
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


def create_report(args, report_generator, integrated_analyzer):
    """리포트 생성"""
    # 날짜 범위 계산
    start_date, end_date = get_date_range(args)
    
    # 분석 데이터 생성
    if args.month:
        year, month = map(int, args.month.split("-"))
        data = integrated_analyzer.analyze_month(
            year, month,
            include_expense=(args.transaction_type in ["expense", "all"]),
            include_income=(args.transaction_type in ["income", "all"]),
            include_trends=True,
            compare_with_previous=args.compare
        )
    else:
        data = integrated_analyzer.analyze_recent_period(
            args.days,
            include_expense=(args.transaction_type in ["expense", "all"]),
            include_income=(args.transaction_type in ["income", "all"]),
            include_trends=True,
            compare_with_previous=args.compare
        )
    
    # 필터 정보 추가
    filters = {}
    if args.category:
        filters["category"] = args.category
    if args.payment_method:
        filters["payment_method"] = args.payment_method
    if args.transaction_type != "all":
        filters["transaction_type"] = args.transaction_type
    
    if filters:
        data["filters"] = filters
    
    # 리포트 유형 매핑
    report_type_map = {
        "summary": ReportGenerator.REPORT_FINANCIAL_SUMMARY,
        "detail": ReportGenerator.REPORT_TRANSACTION_DETAIL,
        "template": ReportGenerator.REPORT_TEMPLATE
    }
    
    # 리포트 생성
    result = report_generator.create_report(
        report_type=report_type_map[args.type],
        data=data,
        output_format=args.output,
        output_file=args.output_file,
        template_name=args.template
    )
    
    # 콘솔 출력인 경우 결과 출력
    if args.output == "console" and result:
        print(result)


def manage_templates(args, report_generator):
    """템플릿 관리"""
    if args.template_command == "list":
        # 템플릿 목록 조회
        templates = report_generator.get_templates()
        
        if not templates:
            print("등록된 템플릿이 없습니다.")
        else:
            print(f"\n{'=' * 60}")
            print(f"템플릿 목록 ({len(templates)}개)")
            print(f"{'-' * 60}")
            for name, path in templates.items():
                print(f"{name:30} | {path}")
    
    elif args.template_command == "add":
        # 템플릿 파일 읽기
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # 템플릿 추가
            if report_generator.add_template(args.name, template_content):
                print(f"템플릿이 추가되었습니다: {args.name}")
            else:
                print(f"템플릿 추가 실패: {args.name}")
        
        except FileNotFoundError:
            print(f"템플릿 파일을 찾을 수 없습니다: {args.file}")
        except Exception as e:
            print(f"템플릿 추가 중 오류 발생: {str(e)}")
    
    elif args.template_command == "remove":
        # 템플릿 제거
        if report_generator.remove_template(args.name):
            print(f"템플릿이 제거되었습니다: {args.name}")
        else:
            print(f"템플릿 제거 실패: {args.name}")


def manage_schedules(args, report_generator, integrated_analyzer):
    """스케줄 관리"""
    if args.schedule_command == "list":
        # 스케줄 목록 조회
        schedules = report_generator.get_scheduled_reports()
        
        if not schedules:
            print("등록된 스케줄이 없습니다.")
        else:
            print(f"\n{'=' * 80}")
            print(f"스케줄 목록 ({len(schedules)}개)")
            print(f"{'-' * 80}")
            for report_id, schedule in schedules.items():
                print(f"ID: {report_id}")
                print(f"  스케줄 유형: {schedule['schedule_type']}")
                print(f"  스케줄 매개변수: {schedule['schedule_params']}")
                print(f"  출력 형식: {schedule['output_format']}")
                print(f"  출력 디렉토리: {schedule['output_dir']}")
                print(f"  마지막 실행: {schedule.get('last_run', '없음')}")
                print(f"  다음 실행: {schedule.get('next_run', '없음')}")
                print(f"{'-' * 80}")
    
    elif args.schedule_command == "add":
        # 스케줄 매개변수 생성
        schedule_params = {"time": args.time}
        
        if args.schedule_type == "weekly" and args.day:
            schedule_params["day"] = args.day
        elif args.schedule_type == "monthly" and args.day:
            try:
                schedule_params["day"] = int(args.day)
            except ValueError:
                print(f"월간 스케줄의 날짜는 숫자여야 합니다: {args.day}")
                return
        
        # 리포트 유형 매핑
        report_type_map = {
            "summary": ReportGenerator.REPORT_FINANCIAL_SUMMARY,
            "detail": ReportGenerator.REPORT_TRANSACTION_DETAIL,
            "template": ReportGenerator.REPORT_TEMPLATE
        }
        
        # 데이터 제공 함수 생성
        days = args.days
        
        def data_provider():
            return integrated_analyzer.analyze_recent_period(
                days,
                include_expense=True,
                include_income=True,
                include_trends=True,
                compare_with_previous=True
            )
        
        # 스케줄 추가
        if report_generator.schedule_report(
            report_id=args.id,
            report_type=report_type_map[args.type],
            data_provider=data_provider,
            schedule_type=args.schedule_type,
            schedule_params=schedule_params,
            output_format=args.output,
            output_dir=args.output_dir,
            template_name=args.template
        ):
            print(f"스케줄이 추가되었습니다: {args.id}")
        else:
            print(f"스케줄 추가 실패: {args.id}")
    
    elif args.schedule_command == "remove":
        # 스케줄 제거
        if report_generator.remove_scheduled_report(args.id):
            print(f"스케줄이 제거되었습니다: {args.id}")
        else:
            print(f"스케줄 제거 실패: {args.id}")
    
    elif args.schedule_command == "run":
        # 스케줄 즉시 실행
        if report_generator.run_report_now(args.id):
            print(f"리포트가 즉시 실행되었습니다: {args.id}")
        else:
            print(f"리포트 실행 실패: {args.id}")
    
    elif args.schedule_command == "start":
        # 스케줄러 시작
        report_generator.start_scheduler()
        print("스케줄러가 시작되었습니다.")
    
    elif args.schedule_command == "stop":
        # 스케줄러 중지
        report_generator.stop_scheduler()
        print("스케줄러가 중지되었습니다.")


def main():
    """메인 함수"""
    args = parse_args()
    
    # 데이터베이스 연결
    db_connection = DatabaseConnection(DB_PATH)
    transaction_repository = TransactionRepository(db_connection)
    config_repository = ConfigRepository(db_connection)
    
    # 분석기 및 리포트 생성기 초기화
    integrated_analyzer = IntegratedAnalyzer(transaction_repository)
    report_generator = ReportGenerator(config_repository)
    
    # 명령에 따라 실행
    if args.command == "create":
        create_report(args, report_generator, integrated_analyzer)
    
    elif args.command == "template":
        manage_templates(args, report_generator)
    
    elif args.command == "schedule":
        manage_schedules(args, report_generator, integrated_analyzer)
    
    else:
        print("명령을 지정하세요. 도움말을 보려면 --help 옵션을 사용하세요.")


if __name__ == "__main__":
    main()