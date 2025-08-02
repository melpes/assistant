# -*- coding: utf-8 -*-
"""
통합 CLI 인터페이스

금융 거래 관리 시스템의 모든 기능에 접근할 수 있는 통합 명령줄 인터페이스입니다.
서브커맨드 기반 구조와 풍부한 도움말을 제공합니다.
"""

import os
import sys
import logging
import argparse
import textwrap
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 현재 디렉토리를 모듈 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 모듈 임포트
from src.config_manager import ConfigManager
from src.backup_manager import BackupManager
from src.ingesters.ingester_factory import IngesterFactory
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.config_repository import ConfigRepository
from src.manual_transaction_manager import ManualTransactionManager
from src.analyze_finances import analyze_finances
from src.generate_report import generate_report

# 로거 설정
def setup_logger(verbose: bool = False, log_file: str = None):
    """
    로거를 설정합니다.
    
    Args:
        verbose: 상세 로깅 활성화 여부
        log_file: 로그 파일 경로
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 추가 (지정된 경우)
    if log_file:
        # 로그 디렉토리 생성
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    logger.debug("로거 설정 완료")

# 명령어 처리 함수
def handle_ingest_command(args):
    """
    데이터 수집 명령어 처리
    
    Args:
        args: 명령줄 인자
    """
    try:
        # 설정 관리자 초기화
        config_manager = ConfigManager()
        
        # 수집기 팩토리 초기화
        ingester_factory = IngesterFactory()
        
        if args.source == 'toss_card':
            # 토스뱅크 카드 수집
            if not args.file:
                logger.error("파일 경로를 지정해야 합니다.")
                return
            
            ingester = ingester_factory.create_ingester('toss_bank_card')
            
            if not ingester.validate_file(args.file):
                logger.error("유효하지 않은 토스뱅크 카드 명세서 파일입니다.")
                return
            
            logger.info(f"토스뱅크 카드 명세서 수집 시작: {args.file}")
            transactions = ingester.process_file(args.file)
            logger.info(f"수집 완료: {len(transactions)}개의 거래")
            
        elif args.source == 'toss_account':
            # 토스뱅크 계좌 수집
            if not args.file:
                logger.error("파일 경로를 지정해야 합니다.")
                return
            
            ingester = ingester_factory.create_ingester('toss_bank_account')
            
            if not ingester.validate_file(args.file):
                logger.error("유효하지 않은 토스뱅크 계좌 명세서 파일입니다.")
                return
            
            logger.info(f"토스뱅크 계좌 명세서 수집 시작: {args.file}")
            transactions = ingester.process_file(args.file)
            logger.info(f"수집 완료: {len(transactions)}개의 거래")
            
        elif args.source == 'manual':
            # 수동 입력
            manual_manager = ManualTransactionManager()
            
            if args.type == 'expense':
                logger.info("수동 지출 입력 시작")
                transaction = manual_manager.add_expense()
                if transaction:
                    logger.info("수동 지출 입력 완료")
                else:
                    logger.error("수동 지출 입력 실패")
            
            elif args.type == 'income':
                logger.info("수동 수입 입력 시작")
                transaction = manual_manager.add_income()
                if transaction:
                    logger.info("수동 수입 입력 완료")
                else:
                    logger.error("수동 수입 입력 실패")
            
            elif args.type == 'batch':
                logger.info("일괄 거래 입력 시작")
                transactions = manual_manager.batch_add_transactions()
                if transactions:
                    logger.info(f"일괄 거래 입력 완료: {len(transactions)}개의 거래")
                else:
                    logger.error("일괄 거래 입력 실패")
            
            elif args.type == 'template':
                logger.info("템플릿 사용 거래 입력 시작")
                transaction = manual_manager.use_template()
                if transaction:
                    logger.info("템플릿 사용 거래 입력 완료")
                else:
                    logger.error("템플릿 사용 거래 입력 실패")
            
        elif args.source == 'all':
            # 모든 소스 수집
            logger.info("모든 데이터 소스 수집 시작")
            
            # 데이터 디렉토리 확인
            data_dir = os.path.join(parent_dir, 'data')
            if not os.path.exists(data_dir):
                logger.error(f"데이터 디렉토리를 찾을 수 없습니다: {data_dir}")
                return
            
            # 토스뱅크 카드 명세서 수집
            card_ingester = ingester_factory.create_ingester('toss_bank_card')
            card_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) 
                         if f.endswith('.xlsx') and card_ingester.validate_file(os.path.join(data_dir, f))]
            
            card_transactions = []
            for file in card_files:
                logger.info(f"토스뱅크 카드 명세서 수집: {file}")
                card_transactions.extend(card_ingester.process_file(file))
            
            logger.info(f"토스뱅크 카드 수집 완료: {len(card_transactions)}개의 거래")
            
            # 토스뱅크 계좌 명세서 수집
            account_ingester = ingester_factory.create_ingester('toss_bank_account')
            account_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) 
                            if f.endswith('.csv') and account_ingester.validate_file(os.path.join(data_dir, f))]
            
            account_transactions = []
            for file in account_files:
                logger.info(f"토스뱅크 계좌 명세서 수집: {file}")
                account_transactions.extend(account_ingester.process_file(file))
            
            logger.info(f"토스뱅크 계좌 수집 완료: {len(account_transactions)}개의 거래")
            
            logger.info(f"모든 데이터 소스 수집 완료: {len(card_transactions) + len(account_transactions)}개의 거래")
        
        else:
            logger.error(f"지원하지 않는 데이터 소스: {args.source}")
    
    except Exception as e:
        logger.error(f"데이터 수집 중 오류 발생: {e}")

def handle_analyze_command(args):
    """
    분석 명령어 처리
    
    Args:
        args: 명령줄 인자
    """
    try:
        # 기간 설정
        if args.period == 'week':
            start_date = datetime.now().date() - timedelta(days=7)
            end_date = datetime.now().date()
        elif args.period == 'month':
            start_date = datetime.now().date() - timedelta(days=30)
            end_date = datetime.now().date()
        elif args.period == 'year':
            start_date = datetime.now().date() - timedelta(days=365)
            end_date = datetime.now().date()
        elif args.period == 'custom':
            if not args.start_date:
                logger.error("시작 날짜를 지정해야 합니다.")
                return
            
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
            
            if args.end_date:
                end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
        else:
            # 기본값: 한 달
            start_date = datetime.now().date() - timedelta(days=30)
            end_date = datetime.now().date()
        
        # 분석 유형에 따라 처리
        if args.type == 'expense':
            logger.info(f"지출 분석 시작: {start_date} ~ {end_date}")
            analyze_finances(start_date, end_date, 'expense', args.category, args.payment_method, args.min_amount, args.max_amount)
        
        elif args.type == 'income':
            logger.info(f"수입 분석 시작: {start_date} ~ {end_date}")
            analyze_finances(start_date, end_date, 'income', args.category, args.payment_method, args.min_amount, args.max_amount)
        
        elif args.type == 'all':
            logger.info(f"전체 거래 분석 시작: {start_date} ~ {end_date}")
            analyze_finances(start_date, end_date, None, args.category, args.payment_method, args.min_amount, args.max_amount)
        
        elif args.type == 'trend':
            logger.info(f"추세 분석 시작: {start_date} ~ {end_date}")
            analyze_finances(start_date, end_date, None, args.category, args.payment_method, args.min_amount, args.max_amount, analysis_type='trend')
        
        elif args.type == 'comparison':
            logger.info(f"비교 분석 시작: {start_date} ~ {end_date}")
            analyze_finances(start_date, end_date, None, args.category, args.payment_method, args.min_amount, args.max_amount, analysis_type='comparison')
        
        else:
            logger.error(f"지원하지 않는 분석 유형: {args.type}")
    
    except Exception as e:
        logger.error(f"분석 중 오류 발생: {e}")

def handle_report_command(args):
    """
    리포트 명령어 처리
    
    Args:
        args: 명령줄 인자
    """
    try:
        # 기간 설정
        if args.period == 'week':
            start_date = datetime.now().date() - timedelta(days=7)
            end_date = datetime.now().date()
        elif args.period == 'month':
            start_date = datetime.now().date() - timedelta(days=30)
            end_date = datetime.now().date()
        elif args.period == 'year':
            start_date = datetime.now().date() - timedelta(days=365)
            end_date = datetime.now().date()
        elif args.period == 'custom':
            if not args.start_date:
                logger.error("시작 날짜를 지정해야 합니다.")
                return
            
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
            
            if args.end_date:
                end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
        else:
            # 기본값: 한 달
            start_date = datetime.now().date() - timedelta(days=30)
            end_date = datetime.now().date()
        
        # 리포트 유형에 따라 처리
        if args.type == 'summary':
            logger.info(f"요약 리포트 생성 시작: {start_date} ~ {end_date}")
            generate_report(start_date, end_date, 'summary', args.format, args.output)
        
        elif args.type == 'detail':
            logger.info(f"상세 리포트 생성 시작: {start_date} ~ {end_date}")
            generate_report(start_date, end_date, 'detail', args.format, args.output)
        
        elif args.type == 'category':
            logger.info(f"카테고리별 리포트 생성 시작: {start_date} ~ {end_date}")
            generate_report(start_date, end_date, 'category', args.format, args.output)
        
        elif args.type == 'payment':
            logger.info(f"결제방식별 리포트 생성 시작: {start_date} ~ {end_date}")
            generate_report(start_date, end_date, 'payment', args.format, args.output)
        
        elif args.type == 'monthly':
            logger.info(f"월간 리포트 생성 시작: {start_date} ~ {end_date}")
            generate_report(start_date, end_date, 'monthly', args.format, args.output)
        
        else:
            logger.error(f"지원하지 않는 리포트 유형: {args.type}")
    
    except Exception as e:
        logger.error(f"리포트 생성 중 오류 발생: {e}")

def handle_backup_command(args):
    """
    백업 명령어 처리
    
    Args:
        args: 명령줄 인자
    """
    try:
        # 설정 관리자 초기화
        config_manager = ConfigManager()
        
        # 백업 관리자 초기화
        backup_manager = BackupManager(config_manager)
        
        if args.action == 'backup-db':
            # 데이터베이스 백업
            logger.info("데이터베이스 백업 시작")
            backup_file = backup_manager.backup_database(args.type)
            
            if backup_file:
                logger.info(f"데이터베이스 백업 완료: {backup_file}")
            else:
                logger.error("데이터베이스 백업 실패")
        
        elif args.action == 'restore-db':
            # 데이터베이스 복원
            if not args.file:
                backups = backup_manager.list_backups()
                if not backups:
                    logger.error("사용 가능한 백업이 없습니다.")
                    return
                
                print("사용 가능한 백업:")
                for i, backup in enumerate(backups, 1):
                    print(f"{i}. {backup['filename']} ({backup['timestamp']})")
                
                choice = input("복원할 백업 번호를 선택하세요: ")
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(backups):
                        backup_file = backups[index]['file']
                    else:
                        logger.error("올바른 백업 번호를 선택해주세요.")
                        return
                except ValueError:
                    logger.error("숫자를 입력해주세요.")
                    return
            else:
                backup_file = args.file
            
            logger.info(f"데이터베이스 복원 시작: {backup_file}")
            result = backup_manager.restore_database(backup_file)
            
            if result:
                logger.info("데이터베이스 복원 완료")
            else:
                logger.error("데이터베이스 복원 실패")
        
        elif args.action == 'backup-config':
            # 설정 백업
            logger.info("설정 백업 시작")
            backup_file = backup_manager.backup_config()
            
            if backup_file:
                logger.info(f"설정 백업 완료: {backup_file}")
            else:
                logger.error("설정 백업 실패")
        
        elif args.action == 'restore-config':
            # 설정 복원
            if not args.file:
                backups = backup_manager.list_backups('config')
                if not backups:
                    logger.error("사용 가능한 설정 백업이 없습니다.")
                    return
                
                print("사용 가능한 설정 백업:")
                for i, backup in enumerate(backups, 1):
                    print(f"{i}. {backup['filename']} ({backup['timestamp']})")
                
                choice = input("복원할 설정 백업 번호를 선택하세요: ")
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(backups):
                        backup_file = backups[index]['file']
                    else:
                        logger.error("올바른 백업 번호를 선택해주세요.")
                        return
                except ValueError:
                    logger.error("숫자를 입력해주세요.")
                    return
            else:
                backup_file = args.file
            
            logger.info(f"설정 복원 시작: {backup_file}")
            result = backup_manager.restore_config(backup_file)
            
            if result:
                logger.info("설정 복원 완료")
            else:
                logger.error("설정 복원 실패")
        
        elif args.action == 'export':
            # 데이터 내보내기
            logger.info(f"데이터 내보내기 시작 ({args.format} 형식)")
            tables = [args.table] if args.table else None
            export_files = backup_manager.export_data(args.format, tables)
            
            if export_files:
                if 'zip' in export_files:
                    logger.info(f"데이터 내보내기 완료: {export_files['zip']}")
                else:
                    logger.info("데이터 내보내기 완료:")
                    for table, file_path in export_files.items():
                        logger.info(f"  - {table}: {file_path}")
            else:
                logger.error("데이터 내보내기 실패")
        
        elif args.action == 'import':
            # 데이터 가져오기
            if not args.file:
                logger.error("가져올 파일 경로를 지정해야 합니다.")
                return
            
            logger.info(f"데이터 가져오기 시작: {args.file}")
            result = backup_manager.import_data(args.file, args.table)
            
            if result:
                logger.info("데이터 가져오기 완료")
            else:
                logger.error("데이터 가져오기 실패")
        
        elif args.action == 'list':
            # 백업 목록 조회
            logger.info("백업 목록 조회")
            
            print("데이터베이스 백업 목록:")
            db_backups = backup_manager.list_backups()
            
            if db_backups:
                for i, backup in enumerate(db_backups, 1):
                    print(f"{i}. {backup['filename']} ({backup['timestamp']}, {backup['type']})")
            else:
                print("  사용 가능한 데이터베이스 백업이 없습니다.")
            
            print("\n설정 백업 목록:")
            config_backups = backup_manager.list_backups('config')
            
            if config_backups:
                for i, backup in enumerate(config_backups, 1):
                    print(f"{i}. {backup['filename']} ({backup['timestamp']})")
            else:
                print("  사용 가능한 설정 백업이 없습니다.")
        
        elif args.action == 'verify':
            # 백업 검증
            if not args.file:
                logger.error("검증할 백업 파일 경로를 지정해야 합니다.")
                return
            
            logger.info(f"백업 파일 검증 시작: {args.file}")
            result = backup_manager.verify_backup(args.file)
            
            if result:
                logger.info("백업 파일 검증 성공")
            else:
                logger.error("백업 파일 검증 실패")
        
        elif args.action == 'start-scheduler':
            # 스케줄러 시작
            logger.info("자동 백업 스케줄러 시작")
            result = backup_manager.start_scheduler()
            
            if result:
                logger.info(f"스케줄러 시작됨 (간격: {backup_manager.backup_interval_days}일)")
            else:
                logger.error("스케줄러 시작 실패")
        
        elif args.action == 'stop-scheduler':
            # 스케줄러 중지
            logger.info("자동 백업 스케줄러 중지")
            result = backup_manager.stop_scheduler()
            
            if result:
                logger.info("스케줄러 중지됨")
            else:
                logger.error("스케줄러 중지 실패")
        
        else:
            logger.error(f"지원하지 않는 백업 작업: {args.action}")
    
    except Exception as e:
        logger.error(f"백업 작업 중 오류 발생: {e}")def hand
le_config_command(args):
    """
    설정 명령어 처리
    
    Args:
        args: 명령줄 인자
    """
    try:
        # 설정 관리자 초기화
        config_manager = ConfigManager()
        
        if args.action == 'get':
            # 설정 값 조회
            if args.key:
                value = config_manager.get_config_value(args.key)
                print(f"{args.key}: {value}")
            elif args.section:
                section_config = config_manager.get_config(args.section)
                print(f"{args.section} 설정:")
                import yaml
                print(yaml.dump(section_config, default_flow_style=False, allow_unicode=True))
            else:
                all_config = config_manager.get_config()
                print("전체 설정:")
                import yaml
                print(yaml.dump(all_config, default_flow_style=False, allow_unicode=True))
        
        elif args.action == 'set':
            # 설정 값 설정
            if not args.key or args.value is None:
                logger.error("설정 키와 값을 모두 지정해야 합니다.")
                return
            
            logger.info(f"설정 값 변경: {args.key} = {args.value}")
            result = config_manager.set_config_value(args.key, args.value)
            
            if result:
                logger.info("설정 값 변경 완료")
                config_manager.save_config()
            else:
                logger.error("설정 값 변경 실패")
        
        elif args.action == 'reset':
            # 설정 초기화
            logger.info(f"설정 초기화: {args.section if args.section else '전체'}")
            result = config_manager.reset_to_defaults(args.section)
            
            if result:
                logger.info("설정 초기화 완료")
            else:
                logger.error("설정 초기화 실패")
        
        elif args.action == 'create-profile':
            # 프로파일 생성
            if not args.profile:
                logger.error("프로파일 이름을 지정해야 합니다.")
                return
            
            logger.info(f"프로파일 생성: {args.profile}")
            result = config_manager.create_profile(args.profile)
            
            if result:
                logger.info("프로파일 생성 완료")
            else:
                logger.error("프로파일 생성 실패")
        
        elif args.action == 'load-profile':
            # 프로파일 로드
            if not args.profile:
                profiles = config_manager.list_profiles()
                if not profiles:
                    logger.error("사용 가능한 프로파일이 없습니다.")
                    return
                
                print("사용 가능한 프로파일:")
                for i, profile in enumerate(profiles, 1):
                    print(f"{i}. {profile}")
                
                choice = input("로드할 프로파일 번호를 선택하세요: ")
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(profiles):
                        profile_name = profiles[index]
                    else:
                        logger.error("올바른 프로파일 번호를 선택해주세요.")
                        return
                except ValueError:
                    logger.error("숫자를 입력해주세요.")
                    return
            else:
                profile_name = args.profile
            
            logger.info(f"프로파일 로드: {profile_name}")
            result = config_manager.load_profile(profile_name)
            
            if result:
                logger.info("프로파일 로드 완료")
            else:
                logger.error("프로파일 로드 실패")
        
        elif args.action == 'list-profiles':
            # 프로파일 목록 조회
            logger.info("프로파일 목록 조회")
            profiles = config_manager.list_profiles()
            
            if profiles:
                print("사용 가능한 프로파일:")
                for profile in profiles:
                    print(f"- {profile}")
            else:
                print("사용 가능한 프로파일이 없습니다.")
        
        elif args.action == 'delete-profile':
            # 프로파일 삭제
            if not args.profile:
                profiles = config_manager.list_profiles()
                if not profiles:
                    logger.error("사용 가능한 프로파일이 없습니다.")
                    return
                
                print("사용 가능한 프로파일:")
                for i, profile in enumerate(profiles, 1):
                    print(f"{i}. {profile}")
                
                choice = input("삭제할 프로파일 번호를 선택하세요: ")
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(profiles):
                        profile_name = profiles[index]
                    else:
                        logger.error("올바른 프로파일 번호를 선택해주세요.")
                        return
                except ValueError:
                    logger.error("숫자를 입력해주세요.")
                    return
            else:
                profile_name = args.profile
            
            confirm = input(f"프로파일 '{profile_name}'을(를) 삭제하시겠습니까? (y/n): ")
            if confirm.lower() != 'y':
                logger.info("프로파일 삭제 취소")
                return
            
            logger.info(f"프로파일 삭제: {profile_name}")
            result = config_manager.delete_profile(profile_name)
            
            if result:
                logger.info("프로파일 삭제 완료")
            else:
                logger.error("프로파일 삭제 실패")
        
        elif args.action == 'export':
            # 설정 내보내기
            if not args.file:
                logger.error("내보낼 파일 경로를 지정해야 합니다.")
                return
            
            logger.info(f"설정 내보내기: {args.file} ({args.format} 형식)")
            result = config_manager.export_config(args.file, args.format)
            
            if result:
                logger.info("설정 내보내기 완료")
            else:
                logger.error("설정 내보내기 실패")
        
        elif args.action == 'import':
            # 설정 가져오기
            if not args.file:
                logger.error("가져올 파일 경로를 지정해야 합니다.")
                return
            
            logger.info(f"설정 가져오기: {args.file}")
            result = config_manager.import_config(args.file)
            
            if result:
                logger.info("설정 가져오기 완료")
            else:
                logger.error("설정 가져오기 실패")
        
        else:
            logger.error(f"지원하지 않는 설정 작업: {args.action}")
    
    except Exception as e:
        logger.error(f"설정 작업 중 오류 발생: {e}")

def handle_transaction_command(args):
    """
    거래 관리 명령어 처리
    
    Args:
        args: 명령줄 인자
    """
    try:
        # 거래 저장소 초기화
        transaction_repository = TransactionRepository()
        
        if args.action == 'search':
            # 거래 검색
            search_params = {}
            
            if args.start_date:
                search_params['start_date'] = datetime.strptime(args.start_date, '%Y-%m-%d').date()
            
            if args.end_date:
                search_params['end_date'] = datetime.strptime(args.end_date, '%Y-%m-%d').date()
            
            if args.type:
                search_params['transaction_type'] = args.type
            
            if args.category:
                search_params['category'] = args.category
            
            if args.payment_method:
                search_params['payment_method'] = args.payment_method
            
            if args.min_amount:
                search_params['min_amount'] = args.min_amount
            
            if args.max_amount:
                search_params['max_amount'] = args.max_amount
            
            if args.description:
                search_params['description'] = args.description
            
            logger.info(f"거래 검색 시작: {search_params}")
            transactions = transaction_repository.search(**search_params)
            
            if transactions:
                print(f"검색 결과: {len(transactions)}개의 거래")
                
                for i, transaction in enumerate(transactions, 1):
                    transaction_dict = transaction.to_dict()
                    print(f"{i}. {transaction_dict['transaction_date']} | "
                          f"{transaction_dict['description']} | "
                          f"{transaction_dict['amount']}원 | "
                          f"{transaction_dict['category']} | "
                          f"{transaction_dict['payment_method']}")
                
                # 상세 정보 보기
                while True:
                    detail_input = input("\n상세 정보를 볼 거래 번호 (0: 종료): ")
                    if not detail_input or detail_input == '0':
                        break
                    
                    try:
                        index = int(detail_input) - 1
                        if 0 <= index < len(transactions):
                            transaction_dict = transactions[index].to_dict()
                            print("\n=== 거래 상세 정보 ===")
                            print(f"ID: {transaction_dict['transaction_id']}")
                            print(f"날짜: {transaction_dict['transaction_date']}")
                            print(f"내용: {transaction_dict['description']}")
                            print(f"금액: {transaction_dict['amount']}원")
                            print(f"유형: {transaction_dict['transaction_type']}")
                            print(f"카테고리: {transaction_dict['category']}")
                            print(f"결제방식: {transaction_dict['payment_method']}")
                            print(f"소스: {transaction_dict['source']}")
                            print(f"계좌유형: {transaction_dict['account_type']}")
                            if transaction_dict['memo']:
                                print(f"메모: {transaction_dict['memo']}")
                            print(f"생성일시: {transaction_dict['created_at']}")
                            print(f"수정일시: {transaction_dict['updated_at']}")
                        else:
                            print("올바른 거래 번호를 입력해주세요.")
                    except ValueError:
                        print("숫자를 입력해주세요.")
            else:
                print("검색 결과가 없습니다.")
        
        elif args.action == 'edit':
            # 거래 편집
            manual_manager = ManualTransactionManager()
            result = manual_manager.edit_transaction()
            
            if result:
                logger.info("거래 편집 완료")
            else:
                logger.error("거래 편집 실패")
        
        elif args.action == 'delete':
            # 거래 삭제
            if not args.id:
                logger.error("삭제할 거래 ID를 지정해야 합니다.")
                return
            
            # 거래 조회
            transaction = transaction_repository.get_by_transaction_id(args.id)
            if not transaction:
                logger.error(f"ID가 '{args.id}'인 거래를 찾을 수 없습니다.")
                return
            
            # 거래 정보 표시
            transaction_dict = transaction.to_dict()
            print("=== 삭제할 거래 정보 ===")
            print(f"ID: {transaction_dict['transaction_id']}")
            print(f"날짜: {transaction_dict['transaction_date']}")
            print(f"내용: {transaction_dict['description']}")
            print(f"금액: {transaction_dict['amount']}원")
            print(f"유형: {transaction_dict['transaction_type']}")
            print(f"카테고리: {transaction_dict['category']}")
            
            # 삭제 확인
            confirm = input("이 거래를 삭제하시겠습니까? (y/n): ")
            if confirm.lower() != 'y':
                logger.info("거래 삭제 취소")
                return
            
            # 거래 삭제
            logger.info(f"거래 삭제: {args.id}")
            result = transaction_repository.delete_by_transaction_id(args.id)
            
            if result:
                logger.info("거래 삭제 완료")
            else:
                logger.error("거래 삭제 실패")
        
        elif args.action == 'exclude':
            # 분석 제외 설정
            if not args.id:
                logger.error("거래 ID를 지정해야 합니다.")
                return
            
            # 거래 조회
            transaction = transaction_repository.get_by_transaction_id(args.id)
            if not transaction:
                logger.error(f"ID가 '{args.id}'인 거래를 찾을 수 없습니다.")
                return
            
            # 제외 여부 설정
            exclude = True if args.exclude is None else args.exclude.lower() == 'true'
            
            # 거래 업데이트
            transaction.exclude_from_analysis(exclude)
            result = transaction_repository.update(transaction)
            
            if result:
                logger.info(f"거래 분석 제외 설정 완료: {args.id} (제외: {exclude})")
            else:
                logger.error("거래 분석 제외 설정 실패")
        
        else:
            logger.error(f"지원하지 않는 거래 작업: {args.action}")
    
    except Exception as e:
        logger.error(f"거래 작업 중 오류 발생: {e}")

def handle_template_command(args):
    """
    템플릿 관리 명령어 처리
    
    Args:
        args: 명령줄 인자
    """
    try:
        # 수동 거래 관리자 초기화
        manual_manager = ManualTransactionManager()
        
        if args.action == 'list':
            # 템플릿 목록 조회
            manual_manager.manage_templates()
        
        elif args.action == 'add':
            # 템플릿 추가
            manual_manager._add_template()
        
        elif args.action == 'delete':
            # 템플릿 삭제
            manual_manager._delete_template()
        
        elif args.action == 'use':
            # 템플릿 사용
            manual_manager.use_template()
        
        else:
            logger.error(f"지원하지 않는 템플릿 작업: {args.action}")
    
    except Exception as e:
        logger.error(f"템플릿 작업 중 오류 발생: {e}")

def setup_parsers():
    """
    명령줄 인자 파서를 설정합니다.
    
    Returns:
        argparse.ArgumentParser: 설정된 인자 파서
    """
    # 메인 파서
    parser = argparse.ArgumentParser(
        description='금융 거래 관리 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
        예시:
          cli.py ingest toss_card --file data/toss_card_statement.xlsx
          cli.py analyze expense --period month
          cli.py report summary --format csv --output report.csv
          cli.py backup backup-db
          cli.py config get --key system.database.path
        ''')
    )
    
    # 공통 인자
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 로깅 활성화')
    parser.add_argument('--log-file', help='로그 파일 경로')
    
    # 서브파서
    subparsers = parser.add_subparsers(dest='command', help='명령어')
    
    # 데이터 수집 명령어
    ingest_parser = subparsers.add_parser('ingest', help='데이터 수집')
    ingest_parser.add_argument('source', choices=['toss_card', 'toss_account', 'manual', 'all'],
                              help='데이터 소스')
    ingest_parser.add_argument('--file', '-f', help='파일 경로')
    ingest_parser.add_argument('--type', '-t', choices=['expense', 'income', 'batch', 'template'],
                              default='expense', help='수동 입력 유형 (manual 소스에만 적용)')
    ingest_parser.set_defaults(func=handle_ingest_command)
    
    # 분석 명령어
    analyze_parser = subparsers.add_parser('analyze', help='거래 분석')
    analyze_parser.add_argument('type', choices=['expense', 'income', 'all', 'trend', 'comparison'],
                               help='분석 유형')
    analyze_parser.add_argument('--period', choices=['week', 'month', 'year', 'custom'],
                               default='month', help='분석 기간')
    analyze_parser.add_argument('--start-date', help='시작 날짜 (YYYY-MM-DD)')
    analyze_parser.add_argument('--end-date', help='종료 날짜 (YYYY-MM-DD)')
    analyze_parser.add_argument('--category', help='카테고리 필터')
    analyze_parser.add_argument('--payment-method', help='결제 방식 필터')
    analyze_parser.add_argument('--min-amount', type=float, help='최소 금액')
    analyze_parser.add_argument('--max-amount', type=float, help='최대 금액')
    analyze_parser.set_defaults(func=handle_analyze_command)
    
    # 리포트 명령어
    report_parser = subparsers.add_parser('report', help='리포트 생성')
    report_parser.add_argument('type', choices=['summary', 'detail', 'category', 'payment', 'monthly'],
                              help='리포트 유형')
    report_parser.add_argument('--period', choices=['week', 'month', 'year', 'custom'],
                              default='month', help='리포트 기간')
    report_parser.add_argument('--start-date', help='시작 날짜 (YYYY-MM-DD)')
    report_parser.add_argument('--end-date', help='종료 날짜 (YYYY-MM-DD)')
    report_parser.add_argument('--format', choices=['console', 'csv', 'json', 'html'],
                              default='console', help='출력 형식')
    report_parser.add_argument('--output', '-o', help='출력 파일 경로')
    report_parser.set_defaults(func=handle_report_command)
    
    # 백업 명령어
    backup_parser = subparsers.add_parser('backup', help='백업 및 복원')
    backup_parser.add_argument('action', choices=[
        'backup-db', 'restore-db', 'backup-config', 'restore-config',
        'export', 'import', 'list', 'verify', 'start-scheduler', 'stop-scheduler'
    ], help='백업 작업')
    backup_parser.add_argument('--type', '-t', choices=['full', 'incremental'],
                              default='full', help='백업 유형')
    backup_parser.add_argument('--file', '-f', help='파일 경로')
    backup_parser.add_argument('--format', choices=['csv', 'json'],
                              default='csv', help='내보내기/가져오기 형식')
    backup_parser.add_argument('--table', help='테이블 이름')
    backup_parser.set_defaults(func=handle_backup_command)
    
    # 설정 명령어
    config_parser = subparsers.add_parser('config', help='설정 관리')
    config_parser.add_argument('action', choices=[
        'get', 'set', 'reset', 'create-profile', 'load-profile',
        'list-profiles', 'delete-profile', 'export', 'import'
    ], help='설정 작업')
    config_parser.add_argument('--key', '-k', help='설정 키')
    config_parser.add_argument('--value', '-v', help='설정 값')
    config_parser.add_argument('--section', '-s', choices=['system', 'user', 'rules'],
                              help='설정 섹션')
    config_parser.add_argument('--profile', '-p', help='프로파일 이름')
    config_parser.add_argument('--file', '-f', help='파일 경로')
    config_parser.add_argument('--format', choices=['yaml', 'json'],
                              default='yaml', help='파일 형식')
    config_parser.set_defaults(func=handle_config_command)
    
    # 거래 관리 명령어
    transaction_parser = subparsers.add_parser('transaction', help='거래 관리')
    transaction_parser.add_argument('action', choices=['search', 'edit', 'delete', 'exclude'],
                                  help='거래 작업')
    transaction_parser.add_argument('--id', help='거래 ID')
    transaction_parser.add_argument('--start-date', help='시작 날짜 (YYYY-MM-DD)')
    transaction_parser.add_argument('--end-date', help='종료 날짜 (YYYY-MM-DD)')
    transaction_parser.add_argument('--type', choices=['expense', 'income'],
                                  help='거래 유형')
    transaction_parser.add_argument('--category', help='카테고리')
    transaction_parser.add_argument('--payment-method', help='결제 방식')
    transaction_parser.add_argument('--min-amount', type=float, help='최소 금액')
    transaction_parser.add_argument('--max-amount', type=float, help='최대 금액')
    transaction_parser.add_argument('--description', help='설명 검색어')
    transaction_parser.add_argument('--exclude', choices=['true', 'false'],
                                  help='분석 제외 여부')
    transaction_parser.set_defaults(func=handle_transaction_command)
    
    # 템플릿 관리 명령어
    template_parser = subparsers.add_parser('template', help='템플릿 관리')
    template_parser.add_argument('action', choices=['list', 'add', 'delete', 'use'],
                               help='템플릿 작업')
    template_parser.set_defaults(func=handle_template_command)
    
    return parser

def main():
    """
    메인 함수
    """
    # 인자 파서 설정
    parser = setup_parsers()
    args = parser.parse_args()
    
    # 로거 설정
    setup_logger(args.verbose, args.log_file)
    
    # 명령어 처리
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()