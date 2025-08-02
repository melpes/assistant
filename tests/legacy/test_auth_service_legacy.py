"""
GoogleAuthService 레거시 테스트 (수동 실행용)
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.calendar.auth import GoogleAuthService
from src.calendar.exceptions import AuthenticationError

def test_auth_service_manual():
    """GoogleAuthService 수동 테스트 (실제 API 사용)"""
    
    print("=== GoogleAuthService 수동 테스트 ===")
    
    # 인증 서비스 인스턴스 생성
    auth_service = GoogleAuthService()
    
    # 인증 상태 확인
    is_authenticated = auth_service.is_authenticated()
    print(f"인증 상태: {'인증됨' if is_authenticated else '인증되지 않음'}")
    
    try:
        # 자격 증명 가져오기
        creds = auth_service.get_credentials()
        print("자격 증명을 성공적으로 가져왔습니다.")
        
        # 자격 증명 정보 출력
        print(f"만료 여부: {'만료됨' if creds.expired else '유효함'}")
        print(f"토큰 만료 시간: {creds.expiry}")
        
    except AuthenticationError as e:
        print(f"인증 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")

if __name__ == "__main__":
    test_auth_service_manual()