#!/usr/bin/env python3
"""
캘린더 서비스 통합 테스트 실행 스크립트

실제 Google Calendar API와 연동하여 통합 테스트를 실행합니다.
이 스크립트는 실제 API 키와 인증 정보가 필요합니다.
"""
import os
import sys
import time
import subprocess
from pathlib import Path


def check_auth_files():
    """인증 파일 존재 여부 확인"""
    project_root = Path(__file__).parent.parent
    
    required_files = [
        project_root / "credentials.json",
        project_root / "token.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not file_path.exists():
            missing_files.append(file_path.name)
    
    if missing_files:
        print("❌ 다음 인증 파일이 없습니다:")
        for file_name in missing_files:
            print(f"   - {file_name}")
        print("\n통합 테스트를 실행하려면 Google Calendar API 인증이 필요합니다.")
        print("1. Google Cloud Console에서 Calendar API를 활성화하세요")
        print("2. 서비스 계정 키를 다운로드하여 credentials.json으로 저장하세요")
        print("3. 첫 실행 시 token.json이 자동 생성됩니다")
        return False
    
    print("✅ 인증 파일 확인 완료")
    return True


def run_auth_test():
    """인증 테스트 실행"""
    print("\n🔐 인증 테스트 실행 중...")
    
    try:
        # 간단한 인증 테스트
        sys.path.append(str(Path(__file__).parent.parent))
        from src.calendar.auth import GoogleAuthService
        
        auth_service = GoogleAuthService()
        service = auth_service.get_calendar_service()
        
        if service:
            print("✅ Google Calendar API 인증 성공")
            return True
        else:
            print("❌ Google Calendar API 인증 실패")
            return False
            
    except Exception as e:
        print(f"❌ 인증 테스트 실패: {e}")
        return False


def run_integration_tests(verbose=False, specific_test=None):
    """통합 테스트 실행"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # pytest 명령어 구성
    cmd = [
        "python", "-m", "pytest",
        "tests/calendar/test_integration.py",
        "-m", "integration",
        "-v" if verbose else "-q",
        "--tb=short",
        "--durations=10"  # 가장 느린 10개 테스트 표시
    ]
    
    if specific_test:
        cmd.extend(["-k", specific_test])
    
    print(f"\n🧪 통합 테스트 실행 중...")
    print(f"명령어: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, check=True, text=True)
        elapsed = time.time() - start_time
        
        print("=" * 60)
        print(f"✅ 통합 테스트 완료! (소요 시간: {elapsed:.2f}초)")
        return True
        
    except subprocess.CalledProcessError as e:
        print("=" * 60)
        print(f"❌ 통합 테스트 실패! (종료 코드: {e.returncode})")
        return False


def run_performance_tests():
    """성능 테스트만 실행"""
    print("\n⚡ 성능 테스트 실행 중...")
    
    performance_tests = [
        "test_list_events_performance",
        "test_create_event_performance",
        "test_large_time_range_query"
    ]
    
    for test_name in performance_tests:
        success = run_integration_tests(verbose=True, specific_test=test_name)
        if not success:
            print(f"❌ {test_name} 실패")
            return False
        time.sleep(1)  # API 호출 간격
    
    print("✅ 모든 성능 테스트 완료")
    return True


def run_error_tests():
    """에러 시나리오 테스트만 실행"""
    print("\n🚨 에러 시나리오 테스트 실행 중...")
    
    error_tests = [
        "test_error_scenarios",
        "test_service_resilience"
    ]
    
    for test_name in error_tests:
        success = run_integration_tests(verbose=True, specific_test=test_name)
        if not success:
            print(f"❌ {test_name} 실패")
            return False
        time.sleep(1)  # API 호출 간격
    
    print("✅ 모든 에러 시나리오 테스트 완료")
    return True


def run_crud_tests():
    """CRUD 플로우 테스트만 실행"""
    print("\n🔄 CRUD 플로우 테스트 실행 중...")
    
    crud_tests = [
        "test_full_crud_flow",
        "test_concurrent_operations"
    ]
    
    for test_name in crud_tests:
        success = run_integration_tests(verbose=True, specific_test=test_name)
        if not success:
            print(f"❌ {test_name} 실패")
            return False
        time.sleep(2)  # API 호출 간격 (CRUD는 더 긴 간격)
    
    print("✅ 모든 CRUD 테스트 완료")
    return True


def run_tools_integration():
    """tools.py 통합 테스트 실행"""
    print("\n🛠️ tools.py 통합 테스트 실행 중...")
    
    success = run_integration_tests(verbose=True, specific_test="TestToolsIntegration")
    if success:
        print("✅ tools.py 통합 테스트 완료")
    else:
        print("❌ tools.py 통합 테스트 실패")
    
    return success


def main():
    print("캘린더 서비스 통합 테스트 실행기")
    print("=" * 50)
    
    # 인증 파일 확인
    if not check_auth_files():
        sys.exit(1)
    
    # 인증 테스트
    if not run_auth_test():
        print("\n인증에 실패했습니다. 설정을 확인해주세요.")
        sys.exit(1)
    
    # 메뉴 표시
    print("\n테스트 옵션을 선택하세요:")
    print("1. 전체 통합 테스트 실행")
    print("2. 성능 테스트만 실행")
    print("3. 에러 시나리오 테스트만 실행")
    print("4. CRUD 플로우 테스트만 실행")
    print("5. tools.py 통합 테스트만 실행")
    print("6. 종료")
    
    while True:
        try:
            choice = input("\n선택 (1-6): ").strip()
            
            if choice == "1":
                success = run_integration_tests(verbose=True)
                break
            elif choice == "2":
                success = run_performance_tests()
                break
            elif choice == "3":
                success = run_error_tests()
                break
            elif choice == "4":
                success = run_crud_tests()
                break
            elif choice == "5":
                success = run_tools_integration()
                break
            elif choice == "6":
                print("종료합니다.")
                sys.exit(0)
            else:
                print("잘못된 선택입니다. 1-6 중에서 선택해주세요.")
                continue
                
        except KeyboardInterrupt:
            print("\n\n테스트가 중단되었습니다.")
            sys.exit(1)
    
    if success:
        print("\n🎉 통합 테스트가 성공적으로 완료되었습니다!")
        print("\n주의사항:")
        print("- 테스트 중 생성된 일정이 있다면 Google Calendar에서 확인해주세요")
        print("- 일부 테스트 일정은 자동으로 삭제되지만, 실패 시 수동 삭제가 필요할 수 있습니다")
    else:
        print("\n❌ 통합 테스트가 실패했습니다.")
        print("로그를 확인하여 문제를 해결해주세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()