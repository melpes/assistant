#!/usr/bin/env python3
"""
통합 테스트 실행 전 환경 검증 스크립트

실제 Google Calendar API 통합 테스트를 실행하기 전에
필요한 환경과 인증 상태를 검증합니다.
"""
import os
import sys
import json
from pathlib import Path


def check_project_structure():
    """프로젝트 구조 확인"""
    print("1. 프로젝트 구조 확인...")
    
    project_root = Path(__file__).parent.parent
    required_paths = [
        project_root / "src" / "calendar",
        project_root / "src" / "calendar" / "providers",
        project_root / "tests" / "calendar",
        project_root / "src" / "config.py",
        project_root / "src" / "tools.py"
    ]
    
    missing_paths = []
    for path in required_paths:
        if not path.exists():
            missing_paths.append(str(path))
    
    if missing_paths:
        print("❌ 다음 경로가 없습니다:")
        for path in missing_paths:
            print(f"   - {path}")
        return False
    
    print("✅ 프로젝트 구조 확인 완료")
    return True


def check_auth_files():
    """인증 파일 확인"""
    print("\n2. 인증 파일 확인...")
    
    project_root = Path(__file__).parent.parent
    
    # credentials.json 확인
    credentials_path = project_root / "credentials.json"
    if not credentials_path.exists():
        print("❌ credentials.json 파일이 없습니다.")
        print("   Google Cloud Console에서 서비스 계정 키를 다운로드하여")
        print("   프로젝트 루트에 credentials.json으로 저장하세요.")
        return False
    
    # credentials.json 유효성 확인
    try:
        with open(credentials_path, 'r', encoding='utf-8') as f:
            creds_data = json.load(f)
        
        # OAuth 2.0 클라이언트 ID 형식 확인
        if 'installed' in creds_data:
            oauth_data = creds_data['installed']
            required_fields = ['client_id', 'project_id', 'auth_uri', 'token_uri', 'client_secret']
            missing_fields = [field for field in required_fields if field not in oauth_data]
            
            if missing_fields:
                print(f"❌ credentials.json에 필수 OAuth 필드가 없습니다: {missing_fields}")
                return False
            
            print("✅ credentials.json (OAuth 2.0 클라이언트 ID) 확인 완료")
        
        # 서비스 계정 형식 확인
        elif creds_data.get('type') == 'service_account':
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in creds_data]
            
            if missing_fields:
                print(f"❌ credentials.json에 필수 서비스 계정 필드가 없습니다: {missing_fields}")
                return False
            
            print("✅ credentials.json (서비스 계정) 확인 완료")
        
        else:
            print("❌ credentials.json이 올바른 형식이 아닙니다.")
            print("   OAuth 2.0 클라이언트 ID 또는 서비스 계정 키여야 합니다.")
            return False
        
    except json.JSONDecodeError:
        print("❌ credentials.json 파일이 유효한 JSON이 아닙니다.")
        return False
    except Exception as e:
        print(f"❌ credentials.json 확인 중 오류: {e}")
        return False
    
    # token.json 확인 (선택사항)
    token_path = project_root / "token.json"
    if token_path.exists():
        print("✅ token.json 파일 존재 (기존 인증 토큰)")
    else:
        print("ℹ️  token.json 파일 없음 (첫 실행 시 자동 생성)")
    
    return True


def check_dependencies():
    """의존성 확인"""
    print("\n3. 의존성 확인...")
    
    required_modules = [
        'google.auth',
        'googleapiclient.discovery',
        'google.auth.transport.requests',
        'google_auth_oauthlib.flow',
        'pytest'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("❌ 다음 모듈이 설치되지 않았습니다:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\n다음 명령어로 설치하세요:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ 의존성 확인 완료")
    return True


def check_calendar_service():
    """캘린더 서비스 초기화 확인"""
    print("\n4. 캘린더 서비스 초기화 확인...")
    
    try:
        # 프로젝트 루트를 Python 경로에 추가
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        from src.calendar.factory import CalendarServiceFactory
        
        factory = CalendarServiceFactory()
        service = factory.create_service()
        
        if service is None:
            print("❌ 캘린더 서비스 생성 실패")
            return False
        
        print("✅ 캘린더 서비스 초기화 성공")
        return True
        
    except Exception as e:
        print(f"❌ 캘린더 서비스 초기화 실패: {e}")
        print("\n가능한 원인:")
        print("- Google Calendar API가 활성화되지 않음")
        print("- 서비스 계정에 캘린더 권한이 없음")
        print("- 네트워크 연결 문제")
        return False


def test_basic_api_call():
    """기본 API 호출 테스트"""
    print("\n5. 기본 API 호출 테스트...")
    
    try:
        # 프로젝트 루트를 Python 경로에 추가
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        from src.calendar.factory import CalendarServiceFactory
        import datetime
        from datetime import timezone, timedelta
        
        factory = CalendarServiceFactory()
        service = factory.create_service()
        
        # 간단한 이벤트 목록 조회 테스트
        now = datetime.datetime.now(timezone.utc)
        start_time = now.isoformat()
        end_time = (now + timedelta(days=1)).isoformat()
        
        events = service.get_events_for_period(start_time, end_time)
        
        print(f"✅ API 호출 성공: {len(events)}개 이벤트 조회")
        return True
        
    except Exception as e:
        print(f"❌ API 호출 실패: {e}")
        print("\n가능한 원인:")
        print("- API 키 또는 인증 정보 오류")
        print("- Google Calendar API 할당량 초과")
        print("- 네트워크 연결 문제")
        return False


def main():
    """메인 검증 함수"""
    print("캘린더 서비스 통합 테스트 환경 검증")
    print("=" * 50)
    
    checks = [
        check_project_structure,
        check_auth_files,
        check_dependencies,
        check_calendar_service,
        test_basic_api_call
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check in checks:
        try:
            if check():
                passed_checks += 1
            else:
                print(f"\n⚠️  검증 실패: {check.__name__}")
        except Exception as e:
            print(f"\n❌ 검증 중 오류 ({check.__name__}): {e}")
    
    print("\n" + "=" * 50)
    print(f"검증 결과: {passed_checks}/{total_checks} 통과")
    
    if passed_checks == total_checks:
        print("✅ 모든 검증 통과! 통합 테스트를 실행할 수 있습니다.")
        print("\n다음 명령어로 통합 테스트를 실행하세요:")
        print("python tests/run_integration_tests.py")
        print("또는")
        print("python run_tests.py --type integration")
        return True
    else:
        print("❌ 일부 검증 실패. 문제를 해결한 후 다시 시도하세요.")
        print("\n도움말:")
        print("1. Google Cloud Console에서 Calendar API 활성화")
        print("2. 서비스 계정 생성 및 키 다운로드")
        print("3. credentials.json을 프로젝트 루트에 저장")
        print("4. pip install -r requirements.txt 실행")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)