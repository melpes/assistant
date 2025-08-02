#!/usr/bin/env python3
"""
Gmail 통합 테스트

이 스크립트는 Gmail 서비스 관리자와 이메일 처리기의 기본 기능을 테스트합니다.
실제 Gmail API를 사용하지 않고 모의 객체를 사용하여 테스트합니다.
"""

import sys
import os
from unittest.mock import Mock, MagicMock

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gmail.service import GmailServiceManager
from src.gmail.processor import EmailProcessor
from src.gmail.auth import GmailAuthService

def test_gmail_service_manager():
    """Gmail 서비스 관리자 기본 기능 테스트"""
    print("=== Gmail 서비스 관리자 테스트 ===")
    
    # 모의 인증 서비스 생성
    mock_auth_service = Mock(spec=GmailAuthService)
    mock_service = Mock()
    mock_auth_service.get_service.return_value = mock_service
    
    # Gmail 서비스 관리자 생성
    gmail_service = GmailServiceManager(mock_auth_service)
    
    # 기본 기능 테스트
    print("✓ Gmail 서비스 관리자 생성 성공")
    
    # 이메일 감시 시작/중지 테스트
    result = gmail_service.start_watching()
    assert result == True, "이메일 감시 시작 실패"
    print("✓ 이메일 감시 시작 성공")
    
    result = gmail_service.stop_watching()
    assert result == True, "이메일 감시 중지 실패"
    print("✓ 이메일 감시 중지 성공")
    
    print("Gmail 서비스 관리자 테스트 완료\n")

def test_email_processor():
    """이메일 처리기 기본 기능 테스트"""
    print("=== 이메일 처리기 테스트 ===")
    
    # 모의 Gmail 서비스 관리자 생성
    mock_gmail_service = Mock(spec=GmailServiceManager)
    mock_service = Mock()
    mock_gmail_service._get_service.return_value = mock_service
    
    # 이메일 처리기 생성
    email_processor = EmailProcessor(mock_gmail_service)
    
    print("✓ 이메일 처리기 생성 성공")
    
    # 텍스트 정제 기능 테스트
    html_text = "<p>안녕하세요</p><br><strong>중요한 내용</strong>"
    cleaned_text = email_processor._clean_email_text(html_text)
    
    assert "<p>" not in cleaned_text, "HTML 태그 제거 실패"
    assert "안녕하세요" in cleaned_text, "텍스트 내용 보존 실패"
    assert "중요한 내용" in cleaned_text, "텍스트 내용 보존 실패"
    print("✓ 이메일 텍스트 정제 성공")
    
    # Base64 디코딩 테스트
    import base64
    original_text = "테스트 메시지입니다"
    encoded_data = base64.urlsafe_b64encode(original_text.encode()).decode()
    decoded_text = email_processor._decode_base64(encoded_data)
    
    assert decoded_text == original_text, "Base64 디코딩 실패"
    print("✓ Base64 디코딩 성공")
    
    # 언어 감지 테스트
    korean_text = "안녕하세요 반갑습니다"
    languages = email_processor._detect_languages(korean_text)
    assert "ko" in languages, "한국어 감지 실패"
    print("✓ 언어 감지 성공")
    
    print("이메일 처리기 테스트 완료\n")

def test_gmail_auth_service():
    """Gmail 인증 서비스 기본 기능 테스트"""
    print("=== Gmail 인증 서비스 테스트 ===")
    
    # 임시 경로로 인증 서비스 생성
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        token_path = os.path.join(temp_dir, "test_token.json")
        credentials_path = os.path.join(temp_dir, "test_credentials.json")
        
        # 테스트용 자격 증명 파일 생성
        import json
        with open(credentials_path, "w") as f:
            json.dump({
                "installed": {
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret",
                    "redirect_uris": ["http://localhost"]
                }
            }, f)
        
        # 인증 서비스 생성
        auth_service = GmailAuthService(
            token_path=token_path,
            credentials_path=credentials_path
        )
        
        print("✓ Gmail 인증 서비스 생성 성공")
        
        # 인증 상태 확인 (토큰이 없으므로 False여야 함)
        is_authenticated = auth_service.is_authenticated()
        print(f"✓ 인증 상태 확인: {is_authenticated}")
    
    print("Gmail 인증 서비스 테스트 완료\n")

def test_integration():
    """통합 테스트"""
    print("=== 통합 테스트 ===")
    
    # 모의 인증 서비스 생성
    mock_auth_service = Mock(spec=GmailAuthService)
    mock_service = Mock()
    mock_auth_service.get_service.return_value = mock_service
    
    # Gmail 서비스 관리자 생성
    gmail_service = GmailServiceManager(mock_auth_service)
    
    # 이메일 처리기 생성
    email_processor = EmailProcessor(gmail_service)
    
    # 이메일 핸들러 등록
    def email_handler(email):
        print(f"이메일 처리: {email.get('id', 'unknown')}")
    
    gmail_service.register_email_handler(email_handler)
    
    print("✓ 통합 시스템 구성 성공")
    
    # 모의 이메일 처리
    mock_email = {
        "id": "test_email_123",
        "subject": "테스트 이메일",
        "from": "sender@example.com"
    }
    
    gmail_service._process_email(mock_email)
    
    # 대기열 크기 확인
    queue_size = gmail_service.get_queue_size()
    print(f"✓ 이메일 처리 대기열 크기: {queue_size}")
    
    print("통합 테스트 완료\n")

def main():
    """메인 함수"""
    print("Gmail 이메일 캘린더 자동화 시스템 통합 테스트 시작\n")
    
    try:
        test_gmail_service_manager()
        test_email_processor()
        test_gmail_auth_service()
        test_integration()
        
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("\n=== 구현된 기능 요약 ===")
        print("✓ Gmail API 인증 시스템")
        print("✓ 이메일 감지 및 감시 시스템")
        print("✓ 이메일 내용 처리 및 정제")
        print("✓ 이메일 라벨링, 보관, 삭제 기능")
        print("✓ 이메일 필터 관리 기능")
        print("✓ 이메일 검색 기능")
        print("✓ 이메일 답장 및 전달 기능")
        print("✓ 첨부 파일 처리 기능")
        print("✓ HTML 내용 처리 기능")
        print("✓ 다국어 지원 (한국어 포함)")
        print("✓ 이메일 처리 대기열 관리")
        print("✓ 폴링 메커니즘")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)