"""
Google 인증 서비스 단위 테스트
"""
import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock, mock_open
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from src.calendar.auth import GoogleAuthService
from src.calendar.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    NetworkError,
    PermissionDeniedError,
    APIQuotaExceededError,
    ServerError
)


class TestGoogleAuthService:
    """GoogleAuthService 클래스 테스트"""
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock Credentials 객체"""
        creds = Mock(spec=Credentials)
        creds.valid = True
        creds.expired = False
        creds.refresh_token = "refresh_token"
        return creds
    
    @pytest.fixture
    def auth_service(self):
        """테스트용 GoogleAuthService 인스턴스"""
        return GoogleAuthService(
            scopes=["https://www.googleapis.com/auth/calendar"],
            token_path="test_token.json",
            credentials_path="test_credentials.json"
        )
    
    def test_init_default_values(self):
        """기본값으로 GoogleAuthService 초기화 테스트"""
        service = GoogleAuthService()
        
        assert service.scopes == ["https://www.googleapis.com/auth/calendar"]
        assert "token.json" in service.token_path
        assert "credentials.json" in service.credentials_path
    
    def test_init_custom_values(self):
        """사용자 정의 값으로 GoogleAuthService 초기화 테스트"""
        custom_scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
        service = GoogleAuthService(
            scopes=custom_scopes,
            token_path="custom_token.json",
            credentials_path="custom_credentials.json"
        )
        
        assert service.scopes == custom_scopes
        assert service.token_path == "custom_token.json"
        assert service.credentials_path == "custom_credentials.json"
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.calendar.auth.Credentials.from_authorized_user_file')
    def test_get_credentials_valid_token_exists(self, mock_from_file, mock_file, mock_exists, auth_service, mock_credentials):
        """유효한 토큰 파일이 존재할 때 get_credentials 테스트"""
        mock_exists.return_value = True
        mock_from_file.return_value = mock_credentials
        
        result = auth_service.get_credentials()
        
        assert result == mock_credentials
        mock_from_file.assert_called_once_with("test_token.json", auth_service.scopes)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.calendar.auth.Credentials.from_authorized_user_file')
    def test_get_credentials_expired_token_refresh_success(self, mock_from_file, mock_file, mock_exists, auth_service, mock_credentials):
        """만료된 토큰을 성공적으로 갱신하는 테스트"""
        mock_exists.return_value = True
        mock_credentials.valid = False
        mock_credentials.expired = True
        mock_from_file.return_value = mock_credentials
        
        # refresh 메서드 모킹
        mock_credentials.refresh = Mock()
        
        with patch('src.calendar.auth.Request') as mock_request:
            result = auth_service.get_credentials()
            
            assert result == mock_credentials
            mock_credentials.refresh.assert_called_once()
            mock_file.assert_called()  # 토큰 저장 확인
    
    @patch('os.path.exists')
    @patch('src.calendar.auth.Credentials.from_authorized_user_file')
    @patch('src.calendar.auth.InstalledAppFlow.from_client_secrets_file')
    def test_get_credentials_refresh_failure(self, mock_flow, mock_from_file, mock_exists, auth_service, mock_credentials):
        """토큰 갱신 실패 시 새로운 인증 플로우 시작 테스트"""
        # 토큰 파일은 있고, credentials 파일도 있다고 설정
        mock_exists.side_effect = lambda path: True
        mock_credentials.valid = False
        mock_credentials.expired = True
        mock_credentials.refresh_token = "refresh_token"
        mock_from_file.return_value = mock_credentials
        
        # refresh 메서드가 RefreshError를 발생시키도록 설정
        mock_credentials.refresh = Mock(side_effect=RefreshError("Refresh failed"))
        
        # 새로운 인증 플로우 모킹
        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = mock_credentials
        mock_flow.return_value = mock_flow_instance
        
        with patch('src.calendar.auth.Request'):
            result = auth_service.get_credentials()
            
            # 새로운 인증 플로우가 시작되었는지 확인
            assert result == mock_credentials
            mock_flow.assert_called_once()
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.calendar.auth.InstalledAppFlow.from_client_secrets_file')
    def test_get_credentials_no_token_new_auth_flow(self, mock_flow, mock_file, mock_exists, auth_service, mock_credentials):
        """토큰이 없을 때 새로운 인증 플로우 테스트"""
        # 토큰 파일은 없고 credentials 파일은 있음
        mock_exists.side_effect = lambda path: "credentials" in path
        
        # Flow 모킹
        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = mock_credentials
        mock_flow.return_value = mock_flow_instance
        
        result = auth_service.get_credentials()
        
        assert result == mock_credentials
        mock_flow.assert_called_once_with("test_credentials.json", auth_service.scopes)
        mock_flow_instance.run_local_server.assert_called_once_with(port=0)
        mock_file.assert_called()  # 토큰 저장 확인
    
    @patch('os.path.exists')
    def test_get_credentials_no_credentials_file(self, mock_exists, auth_service):
        """credentials.json 파일이 없을 때 예외 발생 테스트"""
        mock_exists.return_value = False
        
        with pytest.raises(AuthenticationError, match="인증 정보 파일을 찾을 수 없습니다"):
            auth_service.get_credentials()
    
    @patch('os.path.exists')
    @patch('src.calendar.auth.Credentials.from_authorized_user_file')
    @patch('src.calendar.auth.InstalledAppFlow.from_client_secrets_file')
    def test_get_credentials_invalid_token_no_refresh_token(self, mock_flow, mock_from_file, mock_exists, auth_service, mock_credentials):
        """유효하지 않은 토큰이고 refresh_token이 없을 때 새로운 인증 플로우 시작 테스트"""
        mock_exists.return_value = True
        mock_credentials.valid = False
        mock_credentials.expired = True
        mock_credentials.refresh_token = None
        mock_from_file.return_value = mock_credentials
        
        # 새로운 인증 플로우 모킹
        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = mock_credentials
        mock_flow.return_value = mock_flow_instance
        
        result = auth_service.get_credentials()
        
        # 새로운 인증 플로우가 시작되었는지 확인
        assert result == mock_credentials
        mock_flow.assert_called_once()
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('src.calendar.auth.Credentials.from_authorized_user_file')
    @patch('src.calendar.auth.InstalledAppFlow.from_client_secrets_file')
    def test_save_credentials(self, mock_flow, mock_from_file, mock_file, mock_exists, auth_service, mock_credentials):
        """인증 정보 저장 테스트"""
        # 토큰 파일이 없어서 새로운 인증 플로우가 실행되는 경우
        mock_exists.side_effect = lambda path: "credentials" in path  # credentials 파일만 존재
        mock_credentials.to_json.return_value = '{"token": "test_token"}'
        
        # 새로운 인증 플로우 모킹
        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = mock_credentials
        mock_flow.return_value = mock_flow_instance
        
        auth_service.get_credentials()
        
        # 파일 저장이 호출되었는지 확인
        mock_file.assert_called()
        handle = mock_file()
        handle.write.assert_called_with('{"token": "test_token"}')
    
    @patch('os.path.exists')
    @patch('src.calendar.auth.Credentials.from_authorized_user_file')
    def test_get_credentials_file_permission_error(self, mock_from_file, mock_exists, auth_service):
        """파일 권한 오류 시 예외 발생 테스트"""
        mock_exists.return_value = True
        mock_from_file.side_effect = PermissionError("Permission denied")
        
        with pytest.raises(AuthenticationError):
            auth_service.get_credentials()
    
    @patch('os.path.exists')
    @patch('src.calendar.auth.Credentials.from_authorized_user_file')
    def test_get_credentials_json_decode_error(self, mock_from_file, mock_exists, auth_service):
        """JSON 디코딩 오류 시 예외 발생 테스트"""
        mock_exists.return_value = True
        mock_from_file.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        with pytest.raises(AuthenticationError):
            auth_service.get_credentials()
    
    def test_is_authenticated_with_valid_credentials(self, auth_service, mock_credentials):
        """유효한 인증 정보가 있을 때 is_authenticated 테스트"""
        with patch.object(auth_service, 'get_credentials', return_value=mock_credentials):
            assert auth_service.is_authenticated() is True
    
    def test_is_authenticated_with_invalid_credentials(self, auth_service):
        """유효하지 않은 인증 정보가 있을 때 is_authenticated 테스트"""
        with patch.object(auth_service, 'get_credentials', side_effect=AuthenticationError("Auth failed")):
            assert auth_service.is_authenticated() is False
    
    @patch('os.path.exists')
    @patch('os.remove')
    def test_revoke_token_success(self, mock_remove, mock_exists, auth_service):
        """토큰 취소 성공 테스트"""
        mock_exists.return_value = True
        
        result = auth_service.revoke_token()
        
        assert result is True
        mock_remove.assert_called_once_with("test_token.json")
    
    @patch('os.path.exists')
    def test_revoke_token_file_not_exists(self, mock_exists, auth_service):
        """토큰 파일이 없을 때 취소 테스트"""
        mock_exists.return_value = False
        
        result = auth_service.revoke_token()
        
        assert result is False
    
    @patch('os.path.exists')
    @patch('os.remove')
    def test_revoke_token_permission_error(self, mock_remove, mock_exists, auth_service):
        """토큰 삭제 권한 오류 테스트"""
        mock_exists.return_value = True
        mock_remove.side_effect = PermissionError("Permission denied")
        
        result = auth_service.revoke_token()
        
        assert result is False