#!/usr/bin/env python3
"""
수동 테스트 실행 스크립트

이 스크립트는 실제 Google API를 사용하는 수동 테스트들을 실행합니다.
실행하기 전에 Google API 인증이 설정되어 있어야 합니다.
"""
import os
import sys
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_auth_test():
    """인증 서비스 테스트 실행"""
    print("=" * 60)
    print("GoogleAuthService 수동 테스트 실행")
    print("=" * 60)
    
    try:
        from tests.legacy.test_auth_service_legacy import test_auth_service_manual
        test_auth_service_manual()
    except Exception as e:
        print(f"인증 테스트 실행 중 오류: {e}")

def run_models_test():
    """모델 테스트 실행"""
    print("=" * 60)
    print("CalendarEvent 모델 수동 테스트 실행")
    print("=" * 60)
    
    try:
        from tests.legacy.test_calendar_models_legacy import test_calendar_event_creation_manual
        test_calendar_event_creation_manual()
    except Exception as e:
        print(f"모델 테스트 실행 중 오류: {e}")

def run_provider_test():
    """Google Provider 테스트 실행"""
    print("=" * 60)
    print("GoogleCalendarProvider 수동 테스트 실행")
    print("=" * 60)
    
    try:
        from tests.legacy.test_google_provider_manual import test_list_events_manual, test_create_event_manual
        test_list_events_manual()
        print("\n" + "-" * 40 + "\n")
        test_create_event_manual()
    except Exception as e:
        print(f"Provider 테스트 실행 중 오류: {e}")

def run_tools_test():
    """Tools 통합 테스트 실행"""
    print("=" * 60)
    print("tools.py 캘린더 함수 통합 테스트 실행")
    print("=" * 60)
    
    try:
        from tests.legacy.test_tools_integration import test_tools_calendar_integration
        test_tools_calendar_integration()
    except Exception as e:
        print(f"Tools 테스트 실행 중 오류: {e}")

def main():
    parser = argparse.ArgumentParser(description="수동 테스트 실행")
    parser.add_argument(
        "--test",
        choices=["auth", "models", "provider", "tools", "all"],
        default="all",
        help="실행할 테스트 선택"
    )
    parser.add_argument(
        "--check-auth",
        action="store_true",
        help="테스트 실행 전 인증 상태 확인"
    )
    
    args = parser.parse_args()
    
    # 인증 상태 확인
    if args.check_auth:
        print("인증 상태 확인 중...")
        try:
            from src.calendar.auth import GoogleAuthService
            auth_service = GoogleAuthService()
            if auth_service.is_authenticated():
                print("✅ 인증 상태: 정상")
            else:
                print("❌ 인증 상태: 인증 필요")
                print("Google API 인증을 먼저 설정해주세요.")
                return
        except Exception as e:
            print(f"❌ 인증 확인 중 오류: {e}")
            return
        print()
    
    # 테스트 실행
    if args.test == "all":
        run_auth_test()
        print("\n")
        run_models_test()
        print("\n")
        run_provider_test()
        print("\n")
        run_tools_test()
    elif args.test == "auth":
        run_auth_test()
    elif args.test == "models":
        run_models_test()
    elif args.test == "provider":
        run_provider_test()
    elif args.test == "tools":
        run_tools_test()
    
    print("\n" + "=" * 60)
    print("수동 테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    main()