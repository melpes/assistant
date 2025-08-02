"""
Gmail API 인증 테스트
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.gmail.auth import GmailAuthService

class TestGmailAuthService(unittest.TestCase):
    """Gmail API 인증 서비스 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 임시 파일 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        self.token_path = os.path.join(self.temp_dir.name, "test_token.json")
        self.credentials_path = os.path.join(self.temp_dir.name, "test_credentials.json")
        
        # 테스트용 자격 증명 파일 생성
        with open(self.credentials_path, "w") as f:
            json.dump({
                "installed": {
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret",
                    "redirect_uris": ["http://localhost"]
                }
            }, f)
        
        # 테스트용 토큰 파일 생성
        with open(self.token_path, "w") as f:
            json.dump({
                "token": "test_token",
                "refresh_token": "test_refresh_token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "scopes": ["https://www.googleapis.com/auth/gmail.modify"]
            }, f)
        
        # 인증 서비스 생성
        self.auth_service = GmailAuthService(
            token_path=self.token_path,
            credentials_path=self.credentials_path
        )
    
    def tearDown(self):
        """테스트 정리"""
        self.temp_dir.cleanup()
    
    @patch("src.gmail.auth.Credentials")
    def test_get_credentials_from_token(self, mock_credentials):
        """토큰 파일에서 자격 증명 로드 테스트"""
        # 모의 자격 증명 설정
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_credentials.from_authorized_user_info.return_value = mock_creds
        
        # 자격 증명 가져오기
        creds = self.auth_service.get_credentials()
        
        # 검증
        self.assertEqual(creds, mock_creds)
        mock_credentials.from_authorized_user_info.assert_called_once()
    
    @patch("src.gmail.auth.Credentials")
    def test_get_credentials_refresh_token(self, mock_credentials):
        """만료된 토큰 갱신 테스트"""
        # 모의 자격 증명 설정
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "test_refresh_token"
        mock_credentials.from_authorized_user_info.return_value = mock_creds
        
        # 자격 증명 가져오기
        creds = self.auth_service.get_credentials()
        
        # 검증
        self.assertEqual(creds, mock_creds)
        mock_creds.refresh.assert_called_once()
    
    @patch("src.gmail.auth.InstalledAppFlow")
    def test_start_auth_flow(self, mock_flow):
        """새로운 인증 플로우 테스트"""
        # 기존 토큰 파일 삭제
        os.remove(self.token_path)
        
        # 모의 플로우 설정
        mock_flow_instance = MagicMock()
        mock_creds = MagicMock()
        mock_creds.to_json.return_value = json.dumps({
            "token": "new_test_token",
            "refresh_token": "new_test_refresh_token"
        })
        mock_flow_instance.run_local_server.return_value = mock_creds
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance
        
        # 패치 적용
        with patch.object(self.auth_service, "_start_auth_flow", return_value=mock_creds):
            # 자격 증명 가져오기
            creds = self.auth_service.get_credentials()
            
            # 검증
            self.assertEqual(creds, mock_creds)
    
    def test_revoke_token(self):
        """토큰 취소 테스트"""
        # 모의 자격 증명 설정
        mock_creds = MagicMock()
        mock_creds.token = "test_token"
        self.auth_service._credentials = mock_creds
        
        # Request 패치
        with patch("src.gmail.auth.Request") as mock_request:
            mock_request_instance = MagicMock()
            mock_request.return_value = mock_request_instance
            
            # 토큰 취소
            result = self.auth_service.revoke_token()
            
            # 검증
            self.assertTrue(result)
            mock_request_instance.post.assert_called_once()
            self.assertFalse(os.path.exists(self.token_path))
    
    @patch("src.gmail.auth.Credentials")
    def test_is_authenticated(self, mock_credentials):
        """인증 상태 확인 테스트"""
        # 모의 자격 증명 설정
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.from_authorized_user_info.return_value = mock_creds
        
        # 인증 상태 확인
        result = self.auth_service.is_authenticated()
        
        # 검증
        self.assertTrue(result)
    
    @patch("src.gmail.auth.build")
    @patch("src.gmail.auth.Credentials")
    def test_get_service(self, mock_credentials, mock_build):
        """서비스 객체 가져오기 테스트"""
        # 모의 자격 증명 설정
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_credentials.from_authorized_user_info.return_value = mock_creds
        
        # 모의 서비스 설정
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        # 서비스 객체 가져오기
        service = self.auth_service.get_service()
        
        # 검증
        self.assertEqual(service, mock_service)
        mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)

if __name__ == "__main__":
    unittest.main()